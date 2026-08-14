---
name: RTK-Query cache hit — no network request on project switch-back
description: Switching the sidebar project selector back to a project whose query (same params) already resolved earlier in the test is a cache HIT — no new request fires, so wrapping the click in expect_response times out.
type: feedback
---

Seen implementing ELITEA-2320 (`AnalyticsPage.switch_project`, Agents & Pipelines
tab). Any RTK-Query-backed data fetch (`useAnalyticsAgentsQuery` etc.) is cached
per exact query-key (project id + date range + search + pagination). Switching
the active project A -> B -> A within one test: the A -> B leg fires a genuine
network request, but the B -> A leg is very often served straight from cache
(same params as the original tab-mount fetch) — **no new request fires at all**.

Wrapping the click in `page.expect_response(...)` unconditionally therefore
times out on the cache-hit leg (confirmed live: 15s timeout on the second
`switch_project` call in a personal -> non-personal -> personal round trip).

**Fix (same pattern as `_wait_for_users_settled`/`clear_users_search`,
ELITEA-2312):** don't assume a response always fires. Click, then
`wait_for_network(timeout=...)` (networkidle) + wait for the tab's own
loading-indicator testid to be hidden (`wait_for(state="hidden")` resolves
instantly if already hidden — handles both the cache-hit and fresh-fetch
cases without a race).

Also found while exploring (NOT exercised by the test, out of scope for
ELITEA-2320): switching the active project while a row-click detail
sub-view is open does NOT reset the component's local `selectedAgent`
state — the detail query refires with the NEW project id but the STALE
`entity_id`, producing a 404. Real edge case, not filed (out of AFS scope);
flag to the lead if a future case needs to touch project-switching from
inside a detail sub-view.
