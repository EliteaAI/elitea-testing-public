---
name: Factory-mode Workflow wait is a TaskOutput poll loop, not ending the turn
description: In unattended/factory mode, a multi-hour Workflow() call is waited out with repeated TaskOutput(block=true, timeout=600000) calls in the SAME turn — never by ending the turn to "let the background task notify me later"
type: feedback
---

## The conflict this resolves

The `Workflow` tool description says it "runs in the background... returns
immediately with a task ID... a `<task-notification>` arrives when it
completes" — which reads like an invitation to end the turn and let the
notification wake the session later, same as any other background task.

Factory-mode's own delta rule 5 says the opposite, explicitly and without
carving out an exception for Workflow: *"Waiting is work you do INSIDE the
turn... NEVER end your turn 'to check later': in this mode there is no later
— the loop re-runs you instantly, each glance-and-quit reads as a stalled
attempt... This applies to waiting on ANYTHING."*

Resolved on #1297's `pipelines-remaining` wave-01 (2026-08-08): treated the
factory-mode delta as authoritative over the tool's general background-task
framing, and waited out a ~5.5 hour, 43-agent `batch-build` Workflow call
entirely in-turn.

## The mechanism

`TaskOutput(task_id, block=true, timeout=600000)` — the max allowed timeout
(600000ms = 10min) — called **repeatedly in a loop within the same turn**.
Each call either returns the completed result, or times out with
`<retrieval_status>timeout</retrieval_status>` + `<status>running</status>`,
at which point you just call it again. This is NOT ending the turn — it's a
sequence of tool calls, same turn, same conversation, no notification
mechanism involved at all. 33 such calls covered the wave-01 run.

Between polls (not required, but useful to confirm real progress rather than
blind waiting), read the workflow's own journal directly:
```
<transcriptDir>/subagents/workflows/wf_<runId>/journal.jsonl
```
— each line is a `{"type":"started"|"result", "key":..., "agentId":...,
"result":{...}}` record; grep it for merge confirmations, review verdicts,
or PR numbers to sanity-check the run is actually advancing, not stalled.

## Why this matters beyond just "don't violate the rule"

A `local_workflow` task type behaves differently from a `local_bash`
background task in ONE relevant way for this call: block=true genuinely
blocks up to the timeout server-side and returns the moment the workflow
finishes, so the loop-of-TaskOutput-calls pattern costs zero extra latency
compared to "wait for the notification" — the wall-clock time is identical,
only the mechanism differs. There is no efficiency argument for ending the
turn instead.

## Rule

Any `Workflow()` call dispatched from a factory-mode/unattended session:
write the runId to durable state immediately (campaign card or equivalent —
separately load-bearing, context-fragile regardless of wait mechanism), then
poll it out with a `TaskOutput(block=true, timeout=600000)` loop in the same
turn until it completes. Do not `ScheduleWakeup`, do not end the turn "to be
notified", do not treat the tool's background-task framing as overriding the
factory-mode delta — the delta is the more specific, more recently-loaded
instruction and wins.
