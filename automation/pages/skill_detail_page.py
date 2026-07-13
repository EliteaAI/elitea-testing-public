"""Skill Detail Page - View and manage an individual skill.

Handles: /skills/all/{skill_id}
- View/edit skill form (inherited from SkillFormPage)
- SkillTestPanel — stateless LLM prediction panel
- Overflow menu with delete skill action
"""

import re
import logging
import time
from playwright.sync_api import Page

from playwright.sync_api import Download

from .skill_form_page import SkillFormPage
from .locator_descriptor import LocatorDescriptor
from components.mui import Dialog
from utils.actions import action


logger = logging.getLogger("elitea.pages.skill_detail")


class SkillDetailPage(SkillFormPage):
    """Page object for the skill detail/edit page.

    Inherits form operations from SkillFormPage.
    Adds SkillTestPanel interaction and overflow menu (delete).

    URL: /skills/all/{skill_id}
    """

    # Information section (used for wait_for_page_load)
    information_section = LocatorDescriptor(
        testid="skill-information-section",
        description="Skill information accordion section"
    )

    # SkillTestPanel outer container
    test_panel = LocatorDescriptor(
        testid="skill-test-panel",
        description="SkillTestPanel container"
    )

    # Overflow menu trigger button
    controls_menu_button = LocatorDescriptor(
        testid="skill-controls-menu-button",
        description="Skill controls overflow menu button"
    )

    # Overflow menu — VERSION-scoped Export item (distinct from the
    # SKILL-scoped items further down the same menu)
    export_version_menu_item = LocatorDescriptor(
        testid="export-version-menuitem",
        description="Export the current (base) version via the overflow menu"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to skill detail")
    def navigate(self, skill_id: int):
        """Navigate to a specific skill's detail page and wait until ready.

        Args:
            skill_id: Numeric skill ID.
        """
        super(SkillDetailPage, self).navigate(f"/skills/all/{skill_id}")
        self.wait_for_page_load()
        logger.info("Navigated to skill %d detail page", skill_id)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the skill detail page to fully load.

        Waits for the Information section to appear and network to settle.
        """
        self.page.get_by_test_id("skill-information-section").wait_for(
            state="visible", timeout=timeout,
        )
        self.wait_for_network(timeout=10000)
        logger.info("Skill detail page loaded")

    # ------------------------------------------------------------------
    # Page verification
    # ------------------------------------------------------------------

    def verify_on_detail_page(self):
        """Assert that the browser is on a skill detail page (not create)."""
        url = self.page.url
        assert "/skills/all/" in url, f"Not on skill detail page: {url}"
        assert "/create" not in url, f"Still on create page: {url}"
        logger.info("Verified on skill detail page: %s", url)

    # ------------------------------------------------------------------
    # Skill information
    # ------------------------------------------------------------------

    def get_skill_id(self) -> str:
        """Read the Skill ID from the Information section via the URL.

        Falls back to the 'Copy ID' button text if URL parsing fails.

        URL pattern is ``/skills/all/{skillId}`` (base version, one digit
        segment) or ``/skills/all/{skillId}/{versionId}`` (a named version
        is active, two digit segments) — the Skill ID is always the
        *first* digit segment, so this scans forward and returns on the
        first match (fixed from a reversed/last-match scan that returned
        the Version ID instead of the Skill ID once a second digit segment
        was present — ELITEA-1738; identical result for existing
        single-segment callers).

        Returns:
            Skill ID as string.
        """
        url = self.page.url
        # Extract the numeric ID from the URL path segment
        # e.g. /skills/all/42 → "42"; /skills/all/42/43 → "42"
        parts = [p for p in url.split("?")[0].rstrip("/").split("/") if p]
        for part in parts:
            if part.isdigit():
                return part

        raise RuntimeError(f"Cannot determine skill ID from URL: {url}")

    # ------------------------------------------------------------------
    # SkillTestPanel
    # ------------------------------------------------------------------

    def _test_panel_messages(self):
        """Return locator for all chat-message-item elements in the test panel."""
        return self.page.get_by_test_id("chat-message-item")

    def get_test_message_count(self) -> int:
        """Return the current number of messages in the test panel.

        Returns:
            Integer count of message items.
        """
        return self._test_panel_messages().count()

    @action("Send test message")
    def send_test_message(self, message: str, timeout: int = 5000):
        """Type and send a message in the SkillTestPanel.

        Scopes the chat input and send button to the skill-test-panel container
        to avoid conflicts with any other chat panels on the page.

        Args:
            message: The message text to send.
            timeout: Maximum wait time for elements.
        """
        logger.info("Sending test message: %r", message[:60])
        chat_input = self.page.get_by_test_id("chat-message-input")
        chat_input.wait_for(state="visible", timeout=timeout)
        chat_input.fill(message)
        self.page.wait_for_timeout(300)

        send_btn = self.page.get_by_test_id("chat-send-button")
        send_btn.wait_for(state="visible", timeout=timeout)
        send_btn.click()
        logger.info("Test message sent")

    def wait_for_test_response(
        self,
        initial_count: int = 0,
        stable_duration_ms: int = 3000,
        timeout: int = 30000,
    ):
        """Wait for the AI response in the test panel to stabilize.

        Waits for new messages to appear beyond initial_count, then waits
        for the last message content to stop changing.

        Args:
            initial_count: Number of messages before sending.
            stable_duration_ms: Content must be unchanged for this duration (ms).
            timeout: Overall timeout in milliseconds.
        """
        logger.info(
            "Waiting for test response (initial=%d, stable=%dms, timeout=%dms)",
            initial_count, stable_duration_ms, timeout,
        )
        messages = self._test_panel_messages()
        deadline = time.time() + timeout / 1000

        # Wait for at least one new message to appear
        while time.time() < deadline:
            if messages.count() > initial_count:
                break
            self.page.wait_for_timeout(500)

        # Wait for the delete button to appear on the last response (stream complete).
        delete_btn = self.page.get_by_test_id("chat-delete-button").last
        try:
            delete_btn.wait_for(
                state="visible",
                timeout=max(1000, int((deadline - time.time()) * 1000)),
            )
        except Exception:
            pass  # Fall through to content-stable check

        # Wait for content to stabilize — read via skill-test-last-response (last AI message).
        # The last message in the skill test panel uses testid "skill-test-last-response";
        # non-last messages use "chat-answer-content".
        last_response = self.page.get_by_test_id("skill-test-last-response")
        last_content = ""
        stable_start = time.time()

        while time.time() < deadline:
            try:
                current = (last_response.text_content() or "")
            except Exception:
                current = ""

            if current and current == last_content:
                if (time.time() - stable_start) * 1000 >= stable_duration_ms:
                    logger.info("Test response stabilized (%d chars)", len(current))
                    return
            else:
                last_content = current
                stable_start = time.time()

            self.page.wait_for_timeout(500)

        logger.warning("Test response did not stabilize within timeout")

    def get_last_test_response(self) -> str:
        """Return the text content of the last AI response in the test panel.

        Reads from data-testid="chat-answer-content" (last element).

        Returns:
            Response text as string (stripped).
        """
        # The last message in the skill test panel uses testid "skill-test-last-response".
        return (self.page.get_by_test_id("skill-test-last-response").text_content() or "").strip()

    # ------------------------------------------------------------------
    # Actions menu (overflow/three-dot menu)
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the skill controls overflow menu.

        Uses JavaScript click to bypass any MUI overlay interception.
        Waits for the Delete skill menu item to confirm the menu is open.
        """
        logger.info("Opening skill actions menu")
        self.controls_menu_button.evaluate("el => el.click()")
        self.page.get_by_test_id("skill-delete-menu-item").wait_for(state="visible", timeout=5000)

    @action("Delete skill via menu")
    def delete_skill_via_menu(self, skill_name: str, timeout: int = 10000):
        """Delete the current skill via the overflow menu.

        Opens the menu, clicks "Delete skill", and handles the confirmation
        dialog (type skill name + confirm delete).

        Args:
            skill_name: The exact skill name to type in the confirmation dialog.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Deleting skill via menu: %r", skill_name)

        self.open_actions_menu()
        self.page.get_by_test_id("skill-delete-menu-item").click()

        # Handle the type-to-confirm dialog (Modal.DeleteEntityModal)
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.type_to_confirm(dialog, skill_name)
        self.page.wait_for_timeout(300)
        Dialog.click_button(dialog, "Delete")

        # Wait for redirect to the skills list page (/skills/all without trailing ID).
        # Regex with $ anchor is required — glob **/skills/all also matches /skills/all/4.
        self.page.wait_for_url(
            re.compile(r".*/skills/all/?$"),
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        logger.info("Skill %r deleted via menu", skill_name)

    @action("Export skill base version via menu")
    def export_base_version_via_menu(self, timeout: int = 10000) -> Download:
        """Export the skill's current (base) version via the overflow menu.

        Opens the overflow menu and clicks the VERSION-scoped "Export" item
        (``export-version-menuitem`` — distinct from the SKILL-scoped items
        further down the same menu), waiting for the resulting file download.

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object for the exported ``.md`` file.
        """
        logger.info("Exporting skill base version via menu")
        self.open_actions_menu()

        with self.page.expect_download(timeout=timeout) as download_info:
            self.export_version_menu_item.click()

        download = download_info.value
        logger.info("Skill base version exported — filename: %s", download.suggested_filename)
        return download

    @action("Export current version via menu")
    def export_version_via_menu(self, timeout: int = 10000) -> Download:
        """Export whichever version is currently selected via the overflow menu.

        Thin wrapper around :meth:`export_base_version_via_menu` — that
        method already exports whatever version is currently active (the
        ``export-version-menuitem`` testid is version-scoped, not
        base-specific); this alias just avoids the misleading "base" in the
        call site's name when exporting a non-base version (ELITEA-1738).

        Args:
            timeout: Maximum wait time in milliseconds for the download event.

        Returns:
            Playwright ``Download`` object for the exported ``.md`` file.
        """
        return self.export_base_version_via_menu(timeout=timeout)

    # ------------------------------------------------------------------
    # Version management (Save As Version / VERSION selector)
    # ------------------------------------------------------------------

    def get_version_id(self) -> str:
        """Read the current Version ID from the URL's second path segment.

        URL pattern: ``/skills/all/{skillId}/{versionId}`` — only present
        once a non-base version has been created/selected; on the initial
        ``base`` version the URL is just ``/skills/all/{skillId}`` and the
        Version ID equals the Skill ID.

        Returns:
            Version ID as string.
        """
        url = self.page.url
        parts = [p for p in url.split("?")[0].rstrip("/").split("/") if p]
        digit_parts = [p for p in parts if p.isdigit()]
        if len(digit_parts) >= 2:
            return digit_parts[-1]
        if len(digit_parts) == 1:
            # No explicit version segment yet — Version ID equals Skill ID.
            return digit_parts[0]
        raise RuntimeError(f"Cannot determine version ID from URL: {url}")

    @action("Save current edits as a new version")
    def save_as_version(self, version_name: str, timeout: int = 10000):
        """Click "Save As Version", fill the Name field, and confirm.

        Opens the "Create version" dialog via the "Save As Version" button
        (in the version tab bar, distinct from the overflow menu), types the
        new version name, and clicks the dialog's Save. Waits for the
        ``Version "{version_name}" created`` toast and for the URL to gain a
        new version-id path segment.

        LOCATOR: "Save As Version" button and the dialog's Name textbox have
        no ``data-testid`` yet (confirmed in ELITEA-1738 AFS exploration) —
        located by stable accessible role/name per the project's locator
        priority order (data-testid > accessible role).

        Args:
            version_name: Name for the new version (e.g. ``"ver_1"``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Saving current edits as new version: %r", version_name)
        previous_version_id = self.get_version_id()

        save_as_version_btn = self.page.get_by_role("button", name="Save As Version")
        save_as_version_btn.click()

        dialog = self.page.get_by_role("dialog")
        dialog.wait_for(state="visible", timeout=timeout)
        name_field = dialog.get_by_role("textbox", name="Name")
        name_field.click()
        name_field.type(version_name)
        self.page.wait_for_timeout(200)

        dialog.get_by_role("button", name="Save").click()

        self.page.get_by_text(f'Version "{version_name}" created').wait_for(
            state="visible", timeout=timeout
        )
        self.page.wait_for_function(
            "prevId => window.location.pathname.split('/').filter(Boolean).pop() !== prevId",
            arg=previous_version_id,
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        logger.info(
            "New version %r created — URL: %s", version_name, self.page.url
        )

    def get_version_selector_value(self) -> str:
        """Return the currently displayed value of the VERSION selector.

        LOCATOR: ``#skill-version-select`` — confirmed present live
        (``SkillTabBar.jsx``), no ``data-testid`` yet.

        Returns:
            The version name currently shown in the selector (e.g. ``"ver_1"``).
        """
        return (self.page.locator("#skill-version-select").text_content() or "").strip()

    @action("Switch to a different skill version")
    def switch_version(self, version_name: str, timeout: int = 10000):
        """Select a different version from the VERSION combobox.

        LOCATOR: ``#skill-version-select`` — no ``data-testid`` yet.

        Args:
            version_name: The version name to select (e.g. ``"base"``).
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Switching to version: %r", version_name)
        selector = self.page.locator("#skill-version-select")
        selector.click()
        option = self.page.get_by_role("option", name=version_name, exact=True)
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.wait_for_network(timeout=5000)
        logger.info("Switched to version: %r", version_name)
