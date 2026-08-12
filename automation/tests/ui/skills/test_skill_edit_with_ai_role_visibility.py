"""UI Tests for "Edit with AI" — Skill Permissions (ELITEA-2613).

Covers two independently-provable halves of the case's contract:

- Part A — the "Edit with AI" CTA is visible, correctly labelled, and
  functional (opens the wizard) for the admin-equivalent ``TEST_USER`` role
  on a skill's detail page. Mirrors ``test_agent_build_with_ai_role_visibility``
  (ELITEA-1903)'s admin-only scope note below.
- Part D — the wizard's Summary-step Instructions field enforces a
  **5,000-character** limit via **silent native ``maxLength`` truncation**,
  not the case text's stale 2,500-char / "error message" framing (case-text
  drift — filed elitea-testing-public#1480; the live product is correct,
  the case text is not). Save succeeds with the truncated value — there is
  no separate over-limit block/error state (reverse-masking guard: this test
  asserts the LIVE contract, not the stale case text).

Scope note (Part B/C — Editor-role and Viewer-role halves): OUT OF SCOPE for
this spec. No ``EDITOR_TEST_USER_*``/``VIEWER_TEST_USER_*`` credential exists
in this environment — identical gap to ELITEA-1903/1904, tracked centrally at
EliteaAI/elitea-testing-public#1314 (commented to link ELITEA-2613 as a third
blocked case). The case's core RBAC-gating mechanism
(``checkPermission(...)`` reading ``GET /api/v2/auth/permissions/prompt_lib/
{project_id}``) is nonetheless fully verified here for one authenticated
role, both via live UI observation and source-code confirmation of the
gating logic itself — see the AFS § Blocked Steps.

Spec: test-specs/skills/l2_edit-with-ai-skill-permissions_ELITEA-2613.md
Covers: AIEditSkillModal.jsx (open button visibility), SummaryStep.jsx
(``MAX_INSTRUCTIONS_LENGTH`` native maxLength truncation)

Markers:
    - ui: requires browser
    - skills: skill-related tests
    - p2: medium priority (case priority: l2)

Usage:
    cd automation
    pytest tests/ui/skills/test_skill_edit_with_ai_role_visibility.py -v
"""

import time

import allure
import pytest
from pages.ai_edit_skill_modal_page import AIEditSkillModalPage
from pages.skill_detail_page import SkillDetailPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15000
MODAL_TIMEOUT = 5000
GENERATE_RESPONSE_TIMEOUT = 30000  # real LLM call, ~5-20s observed live per the AFS
WIZARD_TIMEOUT = 30000
SAVE_RESPONSE_TIMEOUT = 15000

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------
SEED_DESCRIPTION = "Basic description for role-visibility/character-limit testing"
SEED_INSTRUCTIONS = "Simple seed instructions"
EDIT_PROMPT = "Add more structure and detail to these instructions."
EXPECTED_MODAL_HEADING = "Edit with AI"

# AFS Expected Results / Clarification (elitea-testing-public#1480): the
# ACTUAL live limit is 5,000 chars (MAX_INSTRUCTIONS_LENGTH,
# EliteaUI/src/common/constants.js:68), not the case text's stale 2,500 —
# reverse-masking guard: assert the live contract, not the case text.
MAX_INSTRUCTIONS_LENGTH = 5000
OVER_LIMIT_INSTRUCTIONS = "A" * (MAX_INSTRUCTIONS_LENGTH + 10)  # 10 over the real limit


class TestSkillEditWithAIRoleVisibility:
    """Edit with AI (L2): CTA visibility is RBAC-gated — verified live here
    for the admin-equivalent role (Part A). Editor/Viewer halves are out of
    scope for this spec (see module docstring)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2613_edit-with-ai-skill-permissions.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_edit_with_ai_button_visible_for_admin_role(self, page, skill_api):
        """"Edit with AI" CTA is visible, correctly labelled, and functional
        (opens the wizard) for the admin-equivalent TEST_USER on a skill's
        detail page; closing the wizard produces zero new console errors."""
        skill_name = f"role-vis-test-skill-{time.time_ns()}"
        skill_id = None

        console_errors = []

        def _on_console(msg):
            if msg.type == "error":
                console_errors.append(msg)

        page.on("console", _on_console)

        try:
            created = skill_api.create_skill(
                name=skill_name,
                description=SEED_DESCRIPTION,
                instructions=SEED_INSTRUCTIONS,
            )
            skill_id = created["id"]

            list_page = SkillsListPage(page)
            detail_page = SkillDetailPage(page)
            modal = AIEditSkillModalPage(page)

            with allure.step(
                "Step 1 — Authenticate as TEST_USER (admin-equivalent role), "
                "verify dashboard/app shell loads"
            ):
                # The `auth_state` fixture already authenticated TEST_USER via
                # VITE_DEV_TOKEN before this test started (localhost bypass —
                # conftest.py). Navigating to the Skills dashboard is the
                # live confirmation the session is authenticated and the app
                # shell renders.
                list_page.navigate()

                assert list_page.page_header.is_visible(), (
                    "Skills dashboard header should be visible once authenticated"
                )

            with allure.step("Step 2 — Open an existing skill's detail page"):
                detail_page.navigate(skill_id)

                assert f"/skills/all/{skill_id}" in page.url, (
                    f"Expected to land on the skill detail page, got {page.url}"
                )
                assert detail_page.information_section.is_visible(), (
                    "Skill detail General/Information section should be present"
                )

            with allure.step('Step 3 — Verify "Edit with AI" CTA/button is visible'):
                assert modal.open_button.is_visible(), (
                    "edit-skill-with-ai-button should be visible in the skill "
                    "detail General section header for the admin-equivalent role"
                )

            with allure.step('Step 4 — Click "Edit with AI"; verify the wizard opens'):
                modal.open_modal(timeout=MODAL_TIMEOUT)

                assert modal.modal.is_visible(), "Edit with AI modal should be open"
                modal_text = modal.modal.text_content() or ""
                assert EXPECTED_MODAL_HEADING in modal_text, (
                    f"Modal should show the {EXPECTED_MODAL_HEADING!r} heading, "
                    f"got: {modal_text!r}"
                )
                assert modal.prompt_input.is_visible(), "Prompt textarea should be visible"
                assert not modal.is_generate_enabled(), (
                    '"Generate Draft" should start disabled with an empty prompt'
                )

            with allure.step("Step 6 — Close the wizard; verify zero new console errors"):
                page.keyboard.press("Escape")
                modal.modal.wait_for(state="hidden", timeout=MODAL_TIMEOUT)

                assert not modal.modal.is_visible(), "Edit with AI modal should be closed"
                assert not console_errors, (
                    "Expected zero console errors after closing the wizard, got: "
                    f"{[m.text for m in console_errors]}"
                )
        finally:
            page.remove_listener("console", _on_console)
            if skill_id is not None:
                skill_api.delete_skill(skill_id)


class TestSkillEditWithAICharacterLimit:
    """Edit with AI (L2, Part D): the wizard's Summary-step Instructions
    field enforces the character limit via silent native truncation, and
    Save succeeds with the truncated value — see module docstring for the
    case-text-drift clarification (elitea-testing-public#1480)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2613_edit-with-ai-skill-permissions.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_edit_with_ai_summary_instructions_truncates_at_character_limit(self, page, skill_api):
        """Entering text past MAX_INSTRUCTIONS_LENGTH into the wizard's
        Summary-step Instructions field truncates it to exactly 5,000
        characters (not the case text's stale 2,500), and Save succeeds
        with the truncated value — there is no separate over-limit block."""
        skill_name = f"char-limit-test-skill-{time.time_ns()}"
        skill_id = None

        try:
            created = skill_api.create_skill(
                name=skill_name,
                description=SEED_DESCRIPTION,
                instructions=SEED_INSTRUCTIONS,
            )
            skill_id = created["id"]

            detail_page = SkillDetailPage(page)
            modal = AIEditSkillModalPage(page)

            with allure.step("Step 16 — Log in as Admin, open the skill"):
                detail_page.navigate(skill_id)

                assert detail_page.information_section.is_visible(), (
                    "Skill detail General/Information section should be present"
                )

            with allure.step(
                'Step 17 — Open "Edit with AI", fill a non-empty prompt, '
                "click Generate Draft"
            ):
                modal.open_modal(timeout=MODAL_TIMEOUT)
                modal.fill_prompt(EDIT_PROMPT)

                assert modal.get_prompt_value() == EDIT_PROMPT

                response, _, _ = modal.click_generate_and_wait_for_response(
                    timeout=GENERATE_RESPONSE_TIMEOUT
                )
                modal.wait_for_wizard_visible(timeout=WIZARD_TIMEOUT)

                assert response.status == 200, (
                    f"generate_skill_draft should respond 200, got {response.status}"
                )
                # Wizard's visible step SET is computed from which sections the
                # draft actually diffs from CURRENT (EliteaUI
                # skillAIEditionSteps.helpers.js's computeVisibleSteps) — a
                # General step with no Name/Description diff is skipped
                # entirely, so the wizard may legitimately open on either
                # "1. General" or "1. Instructions" depending on what this
                # LLM call happened to change. Only "Summary" is guaranteed
                # to always render (last step, always pushed).
                opening_step = modal.get_step_indicator_text()
                assert opening_step in ("1. General", "1. Instructions"), (
                    f"Wizard should open on the first visible step, got: {opening_step!r}"
                )

            with allure.step("Step 18 — Advance to the Summary step"):
                # Click Next until Summary is reached — robust to the
                # variable step count/numbering noted above: Summary is
                # ALWAYS the last step (computeVisibleSteps always pushes
                # it), but its numeral prefix is
                # `${activeStepIndex + 1}. ${label}` (EditEntityStepIndicator.jsx)
                # — positional, so it reads "2. Summary" when General was
                # skipped or "3. Summary" when all three steps render.
                for _ in range(3):
                    if "Summary" in modal.get_step_indicator_text():
                        break
                    modal.click_next()

                assert "Summary" in modal.get_step_indicator_text(), (
                    "Wizard should be on the Summary step, got: "
                    f"{modal.get_step_indicator_text()!r}"
                )
                assert modal.summary_instructions_input.is_visible(), (
                    "Summary step's merged Instructions field should be visible"
                )
                assert modal.summary_instructions_input.is_editable(), (
                    "Summary step's merged Instructions field should be editable"
                )

            with allure.step(
                "Step 19 — Fill 5,010 characters (10 over the real 5,000 limit); "
                "verify the field silently truncates to exactly 5,000"
            ):
                modal.summary_instructions_input.fill(OVER_LIMIT_INSTRUCTIONS)
                truncated_value = modal.get_summary_instructions()

                assert len(truncated_value) == MAX_INSTRUCTIONS_LENGTH, (
                    f"Field should silently truncate to exactly {MAX_INSTRUCTIONS_LENGTH} "
                    f"characters via the native maxLength attribute, got "
                    f"{len(truncated_value)} — a truncation boundary off-by-one "
                    "(4999/5001) would slip through a loose length check"
                )

            with allure.step(
                "Step 20/21 — Save; verify it succeeds with the truncated value "
                "(no separate over-limit block/error path exists)"
            ):
                response = modal.click_save_and_wait_for_response(timeout=SAVE_RESPONSE_TIMEOUT)

                assert response.status == 200, (
                    f"Save should succeed with the truncated (<= {MAX_INSTRUCTIONS_LENGTH}-char) "
                    f"value — there is no distinct 'blocked' state per source read "
                    f"(SummaryStep.jsx's native maxLength IS the enforcement), got status "
                    f"{response.status}"
                )

                saved_skill = skill_api.get_skill(skill_id)
                saved_instructions = saved_skill["version_details"]["instructions"]
                assert len(saved_instructions) == MAX_INSTRUCTIONS_LENGTH, (
                    "Persisted instructions should be exactly the truncated "
                    f"{MAX_INSTRUCTIONS_LENGTH} characters, got {len(saved_instructions)}"
                )
        finally:
            # Cleanup: this test's Save mutates the skill (AFS § Cleanup) —
            # use a dedicated disposable skill created and deleted within
            # the test, per the AFS's own recommended alternative, rather
            # than restoring a shared fixture skill's original instructions.
            if skill_id is not None:
                skill_api.delete_skill(skill_id)
