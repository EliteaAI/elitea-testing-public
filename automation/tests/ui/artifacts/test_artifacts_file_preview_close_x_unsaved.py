"""UI Test for ELITEA-1855 — File Preview/Edit: closing the editor via the X
button without saving does not persist the changes.

Regression test: an unsaved edit is abandoned when the editor is closed via
X. Nothing reaches the backend — the file row's "Last update" is untouched,
the backend `lastModified`/`size` are unchanged, and reopening the file shows
the original content byte-for-byte.

**Declared case-text drift.** ELITEA-1855's step 3 reads "Click the X (close)
icon to close the editor panel -> Editor closes". Live, with unsaved changes
the editor does NOT close directly: `FilePreviewCanvas.handleClose` raises an
unsaved-changes Warning dialog ("You are editing now. Do you want to discard
current changes and continue?") and the editor closes only after Confirm.
This test asserts the LIVE contract and adds the dialog to the assertions
rather than dropping a step; every observable the case asks for is preserved.
Clarification filed as EliteaAI/elitea-testing-public#1687.

Test flow:
1. Seed a fresh bucket (via API) with a 19-line ``machine_learning.py``.
2. Capture the baseline: the row's rendered "Last update" plus the backend
   `lastModified` and `size`.
3. Open the file, capture the original editor content.
4. Append "# unsaved change" to line 17; verify it appears.
5. Wait for Save/Discard to enable (the product's own dirty-state signal).
6. Click X; verify the unsaved-changes Warning dialog appears; Confirm.
7. Verify the editor closed and the file table is back.
8. Verify the row's "Last update" is identical to the baseline.
9. Verify backend `lastModified` and `size` are unchanged.
10. Reopen the file; verify "# unsaved change" is absent and the content is
    byte-equal to the original.

AFS: test-specs/artifacts/l3_file-preview-close-x-without-saving_ELITEA-1855.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3 / case `priority: medium`)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_close_x_unsaved.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

FILE_NAME = "machine_learning.py"

# 19 lines, so the case's "line 17" is a genuinely addressable coordinate.
# Line 17 (1-based) carries a unique marker for deterministic line targeting
# (`Control+Home` navigation is NOT reliable in this CodeMirror instance —
# test-specs/artifacts/_surface.md).
FILE_LINES = [
    "import numpy as np",
    "",
    "LEARNING_RATE_DEFAULT = 0.1",
    "",
    "def train(model, data):",
    "    weights = np.zeros(len(data))",
    "    for row in data:",
    "        weights += row",
    "    return weights",
    "",
    "def predict(model, row):",
    "    return model.dot(row)",
    "",
    "class Trainer:",
    "    def __init__(self, lr):",
    "        self.lr = lr",
    "    EPOCH_LIMIT = 250",
    "    def step(self):",
    "        return self.lr",
]
FILE_CONTENT = ("\n".join(FILE_LINES) + "\n").encode()
LINE_17_MARKER = "EPOCH_LIMIT = 250"

UNSAVED_CHANGE = "  # unsaved change"
# Asserting the whole edited line (not the bare marker) is what proves the
# change landed on LINE 17 specifically, as the case requires.
EDITED_LINE_17 = f"{LINE_17_MARKER}{UNSAVED_CHANGE}"

UNSAVED_CHANGES_WARNING = (
    "You are editing now. Do you want to discard current changes and continue?"
)


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewCloseXUnsaved:
    """ELITEA-1855 — closing the editor via X discards unsaved changes."""

    @pytest.mark.p2
    @allure.title("Closing the editor via X without saving does not persist changes")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1855_file-preview-edit-close-x-no-persist.md",
        "onetest-ai Test Case link",
    )
    def test_close_editor_via_x_does_not_persist_changes(
        self, page, artifact_api, artifact_bucket,
    ):
        """An unsaved edit abandoned via X never reaches the backend."""
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
        assert metadata_before is not None, (
            "Seeded file should be present in the bucket listing"
        )
        size_before = metadata_before["size"]
        modified_before = metadata_before.get("lastModified")

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Precondition — capture the file's known 'Last update' baseline "
            "from the row before any editing"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            row_text_before = artifacts_page.get_file_row_text(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 1 — Navigate to Artifacts and open 'machine_learning.py' "
            "via the 'View/Edit file' icon"
        ):
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            original_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert LINE_17_MARKER in original_content, (
                f"Seeded line 17 marker '{LINE_17_MARKER}' should be in the "
                f"loaded content: {original_content!r}"
            )

        with allure.step(
            "Step 2 — Type '# unsaved change' at line 17 and verify it appears"
        ):
            artifacts_page.edit_file_preview_line_containing(
                LINE_17_MARKER, UNSAVED_CHANGE, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_code_content).to_contain_text(
                EDITED_LINE_17, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 2a — Verify Save/Discard became enabled (the product's own "
            "signal that `hasChanges` has propagated; `useCodeMirror` "
            "debounces `notifyChange` by 30ms and closing inside that window "
            "skips the warning entirely — see the AFS Automation Hints)"
        ):
            assert artifacts_page.is_file_preview_save_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be ENABLED once the editor has an unsaved edit"

        with allure.step(
            "Step 3 — Click the X (close) icon; the live product raises an "
            "unsaved-changes Warning dialog first (case text omits this — "
            "clarification EliteaAI/elitea-testing-public#1687)"
        ):
            artifacts_page.click_file_preview_close_with_unsaved_changes(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.unsaved_changes_alert_content).to_have_text(
                UNSAVED_CHANGES_WARNING, timeout=UI_ELEMENT_TIMEOUT
            )
            artifacts_page.confirm_close_with_unsaved_changes(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 4 — Verify the editor closed and the main panel returned to "
            "the bucket's file table"
        ):
            expect(artifacts_page.file_preview_save_button).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                "File table should be visible again with the file listed"
            )

        with allure.step(
            "Step 5 — Verify the 'Last update' timestamp for "
            "'machine_learning.py' has NOT changed"
        ):
            row_text_after = artifacts_page.get_file_row_text(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            )
            assert row_text_after == row_text_before, (
                "File row (which renders 'Last update' and size) must be "
                f"unchanged after an abandoned edit: {row_text_after!r} != "
                f"{row_text_before!r}"
            )

        with allure.step(
            "Step 5a — Independent ground truth: backend `lastModified` and "
            "`size` are unchanged (the UI column's resolution is whole "
            "minutes, so it alone would pass a real write landing inside the "
            "same minute)"
        ):
            metadata_after = artifact_api.get_file_metadata(bucket_name, FILE_NAME)
            assert metadata_after is not None, "File should still be present"
            assert metadata_after.get("lastModified") == modified_before, (
                "Backend lastModified must not advance when the edit was "
                f"abandoned: {metadata_after.get('lastModified')} != "
                f"{modified_before}"
            )
            assert metadata_after["size"] == size_before, (
                "Backend file size must not change when the edit was "
                f"abandoned: {metadata_after['size']} != {size_before}"
            )

        with allure.step(
            "Step 6 — Reopen 'machine_learning.py' and verify the unsaved "
            "change is absent and the original content is shown"
        ):
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            reopened_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert UNSAVED_CHANGE.strip() not in reopened_content, (
                f"'{UNSAVED_CHANGE.strip()}' must not survive an abandoned "
                f"edit: {reopened_content!r}"
            )
            # Byte-equality, not just marker absence — catches a partial or
            # garbled revert (AFS Axis 2).
            assert reopened_content == original_content, (
                "Reopened content must equal the original byte-for-byte: "
                f"{reopened_content!r} != {original_content!r}"
            )

        with allure.step(
            "Side-channel check — no console errors during the close flow"
        ):
            assert not console_errors, (
                f"Unexpected console errors during the close flow: "
                f"{[m.text for m in console_errors]}"
            )
