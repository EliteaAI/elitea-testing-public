"""UI test — Chat reports a meaningful error when the assigned LLM model uses an invalid credential.

Test case: ELITEA-2416
AFS: test-specs/settings-ai-providers/l2_chat-error-when-llm-model-uses-invalid-credential_ELITEA-2416.md

**SANCTIONED-RED spec** (`.agents/testing.md` § Merge gate, *Analysis-time entry*).
The case's final step — "no raw stack trace or internal error details are exposed
to the user" — FAILS against the live product: the chat renders a raw Python
traceback, an internal exception class, a LiteLLM table name and a credential key
hash. Filed as **EliteaAI/elitea-testing-public#1993** (`bug`, OPEN). The assertion
is written here as the CORRECT expected behaviour under `expect.soft()` +
`# Known defect: #1993`, so steps 1-7 keep reporting and the spec flips green when
the product fix ships. Nothing is masked — `expect.soft` failures ARE pytest
failures on this stack, which is exactly how the red stays visible.

Case-identity note (AFS § Case-identity note): "Settings -> Credentials" and
"Settings -> AI Configuration" are both **Settings -> AI Providers**
(`/settings/ai-providers`); the "+" flow is `/settings/create-ai-provider/{type}`.
Same nonexistent-"AI Configuration"-page drift already tracked by #1250 / #1772 /
#1906 / #1982 — not re-filed.

Step-4 adaptation, DECLARED (`.agents/role-overrides.md` § Declared-improvisation
protocol; AFS § Coverage Map). The case says "open or create an agent that uses the
newly created invalid LLM model". Live, the model is bound to the turn through the
SAME `model-selector-*` control in the plain `/chat` composer and in an agent's
embedded chat panel, and the failure originates in the predict path rather than in
the agent wrapper. This spec therefore selects the model directly in the chat
session — one fewer shared-project object to create and orphan, with the same
observable. It changes the VEHICLE, not what is verified.

No substitution of the system under test (AFS § Fidelity Declaration): every
artifact is created through the real UI form against the real backend, the failure
is produced by the real LLM gateway rejecting a real (invalid) key, and every
asserted value is read off the product's own response bodies and Socket.IO frames.
No `route.fulfill`, no `page.evaluate` writing state, no API-seeded precondition for
a step the case performs in the UI. The API is used ONLY in teardown, which asserts
nothing. Socket.IO frame capture is passive observation, not substitution
(`utils/websocket_frames.py`).

**This spec MUTATES shared project configuration**: it creates a real AI credential
and a real LLM model configuration, both of which appear in every model selector in
the project until deleted. Teardown is name-based, so an object created before a
mid-flow failure is still removed even if its id was never read back. The model is
deleted before the credential (the model references it), and the conversation the
chat step creates is deleted too — the shared user's chat list is already heavily
polluted (`#1082`).

Markers:
    - ui, settings, chat, p2, regression, new
"""

import logging
import re
import time

import allure
import pytest
from config import settings
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.settings,
    pytest.mark.chat,
    pytest.mark.p2,
    pytest.mark.regression,
    pytest.mark.new,
]

# --- The case's Test Data, in ONE block -----------------------------------
CREDENTIAL_TYPE = "open_ai"
MODEL_TYPE = "llm_model"
SECRET_FIELD_KEY = "api_key"
BASE_FIELD_KEY = "api_base"
NAME_FIELD_KEY = "name"
API_BASE = "https://dev.elitea.ai/llm/v1"
INVALID_API_KEY = "sk-invalid-2416-xyz"
#: The llm_model schema's own default for Context Window — asserted, never
#: typed; its arrival is what proves the schema-defaults render has landed.
DEFAULT_CONTEXT_WINDOW = "128000"
CHAT_MESSAGE = "Hello, reply with one word."

#: MAX_NAME_LENGTH on the Display Name input (EliteaUI/src/common/constants.js) —
#: an over-long name is silently TRUNCATED by the field and every later lookup
#: by name then misses, far from the cause.
MAX_DISPLAY_NAME_LENGTH = 32

#: What must NOT reach the user (case step 9). Every alternative is a distinct
#: leak observed live and quoted on #1993: a Python traceback header, a server
#: file path, the internal exception class, an internal DB table name, and the
#: credential key hash.
INTERNAL_DETAIL_PATTERN = re.compile(
    r"Traceback \(most recent call last\)"
    r'|File "/data/'
    r"|InternalSDKError"
    r"|LiteLLM_VerificationTokenTable"
    r"|Key Hash",
    re.IGNORECASE,
)
#: The same leak, surfaced as a tool label rather than as card text.
STACKTRACE_CHIP_TEXT = "Agent Exception Stacktrace"

CREATE_RESPONSE_TIMEOUT = 30_000
UI_ELEMENT_TIMEOUT = 10_000
#: The failing turn resolved in ~8 s live; this is the bounded wait behind the
#: case's "does not hang indefinitely" (step 7), not a settle time.
ERROR_FRAME_TIMEOUT_MS = 90_000
FRAME_POLL_MS = 500

CONVERSATION_URL_PATTERN = re.compile(r"/chat/(\d+)")


def _configurations_matcher(response) -> bool:
    return (
        f"/configurations/configurations/{settings.elitea_project_id}" in response.url
        and response.request.method == "POST"
    )


def _wait_for_error_frame(page, frames, start_index: int) -> dict | None:
    """Return the first ``chat_message_sync`` frame after *start_index* whose
    ``meta.error`` is non-empty, or ``None`` if none arrives in time.

    Pumped with ``page.wait_for_timeout`` and NOT ``time.sleep``: Playwright's
    sync API dispatches ``framereceived`` only while the calling thread is
    inside a Playwright call, so a ``time.sleep`` poll starves the dispatcher
    and the frame list cannot grow (`.agents/testing.md`, measured 2026-08-27).
    """
    deadline = time.monotonic() + ERROR_FRAME_TIMEOUT_MS / 1000
    while True:
        for frame in frames[start_index:]:
            if frame.get("event") != "chat_message_sync":
                continue
            meta = frame.get("meta")
            if isinstance(meta, dict) and meta.get("error"):
                return frame
        if time.monotonic() >= deadline:
            return None
        page.wait_for_timeout(FRAME_POLL_MS)


def _delete_configuration_by_name(credential_api, display_name: str, known_id=None) -> None:
    """Delete the configuration named *display_name* (id-first, name-fallback).

    The name fallback is what makes teardown survive a failure BETWEEN the
    create POST and the id read-back — the window the teardown-guard ordering
    rule exists to close (`.agents/testing.md` § Teardown-guard ordering).
    """
    target_id = known_id
    if target_id is None:
        for item in credential_api.list_all_credentials():
            if item.get("label") == display_name or item.get("elitea_title") == display_name:
                target_id = item.get("id")
                break
    if target_id is None:
        logger.info("Teardown: no configuration named %r to delete", display_name)
        return
    credential_api.delete_credential(target_id)
    logger.info("Teardown: deleted configuration %r (id=%s)", display_name, target_id)


# reruns=0 because this spec is SANCTIONED-RED (#1993): it is EXPECTED to fail, so
# `pytest.ini`'s global `--reruns=2` could never rescue it — it could only multiply
# wall clock (measured: 52.97 s unmarked-single-attempt vs 161.38 s with 2 reruns)
# and put retry noise in the record. Same treatment, same reason, as the
# sanctioned-RED HITL specs in `tests/ui/chat/test_hitl_sensitive_action_authorization.py`.
@pytest.mark.flaky(reruns=0)
@allure.title("ELITEA-2416 — Chat error for a model whose credential is invalid (sanctioned RED: #1993)")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "settings/ai-configuration/ELITEA-2416_chat-throws-a-meaningful-error-when-the-assigned-llm-model-u.md",
    "onetest-ai Test Case link",
)
@allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1993", "Known defect #1993")
def test_chat_error_when_llm_model_uses_invalid_credential(page, credential_api, conversation_api):
    """A chat turn against a model whose credential cannot authenticate fails
    fast and visibly, and must not expose server internals (#1993)."""
    providers_page = AIProvidersPage(page)
    form = AiProviderFormPage(page)
    chat = ChatPage(page)
    page.on("dialog", lambda dialog: dialog.accept())

    stamp = int(time.time())
    credential_name = f"autotest_2416_cred_{stamp}"
    model_display_name = f"autotest_2416_model_{stamp}"
    model_name = f"autotest-2416-badcred-{stamp}"
    for name in (credential_name, model_display_name):
        assert len(name) <= MAX_DISPLAY_NAME_LENGTH, (
            f"Generated Display Name {name!r} is {len(name)} chars, over the field's maxLength "
            f"of {MAX_DISPLAY_NAME_LENGTH} — it would be silently truncated by the input"
        )

    credential_id = None
    model_id = None
    conversation_id = None

    # Entered BEFORE any navigation in this test: Playwright's "websocket" page
    # event fires only at connection-open time.
    with chat.capture_websocket_frames() as frames:
        try:
            with allure.step(f"Step 1 — Create the invalid {CREDENTIAL_TYPE} credential {credential_name!r}"):
                providers_page.navigate()
                expect(providers_page.page_title).to_have_text("AI Providers")
                providers_page.click_create()
                providers_page.click_type_card(CREDENTIAL_TYPE)
                form.wait_for_form()
                # Settle on a SCHEMA-ONLY field — the schema re-render wipes
                # anything typed before it lands (AiProviderFormPage docs).
                form.wait_for_schema_field(BASE_FIELD_KEY)

                # Verified writes: the schema re-render can wipe a write that
                # lands in the gap after wait_for_schema_field (page-object docs).
                form.set_display_name_verified(credential_name)
                form.set_schema_field_verified(BASE_FIELD_KEY, API_BASE)
                form.fill_secret_field(SECRET_FIELD_KEY, INVALID_API_KEY)
                expect(form.secret_native_input(SECRET_FIELD_KEY)).to_have_value(INVALID_API_KEY)
                expect(form.save_button).to_be_enabled()

                with page.expect_response(
                    _configurations_matcher, timeout=CREATE_RESPONSE_TIMEOUT
                ) as cred_info:
                    form.save_button.click()
                cred_response = cred_info.value

                assert cred_response.status == 200, (
                    f"Expected 200 from the credential-create POST, got {cred_response.status}"
                )
                cred_body = cred_response.json()
                credential_id = cred_body.get("id")
                assert credential_id, f"Expected a numeric id in the create response, got {cred_body!r}"
                assert cred_body.get("label") == credential_name, (
                    f"Expected created credential label {credential_name!r}, got {cred_body.get('label')!r}"
                )
                assert cred_body.get("elitea_title") == credential_name, (
                    f"Expected created credential elitea_title {credential_name!r}, "
                    f"got {cred_body.get('elitea_title')!r}"
                )
                form.wait_for_ai_providers_list()
                logger.info("Created credential id=%s name=%s", credential_id, credential_name)

            with allure.step(f"Step 2 — Create the LLM model {model_display_name!r} using that credential"):
                providers_page.click_create()
                providers_page.click_type_card(MODEL_TYPE)
                form.wait_for_form()
                form.wait_for_schema_field(NAME_FIELD_KEY)
                # The schema DEFAULTS landing is the last thing this form does
                # before it settles -- a real product signal, and the one that
                # bounds the re-render window that wipes early keystrokes.
                expect(form.field("context_window")).to_have_value(DEFAULT_CONTEXT_WINDOW)

                form.set_display_name_verified(model_display_name)
                # A unique model `name`: the chat option testid is
                # `model-selector-option-{name}`, so reusing a shared model's
                # name collides with its option (`_surface.md`).
                form.set_schema_field_verified(NAME_FIELD_KEY, model_name)

                # `Ai Credentials` is the last required field: Save is inert
                # until it is chosen. Asserting the BEFORE state is what makes
                # "the model uses THIS credential" true rather than assumed.
                expect(form.save_button).to_be_disabled()
                form.select_saved_private_credential(credential_name)
                expect(form.credential_select_combobox).to_have_text(credential_name)
                expect(form.save_button).to_be_enabled()

                # `Low Tier` / `High Tier` are deliberately left unticked and the
                # model is never made the project default — either would move
                # project-level configuration that every later spec reads.
                expect(form.field_checkbox("low_tier")).not_to_be_checked()
                expect(form.field_checkbox("high_tier")).not_to_be_checked()

            with allure.step("Step 3 — Save the LLM model"):
                with page.expect_response(
                    _configurations_matcher, timeout=CREATE_RESPONSE_TIMEOUT
                ) as model_info:
                    form.save_button.click()
                model_response = model_info.value

                assert model_response.status == 200, (
                    f"Expected 200 from the model-create POST, got {model_response.status}"
                )
                model_body = model_response.json()
                model_id = model_body.get("id")
                assert model_id, f"Expected a numeric id in the create response, got {model_body!r}"
                form.wait_for_ai_providers_list()
                expect(providers_page.card_for_model(model_display_name)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                logger.info("Created LLM model id=%s name=%s", model_id, model_display_name)

            with allure.step("Steps 4-5 (case steps 4-5) — Open a chat session on the new model"):
                chat.navigate_to_chat()
                chat.wait_for_input_ready(timeout=30_000)
                # Selected by rendered display label, not by the `name`-keyed
                # testid suffix (`_surface.md` § Chat-side handles).
                chat.select_llm_model_by_label(model_display_name, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.model_selector_name).to_have_text(model_display_name)

            with allure.step(f"Step 6 (case step 6) — Send {CHAT_MESSAGE!r}"):
                initial_count = chat.get_message_count()
                frames_before = len(frames)
                chat.send_message(CHAT_MESSAGE)
                # The turn was accepted: the user's own bubble renders the text.
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)
                assert CHAT_MESSAGE in chat.get_message_text_at(initial_count), (
                    f"The sent message should render as the user's bubble at index {initial_count}"
                )

            with allure.step("Step 7 (case step 7) — The chat does not hang or go blank"):
                # A POSITIVE, bounded statement: the backend's own error arrives
                # on the wire. This flow produces NO failed HTTP request and no
                # console error — the error exists only in the Socket.IO frames
                # (`.agents/testing.md`, the HITL root-cause entry), so console/
                # HTTP silence must never be read as "nothing went wrong".
                error_frame = _wait_for_error_frame(page, frames, frames_before)
                assert error_frame is not None, (
                    "No chat_message_sync frame carrying a non-empty meta.error arrived within "
                    f"{ERROR_FRAME_TIMEOUT_MS} ms — the turn hung or resolved silently. "
                    f"Events seen after send: "
                    f"{sorted({f.get('event') for f in frames[frames_before:]})}"
                )
                # Asserted on the FIELD, never on its text: the message is
                # backend-authored and will change when #1993 is fixed.
                assert error_frame["meta"]["error"], "meta.error should be non-empty on the failing turn"
                logger.info("Turn failed as expected; meta.error is set on chat_message_sync")

            with allure.step("Step 8 (case step 8) — An error is surfaced to the user"):
                # The assistant turn rendered something rather than a blank bubble.
                chat.wait_for_message_count(initial_count + 2, timeout=UI_ELEMENT_TIMEOUT)
                error_card = chat.messages_container.last
                expect(error_card).to_be_visible()
                rendered = (error_card.inner_text() or "").strip()
                assert rendered, "The assistant's error message rendered with no text at all (blank response)"
                logger.info("Chat rendered %d chars of error text", len(rendered))

            with allure.step("Step 9 (case step 9) — No raw stack trace or internal details are exposed"):
                # Known defect: #1993 — the chat renders the raw backend
                # exception (Python traceback, server file path, internal
                # exception class, LiteLLM table name, credential key hash),
                # while the SAME invalid credential is sanitised and masked two
                # screens away on the credential form's Test connection
                # (ELITEA-2415). Written as the CORRECT behaviour under
                # expect.soft so steps 1-8 keep reporting and this flips green
                # when the product fix ships.
                expect.soft(error_card).not_to_contain_text(INTERNAL_DETAIL_PATTERN)
                # Known defect: #1993 — the same leak, surfaced as a tool label.
                # A fix that only trims the card text would still expose the
                # trace behind this chip.
                expect.soft(chat.answer_tool_chip.filter(has_text=STACKTRACE_CHIP_TEXT)).to_have_count(0)

            match = CONVERSATION_URL_PATTERN.search(page.url)
            if match:
                conversation_id = int(match.group(1))
        finally:
            if conversation_id:
                try:
                    conversation_api.delete_conversation(conversation_id)
                    logger.info("Teardown: deleted conversation id=%s", conversation_id)
                except Exception:  # noqa: BLE001 — teardown must never mask the verdict
                    logger.exception("Teardown failed to delete conversation %s", conversation_id)
            # Model FIRST — it references the credential.
            for name, known_id in ((model_display_name, model_id), (credential_name, credential_id)):
                try:
                    _delete_configuration_by_name(credential_api, name, known_id)
                except Exception:  # noqa: BLE001 — teardown must never mask the verdict
                    logger.exception("Teardown failed to delete the configuration %r", name)
