"""UI Test for ELITEA-1832 — Upload Flow, Duplicate Handling: Cancel Stops
Entire Upload Including Non-Duplicate Files.

Regression test: verifies that clicking "Cancel" in the "Resolve duplicates"
modal aborts the ENTIRE multi-file upload — including any non-duplicate
files selected in the same batch — rather than uploading the non-duplicate
file(s) and only skipping the duplicate.

Test flow:
1. Seed a fresh bucket (via API) with exactly one file, ``sample.txt``.
2. Select both ``sample.txt`` (duplicate) and ``sample.png`` (new) in the
   native file picker.
3. Confirm the "Upload files to ..." dialog, pre-filled with the bucket
   name as the Path prefix.
4. Click "Upload" — triggers client-side duplicate detection (confirmed
   live: fires NO network request; the app diffs the selected filenames
   against the bucket listing it already fetched when the bucket was
   opened).
5. The "Resolve duplicates" modal opens listing ``sample.txt``.
6. Click "Cancel" — confirmed live (2/2 runs): fires NO network request,
   closes the dialog, and leaves the bucket's file list/count/metadata
   completely unchanged (including ``sample.txt``'s ``lastModified``
   timestamp, verified via the S3 JSON listing endpoint — there is no
   UI-visible timestamp column in this app).
7. No success toast is shown; ``sample.png`` never appears in the bucket.

AFS: test-specs/artifacts/l3_upload-flow-duplicate-cancel-stops-entire-upload_ELITEA-1832.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py -v
"""

import logging
import struct
import zlib

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions
ABSENCE_CHECK_TIMEOUT = 3_000     # short wait for an element expected NOT to appear
# ELITEA-1832 AFS step-12 fidelity caveat: a plausibly-related toast for a
# *separate* successful upload had already auto-dismissed by the time the
# analyst's snapshot fired during exploration. Assert absence with a short
# POLLED window (Playwright's auto-retrying `expect`, not a raw sleep) so the
# assertion is robust whether no toast ever fires, or one fires-and-dismisses
# before a naive single-shot DOM read would have caught it.
TOAST_ABSENCE_POLL_TIMEOUT = 2_000

DUPLICATE_FILE_NAME = "sample.txt"
DUPLICATE_FILE_CONTENT = (
    b"Original sample.txt content, seeded before the duplicate-cancel upload attempt."
)
NEW_FILE_NAME = "sample.png"


def _minimal_png_bytes() -> bytes:
    """Build a valid, minimal 1x1 PNG in memory.

    Content is irrelevant to this case's assertions — only the file's
    presence/name/duplicate-detection matters (ELITEA-1832 AFS § Test Data)
    — but the bytes must form a well-formed PNG for the OS file picker to
    accept it without complaint.
    """
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Duplicate Handling")
class TestArtifactUploadDuplicateCancel:
    """ELITEA-1832 — Cancel in 'Resolve duplicates' stops the entire upload.

    Verifies Cancel aborts BOTH the duplicate file's re-upload AND the
    non-duplicate file's first-time upload, leaving the bucket's contents,
    file count, and existing file metadata completely unchanged.
    """

    @pytest.mark.p2
    @allure.title(
        "Cancel in 'Resolve duplicates' modal aborts entire upload, "
        "including the non-duplicate file"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1832_upload-flow-duplicate-cancel-stops-entire-upload.md",
        "onetest-ai Test Case link",
    )
    def test_cancel_stops_entire_upload_including_non_duplicate(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """Cancel in the duplicate-resolution modal stops the WHOLE upload.

        Read-only from the fresh bucket's perspective at the end: the bucket
        is deliberately mutated once (seeded with sample.txt) so the
        duplicate can be triggered at all — this is the minimal state the
        observable inherently requires (workflow skill Hard Rule 10) — then
        the test proves that mutation is the ONLY one that ever lands.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed sample.txt into the fresh bucket via API (fast,
        # independent of the browser; ArtifactAPI.upload_file — added for
        # ELITEA-1832, see automation/api/client.py).
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, DUPLICATE_FILE_NAME, DUPLICATE_FILE_CONTENT, content_type="text/plain",
        )
        baseline_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
        assert baseline_metadata is not None, (
            f"Seed file '{DUPLICATE_FILE_NAME}' should exist in bucket "
            f"'{bucket_name}' immediately after seeding via the API"
        )

        # Local files for the native file-picker step. Project convention is
        # pytest's `tmp_path` (see test_chat_interface.py, test_support_assistant_smoke.py)
        # — no checked-in fixture files exist for uploads, and content is
        # irrelevant to this case's assertions.
        duplicate_file_path = tmp_path / DUPLICATE_FILE_NAME
        duplicate_file_path.write_bytes(DUPLICATE_FILE_CONTENT)
        new_file_path = tmp_path / NEW_FILE_NAME
        new_file_path.write_bytes(_minimal_png_bytes())

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step(
            "Step 2 — Select the bucket containing sample.txt but NOT sample.png"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"Precondition: '{DUPLICATE_FILE_NAME}' should be visible in "
                f"bucket '{bucket_name}' after seeding"
            )
            assert not artifacts_page.file_exists(NEW_FILE_NAME, timeout=ABSENCE_CHECK_TIMEOUT), (
                f"Precondition: '{NEW_FILE_NAME}' should NOT be present in "
                f"bucket '{bucket_name}' before the upload attempt"
            )

        with allure.step("Step 3 — Note the current total number of files"):
            baseline_count = artifacts_page.get_total_file_count_from_pagination()
            assert baseline_count == 1, (
                f"Expected exactly 1 file (sample.txt) in the freshly seeded "
                f"bucket before upload, got {baseline_count}"
            )

        with allure.step(
            "Steps 4-6 — Click the upload icon (native file explorer opens "
            "immediately), select both sample.txt and sample.png, confirm"
        ):
            # Steps 4/5/6 are one mechanically inseparable Playwright action:
            # `expect_file_chooser` must wrap the click, and files are set
            # the instant the chooser resolves — there is no intermediate
            # observable between "click" and "files chosen" (same folding
            # the AFS itself applies to step 5). If the chooser never opened,
            # `upload_files()` would raise a timeout here.
            artifacts_page.upload_files([str(duplicate_file_path), str(new_file_path)])

        with allure.step(
            "Step 7 — Verify the 'Upload files to ...' modal opens with the "
            "Path field pre-filled with the bucket name"
        ):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_text = artifacts_page.get_upload_path_prefix_text()
            assert bucket_name in path_text, (
                f"Path field should show the bucket name '{bucket_name}' as "
                f"its prefix, got: {path_text!r}"
            )

        with allure.step("Step 8 — Click Upload"):
            requests_during_detection = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_upload_path_upload_button()

        with allure.step(
            "Step 9 — Verify the 'Resolve duplicates' modal opens listing "
            "sample.txt, and that detection was purely client-side "
            "(zero network requests between Upload click and the modal)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff "
                f"against the already-fetched bucket listing — no network "
                f"request should fire, but observed: {requests_during_detection}"
            )
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert any(DUPLICATE_FILE_NAME in name for name in duplicate_names), (
                f"'Resolve duplicates' modal should list {DUPLICATE_FILE_NAME!r} "
                f"as the duplicate file, got: {duplicate_names}"
            )

        with allure.step("Step 10 — Click Cancel"):
            requests_during_cancel = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_resolve_duplicates_cancel_button()

        with allure.step(
            "Step 11 — Verify the 'Resolve duplicates' modal is closed, and "
            "that Cancel fired zero network requests (proof it aborts the "
            "ENTIRE upload rather than uploading then rolling back)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog_closed(timeout=DIALOG_TIMEOUT)
            assert not requests_during_cancel, (
                "Cancel must abort the ENTIRE upload with zero network "
                f"requests (including for the non-duplicate {NEW_FILE_NAME}), "
                f"observed: {requests_during_cancel}"
            )

        with allure.step("Step 12 — Verify NO success notification is displayed"):
            expect(artifacts_page.success_toast_message).to_have_count(
                0, timeout=TOAST_ABSENCE_POLL_TIMEOUT,
            )

        with allure.step(f"Step 13 — Verify '{NEW_FILE_NAME}' is NOT listed in the file table"):
            assert not artifacts_page.file_exists(NEW_FILE_NAME, timeout=ABSENCE_CHECK_TIMEOUT), (
                f"'{NEW_FILE_NAME}' should NOT appear in the bucket's file "
                f"table after Cancel — the entire upload must be aborted"
            )

        with allure.step(
            "Step 14 — Verify the total number of files remains the same as "
            "noted in step 3"
        ):
            final_count = artifacts_page.get_total_file_count_from_pagination()
            assert final_count == baseline_count, (
                f"Bucket file count should remain {baseline_count} after "
                f"Cancel, got {final_count}"
            )

        with allure.step(
            "Step 15 — Verify sample.txt is unchanged, including its "
            "'Last update' timestamp (via the S3 JSON listing endpoint — "
            "the Artifacts file table has no UI-visible timestamp column)"
        ):
            final_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
            assert final_metadata is not None, (
                f"'{DUPLICATE_FILE_NAME}' should still exist in the bucket after Cancel"
            )
            assert final_metadata["lastModified"] == baseline_metadata["lastModified"], (
                f"'{DUPLICATE_FILE_NAME}' lastModified must be unchanged after "
                f"Cancel: before={baseline_metadata['lastModified']!r}, "
                f"after={final_metadata['lastModified']!r}"
            )
            assert final_metadata.get("size") == baseline_metadata.get("size"), (
                f"'{DUPLICATE_FILE_NAME}' size must be unchanged after Cancel: "
                f"before={baseline_metadata.get('size')}, after={final_metadata.get('size')}"
            )
            final_content = artifact_api.get_file(bucket_name, DUPLICATE_FILE_NAME)
            assert final_content == DUPLICATE_FILE_CONTENT, (
                f"'{DUPLICATE_FILE_NAME}' content must be byte-identical after Cancel"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → upload → duplicate → cancel flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the duplicate-cancel "
                f"upload flow: {[m.text for m in console_errors]}"
            )
