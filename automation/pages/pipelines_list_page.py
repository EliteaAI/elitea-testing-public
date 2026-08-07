"""Pipelines list page object for Elitea pipeline dashboard.

Handles pipeline dashboard operations: search, view switching, navigation.

URL: /pipelines/all
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.pipelines_list")


class PipelinesListPage(BasePage):
    """Pipeline dashboard page (/pipelines/all).

    Handles:
    - Pipeline search
    - View switching (table/card)
    - Dashboard navigation
    - Pipeline existence checks

    URL: /pipelines/all
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

    # Shared SearchBar.jsx component testid (also used by MCP/Credentials/
    # Skills/Toolkits list pages) — same generic testid, ELITEA-2023 AFS
    # Concrete Handles.
    search_clear_button = LocatorDescriptor(
        testid="search-clear-button",
        description="Search clear (X) icon — shared SearchBar, generic testid",
    )

    # Shared Card.jsx component testid (also used by Agents/Credentials/Mcp/
    # Skills list pages — see AgentsListPage.entity_card_name for the
    # identical collection-locator pattern) — collection locator, one per
    # visible pipeline card.
    entity_card_name = LocatorDescriptor(
        testid="entity-card-name",
        description="Pipeline card name (title) — collection locator, one per visible card",
    )

    # Shared CreateEntityButton.jsx testid (also used by Agents/Toolkits/
    # Credentials/Chat list pages — see ToolkitsListPage.sidebar_create_button
    # for the identical pattern). Confirmed live (ELITEA-2020 implementer
    # Phase 2 exploration): while on the Pipelines dashboard, this control's
    # label resolves to "Pipeline" (CreateEntityButton.jsx's currentLabel via
    # RouteToLabelMap) and clicking it navigates directly to
    # /pipelines/create?viewMode=owner (no dropdown — isSimpleCreateRoute).
    sidebar_create_button = LocatorDescriptor(
        testid="sidebar-create-button",
        description="'+ Pipeline' create button in the sidebar (generic, shared across list pages)",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self):
        """Navigate to the pipelines dashboard and wait for load."""
        super().navigate("/pipelines/all")
        self.wait_for_page_load()
        logger.info("Navigated to pipelines dashboard")

    def navigate_to_create(self):
        """Navigate to the create pipeline page."""
        super().navigate("/pipelines/create?viewMode=owner")
        logger.info("Navigated to create pipeline page")

    def click_create_pipeline(self, timeout: int = 15000) -> None:
        """Click the sidebar '+' control and wait for the create form's URL.

        Mirrors ``ToolkitsListPage.click_create_toolkit()`` — same shared
        ``sidebar-create-button`` testid (ELITEA-2020 case Step 2: "Click the
        '+' button next to 'Pipeline' label in the sidebar header area").

        Args:
            timeout: Maximum wait time in milliseconds for the URL to
                reflect the create form.
        """
        self.sidebar_create_button.click()
        self.page.wait_for_url("**/pipelines/create*", timeout=timeout)
        logger.info("Clicked sidebar '+ Pipeline' — now at %s", self.page.url)

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

    def get_card_names(self, timeout: int = 5000) -> list[str]:
        """Return the exact name text of every currently visible pipeline card.

        Reads each card's own ``text_content()`` off the ``entity-card-name``
        testid rather than matching a raw ``text="..."`` selector (as
        :meth:`pipeline_exists_in_list` does) — needed because an active
        search highlights the matched substring by splitting the name across
        nested ``<span>`` fragments (shared ``Card.jsx``/highlight component);
        confirmed live (ELITEA-2023 implementer Phase 2) that Playwright's
        exact ``text="..."`` locator engine does NOT match the parent
        element's concatenated text in that split-node case, even though
        ``element.textContent`` is correct — a Playwright quirk, not a DOM
        issue. Use this (with an ``in``/``==`` check) instead of
        :meth:`pipeline_exists_in_list` when the grid may be in a filtered
        (highlighted) state.

        Args:
            timeout: How long to wait for at least one card to render before
                concluding the grid is empty.

        Returns:
            List of card name strings (empty list if no cards are visible).
        """
        try:
            self.entity_card_name.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return []
        return [self.entity_card_name.nth(i).text_content() or "" for i in range(self.entity_card_name.count())]

    def search(self, query: str):
        """Type *query* into the search box and press Enter (explicit-activation
        control — typing alone does NOT filter the dashboard grid, per live
        source read of shared ``SearchBar.jsx``: ``onChange`` only updates
        local input state and opens the suggestions popover, the actual
        filter dispatch (``onSearch()`` -> redux ``setQuery``) fires only from
        ``onKeyDown === 'Enter'`` or the send-icon click. Mirrors
        ``McpListPage.search()`` / ``CredentialsListPage.search()`` — same
        shared component (ELITEA-2023 AFS § Extension target).

        Filtering here is client-side against an already-fetched pipeline
        list (no new XHR observed firing on Enter — ELITEA-2023 AFS §
        Network Behavior), so this waits for network-idle plus a short
        settle instead of a response predicate.

        Args:
            query: Text to search for.
        """
        logger.info("Searching pipelines for: %s", query)
        self.search_input.click()
        self.search_input.press_sequentially(query, delay=20)
        self.search_input.press("Enter")
        self.wait_for_network()
        self.page.wait_for_timeout(1000)  # MUI/React filter re-render settle

    def search_and_wait_for_results(self, query: str, timeout: int = 5000):
        """Type a search query and wait for results to update.

        Encapsulates search + debounce wait.

        Args:
            query: Text to search for.
            timeout: Maximum wait for results.
        """
        self.search(query)

    def clear_search(self):
        """Click the search box's Clear (X) icon and wait for the list to settle."""
        self.search_clear_button.click()
        self.wait_for_network()
        self.page.wait_for_timeout(1000)  # MUI/React filter re-render settle

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
