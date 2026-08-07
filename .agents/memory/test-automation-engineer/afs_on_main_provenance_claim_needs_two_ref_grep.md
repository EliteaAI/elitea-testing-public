---
name: AFS "on-main ✓" PROVENANCE claim needs both origin/main AND origin/automation/testids grepped
description: A PROVENANCE row can claim "on-main ✓" for a testid that only exists on origin/automation/testids — grep BOTH refs (fresh git fetch first), never take the analyst's single-ref claim at face value even when dated same-day
type: feedback
---

## What happened (ELITEA-1876, PR #1283, fix round 1)

The analyst's AFS PROVENANCE row for `run-history-list-item` claimed
`on-main ✓ (pre-existing, reused as-is — verified via git fetch + git grep
against origin/main, 2026-08-06)`. Reviewer re-ran the exact same check
(fresh `git fetch origin` + `git grep -- 'run-history-list-item'
origin/main -- src/`) one day later and got **0 hits** (exit 1) — the
testid is real, but it lives only on `src/[fsd]/entities/run-history/ui/
RunHistoryList/RunHistoryListItem.jsx` on `origin/automation/testids`
(1 hit, exit 0), not on `origin/main`.

Root cause unclear (analyst error, or a since-reverted main-side promotion)
— doesn't matter for the fix: the claim was false at review time regardless
of history, and PROVENANCE rows are input to the closure record's
promotability determination, so a wrong "on-main ✓" would have shipped a
false "deployed-env-promotable" signal.

## The check — always grep BOTH refs, not just the one the AFS claims

```bash
cd ../EliteaUI && git fetch origin
git grep -- '<testid>' origin/main -- src/                  # promotable-to-deployed truth
git grep -- '<testid>' origin/automation/testids -- src/    # dev-server/localhost truth
```

A same-day-dated PROVENANCE claim is not exempt from re-verification —
`automation/testids` and `main` diverge routinely (that's the whole point
of the integration-branch design), so "verified yesterday" can already be
stale, and a wrong ref name in the analyst's own check (grepped
`automation/testids` but wrote "on-main") is indistinguishable from staleness
without re-running it yourself.

## Fix mechanics when this fires

1. Correct the PROVENANCE cell to name the real ref: `on automation/testids
   only — NOT yet on origin/main (awaiting human promotion)`.
2. Commit as `docs(afs): (<CASE-ID>) correct false on-main PROVENANCE claim
   for <testid>` — doc-only, no test code change, no regression test
   applicable (the defect is in the AFS text, not in test behavior).
3. Flag the closure-record implication explicitly in the PR comment: the
   case is not deployed-env-promotable until the testid is cherry-picked to
   `main` — the lead's closure record inherits this, don't make them
   re-derive it.
