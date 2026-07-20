---
name: git reset --hard clobbered subagent memory a THIRD time — worktree is now mandatory, not a suggestion
description: despite having both prior write-ups (orchestrator_git_reset_hard_clobbers_subagent_memory.md, git_reset_hard_incident_recurred_use_worktree.md) loaded in memory at session start, I ran the exact same `git checkout <branch> && git reset --hard origin/<branch>` in the shared tree before the merge-gate step on issue #293/ELITEA-2090/PR#682, destroying the just-returned reviewer subagent's uncommitted MEMORY.md index line + daily-log entry
type: feedback
---

## What happened (third occurrence)

Session for issue #293 (ELITEA-2090, PR #682). Immediately after the reviewer
subagent (fresh qa-engineer session, dispatched in the same shared working
tree) returned its APPROVED verdict — with its final report explicitly
stating it had just written a new curated memory file, a daily-log entry, and
an updated `MEMORY.md` index line — I ran, to "freshen" the checkout before
my own independent pre-merge gate:

```
git checkout tests/ELITEA-2090-create-conversation-private-project-default-llm
git reset --hard origin/tests/ELITEA-2090-create-conversation-private-project-default-llm
```

This is the third time this exact command shape, for the exact same reason
(staleness paranoia before the merge gate), has destroyed a subagent's
just-written uncommitted memory. Both prior incidents were already written up
with an explicit "use a worktree instead" fix — and I had read them (they
were in my own memory index at session start, this session) — and still ran
the destructive command in the shared tree anyway.

Damage this time: `qa-engineer/MEMORY.md`'s new index line and the reviewer's
`daily/2026-07-20.md` entry were both discarded (uncommitted, tracked-file
modifications; `reset --hard` wipes those with no stash, no reflog entry to
recover from). The new curated `.md` file itself survived (untracked files
aren't touched by `reset --hard`) — same partial-survival pattern as both
prior incidents. Recovered by hand-reconstructing the index line + daily-log
narration from the reviewer subagent's own final report text (still visible
in the conversation transcript) — lossy in the same way as before, but this
time the loss was caught and fixed within the same turn rather than
discovered later.

## Why "read the memory, be more careful" has now failed three times

Vigilance is empirically not a working control for this failure mode across
three separate sessions/cases (#83, #71/ELITEA-1897, #293/ELITEA-2090). The
task-pressure moment ("I need a clean checkout before the gate, `reset --hard`
is the reflexive tool for that") reliably overrides having read a memory
entry earlier in the same session. A memory note that only says "be careful"
is not a fix; the fix has to remove the decision point entirely.

## The actual, now-mandatory fix

**Never run `git checkout` / `git reset --hard` / `git clean` on the shared
primary working tree for a merge-gate (or any post-subagent) step, full stop.**
Use `EnterWorktree` / `ExitWorktree` (or `git worktree add`) to get an isolated
checkout of the PR branch instead:

```bash
git worktree add /tmp/merge-gate-<case-id> origin/<pr-branch>
cd /tmp/merge-gate-<case-id>/automation
ln -s "$WORKSPACE/elitea-testing-public/automation/.env.test" .env.test
# run the 3x pre-merge gate here — shared tree's HEAD never moves, nobody's
# uncommitted memory writes are ever at risk
cd - && git worktree remove /tmp/merge-gate-<case-id>
```

If a worktree is genuinely unavailable, the fallback is to never check out
away from `automation/base` in the shared tree at all — extract the PR's
content via `git show <sha>:<path>` / `git archive` instead of a working-tree
checkout.

**Standing self-check, now non-negotiable**: before typing `git checkout` or
`git reset` in the shared tree, the question is not "am I being careful" —
it's "why am I not using a worktree for this." If the answer isn't a
documented, genuine worktree-unavailability reason, stop and use the worktree.
