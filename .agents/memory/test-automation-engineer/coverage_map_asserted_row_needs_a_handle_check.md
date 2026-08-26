---
name: Coverage Map 'asserted' row needs a handle, not just a Verify-clause tag
description: ELITEA-2611 fix round 1 — 2 Coverage Map rows said 'asserted' with zero row in the AFS's own Concrete Handles table and zero implementation
type: feedback
---

## What happened (ELITEA-2611, PR #1477, fix round 1)

The AFS's Coverage Map marked rows 10/11 ("Current" value read-only /
"Suggested" value editable, General step) as `asserted`, pointing at `step 6`.
But the AFS's own Concrete Handles table never listed a testid for either
column — only the step indicator, checkboxes, nav buttons, and Summary
inputs were in the "new testids" table. The implementation (round 0) never
noticed the gap and shipped with no locator and no assertion for either row
— caught at review, not before.

This is the SAME failure mode as
`afs_concrete_handles_table_can_undercount_verify_clauses.md` (ELITEA-1906)
but approached from the opposite direction: that entry says "walk every
Verify clause and check for a table row"; this one says **walk every
Coverage Map row marked `asserted` and check it has BOTH a table row AND
actual code that uses it** — the Coverage Map disposition and the Concrete
Handles table can drift from each other, and either one alone will miss it.

## The fix

Added a `testId` prop to the shared `TextDiffHighlight.jsx` (threaded
through `GeneralStep.jsx` → `AIEditSkillModal.jsx`, additive-only, no new
hooks/DOM nodes) and wired two new testids scoped to the Description field
only (the one the test already exercises — canon #511, no orphan for
Name's identical pair): `ai-edit-skill-general-description-current` /
`-suggested`. Asserted structurally: CURRENT has no `contenteditable`
attribute + text equals the seed value; SUGGESTED has
`contenteditable="true"`. Landed on `automation/testids` at
`EliteaAI/EliteaUI@3e1e5c73`.

## How to catch it earlier

In Phase 1 (Absorb), when walking the Coverage Map row-by-row against the
case, ALSO cross-check every `asserted` row's "Asserted where" cell against
the Concrete Handles table: does a real testid exist for what this row
claims to prove? A Coverage Map disposition is not verified just because it
names a step — it has to survive being traced to an actual DOM handle.

## Related

- `afs_concrete_handles_table_can_undercount_verify_clauses.md` — same root
  cause, opposite direction of the walk (Verify clause → table, not
  Coverage Map row → table).
- `afs_is_a_work_order_not_gospel.md` — general principle this is a
  corollary of.

## Multi-handle rows: check EVERY handle a row names, not just one (ELITEA-2081, PR #1613, fix round 1)

A narrower variant, caught at review not before: a Coverage Map row can name
TWO handles for one disposition (`"canvas chrome (toolkit-canvas-close-button,
toolkit-canvas-title) absent from the DOM"`). Round 1 asserted the title-hidden
check but silently dropped the close-button-hidden check — both handles were
correctly identified in the AFS row, but only one made it into code, and the
row still read `asserted` because it was scanned for "is there an assertion
here" rather than "is there an assertion for EACH named handle here". Same PR
also had a separate page-object construction-site slip (an inline
`page.locator(Page.TESTID_TEMPLATE.format(...))` where a compliant wrapper
method — `get_type_card()` — already existed and simply wasn't called).

**Self-review addition:** when a Coverage Map row's "Asserted where" or the
step's own Verify clause lists multiple testids in one sentence, grep the diff
for every one of them individually before calling the row covered — don't
stop at the first handle that happens to already be near your other
assertions in that step's block.
