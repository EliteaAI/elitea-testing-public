---
name: workflow gate stall gives false blocked, lead runs gate directly
description: batch-build's internal gate agent can stall on git fetch and mark a clean batch "blocked" — recover by running the gate yourself, not by resuming
type: feedback
---

Observed on the `approved-top10` batch (2026-08-02, 10 cases, 6 units). All 6
units built, statically reviewed to APPROVED, and merged cleanly into the
batch trunk (`tests/batch-approved-top10`) — but `batch-build.workflow.mjs`'s
internal gate agent stalled on its first step, `git fetch origin --quiet`,
because this repo's remote is OneDrive-hosted and the fetch took longer than
the agent's patience. It returned a real (non-null, non-error) result:
`{verdict: "not-run", runs: 0, failures: []}`, with notes explaining the
stall. The workflow's top-level `cases[]` surfaced this as **every one of the
10 cases marked `blocked`** with the note "gate red for the batch — this spec
did not itself fail; the batch is not proven until the red is resolved" — a
misleading read if taken at face value, since nothing actually failed.

**Don't trust the surface `blocked` reading without checking what actually
happened.** Read `journal.jsonl` (the run's transcript dir) — search near the
end for the gate-shaped result object (`verdict`/`runs`/`green_specs`/
`failures`/`notes` keys). If `verdict: "not-run"` and the notes describe an
infra stall (not a test failure), the batch is NOT actually red — it's
unproven, and every unit's build+review work is still valid and merged.

**Recovery: run the gate yourself, don't resume the workflow.**
`resumeFromRunId` replays any `agent()` call that already returned a non-null
result from cache — including a useless `not-run` gate call, since it
completed rather than errored. Resuming just replays the same bogus verdict.
Instead: `testing.md` § Merge gate already assigns N=3 gate execution to the
**lead**, not exclusively to the workflow's internal agent — so check out the
trunk yourself and run the N spec-together invocations directly (see
`merge_gate_operational_traps.md` for the exact command shape). This is
faster than debugging the workflow's fetch timeout anyway, and it's the
canonical path per this project's own contract, not a workaround.

If the gate then finds a REAL red (as happened here — see
`long_running_gate_bash_calls_get_infra_killed.md` for a second, unrelated red
that turned out to be a genuine flake), route it through `batch-stabilize`
as normal; the workflow's build/review work upstream is unaffected either
way.
