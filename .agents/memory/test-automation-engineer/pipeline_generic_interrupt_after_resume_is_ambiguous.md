---
name: Pipeline generic Interrupt-after resume is ambiguous (not HITL)
description: Live-confirmed 2026-08-08 (ELITEA-2047 exploration) — the raw per-node Interrupt-before/after toggle DOES visibly pause execution, but the chat-side "resume" path is unconfirmed/possibly broken; do NOT assume it works like HITL approve/reject
type: feedback
---

## What I confirmed live (localhost, ELITEA-2047 exploration, pipeline id 8159)

`interrupt_before`/`interrupt_after` (`CommonInterruptSettings.jsx` toggle, every
node type — Code/LLM/MCP/Toolkit/Custom/Decision/Agent) is a genuine
LangGraph-checkpoint debug feature (per `elitea-pipeline` skill's
`workflows.md`), distinct from the HITL **node type**. Turning "Interrupt after"
ON for a Code node (with a real downstream node, e.g. Code 1 -> Printer 1 -> END,
so the toggle isn't `disabled` per the already-documented entry-point/END rule)
and executing via embedded chat:

- **DOES pause visibly**: an `interrupt` pill renders on the canvas EDGE right
  after the interrupted node; the paused node's whole config panel becomes
  `disabled` (locked); the chat header shows "Run is in progress" (persistent
  spinner) + "Run N details" + a "Stop run" button; `Run N details` dialog shows
  `In progress` with a `Timeline step: Start` / `<node>: Completed` breakdown and
  before/after state diffs for that node.
- Chat auto-posts a hint after the node's own execution-result bubble:
  *"How to proceed? To resume the pipeline - type anything..."*
- **Resume is NOT confirmed working from a plain chat message.** Sent `"Hello"`
  (trigger) then `"continue"` (attempted resume): the SAME "How to proceed?"
  hint re-appeared verbatim, `Run is in progress`/the `interrupt` edge pill never
  cleared, and Printer 1 never produced output — even after ~20s of waiting.
  This is either (a) a genuine product defect in the generic-interrupt resume
  path, (b) a much longer settle time than HITL's (~8s) needs, or (c) a resume
  mechanism the UI doesn't actually wire for a bare interrupt (only HITL nodes
  get real approve/reject websocket actions — c.f. the already-documented
  "no REST resume path" gap for the sensitive-action-guardrail interrupt in
  `elitea-testing` skill's `test-patterns.md`).

## Why this blocked automating ELITEA-2047 in one pass

The case's steps 6-8 ("execute, verify pauses, verify UI shows interrupt state,
resume, verify completes") assume a clean pause+resume cycle like HITL's
Approve/Reject. Steps 6-7 are solid and automatable today. Step 8 needs a
dedicated, careful analyst session — NOT an already-mapped-ground assumption —
with: multiple repro attempts, a `capture_websocket_frames()` capture (like
ELITEA-2015's HITL runtime test) to see whether "continue" even sends a distinct
resume-shaped frame vs a fresh `start_task`, and a longer settle-time check
before concluding defect vs slow-but-working.

## Takeaway for the next analyst on this surface

Don't assume "Interrupt after" runtime behavior generalizes from the HITL node's
approve/reject flow (ELITEA-2015) — HITL has dedicated resume wiring
(`chat_continue_predict` + `hitl_action`/`hitl_resume`); a bare
`interrupt_before`/`interrupt_after` on a non-HITL node may have NO equivalent
resume action wired to a plain chat message. Websocket-frame capture is
required before writing the AFS's resume-step assertions, not just DOM
observation.
