---
name: An AFS's own Automation Hints can authorize a masking pattern — build it hard anyway
description: ELITEA-2185/2187 shipped `if body == pre_body: logger.warning(...)` for the case's own headline claim ("Regenerate generates a NEW response") because the AFS's Automation Hints explicitly said "keep it soft/logged, not a hard assert" to dodge a theoretical LLM-coincidence false failure. Reviewer flagged it as No-Defect-Masking regardless — a no-op Regenerate returning cached text would pass green forever.
type: feedback
---

## The trap

An AFS's Coverage-Map/Axis-2/Automation-Hints text can *itself* specify a
weakened assertion (a `logger.warning` instead of `assert`, `expect.soft()`
with no linked ticket, a demoted check) with plausible-sounding reasoning —
here: "an LLM could coincidentally repeat text, so don't hard-fail on it."
Building exactly what the AFS says feels compliant. It isn't: the No Defect
Masking Rule (`test-automation-implementation` skill § Hard Rules → 2) binds
regardless of what the AFS authorizes — an AFS is a work order for *what* to
assert, not a waiver of *how honestly* to assert it (same principle as
`afs_is_a_work_order_not_gospel.md`, one layer over: that entry is about
wrong AFS *facts*, this one is about wrong AFS *assertion-strength policy*).

## The tell

If a "soft/logged, not hard-asserted" instruction sits on the case's own
**headline claim** (the thing the case title says: "Clicking Regenerate
Generates a NEW Response"), that is not an edge-case hedge — it is the
central invariant with its teeth pulled. A regression that makes the feature
literally a no-op (returns cached/identical content) sails through green
forever, silently, because the only check that could catch it is a log line.

## The fix, and why it's safe to make hard

Convert to a real `assert`. The "rare LLM coincidence" concern is a real but
*acceptable* flake source — not masking, because it doesn't hide a
deterministic defect signature; a genuine occurrence is signal to
investigate (no-op bug vs. true coincidence), not something to swallow. In
practice (ELITEA-2185/2187, short open-ended greeting prompts "Hi"/"Hi
there"/"Hi again"), 2 consecutive live runs both produced genuinely
differing text — the theoretical risk the AFS hedged against didn't
materialize even once.

## Process note

Fixing this needs an AFS amendment too (Phase 2 amend-in-PR rule) — the
Automation Hints line that authorized the soft pattern has to be corrected
in the same commit, or the next implementer re-reads the AFS and reproduces
the same masking pattern from the same stale instruction.

See also: afs_is_a_work_order_not_gospel.md
