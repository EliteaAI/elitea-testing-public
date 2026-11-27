"""UI Test for ELITEA-4953 — leave a running agent chat, return during the run and after it ends.

Leaving a running chat must not stop the run (no dialog, no DELETE /task), the chat list shows a
"Generating…" spinner on the running row, returning mid-run shows the finished steps plus the
"Agent is running…" bubble, and after the run ends the final answer, the 5 tool steps and the server
traces agree. Self-provisioning: toolkits, agent and the two conversations are created per run.

Known defect: elitea_issues#7763 — restored/late tool chips lose the tool name until the run ends;
also the Stop button is absent after returning mid-run. Both are soft-asserted.

Markers: ui, chat, p0 (AFS l1 == TMS critical), regression.
"""

import logging
import uuid
from pathlib import Path

import allure
import pytest
from playwright.sync_api import expect

from api import AgentAPI, ConversationAPI, ToolkitAPI
from api.client import _default_llm_settings
from config import settings
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

_DATA_DIR = Path(__file__).resolve().parents[4] / "test-data" / "chat-runs-continue"
_WORD = "SMK1"
_MESSAGE = f"The word is {_WORD}."
_EXPECTED_TOOLS = ["waitSeconds", "getPost", "waitSeconds", "getUser", "waitSeconds"]
RUN_CEILING_MS = 90_000
UI_TIMEOUT = 15_000


def _unlink_quietly(fn, what: str) -> None:
    try:
        fn()
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("Cleanup failed for %s: %s", what, exc)


@pytest.fixture
def long_runner_agent(agent_api: AgentAPI, toolkit_api: ToolkitAPI):
    """R7385LongRunner agent with the two OpenAPI toolkits linked; deleted afterwards."""
    suffix = uuid.uuid4().hex[:6]
    created_toolkits: list[int] = []
    agent_id = None
    try:
        echo = toolkit_api.create_toolkit(
            f"autotest_echo_{suffix}", "Postman Echo delay (ELITEA-4953)", "openapi",
            {
                "spec": (_DATA_DIR / "postman-echo-delay.openapi.yaml").read_text(),
                "selected_tools": ["waitSeconds"],
                "openapi_configuration": {"private": True, "elitea_title": ""},
            },
        )
        created_toolkits.append(echo["id"])
        jph = toolkit_api.create_toolkit(
            f"autotest_jph_{suffix}", "JSONPlaceholder (ELITEA-4953)", "openapi",
            {
                "spec": (_DATA_DIR / "jsonplaceholder.openapi.yaml").read_text(),
                "selected_tools": ["getPost", "getUser"],
                "openapi_configuration": {"private": True, "elitea_title": ""},
            },
        )
        created_toolkits.append(jph["id"])

        llm = _default_llm_settings()
        llm["reasoning_effort"] = "low"
        name = f"autotest_runner_{suffix}"
        agent = agent_api.create_agent_full({
            "name": name,
            "description": "Long-running fixture agent for ELITEA-4953",
            "type": "interface",
            "versions": [{
                "name": "base", "tags": [],
                "instructions": (_DATA_DIR / "r7385-longrunner.instructions.md").read_text(),
                "variables": [], "tools": [], "llm_settings": llm,
                "conversation_starters": [], "agent_type": "openai", "welcome_message": "",
                "meta": {"step_limit": 25},
            }],
        })
        agent_id = agent["id"]
        version_id = agent["version_details"]["id"] if "version_details" in agent else agent["versions"][0]["id"]
        toolkit_api.link_toolkit_to_agent(echo["id"], agent_id, version_id, ["waitSeconds"])
        toolkit_api.link_toolkit_to_agent(jph["id"], agent_id, version_id, ["getPost", "getUser"])
        yield {"id": agent_id, "name": name}
    finally:
        if agent_id is not None:
            _unlink_quietly(lambda: agent_api.delete_agent(agent_id), f"agent {agent_id}")
        for tid in created_toolkits:
            _unlink_quietly(lambda t=tid: toolkit_api.delete_toolkit(t), f"toolkit {tid}")


@pytest.fixture
def two_conversations(conversation_api: ConversationAPI):
    """Fresh conversation A (run) and idle B (switch target); both deleted afterwards."""
    suffix = uuid.uuid4().hex[:6]
    a = conversation_api.create_conversation(f"autotest_run_A_{suffix}")["id"]
    b = conversation_api.create_conversation(f"autotest_idle_B_{suffix}")["id"]
    yield str(a), str(b)
    for cid in (a, b):
        _unlink_quietly(lambda c=cid: conversation_api.delete_conversation(c), f"conversation {cid}")


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
            expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(1, timeout=UI_TIMEOUT)
            delete_requests = chat.start_recording_delete_requests()
            chat.send_message(_MESSAGE)
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1, timeout=UI_TIMEOUT)
            expect(chat.chat_inject_button).to_be_visible(timeout=UI_TIMEOUT)
            expect(chat.answer_tool_chip.first).to_be_visible(timeout=30_000)
            assert conversation_api.has_running_task(conv_a) is True, "has_running_task should be True mid-run"

        with allure.step("Step 2 — Click B in the list: opens at once, no dialog, no DELETE /task"):
            chat.click_conversation_item(conv_b)
            expect(page).to_have_url(f"{settings.elitea_url}{settings.app_prefix}/chat/{conv_b}", timeout=UI_TIMEOUT)
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
            if chat.chat_inject_button.count() == 0:
                # Known defect: elitea_issues#7763 (area) — Stop absent after returning mid-run
                soft_failures.append("#7763 Stop button absent after returning to the running chat")
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(1)

        with allure.step("Step 5 — Stay in A: steps appear live and the answer ends with RUN-DONE SMK1"):
            expect(chat.get_conversation_running_icon(conv_a)).to_have_count(0, timeout=RUN_CEILING_MS)
            expect(chat.get_agent_running_indicator()).to_have_count(0, timeout=UI_TIMEOUT)
            expect(chat.messages_container.last).to_contain_text(f"RUN-DONE {_WORD}", timeout=UI_TIMEOUT)
            expect(chat.answer_tool_chip).to_have_count(len(_EXPECTED_TOOLS), timeout=UI_TIMEOUT)
            final_chips = chat.get_tool_chip_texts()
            names = [c.split("·")[0].split(":")[-1].strip() for c in final_chips]
            if not all(":" in c.split("·")[0] for c in final_chips):
                # Known defect: elitea_issues#7763
                soft_failures.append(f"#7763 final chips lack tool name: {final_chips}")
            assert names == _EXPECTED_TOOLS or not all(":" in c for c in final_chips)

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
