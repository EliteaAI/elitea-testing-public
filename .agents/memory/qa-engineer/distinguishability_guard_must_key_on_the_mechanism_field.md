---
name: Distinguishability guard must key on the mechanism's field, not the assertion's field
description: When a test picks a value specifically to be distinguishable from a product fallback, guard on the field the product MATCHES on, not only the field the assertion reads.
type: feedback
aliases: [items[1] guard, fallback tautology, oracle index choice, non-tautology guard]
tags: [area/test-design, type/review-lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The pattern

A repair derives an expected value from a live catalog and deliberately picks
`items[1]` because the product's silent fallback produces `items[0]`
(ELITEA-1901 / board #2083, import wizard —
`importWizardModels.helpers.js:4-13`). To keep the choice honest it adds a
guard asserting the chosen entry is distinguishable from `items[0]`.

**Where the guard can be subtly wrong: it must assert the property at the level
the PRODUCT keys on, not only the level the ASSERTION reads.**

- the assertion reads `display_name` (`model-selector-name` renders
  `display_name || name`)
- the carry-through mechanism keys on `name` (`find(m => m.name === model_name)`)

A guard of `chosen.display_name != items[0].display_name` is correct for the
common case, but leaves a hole when two catalog entries share a `name`
(possible with `include_shared=true` — the product itself builds a composite
`id: ${project_id}_${name}`, which is evidence duplicates are anticipated).
Then `items[1].name == items[0].name`, the fallback produces the same stored
value as a working carry-through, and the check stops distinguishing them.

**Rule:** guard on BOTH — the mechanism field (`name`) and the rendered field
(`display_name`). One extra `assert` line; it is the whole reason the index
choice exists.

## Review question to reuse

For any "we pick index N so the fallback can't satisfy us" argument, ask:
*what field does the product compare, and is THAT field guaranteed different?*
A guard on the rendered/asserted field only is a proxy that looks like it
holds the property.

Related: [[import_wizard_silently_rewrites_an_unknown_model]]
