---
name: Redispatch finds PR CONFLICTING from parallel memory-log appends — union-merge, don't reimplement
description: In a large concurrent batch-build campaign (many isolated worktrees active at once), a redispatch onto an already-complete case can find gh pr view reporting mergeable:CONFLICTING even though the test/page-object/AFS diff is 100% clean — verify with git merge-tree before assuming real code conflict, then resolve by union-merging the shared append-only memory files and pushing a merge commit.
type: feedback
---

## The situation

ELITEA-2006 (webhook trigger settings modal) implementer-slot dispatch landed
on a case that was, per the sibling `implementer_redispatch_on_already_complete_
case_verify_via_git_gh_not_rerun.md` pattern, already fully done: branch
`tests/ELITEA-2006-webhook-trigger-settings-modal` pushed, PR #1015 open
against `automation/base`, fix round r1 already addressed (commit `ffdce06f`)
and independently verified green 2x locally (27.36s/26.73s) with a 0-hit
mechanical grep — all documented in a prior PR comment.

Unlike ELITEA-1877 (the sibling entry's case, which was cleanly mergeable),
`gh pr view 1015 --json mergeable` returned `CONFLICTING`. This is a NEW wrinkle
the sibling entry doesn't cover: what to do when the redispatch verification
finds a REAL git-level conflict, not just "everything's fine, do nothing."

## Diagnose before assuming it's a real code conflict

`git merge-tree <merge-base> origin/automation/base origin/<pr-branch>` (a
read-only 3-way merge preview, no working-tree side effects) showed exactly
TWO conflict sections, both confined to `.agents/memory/test-automation-
engineer/` — the SAME shared append-only files this role's own `memory` skill
writes to every session (`MEMORY.md`'s index, `daily/<date>.md`). Two
concurrent sessions (this case's implementer/fix-round work, and an unrelated
case's implementer work) had each appended a different new entry at the exact
same insertion point (top of the index / end of the daily log) since the
branches' common ancestor — a textbook append-only-file merge conflict.
Everything else in the merge-tree output was `added in remote` (new files,
no path collision) — i.e. genuinely zero risk to the actual test deliverable.

**In a campaign running dozens of concurrent isolated worktrees (confirmed via
`git worktree list` — 40+ active branches for this one campaign), EVERY
implementer/fix-round branch that commits its own memory-log entries is a
candidate for this exact conflict against `automation/base`**, since they all
write to the same two files. Expect this to recur; don't be surprised by it.

## The fix (safe, mechanical, zero test-code risk)

1. Free the branch name if a stale unlocked worktree still holds it (see the
   companion `fixround_dispatch_collides_with_stale_prior_worktree_same_
   branch.md` entry) — `git merge-base --is-ancestor <stale-tip> origin/<branch>`
   confirms safety before `git worktree remove`.
2. `git checkout -B <pr-branch> origin/<pr-branch>` in your own worktree.
3. `git merge origin/automation/base` — let it fail exactly where `merge-tree`
   predicted.
4. Resolve each memory-file conflict by UNION (keep both sides' entries, no
   deletions, no reordering except placing blocks in roughly chronological
   order) — this is index/log content, not code; there is no "correct" side
   to pick, both are true and durable.
5. Confirm zero conflict markers remain (`grep -n '^<<<<<<<\|^=======\|^>>>>>>>'`
   across both files — exit 1 = clean), stage, commit, push (plain, no refspec
   trick needed if you checked out under the PR's own branch name).
6. Re-check `gh pr view <N> --json mergeable,mergeStateStatus` — expect
   `MERGEABLE`/`CLEAN` within a few seconds of the push.
7. Do NOT re-run the actual test — the merge touched no code path it exercises;
   a lightweight `ruff check` on the PR's touched Python files is sufficient
   sanity evidence that the merge didn't corrupt anything syntactically.
8. Post a PR comment naming exactly what was verified (merge-tree output
   confined to memory files, ruff clean, mergeable now CLEAN) so a fresh
   reviewer/auditor doesn't have to re-derive it.

## Takeaway

`mergeable: CONFLICTING` on an already-complete case is NOT automatically a
"needs-escalation, someone touched my files" signal — check WHERE with
`git merge-tree` first. If the conflict is confined to this role's own
shared memory-log files (a structural side-effect of many parallel sessions
in one campaign, not a design flaw in the case itself), it's a same-dispatch,
zero-risk fix: union-merge and push. Reserve escalation for when merge-tree
shows the conflict actually touching the test/page-object/AFS files.
