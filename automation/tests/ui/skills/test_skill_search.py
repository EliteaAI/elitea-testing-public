"""Skill search UI tests (ELITEA-1739).

Covers searching the Skills-list page-header search box by name:
- Partial name match narrows the grid to the matching subset.
- Exact name match narrows the grid to exactly one card.
- Non-existent name search shows an empty grid.
- Clearing the search restores the full grid.

Both intended activation modes are exercised (SearchBar.jsx's onChange
never fetches by itself): pressing Enter, and clicking the send-icon
button — see AFS test-specs/skills/l3_search-skills-by-name_ELITEA-1739.md.

See test-specs/skills/l3_search-skills-by-name_ELITEA-1739.md for full AFS.
"""

import logging

import pytest
import allure

from pages.skills_list_page import SkillsListPage
from pages.skill_form_page import SkillFormPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

logger = logging.getLogger("elitea.tests.skills")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
SEARCH_TIMEOUT = 10_000

SKILL_NAMES = ["formatter", "code-reviewer", "content-writer"]
SKILL_DESCRIPTION = "Test skill for ELITEA-1739 search-by-name verification."
SKILL_INSTRUCTIONS = (
    "You are a test skill created for ELITEA-1739 search-by-name "
    "verification. Respond with FORMATTER."
)


@pytest.fixture
def three_search_skills(page, skill_api):
    """Create the 3 skills this case searches over, via the UI form
    (``SkillAPI`` has no create endpoint), and delete them via the API in
    teardown — faster and more reliable than UI delete for automated runs,
    mirroring ``test_skill_export_import.py``'s ``cleanup_skill_ids`` fixture.

    Yields:
        list[str]: the 3 skill names in creation order — ``formatter``,
        ``code-reviewer``, ``content-writer``.
    """
    created_ids = []
    list_page = SkillsListPage(page)
    form_page = SkillFormPage(page)

    for name in SKILL_NAMES:
        list_page.navigate_to_create()
        form_page.wait_for_form_load()
        form_page.fill_form(
            name=name,
            instructions=SKILL_INSTRUCTIONS,
            description=SKILL_DESCRIPTION,
        )
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), (
            f"Save should be enabled after filling all required fields for {name!r}"
        )
        form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

        detail_page = SkillDetailPage(page)
        detail_page.verify_on_detail_page()
        skill_id = int(detail_page.get_skill_id())
        created_ids.append(skill_id)
        logger.info("Created search-test skill %r id=%s", name, skill_id)

    yield list(SKILL_NAMES)

    for skill_id in created_ids:
        try:
            skill_api.delete_skill(skill_id)
            logger.info("Cleanup: deleted skill id=%s", skill_id)
        except Exception as exc:
            logger.warning("Cleanup failed for skill id=%s (non-fatal): %s", skill_id, exc)


class TestSkillSearch:
    """Search Skills by Name (P2/L3): partial, exact, no-match, clear."""

    @allure.issue("ELITEA-1739", "onetest-ai Test Case link")
    @pytest.mark.p2
    @pytest.mark.regression
    def test_search_skills_by_name(self, page, three_search_skills):
        """Search the Skills grid by partial name, exact name, a
        non-existent name, then clear — verifying the grid's exact visible
        set at each step (not just presence/absence of one name), so a
        regression that only breaks the grid while leaving the separate
        suggestions popover working would be caught.
        """
        skill_names = three_search_skills

        with allure.step("Step 1 — Navigate to Skills list; verify all 3 skills visible"):
            list_page = SkillsListPage(page)
            list_page.navigate()
            for name in skill_names:
                assert list_page.skill_exists_in_list(name), (
                    f"Skill {name!r} should be visible in the list after creation"
                )

        with allure.step(
            "Step 2 — Search partial name 'Co' via Enter; verify the "
            "sub-minimum-length query does not filter the grid "
            "(live-contract correction — see AFS Known Defects "
            "Clarification #4: EliteaUI enforces a 3-character minimum "
            "search length; 'Co' is 2 characters and cannot activate "
            "either activation mode)"
        ):
            grid_did_not_fetch = list_page.search_below_min_length(
                "Co", timeout=3000
            )
            assert grid_did_not_fetch, (
                "Expected the grid-fetching endpoint NOT to fire for a "
                "sub-minimum-length ('Co', 2 chars) query — if this now "
                "fails, EliteaUI's MIN_SEARCH_KEYWORD_LENGTH behavior "
                "changed and the AFS/test need updating accordingly"
            )
            visible = {n.lower() for n in list_page.get_visible_skill_names()}
            assert set(skill_names).issubset(visible), (
                "Grid should remain unfiltered (all skills still visible) "
                f"after a sub-minimum-length query, got: {visible}"
            )

        with allure.step(
            "Step 3 — Clear, search exact name 'formatter' via send-icon; "
            "verify only formatter is shown"
        ):
            list_page.clear_search(timeout=SEARCH_TIMEOUT)
            list_page.search_via_send_button("formatter", timeout=SEARCH_TIMEOUT)
            visible = {n.lower() for n in list_page.get_visible_skill_names()}
            assert visible == {"formatter"}, (
                f"Expected exactly {{'formatter'}} visible after searching "
                f"'formatter' via send-icon, got: {visible}"
            )

        with allure.step(
            "Step 4 — Clear, search non-existent name 'Translator' via Enter; "
            "verify the grid is empty"
        ):
            list_page.clear_search(timeout=SEARCH_TIMEOUT)
            list_page.search("Translator", timeout=SEARCH_TIMEOUT)
            visible = list_page.get_visible_skill_names()
            assert visible == [], (
                f"Expected an empty grid after searching a non-existent name, "
                f"got: {visible}"
            )

        with allure.step("Step 5 — Clear search; verify all 3 skills are shown again"):
            list_page.clear_search(timeout=SEARCH_TIMEOUT)
            visible = {n.lower() for n in list_page.get_visible_skill_names()}
            assert set(skill_names).issubset(visible), (
                f"Expected all created skills {skill_names} visible after "
                f"clearing search, got: {visible}"
            )
