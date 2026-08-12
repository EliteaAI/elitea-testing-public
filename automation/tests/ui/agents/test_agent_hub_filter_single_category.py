"""Agent Hub — filter agents by single category (ELITEA-2352).

Verifies that clicking a single category filter-rail chip on the Agent Hub
(Catalog) page (`/elitea-catalog`) selects that chip, filters the content
area to that category's agents only, and shows the matching content-list
section header — with zero console errors.

Spec: test-specs/agent-hub/l3_agent-hub-filter-by-single-category_ELITEA-2352.md

Reuses `AgentHubPage` as-is for navigation/heading (ELITEA-2075) and the
category filter-rail chip locators (ELITEA-2350); adds click/selected-state
helpers to the same page object for this case.

Case-text drift (CLARIFICATION, filed — not a defect,
EliteaAI/elitea-testing-public#1212): case text claims a "reload category
items" icon appears next to the filtered section header; no such icon exists
anywhere in the live product or its source. Asserts the header text only.

New testid attribute this implementation added (JSX edit, EliteaAI/EliteaUI
`automation/testids`, EliteaAI/EliteaUI@9b93f67c): `data-selected="true"/"false"`
on each category filter-rail chip in `CategoryRail.jsx` — Playwright's own
accessibility-tree `[active]` marker on the chip reflects DOM focus, not the
app's selection state, so it cannot be used to assert "selected".
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000

FILTER_CATEGORY = "Business Analyst"
EXPECTED_CATEGORY_HEADING = "Business Analyst"
EXPECTED_AGENT_NAMES = {
    "Elitea Feature Story Generator",
    "User Story Creator",
    "AI Platform Design Advisor",
    "Business Analyst",
}


class TestAgentHubFilterSingleCategory:
    """ELITEA-2352: Agent Hub — filter agents by single category (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2352_agent-hub-filter-agents-by-single-category.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_filter_by_single_category(self, page: Page):
        """Clicking a single category filter-rail chip selects that chip and
        filters the Agent Hub content to that category's agents only."""
        agent_hub = AgentHubPage(page)

        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step(f"Step 2 — Click the {FILTER_CATEGORY!r} category filter-rail chip"):
                agent_hub.click_category_filter_chip(FILTER_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Verify the selected chip is highlighted/active"):
                assert agent_hub.is_category_filter_chip_selected(FILTER_CATEGORY, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{FILTER_CATEGORY!r} chip should be marked selected (data-selected='true') after click"
                )

            with allure.step(f"Step 4 — Verify only {FILTER_CATEGORY!r} agents are displayed"):
                visible_headings = agent_hub.get_visible_category_heading_texts()
                assert visible_headings == [EXPECTED_CATEGORY_HEADING], (
                    "Expected exactly one content-list category section "
                    f"({EXPECTED_CATEGORY_HEADING!r}) after filtering, got: {visible_headings!r}"
                )

                for agent_name in EXPECTED_AGENT_NAMES:
                    assert agent_hub.get_agent_card(agent_name).is_visible(), (
                        f"Expected agent card {agent_name!r} to be visible under the "
                        f"{FILTER_CATEGORY!r} filter"
                    )

            with allure.step(
                f"Step 5 — Verify the section header {EXPECTED_CATEGORY_HEADING!r} appears above the results"
            ):
                assert agent_hub.is_category_section_visible("business-analyst", timeout=UI_ELEMENT_TIMEOUT), (
                    f"{EXPECTED_CATEGORY_HEADING!r} content-list heading should be visible above the results"
                )
                # Case text also claims a "reload category items" icon next to the header — confirmed
                # absent from the live product (CLARIFICATION filed,
                # EliteaAI/elitea-testing-public#1212); not asserted here (reverse-masking guard).

            with allure.step("Step 6 — Verify zero console errors during the filter interaction"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
