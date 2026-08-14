---
name: Implementer direct-trunk-commit recurrence (3rd occurrence, ELITEA-2257)
description: Implementer self-flagged committing straight onto the batch trunk instead of cutting a feature branch first — 3rd known recurrence, self-caught before push each time
type: feedback
---

## What happened

During the ELITEA-2257 batch-build run (2026-08-05), the implementer's own
returned findings included a self-flagged process slip: it committed the
test implementation directly onto the batch trunk
(`tests/batch-elitea-2257-notification-text-content`) instead of cutting its
feature branch (`tests/2257-notification-text-content-renders-correctly`)
first. It caught and corrected this **before pushing** the trunk, so no bad
state landed — the PR (#1164) still ended up correctly shaped (case branch →
trunk).

Per the implementer's own memory
(`.agents/memory/test-automation-engineer/verify_feature_branch_before_first_commit.md`),
this is the **3rd recorded recurrence** of the same slip across different
sessions/cases.

## Why it hasn't caused damage (so far)

The batch-build workflow's "Who may run at once" discipline means the
implementer is the only writer on the tree at that point, and the merge step
(a separate dispatch) reads the actual git state rather than trusting a
self-report — so a self-caught-before-push slip is invisible downstream. The
gate and reviewer never saw a malformed branch structure in any of the three
occurrences.

## Why it's worth watching, not yet acting on

Each occurrence was self-caught. There is no confirmed instance where this
recurrence actually corrupted a delivery. Per the "never trust a self-report
for a fact you can observe" rule, the real signal is what merge-back /
gate agents report about branch shape, not what the implementer says it did —
worth spot-checking on a future case (`git log <base>..<branch>` before
trusting a "built" status) rather than pre-emptively reinforcing the
implementer's dispatch prompt.

## If it recurs a 4th time

Consider: (a) adding an explicit pre-flight check to the implementer's
dispatch template ("confirm `git branch --show-current` is your feature
branch, not the trunk, before your first commit"), or (b) a mechanical check
in the merge-back step that verifies the case's commits are NOT already
present in the trunk's own history before it started (i.e. the case branch
diverged from the trunk cleanly). Not needed yet at 3 occurrences with zero
delivered damage.
