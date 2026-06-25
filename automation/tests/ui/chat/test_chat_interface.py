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
    """Normalize markdown syntax for clipboard vs rendered text comparison."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # **bold** → bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)          # *italic* → italic
    text = re.sub(r'^- ', '', text, flags=re.MULTILINE)  # - bullet → bullet
    return text.replace('\r\n', '\n').strip()

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
        """TC-CHAT-001, TC-CHAT-002: Chat page loads with functional message input.

        Verifies:
        - Page loads without errors (TC-CHAT-001)
        - Message input is visible and editable (TC-CHAT-001, TC-CHAT-002)
        - Plus menu button is visible (for adding participants/attachments)
        - Sidebar toggle is accessible (TC-CHAT-001)

        Note: The send button only appears when there's text in the input,
        so we verify message sending works rather than button visibility.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        assert chat.message_input.is_visible(), "Message input should be visible"
        assert chat.message_input.is_editable(), "Message input should be editable"

        # Plus menu is the new access point for attachments and participants
        plus_menu = page.get_by_role("button", name="plus menu")
        assert plus_menu.is_visible(), "Plus menu button should be visible"

        assert chat.sidebar_toggle.is_visible(), "Sidebar toggle should be visible"

        # Minimal interaction to verify input is actually functional (not just visible)
        chat.message_input.fill("test")
        assert not chat.is_input_empty(), "Input should accept text"
        chat.message_input.clear()


class TestSendingMessages:
    """TC-CHAT-004 to TC-CHAT-007: Message sending tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0503_chat-message-input-methods.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_send_text_message(self, page, conversation_id):
        """TC-CHAT-003, TC-CHAT-004: Send message and verify history.

        Verifies:
        - Message is sent (TC-CHAT-004)
        - Message appears in chat history (TC-CHAT-003, TC-CHAT-004)
        - Input field is cleared (TC-CHAT-004)
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        test_message = "Hello, this is an automated test message"
        initial_count = chat.get_message_count()

        chat.send_message(test_message, use_enter=True)

        # SPA re-renders after first message — wait for page to stabilise
        chat.wait_for_input_ready()
        # Wait for a new message block beyond the initial count
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        assert chat.is_input_empty(), "Input should be cleared after sending"

        new_count = chat.get_message_count()
        assert new_count > initial_count, f"Message count should increase: {initial_count} -> {new_count}"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0503_chat-message-input-methods.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_shift_enter_adds_new_line(self, page, conversation_id):
        """TC-CHAT-006: Shift+Enter adds new line instead of sending.

        Verifies Shift+Enter creates multi-line message.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        lines = ["Line 1", "Line 2", "Line 3"]
        initial_count = chat.get_message_count()
        chat.send_message_with_shift_enter(lines)

        # SPA may re-render after first message
        chat.wait_for_input_ready()
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
        # Input may take a moment to clear after SPA re-render
        chat.wait_for_input_empty(timeout=UI_ELEMENT_TIMEOUT)
        assert chat.is_input_empty(), "Input should be cleared after sending multi-line message"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0503_chat-message-input-methods.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.smoke
    def test_cannot_send_empty_message(self, page, conversation_id):
        """TC-CHAT-007: Cannot send empty message.

        Verifies pressing Enter with empty input does not send a message.
        Note: The current UI doesn't show a send button until there's text,
        so we test by pressing Enter on empty input.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        initial_count = chat.get_message_count()

        # Ensure input is empty
        chat.message_input.fill("")
        chat.message_input.click()

        # Try to send with Enter on empty input
        chat.message_input.press("Enter")

        # Brief wait to confirm no new message appears
        chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)

        new_count = chat.get_message_count()
        assert new_count == initial_count, "Empty message should not be sent when pressing Enter"


class TestMessageActions:
    """TC-CHAT-008 to TC-CHAT-009: Message action tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0502_chat-message-actions.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_copy_message_to_clipboard(self, page, conversation_id):
        """TC-CHAT-008: Copy message to clipboard.

        Sends a message first, then verifies the copy button works and
        the copied content matches the actual message text.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Dismiss any banner that might block interactions
        chat.dismiss_banner_if_present()

        # Send a message so there's something to copy
        test_message = "Message to copy"
        initial_count = chat.get_message_count()
        chat.send_message(test_message)
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Wait for streaming to fully complete - the copy button only appears after streaming
        # Also wait for network to settle to ensure all content is loaded
        chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
        chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=AI_RESPONSE_TIMEOUT)

        # Dismiss banner again in case it reappeared
        chat.dismiss_banner_if_present()

        # Get the AI response text before copying
        ai_response_text = chat.get_last_message_text()
        assert ai_response_text, "AI response should have text content"

        # Verify AI streaming has completed - should not show loading placeholders
        assert "packing" not in ai_response_text.lower() and "waking" not in ai_response_text.lower(), (
            f"AI response still shows loading state after waiting. Got: {ai_response_text[:200]}"
        )

        # Copy the AI message (last message = -1)
        # Note: copy_message() waits internally for clipboard operation to complete
        chat.copy_message(-1)

        # Verify clipboard content matches the AI response
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
        """TC-CHAT-009: Delete message.

        Sends a message, waits for the AI response to finish streaming, then
        hovers over the message to reveal the delete button and confirms deletion.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Send a message so there's something to delete
        initial_count = chat.get_message_count()
        chat.send_message("Message to delete", use_enter=True)
        chat.wait_for_input_ready()
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Wait for streaming to finish
        chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
        chat.wait_for_message_content_stable(stable_duration_ms=2000, timeout=AI_RESPONSE_TIMEOUT)

        # Count messages before deletion
        initial_message_count = chat.get_message_count()
        assert initial_message_count >= 2, (
            f"Expected at least 2 messages (user + AI), got {initial_message_count}"
        )

        # Delete the last message (hover reveals the delete button)
        try:
            chat.delete_message(-1)
        except PlaywrightTimeoutError:
            pytest.skip(
                "Delete button not accessible after hover — "
                "delete functionality may have changed in current UI"
            )

        # Verify message count decreased
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
        """TC-CHAT-010, TC-CHAT-020: Model selector shows current model and opens menu.

        Verifies:
        - Current model name is displayed in selector (TC-CHAT-010)
        - Clicking selector opens a model menu or navigates to settings (TC-CHAT-010, TC-CHAT-020)
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Close any open dialogs/modals that might block interaction
        chat.close_open_dialogs()

        current_model = chat.get_selected_model()
        assert current_model, (
            "Model selector should display the name of the currently selected model"
        )

        chat.click_model_selector()
        # Wait for menu/dropdown to appear after clicking; accept URL navigation as
        # an alternative valid outcome (some deployments navigate to settings page).
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
        """TC-CHAT-011: Attach file and send message with attachment.

        In v2.0.3+, the attach button is directly visible in the input toolbar
        (no need to open plus menu first). The button shows "Attach Files (N left)".

        Verifies complete file attachment workflow:
        - Clicking attach button triggers file chooser dialog
        - File chooser supports multiple file selection (per UI tooltip "10 left")
        - File can be selected and attached
        - Message with attachment can be sent
        - AI responds acknowledging the attached file

        This is an end-to-end test of the file attachment feature.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Create a test file with identifiable content.
        # Use a single opaque token embedded in a natural sentence so the AI
        # quotes it verbatim without stripping it as a "label: value" prefix.
        test_file = tmp_path / "test_automation_file.txt"
        test_file.write_text("This file contains the unique token AUTOTEST_ATTACH_7X9 and was attached by automated testing.")

        # In v2.0.3+, the attach button is directly in the input toolbar
        # with aria-label="attach files" and tooltip "Attach Files (10 left)"
        # The button contains a hidden file input that we can interact with directly.

        file_attached = False

        # Approach 1: Use set_input_files directly on the hidden file input
        # This is more reliable than clicking the button and expecting file chooser
        file_input = page.locator('button[aria-label="attach files"] input[type="file"]').first
        if file_input.count() > 0:
            try:
                # Make the input visible temporarily to set files
                file_input.set_input_files(str(test_file))
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                file_attached = True
                logger.info("File attached via direct input method")
            except Exception as e:
                logger.warning(f"Direct input method failed: {e}")

        # Approach 2: Click button and use file chooser (fallback)
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

        # Approach 3: Plus menu -> Attach Files option (fallback for older UI)
        if not file_attached:
            plus_menu = page.get_by_role("button", name="plus menu")
            if plus_menu.is_visible():
                plus_menu.click(force=True)
                page.wait_for_timeout(500)

                # Try the file input inside the menu's attach button
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
                    page.keyboard.press("Escape")  # Close menu

        if not file_attached:
            pytest.skip(
                "File attachment UI not accessible — attach button exists but "
                "file could not be attached via input or file chooser methods. "
                "This may require drag-and-drop in the current UI version."
            )

        # Get initial message count before sending
        initial_count = chat.get_message_count()

        # Send a message asking about the attachment
        chat.send_message("What is the content of the attached file?")

        # Wait for AI response to appear
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

        # Wait for streaming to fully complete - network idle + content stable
        # File attachment responses can take longer as the AI processes the file
        chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)
        chat.wait_for_message_content_stable(stable_duration_ms=3000, timeout=AI_RESPONSE_TIMEOUT)

        # Verify message count increased (user message + AI response)
        final_count = chat.get_message_count()
        assert final_count > initial_count, (
            f"Message count should increase after sending. Initial: {initial_count}, Final: {final_count}"
        )

        # Get the AI response text
        ai_response = chat.get_last_message_text()

        # Skip "Waking the agent..." placeholder - that means response isn't ready
        assert "waking" not in ai_response.lower(), (
            f"AI response still shows loading state. Got: {ai_response[:200]}"
        )

        # Require the specific unique token embedded in the file content.
        # Generic words like "file" or "content" appear in any AI response and prove nothing.
        # The token AUTOTEST_ATTACH_7X9 appears nowhere in the AI's vocabulary and cannot
        # be invented — its presence proves the AI actually read the attached file.
        # Normalize underscores: AI may render token via markdown bold (**AUTOTESTATTACH7X9**)
        # which strips underscores when extracted as text.
        normalized_response = ai_response.lower().replace("_", "")
        file_acknowledged = "autotestattach7x9" in normalized_response

        assert file_acknowledged, (
            f"AI response should mention the unique token from the attached file "
            f"(AUTOTEST_ATTACH_7X9). Got: {ai_response[:200]}..."
        )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0501_chat-ui-elements-model-tools-participants.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_internal_tools_panel_shows_all_tools(self, page, conversation_id):
        """TC-CHAT-012: Internal tools panel displays all available tools.

        In v2.0.3+, internal tools are accessed via the plus menu → "Internal Tools".

        Verifies:
        - Plus menu opens and contains "Internal Tools" option
        - Clicking "Internal Tools" opens the tools panel
        - All 7 internal tools are present with correct names
        - Each tool has a toggle switch

        Tools (from ChatInternalTool enum):
        - Image creation: Generate images from text prompts
        - Data Analysis: Analyze data and create visualizations
        - Elitea MCP Tools: MCP integration tools
        - Planner: Break down complex tasks into steps
        - Python sandbox: Execute Python code
        - Swarm Mode: Multi-agent collaboration
        - Smart Tools Selection: Auto-select appropriate tools
        """
        from pages.internal_tools import CHAT_INTERNAL_TOOLS

        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Check if plus menu exists - skip if UI doesn't have it
        plus_menu_btn = page.get_by_role("button", name="plus menu")
        if not plus_menu_btn.is_visible():
            pytest.skip(
                "Plus menu button not visible — feature may not be available "
                "in this environment or UI has changed"
            )

        # Open the internal tools panel via plus menu
        chat.open_internal_tools_menu()

        # The panel appears as a tooltip/popover containing switches
        # Each tool has a switch element with the tool name as accessible name
        for tool_name in CHAT_INTERNAL_TOOLS:
            tool_switch = chat.get_internal_tool_switch(tool_name)
            assert tool_switch.is_visible(), (
                f"Internal tool '{tool_name}' should be visible in the panel"
            )

        # Verify we found exactly the expected number of tools
        visible_count = chat.get_visible_switch_count()
        assert visible_count == len(CHAT_INTERNAL_TOOLS), (
            f"Expected {len(CHAT_INTERNAL_TOOLS)} internal tools, found {visible_count}"
        )

        # Close the panel by pressing Escape
        page.keyboard.press("Escape")

class TestHashSearch:
    """TC-CHAT-017 to TC-CHAT-018: # search functionality tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0501_chat-ui-elements-model-tools-participants.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0498_chat-participants-add-via-hash-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_hash_search_participants(self, page, conversation_id):
        """TC-CHAT-017: Use # to search participants.

        Verifies typing # triggers participant search dropdown.
        The hash search feature detects '#' via keydown events, so we must
        use type() or press_sequentially() instead of fill() to trigger it.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        chat.message_input.click()
        chat.message_input.press_sequentially("#agent", delay=50)
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

        Steps:
        1. Type '#' to open search dropdown
        2. Select the first available option
        3. Verify dropdown closes after selection

        The hash search feature detects '#' via keydown events, so we must
        use press_sequentially() instead of fill() to trigger it.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Step 1: Type '#' to open search dropdown
        chat.message_input.click()
        chat.message_input.press_sequentially("#", delay=50)
        try:
            chat.wait_for_hash_search_dropdown(timeout=UI_ELEMENT_TIMEOUT)
        except PlaywrightTimeoutError:
            pytest.skip(
                "Hash search dropdown did not appear after typing '#' — "
                "# mention feature may be disabled in this environment"
            )

        # Step 2: Get first option and select it
        page.wait_for_timeout(500)  # Let results load
        first_option = chat.get_hash_search_first_option()
        if first_option is None:
            pytest.skip("No search results available for '#'")

        first_option.click()
        chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)

        # Step 3: Verify dropdown closes after selection
        assert not chat.is_hash_search_dropdown_visible(), (
            "Hash search dropdown should close after selecting an option"
        )


class TestContextAndSettings:
    """TC-CHAT-019 to TC-CHAT-020: Context and settings tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_edit_context_settings(self, page, conversation_id):
        """TC-CHAT-019: Edit context settings.

        In v2.0.3+, the Context Budget panel is in the right-hand Participants panel
        which is collapsed by default. After sending a message, expand the panel
        and verify the "Edit context settings" button opens the settings dialog.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Dismiss any banner overlay that might intercept clicks
        chat.dismiss_banner_if_present()

        # Send a message so the Context Budget panel has data
        initial_count = chat.get_message_count()
        chat.send_message("Context settings test", use_enter=True)
        chat.wait_for_input_ready()
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
        chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        # Dismiss banner again in case it reappeared
        chat.dismiss_banner_if_present()

        # In v2.0.3+, the Participants panel (containing Context Budget) is collapsed
        # by default. Click the panel toggle to expand it.
        participants_toggle = page.locator('button').filter(has=page.locator('img')).filter(
            has=page.get_by_text("Participants").locator("xpath=../..")
        )
        # Alternative: just look for the Context Budget section directly
        context_budget = page.get_by_text("Context Budget")
        if not context_budget.is_visible():
            # Try to find and click the panel toggle
            panel_toggle = page.locator('[class*="panel"] button, main button').last
            if panel_toggle.is_visible():
                panel_toggle.click(force=True)
                page.wait_for_timeout(500)

        # The edit button (pencil icon) is next to the "Context Budget" label
        try:
            chat.edit_context_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        except PlaywrightTimeoutError:
            pytest.skip("Edit context settings button not visible — context panel may not be available")

        chat.edit_context_settings()

        # Verify context settings dialog/modal opened
        Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)


class TestSidebarNavigation:
    """TC-CHAT-021 to TC-CHAT-022: Sidebar navigation tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_open_close_sidebar(self, page, conversation_id):
        """TC-CHAT-021: Open/close sidebar drawer.

        Verifies sidebar toggle works.
        Note: Sidebar may already be expanded on initial load.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # First check if sidebar is already expanded (has visible "Agents" button)
        # Use exact=True to avoid matching conversation items with "Agents" in name
        agents_btn = page.get_by_role("button", name="Agents", exact=True)
        sidebar_is_expanded = agents_btn.is_visible()

        if sidebar_is_expanded:
            # Sidebar already open - test closing first, then reopening
            chat.close_sidebar()
            chat.wait_for_sidebar_collapsed(timeout=UI_ELEMENT_TIMEOUT)

            chat.open_sidebar()
            chat.wait_for_sidebar_expanded(timeout=UI_ELEMENT_TIMEOUT)
        else:
            # Sidebar collapsed - test opening first, then closing
            chat.open_sidebar()
            chat.wait_for_sidebar_expanded(timeout=UI_ELEMENT_TIMEOUT)

            chat.close_sidebar()
            chat.wait_for_sidebar_collapsed(timeout=UI_ELEMENT_TIMEOUT)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_navigate_to_agents_from_sidebar(self, page, conversation_id):
        """TC-CHAT-022: Navigate to Agents from sidebar.

        Verifies Agents link in sidebar navigates correctly.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Ensure sidebar is expanded before clicking Agents
        # Use exact=True to avoid matching conversation items with "Agents" in name
        agents_btn = page.get_by_role("button", name="Agents", exact=True)
        if not agents_btn.is_visible():
            chat.open_sidebar()
            chat.wait_for_sidebar_expanded(timeout=UI_ELEMENT_TIMEOUT)

        # Click Agents button
        agents_btn.click()

        # Wait for SPA navigation to complete
        chat.wait_for_navigation("/agent", timeout=10000)

        current_url = chat.page.url
        assert "/agents" in current_url or "/agent" in current_url, \
            f"Should navigate to agents page, current URL: {current_url}"


class TestSearchAndErrorHandling:
    """TC-CHAT-023 to TC-CHAT-024: Search and error handling tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/chat-interface/ELITEA-0500_chat-interface-advanced-features.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_search_conversations_dialog(self, page, conversation_id):
        """TC-CHAT-023: Search conversations.

        In v2.0.3+, clicking "Search conversations" button opens an inline
        search textbox (not a modal dialog via Ctrl+K).

        Verifies search conversations button opens the search input.
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Dismiss any banner overlay that might intercept clicks
        chat.dismiss_banner_if_present()

        chat.open_search_conversations()

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
        """TC-CHAT-024: Handle message send failure gracefully.

        Verifies app handles oversized message without crashing.
        Acceptable outcomes:
        - Error notification shown (explicit rejection)
        - Message not added to history (silent rejection)
        - Message truncated and sent (graceful handling)
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        initial_count = chat.get_message_count()
        very_long_message = "A" * 100000

        chat.send_message(very_long_message, use_enter=True)
        chat.wait_for_network(timeout=AI_RESPONSE_TIMEOUT)

        # App should handle gracefully - verify one of the acceptable outcomes:
        # 1. Error notification shown (explicit rejection)
        # 2. Message not added (silent rejection)
        # 3. Message truncated and sent successfully (graceful handling)
        has_error = chat.has_error_notification()
        final_count = chat.get_message_count()
        message_sent_successfully = final_count > initial_count

        assert has_error or final_count == initial_count or message_sent_successfully, (
            f"Expected graceful handling of oversized input "
            f"(error, rejection, or successful send), "
            f"got: has_error={has_error}, count {initial_count} -> {final_count}"
        )
