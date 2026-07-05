"""Guardrails Admin configuration page object.

Handles interactions with the Admin UI Guardrails configuration page
for testing blocked toolkits, blocked tools, and sensitive action tools.

URL: Admin UI → Configuration → Guardrails

Page Structure:
- Guardrails sidebar item
- Accordion: "Blocked Toolkits & Tools" (2 settings)
    - Blocked Toolkits: "Type to search and filter..." input + chips
    - Blocked Tools: toolkit blocks with tools, "Add toolkit name..." + "+ Add"
- Accordion: "Sensitive Actions" (3 settings)
    - Sensitive Action Tools: toolkit blocks (artifact, github, etc.)
      each with input + tool chips
    - "Add toolkit name..." + "+ Add" at bottom
- Footer: "Discard" and "Save" buttons
"""

import logging
from playwright.sync_api import Page
from .base_page import BasePage
from utils.actions import action
from config import settings

logger = logging.getLogger("elitea.pages.guardrails_admin")


class GuardrailsAdminPage(BasePage):
    """Page object for Admin UI Guardrails configuration.

    Handles:
    - Navigation to Guardrails configuration page
    - Expanding/collapsing accordion sections
    - Adding/removing blocked toolkits
    - Adding/removing blocked tools
    - Adding/removing sensitive action tools
    - Verifying UI indicators (reload badges, banners)

    URL: /admin/app/configuration#guardrails
    """

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to Guardrails configuration")
    def navigate_to_guardrails(self):
        """Navigate to Admin UI Guardrails configuration page."""
        logger.info("Navigating to Guardrails configuration")
        url = f"{settings.elitea_url}/admin/app/configuration#guardrails"
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle", timeout=30000)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for Guardrails page to fully load."""
        self.wait_for_network(timeout=timeout)
        # Wait for Guardrails sidebar item to be visible
        self.page.locator('text="Guardrails"').first.wait_for(state="visible", timeout=timeout)
        logger.info("Guardrails page loaded")

    # ------------------------------------------------------------------
    # Accordion sections
    # ------------------------------------------------------------------

    def _expand_blocked_section(self, timeout: int = 5000):
        """Expand the 'Blocked Toolkits & Tools' accordion if collapsed."""
        accordion_header = self.page.locator('text="Blocked Toolkits & Tools"').first
        accordion_header.wait_for(state="visible", timeout=timeout)

        # Check if already expanded by looking for "Blocked Toolkits" subsection text
        blocked_toolkits_text = self.page.locator('text="Blocked Toolkits"').first
        try:
            blocked_toolkits_text.wait_for(state="visible", timeout=1000)
            logger.debug("Blocked section already expanded")
        except Exception:
            logger.info("Expanding 'Blocked Toolkits & Tools' accordion")
            accordion_header.click()
            self.page.wait_for_timeout(500)
            blocked_toolkits_text.wait_for(state="visible", timeout=timeout)

    def _expand_sensitive_section(self, timeout: int = 5000):
        """Expand the 'Sensitive Actions' accordion if collapsed."""
        accordion_header = self.page.locator('text="Sensitive Actions"').first
        accordion_header.wait_for(state="visible", timeout=timeout)

        # Check if already expanded - look for "Sensitive Action Tools" text
        sensitive_content = self.page.locator('text="Sensitive Action Tools"')
        if sensitive_content.count() == 0 or not sensitive_content.first.is_visible():
            logger.info("Expanding 'Sensitive Actions' accordion")
            accordion_header.click()
            self.page.wait_for_timeout(500)
            sensitive_content.first.wait_for(state="visible", timeout=timeout)

    # ------------------------------------------------------------------
    # Blocked Toolkits methods
    # ------------------------------------------------------------------

    def get_blocked_toolkits(self) -> list[str]:
        """Get list of currently blocked toolkit names from chips."""
        self._expand_blocked_section()

        # Blocked Toolkits section has "Type to search and filter..." input
        # Chips appear after the input
        toolkit_names = []

        # Look for chips in the Blocked Toolkits area (before Blocked Tools section)
        # The section structure: "Blocked Toolkits" heading -> description -> input -> chips
        blocked_toolkits_section = self.page.locator('text="Blocked Toolkits"').first
        parent = blocked_toolkits_section.locator('xpath=ancestor::div[contains(@class, "MuiBox") or contains(@class, "section")][1]')
        chips = parent.locator('.MuiChip-label')

        for i in range(chips.count()):
            text = chips.nth(i).text_content()
            if text and text.strip():
                toolkit_names.append(text.strip())

        logger.info("Blocked toolkits: %s", toolkit_names)
        return toolkit_names

    def is_toolkit_blocked(self, toolkit_name: str) -> bool:
        """Check if a toolkit is in the blocked list."""
        blocked = self.get_blocked_toolkits()
        return any(toolkit_name.lower() == t.lower() for t in blocked)

    @action("Add blocked toolkit")
    def add_blocked_toolkit(self, toolkit_name: str, timeout: int = 5000):
        """Add a toolkit to the blocked toolkits list.

        Uses the "Type to search and filter..." input in Blocked Toolkits section.

        Args:
            toolkit_name: Name of toolkit to block (e.g., 'github', 'pptx')
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding blocked toolkit: %s", toolkit_name)
        self._expand_blocked_section(timeout)

        # Find the "Type to search and filter..." input
        input_field = self.page.locator('input[placeholder*="search and filter"]').first
        input_field.wait_for(state="visible", timeout=timeout)
        input_field.click()
        input_field.fill(toolkit_name)
        self.page.wait_for_timeout(500)

        # Select from dropdown
        option = self.page.locator(f'[role="option"]:has-text("{toolkit_name}"), li:has-text("{toolkit_name}")').first
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.page.wait_for_timeout(500)

        logger.info("Added blocked toolkit: %s", toolkit_name)

    @action("Remove blocked toolkit")
    def remove_blocked_toolkit(self, toolkit_name: str, timeout: int = 5000):
        """Remove a toolkit from the blocked toolkits list.

        Clicks the X (delete) icon on the toolkit chip.

        Args:
            toolkit_name: Name of toolkit to unblock
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Removing blocked toolkit: %s", toolkit_name)
        self._expand_blocked_section(timeout)
        
        # Find the chip with the toolkit name (case-insensitive)
        # Structure: .MuiChip-root > span.MuiChip-label + svg (delete icon)
        chip = self.page.locator(f'.MuiChip-deletable:has(.MuiChip-label:text-is("{toolkit_name}"))').first
        chip.wait_for(state="visible", timeout=timeout)

        # Click the delete icon (svg inside the chip)
        delete_icon = chip.locator('.MuiChip-deleteIcon')
        delete_icon.click()
        self.page.wait_for_timeout(500)

        logger.info("Removed blocked toolkit: %s", toolkit_name)

    # ------------------------------------------------------------------
    # Blocked Tools methods
    # ------------------------------------------------------------------

    @action("Add blocked tool")
    def add_blocked_tool(self, toolkit_name: str, tool_name: str, timeout: int = 5000):
        """Add a specific tool to the blocked tools list.

        Flow:
        1. Enter toolkit name in "Add toolkit name..." input
        2. Select from dropdown (Enter) - toolkit block auto-creates
        3. Enter tool name in "Type tool name..." input
        4. Select from dropdown (Enter) - tool chip auto-adds

        Args:
            toolkit_name: Name of toolkit containing the tool (e.g., 'github')
            tool_name: Name of tool to block (e.g., 'get_issue')
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding blocked tool: %s:%s", toolkit_name, tool_name)
        self._expand_blocked_section(timeout)

        # Check if toolkit block already exists by looking for "Type tool name..." input
        tool_input = self.page.locator('input[placeholder="Type tool name..."]')

        if tool_input.count() == 0:
            # Toolkit block doesn't exist, create it first
            logger.info("Creating toolkit block for: %s", toolkit_name)

            # Find "Add toolkit name..." input and enter toolkit
            add_toolkit_input = self.page.locator('input[placeholder="Add toolkit name..."]').first
            add_toolkit_input.wait_for(state="visible", timeout=timeout)
            add_toolkit_input.click()
            add_toolkit_input.fill(toolkit_name)
            self.page.wait_for_timeout(500)

            # Press Enter to select from dropdown - block auto-creates
            add_toolkit_input.press("Enter")
            self.page.wait_for_timeout(500)

            # Wait for the toolkit block to appear
            tool_input = self.page.locator('input[placeholder="Type tool name..."]').first
            tool_input.wait_for(state="visible", timeout=timeout)

        # Now find the "Type tool name..." input and add the tool
        tool_input = self.page.locator('input[placeholder="Type tool name..."]').first
        tool_input.wait_for(state="visible", timeout=timeout)
        tool_input.click()
        tool_input.fill(tool_name)
        self.page.wait_for_timeout(500)

        # Press Enter to select from dropdown - auto-adds as chip
        tool_input.press("Enter")
        self.page.wait_for_timeout(500)

        logger.info("Added blocked tool: %s:%s", toolkit_name, tool_name)

    @action("Remove blocked tool")
    def remove_blocked_tool(self, tool_name: str, timeout: int = 5000):
        """Remove a tool from the blocked tools list.

        Clicks the X button on the tool chip.

        Args:
            tool_name: Name of tool to unblock
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Removing blocked tool: %s", tool_name)
        self._expand_blocked_section(timeout)

        # Find the chip with the tool name
        chip = self.page.locator(f'.MuiChip-root:has-text("{tool_name}")').first
        chip.wait_for(state="visible", timeout=timeout)

        # Click the X icon
        delete_icon = chip.locator('svg')
        delete_icon.click()
        self.page.wait_for_timeout(500)

        logger.info("Removed blocked tool: %s", tool_name)

    def is_tool_blocked(self, tool_name: str) -> bool:
        """Check if a specific tool is in the blocked tools list.

        Args:
            tool_name: Name of tool to check (case-insensitive)

        Returns:
            True if tool is blocked
        """
        self._expand_blocked_section()

        # Look for chip with the tool name in the Blocked Tools section
        chips = self.page.locator('.MuiChip-root .MuiChip-label')
        for i in range(chips.count()):
            text = chips.nth(i).text_content()
            if text and tool_name.lower() == text.strip().lower():
                logger.info("Tool '%s' is blocked", tool_name)
                return True

        logger.info("Tool '%s' is NOT blocked", tool_name)
        return False

    # ------------------------------------------------------------------
    # Sensitive Action Tools methods
    # ------------------------------------------------------------------

    @action("Add sensitive tool")
    def add_sensitive_tool(self, toolkit_name: str, tool_name: str, timeout: int = 5000):
        """Add a tool to the sensitive action tools list.

        Structure:
        - Each toolkit (artifact, data_analysis, github) is a block
        - Block has: toolkit name header, trash icon, input field, tool chips
        - At bottom: "Add toolkit name..." input + "+ Add" button

        If toolkit block doesn't exist, creates it first.

        Args:
            toolkit_name: Name of toolkit containing the tool (e.g., 'github')
            tool_name: Name of tool to mark as sensitive (e.g., 'get_issue')
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Adding sensitive tool: %s:%s", toolkit_name, tool_name)
        self._expand_sensitive_section(timeout)

        # Check if toolkit block already exists by looking for its header
        sensitive_section = self.page.locator('text="Sensitive Action Tools"').first.locator('xpath=ancestor::div[3]')
        toolkit_headers = sensitive_section.locator(f'text="{toolkit_name.lower()}"')

        if toolkit_headers.count() == 0:
            # Toolkit block doesn't exist, create it
            logger.info("Creating sensitive toolkit block for: %s", toolkit_name)

            # Find "Add toolkit name..." input in Sensitive Actions section
            add_input = self.page.locator('input[placeholder*="Add toolkit name"]').last
            add_input.wait_for(state="visible", timeout=timeout)
            add_input.click()
            add_input.fill(toolkit_name)
            self.page.wait_for_timeout(500)

            # Press Enter to select from dropdown
            add_input.press("Enter")
            self.page.wait_for_timeout(500)

            # Click "+ Add" button
            add_btn = self.page.locator('button:has-text("Add")').last
            add_btn.wait_for(state="visible", timeout=timeout)
            add_btn.click()
            self.page.wait_for_timeout(500)

            logger.info("Created toolkit block for: %s", toolkit_name)
        else:
            logger.info("Toolkit block '%s' already exists", toolkit_name)

        # Find the toolkit block by its header text (e.g., "github")
        # Structure: div.MuiBox-root > div (header with p "github") + div (input + chips)
        # Find the <p> with toolkit name, then go up to the main container
        toolkit_label = self.page.locator(f'p.MuiTypography-root:text-is("{toolkit_name.lower()}")')
        toolkit_label.wait_for(state="visible", timeout=timeout)

        # Go up 2 levels to the main toolkit block container, then find input
        toolkit_block = toolkit_label.locator('xpath=ancestor::div[contains(@class, "MuiBox-root")][2]')
        tool_input = toolkit_block.locator('input').first

        tool_input.wait_for(state="visible", timeout=timeout)
        tool_input.click()
        tool_input.fill(tool_name)
        self.page.wait_for_timeout(500)

        # Press Enter to select from dropdown - auto-adds as chip
        tool_input.press("Enter")
        self.page.wait_for_timeout(500)

        logger.info("Added sensitive tool: %s:%s", toolkit_name, tool_name)

    @action("Remove sensitive tool")
    def remove_sensitive_tool(self, tool_name: str, timeout: int = 5000):
        """Remove a tool from the sensitive action tools list.

        Clicks the X button on the tool chip.

        Args:
            tool_name: Name of tool to remove from sensitive list
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Removing sensitive tool: %s", tool_name)
        self._expand_sensitive_section(timeout)

        # Find the chip with the tool name
        chip = self.page.locator(f'.MuiChip-root:has-text("{tool_name}")').first
        chip.wait_for(state="visible", timeout=timeout)

        # Click the X icon
        delete_icon = chip.locator('svg')
        delete_icon.click()
        self.page.wait_for_timeout(500)

        logger.info("Removed sensitive tool: %s", tool_name)

    def is_tool_in_sensitive_list(self, tool_name: str, toolkit_name: str = None) -> bool:
        """Check if a tool is in the sensitive action tools list.

        Args:
            tool_name: Name of tool to check
            toolkit_name: Optional toolkit to scope the search

        Returns:
            True if tool is in the sensitive list
        """
        self._expand_sensitive_section()

        if toolkit_name:
            # Look for the tool chip within the toolkit block
            toolkit_block = self.page.locator(f'text="{toolkit_name}"').first.locator('xpath=ancestor::div[2]')
            chip = toolkit_block.locator(f'.MuiChip-root:has-text("{tool_name}")')
        else:
            # Look anywhere in sensitive section
            chip = self.page.locator(f'.MuiChip-root:has-text("{tool_name}")')

        return chip.count() > 0 and chip.first.is_visible()

    # ------------------------------------------------------------------
    # Page actions and indicators
    # ------------------------------------------------------------------

    @action("Save configuration")
    def save_configuration(self, timeout: int = 10000):
        """Click Save button and wait for save to complete.

        The Save button is at the bottom of the page (footer).
        """
        logger.info("Saving Guardrails configuration")

        # Save button is in the footer, labeled "Save"
        save_btn = self.page.locator('button:has-text("Save")').last
        save_btn.wait_for(state="visible", timeout=timeout)
        save_btn.scroll_into_view_if_needed()
        save_btn.click()

        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(1000)

        logger.info("Configuration saved")

    def has_reload_required_badge(self, field_name: str = None) -> bool:
        """Check if reload required badge is visible.

        After live-reload enhancement, these badges should NOT appear
        for Blocked Toolkits, Blocked Tools, and Sensitive Action Tools.

        Args:
            field_name: Optional field name to check specific badge

        Returns:
            True if reload required badge is visible
        """
        if field_name:
            # Look for "Reload required" text near the field
            field_locator = self.page.locator(f'text="{field_name}"').first
            badge = field_locator.locator('xpath=ancestor::div[5]').locator('text="Reload required"')
        else:
            badge = self.page.locator('text="Reload required"')

        visible = badge.count() > 0 and badge.first.is_visible()
        logger.info("Reload required badge visible (field=%s): %s", field_name, visible)
        return visible

    def has_reload_banner_after_save(self) -> bool:
        """Check if yellow reload banner appeared after save.

        After live-reload enhancement, no pylon reload banner should appear.

        Returns:
            True if reload required banner/alert is visible
        """
        banner = self.page.locator('[role="alert"]:has-text("reload"), .MuiAlert-root:has-text("pylon"), .MuiAlert-root:has-text("restart")')
        visible = banner.count() > 0 and banner.first.is_visible()
        logger.info("Reload banner visible: %s", visible)
        return visible

    def get_reload_banner_text(self) -> str:
        """Get the text content of the reload banner if visible."""
        banner = self.page.locator('[role="alert"], .MuiAlert-root')
        if banner.count() > 0 and banner.first.is_visible():
            text = banner.first.text_content() or ""
            logger.info("Reload banner text: %s", text[:100])
            return text
        return ""
