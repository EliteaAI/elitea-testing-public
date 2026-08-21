"""UI Test for ELITEA-1830 — Upload Flow, Duplicate Handling: Replace
Overwrites Existing File.

Regression test: verifies that clicking "Replace" in the "Resolve duplicates"
modal overwrites the existing file IN PLACE — exactly one entry remains in
the bucket (no ``- Copy`` variant, no second row), the success toast fires,
and the file's "Last update" timestamp, size and bytes are all the
replacement's.

Test flow:
1. Seed a fresh bucket (via API) with ``sample.txt``.
2. Open the bucket; record the row's UI-rendered "Last update" value and the
   backend ``lastModified`` / ``size`` baseline.
3. Select a DIFFERENT-length ``sample.txt`` in the native file picker and
   confirm the "Upload files to ..." dialog.
4. Click "Upload" — client-side duplicate detection (confirmed live: zero
   network requests).
5. Click "Replace" — exactly one PUT, to the ORIGINAL key.
6. Success toast, one row, newer timestamp, new size, new bytes.

Substitution declared (fidelity): the ONLY substitution is the API seed of
the precondition file (``artifact_api.upload_file``) — transit only, to
reach a bucket that already contains ``sample.txt``. Every asserted
observable (dialog contents, request trace, toast text, row count, rendered
timestamp/size cells, backend metadata and file bytes) is produced by the
product.

Step-13 granularity (AFS § Step-13 granularity caveat): the "Last update"
column renders at MINUTE resolution in LOCAL time
(``ArtifactTable.jsx`` -> ``format(lastModified, 'dd-MM-yyyy, hh:mm a')``),
so a seed and a replace landing in the same wall-clock minute would render
an identical string. "The timestamp was updated" is therefore asserted
STRICTLY against the backend ``lastModified`` (ms precision), and the UI is
asserted to carry that same value through faithfully — the API response is
the oracle, this test writes no expected timestamp of its own.

AFS: test-specs/artifacts/l3_upload-flow-duplicate-replace-overwrites-existing_ELITEA-1830.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority; same marker ELITEA-1831/1832 use)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_duplicate_replace.py -v
"""

import logging
import re
from datetime import datetime

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions
TABLE_REFETCH_TIMEOUT = 15_000    # file table refetch after a backend write

# The file table's "Last update" column clips below ~1600 px (test-specs/
# artifacts/_surface.md) — same viewport the sibling artifacts specs pin.
# Load-bearing here: steps 3 and 13 read that very column.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

DUPLICATE_FILE_NAME = "sample.txt"
# Deliberately DIFFERENT byte lengths (AFS § Test Data): the length delta
# makes "the file was overwritten" observable in the UI's own Size cell and
# in the backend `size`, independently of the minute-resolution timestamp.
ORIGINAL_CONTENT = b"ORIGINAL sample.txt content, seeded pre-replace.\n"
REPLACEMENT_CONTENT = (
    b"REPLACEMENT sample.txt content, uploaded through the UI to overwrite "
    b"the original file in place.\n"
)
SUCCESS_TOAST_TEXT = "Your file(s) have been successfully uploaded!"

# Matches ArtifactTable.jsx's ARTIFACT_TABLE_CONFIG.DATE_FORMAT
# ('dd-MM-yyyy, hh:mm a'). The "Last update" column has no per-cell testid
# (ArtifactTable renders data cells through the shared, generic
# GridTableRowDataCell), so its displayed value is read via a regex match on
# the row's full text — the established, merged, testid-compliant pattern
# (`test_artifacts_file_preview_edit_save.py`), never a new raw locator.
LAST_UPDATE_TIMESTAMP_RE = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} [AP]M")
LAST_UPDATE_TIMESTAMP_FORMAT = "%d-%m-%Y, %I:%M %p"


def _extract_last_update_display(row_text: str) -> str:
    """Return the file row's UI-rendered 'Last update' string, as displayed.

    Args:
        row_text: A file row's full stripped text (as returned by
            :meth:`ArtifactsPage.get_file_row_text`).

    Returns:
        The rendered timestamp string, e.g. ``"21-08-2026, 08:40 PM"``.
    """
    match = LAST_UPDATE_TIMESTAMP_RE.search(row_text)
    assert match, (
        "File row should render a 'Last update' timestamp matching "
        f"'dd-MM-yyyy, hh:mm a': {row_text!r}"
    )
    return match.group()


def _backend_timestamp(iso_utc: str) -> datetime:
    """Parse the backend's UTC ``lastModified`` into a tz-aware datetime.

    Args:
        iso_utc: e.g. ``"2026-08-21T17:40:37.000Z"``.

    Returns:
        Timezone-aware ``datetime`` in UTC.
    """
    return datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))


def _expected_last_update_display(iso_utc: str) -> str:
    """Render the backend's ``lastModified`` the way the UI column renders it.

    The API response is the oracle: the expected UI string is DERIVED from
    the product's own metadata (UTC -> local, ``dd-MM-yyyy, hh:mm a``), never
    hand-written by the test.

    Args:
        iso_utc: Backend ``lastModified`` value.

    Returns:
        The string the "Last update" cell must display.
    """
    return _backend_timestamp(iso_utc).astimezone().strftime(LAST_UPDATE_TIMESTAMP_FORMAT)


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Duplicate Handling")
class TestArtifactUploadDuplicateReplace:
    """ELITEA-1830 — 'Replace' overwrites the existing file in place.

    Verifies exactly one PUT fires to the ORIGINAL key, the success toast
    appears, exactly one ``sample.txt`` entry remains, and its timestamp,
    size and bytes are the replacement's.
    """

    @pytest.mark.p2
    @allure.title(
        "'Replace' in 'Resolve duplicates' overwrites the existing file in "
        "place, leaving exactly one entry with an updated timestamp"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1830_upload-flow-duplicate-replace-overwrites-existing.md",
        "onetest-ai Test Case link",
    )
    def test_replace_overwrites_existing_file(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """Replace overwrites the duplicate in place — one entry, newer metadata.

        Substitution declared: the precondition file is seeded via the API
        (transit only — it merely creates the collision the case needs);
        every asserted observable is produced by the product.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Setup (preconditions, not case steps) — seed sample.txt into the
        # fresh bucket via the API, and write the DIFFERENT-length
        # replacement file into tmp_path (project convention; no checked-in
        # upload-fixture directory exists).
        # ------------------------------------------------------------------
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifact_api.upload_file(
            bucket_name, DUPLICATE_FILE_NAME, ORIGINAL_CONTENT, content_type="text/plain",
        )
        baseline_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
        assert baseline_metadata is not None, (
            f"Seed file '{DUPLICATE_FILE_NAME}' should exist in bucket "
            f"'{bucket_name}' immediately after seeding via the API"
        )

        replacement_file_path = tmp_path / DUPLICATE_FILE_NAME
        replacement_file_path.write_bytes(REPLACEMENT_CONTENT)
        assert len(REPLACEMENT_CONTENT) != len(ORIGINAL_CONTENT), (
            "Test-data invariant: the replacement must differ in byte length "
            "from the seed, so the overwrite is observable in the Size cell "
            "independently of the minute-resolution timestamp"
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step(
            "Step 2 — Select the bucket that already contains sample.txt"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"Precondition: '{DUPLICATE_FILE_NAME}' should be visible in "
                f"bucket '{bucket_name}' after seeding"
            )

        with allure.step(
            "Step 3 — Note the current 'Last update' timestamp of sample.txt "
            "(UI-rendered cell + the backend lastModified baseline)"
        ):
            artifacts_page.wait_for_file_count(1, timeout=TABLE_REFETCH_TIMEOUT)
            row_text_before = artifacts_page.get_file_row_text(
                DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT,
            )
            last_update_before = _extract_last_update_display(row_text_before)
            assert last_update_before == _expected_last_update_display(
                baseline_metadata["lastModified"]
            ), (
                "The rendered 'Last update' cell should display the backend's "
                f"own lastModified ({baseline_metadata['lastModified']!r}) in "
                f"local time, got: {last_update_before!r} (row: {row_text_before!r})"
            )
            logger.info("Baseline 'Last update' displayed as %r", last_update_before)

        with allure.step(
            "Steps 4-6 — Click the upload icon (native file explorer opens "
            "immediately), select sample.txt (same name as the existing "
            "file), confirm; the 'Upload files to ...' modal opens"
        ):
            # Steps 4/5/6 are one mechanically inseparable Playwright action:
            # `expect_file_chooser` must wrap the click, and files are set the
            # instant the chooser resolves — there is no intermediate
            # observable between "click" and "files chosen" (the same folding
            # the AFS applies). If the chooser never opened, `upload_files()`
            # would raise a timeout here.
            artifacts_page.upload_files([str(replacement_file_path)])
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)

        with allure.step(
            "Step 7 — Verify the 'Upload files to ...' modal is open with the "
            "Path field pre-filled with the bucket name"
        ):
            path_prefix = artifacts_page.get_upload_path_normalized_prefix()
            assert path_prefix == f"{bucket_name}/", (
                f"Path field's read-only prefix should be exactly "
                f"'{bucket_name}/', got: {path_prefix!r}"
            )

        with allure.step("Step 8 — Click Upload"):
            requests_during_detection = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_upload_path_upload_button()

        with allure.step(
            "Step 9 — Verify the 'Resolve duplicates' modal opens listing "
            "sample.txt as the duplicate, and that detection was purely "
            "client-side (zero network requests)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff "
                "against the already-fetched bucket listing — no network "
                f"request should fire, but observed: {requests_during_detection}"
            )
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert duplicate_names == [DUPLICATE_FILE_NAME], (
                f"'Resolve duplicates' modal should list exactly "
                f"[{DUPLICATE_FILE_NAME!r}] as the duplicate, got: {duplicate_names}"
            )

        with allure.step("Step 10 — Click Replace"):
            replace_put_requests = artifacts_page.capture_requests_matching(
                "artifacts/s3", method="PUT",
            )
            artifacts_page.click_resolve_duplicates_replace_button()
            artifacts_page.wait_for_resolve_duplicates_dialog_closed(timeout=DIALOG_TIMEOUT)

        with allure.step(
            "Step 11 — Verify a success notification is displayed with the "
            "exact text 'Your file(s) have been successfully uploaded!'"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 12 — Verify exactly one sample.txt entry exists in the "
            "file table (no duplicate rows), corroborated by the bucket "
            "listing endpoint"
        ):
            artifacts_page.wait_for_file_count(1, timeout=TABLE_REFETCH_TIMEOUT)
            bucket_files = artifact_api.list_bucket_files(bucket_name)
            assert bucket_files == [DUPLICATE_FILE_NAME], (
                f"Replace must leave exactly one entry, '{DUPLICATE_FILE_NAME}' "
                f"(no '- Copy' variant), got bucket listing: {bucket_files}"
            )
            assert artifacts_page.get_total_file_count_from_pagination() == 1, (
                "Pagination total should report exactly 1 file after Replace"
            )

        with allure.step(
            "Network proof — exactly ONE PUT, to the ORIGINAL key (a true "
            "in-place overwrite, not a delete-then-create nor a renamed copy)"
        ):
            put_urls = [r["url"] for r in replace_put_requests]
            assert len(put_urls) == 1, (
                f"Replace should fire exactly one PUT, got {len(put_urls)}: {put_urls}"
            )
            assert f"/{bucket_name}/{DUPLICATE_FILE_NAME}" in put_urls[0], (
                f"The single PUT must target the ORIGINAL key "
                f"'/{bucket_name}/{DUPLICATE_FILE_NAME}', got: {put_urls[0]!r}"
            )
            assert "Copy" not in put_urls[0], (
                f"Replace must not write to a '- Copy' key, got: {put_urls[0]!r}"
            )

        with allure.step(
            "Step 13 — Verify the 'Last update' timestamp has been updated: "
            "backend lastModified strictly newer (ms precision — the case's "
            "actual claim), the UI cell carrying that same value through, "
            "and the size/bytes now the replacement's"
        ):
            metadata_after = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
            assert metadata_after is not None, (
                f"'{DUPLICATE_FILE_NAME}' should still exist after Replace"
            )
            assert _backend_timestamp(metadata_after["lastModified"]) > _backend_timestamp(
                baseline_metadata["lastModified"]
            ), (
                "'lastModified' must be strictly newer after Replace: "
                f"before={baseline_metadata['lastModified']!r}, "
                f"after={metadata_after['lastModified']!r}"
            )
            assert metadata_after["size"] == len(REPLACEMENT_CONTENT), (
                f"Size must be the replacement's ({len(REPLACEMENT_CONTENT)} B), "
                f"got {metadata_after['size']} (seed was "
                f"{baseline_metadata.get('size')} B)"
            )
            content_after = artifact_api.get_file(bucket_name, DUPLICATE_FILE_NAME)
            assert content_after == REPLACEMENT_CONTENT, (
                "File bytes must be the replacement's after Replace — a "
                "metadata-only touch would pass a timestamp check alone"
            )

            # UI carries the product's own values through faithfully. The
            # expected strings are DERIVED from the API response above (the
            # oracle), never hand-written — see the module docstring's
            # step-13 granularity note.
            expected_last_update = _expected_last_update_display(
                metadata_after["lastModified"]
            )
            expected_size_display = f"{metadata_after['size']} B"
            artifacts_page.wait_for_file_row_to_contain_text(
                DUPLICATE_FILE_NAME, expected_last_update, timeout=TABLE_REFETCH_TIMEOUT,
            )
            row_text_after = artifacts_page.get_file_row_text(
                DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT,
            )
            assert expected_size_display in row_text_after, (
                f"The row's Size cell should render {expected_size_display!r} "
                f"(the backend's own size) after Replace, got: {row_text_after!r}"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → upload → duplicate → replace flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the duplicate-replace "
                f"upload flow: {[m.text for m in console_errors]}"
            )
