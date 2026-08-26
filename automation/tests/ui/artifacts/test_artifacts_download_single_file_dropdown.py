"""UI Test for ELITEA-1839 — Download Flow: Download Single File via Actions
Dropdown.

Regression test: verifies that a single file can be downloaded via its file
row's per-row actions dropdown (the 3-dot ``...`` menu), that the download
starts immediately with no ZIP packaging or progress dialog, and that the
downloaded file's name and content are correct.

Test flow:
1. Seed a fresh bucket (via API) with ``a1/sample.txt``.
2. Navigate directly to the bucket's ``a1`` subfolder in one URL navigation
   (folds case steps 1-2: Artifacts page load + bucket/subfolder selection).
3. Verify ``sample.txt`` is the only file listed.
4. Open the file row's actions dot-menu; verify it shows exactly "Download"
   and "Delete".
5. Click "Download", captured via ``page.expect_download()`` with a
   deliberately short timeout — a genuinely blocking ZIP-prep flow would
   exceed it, so the timeout doubles as an immediacy assertion.
6. Verify no ZIP-preparation progress dialog is shown (defensive/regression
   guard — architecturally unreachable from this path, per AFS).
7. Verify the downloaded filename is exactly ``sample.txt``.
8. Verify the downloaded file's bytes are byte-identical to the seeded
   content (a strictly stronger "not corrupted" signal than a bare
   ``size > 0`` check).
9. Verify no new console errors across the flow.

Overlap check (see AFS): zero behavioral overlap with ELITEA-1327's
``test_artifacts_multi_file.py`` — that test spot-checks the download
mechanism (``size > 0``) as one step nested in a much larger agent-chat
data-loss regression; this case asserts the dropdown-download UX contract
itself (menu content, immediacy, no ZIP, filename fidelity, content
integrity), which ELITEA-1327 never touches.

AFS: test-specs/artifacts/l2_download-flow-single-file-actions-dropdown_ELITEA-1839.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_download_single_file_dropdown.py -v
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, dot-menu, menu items
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
# Deliberately SHORT — well under the default. A genuinely blocking ZIP-prep
# flow would exceed it, so this timeout is a meaningful immediacy assertion
# for case steps 7 + 10, not just a wait (AFS § Automation Hints).
DOWNLOAD_TIMEOUT = 5_000
DIALOG_ABSENCE_TIMEOUT = 3_000    # short poll for an element expected NOT to appear

FOLDER_NAME = "a1"
FILE_NAME = "sample.txt"
FILE_CONTENT = b"Sample content for ELITEA-1839 download test.\n"


@allure.epic("Artifacts")
@allure.feature("Download Flow")
class TestArtifactDownloadSingleFileDropdown:
    """ELITEA-1839 — Download a single file via the per-row actions dropdown.

    Verifies the dropdown-download UX contract: menu content ("Download" +
    "Delete"), immediate download with no ZIP packaging/progress dialog,
    exact filename fidelity, and byte-identical content.
    """

    @pytest.mark.p1
    @allure.title(
        "Single file downloads immediately via the actions dropdown, "
        "with no ZIP packaging"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1839_download-flow-single-file-actions-dropdown.md",
        "onetest-ai Test Case link",
    )
    def test_download_single_file_via_dropdown(
        self, page, artifact_api, artifact_bucket,
    ):
        """Downloading via the dropdown's 'Download' item is immediate, no ZIP.

        Read-only from the bucket's perspective at the end: the bucket is
        mutated exactly once (seeded with ``a1/sample.txt``) — the minimal
        state this observable inherently requires (workflow skill Hard
        Rule 10) — then every assertion reads that state without further
        mutation (Delete is verified visible, never clicked).
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed a1/sample.txt into the fresh bucket via API
        # (ArtifactAPI.upload_file — auto-creates the 'a1' folder node; no
        # separate folder-creation call exists or is needed, confirmed live
        # per the AFS).
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, f"{FOLDER_NAME}/{FILE_NAME}", FILE_CONTENT, content_type="text/plain",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate directly to the bucket's 'a1' subfolder "
            "(folds case steps 1-2: Artifacts page load + bucket/subfolder "
            "selection into one navigation)"
        ):
            artifacts_page.navigate_to_bucket_folder(
                bucket_name, FOLDER_NAME, timeout=NAVIGATION_TIMEOUT,
            )

        with allure.step(
            "Step 2 — Verify the file table shows exactly one file, 'sample.txt' "
            "(precondition state: bucket + subfolder containing exactly this file)"
        ):
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}' "
                f"folder '{FOLDER_NAME}' after seeding"
            )
            file_count = artifacts_page.get_total_file_count_from_pagination()
            assert file_count == 1, (
                f"Expected exactly 1 file in the freshly seeded subfolder, got {file_count}"
            )

        with allure.step(
            "Steps 3-4 — Open the file row's actions dot-menu; verify it "
            "shows 'Download' and 'Delete'"
        ):
            artifacts_page.open_file_actions_menu(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.download_menu_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_menu_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Steps 6-7+10 — Click 'Download'; verify the download fires "
            "immediately (short expect_download timeout doubles as an "
            "immediacy assertion) with no ZIP-preparation progress dialog shown"
        ):
            download = artifacts_page.click_download_menu_item(timeout=DOWNLOAD_TIMEOUT)
            # Defensive/regression guard (AFS): architecturally unreachable
            # from this path today — the dropdown's onDownload callback never
            # calls startZipDownload — so this is expected to always pass,
            # not a live positive-control.
            expect(artifacts_page.zip_download_progress_dialog).to_have_count(
                0, timeout=DIALOG_ABSENCE_TIMEOUT,
            )

        with allure.step(
            "Step 8 — Verify the downloaded file's suggested name is exactly 'sample.txt'"
        ):
            assert download.suggested_filename == FILE_NAME, (
                f"Downloaded filename should be exactly '{FILE_NAME}' (the base "
                f"name, not the full '{FOLDER_NAME}/{FILE_NAME}' key), got "
                f"'{download.suggested_filename}'"
            )

        with allure.step(
            "Step 9 — Verify the downloaded file's content is byte-identical "
            "to the seeded content (stronger than a bare 'not empty' check — "
            "detects truncation/corruption that preserves length)"
        ):
            downloaded_path = download.path()
            assert downloaded_path is not None, "Download should have completed to a local path"
            downloaded_bytes = downloaded_path.read_bytes()
            assert downloaded_bytes == FILE_CONTENT, (
                "Downloaded file content should be byte-identical to the "
                f"seeded content: expected {FILE_CONTENT!r}, got {downloaded_bytes!r}"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → open-menu → download flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the single-file dropdown "
                f"download flow: {[m.text for m in console_errors]}"
            )
