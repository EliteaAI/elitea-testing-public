---
name: Distinguishing a deliberate product change from a regression — and why it decides the repair
description: The four tells that a red test is chasing an intentional change, and why guessing wrong ships either permanent false red or reverse-masking
type: feedback
aliases: [product change vs bug, intentional UI change, red test classification, reverse masking, is this a regression]
tags: [area/triage, area/test-repair, type/diagnosis]
created: 2026-08-27
updated: 2026-08-27
---

## Why the distinction is load-bearing

A `[Fix][…]` card offers "product bug" and "test drift" as peers, but they lead to
**opposite** deliveries, and both wrong answers are expensive:

- Calling a deliberate change a **bug** → soft-assert + linked defect → **permanent false
  red** in CI against behavior that is working as designed, and a defect nobody will fix.
- Calling a regression **drift** → the test is rewritten to assert the broken behavior →
  **reverse-masking**: the suite now certifies the defect and can never catch it.

## The four tells (ELITEA-1891 / EliteaUI PR #857 was 4/4 "deliberate")

1. **Targeted, not incidental.** A precise 4-line deletion of one comparator tier — not a
   refactor that happened to break something.
2. **An authored comment states the new intent.** *"Default version stays in its
   chronological position — not pinned to top."* Per `.agents/role-overrides.md`
   § interaction-discovery ladder, **the source is this project's decisive authority on
   intended behavior** — this is canon, not an inference.
3. **Inside a scoped feature PR** with a matching ticket (EL-6302, *"Improve Version
   Selector"*), not a drive-by.
4. **The affordance was preserved, deliberately.** The pin icon was *kept* and given a
   testid, tooltip and `aria-label` — i.e. "which one is default" is still communicated,
   by a different means. A regression deletes; a redesign relocates.

## Do not park this as a question

The instinct is "only a product owner can confirm intent" → file a `question` → park. But
tell 2 makes it answerable from canon, so parking is a **false blocker** on a card whose
repair is fully determined. Instead: proceed, state the reasoning explicitly in the PR and
the closure record, and put the *"was this intended?"* question in the case-drift
clarification issue as an explicitly **non-blocking** section. A human can overturn it in
one comment, and the failure mode is diagnostic — if they say it was unintended, the test
goes red again and lands another Fix card.

## Then file BOTH artifacts

A deliberate change usually means the TMS case text is now wrong. That is a **case-drift
clarification**, and per § Bug filing a clarification for a *different step* of a case that
already has one is a **sibling**, not a duplicate — file it, cross-link both ways. Collapsing
siblings destroys coverage.

Related: [[deployed_only_failure_claims_are_hypotheses]], [[promoted_test_fixes_branch_from_main]], [[a_green_gate_does_not_prove_an_assertion_is_sound]]
