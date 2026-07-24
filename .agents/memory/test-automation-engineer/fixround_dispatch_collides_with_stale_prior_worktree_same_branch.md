---
name: Fix-round dispatch collides with a stale prior-implementer worktree on the same branch
description: A fix-round dispatch gets a brand-new isolated worktree, but the case's branch may still be checked out in the ORIGINAL implementer's now-unlocked worktree from an earlier round — git refuses a second checkout until that worktree is freed.
type: feedback
---

Dispatched for a fix round on ELITEA-2082/2083/2080 (branch
`tests/ELITEA-2082-2083-2080-create-toolkit-from-conversation-canvas`), my
prompt named the branch to work on, but my assigned worktree started on an
unrelated branch (`worktree-wf_<id>`). `git checkout <branch>` initially
wasn't tried directly — `git worktree list` showed the target branch was
still checked out in a DIFFERENT worktree from the original implementer
round (not marked "locked" in the list, i.e. no active session was using
it — that session had ended after committing, without pushing).

**Two dead ends before the fix:**
1. `EnterWorktree(path=<the other worktree>)` reported success ("working
   directory now points at...") but every subsequent `Bash` call was
   refused: "this agent is isolated in worktree X but cwd resolved to Y."
   A subagent with a pinned cwd (worktree isolation) can LOOK at another
   worktree's path via `EnterWorktree(path=...)` but cannot actually run
   commands there — the sandbox enforces the ORIGINAL assignment.
2. `ExitWorktree` then refused outright: "cannot be called from a subagent
   with a cwd override... use Bash with `cd`." The only way back was
   re-issuing `EnterWorktree(path=<my own original worktree>)`.

**The fix:** from my OWN worktree, `git worktree remove <stale-worktree-
path>` — safe here because the stale worktree had no active session and
every commit it held was already reachable via the shared branch ref (a
worktree removal never deletes branch history, only the checkout). After
that, `git checkout <branch>` in my own worktree succeeded normally and
picked up the prior implementer's commits intact.

**Takeaway for next fix-round dispatch:** if the named branch won't
checkout, run `git worktree list | grep <branch>` before escalating — a
non-"locked" entry is very likely an orphaned worktree from the prior
round, safely removable to unblock your own checkout. Don't try to work
inside it via `EnterWorktree(path=...)` — a pinned subagent can't actually
operate there.

**Separately (same session):** the reviewer findings existed even though
no PR had been opened yet — the original implementer round had committed
locally per an explicit "don't push yet, batch-integrate will handle it"
instruction, and review ran against the raw local diff. So a fix-round
dispatch saying "update the PR" can actually mean "open it for the first
time" — check with `gh pr list --json headRefName` (or by branch name)
before assuming one exists to push to.

**CONFIRMED a second time (ELITEA-1976 fix round, 2026-07-24, worktree
`wf_e44028a9-dec-112` vs the stale `wf_e44028a9-dec-58`).** Identical shape:
non-"locked" prior-round worktree still held the branch, `git worktree
remove` from my own worktree freed it, checkout picked up all 3 prior
commits cleanly. This time a PR (#1049) already existed (pushed by the
prior round), so "update the PR" meant literally push + `gh pr edit
--body-file` — the two outcomes ("PR doesn't exist yet" vs "PR exists,
push a new commit") are BOTH live possibilities for a fix-round dispatch;
check `gh pr list --json headRefName,number,url` first, don't assume
either.
