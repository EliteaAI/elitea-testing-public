"""UI Test for ELITEA-1851 — File Preview/Edit: Open Supported Text File via
View/Edit Icon and Verify Editor UI.

Regression test: verifies that clicking a supported text file's row-level
Preview/View-Edit icon opens the file-preview/edit editor panel with the
full expected UI chrome — path header, auto-detected language label, a
CodeMirror instance with a line-number gutter, Save/Discard buttons, the
3-dot overflow menu, and a close icon — and that the browser URL updates
synchronously to include the opened file.

This is the first case in this suite to touch the file preview/edit editor
canvas (``PreviewHeader.jsx``/``PreviewContent.jsx`` in EliteaUI) — zero
prior page-object coverage and zero testids existed on this surface before
this case (see AFS § Concrete Handles) except the pre-existing 3-dot
overflow-menu trigger.

Test flow:
1. Seed a fresh bucket (via API) with ``machine_learning.py`` (a
   deterministically generated, syntactically-valid Python module).
2. Navigate directly to the bucket (folds case steps 1-2: Artifacts page
   load + bucket selection into one navigation).
3. Verify the file row shows Type "Python" and a well-formed Size string
   (the case's literal "bucket-1"/"18.5 KB" are case-text placeholders —
   see AFS § Preconditions/Test Data; neither is asserted literally).
4. Verify the row's Preview icon is present (CLARIFICATION vs. case text:
   confirmed live it is ALWAYS rendered, not hover-gated — see AFS § Known
   Defects #994).
5. Click the Preview icon; verify the editor panel opens and the URL
   updates synchronously to include ``&file=machine_learning.py``.
6. Verify the panel header shows the full ``{bucket}/machine_learning.py``
   path.
7. Verify the language selector shows "Python (detected)".
8. Verify the file content renders inside a CodeMirror instance with a
   left-hand line-number gutter.
9. Verify Save and Discard are both visible but DISABLED on a freshly
   opened, unedited file (CLARIFICATION vs. case text: confirmed live +
   via source that both start disabled, not "active" — see AFS § Known
   Defects #995).
10. Verify the 3-dot overflow menu is visible and enabled; open it and
    verify it contains "Copy Content", "Download", "Delete" (per-item
    locating is ELITEA-1856's scope).
11. Verify the close (X) icon is present; click it and verify the panel
    actually closes (URL drops ``&file=...``, file-list view returns) —
    Axis 2: a functional check beyond the case's own "presence" ask.
12. Verify no new console errors across the whole flow.

AFS: test-specs/artifacts/l2_open-supported-text-file-view-edit-icon-verify-editor-ui_ELITEA-1851.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_open_text_file_editor_ui.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, panel, buttons, menu
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions

FILE_NAME = "machine_learning.py"

# Well-formed file-size cell, e.g. "16.9 KB" / "512 B" — the AFS's own run
# rendered ~17.3 KB of content as "16.9 KB" (KB computed on a 1024 basis);
# the exact value is never asserted, only that a size string is present
# (AFS § Coverage Map: "Size asserted as non-empty/well-formed, not the
# literal 18.5 KB value" — that figure is a case-text placeholder).
FILE_SIZE_PATTERN = re.compile(r"\d+(\.\d+)?\s?(B|KB|MB)")

EXPECTED_LANGUAGE_LABEL = "Python (detected)"


def _python_fixture_content(target_size_bytes: int = 17_300) -> bytes:
    """Build a deterministic, syntactically-valid Python module of ~target size.

    Reused technique from ``test_artifacts_upload_multiple_files.py``'s own
    ``_minimal_png_bytes()`` helper — content is never asserted against (AFS:
    the case only asserts *that* the file opens and *what UI chrome*
    surrounds it), only that it renders as auto-detected Python (by file
    extension, confirmed live) and is large enough to exercise the editor's
    line-number gutter with more than a couple of lines (this run's own AFS
    observed 183+ numbered lines for a ~17.3 KB fixture).
    """
    header = (
        '"""ELITEA-1851 fixture module — a small linear-regression helper.\n\n'
        "Deterministically generated; content is never asserted against, only\n"
        "that it renders as auto-detected Python in the editor.\n"
        '"""\n\n'
    )
    chunks = [header]
    i = 0
    while sum(len(chunk) for chunk in chunks) < target_size_bytes:
        i += 1
        chunks.append(
            f"def linear_step_{i}(x, weight={i}.0, bias=0.5):\n"
            f'    """Compute one linear-regression step (fixture line {i}).\n\n'
            f'    Deterministic filler content, never asserted against.\n"""\n'
            f"    return weight * x + bias\n\n"
        )
    return "".join(chunks).encode("utf-8")


FILE_CONTENT = _python_fixture_content()


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactsOpenTextFileEditorUI:
    """ELITEA-1851 — Open a supported text file via the row's View/Edit icon
    and verify the editor panel's full UI chrome.
    """

    @pytest.mark.p1
    @allure.title(
        "Opening a supported text file via the row's View/Edit icon shows "
        "the full editor panel UI"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1851_open-supported-text-file-view-edit-icon-verify-editor-ui.md",
        "onetest-ai Test Case link",
    )
    def test_open_text_file_editor_ui(self, page, artifact_api, artifact_bucket):
        """Opening machine_learning.py shows path header, language label,
        line numbers, disabled Save/Discard, overflow menu, and close icon;
        the URL updates synchronously and closing actually closes the panel.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed machine_learning.py into the fresh bucket via
        # API (faster, browser-independent; the case tests the open-for-
        # preview flow, not the upload flow itself — same approach the
        # sibling ELITEA-1839 AFS already established for this feature area).
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/x-python",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate directly to the bucket (folds case steps "
            "1-2: Artifacts page load + bucket selection into one "
            "navigation); verify the file table shows exactly the seeded "
            "file with Type 'Python' and a well-formed Size"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)

            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}' after seeding"
            )
            row_text = artifacts_page.get_file_row_text(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "Python" in row_text, (
                f"'{FILE_NAME}' row should show Type 'Python', row text was: {row_text!r}"
            )
            assert FILE_SIZE_PATTERN.search(row_text), (
                f"'{FILE_NAME}' row should show a well-formed Size (e.g. '16.9 KB'), "
                f"row text was: {row_text!r}"
            )

        with allure.step(
            "Steps 2 — Verify the row's Preview/View-Edit icon is present "
            "(CLARIFICATION vs. case text: confirmed always rendered, not "
            "hover-gated — see AFS § Known Defects #994; no hover performed)"
        ):
            expect(artifacts_page.get_file_preview_button(FILE_NAME)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 3 — Click the Preview icon; verify the editor panel "
            "opens and the URL updates synchronously to include "
            "'&file=machine_learning.py'"
        ):
            artifacts_page.open_file_preview(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            expected_url_fragment = f"bucket={bucket_name}&file={FILE_NAME}"
            assert expected_url_fragment in page.url, (
                f"URL should include {expected_url_fragment!r} immediately "
                f"after opening the editor, got: {page.url}"
            )

        with allure.step(
            "Step 4 — Verify the panel header shows the full "
            "'{bucket}/machine_learning.py' path"
        ):
            header_text = artifacts_page.get_file_editor_header_text(timeout=UI_ELEMENT_TIMEOUT)
            expected_header = f"{bucket_name}/{FILE_NAME}"
            assert header_text == expected_header, (
                f"Editor header should read {expected_header!r}, got {header_text!r}"
            )

        with allure.step(
            "Step 5 — Verify the language selector shows 'Python (detected)'"
        ):
            language_label = artifacts_page.get_file_editor_language_label(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert language_label == EXPECTED_LANGUAGE_LABEL, (
                f"Language label should read {EXPECTED_LANGUAGE_LABEL!r}, "
                f"got {language_label!r}"
            )

        with allure.step(
            "Step 6 — Verify the file content renders inside a CodeMirror "
            "instance with a left-hand line-number gutter"
        ):
            assert artifacts_page.is_file_editor_line_numbers_visible(
                timeout=UI_ELEMENT_TIMEOUT
            ), "CodeMirror line-number gutter (.cm-lineNumbers) should be visible"
            content_text = artifacts_page.get_file_editor_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert "linear_step_1(" in content_text, (
                "Editor content should render the seeded file's text — "
                f"expected to find 'linear_step_1(' in the rendered content, "
                f"got a {len(content_text)}-char string"
            )

        with allure.step(
            "Step 7 — Verify Save and Discard are both visible but DISABLED "
            "on a freshly opened, unedited file (CLARIFICATION vs. case "
            "text: confirmed live + via source both start disabled, not "
            "'active' — see AFS § Known Defects #995)"
        ):
            expect(artifacts_page.file_editor_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_editor_save_button).to_be_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_editor_discard_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_editor_discard_button).to_be_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 8 — Verify the 3-dot overflow menu is visible and "
            "enabled; open it and verify it contains 'Copy Content', "
            "'Download', 'Delete' (per-item locating is ELITEA-1856's scope)"
        ):
            expect(artifacts_page.file_preview_overflow_menu_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_overflow_menu_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )
            artifacts_page.open_file_editor_overflow_menu(timeout=UI_ELEMENT_TIMEOUT)
            menu_text = artifacts_page.get_file_editor_overflow_menu_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            for expected_item in ("Copy Content", "Download", "Delete"):
                assert expected_item in menu_text, (
                    f"Overflow menu should contain {expected_item!r}, "
                    f"menu text was: {menu_text!r}"
                )
            # Close the still-open dropdown before proceeding — Escape avoids
            # an extra click potentially landing on a menu item.
            page.keyboard.press("Escape")

        with allure.step(
            "Step 9 — Verify the close (X) icon is present; click it and "
            "verify the panel actually closes (Axis 2 — a functional check "
            "beyond the case's own 'presence' ask): URL drops "
            "'&file=...', file-list view returns"
        ):
            expect(artifacts_page.file_editor_close_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            artifacts_page.close_file_preview(timeout=UI_ELEMENT_TIMEOUT)
            assert f"&file={FILE_NAME}" not in page.url, (
                f"URL should drop '&file={FILE_NAME}' after closing the "
                f"editor, got: {page.url}"
            )
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                "File-list view should be visible again after closing the editor"
            )

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "navigate → open → verify → close flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the open-text-file-editor "
                f"flow: {[m.text for m in console_errors]}"
            )
