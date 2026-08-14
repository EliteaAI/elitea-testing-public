"""UI Test for ELITEA-1856 — File Preview/Edit: Actions Dropdown in Editor
Contains Copy Content, Download, Delete.

Regression test: verifies the editor panel's 3-dot actions dropdown shows
exactly Copy Content / Download / Delete (in that order), and that each
action works correctly — clipboard content, a matching download, and a real
backend delete (editor closes, row disappears, and a fresh API read confirms
server-side removal, not just an optimistic UI update).

Test flow:
1. Seed a fresh bucket (via API) with ``machine_learning.py``; grant clipboard
   permissions.
2. Open the file via the "View/Edit file" icon.
3. Open the 3-dot menu; verify it shows exactly Copy Content / Download /
   Delete, in order.
4. Click "Copy Content"; verify the clipboard holds the full file content.
5. Reopen the menu, click "Download"; verify the download's filename and size.
6. Reopen the menu, click "Delete"; verify the confirmation modal's LIVE text
   (case text is stale — see AFS Coverage Map, filed
   EliteaAI/elitea-testing-public#1109); confirm; verify the LIVE success
   toast text; verify the editor closes and the file is gone both from the
   DOM and a fresh API read.
7. Verify no console errors across the flow.

AFS: test-specs/artifacts/l3_file-preview-actions-dropdown_ELITEA-1856.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_actions_dropdown.py -v
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
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
DOWNLOAD_TIMEOUT = 10_000
DELETE_TIMEOUT = 15_000

FILE_NAME = "machine_learning.py"
FILE_CONTENT = (
    b"import numpy as np\n\n"
    b"def train(model, data):\n"
    b"    weights = np.zeros(len(data))\n"
    b"    for row in data:\n"
    b"        weights += row\n"
    b"    return weights\n"
)
EXPECTED_MENU_ITEMS = ["Copy Content", "Download", "Delete"]
# Confirmed live — differs from the case's stated text (no restore-warning
# clause on the editor-panel delete path). Filed EliteaAI/elitea-testing-public#1109.
EXPECTED_DELETE_CONFIRM_MESSAGE = f"Are you sure to delete the {FILE_NAME}?"
# Confirmed live — differs from the case's stated text. Same ticket as above.
EXPECTED_DELETE_SUCCESS_TOAST = "File deleted successfully"


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewActionsDropdown:
    """ELITEA-1856 — Editor panel's 3-dot actions dropdown: Copy Content,
    Download, Delete.

    Verifies dropdown content/order and that each action works: clipboard
    copy, download fidelity, and a real backend delete.
    """

    @pytest.mark.p2
    @allure.title(
        "Editor panel's actions dropdown contains Copy Content, Download, "
        "Delete and each works correctly"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1856_file-preview-actions-dropdown.md",
        "onetest-ai Test Case link",
    )
    def test_actions_dropdown_copy_download_delete(
        self, page, artifact_api, artifact_bucket,
    ):
        """The editor panel's dropdown shows the right items and each action works."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        page.context.grant_permissions(["clipboard-read", "clipboard-write"])

        # ------------------------------------------------------------------
        # Precondition — seed machine_learning.py into the fresh bucket via API
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/x-python",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Steps 1-2 — Navigate to Artifacts, open 'machine_learning.py' "
            "via the 'View/Edit file' icon, verify the editor panel is open"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Steps 3-4 — Click the 3-dot actions menu; verify it shows "
            "exactly Copy Content / Download / Delete, in this order"
        ):
            artifacts_page.open_file_preview_actions_menu(timeout=UI_ELEMENT_TIMEOUT)
            menu_items = artifacts_page.get_file_preview_menu_item_labels(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert menu_items == EXPECTED_MENU_ITEMS, (
                f"Dropdown should show exactly {EXPECTED_MENU_ITEMS} in order, "
                f"got {menu_items}"
            )

        with allure.step(
            "Steps 5-6 — Click 'Copy Content'; verify the clipboard holds "
            "the full file content (direct clipboard API read — stronger "
            "than 'paste into a text editor', same observable)"
        ):
            artifacts_page.click_file_preview_copy_content(timeout=UI_ELEMENT_TIMEOUT)
            clipboard_text = page.evaluate("navigator.clipboard.readText()")
            assert clipboard_text == FILE_CONTENT.decode(), (
                "Clipboard content should exactly match the uploaded file content"
            )

        with allure.step(
            "Steps 7-9 — Reopen the menu, click 'Download'; verify the "
            "suggested filename and a content-matching byte size"
        ):
            artifacts_page.open_file_preview_actions_menu(timeout=UI_ELEMENT_TIMEOUT)
            download = artifacts_page.click_file_preview_download(timeout=DOWNLOAD_TIMEOUT)
            assert download.suggested_filename == FILE_NAME, (
                f"Downloaded filename should be exactly '{FILE_NAME}', got "
                f"'{download.suggested_filename}'"
            )
            downloaded_path = download.path()
            assert downloaded_path is not None, "Download should have completed to a local path"
            downloaded_bytes = downloaded_path.read_bytes()
            assert downloaded_bytes == FILE_CONTENT, (
                "Downloaded file content should be byte-identical to the "
                f"uploaded content: expected {len(FILE_CONTENT)} bytes, got "
                f"{len(downloaded_bytes)} bytes"
            )

        with allure.step(
            "Steps 10-11 — Reopen the menu, click 'Delete'; verify the "
            "confirmation modal's LIVE message text (case text is stale — "
            "see AFS Coverage Map, filed EliteaAI/elitea-testing-public#1109)"
        ):
            artifacts_page.open_file_preview_actions_menu(timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.click_file_preview_delete(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_message).to_have_text(
                EXPECTED_DELETE_CONFIRM_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 12 — Click 'Delete' in the modal; wait on the "
            "deleteArtifact response"
        ):
            artifacts_page.confirm_file_preview_delete(timeout=DELETE_TIMEOUT)

        with allure.step(
            "Step 13 — Verify a success toast with the LIVE text 'File "
            "deleted successfully' (case text is stale — same ticket as above)"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                EXPECTED_DELETE_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 14 — Verify the editor closes and 'machine_learning.py' "
            "is no longer listed — checked both via the DOM AND a fresh API "
            "read (the DOM row disappearing could be an optimistic update; "
            "the API read confirms server-side removal)"
        ):
            expect(artifacts_page.file_preview_save_button).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.get_file_row(FILE_NAME)).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            remaining_files = artifact_api.list_bucket_files(bucket_name)
            assert FILE_NAME not in remaining_files, (
                f"'{FILE_NAME}' should be gone from the bucket per a fresh API "
                f"read, got: {remaining_files}"
            )

        with allure.step(
            "Side-channel check — no console errors across copy/download/delete"
        ):
            assert not console_errors, (
                f"Unexpected console errors during the actions-dropdown flow: "
                f"{[m.text for m in console_errors]}"
            )
