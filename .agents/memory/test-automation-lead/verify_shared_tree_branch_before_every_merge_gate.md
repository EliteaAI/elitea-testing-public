---
name: Verify the shared tree's branch right before every merge gate, not just at session start
description: A dispatched subagent's own git worktree cleanup (not your own git actions) can leave the shared working tree checked out on a THIRD, unrelated branch by the time you're ready to run your independent pre-merge gate — check `git branch --show-current` immediately before that step every time, regardless of what you dispatched in between.
type: feedback
---

## What happened (#298/ELITEA-2095, PR #693, 2026-07-21)

Between dispatching a fresh reviewer (round 3, PR #693) and running my own
mandatory independent 3x pre-merge gate, the shared working tree ended up
checked out on `tests/ELITEA-2094-chat-new-conversation-participants` — a
**completely different, unrelated open case's branch** (#297/PR #688), not
my case's branch (`tests/ELITEA-2095-open-conversation-today-section`) and
not `automation/base`.

Root cause: the round-3 reviewer subagent did its own independent live
re-run via a `git worktree add`/`git worktree remove --force` cycle
(exactly the technique this project's memory recommends for isolated
verification). That cycle has a known, already-documented failure mode —
`git_worktree_can_leave_main_checkout_on_wrong_branch.md` (qa-engineer
memory, now 3 confirmed occurrences: PR #608, PR #693 rounds 2 and 3
inclusive) — where the MAIN checkout's branch pointer ends up wrong after
the worktree is removed. The reviewer subagent noticed this in its own
session and "restored" the tree to what it believed was the correct
branch — which was actually a THIRD case's branch (`tests/ELITEA-2094-...`,
left over from whatever the tree was on before this reviewer's own session
started), not mine. Its restoration was internally consistent with its own
priors; it had no way to know MY branch was the one that mattered next.

I only discovered this because I happened to run `git branch --show-current`
as a matter of routine right before creating/checking-out for the merge
gate — if I hadn't, my "merge gate" pytest invocations could have silently
run against the WRONG branch's code (a different case entirely), producing
a meaningless green that would not have validated PR #693 at all.

## The generalizable risk

This is a *third* variant of the shared-tree branch-clobber family already
in memory:
1. My OWN `git reset --hard` / careless checkout clobbering a subagent's
   uncommitted memory (multiple prior entries).
2. An IMPLEMENTER's cleanup `git checkout <path>` discarding a concurrent
   session's uncommitted file.
3. **This one**: a subagent's *legitimate, sanctioned* verification
   technique (worktree add/remove for isolated re-runs) has its own
   independent bug that changes which branch the SHARED tree's HEAD points
   to — with no malicious or careless action on anyone's part, just a tool
   quirk in a shared, non-isolated working directory.

All three variants share the same generalizable fix: **never assume the
shared tree is still on the branch you last left it on, at the specific
moment you're about to do something load-bearing with it (a merge-gate
run, a commit, a push).** Re-verify branch + `git status --porcelain`
immediately before that step, every time — not just once at session start,
not just "I didn't dispatch anything that touches git." A dispatched
subagent's OWN sanctioned technique can move the shared tree under you
even when its task had nothing to do with branch management.

## Rule going forward

Immediately before:
- creating/checking-out the branch for your own merge-gate pytest runs,
- any commit or push you're about to make,
- any file read whose content depends on which branch is checked out,

run `git branch --show-current` (and `git status --porcelain` for
uncommitted drift) fresh, even if you believe nothing since your last
check should have moved it. If it's wrong, don't just `checkout` blindly —
check for uncommitted changes first (they may be legitimate deliverables
from whatever subagent last touched the tree) and land them properly
(stash-scoped-to-paths → checkout target → apply → commit on the correct
branch) before switching, per the existing shared-tree-memory-landing
playbook.
