---
name: Pipeline node Output select reuses Input's non-creatable options hook
description: Pipeline node Output/Input state-var selects (LLM/Decision/Code/...) all use useInputOptions() — never freeform; new var needs STATE panel first
type: feedback
---

`OutputSelect.jsx` and `InputSelect.jsx` (pipeline flow-editor,
`src/[fsd]/features/pipelines/flow-editor/ui/select/`) both call the SAME
`useInputOptions()` hook — Output is NOT a separate/freeform/creatable
field despite its different name. A fresh pipeline's Input/Output option
list is `["input", "messages"]` only; any other name (e.g. a Code node's
`result`) must be created first as a custom state variable via the STATE
panel (`PipelineDetailPage.open_state_panel()` +
`add_state_variable(name)`, then `close_state_panel()` before touching
canvas nodes — the open drawer intercepts pointer events).

Confirmed on 3 node types now: Decision's Input (ELITEA-2034), Code's
Output (ELITEA-2009), and by extension every other node type sharing
`InputSelect`/`OutputSelect` (LLM, Toolkit, MCP, Router). Case texts that
list an Output value like a case's Test Data table's "Output variable:
result" almost always assume this is freeform — it isn't. File as a
case-text CLARIFICATION (not a defect), same umbrella as
`#1104`/`#1136`/`#1137`/`#1144`/ELITEA-2034's finding — don't re-litigate
per case.

Testid wiring for a NEW node type's Input/Output/CODE-family fields
follows the SAME opt-in-prop mechanism every time: `dataTestId` on
`InputSelect`/`OutputSelect`, `testIdsByKey` on `SimpleLLMInputs` (per-key
`typeSelectTestId`/`valueFieldTestId`), `interruptAfterTestId`/
`structuredOutputTestId` on `CommonInterruptSettings` — all pre-plumbed
generically; only the call site (e.g. `CodeNode.jsx`) needs edits. No new
component code needed for a node type that already renders these shared
components untagged.
