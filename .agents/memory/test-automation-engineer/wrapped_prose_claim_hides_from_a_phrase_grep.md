---
name: A line-wrapped prose claim hides from a phrase grep
description: Sweeping a docstring for a retracted claim needs a fragment grep plus a whitespace-collapsed pass — the phrase grep misses wrapped copies
type: feedback
aliases: [wrapped docstring claim, phrase grep misses wrap, collapse whitespace grep, docstring sweep]
tags: [area/review, type/technique]
created: 2026-08-27
updated: 2026-08-27
---

## What happened

ELITEA-2215 fix round 2 removed the undated absolute claim *"#1127 has not
fired on that trigger"* from `GATE_EXCLUDED_REASON`. Fix round 3 found the
same sentence still alive in a sibling class's docstring 470 lines away. It
survived because the wrap fell between `has not` and `fired`, so
`grep "has not fired"` returned nothing — the round was closed on a green
grep that could not have found it.

## The technique

When retracting or scoping a claim that appears as **prose** (docstrings,
markdown, comments), one grep is not a sweep. Run two passes:

```bash
# 1. distinctive FRAGMENTS, plus the end-of-line anchor for the wrap point
grep -nE "has not[[:space:]]*$|has not fired|never fired|does not fire" FILE
# 2. whitespace-collapsed whole-file pass — this is the one that finds wraps
tr '\n' ' ' < FILE | tr -s ' ' | grep -oE ".{90}(has not fired|never fired).{90}"
```

Pass 2 is the load-bearing one; pass 1 alone is what let the claim through.
Same reasoning applies to any multi-word invariant in prose: a testid name
split across a wrap, a ticket reference, a policy sentence.

## The paired verification

For a docstring-only fix, "I changed no behaviour" is checkable, not
assertable: parse both revisions, strip every module/class/function
docstring, and diff the ASTs. Identical dumps = provably prose-only.

Related: [[gate_marker_absolute_claim_refuted_by_its_own_module]]
