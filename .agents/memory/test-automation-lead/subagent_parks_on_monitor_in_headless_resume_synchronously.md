---
name: A dispatched subagent can park on a background Monitor mid-task in headless mode — resume it via SendMessage with an explicit synchronous instruction
description: An implementer subagent ended its turn saying "I'll continue once the Monitor notifies me" — no commit/push/PR done; check ground truth on disk, then SendMessage the same agent to finish foreground, don't re-dispatch a fresh one
type: feedback
---

On #370, an implementer subagent (dispatched `run_in_background: false`) still ended its
turn parked on a background Monitor watching its own pytest run: *"I've started a Monitor
to watch for the pytest run to finish; I'll continue once it notifies me."* That's a
session-fatal move in unattended/headless mode — the result has nobody to collect it, and
the handoff (commit/push/PR) never happened.

**Detection:** never trust the parked-message as done. Check ground truth on disk:
`git log`/`git status` in the worktree, `gh pr list --head <branch>`, the junit archive
(`reports/archive/junit_*.xml`) for the actual last run's verdict. On #370 the test had
FAILED once (14s) and the agent was mid-debug — nothing committed.

**Recovery — resume the SAME agent, don't spawn a fresh one:** it holds the debug context.
`SendMessage(to: "<agentId>", ...)` with an explicit instruction to (a) run every pytest
FOREGROUND/blocking and act on the result in the same turn — a Monitor result is a dead end
here; (b) respect the ≤2-reruns/root-cause budget or escalate honestly; (c) finish the
handoff (commit only its own artifacts, push, open PR with Run Report). The resume returns
in the background too, but it's harness-tracked, so a task-notification re-invokes you on
completion — don't poll, don't ScheduleWakeup a short interval (wasted); just let the
completion notification arrive.

A fresh re-dispatch would lose the 6-fixes-deep debug state and repeat work. Resume-with-
context is strictly better when the agent already did most of the work and only fumbled
the finish.
