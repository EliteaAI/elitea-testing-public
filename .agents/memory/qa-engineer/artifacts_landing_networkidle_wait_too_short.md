---
name: navigate_to_artifacts()'s 15s networkidle wait is below the observed floor
description: Project 399 has 1217 buckets; the unpaginated bucket-list GET takes 12.4-43.8s, so the 15s networkidle wait fails deterministically.
type: project
aliases: [navigate_to_artifacts timeout, artifacts networkidle, Navigate to Artifacts Timeout 15000ms, artifacts s3 slow]
tags: [area/artifacts, type/flake, status/open]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

`ArtifactsPage.navigate_to_artifacts()` → `wait_for_page_load(15000)` →
`BasePage.wait_for_network(15000)` → `page.wait_for_load_state("networkidle", 15000)`.

Measured live 2026-09-09 on `localhost:5173`, project `Private` / **399**, which holds
**1217 buckets**:

| Observation | Value |
|---|---|
| `GET /artifacts/s3/?project_id=399&format=json` (backend healthy, unpaginated) | **43.8 s**, 200 OK |
| `goto('/artifacts')` → first `artifacts-bucket-row-*` rendered | **12.4 s** and **15.2 s** (two loads) |
| same, backend under load | 502 / 503, list never rendered inside 80 s |
| the wait's budget | **15 000 ms** |

The budget sits at or below the floor, and the app also holds a persistent `/socket.io/`
poll open — the [[#1847]] `networkidle` mechanism. It fails on a **clean pre-test call**,
not only after a mid-test failure (ELITEA-1866's run logged it twice: pre-test cleanup and
post-test cleanup, both at `:209`).

## Consequences

- Bucket cleanup silently no-ops, leaving exactly **one** stale bucket per name (names are
  unique per project, so it does not pile up — but it never gets removed either).
- Any spec calling `navigate_to_artifacts()` **unguarded** inherits the failure.
  ELITEA-1866's Step 32 does exactly that.

## The fix, when someone touches it

#1847's own prescription — wait on what the caller needs, not on network silence: wrap the
navigation in `page.expect_response(lambda r: "/artifacts/s3/" in r.url and r.status == 200,
timeout=60_000)`. Use the **response**, not a bucket row (wrong for a genuinely-empty
project) and not the empty-state element (poisoned by #2073's false "No buckets created
yet" during load). Precedent: the same removal in `AdminUsersPage` made settings-w09 both
stabler and ~56 s faster.

Related: #636 (bucket delete 404s — the other half of the 1217-bucket accumulation),
#638, #2073, [[toolkit_test_result_text_content_collapses_newlines]]
