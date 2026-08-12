---
name: Subagent git checkout can clobber sibling session memory
description: An implementer's cleanup git checkout on a shared working directory can discard a concurrent orchestrator session's uncommitted memory edit — scope dispatch prompts to avoid touching paths outside the subagent's own role directory
type: feedback
---

## What happened

Working the ELITEA-1792 rework (issue #34), the implementer subagent reported — unprompted, in its own final message — that during cleanup it ran:

```
git checkout automation/base -- .agents/memory/test-automation-lead/daily/2026-07-15.md
```

on the shared working directory (this factory's sessions all operate on the same
sibling-clone checkout, not isolated worktrees per session). That command discarded
an **uncommitted, in-progress edit belonging to a concurrent orchestrator session** —
not the implementer's file to touch at all, and not recoverable via git since it was
never committed or stashed by its owner.

By the time I checked, the file on disk matched `HEAD` with no diff, so nothing was
pending from *my* session specifically at that moment — but the loss is real for
whichever concurrent session owned that edit, and is silent: nothing errors, nothing
warns, the file just quietly reverts.

## Why it matters

This factory runs multiple concurrent orchestrator/IC sessions against the **same**
working directory (no per-session worktree isolation for the lead's own operations,
only for occasional review-branch worktrees). Any subagent with shell access can run
`git checkout <path>`, `git clean`, `git stash`, or similar against paths it doesn't
own — including another role's memory directory — and silently destroy uncommitted
work with no recovery path.

## Fix / rule going forward

- Dispatch prompts to implementers/reviewers should scope git operations to the
  paths relevant to their task (test code, page objects, the AFS, the testid repo)
  and should not imply blanket license to `git checkout`/`git clean` arbitrary paths
  "while cleaning up."
- `.agents/memory/**` outside the dispatched agent's own role directory is never
  the dispatched agent's to touch, checkout, or clean.
- If a subagent needs to discard ITS OWN stray changes, scope the checkout to the
  specific files it created, never a bare `git checkout <ref> -- <path>` on a path
  it didn't create.
- This is a standing risk of the shared-workspace pattern, not a one-off implementer
  mistake — worth raising to scout/operator as a candidate rule addition (not yet
  written into any seed file as of this entry).
