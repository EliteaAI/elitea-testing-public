---
name: A null-delta FIX card still owes a full gate — verification IS the delivery
description: With no code to write there is no dispatch and no review; what makes the close honest is your own N×-green run on the env the red came from
type: feedback
aliases: [zero delta delivery, nothing to fix but still gate, verify don't fix, promotion gap closure evidence]
tags: [area/gate, area/triage, type/process]
created: 2026-09-10
updated: 2026-09-10
---

## The temptation

Once the ancestry check proves a promotion gap, the git output alone *looks* like enough:
repair on base, not on main, done. It is not. The git proof shows the repair **exists**; it does
not show the repair **works on the environment that produced the red**.

On #2173 I ran my own 3× gate against `dev.elitea.ai` on the repaired artifact:
`161.36 / 99.44 / 93.28 s, 3/3 passed, reruns.json {} each`. That is what lets the closure record
say *"the repair is green on the very environment the red came from"* instead of *"someone fixed
this, probably."*

## Cheap, and it produced a second finding

The same 3 runs were a datapoint for the #2124 DEV `Page.goto` ledger: #2149 gated this **identical
artifact** ~6 h earlier and lost **4 of 7 attempts** to the hazard; mine lost **0 of 3**. Third
same-spec swing recorded (after #2171, #2172) — enough to settle that an observed hazard rate is a
property of the sampling window, never of the spec.

## No dispatch is correct here

Dispatch is the work *when there is work*. A null delta has no AFS to write, no code to implement,
no diff to review — dispatching an analyst at it produces a report that re-derives the git check.
Lead-owned verification (gate + ancestry + the 3-question hazard check) is the whole delivery.

## The `.env.test` swap recipe worked verbatim

Detached script, `realpath` the symlink, `re.sub` the two lines, **`exit 2` unless
`settings.app_base_url == https://dev.elitea.ai/app`**, `trap … EXIT INT TERM` restoring from a
backup, and echo the resolved URL again after the restore. Reusable at
`/tmp/gate_2173.sh` shape — the `exit 2` guard is the load-bearing half.

Related: [[ancestry_check_is_the_first_move_on_a_fix_card]] · [[a_fix_card_can_have_no_work_in_it]] · [[a_delivered_card_is_not_verified_until_the_env_ran_it]]
