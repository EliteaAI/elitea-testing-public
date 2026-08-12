"""UI Test for ELITEA-1831 — Upload Flow, Duplicate Handling: Keep Both
Saves Both Files with a 'Copy' Suffix.

Verifies that clicking "Keep both" in the "Resolve duplicates" modal uploads
the new file under a RENAMED key — confirmed live format
``{baseName} - Copy{extension}`` (e.g. ``sample - Copy.txt``) — while never
re-touching the original duplicate's path, and that both files end up in
the bucket with distinct 'lastModified' timestamps.

Case-text CLARIFICATION (AFS § Test Steps, step 11): the source TMS case's
Test Data table names ``sample-copy.txt`` (hyphenated, no space) as its
illustrative example, hedged with "(or similar with 'copy' in name)". Live
product behavior renders ``sample - Copy.txt`` (space, hyphen, space,
capitalized "Copy") — NOT a product defect, filed as a case-text
clarification (EliteaAI/elitea-testing-public#1102). This test asserts the
confirmed live pattern, not the case text's literal example.

Shares the setup/navigation/upload-trigger prefix with
`test_artifacts_upload_duplicate_cancel.py` (ELITEA-1832) and
`test_artifacts_upload_duplicate_detected_modal.py` (ELITEA-1828) — reuses
the same proven page-object methods and fixtures, diverging only at the
button click (Keep both) and the resulting assertion chain.

AFS: test-specs/artifacts/l3_upload-flow-duplicate-keep-both-saves-copy-suffix_ELITEA-1831.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority; same marker ELITEA-1832 used)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_duplicate_keep_both.py -v
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
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions

DUPLICATE_FILE_NAME = "sample.txt"
DUPLICATE_FILE_CONTENT = (
    b"Original sample.txt content, seeded before the duplicate-keep-both upload attempt."
)
SUCCESS_TOAST_TEXT = "Your file(s) have been successfully uploaded!"
# Confirmed live format (AFS § Test Steps, step 11 CLARIFICATION):
# "{baseName} - Copy{extension}" — space, hyphen, space, capitalized "Copy".
EXPECTED_COPY_NAME = "sample - Copy.txt"


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Duplicate Handling")
class TestArtifactUploadDuplicateKeepBoth:
    """ELITEA-1831 — 'Keep both' saves both the original and a renamed copy.

    Verifies exactly one PUT fires (for the renamed copy key), none for the
    original duplicate path; the success toast appears; both files exist in
    the bucket listing; and both have distinct 'lastModified' timestamps.
    """

    @pytest.mark.p2
    @allure.title(
        "'Keep both' in 'Resolve duplicates' saves both the original and "
        "a renamed copy with distinct timestamps"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1831_upload-flow-duplicate-keep-both-copy-suffix.md",
        "onetest-ai Test Case link",
    )
    def test_keep_both_uploads_renamed_copy_alongside_original(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """Keep both uploads a renamed copy; the original duplicate is never re-touched."""
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

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step("Step 2 — Select the bucket containing sample.txt"):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"Precondition: '{DUPLICATE_FILE_NAME}' should be visible in "
                f"bucket '{bucket_name}' after seeding"
            )

        with allure.step(
            "Steps 3-6 — Click the upload icon (native file explorer opens "
            "immediately), select sample.txt, confirm; the 'Upload files "
            "to ...' modal opens with the Path field pre-filled"
        ):
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
            "Step 8 — Verify the 'Resolve duplicates' modal opens listing "
            "sample.txt as the duplicate, and that detection was purely "
            "client-side (zero network requests)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff — no "
                f"network request should fire, but observed: {requests_during_detection}"
            )
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert duplicate_names == [DUPLICATE_FILE_NAME], (
                f"'Resolve duplicates' modal should list exactly "
                f"[{DUPLICATE_FILE_NAME!r}] as the duplicate, got: {duplicate_names}"
            )

        with allure.step("Step 9 — Click Keep both"):
            keep_both_put_requests = artifacts_page.capture_requests_matching(
                "artifacts/s3", method="PUT",
            )
            artifacts_page.click_resolve_duplicates_keep_both_button()
            artifacts_page.wait_for_resolve_duplicates_dialog_closed(timeout=DIALOG_TIMEOUT)

        with allure.step(
            "Step 10 — Verify a success notification is displayed with the "
            "exact text 'Your file(s) have been successfully uploaded!'"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 11 — Verify the file table contains two entries: the "
            "original 'sample.txt' and a new entry with 'copy' added to "
            "the name (confirmed live format: 'sample - Copy.txt' — see "
            "the case-text CLARIFICATION in this file's module docstring)"
        ):
            assert artifacts_page.file_exists(EXPECTED_COPY_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"Renamed copy '{EXPECTED_COPY_NAME}' should appear in the "
                f"file table after Keep both"
            )
            bucket_files = artifact_api.list_bucket_files(bucket_name)
            assert DUPLICATE_FILE_NAME in bucket_files, (
                f"Original '{DUPLICATE_FILE_NAME}' must still be present "
                f"after Keep both, got bucket listing: {bucket_files}"
            )
            assert EXPECTED_COPY_NAME in bucket_files, (
                f"Renamed copy '{EXPECTED_COPY_NAME}' should be present in "
                f"the bucket listing, got: {bucket_files}"
            )
            assert len(bucket_files) == 2, (
                f"Expected exactly 2 files in the bucket after Keep both "
                f"(original + renamed copy), got {len(bucket_files)}: {bucket_files}"
            )

        with allure.step(
            "Network proof — exactly one PUT for the renamed copy key, "
            "none for the original 'sample.txt' path"
        ):
            put_urls = [r["url"] for r in keep_both_put_requests]
            copy_puts = [u for u in put_urls if "Copy" in u]
            original_puts = [
                u for u in put_urls
                if DUPLICATE_FILE_NAME in u and "Copy" not in u
            ]
            assert len(copy_puts) == 1, (
                f"Expected exactly one PUT for the renamed copy key, got "
                f"{len(copy_puts)}: {copy_puts}"
            )
            assert not original_puts, (
                f"Expected NO PUT for the original '{DUPLICATE_FILE_NAME}' "
                f"path after Keep both, but observed: {original_puts}"
            )

        with allure.step(
            "Step 12 — Verify both files have their own distinct "
            "'Last update' timestamps (no UI-visible timestamp column — "
            "read via the S3 JSON listing endpoint, same technique as "
            "ELITEA-1829/1832)"
        ):
            original_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
            copy_metadata = artifact_api.get_file_metadata(bucket_name, EXPECTED_COPY_NAME)
            assert original_metadata is not None, (
                f"'{DUPLICATE_FILE_NAME}' should still exist after Keep both"
            )
            assert copy_metadata is not None, (
                f"'{EXPECTED_COPY_NAME}' should exist after Keep both"
            )
            assert original_metadata["lastModified"] == baseline_metadata["lastModified"], (
                f"Original '{DUPLICATE_FILE_NAME}' lastModified must be "
                f"unchanged by Keep both: before="
                f"{baseline_metadata['lastModified']!r}, after="
                f"{original_metadata['lastModified']!r}"
            )
            assert copy_metadata["lastModified"] != original_metadata["lastModified"], (
                f"Renamed copy and original should have DISTINCT "
                f"lastModified timestamps, both got: "
                f"{original_metadata['lastModified']!r}"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → upload → duplicate → keep-both flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the duplicate-keep-both "
                f"upload flow: {[m.text for m in console_errors]}"
            )
