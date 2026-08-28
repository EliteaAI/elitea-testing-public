---
name: Version-create read race (copy-version-id lags the VERSION trigger)
description: After Save As Version, copy-version-id lags the trigger/URL by ~0.7s — read it only via the three-way convergence predicate
type: feedback
aliases: [save as version race, copy-version-id stale, VERSION_CONVERGED_JS, isFromCreation]
tags: [area/versions, type/race]
created: 2026-08-28
updated: 2026-08-28
---

## The race

Two version signals in EliteaUI come from DIFFERENT sources:

- `agent-version-selector-trigger` — `ApplicationVersionSelect.jsx:81`
  (`if (isFromCreation) return version;`) reads the **URL path param
  synchronously**, so it flips the instant the route changes.
- `copy-version-id` — `ApplicationInformation.jsx:35` renders
  `version_details?.id` from **Formik**, written only after the async
  version-detail GET lands.

So trigger-text and URL are the SAME source, and neither proves the new
version's data arrived. Any `get_version_id()` between the two reads the
PREVIOUS version's id.

## Measured live (2026-08-28, localhost:5173, pipeline Save As Version)

```
t=+   0ms  dialog Save clicked; url=/pipelines/all/10109 (NO version segment)
t=+ 256ms  dialog hidden
t=+1159ms  POST 201 /versions/prompt_lib/399/10109 -> {"id":10523,"name":"v1_test"}
t=+1374ms  url -> /pipelines/all/10109/10523?...&isFromCreation=true ; copy-version-id STILL 10522
t=+1479ms  trigger -> 'v1_test'                                     ; copy-version-id STILL 10522
t=+2139ms  copy-version-id -> 10523  (after GET /version/.../10523)
```

~660 ms window in which trigger says the new name and `copy-version-id`
still says the old id.

## The only safe wait

The three-way predicate (`AgentDetailPage.VERSION_CONVERGED_JS`,
`agent_detail_page.py:126`): trigger text == name **and**
`copy-version-id` non-empty **and** it equals the URL's last path segment.

## Two traps in the same neighbourhood

1. `wait_for_function("prevId => pathname.split('/').pop() !== prevId")`
   after a Save-As-Version is a **guaranteed no-op**: pre-save the last
   path segment is the ENTITY id, `prevId` is a VERSION id, so the
   predicate is already true at t=0. Verified live.
2. `wait_for_network()` is `networkidle` (#1847) and resolves in the dead
   gap between the POST completing and the follow-up GET being issued.

## `PipelineDetailPage.wait_for_network()` is a SWALLOWED wait (review finding, 2026-08-28)

Worse than trap 2 above, and easy to miss because the name promises a wait.
`PipelineDetailPage` **overrides** `BasePage.wait_for_network`
(`pipeline_detail_page.py:1755`) with a `try/except` that logs at debug and
**continues** — its own docstring says persistent WebSocket connections
(Vite HMR + socket.io) "prevent networkidle from ever being reached" on this
page. So on the pipeline detail page `self.wait_for_network(timeout=N)` is
either an unconditional N-ms dead sleep or an early return in the POST→GET
gap. It never asserts anything and never guarantees anything. **8 call sites
in that file.**

Consequence for review: removing a `wait_for_network()` from this page can
never remove coverage — but treat any *remaining* one that is followed by a
Formik-backed read as a live stale-read race.

Still carrying that exact shape after the ELITEA-2002 fix:
`wait_for_fallback_to_base()` (trigger-text-only `wait_for_function` →
`wait_for_network(5000)` → `return self.get_version_id()`), and its docstring
still claims it "mirrors `confirm_new_version`'s wait strategy" — no longer
true once `confirm_new_version` moved to `VERSION_CONVERGED_JS`.

The backend is correct throughout — it genuinely creates a new version
with a new id (POST 201 body proves it). Only the read is racy.

Related: [[[test-automation]]] issues #1872 (agents), #1874/#1893 (pipelines).
