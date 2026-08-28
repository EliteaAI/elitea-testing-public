---
name: Wait-vs-masking test for a repair PR
description: How to decide whether an added wait is an honest fix or papering over a product defect
type: feedback
---

When a repair PR fixes a red test by **adding a wait**, the reviewer's job is to
decide whether the product is correct and the test sampled too early, or whether
the wait is hiding a real defect. Three checks settle it from source — no
execution needed:

1. **Does the product render an honest in-flight state?** Read the component.
   If it renders a real `Loading...` branch while fetching, and the empty/"no
   results" branch is guarded `{!isLoading && items.length === 0 && …}` (i.e.
   the two are **mutually exclusive**), the user is never shown a misleading
   empty view. Product correct → the wait is honest.
   If the empty-state branch can render *during* the fetch, the user sees a
   false "nothing here" and that IS a product defect — `CHANGES_REQUESTED` +
   file a `bug`, no matter how green the runs were.

2. **Can the waited-for handle match the placeholder?** If the loading/empty
   placeholders carry **no testid** and the wait targets a testid rendered only
   from `items.map(...)` (i.e. only from response data), the wait cannot
   manufacture a pass — it can only be satisfied by product-produced rows.
   If the placeholder shares the handle, the wait is a tautology.

3. **Is the wait stronger or weaker than the assertion it precedes?**
   `wait_for(state="visible")` on the first row is *stricter* than
   `.count() > 0` (which counts attached-but-hidden nodes). Stronger → no
   weakening. Note the side effect: the wait becomes the effective oracle and
   a genuine product failure surfaces as a Playwright `TimeoutError` rather
   than the crafted assertion message. That is still an honest red, but say so.

Worked instance: ELITEA-2065 / ELITEA-1955 "+ MCP" popper. `EliteaAI/EliteaUI@94a61b81`
(EL-6351) made `ToolMenu.jsx` pass `forceSkip = !mcpOpened.current` into
`useLibraryToolkits`, so the toolkit-list request only starts on first "+ MCP"
click. `UnifiedDropdown.jsx` renders an untestid'd `Loading...` MenuItem while
`isFetching`, and its empty message is guarded `!isLoading` — all three checks
pass, so the wait was the honest fix.

**Related trap:** Playwright auto-waiting does NOT apply to `.count()`. Any
`.count()`-based assertion on lazily-loaded content is a guaranteed-empty
sample unless the caller waits first.
