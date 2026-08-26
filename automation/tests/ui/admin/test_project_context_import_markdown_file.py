"""UI test — the toolbar's upload-file icon imports a markdown file into the
Project Context editor, and the imported content stays editable.

Walks the real user path: empty state -> Create -> click the "Import from
markdown file" icon -> the browser's file picker opens -> pick a .md file ->
the file's text lands in the editor verbatim, the product's own character
counter reflects its length and Save goes live -> one more character proves the
imported content is editable.

Fidelity (no substitution): the file is handed to the product's own hidden
<input type="file"> through Playwright's file-chooser interception, which stands
in for the OS picker Playwright cannot drive and leaves the application's
handleImportClick / handleFileUpload / FileReader path completely intact. Every
asserted value -- the editor lines, the character counter, the dirty state -- is
produced by the product. No page.route / route.fulfill / monkeypatch /
page.evaluate.

Case-text divergence (declared, reverse-masking guard): the case calls the
target the "Project Background editor". No section of that name exists -- it is
the Project Context editor at /settings/project-context/edit, and the upload
icon lives in that editor's toolbar, so the editor is opened first. Already
filed as clarification #1792 (module-wide, ELITEA-2266 analysis); not re-filed.

Test case: ELITEA-2271
AFS: test-specs/settings-project-params/l3_project-context-import-markdown-file_ELITEA-2271.md
"""

import logging
from pathlib import Path

import allure
import pytest
from pages.project_context_page import ProjectContextPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

#: PROJECT_CONTEXT_MAX_LEN in projectContext.constants.js.
MAX_CHARS = 2500

#: The supported markdown file the case's step 4 selects. Committed rather than
#: generated per run so the expected content is a literal a reviewer can read,
#: and so the assertion compares the editor against the file's OWN bytes read
#: from disk instead of a duplicated string constant.
IMPORT_FILE = (
    Path(__file__).resolve().parents[4] / "test-data" / "project-context" / "elitea-2271-import.md"
)

#: One extra character, typed to prove the imported content is editable
#: (case step 6).
INLINE_EDIT_CHAR = "!"


class TestProjectContextImportMarkdownFile:
    """ELITEA-2271 — the upload-file icon imports content into the editor."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2271_upload-file-icon-allows-importing-content-into-the-project.md",
        "onetest-ai Test Case link",
    )
    def test_import_markdown_file_into_editor_and_edit_it(self, page, clean_project_context):
        """A .md file picked through the upload icon lands in the editor verbatim
        and remains editable."""
        context_page = ProjectContextPage(page)
        console_errors = collect_console_errors(page)

        file_text = IMPORT_FILE.read_text(encoding="utf-8")
        expected_lines = file_text.split("\n")

        with allure.step("Step 1 — Navigate to Settings -> Project Context and open the editor"):
            context_page.navigate()
            context_page.click_create()
            assert page.url.endswith("/settings/project-context/edit"), (
                f"Create should open the editor route, got {page.url}"
            )
            expect(context_page.editor_lines()).to_have_text([""], timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.save_button).to_be_disabled()

        with allure.step(
            "Steps 2-5 — Click the upload file icon, verify a file picker opens, select a "
            "markdown file and verify its contents are imported"
        ):
            is_single_file = context_page.import_markdown_file(str(IMPORT_FILE), expected_lines)
            assert is_single_file, (
                "The import file chooser accepts multiple files, but the product reads "
                "files?.[0] only"
            )
            expect(context_page.editor_lines()).to_have_text(expected_lines)
            expect(context_page.char_counter).to_have_text(
                f"{MAX_CHARS - len(file_text)} characters left.", timeout=UI_ELEMENT_TIMEOUT
            )
            expect(context_page.save_button).to_be_enabled()

        with allure.step("Step 6 — Verify the imported content is editable"):
            context_page.type_at_end_of_content(INLINE_EDIT_CHAR)
            expect(context_page.editor_lines().last).to_contain_text(INLINE_EDIT_CHAR)
            expect(context_page.char_counter).to_have_text(
                f"{MAX_CHARS - len(file_text) - 1} characters left.", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Axis 2 — No console errors during the import flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
