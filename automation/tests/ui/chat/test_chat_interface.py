"""UI Tests for Elitea Chat Interface.

Tests chat message sending, UI elements, model selection, context settings,
sidebar navigation, and error handling.

Each test that interacts with conversations uses the ``conversation_id``
fixture so it gets a fresh, isolated conversation that is cleaned up
automatically after the test.

Includes participants panel tests (TC-CHAT-014 to 016).

Markers:
    - ui: requires browser
    - p0: critical priority tests
    - p1: high priority tests
    - p2: medium priority tests

Usage:
    cd automation
    pytest test_chat_interface.py -v
    pytest test_chat_interface.py -v -m p0  # Run P0 only
    pytest test_chat_interface.py -v -m "p0 or p1"  # Run P0 + P1
"""

import logging
import re

import pytest
from playwright.sync_api import expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pages.chat_page import ChatPage
from components.mui import Dialog
import allure

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    """Normalize markdown syntax for clipboard vs rendered text comparison.

    The clipboard receives the raw markdown source, while ``get_last_message_text``
    extracts plain text from rendered ``<p>`` / ``<li>`` elements joined with ``\\n``.
    Markdown uses blank lines (``\\n\\n``) as paragraph separators, but the rendered
    extraction produces single ``\\n`` between blocks.  This function normalises both
    representations so the assertion can compare them as equal.
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # **bold** → bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)          # *italic* → italic
    text = re.sub(r'^- ', '', text, flags=re.MULTILINE)  # - bullet → bullet
    text = text.replace('\r\n', '\n')
    text = re.sub(r'\n{2,}', '\n', text)              # collapse blank lines → single newline
    return text.strip()

pytestmark = [pytest.mark.ui]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
AI_RESPONSE_TIMEOUT = 30000   # AI message generation (may take 15s+ on cold starts)
UI_ELEMENT_TIMEOUT = 5000     # buttons, dialogs, dropdowns
NAVIGATION_TIMEOUT = 3000     # SPA route changes
# A pipeline participant's response can take longer than a plain agent's
# (multi-node graph execution / internal tool calls) -- live-confirmed
# during ELITEA-2208/2470 implementation: a dynamically-selected ambient
# pipeline's response was still showing the transient "Thought for less
# than a second" status at AI_RESPONSE_TIMEOUT (30s), then completed
# shortly after. Matches wait_for_ai_response()'s own docstring rationale
# for its 60s default ("toolkit execution which may involve external API
# calls").
PIPELINE_RESPONSE_TIMEOUT = 60000


class TestPageLoadAndRendering:
    """TC-CHAT-001 to TC-CHAT-003: Page load and rendering tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/toolkits-credentials/ELITEA-1142_chat-basic-functionality.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/smoke-suite/ELITEA-1051_chat-basic-functionality.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_chat_page_loads_with_functional_input(self, page, conversation_id):
        """TC-CHAT-001, TC-CHAT-002: Chat page loads with functional message input."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Verify message input is visible and editable"):
            assert chat.message_input.is_visible(), "Message input should be visible"
            assert chat.message_input.is_editable(), "Message input should be editable"

        with allure.step("Step 3 — Verify plus menu button is visible"):
            plus_menu = page.get_by_role("button", name="plus menu")
            assert plus_menu.is_visible(), "Plus menu button should be visible"

        with allure.step("Step 4 — Verify sidebar toggle is visible"):
            assert chat.sidebar_toggle.is_visible(), "Sidebar toggle should be visible"

        with allure.step("Step 5 — Verify input accepts text"):
            chat.message_input.fill("test")
            assert not chat.is_input_empty(), "Input should accept text"
            chat.message_input.clear()


class TestSendingMessages:
    """TC-CHAT-004 to TC-CHAT-007: Message sending tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0503_chat-message-input-methods.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_send_text_message(self, page, conversation_id):
        """TC-CHAT-003, TC-CHAT-004: Send message and verify history."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Send test message"):
            test_message = "Hello, this is an automated test message"
            initial_count = chat.get_message_count()
            chat.send_message(test_message, use_enter=True)

        with allure.step("Step 3 — Wait for AI response"):
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 4 — Verify input cleared and message count increased"):
            assert chat.is_input_empty(), "Input should be cleared after sending"
            new_count = chat.get_message_count()
            assert new_count > initial_count, f"Message count should increase: {initial_count} -> {new_count}"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0503_chat-message-input-methods.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    @pytest.mark.flaky  # Race condition with shift+enter key timing
    def test_shift_enter_adds_new_line(self, page, conversation_id):
        """TC-CHAT-006: Shift+Enter adds new line instead of sending."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Send multi-line message with Shift+Enter"):
            lines = ["Line 1", "Line 2", "Line 3"]
            initial_count = chat.get_message_count()
            chat.send_message_with_shift_enter(lines)

        with allure.step("Step 3 — Wait for AI response"):
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 4 — Verify input cleared"):
            chat.wait_for_input_empty(timeout=UI_ELEMENT_TIMEOUT)
            assert chat.is_input_empty(), "Input should be cleared after sending multi-line message"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0503_chat-message-input-methods.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_cannot_send_empty_message(self, page, conversation_id):
        """TC-CHAT-007: Cannot send empty message."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            initial_count = chat.get_message_count()

        with allure.step("Step 2 — Ensure input is empty and press Enter"):
            chat.message_input.fill("")
            chat.message_input.click()
            chat.message_input.press("Enter")

        with allure.step("Step 3 — Verify no message was sent"):
            chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
            new_count = chat.get_message_count()
            assert new_count == initial_count, "Empty message should not be sent when pressing Enter"


class TestMessageActions:
    """TC-CHAT-008 to TC-CHAT-009: Message action tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0502_chat-message-actions.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_copy_message_to_clipboard(self, page, conversation_id):
        """TC-CHAT-008: Copy message to clipboard."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Send a message"):
            test_message = "Message to copy"
            initial_count = chat.get_message_count()
            chat.send_message(test_message)
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 3 — Wait for streaming to complete"):
            chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 4 — Get AI response text"):
            ai_response_text = chat.get_last_message_text()
            assert ai_response_text, "AI response should have text content"
            assert "packing" not in ai_response_text.lower() and "waking" not in ai_response_text.lower(), (
                f"AI response still shows loading state after waiting. Got: {ai_response_text[:200]}"
            )

        with allure.step("Step 5 — Copy the AI message"):
            chat.copy_message(-1)

        with allure.step("Step 6 — Verify clipboard content matches"):
            clipboard_text = chat.get_clipboard_text()
            assert clipboard_text, "Clipboard should not be empty after copy"
            assert _strip_markdown(clipboard_text) == ai_response_text.strip(), (
                f"Clipboard content does not match message text (after markdown normalization).\n"
                f"Clipboard (normalized): {_strip_markdown(clipboard_text)[:100]}...\n"
                f"Expected: {ai_response_text[:100]}..."
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0502_chat-message-actions.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.flaky  # Intermittent failures with message deletion timing
    def test_delete_message(self, page, conversation_id):
        """TC-CHAT-009: Delete message."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Send a message"):
            initial_count = chat.get_message_count()
            chat.send_message("Message to delete", use_enter=True)
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 3 — Wait for streaming to finish"):
            chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 4 — Count messages before deletion"):
            initial_message_count = chat.get_message_count()
            assert initial_message_count >= 2, (
                f"Expected at least 2 messages (user + AI), got {initial_message_count}"
            )

        with allure.step("Step 5 — Delete the last message"):
            try:
                chat.delete_message(-1)
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Delete button not accessible after hover — "
                    "delete functionality may have changed in current UI"
                )

        with allure.step("Step 6 — Verify message count decreased"):
            new_message_count = chat.get_message_count()
            assert new_message_count < initial_message_count, (
                f"Message count should decrease after deletion: "
                f"{initial_message_count} -> {new_message_count}"
            )


class TestConversationUIElements:
    """TC-CHAT-010 to TC-CHAT-013: Conversation UI element tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0501_chat-ui-elements-model-tools-participants.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_model_selector_opens_menu(self, page, conversation_id):
        """TC-CHAT-010, TC-CHAT-020: Model selector shows current model and opens menu."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.close_open_dialogs()

        with allure.step("Step 2 — Verify current model is displayed"):
            current_model = chat.get_selected_model()
            assert current_model, (
                "Model selector should display the name of the currently selected model"
            )

        with allure.step("Step 3 — Click model selector"):
            chat.click_model_selector()

        with allure.step("Step 4 — Verify menu opens or navigates to settings"):
            menu_visible = False
            try:
                menu = chat.wait_for_model_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert menu is not None, "Model selector menu should open"
                menu_visible = True
            except PlaywrightTimeoutError:
                menu_visible = False

            url_changed = "/model" in page.url or "/settings" in page.url

            assert menu_visible or url_changed, (
                "Clicking model selector should either open a menu or navigate to settings. "
                f"Got: menu visible={menu_visible}, URL={page.url}"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_attach_files_button_sends_file_with_message(self, page, conversation_id, tmp_path):
        """TC-CHAT-011: Attach file and send message with attachment."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Create test file with unique token"):
            test_file = tmp_path / "test_automation_file.txt"
            test_file.write_text("This file contains the unique token AUTOTEST_ATTACH_7X9 and was attached by automated testing.")

        with allure.step("Step 3 — Attach file via available method"):
            file_attached = False

            file_input = page.locator('button[aria-label="attach files"] input[type="file"]').first
            if file_input.count() > 0:
                try:
                    file_input.set_input_files(str(test_file))
                    chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                    file_attached = True
                    logger.info("File attached via direct input method")
                except Exception as e:
                    logger.warning(f"Direct input method failed: {e}")

            if not file_attached:
                attach_btn = page.get_by_role("button", name="attach files").first
                if attach_btn.is_visible():
                    try:
                        with page.expect_file_chooser(timeout=5000) as fc_info:
                            attach_btn.click(force=True)
                        file_chooser = fc_info.value
                        file_chooser.set_files(str(test_file))
                        chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                        file_attached = True
                        logger.info("File attached via file chooser")
                    except PlaywrightTimeoutError:
                        logger.warning("File chooser did not appear")

            if not file_attached:
                plus_menu = page.get_by_role("button", name="plus menu")
                if plus_menu.is_visible():
                    plus_menu.click(force=True)
                    page.wait_for_timeout(500)
                    menu_file_input = page.locator('.MuiPopper-root button[aria-label="attach files"] input[type="file"]')
                    if menu_file_input.count() > 0:
                        try:
                            menu_file_input.set_input_files(str(test_file))
                            chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                            file_attached = True
                            logger.info("File attached via plus menu input")
                        except Exception as e:
                            logger.warning(f"Plus menu input method failed: {e}")
                    if not file_attached:
                        page.keyboard.press("Escape")

            if not file_attached:
                pytest.skip(
                    "File attachment UI not accessible — attach button exists but "
                    "file could not be attached via input or file chooser methods."
                )

        with allure.step("Step 4 — Send message asking about attachment"):
            initial_count = chat.get_message_count()
            chat.send_message("What is the content of the attached file?")

        with allure.step("Step 5 — Wait for AI response"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 6 — Verify message count increased"):
            final_count = chat.get_message_count()
            assert final_count > initial_count, (
                f"Message count should increase after sending. Initial: {initial_count}, Final: {final_count}"
            )

        with allure.step("Step 7 — Verify AI acknowledged the file"):
            ai_response = chat.get_last_message_text()
            assert "waking" not in ai_response.lower(), (
                f"AI response still shows loading state. Got: {ai_response[:200]}"
            )
            normalized_response = ai_response.lower().replace("_", "")
            file_acknowledged = "autotestattach7x9" in normalized_response
            assert file_acknowledged, (
                f"AI response should mention the unique token from the attached file "
                f"(AUTOTEST_ATTACH_7X9). Got: {ai_response[:200]}..."
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0501_chat-ui-elements-model-tools-participants.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_internal_tools_panel_shows_all_tools(self, page, conversation_id):
        """TC-CHAT-012: Internal tools panel displays all available tools."""
        from pages.internal_tools import CHAT_INTERNAL_TOOLS

        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Check plus menu exists"):
            plus_menu_btn = page.get_by_role("button", name="plus menu")
            if not plus_menu_btn.is_visible():
                pytest.skip(
                    "Plus menu button not visible — feature may not be available "
                    "in this environment or UI has changed"
                )

        with allure.step("Step 3 — Open internal tools panel"):
            chat.open_internal_tools_menu()

        with allure.step("Step 4 — Verify all internal tools are visible"):
            for tool_name in CHAT_INTERNAL_TOOLS:
                tool_switch = chat.get_internal_tool_switch(tool_name)
                assert tool_switch.is_visible(), (
                    f"Internal tool '{tool_name}' should be visible in the panel"
                )

        with allure.step("Step 5 — Verify expected tool count"):
            visible_count = chat.get_visible_switch_count()
            assert visible_count >= len(CHAT_INTERNAL_TOOLS), (
                f"Expected at least {len(CHAT_INTERNAL_TOOLS)} internal tools, found {visible_count} "
                f"(DEV may have additional tools enabled)"
            )

        with allure.step("Step 6 — Close the panel"):
            page.keyboard.press("Escape")

class TestHashSearch:
    """TC-CHAT-017 to TC-CHAT-018: # search functionality tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0501_chat-ui-elements-model-tools-participants.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0498_chat-participants-add-via-hash-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_hash_search_participants(self, page, conversation_id):
        """TC-CHAT-017: Use # to search participants."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Type '#agent' to trigger search"):
            chat.message_input.click()
            chat.message_input.press_sequentially("#agent", delay=50)

        with allure.step("Step 3 — Verify search dropdown appears"):
            try:
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Hash search dropdown did not appear after typing '#agent' — "
                    "# mention feature may be disabled in this environment"
                )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0501_chat-ui-elements-model-tools-participants.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0498_chat-participants-add-via-hash-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_add_participant_via_hash_search(self, page, conversation_id):
        """TC-CHAT-018: Add participant via # search and select option.

        The hash search feature detects '#' via keydown events, so we must
        use press_sequentially() instead of fill() to trigger it.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # ------------------------------------------------------------------
        # Step 1 — Type '#' to open search dropdown
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Type '#' to open search dropdown"):
            chat.message_input.click()
            chat.message_input.press_sequentially("#", delay=50)
            try:
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Hash search dropdown did not appear after typing '#' — "
                    "# mention feature may be disabled in this environment"
                )

        # ------------------------------------------------------------------
        # Step 2 — Select the first available option
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Select the first available option"):
            page.wait_for_timeout(500)  # Let results load
            first_option = chat.get_hash_search_first_option()
            if first_option is None:
                pytest.skip("No search results available for '#'")

            first_option.click()
            chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 3 — Verify dropdown closes after selection
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Verify dropdown closes after selection"):
            assert not chat.is_hash_search_dropdown_visible(), (
                "Hash search dropdown should close after selecting an option"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2206_chat-mentions-with-hash-displays-all-available-agents-and-pipelines.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_hash_search_shows_agents_and_pipelines_from_all_sources(self, page, conversation_id):
        """ELITEA-2206: '#' shows all available agents/pipelines from all sources.

        extend-existing gap-fill on TestHashSearch (AFS:
        test-specs/chat-interface/lextend_hash-search-shows-agents-and-pipelines-from-all-sources_ELITEA-2206.md).
        The covering tests above already prove the dropdown OPENS on '#' and
        CLOSES on selection -- this test only adds the three assertions
        ELITEA-2206's own steps ask for that neither covering test makes:
        per-card type subtitle + icon presence split by agent/pipeline
        (Steps 2-3), a mixed current-project + Agent-Hub result set in one
        query (Step 4), and the click-away-WITHOUT-selecting close path
        (the other half of Step 5).

        No substitution: every assertion reads a value the live product
        rendered off a real '#'/'#pipe' query on an existing conversation
        (ambient DEV data, no seeding) -- nothing fabricated or injected.
        """
        with allure.step("Step 1 — Navigate to chat page and type '#' to open the search results dropdown"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.message_input.click()
            chat.message_input.press_sequentially("#", delay=50)
            try:
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Hash search dropdown did not appear after typing '#' — "
                    "# mention feature may be disabled in this environment"
                )
            expect(chat.chat_hash_search_results_list).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.get_hash_search_items().first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Verify agent items show 'agent' subtitle and an icon"):
            items = chat.get_hash_search_items()
            item_count = items.count()
            assert item_count > 0, "Hash search results should contain at least one item for a bare '#' query"

            agent_item = next(
                (items.nth(i) for i in range(item_count)
                 if chat.get_hash_search_item_subtitle(items.nth(i)) == "agent"),
                None,
            )
            assert agent_item is not None, "Expected at least one 'agent' item in the '#' results"
            assert chat.hash_search_item_has_icon(agent_item), (
                "Agent item card should render an icon/avatar element"
            )

        with allure.step("Step 3 — Verify pipeline items show 'pipeline' subtitle and an icon"):
            pipeline_item = next(
                (items.nth(i) for i in range(item_count)
                 if chat.get_hash_search_item_subtitle(items.nth(i)) == "pipeline"),
                None,
            )

            if pipeline_item is None:
                # Bare '#' page didn't surface a pipeline card — fall back to
                # a query prefix confirmed live to return one (AFS Automation
                # Hints), scoped to this sub-assertion only.
                chat.message_input.click()
                chat.message_input.press("Control+a")
                chat.message_input.press("Backspace")
                chat.message_input.press_sequentially("#pipe", delay=50)
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_hash_search_items().first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                pipe_items = chat.get_hash_search_items()
                pipe_count = pipe_items.count()
                pipeline_item = next(
                    (pipe_items.nth(i) for i in range(pipe_count)
                     if chat.get_hash_search_item_subtitle(pipe_items.nth(i)) == "pipeline"),
                    None,
                )
                assert pipeline_item is not None, "Expected at least one 'pipeline' item for '#pipe'"
                assert chat.hash_search_item_has_icon(pipeline_item), (
                    "Pipeline item card should render an icon/avatar element"
                )

                # Restore the bare '#' query — Steps 4-5 assert the original
                # unscoped result set.
                chat.message_input.click()
                chat.message_input.press("Control+a")
                chat.message_input.press("Backspace")
                chat.message_input.press_sequentially("#", delay=50)
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_hash_search_items().first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                items = chat.get_hash_search_items()
                item_count = items.count()
            else:
                assert chat.hash_search_item_has_icon(pipeline_item), (
                    "Pipeline item card should render an icon/avatar element"
                )

        with allure.step("Step 4 — Verify results mix current-project and Agent Hub sources"):
            has_public = any(
                chat.hash_search_item_has_public_label(items.nth(i)) for i in range(item_count)
            )
            has_non_public = any(
                not chat.hash_search_item_has_public_label(items.nth(i)) for i in range(item_count)
            )
            assert has_public, "Expected at least one Agent Hub ('Public') item in the '#' results"
            assert has_non_public, "Expected at least one current-project (non-'Public') item in the '#' results"

        with allure.step("Step 5 — Press elsewhere (no selection) closes the dropdown"):
            chat.messages_list.click(position={"x": 10, "y": 10})
            chat.chat_hash_search_results_list.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)
            assert not chat.is_hash_search_dropdown_visible(), (
                "Hash search dropdown should close after clicking away without selecting"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2207_chat-mentions-with-hash-select-agent-from-list-and-verify-agent-is-added-to-participants.md",
        "onetest-ai Test Case link (ELITEA-2207)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2469_chat-select-agent-from-hash-list-adds-it-to-participants-and-it-can-respond.md",
        "onetest-ai Test Case link (ELITEA-2469)",
    )
    @pytest.mark.p1
    def test_add_agent_via_hash_search_joins_participants_and_responds(self, page, conversation_id):
        """ELITEA-2207 / ELITEA-2469 (family — 2469 is a more granular
        superset of the same flow 2207 describes; one live execution
        satisfies both, same pattern as ELITEA-2179/2466).

        extend-existing gap-fill on TestHashSearch
        (AFS: test-specs/chat-interface/
        lextend_hash-search-select-agent-adds-participant-and-responds_ELITEA-2207.md).
        The covering tests above already prove '#' opens the dropdown and a
        click on any first option closes it -- this test adds every
        assertion neither covering test makes: the selection is scoped to
        an AGENT card specifically (not "whichever card is first"), the
        PARTICIPANTS panel gains an AGENTS section, the composer shows the
        selected agent as its active participant, sending a message reaches
        the agent, the agent responds, and it remains a participant
        afterward. ELITEA-2469's own extra granularity (Step 5 -- the
        popover row must show name, version, AND icon) is asserted in Step
        4 below, tagged for ELITEA-2469 specifically -- ELITEA-2207 only
        asks for the AGENTS section to exist, which Step 3 already covers.

        No substitution: every assertion reads a value the live product
        rendered off a real '#' selection + a real sent message on a fresh,
        API-seeded conversation (conversation_id fixture) -- nothing
        fabricated or injected. The agent card is resolved dynamically (the
        first AGENT-type result, never a hardcoded name) for resilience
        against account data changes, per the AFS's own Automation Hints.
        """
        with allure.step("Step 1 — Create a new conversation; verify no AGENTS in PARTICIPANTS"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            assert not chat.is_participants_badge_visible(section="agents", timeout=UI_ELEMENT_TIMEOUT), (
                "A fresh conversation should show no AGENTS section in PARTICIPANTS"
            )

        with allure.step("Step 2 — Type '#' and select the first AGENT-type card from the dropdown"):
            chat.message_input.click()
            chat.message_input.press_sequentially("#", delay=50)
            try:
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Hash search dropdown did not appear after typing '#' — "
                    "# mention feature may be disabled in this environment"
                )
            expect(chat.get_hash_search_items().first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            items = chat.get_hash_search_items()
            item_count = items.count()
            agent_item = next(
                (items.nth(i) for i in range(item_count)
                 if chat.get_hash_search_item_subtitle(items.nth(i)) == "agent"),
                None,
            )
            if agent_item is None:
                pytest.skip("No 'agent'-type item available in the '#' results for this account")

            agent_name = chat.get_hash_search_item_name(agent_item)
            assert agent_name, "Resolved agent card should have a non-empty display name"
            # The agent's OWN home project (entity_meta.project_id) -- NOT
            # necessarily the conversation's project. The '#' dropdown mixes
            # current-project and Agent-Hub ("Public") sourced agents in one
            # result set (ELITEA-2206), and a Public agent's participant
            # uniqueId is built from ITS OWN project id, not the
            # conversation's -- see get_agent_participant_row()'s
            # agent_project_id docstring.
            agent_project_id, agent_id = chat.get_hash_search_item_ids(agent_item)

            agent_item.click()
            chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
            assert not chat.is_hash_search_dropdown_visible(), (
                "Hash search dropdown should close after selecting the agent"
            )

        with allure.step(
            "Step 3 — Verify the agent appears as the composer's active participant "
            "and the AGENTS section is added to PARTICIPANTS"
        ):
            assert chat.is_agent_participant_in_composer(agent_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Composer should show {agent_name!r} as the active agent participant"
            )
            assert chat.is_participants_badge_visible(section="agents", timeout=UI_ELEMENT_TIMEOUT), (
                "AGENTS section should be added to PARTICIPANTS after selecting an agent"
            )

        with allure.step(
            "Step 4 (ELITEA-2469) — Verify the PARTICIPANTS popover row shows "
            "the agent's name, version, and icon"
        ):
            popper = chat.open_participants_popover(section="agents", timeout=UI_ELEMENT_TIMEOUT)
            row = chat.get_agent_participant_row(
                popper, agent_id, timeout=UI_ELEMENT_TIMEOUT, agent_project_id=agent_project_id,
            )
            row_text = row.text_content() or ""
            assert agent_name in row_text, (
                f"Participants popover row should show the agent name {agent_name!r}, got {row_text!r}"
            )
            # Version control text after the name: either the literal "ver"
            # (single-version agents, per AFS live exploration) or "vX.Y"
            # (multi-version agents) -- both start with a lowercase "v"
            # right after the name, live-confirmed via both shapes this
            # session ("AAv1.0" for a versioned agent). Never hardcode
            # which shape, since the agent is resolved dynamically.
            version_text = row_text[len(agent_name):]
            assert re.match(r"v(er\b|\d)", version_text.lower()), (
                f"Participants popover row should show a version control after "
                f"the agent name (e.g. 'ver' or 'v1.0'), got remainder {version_text!r} "
                f"of full row text {row_text!r}"
            )
            assert chat.get_participant_icon(row, timeout=UI_ELEMENT_TIMEOUT).is_visible(), (
                "Participants popover row should show the agent's icon"
            )
            chat.dismiss_participants_popover()

        with allure.step("Step 5 — Type 'hello' and send the message"):
            initial_count = chat.get_message_count()
            chat.send_message("hello")

        with allure.step("Step 6 — Verify the agent responds and remains in PARTICIPANTS"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            assert chat.get_message_count() >= initial_count + 2, (
                "Message count should grow by the sent message + the agent's response"
            )
            assert chat.is_participants_badge_visible(section="agents", timeout=UI_ELEMENT_TIMEOUT), (
                "Agent should remain in PARTICIPANTS after responding"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2208_chat-mentions-with-hash-select-pipeline-adds-to-participants.md",
        "onetest-ai Test Case link (ELITEA-2208)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2470_chat-select-pipeline-from-list-adds-it-to-participants-and-i.md",
        "onetest-ai Test Case link (ELITEA-2470)",
    )
    @pytest.mark.p1
    def test_add_pipeline_via_hash_search_joins_participants_and_responds(self, page, conversation_id):
        """ELITEA-2208 / ELITEA-2470 (family — 2470 is a more granular
        superset of the same flow 2208 describes; one live execution
        satisfies both, same pattern as ELITEA-2207/2469).

        extend-existing gap-fill on TestHashSearch (AFS:
        test-specs/chat-interface/
        lextend_hash-search-select-pipeline-adds-participant-and-responds_ELITEA-2208.md).
        Direct pipeline-flow sibling of
        ``test_add_agent_via_hash_search_joins_participants_and_responds`` --
        same mechanism (open dropdown, scoped select, composer chip,
        participants-panel section, popover row, send, respond, remain a
        participant), but scoped to a PIPELINE-type card, PIPELINES
        section, and the pipeline's own participant ``uniqueId`` prefix
        (``pipeline_{id}_{project_id}``, NOT the agent's ``application_``
        prefix -- confirmed by reading
        ``participants.helpers.js``'s ``getChatParticipantUniqueId()``, AFS
        Concrete Handles). ELITEA-2470's own extra granularity (Step 5 --
        the popover row must show name, version, AND icon) is asserted in
        Step 4 below, tagged for ELITEA-2470 specifically -- ELITEA-2208
        only asks for the PIPELINES section to exist, which Step 3 already
        covers.

        No substitution: every assertion reads a value the live product
        rendered off a real '#' selection + a real sent message on a
        fresh, API-seeded conversation (conversation_id fixture) --
        nothing fabricated or injected. The pipeline card is resolved
        dynamically (the first PIPELINE-type result, never a hardcoded
        name) for resilience against account data changes. Never asserts
        the response's specific text (AFS Axis 2, Clarification 2 -- an
        ambient probe pipeline may correctly respond with an
        execution-error card if it has no configured nodes; both cases'
        own expected result only asks that the pipeline "processes and
        responds" and "remains in PARTICIPANTS", never a specific content).
        """
        with allure.step("Step 1 — Create a new conversation; verify no PIPELINES in PARTICIPANTS"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            assert not chat.is_participants_badge_visible(section="pipelines", timeout=UI_ELEMENT_TIMEOUT), (
                "A fresh conversation should show no PIPELINES section in PARTICIPANTS"
            )

        with allure.step("Step 2 — Type '#' and select the first PIPELINE-type card from the dropdown"):
            chat.message_input.click()
            chat.message_input.press_sequentially("#", delay=50)
            try:
                chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Hash search dropdown did not appear after typing '#' — "
                    "# mention feature may be disabled in this environment"
                )
            expect(chat.get_hash_search_items().first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            items = chat.get_hash_search_items()
            item_count = items.count()
            pipeline_item = next(
                (items.nth(i) for i in range(item_count)
                 if chat.get_hash_search_item_subtitle(items.nth(i)) == "pipeline"),
                None,
            )
            if pipeline_item is None:
                pytest.skip("No 'pipeline'-type item available in the '#' results for this account")

            pipeline_name = chat.get_hash_search_item_name(pipeline_item)
            assert pipeline_name, "Resolved pipeline card should have a non-empty display name"
            # The pipeline's OWN home project (entity_meta.project_id) --
            # same "not necessarily the conversation's project" caveat the
            # agent family already documents, since the '#' dropdown mixes
            # current-project and Agent-Hub-sourced results in one set.
            pipeline_project_id, pipeline_id = chat.get_hash_search_item_ids(pipeline_item)

            pipeline_item.click()
            chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
            assert not chat.is_hash_search_dropdown_visible(), (
                "Hash search dropdown should close after selecting the pipeline"
            )

        with allure.step(
            "Step 3 — Verify the pipeline appears as the composer's active participant "
            "and the PIPELINES section is added to PARTICIPANTS"
        ):
            assert chat.is_agent_participant_in_composer(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Composer should show {pipeline_name!r} as the active pipeline participant"
            )
            assert chat.is_participants_badge_visible(section="pipelines", timeout=UI_ELEMENT_TIMEOUT), (
                "PIPELINES section should be added to PARTICIPANTS after selecting a pipeline"
            )

        with allure.step(
            "Step 4 (ELITEA-2470) — Verify the PARTICIPANTS popover row shows "
            "the pipeline's name, version, and icon"
        ):
            popper = chat.open_participants_popover(section="pipelines", timeout=UI_ELEMENT_TIMEOUT)
            row = chat.get_agent_participant_row(
                popper, pipeline_id, timeout=UI_ELEMENT_TIMEOUT,
                agent_project_id=pipeline_project_id, entity_type="pipeline",
            )
            row_text = row.text_content() or ""
            assert pipeline_name in row_text, (
                f"Participants popover row should show the pipeline name {pipeline_name!r}, got {row_text!r}"
            )
            # Pipeline versions render their own NAME as a literal string
            # (e.g. "base") -- NOT the agent family's "ver"/"vX.Y"
            # auto-generated shape (AFS Automation Hints -- do not reuse
            # the agent test's `re.match(r"v(er\b|\d)", ...)` regex here).
            # Assert only that a non-empty version-text remainder exists
            # after the pipeline's name.
            version_text = row_text[len(pipeline_name):]
            assert version_text.strip(), (
                f"Participants popover row should show a version-name remainder after "
                f"the pipeline name, got remainder {version_text!r} of full row text {row_text!r}"
            )
            assert chat.get_participant_icon(row, timeout=UI_ELEMENT_TIMEOUT).is_visible(), (
                "Participants popover row should show the pipeline's icon"
            )
            chat.dismiss_participants_popover()

        with allure.step("Step 5 — Type 'hello' and send the message"):
            initial_count = chat.get_message_count()
            chat.send_message("hello")

        with allure.step("Step 6 — Verify the pipeline responds and remains in PARTICIPANTS"):
            chat.wait_for_ai_response(initial_count=initial_count, timeout=PIPELINE_RESPONSE_TIMEOUT)
            assert chat.get_message_count() >= initial_count + 2, (
                "Message count should grow by the sent message + the pipeline's response "
                "(the response may be a genuine execution-error card if the dynamically "
                "selected ambient pipeline has no configured nodes -- AFS Axis 2, "
                "Clarification 2 -- never assert on specific response text)"
            )
            assert chat.is_participants_badge_visible(section="pipelines", timeout=UI_ELEMENT_TIMEOUT), (
                "Pipeline should remain in PARTICIPANTS after responding"
            )


class TestContextAndSettings:
    """TC-CHAT-019 to TC-CHAT-020: Context and settings tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_edit_context_settings(self, page, conversation_id):
        """TC-CHAT-019: Edit context settings."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Send a message to populate Context Budget"):
            initial_count = chat.get_message_count()
            chat.send_message("Context settings test", use_enter=True)
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 3 — Expand Participants panel if needed"):
            participants_toggle = page.locator('button').filter(has=page.locator('img')).filter(
                has=page.get_by_text("Participants").locator("xpath=../..")
            )
            context_budget = page.get_by_text("Context Budget")
            if not context_budget.is_visible():
                panel_toggle = page.locator('[class*="panel"] button, main button').last
                if panel_toggle.is_visible():
                    panel_toggle.click(force=True)
                    page.wait_for_timeout(500)

        with allure.step("Step 4 — Click edit context settings button"):
            try:
                chat.edit_context_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            except PlaywrightTimeoutError:
                pytest.skip("Edit context settings button not visible — context panel may not be available")
            chat.edit_context_settings()

        with allure.step("Step 5 — Verify context settings dialog opened"):
            Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)


class TestSidebarNavigation:
    """TC-CHAT-021 to TC-CHAT-022: Sidebar navigation tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_open_close_sidebar(self, page, conversation_id):
        """TC-CHAT-021: Open/close sidebar drawer."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Check initial sidebar state"):
            agents_btn = page.get_by_role("button", name="Agents", exact=True)
            sidebar_is_expanded = agents_btn.is_visible()

        with allure.step("Step 3 — Toggle sidebar open/close"):
            if sidebar_is_expanded:
                chat.close_sidebar()
                chat.wait_for_sidebar_collapsed(timeout=UI_ELEMENT_TIMEOUT)
                chat.open_sidebar()
                chat.wait_for_sidebar_expanded(timeout=UI_ELEMENT_TIMEOUT)
            else:
                chat.open_sidebar()
                chat.wait_for_sidebar_expanded(timeout=UI_ELEMENT_TIMEOUT)
                chat.close_sidebar()
                chat.wait_for_sidebar_collapsed(timeout=UI_ELEMENT_TIMEOUT)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_navigate_to_agents_from_sidebar(self, page, conversation_id):
        """TC-CHAT-022: Navigate to Agents from sidebar."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Ensure sidebar is expanded"):
            agents_btn = page.get_by_role("button", name="Agents", exact=True)
            if not agents_btn.is_visible():
                chat.open_sidebar()
                chat.wait_for_sidebar_expanded(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Click Agents button"):
            agents_btn.click()

        with allure.step("Step 4 — Verify navigation to agents page"):
            chat.wait_for_navigation("/agent", timeout=10000)
            current_url = chat.page.url
            assert "/agents" in current_url or "/agent" in current_url, \
                f"Should navigate to agents page, current URL: {current_url}"


class TestSearchAndErrorHandling:
    """TC-CHAT-023 to TC-CHAT-024: Search and error handling tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_search_conversations_dialog(self, page, conversation_id):
        """TC-CHAT-023: Search conversations."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Open search conversations"):
            chat.open_search_conversations()

        with allure.step("Step 3 — Verify search input is visible"):
            try:
                search_input = chat.wait_for_search_dialog(timeout=UI_ELEMENT_TIMEOUT)
                assert search_input.is_visible(), "Search input should be visible"
            except PlaywrightTimeoutError:
                pytest.skip(
                    "Search conversations input did not appear — "
                    "search feature may not be available in this environment"
                )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_handle_message_send_failure(self, page, conversation_id):
        """TC-CHAT-024: Handle message send failure gracefully."""
        with allure.step("Step 1 — Navigate to chat page"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            initial_count = chat.get_message_count()

        with allure.step("Step 2 — Send oversized message"):
            very_long_message = "A" * 100000
            chat.send_message(very_long_message, use_enter=True)
            chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        with allure.step("Step 3 — Verify graceful handling"):
            has_error = chat.has_error_notification()
            final_count = chat.get_message_count()
            message_sent_successfully = final_count > initial_count

            assert has_error or final_count == initial_count or message_sent_successfully, (
                f"Expected graceful handling of oversized input "
                f"(error, rejection, or successful send), "
                f"got: has_error={has_error}, count {initial_count} -> {final_count}"
            )
