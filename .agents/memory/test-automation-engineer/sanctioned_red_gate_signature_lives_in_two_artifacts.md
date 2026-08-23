---
name: A sanctioned-RED gate signature must be swept across BOTH the AFS and the test docstring
description: Amending only the AFS Test Step leaves the § Known Defects bullet and the module docstring steering the lead's gate classification
type: feedback
aliases: [gate signature drift, sanctioned red, soft failure count, ExceptionGroup count]
tags: [area/handoff, type/drift]
created: 2026-08-23
updated: 2026-08-23
---

## What it costs

`.agents/testing.md` § Merge gate makes the stated signature load-bearing: the
lead classifies the 3x gate run against it. Understate the count and a correct
spec gets blocked; overstate it and a genuinely NEW second cause gets waved
through as "the known defect". The count is the only thing separating those.

## Where the claim hides (ELITEA-1810, PR #1678 fix-round-1)

The analyst wrote "exactly one soft failure". Implementation needed **two**
`expect.soft()` calls for that one cause (measure text *and* value), so the
real signature is a pytest `ExceptionGroup` of **2** sub-exceptions. The AFS's
*Test Step 13* was amended — and two other copies were not:

- the AFS's own **§ Known Defects** bullet, and
- the spec's **module docstring**, which is what a gate operator reads first.

## The sweep, at handoff

```bash
grep -rn "soft failure\|ExceptionGroup\|expect\.soft" <afs> <spec>
grep -c "expect\.soft(" <spec>          # ground truth, must match every prose claim
```

Then state the signature as the **count of sub-exceptions**, not "one soft
failure", and say what a different count means ("investigate, do not classify
as the known defect").

`automation/tests/unit/test_artifacts_bucket_retention_gate_signature_consistency.py`
now enforces exactly this for ELITEA-1810: it AST-counts `expect.soft()` and
asserts both artifacts state that number and no longer carry the retracted
claim un-negated. Same shape as
`tests/unit/test_artifacts_tree_expand_collapse_docstring_mechanism.py` — the
project's established way to pin a docstring claim to code.
