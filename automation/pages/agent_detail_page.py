"""Agent Detail Page - View and manage individual agent.

Handles: /app/agents/all/{id}
- View agent information (ID, version)
- Manage toolkits (add/remove)
- Internal tools (toggle switches)
- Embedded chat panel
- Actions menu (delete, export)
- Edit agent (includes form from AgentFormPage)
"""

import logging
import time
from urllib.parse import urlparse
from playwright.sync_api import Page, Locator

from .base_page import BasePage
from .agent_form_page import AgentFormPage
from .locator_descriptor import LocatorDescriptor
from .internal_tools import InternalTool, get_tool_testid
from components.mui import Dialog, Popper
from utils.actions import action


logger = logging.getLogger("elitea.pages.agent_detail")


class AgentDetailPage(AgentFormPage):
    """Page object for agent detail/edit page.

    Inherits from AgentFormPage to reuse form filling functionality.
    Adds detail-specific operations like toolkits, chat, and actions menu.
    """

    # Tab locators
    configuration_tab = LocatorDescriptor(
        testid="agent-config-tab",
        fallback=lambda page: page.get_by_role("tab", name="Configuration"),
        description="Configuration tab"
    )

    history_tab = LocatorDescriptor(
        testid="agent-history-tab",
        fallback=lambda page: page.get_by_role("tab", name="History"),
        description="History tab"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to agent")
    def navigate(self, agent_id: int):
        """Navigate to a specific agent's detail page and wait until ready.

        Automatically waits for the page to fully load (Information section
        visible and Name field populated). For explicit waiting (e.g., after
        reload), use wait_for_page_load().

        Args:
            agent_id: The numeric agent ID.
        """
        super(AgentDetailPage, self).navigate(f"/app/agents/all/{agent_id}?viewMode=owner")
        self.wait_for_page_load()
        logger.info("Navigated to agent %d and page loaded", agent_id)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the agent detail/edit page to fully load.

        Waits for the INFORMATION section (which contains Agent ID) to appear
        and for the Name field to be populated. The MUI form loads the shell
        first and populates fields after the API call returns.
        """
        # Wait for the INFORMATION section heading to be visible
        self.page.get_by_role("heading", name="Information").wait_for(
            state="visible", timeout=timeout,
        )
        self.wait_for_network(timeout=10000)

        # Wait for the Name input to have a non-empty value
        self.page.wait_for_function(
            """() => {
                const input = document.querySelector('input#name');
                return input && input.value.length > 0;
            }""",
            timeout=timeout,
        )
        logger.info("Agent detail page loaded")

    # ------------------------------------------------------------------
    # Page verification
    # ------------------------------------------------------------------

    def verify_on_detail_page(self, expected_agent_id: int = None):
        """Verify we're on an agent detail page (not create page).

        Args:
            expected_agent_id: Optional agent ID to verify in URL
        """
        url_path = self.page.url
        assert "/app/agents/all/" in url_path, f"Not on detail page: {url_path}"
        assert "/create" not in url_path, f"Still on create page: {url_path}"

        if expected_agent_id:
            assert f"/{expected_agent_id}" in url_path, (
                f"URL doesn't contain agent ID {expected_agent_id}: {url_path}"
            )

        logger.info(f"Verified on detail page: {url_path}")

    def verify_tabs_visible(self):
        """Verify Configuration and History tabs are visible.

        Uses global timeout (10s) configured in conftest.py.
        """
        self.configuration_tab.wait_for(state="visible")
        self.history_tab.wait_for(state="visible")
        logger.info("Verified tabs are visible")

    # ------------------------------------------------------------------
    # Agent information
    # ------------------------------------------------------------------

    def get_agent_id(self) -> str:
        """Read the Agent ID from the Information section.

        Returns:
            Agent ID as string.
        """
        btn = self.page.get_by_role("button", name="Copy ID")
        return btn.text_content().strip()

    def get_version_id(self) -> str:
        """Read the Version ID from the Information section.

        Returns:
            Version ID as string.
        """
        btn = self.page.get_by_role("button", name="Copy version ID")
        return btn.text_content().strip()

    # ------------------------------------------------------------------
    # Internal tools (switches)
    # ------------------------------------------------------------------

    def _get_tool_switch_locator(self, tool: InternalTool) -> Locator:
        """Get locator for an internal tool switch.

        Uses a robust strategy:
        1. Try data-testid if available (future-proof)
        2. Fall back to text-based locator with parent traversal

        Args:
            tool: The internal tool enum value.

        Returns:
            Locator for the tool's switch/checkbox element.
        """
        testid = get_tool_testid(tool)

        # Try testid first (future-proof when frontend adds data-testid)
        testid_locator = self.page.get_by_test_id(testid)
        if testid_locator.count() > 0:
            return testid_locator.first

        # Fallback: text-based locator
        # Strategy: Find text label, go to parent container, find switch within
        tool_label = self.page.locator(f'text="{tool.value}"').first

        # Try to find parent MUI FormControlLabel
        try:
            # Navigate up to find the FormControlLabel container
            container = tool_label.locator('xpath=ancestor::label[contains(@class, "MuiFormControlLabel")]').first
            if container.count() == 0:
                # Try broader search
                container = tool_label.locator('xpath=ancestor::div[contains(@class, "MuiFormControlLabel")]').first

            # Find the switch input within the container
            switch = container.locator('input[type="checkbox"], input[role="switch"]').first
            return switch
        except Exception:
            # Last resort: find any nearby switch
            return self.page.locator(f'text="{tool.value}"').locator('..').locator('input[type="checkbox"]').first

    def _get_tool_label_locator(self, tool: InternalTool) -> Locator:
        """Get locator for an internal tool's clickable label area.

        Args:
            tool: The internal tool enum value.

        Returns:
            Locator for the tool's label (for clicking to toggle).
        """
        # Strategy 1: Try to find within Toolkits section for better specificity
        # This prevents matching unrelated text elsewhere on the page
        toolkits_section = self.page.locator('div:has(> button:has-text("Toolkits"))')

        # Try MUI FormControlLabel within toolkits section
        mui_label = toolkits_section.locator(f'div.MuiFormControlLabel-root:has-text("{tool.value}")')
        if mui_label.count() > 0:
            return mui_label.first

        # Try generic label within toolkits section
        label = toolkits_section.locator(f'label:has-text("{tool.value}")')
        if label.count() > 0:
            return label.first

        # Fallback: text locator within toolkits section
        text_loc = toolkits_section.locator(f'text="{tool.value}"')
        if text_loc.count() > 0:
            return text_loc.first

        # Last resort: page-wide search
        return self.page.locator(f'text="{tool.value}"').first

    def is_tool_enabled(self, tool: InternalTool) -> bool:
        """Check if an internal tool switch is checked.

        Args:
            tool: The internal tool enum value (e.g. InternalTool.SMART_TOOLS).

        Returns:
            True if tool is enabled, False otherwise.

        Example:
            >>> from pages.internal_tools import InternalTool
            >>> detail_page.is_tool_enabled(InternalTool.PYTHON_SANDBOX)
            True
        """
        try:
            # Try to find the checkbox near the tool text
            # Use multiple strategies since MUI structure can vary

            # Strategy 1: Direct sibling or parent search
            text_loc = self.page.locator(f'text="{tool.value}"').first

            # Try finding checkbox in parent container
            try:
                switch = text_loc.locator('xpath=ancestor::*[1]').locator('input[type="checkbox"]').first
                if switch.count() > 0:
                    return switch.is_checked(timeout=1000)
            except Exception:
                pass

            # Strategy 2: Look for checkbox near the text (within 2 parent levels)
            try:
                switch = text_loc.locator('xpath=ancestor::*[2]').locator('input[type="checkbox"]').first
                if switch.count() > 0:
                    return switch.is_checked(timeout=1000)
            except Exception:
                pass

            # Strategy 3: Use CSS selector to find nearby switch
            try:
                # Find any checkbox that's a sibling or in nearby container
                container = self.page.locator(f':has-text("{tool.value}")').locator('input[type="checkbox"]').first
                return container.is_checked(timeout=1000)
            except Exception:
                pass

            logger.warning("Could not find checkbox for tool: %s", tool.value)
            return False

        except Exception as e:
            logger.warning("Failed to check if tool %s is enabled: %s", tool.value, e)
            return False

    @action("Toggle internal tool")
    def toggle_tool(self, tool: InternalTool, wait_for_update: bool = True, timeout: int = 2000):
        """Toggle an internal tool switch by clicking its label area.

        Args:
            tool: The internal tool enum value (e.g. InternalTool.SMART_TOOLS).
            wait_for_update: Wait for UI to update after toggle
            timeout: Maximum wait time in ms

        Example:
            >>> from pages.internal_tools import InternalTool
            >>> detail_page.toggle_tool(InternalTool.PYTHON_SANDBOX)
        """
        logger.info("Toggling tool: %s", tool.value)

        # Ensure toolkits section is visible and scrolled into view
        self.ensure_toolkits_section_visible()
        self.page.wait_for_timeout(500)  # Let scroll animation complete

        # Find the tool using the proper locator method
        tool_locator = self._get_tool_label_locator(tool)
        tool_locator.wait_for(state="visible", timeout=timeout)
        tool_locator.click(force=True)

        if wait_for_update:
            self.page.wait_for_timeout(1000)  # UI animation
            self.wait_for_network(timeout=1000)

        logger.info(f"Toggled tool: {tool.value}")

    @action("Enable internal tool")
    def enable_tool(self, tool: InternalTool):
        """Enable an internal tool if it's not already enabled.

        Args:
            tool: The internal tool enum value.
        """
        if not self.is_tool_enabled(tool):
            self.toggle_tool(tool)
            logger.info("Enabled tool: %s", tool.value)

    @action("Disable internal tool")
    def disable_tool(self, tool: InternalTool):
        """Disable an internal tool if it's currently enabled.

        Args:
            tool: The internal tool enum value.
        """
        if self.is_tool_enabled(tool):
            self.toggle_tool(tool)
            logger.info("Disabled tool: %s", tool.value)

    def ensure_toolkits_section_visible(self, timeout: int = 5000):
        """Scroll to toolkits section and wait for it to be visible.

        Automatically scrolls to the Toolkits heading and waits for
        the section to be visible with animation settle time.

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            Locator for the Toolkits heading
        """
        toolkits_heading = self.page.get_by_role("button", name="Toolkits")
        toolkits_heading.scroll_into_view_if_needed()
        toolkits_heading.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(500)  # Animation settle
        logger.debug("Toolkits section scrolled into view")
        return toolkits_heading

    def get_available_tools(self) -> list[InternalTool]:
        """Get list of internal tools that are visible on the page.

        Automatically scrolls to the Toolkits section if needed.
        Only looks for tools within the Toolkits section to avoid false positives
        from text appearing elsewhere on the page.

        Returns:
            List of InternalTool enum values for tools present in the UI.

        Example:
            >>> tools = detail_page.get_available_tools()
            >>> assert InternalTool.PYTHON_SANDBOX in tools
        """
        # Ensure toolkits section is visible
        self.ensure_toolkits_section_visible()

        available = []

        for tool in InternalTool:
            try:
                # Look for the tool text on the page
                text_locator = self.page.locator(f'text="{tool.value}"')

                if text_locator.count() > 0:
                    first_match = text_locator.first

                    # Check if it's visible
                    if not first_match.is_visible(timeout=1000):
                        continue

                    # Check if it's in a reasonable Y position (below 500px)
                    # to filter out text in headers/banners
                    try:
                        box = first_match.bounding_box()
                        if box and box['y'] > 500:  # Likely in content area, not header
                            available.append(tool)
                    except Exception:
                        # If we can't get bounding box, include it anyway
                        available.append(tool)

            except Exception as e:
                logger.debug("Tool %s not found: %s", tool.value, e)
                continue

        logger.info("Available tools: %s", [t.value for t in available])
        return available

    # ------------------------------------------------------------------
    # External toolkit management
    # ------------------------------------------------------------------

    @action("Add toolkit")
    def add_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Add an external toolkit to the agent via the Toolkits section.

        Scrolls to the Toolkits section, clicks the "+ Toolkit" button,
        searches for the toolkit in the popper dropdown, and selects it.

        Note: The popper dropdown displays toolkit names with spaces removed
        (e.g. "My Toolkit" → "MyToolkit"), so the match is done against
        the space-stripped name.

        Args:
            toolkit_name: Name (or prefix) of the toolkit to add.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Adding toolkit '%s' to agent", toolkit_name)

        # Ensure the Toolkits section is expanded and visible
        toolkits_header = self.page.get_by_role("button", name="Toolkits")
        toolkits_header.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)

        # Click the "+ Toolkit" button to open the popper dropdown
        add_btn = self.page.get_by_role("button", name="Toolkit", exact=True)
        add_btn.wait_for(state="visible", timeout=timeout)
        add_btn.click(force=True)
        self.page.wait_for_timeout(1000)

        # Wait for the popper to appear and search for the toolkit
        popper = Popper.wait_for(self.page, timeout=timeout)

        # Use the search input to filter toolkits
        search_input = popper.locator('input[placeholder*="Search"]')
        if search_input.count() > 0 and search_input.first.is_visible():
            Popper.search(popper, toolkit_name[:20], self.page)

        # The dropdown strips spaces from names, so match against the
        # space-stripped version of the toolkit name
        name_no_spaces = toolkit_name.replace(" ", "")
        Popper.select_menuitem(popper, name_no_spaces, self.page, timeout=timeout)
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("Toolkit '%s' added to agent", toolkit_name)

    def is_toolkit_attached(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check whether a toolkit is attached to the agent.

        Toolkit cards may display the name with or without spaces, so
        both variants are checked.

        Args:
            toolkit_name: Toolkit name to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if toolkit is attached, False otherwise.
        """
        name_no_spaces = toolkit_name.replace(" ", "")
        try:
            self.page.locator(
                f':text("{toolkit_name}"), :text("{name_no_spaces}")'
            ).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    @action("Remove toolkit")
    def remove_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Remove a toolkit from the agent configuration.

        Hovers over the toolkit card to reveal action buttons, then clicks
        the delete button.

        Args:
            toolkit_name: Name of the toolkit to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing toolkit '%s' from agent", toolkit_name)

        # Find the toolkit card by its name text (may be space-stripped)
        name_no_spaces = toolkit_name.replace(" ", "")
        toolkit_text = self.page.locator(
            f':text("{toolkit_name}"), :text("{name_no_spaces}")'
        ).first
        toolkit_text.wait_for(state="visible", timeout=timeout)
        toolkit_text.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)

        # Hover over the text element itself — hover effect propagates to the
        # card container and reveals the hidden delete button.
        toolkit_text.hover()
        self.page.wait_for_timeout(500)

        # Find the toolkit card container (ancestor with data-testid or class)
        # and scope the delete button search to it
        toolkit_card = toolkit_text.locator("xpath=ancestor::div[contains(@class, 'MuiCard') or contains(@class, 'card')]").first
        if toolkit_card.count() == 0:
            # Fallback: use a broader ancestor search
            toolkit_card = toolkit_text.locator("xpath=ancestor::div[.//button[@aria-label='delete tool']]").first
        
        # Click the delete button scoped to this toolkit card
        delete_btn = toolkit_card.locator('button[aria-label="delete tool"]').first
        delete_btn.wait_for(state="visible", timeout=5000)
        delete_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Handle the "Remove toolkit?" confirmation dialog
        dialog = Dialog.wait_for(self.page)
        Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")
        self.page.wait_for_timeout(500)

        self.wait_for_network(timeout=timeout)
        logger.info("Toolkit '%s' removed from agent", toolkit_name)

    # ------------------------------------------------------------------
    # Embedded chat (right panel)
    # ------------------------------------------------------------------

    def _embedded_chat_messages(self):
        """Return a locator for all message LI elements in the embedded chat.

        The embedded chat is in the right panel of the agent detail page.
        Messages are li.MuiListItem-root inside ul.MuiList-root.
        """
        return self.page.locator('ul.MuiList-root li.MuiListItem-root')

    def get_chat_message_count(self) -> int:
        """Return the current number of messages visible in the embedded chat.

        Use this before sending a message to capture the baseline count,
        then pass the count to ``wait_for_chat_response(initial_count=...)``.

        Returns:
            Integer count of message list items currently in the chat.
        """
        return self._embedded_chat_messages().count()

    @action("Send embedded chat message")
    def send_chat_message(self, message: str, timeout: int = 10000):
        """Type and send a message in the embedded chat panel.

        Args:
            message: The message text to send.
            timeout: Maximum wait time for elements.
        """
        logger.info("Sending message in embedded chat: %s", message[:60])
        chat_input = self.page.get_by_role("textbox", name="Type your message.")
        chat_input.wait_for(state="visible", timeout=timeout)
        chat_input.fill(message)
        self.page.wait_for_timeout(300)

        send_btn = self.page.get_by_role("button", name="send your question")
        send_btn.wait_for(state="visible", timeout=timeout)
        send_btn.click()
        logger.info("Message sent in embedded chat")

    def wait_for_chat_response(
        self,
        initial_count: int = 0,
        stable_duration_ms: int = 3000,
        timeout: int = 60000,
    ):
        """Wait for the AI response in the embedded chat to stabilize.

        Waits for new messages to appear beyond initial_count, then waits
        for the last message's text content to stop changing for
        stable_duration_ms.

        Args:
            initial_count: Number of messages before sending.
            stable_duration_ms: Content must be unchanged for this long (ms).
            timeout: Overall timeout in milliseconds.
        """
        logger.info(
            "Waiting for embedded chat response (initial_count=%d, stable=%dms, timeout=%dms)",
            initial_count, stable_duration_ms, timeout,
        )
        messages = self._embedded_chat_messages()
        deadline = time.time() + timeout / 1000

        # Wait for at least one new message beyond initial_count
        while time.time() < deadline:
            if messages.count() > initial_count:
                break
            self.page.wait_for_timeout(500)

        # Wait for the last AI message to have a Delete button (= response complete)
        ai_msg = messages.last
        try:
            ai_msg.locator('[aria-label="Delete"]').wait_for(
                state="visible",
                timeout=max(1000, int((deadline - time.time()) * 1000)),
            )
        except Exception:
            pass  # Fall through to content-stable check

        # Wait for content to stabilize
        last_content = ""
        stable_start = time.time()

        while time.time() < deadline:
            try:
                current = ai_msg.text_content() or ""
            except Exception:
                current = ""

            if current and current == last_content:
                if (time.time() - stable_start) * 1000 >= stable_duration_ms:
                    logger.info("Embedded chat response stabilized (%d chars)", len(current))
                    return
            else:
                last_content = current
                stable_start = time.time()

            self.page.wait_for_timeout(500)

        logger.warning("Embedded chat response did not stabilize within timeout")

    def get_last_chat_message(self) -> str:
        """Return the text content of the last AI message in embedded chat.

        The AI response text is inside the last li.MuiListItem-root.
        Extracts text from the response container.

        Returns:
            Last message text as string.
        """
        messages = self._embedded_chat_messages()
        if messages.count() == 0:
            return ""

        ai_msg = messages.last
        # Try to get text from the response content div
        response_div = ai_msg.locator('div.css-xn5i2e')
        if response_div.count() > 0:
            text = response_div.text_content() or ""
            return text.strip()

        # Fallback: get all text from the message
        text = ai_msg.text_content() or ""
        return text.strip()

    # ------------------------------------------------------------------
    # Actions menu (three-dot menu)
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the three-dot actions menu on the agent detail page.

        Uses JavaScript click to bypass MUI overlay interception.
        The menu button has aria-haspopup="true" and is near the
        Save/Discard buttons in the header.
        """
        logger.info("Opening actions menu")
        menu_btn = self.page.locator('button[aria-haspopup="true"]').last
        menu_btn.evaluate("el => el.click()")
        self.page.locator('[role="menu"]').wait_for(state="visible", timeout=5000)

    @action("Delete agent")
    def delete_agent_via_menu(self, timeout: int = 10000):
        """Delete the current agent via the three-dot menu.

        Opens the menu, clicks "Delete agent", types the agent name into
        the confirmation dialog, and clicks Delete.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting agent via menu")
        # Read the current agent name before opening the menu
        agent_name = self.get_name()

        self.open_actions_menu()
        self.page.get_by_role("menuitem", name="Delete agent").click()

        # Handle type-to-confirm dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)

        # Type the agent name into the confirmation input
        Dialog.type_to_confirm(dialog, agent_name)
        self.page.wait_for_timeout(300)

        # Click the Delete button
        Dialog.click_button(dialog, "Delete")
        self.wait_for_network(timeout=timeout)
        logger.info("Agent deleted via menu")

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    @action("Navigate back")
    def click_back_button(self, timeout: int = 5000):
        """Click the back arrow button on the agent detail page.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking back button")
        # The back button is the first button in the header bar
        back_btn = self.page.locator(
            'tablist:near(:text("Configuration"))'
        ).locator("..").locator("button").first
        back_btn.click()
        self.wait_for_network(timeout=timeout)
