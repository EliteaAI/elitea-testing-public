---
name: Pipeline generic Interrupt-after resume confirmed broken (#1327)
description: ELITEA-2047 — pause works, plain-chat "type anything" resume does NOT resume the checkpointed run; spawns a new run instead. Distinct from HITL's #1103.
type: feedback
---

## What I confirmed live (ELITEA-2047 analysis, 2026-08-08, pipeline id 8159)

Picked up where `test-automation-engineer`'s earlier implementation attempt left off
(`.agents/memory/test-automation-engineer/pipeline_generic_interrupt_after_resume_is_ambiguous.md`
flagged this as "needs-analyst"). Confirmed the ambiguity resolves to a real product
defect, not a timing/UI-discovery issue:

- `interrupt_after` is a **pipeline-level** YAML field (`entry_point: X\ninterrupt_after:
  \n  - X\nnodes: ...`), not nested under the node — the one genuinely new handle shape
  this case needed vs. every other `CommonInterruptSettings.jsx` sibling (structured
  output, etc., which DO nest under the node).
- Pause behavior is 100% correct: interrupted node executes, then an `interrupt` pill
  appears on the canvas edge, the node's whole config panel locks, chat header shows
  "Run is in progress"/"Run N details"/"Stop run", and chat auto-posts "How to proceed?
  To resume the pipeline - type anything...".
- Sending a plain chat message per that instruction does NOT resume — it spawns a
  **second, separate Run History entry** (confirmed via the Run History dialog's
  Date/Version/Duration table showing 2 distinct rows with different durations) instead
  of continuing the checkpointed run. Same "How to proceed?" hint repeats verbatim.
  Printer 1 (the downstream node) never executes. Reproduced 2/2 across two independent
  sessions (implementer's earlier attempt + this one), zero console errors both times.
- Filed `EliteaAI/elitea-testing-public#1327` — explicitly NOT a duplicate of `#1103`
  (HITL node's dedicated approve/reject resume path is a completely different mechanism
  with real action buttons; this is a bare interrupt whose only "resume" affordance is
  a text hint, and the hint doesn't work).

## Classification takeaway

Per `.agents/testing.md` § Merge gate's analysis-time exception: a defect isolated to a
case's TAIL step (here, step 8 of 8 — steps 0-7 pass cleanly) gets `ready-for-automation`
with the tail assertions written as `expect.soft()` + `# Known defect: #N`, not
`defect-found`. `defect-found` is for defects that BLOCK reaching later steps — this one
doesn't (I executed all 9 steps, including the broken one, to completion).

## For the next analyst/implementer on this surface

Don't assume ANY interrupt/pause mechanism resumes like HITL's approve/reject just
because it "looks similar" — HITL has dedicated websocket wiring
(`chat_continue_predict{hitl_resume:true, hitl_action}`); the generic
`interrupt_before`/`interrupt_after` toggle (available on every OTHER node type) has NO
such wiring behind its "type anything" hint. If a future case touches this again, check
`#1327`'s status before re-deriving.
