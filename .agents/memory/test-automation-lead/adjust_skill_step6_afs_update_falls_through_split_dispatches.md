---
name: adjust-automated-test Step 6 (AFS update) falls through split triage/implement dispatches
description: when triage and implementation are two separate dispatches, neither one is told to update the AFS unless you say so explicitly — it's Step 6, between them
type: feedback
---

## What happened (issue #2397, ELITEA-1826, PR #2399, AFS commit 954939e5)

`adjust-automated-test` is six-ish steps: triage (1-2), rail-check (3), locate (4),
re-execute (5), **update the AFS (6)**, update the code (7), gate+PR (8). When I
split this into two dispatches — analyst for Steps 1-2 only, implementer for
Steps 4-7+8 — I wrote both prompts around the code fix and never assigned Step 6
to either one. The implementer's remit is correctly scoped to this-repo-code-only
(doesn't own `test-specs/` conceptually the way the analyst does), and the
analyst's dispatch literally said "do not open a PR, do not touch the TMS case" —
I just forgot to carve out an AFS-update instruction for after the merge. Caught
it myself only by habit-checking the AFS file post-merge, not because anything
flagged the gap.

Fixed cheaply: resumed the SAME analyst agent via `SendMessage` to its `agentId`
(not a fresh dispatch) — it already had the exact commit/root-cause context and
wrote the Adjustment section without re-deriving anything. Landed directly on
`automation/factory` (AFS is analyst-committed-to-trunk, no PR), zero rework.

## Rule going forward

When splitting an `adjust-automated-test` unit into separate triage/implement
dispatches (rather than one agent running the whole skill):
1. Either tell the triage dispatch to ALSO write Step 6 (if you know by then the
   fix won't change its own conclusions — usually true for class A/E), OR
2. explicitly plan a THIRD, short follow-up (resume the triage agent by
   `SendMessage` to its `agentId` after the implementer's PR merges) to close
   Step 6 — don't let "implementer's remit is code-only" quietly mean "nobody
   does the AFS."
Either way, check the AFS file's content (not just its existence) before posting
the closure record — an AFS with no Adjustment section after a drift repair is
the same class of gap as a missing TMS companion PR.
