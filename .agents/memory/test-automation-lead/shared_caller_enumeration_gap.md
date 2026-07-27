---
name: Shared-caller enumeration gap
description: Implementers editing a shared page-object/fixture method tend to under-enumerate its callers in the PR description even when the fix itself is correct — grep-verify caller counts yourself before trusting the write-up, and consider a documentation-only CHANGES_REQUESTED fixable by the orchestrator's own gh pr edit rather than a full redispatch
type: feedback
---

## What happened

Issue #28 (ELITEA-1738), PR #43. Implementer fixed two real bugs in shared
page-object methods (`get_skill_id()`, `fill_instructions()`) used by 4
callers each per `grep -rl`. The PR description enumerated only 3 callers
for `fill_instructions()`, silently omitting `test_skill_management.py`.
The fix itself was correct and backward-compatible — the omission was
purely in the regression-evidence write-up, not the code.

A fresh reviewer caught this via the mandatory shared-file regression
protocol check, independently ran the omitted caller (passed), and
returned `CHANGES_REQUESTED` — explicitly noting no code change was
needed, only the PR description.

## Why it matters

This is a recurring shape, not a one-off: an implementer who fixes a
shared method reasons about the callers they *remember exercising*
(directly, or through the specific flow they were testing) rather than
running the grep the skill's own protocol requires. The fix is usually
fine; the enumeration is what's incomplete. Don't assume "enumerated 3 of
4" means "fix is suspect" — verify independently before judging severity.

## What to do differently

1. **Dispatch-time**: when briefing an implementer who will touch a shared
   page-object/fixture, explicitly remind them the caller enumeration in
   the PR description must come from `grep -rl '<method>' automation/tests/`
   directly, not from memory of what they tested — and every hit needs a
   named re-run result, not just the ones tied to the current case.
2. **Merge-gate time**: when the reviewer's only finding is a
   documentation/evidence gap (explicit "no code changes required"), the
   orchestrator can fix it directly via `gh pr edit` (PR metadata is
   in-scope) instead of a full re-dispatch round-trip to the implementer —
   cheaper, and the orchestrator still owns the independent merge-gate
   re-run regardless, so the evidence gets closed out for real either way.
3. Never skip the orchestrator's own independent re-run just because the
   reviewer already ran the omitted caller — the reviewer's run was a
   verification of the reviewer's own finding, not a substitute for the
   standing independent-gate step before merge.
