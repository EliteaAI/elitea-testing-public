"""UI Tests for ELITEA-1853 / ELITEA-1854 — File Preview/Edit: the Discard
button's Warning modal and its two exit paths.

Family spec (one AFS, one parameterized test, one row per TMS case). Both
cases share the entire prefix — open the editor, edit line 17, click the
header Discard button, assert the Warning modal's full element inventory —
and diverge on exactly one click:

* **ELITEA-1853** — confirm ("Discard"): the content reverts to the original,
  the editor stays open, Save/Discard stay visible but go back to disabled,
  and NO success notification appears.
* **ELITEA-1854** — dismiss ("Cancel"): the modal closes, the unsaved
  "# temp change" survives on line 17, and Save/Discard remain active.

The header Discard button never discards directly — the shared
``Button.DiscardButton`` always raises its own confirmation modal first
(confirmed live). Discarding is a pure client-side state reset: no network
request, no toast.

AFS: test-specs/artifacts/l3_file-preview-discard-warning-modal_ELITEA-1853-1854.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3 / case `priority: medium`)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_discard_warning.py -v
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
# Line 17 (1-based) carries a unique marker used for deterministic
# line-targeting — `Control+Home` navigation is NOT reliable in this
# CodeMirror instance (test-specs/artifacts/_surface.md).
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

TEMP_CHANGE = "  # temp change"
# The edited line as it must read once the change is typed — asserting this
# whole string (not just the bare marker) is what proves the change landed on
# LINE 17 specifically, as the case requires.
EDITED_LINE_17 = f"{LINE_17_MARKER}{TEMP_CHANGE}"

WARNING_TITLE = "Warning"
WARNING_MESSAGE = "Are you sure you want to discard changes?"
CANCEL_LABEL = "Cancel"
DISCARD_LABEL = "Discard"

CASE_LINK_BASE = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/artifacts/"
)
# Real TMS case file names (verified against the cases repo, not guessed).
CASE_FILES = {
    "ELITEA-1853": "ELITEA-1853_file-preview-edit-discard-reverts-stays-in-edit.md",
    "ELITEA-1854": "ELITEA-1854_file-preview-edit-cancel-discard-keeps-changes.md",
}


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewDiscardWarning:
    """ELITEA-1853 / ELITEA-1854 — the Discard Warning modal's two exit paths."""

    @pytest.mark.p2
    @pytest.mark.parametrize(
        (
            "case_id",
            "exit_method",
            "exit_label",
            "expect_change_present",
            "expect_buttons_enabled",
        ),
        [
            pytest.param(
                "ELITEA-1853",
                "confirm_file_preview_discard",
                DISCARD_LABEL,
                False,
                False,
                id="ELITEA-1853-confirm-discard-reverts-and-stays-in-edit-mode",
            ),
            pytest.param(
                "ELITEA-1854",
                "cancel_file_preview_discard",
                CANCEL_LABEL,
                True,
                True,
                id="ELITEA-1854-cancel-returns-to-edit-mode-with-changes-preserved",
            ),
        ],
    )
    @allure.title("Discard Warning modal — {case_id}")
    @allure.severity(allure.severity_level.NORMAL)
    def test_discard_warning_modal_exit_paths(
        self,
        page,
        artifact_api,
        artifact_bucket,
        case_id,
        exit_method,
        exit_label,
        expect_change_present,
        expect_buttons_enabled,
    ):
        """Exiting the Discard Warning modal reverts (Discard) or preserves (Cancel).

        Args:
            case_id: TMS case this row covers.
            exit_method: Page-object method that clicks this row's modal exit
                button and waits for the modal to close.
            exit_label: Visible label of that button ("Discard" / "Cancel").
            expect_change_present: Whether "# temp change" survives the exit.
            expect_buttons_enabled: Whether Save/Discard stay enabled afterwards.
        """
        allure.dynamic.issue(
            f"{CASE_LINK_BASE}{CASE_FILES[case_id]}",
            f"onetest-ai Test Case link ({case_id})",
        )
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed machine_learning.py into the fresh bucket via API
        # (the case's "bucket-1" is the case author's own environment; this
        # suite has no such fixture, and both rows mutate in-editor state, so
        # each row gets its own bucket)
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/x-python",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to Artifacts and open 'machine_learning.py' "
            "via the 'View/Edit file' icon"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Note the original content at line 17"):
            original_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert LINE_17_MARKER in original_content, (
                f"Seeded line 17 marker '{LINE_17_MARKER}' should be in the "
                f"loaded content: {original_content!r}"
            )
            assert TEMP_CHANGE.strip() not in original_content, (
                "Original content must not already contain the change under test"
            )

        with allure.step(
            "Steps 3-4 — Type '# temp change' on line 17 and verify it appears "
            "in the editor"
        ):
            artifacts_page.edit_file_preview_line_containing(
                LINE_17_MARKER, TEMP_CHANGE, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_code_content).to_contain_text(
                EDITED_LINE_17, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 4a — Verify Save and Discard became enabled (the product's "
            "own signal that the unsaved-changes state has propagated; "
            "`useCodeMirror` debounces `notifyChange` by 30ms, so this is a "
            "correctness guard, not a nicety — see the AFS Automation Hints)"
        ):
            assert artifacts_page.is_file_preview_discard_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should be ENABLED once the editor has an unsaved edit"
            assert artifacts_page.is_file_preview_save_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be ENABLED once the editor has an unsaved edit"

        with allure.step(
            "Step 5 — Click the 'Discard' button in the top-right; a Warning "
            "modal opens (the header Discard never discards directly)"
        ):
            artifacts_page.click_file_preview_discard(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 6 — Verify the Warning modal shows every required element: "
            "warning icon, title 'Warning', the discard message, an X icon, "
            "a 'Cancel' button and a 'Discard' button"
        ):
            expect(artifacts_page.file_preview_discard_warning_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_warning_icon).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_warning_title).to_have_text(
                WARNING_TITLE, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_warning_dialog).to_contain_text(
                WARNING_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(
                artifacts_page.file_preview_discard_warning_close_button
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(
                artifacts_page.file_preview_discard_warning_cancel_button
            ).to_have_text(CANCEL_LABEL, timeout=UI_ELEMENT_TIMEOUT)
            expect(
                artifacts_page.file_preview_discard_warning_confirm_button
            ).to_have_text(DISCARD_LABEL, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 7 — Click the modal's '{exit_label}' button ({case_id})"
        ):
            getattr(artifacts_page, exit_method)(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 8 — Verify the modal closes"):
            expect(artifacts_page.file_preview_discard_warning_dialog).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 9 — Verify the file content matches this row's expectation "
            "(ELITEA-1853: reverted byte-for-byte to the original; "
            "ELITEA-1854: '# temp change' still present on line 17)"
        ):
            # Web-first (auto-retrying) assertions: the revert reaches
            # CodeMirror through a React state round-trip that completes
            # slightly AFTER the modal disappears (the parent resets
            # `editedContent`, then `useCodeMirror`'s effect pushes the
            # original text back into the editor), so an immediate one-shot
            # read races the product. Polling on the real observable is the
            # correct wait here — never a sleep.
            if expect_change_present:
                expect(artifacts_page.file_preview_code_content).to_contain_text(
                    EDITED_LINE_17, timeout=UI_ELEMENT_TIMEOUT
                )
            else:
                expect(artifacts_page.file_preview_code_content).not_to_contain_text(
                    TEMP_CHANGE.strip(), timeout=UI_ELEMENT_TIMEOUT
                )
            content_after = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            if not expect_change_present:
                # Stronger than "the marker is gone" — byte-equality catches a
                # revert that drops or mangles unrelated lines (AFS Axis 2).
                assert content_after == original_content, (
                    f"[{case_id}] Discard must restore the ORIGINAL content "
                    f"byte-for-byte: {content_after!r} != {original_content!r}"
                )

        with allure.step(
            "Step 10 — Verify the user remains in edit mode: the editor is "
            "still open and its content surface still rendered"
        ):
            expect(artifacts_page.file_preview_code_content).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_file_path).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 11 — Verify Save and Discard are still visible in the "
            "top-right, in this row's expected enabled state "
            "(ELITEA-1853: back to disabled, since the edit state was reset; "
            "ELITEA-1854: still active)"
        ):
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            if expect_buttons_enabled:
                assert artifacts_page.is_file_preview_save_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Save should remain ACTIVE after Cancel"
                assert artifacts_page.is_file_preview_discard_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Discard should remain ACTIVE after Cancel"
            else:
                # AFS Axis 2 — the case only asks for "visible", but
                # `hasUnsavedChanges` returning to false is the product's own
                # statement that the revert really reset the edit state.
                assert artifacts_page.is_file_preview_save_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Save should be DISABLED again after Discard"
                assert artifacts_page.is_file_preview_discard_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Discard should be DISABLED again after Discard"

        if not expect_change_present:
            with allure.step(
                "Step 12 (ELITEA-1853) — Verify no success notification is "
                "displayed (discarding is a pure client-side state reset: no "
                "network request, no toast)"
            ):
                expect(artifacts_page.success_toast_message).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

        with allure.step(
            "Side-channel check — no console errors during the discard flow"
        ):
            assert not console_errors, (
                f"Unexpected console errors during the discard flow: "
                f"{[m.text for m in console_errors]}"
            )
