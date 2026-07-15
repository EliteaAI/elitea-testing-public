---
name: Never ScheduleWakeup on a live background process
description: In unattended/headless factory mode, waiting on a still-running background Bash/Monitor task must be a blocking foreground call or in-turn poll — ScheduleWakeup ends the turn and can orphan/kill the very process being waited on
type: feedback
---

## What happened (issue #62 / ELITEA-1894, 2026-07-15)

Mid merge-gate (my own independent 3× pre-merge pytest run), a `pytest` invocation
ran long enough that the harness auto-backgrounded it. I armed a `Monitor` to watch
its output file, then called `ScheduleWakeup` to end the turn and resume later.

On the next turn, the task-notification reported BOTH the background pytest task
AND the Monitor as `stopped` with **no completion record** — i.e. the wait was
never resolved, the process was torn down, and I had to re-verify all state
(branch, PR, dev server) and rerun the entire 3× gate from scratch.

## Why this is wrong, not just unlucky

The factory-mode instructions are explicit: "Waiting is work you do INSIDE the
turn... NEVER end your turn 'to check later': in this mode there is no later."
`ScheduleWakeup` is designed for `/loop` dynamic-mode self-pacing (deciding when
to resume a recurring task) — it is NOT a substitute for waiting on a specific
in-flight process this turn. Ending the turn (which `ScheduleWakeup` does,
confirmed by its own tool result: "Nothing more to do this turn") is exactly the
"glance-and-quit" move rule 5 forbids, and in this case it had a second, sharper
cost: the harness/session teardown between turns can orphan a backgrounded child
process, destroying the very result being waited for.

## The correct pattern

- A command likely to run long: just run it via `Bash` with a long enough
  `timeout` that it completes inline (pytest UI runs in this project take
  30-120s — well within the 600000ms max), OR
- If it auto-backgrounds anyway, wait it out truly in-turn: a blocking
  foreground command (`wait`, a polling loop with bounded `sleep`), not a
  turn-ending mechanism. Do NOT call `ScheduleWakeup` as a way to "come back
  after the Monitor fires" — background-task and Monitor notifications already
  resume the session on their own; `ScheduleWakeup` adds nothing there except
  the risk of the turn-boundary teardown.
- Reserve `ScheduleWakeup` for genuine `/loop` dynamic-mode self-pacing (e.g.
  the cardless intake-mission reruns), never for "I'm waiting on a subprocess I
  started this turn."

## Recovery, if it happens anyway

Don't trust anything about the interrupted run. Re-verify from scratch: current
branch/commit, PR state (open/mergeable/head SHA unchanged), dev server up —
then redo the full gate (all N runs, not just the ones that didn't get to
report). A partial gate result from before the interruption is not evidence.
