---
name: Workflow internal gate failed twice in a row — stop retrying, run it yourself
description: batch-build's internal gate agent hit a transient Connection-refused, then on resume was cut off mid-run with 0 runs banked — a third resume isn't warranted; scope your own gate to the batch's exact modified node-ids and run it directly
type: feedback
---

## What happened (`skills-buildwithai-fidelity-rework`, 2026-08-14)

All 3 build units (implement → review → merge) completed cleanly and cached
correctly across two `Workflow()` invocations. The gate+report tail failed
twice in a row, in two DIFFERENT shapes:

1. **First run:** the gate agent AND the report agent both errored with
   `API Error: Connection refused — a firewall or proxy may be blocking it` —
   a genuine infra blip, surfaced in the top-level `<failures>` list, not as
   a per-case `blocked` outcome. All 3 units still showed `merged-ungated`
   (correct — they really were merged, just unproven).
2. **Resumed with `resumeFromRunId` + identical args** (per
   `subagent_wait_and_resume_mechanics.md` — args is mandatory every resume).
   All 9 build-phase agents replayed from cache instantly (correct). The gate
   agent ran LIVE this time and actually did setup work (289s, 25 tool calls:
   fetched, checked out the trunk, confirmed clean tree, identified the
   changed spec) — but never got past setup: returned
   `{"verdict":"incomplete","runs":0,"notes":"CUT OFF mid-flight — do not
   treat as red or not-run"}`. The report writer then ran and returned
   `written:false` (the sibling known pattern, see
   `report_writer_agent_can_refuse_disk_write.md`).

Neither shape is a red gate — both are "no verdict produced." Distinct from
both entries already on file: not the hard `StructuredOutput`-never-called
failure (`workflow_gate_hard_failure_vs_soft_stall_different_recovery.md`,
where `Workflow()` itself throws), and not the soft `not-run` stall
(`workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md`, a
normal-looking completed call with a useless verdict). This is a genuine
external API error the FIRST time, and an incomplete-but-not-hard-failed
in-progress call the SECOND time — two different failure modes in a row on
the same batch's gate/report tail.

## What I did instead of a third resume

Ran the gate myself, directly, no workflow involved:

1. `git fetch origin && git checkout <trunk>` (plain checkout, no worktree).
2. Scoped to the batch's EXACT modified node-ids (derived from each unit's
   brief/AFS Verification section — 8 node-ids here), not the whole file —
   avoids pulling in the file's OTHER pre-existing tests the batch never
   touched (`.agents/memory/test-automation-lead/large_batch_gate_scope_by_nodeid_not_file.md`
   already establishes this; this is a confirming instance).
3. 3 SEPARATE `pytest` invocations (`.agents/testing.md` § Merge gate — N=3,
   three processes, not one run of 3 different tests), all green.
4. Hand-wrote `report.json`/`report.md` myself from the workflow's own
   returned `result` payload (the case rows, findings, branch/PR numbers were
   all present and correct even though the gate/report tail failed — only the
   verdict and the disk write were missing), citing the lead-run gate as the
   verdict source.

## Rule

**Two consecutive gate/report-tail failures on the same batch — of ANY
shape (infra error, cut-off, hard StructuredOutput failure, soft not-run) —
is the threshold to stop resuming and run the gate directly yourself.** The
build-phase work is real and cached; nothing is lost by abandoning the
internal gate. Scope your own gate to the exact node-ids each unit's
brief/AFS names, run N=3 separate invocations, and hand-write the report
from the workflow's `result` object plus your own gate numbers. This mirrors
`workflow_combined_route_unreliable_switch_to_direct_dispatch.md`'s "2
hard-fails = switch approach" threshold, applied to the gate/report tail
specifically rather than the build phase.
