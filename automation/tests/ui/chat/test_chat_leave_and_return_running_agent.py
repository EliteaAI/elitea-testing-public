"""UI Test for ELITEA-4953 — leave a running agent chat, return during the run and after it ends.

Leaving a running chat must not stop the run (no dialog, no DELETE /task), the chat list shows a
"Generating…" spinner on the running row, returning mid-run shows the finished steps plus the
"Agent is running…" bubble, and after the run ends the final answer, the 5 tool steps and the server
traces agree. Self-provisioning: toolkits, agent and the two conversations are created per run.

Known defect: elitea_issues#7763 — restored/late tool chips lose the tool name until the run ends;
soft-asserted. The Stop button IS present after returning mid-run (hard assertion, question #3052).

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

_WORD = "SMK1"
_MESSAGE = f"The word is {_WORD}."
_EXPECTED_TOOLS = ["waitSeconds", "getPost", "waitSeconds", "getUser", "waitSeconds"]
RUN_CEILING_MS = 90_000
UI_TIMEOUT = 15_000


@pytest.fixture
def two_conversations(conversation_api: ConversationAPI):
    """Fresh conversation A (run) and idle B (switch target); both deleted afterwards."""
    suffix = uuid.uuid4().hex[:6]
    a = conversation_api.create_conversation(f"autotest_run_A_{suffix}")["id"]
    b = conversation_api.create_conversation(f"autotest_idle_B_{suffix}")["id"]
    try:
        yield str(a), str(b)
    finally:
        for cid in (a, b):
            stop_and_delete_conversation(conversation_api, cid)
        warn_conversation_leftovers(conversation_api, (a, b))  # Teardown step 5 (log only)


@allure.epic("Chat")
@allure.feature("Chat runs continue in background")
class TestLeaveAndReturnToRunningAgentChat:
    """ELITEA-4953 — core #7385 journey."""

    @pytest.mark.tms("ELITEA-4953")
    @allure.title("Leave a running agent chat, return mid-run and after the run ends")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/chat-runs-continue-in-background/"
        "ELITEA-4953_switch-chats-during-an-agent-run-come-back-during-the-run-an.md",
        "onetest-ai Test Case link",
    )
    def test_leave_and_return_to_running_agent_chat(
        self, page, long_runner_agent, two_conversations, conversation_api: ConversationAPI
    ):
        chat = ChatPage(page)
        conv_a, conv_b = two_conversations
        project_id = settings.elitea_project_id
        soft_failures: list[str] = []

        with allure.step("Step 1 — Open A, add the agent, send the message; run starts with a first tool step"):
            chat.navigate_to_chat(conversation_id=conv_a)
            chat.dismiss_banner_if_present()
            chat.add_agent_participant_by_id(project_id, long_runner_agent["id"], long_runner_agent["name"])
            chat.expand_participants_panel_via_toggle()
            expect(chat.get_participant_rows()).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.switch_participant_button).to_contain_text(long_runner_agent["name"], timeout=UI_TIMEOUT)
            delete_requests = chat.start_recording_delete_requests()
            chat.send_message(_MESSAGE)
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.answer_tool_chip.first).to_be_visible(timeout=30_000)
            assert conversation_api.has_running_task(conv_a) is True, "has_running_task should be True mid-run"

        with allure.step("Step 2 — Click B in the list: opens at once, no dialog, no DELETE /task"):
            chat.click_conversation_item(conv_b)
            expect(page).to_have_url(re.compile(rf"/chat/{conv_b}(\?|$)"), timeout=UI_TIMEOUT)
            expect(chat.messages_container).to_have_count(0)
            expect(chat.open_dialogs).to_have_count(0)
            assert delete_requests == [], f"Leaving a running chat sent DELETE requests: {delete_requests}"

        with allure.step("Step 3 — A's row shows the running spinner with the 'Generating…' label"):
            expect(chat.get_conversation_running_icon(conv_a)).to_have_attribute(
                "aria-label", "Generating…", timeout=UI_TIMEOUT
            )

        with allure.step("Step 4 — Return to A mid-run: finished steps, 'Agent is running…', Stop"):
            chat.click_conversation_item(conv_a)
            expect(chat.get_agent_running_indicator()).to_be_visible(timeout=UI_TIMEOUT)
            expect(chat.answer_tool_chip.first).to_be_visible(timeout=UI_TIMEOUT)
            restored = chat.get_tool_chip_texts()
            assert restored, "No finished steps restored after returning mid-run"
            if not all(":" in t.split("·")[0] for t in restored):
                # Known defect: elitea_issues#7763 — restored chips lose the "<toolkit>: <tool>" name
                soft_failures.append(f"#7763 restored chips lack tool name: {restored}")
            expect(chat.get_composer_stop_button()).to_be_visible(timeout=UI_TIMEOUT)
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1)
            # Soft: a still-running step shows a spinner after the return (same #7763 family)
            try:
                expect(chat.get_running_step_spinner()).not_to_have_count(0, timeout=UI_TIMEOUT)
            except AssertionError:
                # Known defect: elitea_issues#7763 — restored run view loses the running step's spinner
                soft_failures.append("#7763 no running-step spinner after returning mid-run")

        with allure.step("Step 5 — Stay in A: steps appear live and the answer ends with RUN-DONE SMK1"):
            restored_count = len(restored)
            # Live steps: while the run is still going, the chip count grows beyond what was restored on return
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1)
            chat.wait_for_tool_chip_count_above(restored_count, timeout=RUN_CEILING_MS)
            assert chat.get_conversation_running_icon(conv_a).count() == 1, "run ended before late steps were observed live"
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0, timeout=RUN_CEILING_MS)
            expect(chat.get_agent_running_indicator()).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.get_running_step_spinner()).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.get_composer_stop_button()).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.messages_container.last).to_contain_text(f"RUN-DONE {_WORD}", timeout=UI_TIMEOUT)
            expect(chat.answer_tool_chip).to_have_count(len(_EXPECTED_TOOLS), timeout=UI_TIMEOUT)
            final_chips = chat.get_tool_chip_texts()
            names = [c.split("·")[0].split(":")[-1].strip() for c in final_chips]
            if all(":" in c.split("·")[0] for c in final_chips):
                assert names == _EXPECTED_TOOLS, f"final chip tool names {names}"
            else:
                # Known defect: elitea_issues#7763 — chips lack "<toolkit>: <tool>" names
                soft_failures.append(f"#7763 final chips lack tool name: {final_chips}")

        with allure.step("Step 6 — Open B then A: final answer, 5 steps, no spinner, no streaming indicator"):
            chat.click_conversation_item(conv_b)
            expect(chat.messages_container).to_have_count(0, timeout=UI_TIMEOUT)
            chat.click_conversation_item(conv_a)
            expect(chat.messages_container.last).to_contain_text(f"RUN-DONE {_WORD}", timeout=UI_TIMEOUT)
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0)
            expect(chat.get_agent_running_indicator()).to_have_count(0)
            chat.expand_thought_accordion()
            expect(chat.answer_tool_chip).to_have_count(len(_EXPECTED_TOOLS), timeout=UI_TIMEOUT)
            ui_names = [c.split("·")[0].split(":")[-1].strip() for c in chat.get_tool_chip_texts()]

        with allure.step("Step 7 — message_traces oracle: 5 tool_call rows in UI order; run closed server-side"):
            rows = conversation_api.get_message_traces(int(conv_a))["rows"]
            tool_rows = [r["tool_name"] for r in rows if r.get("kind") == "tool_call"]
            assert tool_rows == _EXPECTED_TOOLS, f"message_traces tool_call rows {tool_rows}"
            assert ui_names == tool_rows, f"UI chips {ui_names} != traces {tool_rows}"
            groups = conversation_api.get_message_groups(int(conv_a))
            assert groups[-1].get("is_streaming") is False, "final message group still streaming"
            assert conversation_api.has_running_task(conv_a) is False, "has_running_task still True after the run"

        if soft_failures:
            pytest.fail("; ".join(soft_failures))
