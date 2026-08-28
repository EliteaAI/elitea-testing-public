---
name: git checkout <ref> -- <path> overwrites the INDEX, not just the worktree
description: Destroys staged work silently; use a /tmp copy for before/after comparisons instead
type: feedback
aliases: [checkout ref path, lost staged changes, index overwritten, control run file swap]
tags: [area/git, type/hazard]
created: 2026-08-28
updated: 2026-08-28
---

## What happened

While porting ELITEA-2051 to `main` (PR #1931), I wanted a before/after `ruff`
comparison on four files I had just staged. I ran:

```bash
git checkout origin/main -- <the 4 files>   # ruff "before"
git checkout --          <the 4 files>      # intended: "restore my work"
```

**All four files' changes were destroyed.** `git checkout <ref> -- <path>` writes
the ref's content into **both the index and the working tree**. So the second
command faithfully restored the working tree from an index that now held
`origin/main`'s content. No warning, no reflog entry, no diff — the work was
simply gone. Nothing had been committed yet, so there was no recovery path; I
re-did the whole port.

## The rules that follow

1. **Commit before any comparison manoeuvre.** A commit is the only thing that
   makes `git checkout HEAD -- <path>` a safe restore.
2. **For a before/after or matched-control comparison, never move the ref into
   the tree.** Copy the other version OUT instead:
   ```bash
   git show <ref>:<path> > /tmp/before.py          # read-only, touches nothing
   cp <path> /tmp/MY_VERSION_BACKUP.py             # explicit backup first
   ```
   For a control RUN that genuinely needs the file in place, `cp` the pristine
   version over it (worktree only — the index and HEAD stay intact), then `cp`
   the backup back. That is what I did for the `#1082` control on this PR, and
   it was clean.
3. **`git checkout <ref> -- <path>` is only safe as an *acquisition* move** —
   pulling a file you do not yet have a version of, as the port itself did.

Related: [[zsh_does_not_word_split_unquoted_variables]]
