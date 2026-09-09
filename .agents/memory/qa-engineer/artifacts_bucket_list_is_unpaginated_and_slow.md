---
name: Artifacts bucket list is unpaginated, unvirtualised and ~10s slow on DEV
description: The panel's /artifacts/s3/ list returns every bucket in one response; budget any post-mutation bucket wait at 60s, never 15s
type: project
aliases: [bucket list latency, artifacts-bucket-row timeout, wait_for_bucket_in_list, /artifacts/s3/]
tags: [area/artifacts, type/timing]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

`GET /artifacts/s3/?project_id={p}&format=json` — the request the Artifacts left panel
consumes (`src/api/artifacts.js` `bucketList`) — is **unpaginated**, and
`SimpleBucketList.jsx` renders **every** row (no windowing library anywhere under
`src/pages/Artifacts/`).

Measured 2026-09-09, idle local machine → `dev.elitea.ai`, project 399 (**1221 buckets**):

| | |
|---|---|
| list response | 9.56 – 11.60 s, 238 KB (8 samples) |
| create POST 200 → list refetch | 9.56 / 10.11 / 9.63 s |
| create POST 200 → new row visible | 10.75 / 11.29 / 10.83 s (render adds ~1.2 s) |
| `navigate_to_artifacts()` | 17.78 s |
| rows in the DOM | 1219 – 1222 |

Under CI load the same request measured **12.4 – 43.8 s** (#2066).

## What follows

- Any wait tied to the post-mutation bucket-list refetch needs a **60 s** budget
  (`BUCKET_LIST_RESPONSE_TIMEOUT`), never a spec-level 15 s `NAVIGATION_TIMEOUT`. That
  15 s is what made ELITEA-1808 red in CI (#2084).
- **Never** blame paging/virtualisation for a missing bucket row — everything is in the
  DOM, and Playwright's `visible` does not require the viewport.
- Order is **alphabetical**, not recency (the sort is dead — [[artifacts_bucket_panel_sort_is_dead]], #2126).
- The latency is 96% self-inflicted: 1176 of the 1221 buckets are leaked `autotest-*`
  ones — see [[artifact_api_delete_bucket_calls_a_nonexistent_route]].

Related: [[artifact_api_delete_bucket_calls_a_nonexistent_route]]
