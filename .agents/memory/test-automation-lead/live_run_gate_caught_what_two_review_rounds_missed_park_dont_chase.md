---
name: Live-run gate caught what two review rounds missed — park, don't chase a 3rd round
description: On ELITEA-2094/#297/PR#688, the orchestrator's own mandatory 3x independent live-run gate found 2 non-conforming failures in 2 runs on a PR that 2 fresh reviewer rounds and the implementer's own 9-run local sample had all called stable (sanctioned-RED, closed-set). Correctly did NOT run a 3rd gate cycle to "get past it" or dispatch a 3rd implementer round chasing the same #684 root cause — investigated first (fresh analyst dispatch), then classified per the R2 cap rule as Underlying product change and parked.
type: feedback
---

## What happened

PR #688 (ELITEA-2094, chat participants panel) shipped intentionally RED — sanctioned-RED
per `.agents/testing.md` § Merge gate, against 3 enumerated known defects (#687, #689,
#684). Two full reviewer rounds (fresh `qa-engineer` sessions) both did real, substantive
adversarial work and both converged on APPROVED-with-trivial-fix. The implementer's own
local sample was 9/9 identical sanctioned signature.

Then my own mandatory independent gate (3 separate `pytest` invocations, required before
merge, never substituted by implementer-local or reviewer-local runs) hit:
- **Gate run 1**: a Step-9 nav failure that the test's OWN new signature-verification
  logic (added specifically to prevent this) explicitly flagged: "does NOT match known
  #684's signature ... investigate as a NEW failure, not #684."
- **Gate run 2**: a completely different, previously undocumented, unguarded hard
  failure ("agents badge should persist after sending the first message").

Two non-conforming failures in two runs. Per the merge gate's own text: "Anything else
red — flaky, multi-cause, no linked defect — blocks."

## What I did NOT do (the tempting wrong moves)

- Did NOT run a 3rd gate invocation hoping it would come back clean and let me "call it
  3/3 with 2 flakes excluded" — the merge gate's isolated-flake-restarts-the-count
  allowance (`isolated_flake_restarts_merge_gate_count.md`) is for a SINGLE non-reproducing
  timeout in an otherwise-clean sequence, not for 2-for-2 non-conforming failures that the
  test's own instrumentation is telling you don't match the known set.
- Did NOT dispatch the implementer again to "widen the soft-assert net" on the spot — that
  would have been an R3 round chasing the SAME #684 root cause (R1: wrote the test +
  discovered #684/#687; R2: added Send-time signature verification + split off #689).
  The R2 cap rule exists exactly for this instinct: "the instinct to 'one more round' is
  exactly what the cap exists to override."
- Did NOT just trust my own read of 2 junit.xml dumps and freelance a root-cause guess —
  dispatched a fresh `qa-engineer` (analyst-style, diagnosis only, no code edits) to
  actually reproduce and investigate before deciding anything.

## What the investigation found

The #684 mixup fires at participant-*switch* time (Step 3), not Send-time as originally
scoped — a stale `version_id` gets copied into `entity_settings` on switch, and depending
on a race it can crash immediately, crash later at Send, silently misclassify a badge
into the wrong section (the likely mechanism for both of my gate's new symptoms), or
resolve with zero visible symptom. The investigator's own words: "a well-evidenced
hypothesis, not a confirmed trace." Test-data pollution was checked and ruled out as an
alternative explanation (own runs left zero new orphans; the one 403-on-delete seen
earlier didn't reproduce and traced to a pre-existing, session-predating orphan cluster).

## Decision and why

Classified as **Underlying product change** per the R2 cap rule and parked — did not
dispatch a 3rd implementer round to widen detection around a still-unconfirmed
hypothesis. Posted full reasoning + evidence to the PR and the tracking issue, moved the
board card to `Blocked`, `Waiting on #684`. PR stays open, unmerged. Testids already
safely on `automation/testids` regardless of the block (that part of Ready's bar doesn't
depend on the test PR merging).

## The reusable lesson

**The independent live-run gate is not a formality to rubber-stamp once 2 review rounds
and an implementer's local sample all say stable.** It is specifically positioned to
catch environment-drift / parallel-context / fresh-run flakes that in-session
implementer/reviewer runs structurally can't see (they're all running in the same warm
session against state the earlier steps already primed). On a case whose "sanctioned-RED"
story rests on an admittedly-not-fully-root-caused race condition, expect the gate to be
the place where the story's remaining gaps actually surface — budget for it, don't treat
a clean review as predicting a clean gate.

When the gate DOES surface something outside the enumerated set: investigate before
classifying, don't guess and don't paper over with more gate cycles. And when the honest
classification is "this needs the product side to actually fix or fully diagnose the root
cause" — park. Don't let "the PR is otherwise so well-reviewed" pressure a 3rd
engineering round chasing a moving target.
