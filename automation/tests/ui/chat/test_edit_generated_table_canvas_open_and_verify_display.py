"""UI Test for ELITEA-2086 — Chat: Edit Generated Table in Canvas Mode –
Open Editor and Verify Table Display.

Verifies that clicking the edit icon on an AI-generated Markdown table
opens the in-chat edit canvas, displaying the table as an editable MUI X
DataGrid with all rows/columns, sortable column headers, row checkboxes,
pagination, and a "Download as xlsx" button.

Spec: test-specs/chat-interface/l3_edit-generated-table-canvas-open-and-verify-display_ELITEA-2086.md

New page-object surface (AFS § Automation Hints / Concrete Handles): the
whole in-chat table/diagram/code edit canvas component tree
(``MarkdownTableBlock.jsx``, ``Canvas.jsx``, ``CanvasEditHeader.jsx``,
``MarkdownTableEditor.jsx``, ``EditingPlaceholder.jsx``) had ZERO
data-testids anywhere — confirmed via the AFS's own ``git grep`` against
both ``origin/main`` and ``origin/automation/testids``. Testid gaps filled
this implementation (``add-data-testid``, pushed to ``automation/testids``):
- ``chat-table-edit-button`` (this case's own pencil icon,
  ``MarkdownTableBlock.jsx``).
- ``chat-canvas-title`` / ``chat-canvas-close-button`` /
  ``chat-canvas-editing-indicator`` — the SHARED canvas chrome
  (``CanvasEditHeader.jsx``/``EditingPlaceholder.jsx``) also consumed by
  the sibling cases ELITEA-2087 (same case family, edits the table this
  case opens) and ELITEA-2088 (mermaid diagram); added once here, per the
  AFS's own "add these testids ONCE, coordinate with whichever lands
  first" guidance. This case's own executed path only OBSERVES the close
  button and title (never clicks close — ELITEA-2087 does that).
- ``chat-table-canvas-grid`` — DECLARED IMPROVISATION (flagged for
  reviewer sign-off, no 1:1 precedent match to an existing sanctioned
  exception; see ``pages/chat_table_canvas_page.py`` module docstring):
  MUI X DataGrid's containing Box, with per-cell/row/pagination-footer
  DOM scoped as raw selectors underneath it (library-rendered, not app
  JSX for those specific sub-nodes).
- ``chat-table-download-button`` — new optional ``testId`` prop on the
  shared ``SplitButton.jsx``, wired ONLY at ``MarkdownTableEditor.jsx``'s
  canvas call site (canon ruling #511: ``MarkdownTableBlock.jsx``'s own
  non-edit download button is a distinct, untouched call site).

Known defect handling: none — this case's happy path is fully clean per
the AFS (reproduced live twice by the analyst, no product defect found).
"""

import logging
import re

import allure
import pytest
from pages.chat_canvas_page import ChatCanvasPage
from pages.chat_page import ChatPage
from pages.chat_table_canvas_page import ChatTableCanvasPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.edit_generated_table_canvas_open")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p3, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000  # table generation took 7-8s live, generous headroom

MESSAGE_TEXT = "generate a table of top 10 IT companies"

# Confirmed live, both analyst runs (AFS § Test Steps / Test Data): a
# stable core independent of the AI's exact column-name wording/count.
EXPECTED_CORE_COMPANIES = ("Apple", "Microsoft", "Alphabet", "Amazon")
HQ_HEADER_KEYWORDS = ("hq", "headquarter", "location")
# Broad on purpose: the AFS's own two analyst runs alone produced "Primary
# Focus"/"Primary Business", and this implementation's live run produced
# "Primary Services" — the 4th column's exact business-context wording is
# genuinely AI-generated and not fixed (AFS § Test Steps step 3).
FOCUS_HEADER_KEYWORDS = (
    "focus", "business", "industry", "sector", "service", "product", "primary", "area", "notable",
)


def _find_header_containing(headers: list[str], keywords: tuple[str, ...]) -> str | None:
    """Return the first header whose lowercased text contains any of *keywords*."""
    for header in headers:
        lowered = header.lower()
        if any(keyword in lowered for keyword in keywords):
            return header
    return None


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_agent_via_chat_canvas.py`` / ``test_create_mcp_from_conversation.py``
    — an unrelated toolkit/secrets panel probe that fires on every page
    load in this local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestEditGeneratedTableCanvasOpenAndVerifyDisplay:
    """ELITEA-2086: Chat – Edit Generated Table in Canvas Mode – Open Editor
    and Verify Table Display (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2086_chat-edit-generated-table-in-canvas-mode-open-editor-and-verify-table-display.md",
        "onetest-ai Test Case link",
    )
    def test_edit_generated_table_canvas_open_and_verify_display(self, page, conversation_id):
        """Generate a table via chat, open its edit canvas, and verify the
        full editable-grid display (columns, rows, checkboxes, pagination,
        download button).

        Steps (AFS
        test-specs/chat-interface/l3_edit-generated-table-canvas-open-and-verify-display_ELITEA-2086.md):
        1. Navigate to Chats and open a conversation.
        2. Send "generate a table of top 10 IT companies".
        3. Verify the rendered table's columns.
        4. Verify the rendered table's company data.
        5. Locate the pencil/edit icon.
        6. Click it; verify the canvas opens with heading "Edit table" and
           the conversation pane shows the editing indicator.
        7. Verify the editable DataGrid shows all columns/rows.
        8. Verify sortable column headers.
        9. Verify row checkboxes.
        10. Verify pagination "1-10 of 10" / "Rows per page: 50".
        11. Verify the "Download as xlsx" button.
        """
        chat = ChatPage(page)
        canvas = ChatCanvasPage(page)
        table_canvas = ChatTableCanvasPage(page)

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        with allure.step("Step 1 — Navigate to Chats and open a conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(f'Step 2 — Send "{MESSAGE_TEXT}"; verify a table is generated'):
            initial_count = chat.get_message_count()
            chat.send_message(MESSAGE_TEXT)
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(stable_duration_ms=2000, timeout=30000)

        with allure.step(
            "Step 3 — Verify the table shows a stable core column set "
            "(Rank, Company, a headquarters-type column, a business/focus "
            "column) — column SET is AI-generated, not fixed"
        ):
            rendered_rows = chat.get_rendered_table_data()
            assert rendered_rows, "Expected the rendered table to contain at least one row"
            headers = list(rendered_rows[0].keys())
            assert "Rank" in headers, f"Expected a 'Rank' column, got headers: {headers!r}"
            assert "Company" in headers, f"Expected a 'Company' column, got headers: {headers!r}"
            hq_header = _find_header_containing(headers, HQ_HEADER_KEYWORDS)
            assert hq_header, f"Expected a headquarters-type column among {headers!r}"
            focus_header = _find_header_containing(headers, FOCUS_HEADER_KEYWORDS)
            assert focus_header, f"Expected a business/focus-type column among {headers!r}"
            logger.info("Rendered table columns: %s", headers)

        with allure.step(
            "Step 4 — Verify the table shows 10 rows of company data "
            "including the confirmed-stable core companies (set membership, "
            "not fixed row order/index)"
        ):
            assert len(rendered_rows) == 10, f"Expected 10 data rows, got {len(rendered_rows)}"
            company_values = [row.get("Company", "") for row in rendered_rows]
            for company in EXPECTED_CORE_COMPANIES:
                assert any(company in value for value in company_values), (
                    f"Expected {company!r} to appear in the Company column, got: {company_values!r}"
                )

        with allure.step("Step 5 — Locate the pencil/edit icon in the table toolbar"):
            expect(chat.table_edit_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 6 — Click the pencil/edit icon; verify the canvas opens '
            'with heading "Edit table" and the conversation pane shows the '
            'editing indicator'
        ):
            chat.click_table_edit_icon(timeout=UI_ELEMENT_TIMEOUT)
            canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.title).to_have_text("Edit table", timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.editing_indicator).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.editing_indicator).to_contain_text(
                "Table editing...", timeout=UI_ELEMENT_TIMEOUT
            )
            logger.info("Table edit canvas opened with heading %r", canvas.title.text_content())

        with allure.step(
            "Step 7 — Verify the canvas displays the table as an editable "
            "DataGrid with all columns and rows from step 3/4"
        ):
            table_canvas.wait_for_grid(timeout=UI_ELEMENT_TIMEOUT)
            assert table_canvas.get_row_count() == 10, (
                f"Expected 10 rows in the editable grid, got {table_canvas.get_row_count()}"
            )
            grid_fields = set(table_canvas.get_column_fields())
            assert grid_fields == set(headers), (
                f"Grid column set should match the rendered table's columns. "
                f"Expected {set(headers)!r}, got {grid_fields!r}"
            )

        with allure.step(
            "Step 8 — Verify sortable column headers are present for every "
            "column (via stable data-field attribute, per AFS header-text "
            "extraction caveat)"
        ):
            assert set(table_canvas.get_column_fields()) == set(headers), (
                "Every rendered-table column should have a corresponding "
                "sortable DataGrid column header"
            )

        with allure.step("Step 9 — Verify row checkboxes appear on the left, one per row"):
            assert table_canvas.get_checkbox_count() == 10, (
                f"Expected 10 row checkboxes, got {table_canvas.get_checkbox_count()}"
            )

        with allure.step(
            'Step 10 — Verify pagination shows "1-10 of 10" and "Rows per page: 50"'
        ):
            # text_content() concatenates the footer's separate DOM nodes
            # (label / MUI Select display / range text) with NO inserted
            # whitespace between them (confirmed live: "Rows per
            # page:501–10 of 10") — match with a flexible regex rather
            # than the literal spaced text a human reader sees.
            pagination_text = table_canvas.get_pagination_text(timeout=UI_ELEMENT_TIMEOUT)
            assert re.search(r"Rows per page:\s*50", pagination_text), (
                f"Expected 'Rows per page: 50' in pagination text, got: {pagination_text!r}"
            )
            assert re.search(r"1\s*[–-]\s*10 of 10", pagination_text), (
                f"Expected '1-10 of 10' in pagination text, got: {pagination_text!r}"
            )

        with allure.step('Step 11 — Verify a "Download as xlsx" button appears'):
            expect(table_canvas.download_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(table_canvas.download_button).to_contain_text(
                "Download as xlsx", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Side-channel — verify no unexpected console errors occurred "
            "across the whole flow (known secrets-403 noise is pre-filtered)"
        ):
            assert not console_messages, (
                f"Unexpected console error(s) during the flow: {[m.text for m in console_messages]!r}"
            )
