"""Agent Hub — Trending category displays agents (ELITEA-2366).

Verifies that clicking the Trending category filter-rail chip on the Agent Hub
(Catalog) page (`/elitea-catalog`) selects that chip, filters the content area
to Trending agents only, and shows the matching content-list section header —
with zero console errors.

Spec: test-specs/agent-hub/l2_agent-hub-trending-category-displays-agents_ELITEA-2366.md

Reuses `AgentHubPage` as-is for navigation/heading (ELITEA-2075) and the
category filter-rail chip locators (ELITEA-2350); uses click/selected-state
helpers added in ELITEA-2352 for category filtering.

Case-text drift (CLARIFICATION, filed — not a defect,
EliteaAI/elitea-testing-public#1212): case text claims a "reload category
items" icon appears next to the filtered section header; no such icon exists
anywhere in the live product or its source. Asserts the header text only
(reverse-masking guard).

Pre-existing testids consumed: `catalog-agent-category-filter-chip-trending`,
`catalog-category-heading-trending`, `catalog-agent-card-*` (dynamic).
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000

FILTER_CATEGORY = "Trending"
EXPECTED_CATEGORY_HEADING = "Trending"
EXPECTED_PROJECT_NAME = "Private"


class TestAgentHubTrendingCategoryDisplaysAgents:
    """ELITEA-2366: Agent Hub — Trending category displays agents (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2366_agent-hub-trending-category-displays-agents.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_trending_category_displays_agents(self, page: Page):
        """Clicking the Trending category filter-rail chip selects that chip and
        filters the Agent Hub content to Trending agents only, displaying the
        section header and agent cards."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)

        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Agent Hub (Catalog)"):
                agent_hub.navigate()

                assert page.url.rstrip("/").endswith("/elitea-catalog"), (
                    f"Expected the Catalog URL, got: {page.url!r}"
                )
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
                selector_text = chat.get_selected_project_text()
                assert EXPECTED_PROJECT_NAME in selector_text, (
                    "Sidebar project selector should still show the "
                    f"{EXPECTED_PROJECT_NAME!r} project after navigation, got: {selector_text!r}"
                )

            with allure.step(f"Step 2 — Click the {FILTER_CATEGORY!r} category filter chip"):
                agent_hub.click_category_filter_chip(FILTER_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)
                # Verify the click succeeded (page remains at same URL)
                assert page.url.rstrip("/").endswith("/elitea-catalog"), (
                    f"Page should remain at /elitea-catalog after filter click, got: {page.url!r}"
                )

            with allure.step(f"Step 3 — Verify the {FILTER_CATEGORY!r} chip is highlighted/active"):
                assert agent_hub.is_category_filter_chip_selected(FILTER_CATEGORY, timeout=UI_ELEMENT_TIMEOUT), (
                    f"{FILTER_CATEGORY!r} chip should be marked selected (data-selected='true') after click"
                )

            with allure.step(f"Step 4 — Verify agents are displayed under the {FILTER_CATEGORY!r} section"):
                # Wait for at least one agent card to render
                card_count = agent_hub.get_agent_card_count()
                assert card_count >= 1, (
                    f"Expected at least 1 agent card under {FILTER_CATEGORY!r}, got {card_count}"
                )

            with allure.step(f"Step 5 — Verify the section header {EXPECTED_CATEGORY_HEADING!r} appears above the results"):
                assert agent_hub.is_category_section_visible("trending", timeout=UI_ELEMENT_TIMEOUT), (
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
