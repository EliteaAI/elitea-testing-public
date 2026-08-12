---
name: Scoping-only card Ready means deliverable posted, not merged test
description: When a board card's ask is "list/scope remaining work, don't create tasks yet" (not case automation), Ready = requested artifact delivered; the standard merged-test+closure-record checklist doesn't apply
type: feedback
---

## Context

Issue #1297 "[Automate] Ramaining pipeline test cases" asked, verbatim: "Check
the ones which are not yet automated (doesn't have tasks in our board yet, not
covered in our framework). don't create separate tasks per each test case,
track within current task. update this task with the list of test cases
first." No test code, no PR, no case automation was requested — the whole ask
is an inventory/report deliverable, tracked in the one issue.

## The gap this closes

Factory-mode RULES' "Ready requires ALL of: test green, 3x merge gate, PR
merged to automation/base, testids pushed, TMS back-written, closure record
posted" describes the *case-automation* pipeline outcome. It is silent on
scoping/planning/tech-task cards that never touch test code. Applying that
checklist literally to a scoping card would either wrongly block it forever
(no test was ever going to exist) or force a fabricated closure record.

## Resolution used

Treated "Ready" as generically agent-terminal: *the specific artifact this
card actually asked for has been delivered, and the issue is now waiting on a
human decision, not on more agent work.* For #1297 that meant: post the full
cross-checked list as an issue comment, create zero new board cards (per
instruction), then Approved → In Progress → Ready with a comment explicitly
naming this as a scoping deliverable — "no PR, no test-merge gate applies
here" — so nobody mistakes the Ready state for a merged/gated test.

## Also worth carrying forward

TMS `automation_test_id`/`status: ready` alone is not a fully reliable "not
yet automated" signal for this kind of sweep — cross-checking candidate case
titles against actual `automation/tests/ui/<feature>/*.py` test/class names
surfaced ~13/55 cases (of #1297's pipeline sweep) where the live framework
likely already exercises the flow but the TMS record was never back-written.
Flag such overlaps for the analyst to triage `extend-existing`-or-not at
pickup time — don't resolve them yourself from a title-grep pass, and don't
let TMS metadata alone decide "not covered."
