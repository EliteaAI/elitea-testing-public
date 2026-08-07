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

    # Information accordion root (agent-information-section, shared with the
    # Agent detail page). Confirmed live (ELITEA-2020): expanded by default
    # on a freshly created pipeline's detail page — no click needed to reveal
    # "Pipeline ID:"/"Version ID:"/"Pipeline:" rows.
    information_section = LocatorDescriptor(
        testid="agent-information-section",
        description="Information accordion (Pipeline ID / Version ID / Pipeline link rows)",
    )

    # VERSION selector in the entity tab bar (ApplicationVersionSelect.jsx,
    # shared with Agents). The testid reaches the DOM via a `testId` PROP —
    # ApplicationVersionSelect.jsx:228 passes `testId="agent-version-
    # selector-trigger"` down to VersionSelect.jsx, which applies it as a
    # SINGLE `data-testid={testId}` on the SingleSelect root (that root
    # itself carries `role="combobox"` — same element, not two). There is
    # NO `-combobox`-suffixed testid anywhere in EliteaUI (repo-wide grep,
    # 2026-08-07 review fix, ELITEA-2020) — the prior claim of "two testids
    # render" was fabricated. Matches AgentDetailPage.version_selector_trigger,
    # which reads this exact shared component the same way.
    version_selector = LocatorDescriptor(
        testid="agent-version-selector-trigger",
        description="VERSION selector — text content is the current version name (e.g. 'base')",
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

    canvas_controls = LocatorDescriptor(
        testid="rf__controls",
        description=(
            "ReactFlow canvas zoom/fit-view control panel (bottom-left, pinned "
            "overlay) — real app testid on the panel container; its individual "
            "buttons are ReactFlow's own third-party internal render (#579 "
            "sanctioned exception, see fit_canvas_view())"
        )
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

    # Sanctioned #579 exception (third-party editor library internal render
    # nodes), sibling to YAML_LINE_SELECTOR above: CodeMirror's line-number
    # gutter (".cm-gutters .cm-lineNumbers .cm-gutterElement") has no
    # data-testid anywhere in the DOM (confirmed live via
    # document.querySelector('.cm-gutters') -> data-testid: null,
    # ELITEA-2026 exploration) — library-internal render, not app JSX.
    # Scoped raw selector under the testid-anchored yaml_editor parent
    # (confirmed live: editorTestidEl.contains(gutter) === true).
    #
    # ":visible" is REQUIRED (confirmed live, ELITEA-2026): CodeMirror
    # renders a hidden, zero-height "spacer" gutterElement FIRST in DOM
    # order (style="height: 0px; visibility: hidden; pointer-events: none;")
    # whose text is a measurement placeholder (e.g. "99" — sized to reserve
    # gutter width for the largest expected line-number digit count), NOT
    # line 1's actual number. Without the visibility filter, .nth(0) reads
    # that spacer instead of the first real line-number element.
    YAML_GUTTER_LINE_SELECTOR = ".cm-gutters .cm-lineNumbers .cm-gutterElement:visible"

    # "Copy yaml code to clipboard" icon button, above the editor next to the
    # Flow/Yaml toggle group (EditorPanel.jsx). New testid added for
    # ELITEA-2026 — the button previously carried only an
    # aria-label/tooltip title, no data-testid.
    copy_yaml_button = LocatorDescriptor(
        testid="pipeline-yaml-copy-button",
        description="Copy yaml code to clipboard icon button (visible only in YAML view)",
    )

    # App-wide toast (Toast.jsx, src/components/Toast.jsx) — shared component,
    # testids pre-exist and need no EliteaUI change (confirmed live, ELITEA-2068).
    # Each page object declares its own field for this shared component per
    # existing repo precedent (ChatPage.toast_alert / ArtifactsPage.
    # success_toast_message / SkillDetailPage.version_toast_message, etc.).
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )

    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body.",
    )

    # Severity-scoped toast alert selector — testid identity + data-severity
    # state filter, the compliant shape for a state-dependent assertion
    # (mirrors ChatPage.TOAST_ALERT_SEVERITY).
    TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'

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

    # Added via add-data-testid for ELITEA-2037 (widened BaseToolNode.jsx's
    # interruptAfterTestId/structuredOutputTestId from Toolkit-only to every
    # node type in TEST_ID_PREFIX_BY_NODE_TYPE — EliteaAI/EliteaUI@00768a44).
    mcp_node_interrupt_after_toggle = LocatorDescriptor(
        testid="pipeline-mcp-node-interrupt-after-toggle",
        description="MCP node's 'Interrupt after' switch (CommonInterruptSettings.jsx)"
    )
    mcp_node_structured_output_toggle = LocatorDescriptor(
        testid="pipeline-mcp-node-structured-output-toggle",
        description="MCP node's 'Structured output' switch (CommonInterruptSettings.jsx)"
    )

    # LLM node inline config (ELITEA-2004). Testid-only, added via
    # add-data-testid — LLMNode.jsx call sites only (SimpleLLMInputs is
    # shared with Code/Printer nodes, which stay untagged — untested node
    # types stay untagged, .agents/testing.md § Locator policy). Page-wide
    # (not scoped to a specific node container): correct as long as a test
    # only has a single LLM node on canvas.
    llm_node_system_type_select = LocatorDescriptor(
        testid="pipeline-llm-node-system-type-select",
        description="LLM node's SYSTEM section Type select (inline on canvas card)"
    )
    llm_node_system_value = LocatorDescriptor(
        testid="pipeline-llm-node-system-value",
        description="LLM node's SYSTEM section Value field"
    )
    llm_node_task_type_select = LocatorDescriptor(
        testid="pipeline-llm-node-task-type-select",
        description="LLM node's TASK section Type select"
    )
    llm_node_task_value = LocatorDescriptor(
        testid="pipeline-llm-node-task-value",
        description="LLM node's TASK section Value field"
    )
    llm_node_chat_history_type_select = LocatorDescriptor(
        testid="pipeline-llm-node-chat-history-type-select",
        description="LLM node's CHAT HISTORY section Type select"
    )
    llm_node_chat_history_value = LocatorDescriptor(
        testid="pipeline-llm-node-chat-history-value",
        description="LLM node's CHAT HISTORY section Value field"
    )
    llm_node_input_select = LocatorDescriptor(
        testid="pipeline-llm-node-input-select",
        description="LLM node's tool-agnostic Input state-variable select"
    )
    llm_node_output_select = LocatorDescriptor(
        testid="pipeline-llm-node-output-select",
        description="LLM node's tool-agnostic Output state-variable select"
    )
    llm_node_toolkits_select = LocatorDescriptor(
        testid="pipeline-llm-node-toolkits-select",
        description="LLM node's Toolkits multi-select (ToolkitsSelect.jsx, LLM-only call site)"
    )
    llm_node_interrupt_after_toggle = LocatorDescriptor(
        testid="pipeline-llm-node-interrupt-after-toggle",
        description="LLM node's 'Interrupt after' switch (CommonInterruptSettings.jsx)"
    )
    llm_node_structured_output_toggle = LocatorDescriptor(
        testid="pipeline-llm-node-structured-output-toggle",
        description="LLM node's 'Structured output' switch (CommonInterruptSettings.jsx)"
    )

    # Entry-point Trigger select (ELITEA-2005/06/07/08 testid prep, first
    # consumed here) — TriggerTypeSelector.jsx renders this unconditionally
    # for whichever node is the pipeline's current entry point, regardless of
    # node type; a fresh empty pipeline's first added node becomes the entry
    # point automatically (FlowEditor.jsx), so it's visible for both the LLM
    # node (ELITEA-2004) and the Toolkit node (ELITEA-2010) cases.
    entry_point_trigger_select = LocatorDescriptor(
        testid="pipeline-entry-point-trigger-select",
        description="Entry-point node's Trigger type select (Chat Message/Schedule/Webhook)"
    )

    # Dynamic (runtime-parameterized) testid — CommonInterruptSettings.jsx's
    # "Interrupt before" toggle is keyed by node id, not node type (ELITEA-2008,
    # unconditional for every node type sharing the component). Class-level
    # template constant per .agents/testing.md § Locator policy, formatted
    # with the node's own `data-id` (as returned by wait_for_node_on_canvas).
    NODE_INTERRUPT_BEFORE_TOGGLE = '[data-testid="pipeline-node-interrupt-before-toggle-{}"]'

    # Toolkit node inline config (ELITEA-2010). Testid-only, added via
    # add-data-testid — BaseToolNode.jsx's node-type -> testid-prefix map now
    # covers both "mcp" (unchanged, pipeline-mcp-node-*) and "toolkit" (new,
    # pipeline-toolkit-node-*). Page-wide (not scoped to a specific node
    # container): correct as long as a test only has a single Toolkit node
    # on canvas.
    toolkit_node_toolkit_select = LocatorDescriptor(
        testid="pipeline-toolkit-node-toolkit-select",
        description="Toolkit node's Toolkit select (inline on the ReactFlow canvas card)"
    )
    toolkit_node_tool_select = LocatorDescriptor(
        testid="pipeline-toolkit-node-tool-select",
        description=(
            "Toolkit node's Tool select — conditionally rendered, absent from "
            "the DOM entirely until a Toolkit with >=1 selected_tools is chosen"
        )
    )
    toolkit_node_input_select = LocatorDescriptor(
        testid="pipeline-toolkit-node-input-select",
        description="Toolkit node's tool-agnostic Input state-variable select"
    )
    toolkit_node_output_select = LocatorDescriptor(
        testid="pipeline-toolkit-node-output-select",
        description="Toolkit node's tool-agnostic Output state-variable select"
    )
    toolkit_node_input_mapping_required_heading = LocatorDescriptor(
        testid="pipeline-toolkit-node-input-mapping-heading",
        description="Toolkit node's 'Input mapping (required N)' accordion heading"
    )
    toolkit_node_input_mapping_optional_heading = LocatorDescriptor(
        testid="pipeline-toolkit-node-input-mapping-optional-heading",
        description="Toolkit node's 'Input mapping (optional N)' accordion heading"
    )
    toolkit_node_interrupt_after_toggle = LocatorDescriptor(
        testid="pipeline-toolkit-node-interrupt-after-toggle",
        description="Toolkit node's 'Interrupt after' switch (CommonInterruptSettings.jsx)"
    )
    toolkit_node_structured_output_toggle = LocatorDescriptor(
        testid="pipeline-toolkit-node-structured-output-toggle",
        description="Toolkit node's 'Structured output' switch (CommonInterruptSettings.jsx)"
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

    # Router node inline config (ELITEA-2033). Testid-only, added via
    # add-data-testid — RouterNode.jsx call sites only (untested node types
    # stay untagged, .agents/testing.md § Locator policy). Page-wide (not
    # scoped to a specific node container): correct as long as a test only
    # has a single Router node on canvas.
    router_node_condition_input = LocatorDescriptor(
        testid="pipeline-router-node-condition-input",
        description="Router node's Condition Jinja textarea (inline on canvas card)"
    )

    router_node_routes_select = LocatorDescriptor(
        testid="pipeline-router-node-routes-select",
        description="Router node's Routes multi-select (existing pipeline node ids + END)"
    )

    router_node_input_select = LocatorDescriptor(
        testid="pipeline-router-node-input-select",
        description="Router node's tool-agnostic Input state-variable select"
    )

    router_node_default_output_select = LocatorDescriptor(
        testid="pipeline-router-node-default-output-select",
        description="Router node's Default output single-select"
    )

    # Decision node inline config (ELITEA-2034). Testid-only, added via
    # add-data-testid — NormalDecisionNode.jsx / DecisionNodeShared.jsx call
    # sites only (untested node types stay untagged, .agents/testing.md §
    # Locator policy). Page-wide (not scoped to a specific node container):
    # correct as long as a test only has a single Decision node on canvas.
    decision_node_input_select = LocatorDescriptor(
        testid="pipeline-decision-node-input-select",
        description="Decision node's tool-agnostic Input state-variable multi-select"
    )

    decision_node_description_input = LocatorDescriptor(
        testid="pipeline-decision-node-description-input",
        description="Decision node's Description textarea (classification prompt)"
    )

    decision_node_outputs_container = LocatorDescriptor(
        testid="pipeline-decision-node-outputs-container",
        description="Decision node's DECISION OUTPUTS chip-list container"
    )

    decision_node_interrupt_after_toggle = LocatorDescriptor(
        testid="pipeline-decision-node-interrupt-after-toggle",
        description="Decision node's Interrupt after switch"
    )

    decision_node_output_handle = LocatorDescriptor(
        testid="pipeline-decision-node-output-handle",
        description="Decision node's Output (DECISION OUTPUTS wiring) source handle — visible label reads 'Output'"
    )

    decision_node_default_output_handle = LocatorDescriptor(
        testid="pipeline-decision-node-default-output-handle",
        description="Decision node's Default output source handle — visible label reads 'Default output'"
    )

    # STATE side panel — add-custom-variable flow (ELITEA-2034). Page-wide.
    state_drawer_toggle_button = LocatorDescriptor(
        testid="pipeline-state-drawer-toggle-button",
        description="Collapsed-state 'State' button that opens the STATE side panel"
    )

    state_add_variable_button = LocatorDescriptor(
        testid="pipeline-state-add-variable-button",
        description="STATE panel's '+ Context' button (starts a new custom state variable row)"
    )

    state_add_variable_name_input = LocatorDescriptor(
        testid="pipeline-state-add-variable-name-input",
        description="STATE panel's new-variable name textbox (create mode only)"
    )

    state_drawer_close_button = LocatorDescriptor(
        testid="pipeline-state-drawer-close-button",
        description="STATE panel's close ('x') button"
    )

    # Dynamic (runtime-parameterized) testids — one per STATE panel row,
    # keyed by variable name (ELITEA-2042). Class-level template constants
    # per .agents/testing.md § Locator policy, formatted with test-generated
    # data only at the call site. Added via add-data-testid,
    # EliteaAI/EliteaUI@d120871f (StateVariableItem.jsx / StateVariableItemActions.jsx
    # / StateTypeSelector.jsx / StateVariableIconButton.jsx).
    STATE_VARIABLE_NAME = '[data-testid="pipeline-state-variable-name-{}"]'
    STATE_VARIABLE_TOGGLE = '[data-testid="pipeline-state-variable-toggle-{}"]'
    STATE_VARIABLE_DELETE = '[data-testid="pipeline-state-variable-delete-{}"]'
    STATE_VARIABLE_TYPE_SELECT = '[data-testid="pipeline-state-variable-type-select-{}"]'

    # Static per INTERNAL type value (StateTypeSelector.jsx's Menu items) —
    # NOT the display label. `flowEditor.constants.js`'s `StateVariableTypes`
    # maps String->str, Number->number, List->list, Json->dict (the 4th
    # option's display label "Json" != its internal/YAML value "dict").
    STATE_TYPE_OPTION = '[data-testid="pipeline-state-type-option-{}"]'

    # Dynamic (runtime-parameterized) testid — one chip per DECISION OUTPUTS
    # entry. Class-level template constants per .agents/testing.md § Locator
    # policy: an exact-match template for a known value, and a prefix
    # selector (same convention as SELECT_OPTION / SELECT_OPTION_PREFIX
    # below) for enumerating every rendered chip regardless of value.
    DECISION_NODE_OUTPUT_CHIP = '[data-testid="pipeline-decision-node-output-chip-{}"]'
    DECISION_NODE_OUTPUT_CHIP_PREFIX = '[data-testid^="pipeline-decision-node-output-chip-"]'

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

    # Dynamic (runtime-parameterized) testid — one "Interrupt before" toggle
    # per node (CommonInterruptSettings.jsx, rendered inline on every node
    # type). Class-level template constant per .agents/testing.md § Locator
    # policy, formatted with the target node's id at the call site. Added via
    # add-data-testid, EliteaAI/EliteaUI@a2ce4732 (ELITEA-2008). "Before" was
    # chosen over "after": `disabled={yamlNode?.transition === End || ...}`
    # makes "after" unusable on a freshly-added, unconnected node (pipeline
    # auto-wires new nodes to END, confirmed live) — "before" only disables
    # for the SAVED entry point (`entry_point === id`), which a non-entry-point
    # node never is.
    NODE_INTERRUPT_BEFORE_TOGGLE = '[data-testid="pipeline-node-interrupt-before-toggle-{}"]'

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

    # Entry-point node — Trigger select & Webhook/Schedule settings modals
    # (ELITEA-2005/2006/2007/2008). Rendered inline on whichever node card IS
    # the pipeline's entry point (NodeCard.jsx: `isEntrypoint &&
    # <TriggerTypeSelector>`) — page-wide (not scoped to a specific node
    # container), same convention as the MCP/HITL node fields above: correct
    # as long as a test only has a single entry-point node on canvas at a
    # time. Added via add-data-testid, EliteaAI/EliteaUI@b43fbce0.
    trigger_select = LocatorDescriptor(
        testid="pipeline-entry-point-trigger-select",
        description="Entry-point node's Trigger select (Chat Message/Schedule/Webhook)"
    )

    trigger_schedule_edit_button = LocatorDescriptor(
        testid="pipeline-entry-point-trigger-schedule-edit-button",
        description='"Edit schedule" clock-icon button next to the Trigger select, '
                     "rendered only while currentTriggerType === 'schedule'"
    )

    webhook_modal = LocatorDescriptor(
        testid="pipeline-webhook-settings-modal",
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
    webhook_type_description = LocatorDescriptor(
        testid="pipeline-webhook-type-description",
        description="Webhook Type description text (changes per selected type)"
    )
    webhook_url_input = LocatorDescriptor(
        testid="pipeline-webhook-url-input",
        description="Webhook URL read-only field — testid wired via FormInput's "
                     "inputProps, lands directly on the native <input>"
    )
    webhook_url_copy_button = LocatorDescriptor(
        testid="pipeline-webhook-url-copy-button",
        description="Webhook URL copy button"
    )
    webhook_secret_input = LocatorDescriptor(
        testid="pipeline-webhook-secret-input",
        description="Secret Value masked/revealed field — same inputProps wiring as "
                     "webhook_url_input"
    )
    webhook_secret_toggle_button = LocatorDescriptor(
        testid="pipeline-webhook-secret-toggle-button",
        description="Secret Value eye (show/hide) button"
    )
    webhook_secret_copy_button = LocatorDescriptor(
        testid="pipeline-webhook-secret-copy-button",
        description="Secret Value copy button"
    )
    webhook_secret_regenerate_button = LocatorDescriptor(
        testid="pipeline-webhook-secret-regenerate-button",
        description="Secret Value regenerate (refresh) button"
    )
    webhook_secret_helper_text = LocatorDescriptor(
        testid="pipeline-webhook-secret-helper-text",
        description="Secret Value helper text"
    )
    webhook_payload_format_description = LocatorDescriptor(
        testid="pipeline-webhook-payload-format-description",
        description="Payload Format description (static text)"
    )
    webhook_example_request_block = LocatorDescriptor(
        testid="pipeline-webhook-example-request-block",
        description="Example Request code block"
    )
    webhook_example_request_copy_button = LocatorDescriptor(
        testid="pipeline-webhook-example-request-copy-button",
        description="Example Request copy button"
    )
    webhook_modal_cancel_button = LocatorDescriptor(
        testid="pipeline-webhook-modal-cancel-button",
        description="Webhook settings modal Cancel button"
    )
    webhook_modal_apply_button = LocatorDescriptor(
        testid="pipeline-webhook-modal-apply-button",
        description="Webhook settings modal Apply button"
    )

    schedule_modal = LocatorDescriptor(
        testid="pipeline-schedule-settings-modal",
        description="Schedule settings modal (dialog root)"
    )
    schedule_summary_text = LocatorDescriptor(
        testid="pipeline-schedule-summary-text",
        description='Schedule modal cron summary text (e.g. "At 00:00, only on Saturday")'
    )
    schedule_modal_cancel_button = LocatorDescriptor(
        testid="pipeline-schedule-modal-cancel-button",
        description="Schedule settings modal Cancel button"
    )
    schedule_modal_apply_button = LocatorDescriptor(
        testid="pipeline-schedule-modal-apply-button",
        description="Schedule settings modal Apply button"
    )
    schedule_cron_input = LocatorDescriptor(
        testid="pipeline-schedule-cron-input",
        description="Advanced-mode raw cron expression text input"
    )

    # Mode radio (Default/Advanced) — RadioButtonGroup's `testId` prop
    # auto-derives `${testId}-${item.value.lower()}` on the FormControlLabel
    # wrapper (confirmed via source read, same mechanism as the Webhook Type
    # radios above).
    schedule_mode_radio_default = LocatorDescriptor(
        testid="pipeline-schedule-mode-radio-default",
        description="Schedule modal Mode radio — Default option"
    )
    schedule_mode_radio_advanced = LocatorDescriptor(
        testid="pipeline-schedule-mode-radio-advanced",
        description="Schedule modal Mode radio — Advanced option"
    )

    # Third-party widget (react-js-cron / antd internals) — sanctioned #579
    # exception: no app testid can be placed on the library's own
    # `.ant-select`/`.react-js-cron-select` nodes. Scoped constant, chained
    # off the (testid'd) schedule_modal root per the #579 discipline.
    SCHEDULE_CRON_SELECT = ".react-js-cron-select"

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

    # Dynamic (runtime-parameterized) testids — one Value/Type select pair per
    # tool parameter (e.g. search_query, repo_name, max_count). Class-level
    # template constants per .agents/testing.md § Locator policy, formatted
    # with test-generated data only at the call site. Same mechanism as
    # MCP_NODE_INPUT_MAPPING_VALUE above, gated to nodeType==toolkit in
    # BaseToolNode.jsx (ELITEA-2010).
    TOOLKIT_NODE_INPUT_MAPPING_VALUE = '[data-testid="pipeline-toolkit-node-input-mapping-value-{}"]'
    TOOLKIT_NODE_INPUT_MAPPING_TYPE = '[data-testid="pipeline-toolkit-node-input-mapping-type-{}"]'

    # Select-dropdown option pattern shared by Toolkit/Tool/Input/Output
    # selects (SingleSelectMenuItem.jsx: `select-option-{value}`) — confirmed
    # present and reliable per ELITEA-1954 AFS Concrete Handles.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    # Prefix-match variant of SELECT_OPTION for enumerating every option
    # currently rendered in an open Toolkit/Tool listbox — same testid
    # family (`select-option-{value}`), no value known up front. Still
    # testid-keyed, not a raw role/CSS selector.
    SELECT_OPTION_PREFIX = '[data-testid^="select-option-"]'

    # Canvas "+" Add Node trigger and its popup menu (ELITEA-2030). Testids
    # added via add-data-testid onto AddNodeMenu.jsx's IconButton and Menu —
    # this is app JSX we own, not a #579 third-party exception.
    add_node_button = LocatorDescriptor(
        testid="pipeline-add-node-button",
        description="Canvas '+' Add Node trigger button"
    )

    add_node_menu = LocatorDescriptor(
        testid="pipeline-add-node-menu",
        description="Add Node menu popup listing every node type"
    )

    # Dynamic (runtime-parameterized) testid — one per node type rendered in
    # the Add Node menu, keyed by the INTERNAL type (FlowEditorConstants.
    # PipelineNodeTypes value, e.g. "llm", "hitl", "state_modifier"), not the
    # display label ("LLM", "Human-in-the-loop", "State modifier"). Class-
    # level template constant per .agents/testing.md § Locator policy.
    ADD_NODE_MENU_ITEM_BY_TYPE = '[data-testid="pipeline-add-node-menu-item-{}"]'

    # Prefix-match variant for enumerating every item currently rendered in
    # an open Add Node menu, in DOM order — same testid family, no type
    # known up front.
    ADD_NODE_MENU_ITEM_PREFIX = '[data-testid^="pipeline-add-node-menu-item-"]'

    # Generic "any canvas popup menu" check — shared DOM shape across two
    # distinct app components, each with its own real testid (not a raw
    # role/class selector): the Add Node menu above, and the ReactFlow
    # "create new node" context menu that can appear when a canvas
    # drag-connect misses its target handle (`pipeline-connection-dropdown
    # -menu`, ConnectionDropdown.jsx — testid added alongside the Add Node
    # menu's for the same ELITEA-2030/2031 pair of cases).
    POPUP_MENU_TESTIDS = (
        '[data-testid="pipeline-add-node-menu"], '
        '[data-testid="pipeline-connection-dropdown-menu"]'
    )

    # A "Type" select's (SYSTEM/TASK/CHAT HISTORY on the LLM node; each
    # Input-mapping row on the MCP/Toolkit node) option testid is
    # `select-option-{value}`, but `value` is NOT the display label —
    # FlowEditorConstants.agentTaskTypeOptions defines the raw lowercase
    # type ("fixed"/"fstring"/"variable"), not "Fixed"/"F-String"/"Variable".
    # Confirmed live (ELITEA-2004/ELITEA-2010 exploration) — reusing
    # SELECT_OPTION with the display label 404s. Callers pass the display
    # label (matching what get_*_type() reads back); this map translates.
    TYPE_OPTION_VALUE_BY_LABEL = {"Fixed": "fixed", "F-String": "fstring", "Variable": "variable"}

    # Run Details panel (RunStateNode/RunStateDialog — ELITEA-2450). Testids
    # added via add-data-testid onto app JSX we own, not a #579 exception.
    # The run node's clickable label above the Flow canvas — its accessible
    # name is the tooltip text ("View details"), NOT the visible label
    # ("Run N details"); locate by testid only, never by role/name.
    run_node_label = LocatorDescriptor(
        testid="pipeline-run-node-label",
        description="Run node's clickable label above the Flow canvas (opens Run Details panel)"
    )

    run_details_panel = LocatorDescriptor(
        testid="pipeline-run-details-panel",
        description="Run Details panel root (RunStateDialog content) — scope anchor for panel-internal locators"
    )

    run_details_header = LocatorDescriptor(
        testid="pipeline-run-details-header",
        description='Run Details panel header text ("Run N details")'
    )

    # Status badge: testid = stable identity, state read via the `data-status`
    # attribute mirroring RunStateDialog's `data.status` prop
    # (.agents/testing.md "testid = stable identity; state via data-*" ruling).
    run_details_status_badge = LocatorDescriptor(
        testid="pipeline-run-details-status-badge",
        description='Run Details panel status badge ("Completed"/etc.) — filter by data-status for state'
    )

    # Same-element conditional pair (Stop vs Delete IconButton, mutually
    # exclusive branches) — this AFS only exercises the Completed -> Delete
    # path, so only the Delete branch carries the testid (canon ruling #277
    # shape (a): only the used branch is named).
    run_details_delete_button = LocatorDescriptor(
        testid="pipeline-run-details-delete-button",
        description="Run Details panel delete-run icon button (Completed-status branch)"
    )

    run_details_close_button = LocatorDescriptor(
        testid="pipeline-run-details-close-button",
        description="Run Details panel close icon button"
    )

    run_details_timeline_section = LocatorDescriptor(
        testid="pipeline-run-details-timeline-section",
        description='Run Details panel "Timeline step" section (label + node id + stepper)'
    )

    run_details_states_section = LocatorDescriptor(
        testid="pipeline-run-details-states-section",
        description='Run Details panel "States" section (header + per-variable accordion list)'
    )

    # Run Details panel — State Before/After per node (ELITEA-2452). Testids
    # added via add-data-testid, EliteaAI/EliteaUI@2b40e5a6 (app JSX we own,
    # not a #579 exception).

    # Dynamic (runtime-parameterized) testid — one per timeline stepper dot,
    # keyed by list INDEX (not node id — a looped pipeline could revisit the
    # same node id more than once in one timeline). Class-level template
    # constant per .agents/testing.md § Locator policy.
    RUN_DETAILS_TIMELINE_STEP = '[data-testid="pipeline-run-details-timeline-step-{}"]'

    # Dynamic (runtime-parameterized) testid — one accordion-row header per
    # state variable in the STATES section.
    RUN_DETAILS_STATE_ROW = '[data-testid="pipeline-run-details-state-row-{}"]'

    # Dynamic (runtime-parameterized) testids — Before/After value boxes and
    # their fullscreen/expand icon buttons, one pair per state variable.
    RUN_DETAILS_STATE_VALUE_BEFORE = '[data-testid="pipeline-run-details-state-value-before-{}"]'
    RUN_DETAILS_STATE_VALUE_AFTER = '[data-testid="pipeline-run-details-state-value-after-{}"]'
    RUN_DETAILS_STATE_EXPAND_BEFORE = '[data-testid="pipeline-run-details-state-expand-before-{}"]'
    RUN_DETAILS_STATE_EXPAND_AFTER = '[data-testid="pipeline-run-details-state-expand-after-{}"]'

    # Fullscreen value modal (PipelineStateViewModal.jsx) — feature-scoped
    # literal testids (single consumer, RunStateDialog.jsx).
    run_details_value_modal = LocatorDescriptor(
        testid="pipeline-run-details-value-modal",
        description="Fullscreen value modal root (opened by a Before/After expand icon)"
    )
    run_details_value_modal_header = LocatorDescriptor(
        testid="pipeline-run-details-value-modal-header",
        description="Fullscreen value modal heading (shows the variable name only, not Before/After)"
    )
    run_details_value_modal_close_button = LocatorDescriptor(
        testid="pipeline-run-details-value-modal-close-button",
        description="Fullscreen value modal close (X) button"
    )
    run_details_value_modal_content = LocatorDescriptor(
        testid="pipeline-run-details-value-modal-content",
        description="Fullscreen value modal body — the complete, unclipped JSON.stringify'd value"
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

    def get_version_display(self) -> str:
        """Read the VERSION selector's currently displayed version name.

        Returns:
            Version name text (e.g. ``"base"``) as shown in the entity tab
            bar's VERSION combobox.
        """
        return (self.version_selector.text_content() or "").strip()

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

    def get_yaml_gutter_line_numbers(self):
        """Return the CodeMirror line-number gutter locator.

        Scoped under the testid-anchored ``yaml_editor`` parent via
        ``YAML_GUTTER_LINE_SELECTOR`` (sanctioned #579 exception — see that
        constant's docstring). Callers use ``.count()`` / ``.nth(i)``.
        """
        return self.yaml_editor.locator(self.YAML_GUTTER_LINE_SELECTOR)

    def click_copy_yaml_button(self) -> None:
        """Click the "Copy yaml code to clipboard" icon button (YAML view only)."""
        self.copy_yaml_button.click()

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

    def fit_canvas_view(self, timeout: int = 5000) -> None:
        """Click ReactFlow's own "Fit View" control to recenter/rescale the canvas.

        A node's lower rows (e.g. a Toolkit node's Input-mapping parameters,
        once expanded) can end up positioned directly under the canvas's own
        pinned bottom-left controls panel (live-confirmed, ELITEA-2010: a
        coordinate-based click on the intercepted Type select silently
        landed on the "Fit View" button instead of opening the target's
        dropdown — neither ``force=True`` nor ``evaluate("el => el.click()")``
        reach the real target once another element is genuinely on top of it
        on screen). Fit View reliably clears the overlap by
        repositioning/rescaling the flow to fit all nodes.

        #579 sanctioned exception (third-party widget subtree): the
        individual button is ReactFlow's own internal render
        (``react-flow__controls-fitview``, no app testid can be placed on
        it) — scoped to the real app testid ``canvas_controls`` parent per
        the discipline in ``.agents/testing.md`` § Locator policy.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.canvas_controls.locator('button[title="Fit View"]').click(timeout=timeout)
        self.page.wait_for_timeout(500)  # pan/zoom transition settle

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

    def get_add_node_menu_items(self, timeout: int = 5000) -> list[str]:
        """Open the Add Node menu and return every item's visible label.

        Leaves the menu OPEN for the caller to either select an item (via
        :meth:`select_add_node_menu_item`) or dismiss it (Escape / click
        outside) — this is an inspect-then-decide flow that ``add_node()``
        itself can't serve since that method opens AND selects in one call.

        Duplicates ``add_node()``'s own "+ button click, wait 300ms" open
        sequence rather than extracting a shared private helper — this is
        only the second occurrence, below the third-repetition extraction
        threshold this codebase already applies elsewhere (see
        ``_wait_for_yaml_line_selection_applied``'s docstring).

        Testid-based (ELITEA-2030): ``add_node_button``/``add_node_menu``
        LocatorDescriptor fields plus the ``ADD_NODE_MENU_ITEM_PREFIX``
        template constant, added to AddNodeMenu.jsx via ``add-data-testid``
        — replaces the earlier ``button.MuiIconButton-colorPrimary`` /
        ``get_by_role("menuitem")`` raw handles this test's AFS had flagged
        as a "testid gap, not blocking"; the gap is closed, not waived.

        Args:
            timeout: Maximum wait time for the menu items to be visible.

        Returns:
            List of menu item label texts, in DOM order.
        """
        self.add_node_button.click()
        self.page.wait_for_timeout(300)

        items = self.page.locator(self.ADD_NODE_MENU_ITEM_PREFIX)
        items.first.wait_for(state="visible", timeout=timeout)
        count = items.count()
        return [(items.nth(i).text_content() or "").strip() for i in range(count)]

    def select_add_node_menu_item(self, node_type: str, timeout: int = 5000) -> None:
        """Click a node type in an ALREADY-OPEN Add Node menu.

        Companion to :meth:`get_add_node_menu_items` — use when the menu was
        opened via that method (to inspect labels first). For the common
        "just add this node type" case, prefer :meth:`add_node`.

        Testid-based (ELITEA-2030): uses ``ADD_NODE_MENU_ITEM_BY_TYPE``,
        keyed by the item's INTERNAL type (e.g. "llm", "hitl",
        "state_modifier" — FlowEditorConstants.PipelineNodeTypes value),
        NOT the display label ``add_node()`` takes ("LLM",
        "Human-in-the-loop", "State modifier"). Deliberately different
        contract from :meth:`add_node` — the testid AddNodeMenu.jsx renders
        is keyed by the internal type, not the label.

        Args:
            node_type: Internal node-type key of the item to click (e.g.
                "llm", not "LLM").
            timeout: Maximum wait time for the item to be clickable.
        """
        menu_item = self.page.locator(self.ADD_NODE_MENU_ITEM_BY_TYPE.format(node_type))
        menu_item.wait_for(state="visible", timeout=timeout)
        menu_item.click()
        self.page.wait_for_timeout(1000)

    def is_popup_menu_visible(self) -> bool:
        """Return whether either canvas popup menu is currently rendered.

        Generic check — shared DOM shape for both the Add Node menu (ELITEA-
        2030's Escape-dismiss assertion) and the ReactFlow "create new node"
        context menu that can appear when a canvas drag-connect misses its
        target handle (ELITEA-2031's post-drag assertion, mirroring the
        same check :meth:`connect_nodes` already uses internally to
        auto-dismiss it). Testid-based via ``POPUP_MENU_TESTIDS`` (both
        ``pipeline-add-node-menu`` and ``pipeline-connection-dropdown-menu``
        real app testids), not a raw ``[role="menu"]`` selector.

        Returns:
            True if either popup menu's testid is present in the DOM.
        """
        return self.page.locator(self.POPUP_MENU_TESTIDS).count() > 0

    def wait_for_popup_menu_hidden(self, timeout: int = 5000) -> None:
        """Wait (polling) until neither canvas popup menu remains in the DOM.

        Use after dismissing a menu (Escape / click-outside) instead of an
        instant :meth:`is_popup_menu_visible` check — the menu's close
        animation can leave it mounted-but-fading for a short window, so an
        instant check can false-negative by firing before the unmount
        completes. Testid-based via ``POPUP_MENU_TESTIDS`` — see
        :meth:`is_popup_menu_visible`.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        expect(self.page.locator(self.POPUP_MENU_TESTIDS)).to_have_count(0, timeout=timeout)

    def get_node_count(self) -> int:
        """Return the number of nodes on the canvas.

        Returns:
            Count of .react-flow__node elements.
        """
        return self.page.locator(".react-flow__node").count()

    def wait_for_node_count(self, expected_count: int, timeout: int = 10000) -> None:
        """Poll (not an instant read) until the canvas has exactly *expected_count* nodes.

        Added for ELITEA-2033 (adding two same-type nodes in a row, where
        ``wait_for_node_on_canvas()``'s ``.first`` match can't distinguish
        "still just the first one" from "the second one arrived"). Keeps the
        raw ``.react-flow__node`` handle inside the page object — same
        sanctioned ReactFlow-internal handle :meth:`get_node_count` already
        uses — rather than a spec file constructing its own locator.

        Args:
            expected_count: The exact node count to wait for.
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        expect(self.page.locator(".react-flow__node")).to_have_count(expected_count, timeout=timeout)

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

    # ------------------------------------------------------------------
    # Entry-point node — Trigger select & Webhook/Schedule settings modals
    # (ELITEA-2005/2006/2007/2008)
    # ------------------------------------------------------------------

    _WEBHOOK_TYPE_RADIOS = {
        "github": "webhook_type_radio_github",
        "gitlab": "webhook_type_radio_gitlab",
        "custom": "webhook_type_radio_custom",
    }

    def get_trigger_type_value(self, timeout: int = 5000) -> str:
        """Read the Trigger select's currently-displayed value text.

        Args:
            timeout: Maximum wait time for the select to be visible.
        """
        self.trigger_select.wait_for(state="visible", timeout=timeout)
        return (self.trigger_select.text_content() or "").strip()

    def open_trigger_select(self, timeout: int = 10000, entry_point_node_id: str | None = None) -> None:
        """Open the entry-point node's Trigger dropdown.

        ``force=True`` — an unconnected sibling node dropped near the entry
        point (ELITEA-2008's Printer/HITL/Code nodes) can overlap the entry
        point's own card on the ReactFlow canvas, intercepting the click
        (MUI overlay interception, `.claude/rules/mui-patterns.md`). When an
        overlapping sibling is a real risk (multi-node canvases), pass
        *entry_point_node_id* to re-select the entry point node first,
        raising its z-order above any sibling that landed on top of it.

        Args:
            timeout: Maximum wait time in milliseconds.
            entry_point_node_id: Optional data-id of the entry point node to
                bring to the front before opening the dropdown.
        """
        if entry_point_node_id:
            self._select_node(entry_point_node_id)
        self.trigger_select.click(timeout=timeout, force=True)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(
            state="visible", timeout=timeout
        )

    def get_trigger_options(self, timeout: int = 10000, entry_point_node_id: str | None = None) -> list[str]:
        """Open the Trigger dropdown, read the visible option names, close via Escape.

        Args:
            timeout: Maximum wait time in milliseconds.
            entry_point_node_id: Optional data-id of the entry point node to
                bring to the front before opening the dropdown (see
                :meth:`open_trigger_select`).
        """
        self.open_trigger_select(timeout=timeout, entry_point_node_id=entry_point_node_id)
        options = self.get_open_listbox_option_names()
        self.page.keyboard.press("Escape")
        return options

    def toggle_node_interrupt_before(self, node_id: str, timeout: int = 5000) -> None:
        """Click a node's inline "Interrupt before" switch (CommonInterruptSettings.jsx).

        Disabled by the source only when *node_id* IS the pipeline's saved
        entry point (`yamlJsonObject.entry_point === id`) — callers must
        target a node that is NOT the entry point.

        The testid is wired via `slotProps.switch.slotProps.input` (added
        EliteaAI/EliteaUI, ELITEA-2008 fix) so it lands directly on the
        native ``<input type="checkbox">`` — NOT the `MuiSwitch-switchBase`
        wrapper span MUI's `Switch` normally puts extra props on
        (`.agents/memory/test-automation-engineer/
        testid_lands_on_mui_wrapper_not_input.md`; MUI v7's `Switch` silently
        drops a legacy `inputProps` testid entirely). Clicked via
        ``element.click()`` (JS, `.claude/rules/mui-patterns.md` § MUI
        Overlay Interception — same technique as :meth:`delete_node`), NOT a
        coordinate-based Playwright click, even with ``force=True``.
        Confirmed live (ELITEA-2008): after a node add/delete cycle earlier
        on the canvas (e.g. Printer/HITL added then removed before this
        node), some other canvas element ends up topmost at this switch's
        on-screen coordinates. `force=True` only skips Playwright's
        actionability *checks* — the underlying mouse event is still
        dispatched at those coordinates and the browser still delivers it to
        whatever's topmost there, so a coordinate click silently lands on
        the intercepting element instead of the switch (no exception, no
        `aria-disabled`, the switch's `checked` state simply never flips).
        `element.click()` on the (now testid'd) native checkbox bypasses
        on-screen z-order entirely and still fires React's `onChange`.

        Args:
            node_id: The data-id of the target node.
            timeout: Maximum wait time in milliseconds.
        """
        toggle = self.page.locator(self.NODE_INTERRUPT_BEFORE_TOGGLE.format(node_id))
        toggle.wait_for(state="attached", timeout=timeout)
        toggle.evaluate("el => el.click()")

    def select_trigger_type(self, value: str, timeout: int = 10000) -> dict | None:
        """Open the entry-point node's Trigger select and choose *value*.

        Selecting ``"webhook"`` or ``"chat_message"`` fires a
        `PUT .../pipeline_trigger/.../trigger` immediately (source-confirmed
        `handleTriggerTypeChange`, `TriggerTypeSelector.jsx`) — this waits on
        that response, not a fixed timeout. Selecting ``"webhook"``
        additionally opens the Webhook settings modal once the response
        resolves; callers wait on ``webhook_modal`` separately after this
        returns.

        Selecting ``"schedule"`` is DIFFERENT: `handleTriggerTypeChange` only
        calls `setIsScheduleModalOpen(true)` — a synchronous local-state
        update, no awaited mutation — so no PUT fires until the Schedule
        modal's own Apply. This method returns ``None`` for ``"schedule"``
        rather than waiting on a response that will never arrive; callers
        wait on ``schedule_modal`` separately.

        Args:
            value: One of ``"chat_message"``, ``"schedule"``, ``"webhook"``.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the trigger-update PUT response, or ``None``
            when *value* is ``"schedule"``.
        """
        self.trigger_select.click(timeout=timeout, force=True)
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

    def wait_for_webhook_settings_loaded(self, timeout: int = 10000) -> None:
        """Wait for the Webhook settings modal AND its data-dependent fields.

        The URL/Secret sections render only once `triggerData` is populated
        (`PipelineWebhookModal.jsx`: `{webhookUrl && (...)}` / `{secretValue
        && (...)}`), sourced from the SAME RTK-Query tag the trigger-mutating
        PUT invalidates — whose refetch can resolve slightly AFTER the PUT
        response itself, so the modal can become visible before its fields
        do (confirmed live, ~1.5-4.5s gap). Waits on the Webhook URL field
        specifically rather than a fixed sleep.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.webhook_modal.wait_for(state="visible", timeout=timeout)
        self.webhook_url_input.wait_for(state="visible", timeout=timeout)

    def select_webhook_type(self, webhook_type: str, timeout: int = 5000) -> None:
        """Click the Webhook Type radio matching *webhook_type* in the open modal.

        Pure client-side derivation of the URL/description/example request
        off ``selectedWebhookType`` — no network wait needed (source-
        confirmed `PipelineWebhookModal.jsx`).

        Args:
            webhook_type: One of ``"github"``, ``"gitlab"``, ``"custom"``.
            timeout: Maximum wait time in milliseconds.
        """
        radio = getattr(self, self._WEBHOOK_TYPE_RADIOS[webhook_type])
        radio.click(timeout=timeout)

    def get_selected_webhook_type(self) -> str | None:
        """Return which Webhook Type radio is currently checked, or None.

        The testid lands on the MUI ``FormControlLabel`` wrapping the native
        ``<input type="radio">`` (RadioButtonGroup.jsx) — Playwright's
        ``is_checked()`` resolves correctly through the associated
        ``<label>`` wrapper.
        """
        for webhook_type, attr_name in self._WEBHOOK_TYPE_RADIOS.items():
            if getattr(self, attr_name).is_checked():
                return webhook_type
        return None

    def get_webhook_url(self, timeout: int = 5000) -> str:
        """Read the Webhook URL field's current value."""
        self.webhook_url_input.wait_for(state="visible", timeout=timeout)
        return self.webhook_url_input.input_value()

    def reveal_webhook_secret(self, timeout: int = 5000) -> None:
        """Click the Secret Value eye (show/hide) toggle button."""
        self.webhook_secret_toggle_button.click(timeout=timeout)

    def get_webhook_secret(self, timeout: int = 5000) -> str:
        """Read the Secret Value field's current value (masked or revealed)."""
        self.webhook_secret_input.wait_for(state="visible", timeout=timeout)
        return self.webhook_secret_input.input_value()

    def apply_webhook_settings(self, timeout: int = 10000) -> dict:
        """Click Apply in the Webhook settings modal; wait for the trigger PUT.

        Waits on the actual `PUT .../pipeline_trigger/.../trigger` network
        response rather than the modal merely closing — `applyChanges` calls
        `onSubmit(...)` (a Promise, NOT awaited) then `onClose()`
        synchronously (source-confirmed `PipelineWebhookModal.jsx`), so the
        modal-hidden state can be reached before the mutation resolves.

        Returns:
            Parsed JSON body of the trigger-update PUT response.
        """
        with self.page.expect_response(
            lambda r: "/pipeline_trigger/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            self.webhook_modal_apply_button.click(timeout=timeout)
        self.webhook_modal.wait_for(state="hidden", timeout=timeout)
        return response_info.value.json()

    def wait_for_schedule_settings_loaded(self, timeout: int = 10000) -> None:
        """Wait for the Schedule settings modal to be visible.

        Unlike the Webhook modal, the Schedule modal's content is pure local
        component state — nothing here waits on a network refetch.
        """
        self.schedule_modal.wait_for(state="visible", timeout=timeout)

    def get_schedule_summary_text(self, timeout: int = 5000) -> str:
        """Read the Schedule modal's cron summary text."""
        self.schedule_summary_text.wait_for(state="visible", timeout=timeout)
        return (self.schedule_summary_text.text_content() or "").strip()

    def apply_schedule_settings(self, timeout: int = 10000) -> dict:
        """Click Apply in the Schedule settings modal; wait for the trigger PUT.

        `applyChanges` calls `onSubmit(cronExpression)` (a Promise, NOT
        awaited) then `onClose()` synchronously — same close-before-mutation-
        resolves shape as :meth:`apply_webhook_settings`, so this waits on
        the actual PUT response rather than the modal merely closing.

        Returns:
            Parsed JSON body of the trigger-update PUT response.
        """
        with self.page.expect_response(
            lambda r: "/pipeline_trigger/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            self.schedule_modal_apply_button.click(timeout=timeout)
        self.schedule_modal.wait_for(state="hidden", timeout=timeout)
        return response_info.value.json()

    def get_schedule_cron_select_count(self) -> int:
        """Count the visible `.react-js-cron-select` widgets in the open Schedule modal.

        4 when the day-of-week "on" selector is visible (week/on/hour/minute),
        3 when hidden (day-or-finer/hour/minute) — scoped to the (testid'd)
        ``schedule_modal`` root per the #579 sanctioned third-party exception.
        """
        return self.schedule_modal.locator(self.SCHEDULE_CRON_SELECT).count()

    # react-js-cron's hour/minute "at HH:MM" popovers render as antd
    # `.ant-select-dropdown` panels (same `.ant-select-item-option` item
    # class the Every/on selects use — confirmed live via DOM dump, 2026-08-03
    # ELITEA-2007 implementation) — a MULTI-SELECT checkbox grid, not a
    # single-value dropdown: clicking a new option ADDS to the current
    # selection rather than replacing it. Sanctioned #579 third-party
    # exception, scoped off the page (the dropdown portals to <body>, not
    # inside the testid'd schedule_modal root) since only one such dropdown
    # is ever open at a time.
    # `:visible` is a Playwright CSS-engine extension (not standard CSS) —
    # antd leaves a CLOSED dropdown's DOM node in place (hidden, not
    # removed), so an unfiltered `.ant-select-dropdown` count includes stale
    # closed instances from an earlier field (e.g. the "Every" select) and
    # makes a same-class-family open/closed distinction impossible without it.
    CRON_DROPDOWN = ".ant-select-dropdown:visible"
    # Sub-selectors, scoped off a single open CRON_DROPDOWN instance at the
    # call site (never queried page-wide — see set_schedule_hour_minute).
    CRON_DROPDOWN_OPTION = '.ant-select-item-option[title="{}"]'
    CRON_DROPDOWN_SELECTED_OPTION = '.ant-select-item-option[aria-selected="true"]'
    CRON_DROPDOWN_VIRTUAL_LIST = ".rc-virtual-list-holder"

    def set_schedule_hour_minute(self, hour: str, minute: str, timeout: int = 5000) -> None:
        """Set the Schedule modal's hour/minute "at HH:MM" pickers to a single value.

        To land on a clean single value: open the popover, click the
        currently-checked cell to UNCHECK it, then click the target cell to
        check it — for both hour and minute independently. Both toggles are
        VERIFIED (not just fired-and-forgotten) before moving on: a
        JS-evaluate click dispatches a synthetic ``click`` event with no
        guarantee React's onChange/state-update — or, worse, the
        `rc-virtual-list` re-render triggered by the scroll/scroll-into-view
        calls below — has settled by the time the call returns. An
        unverified miss on either toggle leaves the grid in a multi-value
        state (e.g. both "00" and the target checked), which only surfaces
        several steps later as the modal's own inline validation error
        ("Frequency cannot be less than every hour") rather than here where
        the actual cause is. One re-click retry covers a remount landing
        between the scroll and the click; a persistent mismatch fails loudly
        with a locator-count assertion instead of masking into that
        downstream message (ELITEA-2007 gate flake, 2026-08-04: 2 green / 1
        red across 3 consecutive gate runs of this spec).

        Args:
            hour: Target hour, zero-padded (e.g. ``"09"``).
            minute: Target minute, zero-padded (e.g. ``"30"``).
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        # (target, item_count) — hour grid is 0-23 (24 items), minute grid is
        # 0-59 (60 items), confirmed live via DOM dump. Needed to compute the
        # virtualized list's scroll-to-render offset below.
        dropdown = self.page.locator(self.CRON_DROPDOWN)
        for target, item_count in ((hour, 24), (minute, 60)):
            trigger = self.schedule_modal.get_by_text("00", exact=True).first
            trigger.click(timeout=timeout)
            # Exactly one dropdown must be open at a time — a stale one left
            # open from the previous field (Escape not always closing it
            # reliably here) would make `.last` below ambiguous between two
            # overlapping option grids.
            expect(dropdown).to_have_count(1, timeout=timeout)
            open_dropdown = dropdown.last

            # The dropdown panel overlaps the modal's own helper text (MUI
            # overlay interception, .claude/rules/mui-patterns.md) and can
            # reflow outside the viewport once an item is (un)checked —
            # JS-evaluate click bypasses both the pointer-interception AND
            # viewport-visibility actionability checks (mui-patterns.md:
            # "evaluate() ... for critical actions").
            selected_options = open_dropdown.locator(self.CRON_DROPDOWN_SELECTED_OPTION)
            selected_option = selected_options.first
            selected_option.wait_for(state="attached", timeout=timeout)
            selected_option.evaluate("el => el.click()")  # uncheck default
            try:
                expect(selected_options).to_have_count(0, timeout=timeout)
            except AssertionError:
                # Re-resolve and retry once — the locator queries fresh at
                # call time, so this targets whatever cell is ACTUALLY
                # selected now rather than a stale handle.
                selected_options.first.evaluate("el => el.click()")
                expect(selected_options).to_have_count(0, timeout=timeout)

            # The grid is `rc-virtual-list`-virtualized — an option far from
            # the current scroll position never mounts in the DOM at all, so
            # a plain wait_for(attached) times out. Scroll the list's holder
            # to the target's proportional offset first, matching the
            # standard rc-virtual-list scroll-to-render pattern.
            list_holder = open_dropdown.locator(self.CRON_DROPDOWN_VIRTUAL_LIST)
            list_holder.evaluate(
                "(el, [idx, count]) => { el.scrollTop = (idx / count) * el.scrollHeight; }",
                [int(target), item_count],
            )
            target_option = open_dropdown.locator(self.CRON_DROPDOWN_OPTION.format(target))
            target_option.wait_for(state="attached", timeout=timeout)
            target_option.scroll_into_view_if_needed(timeout=timeout)
            target_option.evaluate("el => el.click()")  # check target
            try:
                expect(selected_options).to_have_count(1, timeout=timeout)
                expect(selected_options.first).to_have_attribute("title", target, timeout=timeout)
            except AssertionError:
                # Same remount risk as above — scroll_into_view_if_needed
                # can itself trigger a further internal scroll that detaches
                # the just-resolved cell out from under the click. Re-scroll
                # + re-click once against a freshly resolved target_option.
                target_option.scroll_into_view_if_needed(timeout=timeout)
                target_option.evaluate("el => el.click()")
                expect(selected_options).to_have_count(1, timeout=timeout)
                expect(selected_options.first).to_have_attribute("title", target, timeout=timeout)

            # Click the modal title (neutral area, no click handler of its
            # own) to close the dropdown — more reliable here than Escape,
            # which this custom grid widget doesn't always capture — then
            # confirm it is actually gone before the next field's trigger
            # click, so the two fields' dropdowns never overlap.
            self.page.get_by_text("Schedule settings", exact=True).click(timeout=timeout)
            expect(dropdown).to_have_count(0, timeout=timeout)

    def edit_node_name(self, node_id: str, new_name: str) -> str:
        """Edit a node's name by double-clicking on its name label.

        Double-clicking the node name span makes the first input inside
        the node become editable and focused.

        NOTE: Renaming a node changes its data-id. Live-confirmed (ELITEA-2033
        exploration) the new data-id is the new name VERBATIM, with no
        retained type prefix — renaming "Printer 1" to "approve" sets the
        data-id to exactly "approve", not "Printer approve". (This corrects
        an earlier, incorrect claim here that the type prefix stayed.)
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

        # The first input[type="text"] inside the node holds the name.
        # NOTE (ELITEA-2033 fix): `press("Control+a")` does NOT select-all in
        # this environment (Chromium/macOS) — live-confirmed via direct DOM
        # inspection that selectionStart/selectionEnd don't change after the
        # keypress, so the prior implementation only Backspace-deleted the
        # LAST character before typing, producing "Printer approve" instead
        # of "approve" for a "Printer 1" -> "approve" rename. Uses
        # `select_text()` + `_wait_for_field_selection_applied` instead — the
        # same reliable, OS-independent clear pattern `_fill_node_field_value`
        # already relies on.
        name_input = node.locator('input[type="text"]').first
        name_input.select_text()
        self._wait_for_field_selection_applied(name_input)
        name_input.press("Backspace")
        name_input.type(new_name)
        self.page.wait_for_timeout(300)

        # Click outside the input to commit the edit
        self._deselect_all()
        self.page.wait_for_timeout(300)

        # Find the node's new data-id (renaming changes it). Prefer an exact
        # verbatim match on new_name first — live-confirmed (ELITEA-2033)
        # this is what the product actually sets, no type prefix retained.
        # A prefix-based fallback is kept for any call site that predates
        # this fix and still expects a prefix-retaining rename.
        new_node_id = self.page.evaluate(
            """([oldId, newName]) => {
                const nodes = document.querySelectorAll('.react-flow__node');
                for (const n of nodes) {
                    const nid = n.getAttribute('data-id');
                    if (nid === newName) return nid;
                }
                const prefix = oldId.split(' ')[0];
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
            [node_id, new_name],
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

    def get_open_listbox_option_testids(self) -> list[str]:
        """Return the ``data-testid`` of every option in the currently-open listbox.

        Same enumeration mechanism as ``get_open_listbox_option_names`` (a
        single open MUI-portaled listbox, matched by ``SELECT_OPTION_PREFIX``),
        reading each option's ``data-testid`` instead of its display text —
        used to assert the exact ``select-option-{value}`` set a Type/Value
        select offers, in DOM order.

        Returns:
            List of option testids, in DOM order.
        """
        options = self.page.locator(self.SELECT_OPTION_PREFIX)
        count = options.count()
        return [options.nth(i).get_attribute("data-testid") or "" for i in range(count)]

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

    def open_mcp_node_input_select(self, timeout: int = 5000) -> None:
        """Open the MCP node's tool-agnostic Input dropdown.

        Mirrors ``open_toolkit_node_input_select`` / ``open_llm_node_input_select``
        — same underlying multi-select component (ELITEA-2037).
        """
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.mcp_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_mcp_node_input_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the MCP node's Input dropdown and select *variable_name*.

        The underlying control is ``role="listbox" aria-multiselectable="true"``
        (AFS step 10 note) — selecting doesn't auto-close the popover, so this
        closes it via Escape same as the sibling LLM/Toolkit node methods.
        """
        self.open_mcp_node_input_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_mcp_node_input_value(self) -> str:
        """Read the MCP node's currently-selected Input display text."""
        text = (self.mcp_node_input_select.text_content() or "").replace("​", "")
        return text.strip()

    def open_mcp_node_output_select(self, timeout: int = 5000) -> None:
        """Open the MCP node's tool-agnostic Output dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.mcp_node_output_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_mcp_node_output_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the MCP node's Output dropdown and select *variable_name*."""
        self.open_mcp_node_output_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_mcp_node_output_value(self) -> str:
        """Read the MCP node's currently-selected Output display text."""
        text = (self.mcp_node_output_select.text_content() or "").replace("​", "")
        return text.strip()

    # ------------------------------------------------------------------
    # LLM node inline config (ELITEA-2004)
    # ------------------------------------------------------------------

    _LLM_NODE_SECTIONS = ("system", "task", "chat_history")

    def _llm_node_type_select_locator(self, section: str) -> Locator:
        """Return the class-level Type-select LocatorDescriptor for *section*."""
        if section not in self._LLM_NODE_SECTIONS:
            raise ValueError(f"Unknown LLM node section: {section!r}, expected one of {self._LLM_NODE_SECTIONS}")
        return getattr(self, f"llm_node_{section}_type_select")

    def _llm_node_value_locator(self, section: str) -> Locator:
        """Return the class-level Value-field LocatorDescriptor for *section*."""
        if section not in self._LLM_NODE_SECTIONS:
            raise ValueError(f"Unknown LLM node section: {section!r}, expected one of {self._LLM_NODE_SECTIONS}")
        return getattr(self, f"llm_node_{section}_value")

    # Variable-mode Value select's role="combobox" display element carries a
    # SEPARATE, "-combobox"-suffixed testid from the field's normal one
    # (SingleSelect.jsx's SelectDisplayProps={{'data-testid': `${dataTestId}-combobox`}}) —
    # the field's own testid (e.g. "pipeline-llm-node-system-value") lands on
    # the outer FormControl/Select root instead, which has no role attribute.
    # Same class-level template-constant mechanism as SELECT_OPTION for a
    # dynamic (base-testid-parameterized) selector.
    LLM_NODE_VALUE_COMBOBOX = '[data-testid="{}-combobox"]'

    def _llm_node_value_field_testid(self, section: str) -> str:
        """Return the base ``data-testid`` string of *section*'s Value-field LocatorDescriptor."""
        if section not in self._LLM_NODE_SECTIONS:
            raise ValueError(f"Unknown LLM node section: {section!r}, expected one of {self._LLM_NODE_SECTIONS}")
        descriptor = getattr(type(self), f"llm_node_{section}_value")
        return descriptor.testid

    def get_llm_node_section_value_combobox_locator(self, section: str) -> Locator:
        """Return the Variable-mode Value select's ``role="combobox"`` display element for *section*.

        Only present/visible when *section*'s current Type is ``"Variable"``
        — proves the Value field is specifically a MUI Select combobox, not
        just "some non-textarea element" (see ``get_llm_node_section_value_field_shape``).

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
        """
        base_testid = self._llm_node_value_field_testid(section)
        return self.page.locator(self.LLM_NODE_VALUE_COMBOBOX.format(base_testid))

    def _wait_for_field_selection_applied(self, field: Locator, timeout: int = 5000) -> None:
        """Wait until *field*'s full value is selected, or it has nothing to select.

        ``Locator.select_text()`` performs the browser selection
        synchronously, but a MUI controlled-input re-render can reset
        ``selectionStart``/``selectionEnd`` on the next tick — poll the real
        DOM selection state (not a fixed delay) before sending Backspace, so
        Backspace can't race a not-yet-applied selection. Same pattern as
        ``McpFormPage._wait_for_selection_applied``.
        """
        handle = field.element_handle()
        self.page.wait_for_function(
            """(el) => el.value.length === 0 ||
               (el.selectionStart === 0 && el.selectionEnd === el.value.length)""",
            arg=handle,
            timeout=timeout,
        )

    def _fill_node_field_value(self, field: Locator, value: str, timeout: int = 5000) -> None:
        """Replace *field*'s content with *value*, robust against pre-populated MUI fields.

        ``press("Control+a")`` does not reliably select-all on a
        pre-populated MUI field — live-confirmed for the LLM node's CHAT
        HISTORY Value field (default ``"[]"``): the caret landed at the end
        instead of selecting, so subsequent typing appended
        (``"[]"`` + ``"[]"`` -> ``"[][]"``) rather than replacing. Uses
        ``select_text()`` + ``Backspace`` instead — the same reliable-clear
        pattern already used by ``McpFormPage._fill_text_input`` /
        ``SkillFormPage.fill_instructions``. MUI/React fields need real
        keyboard events for onChange to fire (.claude/rules/mui-patterns.md),
        so this never uses ``fill()``.

        Args:
            field: The value-field Locator (LLM node section or Toolkit
                node Input-mapping row).
            value: The text to type.
            timeout: Maximum wait time in milliseconds.
        """
        field.wait_for(state="visible", timeout=timeout)
        field.click()
        field.select_text()
        self._wait_for_field_selection_applied(field, timeout=timeout)
        field.press("Backspace")
        field.press_sequentially(value, delay=20)

    def get_llm_node_section_type(self, section: str, timeout: int = 5000) -> str:
        """Read the current Type select value for *section* (system/task/chat_history).

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            timeout: Maximum wait time for the select to be visible.
        """
        type_select = self._llm_node_type_select_locator(section)
        type_select.wait_for(state="visible", timeout=timeout)
        # MUI's empty-select rendering is a zero-width space (U+200B), not
        # an empty string — same gotcha as get_mcp_node_toolkit_value.
        text = (type_select.text_content() or "").replace("​", "")
        return text.strip()

    def select_llm_node_section_type(self, section: str, type_value: str, timeout: int = 5000) -> None:
        """Open *section*'s Type select and choose *type_value* (Fixed/F-String/Variable).

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            type_value: Option display text, e.g. ``"F-String"``.
            timeout: Maximum wait time for the dropdown / option.
        """
        type_select = self._llm_node_type_select_locator(section)
        self._wait_for_open_popovers_closed(timeout=timeout)
        type_select.click(timeout=timeout)
        option_value = self.TYPE_OPTION_VALUE_BY_LABEL.get(type_value, type_value)
        option = self.page.locator(self.SELECT_OPTION.format(option_value))
        option.wait_for(state="visible", timeout=timeout)
        option.click(timeout=timeout)

    def fill_llm_node_section_value(self, section: str, value: str, timeout: int = 5000) -> None:
        """Fill *section*'s Value field.

        Uses click + press_sequentially — MUI/React fields need real keyboard
        events for onChange to fire (.claude/rules/mui-patterns.md).

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            value: The text to type.
            timeout: Maximum wait time for the field to be visible.
        """
        value_field = self._llm_node_value_locator(section)
        self._fill_node_field_value(value_field, value, timeout=timeout)

    def get_llm_node_section_value(self, section: str) -> str:
        """Read *section*'s current Value field content.

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
        """
        return self._llm_node_value_locator(section).input_value()

    def get_llm_node_section_value_field_shape(self, section: str, timeout: int = 5000) -> dict:
        """Return the DOM element identity of *section*'s Value field.

        Distinguishes the Fixed/F-String ``<textarea>`` from the
        Variable-mode MUI ``Select`` (``role="combobox"``) by DOM element
        identity, not just displayed text — a regression that left the old
        textarea mounted (with a stale leftover value) instead of swapping
        to the new Select would otherwise look like a pass if only text
        content were checked.

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            timeout: Maximum wait time for the field to be visible.

        Returns:
            ``{"tag_name": <UPPERCASE tag>, "role": <role attribute or None>}``
        """
        value_field = self._llm_node_value_locator(section)
        value_field.wait_for(state="visible", timeout=timeout)
        tag_name = value_field.evaluate("el => el.tagName")
        role = value_field.get_attribute("role")
        return {"tag_name": tag_name, "role": role}

    def get_llm_node_section_variable_value(self, section: str, timeout: int = 5000) -> str:
        """Read *section*'s Value field when its Type is ``"Variable"``.

        In Variable mode the Value field renders as a MUI ``Select``
        (``role="combobox"``), not a text input — ``input_value()`` (used by
        ``get_llm_node_section_value`` for Fixed/F-String) throws on this
        element. Reads ``text_content()`` with the same zero-width-space
        strip as ``get_llm_node_section_type`` (MUI's empty-select rendering
        is U+200B, not an empty string).

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            timeout: Maximum wait time for the field to be visible.
        """
        value_field = self._llm_node_value_locator(section)
        value_field.wait_for(state="visible", timeout=timeout)
        text = (value_field.text_content() or "").replace("​", "")
        return text.strip()

    def open_llm_node_section_type_select(self, section: str, timeout: int = 5000) -> None:
        """Open *section*'s Type select without choosing an option.

        Use when the caller needs to inspect the open option list (e.g. via
        ``get_open_listbox_option_testids``) before selecting one — mirrors
        ``open_llm_node_input_select``. When no prior inspection is needed,
        prefer ``select_llm_node_section_type``, which opens and selects in
        one call.

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            timeout: Maximum wait time for the select / popover.
        """
        type_select = self._llm_node_type_select_locator(section)
        self._wait_for_open_popovers_closed(timeout=timeout)
        type_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def open_llm_node_section_variable_value_select(self, section: str, timeout: int = 5000) -> None:
        """Open *section*'s Value select without choosing an option.

        Only valid when *section*'s current Type is ``"Variable"`` — at any
        other Type the Value field is a text input, not a select. Use when
        the caller needs to inspect the open option list (e.g. via
        ``get_open_listbox_option_testids``) before selecting one.

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            timeout: Maximum wait time for the select / popover.
        """
        value_field = self._llm_node_value_locator(section)
        self._wait_for_open_popovers_closed(timeout=timeout)
        value_field.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_llm_node_section_variable_value(
        self, section: str, variable_name: str, timeout: int = 5000
    ) -> None:
        """Open *section*'s Value select (Variable mode) and choose *variable_name*.

        Against the same ``_llm_node_value_locator`` field
        ``fill_llm_node_section_value``/``get_llm_node_section_value`` use for
        Fixed/F-String — only the read/write mechanism differs by the widget
        the current Type renders.

        Args:
            section: One of ``"system"``, ``"task"``, ``"chat_history"``.
            variable_name: The state variable's option value (e.g. ``"input"``).
            timeout: Maximum wait time for the select / option.
        """
        self.open_llm_node_section_variable_value_select(section, timeout=timeout)
        self.select_open_listbox_option(variable_name, timeout=timeout)

    def _wait_for_open_popovers_closed(self, timeout: int = 5000) -> None:
        """Wait until no select-option-* row is visible anywhere on the page.

        Selecting an option normally closes its own popover synchronously,
        but the close animation/unmount can still be in flight when the very
        next call opens a DIFFERENT select immediately after (e.g. the LLM/
        Toolkit node's consecutive Input -> Output selects) — the
        still-closing popover's backdrop then intercepts the next select's
        click (live-confirmed: "element ... intercepts pointer events").
        Testid-based (``SELECT_OPTION_PREFIX`` — the same
        ``select-option-{value}`` family every dropdown option carries,
        SingleSelectMenuItem.jsx) rather than a raw MUI popover class, per
        .agents/testing.md § Locator policy. Best-effort — if nothing is
        open this returns immediately.
        """
        from playwright.sync_api import expect

        try:
            expect(self.page.locator(self.SELECT_OPTION_PREFIX)).to_have_count(0, timeout=timeout)
        except Exception:
            pass

    def open_llm_node_input_select(self, timeout: int = 5000) -> None:
        """Open the LLM node's Input dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.llm_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def _select_multi_select_option_and_close(self, variable_name: str, timeout: int = 5000) -> None:
        """Select *variable_name* in the currently-open multi-select listbox, then close it.

        The Input/Output state-variable selects (LLM and Toolkit node) are
        MUI multi-selects (``InputSelect``/``OutputSelect``: ``multiple``) —
        selecting an option does NOT auto-close the popover, unlike a
        single-select (Toolkit/Tool). Left open, the still-visible popover
        intercepts the next select's click (live-confirmed: "intercepts
        pointer events" when opening a second select right after). Closes
        via Escape and waits for the popover to actually leave the DOM.
        """
        self.select_open_listbox_option(variable_name, timeout=timeout)
        self.page.keyboard.press("Escape")
        self._wait_for_open_popovers_closed(timeout=timeout)

    def select_llm_node_input_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the Input dropdown and select *variable_name*."""
        self.open_llm_node_input_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_llm_node_input_value(self) -> str:
        """Read the LLM node's currently-selected Input display text."""
        text = (self.llm_node_input_select.text_content() or "").replace("​", "")
        return text.strip()

    def open_llm_node_output_select(self, timeout: int = 5000) -> None:
        """Open the LLM node's Output dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.llm_node_output_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_llm_node_output_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the Output dropdown and select *variable_name*."""
        self.open_llm_node_output_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_llm_node_output_value(self) -> str:
        """Read the LLM node's currently-selected Output display text."""
        text = (self.llm_node_output_select.text_content() or "").replace("​", "")
        return text.strip()

    def is_node_interrupt_before_toggle_visible(self, node_id: str, timeout: int = 5000) -> bool:
        """Return whether *node_id*'s 'Interrupt before' switch is visible.

        Node-id-keyed, not node-type-keyed (ELITEA-2008) — works for any node
        type sharing CommonInterruptSettings.jsx, e.g. the value returned by
        ``wait_for_node_on_canvas()``.
        """
        toggle = self.page.locator(self.NODE_INTERRUPT_BEFORE_TOGGLE.format(node_id))
        try:
            toggle.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_node_interrupt_before_toggle_disabled(self, node_id: str, timeout: int = 5000) -> bool:
        """Return whether *node_id*'s 'Interrupt before' switch is disabled.

        Sibling of :meth:`is_node_interrupt_before_toggle_visible` (ELITEA-2037)
        — CommonInterruptSettings.jsx disables this toggle when the node is the
        pipeline's entry point (``entry_point === id`` gating).
        """
        toggle = self.page.locator(self.NODE_INTERRUPT_BEFORE_TOGGLE.format(node_id))
        toggle.wait_for(state="visible", timeout=timeout)
        return toggle.is_disabled()

    # ------------------------------------------------------------------
    # Toolkit node inline config (ELITEA-2010)
    # ------------------------------------------------------------------

    def get_toolkit_node_toolkit_value(self, timeout: int = 5000) -> str:
        """Read the Toolkit node's currently-selected Toolkit display text."""
        self.toolkit_node_toolkit_select.wait_for(state="visible", timeout=timeout)
        text = (self.toolkit_node_toolkit_select.text_content() or "").replace("​", "")
        return text.strip()

    def get_toolkit_node_tool_value(self, timeout: int = 5000) -> str:
        """Read the Toolkit node's currently-selected Tool display text.

        Returns empty string both when no tool is selected AND when the Tool
        select isn't rendered at all yet (conditionally rendered — see
        ``toolkit_node_tool_select`` description).

        Args:
            timeout: Maximum wait time for the select to be visible (not
                applied when the element never appears — see above).
        """
        try:
            self.toolkit_node_tool_select.wait_for(state="visible", timeout=timeout)
        except Exception:
            return ""
        text = (self.toolkit_node_tool_select.text_content() or "").replace("​", "")
        return text.strip()

    def is_toolkit_node_tool_select_visible(self, timeout: int = 2000) -> bool:
        """Check whether the Toolkit node's Tool select is rendered at all.

        Used to assert the absence of the Tool select before a Toolkit is
        selected (AFS step 4 negative assertion — the two-stage reveal is a
        test-enforced contract, not a documented assumption).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.toolkit_node_tool_select.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def open_toolkit_node_toolkit_select(self, timeout: int = 5000) -> None:
        """Open the Toolkit node's Toolkit dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.toolkit_node_toolkit_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_toolkit_node_toolkit(self, toolkit_name: str, timeout: int = 5000) -> None:
        """Open the Toolkit dropdown and select *toolkit_name*.

        Args:
            toolkit_name: The toolkit's display value (matches
                ``select-option-{toolkit_name}``).
            timeout: Maximum wait time for the dropdown / option.
        """
        self.open_toolkit_node_toolkit_select(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(toolkit_name))
        option.click(timeout=timeout)

    def open_toolkit_node_tool_select(self, timeout: int = 5000) -> None:
        """Open the Toolkit node's Tool dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.toolkit_node_tool_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_toolkit_node_tool(self, tool_name: str, timeout: int = 5000) -> None:
        """Open the Tool dropdown and select *tool_name*.

        Args:
            tool_name: The tool's value (matches ``select-option-{tool_name}``).
            timeout: Maximum wait time for the dropdown / option.
        """
        self.open_toolkit_node_tool_select(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(tool_name))
        option.click(timeout=timeout)

    def is_toolkit_node_input_mapping_section_visible(self, required_count: int, timeout: int = 5000) -> bool:
        """Check whether the Toolkit node's "Input mapping (required N)" accordion is visible.

        Args:
            required_count: Expected N in the accordion title.
            timeout: Maximum wait time.

        Returns:
            True if the section with the exact required count is visible.
        """
        heading = self.toolkit_node_input_mapping_required_heading
        try:
            heading.wait_for(state="visible", timeout=timeout)
        except Exception:
            return False
        text = (heading.text_content() or "").strip()
        return text == f"Input mapping (required {required_count})"

    def is_toolkit_node_input_mapping_optional_section_visible(self, optional_count: int, timeout: int = 5000) -> bool:
        """Check whether the Toolkit node's "Input mapping (optional N)" accordion is visible.

        Args:
            optional_count: Expected N in the accordion title.
            timeout: Maximum wait time.

        Returns:
            True if the section with the exact optional count is visible.
        """
        heading = self.toolkit_node_input_mapping_optional_heading
        try:
            heading.wait_for(state="visible", timeout=timeout)
        except Exception:
            return False
        text = (heading.text_content() or "").strip()
        return text == f"Input mapping (optional {optional_count})"

    def get_toolkit_node_input_mapping_type(self, param_name: str, timeout: int = 5000) -> str:
        """Read the current Type select value of an Input-mapping row.

        Args:
            param_name: The tool parameter's raw schema key (e.g. ``"search_query"``).
            timeout: Maximum wait time for the select to be visible.
        """
        type_select = self.page.locator(self.TOOLKIT_NODE_INPUT_MAPPING_TYPE.format(param_name))
        type_select.wait_for(state="visible", timeout=timeout)
        text = (type_select.text_content() or "").replace("​", "")
        return text.strip()

    def select_toolkit_node_input_mapping_type(self, param_name: str, type_value: str, timeout: int = 5000) -> None:
        """Open an Input-mapping row's Type select and choose *type_value*.

        Args:
            param_name: The tool parameter's raw schema key (e.g. ``"search_query"``).
            type_value: Option display text, e.g. ``"F-String"``.
            timeout: Maximum wait time for the dropdown / option.
        """
        type_select = self.page.locator(self.TOOLKIT_NODE_INPUT_MAPPING_TYPE.format(param_name))
        self._wait_for_open_popovers_closed(timeout=timeout)
        type_select.scroll_into_view_if_needed(timeout=timeout)
        type_select.click(timeout=timeout)
        option_value = self.TYPE_OPTION_VALUE_BY_LABEL.get(type_value, type_value)
        option = self.page.locator(self.SELECT_OPTION.format(option_value))
        option.wait_for(state="visible", timeout=timeout)
        option.click(timeout=timeout)

    def get_toolkit_node_input_mapping_value(self, param_name: str, timeout: int = 5000) -> str:
        """Read the current value of an Input-mapping "Value" field.

        Args:
            param_name: The tool parameter's raw schema key (e.g. ``"search_query"``).
            timeout: Maximum wait time for the field to be visible.
        """
        field = self.page.locator(self.TOOLKIT_NODE_INPUT_MAPPING_VALUE.format(param_name))
        field.wait_for(state="visible", timeout=timeout)
        return field.input_value()

    def fill_toolkit_node_input_mapping_value(self, param_name: str, value: str, timeout: int = 5000) -> None:
        """Fill an Input-mapping "Value" field for a fixed/f-string tool parameter.

        Args:
            param_name: The tool parameter's raw schema key (e.g. ``"search_query"``).
            value: The text to type.
            timeout: Maximum wait time for the field to be visible.
        """
        field = self.page.locator(self.TOOLKIT_NODE_INPUT_MAPPING_VALUE.format(param_name))
        self._fill_node_field_value(field, value, timeout=timeout)

    def open_toolkit_node_input_select(self, timeout: int = 5000) -> None:
        """Open the Toolkit node's Input dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.toolkit_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_toolkit_node_input_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the Input dropdown and select *variable_name*."""
        self.open_toolkit_node_input_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_toolkit_node_input_value(self) -> str:
        """Read the Toolkit node's currently-selected Input display text."""
        text = (self.toolkit_node_input_select.text_content() or "").replace("​", "")
        return text.strip()

    def open_toolkit_node_output_select(self, timeout: int = 5000) -> None:
        """Open the Toolkit node's Output dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.toolkit_node_output_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_toolkit_node_output_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the Output dropdown and select *variable_name*."""
        self.open_toolkit_node_output_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_toolkit_node_output_value(self) -> str:
        """Read the Toolkit node's currently-selected Output display text."""
        text = (self.toolkit_node_output_select.text_content() or "").replace("​", "")
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

    def save_and_wait_for_error_response(
        self, project_id: str, pipeline_id: int, timeout: int = 15000
    ) -> dict:
        """Click Save and wait for the update PUT's FAILING (4xx/5xx) response.

        Mirrors ``save_and_wait_for_update`` (ELITEA-1954) but matches on a
        failing status instead of ``201`` — for ELITEA-2068's invalid-YAML
        case, where clicking Save with unparseable YAML in the editor is
        expected to be rejected server-side rather than silently succeed.

        Args:
            project_id: Project id, used to scope the response URL match.
            pipeline_id: The pipeline's numeric id.
            timeout: Maximum wait time in milliseconds.

        Returns:
            dict with ``status`` (int) and ``body`` (str — raw response
            text, not assumed-JSON: the error body is a Pydantic-style
            validation error confirmed live, but reading it as text and
            letting the caller substring-match is more robust than
            assuming a fixed schema).
        """
        with self.page.expect_response(
            lambda r: f"/application/prompt_lib/{project_id}/{pipeline_id}" in r.url
            and r.request.method == "PUT"
            and r.status >= 400,
            timeout=timeout,
        ) as response_info:
            self.save_button.evaluate("el => el.click()")
        response = response_info.value
        return {"status": response.status, "body": response.text()}

    def get_toast_alert(self, severity: str):
        """Return the toast Alert locator scoped to a specific data-severity value.

        Testid identity (``toast-alert``) + a ``data-severity`` state filter
        — the compliant shape for a state-dependent assertion (state is
        never encoded in the testid itself). Mirrors
        ``ChatPage.get_toast_alert``.

        Args:
            severity: e.g. "warning", "info", "error", "success".
        """
        return self.page.locator(self.TOAST_ALERT_SEVERITY.format(severity))

    def get_toast_text(self, timeout: int = 10000) -> str:
        """Wait for the app-wide toast message to become visible and return its text."""
        self.toast_message.wait_for(state="visible", timeout=timeout)
        return (self.toast_message.text_content() or "").strip()

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

    def get_edge_locator(self, source_id: str, target_id: str) -> Locator:
        """Return the Locator for the edge from *source_id* to *target_id*.

        Testid-based (ELITEA-2032): uses the same exact ``EDGE_TESTID``
        template :meth:`edge_testid_present` relies on
        (``rf__edge-xy-edge__{source}---{target}``, confirmed live) instead
        of the legacy ``.react-flow__edge`` class-scan + manual prefix/
        substring match ``edge_exists()`` uses. Reading the testid via
        ``get_attribute()`` after a raw CSS-class scan locates the element
        by CLASS, not by testid — not a testid-only locator per
        ``.agents/testing.md`` § Locator policy regardless of precedent
        elsewhere in this file (existing raw handles are tracked tech debt
        — #25/#42 — never a justification for a new one).

        No ``handle_suffix`` parameter (the prior version had one): the
        exact-testid format has no live-confirmed handle-suffix variant
        (e.g. for HITL approve/reject edges), and the sole caller
        (ELITEA-2032) doesn't need one — add it only once a confirmed
        format for a handle-qualified edge testid exists.

        Args:
            source_id: Internal source node id exactly as it appears in the
                edge's data-testid (e.g. "LLM 1").
            target_id: Internal target node id exactly as it appears in the
                edge's data-testid (e.g. "Printer 1", "EliteAPipelineEnd").

        Returns:
            Locator matching the edge's exact
            ``[data-testid="rf__edge-xy-edge__{source}---{target}"]`` element.

        Raises:
            ValueError: If no matching edge is found in the DOM.
        """
        locator = self.page.locator(self.EDGE_TESTID.format(source_id, target_id))
        if locator.count() == 0:
            raise ValueError(f"No edge found from '{source_id}' to '{target_id}'")
        return locator.first

    def wait_for_edge(self, source_id: str, target_id: str, timeout: int = 10000) -> None:
        """Poll (not an instant read) until the exact edge testid appears in the DOM.

        Added for ELITEA-2033: `get_edge_locator()` / `edge_testid_present()`
        are both synchronous, non-polling `.count()` reads (by design — other
        callers rely on an instant read right after an action, e.g. asserting
        ABSENCE) — a Router node's edge is created by a React state update
        that can lag a tick behind the click, so this polls the SAME exact
        ``EDGE_TESTID`` template via Playwright's own
        ``expect().to_have_count()`` before a caller's boolean check.

        Args:
            source_id: Internal source node id exactly as it appears in the
                edge's data-testid (e.g. "Router 1", "Router 1default_output").
            target_id: Internal target node id exactly as it appears in the
                edge's data-testid (e.g. "approve", "END").
            timeout: Maximum wait time in milliseconds.
        """
        from playwright.sync_api import expect

        expect(self.page.locator(self.EDGE_TESTID.format(source_id, target_id))).to_have_count(
            1, timeout=timeout
        )

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
    # Run Details panel (RunStateNode/RunStateDialog — ELITEA-2450)
    # ------------------------------------------------------------------

    def open_run_details_panel(self, timeout: int = 10000):
        """Click the run node's label (above the Flow canvas) to open the
        Run Details panel.

        The run node becomes clickable only after the pipeline execution's
        WebSocket-driven state reaches a terminal status — callers must wait
        for the embedded chat response (``wait_for_embedded_chat_response``)
        before calling this.

        Args:
            timeout: Maximum wait time for the run node label to appear.
        """
        logger.info("Opening Run Details panel")
        self.run_node_label.wait_for(state="visible", timeout=timeout)
        self.run_node_label.click()
        self.run_details_panel.wait_for(state="visible", timeout=timeout)
        logger.info("Run Details panel opened")

    def close_run_details_panel(self, timeout: int = 5000):
        """Click the Run Details panel's close icon button.

        Args:
            timeout: Maximum wait time for the panel to disappear.
        """
        logger.info("Closing Run Details panel")
        self.run_details_close_button.click()
        self.run_details_panel.wait_for(state="hidden", timeout=timeout)
        logger.info("Run Details panel closed")

    def get_run_details_header_text(self) -> str:
        """Return the Run Details panel header text (e.g. "Run 1 details")."""
        return (self.run_details_header.text_content() or "").strip()

    def get_run_details_status(self) -> str:
        """Return the Run Details panel's status badge value via `data-status`."""
        return self.run_details_status_badge.get_attribute("data-status") or ""

    def get_run_details_status_badge_text(self) -> str:
        """Return the Run Details panel's status badge visible text (e.g. "Completed")."""
        return (self.run_details_status_badge.text_content() or "").strip()

    def get_run_details_timeline_section_text(self) -> str:
        """Return the Run Details panel's Timeline step section text content."""
        return (self.run_details_timeline_section.text_content() or "").strip()

    def get_run_details_states_section_text(self) -> str:
        """Return the Run Details panel's States section text content."""
        return (self.run_details_states_section.text_content() or "").strip()

    # ------------------------------------------------------------------
    # Run Details panel — State Before/After per node (ELITEA-2452)
    # ------------------------------------------------------------------

    def get_run_details_state_row_locator(self, variable: str) -> Locator:
        """Return the Locator for *variable*'s accordion-row header in the STATES section."""
        return self.page.locator(self.RUN_DETAILS_STATE_ROW.format(variable))

    def get_run_details_state_value_locator(self, variable: str, direction: str) -> Locator:
        """Return the Locator for *variable*'s Before or After value box.

        Args:
            variable: State variable name (e.g. "messages").
            direction: ``"before"`` or ``"after"``.
        """
        template = (
            self.RUN_DETAILS_STATE_VALUE_BEFORE if direction == "before" else self.RUN_DETAILS_STATE_VALUE_AFTER
        )
        return self.page.locator(template.format(variable))

    def select_run_details_timeline_step(self, index: int, timeout: int = 10000):
        """Click the timeline stepper dot at *index* to select that run step.

        Args:
            index: Zero-based index into the run's timeline (0 = first
                executed node).
            timeout: Maximum wait time for the step control to appear.
        """
        logger.info("Selecting Run Details timeline step %d", index)
        step = self.page.locator(self.RUN_DETAILS_TIMELINE_STEP.format(index))
        step.wait_for(state="visible", timeout=timeout)
        step.click()

    def get_run_details_selected_timeline_step_id(self) -> str:
        """Return the "Timeline step:" label's currently-selected node id.

        The label and the node id render as sibling Typography elements with
        no separator between them (confirmed live, ELITEA-2450) — the raw
        text is returned as-is; callers substring-match the expected node id.
        """
        return self.get_run_details_timeline_section_text()

    def expand_run_details_state_row(self, variable: str, timeout: int = 10000):
        """Click the accordion header for *variable* in the STATES section to
        expand it (a no-op if already expanded — MUI accordion click toggles,
        so only call this on a collapsed row).

        Args:
            variable: State variable name (e.g. "messages").
            timeout: Maximum wait time for the row to appear.
        """
        logger.info("Expanding Run Details state row %r", variable)
        row = self.page.locator(self.RUN_DETAILS_STATE_ROW.format(variable))
        row.wait_for(state="visible", timeout=timeout)
        row.click()

    def get_run_details_state_before_value(self, variable: str, timeout: int = 10000) -> str:
        """Return the Before value box's text for *variable* (row must be expanded)."""
        box = self.page.locator(self.RUN_DETAILS_STATE_VALUE_BEFORE.format(variable))
        box.wait_for(state="visible", timeout=timeout)
        return (box.text_content() or "").strip()

    def get_run_details_state_after_value(self, variable: str, timeout: int = 10000) -> str:
        """Return the After value box's text for *variable* (row must be expanded)."""
        box = self.page.locator(self.RUN_DETAILS_STATE_VALUE_AFTER.format(variable))
        box.wait_for(state="visible", timeout=timeout)
        return (box.text_content() or "").strip()

    def open_run_details_state_value_fullscreen(
        self, variable: str, direction: str, timeout: int = 10000
    ):
        """Click the fullscreen/expand icon on *variable*'s Before or After
        value box, opening the value modal (``PipelineStateViewModal.jsx``).

        Args:
            variable: State variable name (e.g. "messages").
            direction: ``"before"`` or ``"after"``.
            timeout: Maximum wait time for the icon and the resulting modal.
        """
        template = (
            self.RUN_DETAILS_STATE_EXPAND_BEFORE
            if direction == "before"
            else self.RUN_DETAILS_STATE_EXPAND_AFTER
        )
        logger.info("Opening Run Details fullscreen value modal (%s, %s)", variable, direction)
        icon = self.page.locator(template.format(variable))
        icon.wait_for(state="visible", timeout=timeout)
        icon.click()
        self.run_details_value_modal.wait_for(state="visible", timeout=timeout)

    def close_run_details_value_modal(self, timeout: int = 5000):
        """Click the fullscreen value modal's close (X) button."""
        logger.info("Closing Run Details fullscreen value modal")
        self.run_details_value_modal_close_button.click()
        self.run_details_value_modal.wait_for(state="hidden", timeout=timeout)

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
    # Router node inline config (ELITEA-2033)
    # ------------------------------------------------------------------

    def fill_router_node_condition(self, text: str, timeout: int = 5000) -> None:
        """Fill the Router node's Condition Jinja textarea.

        Uses click + press_sequentially — MUI/React fields need real keyboard
        events for onChange to fire (.claude/rules/mui-patterns.md). The
        field is a plain MUI TextField multiline textarea (NOT CodeMirror/
        Monaco despite the `language="jinja"` prop — that only affects the
        separate full-screen AI Assistant modal, confirmed via source read),
        so no CodeMirror-line-scoping technique is needed here. Starts empty
        on a freshly-added node, so no clear-before-type step is needed.

        Args:
            text: The Jinja condition template to type.
            timeout: Maximum wait time for the field to be visible.
        """
        self.router_node_condition_input.wait_for(state="visible", timeout=timeout)
        self.router_node_condition_input.click()
        self.router_node_condition_input.press_sequentially(text, delay=20)

    def get_router_node_condition(self) -> str:
        """Read the Router node's Condition textarea current value."""
        return self.router_node_condition_input.input_value()

    def open_router_node_routes_select(self, timeout: int = 5000) -> None:
        """Open the Router node's Routes multi-select dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.router_node_routes_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_router_node_routes(self, values: list[str], timeout: int = 5000) -> None:
        """Open the Routes dropdown and select every value in *values*, then close.

        Routes is a picklist of EXISTING pipeline node ids (+ a literal
        ``END`` option), not a freeform/creatable tag field (AFS Coverage
        Map clarification) — each value must match a node id already on the
        canvas. A multi-select (like the LLM/HITL Input selects): selecting
        an option does not auto-close the popover, so every value is
        selected before a single Escape closes it.

        Args:
            values: Existing pipeline node ids (or ``"END"``) to select as
                routes — matches ``select-option-{value}``.
            timeout: Maximum wait time in milliseconds.
        """
        self.open_router_node_routes_select(timeout=timeout)
        for value in values:
            self.page.locator(self.SELECT_OPTION.format(value)).click(timeout=timeout)
        self.page.keyboard.press("Escape")
        self._wait_for_open_popovers_closed(timeout=timeout)

    def get_router_node_routes_value(self) -> str:
        """Read the Routes select's currently-selected chips as concatenated text."""
        text = (self.router_node_routes_select.text_content() or "").replace("​", "")
        return text.strip()

    def open_router_node_input_select(self, timeout: int = 5000) -> None:
        """Open the Router node's tool-agnostic Input dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.router_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_router_node_input_variable(self, variable_name: str, timeout: int = 5000) -> None:
        """Open the Input dropdown and select *variable_name*."""
        self.open_router_node_input_select(timeout=timeout)
        self._select_multi_select_option_and_close(variable_name, timeout=timeout)

    def get_router_node_input_value(self) -> str:
        """Read the Router node's currently-selected Input display text."""
        text = (self.router_node_input_select.text_content() or "").replace("​", "")
        return text.strip()

    def open_router_node_default_output_select(self, timeout: int = 5000) -> None:
        """Open the Router node's Default output single-select dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.router_node_default_output_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_router_node_default_output(self, target_node_id: str, timeout: int = 5000) -> None:
        """Open the Default output select and choose *target_node_id* (or ``"END"``).

        A single-select — selecting an option auto-closes the popover
        (unlike the multi-select Routes/Input fields above).
        """
        self.open_router_node_default_output_select(timeout=timeout)
        self.page.locator(self.SELECT_OPTION.format(target_node_id)).click(timeout=timeout)

    def get_router_node_default_output_value(self, timeout: int = 5000) -> str:
        """Read the Default output select's current display text."""
        self.router_node_default_output_select.wait_for(state="visible", timeout=timeout)
        text = (self.router_node_default_output_select.text_content() or "").replace("​", "")
        return text.strip()

    # ------------------------------------------------------------------
    # Decision node inline config (ELITEA-2034)
    # ------------------------------------------------------------------

    def open_decision_node_input_select(self, timeout: int = 5000) -> None:
        """Open the Decision node's tool-agnostic Input dropdown."""
        self._wait_for_open_popovers_closed(timeout=timeout)
        self.decision_node_input_select.click(timeout=timeout)
        self.page.locator(self.SELECT_OPTION_PREFIX).first.wait_for(state="visible", timeout=timeout)

    def select_decision_node_input_variables(self, values: list[str], timeout: int = 5000) -> None:
        """Open the Input dropdown and select every value in *values*, then close.

        A multi-select (same ``InputSelect`` component family as Router's
        Input/Routes fields) — selecting an option does not auto-close the
        popover, so every value is selected before a single Escape closes it.

        Args:
            values: State-variable names to select (matches ``select-option-{value}``).
            timeout: Maximum wait time in milliseconds.
        """
        self.open_decision_node_input_select(timeout=timeout)
        for value in values:
            self.page.locator(self.SELECT_OPTION.format(value)).click(timeout=timeout)
        self.page.keyboard.press("Escape")
        self._wait_for_open_popovers_closed(timeout=timeout)

    def get_decision_node_input_value(self) -> str:
        """Read the Decision node's currently-selected Input display text."""
        text = (self.decision_node_input_select.text_content() or "").replace("​", "")
        return text.strip()

    def fill_decision_node_description(self, text: str, timeout: int = 5000) -> None:
        """Fill the Decision node's Description textarea (classification prompt).

        Plain MUI TextField multiline textarea (same ``AIAssistantInput``
        family as Router's Condition field, NOT CodeMirror/Monaco despite
        node-family styling) — click + press_sequentially for real keyboard
        events (.claude/rules/mui-patterns.md). Starts empty on a
        freshly-added node, so no clear-before-type step is needed.
        """
        self.decision_node_description_input.wait_for(state="visible", timeout=timeout)
        self.decision_node_description_input.click()
        self.decision_node_description_input.press_sequentially(text, delay=20)

    def get_decision_node_description(self) -> str:
        """Read the Decision node's Description textarea current value."""
        return self.decision_node_description_input.input_value()

    def is_decision_node_output_chip_present(self, value: str) -> bool:
        """Check whether a DECISION OUTPUTS chip labeled *value* is present."""
        return self.page.locator(self.DECISION_NODE_OUTPUT_CHIP.format(value)).count() > 0

    def get_decision_node_output_chip_count(self) -> int:
        """Return the number of DECISION OUTPUTS chips currently rendered."""
        return self.page.locator(self.DECISION_NODE_OUTPUT_CHIP_PREFIX).count()

    def wait_for_edge_present(self, source_id: str, target_id: str, timeout: int = 10000) -> None:
        """Poll until an edge from *source_id* to *target_id* appears, tolerating both shapes.

        Unlike ``wait_for_edge()`` (which polls the EXACT post-reload
        ``EDGE_TESTID`` ``---``-only shape and is NOT valid for a Decision
        node's DECISION OUTPUTS edges pre-Save — their pre-save testid drops
        the ``---`` separator entirely, e.g. ``Decision 1nodes-bug_respondertarget``
        vs. the post-reload ``Decision 1---bug_responder``), this polls via
        the SAME loose prefix+substring matching ``edge_exists()`` uses, so
        it works for both shapes without the caller needing to know which
        one is currently live.

        Args:
            source_id: Internal source node id as it appears in the edge's
                data-testid (e.g. "Decision 1", "Decision 1default_output").
            target_id: Internal target node id as it appears in the edge's
                data-testid (e.g. "bug_responder", "END").
            timeout: Maximum wait time in milliseconds.
        """
        self.page.wait_for_function(
            """([source, target]) => {
                const edges = document.querySelectorAll('.react-flow__edge');
                const prefix = `rf__edge-xy-edge__${source}`;
                for (const edge of edges) {
                    const testid = edge.getAttribute('data-testid') || '';
                    if (testid.startsWith(prefix) && testid.includes(`-${target}`)) {
                        return true;
                    }
                }
                return false;
            }""",
            arg=[source_id, target_id],
            timeout=timeout,
        )

    def open_state_panel(self, timeout: int = 5000) -> None:
        """Open the STATE side panel, if it's not already open (idempotent).

        The toggle button (``pipeline-state-drawer-toggle-button``) is only
        rendered in the DOM while the drawer is CLOSED (``FlowEditor.jsx``:
        ``{!isStateDrawerOpen && (...)}``), so its absence means the panel
        is already open.
        """
        if self.state_drawer_toggle_button.count() > 0:
            self.state_drawer_toggle_button.click(timeout=timeout)
        self.state_add_variable_button.wait_for(state="visible", timeout=timeout)

    def add_state_variable(self, name: str, timeout: int = 5000) -> None:
        """Add a new custom state variable via the STATE panel's '+' control.

        Opens a new-row textbox (``pipeline-state-add-variable-name-input``),
        types *name*, and commits via Enter. There is NO separate confirm
        (checkmark) button — live-reverified 2026-08-04 against
        ``StateVariableItem.jsx``/``StateVariableItemActions.jsx``: the
        create-mode row's only other controls are a disabled type-selector
        and a delete/cancel ("x") button. Committing (Enter, which blurs the
        field) unmounts the create-mode row, which this method waits on as
        its completion signal.
        """
        self.state_add_variable_button.click(timeout=timeout)
        self.state_add_variable_name_input.wait_for(state="visible", timeout=timeout)
        self.state_add_variable_name_input.click()
        self.state_add_variable_name_input.press_sequentially(name, delay=20)
        self.state_add_variable_name_input.press("Enter")
        self.state_add_variable_name_input.wait_for(state="detached", timeout=timeout)

    def close_state_panel(self, timeout: int = 5000) -> None:
        """Close the STATE side panel, if it's currently open (idempotent).

        The panel is a wide drawer that overlaps the canvas and intercepts
        clicks/dblclicks on nodes underneath it — close it before continuing
        with node-canvas interactions once state-variable setup is done.
        """
        if self.state_drawer_close_button.count() > 0:
            self.state_drawer_close_button.click(timeout=timeout)
            self.state_drawer_toggle_button.wait_for(state="visible", timeout=timeout)

    def get_state_variable_name_text(self, name: str, timeout: int = 5000) -> str:
        """Read a STATE panel row's display-mode name label text.

        Testid-based (``STATE_VARIABLE_NAME``) — the row's ``<Typography>``
        name label (``StateVariableItem.jsx``), which shows ONLY the
        variable's name, no type indicator (AFS ELITEA-2042 step 4
        clarification — the type is only observable via YAML/the row's own
        type-select icon).
        """
        locator = self.page.locator(self.STATE_VARIABLE_NAME.format(name))
        locator.wait_for(state="visible", timeout=timeout)
        return (locator.text_content() or "").strip()

    def is_state_variable_toggle_checked(self, name: str, timeout: int = 5000) -> bool:
        """Return whether a STATE panel row's toggle switch is checked.

        Testid-based (``STATE_VARIABLE_TOGGLE``) — the testid lands on the
        MUI ``SwitchBase`` span, which itself carries the ``Mui-checked``
        class when on; reading the class is compliant (the testid's
        presence/value is stable identity, state is read separately, same
        discipline as a ``data-*`` state filter per .agents/testing.md §
        Locator policy).
        """
        locator = self.page.locator(self.STATE_VARIABLE_TOGGLE.format(name))
        locator.wait_for(state="visible", timeout=timeout)
        return "Mui-checked" in (locator.get_attribute("class") or "")

    def is_state_variable_delete_button_present(self, name: str) -> bool:
        """Return whether a STATE panel row renders a delete control.

        Testid-based (``STATE_VARIABLE_DELETE``) — used for its ABSENCE on
        default rows (canon ruling #511 extension, absence assertions count
        as references): ``StateVariableItemActions.jsx``'s ``showToggle``
        branch (default rows) is mutually exclusive with the delete-
        ``IconButton`` branch, so a default row's delete testid is never in
        the DOM at all — this is a structural guarantee, not a timing race.
        """
        return self.page.locator(self.STATE_VARIABLE_DELETE.format(name)).count() > 0

    def click_state_variable_type_select(self, name: str, timeout: int = 5000) -> None:
        """Open a STATE panel row's type-selector dropdown.

        Testid-based (``STATE_VARIABLE_TYPE_SELECT``). The button is
        genuinely ``disabled`` while the row is still in create-mode
        (``StateVariableItem.jsx``: ``disableTypeSelector={isCreateMode ||
        !editable}``) — callers must commit the row's name first (see
        :meth:`add_state_variable`).

        Waits on the ``str`` (String) option's own testid rather than a raw
        ``[role="menu"]`` selector — ``StateTypeSelector.jsx`` renders all 4
        options unconditionally (never gated on the row's current type), so
        ``STATE_TYPE_OPTION.format("str")`` becoming visible is itself proof
        the dropdown opened, testid-only per .agents/testing.md § Locator
        policy.
        """
        locator = self.page.locator(self.STATE_VARIABLE_TYPE_SELECT.format(name))
        locator.click(timeout=timeout)
        self.page.locator(self.STATE_TYPE_OPTION.format("str")).wait_for(state="visible", timeout=timeout)

    def get_state_type_dropdown_options(self, timeout: int = 5000) -> list[str]:
        """Return the currently-open type dropdown's visible option labels.

        Call after :meth:`click_state_variable_type_select`. Reads all 4
        options via ``STATE_TYPE_OPTION``, keyed by INTERNAL type value
        (``str``/``number``/``list``/``dict``) in the fixed DOM order the
        component renders them (``StateTypeSelector.jsx`` iterates
        ``FlowEditorConstants.StateVariableTypes`` in declaration order).

        Returns:
            List of the 4 options' visible display labels, in DOM order
            (e.g. ``["String", "Number", "List", "Json"]``).
        """
        labels = []
        for type_key in ("str", "number", "list", "dict"):
            option = self.page.locator(self.STATE_TYPE_OPTION.format(type_key))
            option.wait_for(state="visible", timeout=timeout)
            labels.append((option.text_content() or "").strip())
        return labels

    def select_open_state_type_option(self, type_key: str, timeout: int = 5000) -> None:
        """Select *type_key* in the CURRENTLY-OPEN type dropdown.

        Use after :meth:`click_state_variable_type_select` (and, optionally,
        :meth:`get_state_type_dropdown_options` to inspect the options
        first) — mirrors this page object's existing open-then-select split
        for the Toolkit/Tool listbox (:meth:`select_open_listbox_option`).
        For the common "just pick this type" case without inspecting the
        options, prefer :meth:`select_state_variable_type`.

        Args:
            type_key: The option's INTERNAL type value (matches
                ``pipeline-state-type-option-{type_key}``, e.g. ``"str"``).
            timeout: Maximum wait time for the option to be clickable.
        """
        option = self.page.locator(self.STATE_TYPE_OPTION.format(type_key))
        option.click(timeout=timeout)
        # Testid-only close signal (see click_state_variable_type_select's
        # docstring) — all 4 options unmount together when the menu closes,
        # so "str" leaving the DOM is proof the dropdown closed.
        self.page.locator(self.STATE_TYPE_OPTION.format("str")).wait_for(state="hidden", timeout=timeout)

    def select_state_variable_type(self, name: str, type_key: str, timeout: int = 5000) -> None:
        """Open a row's type selector and choose *type_key* (internal value, e.g. ``"str"``) in one call."""
        self.click_state_variable_type_select(name, timeout=timeout)
        self.select_open_state_type_option(type_key, timeout=timeout)

    def is_state_type_option_selected(self, type_key: str, timeout: int = 5000) -> bool:
        """Return whether *type_key* is the CURRENTLY-SELECTED option in an open type dropdown.

        Call while the dropdown is open (after :meth:`click_state_variable_type_select`).
        Testid-based (``STATE_TYPE_OPTION``) — ``StateTypeSelector.jsx`` passes
        MUI's ``MenuItem`` a ``selected={isSelected}`` prop, which renders a
        ``Mui-selected`` class on the option when it matches the row's current
        type; reading the class is compliant (the testid's presence/value is
        stable identity, state is read separately — same discipline as
        :meth:`is_state_variable_toggle_checked`'s ``Mui-checked`` read).
        """
        option = self.page.locator(self.STATE_TYPE_OPTION.format(type_key))
        option.wait_for(state="visible", timeout=timeout)
        return "Mui-selected" in (option.get_attribute("class") or "")

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
