---
name: Plural wording in case text signals real extend, not duplicate
description: A case whose steps look near-identical to an already-built test can still be genuine new coverage if its wording is aggregate/plural where the existing test only checked one item
type: feedback
---

## The situation

ELITEA-2154 ("Pinned Folder Retains All Conversations After Pinning") landed on
the same batch trunk right after ELITEA-2152 ("Pin a Folder via Pin on Top
Option") had already been built and merged to the trunk. ELITEA-2152's own
Step 5 already asserts "the folder still shows all its conversations when
expanded" — on its face, the same claim ELITEA-2154 makes.

The trap: concluding "already covered, skip" (or worse, silently not filing
any AFS) from the step-text overlap alone.

## Why it wasn't a duplicate

ELITEA-2152's test seeds exactly **ONE** conversation (`conv_in_folder`) and
checks it survives. ELITEA-2154's own case wording is explicit and different
in scope: Step 1 says "Expand a folder with **multiple** conversations and
**note conversation names**"; Step 4 says "Verify **no conversations were
lost**" (plural). A single-conversation check cannot distinguish "all N
conversations survive" from "at least one survives" — a hypothetical bug that
truncates a folder's list to its first item after a remount (a real risk here,
given the pin action is a confirmed remount) would pass ELITEA-2152's existing
assertion and fail ELITEA-2154's.

## The rule to apply

Before calling `already-covered` (or silently treating a new case as
redundant) against an existing test that "looks the same":

1. Diff the CARDINALITY the case text implies (singular item vs "multiple" /
   "all" / "no Xs were lost") against what the existing test's fixture data
   actually seeds. `grep` the existing test for how many entities it creates.
2. If the existing test seeds 1 and the new case's wording is plural/aggregate,
   that is real additional coverage — write it as `extend-existing` with a new
   test method (not a duplicate refusal), and name this exact reasoning in the
   AFS's "Why extend-existing, not already-covered" section.
3. Conversely, don't over-apply this — if the existing test's fixture already
   seeds N>1 and asserts all N, a new case with plural wording covering the
   identical mechanism genuinely IS covered.

Also relevant: `already-covered` may only target a spec MERGED to
`origin/automation/base` (never a same-batch trunk-only spec) — so even a
byte-identical case landing right after an unmerged sibling on the same trunk
cannot be `already-covered`; it is `extend-existing` (trunk-targeting allowed)
or a fresh spec.
