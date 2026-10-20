"""UI Test for ELITEA-3366 — Skill creation from chat with complete information.

With the Skills Builder module enabled, a fully-specified chat message makes the
AI create a Skill without clarifying questions, a Skill chip renders in the
response, clicking it opens the Skill editor Canvas with accurate fields, and the
Skill is NOT auto-added as a chat participant.

Case-text drift (AFS Known Defects/Clarifications, live product is the contract):
chip label and Name are the slugified skill name; Description and Instructions are
AI-rephrased, so they are asserted topically.

Usage:
    cd automation
    pytest tests/ui/chat/test_skill_creation_from_chat_chip_canvas.py -v
"""

import logging
import re
import uuid

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage
from pages.skill_form_page import SkillFormPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.skills,
    pytest.mark.p0,
    pytest.mark.regression,
]

AI_RESPONSE_TIMEOUT = 90_000
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
TOOL_CALL_TEXT = "Elitea Skills: post_elitea_core_skills"


def _slugify(display_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", display_name.lower()).strip("-")


@allure.epic("Chat")
@allure.feature("Skills Builder")
class TestSkillCreationFromChat:
    """ELITEA-3366 — skill creation from chat, chip opens Canvas."""

    @pytest.mark.tms("ELITEA-3366")
    @allure.title("Skill creation from chat with complete info creates skill; chip opens Canvas")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/",
        "onetest-ai Test Case link",
    )
    def test_skill_created_from_chat_chip_opens_canvas(self, page, conversation_api, skill_api):
        chat = ChatPage(page)
        token = uuid.uuid4().hex[:8]
        display_name = f"Daily Standup Summarizer {token}"
        slug = _slugify(display_name)
        message = (
            f"Create a skill called '{display_name}' that summarizes daily standup notes "
            "into action items. Instructions: Given raw standup notes, extract blockers, "
            "decisions, and action items as a bulleted list."
        )
        conv_id = None

        try:
            with allure.step("Precondition — new conversation, enable Skills Builder module"):
                chat.navigate_to_chat()
                chat.dismiss_platform_banner_dialog()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                chat.dismiss_platform_banner_dialog()
                conv_id = chat.get_current_conversation_id()
                chat.open_internal_tools_menu()
                chat.ensure_module_toggle_checked("skill_builder", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_module_toggle_checked("skill_builder"), "Skills Builder toggle should be on"
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 1 — Send the fully-specified message; AI invokes the Skills tool, no question"):
                initial_count = chat.get_message_count()
                chat.send_message(message, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)
                evidence = chat.get_tool_chip_and_message_text()
                assert TOOL_CALL_TEXT in evidence, (
                    f"Expected the Skills tool call '{TOOL_CALL_TEXT}' in the response, got: {evidence[:500]!r}"
                )
                if conv_id is None:
                    conv_id = chat.get_current_conversation_id()

            with allure.step("Step 2 — Response contains exactly one Skill chip labelled with the skill name"):
                labels = chat.get_generated_entity_chip_labels()
                assert len(labels) == 1, f"Expected exactly one generated-entity chip, got {labels}"
                assert labels[0] == slug, f"Chip label should be the slugified skill name {slug!r}, got {labels[0]!r}"

            with allure.step("Step 3 — Click the chip's Open entity button; Skill editor Canvas opens"):
                chat.open_generated_entity_chip(timeout=UI_ELEMENT_TIMEOUT)
                skill_form = SkillFormPage(page)
                expect(skill_form.name_input_field).to_be_visible(timeout=NAVIGATION_TIMEOUT)

            with allure.step("Step 4 — Canvas fields match the created skill; Save disabled, Discard present"):
                expect(skill_form.name_input_field).to_have_value(slug, timeout=UI_ELEMENT_TIMEOUT)
                description = skill_form.get_description().lower()
                assert "standup" in description, f"Description should mention standup, got {description!r}"
                assert "action items" in description or "blockers" in description, (
                    f"Description should be topically consistent, got {description!r}"
                )
                instructions = skill_form.get_instructions_multiline().lower()
                for term in ("standup", "blockers", "decisions", "action items"):
                    assert term in instructions, f"Instructions should contain {term!r}, got {instructions!r}"
                expect(chat.skill_canvas_save_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.skill_canvas_save_button).to_be_disabled()
                expect(chat.skill_canvas_discard_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Participants list does not include the new Skill"):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                rows = page.locator(chat.PARTICIPANT_ROW_PREFIX)
                texts = [(rows.nth(i).inner_text() or "") for i in range(rows.count())]
                assert not any(slug in t for t in texts), (
                    f"Skill {slug!r} must not be auto-added as a participant, got rows: {texts}"
                )
        finally:
            with allure.step("Cleanup — delete created skill and conversation"):
                try:
                    rows = skill_api.list_skills().get("rows", [])
                    for row in rows:
                        if row.get("name") == slug:
                            skill_api.delete_skill(row["id"])
                            logger.info("Deleted skill %s", row["id"])
                except Exception as exc:
                    logger.warning("Skill cleanup failed: %s", exc)
                if conv_id:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:
                        logger.warning("Conversation cleanup failed: %s", exc)
