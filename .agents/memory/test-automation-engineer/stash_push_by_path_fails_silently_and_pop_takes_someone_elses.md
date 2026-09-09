---
name: git stash push by path fails silently, and a chained pop takes someone else's stash
description: A wrong-cwd `git stash push -- <path>` creates nothing; the `&& git stash pop` after it pops stash@{0}, which is not yours
type: feedback
aliases: [stash pop wrong stash, stash push relative path, ruff baseline stash, stash@{0} conflict]
tags: [area/git, type/hazard]
created: 2026-09-09
updated: 2026-09-09
---

## What happened

To measure a ruff baseline I ran, from `automation/`, a single chained command:

```bash
git stash push -- automation/tests/ui/agents/test_x.py >/dev/null 2>&1 && ruff check . ; git stash pop
```

The path was repo-relative but cwd was `automation/`, so **`git stash push` matched
nothing and created no stash** — while still exiting 0 with output suppressed. The
`git stash pop` that followed then popped **`stash@{0}`, which belonged to a completely
different, months-old branch** (this repo carries 18 parked stashes from other agents'
sessions). It conflicted (`UU .agents/automation/campaigns/chat-remaining.md`), which
was the only reason it was noticed at all.

## Why it was recoverable

A conflicting `pop` does **not** drop the stash. `git stash list` still showed the entry
intact, so the fix was `git checkout HEAD -- <the conflicted file>` and nothing was lost.
A *clean* pop would have silently dropped someone else's parked work.

## Rules

- **Never chain `stash push` and `stash pop` in one command.** Run the push, read its
  output, confirm with `git stash list` that YOUR entry is on top, and only then pop.
- **Never suppress `git stash push` output** — "No local changes to save" is the whole
  signal.
- **Paths passed to `git stash push -- <path>` are relative to cwd**, not the repo root.
- **Prefer not stashing at all.** For a before/after tool comparison, `cp` the file
  aside, `git show HEAD:<path> > <path>`, measure, then `cp` it back — no stash, no
  shared state, and it works the same when other people's stashes are parked in the repo.
  (`--stdin-filename` is NOT a substitute — see [[ruff_stdin_filename_gives_a_false_clean]].)

Related: [[ruff_stdin_filename_gives_a_false_clean]]
