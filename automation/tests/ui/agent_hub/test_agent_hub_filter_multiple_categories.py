"""Agent Hub — filter agents by multiple categories simultaneously (ELITEA-2353).

Verifies that clicking multiple category filter-rail chips on the Agent Hub
(Catalog) page (`/elitea-catalog`) accumulates the filters: both chips remain
selected, and agents from both categories are displayed simultaneously in
separate labeled sections — with zero console errors.

Spec: test-specs/agent-hub/l2_agent-hub-filter-by-multiple-categories_ELITEA-2353.md

Reuses `AgentHubPage` from ELITEA-2352 (single-category filtering) — all
required methods already exist, no page-object changes needed. This case
tests the multi-select accumulation behavior: after the first chip click,
the second chip click does NOT deselect the first — both remain selected and
both categories' agents render together (confirmed live during this
dispatch's exploration: `data-selected="true"` on both chips, content-list
headings `["Business Analyst", "Elitea"]` in that order, 5 agent cards total
— 4 Business Analyst + 1 Elitea).

Each step's expected result is asserted immediately within that step's own
`allure.step` block, not deferred to a later step — in particular Step 3's
"both chips selected" check sits in Step 3 (the click-then-verify pairing the
AFS specifies), not pushed into a separate step, per the standing correction
from this case's prior review round.

Case-text drift (CLARIFICATION, filed — not a defect,
EliteaAI/elitea-testing-public#1212): case text claims a "reload category
items" icon appears next to filtered section headers; no such icon exists
anywhere in the live product. Asserts the header text only.

Orchestrator's independent 3x gate hit 1/3 fresh red — an intermittent
console-error 404 at Step 7. Reproduced live (1/12 fresh re-runs) with
temporary debug instrumentation; root-caused as the same known defect
already filed on a sibling case — see ``_is_known_1434_montserrat_font_404``
below.
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p1, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000

FIRST_CATEGORY = "Business Analyst"
SECOND_CATEGORY = "Elitea"


# Known defect elitea-testing-public#1434 (already filed) — an intermittent
# 404 fetching a Montserrat ``.woff2`` file from Google's Fonts CDN
# (fonts.gstatic.com). NOT tied to this test's own flow: EliteaUI's
# ``index.html`` loads Montserrat via a Google Fonts CSS ``<link>`` tag, so
# the woff2 fetch happens on EVERY page render, app-wide — unrelated to the
# Agent Hub category filter-rail or the content-list sections this test
# exercises. ``fonts.gstatic.com`` URLs are content-hashed and essentially
# never 404 once published, so this reads as a transient CDN/network blip
# rather than a broken reference. Live-confirmed via temporary debug
# instrumentation (a print of ``msg.text``/``msg.location`` for every raw
# console error) during this fix-only pass: 1/12 fresh re-runs surfaced the
# exact signature below; removed the debug code once confirmed. Same
# filter-by-resource-URL technique already established by
# ``test_agent_hub_started_conversation_has_agent_as_participant.py``'s
# identically-named helper — match on BOTH ``msg.text`` and
# ``(msg.location or {}).get("url", "")``, never a blanket "any 404" filter.
def _is_known_1434_montserrat_font_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "fonts.gstatic.com" in location_url and "montserrat" in location_url

# Business Analyst category has these agents (confirmed live during analysis and
# re-confirmed live during this implementer dispatch).
BUSINESS_ANALYST_AGENTS = {
    "Elitea Feature Story Generator",
    "User Story Creator",
    "AI Platform Design Advisor",
    "Business Analyst",
}
# Elitea category has this agent (confirmed live during this implementer dispatch:
# 1 card, "Assistant for ELITEA Documentation").
ELITEA_CATEGORY_AGENTS = {
    "Assistant for ELITEA Documentation",
}
EXPECTED_TOTAL_CARD_COUNT = len(BUSINESS_ANALYST_AGENTS) + len(ELITEA_CATEGORY_AGENTS)


class TestAgentHubFilterMultipleCategories:
    """ELITEA-2353: Agent Hub — filter agents by multiple categories simultaneously (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2353_agent-hub-filter-agents-by-multiple-categories.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
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

                for label in (
                    "Trending",
                    "My Liked",
                    "Business Analyst",
                    "DevOps",
                    "Development",
                    "Elitea",
                    "Epam",
                    "Knowledge & Documentation",
                    "Project Management",
                    "Quality Assurance",
                    "Other",
                ):
                    assert agent_hub.is_category_filter_chip_visible(label, timeout=UI_ELEMENT_TIMEOUT), (
                        f"Category filter-rail chip {label!r} should be visible"
                    )

            with allure.step(f"Step 2 — Click the {FIRST_CATEGORY!r} category filter-rail chip"):
                agent_hub.click_category_filter_chip(FIRST_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)

                assert agent_hub.is_category_filter_chip_selected(
                    FIRST_CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                ), f"{FIRST_CATEGORY!r} chip should be marked selected (data-selected='true') after click"

            with allure.step(
                f"Step 3 — Click the {SECOND_CATEGORY!r} category filter-rail chip while "
                f"{FIRST_CATEGORY!r} remains selected"
            ):
                agent_hub.click_category_filter_chip(SECOND_CATEGORY, timeout=UI_ELEMENT_TIMEOUT)

                assert agent_hub.is_category_filter_chip_selected(
                    FIRST_CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"{FIRST_CATEGORY!r} chip should remain selected (data-selected='true') "
                    "after the second chip click (multi-select accumulation)"
                )
                assert agent_hub.is_category_filter_chip_selected(
                    SECOND_CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                ), f"{SECOND_CATEGORY!r} chip should be marked selected (data-selected='true') after click"

            with allure.step(
                f"Step 4 — Verify both {FIRST_CATEGORY!r} and {SECOND_CATEGORY!r} category sections "
                "are displayed, and no others"
            ):
                visible_headings = agent_hub.get_visible_category_heading_texts()
                assert len(visible_headings) == 2, (
                    "Expected exactly two content-list category sections after the accumulated "
                    f"multi-select filter, got {len(visible_headings)}: {visible_headings!r}"
                )
                assert set(visible_headings) == {FIRST_CATEGORY, SECOND_CATEGORY}, (
                    f"Expected sections for exactly {{{FIRST_CATEGORY!r}, {SECOND_CATEGORY!r}}} "
                    f"and no other category, got: {visible_headings!r}"
                )

            with allure.step(
                f"Step 5 — Verify section headers {FIRST_CATEGORY!r} and {SECOND_CATEGORY!r} appear, "
                f"{FIRST_CATEGORY!r} positioned before {SECOND_CATEGORY!r}"
            ):
                assert agent_hub.is_category_section_visible("business-analyst", timeout=UI_ELEMENT_TIMEOUT), (
                    f"{FIRST_CATEGORY!r} content-list heading should be visible"
                )
                assert agent_hub.is_category_section_visible("elitea", timeout=UI_ELEMENT_TIMEOUT), (
                    f"{SECOND_CATEGORY!r} content-list heading should be visible"
                )

                visible_headings = agent_hub.get_visible_category_heading_texts()
                assert visible_headings == [FIRST_CATEGORY, SECOND_CATEGORY], (
                    f"Expected {FIRST_CATEGORY!r} positioned before {SECOND_CATEGORY!r}, "
                    f"got order: {visible_headings!r}"
                )

            with allure.step(
                f"Step 6 — Verify agents from both {FIRST_CATEGORY!r} and {SECOND_CATEGORY!r} are "
                "displayed in their respective sections, and no cards from other categories"
            ):
                for agent_name in BUSINESS_ANALYST_AGENTS:
                    assert agent_hub.get_agent_card(agent_name).is_visible(), (
                        f"Expected agent card {agent_name!r} to be visible under the "
                        f"{FIRST_CATEGORY!r} section"
                    )
                for agent_name in ELITEA_CATEGORY_AGENTS:
                    assert agent_hub.get_agent_card(agent_name).is_visible(), (
                        f"Expected agent card {agent_name!r} to be visible under the "
                        f"{SECOND_CATEGORY!r} section"
                    )

                card_count = agent_hub.get_agent_card_count()
                assert card_count == EXPECTED_TOTAL_CARD_COUNT, (
                    f"Expected exactly {EXPECTED_TOTAL_CARD_COUNT} agent cards total "
                    f"({len(BUSINESS_ANALYST_AGENTS)} {FIRST_CATEGORY!r} + "
                    f"{len(ELITEA_CATEGORY_AGENTS)} {SECOND_CATEGORY!r}, no cards from other "
                    f"categories), got {card_count}"
                )

                # Case text also claims a "reload category items" icon next to each header —
                # confirmed absent from the live product (CLARIFICATION filed,
                # EliteaAI/elitea-testing-public#1212); not asserted here (reverse-masking guard).

            with allure.step("Step 7 — Verify zero console errors during the multi-click filter interaction"):
                # Known defect: elitea-testing-public#1434 — the app-wide Montserrat
                # webfont CDN 404 (see _is_known_1434_montserrat_font_404 docstring
                # above); filtered by resource URL, not a blanket 404 exclusion.
                unexpected_errors = [m.text for m in console_capture if not _is_known_1434_montserrat_font_404(m)]
                assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"
        finally:
            console_capture.stop()
