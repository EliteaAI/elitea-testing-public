"""Shared chat-run fixtures (ELITEA-4953 / ELITEA-4956): the R7385LongRunner agent.

Self-provisioning: two OpenAPI toolkits + an agent are created per test and deleted afterwards.
"""

import logging
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from api import AgentAPI, ToolkitAPI
from api.client import _default_llm_settings

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[2] / "test-data" / "chat-runs-continue"


def _unlink_quietly(fn, what: str) -> None:
    try:
        fn()
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("Cleanup failed for %s: %s", what, exc)


def stop_and_delete_conversation(conversation_api, cid) -> None:
    """Best-effort teardown of one conversation: stop a still-running task first, then delete (never raises)."""
    try:
        if conversation_api.has_running_task(int(cid)):  # test failed midway: stop the run first
            conversation_api.stop_running_task(int(cid))
    except Exception as exc:  # cleanup must not mask the test verdict
        logger.warning("Could not stop the run of conversation %s: %s", cid, exc)
    _unlink_quietly(lambda: conversation_api.delete_conversation(cid), f"conversation {cid}")


def warn_conversation_leftovers(conversation_api, cids) -> None:
    """Log (warning) any of *cids* still listed after teardown; never raises."""
    try:
        for cid in cids:
            if conversation_api.has_conversation(int(cid)):
                logger.warning("Teardown leftover: conversation %s is still listed", cid)
    except Exception as exc:  # the check must not mask the test verdict
        logger.warning("Teardown leftover check failed: %s", exc)


def _list_ids(fn) -> set[str]:
    data = fn()
    rows = data.get("rows", []) if isinstance(data, dict) else data
    return {str(r.get("id")) for r in rows}


@contextmanager
def _provisioned_agent(
    agent_api: AgentAPI,
    toolkit_api: ToolkitAPI,
    *,
    tag: str,
    name_prefix: str,
    description: str,
    instructions_file: str,
    internal_tools: list[str] | None = None,
):
    """Create the two OpenAPI toolkits + an agent linking them; delete all of it afterwards.

    Teardown is best-effort (warnings only, never raises); after the deletes it logs any of the created
    entities that is still listed (ELITEA-4955 Teardown step 5).
    """
    suffix = uuid.uuid4().hex[:6]
    created_toolkits: list[int] = []
    agent_id = None
    try:
        echo = toolkit_api.create_toolkit(
            f"autotest_echo_{suffix}", f"Postman Echo delay ({tag})", "openapi",
            {
                "spec": (_DATA_DIR / "postman-echo-delay.openapi.yaml").read_text(),
                "selected_tools": ["waitSeconds"],
                "openapi_configuration": {"private": True, "elitea_title": ""},
            },
        )
        created_toolkits.append(echo["id"])
        jph = toolkit_api.create_toolkit(
            f"autotest_jph_{suffix}", f"JSONPlaceholder ({tag})", "openapi",
            {
                "spec": (_DATA_DIR / "jsonplaceholder.openapi.yaml").read_text(),
                "selected_tools": ["getPost", "getUser"],
                "openapi_configuration": {"private": True, "elitea_title": ""},
            },
        )
        created_toolkits.append(jph["id"])

        llm = _default_llm_settings()
        llm["reasoning_effort"] = "low"
        name = f"{name_prefix}_{suffix}"
        meta: dict = {"step_limit": 25}
        if internal_tools:
            meta["internal_tools"] = internal_tools
        agent = agent_api.create_agent_full({
            "name": name,
            "description": description,
            "type": "interface",
            "versions": [{
                "name": "base", "tags": [],
                "instructions": (_DATA_DIR / instructions_file).read_text(),
                "variables": [], "tools": [], "llm_settings": llm,
                "conversation_starters": [], "agent_type": "openai", "welcome_message": "",
                "meta": meta,
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
        _warn_leftovers(agent_api, toolkit_api, agent_id, created_toolkits)


def _warn_leftovers(agent_api: AgentAPI, toolkit_api: ToolkitAPI, agent_id, toolkit_ids: list[int]) -> None:
    """Log (warning) any created agent / toolkit still listed after teardown; never raises."""
    try:
        if agent_id is not None and str(agent_id) in _list_ids(agent_api.list_agents):
            logger.warning("Teardown leftover: agent %s is still listed", agent_id)
        if toolkit_ids:
            listed = _list_ids(toolkit_api.list_all_toolkits)
            for tid in toolkit_ids:
                if str(tid) in listed:
                    logger.warning("Teardown leftover: toolkit %s is still listed", tid)
    except Exception as exc:  # the check must not mask the test verdict
        logger.warning("Teardown leftover check failed: %s", exc)


@pytest.fixture
def long_runner_agent(agent_api: AgentAPI, toolkit_api: ToolkitAPI):
    """R7385LongRunner agent with the two OpenAPI toolkits linked; deleted afterwards."""
    with _provisioned_agent(
        agent_api, toolkit_api,
        tag="ELITEA-4953", name_prefix="autotest_runner",
        description="Long-running fixture agent for ELITEA-4953",
        instructions_file="r7385-longrunner.instructions.md",
    ) as agent:
        yield agent


@pytest.fixture
def ask_user_agent(agent_api: AgentAPI, toolkit_api: ToolkitAPI):
    """R7385AskUser agent (waits 10 s, asks which post, answers ASK-DONE) with Ask User on (ELITEA-4955)."""
    with _provisioned_agent(
        agent_api, toolkit_api,
        tag="ELITEA-4955", name_prefix="autotest_askuser",
        description="Ask User fixture agent for ELITEA-4955",
        instructions_file="r7385-askuser.instructions.md",
        internal_tools=["ask_user"],
    ) as agent:
        yield agent
