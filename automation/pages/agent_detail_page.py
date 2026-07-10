"""Agent Detail Page - View and manage individual agent.

Handles: /agents/all/{id}
- View agent information (ID, version)
- Manage toolkits (add/remove)
- Internal tools (toggle switches)
- Embedded chat panel
- Actions menu (delete, export)
- Edit agent (includes form from AgentFormPage)
"""

import logging
import time
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

    # ===================================================================
    # LOCATORS - All element locators defined here for easy maintenance
    # ===================================================================

    # --- Information section ---
    information_section = LocatorDescriptor(testid="agent-information-section")
    copy_id_button = LocatorDescriptor(testid="copy-id")
    copy_version_id_button = LocatorDescriptor(testid="copy-version-id")

    # --- Toolkits section ---
    toolkits_section = LocatorDescriptor(testid="agent-toolkits-section")
    add_toolkit_button = LocatorDescriptor(testid="agent-add-toolkit-button")
    toolkit_card = LocatorDescriptor(testid="agent-toolkit-card")
    toolkit_delete_button = LocatorDescriptor(testid="agent-toolkit-delete-button")
    toolkit_search_input = LocatorDescriptor(testid="toolkit-search-input")
    toolkit_warning_banner = LocatorDescriptor(testid="credential-warning-banner")
    toolkit_reload_button = LocatorDescriptor(locator='#RefreshButton')
    toolkit_open_button = LocatorDescriptor(locator='#OpenInNewTabButton')

    # --- Selectors for scoped use (inside parent locators) ---
    TOOLKIT_BLOCKED_SELECTOR = '[aria-label*="blocked by your organization"]'
    TOOLKIT_TOOL_BLOCKED_SELECTOR = '[aria-label*="not available anymore"]'
    CHAT_MESSAGE_DELETE_SELECTOR = '[aria-label="Delete"]'
    CHAT_MESSAGE_ITEM_SELECTOR = '[data-testid="chat-message-item"]'
    CHAT_INPUT_FIELD_SELECTOR = 'textarea, input'
    CHAT_ARTIFACT_FILE_LIST_SELECTOR = '[data-testid="chat-artifact-file-list"]'
    CHAT_ARTIFACT_FILE_CARD_SELECTOR = '[data-testid="chat-artifact-file-card"]'
    CHAT_ANSWER_CONTENT_SELECTOR = '[data-testid="chat-answer-content"]'

    # --- Sensitive action authorization ---
    sensitive_action_panel = LocatorDescriptor(
        locator='text=/Sensitive Action Authorization Required/'
    )
    sensitive_action_authorize_button = LocatorDescriptor(
        locator='button:has-text("Authorize")'
    )

    # --- Embedded chat ---
    chat_message_list = LocatorDescriptor(testid="chat-message-list")
    chat_message_item = LocatorDescriptor(testid="chat-message-item")
    chat_input = LocatorDescriptor(testid="chat-input")
    chat_send_button = LocatorDescriptor(testid="chat-send-button")
    chat_delete_button = LocatorDescriptor(testid="chat-delete-button")
    chat_answer_content = LocatorDescriptor(testid="chat-answer-content")
    chat_artifact_file_list = LocatorDescriptor(testid="chat-artifact-file-list")
    chat_artifact_file_card = LocatorDescriptor(testid="chat-artifact-file-card")

    # --- Actions menu ---
    actions_menu_button = LocatorDescriptor(testid="agent-actions-menu-button")
    actions_menu = LocatorDescriptor(testid="agent-actions-menu")
    delete_agent_menuitem = LocatorDescriptor(testid="delete-agent-menuitem")

    # --- Navigation ---
    back_button = LocatorDescriptor(testid="back-button")

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
        super(AgentDetailPage, self).navigate(f"/agents/all/{agent_id}?viewMode=owner")
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
        self.information_section.wait_for(state="visible", timeout=timeout)

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
        assert "/agents/all/" in url_path, f"Not on detail page: {url_path}"
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
        return self.copy_id_button.text_content().strip()

    def get_version_id(self) -> str:
        """Read the Version ID from the Information section.

        Returns:
            Version ID as string.
        """
        return self.copy_version_id_button.text_content().strip()

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

        Automatically scrolls to the Toolkits section and waits for
        it to be visible with animation settle time.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.toolkits_section.scroll_into_view_if_needed()
        self.toolkits_section.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(500)  # Animation settle
        logger.debug("Toolkits section scrolled into view")

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
        self.ensure_toolkits_section_visible(timeout=timeout)

        # Click the "+ Toolkit" button to open dropdown
        self.add_toolkit_button.wait_for(state="visible", timeout=timeout)
        self.add_toolkit_button.click(force=True)
        self.page.wait_for_timeout(1000)

        # Wait for the popper to appear and search for the toolkit
        popper = Popper.wait_for(self.page, timeout=timeout)

        # Use the search input
        search_input = popper.locator(f'[data-testid="toolkit-search-input"]')
        if search_input.count() > 0 and search_input.is_visible():
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
        try:
            self.toolkit_card.filter(has_text=toolkit_name).first.wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    @action("Remove toolkit")
    def remove_toolkit(self, toolkit_name: str, timeout: int = 10000):
        """Remove a toolkit from the agent configuration.

        Hovers over the toolkit card to reveal the hidden delete button (CSS
        hover on cardHeader), clicks the delete button, confirms the dialog,
        and then waits until the toolkit card has actually disappeared from the
        DOM before returning.

        Args:
            toolkit_name: Name of the toolkit to remove.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Removing toolkit '%s' from agent", toolkit_name)

        # Find the toolkit card scoped to the toolkit name
        card = self.toolkit_card.filter(has_text=toolkit_name).first
        card.wait_for(state="visible", timeout=timeout)
        card.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)

        # Hover the card to reveal the delete button (CSS hover rule)
        card.hover()
        self.page.wait_for_timeout(500)

        # Locate the delete button inside this specific card
        delete_btn = card.locator('[data-testid="agent-toolkit-delete-button"]').first
        delete_btn.wait_for(state="visible", timeout=5000)
        delete_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Handle the "Remove toolkit?" confirmation dialog.
        dialog = Dialog.wait_for(self.page)
        Dialog.click_first_button(dialog, "Remove", "Confirm", "Delete")

        # Wait for network idle so the PATCH disassociate request completes
        # and any follow-up refetches settle.
        self.wait_for_network(timeout=timeout)

        # Explicitly wait for the toolkit card to disappear from the DOM.
        # This is necessary because React may defer state updates and re-renders
        # asynchronously after the network request completes, which can cause
        # is_toolkit_attached() to still find the card.  A 10-second timeout
        # gives React ample time to propagate the Formik state change.
        try:
            card.wait_for(state="hidden", timeout=10000)
        except Exception:
            # If the card is already gone, that's fine.
            pass

        logger.info("Toolkit '%s' removed from agent", toolkit_name)

    # ------------------------------------------------------------------
    # Toolkit credential indicators (Enhancement #5114, Bug #5183)
    # ------------------------------------------------------------------

    def _get_toolkit_card(self, toolkit_name: str, timeout: int = 10000):
        """Get the toolkit card element by name.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator for the toolkit item container.
        """
        card = self.toolkit_card.filter(has_text=toolkit_name).first
        card.wait_for(state="visible", timeout=timeout)
        return card

    def hover_toolkit_card(self, toolkit_name: str, timeout: int = 10000):
        """Hover over a toolkit card to reveal action icons.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.
        """
        self.ensure_toolkits_section_visible()
        toolkit_card = self._get_toolkit_card(toolkit_name, timeout)
        toolkit_card.hover()
        self.page.wait_for_timeout(500)

    def _get_warning_banner_locator(self):
        """Get locator for credential warning banner on page."""
        return self.toolkit_warning_banner

    def has_toolkit_status_indicator(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit shows credential status indicator (warning banner).

        Uses data-testid="credential-warning-banner" set on BannerMessage.jsx.
        The banner appears below the toolkit card for any validation error.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning banner is visible.
        """
        self.ensure_toolkits_section_visible()
        try:
            self._get_warning_banner_locator().first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_status_indicator_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the status indicator tooltip text for a toolkit.

        Returns the aria-label attribute of the credential-warning-banner element,
        which contains the validation error message text.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (error message text), or None if not found.
        """
        self.ensure_toolkits_section_visible()
        try:
            warning = self._get_warning_banner_locator().first
            warning.wait_for(state="visible", timeout=timeout)
            return warning.get_attribute("aria-label")
        except Exception:
            return None

    def has_toolkit_warning_message(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if warning message is displayed for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning message is visible.
        """
        return self.has_toolkit_status_indicator(toolkit_name, timeout)

    def get_toolkit_warning_message(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the warning message text (alias for get_toolkit_status_indicator_tooltip).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Warning message text, or None if not found.
        """
        return self.get_toolkit_status_indicator_tooltip(toolkit_name, timeout)

    def is_toolkit_blocked(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit shows 'blocked by your organization' indicator.

        Used to verify guardrails blocking is applied without pylon reload.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if blocked indicator is visible.
        """
        self.ensure_toolkits_section_visible()
        card = self.toolkit_card.filter(has_text=toolkit_name)
        blocked_indicator = card.locator(self.TOOLKIT_BLOCKED_SELECTOR)
        try:
            blocked_indicator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_tool_blocked_in_toolkit(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit shows 'Some tools are not available anymore' indicator.

        Used to verify guardrails tool blocking is applied without pylon reload.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if tool blocked indicator is visible.
        """
        self.ensure_toolkits_section_visible()
        card = self.toolkit_card.filter(has_text=toolkit_name)
        blocked_indicator = card.locator(self.TOOLKIT_TOOL_BLOCKED_SELECTOR)
        try:
            blocked_indicator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def has_toolkit_reload_button(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit card has reload button (visible on hover).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if reload button is visible.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_reload_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_reload_button_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the reload button tooltip text for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_reload_button.wait_for(state="visible", timeout=timeout)
            return self.toolkit_reload_button.get_attribute("aria-label")
        except Exception:
            return None

    def click_toolkit_reload_button(self, toolkit_name: str, timeout: int = 10000):
        """Click the reload button on a toolkit card.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        self.toolkit_reload_button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked reload button for toolkit '%s'", toolkit_name)

    def has_toolkit_open_in_new_tab_button(
        self, toolkit_name: str, timeout: int = 5000
    ) -> bool:
        """Check if toolkit card has open-in-new-tab button (visible on hover).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if open-in-new-tab button is visible.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_open_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_open_in_new_tab_button_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the open-in-new-tab button tooltip text for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        try:
            self.toolkit_open_button.wait_for(state="visible", timeout=timeout)
            return self.toolkit_open_button.get_attribute("aria-label")
        except Exception:
            return None

    def click_toolkit_open_in_new_tab(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str:
        """Click the open-in-new-tab button for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            URL of the new tab (toolkit detail page).
        """
        self.hover_toolkit_card(toolkit_name, timeout)
        self.toolkit_open_button.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            self.toolkit_open_button.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        url = new_page.url
        logger.info("Opened toolkit in new tab: %s", url)
        return url

    # ------------------------------------------------------------------
    # Embedded chat (right panel)
    # ------------------------------------------------------------------

    def _embedded_chat_messages(self):
        """Return a locator for all message items in the embedded chat.

        Scoped inside the chat message list container.
        """
        return self.chat_message_list.locator(self.CHAT_MESSAGE_ITEM_SELECTOR)

    def get_chat_message_count(self) -> int:
        """Return the current number of messages visible in the embedded chat.

        Use this before sending a message to capture the baseline count,
        then pass the count to ``wait_for_chat_response(initial_count=...)``.

        Returns:
            Integer count of message items currently in the chat.
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
        # chat_input contains the container; find the actual input element inside
        input_field = self.chat_input.locator(self.CHAT_INPUT_FIELD_SELECTOR).first
        input_field.wait_for(state="visible", timeout=timeout)
        input_field.fill(message)
        self.page.wait_for_timeout(300)

        self.chat_send_button.wait_for(state="visible", timeout=timeout)
        self.chat_send_button.click()
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
            ai_msg.locator(self.CHAT_MESSAGE_DELETE_SELECTOR).wait_for(
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

    def get_chat_artifact_file_names(self, timeout: int = 10000) -> list[str]:
        """Return the names of all artifact file cards shown in the last chat message.

        After an agent creates files via the Artifact toolkit, the chat
        response renders a ``data-testid="chat-artifact-file-list"`` container
        holding individual ``data-testid="chat-artifact-file-card"`` cards,
        each carrying a ``data-name`` attribute with the file name.

        LOCATOR: Scoped to the last ``chat-message-item`` to avoid picking up
        cards from previous turns.

        Args:
            timeout: Maximum wait time for the file-list container to appear.

        Returns:
            List of file name strings (e.g. ["report1.txt", "a.txt", ...]).
            Returns an empty list if no artifact cards are present.
        """
        last_msg = self._embedded_chat_messages().last
        try:
            file_list = last_msg.locator(self.CHAT_ARTIFACT_FILE_LIST_SELECTOR)
            file_list.wait_for(state="visible", timeout=timeout)
        except TimeoutError:
            logger.warning(
                "Timed out waiting for chat-artifact-file-list after %dms — "
                "artifact cards may not have rendered",
                timeout,
            )
            raise
        except Exception:
            logger.info("No chat-artifact-file-list found in last message")
            return []

        cards = file_list.locator(self.CHAT_ARTIFACT_FILE_CARD_SELECTOR)
        count = cards.count()
        names: list[str] = []
        for i in range(count):
            name = cards.nth(i).get_attribute("data-name") or ""
            if name:
                names.append(name)
        logger.info("Artifact file cards in last message (%d): %s", len(names), names)
        return names

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
        # Extract text from the answer content div
        response_div = ai_msg.locator(self.CHAT_ANSWER_CONTENT_SELECTOR)
        if response_div.count() > 0:
            text = response_div.text_content() or ""
            return text.strip()

        # Fallback: get all text from the message
        text = ai_msg.text_content() or ""
        return text.strip()

    def wait_for_sensitive_action_authorization(
        self, timeout: int = 30000, click_authorize: bool = True
    ) -> bool:
        """Wait for the Sensitive Action Authorization panel to appear.

        This panel appears when an agent tries to call a tool that is marked
        as sensitive in Admin UI Guardrails configuration.

        Args:
            timeout: Maximum wait time in milliseconds.
            click_authorize: If True, clicks the Authorize button when panel appears.

        Returns:
            True if the authorization panel appeared, False otherwise.
        """
        logger.info("Waiting for Sensitive Action Authorization panel")
        try:
            self.sensitive_action_panel.wait_for(state="visible", timeout=timeout)
            logger.info("Sensitive Action Authorization panel appeared")

            if click_authorize:
                self.sensitive_action_authorize_button.first.click()
                self.page.wait_for_timeout(2000)
                logger.info("Clicked Authorize button")

            return True
        except Exception:
            logger.warning("Sensitive Action Authorization panel did NOT appear within %dms", timeout)
            return False

    # ------------------------------------------------------------------
    # Actions menu (three-dot menu)
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the three-dot actions menu on the agent detail page.

        Uses JavaScript click to bypass MUI overlay interception.
        """
        logger.info("Opening actions menu")
        self.actions_menu_button.evaluate("el => el.click()")
        self.actions_menu.wait_for(state="visible", timeout=5000)

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
        self.delete_agent_menuitem.click()

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
        self.back_button.click()
        self.wait_for_network(timeout=timeout)
