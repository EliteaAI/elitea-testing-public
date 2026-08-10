"""UI test — Catalog default Agents tab and Skills tab navigation.

Verify that the Catalog page loads with the Agents tab selected by default,
the Skills tab is available, and clicking Skills switches both the tab state
and content display.

Test case: ELITEA-2370
AFS: test-specs/agent-hub/l2_catalog-agents-skills-tabs_ELITEA-2370.md

Markers:
    - ui: requires browser
    - agent-hub: agent hub/catalog tests
    - p2: medium priority (per AFS metadata: priority high → p2)
    - regression
"""

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_hub_page import AgentHubPage

pytestmark = [pytest.mark.ui, pytest.mark.agent_hub, pytest.mark.p2, pytest.mark.regression]


class TestCatalogTabsNavigation:
    """ELITEA-2370 — Catalog default Agents tab & tab navigation to Skills."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/"
        "tests/automated-full-regression-ui/agent-hub/ELITEA-2370.md",
        "onetest-ai Test Case link",
    )
    def test_default_agents_and_skills_switch(self, page):
        """When the Catalog page loads, Agents tab is selected by default.
        User can click Skills tab to switch to Skills content."""
        hub_page = AgentHubPage(page)

        with allure.step("Step 1 — Navigate to Catalog page"):
            hub_page.navigate()

        with allure.step("Step 2 — Verify 'Welcome to ELITEA Catalog!' heading loads"):
            hub_page.page_heading.wait_for(state="visible", timeout=10000)
            heading_text = hub_page.page_heading.text_content()
            assert "Welcome to ELITEA Catalog!" in heading_text, (
                f"Expected 'Welcome to ELITEA Catalog!' heading, got '{heading_text}'"
            )

        with allure.step("Step 3 — Verify Agents tab is selected by default"):
            assert hub_page.is_agents_tab_selected(), (
                "Agents tab should be selected (aria-selected='true') on page load"
            )

        with allure.step("Step 4 — Verify Skills tab is visible"):
            assert hub_page.is_skills_tab_visible(), "Skills tab should be visible"

        with allure.step("Step 5 — Verify main content displays Agents content"):
            agent_count = hub_page.get_agent_card_count()
            assert agent_count > 0, (
                f"Expected at least 1 agent card on default Agents view, got {agent_count}"
            )

        with allure.step("Step 6 — Click the Skills tab"):
            hub_page.click_skills_tab()

        with allure.step("Step 7 — Verify Skills tab becomes active/selected"):
            assert hub_page.is_skills_tab_selected(), (
                "Skills tab should be selected (aria-selected='true') after click"
            )

        with allure.step("Step 8 — Verify Agents tab is no longer selected"):
            assert not hub_page.is_agents_tab_selected(), (
                "Agents tab should no longer be selected after switching to Skills"
            )

        with allure.step("Step 9 — Verify right panel shows category filters"):
            # Right panel should be visible with filter chips
            hub_page.wait_for_filter_panel_visible(timeout=5000)
