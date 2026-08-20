"""UI Test for ELITEA-1840 — Download Flow: Download Multiple Selected Files
as ZIP via Download Icon.

Regression test: verifies that selecting 2 files via checkbox in an artifacts
subfolder and clicking the toolbar "Download files" button shows a
ZIP-preparation progress dialog (title / progress bar / counter /
current-file label / Cancel), that the dialog's indicators update in real
time as each file is processed, and that the resulting ZIP contains exactly
the 2 selected files, flattened to the ZIP root, byte-identical to what was
seeded.

Test flow:
1. Seed a fresh bucket (via API) with 4 files under ``a1/`` — 2 to select
   (``sample.txt``, ``sample.png``), 2 to prove exclusion (``extra1.txt``,
   ``extra2.txt``).
2. Navigate directly to the bucket's ``a1`` subfolder in one URL navigation.
3. Check the checkboxes for ``sample.txt`` and ``sample.png``; verify each
   becomes checked, and that exactly 2 checkboxes are checked in total
   (queried independently per row — not just the two just clicked).
4. Verify the toolbar "Download files" button transitions from disabled
   (0 selected) to enabled (2 selected).
5. Click "Download files"; verify the ZIP-preparation dialog shows the
   correct title, a determinate progress bar, a file counter, and a Cancel
   button — visibility only, never clicked (Cancel-flow testing is out of
   this case's scope).
6. Verify the counter and current-file label update as each file is
   processed, and the progress bar's value advances — observed via a
   `page.route()` network delay scoped to this test only (2 small files
   complete in well under 1s otherwise, too fast to reliably catch an
   intermediate frame).
7. Verify the dialog auto-closes, a success toast appears, and a ZIP file
   named exactly ``{bucket_name}.zip`` downloads.
8. Verify the ZIP's namelist is exactly ``["sample.png", "sample.txt"]``
   (flattened to the ZIP root, not nested under ``a1/``), and each entry's
   bytes are identical to the seeded content.
9. Verify neither ``extra1.txt`` nor ``extra2.txt`` appears in the ZIP.
10. Verify selection state and the toolbar button's enabled state persist
    after the download completes, exactly 2 GET requests fired to the
    single-file artifact endpoint (no dedicated server-side ZIP endpoint),
    and no console errors occurred across the flow.

Overlap check (see AFS): zero behavioral overlap with ELITEA-1327's
``test_artifacts_multi_file.py`` (never touches a checkbox or the toolbar
download button — always downloads exactly one file via the legacy
per-file dropdown) or ELITEA-1839's
``test_artifacts_download_single_file_dropdown.py`` (asserts the ABSENCE of
the ZIP dialog — architecturally the opposite scenario). This case is the
first to click the toolbar "Download files" button and assert the dialog's
actual (populated) contents.

AFS: test-specs/artifacts/l2_download-flow-multiple-selected-files-as-zip_ELITEA-1840.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_download_multiple_files_zip.py -v
"""

import logging
import time
import zipfile

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms unless noted)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, checkboxes, dialog elements
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
# Generous — must accommodate the artificial per-request route delay below
# (2 sequential GETs) plus JSZip generation and the blob-URL download.
DOWNLOAD_TIMEOUT = 20_000
# Window to catch the intermediate "1 of 2 files" progress frame.
PROGRESS_FRAME_TIMEOUT = 8_000

FOLDER_NAME = "a1"
FILE_SAMPLE_TXT = "sample.txt"
FILE_SAMPLE_PNG = "sample.png"
FILE_EXTRA1 = "extra1.txt"
FILE_EXTRA2 = "extra2.txt"

SAMPLE_TXT_CONTENT = b"Sample content for ELITEA-1840 ZIP test - sample.txt\n"
SAMPLE_PNG_CONTENT = b"\x89PNG\r\n\x1a\nFAKE_PNG_BYTES_FOR_ELITEA_1840_TEST"
EXTRA1_CONTENT = b"Excluded file content for ELITEA-1840 test - extra1.txt\n"
EXTRA2_CONTENT = b"Excluded file content for ELITEA-1840 test - extra2.txt\n"

# Confirmed live (AFS + implementer exploration, both runs identical): the
# sequential for-loop in downloadArtifactsAsZip processes the selected files
# in this fixed order regardless of checkbox click order.
EXPECTED_ZIP_NAMELIST = ["sample.png", "sample.txt"]

# Artificial per-request delay (seconds) applied ONLY to this test's
# artifact-download GETs, via page.route() — a legitimate timing-control
# technique (delays a network response, not a synthetic input event), not
# defect masking. With only 2 small (<60 byte) files, the real flow
# completes in well under 1s — too fast to reliably observe the
# intermediate progress frame without it (AFS § Automation Hints).
ROUTE_DELAY_SECONDS = 0.6


def _delayed_route(route):
    time.sleep(ROUTE_DELAY_SECONDS)
    route.continue_()


@allure.epic("Artifacts")
@allure.feature("Download Flow")
class TestArtifactDownloadMultipleFilesZip:
    """ELITEA-1840 — Download multiple selected files as a ZIP via the
    toolbar "Download files" button.

    Verifies the ZIP-preparation progress dialog's structure and live
    updates, and that the resulting ZIP contains exactly the selected
    files, flattened to the ZIP root, byte-identical to what was seeded.
    """

    @pytest.mark.p1
    @allure.title(
        "Selecting 2 files via checkbox and clicking 'Download files' "
        "downloads them as a ZIP with a live progress dialog"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1840_download-flow-multiple-selected-files-as-zip.md",
        "onetest-ai Test Case link",
    )
    def test_download_multiple_files_as_zip(
        self, page, artifact_api, artifact_bucket,
    ):
        """Selecting 2 files and clicking 'Download files' produces a ZIP.

        Read-only from the bucket's perspective at the end: the bucket is
        mutated exactly once (seeded with 4 files under ``a1/``) — the
        minimal state this observable inherently requires (workflow skill
        Hard Rule 10) — then every assertion reads that state without
        further mutation.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # Delay ONLY the single-file artifact-download GETs — scoped to
        # this test's own page instance, not a global/shared config.
        page.route("**/artifact/default/**", _delayed_route)

        # ------------------------------------------------------------------
        # Precondition — seed 4 files under a1/ into the fresh bucket via
        # API (ArtifactAPI.upload_file — auto-creates the 'a1' folder node;
        # no separate folder-creation call exists or is needed, confirmed
        # live per the AFS). 2 files will be selected/downloaded, 2 exist
        # purely to prove exclusion from the resulting ZIP.
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, f"{FOLDER_NAME}/{FILE_SAMPLE_TXT}", SAMPLE_TXT_CONTENT,
            content_type="text/plain",
        )
        artifact_api.upload_file(
            bucket_name, f"{FOLDER_NAME}/{FILE_SAMPLE_PNG}", SAMPLE_PNG_CONTENT,
            content_type="image/png",
        )
        artifact_api.upload_file(
            bucket_name, f"{FOLDER_NAME}/{FILE_EXTRA1}", EXTRA1_CONTENT,
            content_type="text/plain",
        )
        artifact_api.upload_file(
            bucket_name, f"{FOLDER_NAME}/{FILE_EXTRA2}", EXTRA2_CONTENT,
            content_type="text/plain",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate directly to the bucket's 'a1' subfolder "
            "(folds case steps 1-3: Artifacts page load, bucket/subfolder "
            "selection, file-table visibility into one navigation); verify "
            "all 4 seeded files are listed and the toolbar download button "
            "starts disabled (0 selected)"
        ):
            artifacts_page.navigate_to_bucket_folder(
                bucket_name, FOLDER_NAME, timeout=NAVIGATION_TIMEOUT,
            )
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert sorted(file_names) == sorted(
                [FILE_EXTRA1, FILE_EXTRA2, FILE_SAMPLE_PNG, FILE_SAMPLE_TXT]
            ), f"Expected exactly the 4 seeded files, got {file_names}"
            file_count = artifacts_page.get_total_file_count_from_pagination()
            assert file_count == 4, f"Expected pagination to read 4 total files, got {file_count}"
            expect(artifacts_page.download_files_button).to_be_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 2 — Click the checkbox for 'sample.txt'; verify it becomes checked"
        ):
            artifacts_page.select_file_checkbox(FILE_SAMPLE_TXT, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(FILE_SAMPLE_TXT), (
                f"'{FILE_SAMPLE_TXT}' checkbox should be checked after clicking it"
            )

        with allure.step(
            "Step 3 — Click the checkbox for 'sample.png'; verify it becomes checked"
        ):
            artifacts_page.select_file_checkbox(FILE_SAMPLE_PNG, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(FILE_SAMPLE_PNG), (
                f"'{FILE_SAMPLE_PNG}' checkbox should be checked after clicking it"
            )

        with allure.step(
            "Step 4 — Verify exactly 2 checkboxes are checked in total, "
            "querying ALL row checkboxes independently (not just the two "
            "just clicked) — 'extra1.txt'/'extra2.txt' must remain unchecked"
        ):
            states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states == {
                FILE_EXTRA1: False,
                FILE_EXTRA2: False,
                FILE_SAMPLE_PNG: True,
                FILE_SAMPLE_TXT: True,
            }, f"Unexpected checkbox states: {states}"

        with allure.step(
            "Step 5 — Verify the toolbar 'Download files' button is now "
            "enabled (transitioned from disabled at 0 selected to enabled "
            "at 2 selected)"
        ):
            expect(artifacts_page.download_files_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        requests_captured = artifacts_page.capture_requests_matching("artifact/default")

        with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
            with allure.step("Step 6 — Click the toolbar 'Download files' button"):
                artifacts_page.download_files_button.click()

            with allure.step(
                "Step 7 — Verify the ZIP-preparation dialog appears with the "
                "correct title, a determinate progress bar, a file counter, "
                "and a visible Cancel button"
            ):
                expect(artifacts_page.zip_download_progress_dialog).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.zip_download_progress_title).to_have_text(
                    f"Preparing {bucket_name}.zip", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.zip_download_progress_bar).to_have_attribute(
                    "aria-valuemin", "0"
                )
                expect(artifacts_page.zip_download_progress_bar).to_have_attribute(
                    "aria-valuemax", "100"
                )
                expect(artifacts_page.zip_download_progress_counter).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.zip_download_progress_cancel_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Verify the counter and current-file label update as "
                "each file is processed — the current-file label shows the "
                "FULL relative key including the subfolder prefix, not just "
                "the base filename"
            ):
                expect(artifacts_page.zip_download_progress_counter).to_have_text(
                    "1 of 2 files", timeout=PROGRESS_FRAME_TIMEOUT
                )
                expect(artifacts_page.zip_download_progress_current_file).to_have_text(
                    f"Current: {FOLDER_NAME}/{FILE_SAMPLE_PNG}", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 9 — Verify the progress bar's value advances forward "
                "as files are processed"
            ):
                valuenow = artifacts_page.zip_download_progress_bar.get_attribute(
                    "aria-valuenow"
                )
                assert valuenow is not None and int(valuenow) > 0, (
                    f"Progress bar should have advanced past 0 at '1 of 2 files', "
                    f"got aria-valuenow={valuenow!r}"
                )

        download = download_info.value

        with allure.step(
            "Step 10 — Verify the dialog auto-closes, a 'ZIP downloaded "
            "successfully' toast appears, and the ZIP downloads with the "
            "exact filename '{bucket}.zip'"
        ):
            expect(artifacts_page.zip_download_progress_dialog).to_be_hidden(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.success_toast_message).to_have_text(
                "ZIP downloaded successfully", timeout=UI_ELEMENT_TIMEOUT
            )
            assert download.suggested_filename == f"{bucket_name}.zip", (
                f"Expected ZIP filename '{bucket_name}.zip', got "
                f"'{download.suggested_filename}'"
            )

        with allure.step(
            "Step 11 — Verify the ZIP's namelist is exactly "
            "['sample.png', 'sample.txt'], flattened to the ZIP root "
            "(not nested under 'a1/'), and each entry's bytes are "
            "identical to the seeded content"
        ):
            downloaded_path = download.path()
            assert downloaded_path is not None, "Download should have completed to a local path"
            with zipfile.ZipFile(downloaded_path) as zf:
                namelist = zf.namelist()
                assert namelist == EXPECTED_ZIP_NAMELIST, (
                    f"Expected ZIP namelist exactly {EXPECTED_ZIP_NAMELIST}, got {namelist}"
                )
                assert zf.read(FILE_SAMPLE_PNG) == SAMPLE_PNG_CONTENT, (
                    f"'{FILE_SAMPLE_PNG}' ZIP entry content should be byte-identical "
                    "to the seeded content"
                )
                assert zf.read(FILE_SAMPLE_TXT) == SAMPLE_TXT_CONTENT, (
                    f"'{FILE_SAMPLE_TXT}' ZIP entry content should be byte-identical "
                    "to the seeded content"
                )

        with allure.step(
            "Step 12 — Verify neither 'extra1.txt' nor 'extra2.txt' appears "
            "anywhere in the ZIP's namelist"
        ):
            with zipfile.ZipFile(downloaded_path) as zf:
                namelist = zf.namelist()
            assert FILE_EXTRA1 not in namelist, f"'{FILE_EXTRA1}' should NOT be in the ZIP"
            assert FILE_EXTRA2 not in namelist, f"'{FILE_EXTRA2}' should NOT be in the ZIP"

        with allure.step(
            "Side-channel check — selection state and the toolbar button's "
            "enabled state persist after the ZIP download completes; "
            "exactly 2 GET requests fired to the single-file artifact "
            "endpoint (no dedicated server-side ZIP endpoint); no console "
            "errors across the whole flow"
        ):
            assert artifacts_page.is_file_checkbox_checked(FILE_SAMPLE_TXT), (
                "'sample.txt' checkbox should remain checked after the download completes"
            )
            assert artifacts_page.is_file_checkbox_checked(FILE_SAMPLE_PNG), (
                "'sample.png' checkbox should remain checked after the download completes"
            )
            expect(artifacts_page.download_files_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

            assert len(requests_captured) == 2, (
                "Expected exactly 2 GET requests to the single-file artifact "
                f"endpoint (no dedicated server-side ZIP endpoint), got "
                f"{len(requests_captured)}: {requests_captured}"
            )
            assert all(r["method"] == "GET" for r in requests_captured), (
                f"All artifact-download requests should be GET, got: {requests_captured}"
            )

            assert not console_errors, (
                "Unexpected console errors during the multi-file ZIP "
                f"download flow: {[m.text for m in console_errors]}"
            )
