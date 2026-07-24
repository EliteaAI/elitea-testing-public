"""UI Test for GAP-035 — Artifacts File List: Sort files by Name / Type /
Size / Last update column headers.

Regression test: verifies each sortable file-table column header (Name,
Type, Size, Last update) reorders the file list ascending on the first
click and descending on the second click, using the correct per-field
comparator (case-insensitive string, numeric file-size, real date — never
a lexical string compare), with the clicked header shown as the active sort
field via its own computed ``opacity``.

Test flow:
1. Seed a fresh bucket (via API, `artifact_bucket` fixture) with 3 files
   that differ by name, type, and size — `alpha.txt` (smallest), `beta.csv`
   (medium), `gamma.json` (largest) — uploaded with a deliberate gap between
   each so their `lastModified` timestamps land in distinct whole seconds
   (S3 `lastModified` truncates to whole seconds — a back-to-back upload
   loop risks a same-second tie that would make the default "Last update"
   order backend-listing-order-dependent instead of truly chronological).
2. Navigate to the bucket; verify the default sort is Last update
   descending (newest upload first) with no click, and that the "Last
   update" header is the active one.
3. Click each of the four sortable headers twice (ascending, then
   descending); verify the resulting row order after every click, and that
   the clicked header becomes the active one on its first (new-field)
   click.
4. Delete the bucket via its 3-dot menu → Delete → confirm; verify the
   success toast and that the bucket no longer appears in the list.

Overlap check (see AFS): `automation/pages/artifacts_page.py` and every file
under `automation/tests/ui/artifacts/` were grepped for any existing exercise
of the column-header sort feature — zero hits beyond incidental Python-side
`sorted()` calls used for assertion convenience in two unrelated ZIP-download
tests (neither clicks a column header or asserts row-reorder behavior). This
is a wholly fresh scenario.

AFS: test-specs/artifacts/l3_sort-file-list-by-column-headers_GAP-035.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority — AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_sort_file_list_by_column_headers.py -v
"""

import logging
import time
from datetime import datetime

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # rows, headers, dialogs
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions, bucket-list refetch

# GridTableHeader.jsx's styles.headerCell(isActive, ...) sets `opacity: 1` on
# the active sort-field header cell (0.7 otherwise) — the active-state
# indicator this test reads instead of a new selector (AFS § Concrete
# Handles). Asserted via Playwright's own auto-retrying `to_have_css` — the
# cell has `transition: opacity 0.2s ease`, so a one-shot read immediately
# after the click can sample it mid-transition (confirmed live: a raw
# evaluate() caught 0.7077 once, mid-animation).
ACTIVE_HEADER_OPACITY_CSS = "1"

FILE_ALPHA = "alpha.txt"
FILE_BETA = "beta.csv"
FILE_GAMMA = "gamma.json"

# Strict ascending-by-size ordering is the only load-bearing property here —
# exact byte counts are not asserted, only alpha < beta < gamma.
ALPHA_CONTENT = b"a" * 50
BETA_CONTENT = b"b" * 10_000
GAMMA_CONTENT = b"g" * 100_000


def _upload_and_wait_for_new_second(
    artifact_api, bucket_name: str, file_key: str, content: bytes, content_type: str,
) -> None:
    """Upload one file, then poll until the wall clock moves past its own
    ``lastModified`` second.

    S3 `lastModified` timestamps truncate to whole seconds (confirmed live,
    GAP-035 AFS § Preconditions) — issuing all three uploads back-to-back
    risks landing two of them in the same second, producing a same-timestamp
    tie that would make the "Last update" sort order depend on whatever
    order the S3 listing API happens to return, not true chronological
    order. Condition-based (not a fixed sleep, per the project's no-sleep
    convention): polls the just-uploaded file's own metadata against the
    wall clock in a tight loop until they diverge by at least one second.
    """
    artifact_api.upload_file(bucket_name, file_key, content, content_type=content_type)
    metadata = artifact_api.get_file_metadata(bucket_name, file_key)
    uploaded_epoch_second = int(
        datetime.fromisoformat(metadata["lastModified"].replace("Z", "+00:00")).timestamp()
    )
    while int(time.time()) == uploaded_epoch_second:
        time.sleep(0.1)


@allure.epic("Artifacts")
@allure.feature("File List Sorting")
class TestArtifactsSortFileListByColumnHeaders:
    """GAP-035 — Sort the artifacts file list by clicking Name / Type / Size /
    Last update column headers.

    Verifies the ascending/descending toggle and the correct per-field
    comparator (string / numeric size / date) on all four sortable columns,
    and that the clicked header becomes the visually active sort field.
    """

    @pytest.mark.p2
    @allure.title(
        "Clicking each sortable file-table column header (Name, Type, Size, "
        "Last update) reorders the file list ascending then descending"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_sort_file_list_by_column_headers(
        self, page, artifact_api, artifact_bucket,
    ):
        """Each sortable header reorders rows correctly and shows itself as active.

        Read-only from the bucket's perspective at the end: the bucket is
        mutated exactly once (seeded with 3 files, spaced) — the minimal
        state this observable inherently requires (workflow skill Hard Rule
        10) — then every sort assertion reads that state without further
        mutation, until the case's own Step 10 (bucket deletion).
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed 3 files that differ by name, type, and size,
        # each upload spaced into its own whole second so "Last update"
        # sorting is unambiguous (see _upload_and_wait_for_new_second).
        # ------------------------------------------------------------------
        _upload_and_wait_for_new_second(
            artifact_api, bucket_name, FILE_ALPHA, ALPHA_CONTENT, "text/plain",
        )
        _upload_and_wait_for_new_second(
            artifact_api, bucket_name, FILE_BETA, BETA_CONTENT, "text/csv",
        )
        _upload_and_wait_for_new_second(
            artifact_api, bucket_name, FILE_GAMMA, GAMMA_CONTENT, "application/json",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the bucket; verify the 3 seeded files "
            "appear with the default sort (Last update, descending — newest "
            "upload first) and that the 'Last update' header is active with "
            "no click needed"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_GAMMA, FILE_BETA, FILE_ALPHA], (
                f"Expected default sort (Last update desc) to list "
                f"{[FILE_GAMMA, FILE_BETA, FILE_ALPHA]}, got {file_names}"
            )
            expect(artifacts_page.last_update_column_header).to_have_css(
                "opacity", ACTIVE_HEADER_OPACITY_CSS, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 2 — Click the 'Name' column header; verify ascending "
            "case-insensitive string order and that the Name header becomes active"
        ):
            artifacts_page.click_column_header(artifacts_page.name_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_ALPHA, FILE_BETA, FILE_GAMMA], (
                f"Expected ascending name order {[FILE_ALPHA, FILE_BETA, FILE_GAMMA]}, "
                f"got {file_names}"
            )
            expect(artifacts_page.name_column_header).to_have_css(
                "opacity", ACTIVE_HEADER_OPACITY_CSS, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 3 — Click the 'Name' header again; verify the direction "
            "toggles to descending"
        ):
            artifacts_page.click_column_header(artifacts_page.name_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_GAMMA, FILE_BETA, FILE_ALPHA], (
                f"Expected descending name order {[FILE_GAMMA, FILE_BETA, FILE_ALPHA]}, "
                f"got {file_names}"
            )

        with allure.step(
            "Step 4 — Click the 'Size' column header; verify ascending "
            "NUMERIC byte-size order (not a lexical string compare on the "
            "displayed size text) and that the Size header becomes active"
        ):
            artifacts_page.click_column_header(artifacts_page.size_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_ALPHA, FILE_BETA, FILE_GAMMA], (
                f"Expected ascending numeric size order "
                f"{[FILE_ALPHA, FILE_BETA, FILE_GAMMA]} (alpha={len(ALPHA_CONTENT)}B < "
                f"beta={len(BETA_CONTENT)}B < gamma={len(GAMMA_CONTENT)}B), got {file_names}"
            )
            expect(artifacts_page.size_column_header).to_have_css(
                "opacity", ACTIVE_HEADER_OPACITY_CSS, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 5 — Click the 'Size' header again; verify descending "
            "order (largest first)"
        ):
            artifacts_page.click_column_header(artifacts_page.size_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_GAMMA, FILE_BETA, FILE_ALPHA], (
                f"Expected descending size order {[FILE_GAMMA, FILE_BETA, FILE_ALPHA]}, "
                f"got {file_names}"
            )

        with allure.step(
            "Step 6 — Click the 'Last update' column header; verify "
            "ascending date order (oldest upload first, via a real date "
            "comparator) and that the Last update header becomes active"
        ):
            artifacts_page.click_column_header(artifacts_page.last_update_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_ALPHA, FILE_BETA, FILE_GAMMA], (
                f"Expected ascending date order (oldest first) "
                f"{[FILE_ALPHA, FILE_BETA, FILE_GAMMA]}, got {file_names}"
            )
            expect(artifacts_page.last_update_column_header).to_have_css(
                "opacity", ACTIVE_HEADER_OPACITY_CSS, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 7 — Click the 'Last update' header again; verify "
            "descending order (newest first)"
        ):
            artifacts_page.click_column_header(artifacts_page.last_update_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_GAMMA, FILE_BETA, FILE_ALPHA], (
                f"Expected descending date order {[FILE_GAMMA, FILE_BETA, FILE_ALPHA]}, "
                f"got {file_names}"
            )

        with allure.step(
            "Step 8 — Click the 'Type' column header; verify ascending "
            "file-type-label order (CSV < JSON < Text) and that the Type "
            "header becomes active"
        ):
            artifacts_page.click_column_header(artifacts_page.type_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_BETA, FILE_GAMMA, FILE_ALPHA], (
                f"Expected ascending type-label order (CSV, JSON, Text) "
                f"{[FILE_BETA, FILE_GAMMA, FILE_ALPHA]}, got {file_names}"
            )
            expect(artifacts_page.type_column_header).to_have_css(
                "opacity", ACTIVE_HEADER_OPACITY_CSS, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 9 — Click the 'Type' header again; verify descending "
            "order (Text, JSON, CSV)"
        ):
            artifacts_page.click_column_header(artifacts_page.type_column_header)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert file_names == [FILE_ALPHA, FILE_GAMMA, FILE_BETA], (
                f"Expected descending type-label order (Text, JSON, CSV) "
                f"{[FILE_ALPHA, FILE_GAMMA, FILE_BETA]}, got {file_names}"
            )

        with allure.step(
            "Step 10 — Delete the bucket via its 3-dot menu → Delete → "
            "confirm; verify the success toast and that the bucket no "
            "longer appears in the list"
        ):
            artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.click_bucket_menu_delete_item(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            delete_response = artifacts_page.confirm_delete_bucket(timeout=UI_ELEMENT_TIMEOUT)
            assert delete_response.status == 200, (
                f"Expected bucket DELETE to return 200, got "
                f"{delete_response.status} for {delete_response.url}"
            )
            expect(artifacts_page.success_toast_message).to_have_text(
                f"The {bucket_name} bucket has been successfully deleted.",
                timeout=UI_ELEMENT_TIMEOUT,
            )
            artifacts_page.wait_for_bucket_removed_from_list(
                bucket_name, timeout=UI_ELEMENT_TIMEOUT,
            )
            assert artifacts_page.count_bucket_rows(bucket_name) == 0, (
                f"'{bucket_name}' should no longer be listed after deletion"
            )

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "sort + delete flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the column-header sort "
                f"flow: {[m.text for m in console_errors]}"
            )
