---
name: git stash -q push fails and the next pop takes a stranger's stash
description: "`git stash -q push -- <paths>` errors out (flag before subcommand), and a chained `git stash pop` then applies stash@{0} from another branch"
type: feedback
aliases: [stash pop foreign stash, git stash flag order, stash push -q]
tags: [area/git, type/trap]
created: 2026-09-15
updated: 2026-09-15
---

## What happened (ELITEA-3208 batch, 2026-09-15)

`git stash -q push -- api/client.py config.py && … ; git stash pop -q` — the `-q` BEFORE `push`
makes git say "subcommand wasn't specified; 'push' can't be assumed" and stash NOTHING; the
`pop` then applied **stash@{0}, a months-old WIP from a different branch**, which conflicted
(`UU .agents/automation/campaigns/chat-remaining.md`) and was "kept" because of the conflict.
Recovery: `git stash show --stat stash@{0}` to see its file list, `git checkout HEAD -- <that
file>`; the stash list count stayed 18, nothing else touched.

## Rules

- Flags go AFTER the subcommand: `git stash push -q -- <paths>`.
- Never chain `git stash pop` after a stash whose exit code you did not check — if the push
  failed there is nothing of yours to pop, and this clone carries 18 foreign stashes.
- To lint "is this finding pre-existing?", don't stash at all: `git show <trunk>:<path> >
  /tmp/x.py && ruff check /tmp/x.py` and compare counts.

Related: [[git_checkout_ref_path_overwrites_the_index]] · [[never_amend_after_a_failed_husky_commit_on_shared_branch]]
