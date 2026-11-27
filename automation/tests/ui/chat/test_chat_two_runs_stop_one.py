"""UI Test for ELITEA-4957 — two chats run at once; Stop in one leaves the other running.

Both rows show the running spinner; Stop in C sends exactly one DELETE /task for C's run uuid only,
C's spinner and Stop button go away, A keeps running and finishes with its own answer.
Self-provisioning: toolkits, agent and the two conversations are created per run.

Markers: ui, chat, p0 (AFS l1 == TMS critical), regression.
"""

import logging
import re
import uuid

import allure
import pytest
from playwright.sync_api import expect

from api import ConversationAPI
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

_WORD_A = "SMK5A"
_WORD_C = "SMK5C"
RUN_CEILING_MS = 90_000
UI_TIMEOUT = 15_000


def _unlink_quietly(fn, what: str) -> None:
    try:
        fn()
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("Cleanup failed for %s: %s", what, exc)


@pytest.fixture
def two_run_conversations(conversation_api: ConversationAPI, long_runner_agent):
    """Fresh conversations A and C, each with the agent pre-attached by API; both deleted afterwards."""
    suffix = uuid.uuid4().hex[:6]
    a = conversation_api.create_conversation(f"autotest_run_A_{suffix}")["id"]
    c = conversation_api.create_conversation(f"autotest_run_C_{suffix}")["id"]
    try:
        for cid in (a, c):
            conversation_api.add_agent_participant(cid, long_runner_agent["id"])
        yield str(a), str(c)
    finally:
        for cid in (a, c):
            _unlink_quietly(lambda x=cid: conversation_api.delete_conversation(x), f"conversation {cid}")


@allure.epic("Chat")
@allure.feature("Chat runs continue in background")
class TestTwoChatsRunStopOneLeavesOther:
    """ELITEA-4957 — #7385: runs in different chats are independent."""

    @pytest.mark.tms("ELITEA-4957")
    @allure.title("Two chats run at once and Stop in one leaves the other running")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/chat-runs-continue-in-background/"
        "ELITEA-4957_two-chats-run-at-once-and-stop-in-one-leaves-the-other-runni.md",
        "onetest-ai Test Case link",
    )
    def test_two_chats_run_stop_one_leaves_other(
        self, page, long_runner_agent, two_run_conversations, conversation_api: ConversationAPI
    ):
        chat = ChatPage(page)
        conv_a, conv_c = two_run_conversations
        agent_name = long_runner_agent["name"]

        with allure.step("Step 1 — Send in A, open C and send there: both rows show the running spinner"):
            # the socket opens during navigation: the recorder must be attached first
            frames = chat.start_recording_run_status_frames()
            delete_requests = chat.start_recording_delete_requests()
            chat.navigate_to_chat(conversation_id=conv_a)
            chat.dismiss_banner_if_present()
            chat.activate_agent_participant(agent_name)
            chat.send_message(f"The word is {_WORD_A}.")
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)
            chat.click_conversation_item(conv_c)
            expect(page).to_have_url(re.compile(rf"/chat/{conv_c}(\?|$)"), timeout=UI_TIMEOUT)
            chat.activate_agent_participant(agent_name)
            chat.send_message(f"The word is {_WORD_C}.")
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.get_conversation_running_icon(conv_c)).to_have_count(1, timeout=UI_TIMEOUT)

        with allure.step("Step 2 — In C wait for the first step and click Stop: one DELETE /task for C's run only"):
            expect(chat.answer_tool_chip.first).to_be_visible(timeout=30_000)
            expect(chat.get_composer_stop_button()).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.get_agent_running_indicator()).to_be_visible(timeout=UI_TIMEOUT)
            c_running = [f for f in frames if str(f.get("conversation_id")) == conv_c and f.get("status") == "running"]
            assert c_running, f"no chat_run_status 'running' frame seen for C: {frames}"
            c_run_uuid = c_running[-1]["message_group_uuid"]
            chat.get_composer_stop_button().click()
            expect(chat.get_composer_stop_button()).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.get_conversation_running_icon(conv_c)).to_have_count(0, timeout=UI_TIMEOUT)
            task_deletes = [u for u in delete_requests if "/task/" in u]
            assert len(task_deletes) == 1, f"expected exactly one DELETE /task, got {task_deletes}"
            assert task_deletes[0].rstrip("/").endswith(f"/{c_run_uuid}"), (
                f"DELETE /task is not for C's run {c_run_uuid}: {task_deletes[0]}"
            )
            a_uuids = {
                str(f.get("message_group_uuid"))
                for f in frames
                if str(f.get("conversation_id")) == conv_a
            }
            assert not any(u.rstrip("/").endswith(f"/{x}") for u in task_deletes for x in a_uuids), (
                f"DELETE /task targeted A's run: {task_deletes} vs {a_uuids}"
            )
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1)
            assert conversation_api.has_running_task(conv_a) is True, "A's run should still be running"
            assert conversation_api.has_running_task(conv_c) is False, "C's run should be stopped"

        with allure.step("Step 3 — Open A: it is still running (Stop and 'Agent is running…')"):
            chat.click_conversation_item(conv_a)
            expect(page).to_have_url(re.compile(rf"/chat/{conv_a}(\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.get_agent_running_indicator()).to_be_visible(timeout=UI_TIMEOUT)
            expect(chat.get_composer_stop_button()).to_have_count(1, timeout=UI_TIMEOUT)

        with allure.step("Step 4 — Wait for A to end: answer RUN-DONE SMK5A, A never deleted"):
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0, timeout=RUN_CEILING_MS)
            expect(chat.messages_container.last).to_contain_text(f"RUN-DONE {_WORD_A}", timeout=UI_TIMEOUT)
            task_deletes = [u for u in delete_requests if "/task/" in u]
            assert len(task_deletes) == 1, f"A's run was deleted too: {task_deletes}"
            assert conversation_api.has_running_task(conv_a) is False, "has_running_task still True for A"
            groups = conversation_api.get_message_groups(int(conv_a))
            assert groups[-1].get("is_streaming") is False, "A's final message group still streaming"
            rows = conversation_api.get_message_traces(int(conv_a))["rows"]
            tool_rows = [r for r in rows if r.get("kind") == "tool_call"]
            assert len(tool_rows) == 5, f"A's message_traces tool_call rows: {len(tool_rows)}"
