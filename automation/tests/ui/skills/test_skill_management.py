"""Skills management UI tests.

Tests the full lifecycle of a skill:
- Create via UI form
- Execute via SkillTestPanel
- Verify response
- Delete via overflow menu
"""

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


class TestCreateSkill:
    """Create Skill (P0): create via UI, execute via test panel, verify output, delete."""

    @allure.issue("", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_skill_and_verify_execution(self, page, skill_api):
        """Create a skill with caps-only instruction, run it in the test panel,
        verify the response is all uppercase, then delete the skill.

        Steps:
        1. Navigate to create skill page
        2. Fill form: name, description, instructions (CodeMirror)
        3. Save — verify navigation to detail page
        4. Send "hello world" in SkillTestPanel
        5. Assert the response is all uppercase
        6. Delete skill via overflow menu
        7. Verify skill is gone from the list

        Cleanup:
            Falls back to skill_api.delete_skill() if UI delete fails.
        """
        skill_name = "autotest-skill-caps"
        skill_instructions = "type text with caps only"
        skill_description = "Automation test skill - capitalize all output"
        test_message = "hello world"
        created_skill_id = None

        # Pre-cleanup: remove any leftover skill from a previous failed run
        try:
            skills = skill_api.list_skills()
            for skill in skills.get("rows", []):
                if skill.get("name") == skill_name:
                    skill_api.delete_skill(skill["id"])
                    print(f"Pre-cleanup: deleted leftover skill id={skill['id']}")
                    break
        except Exception as pre_cleanup_err:
            print(f"Pre-cleanup skipped: {pre_cleanup_err}")

        # Step 1: Navigate to create skill page
        list_page = SkillsListPage(page)
        list_page.navigate_to_create()

        # Step 2: Fill form (name, description, instructions)
        form_page = SkillFormPage(page)
        form_page.wait_for_form_load()
        form_page.fill_form(
            name=skill_name,
            instructions=skill_instructions,
            description=skill_description,
        )

        # Step 3: Save
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), (
            "Save should be enabled after filling all required fields"
        )
        form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

        # Step 4: Verify on detail page
        detail_page = SkillDetailPage(page)
        detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        detail_page.verify_on_detail_page()

        try:
            created_skill_id = int(detail_page.get_skill_id())

            # Step 5: Send test message in SkillTestPanel
            initial_count = detail_page.get_test_message_count()
            detail_page.send_test_message(test_message)
            detail_page.wait_for_test_response(
                initial_count=initial_count,
                timeout=AI_RESPONSE_TIMEOUT,
            )

            # Step 6: Verify response is uppercase
            response_text = detail_page.get_last_test_response()
            assert len(response_text) > 0, "Response should not be empty"
            assert response_text == response_text.upper(), (
                f"Expected all-uppercase response, got: '{response_text}'"
            )

            # Step 7: Delete skill via overflow menu
            detail_page.delete_skill_via_menu(
                skill_name=skill_name,
                timeout=UI_ELEMENT_TIMEOUT,
            )

            # Verify redirect back to list after deletion
            list_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            # Wait for the list to re-fetch and remove the deleted skill card
            list_page.wait_for_skill_absent(skill_name, timeout=NAVIGATION_TIMEOUT)
            assert not list_page.skill_exists_in_list(skill_name), (
                f"Skill '{skill_name}' should be gone from list after deletion"
            )
            created_skill_id = None  # Successfully deleted via UI

        finally:
            if created_skill_id is not None:
                try:
                    skill_api.delete_skill(created_skill_id)
                except Exception as e:
                    print(
                        f"Warning: API cleanup failed for skill {created_skill_id}: {e}"
                    )
