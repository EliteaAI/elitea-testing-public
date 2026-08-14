"""Help Center page object.

Displays the resource cards (Documentation, Release Notes, Video Library,
Tutorials, Interactive Tours) and their links, some of which launch guided
Interactive Tours in a new tab.

URL: /help-center
"""

import logging

from playwright.sync_api import Locator, Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.help_center")


class HelpCenterPage(BasePage):
    """Page object for the Help Center page.

    URL: /help-center
    """

    page_header = LocatorDescriptor(
        testid="help-center-page-header",
        description="'Help Center' page title",
    )

    # --- Version info tooltip (ELITEA-2225, ResourceVersionInfo.jsx) ---
    version_label = LocatorDescriptor(
        testid="help-center-version-label",
        description="'Version: X.Y.Z (DD-Mon-YYYY)' label, top-right of the header",
    )
    version_info_icon = LocatorDescriptor(
        testid="help-center-version-info-icon",
        description="'i' info icon that opens the version-details tooltip on hover",
    )
    version_info_tooltip = LocatorDescriptor(
        testid="help-center-version-info-tooltip",
        description="Tooltip content panel listing each component's name/version + the copy button",
    )
    version_info_copy_button = LocatorDescriptor(
        testid="help-center-version-info-copy-button",
        description="Copies the full version info block to the clipboard",
    )

    # --- App-wide toast (Toast.jsx, src/components/Toast.jsx) — shared
    # component, testids pre-exist and need no EliteaUI change (same
    # component already used by AgentDetailPage.toast_alert/toast_message,
    # ChatPage.toast_alert/toast_message, etc. — existing repo precedent of
    # each page object declaring its own field for this shared component). ---
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body.",
    )

    # Dynamic testid template — the resource link slug is the kebab-case of
    # the backend-configured link title (no stable id field exists on the
    # link data). Naming: help-center-tour-link-{slug}.
    TOUR_LINK = '[data-testid="help-center-tour-link-{}"]'

    def navigate(self) -> None:
        """Navigate to the Help Center page and wait for it to load."""
        super().navigate("/help-center")
        self.page_header.wait_for(state="visible", timeout=15000)

    def resource_link(self, slug: str) -> Locator:
        """Return the Locator for a resource card link by its kebab-case slug.

        Args:
            slug: kebab-case slug of the link's title, e.g.
                ``"getting-started"``.

        Returns:
            Locator built from the ``TOUR_LINK`` dynamic-testid template.
        """
        return self.page.locator(self.TOUR_LINK.format(slug))

    @action("Open a resource link in a new tab")
    def open_resource_link_in_new_tab(self, slug: str, timeout: int = 10000) -> Page:
        """Click a resource link (``target="_blank"``) and return the new tab.

        Args:
            slug: kebab-case slug of the link's title, e.g.
                ``"sidebar-interactive-tour"``.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The new ``Page`` object for the opened tab.
        """
        link = self.resource_link(slug)
        link.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            link.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        logger.info("Opened resource link %r in new tab: %s", slug, new_page.url)
        return new_page

    @action("Open the version info tooltip")
    def open_version_info_tooltip(self, timeout: int = 10000) -> None:
        """Hover the 'i' info icon so the version-details tooltip appears.

        MUI ``Tooltip`` mounts its content into the DOM on hover — the
        ``version_info_tooltip`` locator is not present/visible beforehand.
        """
        self.version_info_icon.hover(timeout=timeout)
        self.version_info_tooltip.wait_for(state="visible", timeout=timeout)

    @action("Copy the version info to the clipboard")
    def copy_version_info(self, timeout: int = 10000) -> str:
        """Click the tooltip's copy button and return the copied clipboard text.

        Clears the clipboard first (real OS clipboard write — permission is
        granted on the browser context, see ``conftest.py``) so waiting for a
        non-empty value afterward is a real condition, not a sleep. Waits for
        the success toast, then polls the clipboard via ``wait_for_function``
        (same pattern as ``test_agent_copy_version_link.py``) rather than a
        direct ``readText()`` call, which can hang on a permission prompt.
        """
        self.page.evaluate("() => navigator.clipboard.writeText('')")
        self.version_info_copy_button.click(timeout=timeout)
        self.toast_message.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_function(
            "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
            timeout=timeout,
        )
        return self.get_clipboard_text()
