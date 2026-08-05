---
name: Workflow new-ground blocker needs blocking_detail too
description: batch-build's fix-loop stalls if a reviewer's NEW finding lacks a blocking_detail classification, even when it's trivially fixable
type: feedback
---

## What happened (ELITEA-2292 / issue #800)

`batch-build.workflow.mjs` ran ELITEA-2292 through 2 fix rounds cleanly — both
real, both fixed. Round 2's fix (replacing a raw `.locator("svg")` chain with a
dedicated `user-sort-icon-{field}` testid) was itself correct, but left the AFS's
Concrete Handles / Automation Hints sections describing the now-superseded
locator strategy. Round 3's reviewer caught this accurately and reported it as
a `defect` finding — but explicitly reasoned "this is new ground, not a
carryover of the previous finding, so no `blocking_detail` status entry applies
to it" and left `blocking_detail: []`.

The loop-control script only knows how to continue when a surviving blocker is
classified `unaddressed` (round again) vs `persists`/`external` (stop, it's a
genuine backstop). A **new** finding with no classification at all reads as
"cannot tell unaddressed from unfixable" — so it stopped the case as `blocked`
after only 2 rounds, even though the finding was a trivial, well-scoped docs fix.

## The actual cause

The reviewer-contract's `blocking_detail` vocabulary was designed around
*carryover* findings (a prior round's blocker, re-checked: fixed / still-broken
/ can't-fix-here). It has no explicit guidance for a **brand-new** finding
introduced by the round's own fix — the reviewer correctly judged it doesn't fit
persists/external (nothing "persisted", nothing is external) and also isn't
quite "unaddressed" in the carryover sense, so it left the field empty rather
than force a bad fit.

## What to do when you see this

1. **Don't assume `blocked` means unfixable.** Read the report's full finding
   text — if it's a small, well-scoped, correctly-diagnosed fix (as here), it's
   very likely a loop-control gap, not a genuine dead end.
2. **Resolve it manually, outside the workflow**, same as any blocker recovery:
   dispatch a fix-only implementer for exactly the finding's scope, then a fresh
   reviewer session, explicitly instructing it to populate `blocking_detail` on
   anything it raises. Then land the case yourself (merge case→trunk, trunk→base,
   your own 3× gate) exactly as the workflow would have.
3. **When drafting/editing reviewer dispatch prompts** (workflow script or
   sequential): tell the reviewer explicitly that EVERY surviving finding —
   carryover or brand new — needs a `blocking_detail`/classification entry:
   `unaddressed` (new/still-open, another round would help) / `persists`
   (attempted, still failing) / `external` (not fixable on this branch). A round
   that introduces its own new blocker is exactly the case this note closes.

If this pattern recurs on a future batch, it's worth raising as an actual fix to
`batch-build.workflow.mjs` / `reviewer-contract.md` (extend the vocabulary or the
prompt instruction) rather than hand-resolving every time — file it as a
framework-architecture item at that point.
