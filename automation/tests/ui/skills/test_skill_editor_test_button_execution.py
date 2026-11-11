"""UI Test for ELITEA-4635 — Test Skill button in the skill editor opens the test panel; send a message
and verify the skill execution chips and response.

AFS: test-specs/skills/l1_test-skill-button-opens-panel-and-executes-skill_ELITEA-4635.md

Case-text drift (live product is the contract): the skill is created per run via API (not a pre-existing
"lmt-answer-format"); the send button only renders once text is typed (voice button shows before);
there is no explicit success icon, so success is asserted as a non-empty reply with no
alert/error text in the panel.
"""

import logging
import re
import time

import allure
import pytest
from pages.chat_page import ChatPage
from pages.skill_detail_page import SkillDetailPage
from pages.skills_list_page import SkillsListPage
from playwright.sync_api import Page, expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.skills,
    pytest.mark.chat,
    pytest.mark.p1,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 30_000
AI_RESPONSE_TIMEOUT = 60_000
TEST_MESSAGE = "run"


@allure.epic("Skills")
@allure.feature("Test skill from editor")
class TestSkillEditorTestButtonExecution:
    """ELITEA-4635 — skill editor -> Test Skill button -> panel -> send -> execution chips + response."""

    @pytest.mark.tms("ELITEA-4635")
    @allure.title("Test Skill button opens the test panel; message exchange shows skill execution chips")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4635_test-skill-from-editor-interaction-panel.md",
        "onetest-ai Test Case link",
    )
    def test_test_skill_button_opens_panel_and_executes_skill(self, page: Page, skill_api, conversation_api):
        skills = SkillsListPage(page)
        detail = SkillDetailPage(page)
        chat = ChatPage(page)
        skill_name = f"autotest-4635-{int(time.time())}"[:32]
        created = skill_api.create_skill(
            name=skill_name,
            description="4635 probe",
            instructions="Convert the user text to UPPERCASE and reply with only that.",
        )
        skill_id = int(created["id"] if isinstance(created, dict) else created)
        conv_id = None
        try:
            with allure.step("Step 1 — Open the skill editor: Test Skill button next to Edit with AI, panel closed"):
                skills.navigate()
                skills.dismiss_announcement_dialog_if_present()
                detail.navigate(skill_id)
                expect(detail.test_skill_button).to_be_visible(timeout=NAVIGATION_TIMEOUT)
                expect(detail.test_skill_button).to_be_enabled()
                expect(detail.test_skill_button).to_contain_text("Test Skill")
                expect(detail.edit_with_ai_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(detail.test_panel).not_to_be_visible()

            with allure.step("Step 2 — Click Test Skill: the test panel opens"):
                detail.dismiss_announcement_dialog_if_present()
                detail.test_skill_button.click()
                expect(detail.test_panel).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Panel shows the input (placeholder) and no messages"):
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_have_attribute("placeholder", "Type your message...")
                assert detail.get_test_message_count() == 0, "Fresh test panel must have no messages"

            with allure.step(
                "Step 4 — Type the test message; it appears in the input and the send button is offered"
            ):
                detail.dismiss_announcement_dialog_if_present()
                chat.message_input.fill(TEST_MESSAGE)
                expect(chat.message_input).to_have_value(TEST_MESSAGE)
                expect(chat.send_button).to_be_visible()

            with allure.step("Step 5 — Send: the user message appears in the thread with the author name"):
                chat.send_button.click()
                expect(chat.messages_container.first).to_contain_text(TEST_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.messages_container.first).to_contain_text("autotest_user_admin")

            with allure.step("Step 6 — Wait for completion; 'Thought for N secs' indicator is shown"):
                detail.wait_for_test_response(initial_count=1, timeout=AI_RESPONSE_TIMEOUT)
                expect(chat.answer_thought_accordion.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.answer_thought_accordion.first).to_have_text(re.compile(r"Thought for \d+ secs?"))

            with allure.step("Step 7 — Execution chips show 'Skill: <name>' and a model name"):
                expect(chat.answer_tool_chip.first).to_have_text(f"Skill: {skill_name}")
                expect(chat.answer_model_chip.first).to_be_visible()
                expect(chat.answer_model_chip.first).not_to_have_text("")

            with allure.step("Step 8 — Response is relevant and no error is shown"):
                reply = detail.get_last_test_response()
                assert reply, "Skill reply must be non-empty"
                assert "run" in reply.lower(), f"Reply not relevant to the skill instructions: {reply[:200]!r}"
                assert "something went wrong" not in reply.lower(), reply[:200]
                expect(detail.TEST_PANEL_ALERT.within(detail.test_panel)).to_have_count(0)

            conv_match = re.search(r"[?&]run=(\d+)", page.url)
            if conv_match:
                conv_id = int(conv_match.group(1))
        finally:
            with allure.step("Cleanup — delete the conversation and the skill"):
                if conv_id is None:
                    m = re.search(r"[?&]run=(\d+)", page.url)
                    conv_id = int(m.group(1)) if m else None
                if conv_id is not None:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Conversation %s cleanup failed: %s", conv_id, exc)
                skill_api.delete_skill(skill_id)
