"""Analytics page object (Settings → Analytics).

URL: /settings/analytics

Covers the page shell: header (title + project badge), the date-range filter
bar (four presets + From/To pickers), the seven-tab bar, and the
Overview-data loading state. Does NOT cover the per-tab content
(Overview/Costs/Agents & Pipelines/Tools/Users/Health/Guide bodies) —
that's out of scope for ELITEA-2310 (default-load structural check only).

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
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.analytics")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Substring shared by the Overview/Health analytics fetch (`useProjectAnalyticsQuery`)
# — used to wait for the initiating GET to resolve before asserting on the
# loading spinner / Overview KPI content.
ANALYTICS_QUERY_URL_SUBSTRING = "/elitea_core/analytics/prompt_lib/"


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
