---
name: git worktree add/remove can leave the main checkout on the wrong branch
description: In this shared multi-session repo, using `git worktree add <path> <remote-branch> --detach` (then `remove --force`) to independently run a PR branch's tests coincided with the MAIN checkout's HEAD ending up on that PR's local branch instead of automation/base — always verify `git branch --show-current` on the main checkout after any worktree operation, and restore it explicitly if wrong
type: feedback
---

While independently re-running PR #608 (ELITEA-1799) to verify a reviewer fix,
used `git worktree add /tmp/pr608-review origin/tests/ELITEA-1799-new-chat-fresh-session
--detach` to avoid touching the shared main checkout, then `git worktree remove
--force` to clean up. Afterward, `git branch --show-current` on the MAIN
checkout (not the worktree) reported `tests/ELITEA-1799-new-chat-fresh-session`
instead of the expected `automation/base` (this repo's canonical working
branch per CLAUDE.md).

Root cause not fully isolated — this repo already had many local branches from
prior sessions (including one already named `tests/ELITEA-1799-new-chat-fresh-
session` with its own rebase history in the reflog, predating this session), so
it's plausible the main checkout was already on that branch from an earlier
session/turn before this one started, and the worktree add/remove was
coincidental rather than causal. But since `git worktree add --detach` should
never touch the main worktree's HEAD, and no explicit `checkout`/`switch` was
run in this session before the mismatch was noticed, treat this as unconfirmed
but real risk in a repo with this many stale local branches.

**Practical rule going forward:** in this repo specifically (many local
branches, shared checkout across many sessions), always check
`git branch --show-current` on the main checkout:
1. Before starting any worktree-based independent verification (baseline).
2. After removing the worktree (confirm it matches the baseline; if not,
   `git checkout automation/base` explicitly before finishing the session).

Uncommitted working-tree changes (modified/untracked files) survive branch
switches fine as long as there's no conflict — verified via `git status
--short` before and after, contents were identical — so a stray branch switch
by itself doesn't lose work, but leaving the shared checkout on the wrong
branch for the next session is its own hazard worth avoiding.
