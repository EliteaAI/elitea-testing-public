"""UI Test for ELITEA-4954 — leave a running chat four ways, then see the "New response" dot.

New chat, Agents (left menu), browser Back and Artifacts must each open at once with no dialog, no leave-guard
text and no DELETE /task; the run keeps going and, ending while the user is away, marks A's row with the
"New response" dot, which clears when A is opened. Self-provisioning: toolkits, agent and conversation A per run.

Markers: ui, chat, p0 (AFS l1 == TMS critical), regression.
"""

import re
import uuid

import allure
import pytest
from playwright.sync_api import expect

from api import ConversationAPI
from config import settings
from fixtures.chat_run_fixtures import stop_and_delete_conversation, warn_conversation_leftovers
from pages.chat_page import ChatPage

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

_WORD = "SMK2"
_MESSAGE = f"The word is {_WORD}."
_EXPECTED_TOOLS = ["waitSeconds", "getPost", "waitSeconds", "getUser", "waitSeconds"]
RUN_CEILING_MS = 90_000
UI_TIMEOUT = 15_000


@pytest.fixture
def run_conversation(conversation_api: ConversationAPI):
    """Fresh conversation A for the run; stopped (if still running) and deleted afterwards."""
    suffix = uuid.uuid4().hex[:6]
    a = conversation_api.create_conversation(f"autotest_run_A_{suffix}")["id"]
    try:
        yield str(a)
    finally:
        stop_and_delete_conversation(conversation_api, a)
        warn_conversation_leftovers(conversation_api, (a,))  # Teardown step 5 (log only)


@allure.epic("Chat")
@allure.feature("Chat runs continue in background")
class TestLeaveRunningChatNewResponseDot:
    """ELITEA-4954 — leave a running chat four ways, then the New response dot (#7385)."""

    @pytest.mark.tms("ELITEA-4954")
    @allure.title("Leave a running chat for New chat, Agents, Back and Artifacts, then see the New response dot")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/chat-runs-continue-in-background/"
        "ELITEA-4954_leave-a-running-chat-for-new-chat-agents-browser-back-and-ar.md",
        "onetest-ai Test Case link",
    )
    def test_leave_running_chat_four_ways_then_new_response_dot(
        self, page, long_runner_agent, run_conversation, conversation_api: ConversationAPI
    ):
        chat = ChatPage(page)
        conv_a = run_conversation
        agent = long_runner_agent
        dialogs: list[str] = []
        page.on("dialog", lambda d: dialogs.append(d.message))

        def assert_left_cleanly(delete_requests):
            expect(chat.open_dialogs).to_have_count(0)
            expect(chat.FORBIDDEN_LEAVE_TEXT_STILL_IN_PROGRESS).to_have_count(0)
            expect(chat.FORBIDDEN_LEAVE_TEXT_STILL_GENERATING).to_have_count(0)
            assert dialogs == [], f"native dialogs opened: {dialogs}"
            assert delete_requests == [], f"Leaving a running chat sent DELETE requests: {delete_requests}"

        with allure.step("Step 1 — In A, send the message and wait for the first step: the run is going"):
            chat.navigate_to_chat(conversation_id=conv_a)
            chat.dismiss_banner_if_present()
            chat.add_agent_participant_by_id(settings.elitea_project_id, agent["id"], agent["name"])
            chat.expand_participants_panel_via_toggle()
            expect(chat.get_participant_rows()).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.switch_participant_button).to_contain_text(agent["name"], timeout=UI_TIMEOUT)
            delete_requests = chat.start_recording_delete_requests()
            chat.send_message(_MESSAGE)
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.answer_tool_chip.first).to_be_visible(timeout=30_000)
            assert conversation_api.has_running_task(conv_a) is True, "has_running_task should be True mid-run"

        with allure.step("Step 2 — Click New chat: an empty chat opens at once, composer enabled"):
            chat.click_new_chat()
            expect(page).to_have_url(re.compile(r"/chat(\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.message_input).to_be_enabled(timeout=UI_TIMEOUT)
            assert_left_cleanly(delete_requests)

        with allure.step("Step 3 — Open Agents in the left menu: the Agents page opens at once"):
            chat.open_agents_from_menu()
            expect(page).to_have_url(re.compile(r"/agents(\?|$)"), timeout=UI_TIMEOUT)
            assert_left_cleanly(delete_requests)

        with allure.step("Step 4 — Browser Back, then Artifacts: each opens at once, no dialog or guard text"):
            page.go_back()
            expect(page).to_have_url(re.compile(r"/chat(/|\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.get_agent_running_indicator()).to_be_visible(timeout=UI_TIMEOUT)
            assert_left_cleanly(delete_requests)
            chat.open_artifacts_from_menu()
            expect(page).to_have_url(re.compile(r"/artifacts(/|\?|$)"), timeout=UI_TIMEOUT)
            assert_left_cleanly(delete_requests)

        with allure.step("Step 5 — Stay away until the run ends, return in-app: A's row shows the New response dot"):
            conv_id = int(conv_a)
            conversation_api.wait_until_run_ended(conv_id, timeout_s=RUN_CEILING_MS / 1000)
            chat.click_new_chat()
            expect(page).to_have_url(re.compile(r"/chat(\?|$)"), timeout=UI_TIMEOUT)
            chat.expand_sidebar_list()
            badge = chat.get_conversation_unread_badge(conv_a)
            expect(badge).to_have_count(1, timeout=UI_TIMEOUT)
            expect(badge).to_have_attribute("data-reason", "new_response")
            expect(badge).to_have_attribute("aria-label", "New response")
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0)

        with allure.step("Step 6 — Open A: answer RUN-DONE SMK2 and 5 steps; the dot is gone and stays gone"):
            chat.click_conversation_item(conv_a)
            expect(chat.get_conversation_unread_badge(conv_a)).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.messages_container.last).to_contain_text(f"RUN-DONE {_WORD}", timeout=UI_TIMEOUT)
            expect(chat.get_agent_running_indicator()).to_have_count(0)
            chat.expand_thought_accordion()
            expect(chat.answer_tool_chip).to_have_count(len(_EXPECTED_TOOLS), timeout=UI_TIMEOUT)
            rows = conversation_api.get_message_traces(conv_id)["rows"]
            tool_rows = [r["tool_name"] for r in rows if r.get("kind") == "tool_call"]
            assert tool_rows == _EXPECTED_TOOLS, f"message_traces tool_call rows {tool_rows}"
            groups = conversation_api.get_message_groups(conv_id)
            assert groups[-1].get("is_streaming") is False, "final message group still streaming"
            assert conversation_api.has_running_task(conv_a) is False
            chat.click_new_chat()
            chat.expand_sidebar_list()
            expect(chat.get_conversation_item(conv_a)).to_be_visible(timeout=UI_TIMEOUT)
            expect(chat.get_conversation_unread_badge(conv_a)).to_have_count(0)

