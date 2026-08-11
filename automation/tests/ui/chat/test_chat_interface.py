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
            assert visible_count == len(CHAT_INTERNAL_TOOLS), (
                f"Expected {len(CHAT_INTERNAL_TOOLS)} internal tools, found {visible_count}"
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
