"""Analytics page object (Settings → Analytics).

URL: /settings/analytics

Covers the page shell: header (title + project badge), the date-range filter
bar (four presets + From/To pickers), the seven-tab bar, the Overview-data
loading state (ELITEA-2310), and the Users tab's panel content — "User
Activity" header/count, search-by-email input, the 9-column table (header +
repeated data rows), and pagination controls (ELITEA-2312), the Agents &
Pipelines tab and both detail views (ELITEA-2320/2321), and — added for the
settings-w06 batch — the Overview tab's KPI cards (ELITEA-2311), the Tools tab
(ELITEA-2322), the Health tab (ELITEA-2324) and the Guide tab (ELITEA-2325).
The Costs and Tokens tab bodies remain out of scope.

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

**ELITEA-2311 (Overview KPI cards)** — the card and value nodes already carried
``analytics-overview-kpi-card`` / ``-value``; the label, subtitle, value-suffix
and badge nodes were added as four new attribute-only props on the SHARED
``components/KpiCard.jsx`` (``labelTestId`` / ``subtitleTestId`` /
``valueSuffixTestId`` / ``badgeTestId``), wired ONLY at
``AnalyticsOverview.jsx``'s 8 call sites — the same shared component is also
consumed by Costs/Tokens/UserDetailed/AgentDetailed/UsageSummary and those call
sites are deliberately untouched (``.agents/testing.md`` § Locator policy,
shared-component rule). ``analytics-overview-kpi-badge`` is CONDITIONAL
(``kpis.adoption_rate > 0``) and is referenced in both directions — presence +
text + colour in the positive branch, ``to_have_count(0)`` in the zero branch.

**ELITEA-2322 (Tools tab, ``AnalyticsTools.jsx``)** — chart subtitle/container,
details title, count, table header, rows and loading indicator pre-existed;
``analytics-tools-chart-title``, ``-search-input`` (call-site ``testId`` prop on
the shared ``SearchInput.jsx``), ``-row-errors``, ``-pagination-rows-select``,
``-pagination-range`` and ``-pagination-rows-menu`` were added
(``EliteaAI/EliteaUI@bc50bd9d`` + ``@aad6227c``). Recharts' bar ``<path>`` and
X-axis tick ``<text>`` nodes are library-internal and cannot carry an app
testid — reached as raw handles SCOPED inside the
``analytics-tools-chart-container`` testid parent (#579 exception 1), declared
in each method's docstring.

**ELITEA-2324 (Health tab, ``AnalyticsHealth.jsx``)** — zero pre-existing
testids; all 8 added. The tab SHARES the Overview endpoint
(``needsOverview = activeTab === 0 || 6``), so opening it on an unchanged range
is usually an RTK-Query cache hit that fires no request — ``open_health_tab``
therefore waits on rendered content, and the oracle body is captured around the
preset click instead. The chart renders no legend, so the series NAMES exist
only inside the hover tooltip (``analytics-health-chart-tooltip``, wired via the
shared ``ChartTooltip.jsx``'s existing ``testId`` prop).

**ELITEA-2325 (Guide tab, ``AnalyticsGuide.jsx``)** — zero pre-existing testids;
all 7 added. The tab is a pure render of the bundled ``GUIDE_SECTIONS`` constant
and issues NO network request at all, so ``open_guide_tab`` waits on the first
section rather than on a response. The ``Calculation:`` / ``Data source:``
LABELS deliberately carry no testid (asserted through the metric block's own
text), and their VALUE testids sit inside ``{m.calculation && ...}`` /
``{m.source && ...}`` conditional subtrees — referenced in both directions by
the label-iff-value pairing assertion.
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

# Agents & Pipelines tab query (`useAnalyticsAgentsQuery`) — a distinct
# endpoint from Overview/Users; fires on tab mount, on every search-input
# keystroke change, and on a project switch (ELITEA-2320).
ANALYTICS_AGENTS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_agents/prompt_lib/"

# Agent/pipeline-detail-view query (`useAnalyticsAgentDetailQuery`) — fires
# once when an Agents & Pipelines-tab row is clicked (ELITEA-2320).
ANALYTICS_AGENT_DETAIL_QUERY_URL_SUBSTRING = "/elitea_core/analytics_agent_detail/prompt_lib/"

# Tools tab query (`useAnalyticsToolsQuery`) — a distinct endpoint from
# Overview/Users/Agents; fires on tab mount, on every search-input change and
# on any pagination change (ELITEA-2322).
ANALYTICS_TOOLS_QUERY_URL_SUBSTRING = "/elitea_core/analytics_tools/prompt_lib/"

# Recharts-internal render nodes — library DOM that cannot carry an app
# testid (`.agents/testing.md` § Locator policy, #579 exception 1). ALWAYS
# used scoped inside a real app-testid parent (the chart containers below),
# never as a free-floating page-level handle.
RECHARTS_BAR_FILL = ".recharts-bar-rectangle path"
RECHARTS_X_AXIS_TICK = ".recharts-xAxis .recharts-cartesian-axis-tick-value"
RECHARTS_AREA_SERIES = ".recharts-area-area"


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
    # Overview tab KPI cards (ELITEA-2311) — eight repeated cards; the
    # label/subtitle/value-suffix/badge nodes are addressed through the
    # shared `components/KpiCard.jsx`'s per-node testId props, wired at
    # `AnalyticsOverview.jsx`'s 8 call sites ONLY (KpiCard is also consumed
    # by Costs/Tokens/UserDetailed/AgentDetailed/UsageSummary — untouched).
    # ------------------------------------------------------------------
    overview_kpi_cards = LocatorDescriptor(
        testid="analytics-overview-kpi-card",
        description="Repeated Overview KPI card (same testid on all 8 — select via .nth(i))",
    )
    overview_kpi_labels = LocatorDescriptor(
        testid="analytics-overview-kpi-label",
        description="Repeated KPI card label node (TEAM / AI ACTIVE / ... — same rendered order as the cards)",
    )
    overview_kpi_values = LocatorDescriptor(
        testid="analytics-overview-kpi-value",
        description="Repeated KPI card value node (same rendered order as the cards)",
    )
    overview_kpi_subtitles = LocatorDescriptor(
        testid="analytics-overview-kpi-subtitle",
        description="Repeated KPI card subtitle node (same rendered order as the cards)",
    )
    overview_kpi_value_suffix = LocatorDescriptor(
        testid="analytics-overview-kpi-value-suffix",
        description='TEAM card\'s "of {Y}" value suffix — the only Overview card passing valueSuffix',
    )
    overview_kpi_badge = LocatorDescriptor(
        testid="analytics-overview-kpi-badge",
        description="AI ACTIVE card's green adoption badge — CONDITIONAL: rendered only when "
        "`kpis.adoption_rate > 0`, so it is also used for an absence assertion "
        "(`to_have_count(0)`) in the zero branch",
    )

    # ------------------------------------------------------------------
    # Tools tab (ELITEA-2322)
    # ------------------------------------------------------------------
    tools_chart_title = LocatorDescriptor(
        testid="analytics-tools-chart-title",
        description='Bar-chart title — "Most Popular Tools", present only when toolChartData.length > 0',
    )
    tools_chart_subtitle = LocatorDescriptor(
        testid="analytics-tools-chart-subtitle",
        description='Bar-chart subtitle — dynamic "Top {N} by usage"',
    )
    tools_chart_container = LocatorDescriptor(
        testid="analytics-tools-chart-container",
        description="Bar chart's wrapping container — also the testid parent scoping the "
        "recharts-internal bar/axis raw handles (#579 exception 1)",
    )
    tools_details_title = LocatorDescriptor(
        testid="analytics-tools-details-title", description='Table section header — "Tool Details"'
    )
    tools_count = LocatorDescriptor(
        testid="analytics-tools-count", description='Table count subtitle — "{N} tools"'
    )
    tools_search_input = LocatorDescriptor(
        testid="analytics-tools-search-input",
        description='"Search by tool name" input, top-right of the Tool Details card',
    )
    tools_table_header = LocatorDescriptor(
        testid="analytics-tools-table-header", description="5-column table header row"
    )
    tools_loading_indicator = LocatorDescriptor(
        testid="analytics-tools-loading-indicator",
        description="Tools-tab data-fetch loading spinner — present only while a (re)fetch is in flight",
    )
    tools_rows = LocatorDescriptor(
        testid="analytics-tools-row",
        description="Repeated per-tool data row (same testid on every row — select via .nth(i))",
    )
    tools_row_errors = LocatorDescriptor(
        testid="analytics-tools-row-errors",
        description="Repeated per-row Errors cell (same testid on every row — select via .nth(i))",
    )
    tools_pagination_rows_select = LocatorDescriptor(
        testid="analytics-tools-pagination-rows-select", description='"Rows per page" select control'
    )
    tools_pagination_range = LocatorDescriptor(
        testid="analytics-tools-pagination-range", description='Page-range label — "{from}–{to} of {count}"'
    )
    tools_pagination_rows_menu = LocatorDescriptor(
        testid="analytics-tools-pagination-rows-menu",
        description='"Rows per page" dropdown menu list — the app-testid parent scoping the '
        "MUI-generated option items (#579 exception 1)",
    )

    # ------------------------------------------------------------------
    # Health tab (ELITEA-2324)
    # ------------------------------------------------------------------
    health_chart_title = LocatorDescriptor(
        testid="analytics-health-chart-title", description='Area-chart title — "Requests vs Errors"'
    )
    health_chart_subtitle = LocatorDescriptor(
        testid="analytics-health-chart-subtitle",
        description='Area-chart subtitle — "Total requests trend with error overlay"',
    )
    health_chart_container = LocatorDescriptor(
        testid="analytics-health-chart-container",
        description="Area chart's wrapping container — also the testid parent scoping the "
        "recharts-internal area-series raw handle (#579 exception 1)",
    )
    health_chart_tooltip = LocatorDescriptor(
        testid="analytics-health-chart-tooltip",
        description="Recharts hover tooltip (shared ChartTooltip, wired via its testId prop) — "
        "the ONLY place the two series' names exist in the DOM (the chart renders no legend)",
    )
    health_table_title = LocatorDescriptor(
        testid="analytics-health-table-title", description='Table section header — "Health by Event Type"'
    )
    health_table_header = LocatorDescriptor(
        testid="analytics-health-table-header", description="5-column table header row"
    )
    health_rows = LocatorDescriptor(
        testid="analytics-health-row",
        description="Repeated per-event-type data row (same testid on every row — select via .nth(i))",
    )
    health_row_event_type = LocatorDescriptor(
        testid="analytics-health-row-event-type",
        description="Repeated per-row event-type text node (same rendered order as health_rows)",
    )

    # ------------------------------------------------------------------
    # Guide tab (ELITEA-2325) — static content, no network at all
    # ------------------------------------------------------------------
    guide_sections = LocatorDescriptor(
        testid="analytics-guide-section",
        description="Repeated documentation section card (same testid on all 9 — select via .nth(i))",
    )
    guide_section_titles = LocatorDescriptor(
        testid="analytics-guide-section-title",
        description="Repeated section title node (same rendered order as guide_sections)",
    )
    guide_metrics = LocatorDescriptor(
        testid="analytics-guide-metric",
        description="Repeated per-metric block (same testid on all 43 — select via .nth(i))",
    )
    guide_metric_names = LocatorDescriptor(
        testid="analytics-guide-metric-name",
        description="Repeated metric name node (same rendered order as guide_metrics)",
    )
    guide_metric_descriptions = LocatorDescriptor(
        testid="analytics-guide-metric-description",
        description="Repeated metric description node (same rendered order as guide_metrics)",
    )
    guide_metric_calculation_values = LocatorDescriptor(
        testid="analytics-guide-metric-calculation-value",
        description="Repeated Calculation VALUE node — CONDITIONAL ({m.calculation && ...}), "
        "rendered on 14 of 43 metrics; also used for absence assertions on metrics without one",
    )
    guide_metric_source_values = LocatorDescriptor(
        testid="analytics-guide-metric-source-value",
        description="Repeated Data-source VALUE node — CONDITIONAL ({m.source && ...}), "
        "rendered on 7 of 43 metrics; also used for absence assertions",
    )

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

    # Scoped sub-selectors — UPPER_CASE class constants containing a
    # `[data-testid=` string, per `.claude/rules/page-objects.md` (used to
    # read repeated nodes INSIDE a parent testid, e.g. the metric blocks of
    # one Guide section).
    GUIDE_METRIC = '[data-testid="analytics-guide-metric"]'
    GUIDE_METRIC_NAME = '[data-testid="analytics-guide-metric-name"]'
    GUIDE_METRIC_CALCULATION_VALUE = '[data-testid="analytics-guide-metric-calculation-value"]'
    GUIDE_METRIC_SOURCE_VALUE = '[data-testid="analytics-guide-metric-source-value"]'

    # Rows-per-page menu OPTION items — MUI-generated, library-internal nodes
    # that cannot carry an app testid (#579 exception 1). ALWAYS used scoped
    # inside the real app-testid parent `analytics-tools-pagination-rows-menu`
    # (see `open_tools_rows_per_page_options`), never free-floating.
    MUI_MENU_OPTION = '[role="option"]'

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
    # Overview tab KPI cards (ELITEA-2311)
    # ------------------------------------------------------------------

    def select_date_preset_capturing_analytics(self, preset_locator) -> dict:
        """Click a date preset and return the resulting Overview/Health
        analytics response BODY, so the caller can use the live response as
        the oracle for every rendered value.

        Capturing the real response and asserting the UI against it is this
        project's sanctioned way to test a data-driven surface without
        fabricating anything (`.agents/testing.md` § Fidelity policy —
        "capture the real response and assert the UI against it"). Nothing
        is stubbed, intercepted or rewritten: the product produces every
        number, the test only reads the same payload the UI rendered from.

        Waits on that response (never on `networkidle` — this app holds a
        persistent Socket.IO polling transport open, so `networkidle` is a
        race; see `.agents/testing.md` § Known issues, #1847), then for the
        loading spinner to clear so the DOM has caught up with the payload.
        """
        with self.page.expect_response(
            self._is_analytics_query_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            preset_locator.click()
        response = response_info.value
        assert response.status == 200, (
            f"Expected the analytics query to return 200, got {response.status} for {response.url}"
        )
        if self.loading_indicator.count() > 0:
            self.loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
        return response.json()

    def get_overview_kpi_labels(self) -> list[str]:
        """The Overview KPI cards' label texts, in rendered order."""
        return [
            (self.overview_kpi_labels.nth(i).text_content() or "").strip()
            for i in range(self.overview_kpi_labels.count())
        ]

    def get_overview_kpi_subtitles(self) -> list[str]:
        """The Overview KPI cards' subtitle texts, in rendered order."""
        return [
            (self.overview_kpi_subtitles.nth(i).text_content() or "").strip()
            for i in range(self.overview_kpi_subtitles.count())
        ]

    def get_overview_kpi_values(self) -> list[str]:
        """The Overview KPI cards' value texts, in rendered order."""
        return [
            (self.overview_kpi_values.nth(i).text_content() or "").strip()
            for i in range(self.overview_kpi_values.count())
        ]

    # ------------------------------------------------------------------
    # Tools tab (ELITEA-2322)
    # ------------------------------------------------------------------

    def _is_analytics_tools_query_response(self, response) -> bool:
        """True for the Tools-tab data GET (`useAnalyticsToolsQuery`) — a
        distinct endpoint from Overview/Users/Agents; fires on tab mount and
        again on every search-input or pagination change."""
        return (
            ANALYTICS_TOOLS_QUERY_URL_SUBSTRING in response.url
            and response.request.method == "GET"
        )

    def _wait_for_tools_settled(self) -> None:
        """Wait for the Tools-tab render to catch up with a just-resolved
        query response (same response-vs-render gap as
        `_wait_for_users_settled`: rows and spinner are mutually exclusive
        on one `isFetching` branch in `AnalyticsTools.jsx`)."""
        self.tools_loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def open_tools_tab(self) -> dict:
        """Click the Tools tab, wait for its data query to resolve, and
        return that response's BODY as the oracle for the tab's counts,
        tool names and error values (`.agents/testing.md` § Fidelity
        policy). Nothing is intercepted or fabricated — the body returned
        is the same payload the UI rendered from."""
        with self.page.expect_response(
            self._is_analytics_tools_query_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            self.tab_tools.click()
        response = response_info.value
        assert response.status == 200, (
            f"Expected the Tools-tab query to return 200, got {response.status} for {response.url}"
        )
        self.tools_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        self._wait_for_tools_settled()
        return response.json()

    def get_tools_table_column_labels(self) -> list[str]:
        """The Tool Details table's 5 column header labels in rendered order
        (each header cell is a block-level Typography, so splitting the
        header row's aggregate inner text on newline recovers the ordered
        list — same technique as the Users/Agents tabs)."""
        text = self.tools_table_header.inner_text()
        return [line for line in text.split("\n") if line]

    def get_tools_row_count(self) -> int:
        """Number of currently-rendered tool rows."""
        return self.tools_rows.count()

    def get_tool_row_errors_value(self, index: int) -> int:
        """Errors-column value (as int) for the tool row at *index*."""
        return int(self.tools_row_errors.nth(index).text_content())

    def get_tool_row_name(self, index: int) -> str:
        """First column's rendered tool name for the row at *index*, read via
        the row's aggregate inner text (mirrors `get_user_row_identifier`) —
        only the Errors cell has its own testid within a row."""
        lines = [line for line in self.tools_rows.nth(index).inner_text().split("\n") if line]
        return lines[0] if lines else ""

    def get_tools_chart_x_axis_labels(self) -> list[str]:
        """X-axis tick labels of the "Most Popular Tools" bar chart, in
        rendered order.

        #579 exception 1 (third-party widget subtree): Recharts renders its
        axis ticks as library-internal SVG `<text>` nodes that live outside
        `EliteaUI/src` JSX, so no app testid can be placed on them. The raw
        handle is therefore SCOPED inside the real app-testid parent
        (`analytics-tools-chart-container`) and never used free-floating.
        Do NOT extend this exception to any node that COULD carry a testid.
        """
        ticks = self.tools_chart_container.locator(RECHARTS_X_AXIS_TICK)
        return [(ticks.nth(i).text_content() or "").strip() for i in range(ticks.count())]

    def get_tools_chart_bar_fills(self) -> list[str]:
        """`fill` attribute of each rendered bar in the "Most Popular Tools"
        chart, in rendered order.

        Same #579 exception 1 as `get_tools_chart_x_axis_labels`: the bar
        `<path>` nodes are Recharts-internal render nodes, reached only as a
        raw handle SCOPED inside the `analytics-tools-chart-container`
        testid parent.
        """
        bars = self.tools_chart_container.locator(RECHARTS_BAR_FILL)
        return [bars.nth(i).get_attribute("fill") for i in range(bars.count())]

    def open_tools_rows_per_page_options(self) -> list[str]:
        """Open the Tools-tab rows-per-page select, return the offered option
        labels, then close the menu again (Escape) so the page is left as it
        was found.

        #579 exception 1 (third-party widget subtree): MUI's `TablePagination`
        generates the rows-per-page menu items itself from
        `rowsPerPageOptions`, so no app testid can be placed on an individual
        item without changing behaviour. The menu LIST does carry a real app
        testid (`analytics-tools-pagination-rows-menu`, wired via
        `slotProps.select.MenuProps.slotProps.list`), and the item handle is
        SCOPED inside it. Do NOT extend this exception to any node that COULD
        carry a testid.
        """
        self.tools_pagination_rows_select.click()
        self.tools_pagination_rows_menu.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        options = self.tools_pagination_rows_menu.locator(self.MUI_MENU_OPTION)
        labels = [(options.nth(i).text_content() or "").strip() for i in range(options.count())]
        self.page.keyboard.press("Escape")
        self.tools_pagination_rows_menu.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
        return labels

    def clear_tools_search(self) -> None:
        """Clear the Tools-tab search input so tab state doesn't leak into a
        later test in the same session (mirrors `clear_users_search`, including
        its deliberate lack of an `expect_response`: clearing back to
        `search=""` is frequently an RTK-Query cache hit with no new request)."""
        if self.tools_search_input.count() and self.tools_search_input.input_value():
            self.tools_search_input.fill("")
            self._wait_for_tools_settled()

    # ------------------------------------------------------------------
    # Health tab (ELITEA-2324)
    # ------------------------------------------------------------------

    def open_health_tab(self) -> None:
        """Click the Health tab and wait for its content to render.

        Health shares the Overview endpoint (`needsOverview = activeTab === 0
        || activeTab === 6`), so switching to it on an unchanged date range
        is usually an RTK-Query CACHE HIT that fires no request at all —
        an `expect_response` here would time out for a request that
        legitimately never happens. Capture the body around the preset click
        (`select_date_preset_capturing_analytics`) instead, and wait here on
        the tab's own rendered content.
        """
        self.tab_health.click()
        self.health_table_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        if self.loading_indicator.count() > 0:
            self.loading_indicator.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

    def get_health_table_column_labels(self) -> list[str]:
        """The Health-by-Event-Type table's 5 column header labels in
        rendered order (same aggregate-inner-text technique as the other
        analytics tables)."""
        text = self.health_table_header.inner_text()
        return [line for line in text.split("\n") if line]

    def get_health_event_types(self) -> list[str]:
        """The rendered event-type cell texts, in row order."""
        return [
            (self.health_row_event_type.nth(i).text_content() or "").strip()
            for i in range(self.health_row_event_type.count())
        ]

    def get_health_chart_area_series_count(self) -> int:
        """Number of rendered area series in the "Requests vs Errors" chart.

        #579 exception 1 (third-party widget subtree): the `<path>` nodes
        Recharts renders for each `<Area>` are library-internal and cannot
        carry an app testid, so the raw handle is SCOPED inside the real
        app-testid parent (`analytics-health-chart-container`). Do NOT
        extend this exception to any node that COULD carry a testid.
        """
        return self.health_chart_container.locator(RECHARTS_AREA_SERIES).count()

    def hover_health_chart_and_read_tooltip(self) -> str:
        """Hover the "Requests vs Errors" chart and return the Recharts
        hover tooltip's text.

        The chart renders NO legend, so the two series' NAMES exist in the
        DOM only inside this tooltip — hovering is the only honest way to
        assert the case's "Total Requests and Errors series". A real
        `Locator.hover()` is used (never a synthetic event dispatched via
        `page.evaluate`, which would be the test producing the observable
        rather than the product).
        """
        self.health_chart_container.hover()
        self.health_chart_tooltip.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        return self.health_chart_tooltip.inner_text()

    # ------------------------------------------------------------------
    # Guide tab (ELITEA-2325) — static content, issues NO network request
    # ------------------------------------------------------------------

    def open_guide_tab(self) -> None:
        """Click the Guide tab and wait for its first documentation section.

        The Guide tab is a pure render of the bundled `GUIDE_SECTIONS`
        constant and fires NO analytics request, so there is no response to
        wait on — waiting on the first section is the correct settle signal
        (and `networkidle` is wrong here for the usual #1847 reason).
        """
        self.tab_guide.click()
        self.guide_sections.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

    def get_guide_section_titles(self) -> list[str]:
        """The documentation section titles, in rendered order."""
        return [
            (self.guide_section_titles.nth(i).text_content() or "").strip()
            for i in range(self.guide_section_titles.count())
        ]

    def get_guide_section_index_by_title(self, title: str) -> int:
        """Index of the section whose title equals *title*, or -1."""
        titles = self.get_guide_section_titles()
        return titles.index(title) if title in titles else -1

    def get_guide_metric_names_in_section(self, section_index: int) -> list[str]:
        """Metric names inside the section at *section_index*, in rendered
        order (scoped read inside that section card's testid parent)."""
        names = self.guide_sections.nth(section_index).locator(self.GUIDE_METRIC_NAME)
        return [(names.nth(i).text_content() or "").strip() for i in range(names.count())]

    def get_guide_metric_block(self, section_index: int, metric_name: str):
        """The metric block Locator for *metric_name* inside the section at
        *section_index* — scoped inside that section so a metric name that
        repeats across sections cannot resolve to the wrong block."""
        section = self.guide_sections.nth(section_index)
        names = section.locator(self.GUIDE_METRIC_NAME)
        for i in range(names.count()):
            if (names.nth(i).text_content() or "").strip() == metric_name:
                return section.locator(self.GUIDE_METRIC).nth(i)
        raise AssertionError(
            f"Metric {metric_name!r} not found in guide section index {section_index}"
        )

    def get_guide_metric_pairing(self, index: int) -> dict:
        """Label/value pairing facts for the metric block at *index*: whether
        the `Calculation:` / `Data source:` LABELS are present in the block's
        own text, and whether their VALUE nodes are rendered.

        The labels deliberately carry no testid (they are asserted through
        the block's text content), so a `Calculation:` label whose value node
        was dropped — or vice versa — is detectable.
        """
        block = self.guide_metrics.nth(index)
        text = block.inner_text()
        return {
            "calculation_label": "Calculation:" in text,
            "calculation_value": block.locator(self.GUIDE_METRIC_CALCULATION_VALUE).count(),
            "source_label": "Data source:" in text,
            "source_value": block.locator(self.GUIDE_METRIC_SOURCE_VALUE).count(),
        }

    def is_element_clipped(self, locator) -> bool:
        """True if *locator*'s content overflows its own box (i.e. the text
        is visually truncated).

        Read-only DOM measurement — `scrollHeight`/`clientHeight` have no
        Playwright accessor, and reading them observes what the PRODUCT
        laid out; nothing is injected or forced (`.agents/testing.md`
        § Fidelity policy). The 1px tolerance absorbs sub-pixel rounding.
        """
        return locator.evaluate(
            "el => el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1"
        )
