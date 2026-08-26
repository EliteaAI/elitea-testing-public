"""Test for Skill — multiple tags persist on creation and edit.

Verifies that tags committed BEFORE the first Save (on /skills/create) ride
the create POST payload and persist through a fresh reload, and that tags
added LATER (edit flow) merge with the pre-existing ones rather than
replacing them — the full set persists together through another fresh
reload and renders on both the detail-page form and the list-view card.

Test case: ELITEA-2434
AFS: test-specs/skills/l3_multiple-tags-persist-on-creation-and-edit_ELITEA-2434.md
"""

import logging
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

FORM_SAVE_TIMEOUT = 15_000


class TestSkillMultipleTagsPersist:
    """ELITEA-2434 — Multiple tags can be saved on a Skill upon and after creation."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2434_multiple-tags-persist-on-creation-and-edit.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.flaky
    def test_multiple_tags_persist_on_creation_and_edit(self, page, skill_api):
        """Create a Skill with 2 pre-save tags, then add 2 more via edit; all
        4 persist together through fresh reloads and render on the card."""
        ts = int(time.time())
        skill_name = f"autotest-multi-tag-{ts}"[:32]
        skill_id = None

        try:
            with allure.step(
                'Step 1 — Create form: add tags "tag1", "tag2" before the first Save'
            ):
                list_page = SkillsListPage(page)
                form_page = SkillFormPage(page)

                list_page.navigate_to_create()
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=skill_name,
                    instructions="You are a test skill used for multi-tag automation. Reply 'ok'.",
                    description="Autotest skill for ELITEA-2434 multi-tag verification.",
                )
                form_page.add_tag("tag1")
                form_page.add_tag("tag2")
                form_page.wait_for_form_validation()
                assert form_page.get_tags() == ["tag1", "tag2"], (
                    f"Expected ['tag1', 'tag2'] committed pre-save, got: {form_page.get_tags()!r}"
                )
                assert form_page.is_save_enabled(), (
                    "Save should be enabled once name, description, instructions, and tags are valid"
                )

            with allure.step(
                "Step 2 — Save and verify the POST returns 201 with both pre-save tags in the payload"
            ):
                payload, status = form_page.save_and_wait_for_navigation_capturing_payload(
                    timeout=FORM_SAVE_TIMEOUT
                )
                assert status == 201, (
                    f"Expected 201 from the create-flow POST, got {status}"
                )
                assert payload is not None, "Expected to capture the create-flow POST payload"
                # Confirmed live/source-side (CreateSkillTabBar.jsx onSave): tags ride
                # inside versions[0].tags, not a top-level `tags` key.
                version_tags = (payload.get("versions") or [{}])[0].get("tags", [])
                payload_tags = {t.get("name") if isinstance(t, dict) else t for t in version_tags}
                assert {"tag1", "tag2"} <= payload_tags, (
                    f"Expected the create POST payload's versions[0].tags to include "
                    f"tag1/tag2, got: {payload_tags!r}"
                )

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = int(detail_page.get_skill_id())
                logger.info("Skill created — id=%s name=%s", skill_id, skill_name)

            with allure.step("Step 3 — Re-open the Skill (fresh load) and verify both tags persisted"):
                detail_page.navigate(skill_id)
                assert detail_page.get_tags() == ["tag1", "tag2"], (
                    f"Expected ['tag1', 'tag2'] after a fresh reload, got: {detail_page.get_tags()!r}"
                )

            with allure.step(
                'Step 4 — Add "tag3", "tag4" to the saved Skill (edit mode) and Save'
            ):
                detail_page.add_tag("tag3")
                detail_page.add_tag("tag4")
                assert detail_page.get_tags() == ["tag1", "tag2", "tag3", "tag4"], (
                    "Expected all 4 tags present, original order preserved, got: "
                    f"{detail_page.get_tags()!r}"
                )
                assert detail_page.is_save_enabled(), (
                    "Save should be enabled once the new tags are added"
                )

                response = detail_page.save_edits()
                assert response.status == 200, (
                    f"Expected 200 from the edit-flow PUT, got {response.status}"
                )

            with allure.step(
                "Step 5 — Re-open the Skill (fresh load) and verify all 4 tags persist "
                "on both the form and the list card"
            ):
                detail_page.navigate(skill_id)
                assert detail_page.get_tags() == ["tag1", "tag2", "tag3", "tag4"], (
                    "Expected all 4 tags to persist together through a fresh reload, got: "
                    f"{detail_page.get_tags()!r}"
                )

                list_page.navigate()
                # CardTagSection.jsx only ever renders the first 2 tags as
                # individual chips (MAX_NUMBER_TAGS_SHOWN=2, confirmed
                # live/source-side) — a 4-tag skill's card shows 2 chips
                # (both real, listed tags) plus a "+2" overflow badge, never
                # 4 separate chips. See AFS ELITEA-2434 Known Defects for the
                # case-text-drift note.
                card_tags = set(list_page.get_card_tags(skill_name))
                assert card_tags, f"Expected at least the visible tag chips on {skill_name!r}'s card"
                assert card_tags <= {"tag1", "tag2", "tag3", "tag4"}, (
                    f"Card-rendered tags should all be real members of the 4-tag set, got: {card_tags!r}"
                )
                assert list_page.get_card_tag_overflow_text(skill_name) == "+2", (
                    "Expected the card's overflow badge to read '+2' for the 2 tags not "
                    f"shown as chips, got: {list_page.get_card_tag_overflow_text(skill_name)!r}"
                )

        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(skill_id)
                    logger.info("Deleted skill id=%s", skill_id)
