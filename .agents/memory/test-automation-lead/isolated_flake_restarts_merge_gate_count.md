---
name: Merge-gate isolated flake restarts the count
description: A single non-reproducing timeout during the independent 3-consecutive-run merge gate is not a defect and not a block — treat it as infrastructure, discard it from the count, and start the 3-in-a-row sequence fresh from the next clean run
type: feedback
---

## What happened (ELITEA-1739, issue #29)

Running the mandatory independent merge gate (3 SEPARATE consecutive
`pytest` invocations, zero failures between them, per `.agents/testing.md`
§ Merge gate) for PR #208: run 1 GREEN, run 2 GREEN, run 3 **RED** —
`playwright._impl._errors.TimeoutError` on "Navigate to create skill" during
setup. The local dev server was still healthy (curl 200 immediately after).
Re-ran once immediately: GREEN. Re-ran twice more back-to-back: both GREEN.

## What I did

Did not treat the single red as a merge-gate failure (it wasn't
deterministic — the gate's own sanctioned-RED exception requires
"identical failure 3/3, single-cause, tied to an OPEN defect" — a lone
unreproduced timeout satisfies none of that). Did not treat it as proof of
flakiness requiring an implementer fix either, since a single non-reproducing
timeout with a healthy server around it has no diagnosable root cause to
hand back. Instead: discarded that run, and restarted counting from the next
clean run — needed 3 fresh consecutive greens after the flake, not "2 good +
1 bad + 1 good = close enough."

## The rule

The merge gate's "3 SEPARATE consecutive invocations, zero failures between
them" is a strict consecutive-run requirement, not a pass-rate threshold. A
single isolated timeout/crash with no reproduction on immediate retry and a
verified-healthy environment around it:
- is NOT a merge block (it's not deterministic, so it doesn't qualify as a
  real regression or a sanctioned-RED known defect)
- does NOT get "counted through" (2 green + 1 red + 1 green is not "the
  gate," even though the raw ratio looks fine)
- DOES require restarting the 3-in-a-row count from the next clean run

Record it explicitly in the closure record as an infrastructure flake that
did not reproduce, so a future reader isn't puzzled by a run count that
implies more than 3 invocations happened. If the same failure DOES
reproduce on retry, that's a different case entirely — classify and route
per the normal Debug-phase table (infrastructure fix / isolated defect /
blocking defect), don't keep re-rolling hoping for green.
