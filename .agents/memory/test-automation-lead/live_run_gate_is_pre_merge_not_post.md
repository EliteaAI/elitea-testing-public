---
name: Live-run gate is pre-merge, not post
description: The orchestrator's independent live-run gate (N=3 GREEN) must run BEFORE `gh pr merge`, never after — reviewer APPROVED is not a substitute even when the reviewer already ran the test once independently
type: feedback
---

## What happened

Working issue #34 (ELITEA-1792), I merged PR #50 immediately after the fresh
reviewer returned `APPROVED` (which included the reviewer's own independent
GREEN 1/1 run). I did not run my own independent live-run gate first — I
treated the reviewer's independent run as satisfying the orchestrator's gate.

Caught only while writing the daily log entry, by noticing every prior
successful case (#27, #28, #30, #31, #33) explicitly cites "My own independent
live-run gate: N/N GREEN" as a distinct step performed AFTER "Reviewer
APPROVED" and BEFORE "Squash-merged PR". #34 skipped straight from review to
merge.

## Why it matters

Per `references/orchestration-playbook.md` (~line 105): "No implementer
self-report is ever a sufficient merge signal. Reviewer `APPROVED` is
necessary but not sufficient. You re-run the spec yourself, in a clean
process, against the live environment, N times. Only then merge."

The gate exists to catch environment drift / parallel-context interaction /
fresh-credential interaction that a single reviewer run can miss. Running it
AFTER merge (as I did to correct #34) still produces useful signal but
defeats the actual purpose: catching a bad merge *before* it lands on
`automation/base`. A reviewer's independent run and the orchestrator's
independent run are not the same control, even though both say "independent"
— they're two different runners at two different pipeline gates.

## Fix / rule going forward

Between "reviewer returned APPROVED" and "gh pr merge", always insert an
explicit step: checkout/pull the PR branch fresh, run the spec N times
(N=3 default per `.agents/testing.md` § merge gate) against the live local
env, confirm all N green, THEN merge. Never conflate the reviewer's run with
this one, no matter how recently the reviewer ran it.
