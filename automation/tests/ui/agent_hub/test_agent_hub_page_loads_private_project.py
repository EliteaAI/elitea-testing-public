"""Agent Hub — page loads successfully for Private project (ELITEA-2350).

Verifies the public Agent Hub (Catalog) page (`/elitea-catalog`) loads
cleanly for a user in the "Private" project context: heading, search bar,
the full 11-entry category filter rail, and agent cards in the main
content area are all visible, with zero console errors.

Spec: test-specs/agent-hub/l2_agent-hub-page-loads-private-project_ELITEA-2350.md

Reuses `AgentHubPage` as-is for the heading/search/agent-card assertions
(ELITEA-2075) and `ChatPage.get_selected_project_text()` by composition for
the sidebar project-selector read (same reuse-by-composition idiom
ELITEA-2075 used for `AgentDetailPage`/`AgentFormPage`).

Case-text drift (CLARIFICATION, filed — not a defect,
EliteaAI/elitea-testing-public#1208): case text says the heading reads
"Welcome to Agent HUB"; live product shows "Welcome to ELITEA Catalog!"
(`catalog-page-heading`). Asserts the live text (reverse-masking guard).

New testid this implementation added (`add-data-testid`, EliteaAI/EliteaUI
`automation/testids`): `catalog-agent-category-filter-chip-{slug}` on each
MUI `Chip` in `CategoryRail.jsx` (shared with the Skills tab) — threaded via
a caller-supplied `chipTestIdPrefix` prop from `AgentsTab` -> `CatalogBody`
-> `CategoryRail`, per `.agents/testing.md`'s "shared components never
hardcode feature-scoped testids" rule.
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p1, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000

EXPECTED_PAGE_TITLE = "ELITEA Catalog - Private"
EXPECTED_PROJECT_NAME = "Private"
EXPECTED_PAGE_HEADING = "Welcome to ELITEA Catalog!"
EXPECTED_SEARCH_PLACEHOLDER = "Search for agents"

FEATURED_CATEGORY_LABELS = ["Trending", "My Liked"]
OTHER_CATEGORY_LABELS = [
    "Business Analyst",
    "DevOps",
    "Development",
    "Elitea",
    "Epam",
    "Knowledge & Documentation",
    "Project Management",
    "Quality Assurance",
    "Other",
]


class TestAgentHubPageLoadsPrivateProject:
    """ELITEA-2350: Agent Hub — page loads successfully for Private project (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2350_agent-hub-page-loads-successfully-for-private-project.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_agent_hub_page_loads_private_project(self, page: Page):
        """Agent Hub (Catalog) page loads without error for a Private-project
        user: heading, search bar, full category filter rail, and agent
        cards are all visible, with zero console errors."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)

        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Agent Hub from the sidebar while the active project is 'Private'"
            ):
                agent_hub.navigate()

                assert page.url.rstrip("/").endswith("/elitea-catalog"), (
                    f"Expected the Catalog URL, got: {page.url!r}"
                )
                assert page.title() == EXPECTED_PAGE_TITLE, (
                    f"Expected page title {EXPECTED_PAGE_TITLE!r}, got: {page.title()!r}"
                )
                selector_text = chat.get_selected_project_text()
                assert EXPECTED_PROJECT_NAME in selector_text, (
                    "Sidebar project selector should still show the "
                    f"{EXPECTED_PROJECT_NAME!r} project after navigation, got: {selector_text!r}"
                )

            with allure.step("Step 2 — Verify the page loads with the Catalog heading"):
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
                heading_text = (agent_hub.page_heading.text_content() or "").strip()
                assert heading_text == EXPECTED_PAGE_HEADING, (
                    f"Expected the live heading text {EXPECTED_PAGE_HEADING!r}, got: {heading_text!r}"
                )

            with allure.step("Step 3 — Verify the search bar is visible at the top center"):
                assert agent_hub.search_input.is_visible(), "Catalog search bar should be visible"
                placeholder = agent_hub.search_input.get_attribute("placeholder")
                assert placeholder == EXPECTED_SEARCH_PLACEHOLDER, (
                    f"Expected search placeholder {EXPECTED_SEARCH_PLACEHOLDER!r}, got: {placeholder!r}"
                )

            with allure.step("Step 4 — Verify all 11 category filter chips are displayed"):
                for label in FEATURED_CATEGORY_LABELS:
                    assert agent_hub.is_category_filter_chip_visible(label, timeout=UI_ELEMENT_TIMEOUT), (
                        f"'Featured' category filter chip {label!r} should be visible"
                    )
                for label in OTHER_CATEGORY_LABELS:
                    assert agent_hub.is_category_filter_chip_visible(label, timeout=UI_ELEMENT_TIMEOUT), (
                        f"'Categories' category filter chip {label!r} should be visible"
                    )

            with allure.step("Step 5 — Verify agent cards are displayed in the main content area"):
                assert agent_hub.is_category_section_visible("trending", timeout=UI_ELEMENT_TIMEOUT), (
                    "'Trending' content-list heading should be visible"
                )
                card_count = agent_hub.get_agent_card_count()
                assert card_count >= 1, (
                    f"Expected at least 1 agent card in the main content area, got {card_count}"
                )

            with allure.step("Step 6 — Verify zero console errors during the whole page load"):
                assert not console_capture, (
                    f"Unexpected console errors: {[m.text for m in console_capture]!r}"
                )
        finally:
            console_capture.stop()
