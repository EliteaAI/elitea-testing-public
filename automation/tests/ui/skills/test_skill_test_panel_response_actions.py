"""Test — Read aloud and Copy to clipboard are enabled on test panel responses.

Verifies that once a SkillTestPanel response completes, the "Read aloud"
(chat-read-out-button) and "Copy to clipboard" (chat-copy-button) action
buttons on that response are both enabled AND genuinely clickable — not just
non-disabled. Two layers of proof per button: (a) state — `is_enabled()`,
(b) behavior — actually clicking and observing the real effect (copy toast /
voice mini-player mount).

Test case: ELITEA-2442
AFS: test-specs/skills/l3_test-panel-response-actions-enabled_ELITEA-2442.md
"""

import logging
import time

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 30_000
ACTION_TIMEOUT = 10_000


class TestSkillTestPanelResponseActions:
    """ELITEA-2442 — Read aloud / Copy to clipboard enabled+clickable on test-panel responses."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2442_read-aloud-and-copy-to-clipboard-are-enabled-on-test-p.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_test_panel_response_actions_enabled(self, page, skill_api):
        """Read aloud and Copy to clipboard are enabled and clickable on a
        completed test-panel response."""
        ts = int(time.time())
        skill_name = f"autotest-2442-{ts}"[:32]
        skill_id = None
        test_message = "Reply with the single word: PONG"

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Step 1 — Open a Skill and run a test prompt in the test panel"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=skill_name,
                    instructions=test_message,
                    description="Autotest skill for ELITEA-2442 test-panel response actions.",
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

                initial_count = detail_page.get_test_message_count()
                detail_page.send_test_message(test_message)

            with allure.step("Step 2 — Wait for a response to appear"):
                detail_page.wait_for_test_response(
                    initial_count=initial_count,
                    timeout=AI_RESPONSE_TIMEOUT,
                )
                response = detail_page.get_last_test_response()
                assert response, "Expected a non-empty test-panel response"

            with allure.step(
                'Step 3 — Verify "Read aloud" and "Copy to clipboard" are active '
                "and clickable (not grayed out or disabled)"
            ):
                # Layer 1 — state: both buttons enabled, not disabled.
                detail_page.read_out_button.wait_for(state="visible", timeout=ACTION_TIMEOUT)
                detail_page.copy_action_button.wait_for(state="visible", timeout=ACTION_TIMEOUT)
                assert detail_page.read_out_button.is_enabled(), (
                    "Expected 'Read aloud' button to be enabled on the completed response"
                )
                assert detail_page.copy_action_button.is_enabled(), (
                    "Expected 'Copy to clipboard' button to be enabled on the completed response"
                )

                # Layer 2 — behavior: clicking each produces its real effect.
                # Copy to clipboard -> toast "The message has been copied to
                # the clipboard." (version_toast_message reuses the app-wide
                # toast-message testid, already wired on this page).
                detail_page.copy_action_button.click()
                detail_page.version_toast_message.wait_for(state="visible", timeout=ACTION_TIMEOUT)
                toast_text = (detail_page.version_toast_message.text_content() or "").strip()
                assert "copied to the clipboard" in toast_text.lower(), (
                    f"Expected a 'copied to the clipboard' toast, got: {toast_text!r}"
                )

                # Read aloud -> voice mini-player mounts.
                detail_page.read_out_button.click()
                detail_page.voice_mini_player.first.wait_for(state="visible", timeout=ACTION_TIMEOUT)
                assert detail_page.voice_mini_player.first.is_visible(), (
                    "Expected the voice mini-player to appear after clicking 'Read aloud'"
                )

                # Stop TTS playback so it doesn't keep "playing" into teardown.
                detail_page.voice_play_stop_button.click()

            with allure.step(
                "Side-channel check — no console errors across the case's own 3 steps"
            ):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )

        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(int(skill_id))
                    logger.info("Deleted skill id=%s via API", skill_id)
