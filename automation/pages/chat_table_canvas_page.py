"""Chat Table Canvas Page — MUI X DataGrid table editor surface inside the
in-chat edit canvas (ELITEA-2086/2087).

Owns only the DataGrid-editing-specific surface (grid, cells, pagination,
download button). The canvas's shared chrome (title, close button, editing
indicator) lives in :class:`ChatCanvasPage`, composed on the same ``page``
(same pattern as ``McpCanvasPage`` + ``McpFormPage``).

DECLARED IMPROVISATION (AFS ELITEA-2086 § Concrete Handles, flagged for
reviewer sign-off — no 1:1 precedent match to an existing sanctioned
exception): MUI X ``DataGrid`` is a third-party grid widget whose per-cell/
per-row/pagination-footer DOM (``.MuiDataGrid-cell[data-field=...]``,
``.MuiDataGrid-row``, ``.MuiTablePagination-root``) is library-rendered, not
raw app JSX — closely analogous to ``.agents/testing.md`` § Locator policy's
#579 sanctioned-exception categories (ReactFlow subtree / CodeMirror
per-line nodes) but not a literal match to either (DataGrid is neither an
"editor" nor entirely outside app control — each cell DOES render app data).
Treated the SAME way: ONE real testid (``chat-table-canvas-grid``) on the
DataGrid's containing ``Box``, then every ``data-field``/``.MuiDataGrid-row``/
``.MuiTablePagination-root`` raw selector below is scoped as a child of that
testid parent — exactly like ``mcp_form_page.py:121``'s CodeMirror pattern.
The pagination footer specifically has NO JSX call site in app source (it is
DataGrid's own built-in ``TablePagination`` subcomponent, not a prop-threaded
element we render) — un-threadable via a caller-supplied testId the way
``chat-table-download-button`` was, so it is scoped as a raw selector rather
than given its own testid, extending this same declared improvisation rather
than treating it as a separate case.
"""

import logging
import time

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.chat_table_canvas")


class ChatTableCanvasPage(BasePage):
    """Page object for the table-editing DataGrid inside the chat edit canvas."""

    grid = LocatorDescriptor(
        testid="chat-table-canvas-grid",
        description=(
            "Containing Box around the MUI X DataGrid table editor "
            "(MarkdownTableEditor.jsx). Declared-improvisation anchor — "
            "see module docstring."
        ),
    )

    download_button = LocatorDescriptor(
        testid="chat-table-download-button",
        description=(
            "'Download as xlsx' split button (SplitButton.jsx) at the "
            "bottom-right of the grid — new optional testId prop, wired "
            "ONLY at MarkdownTableEditor.jsx's canvas call site (canon "
            "ruling #511: MarkdownTableBlock.jsx's own non-edit download "
            "button is a distinct call site this case's test never "
            "touches, left untagged)."
        ),
    )

    # ------------------------------------------------------------------
    # Scoped raw selectors (MUI DataGrid-internal render nodes — declared
    # improvisation, module docstring). All are children of ``grid``.
    # ------------------------------------------------------------------
    COLUMN_HEADER_WITH_FIELD = ".MuiDataGrid-columnHeader[data-field]"
    ROW = ".MuiDataGrid-row"
    ROW_CHECKBOX = '.MuiDataGrid-cell[data-field="__check__"] input[type="checkbox"]'
    CELL_BY_FIELD = '.MuiDataGrid-cell[data-field="{field}"]'
    # :has-text() is a SUBSTRING match (AFS ELITEA-2087 § Test Data says
    # "the cell whose text is/contains 'Microsoft'" — a generated company
    # name may render as "Microsoft" or a longer variant; confirmed live
    # this implementation's own run needed contains-, not exact-, matching
    # via the initially-tried :text-is()).
    ROW_BY_CELL_TEXT = '.MuiDataGrid-row:has(.MuiDataGrid-cell[data-field="{field}"]:has-text("{text}"))'
    PAGINATION_FOOTER = ".MuiTablePagination-root"
    CELL_EDIT_INPUT = "textarea, input"
    # MUI DataGrid's own scrollable viewport — row-virtualized (only rows
    # near the current scroll position are DOM-rendered). Confirmed live,
    # ELITEA-2086 implementer exploration: at rest, only ~8 of this case's
    # 10 rows were in the DOM (getRowHeight='auto' + word-wrap makes row
    # heights uneven, so the virtualizer's overscan buffer doesn't cover
    # the full 10-row dataset at the default viewport height). NOT in the
    # AFS's own Concrete Handles — a Phase 2 exploration finding.
    VIRTUAL_SCROLLER = ".MuiDataGrid-virtualScroller"

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_grid(self, timeout: int = 15000):
        """Wait until the DataGrid container is visible."""
        self.grid.wait_for(state="visible", timeout=timeout)
        logger.info("Table canvas grid visible")

    def get_column_fields(self) -> list[str]:
        """Return the grid's column ``data-field`` values, excluding the
        built-in checkbox-selection column.

        Column headers carry no reliable text via ``innerText`` extraction
        (confirmed live, AFS step 8 — the label lives one level deeper at
        ``.MuiDataGrid-columnHeaderTitle``); ``data-field`` is the stable,
        implementer-recommended identifier instead. Column headers are
        NOT row-virtualized (fixed header row), so a plain query is safe.
        """
        headers = self.grid.locator(self.COLUMN_HEADER_WITH_FIELD)
        fields = headers.evaluate_all("els => els.map(el => el.getAttribute('data-field'))")
        return [f for f in fields if f and f != "__check__"]

    def _scroll_grid_full_scan(self, timeout: int = 15000) -> dict:
        """Scroll the grid's virtualized scroller from top to bottom,
        returning ``{row_data_id: has_checkbox}`` for every DISTINCT row
        seen along the way.

        MUI DataGrid only DOM-renders rows near the current scroll
        position (see ``VIRTUAL_SCROLLER``'s docstring) — a single
        snapshot undercounts. This walks the full scroll range collecting
        every row's identity once.
        """
        scroller = self.grid.locator(self.VIRTUAL_SCROLLER)
        scroller.wait_for(state="visible", timeout=timeout)
        scroller.evaluate("el => { el.scrollTop = 0; }")
        seen: dict = {}
        deadline = time.monotonic() + timeout / 1000.0
        last_scroll_top = -1
        while time.monotonic() < deadline:
            seen.update(
                self.grid.locator(self.ROW).evaluate_all(
                    "els => Object.fromEntries(els.map(el => "
                    "[el.getAttribute('data-id'), !!el.querySelector('input[type=\"checkbox\"]')]))"
                )
            )
            metrics = scroller.evaluate(
                "el => ({scrollTop: el.scrollTop, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight})"
            )
            if metrics["scrollTop"] + metrics["clientHeight"] >= metrics["scrollHeight"] - 1:
                break
            if metrics["scrollTop"] == last_scroll_top:
                break
            last_scroll_top = metrics["scrollTop"]
            scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight * 0.8; }")
            time.sleep(0.15)
        return seen

    def get_row_count(self) -> int:
        """Return the number of DISTINCT data rows across the whole grid
        (scrolls the virtualized viewport to collect every row — see
        ``VIRTUAL_SCROLLER``)."""
        return len(self._scroll_grid_full_scan())

    def get_checkbox_count(self) -> int:
        """Return the number of DISTINCT rows carrying a row-selection
        checkbox across the whole grid (same full-scroll scan as
        :meth:`get_row_count`)."""
        seen = self._scroll_grid_full_scan()
        return sum(1 for has_checkbox in seen.values() if has_checkbox)

    def _scroll_until_row_visible(self, match_field: str, match_text: str, timeout: int = 10000) -> None:
        """Scroll the grid's virtualized scroller until the row matched by
        *match_field* containing *match_text* is DOM-rendered (see
        ``VIRTUAL_SCROLLER``'s docstring — a virtualized row off-screen
        does not exist in the DOM at all, so Playwright's own
        scroll-into-view auto-waiting cannot find it)."""
        row_selector = self.ROW_BY_CELL_TEXT.format(field=match_field, text=match_text)
        scroller = self.grid.locator(self.VIRTUAL_SCROLLER)
        scroller.wait_for(state="visible", timeout=timeout)
        deadline = time.monotonic() + timeout / 1000.0
        last_scroll_top = -1
        while time.monotonic() < deadline:
            if self.grid.locator(row_selector).count() > 0:
                return
            metrics = scroller.evaluate(
                "el => ({scrollTop: el.scrollTop, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight})"
            )
            if metrics["scrollTop"] + metrics["clientHeight"] >= metrics["scrollHeight"] - 1:
                break
            if metrics["scrollTop"] == last_scroll_top:
                break
            last_scroll_top = metrics["scrollTop"]
            scroller.evaluate("el => { el.scrollTop = el.scrollTop + el.clientHeight * 0.8; }")
            time.sleep(0.15)

    def get_column_values(self, field: str) -> list[str]:
        """Return the text content of every cell in *field*'s column, in row order."""
        cells = self.grid.locator(self.CELL_BY_FIELD.format(field=field))
        return [cells.nth(i).text_content() or "" for i in range(cells.count())]

    def get_pagination_text(self, timeout: int = 10000) -> str:
        """Return the full text of the grid's built-in pagination footer
        (e.g. contains 'Rows per page: 50' and '1–10 of 10')."""
        footer = self.grid.locator(self.PAGINATION_FOOTER)
        footer.wait_for(state="visible", timeout=timeout)
        return footer.text_content() or ""

    def _locate_row_by_content(self, match_field: str, match_text: str, timeout: int = 10000):
        """Scroll until visible (see ``VIRTUAL_SCROLLER``) and return the
        Locator for the row whose *match_field* cell contains *match_text*
        (content match — AI-generated table row order is non-deterministic,
        confirmed live twice, AFS ELITEA-2087 § Test Data; NEVER locate by
        index)."""
        self._scroll_until_row_visible(match_field, match_text, timeout=timeout)
        row = self.grid.locator(self.ROW_BY_CELL_TEXT.format(field=match_field, text=match_text))
        row.wait_for(state="visible", timeout=timeout)
        row.scroll_into_view_if_needed()
        return row

    @action("Enter cell edit mode")
    def enter_cell_edit_mode(self, match_field: str, match_text: str, edit_field: str, timeout: int = 10000) -> None:
        """Double-click *edit_field*'s cell in the row matched by
        *match_field*/*match_text* to enter edit mode.

        A double-click is required (a plain click only selects/focuses the
        cell — confirmed live, standard MUI DataGrid cell-editing UX,
        AFS ELITEA-2087 step 3).
        """
        row = self._locate_row_by_content(match_field, match_text, timeout=timeout)
        cell = row.locator(self.CELL_BY_FIELD.format(field=edit_field))
        cell.dblclick()
        logger.info("Entered edit mode on cell (row matched by %s=%r) %s", match_field, match_text, edit_field)

    def is_cell_editor_active(self, match_field: str, match_text: str, edit_field: str) -> bool:
        """Return True if *edit_field*'s cell (row matched by *match_field*/
        *match_text*) currently has a rendered edit-mode input/textarea."""
        row = self.grid.locator(self.ROW_BY_CELL_TEXT.format(field=match_field, text=match_text))
        cell = row.locator(self.CELL_BY_FIELD.format(field=edit_field))
        return cell.locator(self.CELL_EDIT_INPUT).count() > 0

    def get_cell_editor_value(self, match_field: str, match_text: str, edit_field: str) -> str:
        """Return the current value of *edit_field*'s ACTIVE cell editor
        input (call :meth:`enter_cell_edit_mode` first)."""
        row = self.grid.locator(self.ROW_BY_CELL_TEXT.format(field=match_field, text=match_text))
        cell = row.locator(self.CELL_BY_FIELD.format(field=edit_field))
        return cell.locator(self.CELL_EDIT_INPUT).first.input_value()

    @action("Type new cell value")
    def type_cell_value(
        self, match_field: str, match_text: str, edit_field: str, new_value: str, timeout: int = 10000
    ) -> None:
        """Fill *new_value* into *edit_field*'s already-active cell editor
        (call :meth:`enter_cell_edit_mode` first).

        ``fill()`` works directly on the rendered ``textarea``/``input``
        (2 elements match live inside the editing cell — use ``.first``);
        this DataGrid's own cell editor wires its ``onChange`` directly to
        Playwright-dispatched input events, unlike the general
        MUI-form-field caveat in ``.claude/rules/mui-patterns.md``
        (confirmed live, AFS ELITEA-2087 step 4).
        """
        row = self.grid.locator(self.ROW_BY_CELL_TEXT.format(field=match_field, text=match_text))
        cell = row.locator(self.CELL_BY_FIELD.format(field=edit_field))
        editor_input = cell.locator(self.CELL_EDIT_INPUT).first
        editor_input.wait_for(state="visible", timeout=timeout)
        editor_input.fill(new_value)
        logger.info("Typed %r into cell (row matched by %s=%r) %s", new_value, match_field, match_text, edit_field)

    @action("Confirm cell edit")
    def confirm_cell_edit(self) -> None:
        """Press Enter to commit the active cell edit."""
        self.page.keyboard.press("Enter")

    @action("Edit table cell by row content match")
    def edit_cell_by_row_content(
        self,
        match_field: str,
        match_text: str,
        edit_field: str,
        new_value: str,
        timeout: int = 10000,
    ) -> None:
        """Convenience one-shot composition of :meth:`enter_cell_edit_mode`
        -> :meth:`type_cell_value` -> :meth:`confirm_cell_edit`, for callers
        that don't need per-step assertions between them."""
        self.enter_cell_edit_mode(match_field, match_text, edit_field, timeout=timeout)
        self.type_cell_value(match_field, match_text, edit_field, new_value, timeout=timeout)
        self.confirm_cell_edit()

    def get_cell_text_by_row_content(
        self, match_field: str, match_text: str, read_field: str, timeout: int = 10000
    ) -> str:
        """Return the current text of *read_field*'s cell in the row matched
        by *match_field* containing *match_text*."""
        row = self._locate_row_by_content(match_field, match_text, timeout=timeout)
        return row.locator(self.CELL_BY_FIELD.format(field=read_field)).text_content() or ""
