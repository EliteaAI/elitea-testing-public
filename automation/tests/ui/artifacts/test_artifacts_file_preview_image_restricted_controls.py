"""UI Test for ELITEA-1862 — File Preview/Edit: Image File Opens Directly
as Image Preview with Inactive Edit Controls.

Regression test: verifies that an image file opens directly as a rendered
``<img>`` (no Preview/Raw choice, no code editor, ever), that Save/Discard
are present but permanently disabled (no edit path exists for images), that
the render-mode toggle group and the language-select dropdown are both
structurally ABSENT (not merely hidden), and that the 3-dot actions dropdown
is restricted to exactly Download + Delete (Copy Content structurally
excluded for image files).

Test flow:
1. Seed a fresh bucket (via API) with ``diagram (2).png`` (a minimal valid
   PNG — verbatim filename including the space+parens).
2. Navigate to the bucket; verify the file table shows the file.
3. Hover the row; verify the "View/Edit file" icon becomes visible.
4. Click the icon; verify the image opens directly (no intermediate
   Raw/Preview choice) and becomes visible (condition-based wait — the
   image blob fetch can exceed a short/networkidle-based wait).
5. Verify the panel header shows the full path.
6. Verify Save and Discard are present and BOTH disabled.
7. Verify NO render-mode toggle group is present.
8. Verify NO language-select dropdown is present.
9. Verify NO CodeMirror text editor is present.
10. Verify the 3-dot actions menu is present.
11. Click it; verify the dropdown contains EXACTLY ["Download", "Delete"],
    in that order — no "Copy Content".
12. Verify no console errors during open or menu interaction.

AFS: test-specs/artifacts/l3_file-preview-image-restricted-controls_ELITEA-1862.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_image_restricted_controls.py -v
"""

import base64
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
IMAGE_LOAD_TIMEOUT = 20_000

FILE_NAME = "diagram (2).png"
# Minimal valid 1x1 transparent PNG — the case only requires a real,
# non-corrupt image file, not any specific visual content.
FILE_CONTENT = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YA"
    "AAAASUVORK5CYII="
)
EXPECTED_MENU_ITEMS = ["Download", "Delete"]


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewImageRestrictedControls:
    """ELITEA-1862 — An image file opens directly as an image preview with
    every edit-related control structurally restricted.
    """

    @pytest.mark.p2
    @allure.title(
        "Image file opens directly as image preview with inactive/absent edit controls"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1862_file-preview-image-restricted-controls.md",
        "onetest-ai Test Case link",
    )
    def test_image_file_opens_directly_with_restricted_controls(
        self, page, artifact_api, artifact_bucket,
    ):
        """An image file renders directly, with edit controls absent or disabled."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed diagram (2).png into the fresh bucket via API
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="image/png",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section and select the fixture bucket"):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}'"
            )

        with allure.step(
            "Step 2 — Hover the row; verify the 'View/Edit file' icon becomes visible"
        ):
            artifacts_page.hover_file_row(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_preview_button_visible(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            ), "'View/Edit file' icon should be visible after hovering the row"

        with allure.step(
            "Steps 3-4 — Click the icon; verify the image opens directly "
            "(no intermediate Raw/Preview choice) and becomes visible"
        ):
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_preview_image_visible(
                timeout=IMAGE_LOAD_TIMEOUT
            ), "Rendered <img> preview should become visible"

        with allure.step(
            "Step 5 — Verify the panel header shows the full path "
            f"'<bucket>/{FILE_NAME}'"
        ):
            path_text = artifacts_page.get_file_preview_path_text(timeout=UI_ELEMENT_TIMEOUT)
            assert path_text == f"{bucket_name}/{FILE_NAME}", (
                f"Editor header should show the full path, expected "
                f"'{bucket_name}/{FILE_NAME}', got '{path_text}'"
            )

        with allure.step(
            "Step 6 — Verify Save and Discard are present and BOTH DISABLED"
        ):
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be DISABLED for an image file (no edit path exists)"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should be DISABLED for an image file (no edit path exists)"

        with allure.step(
            "Step 7 — Verify NO render-mode toggle group (Preview/Raw "
            "tabs) is present for an image file"
        ):
            expect(artifacts_page.file_preview_mode_toggle_group).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step 8 — Verify NO language-select dropdown is present"):
            expect(artifacts_page.file_preview_language_select).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 9 — Verify NO CodeMirror text editor / content-editing "
            "area is present — only the image is displayed"
        ):
            expect(artifacts_page.file_preview_code_editor).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Step 10 — Verify the 3-dot actions menu is present"):
            expect(artifacts_page.file_preview_overflow_menu_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_overflow_menu_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 11 — Click the 3-dot menu; verify the dropdown contains "
            "EXACTLY Download + Delete, in that order — no 'Copy Content'"
        ):
            artifacts_page.open_file_preview_actions_menu(timeout=UI_ELEMENT_TIMEOUT)
            menu_items = artifacts_page.get_file_preview_menu_item_labels(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert menu_items == EXPECTED_MENU_ITEMS, (
                f"Editor panel menu for an image file should show exactly "
                f"{EXPECTED_MENU_ITEMS} in order (no 'Copy Content'), got {menu_items}"
            )
            page.keyboard.press("Escape")

        with allure.step(
            "Step 12 — Verify no console errors during open + menu interaction"
        ):
            assert not console_errors, (
                f"Unexpected console errors during image-file preview: "
                f"{[m.text for m in console_errors]}"
            )
