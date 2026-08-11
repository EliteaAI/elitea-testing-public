"""Test for Skill — add, save, and remove a tag.

Verifies that a tag added to an existing (tag-free) Skill via the Tags
combobox persists after Save on both the detail-page form and the list-view
card, and that removing it (via the chip's delete icon) and saving again
correctly clears it everywhere — no orphan tag remains.

Test case: ELITEA-2433
AFS: test-specs/skills/l3_add-save-remove-skill-tag_ELITEA-2433.md
"""

import logging
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression]

TAG_TEXT = "regression_v1"


class TestSkillTagAddRemove:
    """ELITEA-2433 — Add, save, and remove a tag on a Skill."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2433_add-save-remove-skill-tag.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_add_save_and_remove_skill_tag(self, page, skill_api):
        """Add a tag, save, verify persistence, remove it, save, verify it's gone."""
        ts = int(time.time())
        skill_name = f"autotest-tag-add-remove-{ts}"[:32]
        skill_id = None

        try:
            with allure.step("Setup — Create a Skill with no tags via API"):
                skill = skill_api.create_skill(
                    name=skill_name,
                    description="Autotest skill for ELITEA-2433 tag add/remove flow.",
                    instructions="You are a test skill used for tag add/remove automation. Reply 'ok'.",
                )
                skill_id = skill["id"]
                assert skill_id, "Expected a numeric id for the created skill"
                logger.info("Created skill id=%s name=%s", skill_id, skill_name)

            with allure.step("Step 1 — Open the Skill and verify it has no tags"):
                detail_page = SkillDetailPage(page)
                detail_page.navigate(skill_id)
                assert detail_page.information_section.is_visible(), (
                    "Skill information section should be visible after navigating to the detail page"
                )
                assert detail_page.get_tags() == [], (
                    "Precondition: the freshly-created skill should have no tags"
                )

            with allure.step(f"Step 2 — Add tag {TAG_TEXT!r} and verify the chip renders"):
                detail_page.add_tag(TAG_TEXT)
                assert detail_page.get_tags() == [TAG_TEXT], (
                    f"Expected exactly [{TAG_TEXT!r}] after adding the tag, got: {detail_page.get_tags()!r}"
                )
                assert detail_page.is_save_enabled(), (
                    "Save button should become enabled once the tag is added"
                )

            with allure.step("Step 3 — Save and verify the tag appears on the Skill card in the list"):
                response = detail_page.save_edits()
                assert response.status == 200, (
                    f"Expected 200 from the edit-flow PUT, got {response.status}"
                )

                list_page = SkillsListPage(page)
                list_page.navigate()
                card_tags = list_page.get_card_tags(skill_name)
                assert TAG_TEXT in card_tags, (
                    f"Expected {TAG_TEXT!r} on {skill_name!r}'s card, got: {card_tags!r}"
                )

            with allure.step("Step 4 — Re-open the Skill (fresh load) and remove the tag"):
                detail_page.navigate(skill_id)
                assert detail_page.get_tags() == [TAG_TEXT], (
                    f"Expected the tag to persist across a fresh reload, got: {detail_page.get_tags()!r}"
                )

                detail_page.remove_tag(TAG_TEXT)
                assert detail_page.get_tags() == [], (
                    f"Expected no tags after removing {TAG_TEXT!r}, got: {detail_page.get_tags()!r}"
                )
                assert detail_page.is_save_enabled(), (
                    "Save button should become enabled again once the tag is removed"
                )

            with allure.step("Step 5 — Save and verify the tag no longer appears on the card"):
                response = detail_page.save_edits()
                assert response.status == 200, (
                    f"Expected 200 from the edit-flow PUT, got {response.status}"
                )

                list_page.navigate()
                card_tags_after = list_page.get_card_tags(skill_name)
                assert card_tags_after == [], (
                    f"Expected no tags on {skill_name!r}'s card after removal, got: {card_tags_after!r}"
                )

        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(skill_id)
                    logger.info("Deleted skill id=%s", skill_id)
