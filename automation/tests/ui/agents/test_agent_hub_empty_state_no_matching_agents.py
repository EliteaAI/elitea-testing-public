"""Agent Hub — empty state when no agents match filter or search (ELITEA-2367).

Verifies that the Agent Hub's `/elitea-catalog` page displays an empty state
with "No agents found" and "Try adjusting your search terms" messages when
a search term matches no agents. All major UI elements remain visible and
functional; layout is consistent; zero console errors.

Spec: test-specs/agent-hub/l2_empty-state-no-matching-agents_ELITEA-2367.md

Uses `AgentHubPage` for navigation, search, and layout verification.
The empty-state messages ("No agents found", "Try adjusting your search terms")
lack testids per the AFS, so uses `page.get_by_text()` as the fallback locator.
"""

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Search term guaranteed to match no agents (case-insensitive substring match)
NONEXISTENT_SEARCH_TERM = "xyzabc123notreal"


class TestAgentHubEmptyStateNoMatchingAgents:
    """ELITEA-2367: Agent Hub — empty state when no agents match filter or search (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2367_agent-hub-empty-state-when-no-agents-match.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_empty_state_no_matching_agents(self, page: Page):
        """Search for a non-matching term and verify the empty state displays
        correctly: "No agents found" + "Try adjusting your search terms"
        messages visible, all layout elements remain functional."""
        agent_hub = AgentHubPage(page)
        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Agent Hub and verify page loads"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
                expect(page).to_have_url("/elitea-catalog")
                assert not console_capture, (
                    f"Expected zero console errors during page load, got: "
                    f"{[m.text for m in console_capture]}"
                )

            with allure.step("Step 2 — Search for a term that matches no agents"):
                agent_hub.search(NONEXISTENT_SEARCH_TERM, timeout=NAVIGATION_TIMEOUT)
                # Verify the search field contains the typed term
                assert agent_hub.search_input.input_value() == NONEXISTENT_SEARCH_TERM, (
                    f"Search field should display {NONEXISTENT_SEARCH_TERM!r}"
                )

            with allure.step("Step 3 — Verify 'No agents found' message is displayed"):
                # Empty-state messages lack testids; use page.get_by_text() as fallback
                no_results_msg = page.get_by_text("No agents found")
                no_results_msg.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert no_results_msg.is_visible(), (
                    "Text 'No agents found' should be visible in the content area"
                )

            with allure.step("Step 4 — Verify helper message appears"):
                helper_msg = page.get_by_text("Try adjusting your search terms")
                helper_msg.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert helper_msg.is_visible(), (
                    "Text 'Try adjusting your search terms' should be visible below the main message"
                )

            with allure.step("Step 5 — Verify layout remains consistent with no broken UI elements"):
                # Verify page heading is still visible
                assert agent_hub.page_heading.is_visible(), (
                    "Page heading should remain visible during empty state"
                )

                # Verify search input is still visible with the term populated
                assert agent_hub.search_input.is_visible(), (
                    "Search input should remain visible with the search term"
                )
                expect(agent_hub.search_input).to_have_value(NONEXISTENT_SEARCH_TERM)

                # Verify no agent cards are present (zero matches)
                assert agent_hub.get_agent_card_count() == 0, (
                    "Expected zero agent cards when search matches no agents"
                )

                # Verify category filter chips are still visible and functional
                # Check that at least one Featured section chip (Trending or My Liked) is visible
                featured_section_visible = (
                    agent_hub.is_category_filter_chip_visible("Trending") or
                    agent_hub.is_category_filter_chip_visible("My Liked")
                )
                assert featured_section_visible, (
                    "Category filter chips should still be visible (Featured section)"
                )

            with allure.step("Step 6 — Verify zero console errors during empty state render"):
                assert not console_capture, (
                    f"Expected zero console errors during empty state, got: "
                    f"{[m.text for m in console_capture]}"
                )

        finally:
            console_capture.stop()
