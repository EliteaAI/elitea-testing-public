"""Test for Skill — VERSION dropdown pin/set-as-default control.

Verifies that the per-skill VERSION dropdown shows a pin/set-as-default
control on each version row (static for the current default, hover-revealed
for an eligible non-default row), that clicking it opens a confirmation
dialog, that confirming fires the ``skill_default_version`` PATCH and
returns 200, and that a confirmation toast + persistent pin-icon/reorder
indicator are both shown afterward.

Test case: ELITEA-2437
AFS: test-specs/skills/l3_skill-version-dropdown-set-default_ELITEA-2437.md
"""

import logging
import time

import allure
import pytest
from components.mui import Dialog
from pages.skill_detail_page import SkillDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000


class TestSkillVersionSetDefault:
    """ELITEA-2437 — VERSION dropdown pin/set-as-default control."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2437_skill-version-dropdown-set-default.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_version_dropdown_set_default_shows_control_and_confirmation(self, page, skill_api):
        """Version dropdown shows a pin/set-as-default control per row;
        confirming sets the named version as default and shows a
        confirmation toast plus a persistent pin-icon/reorder indicator."""
        ts = int(time.time())
        skill_name = f"autotest-verdefault-skill-{ts}"[:32]
        skill_id = None

        try:
            with allure.step(
                "Setup — Create the skill via API and add a second version "
                "('ver_1', not a numbered case action per the AFS's Test Data)"
            ):
                skill = skill_api.create_skill(
                    name=skill_name,
                    description="Autotest skill for ELITEA-2437 version-default flow.",
                    instructions="You are a test skill used for version-default automation. Reply 'ok'.",
                )
                skill_id = skill["id"]
                assert skill_id, "Expected a numeric id for the seeded skill"
                logger.info("Created skill id=%s name=%s", skill_id, skill_name)

                detail_page = SkillDetailPage(page)
                detail_page.navigate(skill_id)
                detail_page.save_as_version("ver_1")

            console_errors = []
            page.on(
                "console",
                lambda msg: console_errors.append(msg) if msg.type == "error" else None,
            )

            with allure.step(
                "Step 1 — Open a Skill with multiple versions (base + ver_1, "
                "'base' implicit-default since no explicit default has been set yet)"
            ):
                detail_page.verify_on_detail_page()
                assert f"/skills/all/{skill_id}" in page.url, (
                    f"Expected the skill detail URL to contain /skills/all/{skill_id}, got: {page.url}"
                )

            with allure.step("Step 2 — Open the VERSION dropdown"):
                detail_page.open_version_selector()
                assert detail_page.is_version_option_visible("base"), (
                    "Expected the 'base' version option in the open VERSION dropdown"
                )
                assert detail_page.is_version_option_visible("ver_1"), (
                    "Expected the 'ver_1' version option in the open VERSION dropdown"
                )

            with allure.step(
                "Step 3 — Verify each version row shows a pin/set-as-default control "
                "(static for the current default, hover-revealed for the non-default row)"
            ):
                assert detail_page.is_version_option_pinned("base"), (
                    "The implicit-default 'base' row should show the static pin icon"
                )
                assert detail_page.is_version_option_set_default_control_visible("ver_1"), (
                    "The non-default 'ver_1' row should show a hover-revealed set-as-default control"
                )

            with allure.step(
                "Step 4 — Click the set-as-default control on 'ver_1'; "
                "verify the 'Set as default?' confirmation dialog opens"
            ):
                detail_page.click_version_option_set_default("ver_1")
                dialog = Dialog.wait_for(page, timeout=UI_ELEMENT_TIMEOUT)
                assert Dialog.get_title(dialog) == "Set as default?", (
                    f"Expected the 'Set as default?' dialog heading, got: {Dialog.get_title(dialog)!r}"
                )
                dialog_text = dialog.text_content() or ""
                assert "ver_1 will be automatically used" in dialog_text, (
                    f"Expected the ver_1-specific confirmation body text, got: {dialog_text!r}"
                )

            with allure.step(
                "Step 5 — Confirm the dialog; verify the skill_default_version PATCH returns 200"
            ):
                response = detail_page.confirm_set_default_version(timeout=UI_ELEMENT_TIMEOUT)
                assert response.status == 200, (
                    f"Expected 200 OK from the skill_default_version PATCH, got {response.status}"
                )

            with allure.step(
                "Step 6 — Verify a confirmation message and a persistent indicator are shown"
            ):
                toast_text = detail_page.version_toast_message.text_content() or ""
                assert toast_text == "Default version has been set successfully", (
                    f"Expected the default-version-set toast text, got: {toast_text!r}"
                )

                detail_page.open_version_selector()
                assert detail_page.is_version_option_pinned("ver_1"), (
                    "'ver_1' should now carry the persistent default-pin icon"
                )
                assert not detail_page.is_version_option_pinned("base"), (
                    "'base' should no longer carry the default-pin icon"
                )
                order = detail_page.get_version_option_order(timeout=UI_ELEMENT_TIMEOUT)
                assert order.index("ver_1") < order.index("base"), (
                    f"Expected 'ver_1' sorted above 'base' after becoming default, got order: {order}"
                )

            with allure.step("Side-channel check — no console errors across the full flow"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )

        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(skill_id)
                    logger.info("Deleted skill id=%s", skill_id)
