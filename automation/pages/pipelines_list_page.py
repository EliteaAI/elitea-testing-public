"""Pipelines list page object for Elitea pipeline dashboard.

Handles pipeline dashboard operations: search, view switching, navigation.

URL: /app/pipelines/all
"""

import logging
from playwright.sync_api import Page
from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.pipelines_list")


class PipelinesListPage(BasePage):
    """Pipeline dashboard page (/app/pipelines/all).

    Handles:
    - Pipeline search
    - View switching (table/card)
    - Dashboard navigation
    - Pipeline existence checks

    URL: /app/pipelines/all
    """

    # LocatorDescriptors - testid + fallback pattern
    search_input = LocatorDescriptor(
        testid="pipeline-search-input",
        fallback=lambda page: page.locator('input[placeholder="Let\'s find something amazing!"]'),
        description="Pipeline search input field on dashboard"
    )

    page_header = LocatorDescriptor(
        testid="pipelines-page-header",
        fallback=lambda page: page.locator('text="Pipelines"').first,
        description="Pipelines page header text"
    )

    table_view_button = LocatorDescriptor(
        testid="pipeline-table-view",
        fallback=lambda page: page.locator('[aria-label="Table view"] button'),
        description="Switch to table view button"
    )

    card_view_button = LocatorDescriptor(
        testid="pipeline-card-view",
        fallback=lambda page: page.locator('[aria-label="Card list view"] button'),
        description="Switch to card view button"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self):
        """Navigate to the pipelines dashboard and wait for load."""
        super().navigate("/app/pipelines/all")
        self.wait_for_page_load()
        logger.info("Navigated to pipelines dashboard")

    def navigate_to_create(self):
        """Navigate to the create pipeline page."""
        super().navigate("/app/pipelines/create?viewMode=owner")
        logger.info("Navigated to create pipeline page")

    # ------------------------------------------------------------------
    # Wait methods
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the pipelines dashboard to fully load.

        Waits for header and network to settle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.page_header.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        logger.info("Pipelines dashboard loaded")

    def wait_for_search_results(self, timeout: int = 5000):
        """Wait for search results to update after typing query.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(500)  # Search debounce

    def wait_for_view_switch(self):
        """Wait for view switch animation to complete."""
        self.page.wait_for_timeout(500)  # MUI view transition

    # ------------------------------------------------------------------
    # Dashboard actions
    # ------------------------------------------------------------------

    def pipeline_exists_in_list(self, name: str, timeout: int = 5000) -> bool:
        """Check whether a pipeline with *name* is visible on the dashboard.

        Args:
            name: Pipeline name (or prefix) to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if pipeline is visible, False otherwise.
        """
        try:
            self.page.locator(f'text="{name}"').first.wait_for(
                state="visible", timeout=timeout,
            )
            return True
        except Exception:
            return False

    def search(self, query: str):
        """Type a search query and wait for results.

        Args:
            query: Text to search for.
        """
        logger.info("Searching pipelines for: %s", query)
        self.search_input.wait_for(state="visible")
        self.search_input.fill(query)
        self.wait_for_search_results()

    def search_and_wait_for_results(self, query: str, timeout: int = 5000):
        """Type a search query and wait for results to update.

        Encapsulates search + debounce wait.

        Args:
            query: Text to search for.
            timeout: Maximum wait for results.
        """
        self.search(query)

    def clear_search(self):
        """Clear the pipelines search box and wait for results."""
        self.search_input.fill("")
        self.wait_for_search_results()

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    def switch_to_table_view(self):
        """Switch dashboard to table view and wait for transition."""
        logger.info("Switching to table view")
        self.table_view_button.click(force=True)  # MUI overlay may intercept
        self.wait_for_view_switch()

    def switch_to_card_view(self):
        """Switch dashboard to card view and wait for transition."""
        logger.info("Switching to card view")
        self.card_view_button.click(force=True)  # MUI overlay may intercept
        self.wait_for_view_switch()

    def is_table_view_active(self) -> bool:
        """Check if table view is currently active.

        MUI ToggleButton sets aria-pressed="true" when active.

        Returns:
            True if table view is active, False otherwise.
        """
        try:
            pressed = self.table_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            classes = self.table_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()

    def is_card_view_active(self) -> bool:
        """Check if card view is currently active.

        MUI ToggleButton sets aria-pressed="true" when active.

        Returns:
            True if card view is active, False otherwise.
        """
        try:
            pressed = self.card_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            classes = self.card_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()
