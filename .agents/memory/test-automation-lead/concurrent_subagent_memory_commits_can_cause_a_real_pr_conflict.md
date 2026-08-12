---
name: Concurrent subagent memory-log commits can cause a real PR merge conflict
description: two dispatches of the same role (e.g. two implementer rounds on one case) each landing their own daily-log entry from a different starting branch (one on automation/base, one on the feature branch) produces a genuine append-conflict that flips gh pr view --json mergeable to CONFLICTING — resolve by merging automation/base into the feature branch and hand-splicing both entries in chronological order; this is a memory/housekeeping conflict, not test/framework code, so it's within the orchestrator's own editable scope
type: feedback
---

## What happened (#228, ELITEA-1824, PR #653)

Two `test-automation-engineer` dispatches landed in the same delivery: the full
implementation round (wrote the test, opened PR #653) and a later fix-only round
(AFS documentation sweep after reviewer round 1's `CHANGES_REQUESTED`). Each round,
per this project's established convention, committed its own memory-log entry to
`.agents/memory/test-automation-engineer/daily/2026-07-19.md` — but the FIRST round's
memory commit landed straight onto `automation/base` (the role's own habit of
following the "land memory separately from deliverables" pattern), while the SECOND
round's memory commit landed onto the feature branch (per this round's explicit
dispatch instruction: "commit ... push to the same branch").

Both entries were appended at the same insertion point (end of today's log) on
DIVERGENT branches. Right before merging, `gh pr view 653 --json mergeable` came back
`CONFLICTING` — a real git conflict, not a stale computation. `git merge-tree` showed
the daily-log file with actual `<<<<<<<`/`>>>>>>>` markers; a sibling `MEMORY.md`
index-line addendum in the same commits auto-merged cleanly (no overlap), and the
actual page-object/test-code files also auto-merged cleanly (zero code-level
divergence) — the conflict was ISOLATED to the one append-only daily-log file.

## Why it's easy to miss

Nothing about the individual dispatch results looked wrong — both implementer rounds
returned clean, both pushed successfully to their respective branches, and `gh pr
view` returned `MERGEABLE` earlier in the session (checked right after PR #653 opened,
before the fix-only round's memory commit landed on the feature branch). The
conflict only appeared at the FINAL pre-merge check, after all pipeline stages had
already returned green results — easy to skip re-checking `mergeable` between the
last fix-only round and the actual `gh pr merge` call.

## The fix

1. `git fetch origin` then diff/merge-tree the feature branch against
   `origin/automation/base` BEFORE calling `gh pr merge` — don't trust an earlier
   `MERGEABLE` read if any dispatch landed a commit on `automation/base` in between
   (memory-landing commits are exactly the kind of "invisible" commit this can be).
2. On conflict, check `git diff --stat` between the two conflicting commits' content
   FIRST — if it's confined to `.agents/memory/**` (or another housekeeping path,
   never `automation/**`/`test-specs/**`), this is squarely a documentation
   append-conflict, not a test/framework-code conflict. Resolving it yourself (keep
   both entries, order by embedded timestamp) is within the orchestrator's own
   editable scope — it's the same "land memory as routine housekeeping" duty already
   exercised for landing OTHER roles' memory changes (qa-engineer, etc.) throughout
   a normal session, just applied to conflict resolution instead of a clean add.
   If the conflict touches ANYTHING in `automation/**`/`test-specs/**`, do NOT
   resolve it yourself — abort and dispatch the implementer, per
   `sync_time_merge_conflicts_also_dispatch.md`'s generalization of the no-edit
   framework-code guardrail.
3. After resolving + pushing the merge commit, `git diff <old-branch-tip>
   <new-branch-tip> --stat` to confirm the merge touched ONLY the conflicted
   housekeeping file(s) — if so, an already-passed pre-merge live-run gate remains
   valid and does NOT need to be re-run (test/framework code is byte-identical).
   If the merge touched anything under `automation/**`, re-run the gate.

## Rule going forward

Re-check `gh pr view --json mergeable` immediately before `gh pr merge`, every time —
not just once earlier in the session. A `MERGEABLE` read from before the last
subagent dispatch is not evidence of `MERGEABLE` now, because a role's own
memory-landing habit can silently move `automation/base` out from under an
already-open PR. When it does conflict and the conflict is confined to
`.agents/memory/**`, resolve it directly (append-order splice, not a content
rewrite) rather than spending a dispatch round on it.
