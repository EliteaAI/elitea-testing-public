"""UI test -- personalization settings apply to NEW conversations only
(ELITEA-2384).

AFS: test-specs/settings-user-profile/
l3_personalization-applies-to-new-conversations-only_ELITEA-2384.md

A conversation snapshots the user's personalization (`meta.persona` and the
resolved `instructions`) **at creation time**. Changing the defaults afterwards
must reach only conversations created after the change; a pre-existing
conversation keeps the values it was born with.

The observable -- read this before the assertions
--------------------------------------------------
Case steps 4 and 6 have NO UI surface: there is no per-conversation personality
indicator anywhere in the front end (`meta.context_strategy` is the only
conversation meta the UI consumes), and judging the assistant's *tone* would be
nondeterministic LLM output requiring semantic judgment. The conversation
RECORD carries the snapshot, and the app fetches it on the real user path:

* ``POST .../elitea_core/conversations/prompt_lib/<project>`` -> 201, on sending
  the first message;
* ``GET .../elitea_core/conversation/prompt_lib/<project>/<id>`` -> 200, on
  opening a conversation.

So every UI action stays a real UI action and the assertion reads the product's
own response body. That is the response-as-oracle pattern
(`.agents/testing.md` § Fidelity policy), **not** a substitution: nothing is
fabricated, injected or seeded through a wrong interface.

The spec never waits on an LLM answer -- the conversation and its persona
snapshot exist as soon as the message is SENT (the 201 lands before any answer),
which keeps the documented LLM trigger-side flakiness out of this case.

Case-text drift (case-text stale, product correct -- clarifications on
EliteaAI/elitea-testing-public#1960, none filed as a defect):

* "Navigate to Personalization" -> the Default persona select is on
  ``/settings/ai-personality``;
* step 1 "open an existing chat conversation" -- no pre-existing conversation
  can be assumed (the account's list renders folders only), so the spec CREATES
  its own "previously existing" conversation under a first persona, which is
  also what makes step 4 falsifiable: we then know exactly what that
  conversation should still report;
* step 6's "uses the updated personality setting" is unfalsifiable as written;
  the record field ``meta.persona`` is the live contract.

MUTATES SHARED ACCOUNT STATE (`persona` + the per-persona
`personality_instructions` map) and creates 2 conversations, which are deleted
in cleanup via the conversation API.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - chat: drives the chat surface for the conversation half
    - p3: low priority (per AFS metadata: l3 -- case priority `medium`)
    - regression
"""

import logging
import re

import allure
import pytest
from pages.chat_page import ChatPage
from pages.settings_personalization_page import SettingsPersonalizationPage
from playwright.sync_api import Response, expect
from utils.blank_conversation import open_blank_composer
from utils.console_errors import collect_console_errors
from utils.personalization_autosave import (
    AUTOSAVE_TIMEOUT,
    best_effort,
    is_author_autosave,
    restore_persona,
    restore_user_instructions,
    unexpected_console_errors,
)

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.settings,
    pytest.mark.chat,
    pytest.mark.p3,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 30_000

#: Baseline A -- in force when the "previously existing" conversation is born.
BASELINE_PERSONA_VALUE = "quirky"
BASELINE_PERSONA_LABEL = "Quirky"

#: Case value B -- in force when the NEW conversation is born. It MUST differ
#: from the baseline, or step 6's assertion could pass by accident.
CASE_PERSONA_VALUE = "nerdy"
CASE_PERSONA_LABEL = "Nerdy"

#: Written into persona B's instructions slot: a SECOND, independent
#: discriminator alongside `meta.persona` (a bug that snapshots the persona
#: label but resolves instructions live would pass a persona-only check).
INSTRUCTIONS_MARKER = "Always respond in a concise manner. Focus on practical solutions."

SEED_MESSAGE = "Reply with the single word OK."

#: Plural path = conversation CREATE (POST); singular = conversation READ (GET).
#: Neither string is a substring of the other, so the two predicates cannot
#: match each other's request.
CONVERSATION_CREATE_PATH = "/elitea_core/conversations/prompt_lib/"
CONVERSATION_READ_PATH = "/elitea_core/conversation/prompt_lib/"


def _is_conversation_create(response: Response) -> bool:
    """The POST that creates a conversation (project id is dynamic -- match the path)."""
    return CONVERSATION_CREATE_PATH in response.url and response.request.method == "POST"


def _is_conversation_read(response: Response) -> bool:
    """The GET that loads one conversation."""
    return CONVERSATION_READ_PATH in response.url and response.request.method == "GET"


def _personalization_of(body: dict) -> tuple[str | None, str]:
    """(`meta.persona`, `instructions`) as the conversation record reports them."""
    meta = body.get("meta") or {}
    return meta.get("persona"), body.get("instructions") or ""


def _delete_conversations(conversation_api, conversation_ids) -> None:
    """Delete the conversations this spec created, best-effort on BOTH paths.

    Deliberately best-effort even on the success path: a conversation that
    outlives the run only adds to the shared-account pollution class (#1082) --
    it does not corrupt the account state a later spec READS, the way a skipped
    persona/instructions restore does. Those restores are strict on the success
    path (see the ``else`` branch of the test body).
    """
    for conversation_id in conversation_ids:
        if not conversation_id:
            continue
        try:
            conversation_api.delete_conversation(int(conversation_id))
            logger.info("Cleanup: deleted conversation %s", conversation_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cleanup: failed to delete conversation %s: %s", conversation_id, exc)


class TestPersonalizationAppliesToNewConversationsOnly:
    """ELITEA-2384 -- personalization reaches new conversations only."""

    @staticmethod
    def _select_persona(page, personalization: SettingsPersonalizationPage, value: str, label: str) -> None:
        """Set the Default persona, asserting its own autosave PUT.

        No-op when it already holds the wanted value: `useFormikAutoSaveOnBlur`
        legitimately fires no request when Formik is not dirty, so asserting a
        PUT there would be a false red.
        """
        personalization.wait_for_persona_select()
        if personalization.get_persona() != label:
            with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as put_info:
                personalization.select_persona(value)
            assert put_info.value.status == 200, (
                f"Setting the Default persona to {label} should autosave via PUT -> 200, "
                f"got {put_info.value.status}"
            )
        expect(personalization.persona_select_combobox).to_have_text(label)

    @staticmethod
    def _create_conversation(page, chat: ChatPage) -> tuple[str, dict]:
        """Create a conversation by sending the seed message; return (id, body).

        No AI answer is awaited -- the 201 (and its persona snapshot) lands
        before any answer arrives.
        """
        chat.navigate_to_chat()
        chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        open_blank_composer(chat, timeout=NAVIGATION_TIMEOUT)

        with page.expect_response(_is_conversation_create, timeout=NAVIGATION_TIMEOUT) as created:
            # Enter, not the send button: an overlay intercepts pointer events
            # on `chat-send-button` in the fresh-chat view.
            chat.send_message(SEED_MESSAGE, use_enter=True)
        response = created.value
        assert response.status == 201, (
            f"Sending the first message should create a conversation (201), got "
            f"{response.status} from {response.url}"
        )
        body = response.json()

        page.wait_for_url(
            lambda url: re.search(r"/chat/\d+", url) is not None, timeout=NAVIGATION_TIMEOUT
        )
        match = re.search(r"/chat/(\d+)", page.url)
        assert match, f"Sending a message should open the new conversation; URL was {page.url!r}"
        conversation_id = match.group(1)
        assert str(body.get("id")) == conversation_id, (
            f"The created conversation's id ({body.get('id')!r}) should be the one the app "
            f"navigated to ({conversation_id!r})"
        )
        logger.info("Created conversation %s", conversation_id)
        return conversation_id, body

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/user-profile/ELITEA-2384_personalization-settings-only-apply-to-new-conversations-exi.md",
        "onetest-ai Test Case link",
    )
    def test_personalization_applies_to_new_conversations_only(self, page, conversation_api):
        """A conversation keeps the personalization it was created with; a later
        default change reaches only conversations created after it."""
        personalization = SettingsPersonalizationPage(page)
        chat = ChatPage(page)
        console_errors = collect_console_errors(page)
        original_persona_label = None
        original_instructions = None
        existing_conversation_id = None
        new_conversation_id = None

        try:
            with allure.step(
                f"Setup - Baseline A: record the account's persona and "
                f"{CASE_PERSONA_LABEL}'s instructions slot, then set the "
                f"Default persona to {BASELINE_PERSONA_LABEL}"
            ):
                personalization.open_settings_tab("ai-personality")
                personalization.wait_for_persona_select()
                original_persona_label = personalization.get_persona()
                assert original_persona_label, "Could not read the current Default persona"

                # Persona B's slot is read under persona B -- the field renders
                # only the currently selected persona's slot.
                self._select_persona(page, personalization, CASE_PERSONA_VALUE, CASE_PERSONA_LABEL)
                original_instructions = personalization.get_user_instructions()
                logger.info(
                    "Account originals: persona=%r %s-instructions=%r",
                    original_persona_label,
                    CASE_PERSONA_LABEL,
                    original_instructions,
                )

                self._select_persona(
                    page, personalization, BASELINE_PERSONA_VALUE, BASELINE_PERSONA_LABEL
                )

            with allure.step(
                "Step 1 - Create the 'previously existing' conversation and "
                "record what it was born with"
            ):
                existing_conversation_id, existing_body = self._create_conversation(page, chat)
                existing_persona, existing_instructions = _personalization_of(existing_body)
                assert existing_persona == BASELINE_PERSONA_VALUE, (
                    f"The conversation created under {BASELINE_PERSONA_LABEL} should record "
                    f"meta.persona={BASELINE_PERSONA_VALUE!r}, got {existing_persona!r}"
                )
                assert existing_instructions == "", (
                    "The baseline conversation should carry no resolved instructions "
                    f"(the {BASELINE_PERSONA_LABEL} slot is empty), got "
                    f"{existing_instructions!r}"
                )

            with allure.step(
                f"Step 2 - Change the Default Personality to {CASE_PERSONA_LABEL} "
                "and give that persona a distinctive instructions text"
            ):
                personalization.open_settings_tab("ai-personality")
                self._select_persona(page, personalization, CASE_PERSONA_VALUE, CASE_PERSONA_LABEL)

                personalization.fill_user_instructions(INSTRUCTIONS_MARKER)
                with page.expect_response(is_author_autosave, timeout=AUTOSAVE_TIMEOUT) as saved:
                    # Blur is this control's save trigger; the accordion header is
                    # deliberately NOT the "outside" target (it collapses the section).
                    personalization.click_neutral_content_area()
                assert saved.value.status == 200, (
                    f"Saving the user instructions should autosave via PUT -> 200, got "
                    f"{saved.value.status}"
                )
                expect(personalization.user_instructions_textarea).to_have_value(
                    INSTRUCTIONS_MARKER
                )

            with allure.step("Step 3 - Return to the existing conversation"):
                with page.expect_response(
                    _is_conversation_read, timeout=NAVIGATION_TIMEOUT
                ) as reopened:
                    chat.open_conversation(existing_conversation_id, timeout=NAVIGATION_TIMEOUT)
                assert reopened.value.status == 200, (
                    f"Opening conversation {existing_conversation_id} should return 200, got "
                    f"{reopened.value.status} from {reopened.value.url}"
                )
                reopened_body = reopened.value.json()

            with allure.step(
                "Step 4 - The existing conversation's personalization has NOT changed"
            ):
                reopened_persona, reopened_instructions = _personalization_of(reopened_body)
                assert reopened_persona == BASELINE_PERSONA_VALUE, (
                    f"The pre-existing conversation must keep meta.persona="
                    f"{BASELINE_PERSONA_VALUE!r} (its creation-time value), NOT the new global "
                    f"{CASE_PERSONA_VALUE!r}; got {reopened_persona!r}"
                )
                assert reopened_instructions == "", (
                    "The new persona's instructions must not leak into the pre-existing "
                    f"conversation; got {reopened_instructions!r}"
                )

            with allure.step("Step 5 - Create a new conversation"):
                new_conversation_id, new_body = self._create_conversation(page, chat)
                assert new_conversation_id != existing_conversation_id, (
                    "Step 5 should create a NEW conversation, but landed back on "
                    f"{existing_conversation_id} - the comparison would be reading one "
                    "record twice"
                )

            with allure.step(
                f"Step 6 - The new conversation uses the updated setting "
                f"({CASE_PERSONA_LABEL} + its instructions)"
            ):
                new_persona, new_instructions = _personalization_of(new_body)
                assert new_persona == CASE_PERSONA_VALUE, (
                    f"A conversation created after the change should record meta.persona="
                    f"{CASE_PERSONA_VALUE!r}, got {new_persona!r}"
                )
                assert new_instructions == INSTRUCTIONS_MARKER, (
                    "The new conversation should resolve its instructions from the "
                    f"{CASE_PERSONA_LABEL} slot, got {new_instructions!r}"
                )

            with allure.step("Step 7 - No unexpected console errors were logged"):
                # `/settings/ai-personality` always logs the #1771
                # `disableUnderline` warning; nothing else is tolerated.
                # Known defect: #1771.
                assert not unexpected_console_errors(console_errors), (
                    f"unexpected console errors: {unexpected_console_errors(console_errors)}"
                )

        except BaseException:
            # Cleanup (not case steps -- no allure.step). The body already
            # failed, so every restore is best-effort here: a teardown exception
            # raised on this path would REPLACE the real failure in the report.
            _delete_conversations(
                conversation_api, (existing_conversation_id, new_conversation_id)
            )
            if original_instructions is not None:
                best_effort(
                    lambda: restore_user_instructions(
                        personalization, CASE_PERSONA_LABEL, original_instructions
                    ),
                    f"restore {CASE_PERSONA_LABEL}'s user instructions",
                )
            if original_persona_label:
                best_effort(
                    lambda: restore_persona(personalization, original_persona_label),
                    f"restore the original persona ({original_persona_label})",
                )
            raise
        else:
            # Success path: the restores are STRICT. A restore that silently
            # fails here leaks the changed persona + instructions onto the
            # shared `${TEST_USER}` record for every other spec that reads them,
            # and a green run would report nothing. There is no in-flight
            # failure left to mask, so the restore is allowed to be the failure.
            _delete_conversations(
                conversation_api, (existing_conversation_id, new_conversation_id)
            )
            if original_instructions is not None:
                restore_user_instructions(
                    personalization, CASE_PERSONA_LABEL, original_instructions
                )
            if original_persona_label:
                restore_persona(personalization, original_persona_label)
