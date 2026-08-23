"""UI Test for ELITEA-1863 — File Preview/Edit: Unsupported File Type (.xlsx)
Shows the "Preview Not Available" Message.

Regression test: verifies that a non-previewable file type (``.xlsx``) has
NO preview entry point on its file row, and that — reached through the
product's own preview URL — the preview panel renders the unsupported state
(unavailable icon + "Preview Not Available" + "Preview is not supported for
this file type." + the supported-formats sentence + a working Download
button), with Save, Discard and the render-mode toggle group structurally
ABSENT.

Test flow:
1. Seed a fresh bucket (via API) with ``top-5-soccer-players.xlsx``.
2. Navigate to the bucket; verify the file table shows it, with the row's
   type/size cells reading "Excel Spreadsheet" and the formatted size.
3. Verify the "View/Edit file" icon resolves to 0 elements both BEFORE and
   AFTER hovering the row — an unsupported type has no preview icon at all
   (``ArtifactRowActions.jsx`` gates it on ``row.canPreview``).
4. Open the preview panel via the product's own preview URL route.
5. Verify the header shows the full ``<bucket>/<file>`` path.
6. Verify the unsupported-preview body: icon, heading, message, formats line.
7. Verify the centred Download button is present.
8. Verify Save and Discard are ABSENT (count 0), not merely disabled.
9. Verify no Preview/Raw render-mode toggle group is shown.
10. Click Download; verify the filename and byte-identical content.
11. Verify no console errors across the whole flow.

**Case-text drift (asserted per the LIVE contract, not the stale case
text — see the AFS Coverage Map):**
* Case steps 2-4 claim a "View/Edit file" icon appears on hover and opens
  the panel. It does not exist for an unsupported type, so the panel has no
  in-app entry point at all — filed as case-text clarification
  EliteaAI/elitea-testing-public#1692.
* Case step 9 says Save/Discard are "INACTIVE/greyed out". They are
  structurally absent (``PreviewHeader.jsx`` wraps both in
  ``{canPreview && …}``) — filed as EliteaAI/elitea-testing-public#1693.
  Contrast image files (ELITEA-1862), where they DO render, disabled.

**Fidelity:** no substitution of any kind. The preview panel is reached via
``/artifacts?bucket=…&file=…`` — the exact params ``Artifacts.jsx`` itself
writes on every preview open and restores on load — i.e. ordinary product
navigation (a bookmarked / shared preview link), NOT injected state. Every
asserted observable (panel text, absent controls, downloaded bytes) is
produced by the live product. No ``route.fulfill`` / ``page.evaluate`` /
``monkeypatch`` / mocked client anywhere.

AFS: test-specs/artifacts/l3_file-preview-unsupported-xlsx-preview-not-available_ELITEA-1863.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_unsupported_xlsx.py -v
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
DOWNLOAD_TIMEOUT = 10_000
ABSENCE_TIMEOUT = 3_000           # short poll for elements expected NOT to exist

FILE_NAME = "top-5-soccer-players.xlsx"
FILE_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
# The preview gate is a filename-EXTENSION whitelist (`canPreviewFile`,
# src/utils/filePreview.js — `xlsx` is absent from PREVIEWABLE_EXTENSIONS),
# never a content sniff, so a real workbook is not required. A stable stub
# payload is seeded instead so the downloaded-bytes assertion is exact.
FILE_CONTENT = b"ELITEA-1863 unsupported-preview stub payload for .xlsx\n" * 4

EXPECTED_TYPE_LABEL = "Excel Spreadsheet"
# `formatFileSize` (src/utils/filePreview.js) is base-1024; under 1 KiB it
# renders as a bare byte count.
EXPECTED_SIZE_LABEL = f"{len(FILE_CONTENT)} B"

EXPECTED_TITLE = "Preview Not Available"
EXPECTED_MESSAGE = "Preview is not supported for this file type."
EXPECTED_FORMATS_PREFIX = "Supported formats:"
EXPECTED_FORMATS_CONTAINS = ["txt", "md", "json"]


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewUnsupportedXlsx:
    """ELITEA-1863 — an unsupported .xlsx renders the "Preview Not Available"
    state with a working Download button and no edit controls.
    """

    @pytest.mark.p2
    @allure.title(
        "Unsupported .xlsx has no preview icon and renders "
        "'Preview Not Available' with a working Download button"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1863_file-preview-unsupported-xlsx-preview-not-available.md",
        "onetest-ai Test Case link",
    )
    def test_unsupported_xlsx_shows_preview_not_available(
        self, page, artifact_api, artifact_bucket,
    ):
        """An .xlsx file offers no preview entry point and, deep-linked,
        renders the unsupported-preview state.

        Read-only after seeding: the bucket is mutated exactly once (the
        seeded .xlsx) — the minimal state this observable requires — and
        every assertion then reads it without further mutation.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed top-5-soccer-players.xlsx into the fresh bucket
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type=FILE_CONTENT_TYPE,
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the Artifacts section, open the fixture "
            "bucket, and verify the .xlsx is listed with its type/size cells"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}'"
            )
            row_text = artifacts_page.get_file_row_text(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            )
            assert EXPECTED_TYPE_LABEL in row_text, (
                f"Row should show the recognised type '{EXPECTED_TYPE_LABEL}' "
                f"(src/utils/fileTypes.js mapping), got row text: {row_text!r}"
            )
            assert EXPECTED_SIZE_LABEL in row_text, (
                f"Row should show the formatted size '{EXPECTED_SIZE_LABEL}' "
                f"for the {len(FILE_CONTENT)}-byte seeded payload, got row "
                f"text: {row_text!r}"
            )

        with allure.step(
            "Steps 2-3 — Verify the 'View/Edit file' icon is ABSENT both "
            "before and after hovering the row (case steps 2-4 claim the "
            "opposite — clarification #1692)"
        ):
            # Asserting BEFORE any hover is what actually proves absence: an
            # icon that were merely hover-revealed would still be count 0
            # here, so the post-hover re-check below is what distinguishes
            # "absent for this file type" from "hidden until hovered".
            expect(artifacts_page.get_file_preview_button(FILE_NAME)).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )
            artifacts_page.hover_file_row(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.get_file_preview_button(FILE_NAME)).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )

        with allure.step(
            "Step 4 — Open the file's preview panel via the product's own "
            "preview URL route (the only path to this branch — the row has "
            "no preview icon, #1692)"
        ):
            artifacts_page.navigate_to_file_preview(
                bucket_name, FILE_NAME, timeout=NAVIGATION_TIMEOUT,
            )
            expect(artifacts_page.file_preview_close_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            f"Step 5 — Verify the panel header shows '<bucket>/{FILE_NAME}'"
        ):
            path_text = artifacts_page.get_file_preview_path_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert path_text == f"{bucket_name}/{FILE_NAME}", (
                f"Preview header should show the full path, expected "
                f"'{bucket_name}/{FILE_NAME}', got '{path_text}'"
            )

        with allure.step(
            "Steps 6-7 — Verify the unsupported-preview body: icon, "
            "'Preview Not Available' heading, the supporting message, and "
            "the supported-formats line"
        ):
            expect(artifacts_page.file_preview_unavailable_icon).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            title = artifacts_page.get_preview_unavailable_title_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert title == EXPECTED_TITLE, (
                f"Heading should read exactly '{EXPECTED_TITLE}', got '{title}'"
            )
            message = artifacts_page.get_preview_unavailable_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message == EXPECTED_MESSAGE, (
                f"Supporting message should read exactly '{EXPECTED_MESSAGE}' "
                f"for a TYPE-gated file, got '{message}'"
            )
            formats = artifacts_page.get_preview_unavailable_formats_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            # Deliberately NOT full equality — the sentence is a long
            # hardcoded literal in PreviewUnavailable.jsx that will churn as
            # formats are added (AFS step 5).
            assert formats.startswith(EXPECTED_FORMATS_PREFIX), (
                f"Supported-formats line should start with "
                f"'{EXPECTED_FORMATS_PREFIX}', got '{formats}'"
            )
            for fmt in EXPECTED_FORMATS_CONTAINS:
                assert fmt in formats, (
                    f"Supported-formats line should list '{fmt}', got '{formats}'"
                )

        with allure.step(
            "Step 8 — Verify the centred 'Download' button is present in the "
            "preview area"
        ):
            expect(
                artifacts_page.file_preview_unavailable_download_button
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(
                artifacts_page.file_preview_unavailable_download_button
            ).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 9 — Verify Save and Discard are structurally ABSENT "
            "(count 0), not merely disabled (case step 9 says 'greyed out' — "
            "clarification #1693)"
        ):
            expect(artifacts_page.file_preview_save_button).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_button).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )

        with allure.step(
            "Step 10 — Verify no Preview/Raw render-mode toggle group is shown"
        ):
            expect(artifacts_page.file_preview_mode_toggle_group).to_have_count(
                0, timeout=ABSENCE_TIMEOUT
            )

        with allure.step(
            "Step 11 — Click the panel's 'Download' button; verify the "
            "suggested filename and byte-identical content"
        ):
            download = artifacts_page.click_preview_unavailable_download(
                timeout=DOWNLOAD_TIMEOUT
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
                f"payload: expected {len(FILE_CONTENT)} bytes, got "
                f"{len(downloaded_bytes)} bytes"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → deep-link → download flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the unsupported-preview "
                f"flow: {[m.text for m in console_errors]}"
            )
