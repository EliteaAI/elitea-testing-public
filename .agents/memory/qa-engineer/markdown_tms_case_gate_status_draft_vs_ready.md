---
name: Markdown TMS case-gate — status draft vs ready
description: onetest-ai-tm-Elitea status:draft is the normal PRE-automation state (proceed); status:ready + execution_type:automated + populated automation_test_id is the POST-automation state (skip as already-covered). There is no author not-actionable gate on draft for this TMS.
type: feedback
---

CORRECTED 2026-07-17 — supersedes the original version of this entry, which
was WRONG and must not be relied on. The original entry asserted `status:
draft` was an author-set "not actionable" gate that should short-circuit
Phase 0 (`out-of-scope-by-author`, no fetch, no execution). That is backwards
for this project's onetest TMS and misroutes nearly every ELITEA case, since
almost all cases sit in `status: draft` prior to automation.

Ground truth, per `.agents/test-automation.yaml`:

- § `intake.selector` filters cases FOR THIS PIPELINE by `status: draft` +
  `tags: [automated:UI:regression]` — draft is the TARGET population to
  automate, not an exclusion.
- § `intake.already_automated_when` requires ALL THREE of `execution_type:
  automated`, `status: ready`, and non-empty `automation_test_id` to treat a
  case as already covered. `status: ready` is the POST-automation state that
  `backwrite_on_done` writes back after merge — not a precondition to start.
- Confirmed empirically: ELITEA-1737 and ELITEA-1922 (both already automated,
  PRs merged) carry `status: ready` + `execution_type: automated` +
  populated `automation_test_id`/`automation_pr`. ELITEA-1933 has `status:
  draft`, `execution_type: manual`, no `automation_test_id` — exactly the
  shape of a normal, not-yet-automated case, same as every other
  pre-automation case in this pipeline.

Corrected rule for onetest TMS cases in this repo (Phase 0 case-gate):

- `status: draft` + `execution_type: manual` → normal pre-automation state.
  PROCEED to fetch + execute (do not return `out-of-scope-by-author`).
- `status: ready` + `execution_type: automated` + populated
  `automation_test_id` → already automated. Skip as `already-covered`.
- Any other combination (e.g. `ready` but `execution_type: manual`, or
  `draft` but `automation_test_id` populated) → contradictory metadata;
  report, don't guess, don't skip silently (per
  `test-automation.yaml` § `intake.contradictory_metadata`).

There is NO generic "Draft = author hasn't finished, skip it" gate on this
TMS — that's a generic-TMS convention the `test-case-analysis` skill's
example alludes to, but this project's own `test-automation.yaml` seed
overrides it for onetest cases. Do not re-derive the wrong rule from
sibling-case status distribution alone; check `test-automation.yaml`
`intake`/`already_automated_when` first — that's the authoritative gate
definition for this project, not case-file frontmatter convention-guessing.

Practical check before dispatching/accepting an analyst task for any
`onetest-ai-tm-Elitea` case: read `status`, `execution_type`, and
`automation_test_id` together, and classify against
`already_automated_when` — not `status` alone.
