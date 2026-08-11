---
name: git stash push with a mixed tracked/untracked pathspec list can silently no-op, then a later pop grabs someone else's stash
description: git stash push -- <tracked> <untracked-new-file> aborts entirely if any pathspec is untracked-and-unknown; a following stash pop then pops whatever WAS on top — which may be a different task's parked WIP
type: feedback
---

## What happened

While isolating a ruff check against only my own edits, I ran
`git stash push -- automation/pages/skills_list_page.py
automation/tests/unit/test_skills_list_page_locator_inventory.py` — the second
path was a brand-new file I had just `Write`-created but not yet `git add`ed.
`git stash push -- <pathspecs>` treats an untracked, never-`git add`ed path as
"did not match any file(s) known to git" and **aborts the whole command with
exit 128 — no stash is created at all**, even for the tracked path that WOULD
have matched.

I then ran `git stash pop` next (intending to restore what I assumed I'd just
stashed). Since no stash was actually created by the failed push, this popped
whatever was already on top of the stash stack — in this case a **different
in-flight task's parked WIP** (`WIP on tests/2009-pipeline-code-node-configuration`,
not mine), which conflicted with an unrelated file
(`.agents/memory/qa-engineer/daily/2026-08-08.md`) I had never touched.

## The check — before `git stash push -- <paths>`

- `git stash push -- <paths>` needs every pathspec to already be **known to
  git** (tracked, OR staged via `git add -N`/`git add`). A brand-new file you
  only `Write`d is neither — it will make the WHOLE command fail, silently
  producing no stash.
- **Always check `git stash push`'s own exit code / output before running
  `git stash pop` next.** Don't assume "I just ran stash push" means "there is
  now a stash with my changes in it."
- To stash only some paths including a new untracked one: `git add -N <new-file>`
  first (intent-to-add, stages the path without its content) so the pathspec
  resolves, or just don't stash the untracked file at all (it isn't in the
  index yet, so a plain `git stash push -- <tracked-paths>` won't touch it,
  and you can inspect/revert the tracked one in isolation instead).

## The recovery (when this already happened)

If a `git stash pop` produces a conflict and you don't recognize the content —
STOP. It may be someone else's stash, not one you created this turn:
`git stash list` to see what's still there and whose WIP the message names.
**Do not resolve or drop it.** Discard only the unwanted merge on the
conflicted file(s): `git checkout HEAD -- <conflicted file>` restores the
committed content and leaves the stash entry intact in the stash list (a
failed `pop` that hits a conflict does NOT drop the stash — git says "kept in
case you need it again"). Verify with `git stash list` that the foreign entry
is still present afterward.

## Where this came from

Implementer slot, ELITEA-2428 fix round 1 (`tests/ELITEA-2428-skills-card-view-fields`,
PR #1440, 2026-08-12), while verifying a ruff finding was pre-existing rather
than introduced by the fix.
