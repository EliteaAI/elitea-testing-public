---
name: AFS amendment must reach every cell naming the mechanism
description: Amending an AFS step body during implementation leaves stale mechanism names in Coverage Map / Handles Reference cells — check every cell, not just the step.
type: feedback
aliases: [afs amendment drift, coverage map stale mechanism, amended during implementation]
tags: [area/review, type/triangulation]
created: 2026-08-29
updated: 2026-08-29
---

## The pattern

`*Amended during implementation:*` notes get written into the AFS **step body**
where the change was discovered. The same AFS then keeps the pre-amendment
mechanism in its **Coverage Map "Asserted where"** column, its **Axis 2** rows,
and its **Handles Reference** "Shape" column — cells written earlier, in a
different part of the file, that nobody re-read.

Worked examples, PR #1964 (settings-w08 AI Personality family):

| AFS | Step body (amended, correct) | Stale cell |
|---|---|---|
| ELITEA-2381 step 5 | section-still-expanded observed via **visible content** (`PERSONA MANAGEMENT` has no summary testid) | Axis-1 row 12: "section still `aria-expanded=\"true\"`" |
| ELITEA-2381 step 3 | `data-selected` (`SingleSelectMenuItem.jsx:118`) | Axis-2 row: "`aria-selected` marks exactly the current persona" |
| ELITEA-2383 step 3 | toggle read via the `Mui-checked` class (`is_context_management_enabled()`) | Handles Reference: "read `checked` from the `<input>` inside it" |

## Why it matters, and how far

The observable is genuinely asserted in all three, so this is **not** the
round-1 blocker class (a row claiming an assertion with *no* counterpart —
[[coverage_map_row_can_claim_an_assertion_no_handle_supports]]). It is a
weaker, documentation-only defect: an auditor grepping the map for the named
attribute finds nothing in the code and cannot tell which class they are in
without reading the step body.

**Reviewer move:** when a step body carries an `Amended during implementation`
note, grep the whole AFS for the attribute/mechanism it replaced. Report it;
do not block on it alone — the fix is a one-line docs commit and the coverage
claim is sound.

Related: [[coverage_map_row_can_claim_an_assertion_no_handle_supports]] ·
[[finally_block_downgrades_a_strict_teardown]]
