"""UI Tests for Agent + Toolkit execution in Chat.

Tests the end-to-end flow:
1. Create agent via API
2. Add toolkit to agent via AgentPage UI
3. Create conversation via API
4. Add agent as participant in ChatPage
5. Send message that triggers toolkit execution
6. Verify toolkit executes and returns data

This is the correct pattern — agent detail page chat is a preview mode.
Real toolkit execution happens in /chat with agent as participant.

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - toolkits: toolkit-related tests
    - p0: critical priority tests

Usage:
    cd automation
    pytest test_agent_with_toolkit_chat.py -v
"""

import logging
import re

import pytest

from api import AgentAPI
from config import settings
from pages.agent_page import AgentPage
from pages.chat_page import ChatPage
import allure

logger = logging.getLogger(__name__)

_ERROR_REPLY_RE = re.compile(
    r"(?i)\b(unable|cannot|can't|couldn't|could not|sorry|error|failed|don't have access|"
    r"no access|not authorized|unauthorized|forbidden|permission denied|rate limit)\b"
)

_ENTRY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/\-]*")


def _scan_listing_reply(text: str) -> tuple[list[str], list[str]]:
    """Split a reply into branch entries (single tokens) and error-looking prose lines."""
    entries: list[str] = []
    errors: list[str] = []
    for ln in text.splitlines():
        t = re.sub(r"^\s*(?:[-*\u2022]|\d+[.)])\s+", "", ln.strip())
        t = t.replace("`", "").replace("**", "").replace("|", " ").strip()
        t = re.sub(r"\s+\((?:default|protected)\)$", "", t, flags=re.I)
        if not t:
            continue
        if len(t.split()) == 1:
            if _ENTRY_RE.fullmatch(t):
                entries.append(t)
            continue
        m = _ERROR_REPLY_RE.search(t)
        if m:
            errors.append(f"matched '{m.group(0)}': {t[:200]}")
    return entries, errors


pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.toolkits, pytest.mark.p0]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000
TOOLKIT_EXECUTION_TIMEOUT = 60000


# ---------------------------------------------------------------------------
# Fixtures specific to this test module
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_with_toolkit_instructions(agent_api: AgentAPI, request):
    """Create an agent with instructions to use attached toolkits.

    Unlike the generic agent_id fixture, this agent has explicit instructions
    that tell it to always use available tools to fulfill requests, which is
    required for toolkit execution tests.
    """
    name = f"autotest_{request.node.name}"[:32]
    description = f"Agent with toolkit instructions for test {request.node.name}"
    instructions = """You are a helpful assistant with access to external tools.

IMPORTANT: When a user asks you to perform any task that involves external services
(like GitHub, Jira, etc.), you MUST use the available tools to fulfill the request.

Do NOT provide instructions on how to do things manually. Instead, use the tools
directly to perform the action and return the actual results.

For example:
- If asked to list branches, use the GitHub tool to get the actual branch list
- If asked about issues, use the appropriate tool to fetch real issue data
- Always execute tools rather than explaining how to use command line"""

    agent = agent_api.create_agent(name, description, instructions=instructions)
    aid = agent["id"]
    logger.info("Created toolkit-enabled agent %s (%s)", aid, name)

    yield aid

    try:
        agent_api.delete_agent(aid)
        logger.info("Deleted agent %s", aid)
    except Exception as exc:
        logger.warning("Failed to delete agent %s: %s", aid, exc)


# ===========================================================================
# Tests
# ===========================================================================


class TestAgentWithToolkitInChat:
    """Test agent + toolkit execution in real chat (not agent detail preview)."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-0143_agent-with-toolkits.md", "onetest-ai Test Case link")
    @pytest.mark.tms("ELITEA-0143")
    @pytest.mark.p0
    def test_agent_with_toolkit_executes_in_chat(
        self,
        page,
        agent_with_toolkit_instructions: int,
        github_toolkit: dict,
        conversation_id: str,
    ):
        """Create agent with toolkit, add agent as participant in chat, verify toolkit executes.

        The toolkit is attached to the agent (not the conversation directly).
        This tests the agent-owns-toolkit execution path in real chat (/chat).
        """
        toolkit_name = github_toolkit["name"]

        agent_id = agent_with_toolkit_instructions

        # ------------------------------------------------------------------
        # Step 1-3 — Navigate to agent; add GitHub toolkit; save
        # ------------------------------------------------------------------
        with allure.step("Step 1-3 — Navigate to agent; add GitHub toolkit; save"):
            agent_page = AgentPage(page)
            agent_page.navigate_to_agent(agent_id)
            agent_page.wait_for_agent_detail()

            logger.info("Adding toolkit '%s' to agent %d", toolkit_name, agent_id)
            agent_page.add_toolkit(toolkit_name)

            assert agent_page.is_toolkit_attached(toolkit_name), \
                f"Toolkit '{toolkit_name}' should be visible in agent config before save"

            agent_page.save_and_wait(timeout=FORM_SAVE_TIMEOUT)

            assert agent_page.is_toolkit_attached(toolkit_name), \
                f"Toolkit '{toolkit_name}' not attached to agent after save"

            logger.info("Re-loading agent %d to verify toolkit persistence...", agent_id)
            agent_page.navigate_to_agent(agent_id)
            assert agent_page.is_toolkit_attached(toolkit_name), (
                f"Toolkit '{toolkit_name}' should be attached to agent after re-load — "
                "save may not have persisted before navigating to chat"
            )
            logger.info("Toolkit '%s' confirmed persisted on agent %d", toolkit_name, agent_id)

        # ------------------------------------------------------------------
        # Step 4 — Navigate to conversation and let page settle
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Navigate to conversation and let page settle"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.wait_for_page_load()
            chat.wait_for_network(timeout=NAVIGATION_TIMEOUT)
            chat.wait_for_add_agent_button(NAVIGATION_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 5 — Add agent as participant
        # ------------------------------------------------------------------
        with allure.step("Step 5 — Add agent as participant"):
            logger.info("Adding agent as chat participant...")
            chat.add_agent_participant("autotest_", timeout=UI_ELEMENT_TIMEOUT)
            logger.info("Agent added as chat participant")
            chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
            page.wait_for_timeout(2000)  # Extra buffer for tool registration

        # ------------------------------------------------------------------
        # Step 6 — Send message asking to list branches
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Send message asking to list branches"):
            initial_count = chat.get_message_count()
            logger.info("Sending message to trigger toolkit (initial messages: %d)...", initial_count)
            chat.send_message(
                f"Use the GitHub toolkit to list all branches in the {settings.git_repo} repository. "
                "Execute the tool and show me the actual branch names.",
                use_enter=False
            )

        # ------------------------------------------------------------------
        # Step 7 — Wait for AI + toolkit response to stabilise
        # ------------------------------------------------------------------
        with allure.step("Step 7 — Wait for AI + toolkit response to stabilise"):
            logger.info("Waiting for AI + toolkit response...")
            chat.wait_for_ai_response(initial_count=initial_count, timeout=TOOLKIT_EXECUTION_TIMEOUT)
            chat.wait_for_message_content_stable(
                stable_duration_ms=5000, timeout=TOOLKIT_EXECUTION_TIMEOUT
            )

        # ------------------------------------------------------------------
        # Step 8 — Verify response contains branch/repository data from toolkit
        # ------------------------------------------------------------------
        with allure.step("Step 8 — Verify response contains branch/repository data"):
            # The branch list may be a paragraph/list, a Markdown table or a
            # fenced code block — read all of them from the last message.
            last_content = chat.get_last_message_full_text()
            assert last_content, "Expected AI to respond with content"
            logger.info("AI response (%d chars): %s", len(last_content), last_content[:500])

            entries, error_hits = _scan_listing_reply(last_content)

            # Guard (a) NEGATIVE — an error/refusal reply must never pass. Applied to
            # prose lines only, so branch names like 'fix/error-handling' are exempt.
            assert not error_hits, f"AI reply looks like an error/refusal: {error_hits[0]}"

            # Guard (b) POSITIVE — at least two single-token branch entries; intro-only
            # or 'none found' lines do not count. 'main' is not required.
            assert len(entries) >= 2, (
                "Expected toolkit response to list at least 2 branch entries "
                f"(single-token lines). Response: {last_content[:300]}"
            )

            logger.info(
                "Agent executed toolkit successfully — %d listing entries found in response",
                len(entries),
            )
