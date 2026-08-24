---
name: A parked case is a hypothesis, not a verdict
description: Re-test an area card's parked/escalated cases when the ground changes — two "do not schedule" parks dissolved on inspection and cost a whole extra wave
type: feedback
aliases: [parked case, escalated do not schedule, deferred case, do-not-schedule, re-examine park, area backlog leftovers]
tags: [area/planning, type/lesson]
created: 2026-08-24
updated: 2026-08-24
---

## The rule

When you pick up an area card whose earlier waves left cases **parked**,
**deferred**, or **escalated — do not schedule**, treat each park as a *claim
made at a past moment* and spend two minutes re-testing it before honouring it.
Parks are written by a lead who had the context of one wave; you have the
context of everything merged since.

**The single highest-value question: has anything merged since the park that
changes the answer?** The `already-covered` / `extend-existing` verdicts are
gated on a target being **merged to base** — so a case that was genuinely
un-automatable during wave N can become a routine `extend-existing` the moment
wave N+1's spec merges. Nothing announces that transition; you have to look.

## What this cost on #1397 (onboarding, 2026-08-24)

Both parks in the wave-1 plan were wrong, in different ways:

- **ELITEA-2240** — parked *"escalated, do not schedule"* because it asserts
  projects appearing *"after approximately 5 minutes"* of real backend
  provisioning. True at the time. But ELITEA-2232 (a later wave) drives the
  provisioning→ready transition, so once **2232 merged to base**, 2240 needed no
  wall-clock wait at all — only three assertions 2232 never made (checkmark
  state, team projects, full sidebar). Sent to analysis to be *judged*, it came
  back **`extend-existing`** and shipped the same day.
- **ELITEA-2233 / 2234** — deferred pending "an area-reclassification decision".
  That decision was about which TMS *folder* the cases belong in. It was never a
  blocker on automating them, and honouring the park would have left two cases
  (one of them **p1**) unautomated on a card that was otherwise complete.

## How to act on it

- **Send it to analysis; do not pre-decide either way.** The analyst executes
  live and returns the verdict. Assuming *"it's still blocked"* and assuming
  *"it's probably fine now"* are the same error.
- **Say in the dispatch what changed** — name the spec that has since merged.
  That is the fact the analyst cannot see from the case text.
- **A park that survives re-testing gets a `question` card**, so the next lead
  inherits a decision under review rather than a folk belief.
- Distinguish the two failure modes: 2240 was a park whose *premise expired*;
  2233/2234 were a park whose premise was *never load-bearing*. The second kind
  is the more common and the cheaper to check.

Same family as the wave-1 lesson on this card — an analyst's `needs-escalation`
premises were checkable in minutes and both were false. Escalations and parks
decay the same way.

Related: [[afs_gate_rulings]] · [[tms_backwrite_discipline]]
