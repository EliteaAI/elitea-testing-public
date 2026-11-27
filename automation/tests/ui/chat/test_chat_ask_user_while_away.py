"""UI Test for ELITEA-4955 — an Ask User question reached while away waits on the chat row.

Send in A and leave for B during the agent's 10 s wait; the run pauses on the Ask User question, A's row
shows the 'waiting' dot ("Waiting for your answer"), the card is enabled on return, and answering resumes
the run to `ASK-DONE post 2`. Self-provisioning: toolkits, agent (Ask User on) and both chats per run.

Markers: ui, chat, p0, regression.
"""

import logging
import re
import uuid

import allure
import pytest
from playwright.sync_api import expect

from api import ConversationAPI
from config import settings
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

_QUESTION = "Which JSONPlaceholder post should I look up?"
_MESSAGE = "Look up a post for me."
_EXPECTED_TOOLS = ["waitSeconds", "ask_user", "getPost", "getUser"]
UI_TIMEOUT = 15_000
PAUSE_CEILING_MS = 60_000
RUN_CEILING_MS = 90_000


@pytest.fixture
def ask_conversations(conversation_api: ConversationAPI):
    """Fresh conversation A (asks) and idle B (switch target); both deleted afterwards."""
    suffix = uuid.uuid4().hex[:6]
    a = conversation_api.create_conversation(f"autotest_ask_A_{suffix}")["id"]
    b = conversation_api.create_conversation(f"autotest_idle_B_{suffix}")["id"]
    yield str(a), str(b)
    for cid in (a, b):
        try:
            conversation_api.delete_conversation(cid)
        except Exception as exc:  # cleanup must not mask the verdict
            logger.warning("Cleanup failed for conversation %s: %s", cid, exc)


@allure.epic("Chat")
@allure.feature("Chat runs continue in background")
class TestAskUserWhileAway:
    """ELITEA-4955 — Ask User question reached while away (#7385)."""

    @pytest.mark.tms("ELITEA-4955")
    @allure.title("An Ask User question reached while away waits on the chat row and can be answered on return")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/chat-runs-continue-in-background/"
        "ELITEA-4955_an-ask-user-question-reached-while-away-waits-on-the-chat-ro.md",
        "onetest-ai Test Case link",
    )
    def test_ask_user_while_away(
        self, page, ask_user_agent, ask_conversations, conversation_api: ConversationAPI
    ):
        chat = ChatPage(page)
        conv_a, conv_b = ask_conversations
        agent = ask_user_agent

        with allure.step("Step 1 — In A send the message and click B during the wait: B opens, no dialog"):
            chat.navigate_to_chat(conversation_id=conv_a)
            chat.dismiss_banner_if_present()
            chat.add_agent_participant_by_id(settings.elitea_project_id, agent["id"], agent["name"])
            chat.expand_participants_panel_via_toggle()
            expect(chat.switch_participant_button).to_contain_text(agent["name"], timeout=UI_TIMEOUT)
            chat.send_message(_MESSAGE)
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)
            chat.click_conversation_item(conv_b)
            expect(page).to_have_url(re.compile(rf"/chat/{conv_b}(\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.open_dialogs).to_have_count(0)

        with allure.step("Step 2 — The run pauses; A's row shows the waiting dot 'Waiting for your answer'"):
            badge = chat.get_conversation_unread_badge(conv_a)
            expect(badge).to_have_count(1, timeout=PAUSE_CEILING_MS)
            expect(badge).to_have_attribute("data-reason", "waiting")
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0)
            expect(badge).to_have_attribute("aria-label", "Waiting for your answer")

        with allure.step("Step 3 — Open A: the Clarifying Question card is shown and enabled"):
            chat.click_conversation_item(conv_a)
            expect(chat.get_clarify_text(_QUESTION).last).to_be_visible(timeout=UI_TIMEOUT)
            for option in ("Post 1", "Post 2"):
                expect(chat.get_clarify_text(option).last).to_be_visible()
            expect(chat.clarify_skip_button).to_be_enabled()

        with allure.step("Step 4 — Pick Post 2 and Continue: the run resumes and A's row spins again"):
            chat.answer_clarifying_question("Post 2")
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)

        with allure.step("Step 5 — Wait for the end: ASK-DONE post 2 with Leanne Graham; 4 tool steps"):
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0, timeout=RUN_CEILING_MS)
            expect(chat.messages_container.last).to_contain_text("ASK-DONE post 2", timeout=UI_TIMEOUT)
            expect(chat.messages_container.last).to_contain_text("Leanne Graham")
            rows = conversation_api.get_message_traces(int(conv_a))["rows"]
            tools = [r["tool_name"] for r in rows if r.get("kind") == "tool_call"]
            assert tools == _EXPECTED_TOOLS, f"message_traces tool_call rows {tools}"
            assert conversation_api.has_running_task(conv_a) is False, "has_running_task still True after the run"
