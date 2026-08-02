"""Selecting a past run from history loads its messages in the chat panel
(ELITEA-1877).

Verifies that clicking a past (non-most-recent) Run History entry loads that
session's own messages into the right-hand chat panel — visibly selected
(``data-selected="true"``) and textually distinct from the run that was
active immediately before the panel was opened.

Test-data strategy (per AFS): the disposable agent starts with an empty Run
History, so the test creates the 2 distinct entries the case's precondition
requires itself — send Message A, await its reply, click "Clear chat" (which
starts a fresh *local, unsaved* conversation rather than touching Message A's
conversation — confirmed live + code-confirmed, see AFS § Test Data), send
Message B, await its reply. Conversation A then survives as its own Run
History row alongside the now-active conversation B.

``reasoning_effort`` note: the disposable-agent payload uses
``reasoning_effort: "low"`` (not the project's usual ``"none"`` workaround) —
this case opens the embedded chat and sends 2 messages, and ``"none"`` is
confirmed (ELITEA-1897/#560) to 500 the conversation-create call whenever the
agent's chat is actually opened. See AFS § Test Data amendment.

Spec: test-specs/agents/l2_run-history-select-past-run-loads-messages_ELITEA-1877.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

# Newest-first Run History ordering (default sort = Date descending,
# code-confirmed in `RunHistoryList.jsx`'s `useRunHistorySorting(SORT_TYPES.DATE)`
# and live-confirmed during AFS analysis) — index 0 is always the most recent
# entry, so "not the most recent" (the case's own step 3) = index 1.
NEWEST_RUN_INDEX = 0
OLDER_RUN_INDEX = 1


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent
    that both creates successfully AND can open an embedded-chat conversation.

    Uses ``reasoning_effort: "low"`` and omits ``temperature`` and the model
    fields (``model_name``/``model_project_id``) entirely — same shape as
    ``test_agent_management.py``'s ``_build_execution_agent_payload``. This
    avoids both the open #524 creation-400 (``temperature`` + a non-``"none"``
    ``reasoning_effort``) and the #560 embedded-chat 500 (``reasoning_effort:
    "none"`` breaks ``POST .../conversations/prompt_lib/{project}``), while
    staying well within a normal AI-response wait (``"medium"`` avoids both
    defects too but drives noticeably slower "thinking" latency).
    """
    return {
        "name": name,
        "description": "Auto-created for ELITEA-1877 Run History test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": "You are a helpful assistant. Reply concisely.",
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "reasoning_effort": "low",
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


class TestAgentRunHistorySelectPastRun:
    """Run History — selecting a past run loads its own messages (ELITEA-1877, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1877_selecting-a-past-run-from-history-loads-its-messages.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_select_past_run_loads_chat_messages(self, page: Page, agent_api):
        """Clicking an older Run History entry loads its own messages into
        the chat panel, distinct from the run that was active before the
        panel was opened."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1877-runhist-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        # Textually-distinct markers so a test that accidentally read the
        # WRONG run's content cannot pass by coincidence.
        message_a = f"first-run-{uuid.uuid4().hex[:6]}"
        message_b = f"second-run-{uuid.uuid4().hex[:6]}"

        detail_page = None
        # AFS Expected Results: "No console errors during the flow" — captures
        # both "error" and "warning" console messages, same pattern as
        # test_agent_llm_selector_anthropic_models.py.
        console_issues = []
        page.on(
            "console",
            lambda msg: console_issues.append(msg)
            if msg.type in ("error", "warning")
            else None,
        )

        try:
            with allure.step("Step 1 — Navigate to the agent detail page"):
                detail_page = AgentDetailPage(page)
                detail_page.navigate(agent_id)
                assert detail_page.information_section.is_visible(), (
                    "Agent detail page's Information section should be visible"
                )

            with allure.step(
                "Step 2 — Send Message A, clear chat, send Message B "
                "(creates 2 distinct Run History entries)"
            ):
                count_before_a = detail_page.get_chat_message_count()
                detail_page.send_chat_message(message_a, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=count_before_a, timeout=AI_RESPONSE_TIMEOUT
                )
                assert detail_page.get_chat_message_count() > count_before_a, (
                    "Message A's exchange should be visible before starting Message B"
                )

                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)

                count_before_b = detail_page.get_chat_message_count()
                detail_page.send_chat_message(message_b, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=count_before_b, timeout=AI_RESPONSE_TIMEOUT
                )
                last_message_text = detail_page.get_last_chat_message_full_text()
                assert message_b in last_message_text, (
                    "Embedded chat's last message should reflect Message B's "
                    f"exchange — the current/active run this case proves the "
                    f"historical run is distinct from, got: {last_message_text!r}"
                )

            with allure.step("Step 3 — Open the Run History panel"):
                detail_page.open_run_history(timeout=UI_ELEMENT_TIMEOUT)
                item_count = detail_page.get_run_history_item_count()
                assert item_count >= 2, (
                    "Run History list should show at least 2 entries "
                    f"(conversation A + conversation B), got {item_count}"
                )

            with allure.step(
                "Step 4 — Click the older (non-most-recent) run entry and "
                "verify it is highlighted"
            ):
                detail_page.select_run_history_item(OLDER_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_run_history_item_selected(
                    OLDER_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
                ), "The clicked (older) row should carry data-selected=\"true\""
                assert not detail_page.is_run_history_item_selected(
                    NEWEST_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
                ), "The non-clicked (newer) row should stay data-selected=\"false\""

            with allure.step(
                "Step 5 — Verify the Run History chat panel shows Message A's content"
            ):
                history_text = detail_page.get_run_history_chat_messages_text()
                assert message_a in history_text, (
                    f"Run History panel should display Message A ({message_a!r}) "
                    f"after selecting its entry, got: {history_text!r}"
                )

            with allure.step(
                "Step 6 — Verify this is distinct from the current/active run (Message B)"
            ):
                assert message_b not in history_text, (
                    f"Run History panel's loaded content should NOT contain "
                    f"Message B ({message_b!r}) — got: {history_text!r}"
                )

            with allure.step("Verify no console errors or warnings across the full flow"):
                assert not console_issues, (
                    "Expected no console errors/warnings across the flow, got: "
                    f"{[(m.type, m.text) for m in console_issues]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                agent_api.delete_agent(agent_id)
