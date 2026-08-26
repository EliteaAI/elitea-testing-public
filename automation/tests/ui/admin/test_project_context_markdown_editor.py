"""UI test — the Project Context editor accepts markdown and round-trips it
through preview and code view.

Walks the real user path: empty state -> Create -> paste a markdown body with a
heading, bullets and a plain paragraph -> assert the editor displays the raw
source verbatim with line numbers and is editable inline -> preview (eye) ->
assert react-markdown rendered a real <h2> and two <li> and consumed the syntax
characters -> code view (</>) -> assert the raw source is back, unchanged.

Case-text divergence (declared, reverse-masking guard): the case calls the
control the "Project Background editor". No element, section or label of that
name exists in the product -- it is the Project Context editor at
/settings/project-context/edit. Already filed as clarification #1792 (module
wide, ELITEA-2266 analysis); not re-filed. Every observable the case names is
asserted against the live product.

Technique note (no substitution): the markdown body is PASTED, not typed.
CodeMirror's markdown() extension auto-continues list items on Enter, so
per-keystroke typing of a multi-line body is rewritten by the editor
("- - Second bullet", confirmed live 2026-08-26). The paste is a single
transaction that lands the text verbatim and still passes through CodeMirror's
own transaction filter, exactly like typed input. The only page.evaluate is the
clipboard write feeding that gesture (pre-existing reviewed pattern, ELITEA-2272)
-- it loads the browser's clipboard, never the application's state.

Nothing is seeded and nothing is saved: every asserted value is produced by the
product from input the test entered through the UI as a user would.

Test case: ELITEA-2268
AFS: test-specs/settings-project-params/l3_project-context-markdown-editor-and-preview_ELITEA-2268.md
"""

import logging

import allure
import pytest
from pages.project_context_page import ProjectContextPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

#: Headings, bullet points and plain text (case step 3). The blank lines are
#: load-bearing: without them CommonMark treats the trailing sentence as a lazy
#: continuation of the second bullet and renders ONE <li> containing both
#: (confirmed live), which would make the plain-text assertion ambiguous.
MARKDOWN_BODY = "## Project Overview\n\n- First bullet\n- Second bullet\n\nPlain text line."
MARKDOWN_LINES = MARKDOWN_BODY.split("\n")

EXPECTED_HEADING = "Project Overview"
EXPECTED_BULLETS = ["First bullet", "Second bullet"]
EXPECTED_PARAGRAPH = "Plain text line."

#: One extra character typed in place (case step 5 -- "editable inline").
INLINE_EDIT_CHAR = "!"


class TestProjectContextMarkdownEditor:
    """ELITEA-2268 — Project Context editor accepts and displays markdown content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2268_project-background-editor-accepts-and-displays-markdown-cont.md",
        "onetest-ai Test Case link",
    )
    def test_project_context_markdown_editor_and_preview(self, page, clean_project_context):
        """The editor accepts markdown verbatim, numbers its lines and stays
        editable inline; preview renders it as formatted markdown; code view
        brings the raw source back unchanged."""
        context_page = ProjectContextPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 — Navigate to Settings -> Project Context and open the editor via Create"):
            context_page.navigate()
            context_page.click_create()
            assert page.url.endswith("/settings/project-context/edit"), (
                f"Expected Create to open the editor route, landed on {page.url}"
            )
            expect(context_page.editor_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Steps 2-3 — Click inside the editor and enter markdown with a heading, bullets "
            "and plain text: the field accepts it and displays it VERBATIM, syntax characters included"
        ):
            context_page.paste_markdown(MARKDOWN_BODY)
            expect(context_page.editor_lines()).to_have_text(MARKDOWN_LINES)

        with allure.step("Step 4 — The editor shows line numbers alongside the content (1..6)"):
            expect(context_page.line_number_gutter()).to_be_visible()
            expect(context_page.line_numbers()).to_have_text(
                [str(n) for n in range(1, len(MARKDOWN_LINES) + 1)]
            )

        with allure.step(
            "Step 5 — The content is editable inline, not read-only: contenteditable is true "
            "AND a real keystroke lands in the document while the counter drops by one"
        ):
            expect(context_page.editor_content).to_have_attribute("contenteditable", "true")
            counter_before = context_page.get_char_counter_text()
            context_page.type_at_end_of_content(INLINE_EDIT_CHAR)
            expect(context_page.editor_lines().last).to_have_text(EXPECTED_PARAGRAPH + INLINE_EDIT_CHAR)
            expect(context_page.char_counter).not_to_have_text(counter_before)

        with allure.step(
            "Step 6 — Click the preview (eye) icon: it becomes the selected mode and the "
            "CodeMirror pane is replaced (the two panes are mutually exclusive)"
        ):
            context_page.click_preview_mode()
            expect(context_page.mode_edit_button).to_have_attribute("aria-pressed", "false")

        with allure.step(
            "Step 7 — The content renders as FORMATTED markdown in preview: a real <h2>, two "
            "<li>, the paragraph present, and no raw '##' / '- ' syntax left over"
        ):
            expect(context_page.preview_headings()).to_have_count(1)
            expect(context_page.preview_headings()).to_have_text([EXPECTED_HEADING])
            expect(context_page.preview_list_items()).to_have_text(EXPECTED_BULLETS)
            expect(context_page.preview_pane).to_contain_text(EXPECTED_PARAGRAPH)

            preview_text = context_page.preview_pane.text_content() or ""
            assert "##" not in preview_text, (
                f"Preview still shows raw markdown heading syntax: {preview_text!r}"
            )
            assert "- First bullet" not in preview_text, (
                f"Preview still shows raw markdown bullet syntax: {preview_text!r}"
            )

        with allure.step("Step 8 — Click the code view ('</>') icon: it becomes the selected mode"):
            context_page.click_code_view_mode()
            expect(context_page.mode_preview_button).to_have_attribute("aria-pressed", "false")

        with allure.step(
            "Step 9 — The raw markdown source is shown in the editor again, byte-identical "
            "(including the inline edit from step 5) — the case's expected final state"
        ):
            expect(context_page.editor_content).to_be_visible()
            expect(context_page.editor_lines()).to_have_text(
                MARKDOWN_LINES[:-1] + [EXPECTED_PARAGRAPH + INLINE_EDIT_CHAR]
            )

        with allure.step("Side-channel check — no console errors at any step"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
