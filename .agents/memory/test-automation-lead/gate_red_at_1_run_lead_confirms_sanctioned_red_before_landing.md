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

## A third variant: `verdict: "not-run"`, `runs: 0`, outcome `merged-ungated`

When the batch's ONLY new/changed spec is itself the declared red-by-design
test (no other spec needs the N-consecutive-green proof), the gate agent has
**zero eligible specs** for that count — it correctly refuses to report
`green` (nothing proven) or `red` (that would misrepresent a deterministic,
expected, ticketed failure as a batch break) and returns `not-run`, `runs: 0`,
with reasoning in `notes` ("N-consecutive-green covers ZERO eligible specs").
The report writer's generic phrasing — "gate never produced a verdict
(interrupted or dropped) — merged on the trunk but unproven" — makes this
read exactly like an infra stall (see
`workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md`), but
it isn't one: read the gate agent's own `notes`/`failures[]` in the journal
first. If it explicitly reasons through the zero-eligible-specs case and
reports a failure signature matching the declared defect, the gate
substantively succeeded — GATE_SCHEMA's 3-value verdict enum (`green`/`red`/
`not-run`) just has nowhere honest to put "sanctioned-red, N/A for green,
1/3 banked." Treat its one run as run 1 of 3 and finish the count yourself
(same steps 1-4 above); do not resume the workflow (same cached-result trap
as the stall variant) and do not treat `merged-ungated` as broken.

## Seen 2×

#845/ELITEA-2337 — report: `gate.verdict: "red"`, `runs: 1`,
`cases[0].outcome: "blocked"`. Both the covering test and the new
extend-existing test hit OPEN #1203 (React "Maximum update depth exceeded")
on the gate's single sample. Lead ran 3 independent invocations personally:
identical signature all 3 times, step-level Allure check confirmed the new
test's own Steps 1-4 `passed` in every run. Landed via PR #1207, TMS
back-written, closure record posted, card → Ready.

#851/ELITEA-2343 — report: `gate.verdict: "not-run"`, `runs: 0`, outcome
`merged-ungated` (the not-run variant above). The batch's only new spec was
itself the sanctioned-RED test (OPEN #1203, same signature). Gate agent's
notes explicitly reasoned "zero eligible specs for the N-green count," ran
the spec once (18.91s, matched signature). Lead dispatched one more fresh
gate-role agent for 2 more independent runs (18.52s, 17.29s — identical
signature both times, #1203 confirmed still OPEN via `gh issue view`),
reaching 3/3. Opened + merged the trunk→base PR (#1225) personally — the
workflow never does this for a non-green verdict either — TMS back-written,
closure record posted with verified promotability, card → Ready.

See also: batch_report_case_outcome_blocked_can_still_mean_land_it.md ·
merge_gate_extend_existing_sanctioned_red_needs_step_level_check.md ·
merge_gate_operational_traps.md · workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md
