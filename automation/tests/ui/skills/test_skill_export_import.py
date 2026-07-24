"""Skill export/import UI tests.

Covers three import-related scenarios:
- ELITEA-1737: create a skill, export its base version as a ``.md`` file,
  import that file as a new skill, verify the imported skill's fields
  match the source exactly.
- ELITEA-1738: create a skill, save a new named version (``ver_1``),
  export *that* version, import it, and verify the imported skill lands
  on a `base` version (not `ver_1`) whose fields match the exported
  version's content.
- GAP-061: importing a non-``.md`` file is rejected with a toast and never
  opens the preview; importing a valid ``.md`` fixture into a **different**
  target project completes without navigating away from the current
  Skills list.

ELITEA-1737 — see test-specs/skills/l3_import_skill_base_version_ELITEA-1737.md
ELITEA-1738 — see test-specs/skills/l3_import-skill-non-base-version_ELITEA-1738.md
GAP-061 — see test-specs/skills/l4_reject-non-md-file-and-cross-project-import-skips-navigation_GAP-061.md
"""

import logging
import tempfile
import uuid
from pathlib import Path

import pytest
import allure
import yaml

from api import SkillAPI
from pages.skills_list_page import SkillsListPage
from pages.skill_form_page import SkillFormPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
IMPORT_TIMEOUT = 15_000

# GAP-061 — import target project (confirmed live, see AFS Test Data):
# `UI Testing`, safe for both import destination and its own cleanup.
GAP061_TARGET_PROJECT_ID = "400"

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


@pytest.fixture
def cleanup_project_b_skill(_browser_cookies):
    """Track a skill created in GAP-061's target project (400, "UI Testing")
    and delete it via a project-scoped ``SkillAPI`` at teardown.

    GAP-061's cross-project import creates a skill in project 400, not the
    default project (399/"Private") the session-scoped ``skill_api`` fixture
    is pinned to — deleting via that fixture would silently 404 (or worse,
    target the wrong skill) since it always addresses project 399. This
    constructs its own project-400-scoped ``SkillAPI``, mirroring
    :func:`cleanup_skill_ids` above but for the cross-project case.

    The test itself performs the delete as its own case step (GAP-061 step
    7); ``holder["id"]`` is reset to ``None`` once that delete succeeds, so
    this fixture's teardown is a no-op on the happy path and only acts as a
    safety net if an assertion fails before the in-test delete runs.

    Yields:
        dict: ``{"api": SkillAPI, "id": int | None}`` — set ``holder["id"]``
        to the skill id to clean up; the test clears it back to ``None``
        after its own successful delete.
    """
    holder = {"api": SkillAPI(browser_cookies=_browser_cookies, project_id=GAP061_TARGET_PROJECT_ID), "id": None}
    yield holder
    if holder["id"] is not None:
        try:
            holder["api"].delete_skill(holder["id"])
            logger.info("Cleanup: deleted project-%s skill id=%s", GAP061_TARGET_PROJECT_ID, holder["id"])
        except Exception as exc:
            logger.warning(
                "Cleanup failed for project-%s skill id=%s (non-fatal): %s",
                GAP061_TARGET_PROJECT_ID, holder["id"], exc,
            )
    holder["api"].close()


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


class TestSkillImportRejectionAndCrossProjectImport:
    """Reject a non-.md import and import a valid .md into a different project (GAP-061).

    Distinct from the round-trip tests above: no source skill is created —
    a static fixture file is imported directly — and this exercises the
    dialog's PROJECT selector plus the "no navigation on cross-project
    import" branch, the inverse of what ELITEA-1737/1738 assert.
    """

    @allure.issue("GAP-061", "onetest-ai Test Case link")
    @pytest.mark.p3
    @pytest.mark.regression
    def test_reject_non_md_file_and_cross_project_import_skips_navigation(
        self, page, tmp_path, cleanup_project_b_skill
    ):
        """Reject a non-.md import, then import a valid .md into a different project.

        Steps (see AFS for full detail):
        1. With Project A (Private/399) selected, attempt to import a
           non-.md file; verify the exact rejection toast and that the
           preview dialog never opens.
        2. Import a valid .md fixture; verify the preview dialog opens.
        3. Verify the preview's name and hardcoded Type/Version subtitle.
        4. Change the dialog's PROJECT selector to Project B (UI Testing/400).
        5. Confirm the import; verify the dialog closes and a success toast
           appears.
        6. Verify the app stays on Project A's Skills list (no navigation
           into the imported skill).
        7. Switch to Project B, confirm the imported skill is present, then
           delete it.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        skill_name = f"gap061-skill-{unique_suffix}"
        skill_description = (
            "Automation fixture skill for GAP-061 cross-project import verification."
        )
        skill_instructions = (
            "You are a test skill created for GAP-061 cross-project import "
            "verification. Always respond with the single word CONFIRMED."
        )

        invalid_file = tmp_path / "notes.txt"
        invalid_file.write_text("This is not a skill file.\n", encoding="utf-8")

        valid_file = tmp_path / "gap061-skill.md"
        valid_file.write_text(
            "---\n"
            f"name: {skill_name}\n"
            f"description: {skill_description}\n"
            "tags:\n"
            "  - regression\n"
            "---\n"
            f"{skill_instructions}\n",
            encoding="utf-8",
        )

        list_page = SkillsListPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Reject a non-.md file: exact toast, no preview dialog
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Attempt to import a non-.md file; verify rejection"):
            list_page.navigate()
            list_page.attempt_import_invalid_file(str(invalid_file), timeout=UI_ELEMENT_TIMEOUT)
            error_toast = list_page.import_error_toast_message
            assert error_toast.text_content() == "Only .md files can be imported.", (
                f"Expected the exact wrong-extension toast, got: {error_toast.text_content()!r}"
            )
            assert not list_page.import_preview_dialog.is_visible(), (
                "Import preview dialog should never open for a rejected non-.md file"
            )

        # ------------------------------------------------------------------
        # Step 2 — Import a valid .md fixture; verify the preview dialog opens
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Import a valid .md fixture; verify preview dialog opens"):
            list_page.import_skill(str(valid_file), timeout=IMPORT_TIMEOUT)
            assert list_page.import_preview_dialog.is_visible(), (
                "Import preview dialog should open for a valid .md fixture"
            )

        # ------------------------------------------------------------------
        # Step 3 — Verify preview name and hardcoded Type/Version subtitle
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Verify preview name and Type/Version subtitle"):
            preview_name_text = list_page.import_preview_name.text_content()
            preview_type_version_text = list_page.import_preview_type_version.text_content()
            assert preview_name_text == skill_name, (
                f"Import dialog should preview the fixture's name: expected "
                f"{skill_name!r}, got {preview_name_text!r}"
            )
            assert preview_type_version_text == "Type: Skill | Version: base", (
                "Import dialog should show the hardcoded 'Type: Skill | Version: base' "
                f"subtitle (imported skills are always created as base, regardless of "
                f"the fixture's own content), got: {preview_type_version_text!r}"
            )

        # ------------------------------------------------------------------
        # Step 4 — Change the PROJECT selector to Project B (UI Testing/400)
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Change the dialog's PROJECT selector to Project B"):
            list_page.select_import_target_project(GAP061_TARGET_PROJECT_ID, timeout=UI_ELEMENT_TIMEOUT)
            selected_project_text = list_page.import_project_select.text_content() or ""
            assert "UI Testing" in selected_project_text, (
                f"Import dialog's PROJECT selector should show 'UI Testing' after "
                f"selection, got: {selected_project_text!r}"
            )

        # ------------------------------------------------------------------
        # Step 5 — Confirm the import; verify dialog closes + success toast
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Confirm import; verify dialog closes and success toast appears"):
            list_page.confirm_cross_project_import(timeout=NAVIGATION_TIMEOUT)
            assert not list_page.import_preview_dialog.is_visible(), (
                "Import preview dialog should be closed after confirming a cross-project import"
            )
            success_toast_text = list_page.import_success_toast_message.text_content()
            assert success_toast_text == "Skill imported successfully.", (
                f"Expected 'Skill imported successfully.' toast after cross-project "
                f"import, got: {success_toast_text!r}"
            )

        # ------------------------------------------------------------------
        # Step 6 — Verify the app stayed on Project A's Skills list (no navigation)
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Verify no navigation into the imported skill"):
            current_url = list_page.page.url
            current_title = list_page.page.title()
            assert current_url.rstrip("/").endswith("/skills/all"), (
                f"App should stay on the Skills list after a cross-project import "
                f"(no navigation into the imported skill), got URL: {current_url!r}"
            )
            assert current_title == "Skills: all - Private", (
                f"Page title should remain on Project A's Skills list, got: {current_title!r}"
            )
            assert not list_page.skill_exists_in_list(skill_name), (
                "The imported skill was created in Project B and should NOT appear "
                "in Project A's current Skills list"
            )

        # ------------------------------------------------------------------
        # Step 7 — Switch to Project B, confirm presence, then delete
        # ------------------------------------------------------------------
        with allure.step("Step 7 — Confirm the imported skill is present in Project B, then delete it"):
            project_b_skill_api = cleanup_project_b_skill["api"]
            rows = project_b_skill_api.list_skills(limit=500).get("rows", [])
            imported_skill = next((s for s in rows if s.get("name") == skill_name), None)
            assert imported_skill is not None, (
                f"Imported skill {skill_name!r} should be present in Project B "
                f"(id={GAP061_TARGET_PROJECT_ID}, 'UI Testing') after the cross-project import"
            )
            imported_skill_id = imported_skill["id"]
            # Register with the cleanup fixture BEFORE deleting, so a failure in
            # the delete call itself (or the assertions below) still leaves a
            # safety-net teardown delete in place.
            cleanup_project_b_skill["id"] = imported_skill_id

            project_b_skill_api.delete_skill(imported_skill_id)

            remaining = project_b_skill_api.list_skills(limit=500).get("rows", [])
            assert not any(s.get("id") == imported_skill_id for s in remaining), (
                f"Skill id={imported_skill_id} should be gone from Project B after deletion"
            )
            cleanup_project_b_skill["id"] = None  # already deleted — teardown becomes a no-op
