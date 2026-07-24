"""Pipeline detail page object for pipeline detail/edit operations.

Extends PipelineFormPage with additional functionality:
- Tabs (Configuration, History)
- Actions menu (delete, export, fork)
- YAML/Flow view toggle
- ReactFlow canvas node management
- Embedded chat

URL: /pipelines/all/{id}
"""

import logging
import re
import time
from playwright.sync_api import Page, Locator
from .pipeline_form_page import PipelineFormPage
from .locator_descriptor import LocatorDescriptor
from components.mui import Dialog, Popper

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
        description="YAML CodeMirror editor lines (for preserving line breaks)"
    )

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

    # Router node inline config fields (ELITEA-2033). Testid-only, added via
    # add-data-testid — RouterNode.jsx only renders these on router-type
    # nodes. Page-wide (not scoped to a specific node container): correct as
    # long as a test only has a single Router node on canvas (same
    # convention as the MCP/LLM/HITL node fields above).
    router_node_condition_input = LocatorDescriptor(
        testid="pipeline-router-node-condition-input",
        description="Router node's Condition Jinja-template textarea"
    )

    router_node_routes_select = LocatorDescriptor(
        testid="pipeline-router-node-routes-select",
        description="Router node's Routes multi-select (other node ids + END)"
    )

    router_node_input_select = LocatorDescriptor(
        testid="pipeline-router-node-input-select",
        description="Router node's Input state-variable multi-select"
    )

    router_node_default_output_select = LocatorDescriptor(
        testid="pipeline-router-node-default-output-select",
        description="Router node's Default output single-select"
    )

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
        newlines, so we use yaml_lines descriptor to extract each line
        and join with newlines.

        Returns:
            The text content of the YAML editor with preserved line breaks.
        """
        self.yaml_editor.wait_for(state="visible", timeout=5000)
        line_count = self.yaml_lines.count()
        if line_count == 0:
            return self.yaml_editor.text_content() or ""
        return "\n".join(self.yaml_lines.nth(i).text_content() or "" for i in range(line_count))

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
    # Router node inline config (ELITEA-2033)
    # ------------------------------------------------------------------

    def set_router_condition(self, jinja_text: str, timeout: int = 5000) -> None:
        """Type *jinja_text* into the Router node's Condition textarea.

        A plain native ``<textarea name="condition">`` (not CodeMirror), so
        ordinary press_sequentially() is sufficient — no autocomplete-popper
        gotchas apply here (ELITEA-2033 AFS Automation Hints).

        Args:
            jinja_text: The Jinja condition template to type verbatim.
            timeout: Maximum wait time for the field to be visible.
        """
        field = self.router_node_condition_input
        field.wait_for(state="visible", timeout=timeout)
        field.click(timeout=timeout)
        field.press_sequentially(jinja_text, delay=10)

    def get_router_condition(self, timeout: int = 5000) -> str:
        """Read the Router node's Condition textarea's current value."""
        self.router_node_condition_input.wait_for(state="visible", timeout=timeout)
        return self.router_node_condition_input.input_value()

    def select_router_routes(self, node_ids: list[str], timeout: int = 5000) -> None:
        """Open the Router node's Routes multi-select and choose each of *node_ids*.

        Routes is a multi-select (RouteSelect.jsx passes multiple + showBorder)
        that stays open between selections — confirmed live (ELITEA-2033 AFS
        Test Steps 4 / Axis 2), so every target id is clicked in one
        open/close cycle rather than reopening the menu per selection.

        Args:
            node_ids: Target node ids to select (matches
                ``select-option-{node_id}``), e.g. ``["approve", "reject"]``.
            timeout: Maximum wait time for the dropdown / options.
        """
        self.router_node_routes_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)
        for node_id in node_ids:
            self.page.locator(self.SELECT_OPTION.format(node_id)).click(timeout=timeout)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def get_router_routes(self, timeout: int = 5000) -> str:
        """Read the Router node's Routes select's rendered chip text.

        Returns the concatenated text of every selected-route chip (e.g.
        ``"approvereject"`` for two chips with no separator) — sufficient to
        assert membership (``"approve" in text`` / ``"reject" in text"``)
        without needing a per-chip sub-selector.
        """
        self.router_node_routes_select.wait_for(state="visible", timeout=timeout)
        text = (self.router_node_routes_select.text_content() or "").replace("​", "")
        return text.strip()

    def select_router_input(self, value: str, timeout: int = 5000) -> None:
        """Open the Router node's Input select and choose *value*.

        Input is also a multi-select (InputSelect.jsx passes multiple) — an
        explicit Escape close is required afterwards or the leftover MUI
        popover/backdrop intercepts the next click (same gotcha documented
        for the LLM node's Input/Output selects, ELITEA-2004).

        Args:
            value: The state variable name (matches ``select-option-{value}``).
            timeout: Maximum wait time for the dropdown / option.
        """
        self.router_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(value)).click(timeout=timeout)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)

    def get_router_input(self, timeout: int = 5000) -> str:
        """Read the Router node's Input select's rendered chip text."""
        self.router_node_input_select.wait_for(state="visible", timeout=timeout)
        text = (self.router_node_input_select.text_content() or "").replace("​", "")
        return text.strip()

    def select_router_default_output(self, node_id: str, timeout: int = 5000) -> None:
        """Open the Router node's Default output select and choose *node_id*.

        Default output is a single-select (no ``multiple`` prop on this
        ``SingleSelect`` call) — selecting an option auto-closes the menu,
        no explicit Escape needed.

        Args:
            node_id: Target node id, or ``"END"`` (matches
                ``select-option-{node_id}``).
            timeout: Maximum wait time for the dropdown / option.
        """
        self.router_node_default_output_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(node_id)).click(timeout=timeout)

    def get_router_default_output(self, timeout: int = 5000) -> str:
        """Read the Router node's Default output select's current display text.

        NOTE (reverse-masking-guard-relevant, ELITEA-2033 AFS Step 6): a
        freshly-added Router node already DISPLAYS "END" here with zero
        interaction (RouterNode.jsx's client-side ``default_output || 'END'``
        fallback) — this display value alone does NOT prove
        ``default_output: END`` was persisted or that the canvas edge was
        drawn. Callers must corroborate with the YAML view
        (``get_yaml_content()``) and/or ``edge_exists()``, never rely on this
        getter alone to assert persistence.
        """
        self.router_node_default_output_select.wait_for(state="visible", timeout=timeout)
        text = (self.router_node_default_output_select.text_content() or "").replace("​", "")
        return text.strip()

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
