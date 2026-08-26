---
name: Artifacts area backlog (#1392) — outcome and what is still parked
description: 35 automated + 2 sanctioned-RED across 6 waves; the 8 leftovers are all human-decision blocks, not unfinished work
type: project
aliases: [artifacts backlog, ELITEA-18xx, bucket permissions, artifacts coverage]
tags: [area/artifacts, status/blocked]
created: 2026-08-23
updated: 2026-08-23
---

## Outcome

Area coverage **26 → 63 of 73** TMS cases. Six waves, all merged to `automation/base`:
w01 #1625 · w02 #1633 · w03 #1642 · w04 #1686 · w05 #1696 · w06 #1702 (docs-only).

## The 8 that did NOT get automated — none is "unfinished"

Each is parked on a human decision, with the analysis preserved so no
re-exploration is needed:

| Case(s) | Wall | Card |
|---|---|---|
| ELITEA-1806 | no bucket-free project reachable; faking = terminal substitution | #1626 |
| ELITEA-1867 | case text **inverted** — toolkit creation with an existing bucket name succeeds | #1685 |
| ELITEA-1865 | the "Context Management" panel isn't on that surface (lives in `context-budget`; already covered by ELITEA-2374) | #1695 |
| ELITEA-2488/2489/2490 | need a 2nd/3rd **logged-in** identity on a **deployed** env | #1697 |
| ELITEA-2491 | Public project (id=1) unreachable by the test user | #1699 |
| ELITEA-2492 | every bucket-permission **write** 403s for the acting user | #1701 |

## The multi-user wall (reusable fact)

`auth_state_user_b` skips twice over: `TEST_USER_B_EMAIL`/`PASSWORD` are empty,
**and** `session_fixtures.py:158` skips all multi-user tests on localhost because
the `VITE_DEV_TOKEN` bypass authenticates exactly one identity. So **no multi-user
case can ever be verified by the local pipeline** — it needs credentials *and* a
deployed target. Merged `test_bucket_permissions_api.py` (ELITEA-2493/2494) has the
same dependency and is therefore almost certainly **skipping, not passing**.

## Surface gotchas worth knowing before touching artifacts

- The file table lists in **modification order, not name-ascending** — assert partitions, never named slices.
- The buckets listing is **eventually consistent**; footer-vs-rendered-rows is the race-free check, UI-vs-API is not.
- `Exceptions - 0` uses an **en dash** (U+2013) — a hyphen assertion never matches.
- Team-project menu item **count** is permission-dependent — assert the item, never the count.
- Project 399 holds ~970 buckets (teardown leak #636), so bucket-list waits need a longer timeout than the shared 15 s.

Related: [[workflow_gate_verdict_is_not_the_merge_gate]]
