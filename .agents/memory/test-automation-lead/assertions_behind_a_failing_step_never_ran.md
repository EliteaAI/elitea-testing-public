---
name: An assertion downstream of a reliably-failing step has never executed
description: When unparking a blocked case, assume every assertion behind the failing step is unverified — it passed review and gate without ever running
type: feedback
aliases: [unreachable assertion, blocked case rework, assertion order, dead assertion, unparking a case]
tags: [area/review, area/merge-gate, type/convention]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

ELITEA-2213 (#416) was merged, reviewed and gated in 2026-08 while its **primary
observable never executed once**. The backend ground-truth check ("the seeded
file is still in the bucket") sat downstream of a `wait_for_message_content_stable()`
that reliably timed out on an open product defect. The test failed at the wait,
so everything after it was dead code — including a *factually wrong* assertion
(`answer_tool_chip.to_have_count(0)`, asserting a state the product cannot enter)
that survived a full pipeline pass precisely because nothing ever evaluated it.

A gate cannot catch this. The spec was red for a sanctioned reason, the signature
was stable, and the unreached assertions contributed nothing to it.

## The orchestrator move

**When unparking a case blocked on a product defect, treat every assertion
downstream of the failing step as UNVERIFIED**, regardless of how many gates the
spec has passed. Put it in the analyst's dispatch as an explicit question: *is
this assertion reachable, and is it correct?* On #416 that question produced two
of the three findings.

The mirror hazard, same axis: an absence assertion evaluated **too early** passes
vacuously. `to_have_count(0)` returns the instant the count is already 0, so
placed before a transient state settles it asserts nothing — and silently drops a
defect out of a sanctioned-RED closed set, shrinking the signature with no
symptom. Order is an assertion-strength property in **both** directions.

**Confirmed twice, back to back.** ELITEA-2214 (#417) carried the identical shape
and was reworked the next session: same stranded backend ground-truth check, same
never-executed primary observable, same clean review-and-gate history. Two of two
cases in this family shipped this way — so on a blocked-case rework this is the
DEFAULT expectation, not a hypothesis worth a hedge. Both reworks also had to move
absence assertions LATER for the vacuous-pass reason below.

Canon card raised: elitea-testing-public#1841.

Related: [[sanctioned_red_closed_set_variant]] · [[sanctioned_red_tms_backwrite_shape]] · [[merge_gate_extend_existing_sanctioned_red_needs_step_level_check]]
