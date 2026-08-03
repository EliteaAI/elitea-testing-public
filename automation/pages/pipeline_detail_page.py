"""Pipeline detail page object for pipeline detail/edit operations.

Extends PipelineFormPage with additional functionality:
- Tabs (Configuration, History)
- Actions menu (delete, export, fork)
- YAML/Flow view toggle
- ReactFlow canvas node management
- Embedded chat

URL: /pipelines/all/{id}
"""

import json
import logging
import re
import time
from contextlib import contextmanager

from components.mui import Dialog, Popper
from playwright.sync_api import Locator, Page

from .locator_descriptor import LocatorDescriptor
from .pipeline_form_page import PipelineFormPage

logger = logging.getLogger("elitea.pages.pipeline_detail")


class PipelineDetailPage(PipelineFormPage):
    """Pipeline detail/edit page.

    Inherits form operations from PipelineFormPage.
    Adds: tabs, actions menu, YAML/Flow toggle, ReactFlow canvas, embedded chat.

    URL: /pipelines/all/{id}
    """

    # LocatorDescriptors - testid + fallback pattern
    configuration_tab = LocatorDescriptor(
        testid="pipeline-config-tab",
        fallback=lambda page: page.get_by_role("button", name="General"),
        description="Configuration panel General section header (always visible, replaces old tab)"
    )

    history_tab = LocatorDescriptor(
        testid="pipeline-history-tab",
        fallback=lambda page: page.locator('[aria-label="view run history"]'),
        description="View run history icon button (replaces old History tab)"
    )

    copy_id_button = LocatorDescriptor(
        testid="copy-id",
        fallback=lambda page: page.get_by_role("button", name="Copy ID"),
        description="Copy pipeline ID button"
    )

    flow_view_button = LocatorDescriptor(
        testid="pipeline-flow-view",
        fallback=lambda page: page.locator('button[value="flow"]'),
        description="Switch to Flow view button"
    )

    yaml_view_button = LocatorDescriptor(
        testid="pipeline-yaml-view",
        fallback=lambda page: page.locator('button[value="yaml"]'),
        description="Switch to YAML view button"
    )

    canvas_wrapper = LocatorDescriptor(
        testid="rf__wrapper",
        fallback=lambda page: page.locator('[data-testid="rf__wrapper"]'),
        description="ReactFlow canvas wrapper"
    )

    yaml_editor = LocatorDescriptor(
        testid="pipeline-yaml-editor",
        fallback=lambda page: page.locator("div.cm-editor div.cm-content"),
        description="YAML CodeMirror editor content"
    )

    yaml_lines = LocatorDescriptor(
        testid="pipeline-yaml-lines",
        fallback=lambda page: page.locator("div.cm-editor div.cm-content .cm-line"),
        description="YAML CodeMirror editor lines (for preserving line breaks). "
        "DEAD FIELD as of ELITEA-2079: the 'pipeline-yaml-lines' testid was never "
        "added to EliteaUI (confirmed absent on both main and automation/testids, "
        "2026-08-03) — count() always resolves to 0 and the fallback= is never "
        "invoked (LocatorDescriptor never calls fallback when a testid is set), so "
        "get_yaml_content() below no longer reads through this field. Kept "
        "un-deleted (shared-caller conservatism) rather than removed outright."
    )

    # Sanctioned #579 exception (third-party editor library internal render
    # nodes): CodeMirror's per-line <div class="cm-line"> nodes are
    # library-internal, not app JSX — no testid can be placed on them. Scoped
    # raw selector under the testid-anchored yaml_editor parent, same shape
    # already used by edit_yaml_line()'s get_by_text() call below. This is
    # what get_yaml_content() actually reads lines through (ELITEA-2079 fix —
    # yaml_lines above never resolved any elements).
    YAML_LINE_SELECTOR = ".cm-line"

    chat_input = LocatorDescriptor(
        testid="chat-message-input",
        fallback=lambda page: page.locator('textarea#standard-multiline-static'),
        description="Embedded chat input field"
    )

    chat_send_button = LocatorDescriptor(
        testid="chat-send-button",
        fallback=lambda page: page.get_by_role("button", name="send your question"),
        description="Embedded chat send button"
    )

    # MCP node inline config fields (ELITEA-1954). Testid-only, added via
    # add-data-testid — BaseToolNode.jsx only sets these when nodeType is
    # "mcp" (untested node types stay untagged, .agents/testing.md §
    # Locator policy). Page-wide (not scoped to a specific node container):
    # correct as long as a test only has a single MCP node on canvas.
    mcp_node_toolkit_select = LocatorDescriptor(
        testid="pipeline-mcp-node-toolkit-select",
        description="MCP node's Toolkit select (inline on the ReactFlow canvas card)"
    )

    # The outer `pipeline-mcp-node-toolkit-select` testid lands on MUI's
    # MuiInputBase-root wrapper div — confirmed live (ELITEA-1955) that
    # `aria-expanded` is NOT on that element but on a nested child div
    # (role="combobox", MUI's own "display" element). Added via
    # add-data-testid (SingleSelect.jsx SelectDisplayProps) so open/closed
    # state can be read even when the dropdown renders zero real options
    # (no select-option-* row to fall back on — see
    # open_mcp_node_toolkit_select_allow_empty below).
    mcp_node_toolkit_select_combobox = LocatorDescriptor(
        testid="pipeline-mcp-node-toolkit-select-combobox",
        description="MCP node's Toolkit select — inner combobox div carrying aria-expanded"
    )

    mcp_node_tool_select = LocatorDescriptor(
        testid="pipeline-mcp-node-tool-select",
        description="MCP node's Tool select (inline on the ReactFlow canvas card)"
    )

    mcp_node_input_select = LocatorDescriptor(
        testid="pipeline-mcp-node-input-select",
        description="MCP node's tool-agnostic Input state-variable select"
    )

    mcp_node_output_select = LocatorDescriptor(
        testid="pipeline-mcp-node-output-select",
        description="MCP node's tool-agnostic Output state-variable select"
    )

    mcp_node_input_mapping_required_heading = LocatorDescriptor(
        testid="pipeline-mcp-node-input-mapping-heading",
        description=(
            "MCP node's 'Input mapping (required N)' accordion heading "
            "(BasicAccordion.jsx summary, gated to nodeType==mcp in "
            "BaseToolNode.jsx — added via add-data-testid for ELITEA-1954 "
            "review fix pass; case steps 4 and 6)"
        )
    )

    # HITL node inline config (ELITEA-2014). Testid-only, added via
    # add-data-testid — HITLNode.jsx call sites only (untested node types
    # stay untagged, .agents/testing.md § Locator policy). Page-wide (not
    # scoped to a specific node container): correct as long as a test only
    # has a single HITL node on canvas.
    hitl_node_input_select = LocatorDescriptor(
        testid="pipeline-hitl-node-input-select",
        description="HITL node's tool-agnostic Input state-variable select (inline on canvas card)"
    )

    hitl_node_user_message_type_select = LocatorDescriptor(
        testid="pipeline-hitl-node-user-message-type-select",
        description="HITL node's USER MESSAGE Type select"
    )

    hitl_node_user_message_value_input = LocatorDescriptor(
        testid="pipeline-hitl-node-user-message-value-input",
        description="HITL node's USER MESSAGE Value field (textarea when Type is Fixed/F-String)"
    )

    hitl_node_router_mapping_section = LocatorDescriptor(
        testid="pipeline-hitl-node-router-mapping-section",
        description="HITL node's ROUTER MAPPING accordion container"
    )

    hitl_node_edit_state_key_select = LocatorDescriptor(
        testid="pipeline-hitl-node-edit-state-key-select",
        description="HITL node's EDIT STATE KEY Value select"
    )

    # Dynamic (runtime-parameterized) testid — one Route select per HITL
    # action (approve/edit/reject). Class-level template constant per
    # .agents/testing.md § Locator policy, formatted with test-generated
    # data only at the call site.
    HITL_NODE_ROUTE_SELECT = '[data-testid="pipeline-hitl-node-route-select-{}"]'

    # SingleSelect.jsx auto-derives `${data-testid}-combobox` on its inner
    # role="combobox" display div (SelectDisplayProps) whenever a top-level
    # `data-testid` is passed — same mechanism already relied on by
    # mcp_node_toolkit_select_combobox. `aria-disabled`/`aria-expanded` land
    # on THIS inner element, not on the outer `pipeline-hitl-node-route-
    # select-{action}` testid (which lands on MUI's MuiInputBase-root wrapper).
    HITL_NODE_ROUTE_SELECT_COMBOBOX = '[data-testid="pipeline-hitl-node-route-select-{}-combobox"]'

    # Chat HITL runtime actions (ELITEA-2015). Testid-only, added via
    # add-data-testid — ChatHitlActions.jsx's non-sensitive-tool branch +
    # EditControl.jsx's toggle button.
    chat_hitl_actions_panel = LocatorDescriptor(
        testid="chat-hitl-actions-panel",
        description="Chat card container for a paused HITL node's Approve/Edit/Reject actions"
    )

    chat_hitl_approve_button = LocatorDescriptor(
        testid="chat-hitl-approve-button",
        description="Chat HITL card's Approve button"
    )

    chat_hitl_reject_button = LocatorDescriptor(
        testid="chat-hitl-reject-button",
        description="Chat HITL card's Reject button"
    )

    chat_hitl_edit_button = LocatorDescriptor(
        testid="chat-hitl-edit-button",
        description="Chat HITL card's Edit toggle button"
    )

    # TOOLS section (ELITEA-1955). ApplicationTools.jsx / ToolMenu.jsx is a
    # shared component reused by both Agent and Pipeline detail forms
    # (confirmed via PipelineConfigurationForm.jsx import) — same testids as
    # AgentDetailPage's Toolkits-section fields, ported here since
    # PipelineFormPage/PipelineDetailPage had no TOOLS-section locators yet.
    toolkits_section = LocatorDescriptor(
        testid="agent-toolkits-section",
        description="TOOLS section container (Toolkit/MCP/Agent/Pipeline add buttons + MODULES)"
    )
    add_mcp_button = LocatorDescriptor(
        testid="agent-add-mcp-button",
        description='"+ MCP" button in the TOOLS section (ToolMenu.jsx)'
    )
    toolkit_card = LocatorDescriptor(
        testid="agent-toolkit-card",
        description="An attached toolkit/MCP card in the TOOLS section"
    )

    # "+ Toolkit" button (ELITEA-2021). Testid already exists in the DOM on
    # `main` (ToolMenu.jsx) and is already a field on AgentDetailPage — only
    # missing here since PipelineDetailPage previously had no Toolkit-attach
    # field (only the sibling "+ MCP" button above).
    add_toolkit_button = LocatorDescriptor(
        testid="agent-add-toolkit-button",
        description='"+ Toolkit" button in the TOOLS section (ToolMenu.jsx)'
    )

    # General/Welcome/Chat-starters fields (ELITEA-2021). These testids exist
    # in the DOM on `main` already (shared AgentInput/ConversationStarters
    # components, confirmed via ELITEA-2021 AFS provenance check) but had no
    # LocatorDescriptor field on PipelineFormPage/PipelineDetailPage yet.
    welcome_message_input = LocatorDescriptor(
        testid="agent-welcome-message-input",
        description="Welcome message textarea (shared AgentInput.WelcomeMessageInput)"
    )

    conversation_starter_add_button = LocatorDescriptor(
        testid="agent-conversation-starter-add",
        description='"+ Starter" button (shared ConversationStarters component)'
    )

    conversation_starter_inputs = LocatorDescriptor(
        testid="agent-conversation-starter-input",
        description="Conversation starter textarea field(s)"
    )

    # ADVANCED section Step limit (ELITEA-2021). Testid added via
    # add-data-testid onto ApplicationAdvanceSettings.jsx's optional
    # `stepLimitTestId` prop, wired only at PipelineConfigurationForm.jsx's
    # call site (canon #511 scope discipline — no Agent case exercises it).
    step_limit_input = LocatorDescriptor(
        testid="pipeline-step-limit-input",
        description="ADVANCED section Step limit numeric input"
    )

    # EDITOR NOTES section (ELITEA-2021). Testids added via add-data-testid
    # onto ApplicationEditorNotes.jsx's optional `sectionTestId`/
    # `notesInputTestId` props, wired only at PipelineConfigurationForm.jsx's
    # call site (same scope discipline as step_limit_input above).
    editor_notes_section = LocatorDescriptor(
        testid="pipeline-editor-notes-section",
        description="EDITOR NOTES accordion header"
    )

    editor_notes_input = LocatorDescriptor(
        testid="pipeline-editor-notes-input",
        description="EDITOR NOTES textarea"
    )

    # Scoped selector (inside the '+ MCP' popper) — same testid family as
    # AgentDetailPage.toolkit_search_input, per .agents/testing.md § Locator
    # policy (class-level constant for selectors used inside a parent locator).
    TOOLKIT_SEARCH_INPUT_SELECTOR = '[data-testid="toolkit-search-input"]'

    # Scoped selector (inside the '+ MCP' popper) — same `toolkit-menu-item`
    # testid every UnifiedDropdown popper row shares (see
    # components/mui.py Popper.select_menuitem_by_testid), per
    # .agents/testing.md § Locator policy (class-level constant for
    # selectors used inside a parent locator).
    TOOLKIT_MENU_ITEM_SELECTOR = '[data-testid="toolkit-menu-item"]'

    # Dynamic (runtime-parameterized) testid — the Input-mapping "Value"
    # field is one per tool parameter (e.g. RepoName, Question). Class-level
    # template constant per .agents/testing.md § Locator policy, formatted
    # with test-generated data only at the call site.
    MCP_NODE_INPUT_MAPPING_VALUE = '[data-testid="pipeline-mcp-node-input-mapping-value-{}"]'

    # Select-dropdown option pattern shared by Toolkit/Tool/Input/Output
    # selects (SingleSelectMenuItem.jsx: `select-option-{value}`) — confirmed
    # present and reliable per ELITEA-1954 AFS Concrete Handles.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    # Prefix-match variant of SELECT_OPTION for enumerating every option
    # currently rendered in an open Toolkit/Tool listbox — same testid
    # family (`select-option-{value}`), no value known up front. Still
    # testid-keyed, not a raw role/CSS selector.
    SELECT_OPTION_PREFIX = '[data-testid^="select-option-"]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_network(self, timeout: int = 15000) -> None:
        """Wait for network activity to settle.

        Overrides BasePage.wait_for_network to handle the pipeline detail page,
        which has persistent WebSocket connections (Vite HMR and app socket.io)
        that prevent networkidle from ever being reached.  The timeout is
        treated as a best-effort ceiling: if networkidle is not reached we log
        a debug message and continue, matching the strategy used by
        BasePage.navigate().

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            logger.debug(
                "networkidle not reached on pipeline detail page "
                "(persistent WebSocket connections) — continuing"
            )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, pipeline_id: int):
        """Navigate to pipeline detail page and wait for load.

        Args:
            pipeline_id: The numeric pipeline ID.
        """
        super().navigate(f"/pipelines/all/{pipeline_id}?viewMode=owner")
        self.wait_for_detail_page_load()
        logger.info("Navigated to pipeline %d detail page", pipeline_id)

    # ------------------------------------------------------------------
    # Wait methods
    # ------------------------------------------------------------------

    def wait_for_detail_page_load(self, timeout: int = 15000):
        """Wait for the pipeline detail/edit page to fully load.

        Waits for URL to contain /pipelines/all/ (not /create), then
        waits for the Name input to have a non-empty value.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        # Wait for URL to move away from the create page to the detail page.
        # The create form's input#name already has a value after fill_form(),
        # so checking the input alone would false-positive on the create page.
        self.page.wait_for_function(
            """() => window.location.pathname.includes('/pipelines/all/')""",
            timeout=timeout,
        )
        # Wait for the Name input to have a non-empty value
        self.page.wait_for_function(
            """() => {
                const input = document.querySelector('input#name');
                return input && input.value.length > 0;
            }""",
            timeout=timeout,
        )
        logger.info("Pipeline detail page loaded")

    # ------------------------------------------------------------------
    # Pipeline info
    # ------------------------------------------------------------------

    def get_pipeline_id(self) -> str:
        """Read the Pipeline ID from the Information section.

        Returns:
            Pipeline ID as string.
        """
        return self.copy_id_button.text_content().strip()

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def click_configuration_tab(self, timeout: int = 10000):
        """Click the Configuration tab.

        Args:
            timeout: Maximum wait time for tab content to load.
        """
        logger.info("Clicking Configuration tab")
        self.dismiss_banner_if_present()
        self.configuration_tab.click()
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("Configuration tab opened")

    def click_history_tab(self, timeout: int = 10000):
        """Click the History tab.

        Args:
            timeout: Maximum wait time for tab content to load.
        """
        logger.info("Clicking History tab")
        self.dismiss_banner_if_present()
        self.history_tab.click()
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("History tab opened")

    def get_history_entries(self) -> list[str]:
        """Return the list of version entries visible on the History tab.

        History entries are typically shown as rows or cards with version
        names/timestamps.

        Returns:
            List of history entry text content.
        """
        entries = []

        # Try table rows first
        rows = self.page.locator("table tbody tr")
        if rows.count() > 0:
            for i in range(rows.count()):
                entries.append(rows.nth(i).text_content() or "")
            return entries

        # Try list items
        items = self.page.locator('[class*="version"], [class*="history"]')
        if items.count() > 0:
            for i in range(items.count()):
                entries.append(items.nth(i).text_content() or "")
            return entries

        return entries

    # ------------------------------------------------------------------
    # Actions menu
    # ------------------------------------------------------------------

    def open_actions_menu(self):
        """Open the three-dot actions menu on the pipeline detail page.

        Dismisses any banner overlay first, then clicks the three-dot menu
        button in the header bar. The three-dot button is the rightmost
        aria-haspopup button in the top header bar (y < 45px).

        LOCATOR: Pipeline page has a green + button in the flow editor
        that also has aria-haspopup="true", so we must find the correct
        button by position (rightmost in top 45px).
        """
        logger.info("Opening actions menu")
        self.dismiss_banner_if_present()
        self.page.wait_for_timeout(300)
        # The three-dot button is the rightmost button with
        # aria-haspopup in the top 45px of the page.
        self.page.evaluate("""() => {
            const buttons = document.querySelectorAll('button[aria-haspopup="true"]');
            let target = null;
            let maxX = -1;
            for (const btn of buttons) {
                const rect = btn.getBoundingClientRect();
                if (rect.y < 45 && rect.x > maxX) {
                    maxX = rect.x;
                    target = btn;
                }
            }
            if (target) target.click();
        }""")
        self.page.locator('[role="menu"]').wait_for(state="visible", timeout=5000)

    def delete_pipeline_via_menu(self, timeout: int = 10000):
        """Delete the current pipeline via the three-dot menu.

        Opens the menu, clicks "Delete pipeline", types the pipeline name
        into the confirmation dialog, and clicks Delete.

        Args:
            timeout: Maximum wait time for delete operation.
        """
        logger.info("Deleting pipeline via menu")
        pipeline_name = self.get_name()

        self.open_actions_menu()
        # Wait for menu to fully render then click Delete pipeline
        self.page.get_by_role("menuitem", name="Delete pipeline").click()

        # Handle type-to-confirm dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.type_to_confirm(dialog, pipeline_name)
        self.page.wait_for_timeout(300)
        Dialog.click_button(dialog, "Delete")
        # After the delete API response, networkidle fires. The SPA then
        # processes the response asynchronously and may start a client-side
        # navigation. A small wait here lets that navigation begin before
        # wait_for_network() so the latter catches it and waits for completion.
        self.page.wait_for_timeout(800)
        self.wait_for_network(timeout=timeout)
        logger.info("Pipeline deleted via menu")

    def export_pipeline_via_menu(self, timeout: int = 10000) -> bool:
        """Export the pipeline via the three-dot menu.

        Args:
            timeout: Maximum wait time for export action.

        Returns:
            True if the Export menu item was found and clicked.
        """
        logger.info("Exporting pipeline via menu")
        self.open_actions_menu()

        export_item = self.page.get_by_role("menuitem", name="Export")
        if export_item.count() == 0:
            logger.warning("Export menu item not found")
            return False

        export_item.click()
        self.page.wait_for_timeout(1000)
        self.wait_for_network(timeout=timeout)
        logger.info("Pipeline exported via menu")
        return True

    def fork_pipeline_via_menu(self, timeout: int = 10000) -> bool:
        """Fork (duplicate) the pipeline via the three-dot menu.

        Args:
            timeout: Maximum wait time for fork action.

        Returns:
            True if the Fork menu item was found and clicked.
        """
        logger.info("Forking pipeline via menu")
        self.open_actions_menu()

        # May be "Fork", "Duplicate", or "Clone"
        for label in ("Fork", "Duplicate", "Clone"):
            item = self.page.get_by_role("menuitem", name=label)
            if item.count() > 0:
                item.click()
                self.page.wait_for_timeout(1000)
                self.wait_for_network(timeout=timeout)
                logger.info("Pipeline forked via menu (%s)", label)
                return True

        logger.warning("Fork/Duplicate menu item not found")
        return False

    def get_actions_menu_items(self) -> list[str]:
        """Open the three-dot menu and return all menu item labels.

        Returns:
            List of visible menu item text labels.
        """
        self.open_actions_menu()
        items = self.page.locator('[role="menuitem"]')
        labels = []
        for i in range(items.count()):
            text = items.nth(i).text_content() or ""
            if text.strip():
                labels.append(text.strip())
        # Close menu by pressing Escape
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        return labels

    # ------------------------------------------------------------------
    # YAML / Flow view toggle
    # ------------------------------------------------------------------

    def switch_to_flow_view(self):
        """Switch the pipeline editor to the visual Flow view."""
        if self.flow_view_button.is_visible():
            self.flow_view_button.click()
            self.page.wait_for_timeout(1000)

    def switch_to_yaml_view(self):
        """Switch the pipeline editor to the YAML text view."""
        if self.yaml_view_button.is_visible():
            self.yaml_view_button.click()
            self.page.wait_for_timeout(1000)

    def is_yaml_view_active(self) -> bool:
        """Check if the YAML editor view is currently active.

        The YAML view uses a CodeMirror editor (div.cm-editor).

        Returns:
            True if YAML view is active, False otherwise.
        """
        return self.page.locator("div.cm-editor").count() > 0

    def is_flow_view_active(self, timeout: int = 10000) -> bool:
        """Check if the Flow (ReactFlow canvas) view is currently active.

        Waits up to *timeout* ms for the ReactFlow canvas wrapper to appear
        before returning.  The FlowWrapper component is lazy-loaded, so it
        may not be mounted immediately after navigation.

        Args:
            timeout: Maximum time in milliseconds to wait for the canvas.

        Returns:
            True if Flow view is active, False otherwise.
        """
        try:
            self.canvas_wrapper.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return self.canvas_wrapper.count() > 0 and self.canvas_wrapper.is_visible()

    def get_yaml_content(self) -> str:
        """Read the YAML content from the CodeMirror editor.

        CodeMirror renders each line in a separate div.cm-line element.
        Using text_content() on the parent concatenates lines without
        newlines (and interleaves the gutter's line-number nodes before
        each line's actual text in DOM order — confirmed live, ELITEA-2079),
        so lines are read via YAML_LINE_SELECTOR (".cm-line"), scoped under
        the testid-anchored yaml_editor parent (sanctioned #579 exception —
        CodeMirror's per-line nodes are library-internal, not app JSX; see
        YAML_LINE_SELECTOR's docstring), and joined with newlines.

        Returns:
            The text content of the YAML editor with preserved line breaks.
        """
        self.yaml_editor.wait_for(state="visible", timeout=5000)
        lines = self.yaml_editor.locator(self.YAML_LINE_SELECTOR)
        line_count = lines.count()
        if line_count == 0:
            return self.yaml_editor.text_content() or ""
        return "\n".join(lines.nth(i).text_content() or "" for i in range(line_count))

    def edit_yaml_line(self, current_line_text: str, new_line_text: str) -> None:
        """Replace one line of the YAML CodeMirror editor with *new_line_text*.

        DECLARED IMPROVISATION (AFS ELITEA-2028, closely mirrors the
        lead-approved 2026-07-16 pattern in
        ``McpFormPage.fill_raw_json_line``, ``automation/pages/
        mcp_form_page.py:597``): the YAML editor's per-line
        ``<div class="cm-line">`` nodes are CodeMirror-internal render
        nodes, not app JSX — no testid can be placed on them (sanctioned
        #579 "third-party editor library internal render nodes"
        exception, ``.agents/testing.md`` § Locator policy). ``get_by_text
        ()`` scoped inside the testid-anchored ``yaml_editor`` parent
        ``LocatorDescriptor`` field is the sanctioned shape for this
        canon-gap; do not extend it to any handle that COULD carry a
        testid.

        Ambiguity caveat (confirmed live, AFS Concrete Handles):
        ``get_by_text(exact=True)`` matches by DOM/document order, not by
        node association. If more than one line in the document has
        identical (trimmed) text, ``.first`` resolves to whichever occurs
        earliest in the document — this method is not disambiguation-safe
        for a caller with multiple identical target lines in
        unpredictable order; know your document's ordering before relying
        on ``.first``.

        Args:
            current_line_text: Exact current (trimmed) text of the target
                line — no leading indentation, matching
                ``fill_raw_json_line``'s calling convention — used to
                locate the line's div via ``get_by_text(..., exact=True)``
                scoped inside the editor.
            new_line_text: Replacement text for the line, again without
                leading indentation — ``Home`` moves to the first
                non-whitespace character (confirmed live), so the line's
                existing indentation is preserved automatically.
        """
        line = self.yaml_editor.get_by_text(current_line_text, exact=True).first
        line.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self._wait_for_yaml_line_selection_applied(line)
        self.page.keyboard.type(new_line_text)
        self._wait_for_yaml_content_stable()

    def _wait_for_yaml_line_selection_applied(self, line_locator: Locator, timeout_ms: int = 10_000) -> None:
        """Wait until *line_locator*'s content is selected via ``Home``/``Shift+End``.

        Mirrors ``McpFormPage._wait_for_line_selection_applied`` (same
        CodeMirror per-line selection mechanics). Not extracted to a
        shared base — the two page objects share no common ancestor and
        this is only the second occurrence, below Hard Rule 7's
        third-repetition extraction threshold.
        """
        handle = line_locator.element_handle()
        self.page.wait_for_function(
            """(el) => {
                const trimmedLen = el.textContent.trim().length;
                const sel = window.getSelection();
                return trimmedLen === 0 || (sel && sel.toString().length === trimmedLen);
            }""",
            arg=handle,
            timeout=timeout_ms,
        )

    def _wait_for_yaml_content_stable(self, stable_duration_ms: int = 150, timeout_ms: int = 10_000) -> None:
        """Poll the YAML editor's ``text_content()`` until it stops changing.

        Mirrors ``McpFormPage._wait_for_text_content_stable`` — waits for
        the editor's rendered text to converge (typing + any CodeMirror
        formatting/re-render) rather than a fixed delay.
        """
        deadline = time.monotonic() + timeout_ms / 1000.0
        stable_duration = stable_duration_ms / 1000.0
        last_text = None
        stable_since = time.monotonic()
        while time.monotonic() < deadline:
            current_text = self.yaml_editor.text_content() or ""
            if current_text != last_text:
                last_text = current_text
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= stable_duration:
                return
            time.sleep(0.05)
        raise TimeoutError(f"YAML editor text did not stabilise within {timeout_ms}ms (last: {last_text!r})")

    # ------------------------------------------------------------------
    # ReactFlow canvas — node management
    # ------------------------------------------------------------------

    def wait_for_canvas(self, timeout: int = 30000):
        """Wait for the ReactFlow canvas to be visible.

        The FlowWrapper component is lazy-loaded via React.lazy/Suspense, so
        it shows "Preparing the flow editor..." while the JS chunk is loading.
        This method first waits for that Suspense fallback to disappear, then
        waits for the ReactFlow wrapper element to become visible.

        Args:
            timeout: Maximum wait time in milliseconds. Default raised to
                30000ms to accommodate lazy-chunk loading time.
        """
        # Wait for the Suspense fallback text to disappear before checking
        # for the canvas, so we don't consume the full timeout on the spinner.
        try:
            self.page.locator('text="Preparing the flow editor..."').wait_for(
                state="hidden", timeout=timeout
            )
        except Exception:
            pass  # Fallback text was never shown or already gone

        self.canvas_wrapper.wait_for(state="visible", timeout=timeout)
        logger.info("ReactFlow canvas visible")

    def add_node(self, node_type: str, timeout: int = 5000):
        """Add a node to the canvas via the + button menu.

        Available node types: Agent, Code, Custom, Decision, Human-in-the-loop,
        LLM, MCP, Printer, Router, State modifier, Toolkit.

        Note: For wait_for_node_on_canvas, use the internal type name:
        - "Human-in-the-loop" → pass "hitl" to wait_for_node_on_canvas
        - All other types: lowercase display name (e.g. "llm", "code")

        Args:
            node_type: Display name of the node type to add.
            timeout: Maximum wait time for menu to appear.
        """
        logger.info("Adding node: %s", node_type)
        # The green + button is the MuiIconButton-colorPrimary in the
        # canvas area (not the header three-dot button).
        add_btn = self.page.locator("button.MuiIconButton-colorPrimary").first
        add_btn.click()
        self.page.wait_for_timeout(300)

        menu_item = self.page.get_by_role("menuitem", name=node_type, exact=True)
        menu_item.wait_for(state="visible", timeout=timeout)
        menu_item.click()
        self.page.wait_for_timeout(1000)
        logger.info("Added node: %s", node_type)

    def get_node_count(self) -> int:
        """Return the number of nodes on the canvas.

        Returns:
            Count of .react-flow__node elements.
        """
        return self.page.locator(".react-flow__node").count()

    def get_node_ids(self) -> list[str]:
        """Return the data-id values of all nodes on the canvas.

        Returns:
            List of node IDs.
        """
        nodes = self.page.locator(".react-flow__node")
        ids = []
        for i in range(nodes.count()):
            nid = nodes.nth(i).get_attribute("data-id")
            if nid:
                ids.append(nid)
        return ids

    def wait_for_node_on_canvas(
        self, node_type: str, *, timeout: int = 10000,
    ) -> str:
        """Wait for a node of *node_type* to appear on the canvas.

        ReactFlow node CSS class is .react-flow__node-{lowercase_type}.

        Args:
            node_type: The node type name (case-insensitive).
            timeout: Maximum wait time in milliseconds.

        Returns:
            The data-id of the first matching node.
        """
        css_type = node_type.lower().replace(" ", "_")
        selector = f".react-flow__node-{css_type}"
        node = self.page.locator(selector).first
        node.wait_for(state="visible", timeout=timeout)
        node_id = node.get_attribute("data-id") or ""
        logger.info("Node '%s' visible on canvas (id=%s)", node_type, node_id)
        return node_id

    def delete_node(self, node_id: str, timeout: int = 5000):
        """Delete a node from the canvas via its three-dot header menu.

        Each node has two header icon buttons (no aria-labels). The
        second one (the three-dot ⋮ icon) opens a menu containing
        a Delete item. Clicking Delete shows a confirmation dialog
        with Cancel / Delete buttons.

        Args:
            node_id: The data-id of the node to delete.
            timeout: Maximum wait time for menu / dialog to appear.
        """
        logger.info("Deleting node: %s", node_id)

        # Click the three-dot button (second MuiIconButton-colorTertiary)
        # via JS to avoid pointer interception from overlapping nodes.
        self.page.evaluate(
            """(nodeId) => {
                const node = document.querySelector(`[data-id="${nodeId}"]`);
                const btns = node.querySelectorAll(
                    'button.MuiIconButton-colorTertiary'
                );
                if (btns[1]) btns[1].click();
            }""",
            node_id,
        )
        self.page.wait_for_timeout(300)

        # Click "Delete" in the menu
        delete_item = self.page.get_by_role("menuitem", name="Delete")
        delete_item.wait_for(state="visible", timeout=timeout)
        delete_item.click()
        self.page.wait_for_timeout(300)

        # Confirm the "Are you sure to delete this node?" dialog
        dialog = Dialog.wait_for(self.page, timeout=timeout)
        Dialog.click_button(dialog, "Delete")
        self.page.wait_for_timeout(500)
        logger.info("Deleted node: %s", node_id)

    def make_node_entrypoint(self, node_id: str, timeout: int = 5000):
        """Set a node as the pipeline entrypoint via its three-dot menu.

        Args:
            node_id: The data-id of the node.
            timeout: Maximum wait time for the menu to appear.
        """
        logger.info("Making node '%s' the entrypoint", node_id)

        # Click the three-dot button (second MuiIconButton-colorTertiary)
        self.page.evaluate(
            """(nodeId) => {
                const node = document.querySelector(`[data-id="${nodeId}"]`);
                const btns = node.querySelectorAll(
                    'button.MuiIconButton-colorTertiary'
                );
                if (btns[1]) btns[1].click();
            }""",
            node_id,
        )
        self.page.wait_for_timeout(300)

        entrypoint_item = self.page.get_by_role("menuitem", name="Make entrypoint")
        entrypoint_item.wait_for(state="visible", timeout=timeout)
        entrypoint_item.click()
        self.page.wait_for_timeout(500)
        logger.info("Node '%s' set as entrypoint", node_id)

    def get_entrypoint_node_id(self) -> str | None:
        """Find the node that is currently marked as entrypoint.

        Reads the entry_point field from YAML content.

        Returns:
            The node ID of the entrypoint, or None if not determinable.
        """
        # Switch to YAML to read entry_point field
        current_is_flow = self.is_flow_view_active()
        self.switch_to_yaml_view()
        yaml_text = self.get_yaml_content()
        if current_is_flow:
            self.switch_to_flow_view()

        # Use regex to extract the entry_point value robustly.
        # When CodeMirror yaml_lines selector returns 0 matches, the fallback
        # yaml_editor.text_content() returns a concatenated single-line string
        # such as:
        #   "...entry_point: LLM 2nodes:  - id: LLM 1..."
        # A naive split("\n") would produce one element and
        # split("entry_point:")[-1].strip() would return "LLM 2nodes:..."
        # instead of the bare node ID "LLM 2".
        #
        # YAML keys are always lowercase (e.g. "nodes", "id", "type").
        # Node IDs are Title-Case or ALL-CAPS (e.g. "LLM 2", "Code 1").
        # The lookahead (?=\s*[a-z_]+:) terminates the capture at the first
        # lowercase YAML key that immediately follows the value, whether or
        # not a newline separates them.
        match = re.search(r"entry_point:\s*(.+?)(?=\s*[a-z_]+:|\n|$)", yaml_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def edit_node_name(self, node_id: str, new_name: str) -> str:
        """Edit a node's name by double-clicking on its name label.

        Double-clicking the node name span makes the first input inside
        the node become editable and focused.

        NOTE: Renaming a node changes its data-id. For example, renaming
        "LLM 1" to "MyNode" sets the data-id to "LLM MyNode".
        The method returns the new data-id so callers can track it.

        Args:
            node_id: The data-id of the node.
            new_name: New name for the node.

        Returns:
            The node's new data-id after the rename.
        """
        logger.info("Editing node %s name to '%s'", node_id, new_name)
        node = self.page.locator(f'[data-id="{node_id}"]')

        # Double-click the name label to activate inline editing
        name_label = node.locator(".MuiTypography-labelMedium").first
        name_label.dblclick()
        self.page.wait_for_timeout(300)

        # The first input[type="text"] inside the node holds the name
        name_input = node.locator('input[type="text"]').first
        name_input.press("Control+a")
        name_input.press("Backspace")
        name_input.type(new_name)
        self.page.wait_for_timeout(300)

        # Click outside the input to commit the edit
        self._deselect_all()
        self.page.wait_for_timeout(300)

        # Find the node's new data-id (renaming changes it)
        new_node_id = self.page.evaluate(
            """(oldId) => {
                // The type prefix stays, only the name portion changes
                const prefix = oldId.split(' ')[0];
                const nodes = document.querySelectorAll('.react-flow__node');
                for (const n of nodes) {
                    const nid = n.getAttribute('data-id');
                    if (nid && nid !== 'END' && nid.startsWith(prefix) && nid !== oldId) {
                        return nid;
                    }
                }
                // Fallback: return the first non-END node with the prefix
                for (const n of nodes) {
                    const nid = n.getAttribute('data-id');
                    if (nid && nid !== 'END' && nid.startsWith(prefix)) {
                        return nid;
                    }
                }
                return oldId;
            }""",
            node_id,
        )
        logger.info("Node %s renamed to '%s' (new id: %s)", node_id, new_name, new_node_id)
        return new_node_id

    def get_node_name(self, node_id: str) -> str:
        """Read the display name of a node.

        The name is shown in a MuiTypography-labelMedium span in the
        node header.

        Args:
            node_id: The data-id of the node.

        Returns:
            The node's display name text.
        """
        node = self.page.locator(f'[data-id="{node_id}"]')
        return node.locator(".MuiTypography-labelMedium").first.text_content().strip()

    # ------------------------------------------------------------------
    # MCP node inline config (ELITEA-1954)
    # ------------------------------------------------------------------

    def get_mcp_node_toolkit_value(self, timeout: int = 5000) -> str:
        """Read the MCP node's currently-selected Toolkit display text.

        Args:
            timeout: Maximum wait time for the select to be visible.

        Returns:
            The Toolkit select's current display text (empty string if unset).
        """
        self.mcp_node_toolkit_select.wait_for(state="visible", timeout=timeout)
        # MUI's empty-select rendering is a zero-width space (U+200B), not
        # an empty string — confirmed live during ELITEA-1954 exploration
        # (same gotcha as user_profile_settings_page.get_current_voice).
        text = (self.mcp_node_toolkit_select.text_content() or "").replace("​", "")
        return text.strip()

    def get_mcp_node_tool_value(self, timeout: int = 5000) -> str:
        """Read the MCP node's currently-selected Tool display text.

        Returns empty string both when no tool is selected AND when the Tool
        select isn't rendered at all yet (``BaseToolNode`` only renders it
        once ``functionOptions.length > 0`` — see AFS step 6, the "Tool
        field visibly reset to empty" moment right after a Toolkit change).

        Args:
            timeout: Maximum wait time for the select to be visible (not
                applied when the element never appears — see above).
        """
        try:
            self.mcp_node_tool_select.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        # MUI's empty-select rendering is a zero-width space (U+200B), not
        # an empty string — see get_mcp_node_toolkit_value.
        text = (self.mcp_node_tool_select.text_content() or "").replace("​", "")
        return text.strip()

    def open_mcp_node_toolkit_select(self, timeout: int = 5000) -> None:
        """Open the MCP node's Toolkit dropdown."""
        self.mcp_node_toolkit_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(
            state="visible", timeout=timeout
        )

    def open_mcp_node_toolkit_select_allow_empty(self, timeout: int = 5000) -> None:
        """Open the MCP node's Toolkit dropdown, tolerating zero real options.

        Additive sibling to :meth:`open_mcp_node_toolkit_select` (ELITEA-1955)
        — that method blocks on a ``select-option-*`` testid appearing, which
        never renders when the dropdown is genuinely empty (MUI's own
        placeholder ``<MenuItem value=""><em>None</em></MenuItem>`` carries no
        testid — confirmed live, see ELITEA-1955 AFS § Concrete Handles).
        This variant instead waits on the ``mcp_node_toolkit_select_combobox``
        element's ``aria-expanded="true"`` attribute — that inner div (not the
        outer ``mcp_node_toolkit_select`` testid, which lands on MUI's
        MuiInputBase-root wrapper) is the one that actually carries
        ``aria-expanded``, confirmed to flip regardless of option count.
        ``open_mcp_node_toolkit_select`` itself is left unmodified
        (page-objects.md shared-caller rule) — it has an existing merged
        caller (ELITEA-1954) relying on its option-visible wait.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        self.mcp_node_toolkit_select.click(timeout=timeout)
        expect(self.mcp_node_toolkit_select_combobox).to_have_attribute(
            "aria-expanded", "true", timeout=timeout
        )

    def close_mcp_node_toolkit_select(self, timeout: int = 5000) -> None:
        """Close the open MCP node Toolkit dropdown via Escape, without selecting.

        Mirrors ``AgentDetailPage.close_model_selector()``'s Escape-key
        pattern. Waits on ``mcp_node_toolkit_select_combobox``'s
        ``aria-expanded`` flipping back to ``"false"`` — the same element
        :meth:`open_mcp_node_toolkit_select_allow_empty` waits on to open, so
        this works whether or not the dropdown had any real options rendered
        (ELITEA-1955 AFS step 6).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        self.page.keyboard.press("Escape")
        expect(self.mcp_node_toolkit_select_combobox).to_have_attribute(
            "aria-expanded", "false", timeout=timeout
        )

    def open_mcp_node_tool_select(self, timeout: int = 5000) -> None:
        """Open the MCP node's Tool dropdown."""
        self.mcp_node_tool_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(
            state="visible", timeout=timeout
        )

    def get_open_listbox_option_names(self) -> list[str]:
        """Return the visible text of every option in the currently-open listbox.

        Call after ``open_mcp_node_toolkit_select`` / ``open_mcp_node_tool_select``.

        Returns:
            List of option display texts, in DOM order.
        """
        # Each option carries `data-testid="select-option-{value}"`
        # (SingleSelectMenuItem.jsx) — the same testid family already used
        # by select_mcp_node_toolkit/select_mcp_node_tool via SELECT_OPTION.
        # Only one listbox is open at a time (MUI portals it to <body>), so
        # a prefix match across the whole page enumerates exactly this
        # listbox's options.
        options = self.page.locator(self.SELECT_OPTION_PREFIX)
        count = options.count()
        return [(options.nth(i).text_content() or "").strip() for i in range(count)]

    def select_open_listbox_option(self, option_value: str, timeout: int = 5000) -> None:
        """Click an option in the currently-open Toolkit/Tool listbox.

        Use this when the caller needs to inspect the open option list (e.g.
        via ``get_open_listbox_option_names``) before choosing one — the
        dropdown is already open, so this only performs the click. When no
        prior inspection is needed, prefer ``select_mcp_node_toolkit`` /
        ``select_mcp_node_tool``, which open the dropdown and select in one
        call.

        Args:
            option_value: The option's value (matches ``select-option-{value}``).
            timeout: Maximum wait time for the option to be clickable.
        """
        option = self.page.locator(self.SELECT_OPTION.format(option_value))
        option.click(timeout=timeout)

    def select_mcp_node_toolkit(self, toolkit_name: str, timeout: int = 5000) -> None:
        """Open the Toolkit dropdown and select *toolkit_name*.

        Args:
            toolkit_name: The toolkit's display value (matches
                ``select-option-{toolkit_name}``, e.g. the toolkit's
                cleaned display name as rendered in the option list).
            timeout: Maximum wait time for the dropdown / option.
        """
        self.open_mcp_node_toolkit_select(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(toolkit_name))
        option.click(timeout=timeout)

    def select_mcp_node_tool(self, tool_name: str, timeout: int = 5000) -> None:
        """Open the Tool dropdown and select *tool_name*.

        Args:
            tool_name: The tool's value (matches ``select-option-{tool_name}``).
            timeout: Maximum wait time for the dropdown / option.
        """
        self.open_mcp_node_tool_select(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(tool_name))
        option.click(timeout=timeout)

    def get_mcp_node_input_mapping_value(self, param_name: str, timeout: int = 5000) -> str:
        """Read the current value of an Input-mapping "Value" field.

        Args:
            param_name: The tool parameter name (e.g. ``"repoName"``).
            timeout: Maximum wait time for the field to be visible.

        Returns:
            The field's current input value.
        """
        field = self.page.locator(self.MCP_NODE_INPUT_MAPPING_VALUE.format(param_name))
        field.wait_for(state="visible", timeout=timeout)
        return field.input_value()

    def fill_mcp_node_input_mapping_value(self, param_name: str, value: str, timeout: int = 5000) -> None:
        """Fill an Input-mapping "Value" field for a fixed-type tool parameter.

        Uses click + press_sequentially — MUI/React fields need real keyboard
        events for onChange to fire (.claude/rules/mui-patterns.md).

        Args:
            param_name: The tool parameter name (e.g. ``"repoName"``).
            value: The text to type.
            timeout: Maximum wait time for the field to be visible.
        """
        field = self.page.locator(self.MCP_NODE_INPUT_MAPPING_VALUE.format(param_name))
        field.wait_for(state="visible", timeout=timeout)
        field.click()
        field.press("Control+a")
        field.press("Delete")
        field.press_sequentially(value, delay=20)

    def is_mcp_node_input_mapping_value_visible(self, param_name: str, timeout: int = 5000) -> bool:
        """Check whether an Input-mapping "Value" field is visible for *param_name*.

        Used right after a Tool selection to confirm the mapping section
        rendered a Value field for each of the new tool's parameters — a
        pure visibility/rendering check, distinct from reading its content
        (see ``get_mcp_node_input_mapping_value``).

        Args:
            param_name: The tool parameter name (e.g. ``"repoName"``).
            timeout: Maximum wait time for the field to appear.

        Returns:
            True if the field is visible within *timeout*, False otherwise.
        """
        field = self.page.locator(self.MCP_NODE_INPUT_MAPPING_VALUE.format(param_name))
        try:
            field.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_input_mapping_section_visible(self, required_count: int, timeout: int = 5000) -> bool:
        """Check whether the "Input mapping (required N)" accordion is visible.

        Args:
            required_count: Expected N in the accordion title.
            timeout: Maximum wait time.

        Returns:
            True if the section with the exact required count is visible.
        """
        heading = self.mcp_node_input_mapping_required_heading
        try:
            heading.wait_for(state="visible", timeout=timeout)
        except Exception:
            return False
        text = (heading.text_content() or "").strip()
        return text == f"Input mapping (required {required_count})"

    # ------------------------------------------------------------------
    # TOOLS section — MCP attach (ELITEA-1955)
    # ------------------------------------------------------------------

    def ensure_toolkits_section_visible(self, timeout: int = 5000) -> None:
        """Scroll to the TOOLS section and wait for it to be visible.

        Ported from ``AgentDetailPage.ensure_toolkits_section_visible`` —
        same shared component, same testid (see ``toolkits_section``).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.toolkits_section.scroll_into_view_if_needed()
        self.toolkits_section.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(500)  # Animation settle
        logger.debug("TOOLS section scrolled into view")

    def open_mcp_popper(self, timeout: int = 10000) -> Locator:
        """Open the TOOLS section's "+ MCP" popper without selecting anything.

        Ported from ``AgentDetailPage.add_mcp()`` (ELITEA-1950), split into
        an open/select pair — mirrors the existing
        ``open_mcp_node_toolkit_select()`` / ``get_open_listbox_option_names()``
        / ``select_open_listbox_option()`` three-step pattern already used
        for the node's own Toolkit/Tool selects, so callers can assert the
        popper's contents (AFS step 7) before selecting (AFS step 8).
        ApplicationTools.jsx/ToolMenu.jsx is a shared component reused by
        both Agent and Pipeline detail forms (confirmed via
        PipelineConfigurationForm.jsx import; ELITEA-1955 AFS Automation
        Hints), and the same testids apply.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator of the visible MUI popper (see ``components.mui.Popper``).
        """
        logger.info("Opening TOOLS section '+ MCP' popper")
        self.ensure_toolkits_section_visible(timeout=timeout)
        self.add_mcp_button.wait_for(state="visible", timeout=timeout)
        self.add_mcp_button.click(force=True)
        return Popper.wait_for(self.page, timeout=timeout)

    def get_mcp_popper_search_input_count(self, popper: Locator) -> int:
        """Count of the toolkit-search-input field inside an open "+ MCP" popper.

        Kept as a page-object method rather than a raw ``popper.locator(...)``
        call in the test, per the testid-only-as-class-field POM rule —
        callers assert the popper's contents (AFS step 7) via this count.

        Args:
            popper: The popper Locator returned by :meth:`open_mcp_popper`.

        Returns:
            Number of matching elements (0 or 1 in practice).
        """
        return popper.locator(self.TOOLKIT_SEARCH_INPUT_SELECTOR).count()

    def get_mcp_popper_menu_item_count(self, popper: Locator) -> int:
        """Count of toolkit-menu-item rows inside an open "+ MCP" popper.

        Same rationale as :meth:`get_mcp_popper_search_input_count` — keeps
        the ``toolkit-menu-item`` testid centralized on the page object
        instead of constructed inline in the test.

        Args:
            popper: The popper Locator returned by :meth:`open_mcp_popper`.

        Returns:
            Number of matching menu-item rows.
        """
        return popper.locator(self.TOOLKIT_MENU_ITEM_SELECTOR).count()

    def select_mcp_in_popper(
        self, popper: Locator, mcp_name: str, project_id: str, timeout: int = 10000
    ) -> dict:
        """Select *mcp_name* in an already-open "+ MCP" popper.

        Waits on the attach PATCH response itself (not a fixed timeout) per
        AFS § Network Behavior, so a ``201`` is the only way this call
        returns — a non-201 or missing response times out here rather than
        being asserted after the fact. Uses the testid-anchored
        ``Popper.select_menuitem_by_testid`` helper (matches the
        ``toolkit-menu-item`` testid shared by every ``UnifiedDropdown``
        popper row, confirmed live for this popper — ELITEA-1955 AFS §
        Concrete Handles) rather than the older role-based
        ``Popper.select_menuitem`` that ``AgentDetailPage.add_mcp()`` uses.

        Args:
            popper: The popper Locator returned by :meth:`open_mcp_popper`.
            mcp_name: Exact name of the MCP to attach — MCP names are NOT
                space-stripped in this popper (unlike the Toolkit popper),
                per ``AgentDetailPage.add_mcp()``'s docstring.
            project_id: Project id, used to scope the attach response URL match.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the ``201 Created`` attach PATCH response.
        """
        logger.info("Selecting MCP '%s' in popper", mcp_name)
        search_input = popper.locator(self.TOOLKIT_SEARCH_INPUT_SELECTOR)
        if search_input.count() > 0 and search_input.first.is_visible():
            Popper.search(popper, mcp_name[:20], self.page)

        with self.page.expect_response(
            lambda r: f"/tool/prompt_lib/{project_id}/" in r.url
            and r.request.method == "PATCH"
            and r.status == 201,
            timeout=timeout,
        ) as response_info:
            Popper.select_menuitem_by_testid(popper, mcp_name, self.page, timeout=timeout)

        logger.info("MCP '%s' attached", mcp_name)
        return response_info.value.json()

    def open_toolkit_popper(self, timeout: int = 10000) -> Locator:
        """Open the TOOLS section's "+ Toolkit" popper without selecting anything.

        Mirrors :meth:`open_mcp_popper` (ELITEA-1955) but for the "+ Toolkit"
        button (``agent-add-toolkit-button``) — ``ApplicationTools.jsx``/
        ``ToolMenu.jsx`` shares the same ``UnifiedDropdown`` popper for both
        add affordances (ELITEA-2021 AFS § Concrete Handles).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator of the visible MUI popper (see ``components.mui.Popper``).
        """
        logger.info("Opening TOOLS section '+ Toolkit' popper")
        self.ensure_toolkits_section_visible(timeout=timeout)
        self.add_toolkit_button.wait_for(state="visible", timeout=timeout)
        self.add_toolkit_button.click(force=True)
        return Popper.wait_for(self.page, timeout=timeout)

    def select_toolkit_in_popper(self, popper: Locator, toolkit_name: str, timeout: int = 10000) -> None:
        """Select *toolkit_name* in an already-open "+ Toolkit" popper.

        Unlike :meth:`select_mcp_in_popper`, selecting a toolkit here does
        NOT immediately persist — confirmed live during ELITEA-2021
        analysis: the toolkit card appears locally and the actual
        persistence happens on the pipeline's next explicit Save (see
        :meth:`save_and_wait_for_update`). So this only performs the click;
        callers assert the card via :meth:`is_toolkit_attached` and persist
        separately.

        The popper's search input does not reliably narrow the row list
        (known quirk, ELITEA-2021 AFS § Concrete Handles) — select by exact
        visible text among the unfiltered rows via the testid-anchored
        helper instead of relying on search.

        Args:
            popper: The popper Locator returned by :meth:`open_toolkit_popper`.
            toolkit_name: Exact visible name of the toolkit to attach.
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting toolkit '%s' in popper", toolkit_name)
        Popper.select_menuitem_by_testid(popper, toolkit_name, self.page, timeout=timeout)

    def is_toolkit_attached(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check whether a toolkit/MCP card is attached in the TOOLS section.

        Ported from ``AgentDetailPage.is_toolkit_attached`` — same shared
        ``ToolCard.jsx`` component, same ``agent-toolkit-card`` testid.

        Args:
            toolkit_name: Toolkit/MCP name to look for.
            timeout: How long to wait for it to appear.

        Returns:
            True if a matching card is attached, False otherwise.
        """
        try:
            self.toolkit_card.filter(has_text=toolkit_name).first.wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    def save_and_wait_for_update(self, project_id: str, pipeline_id: int, timeout: int = 15000) -> dict:
        """Click Save and wait for the update PUT's 201 response.

        Waits on the network response itself, not a fixed timeout, per
        ELITEA-1954 AFS § Network Behavior / Automation Hints.

        Args:
            project_id: Project id, used to scope the response URL match.
            pipeline_id: The pipeline's numeric id.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the ``201 Created`` response.
        """
        with self.page.expect_response(
            lambda r: f"/application/prompt_lib/{project_id}/{pipeline_id}" in r.url
            and r.request.method == "PUT"
            and r.status == 201,
            timeout=timeout,
        ) as response_info:
            self.save_button.evaluate("el => el.click()")
        return response_info.value.json()

    # ------------------------------------------------------------------
    # General/Welcome/Chat-starters/Advanced/Editor-Notes fields (ELITEA-2021)
    # ------------------------------------------------------------------

    def fill_welcome_message(self, message: str, timeout: int = 5000):
        """Fill the Welcome message textarea.

        Uses click + press_sequentially — MUI/React fields need real
        keyboard events for onChange to fire (.claude/rules/mui-patterns.md).

        Args:
            message: Welcome message text.
            timeout: Maximum wait time for the field to be visible.
        """
        self.welcome_message_input.wait_for(state="visible", timeout=timeout)
        self.welcome_message_input.click()
        self.welcome_message_input.press("Control+a")
        self.welcome_message_input.press("Delete")
        self.welcome_message_input.press_sequentially(message, delay=20)
        self.page.wait_for_timeout(300)

    def get_welcome_message(self) -> str:
        """Read the current value of the Welcome message field."""
        return self.welcome_message_input.input_value()

    def add_conversation_starter(self, text: str = "", timeout: int = 5000):
        """Click "+ Starter" and fill the newly-added starter textarea.

        Args:
            text: Text to fill in the new starter field.
            timeout: Maximum wait time for the new field to appear.
        """
        logger.info("Adding conversation starter")
        self.conversation_starter_add_button.click()
        inputs = self.conversation_starter_inputs
        inputs.last.wait_for(state="visible", timeout=timeout)
        last_input = inputs.last
        last_input.click()
        if text:
            last_input.press_sequentially(text, delay=20)
            self.page.wait_for_timeout(300)

    def get_conversation_starter_value(self, index: int = 0) -> str:
        """Read the value of a conversation starter textarea by index.

        Args:
            index: Index of the conversation starter (0-based).
        """
        return self.conversation_starter_inputs.nth(index).input_value()

    def fill_step_limit(self, value: str, timeout: int = 5000):
        """Fill the ADVANCED section's Step limit numeric input.

        Uses click + JS ``.select()`` + ``keyboard.type()`` — same pattern
        as ``PipelineFormPage.update_text_field`` (native select() reliably
        selects the field's existing default value, e.g. "25"; the first
        typed keystroke then replaces the selection, same as any real user
        typing over a selected value — real keyboard events so the
        digit-only ``handleKeyDown`` validator sees each key).

        Args:
            value: New step limit value (digits only).
            timeout: Maximum wait time for the field to be visible.
        """
        self.step_limit_input.wait_for(state="visible", timeout=timeout)
        self.step_limit_input.click()
        self.step_limit_input.evaluate("el => el.select()")
        self.page.keyboard.type(value)

    def get_step_limit(self) -> str:
        """Read the current value of the Step limit field."""
        return self.step_limit_input.input_value()

    def fill_editor_notes(self, text: str, timeout: int = 5000):
        """Scroll to and fill the EDITOR NOTES textarea.

        Args:
            text: Notes text.
            timeout: Maximum wait time for the field to be visible.
        """
        self.editor_notes_section.scroll_into_view_if_needed()
        self.editor_notes_input.wait_for(state="visible", timeout=timeout)
        self.editor_notes_input.click()
        self.editor_notes_input.press_sequentially(text, delay=20)
        self.page.wait_for_timeout(300)

    def get_editor_notes(self) -> str:
        """Read the current value of the EDITOR NOTES textarea."""
        return self.editor_notes_input.input_value()

    def connect_nodes(
        self,
        source_node_id: str,
        target_node_id: str,
        *,
        source_handle: str | None = None,
        timeout: int = 5000,
    ):
        """Create a connection (edge) between two nodes by dragging.

        Drags from the source handle (bottom) of *source_node_id* to
        the target handle (top) of *target_node_id*.

        For nodes with multiple source handles (e.g., HITL with approve/edit/reject),
        specify which handle to use via the *source_handle* parameter.

        Args:
            source_node_id: data-id of the source node.
            target_node_id: data-id of the target node.
            source_handle: Optional handle ID suffix (e.g., "approve", "reject")
                for nodes with multiple output handles. If None, uses the first
                bottom handle found.
            timeout: Not currently used (reserved for future validation).
        """
        handle_desc = f" (handle={source_handle})" if source_handle else ""
        logger.info("Connecting %s%s -> %s", source_node_id, handle_desc, target_node_id)

        # Get handle positions via JS for precise coordinates
        positions = self.page.evaluate(
            """([srcId, tgtId, handleSuffix]) => {
                const srcNode = document.querySelector(`[data-id="${srcId}"]`);
                const tgtNode = document.querySelector(`[data-id="${tgtId}"]`);
                if (!srcNode || !tgtNode) return null;

                // Find source handle - by specific ID if provided, else first bottom
                let srcHandle;
                if (handleSuffix) {
                    // Look for handle with matching ID suffix
                    srcHandle = srcNode.querySelector(
                        `[data-handlepos="bottom"][data-handleid$="_${handleSuffix}"]`
                    );
                    if (!srcHandle) {
                        // Try exact match without underscore prefix
                        srcHandle = srcNode.querySelector(
                            `[data-handlepos="bottom"][data-handleid="${handleSuffix}"]`
                        );
                    }
                }
                if (!srcHandle) {
                    srcHandle = srcNode.querySelector('[data-handlepos="bottom"]');
                }
                const tgtHandle = tgtNode.querySelector('[data-handlepos="top"]');
                if (!srcHandle || !tgtHandle) return null;

                const sr = srcHandle.getBoundingClientRect();
                const tr = tgtHandle.getBoundingClientRect();
                return {
                    sx: sr.x + sr.width / 2,
                    sy: sr.y + sr.height - 2,
                    tx: tr.x + tr.width / 2,
                    ty: tr.y + 2,
                    srcHandleId: srcHandle.getAttribute('data-handleid'),
                };
            }""",
            [source_node_id, target_node_id, source_handle],
        )

        if not positions:
            raise ValueError(
                f"Could not find handles for {source_node_id} -> {target_node_id}"
            )

        sx, sy = positions["sx"], positions["sy"]
        tx, ty = positions["tx"], positions["ty"]
        logger.info("Using source handle: %s", positions.get("srcHandleId"))

        # Drag from source to target in small steps
        self.page.mouse.move(sx, sy)
        self.page.wait_for_timeout(100)
        self.page.mouse.down()
        self.page.wait_for_timeout(100)

        steps = 15
        for i in range(1, steps + 1):
            x = sx + (tx - sx) * i / steps
            y = sy + (ty - sy) * i / steps
            self.page.mouse.move(x, y)
            self.page.wait_for_timeout(30)

        self.page.mouse.up()
        self.page.wait_for_timeout(500)

        # Dismiss any ReactFlow "create new node" context menu that appears
        # when the drag misses a target handle and lands on empty canvas.
        if self.page.locator('[role="menu"]').count() > 0:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(200)

        logger.info("Connected %s -> %s", source_node_id, target_node_id)

    def get_edge_count(self) -> int:
        """Return the number of edges (connections) on the canvas.

        Returns:
            Count of .react-flow__edge elements.
        """
        return self.page.locator(".react-flow__edge").count()

    def edge_exists(self, source_id: str, target_id: str, handle_suffix: str | None = None) -> bool:
        """Check whether an edge from *source_id* to *target_id* exists.

        ReactFlow edge data-testid format (observed):
            rf__edge-xy-edge__{source_node_id}{source_handle}-{target_node_id}{target_handle}

        Examples:
            - LLM 1 -> END: rf__edge-xy-edge__LLM 1source-ENDtarget
            - LLM 1 -> Code 1: rf__edge-xy-edge__LLM 1source-Code 1target
            - HITL 1 reject -> END: rf__edge-xy-edge__HITL 1reject-ENDtarget

        Args:
            source_id: data-id of the source node.
            target_id: data-id of the target node.
            handle_suffix: Optional source handle suffix (e.g., "approve", "reject").
                If None, searches for any edge from source to target.

        Returns:
            True if the edge exists in the DOM.
        """
        edges = self.page.locator('.react-flow__edge')
        edge_count = edges.count()
        logger.debug("Looking for edge: %s -> %s (total edges: %d)", source_id, target_id, edge_count)

        all_testids = []
        for i in range(edge_count):
            testid = edges.nth(i).get_attribute('data-testid') or ""
            all_testids.append(testid)

            # Pattern: rf__edge-xy-edge__{source_id}{handle}-{target_id}target
            # Handle is 'source' for regular nodes, or 'approve'/'reject'/etc for HITL
            if handle_suffix:
                expected_prefix = f"rf__edge-xy-edge__{source_id}{handle_suffix}-{target_id}"
            else:
                expected_prefix = f"rf__edge-xy-edge__{source_id}"

            if testid.startswith(expected_prefix) and f"-{target_id}" in testid:
                logger.info("Found edge: %s", testid)
                return True

        logger.debug("All edges in DOM: %s", all_testids)
        return False

    # Exact edge testid, keyed by the LITERAL internal source/target ids as
    # they appear in the DOM (not the logical id `edge_exists()` accepts —
    # see `edge_testid_present()`'s docstring for why the two differ for
    # the END node specifically).
    EDGE_TESTID = '[data-testid="rf__edge-xy-edge__{}---{}"]'

    def edge_testid_present(self, source_internal_id: str, target_internal_id: str) -> bool:
        """Check whether the EXACT edge testid is present in the DOM.

        Unlike `edge_exists()` (prefix + substring matching against a
        LOGICAL target_id — unreliable for the END node, whose real
        internal target id is `EliteAPipelineEnd`, not the literal string
        "END"; see `edge_exists()`'s own docstring caveat), this checks
        the literal, exact DOM testid. Callers must pass the INTERNAL ids
        exactly as ReactFlow renders them (e.g. `EliteAPipelineEnd` for
        the END node), not the display name.

        Added for AFS ELITEA-2028 step 4: proving the SAME edge element's
        testid changed in place (`rf__edge-xy-edge__LLM 1---
        EliteAPipelineEnd` -> `rf__edge-xy-edge__LLM 1---Code 1`) rather
        than merely inferring re-wiring from unchanged edge/node counts.

        Args:
            source_internal_id: Literal source node id as rendered in the
                edge testid.
            target_internal_id: Literal target node id as rendered in the
                edge testid.

        Returns:
            True if an edge with that exact testid exists in the DOM.
        """
        return self.page.locator(self.EDGE_TESTID.format(source_internal_id, target_internal_id)).count() > 0

    def fit_view(self):
        """Click the ReactFlow 'Fit View' zoom control."""
        btn = self.page.locator('button[title="Fit View"]')
        if btn.count() > 0:
            btn.click()
            self.page.wait_for_timeout(500)

    def zoom_in(self):
        """Click the ReactFlow 'Zoom In' control."""
        btn = self.page.locator('button[title="Zoom In"]')
        if btn.count() > 0:
            btn.click()
            self.page.wait_for_timeout(300)

    def zoom_out(self):
        """Click the ReactFlow 'Zoom Out' control."""
        btn = self.page.locator('button[title="Zoom Out"]')
        if btn.count() > 0:
            btn.click()
            self.page.wait_for_timeout(300)

    def _select_node(self, node_id: str):
        """Select a node by clicking on it.

        Uses force=True because overlapping nodes can intercept clicks.

        Args:
            node_id: The data-id of the node.
        """
        node = self.page.locator(f'[data-id="{node_id}"]')
        node.click(force=True)
        self.page.wait_for_timeout(300)

    def _deselect_all(self):
        """Click on empty canvas space to deselect all nodes."""
        pane = self.page.locator(".react-flow__pane")
        bb = pane.bounding_box()
        if bb:
            self.page.mouse.click(bb["x"] + 30, bb["y"] + 30)
            self.page.wait_for_timeout(300)

    # ------------------------------------------------------------------
    # Embedded chat (right panel) — pipeline execution
    # ------------------------------------------------------------------

    def _embedded_chat_messages(self):
        """Return a locator for all message LI elements in the embedded chat.

        The embedded chat is in the right panel of the pipeline detail page.
        Messages are li.MuiListItem-root inside ul.MuiList-root.

        Returns:
            Locator for message list items.
        """
        return self.page.locator('ul.MuiList-root li.MuiListItem-root')

    def get_embedded_chat_message_count(self) -> int:
        """Return the number of messages in the embedded chat.

        Returns:
            Message count.
        """
        return self._embedded_chat_messages().count()

    def send_message_in_embedded_chat(self, message: str, timeout: int = 10000):
        """Type and send a message in the embedded chat panel.

        Args:
            message: The message text to send.
            timeout: Maximum wait time for elements.
        """
        logger.info("Sending message in embedded chat: %s", message[:60])
        self.chat_input.wait_for(state="visible", timeout=timeout)
        self.chat_input.fill(message)
        self.page.wait_for_timeout(300)

        self.chat_send_button.wait_for(state="visible", timeout=timeout)
        self.chat_send_button.click()
        logger.info("Message sent in embedded chat")

    def wait_for_embedded_chat_response(
        self,
        initial_count: int = 0,
        stable_duration_ms: int = 3000,
        timeout: int = 60000,
    ):
        """Wait for the AI response in the embedded chat to stabilise.

        Waits for new messages to appear beyond *initial_count*, then
        waits for the last message's text content to stop changing for
        *stable_duration_ms*.

        Args:
            initial_count: Number of messages before sending.
            stable_duration_ms: Content must be unchanged for this long (ms).
            timeout: Overall timeout in milliseconds.
        """
        logger.info(
            "Waiting for embedded chat response (initial=%d, stable=%dms, timeout=%dms)",
            initial_count, stable_duration_ms, timeout,
        )
        messages = self._embedded_chat_messages()
        deadline = time.time() + timeout / 1000

        # Wait for at least one new message beyond initial_count
        while time.time() < deadline:
            if messages.count() > initial_count:
                break
            self.page.wait_for_timeout(500)

        # Wait for the last AI message to have a Delete button (= response complete)
        ai_msg = messages.last
        try:
            ai_msg.locator('[aria-label="Delete"]').wait_for(
                state="visible",
                timeout=max(1000, int((deadline - time.time()) * 1000)),
            )
        except Exception:
            pass  # Fall through to content-stable check

        # Wait for content to stabilise
        last_content = ""
        stable_start = time.time()

        while time.time() < deadline:
            try:
                current = ai_msg.text_content() or ""
            except Exception:
                current = ""

            if current and current == last_content:
                if (time.time() - stable_start) * 1000 >= stable_duration_ms:
                    logger.info("Embedded chat response stabilised (%d chars)", len(current))
                    return
            else:
                last_content = current
                stable_start = time.time()

            self.page.wait_for_timeout(500)

        logger.warning("Embedded chat response did not stabilise within timeout")

    def get_embedded_chat_last_message(self) -> str:
        """Return the text content of the last AI message in embedded chat.

        Extracts text from the response container, skipping the "Thought"
        accordion header.

        Returns:
            Last AI message text content.
        """
        messages = self._embedded_chat_messages()
        if messages.count() == 0:
            return ""

        ai_msg = messages.last
        # Try to get text from the response content div (css-xn5i2e)
        response_div = ai_msg.locator('div.css-xn5i2e')
        if response_div.count() > 0:
            text = response_div.text_content() or ""
            return text.strip()

        # Fallback: extract from <p> tags (Markdown component)
        paragraphs = ai_msg.locator('p')
        if paragraphs.count() > 0:
            parts = []
            for i in range(paragraphs.count()):
                parts.append(paragraphs.nth(i).text_content() or "")
            text = "\n".join(parts).strip()
            if text:
                return text

        # Last fallback: all text from the message
        text = ai_msg.text_content() or ""
        return text.strip()

    def find_message_containing(self, text: str) -> bool:
        """Return True if any embedded chat message contains *text*.

        Searches all visible message items for the given substring.
        Uses the same locator as ``get_embedded_chat_message_count`` so
        both user and AI messages are searched.

        Args:
            text: Substring to look for (case-sensitive).

        Returns:
            True if at least one message contains *text*, False otherwise.
        """
        messages = self._embedded_chat_messages()
        for i in range(messages.count()):
            if text in (messages.nth(i).text_content() or ""):
                return True
        return False

    def clear_embedded_chat(self, timeout: int = 5000):
        """Clear the embedded chat history via the Clear button.

        Args:
            timeout: Maximum wait time for the clear action.
        """
        logger.info("Clearing embedded chat history")
        clear_btn = self.page.locator('[aria-label="Clear the chat history"]')
        if clear_btn.count() > 0 and clear_btn.is_visible():
            clear_btn.click()
            # Handle confirmation dialog if present
            try:
                dialog = Dialog.wait_for(self.page, timeout=3000)
                Dialog.click_button(dialog, "Confirm")
            except Exception:
                pass  # No confirmation dialog
            self.page.wait_for_timeout(1000)
            logger.info("Embedded chat cleared")

    # ------------------------------------------------------------------
    # Toolkit credential indicators (Enhancement #5114, Bug #5183)
    # ------------------------------------------------------------------

    def _get_toolkit_item(self, toolkit_name: str, timeout: int = 10000):
        """Get the toolkit item element in the left panel by name.

        Uses XPath to find the toolkit container inside the second MuiAccordionDetails-root.

        Args:
            toolkit_name: Name of the toolkit (may be truncated in UI).
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator for the toolkit item container.
        """
        name_prefix = toolkit_name[:20]
        toolkit_item = self.page.locator(
            f'xpath=(//div[contains(@class, "MuiAccordionDetails-root")])[2]'
            f'//div[.//div[contains(normalize-space(), "{name_prefix}")]]'
        ).first
        toolkit_item.wait_for(state="visible", timeout=timeout)
        return toolkit_item

    def hover_toolkit_item(self, toolkit_name: str, timeout: int = 10000):
        """Hover over a toolkit item in the left panel to reveal action icons.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.
        """
        toolkit_item = self._get_toolkit_item(toolkit_name, timeout)
        toolkit_item.hover()
        self.page.wait_for_timeout(500)

    def has_toolkit_status_indicator(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit item shows credential status indicator (warning icon).

        In Pipeline, the status indicator is an SVG icon near the toolkit name.
        We detect it by checking for warning message which appears below toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if status indicator/warning is visible.
        """
        return self.has_toolkit_warning_message(timeout)

    def get_toolkit_status_indicator_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the status indicator tooltip text for a toolkit.

        In Pipeline, returns the warning message aria-label.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        return self.get_toolkit_warning_message(timeout)

    def has_toolkit_warning_message(self, timeout: int = 5000) -> bool:
        """Check if credential warning banner is displayed below toolkit.

        Uses data-testid="credential-warning-banner" which is set on BannerMessage.jsx.
        The banner message text varies (e.g. "Authentication failed:", "Base URL is required",
        etc.) depending on the validation error type.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning banner is visible.
        """
        warning_banner = self.page.locator('[data-testid="credential-warning-banner"]')
        try:
            warning_banner.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_warning_message(self, timeout: int = 10000) -> str | None:
        """Get the credential warning banner message text.

        Uses data-testid="credential-warning-banner" which is set on BannerMessage.jsx.
        Returns the aria-label attribute value, which contains the error message text.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Warning message text, or None if not found.
        """
        warning_banner = self.page.locator('[data-testid="credential-warning-banner"]')
        try:
            warning_banner.first.wait_for(state="visible", timeout=timeout)
            return warning_banner.first.get_attribute("aria-label")
        except Exception:
            return None

    def has_toolkit_reload_button(self, toolkit_name: str, timeout: int = 5000) -> bool:
        """Check if toolkit has reload button (id=RefreshButton).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if reload button is visible.
        """
        self.hover_toolkit_item(toolkit_name, timeout)
        reload_btn = self.page.locator('#RefreshButton')
        try:
            reload_btn.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_reload_button_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the reload button tooltip text for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_toolkit_item(toolkit_name, timeout)
        reload_btn = self.page.locator('#RefreshButton')
        try:
            reload_btn.wait_for(state="visible", timeout=timeout)
            return reload_btn.get_attribute("aria-label")
        except Exception:
            return None

    def has_toolkit_open_in_new_tab_button(
        self, toolkit_name: str, timeout: int = 5000
    ) -> bool:
        """Check if toolkit has open-in-new-tab button (id=OpenInNewTabButton).

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if open-in-new-tab button is visible.
        """
        self.hover_toolkit_item(toolkit_name, timeout)
        open_btn = self.page.locator('#OpenInNewTabButton')
        try:
            open_btn.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_toolkit_open_in_new_tab_button_tooltip(
        self, toolkit_name: str, timeout: int = 10000
    ) -> str | None:
        """Get the open-in-new-tab button tooltip text for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_toolkit_item(toolkit_name, timeout)
        open_btn = self.page.locator('#OpenInNewTabButton')
        try:
            open_btn.wait_for(state="visible", timeout=timeout)
            return open_btn.get_attribute("aria-label")
        except Exception:
            return None

    def click_toolkit_open_in_new_tab(
        self, toolkit_name: str, timeout: int = 10000
    ) -> "Page":
        """Click the open-in-new-tab button for a toolkit.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.

        Returns:
            The new Page object for the opened tab.
        """
        self.hover_toolkit_item(toolkit_name, timeout)
        open_btn = self.page.locator('#OpenInNewTabButton')
        open_btn.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            open_btn.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        logger.info("Opened toolkit in new tab: %s", new_page.url)
        return new_page

    def wait_for_no_toolkit_status_indicator(
        self, toolkit_name: str, timeout: int = 15000
    ):
        """Wait for the toolkit warning message to disappear.

        Args:
            toolkit_name: Name of the toolkit.
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        warning_locator = self.page.locator('[data-testid="credential-warning-banner"]')
        expect(warning_locator.first).not_to_be_visible(timeout=timeout)
        logger.info("Toolkit warning message is no longer visible")

    # ------------------------------------------------------------------
    # HITL node inline config (ELITEA-2014)
    # ------------------------------------------------------------------

    def open_hitl_node_input_select(self, timeout: int = 5000) -> None:
        """Open the HITL node's tool-agnostic Input select."""
        self.hitl_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_hitl_node_input_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the Input select and choose *variable_name* (a multi-select; stays open).

        Args:
            variable_name: State variable to select (matches ``select-option-{variable_name}``).
            timeout: Maximum wait time in milliseconds.
        """
        self.open_hitl_node_input_select(timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(variable_name)).click(timeout=timeout)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(200)

    def get_hitl_node_input_display_text(self) -> str:
        """Return the Input select's full rendered text (all selected chips concatenated).

        Reads the testid-anchored field's own ``text_content()`` rather than
        drilling into a raw MUI chip CSS class (``.MuiChip-label`` is
        unstyled third-party markup with no testid — chaining a raw selector
        off an existing field is a page-objects.md anti-pattern). Callers
        checking whether a given variable is selected use substring
        containment against this text.
        """
        return (self.hitl_node_input_select.text_content() or "").strip()

    def open_hitl_node_user_message_type_select(self, timeout: int = 5000) -> None:
        """Open the HITL node's USER MESSAGE Type select."""
        self.hitl_node_user_message_type_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_hitl_node_user_message_type(self, type_value: str, timeout: int = 5000) -> None:
        """Select the USER MESSAGE Type.

        Args:
            type_value: One of ``"fixed"``, ``"fstring"``, ``"variable"`` (matches
                ``select-option-{type_value}`` — the raw YAML value, not the display label).
            timeout: Maximum wait time in milliseconds.
        """
        self.open_hitl_node_user_message_type_select(timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(type_value)).click(timeout=timeout)

    def get_hitl_node_user_message_type_display(self, timeout: int = 5000) -> str:
        """Read the USER MESSAGE Type select's current display text."""
        self.hitl_node_user_message_type_select.wait_for(state="visible", timeout=timeout)
        # MUI's empty-select rendering is a zero-width space (U+200B) — same
        # gotcha as get_mcp_node_toolkit_value.
        text = (self.hitl_node_user_message_type_select.text_content() or "").replace("​", "")
        return text.strip()

    def fill_hitl_node_user_message_value(self, text: str, timeout: int = 5000) -> None:
        """Fill the USER MESSAGE Value textarea (Type = Fixed or F-String).

        Uses click + press_sequentially — MUI/React fields need real keyboard
        events for onChange to fire (.claude/rules/mui-patterns.md).
        """
        self.hitl_node_user_message_value_input.wait_for(state="visible", timeout=timeout)
        self.hitl_node_user_message_value_input.click()
        self.hitl_node_user_message_value_input.press("Control+a")
        self.hitl_node_user_message_value_input.press("Delete")
        self.hitl_node_user_message_value_input.press_sequentially(text, delay=20)

    def get_hitl_node_user_message_value(self) -> str:
        """Read the USER MESSAGE Value textarea's current value."""
        return self.hitl_node_user_message_value_input.input_value()

    def open_hitl_node_route_select(self, action: str, timeout: int = 5000) -> None:
        """Open a ROUTER MAPPING Route select for *action*.

        Args:
            action: One of ``"approve"``, ``"edit"``, ``"reject"``.
            timeout: Maximum wait time in milliseconds.
        """
        select = self.page.locator(self.HITL_NODE_ROUTE_SELECT.format(action))
        select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_hitl_node_route(self, action: str, target_node_id: str, timeout: int = 5000) -> None:
        """Open a Route select for *action* and choose *target_node_id*.

        Args:
            action: One of ``"approve"``, ``"edit"``, ``"reject"``.
            target_node_id: The target node's data-id (or ``"END"``), matches
                ``select-option-{target_node_id}``.
            timeout: Maximum wait time in milliseconds.
        """
        self.open_hitl_node_route_select(action, timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(target_node_id)).click(timeout=timeout)

    def get_hitl_node_route_value(self, action: str, timeout: int = 5000) -> str:
        """Read a ROUTER MAPPING Route select's current display text.

        Args:
            action: One of ``"approve"``, ``"edit"``, ``"reject"``.
            timeout: Maximum wait time in milliseconds.
        """
        select = self.page.locator(self.HITL_NODE_ROUTE_SELECT.format(action))
        select.wait_for(state="visible", timeout=timeout)
        text = (select.text_content() or "").replace("​", "")
        return text.strip()

    def is_hitl_node_route_select_disabled(self, action: str, timeout: int = 5000) -> bool:
        """Return whether a ROUTER MAPPING Route select is ``aria-disabled``.

        Used to confirm the EDIT route select's gating on EDIT STATE KEY
        (ELITEA-2014 AFS step 5 — ``aria-disabled`` flips from ``"true"``
        to absent once EDIT STATE KEY has a value).

        Args:
            action: One of ``"approve"``, ``"edit"``, ``"reject"``.
            timeout: Maximum wait time in milliseconds.
        """
        combobox = self.page.locator(self.HITL_NODE_ROUTE_SELECT_COMBOBOX.format(action))
        combobox.wait_for(state="visible", timeout=timeout)
        return combobox.get_attribute("aria-disabled") == "true"

    def get_hitl_node_route_option_names(self, action: str, timeout: int = 5000) -> list[str]:
        """Open a Route select for *action*, read its option names, then close it.

        Args:
            action: One of ``"approve"``, ``"edit"``, ``"reject"``.
            timeout: Maximum wait time in milliseconds.
        """
        self.open_hitl_node_route_select(action, timeout=timeout)
        names = self.get_open_listbox_option_names()
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(200)
        return names

    def open_hitl_node_edit_state_key_select(self, timeout: int = 5000) -> None:
        """Open the HITL node's EDIT STATE KEY Value select."""
        self.hitl_node_edit_state_key_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_hitl_node_edit_state_key(self, variable_name: str, timeout: int = 5000) -> None:
        """Select *variable_name* in the EDIT STATE KEY Value select."""
        self.open_hitl_node_edit_state_key_select(timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(variable_name)).click(timeout=timeout)

    def get_hitl_node_edit_state_key_value(self, timeout: int = 5000) -> str:
        """Read the EDIT STATE KEY Value select's current display text."""
        self.hitl_node_edit_state_key_select.wait_for(state="visible", timeout=timeout)
        text = (self.hitl_node_edit_state_key_select.text_content() or "").replace("​", "")
        return text.strip()

    # ------------------------------------------------------------------
    # Chat HITL runtime actions (ELITEA-2015)
    # ------------------------------------------------------------------

    def wait_for_chat_hitl_actions_panel(self, timeout: int = 30000) -> None:
        """Wait for the chat's HITL pause card (Approve/Edit/Reject) to appear."""
        self.chat_hitl_actions_panel.wait_for(state="visible", timeout=timeout)

    def click_chat_hitl_approve(self, timeout: int = 10000) -> None:
        """Click the Approve button on the chat's HITL pause card."""
        self.chat_hitl_approve_button.click(timeout=timeout)

    def click_chat_hitl_reject(self, timeout: int = 10000) -> None:
        """Click the Reject button on the chat's HITL pause card."""
        self.chat_hitl_reject_button.click(timeout=timeout)

    @contextmanager
    def capture_websocket_frames(self):
        """Context manager that captures socket.io event frames while open.

        **Must be entered BEFORE the page navigates** (before
        :meth:`navigate` / any ``page.goto``) — Playwright's ``"websocket"``
        page event fires once, at connection-open time; a listener attached
        after the connection is already open never fires (confirmed live:
        an attempt to enter this context manager mid-test, after
        navigation, captured zero frames for the rest of the test). Enter it
        once per test and keep the whole flow inside it; use snapshot
        indices (``len(frames)`` before/after an action) to slice out the
        frames a specific step cares about — do NOT re-enter the context
        manager mid-test expecting a fresh capture window.

        Yields a list that accumulates one dict per application-level
        socket.io EVENT frame (Engine.IO type ``4`` + Socket.IO type ``2``,
        i.e. the ``42["event_name", {...}]`` wire shape), in arrival order.
        Each dict is the event's payload (or ``{"_value": payload}`` if the
        payload isn't itself a dict) plus ``event`` (the socket.io event
        name, e.g. ``"chat_predict"`` / ``"chat_continue_predict"``) and
        ``_direction`` (``"sent"`` or ``"received"``). Non-event frames
        (ping/pong/connect acks, raw ``{"type": "ping"}`` keepalives) are
        silently skipped.

        This project's existing tests read chat content via the DOM; HITL
        resume behavior (ELITEA-2015) is only diagnosable via the raw
        socket.io frames — new infrastructure per AFS Automation Hints, not
        present elsewhere in the codebase.

        Example:
            with pipeline_page.capture_websocket_frames() as frames:
                pipeline_page.navigate(pipeline_id)
                pipeline_page.wait_for_canvas()
                pipeline_page.send_message_in_embedded_chat("Hello")
                pipeline_page.wait_for_chat_hitl_actions_panel()
                before = len(frames)
                pipeline_page.click_chat_hitl_approve()
                pipeline_page.page.wait_for_timeout(5000)
                approve_frames = frames[before:]
            assert any(
                f["event"] == "chat_predict" and f.get("type") == "agent_response"
                for f in approve_frames
            )
        """
        frames: list = []

        def _parse_socketio_event(payload):
            """Return (event_name, payload_dict_or_value) or None.

            Only the ``42[...]`` shape (Engine.IO message + Socket.IO event)
            carries application events; ping/pong/connect frames don't
            match the prefix and are skipped.
            """
            if not isinstance(payload, str) or not payload.startswith("42"):
                return None
            rest = payload[2:]
            if rest.startswith("/"):  # optional namespace prefix, e.g. "/ns,"
                comma = rest.find(",")
                if comma == -1:
                    return None
                rest = rest[comma + 1:]
            try:
                data = json.loads(rest)
            except (ValueError, TypeError):
                return None
            if not isinstance(data, list) or not data:
                return None
            event_name = data[0]
            event_payload = data[1] if len(data) > 1 else None
            return event_name, event_payload

        def _record(direction):
            def _handler(payload):
                parsed = _parse_socketio_event(payload)
                if parsed is None:
                    return
                event_name, event_payload = parsed
                record = dict(event_payload) if isinstance(event_payload, dict) else {"_value": event_payload}
                record["event"] = event_name
                record["_direction"] = direction
                frames.append(record)

            return _handler

        def _on_websocket(ws):
            ws.on("framesent", _record("sent"))
            ws.on("framereceived", _record("received"))

        self.page.on("websocket", _on_websocket)
        try:
            yield frames
        finally:
            self.page.remove_listener("websocket", _on_websocket)
