---
name: Pipeline STATE panel overlap + Page.wait_for_function arg kwarg
description: STATE side drawer intercepts canvas clicks underneath it; Playwright Python wait_for_function needs arg= as keyword
type: feedback
---

## STATE panel overlaps the canvas — close it before further canvas work

`FlowEditor.jsx`'s STATE side drawer (opened via the "State" toggle button,
now `pipeline-state-drawer-toggle-button`) is a wide panel that overlaps the
right side of the canvas while open. Any node that lands underneath it —
including a freshly-added node from `add_node()` — gets its dblclick/click
intercepted by the drawer's own content subtree ("... intercepts pointer
events" in Playwright's error). Two live-confirmed failure modes this
session (ELITEA-2034):

1. Opening the STATE panel *before* adding/renaming target nodes → the
   rename's dblclick on a Printer node fails.
2. Leaving the STATE panel open after adding state variables → a
   subsequently-added Decision node's Input select click fails.

**Fix pattern:** do all canvas node add/rename work FIRST, then open the
STATE panel, add variables, and close it again (`close_state_panel()`) BEFORE
resuming any other canvas interaction. Added `pipeline-state-drawer-close-button`
testid (`StateDrawer.jsx`'s existing close IconButton had none) plus
`PipelineDetailPage.open_state_panel()` / `add_state_variable()` /
`close_state_panel()` methods — reuse these rather than re-deriving the
open/add/close flow.

Also: STATE panel's new-variable row has **no separate confirm/checkmark
button** despite what a stale AFS may claim — the name commits on blur or
Enter (`handleNameBlur` in `StateVariableItem.jsx`). The row's only other
controls are a disabled type-selector and a delete/cancel ("x") affordance.

## `page.wait_for_function()` — `arg` must be a keyword, not positional

Playwright Python's signature is
`wait_for_function(expression, *, arg=None, timeout=None, polling=None)` —
`arg` is keyword-only. Passing the JS function's argument list positionally
(`page.wait_for_function(js, [a, b], timeout=...)`, the natural port from the
JS API's `page.waitForFunction(fn, arg, options)`) raises
`TypeError: Page.wait_for_function() takes 2 positional arguments but 3
were given`. Always `page.wait_for_function(js, arg=[a, b], timeout=...)`.
