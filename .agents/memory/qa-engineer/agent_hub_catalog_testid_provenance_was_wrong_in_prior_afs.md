---
name: Agent Hub catalog testid provenance was wrong in a prior AFS
description: ELITEA-2354's "on-main (pre-existing)" claim for catalog testids was false as of 2026-08-06 — re-verify, don't copy
type: feedback
---

During ELITEA-2363 analysis (2026-08-06), a fresh `git fetch origin` +
`git grep` against `origin/main` in `../EliteaUI` showed that
`catalog-page-heading`, `catalog-search-input`, and `catalog-agent-card-{id}`
do **NOT** exist on `origin/main` — `EliteaCatalog.jsx` there has no
`data-testid` on the heading or search `TextField` at all, and a grep for
`catalog-agent-card-` returns zero hits. All three ARE on
`origin/automation/testids`.

This directly contradicts `test-specs/agent-hub/l3_agent-hub-like-agent-from-list-view_ELITEA-2354.md`
§ Concrete Handles, which lists all three as "on-main ✓ (pre-existing,
ELITEA-2075)". Whether that claim was wrong when made, or `main` was
reset/force-pushed since, wasn't root-caused (out of scope for the case).

Lesson: this is exactly the fresh-ground-truth rule in
`.agents/role-overrides.md` doing its job — a prior AFS's PROVENANCE column
is a claim to re-verify, not a fact to inherit. Any future case touching the
Agent Hub / Catalog surface (`/elitea-catalog`): re-run the fetch+grep
yourself before citing any of this surface's testids as on-main; don't
propagate this or any other prior file's claim forward. Full correction
recorded in `test-specs/agent-hub/_surface.md` (top section) and in
ELITEA-2363's own AFS.
