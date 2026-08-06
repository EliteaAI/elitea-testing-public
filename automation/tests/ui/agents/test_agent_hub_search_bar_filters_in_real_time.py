"""Agent Hub — search bar filters agents in real time (ELITEA-2363).

Verifies that typing a partial term into the Catalog search bar
(`/elitea-catalog`) filters the agent list in real time — debounced ~300ms,
no Enter/submit control involved — to only agents whose name contains the
term (case-insensitive substring match), and that clearing the typed text
(no dedicated clear button exists on this field) restores the exact
original unfiltered set. Zero console errors throughout.

Spec: test-specs/agent-hub/l3_agent-hub-search-bar-filters-in-real-time_ELITEA-2363.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup and the
debounce-aware `search()` method (ELITEA-2075/2354); adds `clear_search()`
and `get_visible_agent_card_names()` to the same page object for this case.

No new testid needed — `catalog-page-heading`, `catalog-search-input`, and
`catalog-agent-card-{id}` already exist on `automation/testids` (this test's
target) and are already wired into `AgentHubPage`.
"""

import logging
from urllib.parse import parse_qs, urlparse

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

SEARCH_TERM = "story"
EXPECTED_EXAMPLE_AGENT = "User Story Creator"
PUBLIC_APPLICATIONS_PATH = "/public_applications/prompt_lib/"


class TestAgentHubSearchBarFiltersInRealTime:
    """ELITEA-2363: Agent Hub — search bar filters agents in real time (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2363_agent-hub-search-bar-filters-agents-in-real-time.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_search_bar_filters_in_real_time(self, page: Page):
        """Typing a partial term into the Catalog search bar filters the
        agent list in real time via a single debounced request; clearing
        the typed text restores the exact original unfiltered set."""
        agent_hub = AgentHubPage(page)
        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Agent Hub and capture the pre-search baseline"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
                baseline_cards = agent_hub.get_visible_agent_card_names()
                assert baseline_cards, "Expected at least one agent card rendered before searching"

            with allure.step("Step 2 — Click into the search bar at the top"):
                agent_hub.search_input.click()
                expect(agent_hub.search_input).to_be_focused()

            with allure.step(
                f"Step 3 — Type a partial search term ({SEARCH_TERM!r}) into the field"
            ):
                network_capture = agent_hub.capture_requests_matching(
                    PUBLIC_APPLICATIONS_PATH, method="GET"
                )
                agent_hub.search(SEARCH_TERM, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.search_input.input_value() == SEARCH_TERM, (
                    f"Search field should display the typed value {SEARCH_TERM!r}"
                )

            with allure.step(
                "Step 4 — Verify exactly one debounced network request fired with query=story, "
                "no Enter/submit control involved"
            ):
                matching_requests = [
                    r
                    for r in network_capture
                    if parse_qs(urlparse(r["url"]).query).get("query") == [SEARCH_TERM]
                ]
                assert len(matching_requests) == 1, (
                    f"Expected exactly one debounced request with query={SEARCH_TERM!r}, "
                    f"got {len(matching_requests)}: {network_capture!r}"
                )
                assert matching_requests[0]["status"] == 200, (
                    f"Expected the debounced search request to return 200, got {matching_requests[0]!r}"
                )
                network_capture.stop()

            with allure.step(
                f"Step 5 — Verify only matching agents are displayed (e.g., {EXPECTED_EXAMPLE_AGENT!r})"
            ):
                agent_hub.wait_for_agent_card_count_not(len(baseline_cards), timeout=UI_ELEMENT_TIMEOUT)
                filtered_cards = agent_hub.get_visible_agent_card_names()
                assert len(filtered_cards) < len(baseline_cards), (
                    f"Expected fewer cards after filtering on {SEARCH_TERM!r} than the "
                    f"{len(baseline_cards)}-card baseline, got {len(filtered_cards)}"
                )
                non_matching = [c for c in filtered_cards if SEARCH_TERM not in c.lower()]
                assert not non_matching, (
                    f"Every visible card should contain {SEARCH_TERM!r} (case-insensitive), "
                    f"but found non-matching card(s): {non_matching!r}"
                )
                assert agent_hub.get_agent_card(EXPECTED_EXAMPLE_AGENT).first.is_visible(), (
                    f"Expected the case's own named example {EXPECTED_EXAMPLE_AGENT!r} "
                    "to be visible among the filtered results"
                )

            with allure.step("Step 6 — Clear the search field and verify all agents return to the list"):
                agent_hub.clear_search(timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.search_input.input_value() == "", "Search field should be empty after clearing"
                agent_hub.wait_for_agent_card_count(len(baseline_cards), timeout=UI_ELEMENT_TIMEOUT)
                restored_cards = agent_hub.get_visible_agent_card_names()
                assert restored_cards == baseline_cards, (
                    "Restored card set after clearing should exactly match the step-1 baseline"
                )

            with allure.step("Step 7 — Verify zero console errors during typing, filtering, and clearing"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
