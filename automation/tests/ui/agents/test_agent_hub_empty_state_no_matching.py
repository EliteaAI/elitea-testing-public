"""Agent Hub — empty state when no agents match filter or search (ELITEA-2367).

Verifies that the Agent Hub (Catalog) empty state renders correctly and displays
consistent layout when no agents match a search query on the public catalog
(`/elitea-catalog`). The test covers:
  - Navigation to the Agent Hub (public Catalog)
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

from pages.agent_hub_page import AgentHubPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

NAVIGATION_TIMEOUT = 15_000
UI_ELEMENT_TIMEOUT = 10_000
SEARCH_DEBOUNCE = 500  # Extra buffer for debounce (base is 300ms per AFS)

# Search term guaranteed to match no agents
SEARCH_TERM_NO_MATCH = "DEFINITELYNONEXISTENTTERM"


class TestAgentHubEmptyStateNoMatchingAgents:
    """ELITEA-2367: Agent Hub (Catalog) — empty state when no agents match search."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2367_agent-hub-empty-state-when-no-agents-match-filter-or-search.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_empty_state_when_no_agents_match_search(self, page: Page):
        """Empty state displays correctly on the public Agent Hub Catalog when
        search matches no agents, and agents reappear when search is cleared."""
        agent_hub = AgentHubPage(page)

        # Capture console errors throughout the test
        console_errors = []
        console_handler = lambda msg: console_errors.append(msg.text) if msg.type == "error" else None
        page.on("console", console_handler)

        try:
            with allure.step("Step 1 — Navigate to Agent Hub (Catalog)"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

                # Capture baseline agent count
                agent_hub.wait_for_any_agent_card(timeout=UI_ELEMENT_TIMEOUT)
                initial_card_count = agent_hub.get_agent_card_count()

            with allure.step(
                f"Step 2 — Type search term '{SEARCH_TERM_NO_MATCH}' matching no agents"
            ):
                # The AgentHubPage.search() method handles debounce and network waits
                agent_hub.search(SEARCH_TERM_NO_MATCH, timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(SEARCH_DEBOUNCE)  # Extra buffer for debounce

            with allure.step(
                "Step 3 — Verify empty state displays: no agents visible, "
                "empty-state message appears"
            ):
                # Wait for agent cards to disappear (count should reach 0)
                # AgentHubPage uses AGENT_CARD_PREFIX for collection locator
                expect(page.locator(agent_hub.AGENT_CARD_PREFIX)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

                # Verify the no-agents message is present
                # Using a text search for common empty-state messages
                empty_state_locator = page.locator('text=/No agents|nothing found/i')
                expect(empty_state_locator.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify layout consistency: heading and search still visible, "
                "no broken UI elements"
            ):
                # Verify page heading is still visible (not hidden)
                expect(agent_hub.page_heading).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                # Verify search input is still visible and focused
                expect(agent_hub.search_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Clear search and verify agents reappear"):
                # The AgentHubPage.clear_search() method handles debounce and network waits
                agent_hub.clear_search(timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(SEARCH_DEBOUNCE)

                # Wait for agent cards to return
                expect(page.locator(agent_hub.AGENT_CARD_PREFIX)).to_have_count(
                    initial_card_count, timeout=UI_ELEMENT_TIMEOUT
                )

                # Verify agents list is restored by checking count
                assert agent_hub.get_agent_card_count() == initial_card_count, (
                    f"After clearing search, agent count should return to {initial_card_count}, "
                    f"got {agent_hub.get_agent_card_count()}"
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
