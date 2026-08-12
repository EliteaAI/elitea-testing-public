"""UI test — Project Context character limit is enforced at 2500 characters.

Verifies the empty-state "Create" flow, that content entry is accepted up to
exactly 2500 characters, that the Save button is enabled at that boundary
(the case's named regression, #5667 — confirmed NOT reproducing on this
build, see the AFS's Known Defects section), that characters beyond the
limit are silently rejected with no console error, and that Save persists
successfully.

Test case: ELITEA-2272
AFS: test-specs/settings-project-params/l2_project-context-character-limit-2500_ELITEA-2272.md
"""

import logging

import allure
import pytest
from api import APIClient
from pages.project_context_page import ProjectContextPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p1, pytest.mark.regression]

MAX_CHARS = 2500
EXPECTED_LIMIT_TEXT = "0 characters left. You have reached the maximum character limit."


class TestProjectContextCharacterLimit:
    """ELITEA-2272 — Project Context character limit is enforced at 2500 characters."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-project-params/ELITEA-2272_project-context-character-limit-2500.md",
        "onetest-ai Test Case link",
    )
    def test_project_context_character_limit_2500(self, page, clean_project_context, api: APIClient):
        """Content is accepted up to exactly 2500 chars; Save stays enabled at
        the boundary, both before and after a rejected extra keystroke; Save
        persists successfully; no console errors throughout."""
        context_page = ProjectContextPage(page)
        console_errors = context_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Precondition already enforced by the clean_project_context "
                "fixture (API DELETE, tolerates 404)"
            ):
                pass

            with allure.step(
                "Step 2 — Navigate to Settings -> Project Context: empty-state "
                "'Create' button is visible"
            ):
                context_page.navigate()
                assert context_page.create_button.is_visible(), (
                    "Expected the empty-state 'Create' button to be visible, "
                    "confirming the page loaded with no existing Project Context"
                )

            with allure.step(
                "Step 3 — Click 'Create': URL becomes ?view=create, editor content "
                "visible, Save is disabled (no edits yet)"
            ):
                context_page.click_create()
                assert "?view=create" in page.url, (
                    f"Expected URL to contain '?view=create', got {page.url!r}"
                )
                assert context_page.editor_content.is_visible(), (
                    "Expected the CodeMirror editor content area to be visible"
                )
                assert not context_page.is_save_enabled(), (
                    "Expected Save to be disabled before any edit (isDirty=false) — "
                    "this is the control condition for the later 'enabled' assertions"
                )

            with allure.step(
                "Step 4 — Enter exactly 2500 characters via clipboard paste: content "
                "length is exactly 2500 and the char counter reads the max-limit text"
            ):
                context_page.set_editor_content_via_paste("A" * MAX_CHARS)
                content_length = context_page.get_editor_content_length()
                assert content_length == MAX_CHARS, (
                    f"Expected editor content length to be exactly {MAX_CHARS}, got {content_length}"
                )
                counter_text = context_page.get_char_counter_text()
                assert counter_text == EXPECTED_LIMIT_TEXT, (
                    f"Expected char counter text {EXPECTED_LIMIT_TEXT!r}, got {counter_text!r}"
                )

            with allure.step(
                "Step 5 — Verify Save is enabled at exactly 2500 characters "
                "(regression #5667)"
            ):
                assert context_page.is_save_enabled(), (
                    "Expected Save to be enabled at the exact 2500-character boundary "
                    "(regression #5667 — confirmed NOT reproducing on this build)"
                )

            with allure.step(
                "Step 6 — Press one additional character with focus still in the "
                "editor: no error thrown"
            ):
                context_page.type_additional_character("B")

            with allure.step(
                "Step 7 — Verify the additional character is silently rejected: "
                "content length still exactly 2500, char counter text unchanged"
            ):
                content_length_after = context_page.get_editor_content_length()
                assert content_length_after == MAX_CHARS, (
                    f"Expected editor content length to remain exactly {MAX_CHARS} after "
                    f"the rejected keystroke, got {content_length_after}"
                )
                counter_text_after = context_page.get_char_counter_text()
                assert counter_text_after == EXPECTED_LIMIT_TEXT, (
                    f"Expected char counter text to remain {EXPECTED_LIMIT_TEXT!r} after "
                    f"the rejected keystroke, got {counter_text_after!r}"
                )

            with allure.step("Step 8 — Verify Save remains enabled at the 2500 boundary"):
                assert context_page.is_save_enabled(), (
                    "Expected Save to remain enabled after the rejected keystroke"
                )

            with allure.step(
                "Step 9 — Click Save: success toast appears, URL reverts to the "
                "saved (non-create) view"
            ):
                context_page.click_save()
                toast_text = context_page.get_toast_text()
                assert "Project Context saved" in toast_text, (
                    f"Expected toast text to contain 'Project Context saved', got {toast_text!r}"
                )
                assert "?view=" not in page.url, (
                    f"Expected the '?view=' query param to be gone after save, got {page.url!r}"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
