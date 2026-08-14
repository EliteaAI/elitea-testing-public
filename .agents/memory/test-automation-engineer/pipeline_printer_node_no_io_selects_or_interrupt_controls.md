---
name: Pipeline Printer node has no Input/Output selects or Interrupt/Structured-output controls
description: PrinterNode.jsx shares SimpleLLMInputs with Code/LLM for the PRINTER Type/Value pair plus a standalone AIAssistantInput Final Message field, but renders NO FlowEditorSelect.InputSelect/OutputSelect and NO CommonInterruptSettings at all — only the two generic ReactFlow handles (ELITEA-2039)
type: feedback
---

## Printer node config shape (confirmed live + via source, 2026-08-08)

`PrinterNode.jsx` (`EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/nodes/PrinterNode.jsx`):

- Renders `FlowEditorSettings.SimpleLLMInputs` (SAME shared component as the
  Code node's CODE section and the LLM node's SYSTEM/TASK/CHAT HISTORY
  sections) with a single mapping key `printer` (label renders "Printer",
  default `{type: 'fixed', value: ''}` via `usePrinterInputMapping.js`).
- Renders a standalone `AIAssistantInput` for `final_message` — NOT part of
  `SimpleLLMInputs`, a separate call site.
- Renders **NEITHER** `FlowEditorSelect.InputSelect`/`OutputSelect` **NOR**
  `FlowEditorSettings.CommonInterruptSettings` — confirmed via source (no
  such import/usage in the file) AND live DOM (`#simple-select-Input`/
  `#simple-select-Output` both 0 matches inside the node; no "Interrupt"/
  "Structured output" substrings in the node's `textContent`). This makes
  Printer the ONLY node type in this suite (vs LLM/Code/HITL/MCP/Toolkit/
  Router/Decision/State-modifier/Custom/Agent, all of which have at least
  Input/Output) with zero state-var comboboxes.
- Only the two generic ReactFlow `CustomHandle` connection points exist
  (`target` top, `source` bottom) — `.react-flow__handle` count == 2 on a
  fresh Printer node, before AND after Save+reload.

## Testid wiring added this session

`PRINTER_NODE_INPUT_TEST_IDS` map (same shape as `CODE_NODE_INPUT_TEST_IDS`
in `CodeNode.jsx`, ELITEA-2009) wired via `testIdsByKey` on the
`SimpleLLMInputs` call site (`pipeline-printer-node-type-select`,
`pipeline-printer-node-value`), plus `inputProps={{'data-testid': ...}}`
directly on the `AIAssistantInput` call site for Final Message
(`pipeline-printer-node-final-message-input` — MUI `TextField`'s `htmlInput`
slot, same pattern as `styledinputenhancer_data_testid_needs_inputprops_not_bare_prop.md`).
Commit: `EliteaAI/EliteaUI@955f88b9` on `automation/testids`.

## Page-object additions of general use beyond this case

Added `PipelineDetailPage.get_node_handle_count(node_id)` and
`.get_node_state_var_select_count(node_id)` — generic per-node DOM-structure
checks (`.react-flow__handle` count; `#simple-select-Input`/
`#simple-select-Output` count) via `page.evaluate` scoped to a `[data-id="..."]`
node, same sanctioned pattern `delete_node()` already used. Any future
node-type case needing to assert "this node has N connection handles" or
"this node has zero state-var selects" should reuse these rather than
re-deriving inline `page.evaluate` calls in a test file.
