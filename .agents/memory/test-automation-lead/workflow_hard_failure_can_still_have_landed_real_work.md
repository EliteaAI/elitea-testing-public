---
name: workflow hard failure can still have landed real work
description: A Workflow status:failed (not just a per-case blocked) doesn't mean nothing happened — check git + journal.jsonl before redoing anything
type: feedback
---

A `batch-build.workflow.mjs` run can end in two different failure shapes, and
they need different responses:

1. **Per-case `outcome: "blocked"` with a caught error** (e.g. a merge-back
   agent returns an empty result / no `StructuredOutput` call) — the script's
   own try/catch absorbed it into a normal case result. `integration_branch`
   and `gate` come back `null` in the JSON, reading as "nothing landed."
2. **The whole `Workflow` call returns `status: "failed"`** with an uncaught
   exception (same underlying cause — an agent not calling `StructuredOutput`
   — but this time nothing catches it). This LOOKS much worse than (1).

**In both cases, checked on a real ELITEA-2352 run: the git-visible effects
(merge commit on the trunk, PR merged, gate's 3× green test runs, even a
pushed memory-log commit from the gate agent) had already happened and
persisted** — only the reporting-layer agent (merge-back's structured return,
or the final report-writer) failed to communicate back to the script. The
actual work was never lost or redone.

**What to do on either failure shape, in order:**
1. Don't trust the failure message's severity — `status: failed` sounds like
   "start over" but often isn't.
2. Check git directly: `git log <trunk>`, `git log origin/<trunk> -1`,
   `gh pr view <N> --json state,mergeCommit`. If the merge commit and PR-merged
   state are there, the unit landed regardless of what the script reported.
3. Read `journal.jsonl` in the run's transcript dir (path is in the tool's own
   diagnostics) for the actual `result` of every completed agent — don't
   assume an `agents_empty_result: 1` or a thrown error means everything
   after it is also lost.
4. **Resume with the same `resumeFromRunId`** rather than hand-repairing or
   restarting. Every agent whose (prompt, opts) pair is unchanged replays from
   cache in under a second — only the actually-failed step re-runs live. It
   is safe to resume 2-3 times in a row on repeated report-writer flakes; each
   resume only pays for the one broken step, not the whole batch.

On the ELITEA-2352 run this took 3 `Workflow` invocations (1 initial + 2
resumes) to get a clean final report, but only the LAST one did any real new
work (~77s, one report-writer agent) — the first two resumes were essentially
free cache replays that each made one more step succeed.

## Seen 2×

#945/ELITEA-2437 — shape 1 again, single `Workflow` call (no resume needed
this time, the run just completed once). `report.json`'s only case carried
`outcome: "blocked"`, note `"build failed: agent({schema}): subagent completed
without calling StructuredOutput (after in-conversation nudge)"`, `gate: null`,
`integration_branch: null` — yet the SAME case object also carried a real
`afs` path, `branch`, and PR number, and the workflow's own agent list showed
`review:ELITEA-2437` returning `APPROVED` and a `merge:` agent completing
cleanly. Verified via git before trusting either half: the case branch was in
fact merged into the batch trunk, the unit PR was MERGED. Only the gate phase
had genuinely not run (`gate: null` was accurate, not stale) — ran it myself
(3× independent green) before landing. Lesson holds: check git, not the
outcome string; but add "gate: null may be accurate even when the rest of the
case data is real" — don't assume a `blocked` outcome's null fields are ALL
stale just because some of the case data survived intact.
