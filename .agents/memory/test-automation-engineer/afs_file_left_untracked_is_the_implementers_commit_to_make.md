---
name: The AFS markdown file is the implementer's commit to make, not the analyst's — verify it landed
description: The analyst slot deliberately leaves the AFS file untracked on disk (workflow.md "commit authority" line + qa-engineer's own memory confirms this is intentional, not an oversight). If the implementer only commits the page-object/test code and never `git add`s the AFS itself, the spec has zero git history anywhere — caught as a merge-blocking reviewer finding on ELITEA-2030's PR #1034.
type: feedback
---

## What happened

ELITEA-2030's implementer session wrote `pipeline_detail_page.py` +
`test_pipeline_add_node_menu.py`, committed and pushed them to
`tests/ELITEA-2030-add-node-menu` (PR #1034) — but never `git add`ed the AFS
file itself
(`test-specs/pipelines/l2_add-node-menu-lists-types-adds-node-and-dismisses_ELITEA-2030.md`).
The file sat correct and complete on disk, untracked, on **every** branch
(`automation/base`, the PR branch, and even the `fixround/ELITEA-2030-review-r1`
branch from a later fix round) — none of the sessions that touched this case
thought to check `git status` for the AFS specifically. A reviewer caught it
as a merge-blocking finding (not a code defect — the content was already
reviewed and correct, just never committed anywhere).

## Why this happens

`.agents/memory/qa-engineer/analyst_slot_has_no_git_commit_authority.md`
confirms the analyst **intentionally** leaves the AFS uncommitted — per
`workflow.md`'s "commit authority: the implementer commits on the work
branch the lead names." That's correct design. But it means the baton pass
is easy to drop: the implementer's own mental model is "commit the test
code," and the AFS — sitting quietly as an untracked file the whole session
— is invisible unless you specifically look for it.

## The fix, mechanically

Before your first commit in an implementer-slot session (Phase 5/6), or
before closing out a fix round:

```bash
git status --porcelain -- test-specs/ | grep '^??'
```

If the AFS shows as `??`, `git add` it in the SAME commit as the test code
(or its own `docs(afs): ...` commit if you want the doc history separate) —
don't assume a prior session already handled it just because the file
exists and reads as final/reviewed. "Content correct" and "content
git-tracked" are two different facts; verify both.

## Resolution when caught late (ELITEA-2030 fix round)

No re-implementation needed — the content was already correct and already
reviewed. Just:
```bash
cp <untracked-path-on-disk> <same-path-in-your-worktree>
git add test-specs/... && git commit -m "docs(afs): commit <CASE-ID> AFS (reviewer finding — never git-tracked)"
git push origin <PR-branch>
```
