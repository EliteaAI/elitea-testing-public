"""Analytics page object (Settings → Analytics).

URL: /settings/analytics

Covers the page shell: header (title + project badge), the date-range filter
bar (four presets + From/To pickers), the seven-tab bar, the Overview-data
loading state (ELITEA-2310), and the Users tab's panel content — "User
Activity" header/count, search-by-email input, the 9-column table (header +
repeated data rows), and pagination controls (ELITEA-2312). Other per-tab
content (Costs/Agents & Pipelines/Tools/Health/Guide bodies) remains out of
scope.

Locator provenance (ELITEA-2310, zero pre-existing testids on this surface
except the unused-by-this-case ``analytics-export-button``):
``analytics-page-title`` / ``analytics-project-badge`` are static
``data-testid``s on ``AnalyticsContainer.jsx``'s header ``Typography``/``Box``.
``analytics-date-preset-{1,7,30,90}`` are wired via the shared
``TabGroupButton``/``TabButtonItem``'s existing ``item.buttonProps`` spread
(``DEFAULT_PRESETS`` array entries) — value is a stable numeric id (days),
state is read via the native ``aria-pressed`` attribute MUI's ``ToggleButton``
sets, never a state-switched testid. ``analytics-date-from-input`` /
``analytics-date-to-input`` are wired via each ``DateTimePicker``'s
``slotProps.textField.inputProps`` (previously a single shared
``datePickerCommonProps`` object — split into a per-field
``getDateFieldSlotProps(testid)`` helper so From/To can carry distinct
testids). ``analytics-tab-*`` are new static ``data-testid``s on each
``BaseTab`` (module-level ``ANALYTICS_TABS`` {label, testid} pairs, MUI's
``Tab``/``ButtonBase`` forwards the prop to the rendered DOM node; the
selected tab's `aria-selected` is native MUI Tab behaviour).
``analytics-loading-indicator`` is a static testid on the
``needsOverview && isFetching`` spinner ``Box`` — used only for an absence
assertion (``to_have_count(0)``/``not_to_be_visible()``) once the analytics
fetch settles, per ``.agents/testing.md`` § Locator policy (absence
assertions count as references). ``analytics-overview-kpi-row`` is a static
testid added on ``AnalyticsOverview.jsx``'s KPI-card row ``Box`` — discovered
during implementation (not in the analyst's original Concrete Handles table)
to prove the Overview tab's content actually rendered, not just that the
spinner disappeared; AFS amended accordingly.

**ELITEA-2312 (Users tab)** — ``AnalyticsUsers.jsx`` had zero pre-existing
testids; all 10 below were added via ``add-data-testid``, straight onto
``automation/testids`` (``EliteaAI/EliteaUI@c7f6b326``). ``analytics-users-*``
static testids sit on the title/count ``Typography``s and the table-header
``Box``. ``analytics-users-search-input`` is wired through a new ``testId``
prop on the shared ``src/components/SearchInput.jsx`` (never a hardcoded
feature-scoped testid on a shared component, per
``.agents/testing.md`` § Locator policy) — passed as
``inputProps={{'data-testid': testId}}`` so it lands on the native
``<input>``, not the wrapping ``Box``. ``analytics-users-row`` /
``analytics-users-row-errors`` repeat identically on every rendered row
(list pattern, mirrors ``artifacts-file-row``) — select a specific row via
``.nth(i)``. The four pagination testids are wired via MUI v7's
non-deprecated ``TablePagination`` ``slotProps`` (``select`` /
``displayedRows`` / ``actions.previousButton`` / ``actions.nextButton``),
confirmed present in ``node_modules/@mui/material/TablePagination``.

**ELITEA-2313 (user detail view, ``AnalyticsUserDetailed.jsx``)** — same-page
state swap (no route change) when a Users-tab row is clicked; zero
pre-existing testids. ``analytics-user-detail-kpi-card`` repeats on all 10
KPI cards (shared ``KpiCard.jsx``, new ``testId`` prop wired on the outer
``Box``). ``analytics-user-detail-kpi-value`` repeats on all 10 cards' VALUE
node specifically (new ``valueTestId`` prop on ``KpiCard.jsx``, same index
order as the card list) — added uniformly, not just on the Errors card,
after live exploration showed the card's own outer ``Box`` carries no
``color`` style at all (constant computed color regardless of the Errors
branch); only the value node reflects the conditional ``color`` prop, so a
card-level check would be a trivially-passing assertion for the other 9
cards. ``analytics-user-detail-chart-tooltip`` is wired on the shared
``ChartTooltip.jsx`` via a render-function ``content`` prop (Recharts injects
``active``/``payload``/``label`` at render time) — only at this call site.
"""

import logging

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.analytics")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring shared by the Overview/Health analytics fetch (`useProjectAnalyticsQuery`)
# — used to wait for the initiating GET to resolve before asserting on the
# loading spinner / Overview KPI content.
ANALYTICS_QUERY_URL_SUBSTRING = "/elitea_core/analytics/prompt_lib/"

# Users-tab query (`useAnalyticsUsersQuery`) — a distinct endpoint from the
# Overview/Health one above; fires on Users-tab mount and again on every
# search-input keystroke change.
ANALYTICS_USERS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_users/prompt_lib/"

# User-detail-view query (`useAnalyticsUserDetailQuery`) — fires once when a
# Users-tab row is clicked (ELITEA-2313).
ANALYTICS_USER_DETAIL_QUERY_URL_SUBSTRING = "/elitea_core/analytics_user_detail/prompt_lib/"


class AnalyticsPage(BasePage):
    """Settings → Analytics page (header, date filter bar, tab bar, loading state)."""

    page_title = LocatorDescriptor(
        testid="analytics-page-title",
        description='Page header title — exact text "Analytics"',
    )
    project_badge = LocatorDescriptor(
        testid="analytics-project-badge",
        description='Project-name badge — "Project: {name}", renders only when a project is selected',
    )

    preset_last_24h = LocatorDescriptor(
        testid="analytics-date-preset-1", description='Date filter preset toggle — "Last 24h"'
    )
    preset_last_7d = LocatorDescriptor(
        testid="analytics-date-preset-7", description='Date filter preset toggle — "Last 7d"'
    )
    preset_last_30d = LocatorDescriptor(
        testid="analytics-date-preset-30", description='Date filter preset toggle — "Last 30d"'
    )
    preset_last_90d = LocatorDescriptor(
        testid="analytics-date-preset-90", description='Date filter preset toggle — "Last 90d"'
    )

    date_from_input = LocatorDescriptor(
        testid="analytics-date-from-input", description="From date/time picker input"
    )
    date_to_input = LocatorDescriptor(testid="analytics-date-to-input", description="To date/time picker input")

    tab_overview = LocatorDescriptor(testid="analytics-tab-overview", description='"Overview" tab')
    tab_costs = LocatorDescriptor(testid="analytics-tab-costs", description='"Costs" tab')
    tab_agents_pipelines = LocatorDescriptor(
        testid="analytics-tab-agents-pipelines", description='"Agents & Pipelines" tab'
    )
    tab_tools = LocatorDescriptor(testid="analytics-tab-tools", description='"Tools" tab')
    tab_users = LocatorDescriptor(testid="analytics-tab-users", description='"Users" tab')
    tab_health = LocatorDescriptor(testid="analytics-tab-health", description='"Health" tab')
    tab_guide = LocatorDescriptor(testid="analytics-tab-guide", description='"Guide" tab')

    loading_indicator = LocatorDescriptor(
        testid="analytics-loading-indicator",
        description="Overview/Health analytics-fetch loading spinner — present only while in flight",
    )
    overview_kpi_row = LocatorDescriptor(
        testid="analytics-overview-kpi-row",
        description="Overview tab's KPI card row (AnalyticsOverview.jsx) — proves the "
        "Overview tab actually rendered content, not just that the spinner disappeared",
    )

    # Users tab (ELITEA-2312)
    users_activity_title = LocatorDescriptor(
        testid="analytics-users-activity-title", description='Users-tab section header — "User Activity"'
    )
    users_count = LocatorDescriptor(
        testid="analytics-users-count", description='Users-tab count subtitle — "{N} users"'
    )
    users_search_input = LocatorDescriptor(
        testid="analytics-users-search-input",
        description='"Search by email" input, top-right of the User Activity card',
    )
    users_table_header = LocatorDescriptor(
        testid="analytics-users-table-header", description="9-column table header row"
    )
    users_loading_indicator = LocatorDescriptor(
        testid="analytics-users-loading-indicator",
        description="Users-tab data-fetch loading spinner — present only while a "
        "(re)fetch is in flight; rows/spinner are mutually exclusive on the same "
        "`isFetching` render branch, so waiting for this to hide also means rows "
        "have (re)rendered",
    )
    users_rows = LocatorDescriptor(
        testid="analytics-users-row",
        description="Repeated per-user data row (same testid on every row — select via .nth(i))",
    )
    users_row_errors = LocatorDescriptor(
        testid="analytics-users-row-errors",
        description="Repeated per-row Errors cell (same testid on every row — select via .nth(i))",
    )
    users_pagination_rows_select = LocatorDescriptor(
        testid="analytics-users-pagination-rows-select", description='"Rows per page" select control'
    )
    users_pagination_range = LocatorDescriptor(
        testid="analytics-users-pagination-range", description='Page-range label — "{from}–{to} of {count}"'
    )
    users_pagination_prev = LocatorDescriptor(
        testid="analytics-users-pagination-prev", description="Previous-page button"
    )
    users_pagination_next = LocatorDescriptor(
        testid="analytics-users-pagination-next", description="Next-page button"
    )

    # User detail view (ELITEA-2313) — same-page state swap when a Users-tab
    # row is clicked, not a route navigation.
    user_detail_back_button = LocatorDescriptor(
        testid="analytics-user-detail-back-button", description="Back arrow to return to the Users-tab table"
    )
    user_detail_title = LocatorDescriptor(
        testid="analytics-user-detail-title", description="Detail-view title — the user's email"
    )
    user_detail_loading_indicator = LocatorDescriptor(
        testid="analytics-user-detail-loading-indicator",
        description="Detail-view data-fetch loading spinner — present only while in flight",
    )
    user_detail_kpi_cards = LocatorDescriptor(
        testid="analytics-user-detail-kpi-card",
        description="Repeated per-KPI card (same testid on all 10 cards — select via .nth(i))",
    )
    user_detail_kpi_values = LocatorDescriptor(
        testid="analytics-user-detail-kpi-value",
        description="Repeated per-KPI card VALUE node (same order as user_detail_kpi_cards, "
        "select via .nth(i)) — used for the Errors-card color check; the color prop is applied "
        "to this Typography specifically, not the outer card Box, so this dedicated node is "
        "required to make the negative-branch (9 default-colored cards) assertion meaningful",
    )
    user_detail_chart_title = LocatorDescriptor(
        testid="analytics-user-detail-chart-title", description='Daily Activity chart title — "Daily Activity"'
    )
    user_detail_chart_subtitle = LocatorDescriptor(
        testid="analytics-user-detail-chart-subtitle",
        description='Daily Activity chart subtitle — "Events by type per day"',
    )
    user_detail_chart_container = LocatorDescriptor(
        testid="analytics-user-detail-chart-container",
        description="Daily Activity chart's wrapping container — used for presence and to "
        "compute hover coordinates",
    )
    user_detail_chart_tooltip = LocatorDescriptor(
        testid="analytics-user-detail-chart-tooltip", description="Recharts hover tooltip content"
    )
    user_detail_models_panel = LocatorDescriptor(
        testid="analytics-user-detail-models-panel", description='"Models Used" summary panel'
    )
    user_detail_tools_panel = LocatorDescriptor(
        testid="analytics-user-detail-tools-panel", description='"Tools Used" summary panel'
    )
    user_detail_agents_panel = LocatorDescriptor(
        testid="analytics-user-detail-agents-panel", description='"Agents & Pipelines Used" summary panel'
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_analytics_query_response(self, response) -> bool:
        """True for the Overview/Health analytics GET (`useProjectAnalyticsQuery`)."""
        return (
            ANALYTICS_QUERY_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def navigate(self) -> None:
        """Navigate to /settings/analytics and wait for the analytics query
        (Overview/Health data fetch, fires on mount) to resolve, then for the
        loading spinner to disappear.

        Waiting on the response — not just DOM visibility of the page shell —
        confirms the page reached a settled state, not merely past the
        initial render (AFS step 8's "no permanent loading state" proof).
        """
        with self.page.expect_response(
            self._is_analytics_query_response, timeout=NAVIGATION_TIMEOUT
        ):
            super().navigate("/settings/analytics")
        self.tab_overview.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        if self.loading_indicator.count() > 0:
            self.loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def get_preset_buttons_in_order(self):
        """Return the four preset-toggle Locators (class-level
        ``LocatorDescriptor`` fields) in their rendered order."""
        return [self.preset_last_24h, self.preset_last_7d, self.preset_last_30d, self.preset_last_90d]

    def get_tabs_in_order(self):
        """Return the seven tab Locators (class-level ``LocatorDescriptor``
        fields) in their rendered order."""
        return [
            self.tab_overview,
            self.tab_costs,
            self.tab_agents_pipelines,
            self.tab_tools,
            self.tab_users,
            self.tab_health,
            self.tab_guide,
        ]

    def is_preset_active(self, preset_locator) -> bool:
        """True if *preset_locator* (one of the ``preset_last_*`` fields) is
        the currently pressed toggle (native ``aria-pressed`` attribute —
        state via a data-*/aria-* attribute on a stable testid, never a
        state-switched testid)."""
        return preset_locator.get_attribute("aria-pressed") == "true"

    def is_tab_selected(self, tab_locator) -> bool:
        """True if *tab_locator* (one of the ``tab_*`` fields) is the
        currently selected tab (native MUI ``aria-selected`` attribute)."""
        return tab_locator.get_attribute("aria-selected") == "true"

    # ------------------------------------------------------------------
    # Users tab (ELITEA-2312)
    # ------------------------------------------------------------------

    def _is_analytics_users_query_response(self, response) -> bool:
        """True for the Users-tab data GET (`useAnalyticsUsersQuery`) — a
        distinct endpoint from the Overview/Health one, fires on tab mount
        and again on every search-input keystroke change."""
        return (
            ANALYTICS_USERS_QUERY_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def _wait_for_users_settled(self) -> None:
        """Wait for the Users-tab render to catch up with a just-resolved
        query response.

        `expect_response` only confirms the network request finished — the
        Redux/RTK-Query state update and the resulting React re-render (which
        flips `isFetching` and swaps the spinner for the row list) can lag a
        response by a render tick. Waiting for the loading indicator to be
        hidden closes that gap: if it's already gone this resolves instantly
        (no false wait), and if it's still showing this waits for the same
        render that also (re)populates the rows — the two are mutually
        exclusive on one `isFetching` branch in `AnalyticsUsers.jsx`.
        """
        self.users_loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def open_users_tab(self) -> None:
        """Click the Users tab and wait for its data query to resolve, then
        for the table header to render."""
        with self.page.expect_response(
            self._is_analytics_users_query_response, timeout=NAVIGATION_TIMEOUT
        ):
            self.tab_users.click()
        self.users_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self._wait_for_users_settled()

    def get_users_table_column_labels(self) -> list[str]:
        """Return the 9 column header labels in rendered order (each header
        cell is a block-level Typography, so splitting the header row's
        aggregate inner text on newline recovers the ordered list)."""
        text = self.users_table_header.inner_text()
        return [line for line in text.split("\n") if line]

    def get_users_row_count(self) -> int:
        """Number of currently-rendered user rows."""
        return self.users_rows.count()

    def get_user_row_errors_value(self, index: int) -> int:
        """Errors-column value (as int) for the row at *index*."""
        return int(self.users_row_errors.nth(index).text_content())

    def get_user_row_identifier(self, index: int) -> str:
        """First column's rendered text (email, or 'User {id}' when no email
        is set) for the row at *index* — read via the row's aggregate inner
        text (mirrors ``get_users_table_column_labels``'s technique), since
        only the Errors cell has its own testid within a row."""
        row_text = self.users_rows.nth(index).inner_text()
        lines = [line for line in row_text.split("\n") if line]
        return lines[0] if lines else ""

    def search_users(self, query: str) -> None:
        """Type *query* into the Users-tab search-by-email input and wait
        for the resulting query to resolve.

        `SearchInput.jsx` wires `onChange` straight off the native `<input>`
        (no MUI TextField/masking layer), and this app's established
        pattern for exactly this shape is `.fill()` (`agents_list_page.py`'s
        `search()`/`clear_search()`) rather than `press_sequentially()` —
        `press_sequentially` was observed here to occasionally drop the
        leading keystroke (a real Playwright/React re-render race, not a
        product defect) while `.fill()` sets the full value atomically in
        one `onChange`, firing the Users query exactly once.

        Waits on that one response via `expect_response`, not
        `wait_for_network()`: `networkidle` is a one-time per-navigation
        lifecycle event in Playwright — once the page has already reached
        it (true by the time this method runs), later calls resolve
        immediately regardless of a request `.fill()` triggers a few
        milliseconds later, so it does not actually wait for the new
        request (observed here as a false-empty filtered result). A second
        wait (`_wait_for_users_settled`) then closes the response-vs-render
        gap (also observed live: response resolved, row count still 0).
        """
        with self.page.expect_response(
            self._is_analytics_users_query_response, timeout=UI_ELEMENT_TIMEOUT
        ):
            self.users_search_input.fill(query)
        self._wait_for_users_settled()

    def clear_users_search(self) -> None:
        """Clear the Users-tab search input so the fixture's page/tab state
        doesn't leak filtered results into a subsequent test.

        Deliberately does NOT wrap the clear in `expect_response` the way
        `search_users` does: clearing back to `search=""` is frequently a
        cache HIT (that exact query already ran once at tab-mount), so
        RTK-Query may serve it from cache with no new network request at
        all — waiting on one would then time out for a request that
        legitimately never fires. `_wait_for_users_settled` handles both
        cases: instant when cached (spinner never shows), or a real wait
        when a fresh fetch is needed.
        """
        if self.users_search_input.input_value():
            self.users_search_input.fill("")
            self._wait_for_users_settled()

    # ------------------------------------------------------------------
    # User detail view (ELITEA-2313)
    # ------------------------------------------------------------------

    def _is_analytics_user_detail_query_response(self, response) -> bool:
        """True for the user-detail GET (`useAnalyticsUserDetailQuery`) —
        fires once when a Users-tab row is clicked."""
        return (
            ANALYTICS_USER_DETAIL_QUERY_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def _wait_for_user_detail_settled(self) -> None:
        """Wait for the detail view's render to catch up with a just-resolved
        query response (same response-vs-render gap as `_wait_for_users_settled`)."""
        self.user_detail_loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def open_user_detail_by_row(self, index: int) -> None:
        """Click the user row at *index* (same testid repeats on every row —
        `.nth(index)`) and wait for the detail view to settle.

        No URL change — `AnalyticsUsers.jsx`'s `handleUserClick` sets local
        `selectedUserId` state, which conditionally renders
        `<AnalyticsUserDetailed>` in place of the table.
        """
        with self.page.expect_response(
            self._is_analytics_user_detail_query_response, timeout=NAVIGATION_TIMEOUT
        ):
            self.users_rows.nth(index).click()
        self.user_detail_title.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self._wait_for_user_detail_settled()

    def get_user_detail_kpi_labels_in_order(self) -> list[str]:
        """Return each rendered KPI card's label (first line of its
        aggregate inner text), in DOM order."""
        cards = self.user_detail_kpi_cards
        return [cards.nth(i).inner_text().split("\n")[0] for i in range(cards.count())]

    def get_panel_summary(self, panel_locator) -> list[str]:
        """Return *panel_locator*'s (one of the ``user_detail_*_panel``
        fields) aggregate inner text split into non-empty lines — line 0 is
        the panel title, line 1 the count label, remaining lines the
        item list (or a single empty-state line when the count is 0)."""
        text = panel_locator.inner_text()
        return [line for line in text.split("\n") if line]

    def back_to_users_table(self, verify_no_refetch: bool = True, no_refetch_timeout: int = 1_500) -> None:
        """Click the detail view's back arrow and confirm the Users-tab
        table is restored.

        By default also confirms NO fresh Users-tab query fires within
        *no_refetch_timeout* ms: `handleBack` only resets local
        `selectedUserId` state — the Users-tab query result was already
        cached by RTK-Query from the original tab-mount fetch (source-
        confirmed). Raises `AssertionError` if a matching request is
        observed instead (a cache-reuse regression).
        """
        if verify_no_refetch:
            try:
                with self.page.expect_response(
                    self._is_analytics_users_query_response, timeout=no_refetch_timeout
                ):
                    self.user_detail_back_button.click()
            except PlaywrightTimeoutError:
                pass  # expected: no matching response observed within the window
            else:
                raise AssertionError(
                    "Expected no fresh Users-tab query on back navigation (the RTK-Query "
                    "cache from the tab-mount fetch should be reused), but a new "
                    "analytics_users/prompt_lib/ request fired"
                )
        else:
            self.user_detail_back_button.click()
        self.users_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
