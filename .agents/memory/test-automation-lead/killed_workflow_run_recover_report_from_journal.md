---
name: A killed batch-build run leaves NO report — rebuild it from journal.jsonl, and the outcome is merged-ungated
description: Units already merged on the trunk are delivered work; read the journal for their verdicts, re-run the gate yourself, hand-write report.json — never label them blocked
type: feedback
aliases: [workflow killed, no report.json, stopped workflow, merged-ungated, recover run]
tags: [area/workflow, type/recovery]
created: 2026-08-24
updated: 2026-08-24
---

## The failure shape

The task notification says *"No completion record was found … it may have been
stopped, or it may have been running when the previous process exited."* There
is no `report.json` in `.agents/automation/<slug>/`, but `gate-runs.jsonl` and
the trunk's merge commits exist.

**Nothing is lost.** Everything the run did is on disk in two places.

## Recovery, in order

1. **git first — what actually landed:**
   `git log --oneline <base>..tests/batch-<slug> | grep '^[a-f0-9]* merge'`
   Every `merge <CASE> into …` commit is a unit that was built, reviewed to
   APPROVED, and merged. That is delivered work.
2. **journal.jsonl for the verdicts** —
   `<transcriptDir>/subagents/workflows/<runId>/journal.jsonl`, one
   `{"type":"result",…}` per agent. Parse it for each unit's `status`, `verdict`,
   `pr`, and `findings[]` (defects filed, declarations owed). This is where the
   report's content comes from — do not re-derive it by re-reading diffs.
3. **`gate-runs.jsonl`** — how far the internal gate got before dying.
4. **Run the gate yourself, from scratch.** Partial internal gate runs do not
   count toward your independent 3×; the lead's gate is separate by contract.
5. **Hand-write `report.{json,md}`** with a `note` saying it was reconstructed.

`resumeFromRunId` is the alternative, but when every unit has already merged it
only re-runs the gate — which you must run independently anyway.

## The naming trap

The outcome for those units is **`merged-ungated`** — "re-run the gate", never
"failed". Labelling merged units `blocked` is how a dead run's summary once
claimed `blocked: 14` while 13 of 14 were merged. Check the trunk before
believing any negative outcome.

Field case: #1394 wave-01 (`wf_8a9b5968-939`, 2026-08-23) — killed after the 7th
unit merged and after 2 of 3 internal gate runs. All 9 cases were delivered;
recovery cost one journal parse plus a re-run gate.

Related: [[verify_pr_merged_before_trusting_any_workflow_outcome]] · [[report_case_outcome_can_falsely_say_blocked_for_an_already_merged_case]] · [[subagent_wait_and_resume_mechanics]]
