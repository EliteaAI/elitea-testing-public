---
name: Retiring a case (not adjusting) — delete the test, TMS status: deprecated via lead-opened PR
description: a human "delete this test, it's not needed" directive is a retirement, not an adjust-automated-test repair — different mechanics in both repos
type: feedback
---

## What happened (#2446/#2452, ELITEA-2441, 2026-10-16)

A test was CI-red because EL-6922 changed intended product behavior (confirmed
accepted-as-designed, not a regression — closed #2452 "Behavior changed,
current behavior is expected"). The human's follow-up instruction was blunt:
"Resolved, delete original test - it is not more needed." That is a
**retirement**, not a drift repair — `adjust-automated-test`'s preserve-the-nature
rail doesn't apply because there's nothing left to preserve; the whole
case/guarantee is gone, not changed.

## The two-repo mechanic, each with its own rule

1. **This repo (elitea-testing-public):** delete the test file + its AFS
   outright (no new files, this isn't `adjust-automated-test`'s "update
   existing code" either — it's a plain removal PR). Implementer confirms via
   grep that no sibling spec imports from the deleted module, and that every
   page-object/API-client method the deleted test called is still used
   elsewhere (shared methods are the common case — don't let a retirement
   turn into an unplanned method-removal sweep). Normal PR → `automation/factory`,
   normal lead gate-then-merge (though "gate" here means collection + lint
   clean, not 3x pytest green — nothing executes anymore).

2. **TMS repo (onetest-ai-tm-Elitea):** there is no "deleted" case status —
   `.onetest/fields.yml` only allows `status: draft|ready|deprecated`.
   `deprecated` is the retirement state. Clear `execution_type` back to
   `manual` and drop `automation_test_id`/`automation_pr` entirely (don't
   leave them pointing at a file that no longer exists) — this matches the
   project's own pre-existing precedent (`ELITEA-0074`, a `status: deprecated`
   case that carries no automation metadata). Add a short "## Deprecation
   note" body section naming the issues and the reason, so a future reader
   doesn't wonder why status flipped.

   **This is a case-CONTENT change, so it follows the existing
   `adjust_skill_expected_result_change_needs_separate_human_merged_tms_pr`
   rule: the lead opens this PR, never a direct-edit back-write, and NEVER
   merges it** — same rule that already governs an expected-result change,
   because "which bucket does this edit fall in" (content vs. pure metadata)
   is the deciding question, not "is this an adjust or a retirement."

3. Before committing anything to the TMS case file, confirm your working
   clone's own `index.json` wasn't touched by a `build_index` MCP call — that
   tool operates on its own workspace clone (`~/.onetest-workspaces/...`), not
   this sibling checkout, so there's nothing to diff/revert here. (Separately:
   if you ever DO see a local `index.json` diff, `build_index_regression_must_be_reverted_not_carried.md`
   is the check to run before trusting it.)

## Checklist for the next "delete this test" ask

- Confirm it's genuinely a retirement (human said so, or the behavior is
  deliberately gone with no replacement) — not an adjust-class case that
  should instead update the assertion to match new behavior.
- This repo: delete test + AFS, grep-confirm no orphaned refs, confirm shared
  page-object methods untouched, normal PR+merge.
- TMS repo: `status: deprecated`, `execution_type: manual`, drop
  `automation_test_id`/`automation_pr`, add a deprecation note. Lead opens
  the PR, never merges.
- Closure record still applies (locator Δ, usually 0 for a pure deletion) —
  note the open TMS PR as the one remaining human-only item, same as any
  other awaiting-external-acceptance artifact.
