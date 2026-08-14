"""Test — Skill test panel uses the currently selected version's instructions.

Verifies that the SkillTestPanel's AI response reflects the currently
selected version's instructions, not a stale/cached one: switching from
"v1" (instructs "Always say V1") to "base" (instructs "Always say BASE")
and re-running the identical prompt changes the response from "V1" to
"BASE".

Test case: ELITEA-2440
AFS: test-specs/skills/l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md
"""

import logging
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000


class TestSkillTestPanelVersionInstructions:
    """ELITEA-2440 — test panel reflects the currently selected version's instructions."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2440_test-panel-uses-the-currently-selected-skill-versions-instru.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_test_panel_uses_selected_skill_version_instructions(self, page, skill_api):
        """Switching the VERSION selector changes which version's instructions
        the test panel's AI response reflects — v1 ("Always say V1") vs
        base ("Always say BASE") for the identical prompt."""
        ts = int(time.time())
        skill_name = f"autotest-2440-ver-{ts}"[:32]
        skill_id = None
        test_message = "What should you say?"

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Step 1 — Create a Skill with base instructions 'Always say BASE' via the UI form"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=skill_name,
                    instructions="Always say BASE",
                    description="Autotest skill for ELITEA-2440 version-instructions flow.",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = detail_page.get_skill_id()
                assert skill_id, "Expected a numeric Skill ID on the detail page"
                logger.info("Created skill id=%s name=%s", skill_id, skill_name)

            with allure.step(
                "Step 2 — Save As Version 'v1' with instructions 'Always say V1'"
            ):
                detail_page.fill_instructions("Always say V1")
                detail_page.save_as_version("v1")

            with allure.step("Step 3 — Switch to 'v1' in the version selector"):
                detail_page.switch_version("v1")
                assert detail_page.get_version_selector_value() == "v1", (
                    "Expected the VERSION selector to display 'v1'"
                )

            with allure.step('Step 4 — Run test prompt "What should you say?" on v1'):
                initial_count = detail_page.get_test_message_count()
                detail_page.send_test_message(test_message)
                detail_page.wait_for_test_response(
                    initial_count=initial_count,
                    timeout=AI_RESPONSE_TIMEOUT,
                )

            with allure.step('Step 5 — Verify the response contains "V1" (not "BASE")'):
                response_v1 = detail_page.get_last_test_response()
                assert "V1" in response_v1, (
                    f"Expected the v1-version response to contain 'V1', got: {response_v1!r}"
                )
                assert "BASE" not in response_v1, (
                    f"Expected the v1-version response NOT to contain 'BASE', got: {response_v1!r}"
                )

            with allure.step(
                'Step 6 — Switch to "base" and run the same prompt; '
                'verify the response contains "BASE"'
            ):
                detail_page.switch_version("base")
                assert detail_page.get_version_selector_value() == "base", (
                    "Expected the VERSION selector to display 'base'"
                )

                initial_count = detail_page.get_test_message_count()
                detail_page.send_test_message(test_message)
                detail_page.wait_for_test_response(
                    initial_count=initial_count,
                    timeout=AI_RESPONSE_TIMEOUT,
                )
                response_base = detail_page.get_last_test_response()
                assert "BASE" in response_base, (
                    f"Expected the base-version response to contain 'BASE', got: {response_base!r}"
                )
                assert "V1" not in response_base, (
                    f"Expected the base-version response NOT to contain 'V1', got: {response_base!r}"
                )

            with allure.step(
                "Side-channel check — no console errors across the case's own 6 steps"
            ):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )

        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(int(skill_id))
                    logger.info("Deleted skill id=%s via API", skill_id)
