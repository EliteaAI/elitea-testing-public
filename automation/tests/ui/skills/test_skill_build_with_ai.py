"""UI Tests for the Skill "Build with AI" generation flow.

Covers ELITEA-2001: generation failure shows an error, preserves the
entered prompt, and a retry (re-clicking the same Generate button) succeeds
once the service recovers.

Covers ELITEA-1990: the generated draft's review-form fields (Name,
Description, Instructions) are editable before creation, and the skill is
created with the edited values (not the originally-generated ones).

Spec: test-specs/skills/l2_build-with-ai-generation-failure-retry_ELITEA-2001.md
Spec: test-specs/skills/l2_generated-skill-draft-fields-are-editable-before-creation_ELITEA-1990.md
Covers: GenerateSkillModal (GenerateEntityModal.jsx via GenerateSkillModal.jsx)

Shares the modal-shell behavior with the Agent flow
(tests/ui/agents/test_agent_build_with_ai.py) via
GenerateEntityModalPageBase — but is a genuinely separate business object
(Skill, not Agent): distinct entry point, endpoint, and review-form field
set (Name/Description/Instructions only — no Welcome Message/conversation
starters).

Markers:
    - ui: requires browser
    - skills: skill-related tests
    - p2: medium priority (case priority: medium)

Usage:
    cd automation
    pytest tests/ui/skills/test_skill_build_with_ai.py -v
"""

import re

import allure
import pytest

from pages.skills_list_page import SkillsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.generate_skill_modal_page import GenerateSkillModalPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15000
GENERATE_RESPONSE_TIMEOUT = 15000
LOADING_STATE_TIMEOUT = 3000
REVIEW_FORM_TIMEOUT = 15000
CREATE_RESPONSE_TIMEOUT = 15000

PROMPT_TEXT = (
    "Create a skill that summarizes long customer support transcripts into "
    "a 3-bullet action list for the assigned agent."
)
SIMULATED_ERROR_MESSAGE = "Simulated generation failure for ELITEA-2001"

# Minimal, valid draft payload mirroring the real generate_skill_draft
# response shape (GenerateSkillModal.jsx / GenerateSkillReviewForm.jsx) —
# used for the retry's synthetic recovery (option (b) per the AFS). Unlike
# the Agent draft payload, the Skill review form only surfaces
# Name/Description/Instructions (no welcome_message/conversation_starters).
RETRY_DRAFT_PAYLOAD = {
    "name": "support-transcript-summarizer",
    "description": "Summarizes long customer support transcripts into a 3-bullet action list.",
    "instructions": "You are a support transcript summarizer. Read the transcript and "
                     "produce a structured 3-bullet action-item summary for the assigned agent.",
}


class TestSkillBuildWithAIGenerationFailureRetry:
    """Build with AI (P2): generation failure shows error, prompt is
    preserved, and retry succeeds once the service recovers."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/build_with_ai/ELITEA-2001_build-with-ai-generation-failure-shows-error-and-allows-retry.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_generation_failure_shows_error_and_allows_retry(self, page):
        """Generation failure surfaces an error, preserves the prompt, and a
        retry (via the same Generate button) succeeds once the service
        recovers."""
        list_page = SkillsListPage(page)
        modal = GenerateSkillModalPage(page)

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
        # Step 5 — Click retry / "Generate" button
        # ------------------------------------------------------------------
        with allure.step('Step 5 — Click retry / "Generate" button'):
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


# ---------------------------------------------------------------------------
# ELITEA-1990 — review-form fields editable before creation
# ---------------------------------------------------------------------------

REVIEW_PROMPT_TEXT = (
    "Create a skill that reviews pull request diffs and flags missing test "
    "coverage."
)

# Synthetic draft returned by the mocked generate-draft call — the review
# form is pre-populated with these values before any user edit.
GENERATED_DRAFT_PAYLOAD = {
    "name": "pr-test-coverage-review",
    "description": "Reviews pull request diffs and flags missing test coverage.",
    "instructions": "You are a PR reviewer. Inspect the diff and flag any "
                     "changed code paths that lack corresponding test coverage.",
}

# User edits applied on top of the generated draft — the case's core
# assertion is that these values (not GENERATED_DRAFT_PAYLOAD's) end up on
# the created skill.
EDITED_NAME = "edited-pr-coverage-skill-v2"
EDITED_DESCRIPTION = "Testid-verified edited description for ELITEA-1990."
EDITED_INSTRUCTIONS = "Testid-verified edited instructions for ELITEA-1990."


class TestSkillBuildWithAIReviewFormEditableFields:
    """Build with AI (P2): the generated draft's review-form fields (Name,
    Description, Instructions) accept user edits before creation, and the
    created skill reflects the edited values, not the originally-generated
    ones."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/build_with_ai/ELITEA-1990_generated-skill-draft-fields-are-editable-before-creation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_review_form_fields_are_editable_before_creation(self, page, skill_api):
        """Overwriting the generated draft's Name/Description/Instructions
        in the review form persists the edits, and creating the skill from
        the edited form produces a skill with the edited (not generated)
        values."""
        list_page = SkillsListPage(page)
        modal = GenerateSkillModalPage(page)
        skill_id = None

        try:
            # ------------------------------------------------------------
            # Step 1 — Open modal, enter prompt
            # ------------------------------------------------------------
            with allure.step("Step 1 — Open modal, enter prompt"):
                list_page.navigate_to_create()
                modal.open_modal()

                assert not modal.is_generate_enabled(), (
                    "Generate button should be disabled while the prompt is empty"
                )

                modal.fill_prompt(REVIEW_PROMPT_TEXT)

                assert modal.is_generate_enabled(), (
                    "Generate button should become enabled once the prompt is non-empty"
                )

            # ------------------------------------------------------------
            # Step 2 — Generate the draft, reach the review-form step
            # ------------------------------------------------------------
            with allure.step("Step 2 — Generate the draft, reach the review-form step"):
                modal.mock_generate_success(GENERATED_DRAFT_PAYLOAD)
                response = modal.click_generate_and_wait_for_response(
                    timeout=GENERATE_RESPONSE_TIMEOUT
                )

                assert response.status == 200, (
                    f"Expected the mocked generate-draft request to resolve 200, got {response.status}"
                )
                modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

                assert modal.get_review_name() == GENERATED_DRAFT_PAYLOAD["name"], (
                    "Review form should be pre-populated with the generated draft's name"
                )
                assert modal.get_review_description() == GENERATED_DRAFT_PAYLOAD["description"], (
                    "Review form should be pre-populated with the generated draft's description"
                )
                assert modal.get_review_instructions() == GENERATED_DRAFT_PAYLOAD["instructions"], (
                    "Review form should be pre-populated with the generated draft's instructions"
                )

            # ------------------------------------------------------------
            # Step 3 — Modify the generated Name
            # ------------------------------------------------------------
            with allure.step("Step 3 — Modify the generated Name"):
                modal.set_review_name(EDITED_NAME)

                assert modal.get_review_name() == EDITED_NAME, (
                    "Name field should accept and display the edited value"
                )

            # ------------------------------------------------------------
            # Step 4 — Modify the generated Description
            # ------------------------------------------------------------
            with allure.step("Step 4 — Modify the generated Description"):
                modal.set_review_description(EDITED_DESCRIPTION)

                assert modal.get_review_description() == EDITED_DESCRIPTION, (
                    "Description field should accept and display the edited value"
                )

            # ------------------------------------------------------------
            # Step 5 — Modify the generated Instructions; verify all three
            # edits persist simultaneously
            # ------------------------------------------------------------
            with allure.step("Step 5 — Modify Instructions; verify all three fields hold their edits"):
                modal.set_review_instructions(EDITED_INSTRUCTIONS)

                assert modal.get_review_instructions() == EDITED_INSTRUCTIONS, (
                    "Instructions field should accept and display the edited value"
                )
                # All three edits must be present at once — not just each in
                # isolation immediately after being typed.
                assert modal.get_review_name() == EDITED_NAME
                assert modal.get_review_description() == EDITED_DESCRIPTION
                assert modal.get_review_instructions() == EDITED_INSTRUCTIONS

            # ------------------------------------------------------------
            # Step 6 — Click "Create Skill"
            # ------------------------------------------------------------
            with allure.step('Step 6 — Click "Create Skill"'):
                with page.expect_response(
                    lambda r: "/elitea_core/skills/prompt_lib/" in r.url
                    and r.request.method == "POST",
                    timeout=CREATE_RESPONSE_TIMEOUT,
                ) as create_response_info:
                    modal.approve_button.click()

                create_response = create_response_info.value
                assert create_response.status == 201, (
                    f"Expected skill creation to resolve 201, got {create_response.status}"
                )

            # ------------------------------------------------------------
            # Step 7 — Verify redirect to the created skill's detail page,
            # with the edited (not generated) values
            # ------------------------------------------------------------
            with allure.step("Step 7 — Verify redirect and edited values on the detail page"):
                page.wait_for_url(re.compile(r".*/skills/all/\d+$"), timeout=NAVIGATION_TIMEOUT)

                skill_id_match = re.search(r"/skills/all/(\d+)$", page.url)
                assert skill_id_match, (
                    f"Expected a numeric skill id in the redirect URL, got: {page.url}"
                )
                skill_id = int(skill_id_match.group(1))

                detail_page = SkillDetailPage(page)
                detail_page.wait_for_page_load()

                assert detail_page.get_name() == EDITED_NAME, (
                    "Created skill should show the edited Name, not the generated draft's"
                )
                assert detail_page.get_description() == EDITED_DESCRIPTION, (
                    "Created skill should show the edited Description, not the generated draft's"
                )
                assert detail_page.get_instructions() == EDITED_INSTRUCTIONS, (
                    "Created skill should show the edited Instructions, not the generated draft's"
                )
                # Explicit contrast against the original generated values —
                # this is the case's core assertion (edited, not generated).
                assert detail_page.get_name() != GENERATED_DRAFT_PAYLOAD["name"]
                assert detail_page.get_description() != GENERATED_DRAFT_PAYLOAD["description"]
                assert detail_page.get_instructions() != GENERATED_DRAFT_PAYLOAD["instructions"]
        finally:
            # Cleanup (not a case step — no allure.step needed): delete the
            # created skill via the API (cookie auth), never a raw fetch()
            # from page JS context — that CORS-fails on this app (AFS Known
            # Defect #2).
            if skill_id is not None:
                skill_api.delete_skill(skill_id)
