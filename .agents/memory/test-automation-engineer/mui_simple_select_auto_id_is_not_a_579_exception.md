---
name: MUI SingleSelect auto-id is not a #579 exception
description: >-
  #simple-select-<Label> DOM ids on pipeline node Input/Output selects look
  library-internal but are NOT a sanctioned #579 exception — add a testid instead.
type: feedback
---

## What happened (ELITEA-2039, PR #1324, fix round 1)

An absence check ("does this pipeline node render an Input/Output
state-variable combobox") was implemented as
`page.evaluate("...querySelectorAll('#simple-select-Input, #simple-select-Output')...")`.
It looked like a sanctioned #579 exception (same shape as the ReactFlow
`.react-flow__handle` count check right next to it in the same file) but
reviewer correctly flagged it as `CHANGES_REQUESTED`.

## Why it's NOT #579

`#simple-select-<Label>` comes from EliteaUI's own
`src/[fsd]/shared/ui/select/SingleSelect.jsx`:
```js
id={id || 'simple-select-' + label}
data-testid={dataTestId}   // <-- also rendered, when the caller passes it
```
This is an **app-owned component**, not a third-party library's internal
render node (ReactFlow / CodeMirror / Monaco / ProseMirror — the only two
sanctioned #579 classes). It already accepts a real `data-testid` — every
node type that DOES render this select passes one (`code_node_input_select`
→ `dataTestId="pipeline-code-node-input-select"` in `CodeNode.jsx`, same
pattern for LLM/State-modifier/Agent/Toolkit/Custom/MCP/HITL/Router/Decision).
The MUI auto-id is a coincidence of no `id` prop being passed, not a
library-internal DOM node — so it's normal "testid needed", not "raw handle
sanctioned".

## The absence-check trap this case hit

The node under test (Printer) never renders `FlowEditorSelect.InputSelect`/
`OutputSelect` at all (confirmed via source) — so there is no live element to
put a testid ON. You can't "add a testid" to something that doesn't render.
**Fix:** declare the `LocatorDescriptor(testid="pipeline-<type>-node-input-select")`
anyway, following the exact naming convention every OTHER node type's real
Input/Output select testid uses, and assert `.count() == 0` — same pattern
as existing absence checks elsewhere in this file
(`chat_hitl_edit_button.count() == 0`, `toolkit_card.count() == 0`). This
also gives real forward regression protection: if a future PrinterNode.jsx
change reintroduces the select AND follows the established testid naming
convention, the count flips to 1 and the test genuinely fails.

## Rule of thumb

Before treating any raw CSS-id/class DOM query as a #579 exception, check:
is this element's component OWNED by EliteaUI (`src/[fsd]/...`) or a
third-party library? If app-owned, it can carry a `data-testid` — the fix is
`add-data-testid` (or, for pure-absence assertions on an element that
structurally never renders, a same-convention testid `LocatorDescriptor` used
only for `.count() == 0`), never a raw selector.
