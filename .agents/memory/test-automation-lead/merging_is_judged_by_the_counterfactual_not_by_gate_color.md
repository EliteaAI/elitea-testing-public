---
name: Merging is judged by the counterfactual, not by gate colour
description: When a verified fix shares a spec with a pre-existing unrelated flake, holding it makes CI redder — compare against not-merging, not against green
type: feedback
aliases: [hold vs merge, pre-existing flake, counterfactual merge, partial green gate, unrelated red]
tags: [area/merge-gate, type/decision]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

A verified repair comes back with a *partially* green environment gate, and the
honest-looking move is to HOLD: "shipping a ~50%-red spec sends a bad signal."

That reasoning compares the result against **green**. The real comparison is
against **not merging**.

## The test to apply

> If I do NOT merge, what does CI show tomorrow?

On ELITEA-1901/#2083 (2026-09-09) the answer was decisive:

| | model assertion | pre-existing `ERR_ABORTED` |
|---|---|---|
| Don't merge | ❌ deterministic (6/6 repro) | ❌ ~50% |
| Merge | ✅ 0 failures in 8 DEV runs | ❌ ~50% (unchanged) |

Merging **strictly improved** the signal. Holding would have kept a
deterministic red alive in order to avoid a flaky red that exists either way.

## The rule

**A pre-existing defect is never a reason to withhold an unrelated verified
fix.** Holding does not make it go away; it only keeps a second failure cause
alive alongside it.

Two obligations that make this honest rather than convenient:

1. **Prove "pre-existing" with a matched control** — run the *unmodified* base
   against the same environment. 3/3 on pristine `automation/base` is what
   converted "the diff might have broken it" into evidence. Never assert
   pre-existing from reasoning alone.
2. **Card the unrelated defect and record it in canon**, and say in the closure
   record that the environment gate is **owed** to that card. Merging on the
   canonical gate is legitimate; pretending the other gate passed is not.

## Watch for

An IC recommending HOLD is doing its job — it should surface the choice, not
make it. The merge call is the lead's, and the IC's framing ("unsafe on the
signal") is worth taking seriously *and* re-deriving from the counterfactual.

Related: [[project_briefing]]
