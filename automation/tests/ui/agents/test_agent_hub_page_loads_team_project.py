"""Agent Hub — page loads successfully for Team project (ELITEA-2351).

Verifies the public Agent Hub (Catalog) page (`/elitea-catalog`) loads
cleanly for a user in a Team project context: heading, search bar,
the full 11-entry category filter rail, and agent cards in the main
content area are all visible, with zero console errors.

Spec: test-specs/agent-hub/l2_agent-hub-page-loads-team-project_ELITEA-2351.md

Reuses `AgentHubPage` as-is for the heading/search/agent-card assertions
(ELITEA-2075) and `ChatPage.switch_project()/get_selected_project_text()`
for the project-switch and assertion.

Case-text drift (same as ELITEA-2350, CLARIFICATION filed —
EliteaAI/elitea-testing-public#1208): case text says the heading reads
"Welcome to Agent HUB"; live product shows "Welcome to ELITEA Catalog!"
(`catalog-page-heading`). Asserts the live text (reverse-masking guard).

New testid required (same as ELITEA-2350): `catalog-agent-category-filter-chip-{slug}`
on each MUI `Chip` in `CategoryRail.jsx` — threaded via a caller-supplied
`chipTestIdPrefix` prop from `AgentsTab` -> `CatalogBody` -> `CategoryRail`,
per `.agents/testing.md`'s "shared components never hardcode feature-scoped
testids" rule.
"""

import logging
import os

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p1]

UI_ELEMENT_TIMEOUT = 10_000

# Note: EXPECTED_PAGE_TITLE will include the actual team project name,
# so we check that it contains the "ELITEA Catalog -" prefix and a project name.
EXPECTED_PAGE_TITLE_PREFIX = "ELITEA Catalog -"
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


@pytest.fixture
def team_project_id():
    """Provide a Team project ID from environment configuration.

    This test requires ELITEA_TEAM_PROJECT_ID to be set in .env.test.
    The team project ID must be a numeric project ID (e.g., "27", "28")
    corresponding to a project that is NOT the default "Private" project
    on the test environment.

    The fixture will SKIP the test if the env var is not set, since
    the case specifically requires a Team project context and cannot
    run with only a Private project available.
    """
    team_id = os.getenv("ELITEA_TEAM_PROJECT_ID")

    if not team_id:
        pytest.skip(
            "ELITEA_TEAM_PROJECT_ID not set in environment. "
            "This test requires a Team project ID to be configured in .env.test. "
            "Example: ELITEA_TEAM_PROJECT_ID=27 (use your actual team project ID from the backend)"
        )

    return team_id


class TestAgentHubPageLoadsTeamProject:
    """ELITEA-2351: Agent Hub — page loads successfully for Team project (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2351_agent-hub-page-loads-successfully-for-team-project.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_agent_hub_page_loads_team_project(self, page: Page, team_project_id: str):
        """Agent Hub (Catalog) page loads without error for a Team-project
        user: heading, search bar, full category filter rail, and agent
        cards are all visible, with zero console errors."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)

        console_capture = agent_hub.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Switch to Team project and navigate to Agent Hub from the sidebar"
            ):
                # First navigate to /chat (any page with the project selector available)
                # so we can switch projects via the sidebar
                chat.navigate("/chat")

                # Switch to the team project via the sidebar project selector
                chat.switch_project(team_project_id)

                # Now navigate to Agent Hub while in the Team project context
                agent_hub.navigate()

                assert page.url.rstrip("/").endswith("/elitea-catalog"), (
                    f"Expected the Catalog URL, got: {page.url!r}"
                )

                page_title = page.title()
                assert page_title.startswith(EXPECTED_PAGE_TITLE_PREFIX), (
                    f"Expected page title to start with {EXPECTED_PAGE_TITLE_PREFIX!r}, "
                    f"got: {page_title!r}"
                )

                selector_text = chat.get_selected_project_text()
                # Verify it's NOT "Private" (it's a team project now)
                assert "Private" not in selector_text, (
                    f"Should be in a Team project, not Private. Got: {selector_text!r}"
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
