"""UI Test for "Edit with AI" — skill navigation and error handling (ELITEA-2612).

Covers four independent guarantees on a single seeded skill (no part mutates
it, so all four share ONE skill — unlike ELITEA-2611, which does mutate via
Save):

- Part A — "Refine Prompt" (the wizard's only dismissal-to-prompt-phase
  control) preserves the exact prompt text the user typed, and the field
  stays editable/regenerable afterward.
- Part B — the modal's Close (X) button — the ONLY dismissal control once
  past the prompt phase, since "Cancel" only renders in the prompt phase —
  never applies any uncommitted wizard state; the skill's original
  Name/Description/Instructions survive a full page reload.
- Part C — a generation failure (simulated via a single ``page.route()``
  interception of ``generate_skill_draft``, since no product-side lever
  exists to force a real backend failure) renders the exact backend error
  text, and "Generate Draft" itself — there is no separate "Retry" control —
  successfully retries once the failure condition is removed.
- Part D — empty AND whitespace-only prompts both keep "Generate Draft"
  disabled (disable-only validation, no separate error message — case-text
  drift, see the AFS's Known Defects/Clarification section and filed
  clarification elitea-testing-public#1478); a forced click on the disabled
  button proves the guard is a real onClick gate, not decorative CSS.

Spec: test-specs/skills/l3_edit-with-ai-navigation-error-handling_ELITEA-2612.md

Markers:
    - ui: requires browser
    - skills: skill-related tests
    - p3: low priority per AFS metadata (case priority: medium — a
      navigation/error-handling regression test, not the p0/p1 smoke gate)

Usage:
    cd automation
    pytest tests/ui/skills/test_skill_edit_with_ai_navigation_error_handling.py -v
"""

import json
import time

import allure
import pytest
from pages.ai_edit_skill_modal_page import AIEditSkillModalPage
from pages.skill_detail_page import SkillDetailPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.skills]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15000
GENERATE_RESPONSE_TIMEOUT = 30000  # real LLM call, ~5-20s observed live per the AFS
WIZARD_TIMEOUT = 30000
MODAL_TIMEOUT = 5000

# ---------------------------------------------------------------------------
# Test data (AFS § Test Data)
# ---------------------------------------------------------------------------
SEED_DESCRIPTION = "Original description that should be preserved"
SEED_INSTRUCTIONS = "Original instructions that should be preserved"
VALID_PROMPT = "Improve this skill with better structure"
WHITESPACE_PROMPT = "   "
SIMULATED_ERROR_MESSAGE = "Simulated generation failure for ELITEA-2612 error-handling coverage"

# No PUT to the skill-update endpoint should EVER fire in this test — Parts
# A-D never click Save/Save-as-Version (AFS § Network Behavior).
SKILL_UPDATE_PUT_PATH = "/elitea_core/skill/prompt_lib/"


class TestSkillEditWithAINavigationErrorHandling:
    """Edit with AI (P3): "Refine Prompt" preserves the prompt, Close never
    applies uncommitted wizard state, a generation failure shows the
    backend's exact error with a working retry, and empty/whitespace
    prompts are blocked by disable-only validation."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2612_edit-with-ai-navigation-error-handling.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_edit_with_ai_navigation_and_error_handling(self, page, skill_api):
        """Edit an existing skill via "Edit with AI": verify Refine Prompt
        preserves the prompt, Close discards uncommitted wizard state,
        a simulated generation failure surfaces the backend error with a
        working retry, and empty/whitespace prompts stay blocked."""
        skill_name = f"nav-error-test-skill-{time.time_ns()}"
        skill_id = None

        # Track any PUT to the skill-update endpoint across the WHOLE test —
        # none of Parts A-D ever clicks Save, so this list must stay empty
        # (AFS § Network Behavior — stronger proof than re-reading the page).
        skill_update_puts = []

        def _track_skill_update_put(request):
            if request.method == "PUT" and SKILL_UPDATE_PUT_PATH in request.url:
                skill_update_puts.append(request.url)

        page.on("request", _track_skill_update_put)

        try:
            # ------------------------------------------------------------
            # Setup — seed a throwaway skill (Rule 10: no part of this test
            # mutates the skill — Save is never clicked — but a shared
            # fixture skill still risks collision with other suites reading
            # its fields while this test's modal is open, per the AFS).
            # ------------------------------------------------------------
            created = skill_api.create_skill(
                name=skill_name,
                description=SEED_DESCRIPTION,
                instructions=SEED_INSTRUCTIONS,
            )
            skill_id = created["id"]

            detail_page = SkillDetailPage(page)
            modal = AIEditSkillModalPage(page)

            detail_page.navigate(skill_id)

            # ==============================================================
            # Part A — "Refine Prompt" preserves the prompt text
            # ==============================================================
            with allure.step('Step 1 — Open the skill and click "Edit with AI"'):
                modal.open_modal()

                assert modal.modal.is_visible(), "Edit with AI modal should be open"
                assert modal.prompt_input.is_visible(), "Prompt textarea should be visible"
                assert modal.get_prompt_value() == "", "Prompt textarea should start empty"

            with allure.step("Step 2 — Enter a valid prompt"):
                modal.fill_prompt(VALID_PROMPT)

                assert modal.get_prompt_value() == VALID_PROMPT, (
                    "Prompt textarea should contain exactly the entered text"
                )

            with allure.step('Step 3 — Click "Generate Draft" and wait for the wizard'):
                modal.click_generate_and_wait_for_response(timeout=GENERATE_RESPONSE_TIMEOUT)
                modal.wait_for_wizard_visible(timeout=WIZARD_TIMEOUT)

                assert modal.get_step_indicator_text() == "1. General", (
                    "Wizard should open on '1. General' after generation, got: "
                    f"{modal.get_step_indicator_text()!r}"
                )

            with allure.step('Step 4 — Click "Refine Prompt" — the wizard\'s only return-to-prompt control'):
                modal.click_refine_prompt()

                assert modal.prompt_input.is_visible(), (
                    "Prompt textarea should be visible again after Refine Prompt"
                )

            with allure.step("Step 5 — Verify the original prompt text was preserved"):
                assert modal.get_prompt_value() == VALID_PROMPT, (
                    "Refine Prompt should preserve the exact prompt text typed in Step 2 — "
                    "handleRefinePrompt resets phase/draftData/activeStepIndex/isDraftValid "
                    "but NOT the prompt itself"
                )

            with allure.step("Step 6 — Verify the field is still editable and regenerate"):
                assert modal.is_generate_enabled(), (
                    '"Generate Draft" should be enabled again with the preserved prompt'
                )

                modal.click_generate_and_wait_for_response(timeout=GENERATE_RESPONSE_TIMEOUT)
                modal.wait_for_wizard_visible(timeout=WIZARD_TIMEOUT)

                assert modal.get_step_indicator_text() == "1. General", (
                    "Regeneration from the preserved prompt should succeed a second time — "
                    f"expected the wizard back on '1. General', got: {modal.get_step_indicator_text()!r}"
                )

            # ==============================================================
            # Part B — Close preserves the original skill configuration
            # ==============================================================
            with allure.step("Step 7 — Read the CURRENT column and skill-page baseline"):
                assert modal.get_general_description_current_text() == SEED_DESCRIPTION, (
                    "General step CURRENT column should still show the original "
                    f"(seeded) Description, got: {modal.get_general_description_current_text()!r}"
                )
                assert detail_page.get_description() == SEED_DESCRIPTION, (
                    "Skill detail page (mounted underneath the modal) should still show the "
                    "original Description — nothing has been saved yet"
                )
                assert detail_page.get_instructions() == SEED_INSTRUCTIONS, (
                    "Skill detail page (mounted underneath the modal) should still show the "
                    "original Instructions — nothing has been saved yet"
                )

            with allure.step("Step 8 — Navigate the wizard without applying anything"):
                modal.click_next()

                assert modal.get_step_indicator_text() != "1. General", (
                    "Clicking Next should move the wizard off the General step, got: "
                    f"{modal.get_step_indicator_text()!r}"
                )

            with allure.step("Step 9 — Close the wizard via the modal's Close (X) button"):
                # Source-confirmed gotcha (AFS step 9): renderActions() returns null
                # once phase != PHASES.PROMPT, so the prompt-phase "Cancel" button
                # does not exist here — Close (X) is the only dismissal control.
                modal.close_button.click()
                modal.modal.wait_for(state="hidden", timeout=MODAL_TIMEOUT)

                assert not modal.modal.is_visible(), "Edit with AI modal should be closed"

            with allure.step("Step 10 — Verify the skill's original values are unchanged"):
                assert detail_page.get_name() == skill_name, (
                    "Skill detail page Name should still be the original seeded value"
                )
                assert detail_page.get_description() == SEED_DESCRIPTION, (
                    "Skill detail page Description should still be the original seeded value"
                )
                assert detail_page.get_instructions() == SEED_INSTRUCTIONS, (
                    "Skill detail page Instructions should still be the original seeded value"
                )

            with allure.step("Step 11 — Reload and verify nothing was persisted server-side"):
                page.reload()
                detail_page.wait_for_page_load()

                assert detail_page.get_name() == skill_name, (
                    "After reload, Name should still be the original seeded value"
                )
                assert detail_page.get_description() == SEED_DESCRIPTION, (
                    "After reload, Description should still be the original seeded value — "
                    "confirms no PUT ever persisted the discarded wizard state"
                )
                assert detail_page.get_instructions() == SEED_INSTRUCTIONS, (
                    "After reload, Instructions should still be the original seeded value"
                )

            # ==============================================================
            # Part C — a generation failure shows an error; Generate Draft
            # itself doubles as the Retry control
            # ==============================================================
            with allure.step('Step 13 — Open "Edit with AI" again (fresh)'):
                modal.open_modal()

                assert modal.modal.is_visible(), "Edit with AI modal should reopen"
                assert modal.prompt_input.is_visible(), "Prompt textarea should be visible"

            with allure.step("Step 14 — Enter a valid prompt"):
                modal.fill_prompt(VALID_PROMPT)

                assert modal.get_prompt_value() == VALID_PROMPT

            with allure.step("Step 15 — Simulate a generation failure via network interception"):
                # DECLARED IMPROVISATION (AFS § Automation Hints): no product lever
                # exists to force a real backend generate_skill_draft failure, so a
                # single-shot page.route() interception (times=1) fulfils exactly
                # ONE call with a 500 + JSON error body, then auto-unregisters —
                # the retry in Step 18 hits the REAL backend. Same class of
                # technique already established for reading POST bodies via route
                # interception elsewhere in this page object.
                def _fail_generation_once(route):
                    route.fulfill(
                        status=500,
                        content_type="application/json",
                        body=json.dumps({"error": SIMULATED_ERROR_MESSAGE}),
                    )

                page.route(modal.GENERATE_DRAFT_ROUTE, _fail_generation_once, times=1)
                modal.generate_button.click()

            with allure.step("Step 16 — Verify the error alert shows the exact backend error text"):
                modal.error_alert.wait_for(state="visible", timeout=GENERATE_RESPONSE_TIMEOUT)

                assert (modal.error_alert.text_content() or "").strip() == SIMULATED_ERROR_MESSAGE, (
                    "Error alert should show exactly the mocked 500 body's 'error' field — "
                    "EditEntityModal.jsx round-trips generateError?.data?.error"
                )

            with allure.step('Step 17 — Verify "Retry" is available (Generate Draft IS the retry control)'):
                # There is no separate "Retry" button/testid — confirmed via source
                # read (AFS step 17): on a handleGenerate catch, phase returns to
                # PHASES.PROMPT, so the prompt phase's own Generate Draft button
                # remains visible AND enabled and IS the retry mechanism.
                assert modal.generate_button.is_visible(), (
                    '"Generate Draft" should remain visible after a generation failure'
                )
                assert modal.is_generate_enabled(), (
                    '"Generate Draft" should remain enabled after a generation failure — '
                    "it is the retry control"
                )

            with allure.step("Step 18 — Click Retry (re-click Generate Draft)"):
                # The times=1 route already auto-unregistered after Step 15's
                # single match — this call reaches the real backend.
                modal.generate_button.click()

            with allure.step("Step 19 — Verify the retry succeeds and the error clears"):
                modal.wait_for_wizard_visible(timeout=WIZARD_TIMEOUT)

                assert modal.get_step_indicator_text() == "1. General", (
                    "Retry should succeed — expected the wizard on '1. General', got: "
                    f"{modal.get_step_indicator_text()!r}"
                )
                expect(modal.error_alert).to_have_count(0)

            # ==============================================================
            # Part D — empty/whitespace prompt validation is disable-only
            # (case-text drift — see AFS Known Defects/Clarification,
            # elitea-testing-public#1478)
            # ==============================================================
            with allure.step('Step 20 — Open "Edit with AI" fresh (empty prompt by default)'):
                modal.close_button.click()
                modal.modal.wait_for(state="hidden", timeout=MODAL_TIMEOUT)

                modal.open_modal()

                assert modal.get_prompt_value() == "", (
                    "Prompt textarea should be empty on a fresh open"
                )

            with allure.step('Step 21 — Verify "Generate Draft" is disabled with an empty prompt'):
                assert not modal.is_generate_enabled(), (
                    '"Generate Draft" should be disabled with an empty prompt — '
                    "EditEntityModal.jsx's disabled={!description.trim()}"
                )

            with allure.step("Step 22 — Verify no separate validation message is rendered"):
                # Case-text drift (AFS step 22 / clarification elitea-testing-public#1478):
                # the live product implements disable-only validation, with NO error
                # text ever rendered for an empty prompt. Also covers case step 23
                # ("Generate button is disabled or blocked" — same assertion as Step 21).
                expect(modal.error_alert).to_have_count(0)

            with allure.step("Step 24 — Enter a whitespace-only prompt"):
                modal.fill_prompt(WHITESPACE_PROMPT)

                assert modal.get_prompt_value() == WHITESPACE_PROMPT

            with allure.step('Step 25 — Verify "Generate Draft" is still disabled'):
                assert not modal.is_generate_enabled(), (
                    "A whitespace-only prompt should trigger the SAME disabled condition as "
                    "an empty prompt — .trim() on '   ' is falsy"
                )

            with allure.step("Step 26 — Force-click the disabled button; verify no generation triggers"):
                # Defense-in-depth: proves the disabled attribute isn't merely
                # decorative — MUI's native <button disabled> suppresses the click
                # event before React's onClick handler runs, even under a forced
                # Playwright click.
                modal.generate_button.click(force=True)

                expect(modal.loading_indicator).to_have_count(0)
                assert modal.prompt_input.is_visible(), (
                    "Modal should remain on the prompt-input step — no generation was triggered"
                )

            # ------------------------------------------------------------
            # Cross-cutting — no PUT to the skill-update endpoint EVER
            # fired across the whole test (AFS § Network Behavior)
            # ------------------------------------------------------------
            assert skill_update_puts == [], (
                "No PUT to the skill-update endpoint should have fired — Parts A-D never "
                f"click Save/Save-as-Version, but observed: {skill_update_puts}"
            )
        finally:
            page.remove_listener("request", _track_skill_update_put)
            # Cleanup (not a case step — no allure.step needed): delete the
            # seeded skill via the API (cookie/Bearer auth), same convention
            # as ELITEA-2611's AFS.
            if skill_id is not None:
                skill_api.delete_skill(skill_id)
