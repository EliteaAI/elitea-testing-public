"""Chat – Agent Hub Agent – Verify Only LLM and LLM Settings Can Be Changed
and Changes Are Saved Per Conversation Only (ELITEA-2075).

Opens a public Agent Hub ("Catalog") agent as a chat participant, verifies
its settings canvas is READ-ONLY except the LLM model selector + LLM
settings (Instructions/Tools/Save-button all locked, "Public" label shown
instead), changes the model + reasoning level, verifies the override is
never written back to the agent's own version (zero PUT/PATCH/POST to any
`application` endpoint) and persists across closing/reopening the canvas
within the same conversation.

Genuinely new coverage — no existing page object or spec covered the Agent
Hub/Catalog surface, or the participant read-only canvas + per-conversation
LLM-override flow, before this implementation.

Spec: test-specs/chat-interface/l2_agent-hub-participant-readonly-canvas-llm-override_ELITEA-2075.md

Test-data substitution (AFS § Test Data / Coverage Map): the case's literal
"Anthropic Claude 4.5 Sonnet" does not exist verbatim in this environment;
selection matches any live dropdown option whose display text contains both
"sonnet" and "4.5" case-insensitively (this environment's option is "Azure
Claude Sonnet 4.5").

Known defect (already tracked, not re-filed — AFS § Known Defects Found):
EliteaAI/elitea-testing-public#1043 — the Catalog agent-preview modal's
"Start Chat" button has no `disabled={isFetching}` guard; clicking it before
the modal's own agent-details fetch resolves throws an uncaught TypeError
and silently no-ops. Worked around via
``AgentHubPage.open_agent_by_name()``'s own wait for the modal's
"Show instructions" link to be visible before Start Chat is ever clicked —
this is test synchronization, not defect-masking (the underlying product gap
stays tracked on #1043, untouched).

New page objects (this implementation — genuinely new surface, no prior
coverage to extend):
- ``AgentHubPage`` — Catalog listing (heading/search/category sections/agent
  cards) + agent preview modal.
- ``AgentParticipantCanvasPage(AgentCanvasPage)`` — the read-only
  participant-settings canvas. Inherits title/subtitle/close from
  ``AgentCanvasPage`` (ELITEA-2166) rather than redeclaring — confirmed via
  source (``AgentEditor.jsx``) that both the create-agent canvas and this
  view/edit canvas share the identical ``EditorHeader`` testids. The LLM
  model selector / Model settings dialog fields are reused directly from
  ``AgentDetailPage`` by composition (same shared ``LLMModelSelector.jsx``
  widget tree, same instance of ``page`` — mirrors the existing
  ``AgentPage`` + ``ChatPage`` composition in
  ``test_agent_with_toolkit_chat.py``); the Instructions field reuses
  ``AgentFormPage.instructions_input`` (``agent-instructions-input``) the
  same way — one data-testid, one file, per the project's locator policy.

AFS amendment (this implementation — filed inline, not as a separate
`docs(afs):` diff, since the AFS itself is being amended in the same PR that
motivated it, per the workflow's Phase 2 allowance): the AFS's "testid
needed: agent-canvas-instructions-text" row was STALE — a live testid
(`agent-instructions-input`, `AgentFormPage.instructions_input`) already
renders on the Instructions field's underlying `<textarea>` regardless of
`viewMode`; `disabled` only toggles editability, never unmounts the element.
No new testid was needed there; this test asserts read-only via
`instructions_input.is_editable() is False`, not element absence.
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import Page

from api import ConversationAPI
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agent_hub_page import AgentHubPage
from pages.agent_participant_canvas_page import AgentParticipantCanvasPage
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 90_000  # live LLM completion — AFS Automation Hints (30-90s)

CATALOG_AGENT_NAME = "Reflexion"
TEST_MESSAGE = "hello"

# Environment's live Sonnet-4.5-family option (case's literal "Anthropic
# Claude 4.5 Sonnet" does not exist verbatim here — AFS Coverage Map).
SONNET_MODEL_FILTER_TOKENS = ("sonnet", "4.5")


def _matches_sonnet_45(display_name: str) -> bool:
    lowered = display_name.lower()
    return all(token in lowered for token in SONNET_MODEL_FILTER_TOKENS)


class TestAgentHubParticipantReadonlyCanvasLlmOverride:
    """ELITEA-2075: Agent Hub agent — read-only canvas + per-conversation LLM override (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2075_chat-agent-hub-agent-verify-only-llm-and-llm-settings-can-be-changed-and-changes-are-saved-per-conversation-only.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_agent_hub_participant_readonly_canvas_llm_override(self, page: Page, _browser_cookies):
        """Catalog agent's in-chat settings canvas allows ONLY LLM model/settings
        changes; Instructions/Tools/Save stay read-only; the LLM override is
        conversation-local (never PUT to the agent) and persists across
        closing/reopening the canvas."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)
        canvas = AgentParticipantCanvasPage(page)
        agent_detail = AgentDetailPage(page)  # composed: reuses model-selector/model-settings fields
        agent_form = AgentFormPage(page)  # composed: reuses instructions_input field

        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        conv_id: int | None = None
        console_capture = chat.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to the Agent Hub (Catalog) from the sidebar"
            ):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), (
                    "Catalog page heading should be visible"
                )
                assert agent_hub.search_input.is_visible(), (
                    "Catalog search bar should be visible"
                )
                assert agent_hub.is_category_section_visible("trending", timeout=UI_ELEMENT_TIMEOUT), (
                    "Catalog 'Trending' category section should be visible"
                )

            with allure.step(f"Step 2 — Locate the {CATALOG_AGENT_NAME!r} agent and click on it"):
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                assert agent_hub.modal_agent_name.text_content().strip() == CATALOG_AGENT_NAME, (
                    f"Preview modal should show the agent name {CATALOG_AGENT_NAME!r}"
                )

            with allure.step('Step 3 — Click "Start Chat"; verify a new conversation opens'):
                agent_hub.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()

                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                participant_row = chat.get_participant_row_by_name(
                    CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                row_text = (participant_row.text_content() or "").strip()
                assert CATALOG_AGENT_NAME in row_text and "v1.0" in row_text, (
                    f"PARTICIPANTS panel row should show '{CATALOG_AGENT_NAME}' and 'v1.0', got: {row_text!r}"
                )

            with allure.step(
                'Step 4 — Click "View settings" next to the agent; verify the canvas opens'
            ):
                chat.open_agent_participant_settings(
                    CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                assert canvas.title.text_content().strip() == CATALOG_AGENT_NAME, (
                    f"Canvas title should read {CATALOG_AGENT_NAME!r}"
                )
                assert canvas.subtitle.text_content().strip() == "v1.0", (
                    "Canvas subtitle should read the version name 'v1.0'"
                )
                assert canvas.public_label.is_visible(), (
                    "Canvas header should show the 'Public' label (no edit permission)"
                )

            with allure.step("Step 5 — Verify the LLM model selector is visible"):
                assert agent_detail.model_selector_name.is_visible(), (
                    "LLM model selector should be visible in the canvas"
                )

            with allure.step("Step 6 — Verify the INSTRUCTIONS section is READ-ONLY"):
                assert agent_form.instructions_input.is_visible(), (
                    "Instructions field should still render (read-only, not absent)"
                )
                assert not agent_form.instructions_input.is_editable(), (
                    "Instructions field should NOT be editable for a public/no-edit-permission agent"
                )

            with allure.step("Step 7 — Verify TOOLS module toggles are DISABLED"):
                toggles = canvas.get_all_tools_toggles()
                toggle_count = toggles.count()
                assert toggle_count > 0, "Expected at least one TOOLS module toggle to be visible"
                first_toggle = toggles.first
                checked_before = first_toggle.is_checked()

                toggle_requests = chat.capture_requests_matching("application")
                first_toggle.click(force=True)
                page.wait_for_timeout(500)
                assert first_toggle.is_checked() == checked_before, (
                    "TOOLS toggle's checked state should NOT change on click attempt"
                )
                assert len(toggle_requests) == 0, (
                    f"Clicking a disabled TOOLS toggle should fire zero requests, got: {toggle_requests!r}"
                )
                toggle_requests.stop()

            with allure.step("Step 8 — Verify no SAVE button is visible in the canvas header"):
                assert agent_form.save_button.count() == 0, (
                    "No Save button should be present in the read-only canvas"
                )

            with allure.step(
                "Step 9 — Click the LLM model chip and select a Sonnet 4.5-family model"
            ):
                application_requests = chat.capture_requests_matching("application")

                agent_detail.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                option_names = agent_detail.get_visible_model_option_names(timeout=UI_ELEMENT_TIMEOUT)
                matching_option = next((name for name in option_names if _matches_sonnet_45(name)), None)
                assert matching_option, (
                    f"Expected a Sonnet-4.5-family model option in the dropdown, got: {option_names!r}"
                )

                agent_detail.select_llm_model(matching_option, timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_timeout(500)

                selected_name = agent_detail.get_selected_model_name()
                assert selected_name == matching_option, (
                    f"Model selector should now show {matching_option!r}, got {selected_name!r}"
                )

            with allure.step(
                "Step 10 — Click the settings/gear icon; verify REASONING/MAX TOKENS/CAPABILITIES sections"
            ):
                agent_detail.open_model_settings_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert agent_detail.is_reasoning_slider_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Reasoning slider should be visible for this reasoning-capable model"
                )
                assert agent_detail.model_settings_max_tokens_section.is_visible(), (
                    "Max Completion Tokens section should be visible"
                )
                assert canvas.model_settings_capabilities_section.is_visible(), (
                    "Capabilities section should be visible for this model"
                )

            with allure.step(
                'Step 11 — Adjust REASONING slider to "High"; click Apply'
            ):
                canvas.select_reasoning_level(canvas.REASONING_LEVEL_HIGH, timeout=UI_ELEMENT_TIMEOUT)
                reasoning_text = agent_detail.get_reasoning_slider_text(timeout=UI_ELEMENT_TIMEOUT)
                assert "high" in reasoning_text.lower(), (
                    f"Reasoning slider should now read 'High', got: {reasoning_text!r}"
                )

                canvas.click_apply_settings()
                agent_detail.model_settings_dialog.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

                assert agent_detail.get_selected_model_name() == matching_option, (
                    "Model selector should still show the selected model after Apply"
                )

                assert len(application_requests) == 0, (
                    "Selecting a model and applying LLM settings for a public agent "
                    f"should never PUT/PATCH/POST to /application/ — got: {application_requests!r}"
                )
                application_requests.stop()

            with allure.step("Step 12 — Attempt to click into the INSTRUCTIONS text area"):
                assert not agent_form.instructions_input.is_editable(), (
                    "Instructions field should remain non-editable after a click attempt"
                )

            with allure.step("Step 13 — Close the canvas; verify the conversation view returns"):
                canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                canvas.title.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.message_input.is_visible(), (
                    "Conversation view (composer) should be displayed after closing the canvas"
                )
                assert "edited_participant_id" not in page.url, (
                    f"URL should drop the edited_participant_id query param, got: {page.url}"
                )

                # Axis-2 addition (AFS § Axis 2) — re-open the SAME agent's
                # settings in the SAME conversation: the override must
                # persist in-conversation (the case's own central claim).
                # Closing the canvas re-collapses the PARTICIPANTS panel
                # (confirmed live) — re-expand before locating the row again.
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                chat.open_agent_participant_settings(
                    CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                assert agent_detail.get_selected_model_name() == matching_option, (
                    "The LLM override should persist after closing and reopening the canvas"
                )
                canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                canvas.title.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 14 — Send "hello"; verify the response uses the newly selected LLM'
            ):
                initial_count = chat.get_message_count()
                chat.send_message(TEST_MESSAGE, use_enter=False)
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL after Send, got: {page.url}"
                conv_id = int(match.group(1))

                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

                chat.answer_model_chip.wait_for(state="visible", timeout=AI_RESPONSE_TIMEOUT)
                chip_text = (chat.answer_model_chip.text_content() or "").strip()
                assert "sonnet" in chip_text.lower(), (
                    f"Response's model chip should attribute to the selected Sonnet model, got: {chip_text!r}"
                )

            with allure.step("Side-channel check — no unexpected console errors across the full flow"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to clean up conversation %s: %s", conv_id, exc)
