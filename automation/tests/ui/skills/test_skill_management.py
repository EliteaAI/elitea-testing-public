"""Skills management UI tests.

Tests the full lifecycle of a skill:
- Create via UI form
- Execute via SkillTestPanel
- Verify response
- Delete via overflow menu
"""

import logging
import re

import pytest
import allure

from pages.skills_list_page import SkillsListPage
from pages.skill_form_page import SkillFormPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000

logger = logging.getLogger("elitea.tests.skills")

SKILL_NAME = "autotest-skill-caps"
MANDATORY_FIELDS_SKILL_NAME = "autotest-skill-mandatory-fields"
EDIT_SKILL_ORIGINAL_NAME = "autotest-skill-edit-original"
EDIT_SKILL_NEW_NAME = "autotest-skill-edit-updated"


@pytest.fixture
def clean_skill(skill_api):
    """Ensure no leftover skill named SKILL_NAME exists before the test,
    and clean up after regardless of outcome.

    Yields the skill name so the test can reference it without repeating
    the constant.
    """
    def _delete_if_exists():
        try:
            for skill in skill_api.list_skills().get("rows", []):
                if skill.get("name") == SKILL_NAME:
                    skill_api.delete_skill(skill["id"])
                    logger.info("Pre/post-cleanup: deleted skill id=%s", skill["id"])
                    break
        except Exception as exc:
            logger.warning("Skill cleanup failed (non-fatal): %s", exc)

    _delete_if_exists()
    yield SKILL_NAME
    _delete_if_exists()


class TestCreateSkill:
    """Create Skill (P0): create via UI, execute via test panel, verify output, delete."""

    @allure.issue("", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_skill_and_verify_execution(self, page, skill_api, clean_skill):
        """Create a skill with caps-only instruction, run it in the test panel,
        verify the response is all uppercase, then delete the skill.
        """
        skill_name = clean_skill
        skill_instructions = "type text with caps only"
        skill_description = "Automation test skill - capitalize all output"
        test_message = "hello world"

        # ------------------------------------------------------------------
        # Step 1 — Navigate to create skill page
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Navigate to create skill page"):
            list_page = SkillsListPage(page)
            list_page.navigate_to_create()

        # ------------------------------------------------------------------
        # Step 2 — Fill form: name, description, instructions
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Fill form: name, description, instructions"):
            form_page = SkillFormPage(page)
            form_page.wait_for_form_load()
            form_page.fill_form(
                name=skill_name,
                instructions=skill_instructions,
                description=skill_description,
            )

        # ------------------------------------------------------------------
        # Step 3 — Save; verify navigation to detail page
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Save; verify navigation to detail page"):
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save should be enabled after filling all required fields"
            )
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

            detail_page = SkillDetailPage(page)
            detail_page.verify_on_detail_page()

        # ------------------------------------------------------------------
        # Step 4 — Send "hello world" in SkillTestPanel
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Send 'hello world' in SkillTestPanel"):
            initial_count = detail_page.get_test_message_count()
            detail_page.send_test_message(test_message)
            detail_page.wait_for_test_response(
                initial_count=initial_count,
                timeout=AI_RESPONSE_TIMEOUT,
            )

        # ------------------------------------------------------------------
        # Step 5 — Assert the response contains only uppercase alphabetic characters
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Assert response contains only uppercase alphabetic characters"):
            response_text = detail_page.get_last_test_response()
            alpha_chars = [c for c in response_text if c.isalpha()]
            assert alpha_chars, (
                f"Response contains no alphabetic characters: '{response_text}'"
            )
            assert all(c.isupper() for c in alpha_chars), (
                f"Expected all-uppercase response, got: '{response_text}'"
            )

        # ------------------------------------------------------------------
        # Step 6 — Delete skill via overflow menu
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Delete skill via overflow menu"):
            detail_page.delete_skill_via_menu(
                skill_name=skill_name,
                timeout=UI_ELEMENT_TIMEOUT,
            )

        # ------------------------------------------------------------------
        # Step 7 — Verify skill is gone from the list
        # ------------------------------------------------------------------
        with allure.step("Step 7 — Verify skill is gone from the list"):
            list_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            list_page.wait_for_skill_absent(skill_name, timeout=NAVIGATION_TIMEOUT)
            assert not list_page.skill_exists_in_list(skill_name), (
                f"Skill '{skill_name}' should be gone from list after deletion"
            )


class TestSkillMandatoryFieldsValidation:
    """Skill creation (P3, ELITEA-2430): Save stays disabled while Name and/or
    Description are empty, and becomes enabled only once both are filled —
    then Save succeeds and the skill appears in the Skills list.
    """

    @allure.issue("ELITEA-2430", "onetest-ai Test Case link")
    @pytest.mark.p3
    @pytest.mark.skills
    def test_save_disabled_until_name_and_description_filled(self, page, skill_api):
        """Walk every Name/Description empty/filled combination the case
        exercises, asserting the Save button's enabled state at each point,
        then save and verify the skill was created and is listed.
        """
        skill_name = MANDATORY_FIELDS_SKILL_NAME
        skill_description = "Test skill description for mandatory field validation"
        skill_instructions = "Always respond with OK"
        skill_id = None

        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate to Create Skill page
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to Create Skill page"):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()
                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()

            # ------------------------------------------------------------------
            # Step 2/3 — Leave Name empty, fill Description + Instructions;
            # verify Save stays disabled
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Leave Name empty, fill Description and Instructions"):
                form_page.set_description(skill_description)
                form_page.fill_instructions(skill_instructions)
                assert form_page.get_description() == skill_description
                assert form_page.get_instructions() == skill_instructions

            with allure.step("Step 3 — Verify Save button is disabled (Name empty)"):
                form_page.wait_for_form_validation()
                assert not form_page.is_save_enabled(), (
                    "Save should stay disabled while Name is empty"
                )

            # ------------------------------------------------------------------
            # Step 4/5 — Fill Name, clear Description, keep Instructions;
            # verify Save stays disabled
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Fill Name, clear Description, keep Instructions filled"):
                form_page.set_name(skill_name)
                form_page.set_description("")
                assert form_page.get_name() == skill_name
                assert form_page.get_description() == ""

            with allure.step("Step 5 — Verify Save button is disabled (Description empty)"):
                form_page.wait_for_form_validation()
                assert not form_page.is_save_enabled(), (
                    "Save should stay disabled while Description is empty"
                )

            # ------------------------------------------------------------------
            # Step 6/7 — Leave both Name and Description empty; verify Save
            # stays disabled
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Leave both Name and Description empty"):
                form_page.set_name("")
                assert form_page.get_name() == ""
                assert form_page.get_description() == ""

            with allure.step("Step 7 — Verify Save button is disabled (both empty)"):
                form_page.wait_for_form_validation()
                assert not form_page.is_save_enabled(), (
                    "Save should stay disabled while both Name and Description are empty"
                )

            # ------------------------------------------------------------------
            # Step 8/9 — Fill both Name and Description, keep Instructions;
            # verify Save becomes enabled
            # ------------------------------------------------------------------
            with allure.step("Step 8 — Fill both Name and Description, keep Instructions filled"):
                form_page.set_name(skill_name)
                form_page.set_description(skill_description)
                assert form_page.get_name() == skill_name
                assert form_page.get_description() == skill_description

            with allure.step("Step 9 — Verify Save button becomes enabled"):
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled once Name and Description are both filled"
                )

            # ------------------------------------------------------------------
            # Step 10 — Click Save; verify the skill is created and appears
            # in the Skills list
            # ------------------------------------------------------------------
            with allure.step("Step 10 — Click Save; verify skill is created and appears in the Skills list"):
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()

                match = re.search(r"/skills/all/(\d+)$", page.url)
                assert match, f"Expected detail-page URL with a skill id, got: {page.url}"
                skill_id = int(match.group(1))

                list_page.navigate()
                assert list_page.skill_exists_in_list(skill_name), (
                    f"Skill '{skill_name}' should appear in the Skills list after creation"
                )
        finally:
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%s", skill_id)
                except Exception as exc:
                    logger.warning("Skill cleanup failed (non-fatal): %s", exc)


class TestEditSkill:
    """Edit an existing skill's Name, Description, and Instructions, save,
    and verify all three values persist across a re-open (ELITEA-2431, P3).
    """

    @allure.issue("ELITEA-2431", "onetest-ai Test Case link")
    @pytest.mark.p3
    @pytest.mark.skills
    def test_edit_name_description_instructions_persist(self, page, skill_api):
        """Seed a skill via API, open it, edit all three fields, Save,
        navigate back to the Skills list and re-open the skill, then verify
        the Name/Description/Instructions fields all show the updated values.
        """
        original_description = "Original description before edit"
        original_instructions = "Always say ORIGINAL"
        updated_description = "Updated description after edit"
        updated_instructions = "Always say UPDATED"
        skill_id = None

        try:
            # ------------------------------------------------------------
            # Setup — seed the skill via API (edit needs pre-existing state)
            # ------------------------------------------------------------
            created = skill_api.create_skill(
                name=EDIT_SKILL_ORIGINAL_NAME,
                description=original_description,
                instructions=original_instructions,
            )
            skill_id = created["id"]

            # ------------------------------------------------------------
            # Step 1 — Open an existing Skill
            # ------------------------------------------------------------
            with allure.step("Step 1 — Open an existing Skill"):
                detail_page = SkillDetailPage(page)
                detail_page.navigate(skill_id)
                assert detail_page.get_name() == EDIT_SKILL_ORIGINAL_NAME
                assert detail_page.get_description() == original_description
                assert detail_page.get_instructions() == original_instructions

            # ------------------------------------------------------------
            # Step 2 — Change the Name, Description, and Instructions
            # ------------------------------------------------------------
            with allure.step("Step 2 — Change the Name, Description, and Instructions to new values"):
                detail_page.set_name(EDIT_SKILL_NEW_NAME)
                detail_page.set_description(updated_description)
                detail_page.fill_instructions(updated_instructions)
                detail_page.wait_for_form_validation()
                assert detail_page.get_name() == EDIT_SKILL_NEW_NAME
                assert detail_page.get_description() == updated_description
                assert detail_page.get_instructions() == updated_instructions
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled once all three fields hold valid values"
                )

            # ------------------------------------------------------------
            # Step 3 — Click Save
            # ------------------------------------------------------------
            with allure.step("Step 3 — Click Save"):
                response = detail_page.save_edits(timeout=FORM_SAVE_TIMEOUT)
                assert response.status == 200, (
                    f"Expected 200 from the skill update PUT, got {response.status}"
                )

            # ------------------------------------------------------------
            # Step 4 — Navigate back to the Skills list and re-open the Skill
            # ------------------------------------------------------------
            with allure.step("Step 4 — Navigate back to the Skills list and re-open the Skill"):
                list_page = SkillsListPage(page)
                list_page.navigate()
                assert list_page.skill_exists_in_list(EDIT_SKILL_NEW_NAME), (
                    f"Skill should be listed under its new name {EDIT_SKILL_NEW_NAME!r}"
                )
                list_page.click_skill_card(EDIT_SKILL_NEW_NAME)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

            # ------------------------------------------------------------
            # Step 5 — Verify all three updated values are persisted
            # ------------------------------------------------------------
            with allure.step("Step 5 — Verify all three updated values are persisted correctly"):
                assert detail_page.get_name() == EDIT_SKILL_NEW_NAME, (
                    "Name should show the updated value after re-open"
                )
                assert detail_page.get_description() == updated_description, (
                    "Description should show the updated value after re-open"
                )
                assert detail_page.get_instructions() == updated_instructions, (
                    "Instructions should show the updated value after re-open"
                )
        finally:
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%s", skill_id)
                except Exception as exc:
                    logger.warning("Skill cleanup failed (non-fatal): %s", exc)
