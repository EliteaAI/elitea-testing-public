"""Agent Hub — Trending category displays agents (ELITEA-2366).

Verifies that clicking the Trending category filter chip on the public Agent
Hub (Catalog) page activates the filter, highlights the chip, and displays
agent cards in the Trending section only (not all categories).

Spec: test-specs/agent-hub/l2_agent-hub-trending-category-displays-agents_ELITEA-2366.md

Reuses ``AgentHubPage`` (Catalog listing + category filter chips, ELITEA-2075/2350)
for all interactions — navigation, chip clicking, category section visibility
checks, and agent card assertions.

Case-text drift (CLARIFICATION, filed — not a defect, EliteaAI/elitea-testing-public#1212):
case text mentions "reload the category items" icon next to the "Trending" heading;
**no such icon exists in the live product**. The Catalog refreshes automatically
via background WebSocket feed, with no manual-trigger UI. Asserts the heading only,
not a non-existent icon (reverse-masking guard per .agents/testing.md).
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000


class TestAgentHubTrendingCategoryDisplaysAgents:
    """ELITEA-2366: Agent Hub — Trending category displays agents (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2366_agent-hub-trending-category-displays-agents.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_trending_category_displays_agents(self, page: Page):
        """Agent Hub (Catalog) Trending category filter shows agents: filter
        chip activates, highlights, and category-specific agent cards render
        below the "Trending" section heading with zero console errors."""
        agent_hub = AgentHubPage(page)

        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()

                assert page.url.rstrip("/").endswith("/elitea-catalog"), (
                    f"Expected the Catalog URL, got: {page.url!r}"
                )

            with allure.step("Step 2 — Click the Trending category filter chip"):
                agent_hub.click_category_filter_chip("Trending")

            with allure.step("Step 3 — Verify the Trending chip is highlighted/active"):
                assert agent_hub.is_category_filter_chip_selected("Trending", timeout=UI_ELEMENT_TIMEOUT), (
                    "Trending filter chip should show selected state (data-selected='true')"
                )

            with allure.step("Step 4 — Verify agents are displayed under the Trending section"):
                # Verify the section heading is visible
                assert agent_hub.is_category_section_visible("trending", timeout=UI_ELEMENT_TIMEOUT), (
                    "'Trending' content-list section heading should be visible"
                )

                # Verify at least one agent card is rendered
                card_count = agent_hub.get_agent_card_count()
                assert card_count >= 1, (
                    f"Expected at least 1 agent card in the Trending section, got {card_count}"
                )

            with allure.step("Step 5 — Verify the section header 'Trending' appears above the results"):
                # Get all visible category headings to verify Trending is present
                visible_headings = agent_hub.get_visible_category_heading_texts()
                assert "Trending" in visible_headings, (
                    f"'Trending' heading should be in visible category headings, got: {visible_headings}"
                )

            with allure.step("Step 6 — Verify zero console errors during filter activation"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
