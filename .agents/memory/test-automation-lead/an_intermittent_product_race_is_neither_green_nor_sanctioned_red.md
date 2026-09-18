---
name: An intermittent product race is neither 3/3 green nor sanctioned-RED — land on the counterfactual, declare it, and label the signature so a new cause cannot hide
description: ELITEA-2056/#2367 — a soft-asserted, filed, single-cause product race that fires ~15-60% of cold opens fits no merge-gate rule; the repair still lands if main's alternative is worse, but the disposition is a declared improvisation (#2369), and the failure messages must make "member fired" vs "new cause" mechanically distinguishable
type: feedback
aliases: [intermittent sanctioned red, bursty product bug gate, mermaid bomb, mermaid.run vs render race, two-message signature, conditional known-defect attribution, DiagramOutput race, Syntax error in text]
tags: [area/merge-gate, area/triage, type/lesson]
created: 2026-09-18
updated: 2026-09-18
---

## The shape (#2366 → #2367, PR #2368)

DEV Stable red 3/3 at Step 9 of `test_pipeline_information_section`: modal opens, Mermaid renders its
**"Syntax error in text / mermaid version 11.17.2"** bomb, so `.node` never attaches. The card said "Show
link not found" — wrong step; the CI screenshot said everything in 30 s (read it FIRST, #2074 rule).

Root cause is a product race, not text: `DiagramOutput.jsx` runs an explicit `m.render()` AND
`mermaid.run()` (`initialize({startOnLoad:true}); contentLoaded()`) on the same element. Whichever lands
last wins; on a cold page `run()` does, wipes the good SVG, throws on its own temp-div markup, leaves the
bomb. Diagram text is valid on 11.16.0 and 11.17.2. **A Mermaid bomb with NO console error and NO red error
box = this race, not a bad diagram** — diagnose with a MutationObserver on the container; the bomb also
flashes ~1 ms in the good ordering, so never fast-fail on its presence, only assert its absence AFTER a node
is visible.

## Why it fits no rule, and what I did

Merge gate admits 3/3 green or deterministic 3/3 identical sanctioned-RED; "flaky … blocks". This defect
is real, single-cause, filed, OPEN, soft-asserted — and intermittent (6/40 implementer loop; my DEV gate
1 of 3; localhost 2 of 3 minutes later; bursty, not version-specific). The gate is green-or-red by luck.

Landed it anyway, on the **counterfactual**: `main` otherwise keeps a WORSE version of the same intermittent
red — raw `TimeoutError` naming the wrong subsystem, and `--only-rerun TimeoutError` letting `--reruns=2`
swallow most occurrences (a hidden product bug). The repair changes nothing about WHAT is verified (strictly
stronger: adds bomb-absence), only how the red surfaces. Recorded the gate honestly (2 green + 1 red on the
signature), declared it, filed the canon card (#2369, limit 2 of the protocol). Card → Ready, not Blocked:
"red-for-a-real-product-bug with a filed, linked ticket" is the definition of done.

## The label rule the reviewer caught — copy it

Two soft asserts (`.node` first visible; `.error-icon` count 0) = the signature. The FIRST message must NOT
attribute to the bug unconditionally: an empty container with no bomb (chunk never loaded, component threw
before either render) fires the node message ALONE and is a NEW cause. Message text: *"This is known defect
#N ONLY if the '.error-icon count 0' assertion below ALSO failed. If this failed ALONE — it is a NEW cause:
do not file under #N."* Otherwise the #2366 misattribution class is rebuilt in the other direction, and once
#N closes the message names a closed issue for an unrelated failure.

## Costs to expect

Every lost race is now a visible nightly red naming #2367 → `[FIX]` re-filings that are duplicates of the bug
(#2064 pattern), until the product fix ships. That is the honest price; a `flaky(reruns=N)` on a product race
is masking.

Related: [[merging_is_judged_by_the_counterfactual_not_by_gate_color]] ·
[[sanctioned_red_closed_set_variant]] · [[sanctioned_red_tms_backwrite_shape]] ·
[[fix_card_body_can_carry_a_policy_violating_instruction]]
