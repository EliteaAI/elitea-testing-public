"""UI Test for ELITEA-4630 — Chat: skill auto-invocation from user intent (no participant, no "~").

AFS: test-specs/chat-interface/l1_skill-auto-invocation-from-chat-by-intent_ELITEA-4630.md

Case-text drift (live product is the contract): "jira-issue-creator" does not exist on DEV, so two
fixture skills with distinct-domain descriptions are used and execution is tied to the chosen skill
through deterministic marker tokens (the fixture skill has no Jira toolkit). Relies on the project
setting "Project skills in chat" being on (platform default Enabled on DEV).
"""

import logging
import time

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.skills,
    pytest.mark.p0,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
RESPONSE_TIMEOUT = 90_000
MARKER_JIRA = "JIRATICKET:"
MARKER_RECIPE = "RECIPEPLAN:"
JIRA_INTENT = "I need to create a new ticket in Jira for bug fix"
RECIPE_INTENT = "Can you suggest a vegetarian dinner menu for four people?"


@allure.epic("Chat")
@allure.feature("Skill auto-invocation")
class TestChatSkillAutoInvocationByIntent:
    """ELITEA-4630 — project skills are auto-selected from the user's intent."""

    @pytest.mark.tms("ELITEA-4630")
    @allure.title("Chat: a skill is auto-invoked from user intent without participant or ~ mention")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4630_skill-auto-invocation-from-chat.md",
        "onetest-ai Test Case link",
    )
    def test_skill_auto_invocation_by_intent(self, page, skill_api, conversation_api):
        chat = ChatPage(page)
        ts = int(time.time())
        name_a = f"jira-ticket-maker-{ts}"[:32]
        name_b = f"recipe-planner-{ts}"[:32]
        skill_ids = []
        conv_id = None
        try:
            with allure.step("Setup — create Jira skill A and recipe skill B via API"):
                skill_a = skill_api.create_skill(
                    name=name_a,
                    description=(
                        "Creates Jira tickets and issues for bug fixes. "
                        "Use when the user wants to create a ticket or issue in Jira."
                    ),
                    instructions=f"Whenever loaded, begin your reply with the exact token {MARKER_JIRA} then outline it.",
                )
                skill_ids.append(skill_a["id"])
                skill_b = skill_api.create_skill(
                    name=name_b,
                    description=(
                        "Plans cooking recipes and meal menus. "
                        "Use when the user wants a recipe, dinner idea or meal plan."
                    ),
                    instructions=f"Whenever loaded, begin your reply with the exact token {MARKER_RECIPE} then a menu.",
                )
                skill_ids.append(skill_b["id"])

            with allure.step("Step 1 — Open a blank chat; no skill or agent participant"):
                chat.navigate_to_chat()
                chat.dismiss_platform_banner_dialog()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                chat.dismiss_platform_banner_dialog()
                expect(chat.new_conversation_greeting).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.expand_participants_panel_via_toggle()
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(0)

            with allure.step("Step 2 — Type the natural-language Jira intent (no ~ mention)"):
                chat.message_input.press_sequentially(JIRA_INTENT, delay=30)
                expect(chat.message_input).to_have_value(JIRA_INTENT)

            with allure.step("Step 3 — Send; the user message shows the text"):
                initial_count = chat.get_message_count()
                chat.send_button.click(force=True)
                chat.wait_for_input_ready()
                conv_id = chat.get_current_conversation_id()
                expect(chat.messages_container.filter(has_text=JIRA_INTENT)).to_have_count(
                    1, timeout=UI_ELEMENT_TIMEOUT
                )
                chat.wait_for_message_count(initial_count + 1, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Wait for the reply to finish generating"):
                chat.wait_for_generation_complete(timeout=RESPONSE_TIMEOUT)

            with allure.step("Step 5 — Skill A auto-invoked: marker + Skill chip; skill B not selected"):
                reply = chat.messages_container.filter(has_text=MARKER_JIRA)
                expect(reply).to_have_count(1, timeout=RESPONSE_TIMEOUT)
                expect(reply.filter(has=chat.answer_tool_chip.filter(has_text=f"Skill: {name_a}"))).to_have_count(
                    1, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.messages_container.filter(has_text=MARKER_RECIPE)).to_have_count(0)
                expect(chat.answer_tool_chip.filter(has_text=f"Skill: {name_b}")).to_have_count(0)

            with allure.step("Step 6 — Skill was not an explicit participant and no ~ mention was used"):
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(0)
                expect(chat.messages_container.filter(has_text="~")).to_have_count(0)

            with allure.step("Step 7 — A different intent selects the other skill"):
                chat.message_input.press_sequentially(RECIPE_INTENT, delay=30)
                expect(chat.message_input).to_have_value(RECIPE_INTENT)
                chat.send_button.click(force=True)
                chat.wait_for_input_ready()
                chat.wait_for_generation_complete(timeout=RESPONSE_TIMEOUT)
                recipe_reply = chat.messages_container.filter(has_text=MARKER_RECIPE)
                expect(recipe_reply).to_have_count(1, timeout=RESPONSE_TIMEOUT)
                chip_b = chat.answer_tool_chip.filter(has_text=f"Skill: {name_b}")
                chip_a = chat.answer_tool_chip.filter(has_text=f"Skill: {name_a}")
                expect(recipe_reply.filter(has=chip_b)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(recipe_reply.filter(has=chip_a)).to_have_count(0)
        finally:
            with allure.step("Cleanup — delete conversation and skills"):
                if conv_id:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:
                        logger.warning("Conversation cleanup failed: %s", exc)
                for sid in skill_ids:
                    try:
                        skill_api.delete_skill(sid)
                    except Exception as exc:
                        logger.warning("Skill cleanup failed: %s", exc)
