"""UI Test for ELITEA-4956 — send in a brand-new chat and switch to another chat at once.

Leaving before the first chunk races the chat creation: the chat must still be created and listed with
the running spinner, the user must stay on the chat they clicked (no dialog, no DELETE), and the run must
complete with the final answer. Self-provisioning: agent + toolkits (shared fixture) and idle chat B.

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

_WORD = "SMK4"
_MESSAGE = f"The word is {_WORD}."
_EXPECTED_TOOLS = ["waitSeconds", "getPost", "waitSeconds", "getUser", "waitSeconds"]
RUN_CEILING_MS = 90_000
UI_TIMEOUT = 15_000
LIST_LIMIT = 100  # the API pages ungrouped chats by 10 unless asked


def _unlink_quietly(fn, what: str) -> None:
    try:
        fn()
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("Cleanup failed for %s: %s", what, exc)


def _conversation_ids(conversation_api: ConversationAPI) -> set[str]:
    return {str(r["id"]) for r in conversation_api.list_conversations(limit=LIST_LIMIT).get("rows", [])}


def _stop_and_delete(conversation_api: ConversationAPI, cid: str) -> None:
    """Best-effort teardown of one conversation: stop a still-running task first, then delete."""
    try:
        if conversation_api.has_running_task(int(cid)):  # test failed midway: stop the run first
            conversation_api.stop_running_task(int(cid))
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("Could not stop the run of conversation %s: %s", cid, exc)
    _unlink_quietly(lambda: conversation_api.delete_conversation(int(cid)), f"conversation {cid}")


@pytest.fixture
def idle_conversation_b(conversation_api: ConversationAPI):
    """Idle conversation B (the switch target) plus cleanup of the UI-created chat."""
    suffix = uuid.uuid4().hex[:6]
    b = str(conversation_api.create_conversation(f"autotest_idle_B_{suffix}")["id"])
    before = _conversation_ids(conversation_api)
    created: list[str] = []
    yield b, created
    # the chat made by the UI has a client-side id first; sweep whatever the server listed since
    try:
        created.extend(sorted(_conversation_ids(conversation_api) - before))
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("New-chat sweep failed: %s", exc)
    targets = list(dict.fromkeys([b, *created]))
    for cid in targets:
        _stop_and_delete(conversation_api, cid)
    try:  # Teardown step 5: none of them may still be listed
        for cid in targets:
            if conversation_api.has_conversation(int(cid)):
                logger.warning("Teardown leftover: conversation %s is still listed", cid)
    except Exception as exc:
        logger.warning("Teardown leftover check failed: %s", exc)


@allure.epic("Chat")
@allure.feature("Chat runs continue in background")
class TestSendInNewChatAndSwitchAway:
    """ELITEA-4956 — #7385 race: switch away right after Send in a new chat."""

    @pytest.mark.tms("ELITEA-4956")
    @allure.title("Send in a new chat and switch to another chat at once")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/chat-runs-continue-in-background/"
        "ELITEA-4956_send-in-a-new-chat-and-switch-to-another-chat-at-once.md",
        "onetest-ai Test Case link",
    )
    def test_send_in_new_chat_and_switch_away_at_once(
        self, page, long_runner_agent, idle_conversation_b, conversation_api: ConversationAPI
    ):
        chat = ChatPage(page)
        conv_b, created = idle_conversation_b

        with allure.step("Step 1 — New chat, pick the agent with '#', type the message; agent is the participant"):
            chat.navigate_to_chat(conversation_id=conv_b)
            chat.dismiss_banner_if_present()
            ids_before = chat.get_conversation_item_ids()
            chat.start_new_chat_with_agent_by_hash(long_runner_agent["name"])
            expect(chat.switch_participant_button).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.switch_participant_button).to_contain_text(long_runner_agent["name"])
            chat.message_input.click()
            chat.message_input.press_sequentially(_MESSAGE)
            expect(chat.send_button).to_be_visible(timeout=UI_TIMEOUT)

        with allure.step("Step 2 — Send and click B in the same browser task: B opens, user stays on B"):
            delete_requests = chat.start_recording_delete_requests()
            chat.send_and_open_conversation_at_once(conv_b)
            expect(page).to_have_url(re.compile(rf"/chat/{conv_b}(\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.open_dialogs).to_have_count(0)
            assert delete_requests == [], f"Switching away sent DELETE requests: {delete_requests}"

        with allure.step("Step 3 — The new chat is listed with the running spinner"):
            expect(chat.get_conversation_item_rows()).to_have_count(len(ids_before) + 1, timeout=UI_TIMEOUT)
            # the chat now exists server-side: the user must not have been pulled back to it
            expect(page).to_have_url(re.compile(rf"/chat/{conv_b}(\?|$)"))
            running_row = chat.get_running_conversation_rows()
            expect(running_row).to_have_count(1, timeout=UI_TIMEOUT)
            new_id = (running_row.get_attribute("data-testid") or "").removeprefix("chat-conversation-item-")
            assert new_id and new_id not in ids_before and new_id != conv_b, f"running row is not the new chat: {new_id}"
            expect(chat.get_conversation_running_icon(new_id)).to_have_attribute(
                "aria-label", "Generating…", timeout=UI_TIMEOUT
            )

        with allure.step("Step 4 — After the run ends, open the new chat: user message and RUN-DONE SMK4"):
            expect(running_row).to_have_count(0, timeout=RUN_CEILING_MS)
            # the row may be re-keyed (client id -> server id) when the run ends: re-resolve the new row
            new_ids = chat.get_conversation_item_ids() - ids_before
            assert len(new_ids) == 1, f"expected exactly one new chat row, got {new_ids}"
            new_id = new_ids.pop()
            chat.click_conversation_item(new_id)
            expect(page).to_have_url(re.compile(rf"/chat/{new_id}(\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.messages_container).to_have_count(2, timeout=UI_TIMEOUT)
            expect(chat.messages_container.first).to_contain_text(_MESSAGE, timeout=UI_TIMEOUT)
            expect(chat.messages_container.last).to_contain_text(f"RUN-DONE {_WORD}", timeout=UI_TIMEOUT)

        with allure.step("Step 5 — API oracle: 5 tool_call traces, no running task, not streaming"):
            rows = conversation_api.get_message_traces(int(new_id))["rows"]
            tool_rows = [r["tool_name"] for r in rows if r.get("kind") == "tool_call"]
            assert tool_rows == _EXPECTED_TOOLS, f"message_traces tool_call rows {tool_rows}"
            groups = conversation_api.get_message_groups(int(new_id))
            assert groups[-1].get("is_streaming") is False, "final message group still streaming"
            assert conversation_api.has_running_task(int(new_id)) is False, "has_running_task still True after the run"
