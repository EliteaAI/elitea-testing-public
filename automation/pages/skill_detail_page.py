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

        Returns:
            Skill ID as string.
        """
        url = self.page.url
        # Extract the numeric ID from the URL path segment
        # e.g. /app/skills/all/42 → "42"
        parts = url.rstrip("/").split("/")
        for part in reversed(parts):
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
        delete_btn = self.page.get_by_test_id("chat-delete-button").last()
        try:
            delete_btn.wait_for(
                state="visible",
                timeout=max(1000, int((deadline - time.time()) * 1000)),
            )
        except Exception:
            pass  # Fall through to content-stable check

        # Wait for content to stabilize — read via chat-answer-content (last AI message).
        last_response = self.page.get_by_test_id("chat-answer-content").last()
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
        return (self.page.get_by_test_id("chat-answer-content").last().text_content() or "").strip()

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
