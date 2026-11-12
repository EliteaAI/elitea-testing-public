"""UI Test for ELITEA-4634 — run an own Skill from the Skills page (table-row menu) and exchange a message.

AFS: test-specs/skills/l1_run-own-skill-from-skills-page-and-message-exchange_ELITEA-4634.md

Case-text drift (live product is the contract): Run lives in the table-view row menu (not a card icon),
opens the skill detail page with the Skill test panel (no new chat, no participants panel, empty
placeholder); a skill-source run is not listed in the Chats sidebar, so the persisted `?run=<id>`
conversation is asserted instead.
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
TEST_MESSAGE = "Convert this to uppercase: hello world"


@allure.epic("Skills")
@allure.feature("Run skill")
class TestOwnSkillRunMessageExchange:
    """ELITEA-4634 — Skills table row menu -> Run -> skill test panel -> message exchange."""

    @pytest.mark.tms("ELITEA-4634")
    @allure.title("Own skill: run from the Skills page and verify the message exchange")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4634_run-own-skill-from-skills-page.md",
        "onetest-ai Test Case link",
    )
    def test_run_own_skill_and_exchange_message(self, page: Page, skill_api, conversation_api):
        skills = SkillsListPage(page)
        detail = SkillDetailPage(page)
        chat = ChatPage(page)
        skill_name = f"autotest-4634-{int(time.time())}"[:32]
        created = skill_api.create_skill(
            name=skill_name,
            description="Autotest skill for ELITEA-4634.",
            instructions="Convert the user text to UPPERCASE and reply with only that.",
        )
        skill_id = int(created["id"] if isinstance(created, dict) else created)
        conv_id = None
        try:
            with allure.step("Step 1 — Open the Skills page; the own skill is listed"):
                skills.navigate()
                skills.dismiss_announcement_dialog_if_present()
                expect(skills.skill_card_name.filter(has_text=skill_name)).to_have_count(
                    1, timeout=NAVIGATION_TIMEOUT
                )

            with allure.step("Step 2 — Switch to table view; the skill's row is present"):
                skills.table_view_button.click()
                expect(skills.row_action_button(skill_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Open the row menu: Run offered, no Catalog badge"):
                skills.row_action_button(skill_id).click()
                expect(skills.ROW_RUN_MENU_ITEM.within(page)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(page.locator(chat.PARTICIPANT_CATALOG_TAG)).to_have_count(0)

            with allure.step("Step 4 — Click Run: skill detail opens with the empty test panel"):
                skills.ROW_RUN_MENU_ITEM.within(page).click()
                page.wait_for_url(re.compile(rf"/skills/all/{skill_id}(\?.*)?$"), timeout=NAVIGATION_TIMEOUT)
                expect(detail.test_panel).to_be_visible(timeout=NAVIGATION_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_have_value("")
                assert detail.get_test_message_count() == 0, "Fresh run panel must have no messages"

            with allure.step("Step 5 — Send the message; it appears in the thread"):
                skills.dismiss_announcement_dialog_if_present()
                detail.send_test_message(TEST_MESSAGE)
                expect(chat.messages_container.filter(has_text=TEST_MESSAGE)).to_have_count(
                    1, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6 — Skill replies with the uppercased text"):
                detail.wait_for_test_response(initial_count=1, timeout=AI_RESPONSE_TIMEOUT)
                reply = detail.get_last_test_response()
                assert "HELLO WORLD" in reply, f"Unexpected skill reply: {reply[:200]!r}"
                assert "something went wrong" not in reply.lower(), reply[:200]

            with allure.step("Step 7 — Conversation is persisted (?run=<id>) and restored on reload"):
                page.wait_for_url(re.compile(r"[?&]run=\d+"), timeout=UI_ELEMENT_TIMEOUT)
                conv_id = int(re.search(r"[?&]run=(\d+)", page.url).group(1))
                page.reload()
                # Reload keeps the panel closed (aria-hidden); the ?run= conversation restores on open.
                detail.open_test_skill_panel(timeout=NAVIGATION_TIMEOUT)
                expect(chat.messages_container).to_have_count(2, timeout=NAVIGATION_TIMEOUT)
        finally:
            with allure.step("Cleanup — delete the conversation and the skill"):
                if conv_id is not None:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Conversation %s cleanup failed: %s", conv_id, exc)
                skill_api.delete_skill(skill_id)
