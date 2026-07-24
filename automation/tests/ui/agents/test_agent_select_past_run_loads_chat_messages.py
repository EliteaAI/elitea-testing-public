"""Selecting a past run from history loads its messages in the chat panel
(ELITEA-1877).

Verifies that clicking a past (non-active) run entry in the Run History
panel loads that session's own messages into the chat panel — distinct
from whichever run was active immediately before the panel was opened.

Test-data strategy (per AFS): the ``agent_id`` fixture creates a fresh,
empty agent — Run History starts empty, so the test itself creates the
2 distinct runs the case's precondition requires (send message -> await
response -> clear chat -> send a second, textually-distinct message ->
await response), each marked with a unique, mutually-distinguishable
string so the Step 6/7 content assertions cannot pass by coincidence.

Spec: test-specs/agents/l2_select-past-run-loads-chat-messages_ELITEA-1877.md
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

# Textually-distinct markers (AFS Test Data) — must differ from each other
# so a test that accidentally read the WRONG run's content cannot pass.
RUN_1_MESSAGE = f"Run 1 marker {uuid.uuid4().hex[:8]}"
RUN_2_MESSAGE = f"Run 2 marker {uuid.uuid4().hex[:8]}"

# Newest-first Run History ordering (confirmed live during AFS analysis):
# index 0 = Run 2 (most recent / active-when-panel-opened), index 1 = Run 1
# (the "past run" the case asks to select).
NEWEST_RUN_INDEX = 0
OLDER_RUN_INDEX = 1


class TestAgentSelectPastRunLoadsChatMessages:
    """Selecting a past run from history loads its messages (ELITEA-1877, p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1877_selecting-a-past-run-from-history-loads-its-messages.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_select_past_run_loads_chat_messages(self, page: Page, agent_id):
        """Clicking an older Run History entry loads its own messages into
        the chat panel, distinct from the run that was active before the
        panel was opened."""
        with allure.step("Step 1 — Navigate to the agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)
            assert detail_page.information_section.is_visible(), (
                "Agent detail page's Information section should be visible"
            )

        with allure.step(
            "Setup — Create 2 distinct run history entries (Run 1, Run 2)"
        ):
            count_before_run1 = detail_page.get_chat_message_count()
            detail_page.send_chat_message(RUN_1_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
            detail_page.wait_for_chat_response(
                initial_count=count_before_run1, timeout=AI_RESPONSE_TIMEOUT
            )
            assert detail_page.get_chat_message_count() > count_before_run1, (
                "Run 1's message + AI reply should be visible before starting Run 2"
            )

            detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)

            count_before_run2 = detail_page.get_chat_message_count()
            detail_page.send_chat_message(RUN_2_MESSAGE, timeout=UI_ELEMENT_TIMEOUT)
            detail_page.wait_for_chat_response(
                initial_count=count_before_run2, timeout=AI_RESPONSE_TIMEOUT
            )
            assert detail_page.get_chat_message_count() > count_before_run2, (
                "Run 2's message + AI reply should be visible — this is the "
                "active/current run when the Run History panel is opened next"
            )

        with allure.step("Step 2 — Open the Run History panel"):
            detail_page.open_run_history_panel(timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.run_history_panel_heading.is_visible(), (
                "Run History panel heading should be visible once the panel opens"
            )

        with allure.step("Step 3 — Verify the Run History list shows at least 2 entries"):
            item_count = detail_page.get_run_history_item_count()
            assert item_count >= 2, (
                f"Run History list should show at least 2 entries (Run 1 + Run 2), "
                f"got {item_count}"
            )

        with allure.step(
            "Step 4 — Click the older (non-most-recent) run entry and verify "
            "it is highlighted, and only it"
        ):
            detail_page.click_run_history_item(OLDER_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.is_run_history_item_selected(
                OLDER_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
            ), "The clicked (older, Run 1) row should carry data-selected=\"true\""
            # Axis 2 addition (AFS): the non-clicked row must stay unselected —
            # catches the class of bug where the wrong row lights up.
            assert not detail_page.is_run_history_item_selected(
                NEWEST_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
            ), "The non-clicked (newer, Run 2) row should stay data-selected=\"false\""

        with allure.step(
            "Step 5 — Verify the chat panel shows Run 1's own message and AI reply"
        ):
            history_text = detail_page.get_all_chat_messages_text(
                expected_text=RUN_1_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
            )
            assert RUN_1_MESSAGE in history_text, (
                f"Chat panel should display Run 1's message ({RUN_1_MESSAGE!r}) "
                f"after selecting its history entry, got: {history_text!r}"
            )
            assert detail_page.get_chat_message_count() == 2, (
                "Run 1's conversation should show exactly 2 messages "
                "(the user message + the AI reply)"
            )

        with allure.step(
            "Step 6 — Verify this is distinct from the current/active run (Run 2)"
        ):
            assert RUN_2_MESSAGE not in history_text, (
                f"Run 1's loaded content should NOT contain Run 2's marker "
                f"({RUN_2_MESSAGE!r}) — got: {history_text!r}"
            )
