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

from config import settings
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, ScopedLocator

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

    # Footer Save of ConfigurationPage.jsx: disabled={!canSave || saving}, label
    # "Saving..." while the request is in flight. Only one exact "Save" on the page.
    save_button = LocatorDescriptor(
        role="button", name="Save", exact=True, suggested_testid="admin-config-save-button",
        description="Configuration footer Save button",
    )
    # Save result snackbar (filled MUI Alert, role=alert). The warning Alert in the
    # action bar also has role=alert, so each result is addressed by its own name:
    # "Configuration saved successfully" | "Configuration saved. Reload required: ..." |
    # "Failed to save: ...". All suggested_testid hints below are for the admin_ui app.
    save_success_alert = LocatorDescriptor(
        xpath="//*[@role='alert'][contains(normalize-space(), 'Configuration saved')]",
        suggested_testid="admin-config-save-success-alert",
        description="Save success snackbar (admin_ui); also carries the 'Reload required' variant. "
        "MUI Alert role=alert has no content-derived accessible name, and the action-bar warning "
        "Alert shares the role, so role+name cannot isolate it",
    )
    save_failure_alert = LocatorDescriptor(
        xpath="//*[@role='alert'][contains(normalize-space(), 'Failed to save')]",
        suggested_testid="admin-config-save-failure-alert",
        description="Save failure snackbar (admin_ui); role=alert has no content-derived name",
    )
    reload_snackbar_alert = LocatorDescriptor(
        xpath="//*[@role='alert'][contains(normalize-space(), 'Reload required')]",
        suggested_testid="admin-config-reload-snackbar-alert",
        description="Warning snackbar after a save that returned requires_restart (admin_ui); "
        "role=alert has no content-derived name",
    )
    # Pending-restart bar rendered after a save that returned requires_restart.
    restart_bar_label = LocatorDescriptor(
        xpath="//span[normalize-space()='Reload required:']",
        suggested_testid="admin-config-restart-bar-label",
        description="Restart bar caption (admin_ui); no role/label/stable css - it is a bare Typography span",
    )
    # GuardrailsFieldCard.jsx (admin_ui): fieldTitleRow = <p>{title}</p> + <Chip label="Reload required">
    # when the field declares requires_restart.
    FIELD_TITLE = ScopedLocator(
        xpath="//p[normalize-space()='{}']",
        suggested_testid="admin-guardrails-field-title-{}",
        description="Field title is a bare body2 Typography (admin_ui); no role/label/stable css",
    )
    FIELD_CARD = ScopedLocator(
        xpath="//p[normalize-space()='{0}']/ancestor::div[.//input]"
        "[not(.//div[.//input][.//p[normalize-space()='{0}']])]",
        suggested_testid="admin-guardrails-field-card-{}",
        description="Field card = nearest ancestor of the title Typography holding the field input, "
        "expressed without positions (admin_ui); no role/label/stable css",
    )
    # Scoped inside a FIELD_CARD: toolkit block of Blocked Tools / Sensitive Action Tools,
    # i.e. nearest ancestor of the toolkit-name Typography that holds its own tool input.
    TOOLKIT_BLOCK = ScopedLocator(
        xpath=".//p[normalize-space()='{0}']/ancestor::div[.//input]"
        "[not(.//div[.//input][.//p[normalize-space()='{0}']])]",
        suggested_testid="admin-guardrails-toolkit-block-{}",
        description="Toolkit block inside a field card (admin_ui); no role/label/stable css",
    )
    EMPTY_TOOLKIT_DELETE = ScopedLocator(
        xpath=".//div[p and button][not(following-sibling::*//*[@role='button'])]/button",
        suggested_testid="admin-guardrails-empty-toolkit-delete-button",
        description="Trash button in the header row (toolkit-name p + button) of a toolkit block "
        "that holds no tool chip (admin_ui); the button has no accessible name",
    )
    FIELD_CHIP_LABEL = ScopedLocator(
        xpath=".//div[@role='button']/span",
        suggested_testid="admin-guardrails-field-chip-label",
        description="Label span of every deletable chip (div[role=button]) in a field card (admin_ui); "
        "enumerates all chips, so it needs no accessible name",
    )
    # MUI deletable chips render role=button with the label as accessible name.
    FIELD_CHIP = ScopedLocator(
        role="button", name="{}", exact=True, suggested_testid="admin-guardrails-field-chip-{}",
    )
    # Anchored inside the field card, so it depends on the same verified anchor as FIELD_CARD.
    FIELD_RELOAD_CHIP = ScopedLocator(
        xpath=".//*[normalize-space()='Reload required']",
        suggested_testid="admin-guardrails-field-reload-chip-{}",
        description="Reload required chip label searched inside the field card (admin_ui); "
        "Chip has no role/name of its own",
    )

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
        """Get names of currently blocked toolkits (chips in the Blocked Toolkits card)."""
        self._expand_blocked_section()
        card = self.FIELD_CARD.within(self.page, "Blocked Toolkits")
        labels = self.FIELD_CHIP_LABEL.within(card)
        names = []
        for i in range(labels.count()):  # enumerates every chip, never picks one
            text = (labels.nth(i).text_content() or "").strip()
            if text:
                names.append(text)
        logger.info("Blocked toolkits: %s", names)
        return names

    def is_toolkit_blocked(self, toolkit_name: str) -> bool:
        """Check if a toolkit is in the blocked list."""
        card = self.FIELD_CARD.within(self.page, "Blocked Toolkits")
        return any(
            self.FIELD_CHIP.within(card, name).count() > 0
            for name in self.get_blocked_toolkits()
            if name.lower() == toolkit_name.lower()
        )

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

    def remove_empty_toolkit_containers(self, timeout: int = 5000):
        """Remove empty toolkit blocks (header + trash button, no tool chips) from Blocked Tools.

        After removing the last tool chip of a toolkit, its block stays. Every match of
        EMPTY_TOOLKIT_DELETE is such a block's trash button, so any of them is the right
        one to remove next; re-counted after each click because the DOM re-renders.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self._expand_blocked_section(timeout)
        card = self.FIELD_CARD.within(self.page, "Blocked Tools")
        removed = 0
        for _ in range(10):  # bounded: a block that refuses to go away must not loop forever
            empty_trash = self.EMPTY_TOOLKIT_DELETE.within(card)
            remaining = empty_trash.count()
            if remaining == 0:
                break
            empty_trash.all()[0].click(timeout=timeout)
            expect(empty_trash).to_have_count(remaining - 1, timeout=timeout)
            removed += 1
        logger.info("Removed %d empty toolkit container(s) from Blocked Tools", removed)

    def is_tool_blocked(self, tool_name: str) -> bool:
        """Check if a specific tool is in the blocked tools list.

        Args:
            tool_name: Name of tool to check (case-insensitive)

        Returns:
            True if tool is blocked
        """
        self._expand_blocked_section()

        card = self.FIELD_CARD.within(self.page, "Blocked Tools")
        blocked = self.FIELD_CHIP.within(card, tool_name).count() > 0
        logger.info("Tool '%s' blocked: %s", tool_name, blocked)
        return blocked

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

        logger.info("Checking if toolkit block exists for: %s (found: %d)", toolkit_name, toolkit_headers.count())
        print(f"[ADD_SENSITIVE] Checking toolkit '{toolkit_name}': found {toolkit_headers.count()} existing blocks")

        if toolkit_headers.count() == 0:
            # Toolkit block doesn't exist, create it
            logger.info("Creating sensitive toolkit block for: %s", toolkit_name)
            print(f"[ADD_SENSITIVE] Creating new toolkit block: {toolkit_name}")

            # Find "Add toolkit name..." input in Sensitive Actions section
            add_input = self.page.locator('input[placeholder*="Add toolkit name"]').last
            add_input.wait_for(state="visible", timeout=timeout)
            print(f"[ADD_SENSITIVE] Found input field, typing: {toolkit_name}")
            add_input.click()
            add_input.clear()
            add_input.press_sequentially(toolkit_name, delay=50)
            self.page.wait_for_timeout(500)

            # Check if dropdown appeared with matching option
            dropdown_option = self.page.locator(f'[role="option"]:has-text("{toolkit_name}")').first

            try:
                # Wait for dropdown to appear
                dropdown_option.wait_for(state="visible", timeout=2000)

                # UI Flow: Clicking dropdown option CREATES the toolkit block immediately
                # No Add button click needed - dropdown selection is sufficient
                print("[ADD_SENSITIVE] Dropdown option found, clicking to create toolkit block")
                dropdown_option.click()
                self.page.wait_for_timeout(1000)  # Wait for toolkit block creation

                print("[ADD_SENSITIVE] Toolkit block created via dropdown selection")

            except Exception:
                # No dropdown option found - use Add button for manual entry
                # This allows adding arbitrary/non-existent toolkit names
                print(f"[ADD_SENSITIVE] No dropdown option for '{toolkit_name}', using Add button")

                add_btn = self.page.locator('button:has-text("Add")').last
                add_btn.wait_for(state="visible", timeout=timeout)

                # Add button should be enabled when typing arbitrary text
                try:
                    add_btn.wait_for(state="enabled", timeout=2000)
                    print("[ADD_SENSITIVE] Add button enabled, clicking")
                    add_btn.click()
                    self.page.wait_for_timeout(1000)
                except Exception:
                    logger.warning("Add button did not enable for manual entry")
                    raise Exception(
                        f"Cannot add toolkit '{toolkit_name}': dropdown option not found and Add button disabled"
                    )

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

    @action("Remove empty toolkit blocks from Sensitive Action Tools")
    def remove_empty_sensitive_toolkit_blocks(self, timeout: int = 5000):
        """Remove empty toolkit blocks from Sensitive Action Tools section.

        After removing all tool chips from a toolkit block, the block container
        (header + trash icon + empty input) remains. This method clicks the trash
        icon to remove empty blocks.

        Uses dynamic discovery to find ALL toolkit blocks, not just known types.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Removing empty toolkit blocks from Sensitive Action Tools")
        print("[CLEANUP] Removing empty sensitive toolkit blocks - using dynamic discovery")
        self._expand_sensitive_section(timeout)

        removed_count = 0

        # DYNAMIC DISCOVERY: Find all visible toolkit labels in Sensitive Action Tools section
        # Look for the Sensitive Action Tools section header first
        sensitive_section = self.page.locator('text="Sensitive Action Tools"').first
        if sensitive_section.count() == 0:
            print("[CLEANUP] Sensitive Action Tools section not found")
            return

        # Get the parent container that holds all toolkit blocks
        # Structure: Header -> parent div -> toolkit blocks
        section_container = sensitive_section.locator('xpath=ancestor::div[3]')

        # Find all typography elements that could be toolkit labels
        # They are <p class="MuiTypography-root"> with toolkit names
        all_labels = section_container.locator('p.MuiTypography-root').all()
        print(f"[CLEANUP] Found {len(all_labels)} potential toolkit labels in Sensitive Actions section")

        # Discover toolkit names dynamically
        discovered_toolkits = []
        for label in all_labels:
            try:
                if not label.is_visible():
                    continue

                text = label.text_content() or ""
                text = text.strip().lower()

                # Skip section headers and empty labels
                if not text or text in ["sensitive action tools", "add toolkit name..."]:
                    continue

                # This is likely a toolkit name
                discovered_toolkits.append(text)
                print(f"[CLEANUP] Discovered toolkit: '{text}'")

            except Exception as e:
                logger.debug("Error reading label: %s", e)
                continue

        # Remove duplicates while preserving order
        discovered_toolkits = list(dict.fromkeys(discovered_toolkits))
        print(f"[CLEANUP] Total unique toolkits discovered: {len(discovered_toolkits)}")

        # Now process each discovered toolkit
        for toolkit_name in discovered_toolkits:
            try:
                # Look for toolkit label by exact text match
                label = self.page.locator(f'p.MuiTypography-root:text-is("{toolkit_name}")').first

                # Wait briefly for the label to be stable
                try:
                    label.wait_for(state="visible", timeout=2000)
                except Exception:
                    print(f"[CLEANUP] Toolkit '{toolkit_name}' label no longer visible, skipping")
                    continue

                if label.count() == 0:
                    continue

                print(f"[CLEANUP] Processing toolkit block: {toolkit_name}")

                # Get the parent container (toolkit block)
                # Structure: <div> -> <div> -> <div containing label + trash + input>
                toolkit_block = label.locator('xpath=ancestor::div[contains(@class, "MuiBox-root")][2]')
                if toolkit_block.count() == 0:
                    print(f"[CLEANUP] Could not find container for: {toolkit_name}")
                    continue

                # Check if block has any tool chips
                chips = toolkit_block.locator('.MuiChip-root')
                chip_count = chips.count()
                print(f"[CLEANUP] Toolkit '{toolkit_name}' has {chip_count} tool chips")

                if chip_count > 0:
                    print(f"[CLEANUP] Toolkit '{toolkit_name}' has tools, keeping block")
                    continue  # Block has tools, skip

                # Empty block found - click the trash icon next to the label
                print(f"[CLEANUP] Toolkit '{toolkit_name}' is empty, removing block")

                # Try to find delete/trash icon near the label
                trash_icon = label.locator('xpath=following-sibling::*[1]//svg').first
                if trash_icon.count() == 0:
                    # Try finding it in the parent row
                    trash_icon = toolkit_block.locator('svg').first

                if trash_icon.count() > 0:
                    print(f"[CLEANUP] Clicking trash icon for empty block: {toolkit_name}")
                    trash_icon.click()
                    self.page.wait_for_timeout(1000)  # Wait for removal animation
                    removed_count += 1
                    logger.info("Removed empty toolkit block: %s", toolkit_name)
                    print(f"[CLEANUP] ✓ Removed empty block: {toolkit_name}")
                else:
                    print(f"[CLEANUP] Could not find trash icon for: {toolkit_name}")

            except Exception as e:
                logger.debug("Error removing toolkit block %s: %s", toolkit_name, e)
                print(f"[CLEANUP] Error removing '{toolkit_name}': {e}")
                continue

        logger.info("Removed %d empty toolkit blocks from Sensitive Action Tools", removed_count)
        print(f"[CLEANUP] Total removed: {removed_count} empty blocks")

    def is_tool_in_sensitive_list(self, tool_name: str, toolkit_name: str) -> bool:
        """Check if a tool chip is inside the toolkit's block of Sensitive Action Tools.

        Args:
            tool_name: Exact tool name (e.g. "list_projects")
            toolkit_name: Toolkit block the chip must belong to (e.g. "jira")
        """
        self._expand_sensitive_section()
        card = self.FIELD_CARD.within(self.page, "Sensitive Action Tools")
        block = self.TOOLKIT_BLOCK.within(card, toolkit_name)
        return self.FIELD_CHIP.within(block, tool_name).count() > 0

    # ------------------------------------------------------------------
    # Page actions and indicators
    # ------------------------------------------------------------------

    @action("Save configuration")
    def save_configuration(self, timeout: int = 10000) -> str:
        """Click Save, verify the PUT response and return the save-result snackbar text.

        The PUT of /plugin_config_values/ is the ground truth (a stale snackbar from a
        previous save inside its 5 s auto-hide window cannot satisfy it). Save that
        stays disabled means there was nothing to save - a test-flow error, raised.

        Raises:
            AssertionError: Save stayed disabled, the PUT failed, or no result
                snackbar appeared within timeout.
        """
        logger.info("Saving Guardrails configuration")
        self.save_button.scroll_into_view_if_needed()
        try:
            expect(self.save_button).to_be_enabled(timeout=timeout)
        except AssertionError as exc:
            raise AssertionError("Save button stayed disabled - no unsaved changes to save") from exc

        try:
            with self.page.expect_response(
                lambda r: "/plugin_config_values/" in r.url and r.request.method == "PUT", timeout=timeout
            ) as response_info:
                self.save_button.click()
        except PlaywrightTimeoutError as exc:
            raise AssertionError("No configuration PUT response after clicking Save") from exc
        response = response_info.value
        if not response.ok:
            raise AssertionError(f"Guardrails save failed: HTTP {response.status}")

        result = self.save_success_alert.or_(self.save_failure_alert)
        try:
            result.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError as exc:
            raise AssertionError("No save result snackbar appeared after the save request") from exc
        text = (result.text_content() or "").strip()
        logger.info("Save result: %s", text[:200])
        if "Failed to save" in text:
            raise AssertionError(f"Guardrails save failed: {text}")
        return text

    def has_reload_required_badge(self, field_name: str) -> bool:
        """Check if a "Reload required" chip is shown on one field card.

        After live-reload enhancement, these badges should NOT appear
        for Blocked Toolkits, Blocked Tools, and Sensitive Action Tools.

        Args:
            field_name: Field title (e.g. "Blocked Toolkits"); the field card
                must be on the page, otherwise the check would be vacuous.

        Returns:
            True if the reload required badge is visible
        """
        if self.FIELD_TITLE.within(self.page, field_name).count() == 0:
            raise AssertionError(f"Field title {field_name!r} not found - cannot check its badge")
        card = self.FIELD_CARD.within(self.page, field_name)
        if card.count() != 1:
            raise AssertionError(f"Expected exactly 1 field card for {field_name!r}, found {card.count()}")
        visible = self.FIELD_RELOAD_CHIP.within(card, field_name).count() > 0
        logger.info("Reload required badge visible (field=%s): %s", field_name, visible)
        return visible

    def has_reload_banner_after_save(self) -> bool:
        """Check whether the save asked for a pylon reload.

        Covers both signals ConfigurationPage.jsx emits for requires_restart:
        the warning snackbar ("Configuration saved. Reload required: ...") and
        the pending-restart bar ("Reload required:" + reload buttons).
        """
        visible = self.reload_snackbar_alert.count() > 0 or self.restart_bar_label.count() > 0
        logger.info("Reload banner visible: %s", visible)
        return visible
