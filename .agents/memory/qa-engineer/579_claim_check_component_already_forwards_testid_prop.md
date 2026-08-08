---
name: 579 claim check component already forwards testid prop
description: A #579 "library-internal DOM" claim is void if the app component already forwards a testId prop to that DOM node — check source before accepting it.
type: feedback
---

## What happened

ELITEA-2039 (Pipeline Printer node) round-1 review flagged
`get_node_state_var_select_count()` — a `page.evaluate()` raw DOM query
against MUI-auto-generated ids — as NOT a sanctioned #579 exception, because
the underlying `Select.SingleSelect` component already accepted a real
`data-testid` (wired by every other node type via a `dataTestId` prop). The
implementer fixed it correctly.

But the SAME PR's `get_node_handle_count()` (pipeline_detail_page.py, added
in the very first commit, untouched by the round-1 fix) does the identical
thing one layer down: `page.evaluate()` + `document.querySelector` to count
`.react-flow__handle` descendants, justified in its docstring as "sanctioned
#579 exception, same class of handle `get_node_count()` already uses."

That justification does not hold up against source. `get_node_count()`'s
`.react-flow__node` is ReactFlow's own auto-injected wrapper — no app opt-in
possible, a real #579 case. But `.react-flow__handle` elements are rendered
by the APP's own `CustomHandle.jsx` component
(`EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/nodes/CustomHandle.jsx`),
which already destructures a `testId` prop and forwards it as
`data-testid={testId}` on the underlying `<Handle>` — nobody has ever passed
that prop from any node type (LLM/Printer/StateModifier/Agent/Subgraph all
omit it), but the plumbing exists. "Missing testid alone ⇒ add it," not a
rung-down to a raw DOM query — same rule the round-1 finding already
established, missed because it looked like reused, already-approved
precedent (superficially resembling `get_node_count()`).

## Lesson for review

When a new raw-DOM/`page.evaluate()` handle in a diff cites "sanctioned
#579 exception, same as `existing_method()`" — don't take the analogy at
face value. Read the actual rendering component's source (one grep away):
does it already destructure and forward a testid-shaped prop
(`testId`, `dataTestId`, etc.) to the DOM node being queried? If yes, the
exception doesn't apply regardless of how library-internal the CSS class
looks (`.react-flow__handle` LOOKS as library-internal as `.react-flow__node`,
but one is auto-injected by the library and the other is app-rendered with
opt-in testid support already wired). This is exactly the class of bug the
mechanical grep (`get_by_role|...|page\.locator|\.locator\(`) does NOT
catch — `page.evaluate()` with an inline `document.querySelector` string
evades it entirely, so this check has to be manual, every time a
`page.evaluate` shows up in a reviewed diff touching `automation/pages/`.
