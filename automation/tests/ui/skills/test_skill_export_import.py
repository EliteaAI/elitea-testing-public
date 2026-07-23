"""Skill export/import UI tests.

Covers two export/import round trips:
- ELITEA-1737: create a skill, export its base version as a ``.md`` file,
  import that file as a new skill, verify the imported skill's fields
  match the source exactly.
- ELITEA-1738: create a skill, save a new named version (``ver_1``),
  export *that* version, import it, and verify the imported skill lands
  on a `base` version (not `ver_1`) whose fields match the exported
  version's content.

ELITEA-1737 — see test-specs/skills/l3_import_skill_base_version_ELITEA-1737.md
ELITEA-1738 — see test-specs/skills/l3_import-skill-non-base-version_ELITEA-1738.md
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
            # Preview fields are addressed by their own testids (set on the
            # dialog's underlying content nodes in EliteaUI, ELITEA-1737
            # rework, exposed as SkillsListPage LocatorDescriptor fields) and
            # asserted by text content, rather than located BY the expected
            # text — the name/description/instructions values are
            # test-generated data, not static copy.
            preview_name = list_page.import_preview_name
            preview_type_version = list_page.import_preview_type_version
            assert preview_type_version.text_content() == "Type: Skill | Version: base", (
                f"Import dialog should show 'Type: Skill | Version: base', "
                f"got: {preview_type_version.text_content()!r}"
            )
            assert preview_name.text_content() == skill_name, (
                f"Import dialog should preview the source skill's name: "
                f"expected {skill_name!r}, got {preview_name.text_content()!r}"
            )

            # Description/Instructions preview fields render collapsed by
            # default ("Show details" toggle) — expand before reading them.
            list_page.expand_import_preview_details(timeout=IMPORT_TIMEOUT)
            preview_description = list_page.import_preview_description
            preview_instructions = list_page.import_preview_instructions
            assert preview_description.text_content() == skill_description, (
                f"Import dialog should preview the source skill's description: "
                f"expected {skill_description!r}, got {preview_description.text_content()!r}"
            )
            assert preview_instructions.text_content() == skill_instructions, (
                f"Import dialog should preview the source skill's instructions: "
                f"expected {skill_instructions!r}, got {preview_instructions.text_content()!r}"
            )

        # ------------------------------------------------------------------
        # Step 8 — Confirm import; verify navigation + success toast + new ID
        # ------------------------------------------------------------------
        with allure.step("Step 8 — Confirm import; verify success toast and new unique ID"):
            list_page.confirm_import(timeout=NAVIGATION_TIMEOUT)
            # ``toast-message`` is a generic testid on the app-wide Toast
            # component's message container (EliteaUI ELITEA-1737 rework,
            # exposed as SkillsListPage.import_success_toast_message) —
            # asserted by text content rather than located BY the text.
            success_toast = list_page.import_success_toast_message
            success_toast.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert success_toast.text_content() == "Skill imported successfully.", (
                f"Expected 'Skill imported successfully.' toast after import, "
                f"got: {success_toast.text_content()!r}"
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

            console_messages = detail_page.capture_console_errors()
            try:
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
            finally:
                console_messages.stop()


class TestSkillExportImportNonBaseVersion:
    """Export a skill's non-base version and import it (ELITEA-1738).

    Verifies that importing a `.md` file exported from a non-base version
    (`ver_1`) creates a new skill whose version is `base` (not `ver_1`),
    with all fields populated from the exported version's content — not
    the source skill's original base-version content.
    """

    @allure.issue("ELITEA-1738", "onetest-ai Test Case link")
    @pytest.mark.p3
    @pytest.mark.regression
    def test_import_skill_non_base_version(self, page, skill_api, cleanup_skill_ids):
        """Export a skill's ver_1 version, import the file, verify the round trip.

        Steps (see AFS for full detail):
        1. Create a Skill with base version; note the source skill ID.
        2. Edit instructions, click "Save As Version" → create `ver_1`.
        3. With `ver_1` selected, export via the overflow menu; verify
           the downloaded filename embeds the version name.
        4. Read the exported file; verify frontmatter (incl. `elitea_version`)
           and instructions body.
        5. Navigate to Skills list; import the exported file; verify the
           Import parameters dialog previews the ver_1 content.
        6. Confirm import; verify navigation + unique new skill ID.
        7. Verify imported skill's version is `base` and fields match the
           exported ver_1 content.
        8. Edit + save the imported skill; verify a clean save.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        skill_name = f"el-1738-skill-{unique_suffix}"
        skill_description = (
            "Automation test skill for non-base version export/import "
            "verification (ELITEA-1738)."
        )
        skill_tag = "regression"
        base_instructions = (
            "You are a test skill created for ELITEA-1738 base-version "
            "export/import verification. Always respond with the single "
            "word BASE."
        )
        version_name = "ver_1"
        ver1_instructions = (
            base_instructions
            + " This is version ver_1 with modified instructions - respond with VER1 instead."
        )

        list_page = SkillsListPage(page)
        form_page = SkillFormPage(page)
        detail_page = SkillDetailPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Create a Skill with base version; note the source skill ID
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Create a Skill with base version"):
            list_page.navigate_to_create()
            form_page.wait_for_form_load()
            form_page.fill_form(
                name=skill_name,
                instructions=base_instructions,
                description=skill_description,
            )
            form_page.add_tag(skill_tag)
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled once name (kebab-case), description, "
                "and instructions are all valid"
            )

            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.verify_on_detail_page()
            source_skill_id = detail_page.get_skill_id()
            cleanup_skill_ids.append(int(source_skill_id))
            assert detail_page.get_version_id() == source_skill_id, (
                "Version ID should equal Skill ID on first save (base version)"
            )
            logger.info("Source skill created — id=%s", source_skill_id)

        # ------------------------------------------------------------------
        # Step 2 — Edit instructions; "Save As Version" → create ver_1
        # ------------------------------------------------------------------
        with allure.step('Step 2 — Edit instructions; "Save As Version" creates ver_1'):
            form_page.fill_instructions(ver1_instructions)
            form_page.wait_for_form_validation()

            detail_page.save_as_version(version_name, timeout=UI_ELEMENT_TIMEOUT)

            new_version_id = detail_page.get_version_id()
            assert new_version_id != source_skill_id, (
                "Version ID should change after creating a new named version"
            )
            assert detail_page.get_skill_id() == source_skill_id, (
                "Skill ID should stay the same after creating a new version"
            )
            assert detail_page.get_version_selector_value() == version_name, (
                f"VERSION selector should show {version_name!r} after Save As Version"
            )

        # ------------------------------------------------------------------
        # Step 3 — Export the ver_1 version via the overflow menu
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Export ver_1 via overflow menu; verify .md download"):
            download = detail_page.export_version_via_menu(timeout=UI_ELEMENT_TIMEOUT)
            assert download.suggested_filename.endswith(".md"), (
                f"Expected a .md download, got: {download.suggested_filename}"
            )
            assert skill_name in download.suggested_filename, (
                f"Downloaded filename should embed the skill name: {download.suggested_filename!r}"
            )
            assert version_name in download.suggested_filename, (
                "Downloaded filename should embed the exported version name "
                f"({version_name!r}), got: {download.suggested_filename!r}"
            )
            download_path = Path(tempfile.gettempdir()) / download.suggested_filename
            download.save_as(download_path)
            assert download_path.exists() and download_path.stat().st_size > 0, (
                "Downloaded export file should exist and be non-empty"
            )

        # ------------------------------------------------------------------
        # Step 4 — Verify exported file contents (frontmatter + instructions)
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Verify exported file contents (frontmatter + instructions)"):
            raw_content = download_path.read_text(encoding="utf-8")
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
            # Non-base version exports carry an explicit elitea_version key
            # (Axis 2 addition — unlike base exports, which have no such key).
            assert frontmatter.get("elitea_version") == version_name, (
                f"Exported frontmatter elitea_version mismatch: {frontmatter.get('elitea_version')!r}"
            )
            assert instructions_body == ver1_instructions, (
                "Exported instructions body should match the ver_1 instructions, not base"
            )

        # ------------------------------------------------------------------
        # Step 5 — Import the exported file; verify Import parameters dialog
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Navigate to Skills list; import file; verify preview dialog"):
            list_page.navigate()
            list_page.import_skill(str(download_path), timeout=IMPORT_TIMEOUT)
            # Preview fields are addressed by their own testids (set on the
            # dialog's underlying content nodes in EliteaUI, ELITEA-1737
            # rework, exposed as SkillsListPage LocatorDescriptor fields) and
            # asserted by text content, rather than located BY the expected
            # text.
            preview_type_version = list_page.import_preview_type_version
            preview_name = list_page.import_preview_name
            # The dialog's "Version: base" label is hardcoded
            # (SkillImportModal.jsx), not derived from the file's
            # elitea_version field — it always reads "base" regardless of
            # which version was exported.
            assert preview_type_version.text_content() == "Type: Skill | Version: base", (
                f"Import dialog should show 'Type: Skill | Version: base' "
                f"(hardcoded label, regardless of exported version), "
                f"got: {preview_type_version.text_content()!r}"
            )
            assert preview_name.text_content() == skill_name, (
                f"Import dialog should preview the source skill's name: "
                f"expected {skill_name!r}, got {preview_name.text_content()!r}"
            )

            list_page.expand_import_preview_details(timeout=IMPORT_TIMEOUT)
            preview_description = list_page.import_preview_description
            preview_instructions = list_page.import_preview_instructions
            assert preview_description.text_content() == skill_description, (
                f"Import dialog should preview the ver_1 description: "
                f"expected {skill_description!r}, got {preview_description.text_content()!r}"
            )
            assert preview_instructions.text_content() == ver1_instructions, (
                "Import dialog preview should show the ver_1 instructions "
                "(not the source skill's original base instructions), proving "
                f"the exported ver_1 content is what's staged for import — "
                f"got: {preview_instructions.text_content()!r}"
            )

        # ------------------------------------------------------------------
        # Step 6 — Confirm import; verify navigation + unique new skill ID
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Confirm import; verify success toast and new unique ID"):
            list_page.confirm_import(timeout=NAVIGATION_TIMEOUT)
            # ``toast-message`` is a generic testid on the app-wide Toast
            # component's message container (EliteaUI ELITEA-1737 rework,
            # exposed as SkillsListPage.import_success_toast_message) —
            # asserted by text content rather than located BY the text.
            success_toast = list_page.import_success_toast_message
            success_toast.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert success_toast.text_content() == "Skill imported successfully.", (
                f"Expected 'Skill imported successfully.' toast after import, "
                f"got: {success_toast.text_content()!r}"
            )

            imported_skill_id = detail_page.get_skill_id()
            cleanup_skill_ids.append(int(imported_skill_id))
            assert imported_skill_id != source_skill_id, (
                f"Imported skill ID should differ from source: "
                f"imported={imported_skill_id!r}, source={source_skill_id!r}"
            )
            logger.info("Imported skill created — id=%s", imported_skill_id)

        # ------------------------------------------------------------------
        # Step 7 — Verify imported skill lands on `base` version with ver_1 content
        # ------------------------------------------------------------------
        with allure.step("Step 7 — Verify imported skill version=base, fields match ver_1 content"):
            assert detail_page.get_version_selector_value() == "base", (
                "Imported skill should show a 'base' version, regardless of "
                "which version was exported"
            )
            assert detail_page.get_name() == skill_name, (
                "Imported skill's name should match the exported ver_1 content"
            )
            assert detail_page.get_description() == skill_description, (
                "Imported skill's description should match the exported ver_1 content"
            )
            assert detail_page.get_tags() == [skill_tag], (
                f"Imported skill's tags mismatch: {detail_page.get_tags()!r}"
            )
            assert detail_page.get_instructions() == ver1_instructions, (
                "Imported skill's instructions should match the exported ver_1 "
                "content, not the source skill's original base instructions"
            )
            assert detail_page.get_skill_id() != source_skill_id, (
                "Imported skill's ID should be unique vs. the source skill ID"
            )

        # ------------------------------------------------------------------
        # Step 8 — Edit + save the imported skill; verify a clean save
        # ------------------------------------------------------------------
        with allure.step("Step 8 — Edit description and save; verify clean save, no console errors"):
            edited_description = skill_description + " (edited)"

            console_messages = detail_page.capture_console_errors()
            try:
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
            finally:
                console_messages.stop()
