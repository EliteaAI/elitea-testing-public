---
name: New root cause exposed by a correct fix is not an R2-cap violation
description: A review round-2 CHANGES_REQUESTED that surfaces a DIFFERENT failure mode than round 1 (especially one round-1's own correct fix exposed) is progress, not a repeat — don't conflate "review round N" with "N rounds on the same root cause" when applying the R2 cap rule
type: feedback
---

## What happened (#160/ELITEA-1962, PR #617)

Reviewer round 1 found two real issues: a console-listener registered after
`navigate()` (missing the exact page-load window it existed to guard) and a
dead `LocatorDescriptor` field. Implementer fixed both correctly — moved the
listener earlier, dropped the dead field.

Reviewer round 2 (fresh session, independently re-running the spec 4×) came
back `CHANGES_REQUESTED` again — but for something round 1 never mentioned:
the test was now flaky (3/4 fail). Root cause: moving the listener earlier
(round 1's *correct* fix) meant it now legitimately caught console spam from
an already-open, already-tracked product defect (#518, ~60-75% reproduction)
that the test's console-noise filter didn't know about yet. The implementer's
original PR had reported "3/3 clean, no flake" — true at the time, but stale,
because that run predated the listener-timing fix that made the flake
observable.

## The distinction that matters

This is NOT the R2-cap rule's "R1 + R2 both RED on the same root cause, don't
dispatch R3" scenario. The R2 cap targets a pipeline stuck re-treating the
same symptom without progress. Here, round 2 found a *different* bug that
round 1's fix causally exposed — that's the pipeline working as intended
(catching a real gap), not spinning. Fixing it (a third, narrowly-scoped
console filter, verified against a live reproduction of #518) and sending it
back for round 3 was correct; treating it as "round 3, must park per the cap"
would have been wrong — it would park a nearly-done, converging delivery on a
rule meant for genuinely stuck ones.

## Rule going forward

Before applying the R2 cap (or its review-round analog) count how many rounds
addressed the SAME failure signature, not just how many rounds happened.
- Same root cause repeating across rounds (same assertion failing the same
  way, same class of defect) → the cap applies, park/reclassify per the rule.
- A later round's finding is a NEW signature — especially one causally
  triggered by an earlier round's own correct fix (fixing timing exposes a
  race; fixing a leak exposes a downstream consumer's dependency on it) —
  that's forward progress. Keep going through normal fix→re-review rounds;
  don't let round-count alone trigger a park.

Corollary: an implementer's "clean N/N, no flake" self-report can go stale
mid-PR if a later commit in the same PR changes execution order/timing —
don't treat an earlier commit's clean run as still describing the current
HEAD.
