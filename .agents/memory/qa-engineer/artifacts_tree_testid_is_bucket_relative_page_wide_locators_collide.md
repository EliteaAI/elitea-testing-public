---
name: Artifacts tree testids are bucket-relative, so page-wide tree locators collide
description: artifacts-tree-item-{key} has no bucket qualifier and /artifacts auto-expands a bucket — generic seed keys risk strict-mode violations
type: feedback
aliases: [artifacts tree item testid, strict mode violation tree, auto-selected bucket pollution]
tags: [area/artifacts, type/selector]
created: 2026-08-21
updated: 2026-08-21
---

## The trap

`FileTreeItem.jsx:107` renders ``data-testid={`artifacts-tree-item-${item.key}`}``
where `item.key` is the **bucket-relative** path (`a1/`, `root.txt`) — there is no
bucket qualifier. `BucketsListContent.jsx`'s effect sets
`expandedBuckets[selectedBucketName] = true` for **any** selected bucket, and a
param-less `/artifacts` load auto-selects (and therefore expands) the
alphabetically-first bucket. That foreign bucket's tree stays mounted for the rest
of the test — selecting another bucket does not collapse it (that is ELITEA-1838's
own confirmed behaviour).

Consequence: `page.locator('[data-testid="artifacts-tree-item-root.txt"]')` matches
BOTH buckets' nodes if the auto-selected bucket happens to hold a same-named file →
Playwright strict-mode violation on `click()` / `to_be_visible()` / `to_have_attribute()`,
surfacing as a `broken` test, not an assertion failure. `test-specs/artifacts/_surface.md`
already states the rule ("any page-wide count of tree item elements is polluted by
that auto-selected bucket — always scope per bucket").

## What to require at review

Seeded tree keys must be globally distinctive (carry the case id, e.g. `a1836/`,
`root-1836.txt`) — generic `a1/`, `root.txt`, `f1.txt` are exactly the names a
hand-made scratch bucket holds. Scoping the locator is not currently possible:
no testid marks a bucket's own subtree container.
