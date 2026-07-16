---
name: Orchestrator's own git reset --hard clobbers just-dispatched subagent memory
description: Mirror image of subagent_git_checkout_can_clobber_sibling_session_memory — the LEAD's own unnecessary `git checkout <branch> && git reset --hard origin/<branch>` before the merge gate silently discarded uncommitted memory-log writes from the implementer/reviewer subagents that had just run in the same shared working tree
type: feedback
---

## What happened

Working issue #83 (ELITEA-1963), before running my independent 3x pre-merge
live-run gate I did:

```
git checkout tests/ELITEA-1963-edit-credential-rename
git reset --hard origin/tests/ELITEA-1963-edit-credential-rename
```

The `reset --hard` was unnecessary — the checkout alone already landed on the
correct commit (`git status` showed "up to date" before the reset ran). The
reset's own output listed several `.agents/memory/**` files as modified-then-
discarded, including `test-automation-engineer/daily/2026-07-16.md` and (oddly)
files under my own `test-automation-lead/` tree — uncommitted memory-log writes
the implementer and reviewer subagents had made moments earlier in this same
shared working tree (per `.agents/workflow.md`, all dispatches share the
parent's working tree, no per-session isolation) before I ran the reset.

`git stash list` was empty afterward and the reflog showed no intermediate
commit — the content was gone, not stashed, not recoverable.

## Why it matters

This is the mirror image of `subagent_git_checkout_can_clobber_sibling_session_memory.md`
(a *subagent's* checkout destroying the *orchestrator's* uncommitted memory).
Here it's the *orchestrator's* own git hygiene destroying *subagents'* uncommitted
memory writes, moments after they returned. No functional/deliverable loss this
time (PR content, AFS, TMS back-write were all already committed/pushed by the
time of the reset), but real memory-logging content was silently lost, and a
different sequencing could just as easily have clobbered something load-bearing
(an uncommitted AFS, an uncommitted analyst finding).

## Fix / rule going forward

- Before any `git checkout`/`git reset --hard`/`git clean` in the shared working
  tree, run `git status --porcelain` first. If it's not empty, that's real
  uncommitted work — commit or stash it (never discard) before proceeding, even
  if you don't recognize whose it is.
- Don't reach for `git reset --hard` reflexively "to be safe" before a gate run —
  a plain `git checkout <branch>` is sufficient when the branch already matches
  origin (verify with `git status` / `git log --oneline -1` first); the hard
  reset is the destructive step and should only run when there's a *known*,
  *unwanted* local diff to discard, never as a default precaution.
- The standing risk from the sibling lesson applies both directions: this is a
  shared-workspace hazard for every git-touching actor, orchestrator included,
  not just dispatched subagents.
