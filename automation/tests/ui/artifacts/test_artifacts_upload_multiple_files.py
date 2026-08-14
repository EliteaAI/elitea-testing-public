"""UI Test for ELITEA-1826 — Upload Flow: Upload Multiple Files at Once.

Regression test: verifies the plain multi-file-at-once happy path — three
brand-new files selected simultaneously in the native file picker and
uploaded through the toolbar ``upload_files_button`` in ONE operation, with
no duplicates in play. This is the "upload actually completes" counterpart
to ELITEA-1832 (`test_artifacts_upload_duplicate_cancel.py`), whose test is
built entirely around the duplicate-detected → Resolve-duplicates → Cancel
path and never reaches a completed upload (zero network requests fire
there; the Upload click is purely a client-side diff). Here, clicking
"Upload" fires three concurrent PUT requests (one per file), all 200 OK, a
success toast appears with the exact expected text, and all three files
land in the file table with correct Name/Type/Size/Last-update metadata.

Test flow:
1. Seed a fresh, empty bucket via the ``artifact_bucket`` fixture.
2. Select the bucket; verify it is empty (baseline).
3-6. Click the toolbar upload button (native file chooser opens
   immediately), select all three files — ``sample1.txt``, ``sample1.png``,
   ``sample1.md`` — in one ``set_files()`` call (Playwright's equivalent of
   Ctrl/Shift+click multi-select), confirm; the "Upload files to ..." modal
   opens with ONE shared Path field pre-filled with the bucket name.
7. Click "Upload" — fires three separate PUT requests, one per file, all
   200 OK (verified after the file table confirms completion, to avoid the
   ``status: None`` race on ``capture_requests_matching()`` for
   multi-request flows — see ELITEA-1808's AFS).
8. A success toast appears with the exact text "Your file(s) have been
   successfully uploaded!".
9. All three files appear in the file table with Name, Type, Size, and
   Last-update populated; ``get_total_file_count_from_pagination() == 3``.

AFS: test-specs/artifacts/l2_upload-flow-upload-multiple-files-at-once_ELITEA-1826.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_multiple_files.py -v
"""

import logging
import re
import struct
import zlib

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, toast, file rows
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions, bucket panel load
DIALOG_TIMEOUT = 10_000           # dialog open transitions

# ELITEA-1826 AFS Test Step 9 viewport note (reconfirms ELITEA-1808's own
# finding): the "Last update" column is present in the DOM but visually
# clipped/hidden below ~1600px viewport width — it is NOT conditionally
# omitted based on data. The project's default context viewport (headed:
# fits the OS window; headless: 1366x768, see conftest.py's `context`
# fixture) is not guaranteed to be wide enough, so this test sets an
# explicit viewport before asserting the timestamp segment.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

TXT_FILE_NAME = "sample1.txt"
TXT_FILE_CONTENT = b"Sample text content for the ELITEA-1826 multi-file upload test.\n"

MD_FILE_NAME = "sample1.md"
MD_FILE_CONTENT = b"# Sample Markdown\n\nContent for the ELITEA-1826 multi-file upload test.\n"

PNG_FILE_NAME = "sample1.png"

SUCCESS_TOAST_TEXT = "Your file(s) have been successfully uploaded!"

# Confirmed live this run (AFS § Test Step 9): "DD-MM-YYYY, HH:MM AM/PM".
# Pattern only, never an exact value — the clock differs per run.
LAST_UPDATE_TIMESTAMP_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)")


def _minimal_png_bytes() -> bytes:
    """Build a valid, minimal 1x1 PNG in memory.

    Reused technique from ``test_artifacts_upload_duplicate_cancel.py:75-91``
    (ELITEA-1832) — content is irrelevant to this case's assertions beyond
    being a well-formed PNG the OS file picker accepts and that renders as
    "PNG Image" in the Type column (AFS § Test Data, confirmed live).
    """
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Multiple Files")
class TestArtifactsUploadMultipleFiles:
    """ELITEA-1826 — Upload multiple files at once via the toolbar button.

    Complementary/opposite scenario to ELITEA-1832
    (``test_artifacts_upload_duplicate_cancel.py``): a clean multi-file
    batch with NO duplicates, where the Upload click actually fires the PUT
    requests and the upload completes — a materially different code path
    than the duplicate-detection/Cancel flow that test exercises.
    """

    @pytest.mark.p1
    @allure.title(
        "Upload multiple files at once via the toolbar upload button"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1826_upload-flow-upload-multiple-files-at-once.md",
        "onetest-ai Test Case link",
    )
    def test_upload_multiple_files_at_once(self, page, artifact_bucket, tmp_path):
        """Select 3 files in one native-picker call, upload, verify metadata.

        Read-only from the fresh bucket's perspective going in — the bucket
        itself is the test's own mutation (via ``artifact_bucket``, deleted
        in its own teardown), the minimal state this observable inherently
        requires (workflow skill Hard Rule 10): the case's own subject IS
        the multi-file upload, so there is no pre-existing empty bucket to
        assert against read-only.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # AFS § Test Step 9 viewport note — set explicitly so the "Last
        # update" timestamp column is actually in view before asserting it.
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        txt_path = tmp_path / TXT_FILE_NAME
        txt_path.write_bytes(TXT_FILE_CONTENT)
        md_path = tmp_path / MD_FILE_NAME
        md_path.write_bytes(MD_FILE_CONTENT)
        png_path = tmp_path / PNG_FILE_NAME
        png_bytes = _minimal_png_bytes()
        png_path.write_bytes(png_bytes)

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step(
            "Step 2 — Select the fresh precondition bucket — verify it is "
            "empty (baseline, confirms the fixture handed over a genuinely "
            "empty bucket)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.is_bucket_empty(), (
                f"Precondition: bucket '{bucket_name}' should be empty "
                f"before the multi-file upload"
            )

        with allure.step(
            "Steps 3-6 — Click the upload icon (native file explorer opens "
            "immediately), select all three files at once via one "
            "set_files() call (Playwright's equivalent of Ctrl/Shift+click "
            "multi-select), confirm — verify the 'Upload files to ...' "
            "modal opens with ONE shared Path field pre-filled with the "
            "bucket name"
        ):
            # Steps 3/4/5/6 are one mechanically inseparable Playwright
            # action (same folding the AFS itself applies): the click, the
            # chooser firing, and set_files() with a LIST ARE the multi-file
            # confirm — there is no intermediate observable between them,
            # and no separate native "Open" click to drive.
            artifacts_page.upload_files([str(txt_path), str(png_path), str(md_path)])
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_text = artifacts_page.get_upload_path_prefix_text()
            assert f"{bucket_name}/" in path_text, (
                f"Path field should show the bucket name '{bucket_name}' as "
                f"its (single, shared) prefix, got: {path_text!r}"
            )

        with allure.step("Step 7 — Click Upload in the modal"):
            # Capture BEFORE clicking so the listener is attached before the
            # requests fire. Checked for count/status AFTER Step 9's
            # file-table condition wait below (not immediately here) — that
            # wait is the real completion signal and guarantees the PUTs
            # have already resolved by the time we read this list, avoiding
            # the `status: None` race ELITEA-1808's AFS documented for
            # `capture_requests_matching()` on multi-request flows.
            upload_put_requests = artifacts_page.capture_requests_matching(
                "artifacts/s3", method="PUT"
            )
            artifacts_page.click_upload_path_upload_button()

        with allure.step(
            "Step 8 — Verify a success notification is displayed with the "
            "exact text 'Your file(s) have been successfully uploaded!' — "
            "Playwright's auto-retrying expect(), not a single-shot read "
            "(the toast is short-lived / auto-dismisses quickly)"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 9 — Verify all three files are listed in the file table "
            "with Name, Type, Size, and Last-update populated"
        ):
            total_count = artifacts_page.get_total_file_count_from_pagination()
            assert total_count == 3, (
                f"Expected exactly 3 files in the bucket after the batch "
                f"upload, got {total_count} (a partial-upload regression "
                f"would show fewer)"
            )

            file_names = set(artifacts_page.get_file_names())
            assert file_names == {TXT_FILE_NAME, PNG_FILE_NAME, MD_FILE_NAME}, (
                f"Expected all three uploaded files in the table, got: "
                f"{file_names}"
            )

            txt_row = artifacts_page.get_file_row_text(TXT_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "Text" in txt_row, (
                f"'{TXT_FILE_NAME}' row should show Type 'Text', row text "
                f"was: {txt_row!r}"
            )
            expected_txt_size = f"{len(TXT_FILE_CONTENT)} B"
            assert expected_txt_size in txt_row, (
                f"'{TXT_FILE_NAME}' row should show Size {expected_txt_size!r} "
                f"(exact byte count of the generated content), row text "
                f"was: {txt_row!r}"
            )
            assert LAST_UPDATE_TIMESTAMP_PATTERN.search(txt_row), (
                f"'{TXT_FILE_NAME}' row should show a 'Last update' "
                f"timestamp matching DD-MM-YYYY, HH:MM AM/PM, row text "
                f"was: {txt_row!r}"
            )

            png_row = artifacts_page.get_file_row_text(PNG_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "PNG Image" in png_row, (
                f"'{PNG_FILE_NAME}' row should show Type 'PNG Image', row "
                f"text was: {png_row!r}"
            )
            expected_png_size = f"{len(png_bytes)} B"
            assert expected_png_size in png_row, (
                f"'{PNG_FILE_NAME}' row should show Size {expected_png_size!r} "
                f"(exact byte count of the generated content), row text "
                f"was: {png_row!r}"
            )
            assert LAST_UPDATE_TIMESTAMP_PATTERN.search(png_row), (
                f"'{PNG_FILE_NAME}' row should show a 'Last update' "
                f"timestamp matching DD-MM-YYYY, HH:MM AM/PM, row text "
                f"was: {png_row!r}"
            )

            md_row = artifacts_page.get_file_row_text(MD_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "Markdown" in md_row, (
                f"'{MD_FILE_NAME}' row should show Type 'Markdown', row "
                f"text was: {md_row!r}"
            )
            expected_md_size = f"{len(MD_FILE_CONTENT)} B"
            assert expected_md_size in md_row, (
                f"'{MD_FILE_NAME}' row should show Size {expected_md_size!r} "
                f"(exact byte count of the generated content), row text "
                f"was: {md_row!r}"
            )
            assert LAST_UPDATE_TIMESTAMP_PATTERN.search(md_row), (
                f"'{MD_FILE_NAME}' row should show a 'Last update' "
                f"timestamp matching DD-MM-YYYY, HH:MM AM/PM, row text "
                f"was: {md_row!r}"
            )

        with allure.step(
            "Step 7 (network proof) — verify the Upload click fired three "
            "concurrent PUT requests, one per file, all 200 OK — this is "
            "the load-bearing proof the upload actually completed, as "
            "opposed to ELITEA-1832's duplicate path (which fires zero "
            "requests)"
        ):
            assert len(upload_put_requests) == 3, (
                f"Expected exactly 3 PUT requests fired by the Upload "
                f"click (one per file), got {len(upload_put_requests)}: "
                f"{upload_put_requests}"
            )
            assert all(r["status"] == 200 for r in upload_put_requests), (
                f"All 3 upload PUT requests should return 200 OK, got: "
                f"{upload_put_requests}"
            )
            for expected_name in (TXT_FILE_NAME, PNG_FILE_NAME, MD_FILE_NAME):
                assert any(expected_name in r["url"] for r in upload_put_requests), (
                    f"Expected a PUT request whose URL contains "
                    f"{expected_name!r}, captured requests: "
                    f"{upload_put_requests}"
                )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → select-bucket → upload flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the multi-file upload "
                f"flow: {[m.text for m in console_errors]}"
            )
