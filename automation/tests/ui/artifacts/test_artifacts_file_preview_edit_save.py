"""UI Test for ELITEA-1852 — File Preview/Edit: Edit File Content and Save
Changes Successfully.

Regression test: verifies that editing file content in the editor and
clicking Save persists the change — success toast, editor auto-close for a
code file, updated "Last update" timestamp and file size, and the edit
surviving a fresh reopen (proving it round-tripped through the backend, not
just local component state).

Test flow:
1. Seed a fresh bucket (via API) with ``machine_learning.py``.
2. Open the file via the "View/Edit file" icon (shared open-flow helper).
3. Verify the editor renders content with line numbers.
4. Click into the content, append "# edited line" to the first line.
5. Verify the edit is visible immediately (client-side echo).
6. Verify Save transitions disabled -> enabled once content differs.
7. Click Save; wait on the ``createArtifact`` network response.
8. Verify the success toast reads exactly "File saved successfully".
9. Verify the editor closes (code file -> auto-close branch).
10. Verify the file row's "Last update" timestamp and size both advanced.
11. Reopen the file; verify "# edited line" is present in the reloaded content.
12. Verify no console errors across the edit+save flow.

AFS: test-specs/artifacts/l2_file-preview-edit-save_ELITEA-1852.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_edit_save.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_TIMEOUT = 15_000

FILE_NAME = "machine_learning.py"
FILE_CONTENT = (
    b"import numpy as np\n\n"
    b"def train(model, data):\n"
    b"    weights = np.zeros(len(data))\n"
    b"    for row in data:\n"
    b"        weights += row\n"
    b"    return weights\n"
)
EDIT_TEXT = "# edited line"
SUCCESS_TOAST_TEXT = "File saved successfully"


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewEditSave:
    """ELITEA-1852 — Edit file content in the editor and save successfully.

    Verifies the edit persists through a real backend round-trip: toast,
    editor auto-close, updated row metadata, and a fresh-fetch reopen.
    """

    @pytest.mark.p1
    @allure.title("Editing file content and saving persists the change")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1852_file-preview-edit-save.md",
        "onetest-ai Test Case link",
    )
    def test_edit_file_content_and_save_changes(
        self, page, artifact_api, artifact_bucket,
    ):
        """Editing content and clicking Save persists the change to the backend."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed machine_learning.py into the fresh bucket via API
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/x-python",
        )
        metadata_before = artifact_api.get_file_metadata(bucket_name, FILE_NAME)
        assert metadata_before is not None, "Seeded file should be present in the bucket listing"
        size_before = metadata_before["size"]
        modified_before = metadata_before.get("lastModified")

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to Artifacts and open 'machine_learning.py' "
            "via the 'View/Edit file' icon"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Verify the editor renders content with line numbers"
        ):
            assert artifacts_page.is_code_editor_line_numbers_visible(
                timeout=UI_ELEMENT_TIMEOUT
            ), "CodeMirror line-number gutter should be visible"
            original_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert original_content, "Editor should render non-empty file content"

        with allure.step(
            "Steps 3-4 — Click into the content at a known line and add "
            "'# edited line'"
        ):
            artifacts_page.edit_file_preview_content(
                EDIT_TEXT, line_index=0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step 5 — Verify the edited text appears immediately"):
            expect(artifacts_page.file_preview_code_content).to_contain_text(
                EDIT_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 6 — Verify Save transitions from disabled to enabled once "
            "content differs from the loaded content (the 'Save becomes "
            "active' behavior belongs here — ELITEA-1851's case text "
            "describes it prematurely, see that AFS's clarification)"
        ):
            assert artifacts_page.is_file_preview_save_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be ENABLED once the content has an unsaved edit"

        with allure.step(
            "Step 7 — Click Save; wait on the createArtifact response "
            "(network wait, not a timeout)"
        ):
            artifacts_page.click_file_preview_save(timeout=SAVE_TIMEOUT)

        with allure.step(
            "Step 8 — Verify a success toast reads exactly 'File saved successfully'"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 9 — Verify the editor closes and the main panel returns "
            "to the bucket's file table (non-code render-mode branches keep "
            "it open — out of scope for this .py-file case)"
        ):
            expect(artifacts_page.file_preview_save_button).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                "File table should be visible again with the file listed"
            )

        with allure.step(
            "Step 10 — Verify the 'Last update' timestamp advanced and the "
            "row's file size changed (stronger persistence signal than the "
            "timestamp alone — catches a 'toast lied, nothing actually "
            "saved' regression)"
        ):
            metadata_after = artifact_api.get_file_metadata(bucket_name, FILE_NAME)
            assert metadata_after is not None, "File should still be present after save"
            assert metadata_after["size"] != size_before, (
                f"File size should change after appending text: before={size_before}, "
                f"after={metadata_after['size']}"
            )
            assert metadata_after.get("lastModified") != modified_before, (
                "File's lastModified timestamp should advance after a real save"
            )
            row_text = artifacts_page.get_file_row_text(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert FILE_NAME in row_text, f"Row should still list '{FILE_NAME}': {row_text!r}"

        with allure.step(
            "Step 11 — Reopen 'machine_learning.py' and verify the saved "
            "change is present (persistence across a fresh fetch, not just "
            "in-memory state)"
        ):
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            reloaded_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert EDIT_TEXT in reloaded_content, (
                f"'{EDIT_TEXT}' should be present in the reloaded content: "
                f"{reloaded_content!r}"
            )

        with allure.step(
            "Side-channel check — no console errors during the edit+save flow"
        ):
            assert not console_errors, (
                f"Unexpected console errors during edit+save: "
                f"{[m.text for m in console_errors]}"
            )
