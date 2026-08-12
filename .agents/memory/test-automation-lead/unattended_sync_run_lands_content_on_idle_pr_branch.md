---
name: An unattended sync run can judge an idle PR branch "stale" and land unrelated content on it
description: A scheduled sync-base-branches run found my feature branch checked out and idle for ~11h (spanning an unrelated interruption storm), correctly-by-its-own-guard-logic judged it abandoned, and committed unrelated content (a hook perf fix + a different case's memory) directly onto it — recovered without data loss by redirecting the content to its real home (automation/base) before resetting the branch ref
type: feedback
---

## What happened (#335/ELITEA-2132, PR#698)

While round-4 reviewer dispatches were repeatedly failing (see the companion
`stale_branch_sessionstart_hook_hang_mimics_user_interruption.md` entry — the real
cause, discovered via this exact incident), my feature branch
(`tests/ELITEA-2132-chat-folder-creation-via-chats-header-icon`) sat checked out
and idle in the shared working tree for roughly 11 hours across several stalled
session restarts. A separate, scheduled unattended sync run (#712, working an
unrelated card) found the tree dirty and checked out on this branch, applied its
own recency-based liveness guard (mtimes / last-commit age — the exact guard this
project's `mid_work_guard_needs_recency_not_just_dirty_tree_presence.md` entry
describes), judged everything ~11-19h stale, and — correctly per its own
Step-0-style "classify and land" logic — committed the accumulated uncommitted
content as a single local commit **directly onto my branch**, since that's what
was checked out at the time. Content: a `.claude/hooks/sdlc-skills/lib.sh` perf
fix (see companion entry) plus an unrelated case's (ELITEA-2166) qa-engineer
memory writes. Never pushed — so PR#698 itself was never at risk — but it did sit
as a real local commit on the branch ref.

## Why this isn't a bug in the other session

The other run's guard logic is sound: literal dirty-tree-plus-checked-out-branch
presence is NOT sufficient signal of live work in a factory that runs many
concurrent conversations sharing one physical git tree — nearly every run would
trip a naive guard. Recency IS the right secondary signal. The failure mode here
is a genuine blind spot neither side could see from inside its own session: MY
session's branch really was idle for that whole window (the interruption storm
meant zero actual progress, zero commits, for ~11h) — from the sync run's
perspective this was indistinguishable from an abandoned branch. Both sessions
behaved reasonably given what each could observe.

## The recovery

1. Diagnosed via `git log --oneline` on the branch (found the unexpected commit),
   `git show --stat` (confirmed exact file list — memory + an unrelated hook fix,
   nothing in `automation/`/`test-specs/`), and cross-referenced the daily-log
   entry the other run had already written explaining its own reasoning.
2. **Never discarded any of it.** Re-homed the content to where it actually
   belonged: committed it onto `automation/base` directly (2 commits — one for
   content that happened to already be staged correctly since the shared tree's
   `HEAD` had ALSO drifted onto `automation/base` by the time I acted, one
   `cherry-pick` for the rest), pushed.
3. Only then reset the local feature-branch ref
   (`git branch -f tests/ELITEA-2132-... origin/tests/ELITEA-2132-...`) to discard
   the now-redundant local-only commit — safe because (a) it was never pushed
   anywhere else, (b) its content was already durably preserved on
   `automation/base` first, (c) the branch wasn't checked out at the moment of the
   `branch -f` (avoids the plain-checkout-silently-reverts-shared-file trap this
   file already documents several variants of).
4. Re-checked out the feature branch, verified clean, verified the PR diff was
   completely unaffected throughout (`gh pr diff --name-only` before and after
   matched).

## Standing rule

When a shared tree's `git log` on your own branch shows a commit you don't
recognize authoring: don't assume corruption or panic-reset. Read the commit
message and diff first — a genuinely helpful, well-reasoned concurrent process
(this project runs several) may have acted on your idle branch with good
intentions and left a clear paper trail explaining why. Redirect misplaced
content to its correct home before ever discarding the commit that carries it,
and never touch the branch ref while it's the checked-out `HEAD` of any active
worktree.
