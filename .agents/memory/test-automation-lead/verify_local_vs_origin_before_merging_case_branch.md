---
name: Verify local vs origin before merging a case branch
description: A case branch's commits can exist only in the lead's local working tree — merging origin/<branch> silently no-ops ("Already up to date"), landing nothing
type: feedback
---

## What happened

Batch #1298 (2026-08-08), ELITEA-1903: the implementer subagent committed its
test + memory commits on `tests/1903-...` (shared working tree, same clone
the lead uses) but never pushed, despite the dispatch saying "commit your
work on this branch." The lead's merge step ran
`git merge --no-ff origin/tests/1903-...` — this succeeded with **"Already up
to date"** and no error, because `origin/tests/1903-...` still pointed at the
pre-implementer commit. The trunk silently did NOT get the case's work.
Caught only because a post-merge `pytest --collect-only` found 0 tests
instead of 1 — not because the merge command itself signalled anything wrong.

## The fix

Before every case-branch merge, compare the local and remote refs:

```bash
git rev-parse <local-branch>
git rev-parse origin/<local-branch>
```

If they differ, merge the **local** ref (`git merge --no-ff <local-branch>`),
not `origin/<local-branch>` — the local tree has the real work. This is safe
specifically because the implementer/reviewer subagents share the lead's
working tree (sequential dispatch, one case at a time) rather than each
having their own clone.

## Why "Already up to date" doesn't fail loud

Git's merge command has no way to know the branch you *meant* to merge has
newer commits sitting locally under a different ref state — from git's
perspective, merging a ref that IS an ancestor of HEAD is a legitimate no-op,
not an error. The only real signal is downstream: the file you expected
isn't there, or (worse, silently) the test that should now exist doesn't
collect. Always run a positive post-merge check (`pytest --collect-only` for
the new node-id, or `git show HEAD:<path>`) — trusting "merge succeeded, no
error" as proof of a real merge is the actual bug here.

## Standing practice

Run the local-vs-origin rev-parse comparison before every case-branch merge
in a batch, not just when something looks wrong — it costs two cheap
commands and catches this before it ever reaches a "why is my test missing"
investigation.
