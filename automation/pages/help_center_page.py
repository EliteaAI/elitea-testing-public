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
