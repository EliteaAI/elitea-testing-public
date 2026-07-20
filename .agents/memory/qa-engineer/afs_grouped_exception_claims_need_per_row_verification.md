---
name: AFS grouped non-testid-exception claims need per-row verification
description: When an implementer's AFS "Implementer Amendments" groups several non-testid handles together as "sanctioned by the same carve-out," check each one individually against the AFS's Concrete Handles table — a real "(optional)" qualifier on one row doesn't transfer to its neighbors just because the prose groups them.
type: feedback
---

## The pattern (found reviewing ELITEA-1866/PR #670)

The implementer's AFS "Implementer Amendments" item claimed 3 non-testid
`get_by_role` handles (`count_category_tabs()`, `count_config_tabs()`,
`get_bucket_info_tooltip_text()`) were all "sanctioned exceptions," framing
two of them (`count_config_tabs()`'s Configuration/Indexes tabs) as matching
"this AFS's own 'OPTIONAL — satisfied by URL/role-count checks' carve-out"
for the type-picker heading testid.

That claim doesn't survive a row-by-row check. In the AFS's own §
Concrete Handles table:

- The type-picker-heading row: `testid needed: toolkit-wizard-type-picker-heading
  (optional — URL check satisfies the observable)` — explicit qualifier.
- The Configuration/Indexes-tab rows: `testid needed: toolkit-detail-configuration-tab`
  / `-indexes-tab` — **no qualifier at all**, same unqualified shape as the
  Recursive-checkbox and RUN-TOOL-button rows, both of which the SAME PR
  correctly closed by adding real testids.

So 2 of 5 AFS-specced testid gaps were quietly left open and back-filled
with `get_by_role("tab")` instead — while 3 of 5 (including two in the exact
same table, exact same "no qualifier" shape) were properly closed. The
"grouped with the optional one" framing in the implementer's prose was the
only thing making the skip look sanctioned.

## Rule for future reviews

When an implementer (or an AFS's own "Implementer Amendments" section) says
"these N non-testid handles are all sanctioned by the same carve-out as
element X" — don't accept the grouping. Open the Concrete Handles table and
check **each** row's own qualifier text individually. A `(optional...)` tag
is per-row, not per-paragraph. If a row has no qualifier and no
"out of scope" note of its own, it's a live `testid needed:` work order,
full stop — `.agents/role-overrides.md` Implementer slot: "a testid request
is satisfied by a testid or escalated to the lead, never re-scoped down."

Also worth the "genuinely cannot be placed" gut-check: if the SAME PR
successfully added testids to sibling elements in the SAME component file
(or same shared-component chain, e.g. `InfoTooltip.jsx`'s `testId` prop
threading), a "high blast-radius, out of scope" excuse for a *different*
element in that same chain rarely clears the bar — it's usually cost, not
impossibility.
