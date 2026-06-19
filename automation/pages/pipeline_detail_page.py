"""Pipeline detail page object for pipeline detail/edit operations.

Extends PipelineFormPage with additional functionality:
- Tabs (Configuration, History)
- Actions menu (delete, export, fork)
- YAML/Flow view toggle
- ReactFlow canvas node management
- Embedded chat

URL: /app/pipelines/all/{id}
"""

import logging
import time
from playwright.sync_api import Page
from .pipeline_form_page import PipelineFormPage
from .locator_descriptor import LocatorDescriptor
from components.mui import Dialog

logger = logging.getLogger("elitea.pages.pipeline_detail")


class PipelineDetailPage(PipelineFormPage):
    """Pipeline detail/edit page.

    Inherits form operations from PipelineFormPage.
    Adds: tabs, actions menu, YAML/Flow toggle, ReactFlow canvas, embedded chat.

    URL: /app/pipelines/all/{id}
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
        testid="pipeline-copy-id",
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
        testid="pipeline-chat-input",
        fallback=lambda page: page.get_by_role("textbox", name="Type your message."),
        description="Embedded chat input field"
    )

    chat_send_button = LocatorDescriptor(
        testid="pipeline-chat-send",
        fallback=lambda page: page.get_by_role("button", name="send your question"),
        description="Embedded chat send button"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, pipeline_id: int):
        """Navigate to pipeline detail page and wait for load.

        Args:
            pipeline_id: The numeric pipeline ID.
        """
        super().navigate(f"/app/pipelines/all/{pipeline_id}?viewMode=owner")
        self.wait_for_detail_page_load()
        logger.info("Navigated to pipeline %d detail page", pipeline_id)

    # ------------------------------------------------------------------
    # Wait methods
    # ------------------------------------------------------------------

    def wait_for_detail_page_load(self, timeout: int = 15000):
        """Wait for the pipeline detail/edit page to fully load.

        Waits for URL to contain /app/pipelines/all/ (not /create), then
        waits for the Name input to have a non-empty value.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=10000)
        # Wait for URL to move away from the create page to the detail page.
        # The create form's input#name already has a value after fill_form(),
        # so checking the input alone would false-positive on the create page.
        self.page.wait_for_function(
            """() => window.location.pathname.includes('/app/pipelines/all/')""",
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

    def is_flow_view_active(self) -> bool:
        """Check if the Flow (ReactFlow canvas) view is currently active.

        Returns:
            True if Flow view is active, False otherwise.
        """
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

    def wait_for_canvas(self, timeout: int = 10000):
        """Wait for the ReactFlow canvas to be visible.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
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

        for line in yaml_text.split("\n"):
            if "entry_point:" in line:
                return line.split("entry_point:")[-1].strip()
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
