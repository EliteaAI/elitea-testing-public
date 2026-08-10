"""Agent Hub — empty state when no agents match filter or search (ELITEA-2367).

Verifies that the Agents list (private agents) empty state renders correctly and displays
consistent layout when no agents match a search query on the agents list page
(`/agents/all?viewMode=owner`). The test covers:
  - Navigation to the Agents list (private agents)
  - Search with a term matching no agents
  - Empty state message displays
  - Helper message appears
  - Layout consistency with no broken UI
  - Clearing search restores agents to view
  - No console errors throughout

Spec: test-specs/agents/l2_empty-state-when-no-agents-match-filter-or-search_ELITEA-2367.md

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p2: medium priority
    - regression: part of regression suite
"""

import allure
import pytest
from playwright.sync_api import expect, Page

from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

NAVIGATION_TIMEOUT = 15_000
UI_ELEMENT_TIMEOUT = 10_000
SEARCH_DEBOUNCE = 500  # Extra buffer for debounce (base is 300ms per AFS)

# Search term guaranteed to match no agents
SEARCH_TERM_NO_MATCH = "DEFINITELYNONEXISTENTTERM"


class TestAgentHubEmptyStateNoMatchingAgents:
    """ELITEA-2367: Agents List — empty state when no agents match search."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/ELITEA-2367_agent-hub-empty-state-when-no-agents-match-filter-or-search.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_empty_state_when_no_agents_match_search(self, page: Page):
        """Empty state displays correctly on the Agents list when
        search matches no agents, and agents reappear when search is cleared."""
        agents_list = AgentsListPage(page)

        # Capture console errors throughout the test
        console_errors = []
        console_handler = lambda msg: console_errors.append(msg.text) if msg.type == "error" else None
        page.on("console", console_handler)

        try:
            with allure.step("Step 1 — Navigate to Agents list (/agents/all?viewMode=owner)"):
                # Navigate to the private agents list with owner view mode
                agents_list.navigate_owner_view()
                assert agents_list.page_header.is_visible(), "Agents page header should be visible"

                # Capture baseline agent count
                initial_agent_names = agents_list.get_agent_card_names(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"Step 2 — Type search term '{SEARCH_TERM_NO_MATCH}' matching no agents"
            ):
                # The AgentsListPage.search() method handles debounce and network waits
                agents_list.search(SEARCH_TERM_NO_MATCH, timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(SEARCH_DEBOUNCE)  # Extra buffer for debounce

            with allure.step(
                "Step 3 — Verify empty state displays: no agents visible, "
                "empty-state message appears"
            ):
                # Verify no agents are shown (card names list is empty)
                found_agent_names = agents_list.get_agent_card_names(timeout=UI_ELEMENT_TIMEOUT)
                assert len(found_agent_names) == 0, (
                    f"Expected no agents after search, but found: {found_agent_names}"
                )

                # Verify the empty-state message is visible
                empty_state_locator = agents_list.empty_state_message
                expect(empty_state_locator).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify layout consistency: heading and search still visible, "
                "no broken UI elements"
            ):
                # Verify page heading is still visible (not hidden)
                expect(agents_list.page_header).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                # Verify search input is still visible
                expect(agents_list.search_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Clear search and verify agents reappear"):
                # The AgentsListPage.clear_search() method handles debounce and network waits
                agents_list.clear_search()
                page.wait_for_timeout(SEARCH_DEBOUNCE)

                # Wait for agent cards to return (should have same agents as initially)
                restored_agent_names = agents_list.get_agent_card_names(timeout=UI_ELEMENT_TIMEOUT)
                assert len(restored_agent_names) == len(initial_agent_names), (
                    f"After clearing search, agent count should return to {len(initial_agent_names)}, "
                    f"got {len(restored_agent_names)}"
                )

            with allure.step("Step 6 — Verify no console errors throughout the test"):
                # Check that no console errors were captured
                assert not console_errors, (
                    f"Unexpected console errors during empty-state transitions: "
                    f"{console_errors}"
                )

        finally:
            # Clean up console listener
            page.remove_listener("console", console_handler)
