---
name: Implementer redispatch on an already-complete case, but with a real unpushed fix round — land it, don't redo it
description: A THIRD implementer dispatch for a case can land on a state where the original implementation AND a correct fix round both already exist, but the fix round never reached the open PR's branch — verify it's correct, fast-forward-merge it in, run it fresh once, and push, rather than redoing the fix or opening a duplicate PR.
type: feedback
---

## The situation

ELITEA-2018 (Pipeline Canvas — Delete Node) board history: `implementing` →
`ready-for-review` (green 1x) → `parked` (review CHANGES_REQUESTED: Important,
CONFIRMED — `confirm_node_delete()` used a fixed `self.page.wait_for_timeout(300)`
instead of a real condition wait) → `analysis` → `ready-for-automation` →
`implementing` again (this dispatch, third overall, fresh isolated worktree).

`gh pr view 1028` showed the PR still OPEN but with only the ORIGINAL 2 commits —
no fix-round commit anywhere on origin. `git worktree list` found the answer:
`fixround/ELITEA-2018-review-r1` existed as a real branch, checked out (and
LOCKED) in a separate worktree, holding exactly the right fix — replaced the
sleep with `dialog.wait_for(state="hidden", timeout=timeout)`, backed by a
docstring citing `useDeleteItems.hooks.js`'s synchronous React-batched
`onConfirmDelete` handler, plus an AFS drift correction and a strengthened
dialog-title assertion. The fix round had been done correctly — it just never
got pushed onto the PR branch before the board bounced back to `analysis`.

This is the qa-engineer analyst-slot "approved-static/parked → analysis with no
reason" bounce family (`analyst_redispatch_on_already_complete_case_*.md`,
14+ instances documented there) hitting the **implementer** slot with a NEW
sub-shape: not "verify and do nothing" (the ELITEA-1877 case my sibling entry
`implementer_redispatch_on_already_complete_case_verify_via_git_gh_not_rerun.md`
covers), but "verify AND land a real fix that's stuck on the wrong side of a
push."

## The move

1. **Don't redo the fix.** Read the fix-round branch's diff directly
   (`git diff origin/<pr-branch> <fixround-branch> -- automation/`, no
   checkout needed — branches share refs across worktrees even when a
   worktree-isolated agent can't `git -C`/`cd` into another worktree's
   directory). Confirm it actually addresses the reviewer's finding and looks
   sound.
2. **Free the PR branch if it's stuck in a stale worktree.** `git worktree
   list` — a non-"locked" entry holding the PR branch is safely removable
   (`git worktree remove <path>`) per the sibling entry
   `fixround_dispatch_collides_with_stale_prior_worktree_same_branch.md`.
   Don't touch a LOCKED worktree (here, the fix-round branch's own worktree
   stayed locked/untouched — no need to enter it, `git diff`/`git merge`
   against a branch name work fine without checking it out).
3. **Checkout the now-free PR branch in your own worktree, `git merge
   --ff-only <fixround-branch>`.** If the fix round was built directly on top
   of the PR branch's tip (the common case — a fix round conventionally
   branches from the exact commit under review), this is a clean fast-forward,
   zero conflict risk.
4. **Run the actual test fresh, once, in your own environment.** This is a
   genuinely NEW confirmation (different worktree, different environment
   setup) of the FIXED code — not a repeat of a pre-fix green run, and not
   performative the way re-running an already-proven-unchanged case would be
   (contrast with the sibling ELITEA-1877 entry).
5. **Push to the EXISTING PR branch, not a new one.** Updates the open PR in
   place — "one PR, one purpose" holds; a duplicate PR for the same case would
   hand the orchestrator two competing deliverables.
6. **If `automation/base` has drifted since and the PR shows
   DIRTY/CONFLICTING**: compute the file-set intersection between the PR
   branch's own changes and `automation/base`'s changes since their shared
   merge-base (`git diff --name-only <merge-base> <ref>` on each side,
   intersect) before assuming it's a real conflict. Append-only shared files
   (team memory logs are the recurring example here) produce a git merge
   conflict from concurrent line-appends but are trivially resolvable by
   keeping both sides' additions — this is NOT the substantive-conflict case
   the qa-engineer memory's file-set-intersection technique was built for, but
   the exact same check applies and the exact same resolution (merge, keep
   both, done) works from the implementer slot too.

## Why this beats either extreme

- Redoing the fix from scratch would duplicate real, already-correct work and
  risk introducing a DIFFERENT (possibly worse) fix for the identical finding.
- Doing nothing (per the sibling "verify, don't touch" entry) would be wrong
  here specifically because the verification ITSELF revealed a gap the
  existing artifacts don't cover — the fix exists but isn't actually landed on
  the deliverable the orchestrator/reviewer/merge-gate will look at. The
  sibling entry's "reserve an actual re-run for when it would be informative"
  clause applies directly: here, re-running is informative because the code
  under test actually changed (fix landed) since the last recorded green run.

## Report shape

Named explicitly in both the PR comment and the Run Report: (1) the fix round
already existed and was correct, just unpushed; (2) exact git operations used
to land it (worktree-free, FF-merge, no rebase); (3) the fresh test run's own
timing/result as new evidence, not a copy of a prior run's number; (4) the
trivial-conflict-resolution merge with automation/base and why it was judged
non-substantive; (5) zero new implementation — this dispatch's contribution
was landing + verifying, not authoring.
