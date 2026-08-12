"""UI Test for the Skill "Edit with AI" happy-path workflow (ELITEA-2611).

Covers the complete "Edit with AI" wizard round-trip on an EXISTING skill:
CTA visibility, prompt input, loading state, the 3-step wizard
(General -> Instructions -> Summary) with Current-vs-Suggested comparison
and per-field "Apply changes" checkboxes (checked by default), partial
apply (unchecking one suggestion), Save, and persistence across a full
page reload.

Diff-differs assertions (AFS steps 6/7 — "SUGGESTED text differs from
CURRENT text") are verified at the DATA level via the
``generate_skill_draft`` response body, not by reading the rendered
General/Instructions comparison DOM — that content deliberately carries no
data-testid (AFS Automation Hints § Diff-highlighting assertion); the
response body is both the more robust source and exactly what the AFS
calls for ("asserted at the data level").

Spec: test-specs/skills/l2_edit-with-ai-skill-happy-path_ELITEA-2611.md

Markers:
    - ui: requires browser
    - skills: skill-related tests
    - p2: medium priority (case priority: high; happy path within a
      broader "high" TMS priority is scoped p2 by convention — this is a
      single-flow regression test, not the p0/p1 smoke gate)

Usage:
    cd automation
    pytest tests/ui/skills/test_skill_edit_with_ai_happy_path.py -v
"""

import time

import allure
import pytest
from pages.ai_edit_skill_modal_page import AIEditSkillModalPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15000
GENERATE_RESPONSE_TIMEOUT = 30000  # real LLM call, ~5-20s observed live per the AFS
LOADING_STATE_TIMEOUT = 5000
WIZARD_TIMEOUT = 30000
SAVE_RESPONSE_TIMEOUT = 15000

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------
SEED_DESCRIPTION = "Basic description for testing"
SEED_INSTRUCTIONS = "Simple instructions to be enhanced"
EDIT_PROMPT = (
    "Make this skill more detailed and professional. Add better structure "
    "to the instructions."
)


class TestSkillEditWithAIHappyPath:
    """Edit with AI (P2): the full wizard round-trip on an existing skill —
    generate, review General/Instructions with per-field Apply-changes
    checkboxes, partially apply via Summary, Save, and verify persistence
    across a reload."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2611_edit-with-ai-skill-happy-path.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_edit_with_ai_happy_path(self, page, skill_api):
        """Edit an existing skill via "Edit with AI": generate a draft,
        keep Name + Instructions suggestions but uncheck Description
        (keep original), verify the Summary step merges correctly, Save,
        and confirm the partial-apply result persists across a reload."""
        skill_name = f"edit-ai-test-skill-{time.time_ns()}"
        skill_id = None

        try:
            # ------------------------------------------------------------
            # Setup — seed a throwaway skill with known Name/Description/
            # Instructions via the API (Rule 10: this test mutates the
            # skill, so fresh state is genuinely required — not a
            # read-only-eligible observable).
            # ------------------------------------------------------------
            created = skill_api.create_skill(
                name=skill_name,
                description=SEED_DESCRIPTION,
                instructions=SEED_INSTRUCTIONS,
            )
            skill_id = created["id"]

            detail_page = SkillDetailPage(page)
            modal = AIEditSkillModalPage(page)

            # ------------------------------------------------------------
            # Step 1 — Navigate to the skill detail page; verify seeded
            # values are populated
            # ------------------------------------------------------------
            with allure.step("Step 1 — Navigate to the skill detail page"):
                detail_page.navigate(skill_id)

                assert detail_page.get_name() == skill_name, (
                    "Skill detail page should show the seeded Name"
                )
                assert detail_page.get_description() == SEED_DESCRIPTION, (
                    "Skill detail page should show the seeded Description"
                )
                assert detail_page.get_instructions() == SEED_INSTRUCTIONS, (
                    "Skill detail page should show the seeded Instructions"
                )

            # ------------------------------------------------------------
            # Step 2 — Verify the "Edit with AI" button is visible
            # ------------------------------------------------------------
            with allure.step('Step 2 — Verify "Edit with AI" button is visible'):
                assert modal.open_button.is_visible(), (
                    '"Edit with AI" button should be visible in the General section header'
                )

            # ------------------------------------------------------------
            # Step 3 — Click "Edit with AI"; verify the modal and prompt
            # input open
            # ------------------------------------------------------------
            with allure.step('Step 3 — Click "Edit with AI"'):
                modal.open_modal()

                assert modal.modal.is_visible(), "Edit with AI modal should be open"
                assert modal.prompt_input.is_visible(), "Prompt textarea should be visible"
                assert modal.get_prompt_value() == "", "Prompt textarea should start empty"

            # ------------------------------------------------------------
            # Step 4 — Type the edit prompt
            # ------------------------------------------------------------
            with allure.step("Step 4 — Type the edit prompt"):
                modal.fill_prompt(EDIT_PROMPT)

                assert modal.get_prompt_value() == EDIT_PROMPT, (
                    "Prompt textarea should contain exactly the entered text"
                )

            # ------------------------------------------------------------
            # Step 5 — Click "Generate Draft"; verify generation succeeds
            # and capture the request body (skill_id/version_id
            # distinguish this from the Build-with-AI/creation flow) and
            # the response body (source of truth for the diff-differs
            # assertions in Steps 6/7 below)
            # ------------------------------------------------------------
            with allure.step('Step 5 — Click "Generate Draft" and capture the draft response'):
                response, request_body, loading_text = modal.click_generate_and_wait_for_response(
                    timeout=GENERATE_RESPONSE_TIMEOUT
                )

                assert loading_text == "Generating skill draft...", (
                    "Loading indicator should display the exact text "
                    f"'Generating skill draft...' while a draft is being generated, got: {loading_text!r}"
                )
                assert response.status == 200, (
                    f"Expected the generate_skill_draft request to resolve 200, got {response.status}"
                )
                assert request_body is not None, "generate_skill_draft POST body should have been captured"
                assert request_body.get("skill_id") == skill_id, (
                    "generate_skill_draft request body should carry this skill's skill_id "
                    "— the mechanism distinguishing Edit-with-AI from Build-with-AI"
                )
                assert request_body.get("version_id") is not None, (
                    "generate_skill_draft request body should carry a version_id for the Edit flow"
                )

                draft = response.json()

            # ------------------------------------------------------------
            # Step 6 — Wait for generation to finish; verify the wizard's
            # first step is "1. General", the Name/Description checkboxes
            # are checked by default, and the SUGGESTED text differs from
            # CURRENT (data-level, via the captured draft response)
            # ------------------------------------------------------------
            with allure.step("Step 6 — Verify the wizard's General step"):
                modal.wait_for_wizard_visible(timeout=WIZARD_TIMEOUT)

                assert modal.get_step_indicator_text() == "1. General", (
                    f"Expected the wizard to open on '1. General', got: {modal.get_step_indicator_text()!r}"
                )
                assert modal.is_name_checkbox_checked(), (
                    "Name 'Apply changes' checkbox should be checked by default"
                )
                assert modal.is_description_checkbox_checked(), (
                    "Description 'Apply changes' checkbox should be checked by default"
                )

                assert draft.get("description") != SEED_DESCRIPTION, (
                    "AI-suggested Description should differ from the seeded (current) "
                    f"Description — got identical text: {draft.get('description')!r}"
                )

                # Coverage Map rows 10/11 — CURRENT is a read-only display of
                # the original value, SUGGESTED is a genuinely editable
                # field. Asserted structurally (contenteditable attribute)
                # rather than by content, matching the AFS's data-level
                # treatment of the AI-generated SUGGESTED text elsewhere.
                assert modal.get_general_description_current_text() == SEED_DESCRIPTION, (
                    "General step CURRENT column should display the original (seeded) "
                    f"Description, got: {modal.get_general_description_current_text()!r}"
                )
                assert not modal.is_general_description_current_editable(), (
                    "General step CURRENT column should be read-only (no contenteditable "
                    "attribute)"
                )
                assert modal.is_general_description_suggested_editable(), (
                    "General step SUGGESTED column should be editable (contenteditable=true)"
                )

            # ------------------------------------------------------------
            # Step 7 — Navigate to the Instructions step; verify the
            # checkbox is checked by default and the suggestion differs
            # (data-level)
            # ------------------------------------------------------------
            with allure.step("Step 7 — Navigate to the Instructions step"):
                modal.click_next()

                assert modal.get_step_indicator_text() == "2. Instructions", (
                    f"Expected '2. Instructions', got: {modal.get_step_indicator_text()!r}"
                )
                assert modal.is_instructions_checkbox_checked(), (
                    "Instructions 'Apply changes' checkbox should be checked by default"
                )
                assert draft.get("instructions") != SEED_INSTRUCTIONS, (
                    "AI-suggested Instructions should differ from the seeded (current) "
                    f"Instructions — got identical text: {draft.get('instructions')!r}"
                )

            # ------------------------------------------------------------
            # Step 8 — Return to the General step and uncheck the
            # Description checkbox (keep the original description); Name
            # stays checked
            # ------------------------------------------------------------
            with allure.step("Step 8 — Uncheck Description on the General step"):
                modal.click_previous()

                assert modal.get_step_indicator_text() == "1. General", (
                    "Previous should return the wizard to the General step"
                )

                modal.uncheck_description_checkbox()

                assert not modal.is_description_checkbox_checked(), (
                    "Description checkbox should be unchecked after the click"
                )
                assert modal.is_name_checkbox_checked(), (
                    "Name checkbox should remain checked — per-field state persists "
                    "across step navigation"
                )

            # ------------------------------------------------------------
            # Step 9 — Advance to the Summary step (General -> Instructions
            # -> Summary); verify the merged fields reflect each checkbox's
            # state
            # ------------------------------------------------------------
            with allure.step("Step 9 — Verify the Summary step merges per checkbox state"):
                modal.click_next()  # General -> Instructions
                modal.click_next()  # Instructions -> Summary

                assert modal.get_step_indicator_text() == "3. Summary", (
                    f"Expected '3. Summary', got: {modal.get_step_indicator_text()!r}"
                )
                assert modal.get_summary_description() == SEED_DESCRIPTION, (
                    "Summary Description should show the ORIGINAL value — its checkbox "
                    "was unchecked, so the suggestion should NOT carry through"
                )
                assert modal.get_summary_instructions() == draft.get("instructions"), (
                    "Summary Instructions should show the AI-SUGGESTED value — its "
                    "checkbox stayed checked"
                )
                assert modal.get_summary_name() == (draft.get("name") or ""), (
                    "Summary Name should show the AI-suggested name (checked, "
                    "typically unchanged from current for this prompt) — mirrors "
                    "SummaryStep.jsx's mergedName formula exactly"
                )

            # ------------------------------------------------------------
            # Step 10 — Click "Save"; verify the toast, the skill-update
            # PUT response, the modal closing, and the detail page showing
            # the correct partial-apply result
            # ------------------------------------------------------------
            with allure.step('Step 10 — Click "Save" and verify the partial-apply result'):
                save_response = modal.click_save_and_wait_for_response(timeout=SAVE_RESPONSE_TIMEOUT)

                assert save_response.status == 200, (
                    f"Expected the skill-update PUT to resolve 200, got {save_response.status}"
                )

                detail_page.toast_message.wait_for(state="visible", timeout=SAVE_RESPONSE_TIMEOUT)
                assert detail_page.toast_message.text_content() == "Skill saved", (
                    'Expected the "Skill saved" toast after Save'
                )
                modal.modal.wait_for(state="hidden", timeout=SAVE_RESPONSE_TIMEOUT)

                detail_page.wait_for_page_load()

                assert detail_page.get_description() == SEED_DESCRIPTION, (
                    "Detail page Description should still be the ORIGINAL value "
                    "(unchecked -> NOT applied)"
                )
                # Instructions verified via the API, not the CodeMirror DOM:
                # confirmed live that CodeMirror only renders the VIEWPORT's
                # lines for long content (view-based virtualization) — a
                # multi-paragraph AI-generated instructions block silently
                # truncates under text_content()/inner_text() alike, unlike
                # the short seeded/description text. Same "assert at the
                # data level for AI-generated content" reasoning the AFS
                # already applies to the diff-differs checks (Automation
                # Hints § Diff-highlighting assertion), and a strictly
                # stronger persistence proof than a DOM read.
                saved_skill = skill_api.get_skill(skill_id)
                assert saved_skill["version_details"]["instructions"] == draft.get("instructions"), (
                    "Persisted skill Instructions should now be the AI-generated content "
                    "(checked -> applied)"
                )

            # ------------------------------------------------------------
            # Step 11 — Reload the skill detail page; verify the
            # partial-apply result persisted server-side, not just in
            # local Formik state
            # ------------------------------------------------------------
            with allure.step("Step 11 — Reload and verify persistence"):
                page.reload()
                detail_page.wait_for_page_load()

                assert detail_page.get_description() == SEED_DESCRIPTION, (
                    "After reload, Description should still be the ORIGINAL value"
                )
                # Same API-level read as Step 10 (CodeMirror viewport
                # virtualization truncates a long DOM read) — re-fetches
                # from the server AFTER the reload, so this still proves
                # the partial-apply result is server-side, not local state.
                reloaded_skill = skill_api.get_skill(skill_id)
                assert reloaded_skill["version_details"]["instructions"] == draft.get("instructions"), (
                    "After reload, Instructions should still be the AI-generated content — "
                    "confirms the partial apply persisted server-side"
                )
        finally:
            # Cleanup (not a case step — no allure.step needed): delete the
            # seeded skill via the API (cookie/Bearer auth), never a raw
            # fetch() DELETE from page JS context — that CORS-fails on
            # this backend's Keycloak forward-auth path (AFS § Cleanup).
            if skill_id is not None:
                skill_api.delete_skill(skill_id)
