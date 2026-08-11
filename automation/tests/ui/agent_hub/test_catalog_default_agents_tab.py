"""Test: Catalog default view opens on Agents tab and user clicks Skills to navigate.

ELITEA-2370: Verify the Catalog page loads with the Agents tab selected by
default, and that clicking the Skills tab activates it and switches the
right-panel filter rail + main content from Agents-scoped to Skills-scoped.

AFS: test-specs/agent-hub/l1_catalog-default-agents-and-skills-tabs_ELITEA-2370.md
"""

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.ui, pytest.mark.agent_hub, pytest.mark.regression, pytest.mark.p1]


class TestCatalogDefaultAgentsTab:
    """Catalog default-tab state and Agents <-> Skills tab navigation."""

    @allure.title("Catalog defaults to Agents tab; clicking Skills switches tab + content")
    @allure.description(
        "Verify the Catalog page loads with the Agents tab selected by default (aria-selected), "
        "the Skills tab is visible with its icon, and the main content area (agent-scoped filter "
        "rail + agent cards) reflects the Agents tab. Clicking Skills activates it and switches "
        "the right-panel filter rail from agent-scoped to skill-scoped chips, with Agents tab "
        "content unmounting."
    )
    def test_catalog_default_agents_tab_and_skills_navigation(self, page: Page):
        """
        ELITEA-2370: Catalog default view opens on Agents tab; Skills tab click navigates.

        Steps:
        1. Navigate to Catalog
        2. Verify page heading "Welcome to ELITEA Catalog!"
        3. Verify Agents tab selected by default
        4. Verify Skills tab visible with icon
        5. Verify main content displays Agents content by default
        6-7. Click Skills tab; verify it becomes active
        8. Verify main content switches to Skills
        9. Right panel FEATURED + CATEGORIES filters (folded into steps 5/8 chip counts)
        """

        agent_hub = AgentHubPage(page)

        with allure.step("Step 1 — Navigate to Catalog"):
            agent_hub.navigate()

        with allure.step("Step 2 — Verify page heading 'Welcome to ELITEA Catalog!'"):
            expect(agent_hub.page_heading).to_be_visible()
            expect(agent_hub.page_heading).to_have_text("Welcome to ELITEA Catalog!")

        with allure.step("Step 3 — Verify Agents tab selected by default"):
            assert agent_hub.is_agents_tab_selected(), "Agents tab should be aria-selected by default"
            assert not agent_hub.is_skills_tab_selected(), "Skills tab should not be selected by default"

        with allure.step("Step 4 — Verify Skills tab visible with its icon"):
            assert agent_hub.skills_tab.is_visible(), "Skills tab should be visible"
            assert agent_hub.skills_tab_icon.is_visible(), "Skills tab's icon should be visible"

        with allure.step("Step 5 — Verify main content displays Agents content by default"):
            agent_hub.wait_for_any_agent_card()
            agent_chips = agent_hub.get_visible_category_filter_chips()
            skill_chips = agent_hub.get_visible_skill_category_filter_chips()
            # Web-first, auto-retrying: the filter-rail's own categories fetch can settle
            # a beat after wait_for_any_agent_card() resolves (confirmed live — a one-shot
            # .count() read taken immediately raced the rail and read a partial chip set).
            # Expected: 11 agent-scoped filter chips (2 FEATURED + 9 CATEGORIES) visible by default.
            expect(agent_chips).to_have_count(11, timeout=10000)
            # Expected: skill-scoped filter chips not present on the Agents tab.
            expect(skill_chips).to_have_count(0, timeout=5000)

        with allure.step("Step 6 — Click the Skills tab"):
            agent_hub.click_skills_tab()

        with allure.step("Step 7 — Verify Skills tab active after click"):
            assert agent_hub.is_skills_tab_selected(), "Skills tab should be aria-selected after click"
            assert not agent_hub.is_agents_tab_selected(), "Agents tab should no longer be selected"

        with allure.step("Step 8 — Verify main content switches to Skills"):
            agent_hub.wait_for_agent_card_count(0)
            skill_chips_after = agent_hub.get_visible_skill_category_filter_chips()
            agent_chips_after = agent_hub.get_visible_category_filter_chips()
            # Same race as Step 5 (rail settles a beat after the card-count signal) —
            # auto-retrying expect() instead of a one-shot .count() read.
            # Expected: 11 skill-scoped filter chips (2 FEATURED + 9 CATEGORIES) after switching.
            expect(skill_chips_after).to_have_count(11, timeout=10000)
            # Expected: agent-scoped filter chips not present on the Skills tab.
            expect(agent_chips_after).to_have_count(0, timeout=5000)

        # Step 9 (right panel FEATURED + CATEGORIES filters) is verified by the
        # chip-count assertions folded into Steps 5 and 8 above — see AFS Step 9 note.
