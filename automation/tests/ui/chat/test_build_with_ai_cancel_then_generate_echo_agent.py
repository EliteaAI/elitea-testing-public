"""Chat — Build with AI: Cancel-then-Generate an Echo Agent from the in-chat
canvas (ELITEA-2073).

Coverage boundary (AFS § Coverage decision): `test_build_with_ai_from_chat_
canvas.py` (ELITEA-1920, merged) proves Generate -> review -> Create Agent
inside the chat canvas, but never exercises Cancel. `test_agent_build_with_
ai.py`'s `TestAgentBuildWithAICancelFromPromptStep` (ELITEA-1917, merged)
proves Cancel-before-Generate closes the modal without creating an agent,
but on the standalone `/agents/create` page, not the chat canvas, and never
re-opens the modal and retries a real generation afterward. This case's own
subject — canvas sections + entry point, Cancel resets the modal, then a
real re-opened Generate -> review -> Create Agent cycle lands the canvas in
the "Editing..." state — is the genuinely new combination neither existing
spec runs end-to-end.

Spec: test-specs/chat-interface/l2_build-with-ai-cancel-then-generate-echo-agent-from-chat-canvas_ELITEA-2073.md

Zero new page-object locators or testids were needed (100% reuse of
``ChatPage``, ``AgentCanvasPage``, ``GenerateAgentModalPage``,
``AgentFormPage``).
"""

import logging

import allure
import pytest
from pages.agent_canvas_page import AgentCanvasPage
from pages.agent_form_page import AgentFormPage
from pages.chat_page import ChatPage
from pages.generate_agent_modal_page import GenerateAgentModalPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.build_with_ai_cancel_then_generate")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.agents, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
# The generate-draft call is a real (non-mocked) LLM call — this session's
# live run took ~35s wall time. A generous timeout avoids flaking on
# ordinary LLM-latency variance (same rationale as LIVE_GENERATE_RESPONSE_
# TIMEOUT in test_agent_build_with_ai.py / test_build_with_ai_from_chat_canvas.py).
LIVE_GENERATE_RESPONSE_TIMEOUT = 45_000

# Verbatim from the case's own Test Data table.
PROMPT_TEXT = "generate an echo agent"

# ``AgentCanvasPage.SECTION_KEYS`` already enumerates exactly the 5 keys the
# case's own step 3 names (GENERAL/INSTRUCTIONS/WELCOME MESSAGE/CHAT
# STARTERS/ADVANCED) — asserted here by iterating that same tuple so the
# case's checklist and the page object's inventory can never silently drift
# apart.
EXPECTED_SECTION_COUNT = 5


class TestBuildWithAICancelThenGenerateEchoAgent:
    """ELITEA-2073: Chat – Create Agent with AI Build – Click Cancel and
    Verify Creation is Terminated (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2073_chat-create-agent-with-ai-build-click-cancel-and-verify-creation-is-terminated.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_cancel_then_generate_creates_echo_agent_in_canvas(self, page, agent_api):
        """Cancel on the Build-with-AI prompt step (inside the chat canvas)
        closes the modal without generating anything; re-opening the SAME
        modal and completing a real Generate -> Create Agent cycle populates
        the canvas with the AI-generated "Echo Agent" configuration and
        leaves it in the "Editing..." state.

        Steps (AFS
        test-specs/chat-interface/l2_build-with-ai-cancel-then-generate-echo-agent-from-chat-canvas_ELITEA-2073.md):
        1-2. + Chat -> + menu -> Agents -> + Create New Agent; canvas opens.
        3. All 5 accordion sections present.
        4. Build with AI button visible.
        5-6. Open the modal; placeholder + Cancel/Generate shown; Generate
             disabled until text entered.
        7. Type the prompt; Generate becomes enabled.
        8-9. Click Cancel; modal closes immediately; canvas stays open/empty.
        10. Re-open the modal; prompt textarea is empty again.
        11-12. Type + Generate; loading indicator, then a populated review
               form.
        13. Click Create Agent; stays on /chat, canvas title updates.
        14-15. Canvas shows the generated Name; "Editing..." state shown.
        """
        chat = ChatPage(page)
        agent_canvas = AgentCanvasPage(page)
        agent_form = AgentFormPage(page)
        modal = GenerateAgentModalPage(page)

        agent_id = None

        console_messages = []

        def _on_console(msg):
            # Excludes the pre-existing, already-documented `disableUnderline`
            # React-prop warning on GenerateAgentReviewForm.jsx (AFS § step 12
            # / Expected Results; test-specs/agents/_surface.md,
            # test-specs/skills/_surface.md carry the same baseline entry).
            if msg.type == "error" and "disableUnderline" not in msg.text:
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Setup — navigate to chat and open a fresh conversation"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Steps 1-2 — + menu -> Agents -> + Create New Agent; verify the "
                "canvas panel opens with heading 'Create New Agent'"
            ):
                chat.open_create_new_agent_canvas(timeout=NAVIGATION_TIMEOUT)
                agent_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_have_text("Create New Agent", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify all 5 canvas sections are visible: GENERAL, "
                "INSTRUCTIONS, WELCOME MESSAGE, CHAT STARTERS, ADVANCED"
            ):
                assert len(agent_canvas.SECTION_KEYS) == EXPECTED_SECTION_COUNT, (
                    "Page object's SECTION_KEYS inventory should list exactly the "
                    "case's own 5 named sections"
                )
                for key in agent_canvas.SECTION_KEYS:
                    expect(agent_canvas.get_section_header(key)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 4 — Verify the "Build with AI" button is visible in the GENERAL section'):
                expect(modal.open_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 5 — Click "Build with AI"; verify the modal opens'):
                modal.open_modal(timeout=UI_ELEMENT_TIMEOUT)
                expect(modal.modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6 — Verify placeholder text and Cancel/Generate buttons; "
                "Generate is disabled before any text is entered"
            ):
                expect(modal.prompt_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert (modal.prompt_input.get_attribute("placeholder") or "").strip(), (
                    "Prompt textarea should carry non-empty placeholder text"
                )
                expect(modal.cancel_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(modal.generate_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert not modal.is_generate_enabled(), (
                    "Generate button should be disabled before any prompt text is entered"
                )

            with allure.step('Step 7 — Type the prompt; verify Generate becomes enabled'):
                modal.fill_prompt(PROMPT_TEXT)
                assert modal.get_prompt_value() == PROMPT_TEXT
                assert modal.is_generate_enabled(), (
                    "Generate button should become enabled once the prompt textarea is non-empty"
                )

            with allure.step('Step 8 — Click "Cancel" without generating'):
                modal.cancel_button.click()
                expect(modal.modal).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 9 — Verify no generation took place: canvas remains open, "
                "the Name field is still empty"
            ):
                expect(agent_canvas.title).to_have_text("Create New Agent", timeout=UI_ELEMENT_TIMEOUT)
                assert agent_form.name_input.input_value() == "", (
                    "Agent Name field should remain empty after cancelling Build with AI"
                )

            with allure.step('Step 10 — Click "Build with AI" again; verify the prompt textarea is empty'):
                modal.open_modal(timeout=UI_ELEMENT_TIMEOUT)
                assert modal.get_prompt_value() == "", (
                    "Prompt textarea should be empty again on re-opening the modal after Cancel"
                )

            with allure.step(
                'Step 11 — Type the prompt and click "Generate"; verify the '
                'loading indicator appears'
            ):
                modal.fill_prompt(PROMPT_TEXT)
                modal.generate_button.click()
                expect(modal.loading_indicator).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 12 — Wait for AI generation to complete; verify the review "
                "form renders with populated Name/Description/Instructions and "
                "Create Agent/Back to prompt buttons"
            ):
                modal.wait_for_review_form(timeout=LIVE_GENERATE_RESPONSE_TIMEOUT)
                generated_name = modal.get_review_name()
                assert generated_name, "Review-form Name field should be pre-populated"
                assert modal.get_review_description(), (
                    "Review-form Description field should be pre-populated"
                )
                assert modal.get_review_instructions(), (
                    "Review-form Instructions field should be pre-populated"
                )
                expect(modal.approve_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(modal.back_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 13 — Click "Create Agent"; verify the creation POST resolves '
                "201 and the canvas stays on /chat"
            ):
                create_response = modal.click_approve_and_wait_for_agent_created(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert create_response.status == 201, (
                    f"Agent-creation POST should resolve 201, got {create_response.status}"
                )
                created_agent = create_response.json()
                agent_id = created_agent.get("id")
                assert agent_id, f"Expected a numeric agent id in the creation response, got: {created_agent!r}"
                created_agent_name = created_agent.get("name")
                assert "/agents/all/" not in page.url, (
                    f"Should stay on /chat, not navigate to the agent's own detail page — got {page.url}"
                )

            with allure.step(
                "Step 14 — Verify the canvas shows the generated Name (case's own "
                "\"shows Name\" claim, satisfied via the same title-transition "
                "contract ELITEA-1920/2166 already prove)"
            ):
                expect(agent_canvas.title).to_have_text(created_agent_name, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 15 — Verify the agent is in "Editing..." state'):
                expect(chat.chat_participant_settings_button).to_contain_text(
                    "Editing...", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Side-channel check — zero console errors across the whole flow"):
                assert not console_messages, f"Unexpected console errors: {console_messages}"
        finally:
            with allure.step("Cleanup — delete the created agent"):
                # No message was ever sent in this flow, so the conversation
                # never acquired a server-side id (same "unsaved until first
                # message" behavior ELITEA-1920/2166 already document) —
                # nothing to delete server-side.
                if agent_id:
                    try:
                        agent_api.delete_agent(agent_id)
                        logger.info("Deleted agent %s", agent_id)
                    except Exception as exc:
                        logger.warning("Cleanup failed for agent %s: %s", agent_id, exc)
