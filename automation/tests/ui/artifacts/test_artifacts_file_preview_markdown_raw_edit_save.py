"""UI Test for ELITEA-1858 — File Preview/Edit: Markdown File Raw Tab
Enables Editing with Save and Discard Active.

Regression test: verifies that switching a Markdown file to the "Raw" tab
shows CodeMirror content with line numbers, that Save/Discard stay disabled
right after the tab switch (no edit made yet) and enable only once a real
edit is made, that saving persists the change (success toast, editor stays
open, render-mode auto-switches back to "Preview" showing the update in the
SAME session), that Save/Discard re-disable post-save, and that a genuine
navigate-away-and-reopen shows the persisted change (backend round-trip).

Test flow:
1. Seed a fresh bucket (via API) with ``project-background.md`` whose first
   line is the heading ``# Project Overview``.
2. Open the file via the "View/Edit file" icon (editor opens in Preview).
3. Verify "Raw" is present, not yet pressed.
4. Click "Raw"; verify it becomes pressed and "Preview" becomes unpressed.
5. Verify content renders via CodeMirror with line numbers.
6. Verify Save/Discard remain DISABLED right after the tab switch.
7. Click the CodeMirror line containing "# Project Overview" and append
   " Updated".
8. Verify Save/Discard transition to ENABLED.
9. Click Save; verify the createArtifact POST resolves 200.
10. Verify the success toast reads exactly "File saved successfully".
11. Verify the editor remains open and auto-switches back to "Preview"
    (pressed).
12. Verify the updated heading is rendered in Preview, in the same session.
13. Verify Save/Discard re-disable once the save completes.
14. Navigate away and reopen the file; verify it reopens in Preview mode
    showing the persisted updated heading (proves backend round-trip).
15. Verify no console errors across the whole flow.

AFS: test-specs/artifacts/l3_file-preview-markdown-raw-tab-edit-save_ELITEA-1858.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_markdown_raw_edit_save.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_TIMEOUT = 15_000

FILE_NAME = "project-background.md"
ORIGINAL_HEADING = "# Project Overview"
APPEND_TEXT = " Updated"
UPDATED_HEADING_TEXT = "Project Overview Updated"
FILE_CONTENT = (
    b"# Project Overview\n\n"
    b"This is a **bold** statement about the project.\n\n"
    b"## Scope\n\n"
    b"Covers the automation of file preview features.\n\n"
    b"## Architecture\n\n"
    b"Uses a layered design.\n\n"
    b"## Key Components\n\n"
    b"- Component A\n"
    b"- Component B\n"
)
SUCCESS_TOAST_TEXT = "File saved successfully"


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewMarkdownRawEditSave:
    """ELITEA-1858 — Raw tab enables editing a Markdown file; the change
    saves, persists, and auto-shows in Preview in the same session.
    """

    @pytest.mark.p2
    @allure.title(
        "Markdown file Raw tab enables editing; Save persists and Preview "
        "auto-shows the change"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1858_file-preview-markdown-raw-tab-edit-save.md",
        "onetest-ai Test Case link",
    )
    def test_raw_tab_enables_editing_and_save_persists(
        self, page, artifact_api, artifact_bucket,
    ):
        """Raw tab enables editing; Save persists the change and re-shows it in Preview."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed project-background.md into the fresh bucket via API
        # (fresh bucket per test — must NOT share a bucket with ELITEA-1857's
        # read-only verification, since this case mutates the file)
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/markdown",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to Artifacts and open 'project-background.md' "
            "via the 'View/Edit file' icon (editor opens in Preview by default)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Verify the file opens in 'Preview' tab by default "
            "with rendered Markdown (reuses ELITEA-1857's open-flow "
            "assertions, not re-derived here)"
        ):
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state["rendered"] == "true", (
                f"Editor should open with Preview (rendered) pressed by default, "
                f"got {toggle_state}"
            )

        with allure.step(
            "Steps 3-4 — Click the 'Raw' tab; verify it becomes pressed and "
            "'Preview' becomes unpressed"
        ):
            artifacts_page.click_file_preview_mode_toggle_code(timeout=UI_ELEMENT_TIMEOUT)
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == {"rendered": "false", "code": "true"}, (
                f"After clicking Raw, 'code' should be pressed and 'rendered' "
                f"unpressed, got {toggle_state}"
            )

        with allure.step(
            "Step 5 — Verify the content now renders via CodeMirror with line numbers"
        ):
            assert artifacts_page.is_code_editor_line_numbers_visible(
                timeout=UI_ELEMENT_TIMEOUT
            ), "CodeMirror line-number gutter should be visible in Raw mode"

        with allure.step(
            "Step 6 — Verify Save and Discard remain DISABLED immediately "
            "after switching to Raw (no edit made yet — switching tabs "
            "alone is not an edit)"
        ):
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should still be DISABLED right after switching to Raw"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should still be DISABLED right after switching to Raw"

        with allure.step(
            "Step 7 — Click the CodeMirror line containing "
            f"'{ORIGINAL_HEADING}' and append '{APPEND_TEXT}'"
        ):
            artifacts_page.edit_file_preview_line_containing(
                ORIGINAL_HEADING, APPEND_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_code_content).to_contain_text(
                UPDATED_HEADING_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 8 — Verify Save and Discard transition to ENABLED the "
            "moment content differs from the loaded content"
        ):
            assert artifacts_page.is_file_preview_save_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be ENABLED once the content has an unsaved edit"
            assert artifacts_page.is_file_preview_discard_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should be ENABLED once the content has an unsaved edit"

        with allure.step(
            "Step 9 — Click Save; wait on the createArtifact response "
            "(network wait, not a timeout)"
        ):
            artifacts_page.click_file_preview_save(timeout=SAVE_TIMEOUT)

        with allure.step(
            "Step 10 — Verify a success toast reads exactly 'File saved successfully'"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 11 — Verify the editor REMAINS open (does NOT close) and "
            "the render-mode toggle auto-switches back to 'Preview' "
            "(pressed) — live behavior differs from the case's literal "
            "'reopen' wording, see AFS Coverage Map, "
            "EliteaAI/elitea-testing-public#1111"
        ):
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state["rendered"] == "true", (
                f"After Save, the mode toggle should auto-switch back to "
                f"Preview (rendered) pressed without a reopen, got {toggle_state}"
            )

        with allure.step(
            "Step 12 — Verify the updated heading is rendered in the "
            "Preview content, in the SAME session (no navigation away)"
        ):
            rendered_text = artifacts_page.get_file_preview_markdown_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert UPDATED_HEADING_TEXT in rendered_text, (
                f"Preview should render the updated heading "
                f"'{UPDATED_HEADING_TEXT}' immediately after save: {rendered_text!r}"
            )

        with allure.step(
            "Step 13 — Verify Save/Discard RE-DISABLE once the save "
            "completes (content is no longer 'unsaved' relative to the "
            "newly-persisted baseline)"
        ):
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should re-disable once the save completes"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should re-disable once the save completes"

        with allure.step(
            "Step 14 — Navigate away (back to the bucket's file table) and "
            "reopen the file; verify it reopens in Preview mode showing "
            "the persisted heading (proves the change round-tripped "
            "through the backend, not just local component/session state)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should still be listed in bucket '{bucket_name}'"
            )
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state["rendered"] == "true", (
                f"Reopening should default back to Preview mode, got {toggle_state}"
            )
            reopened_text = artifacts_page.get_file_preview_markdown_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert UPDATED_HEADING_TEXT in reopened_text, (
                f"'{UPDATED_HEADING_TEXT}' should be present after a fresh "
                f"reopen (independent of in-memory session state): {reopened_text!r}"
            )

        with allure.step(
            "Side-channel check — no console errors during the edit+save+"
            "auto-switch+reopen flow"
        ):
            assert not console_errors, (
                f"Unexpected console errors during Markdown edit+save: "
                f"{[m.text for m in console_errors]}"
            )
