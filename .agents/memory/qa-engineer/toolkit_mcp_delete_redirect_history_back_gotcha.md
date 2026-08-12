---
name: Toolkit/MCP delete-redirect is navigate(-1), not a fixed route
description: Post-delete redirect on Toolkit/MCP detail pages is browser-history "go back", not a fixed navigate-to-list — self-caught near-false-positive on ELITEA-1947, path matters for automation correctness
type: feedback
---

## What (confirmed live + via source, ELITEA-1947, 2026-07-18)

`useDeleteToolkit()` in `DeleteToolkitButton.jsx` redirects after a successful
delete via:

```js
if (window.history.length > 1) {
  navigate(-1);
} else {
  navigate((!isMCP ? RouteDefinitions.ToolkitsWithTab : RouteDefinitions.MCPsWithTab)
    .replace(':tab', 'all'), { replace: true });
}
```

This is "go back one browser-history entry", NOT a fixed redirect to the
Toolkits/MCP list — the fallback-to-list branch only fires when
`window.history.length <= 1` (essentially never true in a real session).

## Why this bit me

First exploration pass: created an MCP, stayed on its own post-create detail
page (`/mcps/all/{id}`), and deleted immediately — WITHOUT an intervening
navigation to the list. The immediately-prior history entry was the create
flow's own type-picker (`/mcps/create`), so `navigate(-1)` landed there instead
of on `/mcps/all`. This LOOKED like a real product bug matching the case's own
step-8 failure condition ("redirected to MCP list" not satisfied).

Re-ran clean, following the case's own literal step order (create → navigate to
list via sidebar → open the MCP FROM its list card → delete) — this time
`navigate(-1)`'s target was correctly the list page, matching expected behavior
both times (verified with a fresh second MCP, id 1475).

**Verdict: NOT a defect.** The case's own step sequence is exactly what makes the
history-back redirect land correctly. My first pass's shortcut (staying on the
create flow's own redirect instead of visiting the list) produced a misleading
result that would have been a false-positive bug report if filed without the
re-run.

## Automation implication

Any automated test for a Toolkit/MCP delete flow MUST open the detail page via
a real navigation FROM the list (e.g. click an `entity-card-name` from
`/mcps/all`), not by reusing the create flow's own post-save detail-page
reference/URL — or the post-delete redirect assertion will be flaky/wrong. This
is load-bearing for test correctness, not a style preference.

## Where

`EliteaUI/src/pages/Toolkits/DeleteToolkitButton.jsx` (`useDeleteToolkit`),
AFS: `test-specs/mcp/l3_delete-remote-mcp_ELITEA-1947.md` § Known Defects Found
(full investigation write-up) and § Automation Hints.
