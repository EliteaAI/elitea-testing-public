---
name: No TaskOutput tool this session — fallback is ListAgents + Bash run_in_background sleep, still in-turn
description: TaskOutput(block=true) from factory_mode_workflow_wait_... isn't always an available tool; when absent, poll ListAgents between short Bash run_in_background sleeps in the SAME turn — notifications for both the sleep and the agent still arrive mid-turn, satisfying the same in-turn-wait rule
type: feedback
---

## What happened (ELITEA-1805, issue #2392, 2026-10-06)

Needed to wait out a `SendMessage`-resumed implementer (fix-only round: priority
marker p3→p2) and then a resumed reviewer (re-review), in factory/unattended mode.
`factory_mode_workflow_wait_is_taskoutput_poll_loop_not_turn_end.md` prescribes
`TaskOutput(task_id, block=true, timeout=600000)` in a loop — but no `TaskOutput`
tool was present in this session's tool list at all (checked the full tool set
given at dispatch). A bare foreground `sleep` is also blocked by the harness
("Blocked: standalone sleep N... use Monitor" or "use run_in_background: true") —
and `Monitor` is the one tool the factory-mode delta explicitly forbids outright.

## The working fallback

`Bash(sleep <=60; echo tag, run_in_background: true)` + `ListAgents` between
calls, repeated **within the same turn** (never ending the turn to "be notified
later"). Both the background bash job's completion and the resumed agent's own
completion arrive as `<task-notification>` system reminders **mid-turn, while
still issuing tool calls** — confirmed twice in this session (SendMessage-resumed
implementer AND reviewer both completed and notified correctly this way, no
process-restart loss, unlike the two failures in
`sendmessage_resume_fragile_in_factory_mode.md`). `ListAgents` itself is cheap and
side-effect-free, so polling it every ~30-60s between bounded background sleeps is
safe to repeat as many times as needed.

## Rule

If `TaskOutput` isn't in your tool list, don't substitute `Monitor` (forbidden) or
a bare `sleep` (harness-blocked) — use `Bash(run_in_background: true, sleep <=60)`
+ `ListAgents` polling, all inside the current turn. This satisfies the same
"wait is work you do INSIDE the turn" rule the TaskOutput pattern exists for; the
only difference is which tool delivers the notification.
