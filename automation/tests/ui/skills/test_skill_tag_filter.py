"""Skills tag-filter UI test.

ELITEA-1740 — Search Skills by Tag: create 3 skills with shared and unique
tags, verify the page-header "Tags" filter panel narrows the grid correctly
for a shared tag (2 skills) and unique tags (1 skill each), and that
"Clear all" restores the unfiltered grid.

See test-specs/skills/l3_search-skills-by-tag_ELITEA-1740.md
"""

import logging
import uuid

import pytest
import allure

from pages.skills_list_page import SkillsListPage
from pages.skill_form_page import SkillFormPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")


@pytest.fixture
def cleanup_skill_ids(skill_api):
    """Track skill IDs created during the test and delete them at teardown.

    Mirrors the pattern in test_skill_export_import.py — IDs are appended
    as they're known (each skill only exists once created mid-test).
    Deletion tolerates "already gone" errors the same way.

    Yields:
        list: append skill IDs (int) here as they're created.
    """
    ids = []
    yield ids
    for skill_id in ids:
        try:
            skill_api.delete_skill(skill_id)
            logger.info("Cleanup: deleted skill id=%s", skill_id)
        except Exception as exc:
            logger.warning("Cleanup failed for skill id=%s (non-fatal): %s", skill_id, exc)


class TestSkillTagFilter:
    """Filter the Skills grid by tag — shared tags, unique tags, and clear (ELITEA-1740)."""

    @allure.issue("ELITEA-1740", "onetest-ai Test Case link")
    @pytest.mark.p3
    @pytest.mark.regression
    def test_filter_skills_by_tag(self, page, skill_api, cleanup_skill_ids):
        """Create 3 skills with shared/unique tags; verify tag-filter narrowing.

        Steps (see AFS for full detail):
        1. Capture baseline grid state; create Skill A (formatting, output),
           Skill B (formatting, english), Skill C (translation); verify all
           3 plus any pre-existing skills are visible with their own tags.
        2. Filter by `formatting` (shared tag) — verify exactly Skill A and
           Skill B are shown, Skill C is excluded.
        3. Clear the filter, then filter by `translation` (unique tag) —
           verify exactly Skill C is shown.
        4. Clear the filter, then filter by `output` (unique tag) — verify
           exactly Skill A is shown.
        5. Clear the filter — verify the grid is restored to the baseline
           plus the 3 new skills.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        skill_a_name = f"skill-a-{unique_suffix}"
        skill_b_name = f"skill-b-{unique_suffix}"
        skill_c_name = f"skill-c-{unique_suffix}"

        list_page = SkillsListPage(page)
        form_page = SkillFormPage(page)
        detail_page = SkillDetailPage(page)

        # Console-error capture across the whole test (tag creation +
        # filtering), mirroring test_skill_export_import.py's pattern.
        # Filters out the single known-and-not-filed cosmetic React
        # dev-mode warning ("Invalid value for prop `sx` on <svg>", fired
        # from TagEditor's SvgCheckedIcon when selecting an existing tag
        # from the autocomplete dropdown — AFS Known Defects #2) so a
        # real regression isn't masked by an expected, harmless warning.
        console_messages = []
        _console_listener = None  # Store reference for cleanup

        def _is_known_sx_svg_warning(msg) -> bool:
            text = msg.text
            return (
                "Invalid value for prop" in text
                and "sx" in text
                and "svg" in text.lower()
            )

        def _on_console(msg):
            if msg.type == "error" and not _is_known_sx_svg_warning(msg):
                console_messages.append(msg)

        _console_listener = _on_console
        page.on("console", _on_console)

        # ------------------------------------------------------------------
        # Step 1 — Capture baseline; create 3 skills with tags; verify visible
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Create Skill A/B/C with shared and unique tags"):
            list_page.navigate()
            baseline_names = list_page.get_visible_skill_names()

            # Skill A: both tags are new — commit each via type + Enter.
            list_page.navigate_to_create()
            form_page.wait_for_form_load()
            form_page.fill_form(
                name=skill_a_name,
                instructions=(
                    "You are Skill A, a test skill for ELITEA-1740 tag filter "
                    "verification."
                ),
                description="Test skill A for ELITEA-1740 tag filter verification.",
            )
            form_page.add_tag("formatting")
            form_page.add_tag("output")
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled once name, description, instructions, "
                "and tags are all valid"
            )
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.verify_on_detail_page()
            skill_a_id = int(detail_page.get_skill_id())
            cleanup_skill_ids.append(skill_a_id)
            logger.info("Skill A created — id=%s", skill_a_id)

            # Skill B: "formatting" now exists in the project — select it from
            # the autocomplete dropdown; "english" is new — type + Enter.
            list_page.navigate_to_create()
            form_page.wait_for_form_load()
            form_page.fill_form(
                name=skill_b_name,
                instructions=(
                    "You are Skill B, a test skill for ELITEA-1740 tag filter "
                    "verification."
                ),
                description="Test skill B for ELITEA-1740 tag filter verification.",
            )
            form_page.select_existing_tag("formatting")
            form_page.add_tag("english")
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled once name, description, instructions, "
                "and tags are all valid"
            )
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.verify_on_detail_page()
            skill_b_id = int(detail_page.get_skill_id())
            cleanup_skill_ids.append(skill_b_id)
            logger.info("Skill B created — id=%s", skill_b_id)

            # Skill C: "translation" is new — type + Enter.
            list_page.navigate_to_create()
            form_page.wait_for_form_load()
            form_page.fill_form(
                name=skill_c_name,
                instructions=(
                    "You are Skill C, a test skill for ELITEA-1740 tag filter "
                    "verification."
                ),
                description="Test skill C for ELITEA-1740 tag filter verification.",
            )
            form_page.add_tag("translation")
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled once name, description, instructions, "
                "and tags are all valid"
            )
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.verify_on_detail_page()
            skill_c_id = int(detail_page.get_skill_id())
            cleanup_skill_ids.append(skill_c_id)
            logger.info("Skill C created — id=%s", skill_c_id)

            list_page.navigate()
            # Wait for grid to load and settle after navigation
            list_page.wait_for_network(timeout=10000)
            list_page.page.wait_for_timeout(1000)  # Allow React to render
            visible_names = list_page.get_visible_skill_names()
            assert list_page.skill_exists_in_list(skill_a_name), (
                f"{skill_a_name!r} should be visible in the grid after creation"
            )
            assert list_page.skill_exists_in_list(skill_b_name), (
                f"{skill_b_name!r} should be visible in the grid after creation"
            )
            assert list_page.skill_exists_in_list(skill_c_name), (
                f"{skill_c_name!r} should be visible in the grid after creation"
            )
            assert len(visible_names) == len(baseline_names) + 3, (
                f"Expected {len(baseline_names) + 3} cards after creating 3 "
                f"skills (baseline {len(baseline_names)} + 3), got "
                f"{len(visible_names)}: {visible_names!r}"
            )

            # Each card renders its own tags (case's step 1 expected result:
            # "visible in the Skills list with their respective tags").
            skill_a_tags = {t.lower() for t in list_page.get_card_tags(skill_a_name)}
            skill_b_tags = {t.lower() for t in list_page.get_card_tags(skill_b_name)}
            skill_c_tags = {t.lower() for t in list_page.get_card_tags(skill_c_name)}
            assert skill_a_tags == {"formatting", "output"}, (
                f"Skill A's card should show tags {{'formatting', 'output'}}, "
                f"got: {skill_a_tags!r}"
            )
            assert skill_b_tags == {"formatting", "english"}, (
                f"Skill B's card should show tags {{'formatting', 'english'}}, "
                f"got: {skill_b_tags!r}"
            )
            assert skill_c_tags == {"translation"}, (
                f"Skill C's card should show tags {{'translation'}}, "
                f"got: {skill_c_tags!r}"
            )

        # ------------------------------------------------------------------
        # Step 2 — Filter by `formatting` (shared tag) — Skill A + B only
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Filter by 'formatting': Skill A and B only, C excluded"):
            list_page.filter_by_tag("formatting", timeout=UI_ELEMENT_TIMEOUT)
            filtered_names = {n.lower() for n in list_page.get_visible_skill_names()}
            assert filtered_names == {skill_a_name.lower(), skill_b_name.lower()}, (
                f"'formatting' filter should show exactly Skill A and Skill B, "
                f"got: {filtered_names!r}"
            )

        # ------------------------------------------------------------------
        # Step 3 — Clear, then filter by `translation` (unique tag) — Skill C only
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Clear filter, then filter by 'translation': Skill C only"):
            list_page.clear_tag_filter(timeout=UI_ELEMENT_TIMEOUT)
            list_page.filter_by_tag("translation", timeout=UI_ELEMENT_TIMEOUT)
            filtered_names = {n.lower() for n in list_page.get_visible_skill_names()}
            assert filtered_names == {skill_c_name.lower()}, (
                f"'translation' filter should show exactly Skill C, "
                f"got: {filtered_names!r}"
            )

        # ------------------------------------------------------------------
        # Step 4 — Clear, then filter by `output` (unique tag) — Skill A only
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Clear filter, then filter by 'output': Skill A only"):
            list_page.clear_tag_filter(timeout=UI_ELEMENT_TIMEOUT)
            list_page.filter_by_tag("output", timeout=UI_ELEMENT_TIMEOUT)
            filtered_names = {n.lower() for n in list_page.get_visible_skill_names()}
            assert filtered_names == {skill_a_name.lower()}, (
                f"'output' filter should show exactly Skill A, "
                f"got: {filtered_names!r}"
            )

        # ------------------------------------------------------------------
        # Step 5 — Clear all — grid restored to baseline + 3
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Clear all: grid restored to full unfiltered list"):
            list_page.clear_tag_filter(timeout=UI_ELEMENT_TIMEOUT)
            restored_names = list_page.get_visible_skill_names()
            assert len(restored_names) == len(baseline_names) + 3, (
                f"Expected grid restored to {len(baseline_names) + 3} cards "
                f"after 'Clear all', got {len(restored_names)}: {restored_names!r}"
            )
            assert list_page.skill_exists_in_list(skill_a_name), (
                f"{skill_a_name!r} should be visible again after clearing the filter"
            )
            assert list_page.skill_exists_in_list(skill_b_name), (
                f"{skill_b_name!r} should be visible again after clearing the filter"
            )
            assert list_page.skill_exists_in_list(skill_c_name), (
                f"{skill_c_name!r} should be visible again after clearing the filter"
            )

        # ------------------------------------------------------------------
        # Console errors — none expected across tag creation/filtering
        # ------------------------------------------------------------------
        with allure.step("Verify no console errors during tag creation/filtering"):
            assert not console_messages, (
                "Expected no console errors during tag creation/filtering, got: "
                f"{[m.text for m in console_messages]}"
            )

        # Clean up the console listener to prevent resource leaks
        if _console_listener is not None:
            try:
                page.remove_listener("console", _console_listener)
            except Exception:
                pass
