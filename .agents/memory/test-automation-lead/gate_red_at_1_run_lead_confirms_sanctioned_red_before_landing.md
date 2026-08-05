---
name: Batch report gate.verdict red at runs=1 — confirm sanctioned-RED yourself, don't park
description: internal gate agent correctly stops at 1/3 on a red and refuses to self-classify; that is honest reporting, not a real blocker — run your own N=3 (+ step-level check if extend-existing) before deciding
type: feedback
---

## Rule

The internal gate agent's contract is "a red anywhere ends the attempt — N
CONSECUTIVE is the contract, not best-of-N." So a batch report can come back
with `gate.verdict: "red"`, `gate.runs: 1`, and `cases[].outcome: "blocked"`
— **and still be a sanctioned-RED case**, not a real blocker. The gate agent
deliberately does NOT self-classify (it says so in its notes: "I am NOT
classifying this failure") — it hands you one data point and stops, correctly,
because it isn't its job to decide the failure is a known defect on n=1.

This is a **different** trap from `batch_report_case_outcome_blocked_can_still_mean_land_it.md`
(that entry: internal gate already reached `gate.verdict: "green"` — 3/3 done
— but the per-case `outcome` string still says "blocked", a pure labeling
bug). Here `gate.verdict: "red"` is an *honest, incomplete* signal — the gate
only sampled once and won't guess further.

**Don't read `runs: 1` + `red` as "the batch is broken, route to
batch-stabilize."** First check whether the failure signature is a
`pytest.fail()`/soft-assert on a linked, OPEN, already-known defect ("all
functional assertions passed, but known-defect soft failure(s) were
recorded: Known defect <issue-url>"). If so:

1. Confirm the defect issue is still OPEN (`gh issue view`).
2. Check out the trunk yourself, run the spec 3 independent times
   (`.agents/testing.md` § Merge gate already assigns this to the lead, not
   exclusively the workflow's internal agent).
3. If this is `extend-existing` onto an already-sanctioned covering test,
   additionally read the Allure step-level JSON in each of the 3 runs and
   confirm every NEW step (not just the pre-existing known-defect step)
   shows `passed` — see `merge_gate_extend_existing_sanctioned_red_needs_step_level_check.md`.
4. 3/3 identical signature + all new steps green ⇒ sanctioned-RED. Land it
   yourself (open + merge the trunk→base PR — the workflow never does this
   either, see `batch_workflow_never_opens_trunk_to_base_pr.md`), back-write
   the TMS, post the closure record naming the exception, card → `Ready`.
5. Any run that DOESN'T match (different cause, or a new step also fails) ⇒
   real red — route to `batch-stabilize` or classify as a genuine defect.

## Seen 1×

#845/ELITEA-2337 — report: `gate.verdict: "red"`, `runs: 1`,
`cases[0].outcome: "blocked"`. Both the covering test and the new
extend-existing test hit OPEN #1203 (React "Maximum update depth exceeded")
on the gate's single sample. Lead ran 3 independent invocations personally:
identical signature all 3 times, step-level Allure check confirmed the new
test's own Steps 1-4 `passed` in every run. Landed via PR #1207, TMS
back-written, closure record posted, card → Ready.

See also: batch_report_case_outcome_blocked_can_still_mean_land_it.md ·
merge_gate_extend_existing_sanctioned_red_needs_step_level_check.md ·
merge_gate_operational_traps.md · workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md
