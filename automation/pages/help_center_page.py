"""Help Center page object.

Displays the resource cards (Documentation, Release Notes, Video Library,
Tutorials, Interactive Tours) and their links, some of which launch guided
Interactive Tours in a new tab.

URL: /help-center
"""

import logging

from playwright.sync_api import Page
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

    # Sidebar footer "?" icon (aria-label only on DEV) — opens the Help Center.
    sidebar_help_icon = LocatorDescriptor(
        label="Help Center",
        suggested_testid="sidebar-help-center-button",
        description="'?' Help Center icon in the sidebar footer, next to Support Bot",
    )
    interactive_tours_card = LocatorDescriptor(
        css='[data-tour="resources-interactive-tours-card"]',
        suggested_testid="help-center-interactive-tours-card",
        description="INTERACTIVE TOURS resource card (data-tour hook; no testid on DEV)",
    )

    # Dynamic testid template — the resource link slug is the kebab-case of
    # the backend-configured link title (no stable id field exists on the
    # link data). Naming: help-center-tour-link-{slug}.
    TOUR_LINK = '[data-testid="help-center-tour-link-{}"]'

    def navigate(self) -> None:
        """Navigate to the Help Center page and wait for it to load."""
        super().navigate("/help-center")
        self.page_header.wait_for(state="visible", timeout=15000)

    @action("Open Help Center via the sidebar icon")
    def open_via_sidebar_icon(self, timeout: int = 15000) -> None:
        """Click the sidebar "?" icon (from the current page) and wait for the Help Center."""
        self.sidebar_help_icon.click(timeout=timeout)
        self.page_header.wait_for(state="visible", timeout=timeout)

    @action("Start an interactive tour via its deep link")
    def start_tour_via_url(self, tour_id: str) -> None:
        """Start a tour the way the app itself does: the ``?tour=<id>`` deep link.

        DEV's Interactive Tours card has no CMS-configured links, so the
        link click is not available; the deep link is what those links resolve to.
        """
        BasePage.navigate(self, f"/?tour={tour_id}")

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
        link = self.page.locator(self.TOUR_LINK.format(slug))
        link.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            link.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        logger.info("Opened resource link %r in new tab: %s", slug, new_page.url)
        return new_page
