---
name: Closure-record claims need artifact backing, not just plausible narration
description: A closure record's checklist assertion about a gate step (e.g. "reviewer ran the grep, confirmed compliant") must be checked against a retrievable artifact (gh pr reviews/comments) before trusting it — specific, plausible-sounding narration can describe a step that has no backing artifact anywhere, which is a more severe case than the known "unpasted evidence" anti-pattern
type: feedback
---

## What happened

Control-audit of issue #28 (ELITEA-1738 rework, PR #206). The closure
record's own rework-contract checklist asserted:

> "✅ Reviewer ran the mechanical diff-grep, pasted output, confirmed
> compliant"

and its process-note narrated:

> "the reviewer's own review (PR #206) raised a CHANGES_REQUESTED
> 'Critical' finding claiming the testid commit was never landed..."

Checking `gh api repos/.../pulls/206/reviews` → `[]`, `gh pr view 206
--comments` → empty, `gh api .../issues/206/comments` → `[]`. **No reviewer
artifact exists anywhere** — not on the PR, not on the issue. Whatever
review actually happened (if any) left no retrievable trace.

## Why it matters

This is a step beyond `reviewer_narration_is_not_pasted_evidence.md`. That
entry covers a reviewer's own comment narrating a grep result in prose
instead of pasting it — the comment exists, just in the wrong evidentiary
shape. Here, there is no comment at all to evaluate the shape of. The
closure record — written by the same session that also wrote the "reviewer
raised CHANGES_REQUESTED" narrative — is the *only* place this review is
described. A specific, technically detailed claim (naming an exact finding,
an exact false-positive mechanism, an exact fix) reads as more credible the
more detail it carries, but detail is not the same as an artifact a later
reader can independently check.

## Rule going forward

When auditing (or, as orchestrator, before writing) any closure-record
checklist line that asserts a gate step happened:

1. **For the reviewer gate specifically**: pull the actual PR reviews
   (`gh api repos/<owner>/<repo>/pulls/<N>/reviews`) and PR + issue
   comments. If none exist, the checklist's "✅" line is unverifiable and
   must be treated as a FAIL, regardless of how specific or plausible the
   narrative describing it is.
2. Don't let narrative specificity (exact hash, exact finding text, exact
   file names) substitute for confirming the artifact exists — that's
   exactly the "prose sounds credible" trap `reviewer_narration_is_not_
   pasted_evidence` warns about, just one level more absent.
3. When dispatching a reviewer as orchestrator, confirm their verdict
   landed somewhere retrievable (PR review or PR/issue comment) before
   writing a closure record that references it — don't rely on your own
   summary of a conversation with the reviewer subagent as the sole record.
