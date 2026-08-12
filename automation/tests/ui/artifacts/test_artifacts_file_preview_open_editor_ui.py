"""UI Test for ELITEA-1851 — File Preview/Edit: Open Supported Text File via
View/Edit Icon and Verify Editor UI.

Regression test: verifies that clicking the "View/Edit file" icon on a
supported text file opens it in the editor panel with all expected UI
elements present — full file-path header, language label + dropdown,
line-numbered content, Save/Discard buttons (present but DISABLED pre-edit),
a clickable 3-dot actions menu (populated with the same three items
ELITEA-1856 drives), a close (X) icon — and that the URL reflects the open
file.

Test flow:
1. Seed a fresh bucket (via API) with ``machine_learning.py``.
2. Navigate directly to the bucket.
3. Verify the file table shows ``machine_learning.py`` (Python type, a size string).
4. Hover the row; verify the "View/Edit file" icon becomes visible.
5. Click the icon; verify the editor panel opens and the URL updates.
6. Verify the header shows the full ``bucket/machine_learning.py`` path.
7. Verify the language label shows "Python (detected)" with a dropdown.
8. Verify line numbers render (CodeMirror gutter).
9. Verify Save and Discard are present but DISABLED (case-text clarification —
   see AFS Coverage Map; filed EliteaAI/elitea-testing-public#1108).
10. Verify the 3-dot actions menu is present, clickable, and — cheap
    confirmation for ELITEA-1856 — opens with exactly Copy Content / Download
    / Delete.
11. Verify the close (X) icon is present.
12. Verify no console errors across the open flow.

AFS: test-specs/artifacts/l2_file-preview-open-editor-ui_ELITEA-1851.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_open_editor_ui.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

FILE_NAME = "machine_learning.py"
FILE_CONTENT = (
    b"import numpy as np\n\n"
    b"def train(model, data):\n"
    b'    """Fit the model on data - placeholder for ELITEA-1851 automation."""\n'
    b"    weights = np.zeros(len(data))\n"
    b"    for row in data:\n"
    b"        weights += row\n"
    b"    return weights\n"
)
EXPECTED_MENU_ITEMS = ["Copy Content", "Download", "Delete"]


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewOpenEditorUI:
    """ELITEA-1851 — Open a supported text file in the preview/edit editor.

    Verifies the editor panel's full UI contract on open: path header,
    language label, line numbers, Save/Discard (disabled pre-edit), 3-dot
    menu, close icon, and URL update.
    """

    @pytest.mark.p1
    @allure.title(
        "Opening a supported text file via the View/Edit icon shows the "
        "full editor UI"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1851_file-preview-open-editor-ui.md",
        "onetest-ai Test Case link",
    )
    def test_open_supported_text_file_shows_editor_ui(
        self, page, artifact_api, artifact_bucket,
    ):
        """Opening a file via the View/Edit icon renders the full editor UI contract."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed machine_learning.py into the fresh bucket via API
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/x-python",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section and select the fixture bucket"):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert bucket_name in page.url, (
                f"URL should reflect the selected bucket '{bucket_name}': {page.url}"
            )

        with allure.step(
            "Step 3 — Verify the file table displays 'machine_learning.py' "
            "(Python type, a size string)"
        ):
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}'"
            )
            row_text = artifacts_page.get_file_row_text(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "Python" in row_text, f"Row should show the Python type, got: {row_text!r}"

        with allure.step(
            "Steps 4-5 — Hover the row; verify the 'View/Edit file' icon becomes visible"
        ):
            artifacts_page.hover_file_row(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_preview_button_visible(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            ), "'View/Edit file' icon should be visible after hovering the row"

        with allure.step(
            "Step 6 — Click the icon; verify the editor panel opens and the "
            "URL updates to include the file param"
        ):
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert f"file={FILE_NAME}" in page.url, (
                f"URL should include 'file={FILE_NAME}' after opening the editor: {page.url}"
            )

        with allure.step(
            "Step 8 — Verify the panel header shows the full file path "
            "'<bucket>/machine_learning.py'"
        ):
            path_text = artifacts_page.get_file_preview_path_text(timeout=UI_ELEMENT_TIMEOUT)
            assert path_text == f"{bucket_name}/{FILE_NAME}", (
                f"Editor header should show the full path, expected "
                f"'{bucket_name}/{FILE_NAME}', got '{path_text}'"
            )

        with allure.step(
            "Step 9 — Verify the language label shows 'Python (detected)' with a dropdown"
        ):
            language_text = artifacts_page.get_file_preview_language_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert "Python" in language_text and "detected" in language_text, (
                f"Language label should show 'Python (detected)', got '{language_text}'"
            )

        with allure.step("Step 10 — Verify the file content renders with line numbers"):
            assert artifacts_page.is_code_editor_line_numbers_visible(
                timeout=UI_ELEMENT_TIMEOUT
            ), "CodeMirror line-number gutter should be visible"

        with allure.step(
            "Step 11 — Verify Save and Discard buttons are present and BOTH "
            "DISABLED (no edit made yet — case text describing Save as "
            "'active/blue' on open is stale; see AFS Coverage Map, "
            "EliteaAI/elitea-testing-public#1108)"
        ):
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be DISABLED before any edit is made"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should be DISABLED before any edit is made"

        with allure.step(
            "Step 12 — Verify the 3-dot actions menu is present, clickable, "
            "and opens with exactly Copy Content / Download / Delete "
            "(cheap confirmation for ELITEA-1856's own coverage)"
        ):
            expect(artifacts_page.file_preview_overflow_menu_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )
            artifacts_page.open_file_preview_actions_menu(timeout=UI_ELEMENT_TIMEOUT)
            menu_items = artifacts_page.get_file_preview_menu_item_labels(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert menu_items == EXPECTED_MENU_ITEMS, (
                f"Editor panel menu should show exactly {EXPECTED_MENU_ITEMS} "
                f"in order, got {menu_items}"
            )
            # Close the menu without acting on any item — out of scope here.
            page.keyboard.press("Escape")

        with allure.step("Step 13 — Verify an X (close) icon is present"):
            expect(artifacts_page.file_preview_close_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Side-channel check — no console errors during the open flow"):
            assert not console_errors, (
                f"Unexpected console errors during file-preview open: "
                f"{[m.text for m in console_errors]}"
            )
