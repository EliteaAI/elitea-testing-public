---
name: Closure record must paste the 3x merge-gate output, not narrate it
description: When authoring a closure record as the delivering lead, include a fenced command+output block for all 3 separate pre-merge pytest invocations (or at minimum the 3 pass/fail summary lines with distinct timings) — a one-line narrated summary ("3/3 deterministic GREEN, 3 separate invocations") fails a later control audit even when the gate genuinely ran, because the audit can't independently reproduce this evidence and treats unpasted narration as missing
type: feedback
---

## What happened

Delivered issue #73 (ELITEA-1990, PR #532) myself on 2026-07-15, closure
record included: *"Independent live-run gate (mine, before merge): 3/3
deterministic GREEN, 3 separate `pytest` invocations against
localhost:5173, `-p no:cacheprovider`."* A separate control-audit session
(same role, fresh session, auditing my own prior delivery per the factory's
independent-audit pattern) checked every retrievable location — PR
comments, issue comments, PR checks, timeline — for a fenced command+output
block backing that claim. Found none. The only pasted pytest output on the
PR was the *reviewer's* independent run (item 6, a different gate). Audit
verdict: FAIL on item 5, even though the gate almost certainly did run
(the closure record is otherwise meticulous and this delivery had no other
red flags).

## Why it matters

This is the same failure mode `merge_gate_narration_needs_artifact_too.md`
documents from auditing *other* deliveries (#60/#292) — but this is the
first time it recurred on my *own* delivery, caught by my own later audit
session. The control-audit protocol (`.agents/role-overrides.md` § the
evidence principle) is explicit: the 3x merge-gate run is NOT cheaply
reproducible by an auditor (needs live local UI, minutes per card), so the
delivery's own pasted evidence is the ONLY proof and stays REQUIRED —
narration is not a substitute no matter how specific or plausible-sounding.

## Rule going forward

When writing a closure record as the delivering lead (not just when
auditing one), paste the actual gate evidence, not a summary of it:
- Either a fenced block with all 3 `pytest ... -v -p no:cacheprovider`
  invocations' final lines (e.g. `1 passed in 11.42s` ×3 with distinct
  timings — proof they're 3 separate processes, not one claim repeated), or
- At minimum, 3 distinct timing/timestamp data points that couldn't have
  been fabricated from a single run.

Treat this as part of the closure-record template's merge-gate row, on par
with the promotability row's requirement for pasted verification output
(`templated_promotability_row_can_mask_wrong_literal_testid.md` already
established that principle for promotability — extend the same discipline
to the merge gate).
