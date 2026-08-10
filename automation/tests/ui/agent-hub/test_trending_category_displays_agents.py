"""UI test — Trending category displays agents in Agent Hub Catalog.

Verify that the Trending category filter works: clicking the filter activates
it, agents display in the Trending section, and the section header is visible.

Test case: ELITEA-2366
AFS: test-specs/agent-hub/l2_agent-hub-trending-category-displays-agents_ELITEA-2366.md

Markers:
    - ui: requires browser
    - agent-hub: agent hub/catalog tests
    - p2: medium priority (per AFS metadata: priority medium)
    - regression
"""

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_hub_page import AgentHubPage

pytestmark = [pytest.mark.ui, pytest.mark.agent_hub, pytest.mark.p2, pytest.mark.regression]


class TestTrendingCategoryDisplaysAgents:
    """ELITEA-2366 — Trending category displays agents in Agent Hub Catalog."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/"
        "tests/automated-full-regression-ui/agent-hub/ELITEA-2366.md",
        "onetest-ai Test Case link",
    )
    def test_trending_category_displays_agents(self, page):
        """When Trending filter is applied, the section renders with visible header
        and multiple agent cards displayed underneath."""
        hub_page = AgentHubPage(page)

        with allure.step("Step 1 — Navigate to Agent Hub (Catalog page)"):
            hub_page.navigate()

        with allure.step("Step 2 — Click the Trending category filter chip"):
            hub_page.click_category_filter_chip("Trending")

        with allure.step("Step 3 — Verify the Trending filter chip is highlighted/active"):
            assert hub_page.is_category_filter_chip_selected("Trending"), (
                "Trending filter chip should be in selected state (data-selected='true')"
            )

        with allure.step("Step 4 — Verify agents are displayed under Trending section"):
            agent_count = hub_page.get_agent_card_count()
            assert agent_count > 0, f"Expected at least 1 agent card in Trending, got {agent_count}"

        with allure.step("Step 5 — Verify Trending section header is visible"):
            assert hub_page.is_category_section_visible("trending"), (
                "Trending section header should be visible"
            )
            # Verify that ONLY Trending is shown (no other category sections)
            visible_categories = hub_page.get_visible_category_heading_texts()
            assert visible_categories == ["Trending"], (
                f"Expected only [Trending] section after filter, got {visible_categories}"
            )
