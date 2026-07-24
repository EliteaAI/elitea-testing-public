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

from components.mui import Dialog, Popper
from playwright.sync_api import Locator, Page, expect

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

    # Entry-point node — Trigger select & Webhook settings modal (ELITEA-2006).
    # Rendered inline on whichever node card IS the pipeline's entry point
    # (NodeCard.jsx: `isEntrypoint && <TriggerTypeSelector>`) — page-wide (not
    # scoped to a specific node container), same convention as the MCP node
    # fields above: correct as long as a test only has a single entry-point
    # node on canvas.
    trigger_select = LocatorDescriptor(
        testid="pipeline-trigger-select",
        description="Entry-point node's Trigger select (Chat Message/Schedule/Webhook)"
    )

    trigger_webhook_edit_button = LocatorDescriptor(
        testid="pipeline-trigger-webhook-edit-button",
        description='"Edit webhook settings" link-icon button next to the Trigger '
                     "select, rendered only once trigger=webhook"
    )

    webhook_modal = LocatorDescriptor(
        testid="pipeline-webhook-modal",
        description="Webhook settings modal (dialog root)"
    )

    webhook_type_radio_github = LocatorDescriptor(
        testid="pipeline-webhook-type-radio-github",
        description="Webhook Type radio — GitHub option"
    )
    webhook_type_radio_gitlab = LocatorDescriptor(
        testid="pipeline-webhook-type-radio-gitlab",
        description="Webhook Type radio — GitLab option"
    )
    webhook_type_radio_custom = LocatorDescriptor(
        testid="pipeline-webhook-type-radio-custom",
        description="Webhook Type radio — Custom option"
    )

    # AFS Concrete Handles gap fill (implementer Phase 2 — case steps 3/4/5
    # explicitly require verifying description text presence/content, but the
    # AFS table didn't carry a handle for it): added via add-data-testid
    # alongside the rest of this modal's testids, same call site edit.
    webhook_type_description = LocatorDescriptor(
        testid="pipeline-webhook-type-description",
        description="Webhook Type description text (changes per selected type)"
    )
    webhook_payload_format_description = LocatorDescriptor(
        testid="pipeline-webhook-payload-format-description",
        description="Payload Format description (static text)"
    )
    webhook_secret_helper_text = LocatorDescriptor(
        testid="pipeline-webhook-secret-helper-text",
        description="Secret Value helper text (e.g. 'Enter this secret in your "
                     "GitHub webhook configuration under Secret')"
    )

    webhook_url_input = LocatorDescriptor(
        testid="pipeline-webhook-url-input",
        description="Webhook URL read-only field — testid wired via MUI's own "
                     "inputProps mechanism, lands directly on the native <input> "
                     "(established codebase pattern, e.g. agent-instructions-input)"
    )
    webhook_url_copy_button = LocatorDescriptor(
        testid="pipeline-webhook-url-copy-button",
        description="Webhook URL copy button"
    )
    webhook_secret_input = LocatorDescriptor(
        testid="pipeline-webhook-secret-input",
        description="Secret Value masked field — same inputProps testid wiring as "
                     "webhook_url_input, lands on the native <input>"
    )
    webhook_secret_toggle_visibility_button = LocatorDescriptor(
        testid="pipeline-webhook-secret-toggle-visibility-button",
        description="Secret Value eye (show/hide) button"
    )
    webhook_secret_copy_button = LocatorDescriptor(
        testid="pipeline-webhook-secret-copy-button",
        description="Secret Value copy button"
    )
    webhook_secret_regenerate_button = LocatorDescriptor(
        testid="pipeline-webhook-secret-regenerate-button",
        description="Secret Value regenerate (refresh) button — stages a pending secret "
                     "client-side until Apply is clicked"
    )
    webhook_example_request = LocatorDescriptor(
        testid="pipeline-webhook-example-request",
        description="Example Request code block"
    )
    webhook_example_copy_button = LocatorDescriptor(
        testid="pipeline-webhook-example-copy-button",
        description="Example Request copy button"
    )
    webhook_cancel_button = LocatorDescriptor(
        testid="pipeline-webhook-cancel-button",
        description="Webhook settings modal Cancel button"
    )
    webhook_apply_button = LocatorDescriptor(
        testid="pipeline-webhook-apply-button",
        description="Webhook settings modal Apply button"
    )

    # Entry-point node — Schedule settings modal (ELITEA-2005). Sibling of the
    # Webhook settings modal above, added via the same add-data-testid pass
    # (PipelineScheduleModal.jsx — Modal.BaseModal `data-testid` prop, same
    # mechanism as pipeline-webhook-modal).
    schedule_modal = LocatorDescriptor(
        testid="pipeline-schedule-modal",
        description="Schedule settings modal (dialog root)"
    )
    schedule_modal_summary_text = LocatorDescriptor(
        testid="pipeline-schedule-modal-summary-text",
        description='Schedule modal cron summary text (e.g. "At 00:00, only on Saturday")'
    )
    schedule_apply_button = LocatorDescriptor(
        testid="pipeline-schedule-apply-button",
        description="Schedule settings modal Apply button"
    )

    # Entry-point node — Schedule settings modal internals (ELITEA-2007).
    # Sibling gap-fill on top of ELITEA-2005's 3 fields above — same
    # add-data-testid pass, same PipelineScheduleModal.jsx call site.
    trigger_schedule_edit_button = LocatorDescriptor(
        testid="pipeline-trigger-schedule-edit-button",
        description='"Edit schedule" icon button next to the Trigger select, '
                     "rendered only once trigger=schedule (sibling of "
                     "trigger_webhook_edit_button)"
    )
    schedule_mode_radio_default = LocatorDescriptor(
        testid="pipeline-schedule-mode-radio-default",
        description="Schedule modal mode radio — Default option"
    )
    schedule_mode_radio_advanced = LocatorDescriptor(
        testid="pipeline-schedule-mode-radio-advanced",
        description="Schedule modal mode radio — Advanced option"
    )
    schedule_cancel_button = LocatorDescriptor(
        testid="pipeline-schedule-cancel-button",
        description="Schedule settings modal Cancel button"
    )
    schedule_cron_input = LocatorDescriptor(
        testid="pipeline-schedule-modal-cron-input",
        description="Advanced-mode raw cron expression input — testid wired via "
                     "FormInput's inputProps mechanism, lands directly on the "
                     "native <input> (same convention as webhook_url_input / "
                     "webhook_secret_input, no locator chaining needed)"
    )

    # Default-mode Cron fields (react-js-cron ^5.2.0) — third-party npm
    # dependency; testids are baked into the library itself, not app code
    # (on-main already, per AFS Concrete Handles). `period` is a plain
    # single-select; `week-days`/`hours`/`minutes` are ant-design
    # MULTI-selects — see _set_cron_multiselect_value().
    schedule_period_select = LocatorDescriptor(
        testid="select-period",
        description='Schedule modal "Every" period select (react-js-cron, single-select)'
    )
    schedule_week_days_select = LocatorDescriptor(
        testid="custom-select-week-days",
        description='Schedule modal "on" day-of-week select (react-js-cron, '
                     "week period only — unmounts entirely for other periods)"
    )
    schedule_hours_select = LocatorDescriptor(
        testid="custom-select-hours",
        description="Schedule modal hour select (react-js-cron, MULTI-select)"
    )
    schedule_minutes_select = LocatorDescriptor(
        testid="custom-select-minutes",
        description="Schedule modal minute select (react-js-cron, MULTI-select)"
    )

    # react-js-cron's Default-mode option popups (period/hours/minutes/
    # week-days) render via antd's own portal (getPopupContainer defaults to
    # document.body) — NOT as a DOM descendant of the trigger element, so a
    # popup can't be reached via `self.trigger.locator(...)`. DECLARED
    # IMPROVISATION (role-overrides.md § Declared-improvisation protocol):
    # the canon's two sanctioned #579 shapes both assume descendant-chaining
    # off a testid parent (e.g. CodeMirror per-line divs inside
    # raw_json_editor_content); a portalled popup has no such DOM
    # relationship. The library instead tags each field's popup with a
    # STABLE, field-specific class `react-js-cron-select-dropdown-{type}`
    # (confirmed live, ELITEA-2007 exploration) — used here as the closest
    # spirit-compliant equivalent: the "parent" is the field's own real
    # testid trigger (schedule_period_select / schedule_hours_select /
    # schedule_minutes_select / schedule_week_days_select), and the popup is
    # scoped by the ONE class value that library ties 1:1 to that exact
    # field, never a free-floating `.ant-select-dropdown` page-wide handle.
    # A closed dropdown stays MOUNTED with an added `ant-select-dropdown-
    # hidden` class instead of being removed (confirmed live) —
    # `:not(.ant-select-dropdown-hidden)` is required so a stale prior
    # dropdown is never matched (AFS Automation Hints' documented scoping
    # gotcha). Option rows themselves (`.ant-select-item-option`) carry no
    # testid — third-party antd render, library-internal — same sanctioned
    # shape as the CodeMirror per-line divs.
    CRON_FIELD_DROPDOWN = '.react-js-cron-select-dropdown-{}:not(.ant-select-dropdown-hidden)'

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
    # Entry-point node — Trigger select & Webhook settings modal (ELITEA-2006)
    # ------------------------------------------------------------------

    # Maps the Webhook Type radio's value to its LocatorDescriptor field —
    # avoids a dynamic-testid template for a fixed 3-value set (matches the
    # 3 values TriggerTypeSelector.jsx / PipelineWebhookModal.jsx render).
    _WEBHOOK_TYPE_RADIOS = {
        "github": "webhook_type_radio_github",
        "gitlab": "webhook_type_radio_gitlab",
        "custom": "webhook_type_radio_custom",
    }

    def select_trigger_type(self, value: str, timeout: int = 10000) -> dict | None:
        """Open the entry-point node's Trigger select and choose *value*.

        Selecting ``"webhook"`` or ``"chat_message"`` fires a `PUT
        .../pipeline_trigger/.../trigger` immediately — this waits on that
        response, not a fixed sleep (`.claude/rules/ui-tests.md` § Wait
        Patterns). Selecting ``"webhook"`` additionally opens the Webhook
        settings modal as a product side-effect once the response resolves
        (source-confirmed `handleTriggerTypeChange`'s awaited `updateTrigger`
        call, `TriggerTypeSelector.jsx`) — callers wait on ``webhook_modal``
        separately after this returns.

        Selecting ``"schedule"`` is DIFFERENT (ELITEA-2005, source-confirmed):
        `handleTriggerTypeChange` only calls `setIsScheduleModalOpen(true)` —
        a synchronous local-state update, no awaited mutation — so no PUT
        fires until the Schedule modal's own Apply is clicked. This method
        returns ``None`` for ``"schedule"`` rather than waiting on a response
        that will never arrive; callers wait on ``schedule_modal`` separately.

        Args:
            value: One of ``"chat_message"``, ``"schedule"``, ``"webhook"``.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the trigger-update PUT response, or ``None``
            when *value* is ``"schedule"`` (no auto-save on selection).
        """
        self.trigger_select.click(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(value))
        option.wait_for(state="visible", timeout=timeout)

        if value == "schedule":
            option.click(timeout=timeout)
            return None

        with self.page.expect_response(
            lambda r: "/pipeline_trigger/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            option.click(timeout=timeout)

        return response_info.value.json()

    def get_trigger_type_value(self, timeout: int = 5000) -> str:
        """Read the Trigger select's currently-displayed value text.

        Args:
            timeout: Maximum wait time for the select to be visible.
        """
        self.trigger_select.wait_for(state="visible", timeout=timeout)
        return (self.trigger_select.text_content() or "").strip()

    def open_webhook_settings(self, timeout: int = 10000) -> None:
        """Click the "Edit webhook settings" icon and wait for the modal to load.

        Only visible once ``trigger == "webhook"`` (source-confirmed
        `currentTriggerType === TRIGGER_TYPES.webhook` gate,
        `TriggerTypeSelector.jsx`) — call :meth:`select_trigger_type` with
        ``"webhook"`` first if the trigger isn't already webhook.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.trigger_webhook_edit_button.click(timeout=timeout)
        self.wait_for_webhook_settings_loaded(timeout=timeout)

    def wait_for_webhook_settings_loaded(self, timeout: int = 10000) -> None:
        """Wait for the Webhook settings modal AND its data-dependent fields.

        The URL/Secret sections (`PipelineWebhookModal.jsx`: `{webhookUrl &&
        (...)}` / `{secretValue && (...)}`) render only once `triggerData` is
        populated. `triggerData` comes from the SAME RTK-Query tag a
        trigger-mutating PUT invalidates, whose re-fetch can resolve slightly
        AFTER the PUT response itself — so the modal can become visible
        before its fields do. Waits on the Webhook URL field specifically
        (present whenever `webhook_url` is populated) rather than a fixed
        sleep.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.webhook_modal.wait_for(state="visible", timeout=timeout)
        self.webhook_url_input.wait_for(state="visible", timeout=timeout)

    def select_webhook_type(self, webhook_type: str, timeout: int = 5000) -> None:
        """Click the Webhook Type radio matching *webhook_type* in the open modal.

        Pure client-side `useMemo` derivation of the URL/description/example
        request off ``selectedWebhookType`` — no network wait needed
        (source-confirmed `PipelineWebhookModal.jsx`).

        Args:
            webhook_type: One of ``"github"``, ``"gitlab"``, ``"custom"``.
            timeout: Maximum wait time in milliseconds.
        """
        radio = getattr(self, self._WEBHOOK_TYPE_RADIOS[webhook_type])
        radio.click(timeout=timeout)

    def get_selected_webhook_type(self) -> str | None:
        """Return which Webhook Type radio is currently checked, or None.

        The testid lands on the MUI ``FormControlLabel`` wrapping the native
        ``<input type="radio">`` (not the input itself) — same
        already-verified pattern as
        ``CredentialCreatePage.auth_radio``: Playwright's ``is_checked()``
        resolves correctly through the associated ``<label>`` wrapper.
        """
        for webhook_type, attr_name in self._WEBHOOK_TYPE_RADIOS.items():
            if getattr(self, attr_name).is_checked():
                return webhook_type
        return None

    def get_webhook_url(self, timeout: int = 5000) -> str:
        """Read the Webhook URL field's current value.

        Args:
            timeout: Maximum wait time for the field to be visible.
        """
        self.webhook_url_input.wait_for(state="visible", timeout=timeout)
        return self.webhook_url_input.input_value()

    def reveal_webhook_secret(self, timeout: int = 5000) -> None:
        """Click the Secret Value eye (show/hide) toggle button.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.webhook_secret_toggle_visibility_button.click(timeout=timeout)

    def get_webhook_secret(self, timeout: int = 5000) -> str:
        """Read the Secret Value field's current value (masked or revealed).

        Args:
            timeout: Maximum wait time for the field to be visible.
        """
        self.webhook_secret_input.wait_for(state="visible", timeout=timeout)
        return self.webhook_secret_input.input_value()

    def apply_webhook_settings(self, timeout: int = 10000) -> dict:
        """Click Apply in the Webhook settings modal; wait for the trigger PUT.

        Waits on the actual `PUT .../pipeline_trigger/.../trigger` network
        response rather than the modal merely closing.
        `PipelineWebhookModal.applyChanges` calls `onSubmit(...)` (a Promise,
        NOT awaited) and then `onClose()` synchronously — the modal-hidden
        state can be reached before the mutation actually resolves, so a
        wait keyed only on visibility would race the real persistence
        (declared improvisation departing from this case's own AFS
        Automation Hints, which assumed the mutation was awaited before
        close — source-verified during implementation that it is not;
        `role-overrides.md` § Declared-improvisation protocol).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the trigger-update PUT response.
        """
        with self.page.expect_response(
            lambda r: "/pipeline_trigger/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            self.webhook_apply_button.click(timeout=timeout)
        self.webhook_modal.wait_for(state="hidden", timeout=timeout)
        return response_info.value.json()

    def cancel_webhook_settings(self, timeout: int = 10000) -> None:
        """Click Cancel in the Webhook settings modal; wait for it to close.

        Discards any in-modal changes without persisting — `onClose()` is a
        pure local state update (no network call), so waiting on the modal
        becoming hidden is sufficient here (unlike :meth:`apply_webhook_settings`).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.webhook_cancel_button.click(timeout=timeout)
        self.webhook_modal.wait_for(state="hidden", timeout=timeout)

    def wait_for_schedule_settings_loaded(self, timeout: int = 10000) -> None:
        """Wait for the Schedule settings modal to be visible.

        Unlike the Webhook modal, the Schedule modal's content is pure local
        component state (`cronExpression`/`cronType`, defaulted from the
        `cron` prop) — nothing here waits on a network refetch, so waiting
        on the modal root is sufficient.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.schedule_modal.wait_for(state="visible", timeout=timeout)

    def get_schedule_summary_text(self, timeout: int = 5000) -> str:
        """Read the Schedule modal's cron summary text (e.g. "At 00:00, only on Saturday").

        Args:
            timeout: Maximum wait time for the element to be visible.
        """
        self.schedule_modal_summary_text.wait_for(state="visible", timeout=timeout)
        return (self.schedule_modal_summary_text.text_content() or "").strip()

    def apply_schedule_settings(self, timeout: int = 10000) -> dict:
        """Click Apply in the Schedule settings modal; wait for the trigger PUT.

        `PipelineScheduleModal.applyChanges` calls `onSubmit(cronExpression)`
        (a Promise, NOT awaited) then `onClose()` synchronously — same
        close-before-mutation-resolves shape already confirmed for the
        Webhook modal's Apply (see :meth:`apply_webhook_settings`), so this
        waits on the actual `PUT .../pipeline_trigger/.../trigger` response
        rather than the modal merely closing.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the trigger-update PUT response.
        """
        with self.page.expect_response(
            lambda r: "/pipeline_trigger/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            self.schedule_apply_button.click(timeout=timeout)
        self.schedule_modal.wait_for(state="hidden", timeout=timeout)
        return response_info.value.json()

    # ------------------------------------------------------------------
    # Entry-point node — Schedule settings modal internals (ELITEA-2007)
    # ------------------------------------------------------------------

    def open_schedule_settings(self, timeout: int = 10000) -> None:
        """Click the "Edit schedule" icon and wait for the modal to load.

        Only visible once ``trigger == "schedule"`` (mirrors
        :meth:`open_webhook_settings` — source-confirmed
        `currentTriggerType === TRIGGER_TYPES.schedule` gate,
        `TriggerTypeSelector.jsx`). Call :meth:`select_trigger_type` with
        ``"schedule"`` first if the trigger isn't already schedule.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.trigger_schedule_edit_button.click(timeout=timeout)
        self.wait_for_schedule_settings_loaded(timeout=timeout)

    def cancel_schedule_settings(self, timeout: int = 10000) -> None:
        """Click Cancel in the Schedule settings modal; wait for it to close.

        Discards any in-modal changes without persisting — `onClose()` is a
        pure local state update (no network call), mirrors
        :meth:`cancel_webhook_settings`.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.schedule_cancel_button.click(timeout=timeout)
        self.schedule_modal.wait_for(state="hidden", timeout=timeout)

    # Maps the Schedule mode radio's value to its LocatorDescriptor field —
    # same shape as _WEBHOOK_TYPE_RADIOS (fixed 2-value set, same shared
    # RadioButtonGroup component).
    _SCHEDULE_MODE_RADIOS = {
        "default": "schedule_mode_radio_default",
        "advanced": "schedule_mode_radio_advanced",
    }

    def select_schedule_mode(self, mode: str, timeout: int = 5000) -> None:
        """Click the mode radio ("default" or "advanced") in the open Schedule modal.

        Pure client-side state toggle (`cronType`) — no network wait needed,
        mirrors :meth:`select_webhook_type`.

        Args:
            mode: One of "default", "advanced".
            timeout: Maximum wait time in milliseconds.
        """
        radio = getattr(self, self._SCHEDULE_MODE_RADIOS[mode])
        radio.click(timeout=timeout)

    def get_selected_schedule_mode(self) -> str | None:
        """Return which Schedule mode radio is currently checked, or None.

        Mirrors :meth:`get_selected_webhook_type` — same
        `RadioButtonGroup`-wrapped-native-radio `is_checked()` mechanism.
        """
        for mode, attr_name in self._SCHEDULE_MODE_RADIOS.items():
            if getattr(self, attr_name).is_checked():
                return mode
        return None

    def get_schedule_cron_expression(self, timeout: int = 5000) -> str:
        """Read the Advanced-mode raw cron expression input's current value.

        Args:
            timeout: Maximum wait time for the field to be visible.
        """
        self.schedule_cron_input.wait_for(state="visible", timeout=timeout)
        return self.schedule_cron_input.input_value()

    def get_schedule_period_value(self, timeout: int = 5000) -> str:
        """Read the Default-mode "Every" period select's current display text.

        Args:
            timeout: Maximum wait time for the select to be visible.
        """
        self.schedule_period_select.wait_for(state="visible", timeout=timeout)
        return (self.schedule_period_select.text_content() or "").strip()

    def get_schedule_hour_value(self, timeout: int = 5000) -> str:
        """Read the Default-mode hour select's current display text (e.g. "09").

        Args:
            timeout: Maximum wait time for the select to be visible.
        """
        self.schedule_hours_select.wait_for(state="visible", timeout=timeout)
        return (self.schedule_hours_select.text_content() or "").strip()

    def get_schedule_minute_value(self, timeout: int = 5000) -> str:
        """Read the Default-mode minute select's current display text (e.g. "30").

        Args:
            timeout: Maximum wait time for the select to be visible.
        """
        self.schedule_minutes_select.wait_for(state="visible", timeout=timeout)
        return (self.schedule_minutes_select.text_content() or "").strip()

    def _open_cron_field_dropdown(self, trigger: Locator, field_type: str, timeout: int) -> Locator:
        """Click *trigger* and return the Locator for its own option popup.

        See :attr:`CRON_FIELD_DROPDOWN` for why this scoping (a stable
        field-specific class, not descendant-chaining) is necessary here.

        Args:
            trigger: The field's own LocatorDescriptor-backed Locator
                (e.g. ``self.schedule_hours_select``).
            field_type: The react-js-cron field-type suffix ("period",
                "hours", "minutes", "week-days").
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator scoped to the currently-open (non-stale) dropdown for
            this specific field.
        """
        trigger.click(timeout=timeout)
        dropdown = self.page.locator(self.CRON_FIELD_DROPDOWN.format(field_type))
        dropdown.wait_for(state="visible", timeout=timeout)
        return dropdown

    def _click_cron_dropdown_option(self, dropdown: Locator, value: str, timeout: int) -> None:
        """Click the option row reading exactly *value* inside an open *dropdown*.

        rc-select/antd renders EACH option TWICE: a zero-size
        (``height:0;width:0;overflow:hidden``) accessibility-only mirror
        carrying ``role="option"``/``aria-label`` (confirmed live,
        ELITEA-2007 implementer exploration — NOT visually rendered, so
        Playwright correctly refuses to click it: "element is not
        visible"), and the REAL visible row inside `.rc-virtual-list`
        (`.ant-select-item-option-content`). Scoping to the
        `.ant-select-item-option-content` class excludes the invisible
        mirror entirely (it lacks that class) — `get_by_text`/`get_by_role`
        both match across BOTH copies and either time out (role picks the
        invisible mirror) or raise a strict-mode violation (text matches
        both the mirror and the nested content div).

        Args:
            dropdown: Locator scoped to one field's open popup (see
                :meth:`_open_cron_field_dropdown`).
            value: Exact option text to click, e.g. "day" or "09".
            timeout: Maximum wait time in milliseconds.
        """
        option = dropdown.locator(".ant-select-item-option-content").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        )
        option.click(timeout=timeout)

    def select_schedule_period(self, value: str, timeout: int = 5000) -> None:
        """Open the "Every" period select and choose *value*.

        Single-select (no `mode` prop passed to react-js-cron's underlying
        antd Select) — clicking an option REPLACES the current value,
        unlike the hour/minute multi-selects below. Choosing "day" hides
        the "on" day-of-week field entirely (source-confirmed: the
        week-days field only mounts for the "year"/"month"/"week" periods).

        Args:
            value: One of "year", "month", "week", "day", "hour", "minute".
            timeout: Maximum wait time in milliseconds.
        """
        dropdown = self._open_cron_field_dropdown(self.schedule_period_select, "period", timeout)
        self._click_cron_dropdown_option(dropdown, value, timeout)

    def _set_cron_multiselect_value(self, trigger: Locator, field_type: str, value: str, timeout: int) -> None:
        """Set an ant-design MULTI-select Cron field to exactly *value*.

        ``custom-select-hours``/``custom-select-minutes`` are ant-design
        MULTI-selects whose default value ("00") is NOT replaced by
        clicking a new option — it is ADDED (confirmed live, AFS Test
        Steps 4/5 + Automation Hints). This opens the dropdown, clicks
        *value* to add it, then clicks "00" to deselect the default —
        leaving exactly *value* selected. Do not call this with
        ``value="00"`` — the default is already "00" with nothing to add,
        and the deselect click would just remove it, leaving no value
        selected.

        Args:
            trigger: The field's own Locator (``self.schedule_hours_select``
                or ``self.schedule_minutes_select``).
            field_type: "hours" or "minutes".
            value: Two-digit target value, e.g. "09".
            timeout: Maximum wait time in milliseconds.
        """
        dropdown = self._open_cron_field_dropdown(trigger, field_type, timeout)
        value_row = dropdown.locator(".ant-select-item-option").filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        )
        value_row.locator(".ant-select-item-option-content").click(timeout=timeout)
        # Wait for the ADD to actually register in the clicked OPTION ROW's
        # own selection-state class before clicking to deselect "00".
        expect(value_row).to_have_class(re.compile(r"\bant-select-item-option-selected\b"), timeout=timeout)

        zero_row = dropdown.locator(".ant-select-item-option").filter(has_text=re.compile(r"^00$"))
        zero_content = zero_row.locator(".ant-select-item-option-content")
        # Click-and-verify with a bounded retry, not a single fire-and-forget
        # click. Confirmed live (ELITEA-2007 implementer exploration) that a
        # single deselect click on "00" can occasionally leave BOTH values
        # selected — reproduced deterministically under pytest's context
        # (which always records video via a CDP screencast, per conftest.py's
        # `context` fixture) while the identical sequence passed standalone
        # without video recording. The screencast's extra CDP traffic shifts
        # this third-party widget's render timing just enough to occasionally
        # miss the click's intended target update. This loop is a condition
        # check + bounded retry against the OBSERVABLE result (the trigger's
        # own displayed value), not a blind sleep and not defect-masking —
        # it fails loudly via the final `expect()` if genuinely broken.
        for _ in range(3):
            zero_content.click(timeout=timeout)
            try:
                expect(trigger).to_have_text(value, timeout=1500)
                return
            except AssertionError:
                continue
        expect(trigger).to_have_text(value, timeout=timeout)

    def set_schedule_hour(self, value: str, timeout: int = 5000) -> None:
        """Set the Default-mode hour select to exactly *value* (e.g. "09").

        See :meth:`_set_cron_multiselect_value` for the deselect-the-default
        mechanism this requires.

        Args:
            value: Two-digit hour string, e.g. "09".
            timeout: Maximum wait time in milliseconds.
        """
        self._set_cron_multiselect_value(self.schedule_hours_select, "hours", value, timeout)

    def set_schedule_minute(self, value: str, timeout: int = 5000) -> None:
        """Set the Default-mode minute select to exactly *value* (e.g. "30").

        See :meth:`_set_cron_multiselect_value` for the deselect-the-default
        mechanism this requires. Passing through an intermediate two-value
        state (e.g. "00,30") may transiently show the "Frequency cannot be
        less than every hour" validation message if the hour field is also
        narrow at that instant — correct guard-rail behavior, not a defect
        (AFS Test Step 5 / Known Findings); it clears once this method
        finishes (exactly one value selected).

        Args:
            value: Two-digit minute string, e.g. "30".
            timeout: Maximum wait time in milliseconds.
        """
        self._set_cron_multiselect_value(self.schedule_minutes_select, "minutes", value, timeout)

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
