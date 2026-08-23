"""UI Test for ELITEA-1864 — File Preview/Edit: Unsupported File Type (.zip)
Has No Preview and Only Download/Delete in Actions.

Regression test: verifies the ROW-LEVEL contract for a non-previewable file
type (``.zip``) — no "View/Edit file" icon (ever, hovered or not), a 3-dot
actions dropdown restricted to exactly Download + Delete, and a working
single-file download with no ZIP-packaging progress dialog.

Test flow:
1. Seed a fresh bucket (via API) with ``new-file-storage.zip``, sized to
   exactly 235_520 bytes so the row's size cell reads the case's literal
   "230.0 KB" (``formatFileSize`` is base-1024 with one decimal).
2. Navigate to the bucket; verify the file table shows the file.
3. Verify the row's metadata cells read "ZIP Archive" / "230.0 KB".
4. Verify the "View/Edit file" icon resolves to 0 elements both BEFORE and
   AFTER hovering, while the 3-dot trigger is visible in both states.
5. Open the 3-dot dropdown; verify it contains EXACTLY ["Download",
   "Delete"], in that order — no preview / view-edit / Copy Content item.
6. Click "Download"; verify the suggested filename, byte-identical content,
   and that no ZIP-packaging progress dialog appears.
7. Verify no console errors across the whole flow.

**Case-text note:** case steps 3/5 phrase the row controls as appearing "on
hover". Neither the preview icon nor the 3-dot trigger is hover-gated in the
current product (already filed for this surface as
EliteaAI/elitea-testing-public#994). This test asserts the stronger,
hover-independent contract — both states are checked before AND after a
hover — so it holds either way, and would catch a future hover-gating
regression.

**Fidelity:** no substitution of any kind — every observable (row cells,
control presence, menu labels, downloaded bytes) is produced by the live
product and reached through ordinary UI gestures. No ``route.fulfill`` /
``page.evaluate`` / ``monkeypatch`` / mocked client anywhere.

AFS: test-specs/artifacts/l3_file-preview-unsupported-zip-no-preview-row-actions_ELITEA-1864.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_unsupported_zip_row_actions.py -v
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
# Deliberately SHORT (same rationale as ELITEA-1839): a genuinely blocking
# ZIP-prep flow would exceed it, so the timeout doubles as an immediacy
# assertion for the single-file download path.
DOWNLOAD_TIMEOUT = 5_000
ABSENCE_TIMEOUT = 3_000           # short poll for elements expected NOT to exist

FILE_NAME = "new-file-storage.zip"
# Exactly 230.0 KiB: `formatFileSize` (src/utils/filePreview.js) is base-1024
# with one decimal, and 235520 / 1024 == 230.0 exactly — so the row renders
# the case's literal "230.0 KB". A real archive is NOT required: the preview
# gate is a filename-EXTENSION whitelist (`canPreviewFile`; `zip` is absent
# from PREVIEWABLE_EXTENSIONS), never a content sniff.
FILE_SIZE_BYTES = 235_520
FILE_CONTENT = b"PK\x03\x04" + b"\x00" * (FILE_SIZE_BYTES - 4)

EXPECTED_TYPE_LABEL = "ZIP Archive"
EXPECTED_SIZE_LABEL = "230.0 KB"
EXPECTED_MENU_ITEMS = ["Download", "Delete"]


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewUnsupportedZipRowActions:
    """ELITEA-1864 — a .zip row offers no preview icon, only a two-item
    actions dropdown, and downloads intact.
    """

    @pytest.mark.p2
    @allure.title(
        "Unsupported .zip has no View/Edit icon and only Download + Delete "
        "in its actions dropdown"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1864_file-preview-unsupported-zip-no-preview-row-actions.md",
        "onetest-ai Test Case link",
    )
    def test_unsupported_zip_row_has_no_preview_and_two_actions(
        self, page, artifact_api, artifact_bucket,
    ):
        """A .zip row shows no preview entry point and downloads intact.

        Read-only after seeding: the bucket is mutated exactly once (the
        seeded .zip) — the minimal state this observable requires — and
        every assertion then reads it without further mutation ("Delete" is
        verified present in the dropdown, never clicked).
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed new-file-storage.zip into the fresh bucket
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="application/zip",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the Artifacts section and open the fixture "
            "bucket (the case's literal 'bucket-1' does not exist in this "
            "suite; the test seeds its own)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}'"
            )

        with allure.step(
            f"Step 2 — Verify the row's metadata cells read "
            f"'{EXPECTED_TYPE_LABEL}' / '{EXPECTED_SIZE_LABEL}'"
        ):
            row_text = artifacts_page.get_file_row_text(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            )
            assert EXPECTED_TYPE_LABEL in row_text, (
                f"Row should show the recognised type '{EXPECTED_TYPE_LABEL}' "
                f"(src/utils/fileTypes.js mapping), got row text: {row_text!r}"
            )
            assert EXPECTED_SIZE_LABEL in row_text, (
                f"Row should show '{EXPECTED_SIZE_LABEL}' for the "
                f"{FILE_SIZE_BYTES}-byte seeded payload, got row text: "
                f"{row_text!r}"
            )

        with allure.step(
            "Steps 3-5 — Verify the 'View/Edit file' icon is ABSENT and the "
            "3-dot actions trigger IS visible, both before and after "
            "hovering the row (neither control is hover-gated — #994)"
        ):
            # Asserting BEFORE any hover is what actually catches a future
            # hover-gating regression on the dot-menu trigger; the post-hover
            # re-check is what distinguishes "absent for this file type" from
            # "hidden until hovered" for the preview icon.
            expect(artifacts_page.get_file_preview_button(FILE_NAME)).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )
            expect(
                artifacts_page.get_file_actions_menu_button(FILE_NAME)
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            artifacts_page.hover_file_row(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)

            expect(artifacts_page.get_file_preview_button(FILE_NAME)).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )
            expect(
                artifacts_page.get_file_actions_menu_button(FILE_NAME)
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Steps 6-7 — Open the 3-dot actions dropdown; verify it contains "
            "EXACTLY ['Download', 'Delete'] in that order — no preview / "
            "view-edit / Copy Content item"
        ):
            artifacts_page.open_file_actions_menu(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            menu_items = artifacts_page.get_file_actions_menu_item_labels(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            )
            # Exact list equality (not a per-item is_visible sweep) — this is
            # what catches an ADDED item, which the case's "only Download and
            # Delete" expectation forbids.
            assert menu_items == EXPECTED_MENU_ITEMS, (
                f"The .zip row's actions dropdown should show exactly "
                f"{EXPECTED_MENU_ITEMS} in order, got {menu_items}"
            )

        with allure.step(
            "Step 8 — Click 'Download'; verify the suggested filename, "
            "byte-identical content, and that NO ZIP-packaging progress "
            "dialog appears (a single-file download streams the file itself)"
        ):
            download = artifacts_page.click_download_menu_item(
                timeout=DOWNLOAD_TIMEOUT
            )
            # Defensive/regression guard: the row dropdown's onDownload never
            # calls startZipDownload today, so this guards against the row
            # action ever being re-routed through the multi-select ZIP flow.
            expect(artifacts_page.zip_download_progress_dialog).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )
            assert download.suggested_filename == FILE_NAME, (
                f"Downloaded filename should be exactly '{FILE_NAME}', got "
                f"'{download.suggested_filename}'"
            )
            downloaded_path = download.path()
            assert downloaded_path is not None, (
                "Download should have completed to a local path"
            )
            downloaded_bytes = downloaded_path.read_bytes()
            assert downloaded_bytes == FILE_CONTENT, (
                "Downloaded bytes should be byte-identical to the seeded "
                f"archive: expected {len(FILE_CONTENT)} bytes, got "
                f"{len(downloaded_bytes)} bytes"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → menu → download flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the unsupported .zip row "
                f"flow: {[m.text for m in console_errors]}"
            )
