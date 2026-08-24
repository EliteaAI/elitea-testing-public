"""Toolkit / MCP Run History page object.

URL: ``/toolkits/all/{id}/history`` — reached from the toolkit/MCP detail
action bar's **Run History** button (``McpFormPage.open_run_history()``).
MCPs deliberately reuse the *toolkit* route with an ``?isMCP=true`` query
flag rather than owning a ``/mcps/...`` one
(``useToolkitDetailNavigation.hooks.js``'s own doc comment says so), so one
page object serves both surfaces.

Deliberately a NEW page object rather than more methods on
:class:`McpFormPage` (added ELITEA-1940): this is a distinct ROUTE with its
own container (``ToolkitRunHistory.jsx`` -> the shared
``RunHistoryContainer``), not a region of the detail form. It mirrors the
run-history method set ``PipelineDetailPage`` (ELITEA-2011/2070) and
``AgentDetailPage`` (ELITEA-1876/1877) already expose for the SAME shared
component — same literal testids, different entry point, different route,
different ``source``/``entityId`` pairing, and a different column set
(Date + Duration here; no Version column — assert per surface).

A shared mixin across the three surfaces would remove the triplication, but
that is a suite-health refactor touching two merged page objects, not this
case's work — flagged in the ELITEA-1940 Run Report instead.
"""

import logging

from playwright.sync_api import Page, expect
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.toolkit_run_history")

UI_ELEMENT_TIMEOUT = 10_000


class ToolkitRunHistoryPage(BasePage):
    """Run History page for a toolkit / MCP entity.

    URL: ``/toolkits/all/{id}/history?isMCP=true`` for an MCP.
    """

    # `run-history-list-item` / `data-selected` — testid + state attribute,
    # the shape `.agents/testing.md` § Locator policy requires (never a
    # state-dependent testid). `RunHistoryListItem.jsx:151` sets
    # `data-selected={selectedItem === item.id}`. The SAME literal testid is
    # on every row, so rows are distinguished positionally — the list's
    # default sort is Date descending, i.e. index 0 = most recent run.
    RUN_HISTORY_LIST_ITEM_SELECTOR = '[data-testid="run-history-list-item"]'
    RUN_HISTORY_LIST_ITEM_SELECTED_SELECTOR = (
        '[data-testid="run-history-list-item"][data-selected="true"]'
    )

    # Detail pane: the selected run's conversation, rendered through the same
    # shared `ChatMessageList` component every chat surface in the app uses
    # (`RunHistoryChat.jsx`). One `chat-message-item` per message — for a tool
    # run that is exactly two: the input ("Calling '<tool>' with parameters:"
    # + the parameter JSON) and the output.
    CHAT_MESSAGE_LIST_SELECTOR = '[data-testid="chat-message-list"]'
    CHAT_MESSAGE_ITEM_SELECTOR = '[data-testid="chat-message-item"]'

    detail_message_list = LocatorDescriptor(
        testid="chat-message-list",
        description="Detail pane's message list for the currently-selected "
        "run (RunHistoryChat.jsx -> the shared ChatMessageList component). "
        "Assert new content through this container with an auto-retrying "
        "expect(...).to_contain_text(...): switching selection re-renders it "
        "asynchronously, so a one-shot text read can catch the PREVIOUS "
        "run's content.",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def wait_for_loaded(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait until the run-history list has rendered at least one row.

        The list is fetched on mount
        (``RunHistoryApi.useLazyGetRunHistoryListQuery()``, keyed on
        ``{source, projectId, entityId, page}``) — a real network round
        trip — so arriving at the route is not the same as the rows being
        there. Poll for the first row rather than the URL alone.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).first.wait_for(
            state="visible", timeout=timeout
        )

    def get_items(self):
        """Return the Locator matching every rendered run-history row.

        Returned as a Locator (not a pre-computed int) so callers get
        Playwright's auto-retry semantics on ``expect(...).to_have_count()``
        — same style as ``ToolkitTestSettingsPage.get_result_items()``.
        """
        return self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR)

    def get_item_texts(self) -> list[str]:
        """Return the full rendered text of every run-history row.

        Each row renders its Date and Duration columns as plain child text
        nodes — no per-cell testid exists, the row's own text already
        exposes both.

        Returns:
            List of each row's text content, in current display order
            (index 0 = most recent).
        """
        return self.get_items().all_text_contents()

    def is_item_selected(self, index: int, timeout: int = UI_ELEMENT_TIMEOUT) -> bool:
        """Return whether the row at *index* carries ``data-selected="true"``.

        Args:
            index: Zero-based row index (0 = most recent).
            timeout: Maximum wait time in milliseconds for the row to render.

        Returns:
            True if that row is the one currently marked selected.
        """
        row = self.get_items().nth(index)
        row.wait_for(state="visible", timeout=timeout)
        return row.get_attribute("data-selected") == "true"

    @action("Select a Run History row")
    def select_item(self, index: int, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the run-history row at *index* and wait for it to be selected.

        ``RunHistoryContainer.jsx`` auto-selects ``historyRows[0]`` on mount,
        so a caller proving "selecting an entry shows its details" must
        click a row OTHER than 0 and assert the delta.

        Completion is confirmed on the row's own ``data-selected`` state
        attribute flipping to ``"true"`` (Playwright's auto-retrying
        ``expect``), not on a network response: the conversation-detail
        fetch can resolve a tick ahead of React committing the selection,
        and the state attribute is the observable the case asserts anyway.

        Args:
            index: Zero-based row index (0 = most recent).
            timeout: Maximum wait time in milliseconds.
        """
        row = self.get_items().nth(index)
        row.wait_for(state="visible", timeout=timeout)
        row.click()
        expect(row).to_have_attribute("data-selected", "true", timeout=timeout)
        logger.info("Selected run-history row %d", index)

    # ------------------------------------------------------------------
    # Detail pane (selected run's conversation)
    # ------------------------------------------------------------------

    def get_detail_message_items(self):
        """Return the Locator matching every message in the detail pane."""
        return self.page.locator(self.CHAT_MESSAGE_ITEM_SELECTOR)

    def get_detail_text(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the concatenated text of the selected run's detail pane.

        Waits (bounded by *timeout*) for the first message item to render
        before reading — :meth:`select_item` returns as soon as the row's
        selection state flips, which can land a tick before the detail
        pane has re-rendered, producing a transient empty read.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Joined text of all ``chat-message-item`` elements, or ``""`` if
            none render within *timeout*.
        """
        items = self.get_detail_message_items()
        try:
            items.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        return "\n".join(items.all_text_contents())
