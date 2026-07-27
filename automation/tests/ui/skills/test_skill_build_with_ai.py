"""UI Tests for the Skill "Build with AI" generation flow.

Covers ELITEA-2001: generation failure shows an error, preserves the
entered prompt, and a retry (re-clicking the same Generate button) succeeds
once the service recovers.

Covers ELITEA-1990: the generated draft's review-form fields (Name,
Description, Instructions) are editable before creation, and the skill is
created with the edited values (not the originally-generated ones).

Covers ELITEA-1989 (extend-existing gap fill): the loading state shown
during generation displays the exact text "Generating skill draft...", and
the resulting review form shows only Name/Description/Instructions — no
tools/agents/pipelines/toolkits/MCPs/resources section is rendered.

Covers ELITEA-1988 (extend-existing gap fill): standalone, first-class
visibility assertions that clicking "Build with AI" opens the modal, and
that the modal displays a prompt input, a "Generate" button, and a
"Cancel" button — the latter never referenced by any other test in this
file before this gap fill.

Covers ELITEA-1991 (extend-existing gap fill): clicking "Create Skill"
directly on an unmodified generated draft (no edits) persists the
*generated* values verbatim, redirects to the Skill details page showing
those values, and the new skill appears in the Skills list — the
through-line ELITEA-1990's test does not cover, since that test always
edits the review form before creating.

Spec: test-specs/skills/l2_build-with-ai-generation-failure-retry_ELITEA-2001.md
Spec: test-specs/skills/l2_generated-skill-draft-fields-are-editable-before-creation_ELITEA-1990.md
Spec: test-specs/skills/lextend_skill-draft-generated-from-natural-language-description_ELITEA-1989.md
Spec: test-specs/skills/lextend_clicking-build-with-ai-opens-the-generation-modal_ELITEA-1988.md
Spec: test-specs/skills/lextend_create-skill-from-draft-saves-and-redirects-to-skill-details_ELITEA-1991.md
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

# ---------------------------------------------------------------------------
# ELITEA-1991 — create skill from an unmodified draft
# ---------------------------------------------------------------------------

UNMODIFIED_PROMPT_TEXT = (
    "Create a skill that reviews changelog entries and rewrites them in a "
    "consistent, user-facing tone."
)

# Distinct from GENERATED_DRAFT_PAYLOAD (ELITEA-1990) so the two sibling
# tests never share created-skill names, even though route mocks are
# scoped per-page and don't actually collide.
UNMODIFIED_DRAFT_PAYLOAD = {
    "name": "changelog-editor",
    "description": "Reviews and rewrites changelog entries in a consistent, "
                    "user-facing tone.",
    "instructions": "You are a changelog editor. Rewrite technical commit "
                     "messages and internal notes into clear, benefit-focused "
                     "updates that help users understand what changed and why "
                     "it matters.",
}


class TestSkillBuildWithAIReviewFormEditableFields:
    """Build with AI (P2): the generated draft's review-form fields (Name,
    Description, Instructions) accept user edits before creation, and the
    created skill reflects the edited values, not the originally-generated
    ones.

    Also covers ELITEA-1989 (extend-existing gap fill, see
    ``test_loading_state_shows_exact_text_and_review_form_has_no_extra_sections``
    below): the loading state's exact text during generation, and the
    absence of any tools/agents/pipelines/toolkits/MCPs/resources section on
    the review form.

    Also covers ELITEA-1991 (extend-existing gap fill, see
    ``test_create_skill_from_unmodified_draft_persists_generated_values``
    below): clicking "Create Skill" with the review form left completely
    unmodified persists the *generated* values verbatim, and the created
    skill is visible in the Skills list — the two gaps this sibling class's
    always-edit test does not cover."""

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

    # ------------------------------------------------------------------
    # ELITEA-1991 — extend-existing gap fill: create skill from an
    # unmodified draft (no edits at all), verify the *generated* values
    # persist on the detail page, and verify the new skill appears in the
    # Skills list. All handles reused from the sibling ELITEA-1990 test
    # above; no new testids or locators added by this test.
    # ------------------------------------------------------------------

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/build_with_ai/ELITEA-1991_create-skill-from-draft-saves-and-redirects-to-skill-details.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_create_skill_from_unmodified_draft_persists_generated_values(self, page, skill_api):
        """Clicking "Create Skill" directly on a freshly generated draft —
        with no edits to Name/Description/Instructions — creates the skill
        with the generated values verbatim, redirects to its detail page
        showing those values, and the new skill appears in the Skills
        list."""
        list_page = SkillsListPage(page)
        modal = GenerateSkillModalPage(page)
        skill_id = None

        console_warnings = []
        page.on(
            "console",
            lambda msg: console_warnings.append(msg.text) if msg.type == "warning" else None,
        )

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

                modal.fill_prompt(UNMODIFIED_PROMPT_TEXT)

                assert modal.is_generate_enabled(), (
                    "Generate button should become enabled once the prompt is non-empty"
                )

            # ------------------------------------------------------------
            # Step 2 — Generate the draft, reach the review-form step
            # ------------------------------------------------------------
            with allure.step("Step 2 — Generate the draft, reach the review-form step"):
                modal.mock_generate_success(UNMODIFIED_DRAFT_PAYLOAD)
                response = modal.click_generate_and_wait_for_response(
                    timeout=GENERATE_RESPONSE_TIMEOUT
                )

                assert response.status == 200, (
                    f"Expected the mocked generate-draft request to resolve 200, got {response.status}"
                )
                modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

            # ------------------------------------------------------------
            # Step 3 — Review the generated Name/Description/Instructions
            # without modifying any of them
            # ------------------------------------------------------------
            with allure.step("Step 3 — Review generated values without modifying them"):
                generated_name = modal.get_review_name()
                generated_description = modal.get_review_description()
                generated_instructions = modal.get_review_instructions()

                assert generated_name == UNMODIFIED_DRAFT_PAYLOAD["name"], (
                    "Review form should be pre-populated with the generated draft's name"
                )
                assert generated_description == UNMODIFIED_DRAFT_PAYLOAD["description"], (
                    "Review form should be pre-populated with the generated draft's description"
                )
                assert generated_instructions == UNMODIFIED_DRAFT_PAYLOAD["instructions"], (
                    "Review form should be pre-populated with the generated draft's instructions"
                )
                # No set_review_*() calls anywhere in this test — the point
                # is to leave the review form entirely untouched.

            # ------------------------------------------------------------
            # Step 4 — Click "Create Skill" with no edits made
            # ------------------------------------------------------------
            with allure.step('Step 4 — Click "Create Skill" with no edits'):
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
                assert not console_warnings, (
                    f"Expected zero console warnings during skill creation, got: {console_warnings}"
                )

            # ------------------------------------------------------------
            # Step 5 — Verify redirect to the created skill's detail page
            # ------------------------------------------------------------
            with allure.step("Step 5 — Verify redirect to the Skill details page"):
                page.wait_for_url(re.compile(r".*/skills/all/\d+$"), timeout=NAVIGATION_TIMEOUT)

                skill_id_match = re.search(r"/skills/all/(\d+)$", page.url)
                assert skill_id_match, (
                    f"Expected a numeric skill id in the redirect URL, got: {page.url}"
                )
                skill_id = int(skill_id_match.group(1))

            # ------------------------------------------------------------
            # Step 6 — Verify the detail page holds the generated
            # (unmodified) values — the contrast with ELITEA-1990, which
            # proves edited values win
            # ------------------------------------------------------------
            with allure.step("Step 6 — Verify detail page shows the generated values, unmodified"):
                detail_page = SkillDetailPage(page)
                detail_page.wait_for_page_load()

                assert detail_page.get_name() == generated_name, (
                    "Created skill should show the generated Name, unmodified"
                )
                assert detail_page.get_description() == generated_description, (
                    "Created skill should show the generated Description, unmodified"
                )
                assert detail_page.get_instructions() == generated_instructions, (
                    "Created skill should show the generated Instructions, unmodified"
                )

            # ------------------------------------------------------------
            # Step 7 — Navigate to the Skills list and verify the new
            # Skill appears there
            # ------------------------------------------------------------
            with allure.step("Step 7 — Verify the new Skill appears in the Skills list"):
                list_page.navigate()

                assert list_page.skill_exists_in_list(generated_name), (
                    f"Newly created skill {generated_name!r} should appear in the Skills list"
                )
        finally:
            # Cleanup (not a case step — no allure.step needed): delete the
            # created skill via the API (cookie auth), same pattern as the
            # sibling ELITEA-1990 test above.
            if skill_id is not None:
                skill_api.delete_skill(skill_id)

    # ------------------------------------------------------------------
    # ELITEA-1989 — extend-existing gap fill: loading-state exact text +
    # absence of any tools/agents/pipelines/toolkits/MCPs/resources section
    # on the review form. Both handles (`generate-skill-loading-indicator`,
    # the three `review_*_input` fields) already exist on
    # `GenerateSkillModalPage`/`GenerateEntityModalPageBase` — no new
    # testids or locators added by this test.
    # ------------------------------------------------------------------

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/build_with_ai/ELITEA-1989_skill-draft-generated-from-natural-language-description.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_loading_state_shows_exact_text_and_review_form_has_no_extra_sections(self, page):
        """During generation, the loading indicator displays the exact text
        "Generating skill draft...", and once the review form is shown it
        contains only the Name/Description/Instructions fields — no
        tools/agents/pipelines/toolkits/MCPs/resources section renders."""
        list_page = SkillsListPage(page)
        modal = GenerateSkillModalPage(page)

        # ------------------------------------------------------------
        # Step 1 — Open modal, enter prompt
        # ------------------------------------------------------------
        with allure.step("Step 1 — Open modal, enter prompt"):
            list_page.navigate_to_create()
            modal.open_modal()

            modal.fill_prompt(REVIEW_PROMPT_TEXT)

            assert modal.get_prompt_value() == REVIEW_PROMPT_TEXT, (
                "Prompt textarea should display the entered description"
            )

            assert modal.is_generate_enabled(), (
                "Generate button should become enabled once the prompt is non-empty"
            )

        # ------------------------------------------------------------
        # Step 2 — Click Generate; verify the loading state shows the
        # exact text "Generating skill draft..." while generation is in
        # flight (mocked, with the shared base's artificial delay_ms so
        # the transient state is reliably observable — same pattern as
        # ELITEA-2001's retry step).
        # ------------------------------------------------------------
        with allure.step('Step 2 — Verify loading state text during generation'):
            modal.mock_generate_success(GENERATED_DRAFT_PAYLOAD)

            with modal.expect_generate_response(timeout=GENERATE_RESPONSE_TIMEOUT) as response_info:
                modal.generate_button.click()
                modal.wait_for_loading_visible(timeout=LOADING_STATE_TIMEOUT)

                assert modal.loading_indicator.text_content() == "Generating skill draft...", (
                    "Loading indicator should display the exact text "
                    "'Generating skill draft...' while a draft is being generated"
                )

            response = response_info.value
            assert response.status == 200, (
                f"Expected the mocked generate-draft request to resolve 200, got {response.status}"
            )
            modal.wait_for_review_form(timeout=REVIEW_FORM_TIMEOUT)

        # ------------------------------------------------------------
        # Step 3 — Verify the review form shows only the three known
        # fields, and no tools/agents/pipelines/toolkits/MCPs/resources
        # section is present anywhere in the dialog.
        # ------------------------------------------------------------
        with allure.step("Step 3 — Verify no extra sections render on the review form"):
            forbidden_terms_pattern = re.compile(
                r"\b(tools?|agents?|pipelines?|toolkits?|mcps?|resources?)\b",
                re.IGNORECASE,
            )
            dialog_text = modal.modal.text_content() or ""
            forbidden_match = forbidden_terms_pattern.search(dialog_text)
            matched_term = forbidden_match.group(0) if forbidden_match else ""

            assert forbidden_match is None, (
                "Review form should not render a tools/agents/pipelines/toolkits/"
                f"MCPs/resources section, but found forbidden term {matched_term!r} "
                "in the dialog"
            )


# ---------------------------------------------------------------------------
# ELITEA-1988 — extend-existing gap fill: standalone, first-class visibility
# assertions that clicking "Build with AI" opens the modal, and that the
# modal's prompt input, Generate button, and Cancel button are all visible.
# All four handles already exist on GenerateSkillModalPage/
# GenerateEntityModalPageBase — no new testids or locators added by this
# test. The Cancel button (`generate-skill-cancel-button`) is referenced by
# no other test in this file before this gap fill.
# ---------------------------------------------------------------------------


class TestSkillBuildWithAIModalElements:
    """Build with AI (P1, smoke): clicking "Build with AI" opens the
    generation modal, and the modal displays the expected static elements —
    a natural-language prompt input, a "Generate" button, and a "Cancel"
    button."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/build_with_ai/ELITEA-1988_clicking-build-with-ai-opens-the-generation-modal.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_build_with_ai_opens_modal_with_expected_elements(self, page):
        """Clicking "Build with AI" opens the modal, and the modal shows a
        prompt input, a "Generate" button, and a "Cancel" button — all
        asserted as explicit, standalone visibility checks (no prompt is
        entered, no network call is made; case never reaches the network
        layer)."""
        list_page = SkillsListPage(page)
        modal = GenerateSkillModalPage(page)

        with allure.step("Step 1-2 — Navigate to New Skill screen, click Build with AI"):
            list_page.navigate_to_create()
            modal.open_modal()

            assert modal.modal.is_visible(), (
                "Build with AI modal should be open after clicking the button"
            )

        with allure.step("Step 3 — Verify prompt input is visible"):
            assert modal.prompt_input.is_visible(), (
                "Natural-language prompt input should be visible in the modal"
            )

        with allure.step("Step 4 — Verify Generate button is visible"):
            assert modal.generate_button.is_visible(), (
                "Generate button should be visible in the modal"
            )

        with allure.step("Step 5 — Verify Cancel button is visible"):
            assert modal.cancel_button.is_visible(), (
                "Cancel button should be visible in the modal"
            )
