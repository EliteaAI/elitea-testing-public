---
name: automation/base moves mid-task during a live campaign — two-dot diff lies, use three-dot + merge before PR
description: With multiple concurrent implementer sessions pushing straight to automation/base, a feature branch's PARENT branch ref can advance while you're still working — `git diff automation/base --stat` then shows large, unrelated churn (files you never touched) because it's comparing against automation/base's CURRENT tip, not the commit you actually forked from.
type: feedback
---

## What happened (cov60 foundation pass)

Branched `tests/foundation-cov60-gap` from `automation/base` (at commit
`2f71de04`), did my own work, then ran `git diff automation/base --stat`
before committing to sanity-check my diff. It showed **-288 / -93 line
deletions** in `test-specs/chat-interface/_surface.md` and
`test-specs/hubs/_surface.md` — files I had never touched. Panic moment:
looked like I'd clobbered someone else's docs.

Root cause: this is a highly concurrent campaign (multiple implementer
worktrees pushing `docs(afs):`/test commits straight onto `automation/base`
continuously). Three unrelated commits landed on `automation/base` (touching
those exact two files) in the time between my branch-cut and my check.
`git diff <ref> --stat` (two dots, or bare ref vs. working tree) always
resolves `<ref>` to its CURRENT tip — it does NOT diff against the commit
you branched from. So it was showing me automation/base's forward motion,
not my own changes.

## The fix / correct verification sequence

1. **To see only what YOUR branch actually changed**, use the merge-base
   (three-dot) form: `git diff automation/base...HEAD --stat` — but note
   this only works once you have at least one COMMIT on your branch (it
   compares committed trees, not working-tree state). For uncommitted
   work, just trust `git status --short` / `git diff --stat` (no ref) and
   stage exactly those paths — don't reach for a base-branch diff to
   "sanity check" scope while anything is still uncommitted.
2. **Before opening the PR**, fetch + merge the CURRENT `origin/automation/base`
   into your branch (`git fetch origin automation/base && git merge
   origin/automation/base`) — cheap insurance so the PR's diff is against a
   fresh parent and doesn't silently miss/duplicate concurrent work. This
   merge is usually conflict-free when the concurrent work touches unrelated
   files (docs digests, other surfaces' page objects).
3. **Re-run your test suite once more after that merge** — a clean merge can
   still change *behavior* even without conflicts if the merged-in commits
   touched a shared file your tests exercise (e.g. `chat_page.py`). Don't
   treat "merge succeeded with no conflicts" as equivalent to "nothing
   changed for me."

## Why this matters more here than on other projects

This project's workflow (`.agents/workflow.md`) explicitly has NO CI gate on
`automation/base` and relies on direct pushes from many concurrent implementer
sessions — branch drift mid-task is the norm, not an edge case, whenever a
campaign (multiple simultaneous implementer dispatches) is running.
