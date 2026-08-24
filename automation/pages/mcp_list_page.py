"""MCP List Page - Dashboard view for browsing MCPs.

Handles: /mcps/all
- MCP list display (card / table view)
- View toggle (Card list view <-> Table view)
- Search by name (shared ``SearchBar.jsx`` component)

Mirrors the identical card/table toggle pattern already implemented in
``AgentsListPage`` (agents_list_page.py) and ``PipelinesListPage``
(pipelines_list_page.py) — both share the same underlying MUI
``ToggleButtonGroup`` component.

Search mirrors ``CredentialsListPage.search()`` / ``clear_search()``
(credentials_list_page.py) — same shared ``SearchBar.jsx`` component,
explicit-activation (Enter/send-icon, not live-filter-as-you-type). Unlike
Credentials, MCP filtering is client-side against an already-fetched list
(no server round-trip observed on Enter — ELITEA-1941 AFS § Network
Behavior), so there is no response predicate to await; a network-settle +
short render-lag wait is used instead.
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.mcp_list")

UI_ELEMENT_TIMEOUT = 10_000


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

    # Shared CardTagSectionItem.jsx testid (also used by every entity-list
    # badge/tag, e.g. Toolkits/Applications) — collection locator, one per
    # tag chip rendered on a card (e.g. "Remote"). Scoped-selector UPPER_CASE
    # constant per .claude/rules/page-objects.md "Scoped selectors" pattern,
    # NOT a plain LocatorDescriptor: a page-wide entity-card-tag-chip locator
    # would resolve to every card's chip, not just the one for a specific
    # MCP name — this constant is meant to be scoped inside a single matched
    # `mcp_card` via .filter(has_text=name).locator(CARD_TAG_CHIP_SELECTOR)
    # (see :meth:`get_card_type_badge_text`, ELITEA-1921 AFS Automation Hints).
    CARD_TAG_CHIP_SELECTOR = '[data-testid="entity-card-tag-chip"]'

    # Table view column headers (EliteaUI draft PR EliteaAI/EliteaUI#564,
    # ELITEA-1944 fix pass): GridTableHeader.jsx's new optional
    # `columnTestIdPrefix` prop, wired only when DataTable's cardType is MCP
    # (`isMCPs`), renders `data-testid="mcp-table-column-header-{field}"` on
    # each header cell — zero impact on Agents/Pipelines/Skills/Credentials/
    # Toolkits table views, which don't set the prop (confirmed live).
    TABLE_COLUMN_HEADER_TESTID = '[data-testid="mcp-table-column-header-{}"]'

    # Column field ids (EliteaUI SortFields / DataTable.jsx columnsMeta) in
    # display order, paired with their visible label for readable assertions.
    TABLE_COLUMNS = (
        ("name", "Name & Description"),
        ("author", "Authors"),
        ("created_at", "Created"),
        ("online", "Status"),
        ("actions", "Actions"),
    )

    # Table view row name (same draft PR): DataTableNameCell.jsx renders
    # `data-testid="mcp-table-row-name"` on each row's name Typography,
    # gated the same way — a shared, collection-style testid mirroring the
    # `entity-card-name` convention already used in card view.
    mcp_table_row_name = LocatorDescriptor(
        testid="mcp-table-row-name",
        description="MCP name cell in table-view rows — collection locator, one per visible row",
    )

    # Shared SearchBar.jsx component testids (also used by Credentials/
    # Skills/Toolkits/Applications list pages) — same shared component, same
    # mechanics as CredentialsListPage. ELITEA-1941 AFS Concrete Handles.
    search_input = LocatorDescriptor(
        testid="agent-search-input",
        description="MCP search box (shared SearchBar component, default testId)",
    )
    search_send_button = LocatorDescriptor(
        testid="search-send-button",
        description="Search submit (send) icon — shared SearchBar, generic testid",
    )
    search_clear_button = LocatorDescriptor(
        testid="search-clear-button",
        description="Search clear (X) icon — shared SearchBar, generic testid",
    )

    # Shared EmptyStatePage.jsx component testid (also used by Toolkits/
    # Applications/Skills/Pipelines/PersonalTokens list pages) — renders for
    # both "zero MCPs in project" and "zero MCPs match this search" (same
    # generic copy, see ELITEA-1941 AFS step 6 CLARIFICATION).
    empty_state_title = LocatorDescriptor(
        testid="empty-state-title",
        description="Zero-results/zero-MCPs empty-state title ('No MCPs yet')",
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
    # Search
    # ------------------------------------------------------------------

    @action("Search MCPs by name")
    def search(self, term: str) -> None:
        """Type *term* into the search box and press Enter (explicit-activation
        control — typing alone does NOT filter, same ``SearchBar.jsx`` mechanics
        as ``CredentialsListPage.search()``: ``onChange`` only updates local
        input state, the actual filter dispatch fires only from ``onSearch()``,
        wired to Enter/the send icon, and only once the trimmed term is
        ``>= MIN_SEARCH_KEYWORD_LENGTH`` (3) characters).

        Filtering here is client-side against an already-fetched MCP list (no
        new XHR observed firing on Enter — ELITEA-1941 AFS § Network
        Behavior), so this waits for network-idle plus a short settle instead
        of a response predicate — confirmed ~1-1.5s live render lag (AFS §
        Automation Hints).
        """
        self.search_input.click()
        self.search_input.press_sequentially(term, delay=20)
        self.search_input.press("Enter")
        self.wait_for_network()
        self.page.wait_for_timeout(1500)  # MUI/React filter re-render settle
        logger.info("Searched MCPs for %r", term)

    @action("Clear MCP search")
    def clear_search(self) -> None:
        """Click the search box's Clear (X) icon and wait for the list to settle.

        KNOWN DEFECT (EliteaAI/elitea-testing-public#585, ELITEA-1941): clicking
        Clear while the zero-match empty state is showing navigates away to
        ``/mcps/create`` instead of restoring the list — this method still
        performs the click and the network-settle wait; asserting the
        resulting state (restored list vs. the defect's redirect) is the
        caller's responsibility, same division of concerns as
        ``CredentialsListPage.clear_search()``.
        """
        self.search_clear_button.click()
        self.wait_for_network()
        self.page.wait_for_timeout(1500)  # MUI/React filter re-render settle
        logger.info("Cleared MCP search")

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

    def get_card_type_badge_text(self, name: str, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the type/tag badge text (e.g. "Remote") for the card matching *name*.

        Scoped inside the matching ``mcp_card`` via :attr:`CARD_TAG_CHIP_SELECTOR`
        (ELITEA-1921 AFS Automation Hints) so this reads the badge for the
        SPECIFIC card, not the first tag chip anywhere on the page. The API
        list response carries no ``tags`` field — the badge text is
        synthesized client-side from the toolkit's ``type`` (AFS Concrete
        Handles row 13), so there is nothing to assert at the network layer
        for this value, only in the rendered DOM.

        Args:
            name: The MCP card's name (title) text to match.
            timeout: Maximum time to wait for the matching card/chip.
        """
        card = self.mcp_card.filter(has_text=name)
        card.first.wait_for(state="visible", timeout=timeout)
        chip = card.first.locator(self.CARD_TAG_CHIP_SELECTOR).first
        chip.wait_for(state="visible", timeout=timeout)
        return chip.text_content() or ""

    def get_card_texts(self, timeout: int = UI_ELEMENT_TIMEOUT) -> list[str]:
        """Return the full rendered text of every visible MCP card.

        Scoped to the ``entity-card`` testid (the :attr:`mcp_card` collection
        locator) — no raw page-level handle. Used by ELITEA-1936 step 2 to
        assert an ABSENCE: no Remote MCP card renders a connection-status
        badge. The badge the case expects does not exist in the product
        (clarification EliteaAI/elitea-testing-public#1723), so there is no
        testid to bind an absence assertion to — reading each card's own text
        through its testid-anchored container is the closest testid-only
        shape, and it keeps the case's claim test-enforced instead of silently
        dropped.

        Args:
            timeout: Maximum time to wait for the first card to render.
        """
        try:
            self.mcp_card.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return []
        return [self.mcp_card.nth(i).inner_text() for i in range(self.mcp_card.count())]

    @action("Open an MCP card by name from the list")
    def open_card_by_name(self, name: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the MCP card matching *name*, navigating to its detail page.

        Assumes :meth:`navigate` (or an equivalent list-page load) already
        happened — this method does NOT re-navigate to ``/mcps/all`` first.
        This is deliberate: ELITEA-1947's own case has "navigate to the list
        and verify appears" (step 2) and "click the card" (step 3) as two
        separate steps/assertions, and the resulting redirect-after-delete
        assertion (step 8) is only reliable when the detail page was reached
        via a REAL list-card click, not the create flow's own post-save
        redirect (AFS § Known Defects Found / Automation Hints) — so callers
        must land on the list via :meth:`navigate` themselves first, then
        call this method, rather than this method silently re-navigating and
        collapsing the two steps into one.

        After the click, the caller is responsible for waiting on the
        detail page's own ready state (e.g. ``McpFormPage.wait_for_page_load()``)
        — this method only waits for the click's own network settle, since
        it has no knowledge of the destination page object's readiness
        signal.

        Args:
            name: The MCP card's name (title) text to match.
            timeout: Maximum time to wait for the matching card to appear.
        """
        card = self.mcp_card.filter(has_text=name)
        card.first.wait_for(state="visible", timeout=timeout)
        card.first.click()
        self.wait_for_network()
        logger.info("Opened MCP card %r from the list", name)

    # ------------------------------------------------------------------
    # Table view
    # ------------------------------------------------------------------

    def get_visible_table_column_headers(self) -> list[str]:
        """Return which of the expected table column headers are visible.

        Resolved via the per-column ``mcp-table-column-header-{field}``
        testid (EliteaUI draft PR #564) — each column's field id is checked
        for visibility, and its display label is returned on a match.
        """
        visible = []
        for field, label in self.TABLE_COLUMNS:
            header = self.page.locator(self.TABLE_COLUMN_HEADER_TESTID.format(field))
            if header.count() > 0 and header.first.is_visible():
                visible.append(label)
        return visible

    def get_visible_table_row_names(self, candidate_names: list[str]) -> list[str]:
        """Return which of *candidate_names* are visible as table row names.

        Resolved via the shared ``mcp-table-row-name`` testid (EliteaUI
        draft PR #564) — a collection locator, one per visible row, matched
        by text content (same pattern as :meth:`get_card_names`).

        Args:
            candidate_names: MCP names to check (typically the names
                captured from card view via :meth:`get_card_names`).
        """
        try:
            self.mcp_table_row_name.first.wait_for(state="visible", timeout=5000)
        except Exception:
            return []
        visible_names = {
            self.mcp_table_row_name.nth(i).text_content().strip()
            for i in range(self.mcp_table_row_name.count())
        }
        return [name for name in candidate_names if name in visible_names]
