"""Agent Hub — filter agents by multiple categories simultaneously (ELITEA-2353).

Verifies that clicking multiple category filter-rail chips on the Agent Hub
(Catalog) page (`/elitea-catalog`) accumulates the filters: both chips remain
selected, and agents from both categories are displayed simultaneously in
separate labeled sections — with zero console errors.

Spec: test-specs/agent-hub/l2_agent-hub-filter-by-multiple-categories_ELITEA-2353.md

Reuses `AgentHubPage` from ELITEA-2352 (single-category filtering) — all
required methods already exist. This case tests the multi-select accumulation
behavior: after the first chip click, the second chip click does NOT deselect
the first — both remain selected and both categories' agents render together.

Case-text drift (CLARIFICATION, filed — not a defect,
EliteaAI/elitea-testing-public#1212): case text claims a "reload category
items" icon appears next to filtered section headers; no such icon exists
anywhere in the live product or its source. Asserts the header text only.
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000

FIRST_CATEGORY = "Business Analyst"
SECOND_CATEGORY = "Elitea"

# Business Analyst category has these agents (confirmed live during analysis)
BUSINESS_ANALYST_AGENTS = {
    "Elitea Feature Story Generator",
    "User Story Creator",
    "AI Platform Design Advisor",
    "Business Analyst",
}


class TestAgentHubFilterMultipleCategories:
    """ELITEA-2353: Agent Hub — filter agents by multiple categories simultaneously (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2353_agent-hub-filter-agents-by-multiple-categories.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_filter_by_multiple_categories(self, page: Page):
        """Clicking multiple category filter-rail chips accumulates filters:
        both chips remain selected and agents from both categories display
        simultaneously in separate labeled sections."""
        agent_hub = AgentHubPage(page)

        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step(f"Step 2 — Click the {FIRST_CATEGORY!r} category filter-rail chip"):
                agent_hub.click_category_filter_chip(FIRST_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(f"Step 3 — Click the {SECOND_CATEGORY!r} category filter-rail chip while {FIRST_CATEGORY!r} remains selected"):
                agent_hub.click_category_filter_chip(SECOND_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(f"Step 4 — Verify both {FIRST_CATEGORY!r} and {SECOND_CATEGORY!r} chips are highlighted/active"):
                assert agent_hub.is_category_filter_chip_selected(
                    FIRST_CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"{FIRST_CATEGORY!r} chip should remain selected (data-selected='true') "
                    "after second chip click (multi-select accumulation)"
                )

                assert agent_hub.is_category_filter_chip_selected(
                    SECOND_CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"{SECOND_CATEGORY!r} chip should be marked selected (data-selected='true') after click"
                )

            with allure.step(f"Step 5 — Verify both {FIRST_CATEGORY!r} and {SECOND_CATEGORY!r} agents are displayed in separate labeled sections"):
                visible_headings = agent_hub.get_visible_category_heading_texts()
                assert len(visible_headings) == 2, (
                    "Expected exactly two content-list category sections after multi-select filter, "
                    f"got {len(visible_headings)}: {visible_headings!r}"
                )

                assert "Business Analyst" in visible_headings, (
                    f"Expected 'Business Analyst' section in visible headings, got: {visible_headings!r}"
                )

                assert "Elitea" in visible_headings, (
                    f"Expected 'Elitea' section in visible headings, got: {visible_headings!r}"
                )

            with allure.step(f"Step 6 — Verify section headers and agents from both {FIRST_CATEGORY!r} and {SECOND_CATEGORY!r} are visible"):
                # Verify Business Analyst section header
                assert agent_hub.is_category_section_visible(
                    "business-analyst", timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"{FIRST_CATEGORY!r} content-list heading should be visible"
                )

                # Verify Elitea section header
                assert agent_hub.is_category_section_visible(
                    "elitea", timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"{SECOND_CATEGORY!r} content-list heading should be visible"
                )

                # Verify Business Analyst agents are visible
                for agent_name in BUSINESS_ANALYST_AGENTS:
                    assert agent_hub.get_agent_card(agent_name).is_visible(), (
                        f"Expected agent card {agent_name!r} to be visible under the "
                        f"{FIRST_CATEGORY!r} section"
                    )

                # Case text also claims a "reload category items" icon next to each header — confirmed
                # absent from the live product (CLARIFICATION filed,
                # EliteaAI/elitea-testing-public#1212); not asserted here (reverse-masking guard).

            with allure.step("Step 7 — Verify zero console errors during the multi-click filter interaction"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
