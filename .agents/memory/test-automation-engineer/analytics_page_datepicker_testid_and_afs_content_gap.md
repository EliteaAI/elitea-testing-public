---
name: Analytics page DateTimePicker testid + AFS content-assertion gap
description: MUI X DateTimePicker slotProps.textField.inputProps carries data-testid to the real <input>; AFS "content renders" claims may lack a handle
type: feedback
---

## Context
ELITEA-2310 (Analytics page default-load). `AnalyticsContainer.jsx`'s From/To
`DateTimePicker`s shared one `datePickerCommonProps.slotProps` object — could
not carry two distinct testids. Split into a per-field
`getDateFieldSlotProps(testid)` helper returning
`{ textField: { ..., inputProps: { 'data-testid': testid } }, actionBar, popper }`,
applied via `slotProps={getDateFieldSlotProps(...)}` placed AFTER the
`{...datePickerCommonProps}` spread so it isn't clobbered. Confirms the same
`inputProps` (lowercase, not `InputProps`) pattern already recorded in
`generateagentreviewform_inputbase_slotprops_discarded_use_inputprops.md` and
`styledinputenhancer_data_testid_needs_inputprops_not_bare_prop.md` — this is
now the third confirmed MUI-X/MUI-TextField site where `inputProps` (not
`InputProps`, not a bare top-level prop) is required to land `data-testid` on
the actual `<input>` DOM node.

## The AFS content-assertion gap
The AFS's step 8 required "the Overview tab's content (KPI row) is rendered"
but the Concrete Handles table had NO testid for it — only the loading
spinner. Asserting "content rendered" without a locator would have meant
either a fake handle (forbidden) or a weak proxy assertion (defect-masking
risk: spinner-gone alone doesn't prove content arrived, per the AFS's own
Axis-2 rationale for that very step). Added `analytics-overview-kpi-row`
testid on `AnalyticsOverview.jsx`'s KPI-row `Box` during Phase 2, amended the
AFS Concrete Handles table + provenance note in the same PR (spirit-compliant
addition, in scope — same case, same step, not scope creep).

**Preventive takeaway for other cases:** when an AFS step's expected result is
phrased as "X's content renders" / "page settles into a working state" without
a named handle in the Concrete Handles table, that's a real gap to close via
implementer exploration (Phase 2), not something to wave through with an
absence-of-loading-state proxy alone.
