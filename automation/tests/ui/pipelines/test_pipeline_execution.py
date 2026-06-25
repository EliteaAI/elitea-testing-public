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
    detail_page.dismiss_banner_if_present()
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
        """PIPE-011, PIPE-012: Execute a simple pipeline and verify meaningful response.

        Sends a specific question and verifies the pipeline processes it through
        the LLM node and returns a substantive, error-free answer.

        Verifies:
        - Pipeline returns a non-empty response (PIPE-011)
        - Response is not an error message (PIPE-012)
        - Response has substantive content (PIPE-012)
        """
        pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        response = _execute_pipeline(
            pipelines,
            "What is 2 + 2? Reply with just the number.",
        )

        _assert_response_quality(response)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_message_count_starts_at_zero_and_grows(self, page, pipeline_with_llm_id):
        """PIPE-013: Fresh pipeline starts at zero messages and count grows with each send.

        Verifies that:
        - Fresh pipeline starts with 0 messages (PIPE-013)
        - After first send there are at least 2 messages: user + AI (PIPE-013)
        - A second send grows the count by at least 2 more (PIPE-013)
        """
        pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        initial_count = pipelines.get_embedded_chat_message_count()
        assert initial_count == 0, (
            f"Fresh pipeline should have 0 messages, got {initial_count}"
        )

        # First execution
        _execute_pipeline(pipelines, "First message")
        count_after_first = pipelines.get_embedded_chat_message_count()
        assert count_after_first >= 2, (
            f"Should have >= 2 messages after first run, got {count_after_first}"
        )

        # Second execution
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
        """PIPE-015: Executing a pipeline with no nodes (only END).

        An empty pipeline should either return an error message or produce
        some response — it should not hang or crash the UI.
        """
        pipelines = _navigate_to_pipeline_detail(page, pipeline_id)

        initial_count = pipelines.get_embedded_chat_message_count()

        pipelines.send_message_in_embedded_chat(
            "Test message", timeout=UI_ELEMENT_TIMEOUT,
        )

        # Wait for any response (may be an error) with a shorter timeout
        pipelines.wait_for_embedded_chat_response(
            initial_count=initial_count,
            stable_duration_ms=STABLE_DURATION_MS,
            timeout=60_000,
        )

        # The pipeline should produce some output (even if it's an error)
        final_count = pipelines.get_embedded_chat_message_count()
        assert final_count >= initial_count + 2, "Empty pipeline should produce user message AND at least one response"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_navigate_away_and_reexecute(self, page, pipeline_with_llm_id):
        """PIPE-016: Navigate away from the pipeline and return to re-execute.

        After navigating to a different page and returning, the pipeline
        should still be executable.
        """
        pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        # First execution
        _execute_pipeline(pipelines, "First run")
        assert pipelines.get_embedded_chat_message_count() >= 2, (
            "Should have >= 2 messages after first execution before navigating away"
        )

        # Navigate away to the pipelines dashboard
        list_page = PipelinesListPage(page)
        list_page.navigate()

        # Navigate back to the pipeline detail
        pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        # Re-execute — the pipeline should work again
        response = _execute_pipeline(pipelines, "After navigation")
        _assert_response_quality(response)


class TestPipelineChatMessages:
    """PIPE-017 to PIPE-018: Message display and accumulation tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0856_pipeline-execution-message-flow-and-history.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0862_pipeline-execution.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_user_message_visible(self, page, pipeline_with_llm_id):
        """PIPE-017: User message appears in chat alongside AI response.

        Both the user's input and the pipeline's output should be visible
        in the message list after execution.
        """
        pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

        user_msg = "Tell me a fun fact about space"
        _execute_pipeline(pipelines, user_msg)

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
        """PIPE-014, PIPE-018: Multiple sequential executions accumulate messages.

        Sending 3 messages should result in at least 6 messages (3 user + 3 AI).
        Also verifies count grows after each individual send.
        """
        pipelines = _navigate_to_pipeline_detail(page, pipeline_with_llm_id)

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

        final_count = pipelines.get_embedded_chat_message_count()
        expected_min = len(messages_to_send) * 2
        assert final_count >= expected_min, (
            f"Should have >= {expected_min} messages after {len(messages_to_send)} "
            f"executions, got {final_count}"
        )
        assert final_count <= expected_min + 2, f"Unexpected extra messages: expected ~{expected_min}, got {final_count}"

        # Last response should have content
        last_response = pipelines.get_embedded_chat_last_message()
        assert len(last_response.strip()) > 3, f"Expected substantive response, got: {last_response!r}"
