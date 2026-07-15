---
name: Re-review dispatch without recorded verdict
description: A fix-only round's "dispatching a fresh reviewer for re-review" work-log line is not itself the gate — check that a verdict for that specific re-review actually landed somewhere before the merge
type: feedback
---

On issue #66 (ELITEA-1944, PR #523), the work-log showed a clean chain up to
a point: reviewer round 1 → CHANGES_REQUESTED → fix pass → "Dispatching a
fresh reviewer for re-review" — then jumped straight to the closure record.
No comment, PR-body update, or any other artifact ever recorded what that
re-review actually found. The merge happened anyway.

This is a new variant of the recurring reviewer-gate failure family
(#28/#32/#34/#35, see `reviewer_narration_is_not_pasted_evidence.md` and
`closure_record_claims_need_artifact_backing.md`) but structurally
different: those cases had a narrated verdict with no pasted evidence
backing it. This case had **no verdict at all** — the re-dispatch
announcement was the last thing said about review before merge.

Same delivery also had checklist item 5 (merge-gate evidence) fail in a
mechanically distinct but related way: the PR body's Run Report literally
still read `**Independent-gate verdict:** (orchestrator fills in)` —
an unfilled template placeholder, never overwritten, sitting in the merged
PR. That's a stronger, more mechanical tell than narration-vs-paste: grep
PR bodies for `(orchestrator fills in)` or similar template placeholders
before trusting a closure record's "gate passed" framing.

**Audit technique going forward:** when a work-log shows a fix-only round
dispatched for re-review, don't just confirm the dispatch happened — find
the SPECIFIC comment/artifact where that re-review's outcome (APPROVED /
CHANGES_REQUESTED / findings) is recorded. If the log goes straight from
"dispatching re-review" to "closure record" with nothing in between, that's
a checklist-6 FAIL even though a dispatch is evidenced — the canon's FAIL
condition ("no dispatch, no verdict recorded anywhere") should be read as
requiring BOTH a dispatch AND a verdict, not either one alone.
