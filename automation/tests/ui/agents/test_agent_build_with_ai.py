"""UI Tests for the Agent "Build with AI" generation flow.

Covers ELITEA-1915: generation failure shows an error, preserves the
entered prompt, and a retry (re-clicking the same Generate button) succeeds
once the service recovers.

Spec: test-specs/agents/l2_build-with-ai-generation-failure-retry_ELITEA-1915.md
Covers: GenerateAgentModal (GenerateEntityModal.jsx via GenerateAgentModal.jsx)

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p2: medium priority (case priority: medium)

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_build_with_ai.py -v
"""

import allure
import pytest

from pages.agents_list_page import AgentsListPage
from pages.generate_agent_modal_page import GenerateAgentModalPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15000
GENERATE_RESPONSE_TIMEOUT = 15000
LOADING_STATE_TIMEOUT = 3000
REVIEW_FORM_TIMEOUT = 15000

PROMPT_TEXT = (
    "Create a customer support triage agent that categorizes incoming "
    "tickets by urgency and routes them to the correct team."
)
SIMULATED_ERROR_MESSAGE = "Simulated generation failure for ELITEA-1915"

# Minimal, valid draft payload mirroring the real generate_application_draft
# response shape (GenerateAgentModal.jsx / GenerateAgentReviewForm.jsx) —
# used for the retry's synthetic recovery (option (b) per the AFS).
RETRY_DRAFT_PAYLOAD = {
    "name": "Support Ticket Triage Agent",
    "description": "Categorizes incoming support tickets by urgency and routes them to the correct team.",
    "instructions": "You are a support ticket triage agent. Read each incoming ticket, "
                     "classify its urgency, and route it to the correct team.",
    "welcome_message": "Hi! I'll help triage your support tickets.",
    "conversation_starters": [
        "Triage this ticket for me",
        "What urgency is this issue?",
        "Which team should handle this?",
        "Summarize today's incoming tickets",
    ],
}


class TestAgentBuildWithAIGenerationFailureRetry:
    """Build with AI (P2): generation failure shows error, prompt is
    preserved, and retry succeeds once the service recovers."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/build_with_ai/ELITEA-1915_build-with-ai-generation-failure-shows-error-and-allows-retry.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_generation_failure_shows_error_and_allows_retry(self, page):
        """Generation failure surfaces an error, preserves the prompt, and a
        retry (via the same Generate button) succeeds once the service
        recovers."""
        list_page = AgentsListPage(page)
        modal = GenerateAgentModalPage(page)

        # ------------------------------------------------------------------
        # Step 1 — Open modal, enter description
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Open modal, enter description"):
            list_page.navigate_to_create()
            modal.open_modal()

            assert not modal.is_generate_enabled(), (
                "Generate button should be disabled while the prompt is empty"
            )

            modal.fill_prompt(PROMPT_TEXT)

            assert modal.get_prompt_value() == PROMPT_TEXT, (
                "Prompt textarea should contain exactly the entered text"
            )
            assert modal.is_generate_enabled(), (
                "Generate button should become enabled once the prompt is non-empty"
            )

        # ------------------------------------------------------------------
        # Step 2 — Trigger/simulate generation failure
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Trigger/simulate generation failure"):
            modal.mock_generate_failure(SIMULATED_ERROR_MESSAGE, status=500)
            response = modal.click_generate_and_wait_for_response(timeout=GENERATE_RESPONSE_TIMEOUT)

            assert response.status == 500, (
                f"Expected the mocked generate-draft request to resolve 500, got {response.status}"
            )
            modal.wait_for_input_step(timeout=LOADING_STATE_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 3 — Verify clear error message displayed
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Verify clear error message displayed"):
            assert modal.is_error_alert_visible(), (
                "An error alert should be displayed in the modal after a generation failure"
            )
            assert modal.get_error_message() == SIMULATED_ERROR_MESSAGE, (
                "Error alert should surface the backend's error message verbatim, "
                f"got: {modal.get_error_message()!r}"
            )

        # ------------------------------------------------------------------
        # Step 4 — Verify the previously entered prompt is still present
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Verify the previously entered prompt is still present"):
            assert modal.get_prompt_value() == PROMPT_TEXT, (
                "Prompt text entered before the failure should still be visible after the failure"
            )

        # ------------------------------------------------------------------
        # Step 5 — Click retry / "Generate agent" button
        # ------------------------------------------------------------------
        with allure.step('Step 5 — Click retry / "Generate agent" button'):
            modal.clear_generate_mock()
            modal.mock_generate_success(RETRY_DRAFT_PAYLOAD)

            with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as retry_response_info:
                modal.generate_button.click()

                # resetGenerate() fires before the retry request — the stale
                # Step 3 error should be gone as soon as the retry is in
                # flight, not only once the new (artificially delayed)
                # request resolves.
                modal.error_alert.wait_for(state="hidden", timeout=LOADING_STATE_TIMEOUT)
                modal.wait_for_loading_visible(timeout=LOADING_STATE_TIMEOUT)

        # ------------------------------------------------------------------
        # Step 6 — Verify the retry succeeds and a draft is returned
        # ------------------------------------------------------------------
        with allure.step("Step 6 — Verify the retry succeeds and a draft is returned"):
            retry_response = retry_response_info.value
            assert retry_response.status == 200, (
                f"Expected the retried generate-draft request to succeed, got {retry_response.status}"
            )
            assert retry_response.json()["name"] == RETRY_DRAFT_PAYLOAD["name"], (
                "Retried request should resolve with the recovered draft payload"
            )

            modal.wait_for_input_step_hidden(timeout=1000)
            modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)
