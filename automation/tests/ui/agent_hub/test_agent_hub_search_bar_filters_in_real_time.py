"""Agent Hub — search bar filters agents in real time (ELITEA-2363).

Verifies that typing a partial term into the Catalog search bar
(`/elitea-catalog`) filters the agent list in real time — debounced ~300ms,
no Enter/submit control involved — to only agents the server matched on the
term in name OR description (case-insensitive; the backend search matches both), and that clearing the typed text
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

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

SEARCH_TERM = "story"
EXPECTED_EXAMPLE_AGENT = "User Story Creator"
PUBLIC_APPLICATIONS_PATH = "/public_applications/prompt_lib/"


class TestAgentHubSearchBarFiltersInRealTime:
    """ELITEA-2363: Agent Hub — search bar filters agents in real time (l3, medium)."""

    @pytest.mark.tms("ELITEA-2363")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2363_agent-hub-search-bar-filters-agents-in-real-time.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/2537",
        "Known defect — dev-vm.elitea.ai default-icon CSP violation + application_icon 404s (console errors)",
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
                # navigate_and_capture_applications() (ELITEA-2354) waits specifically
                # on the bulk all-applications response (excluding the parallel
                # Trending/My-Liked calls) before returning — the network-level
                # completion signal. The DOM render is a SEPARATE async step relative
                # to that response resolving (the same race class as clear_search()
                # below: the heading is static and renders before the data-dependent
                # card grid does), so wait_for_any_agent_card() additionally confirms
                # the render itself landed before reading names for the baseline —
                # NOT a wait for the DOM count to equal the response's raw row count,
                # since each category section only renders its first
                # INITIAL_CARD_DISPLAY_COUNT items initially (AgentCategorySection.jsx).
                applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
                assert applications, "Expected the bulk applications fetch to return at least one row"
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
                agent_hub.wait_for_any_agent_card(timeout=UI_ELEMENT_TIMEOUT)
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
                search_response = agent_hub.search_and_capture_response(SEARCH_TERM, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.search_input.input_value() == SEARCH_TERM, (
                    f"Search field should display the typed value {SEARCH_TERM!r}"
                )

            with allure.step(
                "Step 4 — Verify exactly one debounced network request fired with query=story, "
                "no Enter/submit control involved"
            ):
                # Count ALL requests fired to the search endpoint during the typing
                # window FIRST, then check the single survivor's query param — not
                # filter-by-query-then-count-1. A broken per-keystroke debounce (firing
                # once per character instead of once after the debounce window) would
                # still leave exactly one entry whose query param is the FINAL value
                # "story" if we filtered first, silently passing a real regression.
                assert len(network_capture) == 1, (
                    f"Expected exactly one request to {PUBLIC_APPLICATIONS_PATH!r} fired "
                    f"while typing {SEARCH_TERM!r} (debounced), got {len(network_capture)}: "
                    f"{network_capture!r}"
                )
                only_request = network_capture[0]
                assert parse_qs(urlparse(only_request["url"]).query).get("query") == [SEARCH_TERM], (
                    f"Expected the single request's query param to be {SEARCH_TERM!r}, "
                    f"got {only_request!r}"
                )
                assert only_request["status"] == 200, (
                    f"Expected the debounced search request to return 200, got {only_request!r}"
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
                # The backend search matches name OR description, so the captured
                # response rows are the ground truth for what may be rendered.
                rows = search_response.get("rows") or []
                assert rows, f"Expected the search response to contain rows for {SEARCH_TERM!r}"
                bad_rows = [
                    r.get("name")
                    for r in rows
                    if SEARCH_TERM not in f"{r.get('name') or ''} {r.get('description') or ''}".lower()
                ]
                assert not bad_rows, (
                    f"Every returned row should match {SEARCH_TERM!r} in name or description, "
                    f"but found: {bad_rows!r}"
                )
                row_ids = {r["id"] for r in rows}
                stray_ids = [i for i in agent_hub.get_visible_agent_card_ids() if i not in row_ids]
                assert not stray_ids, (
                    f"Every rendered card must map to a returned search row; stray card id(s): {stray_ids!r}"
                )
                name_matches = [r["name"] for r in rows if SEARCH_TERM in (r.get("name") or "").lower()]
                assert name_matches, f"Expected at least one agent whose name contains {SEARCH_TERM!r}"
                # Every returned name-match must be rendered (cards carry the name as a prefix of their text).
                missing = [n for n in name_matches if not any(c.startswith(n) for c in filtered_cards)]
                assert not missing, f"Name-matching agent(s) returned by the server but not rendered: {missing!r}"
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
                # Known defect: #2537 — Step 7 stays red until fixed (sanctioned RED, deterministic):
                # dev-vm.elitea.ai default-icon CSP violation + application_icon 404s on Agent Hub cards.
                # Assertion intentionally stays strict (no filtering of these errors).
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
