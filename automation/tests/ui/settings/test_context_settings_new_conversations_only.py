"""UI test — Context Management settings apply to NEW conversations only (ELITEA-2390).

A conversation snapshots the user's Settings -> Memory context-management
defaults **at creation time**. Changing those defaults afterwards must affect
only conversations created after the change; an existing conversation keeps
the values it was born with.

AFS: test-specs/settings-user-profile/
l1_context-settings-apply-to-new-conversations-only_ELITEA-2390.md

Shape of the run (the AFS explains why the first two steps exist):
    baseline A (32000 / 10) -> create conversation #1 -> read ITS modal
    -> case values (32000 / 3) -> create conversation #2 -> read ITS modal
    -> reopen conversation #1 -> its Preserve Recent Messages must STILL be 10

The case says "open a previously existing conversation", but the account has
none (verified live: the conversation list renders folders only), and
"unchanged" is unfalsifiable without a recorded before-value — so the spec
creates its own baseline conversation under a deliberately DIFFERENT Preserve
Recent Messages (10 vs the case's 3). That difference is what makes the final
assertion a real discriminator rather than a coincidence.

Known case-text vs live-product divergence (not weakened — the live contract
is asserted; EliteaAI/elitea-testing-public#1238): the case says
"Settings -> Personalization -> DEFAULT CONTEXT MANAGEMENT";
`/settings/personalization` 404s and the live route is Settings -> Memory.

No substitution of the system under test: every asserted value is read from
the product's own UI (the per-conversation "Edit context settings" modal),
after the product itself produced it. The modal is opened read-only — its
Save button is never clicked, because saving would rewrite the very value the
final step observes.

Deliberately does NOT wait for an AI answer: the conversation and its context
snapshot exist as soon as the message is SENT (confirmed live — the
`/chat/<id>` route and a 200 `context_analytics` carrying the inherited
`max_tokens` both land before any answer). That keeps the documented
LLM trigger-side flakiness out of this case entirely.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - chat: drives the chat surface for the per-conversation half
    - p1: high priority (case priority `high` -> l1 -> p1)
    - regression
"""

import logging
import re
import time

import allure
import pytest
from components.mui import Dialog
from pages.chat_page import ChatPage
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import Response, expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.settings,
    pytest.mark.chat,
    pytest.mark.p1,
    pytest.mark.regression,
]

# ---------------------------------------------------------------------------
# Timeout / autosave constants
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000     # Fields, toggles, section container
NAVIGATION_TIMEOUT = 30_000     # SPA route changes / conversation creation
AUTOSAVE_TIMEOUT = 15_000       # Autosave PUT round-trip (per-keystroke typing)
CONTEXT_PANEL_TIMEOUT = 30_000  # Context Budget panel (waits on context_analytics)
AUTOSAVE_PUT_PATH = "/api/v2/social/author/"

# AFS § Test Data — the two phases. The Preserve Recent Messages values MUST
# differ: `10` is what conversation #1 is born with, `3` is the case's value
# applied afterwards.
MAX_CONTEXT_TOKENS = 32000
BASELINE_PRESERVE_RECENT = 10
CASE_PRESERVE_RECENT = 3

SEED_MESSAGE = "Reply with the single word OK."


def _is_autosave_put_response(response: Response) -> bool:
    """True for the Settings -> Memory autosave PUT."""
    return response.request.method == "PUT" and AUTOSAVE_PUT_PATH in response.url


BLANK_URL_PATTERN = re.compile(r"/chat/?(?:\?.*)?$")
BLANK_SETTLE_MS = 1500      # The last-viewed-conversation restore's own timing window
BLANK_POLL_INTERVAL_S = 0.25


def _poll_blank_state_holds(
    chat: ChatPage,
    settle_ms: int = BLANK_SETTLE_MS,
    poll_interval_s: float = BLANK_POLL_INTERVAL_S,
) -> tuple[bool, str]:
    """Poll message-count + URL at short intervals across *settle_ms*,
    instead of a fixed-latency sleep-then-recheck-once.

    Duplicated with attribution from ``_poll_blank_state_holds()`` in
    ``tests/ui/chat/test_team_users_mention_and_remove_participants.py``
    (wave-11), which in turn copied it from ``test_invite_users_add_cancel_close.py``
    (ELITEA-2175/2176, wave-10). Per-file duplication is this suite's own
    established pattern for sharing the ``_open_blank_*`` helper family across
    chat-driving test files — no shared module or conftest fixture exists for
    it, and creating one would rewire three merged specs (Hard Rule 3,
    additive-only on shared-caller files).

    Why a *poll* and not a sleep-then-check-once (the shape this spec shipped
    in PR #1962 and which review correctly blocked): a single sample taken at
    the END of the window only ever observes the window's final state. The
    blank state is required to **hold** for the whole window, so any restore
    that lands inside it and is then superseded is invisible to one late
    sample — which is precisely the race
    ``_open_genuinely_blank_conversation()`` was written to close. Polling also
    exits the instant either signal flips, turning a definitive failure into an
    immediate retry instead of a full window burned blind.

    Note ``time.sleep`` is safe as the poll interval here (unlike the
    WebSocket-frame case in ``.agents/testing.md``): every iteration calls
    ``chat.get_message_count()``, a Playwright call, so the sync dispatcher is
    pumped on each pass and no event backlog can build up.

    Returns ``(settled, reason)`` — ``settled`` is False (with a reason) the
    moment either signal flips during the window, True only if both signals
    held blank for the entire window.
    """
    deadline = time.monotonic() + settle_ms / 1000.0
    while time.monotonic() < deadline:
        time.sleep(poll_interval_s)
        count = chat.get_message_count()
        url = chat.page.url
        if count != 0 or not BLANK_URL_PATTERN.search(url):
            return False, f"blank state reverted mid-settle (url={url!r}, message_count={count})"
    return True, ""


class TestContextSettingsApplyToNewConversationsOnly:
    """Settings changes reach new conversations; existing ones keep their own."""

    # ------------------------------------------------------------------
    # Suite-local helpers (single caller each — kept beside the test per the
    # project's suite-local-helper convention, not promoted to a page object)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_settings(page, profile: UserProfileSettingsPage, preserve_recent: int) -> None:
        """Set Max Context Tokens + Preserve Recent Messages, asserting each autosave.

        Blur is the page's only save trigger (no Save button exists here), so
        the PUT status is asserted rather than merely awaited — **except when
        the field already holds the wanted value**. ``useFormikAutoSaveOnBlur``
        returns early when Formik is not ``dirty``, so re-typing an unchanged
        value legitimately fires NO request; asserting a PUT there would be a
        false red. Each field is therefore written only when it needs to
        change, and every write that does happen is asserted.
        """
        if profile.get_max_context_tokens() != MAX_CONTEXT_TOKENS:
            with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                profile.type_max_context_tokens_raw(str(MAX_CONTEXT_TOKENS))
            assert put_info.value.status == 200, (
                f"Setting Max Context Tokens to {MAX_CONTEXT_TOKENS} should autosave via "
                f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
            )
        expect(profile.max_context_tokens_input).to_have_value(
            str(MAX_CONTEXT_TOKENS), timeout=UI_ELEMENT_TIMEOUT
        )

        if profile.get_preserve_recent_messages() != preserve_recent:
            with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                profile.set_preserve_recent_messages(preserve_recent)
            assert put_info.value.status == 200, (
                f"Setting Preserve Recent Messages to {preserve_recent} should autosave via "
                f"PUT {AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
            )
        expect(profile.preserve_recent_messages_input).to_have_value(
            str(preserve_recent), timeout=UI_ELEMENT_TIMEOUT
        )

    @staticmethod
    def _open_blank_composer(chat: ChatPage, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Reach a genuinely blank composer (URL ``/chat`` with no id, 0 messages).

        Duplicated-with-attribution from ``_open_genuinely_blank_conversation()``
        in ``tests/ui/chat/test_team_users_mention_and_remove_participants.py``
        (wave-10/11), per the same suite-local convention. It asserts less than
        the ancestor about *participant* state — this case needs only "am I on a
        blank composer" — but it carries the ancestor's settle machinery
        verbatim (:func:`_poll_blank_state_holds`), because that machinery is
        what closes the race, not an optional strictness knob. An earlier
        revision of this helper substituted a fixed
        ``page.wait_for_timeout(1500)`` + one recheck for the poll; that is both
        a ``.agents/conventions.md`` § Hard don'ts violation and a silent
        regression of the ancestor, and review blocked it (PR #1962).

        Why it is required rather than defensive: the SPA restores the
        last-viewed conversation (documented on
        ``ChatPage.navigate_to_chat()``), so a bare ``navigate_to_chat()`` +
        ``send_message()`` appends to an EXISTING conversation instead of
        creating one — observed on this spec's first run, where step 4 landed
        back on the conversation created moments earlier. Clicking +Chat and
        then verifying BOTH the id-less URL and a zero message count is what
        makes "create a new conversation" a fact.
        """
        last_reason = "unknown"
        for attempt in range(3):
            chat.click_create_conversation(timeout=timeout)
            try:
                chat.new_conversation_greeting.wait_for(state="visible", timeout=5000)
            except Exception:  # noqa: BLE001 — retried below, reason recorded
                last_reason = "new-conversation greeting never appeared"
                logger.warning("Attempt %d: %s — retrying", attempt + 1, last_reason)
                continue
            if chat.get_message_count() != 0:
                last_reason = "blank greeting shown but the conversation has message history"
                logger.warning("Attempt %d: %s — retrying", attempt + 1, last_reason)
                continue
            # Settle window for the DELAYED last-viewed-conversation restore:
            # the greeting can render before the restore snaps the route back.
            # Polled, not slept — see _poll_blank_state_holds().
            settled, reason = _poll_blank_state_holds(chat)
            if not settled:
                last_reason = reason
                logger.warning("Attempt %d: %s — retrying", attempt + 1, last_reason)
                continue
            return
        raise AssertionError(
            f"Could not reach a blank composer after 3 +Chat attempts — last reason: {last_reason}"
        )

    @classmethod
    def _create_conversation(cls, page, chat: ChatPage) -> str:
        """Create a NEW conversation by sending the seed message; return its id.

        The conversation is created by SENDING — no AI answer is awaited (see
        the module docstring).
        """
        chat.navigate_to_chat()
        chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        cls._open_blank_composer(chat)
        chat.send_message(SEED_MESSAGE, use_enter=True)
        page.wait_for_url(
            lambda url: re.search(r"/chat/\d+", url) is not None,
            timeout=NAVIGATION_TIMEOUT,
        )
        match = re.search(r"/chat/(\d+)", page.url)
        assert match, f"Sending a message should create a conversation; URL was {page.url!r}"
        conversation_id = match.group(1)
        logger.info("Created conversation %s", conversation_id)
        return conversation_id

    @staticmethod
    def _read_conversation_context_settings(page, chat: ChatPage) -> dict:
        """Open the conversation's 'Edit context settings' modal and read it.

        The Context Budget panel is UNMOUNTED while the participants panel is
        collapsed (it starts collapsed on every conversation load), so the
        panel is expanded first — otherwise a missing panel is
        indistinguishable from a product failure. Closes the dialog with
        Escape; the Save button is never clicked (read-only by design).
        """
        chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
        chat.context_budget_panel.wait_for(state="visible", timeout=CONTEXT_PANEL_TIMEOUT)

        chat.edit_context_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        chat.edit_context_settings()
        Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)

        settings = {
            "management_enabled": chat.is_context_modal_management_enabled(),
            "max_tokens": chat.context_modal_max_tokens_input.input_value(),
            "preserve_recent": chat.context_modal_preserve_recent_input.input_value(),
        }
        logger.info("Conversation context settings read from modal: %s", settings)

        chat.close_context_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
        return settings

    # ------------------------------------------------------------------
    # The case
    # ------------------------------------------------------------------

    def test_context_settings_apply_to_new_conversations_only(self, page, conversation_api):
        """A settings change reaches new conversations only; existing ones keep theirs."""
        profile = UserProfileSettingsPage(page)
        chat = ChatPage(page)
        baseline_conversation_id = None
        new_conversation_id = None

        with allure.step(
            "Setup — Navigate to Settings -> Memory, ensure Context Management "
            "is ON, and record the account's current values for teardown"
        ):
            profile.navigate_to_profile()
            expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            if not profile.is_context_management_enabled():
                with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_context_management()
                assert put_info.value.status == 200, (
                    f"Turning Context Management ON should autosave via PUT "
                    f"{AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                )
            original_max_tokens = profile.get_max_context_tokens()
            original_preserve_recent = profile.get_preserve_recent_messages()
            logger.info(
                "Account originals: max_context_tokens=%d, preserve_recent_messages=%d",
                original_max_tokens,
                original_preserve_recent,
            )

        try:
            with allure.step(
                f"Setup — Baseline A: set Max Context Tokens {MAX_CONTEXT_TOKENS} "
                f"and Preserve Recent Messages {BASELINE_PRESERVE_RECENT} (the "
                f"values the 'previously existing' conversation will be born with)"
            ):
                self._apply_settings(page, profile, BASELINE_PRESERVE_RECENT)

            with allure.step(
                "Setup — Create the 'previously existing' conversation and read "
                "its context settings (the before-value step 7 compares against)"
            ):
                baseline_conversation_id = self._create_conversation(page, chat)
                baseline_settings = self._read_conversation_context_settings(page, chat)
                assert baseline_settings["management_enabled"], (
                    "The baseline conversation should have context management active"
                )
                assert baseline_settings["max_tokens"] == str(MAX_CONTEXT_TOKENS), (
                    f"The baseline conversation should inherit Max Context Tokens "
                    f"{MAX_CONTEXT_TOKENS}, got {baseline_settings['max_tokens']!r}"
                )
                assert baseline_settings["preserve_recent"] == str(BASELINE_PRESERVE_RECENT), (
                    f"The baseline conversation should inherit Preserve Recent Messages "
                    f"{BASELINE_PRESERVE_RECENT}, got {baseline_settings['preserve_recent']!r}"
                )

            with allure.step(
                f"Step 1-2 — Back on Settings -> Memory: context management "
                f"enabled, Max Context Tokens {MAX_CONTEXT_TOKENS}, Preserve "
                f"Recent Messages {CASE_PRESERVE_RECENT}"
            ):
                profile.navigate_to_profile()
                expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert profile.is_context_management_enabled(), (
                    "Context Management should still read ON before applying the case values"
                )
                self._apply_settings(page, profile, CASE_PRESERVE_RECENT)

            with allure.step(
                "Step 3 — Navigate away and back; the values were auto-saved"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                profile.navigate_to_profile()
                expect(profile.max_context_tokens_input).to_have_value(
                    str(MAX_CONTEXT_TOKENS), timeout=UI_ELEMENT_TIMEOUT
                )
                expect(profile.preserve_recent_messages_input).to_have_value(
                    str(CASE_PRESERVE_RECENT), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 4 — Create a new conversation"):
                new_conversation_id = self._create_conversation(page, chat)
                assert new_conversation_id != baseline_conversation_id, (
                    f"Step 4 should create a NEW conversation, but landed back on "
                    f"{baseline_conversation_id}"
                )

            with allure.step(
                f"Step 5 — The new conversation has context management active "
                f"with the configured values ({MAX_CONTEXT_TOKENS} / "
                f"{CASE_PRESERVE_RECENT})"
            ):
                new_settings = self._read_conversation_context_settings(page, chat)
                assert new_settings["management_enabled"], (
                    "The new conversation should have context management active"
                )
                assert new_settings["max_tokens"] == str(MAX_CONTEXT_TOKENS), (
                    f"The new conversation should show Max Context Tokens "
                    f"{MAX_CONTEXT_TOKENS}, got {new_settings['max_tokens']!r}"
                )
                assert new_settings["preserve_recent"] == str(CASE_PRESERVE_RECENT), (
                    f"The new conversation should show the newly configured Preserve "
                    f"Recent Messages {CASE_PRESERVE_RECENT}, got "
                    f"{new_settings['preserve_recent']!r}"
                )

            with allure.step("Step 6 — Open the previously existing conversation"):
                # open_conversation(), not navigate_to_chat(): the latter
                # short-circuits while already on a /chat route and cannot
                # switch conversations (see its docstring).
                chat.open_conversation(baseline_conversation_id, timeout=NAVIGATION_TIMEOUT)
                assert f"/chat/{baseline_conversation_id}" in page.url, (
                    f"Should be on the baseline conversation {baseline_conversation_id}, "
                    f"URL is {page.url!r}"
                )

            with allure.step(
                f"Step 7 — Its context management settings remain unchanged: "
                f"Preserve Recent Messages is still {BASELINE_PRESERVE_RECENT} "
                f"(its creation-time value), NOT the new global "
                f"{CASE_PRESERVE_RECENT}"
            ):
                reopened_settings = self._read_conversation_context_settings(page, chat)
                assert reopened_settings == baseline_settings, (
                    f"The pre-existing conversation's context settings must be unchanged "
                    f"by the later settings edit: expected {baseline_settings}, got "
                    f"{reopened_settings}"
                )
                assert reopened_settings["preserve_recent"] != str(CASE_PRESERVE_RECENT), (
                    f"The pre-existing conversation must NOT pick up the new global "
                    f"Preserve Recent Messages ({CASE_PRESERVE_RECENT}) — settings apply "
                    f"to new conversations only"
                )
        finally:
            # Cleanup (not case steps — no allure.step): delete both
            # conversations and restore the shared ${TEST_USER} account's
            # settings. Best-effort so a cleanup failure cannot mask the real
            # assertion failure, but each failure is logged loudly.
            for conversation_id in (baseline_conversation_id, new_conversation_id):
                if conversation_id:
                    try:
                        conversation_api.delete_conversation(int(conversation_id))
                        logger.info("Cleanup: deleted conversation %s", conversation_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Cleanup: failed to delete conversation %s: %s", conversation_id, exc
                        )
            try:
                profile.navigate_to_profile()
                profile.type_max_context_tokens_raw(str(original_max_tokens))
                profile.set_preserve_recent_messages(original_preserve_recent)
                profile.wait_for_autosave(timeout=AUTOSAVE_TIMEOUT)
                logger.info(
                    "Cleanup: restored max_context_tokens=%d, preserve_recent_messages=%d",
                    original_max_tokens,
                    original_preserve_recent,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Cleanup: failed to restore profile context settings: %s", exc)
