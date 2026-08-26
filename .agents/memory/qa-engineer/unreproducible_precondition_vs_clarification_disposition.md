---
name: Unreproducible literal precondition classified as clarification, not blocked
description: When a case's precondition text can't be literally seeded but the mechanism is proven equivalent, "clarification" is defensible — but it borders the declared-improvisation ceiling on "swapping the subject of the case".
type: feedback
---

Seen in ELITEA-2140 (chat-remaining-w07, PR #1540, reviewed 2026-08-15): the case's stated
precondition ("a conversation that was originally in Older is now inside a folder") could not be
produced on any test-accessible surface — live-verified the API silently ignores caller-supplied
`created_at`/`updated_at`, and no naturally-Older conversation existed in the shared DEV project to
reuse read-only. Rather than blocking, the analyst reasoned from an empirically-confirmed mechanism
(the "Back to the list" PUT unconditionally refreshes `updated_at` regardless of prior recency) to
argue the literal origin is irrelevant to the outcome, and classified the case's precondition line
as a `clarification` while asserting the case's own Pass/Fail criteria in full (today==True AND
older==False) against a freshly-seeded (not literally Older-origin) conversation.

**Review verdict on this pattern:** defensible when (a) the infeasibility is live-verified, not
assumed, (b) the mechanism-equivalence claim is itself empirically proven (network capture), not
just argued from source, and (c) the case's OWN Pass/Fail criteria are asserted in full, nothing
weakened or dropped. This is a "how to reach the precondition" technique choice
(`test-automation-implementation` Phase 2), not a change to *what* is verified.

**Where it borders the ceiling:** `.agents/role-overrides.md` § declared-improvisation protocol
ceiling forbids a declaration that "swaps the subject of the case". A precondition-origin swap is
adjacent to that language even when the outcome assertions are intact — worth flagging to the lead
as a question/spot-check rather than silently approving, especially the FIRST time this shape
appears for a given case family. Don't block solely for this — but don't wave it through unremarked
either.
