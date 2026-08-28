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

**ELITEA-2320 (Agents & Pipelines tab, ``AnalyticsAgents.jsx``)** — zero
pre-existing testids; all 17 below added via ``add-data-testid``, straight
onto ``automation/testids`` (``EliteaAI/EliteaUI@019797e6``). Bar chart
(``analytics-agents-chart-*``) and Chat Messages area chart
(``analytics-agents-chat-chart-*``) are each conditionally rendered
(``agentChartData.length > 0`` / ``chat_daily.length > 0``) — testids only
exist in the DOM when their chart is shown. ``analytics-agents-search-input``
reuses the shared ``SearchInput.jsx`` ``testId`` prop wired during ELITEA-2312
(call-site-only change here). ``analytics-agents-row`` /
``analytics-agents-row-errors`` repeat per rendered row (same pattern as the
Users tab). The table header column SET varies by ``isPersonalProject``
(``!isPersonalProject && <Users column>``) — 8 columns for a personal
project, 9 for a non-personal one (``Users`` inserted after ``Runs``). The
four pagination testids reuse the same MUI v7 ``TablePagination``
``slotProps`` pattern as the Users tab.

**ELITEA-2321 (agent/pipeline detail view, ``AnalyticsAgentDetailed.jsx``)** —
same-page state swap (no route change) when an Agents & Pipelines-tab row is
clicked, mirroring ELITEA-2313's user-detail view; zero pre-existing testids.
All 7 distinct testids below added via ``add-data-testid``, straight onto
``automation/testids`` (``EliteaAI/EliteaUI@52eb4729``).
``analytics-agent-detail-kpi-card`` / ``analytics-agent-detail-kpi-value``
reuse the ``testId``/``valueTestId`` prop pair already wired on the shared
``KpiCard.jsx`` (ELITEA-2313's call site) — this is the second call site for
the same shared-component props, not new component work; repeat on all 8
``<KPICard>`` call sites in this file. The "Runs by Day" chart title/
container are conditionally rendered (``daily_usage.length > 0``) — testids
only exist in the DOM when the chart is shown. Users/Tools panels use the
same ``get_panel_summary`` aggregate-text technique as ELITEA-2313's Models/
Tools/Agents panels.
"""

import logging
import re
from datetime import datetime

from playwright.sync_api import Page, expect
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

# Agents & Pipelines tab query (`useAnalyticsAgentsQuery`) — a distinct
# endpoint from Overview/Users; fires on tab mount, on every search-input
# keystroke change, and on a project switch (ELITEA-2320).
ANALYTICS_AGENTS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_agents/prompt_lib/"

# Agent/pipeline-detail-view query (`useAnalyticsAgentDetailQuery`) — fires
# once when an Agents & Pipelines-tab row is clicked (ELITEA-2320).
ANALYTICS_AGENT_DETAIL_QUERY_URL_SUBSTRING = "/elitea_core/analytics_agent_detail/prompt_lib/"

# Tools tab query (`useAnalyticsToolsQuery`) — a distinct endpoint again; fires
# on tab mount, on a search-input change, and on a date-range change while the
# Tools tab is open (ELITEA-2318).
ANALYTICS_TOOLS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_tools/prompt_lib/"

# The DateTimePicker's display format (`format: 'dd/MM/yyyy HH:mm'`, `ampm: false`
# — `AnalyticsContainer.jsx`'s `datePickerCommonProps`).
PICKER_DATETIME_FORMAT = "%d/%m/%Y %H:%M"

# Analytics aggregations over a WIDE range are genuinely slow on a busy project
# — a 30/90-day query regularly needs far longer than NAVIGATION_TIMEOUT
# (measured 2026-08-28: 15s was not enough for `Last 30d`/`Last 90d` while
# `Last 24h`/`Last 7d` answered in a few seconds). Waits on a range-changing
# query therefore use their own, longer budget.
DATA_QUERY_TIMEOUT = 60_000


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

    # ------------------------------------------------------------------
    # Agents & Pipelines tab (ELITEA-2320)
    # ------------------------------------------------------------------
    agents_chart_title = LocatorDescriptor(
        testid="analytics-agents-chart-title",
        description='Bar-chart title — "Most Active Agents & Pipelines", present only when '
        "agentChartData.length > 0",
    )
    agents_chart_subtitle = LocatorDescriptor(
        testid="analytics-agents-chart-subtitle",
        description='Bar-chart subtitle — dynamic "Top {N} by runs"',
    )
    agents_chart_container = LocatorDescriptor(
        testid="analytics-agents-chart-container", description="Bar chart's wrapping container — presence only"
    )
    agents_chat_chart_title = LocatorDescriptor(
        testid="analytics-agents-chat-chart-title",
        description='Chat Messages area-chart title, present only when chat_daily.length > 0',
    )
    agents_chat_chart_subtitle = LocatorDescriptor(
        testid="analytics-agents-chat-chart-subtitle",
        description='Chat Messages area-chart subtitle — static "User messages per day"',
    )
    agents_chat_chart_container = LocatorDescriptor(
        testid="analytics-agents-chat-chart-container",
        description="Chat Messages chart's wrapping container — presence only",
    )
    agents_activity_title = LocatorDescriptor(
        testid="analytics-agents-activity-title",
        description='Table section header — "Agent & Pipeline Activity"',
    )
    agents_count = LocatorDescriptor(
        testid="analytics-agents-count", description='Table count subtitle — "{N} agents & pipelines"'
    )
    agents_search_input = LocatorDescriptor(
        testid="analytics-agents-search-input",
        description='"Search by agent or pipeline name" input, top-right of the Activity card',
    )
    agents_table_header = LocatorDescriptor(
        testid="analytics-agents-table-header",
        description="Table header row — 8 columns (personal project) or 9 (non-personal, adds Users)",
    )
    agents_loading_indicator = LocatorDescriptor(
        testid="analytics-agents-loading-indicator",
        description="Agents-tab data-fetch loading spinner — present only while a (re)fetch is in flight",
    )
    agents_rows = LocatorDescriptor(
        testid="analytics-agents-row",
        description="Repeated per-agent/pipeline data row (same testid on every row — select via .nth(i))",
    )
    agents_row_errors = LocatorDescriptor(
        testid="analytics-agents-row-errors",
        description="Repeated per-row Errors cell (same testid on every row — select via .nth(i))",
    )
    agents_pagination_rows_select = LocatorDescriptor(
        testid="analytics-agents-pagination-rows-select", description='"Rows per page" select control'
    )
    agents_pagination_range = LocatorDescriptor(
        testid="analytics-agents-pagination-range", description='Page-range label — "{from}–{to} of {count}"'
    )
    agents_pagination_prev = LocatorDescriptor(
        testid="analytics-agents-pagination-prev", description="Previous-page button"
    )
    agents_pagination_next = LocatorDescriptor(
        testid="analytics-agents-pagination-next", description="Next-page button"
    )

    # ------------------------------------------------------------------
    # Agent/pipeline detail view (ELITEA-2321) — same-page state swap when
    # an Agents & Pipelines-tab row is clicked, not a route navigation.
    # ------------------------------------------------------------------
    agent_detail_back_button = LocatorDescriptor(
        testid="analytics-agent-detail-back-button",
        description="Back arrow to return to the Agents & Pipelines-tab table",
    )
    agent_detail_title = LocatorDescriptor(
        testid="analytics-agent-detail-title", description="Detail-view title — the agent/pipeline's name"
    )
    agent_detail_loading_indicator = LocatorDescriptor(
        testid="analytics-agent-detail-loading-indicator",
        description="Detail-view data-fetch loading spinner — present only while in flight",
    )
    agent_detail_kpi_cards = LocatorDescriptor(
        testid="analytics-agent-detail-kpi-card",
        description="Repeated per-KPI card (same testid on all 8 cards — select via .nth(i))",
    )
    agent_detail_kpi_values = LocatorDescriptor(
        testid="analytics-agent-detail-kpi-value",
        description="Repeated per-KPI card VALUE node (same order as agent_detail_kpi_cards, "
        "select via .nth(i)) — used for the Errors-card color check; the color prop is applied "
        "to this Typography specifically, not the outer card Box (same shape as "
        "user_detail_kpi_values)",
    )
    agent_detail_chart_title = LocatorDescriptor(
        testid="analytics-agent-detail-chart-title",
        description='"Runs by Day" chart title, present only when daily_usage.length > 0',
    )
    agent_detail_chart_container = LocatorDescriptor(
        testid="analytics-agent-detail-chart-container",
        description="Runs by Day chart's wrapping container — used for presence only",
    )
    agent_detail_users_panel = LocatorDescriptor(
        testid="analytics-agent-detail-users-panel", description='"Users" summary panel'
    )
    agent_detail_tools_panel = LocatorDescriptor(
        testid="analytics-agent-detail-tools-panel", description='"Tools" summary panel'
    )


    # ------------------------------------------------------------------
    # Date-filter pickers + Overview/Tools content (ELITEA-2314..2319)
    # ------------------------------------------------------------------
    preset_custom = LocatorDescriptor(
        testid="analytics-date-preset-custom",
        description='Fifth "Custom" preset chip — rendered ONLY while a picker has been '
        "edited directly (`selectedDatePreset === 'custom'`); absent otherwise",
    )
    date_from_open_button = LocatorDescriptor(
        testid="analytics-date-from-open-button", description="From picker's calendar icon button"
    )
    date_to_open_button = LocatorDescriptor(
        testid="analytics-date-to-open-button", description="To picker's calendar icon button"
    )
    date_from_popper = LocatorDescriptor(
        testid="analytics-date-from-popper",
        description="From picker's popper root — the scoping parent for MUI's internal "
        "calendar cells / action buttons (present only while the picker is open)",
    )
    date_to_popper = LocatorDescriptor(
        testid="analytics-date-to-popper", description="To picker's popper root (same role as above)"
    )

    overview_kpi_values = LocatorDescriptor(
        testid="analytics-overview-kpi-value",
        description="Repeated per-KPI VALUE node on the Overview tab (same testid on all 8 "
        "cards, DOM order = TEAM, AI ACTIVE, LLM CALLS, TOOL RUNS, CHAT MSG, "
        "AGENT & PIPELINE RUNS, TOKENS, COST — select via .nth(i))",
    )
    overview_daily_chart_container = LocatorDescriptor(
        testid="analytics-overview-daily-chart-container",
        description="Daily Activity chart wrapper — scoping parent for the recharts X-axis ticks",
    )
    overview_leaderboard = LocatorDescriptor(
        testid="analytics-overview-leaderboard",
        description='"Top 5 AI Adopters" row container — rendered ONLY when top_ai_users is '
        "non-empty (the empty branch renders a \"No AI activity data.\" line instead)",
    )
    overview_leaderboard_rows = LocatorDescriptor(
        testid="analytics-overview-leaderboard-row",
        description="Repeated per-adopter leaderboard row (select via .nth(i))",
    )
    overview_model_usage_table = LocatorDescriptor(
        testid="analytics-overview-model-usage-table",
        description='"Model Usage Breakdown" card — the whole component returns null when the '
        "response's models list is empty, so absence is a real product branch",
    )
    overview_model_usage_rows = LocatorDescriptor(
        testid="analytics-overview-model-usage-row",
        description="Repeated per-model row (select via .nth(i))",
    )

    tools_details_title = LocatorDescriptor(
        testid="analytics-tools-details-title", description='Tools-tab section header — "Tool Details"'
    )
    tools_count = LocatorDescriptor(
        testid="analytics-tools-count", description='Tools-tab count subtitle — "{N} tools"'
    )
    tools_table_header = LocatorDescriptor(
        testid="analytics-tools-table-header",
        description="Tools-tab table header row (Tool, Calls, Users, Avg Latency, Errors)",
    )
    tools_loading_indicator = LocatorDescriptor(
        testid="analytics-tools-loading-indicator",
        description="Tools-tab data-fetch spinner — present only while a (re)fetch is in flight",
    )
    tools_rows = LocatorDescriptor(
        testid="analytics-tools-row",
        description="Repeated per-tool data row (same testid on every row — select via .nth(i))",
    )

    # ------------------------------------------------------------------
    # Scoped raw sub-selectors — `.agents/testing.md` § Locator policy,
    # #579 sanctioned exception 1 (third-party widget subtree).
    #
    # Everything inside a DateTimePicker popper (day cells, month header,
    # month-nav arrows, the Clear/Apply action buttons) and everything inside
    # a recharts plot (axis tick labels) is rendered by the LIBRARY, not by
    # EliteaUI JSX — MUI's `PickersDay`/`PickersActionBar`/`PickersCalendarHeader`
    # and recharts' SVG internals accept no `data-testid` without overriding
    # their slot components, which would be a functional change (forbidden by
    # `add-data-testid` § zero-functional-impact). Each constant below is used
    # ONLY chained off a real app testid parent (`date_*_popper`,
    # `overview_daily_chart_container`), never as a page-level handle. Do NOT
    # extend this list to any element that COULD carry a testid.
    # ------------------------------------------------------------------
    PICKER_DAY_CELL = "button.MuiPickersDay-root"
    PICKER_MONTH_LABEL = ".MuiPickersCalendarHeader-label"
    PICKER_PREV_MONTH_BUTTON = 'button[aria-label="Previous month"]'
    PICKER_NEXT_MONTH_BUTTON = 'button[aria-label="Next month"]'
    PICKER_ACTION_BUTTON = ".MuiDialogActions-root button"
    CHART_X_AXIS_TICK = ".recharts-xAxis .recharts-cartesian-axis-tick-value"

    # Sidebar project-selector combobox — pre-existing testid, duplicated
    # here (not cross-imported from ChatPage) per the project's page-object
    # convention (same shape as AdminUsersPage.project_selector_trigger).
    # Needed to exercise the personal-vs-non-personal column-set branch
    # (step 5's Axis-2 addition) without leaving this page.
    project_selector_trigger = LocatorDescriptor(
        testid="project-selector-trigger-combobox",
        description="Sidebar project selector combobox trigger.",
    )

    # Project-selector dropdown options — same shared select-option-{value}
    # family (SingleSelectMenuItem.jsx) as ChatPage.SELECT_OPTION /
    # AdminUsersPage.SELECT_OPTION — reuse the pattern, don't invent a new one.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

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

    # ------------------------------------------------------------------
    # Agents & Pipelines tab (ELITEA-2320)
    # ------------------------------------------------------------------

    def _is_analytics_agents_query_response(self, response) -> bool:
        """True for the Agents & Pipelines-tab data GET (`useAnalyticsAgentsQuery`)
        — a distinct endpoint from Overview/Users, fires on tab mount, on
        every search-input keystroke change, and on a project switch."""
        return (
            ANALYTICS_AGENTS_QUERY_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def _wait_for_agents_settled(self) -> None:
        """Wait for the Agents-tab render to catch up with a just-resolved
        query response (same response-vs-render gap as `_wait_for_users_settled`)."""
        self.agents_loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def open_agents_pipelines_tab(self) -> None:
        """Click the Agents & Pipelines tab and wait for its data query to
        resolve, then for the table header to render."""
        with self.page.expect_response(
            self._is_analytics_agents_query_response, timeout=NAVIGATION_TIMEOUT
        ):
            self.tab_agents_pipelines.click()
        self.agents_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self._wait_for_agents_settled()

    def get_agents_table_column_labels(self) -> list[str]:
        """Return the table column header labels in rendered order (each
        header cell is a block-level Typography, so splitting the header
        row's aggregate inner text on newline recovers the ordered list).
        Column SET varies by `isPersonalProject` — 8 columns for a personal
        project, 9 (Users inserted after Runs) for a non-personal one."""
        text = self.agents_table_header.inner_text()
        return [line for line in text.split("\n") if line]

    def get_agents_row_count(self) -> int:
        """Number of currently-rendered agent/pipeline rows."""
        return self.agents_rows.count()

    def get_agent_row_errors_value(self, index: int) -> int:
        """Errors-column value (as int) for the row at *index*."""
        return int(self.agents_row_errors.nth(index).text_content())

    def switch_project(self, project_id: str, timeout: int = NAVIGATION_TIMEOUT) -> None:
        """Switch the sidebar's active project while staying on the
        Agents & Pipelines tab, then wait for the render to settle.

        Used to exercise the `isPersonalProject` column-set branch (step 5's
        Axis-2 addition) without leaving `/settings/analytics` — the sidebar
        project selector is app-wide chrome, not scoped to any one page.

        Deliberately does NOT wrap the click in `expect_response` the way
        `open_agents_pipelines_tab` does: switching BACK to a project whose
        analytics query (same date range, same search="") already resolved
        earlier in the same test is frequently a RTK-Query cache HIT — no
        new network request fires at all (observed live switching 400 -> 399
        after 399 was already fetched at tab-mount) — so waiting on one would
        time out for a request that legitimately never fires (same reasoning
        as `clear_users_search`). `wait_for_network` + `_wait_for_agents_settled`
        handle both cases: instant when cached, a real wait when a fresh
        fetch is needed.
        """
        self.project_selector_trigger.click()
        option = self.page.locator(self.SELECT_OPTION.format(project_id))
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        self.wait_for_network(timeout=timeout)
        self._wait_for_agents_settled()

    def open_agent_detail_by_row(self, index: int) -> None:
        """Click the agent/pipeline row at *index* (same testid repeats on
        every row — `.nth(index)`) and wait for the detail-view query to
        resolve.

        No dedicated detail-view page object yet (AFS: full detail-sub-view
        content is out of scope for ELITEA-2320) — callers confirm the
        navigation via the response status plus `agents_table_header`
        leaving the DOM (same-page state swap, `AnalyticsAgents.jsx`'s
        `handleAgentClick` sets local `selectedAgent` state).
        """
        with self.page.expect_response(
            self._is_analytics_agent_detail_query_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            self.agents_rows.nth(index).click()
        return response_info.value

    def _is_analytics_agent_detail_query_response(self, response) -> bool:
        """True for the agent/pipeline-detail GET (`useAnalyticsAgentDetailQuery`)
        — fires once when an Agents & Pipelines-tab row is clicked."""
        return (
            ANALYTICS_AGENT_DETAIL_QUERY_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def get_agent_row_identifier(self, index: int) -> str:
        """First column's rendered text (agent/pipeline name) for the row at
        *index* — read via the row's aggregate inner text (mirrors
        ``get_user_row_identifier``'s technique), since only the Errors cell
        has its own testid within a row."""
        row_text = self.agents_rows.nth(index).inner_text()
        lines = [line for line in row_text.split("\n") if line]
        return lines[0] if lines else ""

    # ------------------------------------------------------------------
    # Agent/pipeline detail view (ELITEA-2321)
    # ------------------------------------------------------------------

    def _wait_for_agent_detail_settled(self) -> None:
        """Wait for the detail view's render to catch up with a just-resolved
        query response (same response-vs-render gap as `_wait_for_users_settled`)."""
        self.agent_detail_loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def open_agent_detail(self, index: int) -> None:
        """Click the agent/pipeline row at *index* and wait for the detail
        view to fully settle (network response + title visible + loading
        spinner hidden) — a superset of `open_agent_detail_by_row`, which
        only waits on the network response (kept for ELITEA-2320's own
        navigation-only assertions)."""
        self.open_agent_detail_by_row(index)
        self.agent_detail_title.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self._wait_for_agent_detail_settled()

    def get_agent_detail_kpi_labels_in_order(self) -> list[str]:
        """Return each rendered KPI card's label (first line of its
        aggregate inner text), in DOM order."""
        cards = self.agent_detail_kpi_cards
        return [cards.nth(i).inner_text().split("\n")[0] for i in range(cards.count())]

    def back_to_agents_table(self, verify_no_refetch: bool = True, no_refetch_timeout: int = 1_500) -> None:
        """Click the detail view's back arrow and confirm the Agents &
        Pipelines-tab table is restored.

        By default also confirms NO fresh Agents-tab query fires within
        *no_refetch_timeout* ms: `handleBack` only resets local
        `selectedAgent` state — the Agents-tab query result was already
        cached by RTK-Query from the original tab-mount fetch (source-
        confirmed, mirrors `back_to_users_table`'s identical reasoning).
        Raises `AssertionError` if a matching request is observed instead
        (a cache-reuse regression).
        """
        if verify_no_refetch:
            try:
                with self.page.expect_response(
                    self._is_analytics_agents_query_response, timeout=no_refetch_timeout
                ):
                    self.agent_detail_back_button.click()
            except PlaywrightTimeoutError:
                pass  # expected: no matching response observed within the window
            else:
                raise AssertionError(
                    "Expected no fresh Agents & Pipelines-tab query on back navigation (the "
                    "RTK-Query cache from the tab-mount fetch should be reused), but a new "
                    "analytics_agents/prompt_lib/ request fired"
                )
        else:
            self.agent_detail_back_button.click()
        self.agents_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    # ------------------------------------------------------------------
    # Date filter — presets, pickers, and range reading (ELITEA-2314..2319)
    # ------------------------------------------------------------------
    def _is_analytics_tools_query_response(self, response) -> bool:
        """True for the Tools-tab data GET (`useAnalyticsToolsQuery`)."""
        return ANALYTICS_TOOLS_QUERY_URL_SUBSTRING in response.url and response.request.method == "GET"

    # Tab/endpoint predicates keyed by the surface a caller is waiting on, so
    # one preset-click helper can serve every tab (ELITEA-2318).
    def _query_predicate(self, surface: str):
        predicates = {
            "overview": self._is_analytics_query_response,
            "users": self._is_analytics_users_query_response,
            "agents": self._is_analytics_agents_query_response,
            "tools": self._is_analytics_tools_query_response,
        }
        return predicates[surface]

    def get_date_from_text(self) -> str:
        """Raw From input value, as displayed (`dd/MM/yyyy HH:mm`)."""
        return self.date_from_input.input_value()

    def get_date_to_text(self) -> str:
        """Raw To input value, as displayed (`dd/MM/yyyy HH:mm`)."""
        return self.date_to_input.input_value()

    def get_date_range(self) -> tuple[datetime, datetime]:
        """Both picker values parsed into naive local `datetime`s."""
        return (
            datetime.strptime(self.get_date_from_text(), PICKER_DATETIME_FORMAT),
            datetime.strptime(self.get_date_to_text(), PICKER_DATETIME_FORMAT),
        )

    def get_pressed_preset_labels(self) -> list[str]:
        """Labels of every date preset currently `aria-pressed="true"`.

        Includes the conditional "Custom" chip when it is rendered, so a
        caller can assert mutual exclusivity across the whole control.
        """
        pressed = []
        for locator, label in (
            (self.preset_last_24h, "Last 24h"),
            (self.preset_last_7d, "Last 7d"),
            (self.preset_last_30d, "Last 30d"),
            (self.preset_last_90d, "Last 90d"),
            (self.preset_custom, "Custom"),
        ):
            if locator.count() > 0 and locator.get_attribute("aria-pressed") == "true":
                pressed.append(label)
        return pressed

    def click_preset(self, preset_locator, surface: str = "overview", timeout: int = DATA_QUERY_TIMEOUT):
        """Click a date preset and return the analytics response it triggers.

        *surface* selects which endpoint to wait on ("overview", "users",
        "agents", "tools") — the visible tab decides which query re-fires.
        Returning the `Response` lets the caller use the SYSTEM's own payload
        as the assertion oracle (`.agents/testing.md` § Fidelity policy)
        instead of a hand-written expectation.
        """
        with self.page.expect_response(self._query_predicate(surface), timeout=timeout) as info:
            preset_locator.click()
        return info.value

    def wait_for_overview_settled(self) -> None:
        """Wait for the Overview subtree to be back on screen after a refetch.

        The Overview body unmounts while `needsOverview && isFetching`, so the
        KPI row reappearing is the proof the content re-rendered — not merely
        that a request completed.
        """
        if self.loading_indicator.count() > 0:
            self.loading_indicator.wait_for(state="hidden", timeout=DATA_QUERY_TIMEOUT)
        self.overview_kpi_row.wait_for(state="visible", timeout=DATA_QUERY_TIMEOUT)

    # -- picker popper -------------------------------------------------
    def _popper(self, field: str):
        return self.date_from_popper if field == "from" else self.date_to_popper

    def open_date_picker(self, field: str) -> None:
        """Open the "from"/"to" DateTimePicker via its calendar icon button."""
        (self.date_from_open_button if field == "from" else self.date_to_open_button).click()
        self._popper(field).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_picker_month_label(self, field: str) -> str:
        """Month/year the open picker is displaying, e.g. "May 2026".

        #579-scoped raw handle: MUI's `PickersCalendarHeader` label, read
        strictly inside the popper's own app testid.
        """
        return self._popper(field).locator(self.PICKER_MONTH_LABEL).inner_text().strip()

    def get_picker_day_cell(self, field: str, day: int):
        """Locator for a single day cell in the open picker.

        #579-scoped raw handle: MUI renders day cells as `PickersDay` buttons
        with no testid hook; scoped inside the popper's app testid and matched
        on exact day text.

        Waits for the match to settle to exactly ONE element: MUI slides
        between month grids and keeps the outgoing grid mounted for the
        duration of the transition, so right after a month change the same day
        number legitimately resolves to 2-4 nodes (measured live: 4 during a
        3-month walk back). This is a condition wait on the transition
        finishing, not a sleep.
        """
        cell = (
            self._popper(field)
            .locator(self.PICKER_DAY_CELL)
            .filter(has_text=re.compile(rf"^{day}$"))
        )
        expect(cell).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
        return cell

    def picker_month_nav(self, field: str, direction: str):
        """Previous/next-month arrow of the open picker (#579-scoped raw handle)."""
        selector = self.PICKER_PREV_MONTH_BUTTON if direction == "prev" else self.PICKER_NEXT_MONTH_BUTTON
        return self._popper(field).locator(selector)

    def picker_apply_button(self, field: str):
        """The popper's confirm button.

        Labelled **"Apply"** (`localeText.okButtonLabel`), not "Ok" as several
        TMS case texts say. #579-scoped raw handle: MUI's `PickersActionBar`
        renders Clear/Apply itself and `slotProps.actionBar` reaches only the
        container, never the individual buttons.
        """
        return (
            self._popper(field)
            .locator(self.PICKER_ACTION_BUTTON)
            .filter(has_text=re.compile(r"^Apply$"))
        )

    def go_to_picker_month(self, field: str, month_label: str, max_steps: int = 6) -> None:
        """Click "Previous month" until the open picker displays *month_label*.

        Bounded loop (the callers move at most a few months), so a mismatch
        fails loudly instead of spinning.
        """
        for _ in range(max_steps):
            current = self.get_picker_month_label(field)
            if current == month_label:
                return
            self.picker_month_nav(field, "prev").click()
            # Condition wait on the header actually changing (MUI slides the
            # month grid) — never a fixed sleep.
            expect(self._popper(field).locator(self.PICKER_MONTH_LABEL)).not_to_have_text(
                current, timeout=UI_ELEMENT_TIMEOUT
            )
        raise AssertionError(
            f"Picker {field!r} never reached month {month_label!r} within {max_steps} "
            f"'Previous month' clicks (last shown: {self.get_picker_month_label(field)!r})"
        )

    def select_picker_day(self, field: str, day: int, surface: str = "overview", timeout: int = DATA_QUERY_TIMEOUT):
        """Click a day cell and return the analytics response it triggers.

        The picker's `onChange` fires on the day click itself — **not** on
        Apply (live-confirmed: no request follows the Apply click), so the
        response wait belongs here.
        """
        with self.page.expect_response(self._query_predicate(surface), timeout=timeout) as info:
            self.get_picker_day_cell(field, day).click()
        return info.value

    def apply_picker(self, field: str) -> None:
        """Confirm the open picker (the "Apply" action) and wait for it to close."""
        self.picker_apply_button(field).click()
        self._popper(field).wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def assert_no_analytics_request(self, surface: str = "overview", window_ms: int = 1_500) -> None:
        """Assert no request fires on *surface* within *window_ms*.

        Used by ELITEA-2316: "no data changed to the incorrect timespan" is
        only really proven if the app never ASKED for the incorrect timespan.
        """
        try:
            with self.page.expect_response(self._query_predicate(surface), timeout=window_ms):
                pass
        except PlaywrightTimeoutError:
            return  # expected: nothing fired
        raise AssertionError(
            f"Expected no {surface} analytics request within {window_ms}ms, but one fired"
        )

    # -- Overview content ---------------------------------------------
    def get_overview_kpi_values(self) -> list[str]:
        """The 8 Overview KPI values in DOM order."""
        return [v.strip() for v in self.overview_kpi_values.all_inner_texts()]

    def get_daily_chart_tick_labels(self) -> list[str]:
        """Rendered X-axis tick labels ("MM-DD") of the Daily Activity chart.

        #579-scoped raw handle: recharts draws its axis as internal SVG
        `<text>` nodes; scoped strictly inside the chart container's app
        testid. Recharts THINS labels, so callers assert the span/endpoints,
        never a tick-per-day count.
        """
        ticks = self.overview_daily_chart_container.locator(self.CHART_X_AXIS_TICK)
        # `all_inner_texts()` yields None for SVG <text> nodes (no innerText on
        # SVG elements) — textContent is the correct read here.
        return [t.strip() for t in ticks.all_text_contents()]

    def get_leaderboard_row_count(self) -> int:
        """Rendered "Top 5 AI Adopters" rows (0 when the empty branch shows)."""
        return self.overview_leaderboard_rows.count()

    def get_leaderboard_row_text(self, index: int) -> str:
        """Aggregate inner text of one leaderboard row (rank, email, stats, score)."""
        return self.overview_leaderboard_rows.nth(index).inner_text()

    def get_model_usage_row_count(self) -> int:
        """Rendered "Model Usage Breakdown" rows (0 when the card is absent)."""
        return self.overview_model_usage_rows.count()

    # -- Tools tab -----------------------------------------------------
    def open_tools_tab(self, timeout: int = DATA_QUERY_TIMEOUT):
        """Click the Tools tab, wait for its data query, return the response."""
        with self.page.expect_response(self._is_analytics_tools_query_response, timeout=timeout) as info:
            self.tab_tools.click()
        self.tools_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        if self.tools_loading_indicator.count() > 0:
            self.tools_loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
        return info.value

    def open_tab_awaiting(self, tab_locator, surface: str, timeout: int = DATA_QUERY_TIMEOUT):
        """Click *tab_locator* and return the response of *surface*'s query.

        Additive sibling of `open_users_tab()`/`open_agents_pipelines_tab()`
        (both keep their existing signatures and callers) for cases that need
        the response BODY as their assertion oracle.
        """
        with self.page.expect_response(self._query_predicate(surface), timeout=timeout) as info:
            tab_locator.click()
        return info.value

    def get_tools_row_count(self) -> int:
        """Number of currently-rendered tool rows."""
        return self.tools_rows.count()
