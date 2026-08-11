"""UI Tests for Pipeline Execution — Phase 2.

Tests pipeline execution via the embedded chat on the pipeline detail page.
Pipelines execute when a user sends a message in the right-panel chat;
the pipeline processes the input through its nodes and returns a response.

Each test uses the ``pipeline_with_llm_id`` fixture for a pipeline that has
a single LLM node connected to END — the minimal runnable pipeline.

Test IDs:
    PIPE-011, PIPE-012: Execute pipeline and verify meaningful response
    PIPE-013: Message count updates after single and fresh pipeline execution
    PIPE-014, PIPE-018: Multiple sequential executions accumulate messages
    PIPE-015: Pipeline with no nodes shows error or empty response
    PIPE-016: Navigate away and re-execute pipeline
    PIPE-017: User message appears in chat alongside AI response

Markers:
    - ui: requires browser
    - pipelines: pipeline-related tests
    - p0/p1/p2: priority markers

Usage:
    cd automation
    pytest test_pipeline_execution.py -v
    pytest test_pipeline_execution.py -v -k "execute_simple"
"""

import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage
import allure

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
PIPELINE_EXECUTION_TIMEOUT = 90_000
STABLE_DURATION_MS = 3_000  # 3 s stability window for streaming LLM responses to finish rendering


def _assert_response_quality(response: str) -> None:
    assert len(response.strip()) > 3, f"Expected substantive response, got: {response!r}"
    assert "unexpected error" not in response.lower(), f"Response contains error: {response}"


def _navigate_to_pipeline_detail(page, pipeline_id):
    """Navigate to pipeline detail page and wait for it to load.

    Returns a PipelineDetailPage instance ready for interaction.
    """
    detail_page = PipelineDetailPage(page)
    detail_page.navigate(pipeline_id)
    return detail_page


def _execute_pipeline(pipelines, message, *, timeout=PIPELINE_EXECUTION_TIMEOUT):
    """Send a message in the embedded chat and wait for the response.

    Returns the response text from the last AI message.

    Args:
        pipelines: PipelineDetailPage instance on the detail page.
        message: The user message to send.
        timeout: Maximum wait time for execution.

    Returns:
        The AI response text.
    """
    initial_count = pipelines.get_embedded_chat_message_count()

    pipelines.send_message_in_embedded_chat(message, timeout=UI_ELEMENT_TIMEOUT)
    pipelines.wait_for_embedded_chat_response(
        initial_count=initial_count,
        stable_duration_ms=STABLE_DURATION_MS,
        timeout=timeout,
    )

    return pipelines.get_embedded_chat_last_message()


# ===========================================================================
# Tests — Pipeline execution via embedded chat
# ===========================================================================


class TestExecutePipeline:
    """PIPE-011 to PIPE-014: Core pipeline execution tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0862_pipeline-execution.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_pipeline_response_is_meaningful(self, page, pipeline_with_llm_id):
        """PIPE-011, PIPE-012: Execute a simple pipeline and verify meaningful response."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        with allure.step("Step 2 — Execute pipeline with a question"):
            response = _execute_pipeline(
                pipelines,
                "What is 2 + 2? Reply with just the number.",
            )

        with allure.step("Step 3 — Verify response is meaningful and error-free"):
            _assert_response_quality(response)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_message_count_starts_at_zero_and_grows(self, page, pipeline_with_llm_id):
        """PIPE-013: Fresh pipeline starts at zero messages and count grows with each send."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        with allure.step("Step 2 — Verify fresh pipeline starts with 0 messages"):
            initial_count = pipelines.get_embedded_chat_message_count()
            assert initial_count == 0, (
                f"Fresh pipeline should have 0 messages, got {initial_count}"
            )

        with allure.step("Step 3 — Execute first message and verify count grows"):
            _execute_pipeline(pipelines, "First message")
            count_after_first = pipelines.get_embedded_chat_message_count()
            assert count_after_first >= 2, (
                f"Should have >= 2 messages after first run, got {count_after_first}"
            )

        with allure.step("Step 4 — Execute second message and verify count grows again"):
            _execute_pipeline(pipelines, "Second message")
            count_after_second = pipelines.get_embedded_chat_message_count()
            assert count_after_second >= count_after_first + 2, (
                f"Should have >= {count_after_first + 2} messages after second run, "
                f"got {count_after_second}"
            )


class TestPipelineExecutionEdgeCases:
    """PIPE-015 to PIPE-016: Edge cases for pipeline execution."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0852_pipeline-execution-edge-cases.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_empty_pipeline_execution(self, page, pipeline_id):
        """PIPE-015: Executing a pipeline with no nodes (only END)."""
        with allure.step("Step 1 — Navigate to empty pipeline detail page"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_id)
            initial_count = pipelines.get_embedded_chat_message_count()

        with allure.step("Step 2 — Send message to empty pipeline"):
            pipelines.send_message_in_embedded_chat(
                "Test message", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step("Step 3 — Wait for any response"):
            pipelines.wait_for_embedded_chat_response(
                initial_count=initial_count,
                stable_duration_ms=STABLE_DURATION_MS,
                timeout=60_000,
            )

        with allure.step("Step 4 — Verify pipeline produces some output"):
            final_count = pipelines.get_embedded_chat_message_count()
            assert final_count >= initial_count + 2, "Empty pipeline should produce user message AND at least one response"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_navigate_away_and_reexecute(self, page, pipeline_with_llm_id):
        """PIPE-016: Navigate away from the pipeline and return to re-execute."""
        with allure.step("Step 1 — Navigate to pipeline and execute first message"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)
            _execute_pipeline(pipelines, "First run")
            assert pipelines.get_embedded_chat_message_count() >= 2, (
                "Should have >= 2 messages after first execution before navigating away"
            )

        with allure.step("Step 2 — Navigate away to pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 3 — Navigate back to pipeline detail"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        with allure.step("Step 4 — Re-execute pipeline and verify response"):
            response = _execute_pipeline(pipelines, "After navigation")
            _assert_response_quality(response)


class TestPipelineChatMessages:
    """PIPE-017 to PIPE-018: Message display and accumulation tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0862_pipeline-execution.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_user_message_visible(self, page, pipeline_with_llm_id):
        """PIPE-017: User message appears in chat alongside AI response."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        with allure.step("Step 2 — Execute pipeline with user message"):
            user_msg = "Tell me a fun fact about space"
            _execute_pipeline(pipelines, user_msg)

        with allure.step("Step 3 — Verify user message appears in chat"):
            msg_count = pipelines.get_embedded_chat_message_count()
            assert msg_count >= 2, (
                f"Should have >= 2 messages after execution, got {msg_count}"
            )
            assert pipelines.find_message_containing(user_msg), (
                f"User message '{user_msg}' should appear in the chat"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_multiple_executions_accumulate(self, page, pipeline_with_llm_id):
        """PIPE-014, PIPE-018: Multiple sequential executions accumulate messages."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        with allure.step("Step 2 — Send 3 messages and verify count grows after each"):
            messages_to_send = [
                "What is 2 + 2?",
                "What is the color of the sky?",
                "Name a fruit",
            ]

            prev_count = pipelines.get_embedded_chat_message_count()
            for msg in messages_to_send:
                _execute_pipeline(pipelines, msg)
                current_count = pipelines.get_embedded_chat_message_count()
                assert current_count >= prev_count + 2, (
                    f"Count should grow by >= 2 after each send: "
                    f"was {prev_count}, now {current_count} [msg={msg!r}]"
                )
                prev_count = current_count

        with allure.step("Step 3 — Verify total message count is correct"):
            final_count = pipelines.get_embedded_chat_message_count()
            expected_min = len(messages_to_send) * 2
            assert final_count >= expected_min, (
                f"Should have >= {expected_min} messages after {len(messages_to_send)} "
                f"executions, got {final_count}"
            )
            assert final_count <= expected_min + 2, f"Unexpected extra messages: expected ~{expected_min}, got {final_count}"

        with allure.step("Step 4 — Verify last response has content"):
            last_response = pipelines.get_embedded_chat_last_message()
            assert len(last_response.strip()) > 3, f"Expected substantive response, got: {last_response!r}"
