"""UI tests for the Artifacts LANDING PAGE rendering cases.

Covers three sibling TMS cases that all assert what the Artifacts page
renders for a given bucket state — same surface, three data preconditions:

- **ELITEA-1803** — bucket with at least one file: left-panel chrome
  (heading + create/search icons, storage selector, footer stats), the
  five-column file table with a correctly populated row, the toolbar icon
  set, and single-page pagination (``1 - 1 of 1``, both arrows disabled).
- **ELITEA-1804** — bucket with 12 files: page-size default, 10 rows on
  page 1, counter/arrow states across next → last page → prev, and the
  exact file slice shown on each page.
- **ELITEA-1805** — empty bucket: the empty state in BOTH panels, the
  absence of the file table AND of the pagination block, and the
  bucket-info tooltip reporting ``Number of files: 0``.

(ELITEA-1806, the fourth case of this cluster — the "project has no
buckets" empty state — is **blocked**: no bucket-free project exists for
the automation user, the suite has no project-lifecycle client, and faking
the buckets response would be a terminal substitution of the very thing
the case observes. See
``test-specs/artifacts/l3_artifacts-landing-page-no-buckets_ELITEA-1806.md``.)

CLARIFICATION (case-text drift, not a defect — reverse-masking guard):
- EliteaAI/elitea-testing-public#1617 — ELITEA-1805 step 11 says the
  Retention-Policy / Number-of-files tooltip appears on hovering the bucket
  name in the LEFT panel. Live, that element carries only a conditional
  overflow tooltip repeating the bucket name; the retention/file-count
  tooltip belongs to a separate info (i) icon in the MAIN-panel toolbar
  (``BucketInfoTooltip.jsx``). The tooltip and its content are correct — the
  location in the case text is not — so the live contract is asserted.

Fidelity: buckets and their files are seeded through ``ArtifactAPI``
(``artifact_bucket`` fixture + ``upload_file``) — **transit substitution
only**, declared in each AFS's § Fidelity Declaration. Every value asserted
below (footer stats, table contents, counters, arrow states, tooltip text)
is produced and rendered by the product from its own listing responses;
nothing is read off the seeding calls. The footer's bucket count is
cross-checked against the API's own bucket list rather than a literal,
because the project's bucket total drifts constantly (known teardown leak
#636).

AFS:
    test-specs/artifacts/l2_artifacts-landing-page-bucket-with-files_ELITEA-1803.md
    test-specs/artifacts/l3_artifacts-landing-page-pagination-more-than-10-files_ELITEA-1804.md
    test-specs/artifacts/l3_artifacts-landing-page-empty-bucket_ELITEA-1805.md

Markers:
    - ui: requires browser
    - regression: regression test
    - new: added on automation/base, not yet validated on deployed envs

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_landing_page_ui.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# The "Last update" column is width-gated (`hideBelow: 900` on the table's own
# width, ArtifactTable.jsx) — the same viewport pin ELITEA-1824's spec uses.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

STORAGE_PROVIDER_NAME = "Elitea S3 storage"

# Column FIELD keys → their visible labels. "Last update" is keyed `modified`,
# NOT `lastUpdate` (confirmed live + in ArtifactTable.jsx's ARTIFACT_COLUMNS).
EXPECTED_COLUMNS = {
    "name": "Name",
    "fileType": "Type",
    "size": "Size",
    "modified": "Last update",
    "actions": "Actions",
}

SINGLE_FILE_NAME = "sample.txt"
SINGLE_FILE_CONTENT = b"Sample text content for the ELITEA-1803 landing-page test.\n"
SINGLE_FILE_TYPE_LABEL = "Text"

# Zero-padded on purpose: the file table sorts by name ascending, so padding is
# what makes "page 1 = 01..10, page 2 = 11..12" deterministic (unpadded names
# would sort lexicographically and scramble the slices).
PAGINATION_FILE_COUNT = 12
PAGE_SIZE = 10

# Confirmed live: "DD-MM-YYYY, HH:MM AM/PM". Pattern only — never an exact
# value, the clock differs per run.
LAST_UPDATE_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)")
FILE_SIZE_PATTERN = re.compile(r"\d+(\.\d+)?\s*[KMG]?B")

# Label and value are two sibling <Typography> nodes inside one testid'd Box,
# so text_content() has no separator between them ("Buckets:757").
FOOTER_COUNT_PATTERN = re.compile(r"Buckets:\s*(\d+)")
FOOTER_SIZE_PATTERN = re.compile(r"Size:\s*\d+(\.\d+)?\s*[KMG]?B")

EMPTY_STATE_TEXT = "No files in this bucket"


def _pagination_file_name(index: int) -> str:
    """Return the seeded pagination file name for 1-based *index*."""
    return f"file-{index:02d}.txt"


@allure.epic("Artifacts")
@allure.feature("Landing Page UI")
class TestArtifactsLandingPageUI:
    """ELITEA-1803 / 1804 / 1805 — Artifacts landing-page rendering.

    Each test seeds its own bucket via the ``artifact_bucket`` fixture (the
    minimal state these observables inherently require, workflow skill Hard
    Rule 10 — the case's subject IS how a bucket in a specific state
    renders, so there is no pre-existing stable bucket to read). The
    fixture deletes it in teardown, subject to the known ``#636`` 404 leak.
    """

    @pytest.mark.p1
    @allure.title("ELITEA-1803 — Landing page renders fully for a bucket with files")
    @allure.description(
        "Verifies the whole Artifacts landing-page chrome for a bucket "
        "containing one file: left-panel heading + icons, storage selector, "
        "bucket selection and tree expansion, main-panel header, the "
        "five-column file table with a populated row, the toolbar icon set, "
        "the footer stats, and single-page pagination."
    )
    def test_landing_page_bucket_with_files(self, page, artifact_bucket, artifact_api):
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)
        bucket = artifact_bucket["name"]

        artifact_api.upload_file(bucket, SINGLE_FILE_NAME, SINGLE_FILE_CONTENT)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            expect(artifacts_page.buckets_heading).to_be_visible(timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 2 — Left-panel header: 'Buckets' label, create + search icons"):
            expect(artifacts_page.buckets_heading).to_have_text("Buckets")
            expect(artifacts_page.create_bucket_button).to_be_visible()
            expect(artifacts_page.search_buckets_button).to_be_visible()

        with allure.step("Step 3 — Bucket list sits under the storage provider with a dropdown arrow"):
            expect(artifacts_page.storage_selector).to_have_text(STORAGE_PROVIDER_NAME)
            expect(artifacts_page.storage_selector_arrow).to_be_visible()
            assert artifacts_page.get_visible_bucket_count() > 0, "No bucket rows rendered"

        with allure.step("Step 4 — Click the bucket that contains a file"):
            artifacts_page.click_bucket_row(bucket, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Bucket is highlighted and its file is listed beneath it"):
            assert artifacts_page.is_bucket_selected(bucket), (
                f"Bucket '{bucket}' did not become the selected row"
            )
            expect(artifacts_page.tree_item(SINGLE_FILE_NAME)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            # Mirror check: a bucket WITH files must not show the empty-tree
            # label (the positive twin of ELITEA-1805's own assertion).
            expect(artifacts_page.bucket_tree_empty_label(bucket)).to_have_count(0)

        with allure.step("Step 6 — Main panel header shows the bucket name"):
            expect(artifacts_page.breadcrumb_bucket_label).to_have_text(bucket)

        with allure.step("Step 7 — File table shows all five columns"):
            for field, label in EXPECTED_COLUMNS.items():
                expect(artifacts_page.column_header(field)).to_have_text(
                    label, timeout=UI_ELEMENT_TIMEOUT
                )

        with allure.step("Step 8 — The file row shows checkbox, name, type, size, timestamp and actions"):
            expect(artifacts_page.file_rows()).to_have_count(1)
            row_text = artifacts_page.get_file_row_text(SINGLE_FILE_NAME)
            assert SINGLE_FILE_NAME in row_text, f"File name missing from row: {row_text!r}"
            assert SINGLE_FILE_TYPE_LABEL in row_text, f"Type missing from row: {row_text!r}"
            assert FILE_SIZE_PATTERN.search(row_text), f"Size missing from row: {row_text!r}"
            assert LAST_UPDATE_PATTERN.search(row_text), f"Timestamp missing from row: {row_text!r}"
            expect(artifacts_page.file_row_checkboxes()).to_have_count(1)
            expect(artifacts_page.file_row_action_buttons()).to_have_count(1)

        with allure.step("Step 9 — Toolbar shows the search bar and upload/download/delete icons"):
            expect(artifacts_page.file_search_input).to_be_visible()
            expect(artifacts_page.upload_files_button).to_be_visible()
            expect(artifacts_page.download_files_button).to_be_visible()
            expect(artifacts_page.delete_files_button).to_be_visible()

        with allure.step("Step 10 — Left-panel footer reports the actual bucket count and total size"):
            footer_count_text = artifacts_page.get_buckets_footer_count_text()
            match = FOOTER_COUNT_PATTERN.search(footer_count_text)
            assert match, f"Footer bucket count not in 'Buckets: N' shape: {footer_count_text!r}"
            rendered_buckets = artifacts_page.get_rendered_bucket_names()
            assert int(match.group(1)) == len(rendered_buckets), (
                f"Footer claims {match.group(1)} buckets, the left panel renders "
                f"{len(rendered_buckets)}"
            )
            footer_size_text = artifacts_page.get_buckets_footer_size_text()
            assert FOOTER_SIZE_PATTERN.search(footer_size_text), (
                f"Footer size not in 'Size: X B/KB/MB/GB' shape: {footer_size_text!r}"
            )

        with allure.step("Step 11 — 'Rows per page' defaults to 10"):
            assert artifacts_page.get_rows_per_page_value() == str(PAGE_SIZE)

        with allure.step("Step 12 — Pagination counter reads '1 - 1 of 1'"):
            assert artifacts_page.get_pagination_info_text() == "1 - 1 of 1"

        with allure.step("Step 13 — Both prev and next arrows are present"):
            expect(artifacts_page.pagination_prev_button).to_be_visible()
            expect(artifacts_page.pagination_next_button).to_be_visible()

        with allure.step("Step 14 — Prev arrow is disabled on the first page"):
            expect(artifacts_page.pagination_prev_button).to_be_disabled()

        with allure.step("Step 15 — Next arrow is disabled when all files fit on one page"):
            expect(artifacts_page.pagination_next_button).to_be_disabled()

    @pytest.mark.p2
    @allure.title("ELITEA-1804 — Pagination across a bucket with more than 10 files")
    @allure.description(
        "Verifies the file table paginates a 12-file bucket correctly: 10 "
        "rows and '1 - 10 of 12' on page 1 with prev disabled and next "
        "enabled, '11 - 12 of 12' with the last two files and next disabled "
        "on page 2, and a full restoration of page 1 after clicking prev."
    )
    def test_landing_page_pagination_more_than_ten_files(
        self, page, artifact_bucket, artifact_api
    ):
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)
        bucket = artifact_bucket["name"]

        for index in range(1, PAGINATION_FILE_COUNT + 1):
            artifact_api.upload_file(
                bucket, _pagination_file_name(index), b"x" * (100 * index)
            )

        seeded_names = {
            _pagination_file_name(i) for i in range(1, PAGINATION_FILE_COUNT + 1)
        }

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            expect(artifacts_page.buckets_heading).to_be_visible(timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 2 — Click the bucket that contains 12 files"):
            artifacts_page.click_bucket_row(bucket, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Bucket is highlighted and its files are listed"):
            assert artifacts_page.is_bucket_selected(bucket), (
                f"Bucket '{bucket}' did not become the selected row"
            )
            expect(artifacts_page.breadcrumb_bucket_label).to_have_text(bucket)
            artifacts_page.wait_for_file_count(PAGE_SIZE, timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 4 — File table shows all five columns"):
            for field, label in EXPECTED_COLUMNS.items():
                expect(artifacts_page.column_header(field)).to_have_text(
                    label, timeout=UI_ELEMENT_TIMEOUT
                )

        with allure.step("Step 5 — 'Rows per page' defaults to 10"):
            assert artifacts_page.get_rows_per_page_value() == str(PAGE_SIZE)

        with allure.step("Step 6 — Exactly 10 rows are shown on the first page"):
            expect(artifacts_page.file_rows()).to_have_count(PAGE_SIZE)
            first_page_names = set(artifacts_page.get_file_names())
            assert first_page_names <= seeded_names, (
                f"Page 1 shows files that were never seeded: {first_page_names - seeded_names}"
            )

        with allure.step("Step 7 — Pagination counter reads '1 - 10 of 12'"):
            assert artifacts_page.get_pagination_info_text() == (
                f"1 - {PAGE_SIZE} of {PAGINATION_FILE_COUNT}"
            )

        with allure.step("Step 8 — Prev arrow is disabled on the first page"):
            expect(artifacts_page.pagination_prev_button).to_be_disabled()

        with allure.step("Step 9 — Next arrow is enabled"):
            expect(artifacts_page.pagination_next_button).to_be_enabled()

        with allure.step("Step 10 — Click the next arrow"):
            artifacts_page.click_pagination_next(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 11 — Counter updates to '11 - 12 of 12'"):
            assert artifacts_page.get_pagination_info_text() == (
                f"{PAGE_SIZE + 1} - {PAGINATION_FILE_COUNT} of {PAGINATION_FILE_COUNT}"
            )

        with allure.step("Step 12 — Prev arrow becomes enabled after leaving the first page"):
            expect(artifacts_page.pagination_prev_button).to_be_enabled()

        with allure.step("Step 13 — The table shows the remaining files, and none of page 1's"):
            last_page_names = set(artifacts_page.get_file_names())
            # The table's default order is NOT name-ascending (confirmed live —
            # the listing comes back in modification order, and same-second
            # uploads tie), so the contract asserted here is the PARTITION,
            # which is what "the next set of files" actually means: page 2 is
            # disjoint from page 1 and together they are exactly the 12 seeded
            # files.
            assert not (last_page_names & first_page_names), (
                f"Page 2 repeats files from page 1: {last_page_names & first_page_names}"
            )
            assert first_page_names | last_page_names == seeded_names, (
                "Pages 1+2 are not exactly the seeded file set: missing "
                f"{seeded_names - (first_page_names | last_page_names)}, unexpected "
                f"{(first_page_names | last_page_names) - seeded_names}"
            )

        with allure.step("Step 14 — Next arrow is disabled: 12 files means this IS the last page"):
            expect(artifacts_page.pagination_next_button).to_be_disabled()

        with allure.step("Step 15 — Next arrow remains disabled on the last page"):
            expect(artifacts_page.pagination_next_button).to_be_disabled()

        with allure.step("Step 16 — Only the remaining 2 files are displayed"):
            expect(artifacts_page.file_rows()).to_have_count(
                PAGINATION_FILE_COUNT - PAGE_SIZE
            )

        with allure.step("Step 17 — Click the prev arrow"):
            artifacts_page.click_pagination_prev(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 18 — Counter returns to '1 - 10 of 12'"):
            assert artifacts_page.get_pagination_info_text() == (
                f"1 - {PAGE_SIZE} of {PAGINATION_FILE_COUNT}"
            )

        with allure.step("Step 19 — Prev arrow is disabled again on the first page"):
            expect(artifacts_page.pagination_prev_button).to_be_disabled()

        with allure.step("Step 20 — 10 rows are shown again, and they are page 1's files"):
            expect(artifacts_page.file_rows()).to_have_count(PAGE_SIZE)
            assert set(artifacts_page.get_file_names()) == first_page_names, (
                "Returning to page 1 shows a different set of files than it did before"
            )

    @pytest.mark.p2
    @allure.title("ELITEA-1805 — Landing page renders the empty state for a bucket with no files")
    @allure.description(
        "Verifies the empty-bucket state in both panels: the left tree's "
        "'No files in this bucket' label, the centred empty state with its "
        "'Upload files' button, the absence of the file table (no rows AND "
        "no column headers) and of the pagination block, the still-present "
        "toolbar icons and footer stats, and the bucket-info tooltip "
        "reporting 'Number of files: 0'."
    )
    def test_landing_page_empty_bucket(self, page, artifact_bucket):
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)
        bucket = artifact_bucket["name"]  # fresh fixture bucket — empty by construction

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            expect(artifacts_page.buckets_heading).to_be_visible(timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 2 — Left-panel header: 'Buckets' label, create + search icons"):
            expect(artifacts_page.buckets_heading).to_have_text("Buckets")
            expect(artifacts_page.create_bucket_button).to_be_visible()
            expect(artifacts_page.search_buckets_button).to_be_visible()

        with allure.step("Step 3 — Bucket list sits under the storage provider with a dropdown arrow"):
            expect(artifacts_page.storage_selector).to_have_text(STORAGE_PROVIDER_NAME)
            expect(artifacts_page.storage_selector_arrow).to_be_visible()
            assert artifacts_page.get_visible_bucket_count() > 0, "No bucket rows rendered"

        with allure.step("Step 4 — Click the bucket that contains no files"):
            artifacts_page.click_bucket_row(bucket, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Bucket is highlighted and its tree shows 'No files in this bucket'"):
            assert artifacts_page.is_bucket_selected(bucket), (
                f"Bucket '{bucket}' did not become the selected row"
            )
            expect(artifacts_page.bucket_tree_empty_label(bucket)).to_have_text(
                EMPTY_STATE_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step 6 — Main panel header shows the bucket name"):
            expect(artifacts_page.breadcrumb_bucket_label).to_have_text(bucket)

        with allure.step("Step 7 — No file table is rendered (no rows AND no column headers)"):
            expect(artifacts_page.file_rows()).to_have_count(0)
            assert artifacts_page.get_column_header_count() == 0, (
                "File-table column headers rendered for an empty bucket"
            )

        with allure.step("Step 8 — Centre empty state shows the message and the 'Upload files' button"):
            expect(artifacts_page.empty_state_label).to_have_text(EMPTY_STATE_TEXT)
            expect(artifacts_page.upload_files_empty_state_button).to_be_visible()
            # Analyst addition: GridTablePagination renders null at
            # totalRows === 0 — a "0 - 0 of 0" footer would be a real bug.
            expect(artifacts_page.pagination_page_info).to_have_count(0)

        with allure.step("Step 9 — Toolbar still shows the search bar and upload/download/delete icons"):
            expect(artifacts_page.file_search_input).to_be_visible()
            expect(artifacts_page.upload_files_button).to_be_visible()
            expect(artifacts_page.download_files_button).to_be_visible()
            expect(artifacts_page.delete_files_button).to_be_visible()

        with allure.step("Step 10 — Left-panel footer reports the actual bucket count and total size"):
            footer_count_text = artifacts_page.get_buckets_footer_count_text()
            match = FOOTER_COUNT_PATTERN.search(footer_count_text)
            assert match, f"Footer bucket count not in 'Buckets: N' shape: {footer_count_text!r}"
            rendered_buckets = artifacts_page.get_rendered_bucket_names()
            assert int(match.group(1)) == len(rendered_buckets), (
                f"Footer claims {match.group(1)} buckets, the left panel renders "
                f"{len(rendered_buckets)}"
            )
            footer_size_text = artifacts_page.get_buckets_footer_size_text()
            assert FOOTER_SIZE_PATTERN.search(footer_size_text), (
                f"Footer size not in 'Size: X B/KB/MB/GB' shape: {footer_size_text!r}"
            )

        with allure.step(
            "Step 11 — Bucket-info tooltip shows the retention policy and 'Number of files: 0' "
            "(CLARIFICATION #1617 — main-panel info icon, not the left-panel bucket name)"
        ):
            artifacts_page.hover_bucket_info_icon(timeout=UI_ELEMENT_TIMEOUT)
            tooltip_text = artifacts_page.get_bucket_info_tooltip_text()
            retention = re.search(r"Retention Policy:\s*(\S.*?)\s*Number of files:", tooltip_text)
            assert retention and retention.group(1), (
                f"Tooltip has no retention-policy value: {tooltip_text!r}"
            )
            files_count = re.search(r"Number of files:\s*(\d+)", tooltip_text)
            assert files_count, f"Tooltip has no file count: {tooltip_text!r}"
            assert files_count.group(1) == "0", (
                f"Tooltip reports {files_count.group(1)} files for an empty bucket: {tooltip_text!r}"
            )
