"""MCP List Page - Dashboard view for browsing MCPs.

Handles: /mcps/all
- MCP list display (card / table view)
- View toggle (Card list view <-> Table view)

Mirrors the identical card/table toggle pattern already implemented in
``AgentsListPage`` (agents_list_page.py) and ``PipelinesListPage``
(pipelines_list_page.py) — both share the same underlying MUI
``ToggleButtonGroup`` component.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.mcp_list")


class McpListPage(BasePage):
    """Page object for the MCP list/dashboard page.

    URL: /mcps/all

    Note: with zero MCPs in the project, ``/mcps/all`` auto-redirects to
    ``/mcps/create`` (confirmed live, ELITEA-1944 implementer Phase 2) —
    :meth:`navigate` assumes at least one MCP already exists; callers that
    can't guarantee that should call :meth:`has_any_mcp` first (see
    ``tests/ui/toolkits/test_mcp_view_toggle.py`` for the seed-if-empty
    pattern).
    """

    # ------------------------------------------------------------------
    # Locators
    # ------------------------------------------------------------------

    # KNOWN DEFECT (EliteaAI/elitea-testing-public#521, non-blocking): these
    # testids are shared verbatim with AgentsListPage — the MCP list page has
    # no MCP-scoped view-toggle testids of its own yet. Stable and
    # functionally correct; automate against them as-is per the ELITEA-1944
    # AFS, re-point to mcp-* testids if/when #521 is fixed.
    table_view_button = LocatorDescriptor(
        testid="agent-table-view-button",
        description="Switch to table view (misnamed — see EliteaAI/elitea-testing-public#521)",
    )

    card_view_button = LocatorDescriptor(
        testid="agent-card-view-button",
        description="Switch to card view (misnamed — see EliteaAI/elitea-testing-public#521)",
    )

    # Shared Card.jsx component testid (also used by Agents/Pipelines/Skills
    # list pages) — collection locator, one per visible MCP card.
    mcp_card = LocatorDescriptor(
        testid="entity-card",
        description="MCP card outer container (card view)",
    )

    mcp_card_name = LocatorDescriptor(
        testid="entity-card-name",
        description="MCP card name (title) — collection locator, one per visible card",
    )

    # Table view renders no per-row/per-cell testids (confirmed live — plain
    # DOM, no role="row"/MuiDataGrid-row/<tr> structure with testids). Column
    # headers and row presence are asserted via visible text as an interim
    # measure (AFS Concrete Handles) until a follow-up adds per-row testids.
    TABLE_COLUMN_HEADERS = (
        "Name & Description",
        "Authors",
        "Created",
        "Status",
        "Actions",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to MCP list")
    def navigate(self):
        """Navigate to the MCP dashboard and wait until ready.

        Assumes the project already has at least one MCP — see
        :meth:`has_any_mcp` for the zero-MCP precondition check.
        """
        super().navigate("/mcps/all")
        self.wait_for_page_load()
        logger.info("Navigated to MCP dashboard and page loaded")

    @action("Check whether the project has any MCP")
    def has_any_mcp(self, timeout: int = 8000) -> bool:
        """Navigate to ``/mcps/all`` and report whether the project has >=1 MCP.

        With zero MCPs, the app auto-redirects ``/mcps/all`` -> ``/mcps/create``
        (confirmed live, ELITEA-1944 implementer Phase 2 — the AFS had flagged
        this as an untested edge case). On a "no MCPs" result, the page is
        left sitting on ``/mcps/create`` (the type picker) as a side effect,
        which callers can use directly to seed one via ``McpFormPage``.

        Args:
            timeout: Maximum time to wait for either the card view button
                (non-empty) or the redirect to settle (empty).

        Returns:
            True if at least one MCP is present, False if the project is
            empty (and the page is now on ``/mcps/create``).
        """
        super().navigate("/mcps/all")
        try:
            self.card_view_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            logger.info("has_any_mcp: no MCPs found (redirected to %s)", self.page.url)
            return False

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the MCP dashboard to load.

        No dedicated ``mcps-page-header`` testid exists yet (unlike Agents'
        ``agents-page-header`` / Pipelines' ``pipelines-page-header`` — see
        AFS Concrete Handles), so the Card list view button's visibility is
        used as the load-complete proxy: it is present as soon as the list
        renders.
        """
        self.card_view_button.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        logger.info("MCP dashboard loaded")

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    @action("Switch to table view")
    def switch_to_table_view(self, wait_for_render: bool = True):
        """Switch to table view and optionally wait for the transition."""
        self.table_view_button.click(force=True)  # MUI overlay may intercept
        if wait_for_render:
            self.page.wait_for_timeout(500)  # MUI view-switch animation
        logger.info("Switched to table view")

    @action("Switch to card view")
    def switch_to_card_view(self, wait_for_render: bool = True):
        """Switch to card view and optionally wait for the transition."""
        self.card_view_button.click(force=True)  # MUI overlay may intercept
        if wait_for_render:
            self.page.wait_for_timeout(500)  # MUI view-switch animation
        logger.info("Switched to card view")

    def is_table_view_active(self) -> bool:
        """Check if table view is currently active (aria-pressed)."""
        try:
            pressed = self.table_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            classes = self.table_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()

    def is_card_view_active(self) -> bool:
        """Check if card view is currently active (aria-pressed)."""
        try:
            pressed = self.card_view_button.get_attribute("aria-pressed")
            return pressed == "true"
        except Exception:
            classes = self.card_view_button.get_attribute("class") or ""
            return "selected" in classes.lower() or "active" in classes.lower()

    # ------------------------------------------------------------------
    # Card view
    # ------------------------------------------------------------------

    def get_card_count(self, timeout: int = 5000) -> int:
        """Return the number of MCP cards currently visible."""
        try:
            self.mcp_card.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return 0
        return self.mcp_card.count()

    def get_card_names(self, timeout: int = 5000) -> list[str]:
        """Return the names of all MCP cards currently visible."""
        try:
            self.mcp_card_name.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return []
        names = []
        for i in range(self.mcp_card_name.count()):
            names.append(self.mcp_card_name.nth(i).text_content().strip())
        return names

    # ------------------------------------------------------------------
    # Table view
    # ------------------------------------------------------------------

    def get_visible_table_column_headers(self) -> list[str]:
        """Return which of the expected table column headers are visible.

        No per-column testids exist (AFS Concrete Handles) — matched via
        visible text, same as the AFS's live exploration approach.
        """
        visible = []
        for header in self.TABLE_COLUMN_HEADERS:
            if self.page.get_by_text(header, exact=True).count() > 0:
                visible.append(header)
        return visible

    def get_visible_table_row_names(self, candidate_names: list[str]) -> list[str]:
        """Return which of *candidate_names* are visible as table row text.

        Individual table rows carry no ``data-testid`` (confirmed live — the
        table renders via plain DOM), so row presence is verified via visible
        text matching, per the AFS's interim measure.

        Args:
            candidate_names: MCP names to check (typically the names
                captured from card view via :meth:`get_card_names`).
        """
        return [
            name for name in candidate_names
            if self.page.get_by_text(name, exact=True).count() > 0
        ]
