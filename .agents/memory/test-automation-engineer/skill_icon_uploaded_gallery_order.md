---
name: skill icon uploaded gallery order
description: SelectIconDialog "Uploaded" gallery has no stable recency order — target selection via data-selected, never index
type: feedback
---

Confirmed live during ELITEA-2604. The icon picker's "Uploaded" gallery
(`agent-icon-picker-uploaded-{index}`) is a shared, project-scoped list
(icons from every skill/agent in the project accumulate there — see the
AFS's precondition note). Neither index 0 nor the LAST index reliably
corresponds to "the icon this test just uploaded/applied" — tried both,
both wrong (deleted an unrelated pre-existing entry each time, leaving the
actually-applied icon untouched).

`ProjectIconItem.jsx` (shared by both the Default and Uploaded galleries in
`SelectIconDialog.jsx`) tracked selection only via a CSS border/background
style with no queryable DOM signal — fixed by adding
`data-selected={isSelected}` alongside the existing `data-testid`
(`EliteaAI/EliteaUI@e7ff6c06`), the project's standard "testid identity +
data-* state" shape.

`SkillFormPage.delete_selected_uploaded_icon()` locates the target via
`[data-testid^="agent-icon-picker-uploaded-"][data-selected="true"]` —
reads the matched element's own `data-testid` to derive the index for the
delete button, rather than assuming a position. Use this pattern (not a
literal index) any time a test needs "the currently-applied icon" in
either gallery.
