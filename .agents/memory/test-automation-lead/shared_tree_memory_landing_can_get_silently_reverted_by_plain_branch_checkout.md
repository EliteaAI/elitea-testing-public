---
name: Shared-tree memory landing can get silently reverted by a plain branch checkout
description: A routine "checkout automation/base, commit subagent memory, checkout back to feature branch" cycle can silently revert the feature branch's working-tree copy of a shared memory file to its pre-commit content — no flags, no error, just a clean checkout doing exactly what it's supposed to
type: feedback
---

## What happened

On #227/ELITEA-1809, my usual per-slot pattern was: after each subagent (analyst,
implementer, reviewer) finished and left uncommitted memory edits in the shared
working tree, I'd `git checkout automation/base`, stage+commit+push just the memory
files, then `git checkout <feature-branch>` to get back to PR work.

This worked cleanly for the analyst's and implementer's rounds. But `qa-engineer`'s
`daily/2026-07-19.md` and `MEMORY.md` are the SAME two files both the analyst and
(later) the reviewer write to. Sequence:

1. Analyst appends an entry (uncommitted).
2. I `checkout automation/base` → succeeds (no conflicting local changes yet) →
   commit → push.
3. I `checkout <feature-branch>` → **succeeds silently** and rewrites the working
   copy of those 2 files back to the feature branch's OLDER tracked version — i.e.
   WITHOUT the analyst's entry. Git does this because the working tree exactly
   matched the commit I'd just made (no uncommitted diff), so switching branches is
   a "clean" operation from git's point of view: it just checks out the target
   branch's tracked content for those files.
4. Reviewer runs much later, reads the (now-reverted, analyst-entry-less) daily log,
   appends its own entry on top of that stale base.
5. I try the same land-on-base cycle: `git diff automation/base -- daily/....md`
   now shows "delete the analyst's whole paragraph, add the reviewer's paragraph" —
   because from `automation/base`'s perspective (which HAS the analyst's entry),
   the reviewer's uncommitted version never saw it and is missing it.
6. This time `git checkout automation/base` correctly REFUSED ("local changes would
   be overwritten") instead of silently merging — the difference from the
   implementer's round (which merged silently via git's internal three-way apply)
   was luck of which lines overlapped, not something to rely on.

## Why it matters

No content was permanently lost — everything was still safely committed to
`automation/base`'s history at each step. But the WORKING TREE silently diverged
from what I'd just landed, and the next subagent's edit built on top of the stale
copy. Left unnoticed, this is exactly the shape that produces a squashed "delete
paragraph, add paragraph" commit that actually erases a prior round's memory entry
from the file for good the next time someone commits without checking the diff
first.

This is a NEW mechanism distinct from the two already-logged shared-tree-clobber
entries:
- `subagent_git_checkout_can_clobber_sibling_session_memory.md` — a subagent's own
  cleanup `git checkout -- <path>` (path-restore form) discarding someone else's
  uncommitted edit.
- `orchestrator_git_reset_hard_clobbers_subagent_memory.md` — an unnecessary
  `git reset --hard` wiping uncommitted edits outright.

Both of those are avoidable "don't run that command" fixes. This one isn't — it's
what a completely ordinary, no-flags `git checkout <branch-name>` does whenever the
working tree is clean relative to the branch you're leaving. There's no misuse to
avoid; it's baseline git behavior colliding with a shared (non-worktree-isolated)
working directory.

## Fix applied

Reconciled by hand: `git show automation/base:<path>` to get the true landed
content, manually appended the reviewer's new paragraph / index line on top in
`/tmp`, wrote the merged result back, then committed. No data lost, but required
manual archaeology instead of a clean `git add`.

## Rule going forward

Before switching FROM a branch where you just committed shared-tree files BACK to
a feature branch, if you know another subagent will edit those SAME files again
later in the session: either (a) don't checkout away at all — stay on
`automation/base` for the accumulation phase and only branch-hop right before the
PR-specific commit, or (b) after switching back, immediately re-check
`git diff automation/base -- <path>` is non-empty in the expected direction (only
adds relative to the ancestor) before trusting the working copy as a clean base for
the next subagent's edit. When a later `git checkout automation/base` refuses with
"local changes would be overwritten," that is git catching the divergence for
you — treat it as a signal to reconcile by hand (`git show <branch>:<path>` + merge
the two additions manually), not as an obstacle to route around with `checkout -f`
or `stash` (either would silently pick one side and drop the other).

For files that ONLY one agent role ever touches (e.g.
`.agents/memory/test-automation-engineer/**`, written only by the implementer),
this class of collision cannot happen — the risk is specific to files multiple
slots share, which in this pipeline means `qa-engineer`'s memory (both analyst and
reviewer slots resolve to `qa-engineer`).
