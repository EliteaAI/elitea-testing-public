"""Agent Hub — search bar filters agents in real time (ELITEA-2363).

Verifies that typing a partial term into the Catalog search bar
(`/elitea-catalog`) filters the agent list in real time — debounced ~300ms,
no Enter/submit control involved — to only agents whose name contains the
term (case-insensitive substring match), and that clearing the typed text
(no dedicated clear button exists on this field) restores the exact
original unfiltered set. Zero console errors throughout.

Spec: test-specs/agent-hub/l3_agent-hub-search-bar-filters-in-real-time_ELITEA-2363.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup and the
debounce-aware `search()` method (ELITEA-2075/2354); adds `clear_search()`,
`get_visible_agent_card_texts()`, `get_visible_agent_card_ids()` and
`wait_for_agent_card_ids()` to the same page object for this case.

REPAIR, 2026-09-10 (#2179, AFS § Adjustment — 2026-09-10). Step 6 took this spec
RED in CI run 34436416962 because it compared cards by their rendered TEXT, and a
card's text carries its live like count (`AgentCard.jsx` renders name + author
initials + `AgentHubLike` inside one `<Card>`, no separator). A like landing on a
catalog agent mid-run — which sibling specs in this same suite do by design —
changed one card's string AND legitimately re-ranked the likes-desc-sorted
Trending section. Identity now comes from the card's own `catalog-agent-card-{id}`
testid and is compared as a sorted MULTISET (the grid renders three agents twice —
Trending plus their own category — so a `set()` would stop detecting a dropped
duplicate). Membership and multiplicity are still asserted in full against the
complete step-1 baseline; only position is dropped, which the TMS case never
claimed. No substitution of any kind is used: every value asserted here is read
off the live product.

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
                # Two baselines, deliberately: IDS are the identity of the
                # rendered set (Step 6's restore comparison), TEXTS are only
                # used for Step 5's substring check. They must never be
                # swapped — a card's text carries its live like count, which
                # shared suite data mutates (#2179).
                baseline_ids = agent_hub.get_visible_agent_card_ids()
                baseline_cards = agent_hub.get_visible_agent_card_texts()
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
                filtered_cards = agent_hub.get_visible_agent_card_texts()
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
                # The wait polls the identity multiset itself (not a raw card
                # count), so it is terminal by construction: a half-restored
                # grid can never satisfy it, and shared data publishing a new
                # agent mid-run cannot make it resolve on a transient state.
                agent_hub.wait_for_agent_card_ids(baseline_ids, timeout=UI_ELEMENT_TIMEOUT)
                restored_ids = agent_hub.get_visible_agent_card_ids()
                # SORTED LIST, never set(): the grid renders three agents twice
                # (Trending + their own category section), so a set would
                # collapse 27 cards to 24 ids and stop detecting a dropped
                # duplicate render. Membership AND multiplicity are asserted;
                # position is not — ELITEA-2363 makes a membership claim only
                # ("verify all agents return to the list"), and the Trending
                # section's order is a function of live like counts, which no
                # test can demand be frozen (#2179, AFS § Adjustment).
                assert sorted(restored_ids) == sorted(baseline_ids), (
                    "Every agent present before searching should be present again after clearing "
                    f"(baseline {len(baseline_ids)} cards, restored {len(restored_ids)}); "
                    f"missing={sorted(set(baseline_ids) - set(restored_ids))!r} "
                    f"unexpected={sorted(set(restored_ids) - set(baseline_ids))!r}"
                )

            with allure.step("Step 7 — Verify zero console errors during typing, filtering, and clearing"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
