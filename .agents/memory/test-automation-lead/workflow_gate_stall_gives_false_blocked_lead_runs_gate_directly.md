---
name: workflow gate stall gives false blocked, lead runs gate directly
description: batch-build's internal gate agent can stall (fetch timeout, OR a real conflict you then fix externally) and leave a stale cached verdict — recover by running the gate yourself, not by resuming
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

## Same trap, different cause: a REAL conflict you fix externally still replays stale

Observed on `settings-w01` (2026-08-26), recovering a batch interrupted by an
org spend ceiling. The gate call returned a real (non-error) completed
result: `{verdict: "incomplete", runs: 0, failures: [{signature: "gate-case.mjs
verdict=conflict — merging origin/automation/base into tests/batch-<slug>
FAILS..."}]}` — a genuine merge conflict in an additive memory-index file
(two branches appended different lines in the same region). I fixed it for
real: checked out the trunk, merged base, resolved the conflict (union both
sides' lines), pushed. Then resumed the SAME workflow run expecting the gate
to re-attempt and succeed.

**It didn't — the resumed gate call replayed the identical stale
`verdict=incomplete` failure**, because `resumeFromRunId` caches by
`(prompt, opts)`, not by live repo state. My external git fix didn't change
the gate agent's dispatch prompt, so the cache key was unchanged and the
call never re-ran — I just paid for another full journal replay + report
rewrite to rediscover the exact same "fixed already" failure.

**The lesson generalizes past "not-run": ANY gate call that returns a
completed-but-unproven verdict (`not-run`, `incomplete`, `conflict`) is
cached as done and will replay verbatim on resume, no matter what you fix
on disk in between.** Don't resume a second time hoping the fix takes —
once you've identified the cause and fixed it yourself, finish the job
yourself too: run `gate-case.mjs` directly (one `--n 1` call per run, per
`merge_gate_operational_traps.md`), then hand-write the verdict back into
`report.json` (playbook § Handle a red gate — "write the verdict back before
the closure comment, not later"). Resuming again only makes sense if you
expect the workflow's OWN gate agent to discover something new (e.g. you
haven't touched the repo at all) — never as a way to "confirm" a fix you
already made.
