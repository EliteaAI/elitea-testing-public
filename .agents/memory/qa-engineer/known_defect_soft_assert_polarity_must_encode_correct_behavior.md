---
name: Known-defect soft-assert polarity must encode CORRECT behavior
description: A known-defect soft assertion that encodes the CURRENT buggy state as "expected" is a hidden green, not sanctioned RED — check the trigger condition's direction, not just its presence
type: feedback
---

## What happened (ELITEA-2445, PR #1382)

The AFS and implementation for ELITEA-2445 wrote a "Known defect: #1381"
soft-assertion whose trigger condition was **backwards**: it declared
`_EXPECTED_TIMELINE_STEP_COUNT_WITH_BLOCKED_NODE_C = 4` (the CURRENT, BUGGY
count — CODE2/Node_C never executes) as the expected value, then appended to
`soft_failures` only when the actual count **deviated** from that buggy
baseline (i.e., only if the defect got FIXED or the fixture shape changed).
Same inversion on the second check (`if any("CODE2" in node_id ...)`  →
fail only if CODE2 *starts* appearing).

Net effect: while defect `#1381` is open, both conditions are false → no
soft failures → `pytest.fail()` never fires → **test is GREEN**. The PR
description even said so explicitly: "currently both structural checks
match the known-defect state, so the test is GREEN." This is a **hidden
green for an open, confirmed, filed product defect** — the opposite of
`.agents/testing.md` § Merge gate's sanctioned-RED exception ("staying red
in CI is the correct signal until the product fix ships") and
`test-automation-implementation` SKILL.md's own precedent ("The test is now
red until the product ships").

Compare the CORRECT existing precedent in the same file
(`test_pipeline_hitl_node_runtime_behavior.py`, defect #1103): the trigger
condition is `if restarted_types: soft_failures.append(...)` — `restarted_types`
is truthy exactly when the DEFECT'S SYMPTOM occurs, so the test is currently
RED (matches the open defect) and will go green automatically once fixed.

## The check to run on every "Known defect" soft-assertion review

Don't just confirm a `soft_failures`/`pytest.fail()` mechanism exists (that's
necessary but NOT sufficient) — trace the **boolean direction**:

> Does the `if` condition that appends to `soft_failures` become TRUE when
> the ACTUAL (currently-buggy) behavior is observed, or when the CORRECT
> (post-fix) behavior would be observed?

- Condition true on the buggy symptom → test is RED now, flips GREEN when
  fixed → compliant sanctioned-RED.
- Condition true only on a DEVIATION from the buggy baseline (i.e., true
  when the bug is fixed or something else changes) → test is GREEN now,
  would go RED when fixed → **inverted, a hidden green, CHANGES_REQUESTED**
  even though the mechanical `soft_failures`/`# Known defect: #N` shape
  looks identical to the compliant pattern.

This is invisible to the mechanical non-testid-handle grep and to a
"does soft_failures exist" skim — it only surfaces by reading which branch
of the `if` actually fires today.
