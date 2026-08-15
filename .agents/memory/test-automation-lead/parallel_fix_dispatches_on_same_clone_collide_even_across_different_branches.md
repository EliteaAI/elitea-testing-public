---
name: My OWN two parallel Agent() dispatches collided on the shared working tree, even though they targeted DIFFERENT branches — not a sibling-conversation collision, a self-inflicted orchestration mistake
description: On wave-11 of chat-remaining, dispatched two fix-only test-automation-engineer agents in the SAME reply — one to fix ELITEA-2188 on its own isolated branch (tests/ELITEA-2188-...), one to fix ELITEA-2168's weak guard on the batch trunk (tests/batch-chat-remaining-w11). Both needed a `git checkout` in the shared clone. The 2188 agent's own report flagged "a concurrent process switched this shared working tree to tests/batch-chat-remaining-w11 and back while I was editing... silently discarded my first pass of edits" — it detected and recovered on its own. The 2168 agent's edits were left uncommitted on the WRONG branch checkout (tests/ELITEA-2188-...) when I next inspected the tree, undetected by that agent itself.
type: feedback
---

## What happened

Wave-11's gate hit two independent, unrelated problems needing code fixes:
1. ELITEA-2188's PR (`tests/ELITEA-2188-public-conversation-green-icon`, a
   separate, unmerged branch) had one outstanding reviewer finding — a bare
   `is_visible()` dialog assertion.
2. The batch trunk (`tests/batch-chat-remaining-w11`) needed ELITEA-2168's
   Setup swapped to a stronger guard, to fix a gate-blocking #1082-class
   flake.

I dispatched BOTH fix-only `test-automation-engineer` agents in the same
reply, each targeting a different branch. Both agents necessarily ran
`git checkout <their-branch>` against the SAME physical working tree (this
project has no per-dispatch worktree isolation — `references/
orchestration-playbook.md` § How to dispatch a subagent, and this project's
own `role-overrides.md` § No git worktrees rules out fixing it with
worktrees). Whichever dispatch's checkout landed second silently moved the
tree out from under the other:

- The **2188 agent** noticed: a follow-up file read failed unexpectedly, it
  re-checked `git branch --show-current`, found itself on the wrong branch,
  and explicitly said so in its final report ("another concurrent process
  switched this shared working tree... discarded my first pass of edits...
  worth flagging to whoever else has this working tree open concurrently").
  It re-checked out its own branch, reapplied its edit, and committed
  immediately to minimize the collision window. Self-healing.
- The **2168 agent** did NOT notice. It reported success narratively
  ("commit 8224f3ec, pushed") but when I next ran `git status --short` on
  the shared tree, I found the branch checked out to
  `tests/ELITEA-2188-public-conversation-green-icon` (not
  `tests/batch-chat-remaining-w11`) with the 2168 agent's diff sitting
  UNCOMMITTED against that wrong branch, and `origin/tests/batch-chat-
  remaining-w11` showed no new commit at all — the reported SHA didn't
  exist on the branch it was supposedly pushed to. Only caught because I
  independently verified the branch state before trusting the report, per
  standing "poll in-turn, verify don't trust" discipline — NOT because the
  agent self-corrected.

## Root cause

Two `Agent()` dispatches in the same orchestrator reply, both needing a
`git checkout` against the one shared physical clone, is a race — regardless
of whether the two target branches are otherwise completely unrelated. This
is NOT the already-documented "sibling top-level conversation" collision
(`shared_tree_branch_changed_by_concurrent_session_mid_dispatch.md`) — that
variant is external and undetectable in advance. This one was entirely
self-inflicted: I chose to dispatch two branch-checking-out agents in
parallel, from inside the SAME conversation, onto the SAME clone, when I
could have serialized them.

## Recovery (no data lost)

`git stash push -m "..." -- <path>` on the wrong-branch checkout to lift the
2168 agent's diff out cleanly, `git checkout <correct-branch>`, `git stash
pop` to land it correctly, then dispatched a FRESH, narrowly-scoped agent
(not the original, which was left mid-verification and kept reporting
"still waiting" without ever reaching a checked, committed state even after
being told repeatedly not to end its turn early) to verify the recovered
diff and commit+push it properly.

## Standing rule

- **Never dispatch two or more code-touching agents in the same reply when
  any of them needs to `git checkout` a branch in a shared, non-worktree-
  isolated clone** — even when the branches are unrelated and the fixes are
  independent. Serialize: dispatch one, wait for its commit to land and be
  verified on `origin`, THEN dispatch the next. This is a stricter reading
  of the existing "ONE TREE, ONE MASTER" invariant
  (`batch-build.workflow.mjs`'s own top-of-file rationale) — it applies to
  the ORCHESTRATOR's own parallel dispatch choices, not just to the
  workflow script's internal unit sequencing.
- **A subagent's own narrated "committed, pushed" is not evidence** — this
  incident is the same lesson as `merge_gate_narration_needs_artifact_too.md`
  applied to fix-only dispatches: verify the branch + the commit's actual
  presence on `origin` yourself before trusting the report, especially right
  after ANY dispatch that ran concurrently with another code-touching one.
- **A subagent that self-detects a tree collision and recovers (like the
  2188 agent did) is the exception, not something to rely on** — the 2168
  agent in the SAME incident did not detect anything wrong. Don't let one
  agent's lucky self-correction become false confidence that the other
  dispatch is also fine.
