---
name: AFS "on-main" testid provenance claims keep turning out false — re-verify every time
description: two confirmed cases (Agent Hub catalog, Run History row) where a dated "on-main ✓" AFS claim was false — never inherit, always fresh-fetch+grep
type: feedback
---

**Confirmed twice now — this is a pattern, not a one-off.**

1. **ELITEA-2363 analysis (2026-08-06):** a fresh `git fetch origin` + `git grep`
   against `origin/main` in `../EliteaUI` showed `catalog-page-heading`,
   `catalog-search-input`, and `catalog-agent-card-{id}` do **NOT** exist on
   `origin/main` — contradicting
   `test-specs/agent-hub/l3_agent-hub-like-agent-from-list-view_ELITEA-2354.md`
   § Concrete Handles, which listed all three as "on-main ✓ (pre-existing,
   ELITEA-2075)". All three were only on `origin/automation/testids`.
2. **ELITEA-1876 review (2026-08-07, PR #1283):** the AFS
   (`test-specs/agents/lextend_run-history-list-shows-timestamp-and-version-duration_ELITEA-1876.md`)
   claimed `run-history-list-item` was "on-main ✓ (pre-existing, reused as-is
   — verified via `git fetch origin` + `git grep`... origin/main, 2026-08-06)".
   A fresh fetch+grep at review time found **zero** matches anywhere on
   `origin/main` (HEAD `8195b5af`, 2026-08-06T13:25) — the testid (added
   alongside `data-selected` as part of ELITEA-1877's implementation) exists
   only on `origin/automation/testids` (HEAD `cc327ec9`, later the same day).
   The claimed verification command, run fresh, contradicted the AFS's own
   dated claim from the SAME day.

Neither case was root-caused (stale claim at write time vs. main moving/
resetting after) — and it doesn't matter which: the point is a dated
"verified" stamp in an AFS is not load-bearing on its own.

Lesson: this is exactly the fresh-ground-truth rule in
`.agents/role-overrides.md` doing its job — a PROVENANCE column (in ANY
AFS, written by anyone, on any surface, however recently dated) is a claim
to re-verify with your OWN fresh `git fetch origin` + `git grep` against
`origin/main`, never a fact to inherit or cite forward. This applies as
much to a reviewer checking an implementer's/analyst's claim as to an
analyst reusing a neighbour AFS. Don't let "verified 2026-08-06" read as
"still true" — check it yourself, every time, regardless of how fresh the
date looks.
