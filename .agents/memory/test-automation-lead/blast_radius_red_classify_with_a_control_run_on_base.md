---
name: Classify a blast-radius red with a CONTROL run on the base branch, not by reading it
description: Re-run the failing specs on the base ref with no batch code; identical failures prove pre-existing, and that is the only evidence that separates regression from noise
type: feedback
aliases: [control run, blast radius regression, pre-existing red, is this my fault]
tags: [area/merge-gate, type/technique]
created: 2026-08-24
updated: 2026-08-24
---

## The move

When the blast-radius run comes back red, **do not classify it from the failure
text.** Check the base ref out and run *those exact specs* with none of the
batch's code:

```bash
git checkout <base>                     # e.g. automation/base
HEADLESS=true ../.venv/bin/pytest <the failing specs> -v -p no:cacheprovider
```

- **Identical failures** ⇒ pre-existing. Not your batch. Land it, and say so in
  the PR with both refs and both results.
- **Green on base, red on the trunk** ⇒ a real regression your batch caused.
  That blocks.

This is cheap (one invocation) and it is the *only* thing that turns "these
reds look unrelated" into a defensible claim. Reading the stack trace and
deciding it looks unconnected is a guess wearing a verdict's clothes.

## Why it matters both ways

It protects against **both** errors, which is why it beats judgement:

- It stops a false alarm — #1394 wave-01 showed 3 reds in 11 pre-existing
  credential specs; the control on `automation/base` (`b1be8d208`) reproduced
  all three byte-identically, so the batch merged on evidence rather than on a
  hunch.
- It stops a false clean bill — two of those three were known sanctioned-REDs
  (#551, #1004), which makes it *very* easy to wave the whole set through. The
  third had no linked defect and no soft-assert: an uncontrolled red sitting on
  the base branch that nobody had noticed (filed as #1703). Without the control
  run its signature would have been absorbed into "the known ones".

## Then write both numbers down

The PR body and the closure record carry the control's ref and result, not just
the claim. "No regression" without the control ref is unverifiable six months
later — the same standard as the promotability row.

Related: [[blast_radius_red_does_not_block_gate_verdict]] · [[merge_gate_operational_traps]] · [[evidence_must_be_pasted_artifact]]
