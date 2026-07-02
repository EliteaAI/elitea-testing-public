"""Skills management UI tests.

Tests the full lifecycle of a skill:
- Create via UI form
- Execute via SkillTestPanel
- Verify response
- Delete via overflow menu
"""

import logging

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

        Steps:
        1. Navigate to create skill page
        2. Fill form: name, description, instructions (CodeMirror)
        3. Save — verify navigation to detail page
        4. Send "hello world" in SkillTestPanel
        5. Assert the response contains only uppercase alphabetic characters
        6. Delete skill via overflow menu
        7. Verify skill is gone from the list
        """
        skill_name = clean_skill
        skill_instructions = "type text with caps only"
        skill_description = "Automation test skill - capitalize all output"
        test_message = "hello world"

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

        # Step 3: Save — save_and_wait_for_navigation waits for the detail
        # page's skill-information-section to be visible, so no additional
        # wait_for_page_load call is needed after this.
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), (
            "Save should be enabled after filling all required fields"
        )
        form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

        # Step 4: Verify on detail page
        detail_page = SkillDetailPage(page)
        detail_page.verify_on_detail_page()

        # Step 5: Send test message in SkillTestPanel
        initial_count = detail_page.get_test_message_count()
        detail_page.send_test_message(test_message)
        detail_page.wait_for_test_response(
            initial_count=initial_count,
            timeout=AI_RESPONSE_TIMEOUT,
        )

        # Step 6: Verify response contains uppercase alphabetic characters only
        response_text = detail_page.get_last_test_response()
        alpha_chars = [c for c in response_text if c.isalpha()]
        assert alpha_chars, (
            f"Response contains no alphabetic characters: '{response_text}'"
        )
        assert all(c.isupper() for c in alpha_chars), (
            f"Expected all-uppercase response, got: '{response_text}'"
        )

        # Step 7: Delete skill via overflow menu
        detail_page.delete_skill_via_menu(
            skill_name=skill_name,
            timeout=UI_ELEMENT_TIMEOUT,
        )

        # Verify redirect back to list and skill card is gone.
        # wait_for_page_load confirms the list URL; wait_for_skill_absent
        # polls until the card disappears and raises TimeoutError if it does not.
        list_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        list_page.wait_for_skill_absent(skill_name, timeout=NAVIGATION_TIMEOUT)
        assert not list_page.skill_exists_in_list(skill_name), (
            f"Skill '{skill_name}' should be gone from list after deletion"
        )
