---
name: Derive an expected set from the product's composition function, not from a live snapshot of it
description: When a list mixes frontend constants with backend data, model the function that assembles it — a set derived from "what the API returned today" carries the snapshot's accidents into the assertion.
type: feedback
aliases: [expected set, oracle derivation, buildAllCategories, mixed constant and data list, hardcoded count drift]
tags: [area/assertions, type/pattern]
created: 2026-09-09
updated: 2026-09-09
---

## The situation

A rendered list is often assembled from two sources with different change
rates — frontend constants (move when the UI team ships a feature) and backend
data (moves when an admin edits content). A single hardcoded count pins both,
so a routine data change and a deliberate feature change become
indistinguishable, and the failure message names neither.

Worked case: the Catalog filter rail (ELITEA-2367 / card #2079). `chip_count == 11`
went red on a legitimate third Featured chip. Bumping it to 12 would have re-armed
the identical tripwire on the data half.

## The move

Read the response the page itself fetched (passively — `page.expect_response`,
never `page.route`) and derive the expectation. But derive it from the product's
**composition function**, not from what the response happened to contain today:

```
buildAllCategories(names) = [TRENDING, MY_LIKED, NEW, ...sorted(names - {OTHER}), OTHER]
⇒ expected = set(FEATURED) | set(api_names) | {OTHER}
```

`| {OTHER}` looks redundant — live, the API *does* return "Other". It is not:
the helper re-appends "Other" whether or not the backend lists it, so a backend
that stopped listing it would produce a **false red** on a set derived from the
snapshot. Reading the helper (30 seconds in the UI source) is what surfaces the
difference; the live payload alone cannot tell you which of its entries are
load-bearing.

## The generalisation

Ask of every derived expectation: *if the source data changed shape, would my
derivation still describe the product, or only today's data?* Assert the
**invariant** the product implements, not the sample it produced. Pair it with
a visibility assertion — `to_have_count` matches attached-but-hidden elements,
so a count+membership check alone passes on a collapsed container.
