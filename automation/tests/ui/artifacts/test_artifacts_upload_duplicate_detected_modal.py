"""UI Test for ELITEA-1828 — Upload Flow, Duplicate File Detected: 'Resolve
duplicates' Modal Appears.

Verifies that uploading a file with the same name as an existing file in the
bucket triggers client-side duplicate detection and opens the "Resolve
duplicates" modal with the exact singular-form message, the duplicate
filename, and all four named action buttons (Cancel, Skip, Replace, Keep
both) visible.

This case stops at inspecting the already-open modal — it never clicks any
action button (see ELITEA-1829/1831 for the Skip/Keep-both click cases, and
ELITEA-1832 for the Cancel-click case). It shares the setup/navigation/
upload-trigger prefix with all three sibling cases (see
`test_artifacts_upload_duplicate_cancel.py`), reusing the same proven
page-object methods and fixtures.

AFS: test-specs/artifacts/l3_upload-flow-duplicate-detected-resolve-modal-appears_ELITEA-1828.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority; same marker ELITEA-1832 used)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_duplicate_detected_modal.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions

DUPLICATE_FILE_NAME = "sample.md"
DUPLICATE_FILE_CONTENT = (
    b"# Sample\n\nSeeded before the duplicate-detected upload attempt (ELITEA-1828)."
)
EXPECTED_MESSAGE_TEXT = (
    "This file already exists in this bucket. Choose how to handle duplicates."
)


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Duplicate Handling")
class TestArtifactUploadDuplicateDetectedModal:
    """ELITEA-1828 — 'Resolve duplicates' modal appears on a duplicate upload.

    Verifies the modal opens (purely client-side, zero network requests),
    shows the exact singular-form message text, lists the duplicate
    filename, and exposes all four named action buttons — without clicking
    any of them.
    """

    @pytest.mark.p2
    @allure.title(
        "Uploading a same-named file opens the 'Resolve duplicates' modal "
        "with the correct message, filename, and all four action buttons"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1828_upload-flow-duplicate-detected-resolve-modal.md",
        "onetest-ai Test Case link",
    )
    def test_duplicate_detected_opens_resolve_duplicates_modal(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """Uploading a same-named file opens 'Resolve duplicates' with full content.

        Read-only from the bucket's perspective: the bucket is seeded once
        with the duplicate-detection target, then the test never mutates
        state further — it only inspects the modal that opens (workflow
        skill Hard Rule 10 — minimal mutation for the observable).
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed sample.md into the fresh bucket via API (fast,
        # independent of the browser; ArtifactAPI.upload_file — added for
        # ELITEA-1832, reused here per this cluster's AFS).
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, DUPLICATE_FILE_NAME, DUPLICATE_FILE_CONTENT, content_type="text/markdown",
        )

        # Local file for the native file-picker step, same content as the
        # seeded file (content is irrelevant to duplicate detection, which
        # is filename-based — project convention, ELITEA-1832's test).
        duplicate_file_path = tmp_path / DUPLICATE_FILE_NAME
        duplicate_file_path.write_bytes(DUPLICATE_FILE_CONTENT)

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step("Step 2 — Select the bucket containing sample.md"):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"Precondition: '{DUPLICATE_FILE_NAME}' should be visible in "
                f"bucket '{bucket_name}' after seeding"
            )

        with allure.step(
            "Steps 3-6 — Click the upload icon (native file explorer opens "
            "immediately), select sample.md, confirm; the 'Upload files to "
            "...' modal opens with the Path field pre-filled"
        ):
            # Steps 3/4/5 are one mechanically inseparable Playwright action
            # (same folding ELITEA-1832's AFS/test already applies): the
            # file chooser must be awaited around the click, and the file is
            # set the instant it resolves.
            artifacts_page.upload_files([str(duplicate_file_path)])
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_text = artifacts_page.get_upload_path_prefix_text()
            assert bucket_name in path_text, (
                f"Path field should show the bucket name '{bucket_name}' as "
                f"its prefix, got: {path_text!r}"
            )

        with allure.step("Step 7 — Click Upload"):
            requests_during_detection = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_upload_path_upload_button()

        with allure.step(
            "Step 8 — Verify the 'Resolve duplicates' modal opens with the "
            "exact singular-form message text, and that detection was "
            "purely client-side (zero network requests)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff "
                f"against the already-fetched bucket listing — no network "
                f"request should fire, but observed: {requests_during_detection}"
            )
            message_text = (
                artifacts_page.resolve_duplicates_message_text.text_content() or ""
            ).strip()
            assert message_text == EXPECTED_MESSAGE_TEXT, (
                "'Resolve duplicates' modal message should be the exact "
                f"singular-form string (one duplicate file): "
                f"{EXPECTED_MESSAGE_TEXT!r}, got: {message_text!r}"
            )

        with allure.step("Step 9 — Verify the duplicate filename 'sample.md' is listed"):
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert duplicate_names == [DUPLICATE_FILE_NAME], (
                f"'Resolve duplicates' modal should list exactly "
                f"[{DUPLICATE_FILE_NAME!r}] as the duplicate, got: {duplicate_names}"
            )

        with allure.step(
            "Step 10 — Verify all four action buttons (Cancel, Skip, "
            "Replace, Keep both) are present and visible"
        ):
            for label, locator in (
                ("Cancel", artifacts_page.resolve_duplicates_cancel_button),
                ("Skip", artifacts_page.resolve_duplicates_skip_button),
                ("Replace", artifacts_page.resolve_duplicates_replace_button),
                ("Keep both", artifacts_page.resolve_duplicates_keep_both_button),
            ):
                assert locator.is_visible(), (
                    f"'{label}' button should be visible in the 'Resolve "
                    f"duplicates' modal"
                )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → upload → duplicate-detected flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the duplicate-detected "
                f"upload flow: {[m.text for m in console_errors]}"
            )
