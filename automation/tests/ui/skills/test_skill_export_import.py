"""Skill export/import (base version) UI tests.

Covers the round trip: create a skill, export its base version as a
``.md`` file, import that file as a new skill, and verify the imported
skill's fields match the source exactly.

ELITEA-1737 — see test-specs/skills/l3_import_skill_base_version_ELITEA-1737.md
"""

import logging
import tempfile
import uuid
from pathlib import Path

import pytest
import allure
import yaml

from pages.skills_list_page import SkillsListPage
from pages.skill_form_page import SkillFormPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
IMPORT_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.skills")


@pytest.fixture
def cleanup_skill_ids(skill_api):
    """Track skill IDs created during the test and delete them at teardown.

    Export/import round-trips create two entities (source + imported skill)
    that don't exist until mid-test, so IDs are appended as they're known
    rather than resolved by name up front (unlike ``clean_skill`` in
    test_skill_management.py). Deletion tolerates "already gone" errors the
    same way ``clean_skill`` does.

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


class TestSkillExportImport:
    """Export a skill's base version and import it as a new skill (ELITEA-1737)."""

    @allure.issue("ELITEA-1737", "onetest-ai Test Case link")
    @pytest.mark.p2
    @pytest.mark.regression
    def test_export_and_import_skill_base_version(self, page, skill_api, cleanup_skill_ids):
        """Export a skill's base version, import the file, verify the round trip.

        Steps (see AFS for full detail):
        1. Navigate to create-skill form; Save starts disabled.
        2. Fill name/description/tags/instructions; Save enables.
        3. Save; note the source skill ID.
        4. Export the base version via the overflow menu; verify .md download.
        5. Read the exported file; verify frontmatter + instructions body.
        6. Navigate to Skills list; click Import; verify file chooser.
        7. Upload the exported file; verify the Import parameters dialog.
        8. Confirm import; verify navigation + success toast + new unique ID.
        9. Verify imported skill's version/name/description/tags/instructions.
        10. Edit + save the imported skill; verify a clean save.
        """
        # Kebab-case, <= 32 chars (MAX_NAME_LENGTH), lowercase letters/digits/hyphens only.
        unique_suffix = uuid.uuid4().hex[:8]
        skill_name = f"el-1737-skill-{unique_suffix}"
        skill_description = (
            "Automation test skill for base version export/import round trip (ELITEA-1737)."
        )
        skill_tag = "regression"
        skill_instructions = (
            "You are a test skill created for ELITEA-1737 export/import base version "
            "verification. Always respond with the single word CONFIRMED."
        )

        list_page = SkillsListPage(page)
        form_page = SkillFormPage(page)
        detail_page = SkillDetailPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Navigate to create-skill form; Save starts disabled
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Navigate to create-skill form; Save starts disabled"):
            list_page.navigate_to_create()
            form_page.wait_for_form_load()
            assert form_page.name_input.is_visible(), "Skill name input should be visible"
            assert not form_page.is_save_enabled(), (
                "Save should be disabled before the form is filled"
            )

        # ------------------------------------------------------------------
        # Step 2 — Fill name/description/tags/instructions; Save enables
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Fill name, description, tags, instructions"):
            form_page.fill_form(
                name=skill_name,
                instructions=skill_instructions,
                description=skill_description,
            )
            form_page.add_tag(skill_tag)
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled once name (kebab-case), description, "
                "and instructions are all valid"
            )

        # ------------------------------------------------------------------
        # Step 3 — Save; note the source skill ID
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Save; capture source skill ID"):
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.verify_on_detail_page()
            source_skill_id = detail_page.get_skill_id()
            cleanup_skill_ids.append(int(source_skill_id))
            logger.info("Source skill created — id=%s", source_skill_id)

        # ------------------------------------------------------------------
        # Step 4 — Export the base version via the overflow menu
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Export base version via overflow menu; verify .md download"):
            download = detail_page.export_base_version_via_menu(timeout=UI_ELEMENT_TIMEOUT)
            assert download.suggested_filename.endswith(".md"), (
                f"Expected a .md download, got: {download.suggested_filename}"
            )
            # Playwright stores downloads under a temp internal path whose
            # basename does not preserve the suggested filename/extension —
            # save_as() to a path that keeps the ".md" extension, since the
            # import flow validates the uploaded File object's name.
            download_path = Path(tempfile.gettempdir()) / download.suggested_filename
            download.save_as(download_path)
            assert download_path.exists() and download_path.stat().st_size > 0, (
                "Downloaded export file should exist and be non-empty"
            )

        # ------------------------------------------------------------------
        # Step 5 — Read the exported file; verify frontmatter + instructions body
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Verify exported file contents (frontmatter + instructions)"):
            raw_content = download_path.read_text(encoding="utf-8")
            # Frontmatter is delimited by leading/trailing '---' lines.
            parts = raw_content.split("---", 2)
            assert len(parts) == 3, (
                f"Expected YAML frontmatter delimited by '---', got structure: {raw_content[:200]!r}"
            )
            frontmatter = yaml.safe_load(parts[1])
            instructions_body = parts[2].strip()

            assert frontmatter.get("name") == skill_name, (
                f"Exported frontmatter name mismatch: {frontmatter.get('name')!r} != {skill_name!r}"
            )
            assert frontmatter.get("description") == skill_description, (
                "Exported frontmatter description should match the source skill"
            )
            assert frontmatter.get("tags") == [skill_tag], (
                f"Exported frontmatter tags mismatch: {frontmatter.get('tags')!r}"
            )
            # No explicit 'version' key is expected in the frontmatter — this is
            # expected live behavior (case-text drift clarification #21), not a bug.
            assert instructions_body == skill_instructions, (
                "Exported instructions body should match the source skill's instructions"
            )

        # ------------------------------------------------------------------
        # Step 6 — Navigate to Skills list; click Import; verify file chooser
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Navigate to Skills list; open Import file chooser"):
            list_page.navigate()

        # ------------------------------------------------------------------
        # Step 7 — Upload the exported file; verify Import parameters dialog
        # ------------------------------------------------------------------
        with allure.step("Step 7 — Upload exported file; verify Import parameters dialog"):
            list_page.import_skill(str(download_path), timeout=IMPORT_TIMEOUT)
            dialog = page.get_by_role("dialog")
            assert dialog.get_by_text("Type: Skill | Version: base").is_visible(), (
                "Import dialog should show Type: Skill | Version: base"
            )
            assert dialog.get_by_text(skill_name).first.is_visible(), (
                "Import dialog should preview the source skill's name"
            )

            # Description/Instructions preview fields render collapsed by
            # default ("Show details" toggle) — expand before reading them.
            list_page.expand_import_preview_details(timeout=IMPORT_TIMEOUT)
            assert dialog.get_by_text(skill_description, exact=False).is_visible(), (
                "Import dialog should preview the source skill's description"
            )
            assert dialog.get_by_text(skill_instructions, exact=False).is_visible(), (
                "Import dialog should preview the source skill's instructions"
            )

        # ------------------------------------------------------------------
        # Step 8 — Confirm import; verify navigation + success toast + new ID
        # ------------------------------------------------------------------
        with allure.step("Step 8 — Confirm import; verify success toast and new unique ID"):
            list_page.confirm_import(timeout=NAVIGATION_TIMEOUT)
            success_toast = page.get_by_text("Skill imported successfully.")
            assert success_toast.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Expected 'Skill imported successfully.' toast after import"
            )

            imported_skill_id = detail_page.get_skill_id()
            cleanup_skill_ids.append(int(imported_skill_id))
            assert imported_skill_id != source_skill_id, (
                f"Imported skill ID should differ from source: "
                f"imported={imported_skill_id!r}, source={source_skill_id!r}"
            )
            logger.info("Imported skill created — id=%s", imported_skill_id)

        # ------------------------------------------------------------------
        # Step 9 — Verify imported skill's fields match the source
        # ------------------------------------------------------------------
        with allure.step("Step 9 — Verify version/name/description/tags/instructions match source"):
            assert detail_page.get_name() == skill_name, (
                "Imported skill's name should match the source skill"
            )
            assert detail_page.get_description() == skill_description, (
                "Imported skill's description should match the source skill"
            )
            assert detail_page.get_tags() == [skill_tag], (
                f"Imported skill's tags mismatch: {detail_page.get_tags()!r}"
            )
            assert detail_page.get_instructions() == skill_instructions, (
                "Imported skill's instructions should match the source skill's exported content"
            )

        # ------------------------------------------------------------------
        # Step 10 — Edit + save the imported skill; verify a clean save
        # ------------------------------------------------------------------
        with allure.step("Step 10 — Edit description and save; verify clean save, no console errors"):
            edited_description = skill_description + " (edited)"

            console_messages = []
            page.on("console", lambda msg: console_messages.append(msg) if msg.type == "error" else None)

            form_page.set_description(edited_description)
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled after editing the description"
            )

            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

            assert not form_page.is_save_enabled(), (
                "Save should return to disabled after a clean save (dirty flag cleared)"
            )
            assert detail_page.get_description() == edited_description, (
                "Description should persist the edit after save"
            )
            assert not console_messages, (
                f"Expected no new console errors during final Save, got: {console_messages}"
            )
