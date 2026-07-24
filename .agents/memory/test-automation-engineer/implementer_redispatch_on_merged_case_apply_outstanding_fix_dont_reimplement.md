---
name: Implementer redispatch on an ALREADY-MERGED case — apply the one real outstanding gap, don't re-implement
description: ELITEA-2170 arrived as a fresh "Implementer slot — implement ELITEA-2170" dispatch, but PR #1030 for this exact case was already MERGED to automation/base. Ground-truth check (gh pr list --search, git merge-base --is-ancestor) confirmed it in under a minute; the only real, still-open gap was a one-line p2->p1 priority-marker fix prepared in an earlier session's local-only fix-round commit that never reached origin before the merge. Cherry-picked that exact commit into a small standalone PR instead of re-driving the whole case from scratch.
type: feedback
---

## The situation

Dispatched as implementer for ELITEA-2170 with an AFS path and a source.md
case-snapshot path. Both were missing from my fresh worktree (checked out
from an older `automation/base` commit) — but `gh pr list --state all
--search "2170"` immediately showed PR #1030, `test(ELITEA-2170): remove
user from conversation via USERS popper confirm dialog`, state **MERGED**.
`git merge-base --is-ancestor <merge-sha> origin/automation/base` confirmed
it's a real ancestor; my local worktree was just 2 commits behind. This is
the implementer-slot sibling of the qa-engineer memory's extensively
documented "redispatch on an already-complete case" bounce-loop pattern
(`.agents/memory/qa-engineer/analyst_redispatch_on_already_complete_case_
check_board_git_then_bounded_spotcheck.md`, eleventh instance is this exact
case) — the board's `case.md` had bounced `merged` → `analysis` →
`implementing` again with zero recorded reason, a routing/board-state bug,
not a real re-automation need.

## What NOT to do

Don't re-run the whole AFS from scratch, don't re-add already-landed
testids, don't re-author a test file that's already merged and green. That
duplicates real work and risks landing a second, divergent test for the
same case.

## What to actually check and do

1. `gh pr list --state all --search "<CASE-ID>"` (real-time, not the lagged
   search index) — if MERGED, the case's core work is done.
2. `git merge-base --is-ancestor <merge-commit> origin/automation/base` to
   confirm it's really landed (after `git fetch origin`).
3. Look for a **local-only fix-round commit** the merge might have missed —
   in this factory, other worktrees share the same `.git` object store, so
   `git show <sha>` works across worktrees even for commits that were never
   pushed. `git worktree list` + `git log <candidate-branch> --oneline`
   surfaced `fixround/ELITEA-2170-review-r1` with a clean, already-verified
   one-line fix (`1279958b`, "correct priority marker p2 -> p1") that a
   same-day reviewer pass had found but that never reached `origin` before
   the merge happened.
4. Confirm the gap is STILL present on the merged code
   (`git show origin/automation/base:<path> | grep pytest.mark` → still
   `p2`) before doing anything — don't trust a stale note blindly either.
5. Cherry-pick the exact verified commit onto a **fresh small branch cut
   from `origin/automation/base`** (`fix/<CASE-ID>-<slug>`, not
   `tests/...` — this is a fix to already-shipped code, not new test
   authorship). `git cherry-pick <sha>` applied cleanly with zero conflicts
   since it was already rebase-tested against a very similar tree.
6. Run the ONE affected test green once (`HEADLESS=true pytest
   <node-id> -v -p no:cacheprovider` — 1 passed, 47.18s), mechanical
   non-testid-handle grep on the diff (0 hits, expected for a marker-only
   change), push, open a small standalone PR citing the original PR + the
   AFS + the exact reasoning.

## Reusable lesson

An implementer redispatch that lands on an already-merged case is not
automatically "nothing to do" — check whether a **verified, previously-
prepared fix sitting in a local-only branch** (same or different worktree,
same repo, shared object store) never made it to origin before the merge
closed the window. `git worktree list` + `git log --all --grep "<CASE-ID>"`
finds these cheaply. When one exists, cherry-picking it into its own small
PR is real, correctly-scoped implementer work — faster and safer than
either (a) re-implementing the whole case, or (b) doing nothing and letting
a known, already-diagnosed gap sit unfixed indefinitely because the case
"looks done" from the board's stale status alone.

See also: `.agents/memory/test-automation-engineer/afs_priority_vs_pytest_
mark_preflight_check.md` (the general p2-vs-p1 preflight check that would
have caught this before merge in the first place) and
`.agents/memory/qa-engineer/analyst_redispatch_on_already_complete_case_
check_board_git_then_bounded_spotcheck.md` § Eleventh confirmed instance
(the analyst-side sighting of this exact case's bounce).
