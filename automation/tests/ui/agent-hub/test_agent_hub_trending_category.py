"""ELITEA-2366: Agent Hub — Trending category displays agents.

Case: Verify that clicking the Trending category filter displays the
Trending section with agents listed under it.

Note: Case text references a "reload category items" icon which does NOT
exist in the live product (issue #1212). Test asserts only what exists:
the Trending section header and displayed agents.

Status: ready-for-automation
Priority: p2 (medium)
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.agent_hub_page import AgentHubPage


@pytest.mark.regression
@pytest.mark.agents
@pytest.mark.p2
class TestAgentHubTrendingCategory:
    """Test suite for Agent Hub Trending category filter behavior (ELITEA-2366)."""

    def test_agent_hub_trending_category_displays_agents(self, page: Page):
        """Verify Trending category filter shows agents when selected.

        Steps:
        1. Navigate to Agent Hub (Catalog)
        2. Click the Trending category filter chip
        3. Verify the filter is highlighted/active
        4. Verify agents are displayed under Trending section
        5. Verify the section header "Trending" is visible
        """
        agent_hub_page = AgentHubPage(page)

        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub_page.navigate()
            # Verify page URL contains elitea-catalog
            current_url = page.url
            assert "elitea-catalog" in current_url, f"Expected URL to contain 'elitea-catalog', got {current_url}"
            # Verify page heading is visible
            expect(agent_hub_page.page_heading).to_be_visible()

        with allure.step("Step 2 — Click the Trending category filter chip"):
            # The Trending section is the default view, but verify the chip
            # is present and clickable
            assert agent_hub_page.is_category_filter_chip_visible(
                "Trending", timeout=10000
            ), "Trending filter chip not found"
            # Click to ensure it's selected
            agent_hub_page.click_category_filter_chip("Trending")

        with allure.step("Step 3 — Verify the Trending filter is active"):
            # Check that the Trending chip is marked as selected
            # Uses data-selected="true" attribute per ELITEA-2352
            is_selected = agent_hub_page.is_category_filter_chip_selected(
                "Trending", timeout=10000
            )
            assert is_selected, "Trending filter chip should be selected"

        with allure.step("Step 4 — Verify agents are displayed under Trending"):
            # Wait for at least one agent card to be visible
            agent_count = agent_hub_page.get_agent_card_count()
            assert agent_count >= 1, (
                f"Expected at least 1 agent card in Trending section, "
                f"found {agent_count}"
            )

        with allure.step("Step 5 — Verify the section header Trending is visible"):
            # Verify the Trending section heading is visible and readable
            assert agent_hub_page.is_category_section_visible(
                "trending", timeout=10000
            ), "Trending section heading not found"
            # Additionally verify via visible category headings
            visible_headings = agent_hub_page.get_visible_category_heading_texts()
            assert "Trending" in visible_headings, (
                f"'Trending' heading not in visible categories. Found: {visible_headings}"
            )
