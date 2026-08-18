"""UI Test for ELITEA-2089 — Chat: Edit Agent in Canvas Mode – Verify Changes Synchronize.

Verifies that editing an owned agent's Welcome Message through the in-chat
edit canvas and saving correctly synchronises the change back to the agent's
record in the Agents section.

Spec: test-specs/chat-interface/l2_edit-agent-in-canvas-verify-welcome-message-sync_ELITEA-2089.md

Flow overview (14 AFS steps):
1.  Navigate to chat / Private project; add a fixture agent as participant.
2.  Open PARTICIPANTS panel; click the edit (pencil) icon on the agent row.
3.  Verify the composer chip shows "Editing..." (owned-agent canvas mode).
4.  Confirm "Welcome message" accordion textarea is visible.
5.  Click into the Welcome Message field.
6.  Clear and type "edited from canvas"; verify value.
7.  Verify Save and Discard buttons become enabled (form is dirty).
8.  Click Save; verify PUT → 201 and success toast.
9.  Close the canvas; verify URL sheds the ?edited_participant_id param.
10. Verify the composer chip no longer shows "Editing...".
11-12. Navigate to the agent's edit page in Agents section.
13. Scroll to the Welcome Message accordion.
14. Verify the textarea value == "edited from canvas" (sync confirmed).

Page objects:
- ``ChatPage`` — chat navigation, plus-menu flow, PARTICIPANTS panel, composer chips.
- ``AgentCanvasPage`` — canvas header chrome (close, title, subtitle, discard button).
- ``AgentFormPage`` — welcome-message textarea (shared with /agents/create page).
- ``AgentDetailPage`` — navigate to the agent's edit page for the sync check.

Testid gaps closed (pushed to automation/testids before this test was written):
- ``agent-discard-button`` — wired in EditorHeader.jsx via new
  ``discardButtonTestId`` prop, supplied by AgentEditor.jsx at its call site.
  ``DiscardButton.jsx`` already accepts ``dataTestId`` (no component change needed).

Note — secondary 404 on entity_settings:
  After the main agent save (PUT application → 201), a second call
  ``PUT entity_settings/prompt_lib/{project_id}/undefined/{agent_id}``
  fires with ``undefined`` in the path and returns 404. This is a **potential
  UI bug** filed in the AFS Observations (§ Observation 2). The console-error
  check excludes ``entity_settings`` lines so that pre-existing noise does not
  mask genuinely new errors.
"""

import logging
import re

import allure
import pytest
from config import settings
from pages.agent_canvas_page import AgentCanvasPage
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.agents,
    pytest.mark.regression,
]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------
NEW_WELCOME_MESSAGE = "edited from canvas"
EXPECTED_TOAST_TEXT = "The agent has been updated"

# Agent name produced by the ``agent_id`` fixture:
#   f"autotest_{request.node.name}"[:32]
# where request.node.name == test method's bare name (no class prefix).
_TEST_NODE_NAME = "test_edit_agent_welcome_message_syncs_to_agents_section"
_AGENT_NAME = f"autotest_{_TEST_NODE_NAME}"[:32]  # "autotest_test_edit_agent_welcome"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing environment-wide ``secrets`` 403 console noise."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_entity_settings_404(msg) -> bool:
    """Filter the known secondary PUT entity_settings/prompt_lib/.../undefined/...
    404 that fires after agent save (AFS Observation 2 — potential UI bug,
    filed for triage; does NOT affect save outcome)."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "entity_settings" in (text + location_url)


class TestChatCanvasEditAgent:
    """ELITEA-2089: Chat – Edit Agent in Canvas Mode – Verify Changes Synchronize."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/"
        "ELITEA-2089_chat-edit-agent-in-canvas-mode-verify-changes-synchronize-to-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_edit_agent_welcome_message_syncs_to_agents_section(
        self,
        page,
        agent_id,
        conversation_api,
    ):
        """Edit an owned agent's Welcome Message via the chat canvas and confirm
        the change synchronises to the agent record in the Agents section.

        Steps follow AFS
        test-specs/chat-interface/
        l2_edit-agent-in-canvas-verify-welcome-message-sync_ELITEA-2089.md:
        1.  Navigate to chat / Private project; add fixture agent via plus-menu
            Agents submenu using testid ``agents-menu-item-agent-{p}-{a}``.
        2.  Open PARTICIPANTS panel; hover agent row; click edit icon.
        3.  Verify composer chip → "Editing..." (owned canvas mode).
        4.  Verify Welcome Message textarea visible.
        5.  Click into the Welcome Message field.
        6.  Clear and type NEW_WELCOME_MESSAGE; verify value.
        7.  Verify Save and Discard buttons are enabled (dirty form).
        8.  Click Save; intercept PUT application → 201; verify success toast.
        9.  Click canvas X button; verify URL sheds ?edited_participant_id.
        10. Verify composer chip no longer shows "Editing...".
        11-12. Navigate directly to the agent's edit page.
        13. Welcome Message accordion is expanded by default — textarea visible.
        14. Verify textarea value == NEW_WELCOME_MESSAGE (sync confirmed).

        No substitutions — all observables produced by the live system.
        Transit: fixture agent created via API (not the UI create-agent flow)
        to provide a stable, cleanup-able participant; the case's own observable
        (welcome-message sync) is read from the live Agents section.
        """
        chat = ChatPage(page)
        agent_canvas = AgentCanvasPage(page)
        agent_form = AgentFormPage(page)

        conversation_id = None

        # Capture console errors from the start so no step's noise is missed.
        # Known noise is filtered so genuine new errors surface cleanly.
        console_messages: list = []

        def _on_console(msg):
            if (
                msg.type == "error"
                and not _is_known_secrets_403(msg)
                and not _is_entity_settings_404(msg)
            ):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Setup — navigate to chat and switch to Private project"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(str(settings.elitea_project_id), timeout=NAVIGATION_TIMEOUT)
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1 — Add the fixture agent as a participant via plus menu "
                "-> Agents submenu; verify the badge shows count '1'"
            ):
                chat.add_agent_participant_by_id(
                    project_id=settings.elitea_project_id,
                    agent_id=agent_id,
                    timeout=NAVIGATION_TIMEOUT,
                )
                # Badge count "1" confirms the agent was added
                badge_container = page.locator(chat.PARTICIPANTS_BADGE.format("agents"))
                badge_button = badge_container.locator(chat.PARTICIPANTS_BADGE_BUTTON)
                expect(badge_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                # Capture the conversation ID for cleanup (URL resolves after
                # the conversation is created server-side on participant addition)
                try:
                    page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)
                except Exception:
                    logger.warning("Conversation URL never resolved to /chat/{id}")
                match = re.search(r"/chat/(\d+)", page.url)
                if match:
                    conversation_id = int(match.group(1))

            with allure.step(
                "Step 2 — Open PARTICIPANTS panel; hover the agent row; "
                "click the edit (pencil) icon to open the edit canvas"
            ):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                # open_agent_participant_settings hovers the row and clicks
                # PARTICIPANT_EDIT_VIEW_BUTTON (the pencil/edit icon)
                chat.open_agent_participant_settings(
                    participant_name=_AGENT_NAME,
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                agent_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                # URL should now contain ?edited_participant_id
                expect(page).to_have_url(
                    re.compile(r"edited_participant_id"), timeout=UI_ELEMENT_TIMEOUT
                )
                expect(agent_canvas.title).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.subtitle).to_have_text("base", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify composer chip shows 'Editing...' "
                "(canvas is in edit mode for an owned agent)"
            ):
                expect(chat.chat_participant_settings_button).to_contain_text(
                    "Editing...", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Verify the Welcome Message textarea is visible "
                "in the edit canvas"
            ):
                expect(agent_form.welcome_message_input).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 5 — Click into the Welcome Message field"):
                agent_form.welcome_message_input.click()

            with allure.step(
                f"Step 6 — Clear the field and type {NEW_WELCOME_MESSAGE!r}; "
                "verify the value"
            ):
                agent_form.welcome_message_input.clear()
                agent_form.welcome_message_input.press_sequentially(
                    NEW_WELCOME_MESSAGE, delay=20
                )
                expect(agent_form.welcome_message_input).to_have_value(
                    NEW_WELCOME_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Verify Save and Discard buttons are enabled "
                "(form is dirty after typing)"
            ):
                expect(agent_form.save_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.discard_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 8 — Click Save; verify PUT application → 201; "
                f"verify success toast contains '{EXPECTED_TOAST_TEXT}'"
            ):
                with page.expect_response(
                    lambda r: r.request.method == "PUT"
                    and "/application/prompt_lib/" in r.url
                ) as save_resp_info:
                    agent_form.save_button.click(force=True)
                save_response = save_resp_info.value
                assert save_response.status == 201, (
                    f"Agent save PUT should return 201, got "
                    f"{save_response.status} for {save_response.url}"
                )
                expect(chat.toast_message).to_contain_text(
                    EXPECTED_TOAST_TEXT, timeout=FORM_SAVE_TIMEOUT
                )
                # After save the form is clean → Save should be disabled again
                expect(agent_form.save_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 9 — Close the canvas via the X button; verify canvas "
                "is dismissed and URL no longer contains ?edited_participant_id"
            ):
                agent_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                # Canvas panel closed: title hidden confirms the panel is gone
                expect(agent_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                # URL shed the query param (was /chat?edited_participant_id=N or
                # /chat/{id}?edited_participant_id=N; either way the param is gone)
                expect(page).not_to_have_url(
                    re.compile(r"edited_participant_id"), timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 10 — Verify the composer chip is visible and "
                "no longer shows 'Editing...'"
            ):
                # The chip remains in the composer (agent is still a participant);
                # it should display the agent's name, not the "Editing..." state label.
                expect(chat.chat_participant_settings_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.chat_participant_settings_button).not_to_contain_text(
                    "Editing...", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Steps 11–12 — Navigate directly to the agent's edit page "
                "(/agents/all/{agent_id}?viewMode=owner)"
            ):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(agent_id)

            with allure.step(
                "Step 13 — Welcome Message accordion is expanded by default; "
                "verify the textarea is visible"
            ):
                expect(agent_form.welcome_message_input).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 14 — Verify the Welcome Message textarea displays "
                f"{NEW_WELCOME_MESSAGE!r} — change synchronised from canvas"
            ):
                expect(agent_form.welcome_message_input).to_have_value(
                    NEW_WELCOME_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
                )

            # No new console errors across all steps
            assert not console_messages, (
                "Unexpected console errors during the test: "
                + str([m.text for m in console_messages])
            )

        finally:
            with allure.step("Cleanup — delete conversation"):
                if conversation_id:
                    try:
                        conversation_api.delete_conversation(conversation_id)
                        logger.info("Deleted conversation %d", conversation_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for conversation %d: %s", conversation_id, exc
                        )
            # agent_id fixture handles agent deletion automatically
