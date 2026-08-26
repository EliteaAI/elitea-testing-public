"""Pipeline Run History panel — view past executions (ELITEA-2011) and close
the panel (ELITEA-2070, extend-existing).

``TestPipelineRunHistoryViewExecutions`` verifies that the Run History panel
(reachable via the ``pipeline-history-tab`` icon button once at least one
execution exists) lists every past execution for a pipeline and that
clicking any entry loads that specific execution's message + AI-response
content into the right-hand panel.

Test-data strategy (per AFS): the disposable pipeline starts with an empty
Run History, so the test creates the 2 distinct entries the case's
precondition requires itself — send Message A, await its reply, click
"Clear the chat" (which starts a fresh *local, unsaved* conversation rather
than touching Message A's conversation — confirmed live this session,
identical mechanism to the Agent-surface ELITEA-1877 case, same shared
``ChatBox``/``ChatPanel.jsx`` component), send Message B, await its reply.
Conversation A then survives as its own Run History row alongside the
now-active conversation B.

``TestPipelineRunHistoryPanelClose`` extends the above with the one gap
ELITEA-2011 never covered — closing the panel via its ``X`` button (case
step 7) — reusing the same fixture and page-object methods; it does not
modify ``TestPipelineRunHistoryViewExecutions``'s test body.

Specs:
  test-specs/pipelines/l2_pipeline-run-history-panel-view-executions_ELITEA-2011.md
  test-specs/pipelines/lextend_pipeline-run-history-panel-close_ELITEA-2070.md
"""

import re
import uuid

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from playwright.sync_api import Page

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

# Run History row rendered-text patterns (Date + Version + Duration columns;
# RunHistoryListItem.jsx / RunHistorySortableHeader.jsx — same shared
# components the Agent surface documents, ELITEA-1876). Displayed date
# format is `dd-MM-yyyy, hh:mm a`.
RUN_HISTORY_DATE_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)", re.IGNORECASE)
RUN_HISTORY_DURATION_PATTERN = re.compile(r"\d+(\.\d+)?\s*s\b")
# Known version name for the disposable pipelines the `pipeline_with_llm_id`
# fixture creates (AFS § Concrete Handles / matches ELITEA-1877's precedent).
RUN_HISTORY_VERSION_TEXT = "base"

# Newest-first Run History ordering (default sort = Date descending,
# code-confirmed live during AFS analysis) — index 0 is always the most
# recent entry, so "the non-selected one" (the case's own step 6) = index 1.
NEWEST_RUN_INDEX = 0
OLDER_RUN_INDEX = 1


class TestPipelineRunHistoryViewExecutions:
    """Run History panel — viewing past pipeline executions (ELITEA-2011, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2011_pipeline-run-history-view-executions.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_run_history_panel_lists_and_shows_execution_details(
        self, page: Page, pipeline_with_llm_id
    ):
        """Executing a pipeline twice creates 2 Run History entries; opening
        the panel lists both, and clicking an entry loads that execution's
        own message + response content into the right-hand panel."""
        # Textually-distinct markers so a test that accidentally read the
        # WRONG run's content cannot pass by coincidence.
        message_a = f"first-run-{uuid.uuid4().hex[:6]}"
        message_b = f"second-run-{uuid.uuid4().hex[:6]}"

        # AFS Axis 2: "Zero console errors during the whole flow."
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        detail_page = PipelineDetailPage(page)

        with allure.step("Step 1 — Navigate to a pipeline with a runnable LLM node"):
            detail_page.navigate(pipeline_with_llm_id)
            detail_page.dismiss_banner_if_present()
            assert detail_page.canvas_wrapper.is_visible(), (
                "Pipeline canvas should be displayed after navigating to the detail page"
            )
            assert detail_page.chat_input.is_visible(), (
                "Embedded chat panel should be visible on the right"
            )

        with allure.step(
            "Step 2 — Send Message A, clear the chat, send Message B "
            "(creates 2 distinct Run History entries)"
        ):
            count_before_a = detail_page.get_embedded_chat_message_count()
            detail_page.send_message_in_embedded_chat(message_a, timeout=UI_ELEMENT_TIMEOUT)
            detail_page.wait_for_embedded_chat_response(
                initial_count=count_before_a, timeout=AI_RESPONSE_TIMEOUT
            )
            assert detail_page.get_embedded_chat_message_count() > count_before_a, (
                "Message A's exchange should be visible before clearing the chat"
            )

            detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)

            count_before_b = detail_page.get_embedded_chat_message_count()
            detail_page.send_message_in_embedded_chat(message_b, timeout=UI_ELEMENT_TIMEOUT)
            detail_page.wait_for_embedded_chat_response(
                initial_count=count_before_b, timeout=AI_RESPONSE_TIMEOUT
            )
            assert detail_page.find_message_containing(message_b), (
                f"Embedded chat should show Message B's exchange ({message_b!r}) — "
                "the current/active run this case proves the historical run is "
                "distinct from"
            )

        with allure.step(
            "Step 3 — Click the 'view run history' icon button; the Run "
            "History panel opens (replacing the Configuration form + "
            "embedded chat)"
        ):
            detail_page.open_run_history(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 4 — Verify the run history panel opened: execution entries "
            "(run-history-list-item rows) are present"
        ):
            item_count = detail_page.get_run_history_item_count()
            assert item_count > 0, (
                "Run History panel should list at least one execution entry "
                "once opened"
            )

        with allure.step(
            "Step 5 — Verify at least 2 execution entries are listed "
            "(conversation A + conversation B)"
        ):
            item_count = detail_page.get_run_history_item_count()
            assert item_count == 2, (
                f"Run History list should show exactly 2 entries "
                f"(conversation A + conversation B), got {item_count}"
            )
            row_texts = detail_page.get_run_history_item_texts()
            assert len(row_texts) == item_count, (
                f"Expected {item_count} Run History row texts, got "
                f"{len(row_texts)}: {row_texts!r}"
            )
            for i, row_text in enumerate(row_texts):
                assert RUN_HISTORY_DATE_PATTERN.search(row_text), (
                    f"Run History row {i} should display a timestamp matching "
                    f"'dd-MM-yyyy, hh:mm AM/PM', got: {row_text!r}"
                )
                assert RUN_HISTORY_VERSION_TEXT in row_text, (
                    f"Run History row {i} should display its Version "
                    f"({RUN_HISTORY_VERSION_TEXT!r}), got: {row_text!r}"
                )
                assert RUN_HISTORY_DURATION_PATTERN.search(row_text), (
                    f"Run History row {i} should display a Duration matching "
                    f"'<number> s', got: {row_text!r}"
                )

        with allure.step(
            "Step 6 — Click the non-selected (older) entry; verify it shows "
            "the message and response details for that execution"
        ):
            detail_page.select_run_history_item(OLDER_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.is_run_history_item_selected(
                OLDER_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
            ), "The clicked (older) row should carry data-selected=\"true\""
            assert not detail_page.is_run_history_item_selected(
                NEWEST_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
            ), "The non-clicked (newer) row should stay data-selected=\"false\""

            history_text = detail_page.get_run_history_chat_messages_text()
            assert message_a in history_text, (
                f"Run History panel should display Message A ({message_a!r}) "
                f"after selecting its (older) entry, got: {history_text!r}"
            )
            assert message_b not in history_text, (
                f"Run History panel's loaded content should NOT contain "
                f"Message B ({message_b!r}) — it belongs to the other "
                f"(newer, non-selected) entry — got: {history_text!r}"
            )

        with allure.step("Verify no console errors across the full flow"):
            assert not console_errors, (
                f"Expected no console errors across the flow, got: "
                f"{[(m.type, m.text) for m in console_errors]}"
            )


class TestPipelineRunHistoryPanelClose:
    """Run History panel close (X) button (ELITEA-2070, p1).

    Extension of ELITEA-2011's covering test above: steps 1-6 of the case
    (open a pipeline with a prior execution, open Run History, list
    executions, select one, view its details) are already proven by
    ``TestPipelineRunHistoryViewExecutions`` on the identical shared
    ``PipelineDetailPage``/``RunHistoryContainer`` stack — see AFS
    ``test-specs/pipelines/lextend_pipeline-run-history-panel-close_ELITEA-2070.md``
    § Coverage Map. This test's own new observable is case step 7 only:
    closing the panel via its ``X`` button restores the Configuration form +
    embedded chat, with zero network requests during the close itself
    (purely client-side ``onClose`` state flip, confirmed via source read of
    ``RunHistoryContainer.jsx``).
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/pipelines/ELITEA-2070_pipeline-run-history-panel.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_run_history_panel_closes_and_restores_chat(self, page: Page, pipeline_with_llm_id):
        """Closing the Run History panel (after selecting an entry) removes
        the panel from the DOM and restores the Configuration form +
        embedded chat, with zero network requests fired by the close itself."""
        message = f"close-run-history-{uuid.uuid4().hex[:6]}"

        # AFS Axis 2: "Zero console errors during the whole flow."
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # AFS step 4 / § Network Behavior: closing the panel must fire zero
        # network requests (purely client-side onClose state flip).
        api_requests = []
        page.on(
            "request",
            lambda request: api_requests.append(request.url) if "/api/v2/" in request.url else None,
        )

        detail_page = PipelineDetailPage(page)

        with allure.step(
            "Step 1 — Navigate to a pipeline with a runnable LLM node, send one "
            "message via the embedded chat, and wait for the AI response"
        ):
            detail_page.navigate(pipeline_with_llm_id)
            detail_page.dismiss_banner_if_present()
            assert detail_page.chat_input.is_visible(), (
                "Embedded chat panel should be visible on the right"
            )
            count_before = detail_page.get_embedded_chat_message_count()
            detail_page.send_message_in_embedded_chat(message, timeout=UI_ELEMENT_TIMEOUT)
            detail_page.wait_for_embedded_chat_response(
                initial_count=count_before, timeout=AI_RESPONSE_TIMEOUT
            )
            assert detail_page.get_embedded_chat_message_count() > count_before, (
                "The message's exchange should be visible before opening Run History "
                "(one execution now exists server-side)"
            )

        with allure.step(
            "Step 2 — Click the 'view run history' icon button; the Run "
            "History panel opens"
        ):
            detail_page.open_run_history(timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.get_run_history_item_count() > 0, (
                "Run History panel should list the execution just created"
            )

        with allure.step(
            "Step 3 — Click the one execution entry; its details (message + "
            "response) render in the right-hand panel"
        ):
            detail_page.select_run_history_item(NEWEST_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.is_run_history_item_selected(
                NEWEST_RUN_INDEX, timeout=UI_ELEMENT_TIMEOUT
            ), "The clicked row should carry data-selected=\"true\""
            history_text = detail_page.get_run_history_chat_messages_text()
            assert message in history_text, (
                f"Run History panel should display the sent message ({message!r}) "
                f"after selecting its entry, got: {history_text!r}"
            )

        with allure.step(
            "Step 4 — Click the close (X) button; the Run History panel is "
            "removed and the Configuration form + embedded chat is restored, "
            "with no Run-History-specific network activity re-fired by the "
            "close itself"
        ):
            api_requests.clear()
            detail_page.close_run_history(timeout=UI_ELEMENT_TIMEOUT)
            # AFS § Network Behavior (amended per this session's live run):
            # RunHistoryContainer's onClose prop (RunHistoryContainer.jsx:74-91)
            # is itself a pure client-side state flip with no fetch call — but
            # closing also unmounts the panel and remounts the Configuration
            # form, which independently re-fires ITS OWN view-population
            # requests (tools/toolkits/tags/applications/index_types) as a
            # normal consequence of remounting, unrelated to Run History.
            # The precise, durable claim is scoped to Run-History's OWN
            # endpoints: closing must not re-fetch the conversations list
            # (`conversation(s)/prompt_lib`) — confirmed zero hits live.
            conversation_requests = [u for u in api_requests if "conversation" in u]
            assert not conversation_requests, (
                f"Closing the Run History panel should not re-fetch the "
                f"conversations list (that data is being discarded, not "
                f"re-read), got: {conversation_requests}"
            )
            assert detail_page.chat_input.is_visible(), (
                "Embedded chat input should be visible again after closing Run History"
            )
            assert detail_page.history_tab.is_visible(), (
                "The 'view run history' icon button should be visible again after "
                "closing the panel (Configuration form + embedded chat restored)"
            )
            assert detail_page.get_run_history_item_count() == 0, (
                "Run History list items should no longer be present in the DOM "
                "once the panel is closed"
            )

        with allure.step("Verify no console errors across the full flow"):
            assert not console_errors, (
                f"Expected no console errors across the flow, got: "
                f"{[(m.type, m.text) for m in console_errors]}"
            )
