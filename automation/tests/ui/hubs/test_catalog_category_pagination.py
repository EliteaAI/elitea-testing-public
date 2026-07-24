"""UI Test for GAP-054 — Catalog: Category section "Show more"/"Show less"
pagination expands and collapses cards.

Local-file-backed coverage-gap case (board `cov60`; no onetest TMS entry —
see `.agents/automation-board/campaigns/cov60.md` decision #6: GAP-* cases
back-write to their own case file, not the onetest TMS).

Verifies a category with more items than the initial display count
(``INITIAL_CARD_DISPLAY_COUNT.DEFAULT`` = 6, confirmed live at this suite's
1366x768 headless viewport — well under the 1800px `prompt_list_xl`
breakpoint that would otherwise raise it to 8) exposes "Show more", reveals
additional cards on click, flips its label to "Show less", and collapses
back to exactly the initial count on a second click.

Uses the live, read-only ``Other`` category on the Agents tab (35 items at
analysis time — incidental shared-suite test-fixture cruft, not a seeded
fixture, see AFS § Test Data) — comfortably above the 6-item initial count,
and a regular (non-paginated) bucket, so the click is a pure client-side
re-slice with no network dependency (confirmed live: zero network requests
fire on either click).

Step 8 of the source case (the network-driven loading-skeleton branch,
``isLoadingMore``) is intentionally NOT automated here: it is structurally
unreachable via user interaction in the current codebase, root-caused to a
confirmed product defect
(EliteaAI/elitea-testing-public#1016 — the "Show more" toggle permanently
locks to "Show less" after the first click, so ``handleShowMore`` can never
be invoked a second time to trigger the network branch, on ANY category).
See the AFS § Blocked Steps and § Known Defects Found — not asserted here,
not masked; a real product bug filed separately.

AFS: test-specs/hubs/l3_category-show-more-show-less-pagination_GAP-054.md

Markers:
    - ui: requires browser
    - regression: regression test
    - hubs: Agent Hub / Skill Hub / Catalog tests
    - p2: medium priority (matches case priority)

Usage:
    cd automation
    pytest tests/ui/hubs/test_catalog_category_pagination.py -v
"""

import allure
import pytest
from pages.catalog_page import CatalogPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.hubs]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
CATEGORY_SECTION_TIMEOUT = 15_000  # initial page/category render
CARD_COUNT_CHANGE_TIMEOUT = 10_000  # client-side re-slice settle after a toggle click

CATEGORY_NAME = "Other"
# The initial display count this suite's viewport (1366x768, well under the
# 1800px `prompt_list_xl` breakpoint) always uses — confirmed live, AFS §
# Preconditions / test-specs/hubs/_surface.md § Viewport gotcha.
INITIAL_DISPLAY_COUNT = 6


@allure.epic("Agent Hub / Catalog")
@allure.feature("Category Show more / Show less pagination")
class TestCatalogCategoryPagination:
    """GAP-054 — 'Other' category Show more/Show less expand-collapse cycle.

    One live expand + one live collapse cycle, matching the case's own
    Pass/Fail criteria exactly. A confirmed product defect (#1016) makes a
    SECOND expand structurally unreachable via this control on ANY
    category — not exercised here, see the module docstring.
    """

    @pytest.mark.p2
    @allure.title("Catalog category Show more/Show less expands then collapses to the initial count")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1016",
        "Known defect #1016 (found during analysis, NOT asserted live here — see docstring)",
    )
    def test_category_show_more_show_less_pagination(self, page):
        """'Other' category: Show more reveals cards + flips label; Show less collapses back."""
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        catalog_page = CatalogPage(page)

        with allure.step(
            f"Step 1 — Open the '{CATEGORY_NAME}' category section (holds more items than "
            "the initial display count); grid renders exactly the initial count"
        ):
            catalog_page.navigate_to_tab("agents")
            catalog_page.category_section(CATEGORY_NAME).wait_for(
                state="visible", timeout=CATEGORY_SECTION_TIMEOUT,
            )
            initial_count = catalog_page.get_category_card_count(CATEGORY_NAME)
            assert initial_count == INITIAL_DISPLAY_COUNT, (
                f"'{CATEGORY_NAME}' category grid should render exactly "
                f"{INITIAL_DISPLAY_COUNT} cards initially, got {initial_count}"
            )

        with allure.step("Step 2 — Assert the toggle reads 'Show more'"):
            assert catalog_page.get_show_more_button_text(CATEGORY_NAME) == "Show more"

        with allure.step("Step 3 — Click the toggle; displayCount increases, more cards render"):
            catalog_page.toggle_show_more(CATEGORY_NAME)

        with allure.step("Step 4 — Assert the grid now shows more than the initial count"):
            # Auto-retrying wait for the client-side re-slice to settle before
            # reading the exact count (no network wait needed — confirmed live,
            # AFS § Network Behavior — but the React re-render still takes a tick).
            expect(catalog_page.category_cards(CATEGORY_NAME)).not_to_have_count(
                initial_count, timeout=CARD_COUNT_CHANGE_TIMEOUT,
            )
            expanded_count = catalog_page.get_category_card_count(CATEGORY_NAME)
            assert expanded_count > initial_count, (
                f"Expected more than {initial_count} cards after Show more, got {expanded_count}"
            )

        with allure.step("Step 5 — Assert the toggle now reads 'Show less'"):
            assert catalog_page.get_show_more_button_text(CATEGORY_NAME) == "Show less"

        with allure.step("Step 6 — Click the toggle again (now 'Show less')"):
            catalog_page.toggle_show_more(CATEGORY_NAME)

        with allure.step(
            "Step 7 — Assert the grid collapses back to exactly the initial count, "
            "and the toggle label flips back to 'Show more'"
        ):
            expect(catalog_page.category_cards(CATEGORY_NAME)).to_have_count(
                initial_count, timeout=CARD_COUNT_CHANGE_TIMEOUT,
            )
            assert catalog_page.get_show_more_button_text(CATEGORY_NAME) == "Show more"

        with allure.step(
            "Side-channel check — no console errors across the navigate -> "
            "expand -> collapse flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the Show more/Show less flow: "
                f"{[m.text for m in console_errors]}"
            )
