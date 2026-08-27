---
name: A "non-deterministic" defect rate may be an aggregate of deterministic populations — split it by trigger before honouring a park
description: A case parked on a flaky product defect deserves a re-measurement SPLIT BY TRIGGER; #1127's famous 2/5 was create_file 14/14 green + delete_file 9/9 red
type: feedback
aliases: [flaky defect rate, non-deterministic defect, 2 of 5, aggregate rate, sanctioned-RED bar, deterministic 3/3, split the rate, blocked on a flaky bug, re-measure the defect]
tags: [area/merge-gate, type/lesson]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

A recorded defect rate like *"fires 2 of 5 runs"* is a **summary statistic over
whatever runs happened to be pooled**. Before you honour a park that rests on
one, re-measure it and **split the runs by trigger** — the tool called, the
message sent, the entity type, the user. An aggregate rate is only meaningful
if the pooled runs were the same experiment.

This matters specifically because `.agents/testing.md` § Merge gate's
sanctioned-RED exception requires *(a) deterministic — identical failure 3/3*.
A defect that looks probabilistic satisfies **neither** the plain green gate nor
the sanctioned-RED exception, so the case has nowhere to go and gets parked.
Split the population and both halves usually land somewhere legal.

## The worked case — #1127 / ELITEA-2215, parked 3 weeks (2026-08-04 → 08-27)

#1127 ("direct toolkit call narrates the tool call instead of executing it") was
filed with **2/5**, and ELITEA-2215 was downgraded `ready-for-automation` →
`blocked` on exactly that number, with the module marked gate-excluded.

Re-measured across three sessions, every run a separate invocation with
`--reruns 0`, both specs backend-verified via `ArtifactAPI` (never DOM-only):

| Trigger | Spec | Result |
|---|---|---|
| `create_file` — ELITEA-2215's own observable | `TestDirectToolkitCallCompleteFlow` | **14 GREEN / 0 RED** |
| `delete_file` — ELITEA-2210's observable | `TestDirectToolkitCallDeleteFileChip` | **4 RED / 0 GREEN** today, **9/9 RED** lifetime |

Two deterministic populations, pooled into one meaningless average. Consequence:
ELITEA-2215 needed **no sanctioned-RED argument at all** — plain green gate,
delivered the same hour. The sibling moved from "excluded because flaky" to
"excluded because **deterministic** + linked open defect", which is the
*stronger* position.

**The measurement cost ~5 minutes of pytest. The park cost three weeks.** When a
card is parked on a defect rate, re-measuring is the cheapest move available and
it is the FIRST one.

## Two disciplines that keep the re-measurement honest

- **Never claim a per-trigger lifetime rate the record cannot support.** #1127's
  original 5 runs are not attributable per-tool from the ticket text, so the
  right statement is *"did not fire in any of the 14 runs measured on
  <date>"* — dated and window-scoped — never *"has not fired on this trigger"*.
  An undated absolute claim is the shape a reviewer will (correctly) block, and
  it is the shape that survives a phrase grep by wrapping across a line break.
- **The variable is rarely isolated.** Here the two specs also differed in prompt
  forcefulness and setup. Report the discriminator as *best-supported*, not as
  root cause — root cause belongs on the defect ticket, not in an AFS or a gate
  marker.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]] · [[afs_gate_rulings]] · [[blocker_premise_symptom_vs_cause]]
