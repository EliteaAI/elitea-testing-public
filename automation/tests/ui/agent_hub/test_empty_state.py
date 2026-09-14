"""Test: Agent Hub empty state when no agents match search or filter.

ELITEA-2367: Verify the empty state displays correctly when no agents match
a search query. Layout remains consistent; all major UI elements visible.

AFS: test-specs/agent-hub/l2_empty-state-no-matching-agents_ELITEA-2367.md
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.agent_hub_page import AgentHubPage

#: Budget for the filter rail to settle. The rail's categories fetch lands a beat
#: after the content grid, so the chip-count assertion must be the auto-retrying
#: web-first form rather than a one-shot ``.count()`` (ELITEA-2367, FIX card #2079).
FILTER_RAIL_TIMEOUT = 10_000


class TestCatalogEmptyState:
    """Agent Hub empty state verification when search matches zero agents."""

    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.agent_hub
    @allure.title("Empty state displays when search matches no agents")
    @allure.description(
        "Verify that when a search term matches zero agents, the 'No agents found' "
        "and 'Try adjusting your search terms' messages display. Page heading, search "
        "input, tabs, and filter rail remain visible and functional. No agent cards present."
    )
    @pytest.mark.tryfirst  # @ELITEA-2367
    def test_empty_state_when_search_matches_no_agents(self, page: Page):
        """
        ELITEA-2367: Agent Hub empty state when search matches no agents.

        Steps:
        1. Navigate to Agent Hub (Catalog)
        2. Verify page heading visible
        3. Search for a term that matches no agents
        4. Verify "No agents found" message displays
        5. Verify "Try adjusting your search terms" helper displays
        6. Verify layout consistency: heading, search, tabs, filter rail visible
        7. Verify zero agent cards present
        8. Verify zero console errors during empty state

        Step 6's filter-rail expectation is DERIVED, not hardcoded: the expected chip
        set comes from the categories response the page itself fetches on load
        (observed via ``page.expect_response``, never routed or fulfilled -- nothing
        is substituted). See ``AgentHubPage.expected_category_filter_labels`` for why
        the rail's frontend-constant half and backend-data half must be treated
        differently, and FIX card #2079 for the drift that motivated it.
        """

        agent_hub = AgentHubPage(page)
        search_term = "xyznonexistent123"

        # Set up console message listener to capture errors during the test
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg.type))

        # Step 1: Navigate to Catalog
        with allure.step("Step 1 — Navigate to Agent Hub"):
            # Capture the page's OWN categories response on the way in — it is the
            # oracle for Step 6's filter-rail assertion (read-only observation).
            api_category_names = agent_hub.navigate_and_capture_category_names()

        # Step 2: Verify page heading visible
        with allure.step("Step 2 — Verify page heading 'Welcome to ELITEA Catalog!'"):
            expect(agent_hub.page_heading).to_be_visible()
            expect(agent_hub.page_heading).to_have_text("Welcome to ELITEA Catalog!")

        # Step 3: Search for a term that matches no agents
        with allure.step(f"Step 3 — Search for term '{search_term}' (no matches expected)"):
            search_input = agent_hub.search_input
            search_input.click()
            search_input.type(search_term)
            # Wait for the debounce (300ms) + network request (~150-200ms)
            # Total ~500ms end-to-end before empty state renders
            page.wait_for_timeout(600)

        # Step 4: Verify "No agents found" message displays
        with allure.step("Step 4 — Verify 'No agents found' message visible"):
            agent_hub.no_results_title.wait_for(state="visible", timeout=5000)
            expect(agent_hub.no_results_title).to_be_visible()

        # Step 5: Verify helper message displays
        with allure.step("Step 5 — Verify 'Try adjusting your search terms' helper"):
            agent_hub.no_results_description.wait_for(state="visible", timeout=5000)
            expect(agent_hub.no_results_description).to_be_visible()

        # Step 6: Verify layout consistency — all major elements remain visible
        with allure.step("Step 6 — Verify layout consistency (heading, search, tabs, filter rail)"):
            # Heading still visible
            expect(agent_hub.page_heading).to_be_visible()

            # Search input still visible with the search term populated
            expect(search_input).to_be_visible()
            expect(search_input).to_have_value(search_term)

            # Agents/Skills tabs still visible
            expect(agent_hub.agents_tab).to_be_visible()
            expect(agent_hub.skills_tab).to_be_visible()

            # Category filter rail intact. The expected chip set is DERIVED from the
            # categories response captured in Step 1, never hardcoded: the rail mixes
            # frontend constants (the Featured head + the trailing "Other") with
            # backend data (the middle categories, which an admin can change with no
            # code change). A hardcoded total pins both halves with one number — that
            # is what went red on the legitimate third Featured chip "New"
            # (EliteaAI/EliteaUI@18170f71 / EL-6238), and bumping it would only re-arm
            # the same tripwire on the data half.
            expected_labels = AgentHubPage.expected_category_filter_labels(api_category_names)
            filter_chips = agent_hub.get_visible_category_filter_chips()

            # A — exact count. Auto-retrying expect(), not a one-shot .count(): the
            # rail's categories fetch settles a beat after the content grid. Catches a
            # duplicated or dropped chip, which set equality alone cannot.
            expect(filter_chips).to_have_count(len(expected_labels), timeout=FILTER_RAIL_TIMEOUT)

            # B — set membership, delta named BOTH ways so the next drift is triaged
            # from the failure message instead of from a session of archaeology.
            rendered_labels = set(agent_hub.get_category_filter_chip_labels())
            assert rendered_labels == expected_labels, (
                "Filter-rail chips do not match the categories the page itself fetched — "
                f"missing: {sorted(expected_labels - rendered_labels)}, "
                f"unexpected: {sorted(rendered_labels - expected_labels)}"
            )

            # C/D — head and tail VISIBILITY. Load-bearing, not decoration: Playwright's
            # to_have_count matches *attached* elements including hidden ones, so A and B
            # alone would pass on a collapsed or display:none rail — precisely what case
            # Step 5 ("layout remains consistent with no broken UI elements") forbids.
            # C — the three Featured chips at the head of the rail.
            for featured_label in AgentHubPage.FEATURED_CATEGORY_LABELS:
                expect(agent_hub.get_category_filter_chip(featured_label)).to_be_visible()
            # D — "Other", the rail's deterministic tail.
            expect(agent_hub.get_category_filter_chip(AgentHubPage.OTHER_CATEGORY_LABEL)).to_be_visible()

        # Step 7: Verify zero agent cards present in the DOM
        with allure.step("Step 7 — Verify zero agent cards in the DOM"):
            card_count = agent_hub.get_agent_card_count()
            assert card_count == 0, f"Expected 0 agent cards, found {card_count}"

        # Step 8: Verify zero console errors during empty state
        with allure.step("Step 8 — Verify no console errors"):
            error_types = [msg_type for msg_type in console_messages if msg_type == "error"]
            assert len(error_types) == 0, f"Expected no console errors, found {len(error_types)} error(s)"
