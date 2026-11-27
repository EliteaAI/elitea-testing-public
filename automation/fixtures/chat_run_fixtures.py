"""Shared chat-run fixtures (ELITEA-4953 / ELITEA-4956): the R7385LongRunner agent.

Self-provisioning: two OpenAPI toolkits + an agent are created per test and deleted afterwards.
"""

import logging
import uuid
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
def ask_user_agent(agent_api: AgentAPI, toolkit_api: ToolkitAPI):
    """R7385AskUser agent (waits 10 s, asks which post, answers ASK-DONE) with Ask User on (ELITEA-4955)."""
    suffix = uuid.uuid4().hex[:6]
    created_toolkits: list[int] = []
    agent_id = None
    try:
        echo = toolkit_api.create_toolkit(
            f"autotest_echo_{suffix}", "Postman Echo delay (ELITEA-4955)", "openapi",
            {
                "spec": (_DATA_DIR / "postman-echo-delay.openapi.yaml").read_text(),
                "selected_tools": ["waitSeconds"],
                "openapi_configuration": {"private": True, "elitea_title": ""},
            },
        )
        created_toolkits.append(echo["id"])
        jph = toolkit_api.create_toolkit(
            f"autotest_jph_{suffix}", "JSONPlaceholder (ELITEA-4955)", "openapi",
            {
                "spec": (_DATA_DIR / "jsonplaceholder.openapi.yaml").read_text(),
                "selected_tools": ["getPost", "getUser"],
                "openapi_configuration": {"private": True, "elitea_title": ""},
            },
        )
        created_toolkits.append(jph["id"])

        llm = _default_llm_settings()
        llm["reasoning_effort"] = "low"
        name = f"autotest_askuser_{suffix}"
        agent = agent_api.create_agent_full({
            "name": name,
            "description": "Ask User fixture agent for ELITEA-4955",
            "type": "interface",
            "versions": [{
                "name": "base", "tags": [],
                "instructions": (_DATA_DIR / "r7385-askuser.instructions.md").read_text(),
                "variables": [], "tools": [], "llm_settings": llm,
                "conversation_starters": [], "agent_type": "openai", "welcome_message": "",
                "meta": {"step_limit": 25, "internal_tools": ["ask_user"]},
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
