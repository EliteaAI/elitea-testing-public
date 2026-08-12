"""Skills listing — card view shows correct fields (ELITEA-2428).

Verifies that a Skills grid card shows all four expected fields for a
freshly created skill: the entity icon, the skill name, the description
(revealed only on hover via a tooltip — never as always-visible card text),
and the assigned tag(s). Also confirms Card view is the active list view on
`/skills/all` by default, with no click on the view toggle required.

No product defect found — all four fields, plus the Card-view-default
behavior, live-verified end-to-end.

Spec: test-specs/skills/l2_skills-card-view-fields_ELITEA-2428.md
"""

import logging
import uuid

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

FORM_SAVE_TIMEOUT = 15_000
UI_ELEMENT_TIMEOUT = 10_000


class TestSkillCardViewFields:
    """ELITEA-2428 — Skills list card view shows icon, name, hover-description, tags."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2428_skills-card-view-fields.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_skill_card_shows_icon_name_description_and_tags(self, page, skill_api):
        """Create a skill with name/description/tag; verify its card shows
        icon, name, description-on-hover, and tag(s) in the default Card view."""
        unique_suffix = uuid.uuid4().hex[:8]
        skill_name = f"autotest-card-fields-{unique_suffix}"
        description = (
            "ELITEA-2428 card-view field verification description text, "
            "unique enough to spot in a hover tooltip."
        )
        tag = "cardfields2428"
        skill_id = None

        console_messages = []
        page.on(
            "console",
            lambda msg: console_messages.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step("Step 1 — Create a Skill with a name, description, and tag via the create form"):
                list_page = SkillsListPage(page)
                form_page = SkillFormPage(page)
                detail_page = SkillDetailPage(page)

                list_page.navigate_to_create()
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=skill_name,
                    instructions="You are a test skill used for ELITEA-2428 card-field verification. Reply 'ok'.",
                    description=description,
                )
                form_page.add_tag(tag)
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled once name, description, instructions, "
                    "and tags are all valid"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
                detail_page.verify_on_detail_page()
                skill_id = int(detail_page.get_skill_id())
                assert skill_id, "Expected a numeric Skill ID on the detail page"
                logger.info("Created skill %r — id=%s", skill_name, skill_id)

            with allure.step("Step 2 — Navigate to the Skills list; confirm Card view is active by default"):
                list_page.navigate()
                list_page.card_view_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert list_page.is_card_view_active(), (
                    "Card view should be the active list view on a fresh "
                    "navigation to /skills/all, with no click on the toggle"
                )

            with allure.step("Step 3a — Verify the created skill's card shows its icon"):
                card = list_page.skill_card.filter(has_text=skill_name).first
                card.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                expect(list_page.card_icon_locator(skill_name)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 3b — Verify the created skill's card shows its exact name"):
                card_name_locator = list_page.skill_card_name.filter(has_text=skill_name)
                expect(card_name_locator).to_have_text(skill_name)

            with allure.step("Step 3c — Hover the card name and verify the tooltip shows the exact description"):
                card_name_locator.first.hover()
                expect(list_page.card_description_tooltip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(list_page.card_description_tooltip).to_have_text(description)

            with allure.step("Step 3d — Verify the created skill's card shows the assigned tag"):
                card_tags = list_page.get_card_tags(skill_name)
                assert tag in card_tags, (
                    f"Expected tag {tag!r} on skill card {skill_name!r}, got {card_tags}"
                )

            with allure.step("Step 4 — Verify zero console errors across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors: {[m.text for m in console_messages]}"
                )
        finally:
            if skill_id:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%s", skill_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for skill id=%s (non-fatal): %s", skill_id, exc)
