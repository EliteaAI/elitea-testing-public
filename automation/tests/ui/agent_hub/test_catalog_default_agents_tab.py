"""Test: Catalog default view opens on Agents tab and user must click Skills to navigate.

ELITEA-2370: Verify the Catalog page loads with Agents tab selected by default,
and clicking the Skills tab activates it and switches the view.

AFS: test-specs/agent-hub/l3_catalog-default-agents-tab_ELITEA-2370.md
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.agent_hub_page import AgentHubPage


class TestCatalogDefaultAgentsTab:
    """Catalog page navigation: Agents default, Skills tab toggle."""

    @pytest.mark.p3
    @pytest.mark.regression
    @pytest.mark.agent_hub
    @allure.title("Catalog default view opens on Agents tab; user clicks Skills to switch")
    @allure.description(
        "Verify Catalog page loads with Agents tab active by default, Skills tab visible, "
        "and that clicking Skills switches both tab state and main content area to Skills content."
    )
    def test_catalog_default_agents_tab_switch_to_skills(self, page: Page):
        """
        ELITEA-2370: Catalog default view and tab navigation.

        Steps:
        1. Navigate to Catalog (/elitea-catalog)
        2. Verify page heading is visible
        3. Verify Agents tab is selected by default (aria-selected=true)
        4. Verify Skills tab is visible with icon
        5. Verify main content displays Agents-related content
        6. Verify right panel shows FEATURED + CATEGORIES filters
        7. Click Skills tab
        8. Verify Skills tab becomes active (aria-selected=true)
        9. Verify main content switches to Skills-related content
        10. Verify right panel filters update to Skills scope
        """

        agent_hub = AgentHubPage(page)

        # Step 1: Navigate to Catalog
        with allure.step("Step 1 — Navigate to Catalog"):
            agent_hub.navigate()

        # Step 2: Verify page heading visible
        with allure.step("Step 2 — Verify page heading 'Welcome to ELITEA Catalog!'"):
            expect(agent_hub.page_heading).to_have_text("Welcome to ELITEA Catalog!")

        # Step 3: Verify Agents tab selected by default
        with allure.step("Step 3 — Verify Agents tab selected by default"):
            expect(agent_hub.agents_tab).to_have_attribute("aria-selected", "true")

        # Step 4: Verify Skills tab visible with icon
        with allure.step("Step 4 — Verify Skills tab visible with icon"):
            expect(agent_hub.skills_tab).to_be_visible()
            # Verify Skills tab contains an icon (svg or Icon component child)
            icon = agent_hub.skills_tab.locator("svg, [class*='Icon']")
            assert icon.count() > 0, "Skills tab should contain an icon"

        # Step 5: Verify main content displays Agents content
        with allure.step("Step 5 — Verify main content displays Agents content"):
            main_content = agent_hub.get_main_content()
            main_text = main_content.text_content().lower()
            assert (
                "agent" in main_text
            ), f"Main content should contain 'agent' text, got: {main_text[:100]}"

        # Step 6: Verify right panel shows FEATURED + CATEGORIES filters
        with allure.step("Step 6 — Verify right panel shows FEATURED + CATEGORIES filters"):
            # Count filter chips in Agents view
            agent_filter_chips = page.locator(agent_hub.AGENT_CATEGORY_FILTER_CHIP_PREFIX)
            chip_count = agent_filter_chips.count()
            assert (
                chip_count >= 11
            ), f"Expected ≥11 agent filter chips (2 FEATURED + 9 CATEGORIES), got {chip_count}"

            # Verify FEATURED section visible
            page_text = page.content()
            assert "Featured" in page_text or "FEATURED" in page_text, "Right panel should show 'FEATURED'"
            assert "Categories" in page_text or "CATEGORIES" in page_text, "Right panel should show 'CATEGORIES'"

        # Step 7: Click Skills tab
        with allure.step("Step 7 — Click Skills tab"):
            agent_hub.skills_tab.click()
            # Wait for at least one skill filter chip to appear before proceeding
            page.wait_for_selector(agent_hub.SKILL_CATEGORY_FILTER_CHIP_PREFIX, timeout=10000)
            page.wait_for_timeout(1000)  # Extra settle time

        # Step 8: Verify Skills tab becomes active
        with allure.step("Step 8 — Verify Skills tab becomes active"):
            expect(agent_hub.skills_tab).to_have_attribute("aria-selected", "true")

        # Step 9: Verify main content switches to Skills content
        with allure.step("Step 9 — Verify main content switches to Skills content"):
            main_text = main_content.text_content().lower()
            assert "skill" in main_text, f"Main content should contain 'skill' text, got: {main_text[:100]}"

        # Step 10: Verify right panel filters update to Skills scope
        with allure.step("Step 10 — Verify right panel filters update to Skills scope"):
            # Verify filter chips changed from agent-scoped to skill-scoped testid prefix
            # (the actual count depends on how many Skills exist in each category in the project)
            skill_filter_chips = page.locator(agent_hub.SKILL_CATEGORY_FILTER_CHIP_PREFIX)
            skills_chip_count = skill_filter_chips.count()
            assert (
                skills_chip_count > 0
            ), f"Expected skill-scoped filter chips to exist, got {skills_chip_count}"

            # Verify agent-scoped filter chips are NO LONGER visible
            agent_filter_chips = page.locator(agent_hub.AGENT_CATEGORY_FILTER_CHIP_PREFIX)
            agent_chip_count_after = agent_filter_chips.count()
            assert (
                agent_chip_count_after == 0
            ), f"Agent-scoped chips should not be visible in Skills tab, but found {agent_chip_count_after}"
