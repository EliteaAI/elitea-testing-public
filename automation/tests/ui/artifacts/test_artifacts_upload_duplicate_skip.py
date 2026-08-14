"""UI Test for ELITEA-1829 — Upload Flow, Duplicate Handling: Skip Skips
Duplicate and Saves Non-Duplicate Files.

Verifies that clicking "Skip" in the "Resolve duplicates" modal uploads
ONLY the non-duplicate file(s) in the same batch, leaves the duplicate file
entirely untouched (content, size, and 'lastModified' timestamp all
byte-identical before/after), and shows the generic upload-success toast.

Shares the setup/navigation/upload-trigger prefix with
`test_artifacts_upload_duplicate_cancel.py` (ELITEA-1832) and
`test_artifacts_upload_duplicate_detected_modal.py` (ELITEA-1828) — reuses
the same proven page-object methods and fixtures, diverging only at the
button click (Skip) and the resulting assertion chain.

AFS: test-specs/artifacts/l3_upload-flow-duplicate-skip-skips-and-saves-non-duplicate_ELITEA-1829.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority; same marker ELITEA-1832 used)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_duplicate_skip.py -v
"""

import logging
import struct
import zlib

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions
ABSENCE_CHECK_TIMEOUT = 3_000     # short wait for an element expected NOT to appear

DUPLICATE_FILE_NAME = "sample.txt"
DUPLICATE_FILE_CONTENT = (
    b"Original sample.txt content, seeded before the duplicate-skip upload attempt."
)
NEW_FILE_NAME = "sample.png"
SUCCESS_TOAST_TEXT = "Your file(s) have been successfully uploaded!"


def _minimal_png_bytes() -> bytes:
    """Build a valid, minimal 1x1 PNG in memory.

    Content is irrelevant to this case's assertions — only the file's
    presence/name/duplicate-detection matters (AFS § Test Data) — but the
    bytes must form a well-formed PNG for the OS file picker to accept it
    without complaint. Same helper as ELITEA-1832's test.
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
class TestArtifactUploadDuplicateSkip:
    """ELITEA-1829 — 'Skip' uploads only the non-duplicate file, leaves the
    duplicate entirely untouched.

    Verifies exactly one PUT fires (for the non-duplicate file), none for
    the duplicate; the success toast appears; the non-duplicate appears in
    the file table; and the duplicate's count/content/metadata are
    unchanged.
    """

    @pytest.mark.p2
    @allure.title(
        "'Skip' in 'Resolve duplicates' uploads only the non-duplicate "
        "file, leaves the duplicate untouched"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1829_upload-flow-duplicate-skip-saves-non-duplicate.md",
        "onetest-ai Test Case link",
    )
    def test_skip_uploads_only_non_duplicate_file(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """Skip uploads ONLY the non-duplicate file; the duplicate is never touched."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed sample.txt into the fresh bucket via API.
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, DUPLICATE_FILE_NAME, DUPLICATE_FILE_CONTENT, content_type="text/plain",
        )
        baseline_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
        assert baseline_metadata is not None, (
            f"Seed file '{DUPLICATE_FILE_NAME}' should exist in bucket "
            f"'{bucket_name}' immediately after seeding via the API"
        )

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

        with allure.step(
            "Steps 3-6 — Click the upload icon (native file explorer opens "
            "immediately), select both sample.txt and sample.png, confirm; "
            "the 'Upload files to ...' modal opens with the Path field "
            "pre-filled"
        ):
            artifacts_page.upload_files([str(duplicate_file_path), str(new_file_path)])
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
            "Step 8 — Verify the 'Resolve duplicates' modal opens listing "
            "only sample.txt as the duplicate, and that detection was "
            "purely client-side (zero network requests)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff — no "
                f"network request should fire, but observed: {requests_during_detection}"
            )
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert duplicate_names == [DUPLICATE_FILE_NAME], (
                f"'Resolve duplicates' modal should list exactly "
                f"[{DUPLICATE_FILE_NAME!r}] as the duplicate ({NEW_FILE_NAME!r} "
                f"is not a duplicate and must never appear here), got: {duplicate_names}"
            )

        with allure.step("Step 9 — Click Skip"):
            skip_put_requests = artifacts_page.capture_requests_matching(
                "artifacts/s3", method="PUT",
            )
            artifacts_page.click_resolve_duplicates_skip_button()
            artifacts_page.wait_for_resolve_duplicates_dialog_closed(timeout=DIALOG_TIMEOUT)

        with allure.step(
            "Step 10 — Verify a success notification is displayed with the "
            "exact text 'Your file(s) have been successfully uploaded!'"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 11 — Verify 'sample.png' is listed in the file table as a "
            "newly uploaded file"
        ):
            assert artifacts_page.file_exists(NEW_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{NEW_FILE_NAME}' should appear in the file table after Skip"
            )

        with allure.step(
            "Network proof — exactly one PUT for sample.png, none for "
            "sample.txt (Skip uploads only the non-duplicate)"
        ):
            put_urls = [r["url"] for r in skip_put_requests]
            new_file_puts = [u for u in put_urls if NEW_FILE_NAME in u]
            duplicate_puts = [u for u in put_urls if DUPLICATE_FILE_NAME in u]
            assert len(new_file_puts) == 1, (
                f"Expected exactly one PUT for '{NEW_FILE_NAME}', got "
                f"{len(new_file_puts)}: {new_file_puts}"
            )
            assert not duplicate_puts, (
                f"Expected NO PUT for the duplicate '{DUPLICATE_FILE_NAME}' "
                f"after Skip, but observed: {duplicate_puts}"
            )

        with allure.step(
            "Step 12 — Verify only one 'sample.txt' entry exists in the "
            "bucket (the original, not replaced)"
        ):
            bucket_files = artifact_api.list_bucket_files(bucket_name)
            duplicate_key_matches = [k for k in bucket_files if k == DUPLICATE_FILE_NAME]
            assert len(duplicate_key_matches) == 1, (
                f"Expected exactly one '{DUPLICATE_FILE_NAME}' key in the "
                f"bucket listing, got {len(duplicate_key_matches)}: "
                f"{[k for k in bucket_files if DUPLICATE_FILE_NAME.split('.')[0] in k]}"
            )

        with allure.step(
            "Step 13 — Verify the 'sample.txt' 'lastModified' timestamp and "
            "size have NOT changed (no UI-visible timestamp column — read "
            "via the S3 JSON listing endpoint, same technique as ELITEA-1832)"
        ):
            final_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
            assert final_metadata is not None, (
                f"'{DUPLICATE_FILE_NAME}' should still exist in the bucket after Skip"
            )
            assert final_metadata["lastModified"] == baseline_metadata["lastModified"], (
                f"'{DUPLICATE_FILE_NAME}' lastModified must be unchanged after "
                f"Skip: before={baseline_metadata['lastModified']!r}, "
                f"after={final_metadata['lastModified']!r}"
            )
            assert final_metadata.get("size") == baseline_metadata.get("size"), (
                f"'{DUPLICATE_FILE_NAME}' size must be unchanged after Skip: "
                f"before={baseline_metadata.get('size')}, after={final_metadata.get('size')}"
            )
            final_content = artifact_api.get_file(bucket_name, DUPLICATE_FILE_NAME)
            assert final_content == DUPLICATE_FILE_CONTENT, (
                f"'{DUPLICATE_FILE_NAME}' content must be byte-identical after Skip"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → upload → duplicate → skip flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the duplicate-skip upload "
                f"flow: {[m.text for m in console_errors]}"
            )
