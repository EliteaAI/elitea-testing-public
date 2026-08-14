"""UI Test for ELITEA-2087 — Chat: Edit Table in Canvas Mode – Modify Cell
Value and Save Changes.

Verifies that editing a cell value in the canvas table editor and closing
the canvas synchronizes the changed value back to the conversation's
rendered table, leaving all other data untouched.

Spec: test-specs/chat-interface/l3_edit-table-canvas-modify-cell-and-save_ELITEA-2087.md

This case's own precondition IS ELITEA-2086's outcome (AFS § Preconditions:
"the canvas table editor is open — this case's precondition is literally
ELITEA-2086's outcome"). Per the AFS's own Automation Hints, this test
reaches that state itself (send message -> open canvas) rather than
depending on ELITEA-2086's test having run first (test isolation,
``.claude/rules/ui-tests.md`` § Test Isolation) — accepting the duplicated
setup rather than composing across test boundaries.

New page-object surface: reuses ``ChatCanvasPage``/``ChatTableCanvasPage``
(introduced for ELITEA-2086, same PR/branch) — this case is the first to
actually CLICK the shared canvas close button (ELITEA-2086 only observes
it) and adds cell-editing methods (``enter_cell_edit_mode``/
``type_cell_value``/``confirm_cell_edit``) to ``ChatTableCanvasPage``.
Testid gap filled this implementation (``add-data-testid``, pushed to
``automation/testids``): none new — all shared canvas-chrome testids
(``chat-canvas-close-button``, ``chat-canvas-editing-indicator``,
``chat-canvas-title``) and ``chat-table-canvas-grid`` were added for
ELITEA-2086 in the same PR.

Known defect handling: none — this case's happy path is fully clean per
the AFS (reproduced live twice by the analyst, no product defect found).
"""

import logging

import allure
import pytest
from pages.chat_canvas_page import ChatCanvasPage
from pages.chat_page import ChatPage
from pages.chat_table_canvas_page import ChatTableCanvasPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.edit_table_canvas_modify_cell")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000

MESSAGE_TEXT = "generate a table of top 10 IT companies"
COMPANY_FIELD = "Company"
ORIGINAL_VALUE = "Microsoft"
EDITED_VALUE = "Microsoft_edited"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise (see
    ``test_edit_generated_table_canvas_open_and_verify_display.py``)."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestEditTableCanvasModifyCellAndSave:
    """ELITEA-2087: Chat – Edit Table in Canvas Mode – Modify Cell Value and
    Save Changes (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2087_chat-edit-table-in-canvas-mode-modify-cell-value-and-save-changes.md",
        "onetest-ai Test Case link",
    )
    def test_edit_table_canvas_modify_cell_and_save(self, page, conversation_id):
        """Generate a table, open its canvas, edit the Microsoft cell
        (located by content match, never by index), close the canvas, and
        verify the change synced back to the conversation view while every
        other row stayed unchanged.

        Steps (AFS
        test-specs/chat-interface/l3_edit-table-canvas-modify-cell-and-save_ELITEA-2087.md):
        Setup (this case's own precondition = ELITEA-2086's outcome,
        reached independently): send message, open the table edit canvas.
        1. Verify the canvas editor is open.
        2. Verify the "Table editing..." indicator.
        3. Click the "Microsoft" cell (content match, not index).
        4. Change it to "Microsoft_edited".
        5. Confirm with Enter.
        6. Verify the update persisted in the grid.
        7. Close the canvas.
        8. Locate the table in the conversation.
        9. Verify "Microsoft_edited" is reflected.
        10. Verify all other data is unchanged.
        """
        chat = ChatPage(page)
        canvas = ChatCanvasPage(page)
        table_canvas = ChatTableCanvasPage(page)

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        with allure.step(
            "Setup — send the message and open the table edit canvas "
            "(this case's own precondition = ELITEA-2086's outcome, "
            "reached independently per AFS Automation Hints)"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            initial_count = chat.get_message_count()
            chat.send_message(MESSAGE_TEXT)
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(stable_duration_ms=2000, timeout=30000)

            pre_edit_rows = chat.get_rendered_table_data()
            assert len(pre_edit_rows) == 10, f"Expected 10 pre-edit rows, got {len(pre_edit_rows)}"
            pre_edit_companies = [row.get(COMPANY_FIELD, "") for row in pre_edit_rows]
            assert any(ORIGINAL_VALUE in value for value in pre_edit_companies), (
                f"Expected {ORIGINAL_VALUE!r} to appear in the generated table, "
                f"got: {pre_edit_companies!r}"
            )
            # The AI-generated company name is matched by SUBSTRING everywhere
            # else in this test (cell/row lookup below uses :has-text()) — it
            # may render as "Microsoft" or a longer variant like "Microsoft
            # Corporation". Capture the ACTUAL matched string here so Step 10's
            # untouched-rows comparison subtracts the real edited value, not
            # the literal ORIGINAL_VALUE constant. Root cause of an
            # intermittent gate failure (2026-08-04): when the AI generated
            # "Microsoft Corporation", `set(pre_edit_companies) - {"Microsoft"}`
            # (exact-match subtraction) silently failed to remove it, so
            # expected_unchanged kept the very row that had been edited away —
            # a test-code bug, not a product defect or a DOM-read gap (both
            # pre/post reads asserted `len(...) == 10` clean; the mismatch was
            # purely in the set arithmetic, not in what was rendered).
            edited_company_name = next(v for v in pre_edit_companies if ORIGINAL_VALUE in v)

            chat.click_table_edit_icon(timeout=UI_ELEMENT_TIMEOUT)
            canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
            logger.info("Table edit canvas opened; pre-edit companies: %s", pre_edit_companies)

        with allure.step("Step 1 — Verify the table canvas editor is open"):
            table_canvas.wait_for_grid(timeout=UI_ELEMENT_TIMEOUT)
            assert table_canvas.get_row_count() == 10, (
                f"Expected 10 rows in the editable grid, got {table_canvas.get_row_count()}"
            )

        with allure.step('Step 2 — Verify the "Table editing..." indicator is visible'):
            expect(canvas.editing_indicator).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.editing_indicator).to_contain_text(
                "Table editing...", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            f'Step 3 — Double-click the "{ORIGINAL_VALUE}" cell in the '
            f"Company column (content match, never by row index — AI-"
            f"generated row order is non-deterministic)"
        ):
            table_canvas.enter_cell_edit_mode(COMPANY_FIELD, ORIGINAL_VALUE, COMPANY_FIELD, timeout=UI_ELEMENT_TIMEOUT)
            assert table_canvas.is_cell_editor_active(COMPANY_FIELD, ORIGINAL_VALUE, COMPANY_FIELD), (
                "Cell should be in edit mode (nested input/textarea rendered) after double-click"
            )

        with allure.step(f'Step 4 — Change "{ORIGINAL_VALUE}" to "{EDITED_VALUE}"'):
            table_canvas.type_cell_value(
                COMPANY_FIELD, ORIGINAL_VALUE, COMPANY_FIELD, EDITED_VALUE, timeout=UI_ELEMENT_TIMEOUT
            )
            assert table_canvas.get_cell_editor_value(COMPANY_FIELD, ORIGINAL_VALUE, COMPANY_FIELD) == EDITED_VALUE, (
                "Cell editor's input value should reflect the typed text"
            )

        with allure.step("Step 5 — Press Enter to confirm the change"):
            table_canvas.confirm_cell_edit()
            edited_cell_text = table_canvas.get_cell_text_by_row_content(
                COMPANY_FIELD, EDITED_VALUE, COMPANY_FIELD, timeout=UI_ELEMENT_TIMEOUT
            )
            assert edited_cell_text == EDITED_VALUE, (
                f"Cell should display {EDITED_VALUE!r} after confirming, got {edited_cell_text!r}"
            )

        with allure.step(
            "Step 6 — Verify the update persisted in the grid automatically "
            "(no explicit per-cell Save action required)"
        ):
            persisted_text = table_canvas.get_cell_text_by_row_content(
                COMPANY_FIELD, EDITED_VALUE, COMPANY_FIELD, timeout=UI_ELEMENT_TIMEOUT
            )
            assert persisted_text == EDITED_VALUE, (
                f"Edited value should remain {EDITED_VALUE!r} without further action, got {persisted_text!r}"
            )

        with allure.step("Step 7 — Click the X button to close the canvas"):
            canvas.close(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.close_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            logger.info("Canvas closed after confirming edit %r -> %r", ORIGINAL_VALUE, EDITED_VALUE)

        with allure.step("Step 8 — Locate the table back in the conversation"):
            # Confirmed live (Phase 2 exploration finding, not in the AFS's
            # own Concrete Handles): once a table has been through one
            # canvas edit-and-close cycle, its conversation-pane render
            # switches from a plain Markdown "text_message" item (rendered
            # via Token.jsx -> MarkdownTableBlock, whose OWN toolbar/pencil
            # this case's chat.table_edit_button targets) to a
            # "canvas_message" item rendered via Canvas.jsx's CanvasContent
            # (its OWN separate, currently-untested pencil, showToolbar=
            # false on the nested Markdown so MarkdownTableBlock's toolbar
            # is hidden). The underlying <table> markup is still rendered
            # by the SAME MarkdownTableBlock component either way (Canvas.
            # jsx nests <Markdown>, which parses the identical table
            # tokens) — so table PRESENCE, per the AFS's own Coverage Map
            # disposition for this step ("MarkdownTableBlock table element
            # visible"), is the correct assertion; the pencil button is not.
            post_edit_rows = chat.get_rendered_table_data()
            assert len(post_edit_rows) == 10, f"Expected 10 rows in the conversation table, got {len(post_edit_rows)}"

        with allure.step(
            f'Step 9 — Verify "{EDITED_VALUE}" is reflected in the '
            f"conversation table's Company column (the row that WAS the "
            f"{ORIGINAL_VALUE} row, not literally 'first row' — case-text "
            f"drift, AFS Axis 2)"
        ):
            post_edit_companies = [row.get(COMPANY_FIELD, "") for row in post_edit_rows]
            assert EDITED_VALUE in post_edit_companies, (
                f"Expected {EDITED_VALUE!r} to appear in the conversation table's "
                f"Company column, got: {post_edit_companies!r}"
            )

        with allure.step(
            "Step 10 — Verify every other row's Company value is unchanged"
        ):
            # Subtract the ACTUAL matched pre-edit string (edited_company_name),
            # not the literal ORIGINAL_VALUE constant — the AI may have named
            # the row "Microsoft Corporation" (or another variant containing
            # ORIGINAL_VALUE), and an exact-match subtraction against the bare
            # constant would leave that row stranded in expected_unchanged.
            expected_unchanged = set(pre_edit_companies) - {edited_company_name}
            actual_unchanged = set(post_edit_companies) - {EDITED_VALUE}
            assert actual_unchanged == expected_unchanged, (
                f"Non-edited rows should be untouched.\n"
                f"Expected: {expected_unchanged!r}\nGot: {actual_unchanged!r}"
            )

        with allure.step(
            "Side-channel — verify no unexpected console errors occurred "
            "across the whole flow (known secrets-403 noise is pre-filtered)"
        ):
            assert not console_messages, (
                f"Unexpected console error(s) during the flow: {[m.text for m in console_messages]!r}"
            )
