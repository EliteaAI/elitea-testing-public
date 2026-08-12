---
name: skill icon uploaded gallery order
description: SelectIconDialog "Uploaded" gallery has no stable order AND its infinite-scroll can get permanently stuck — see #1459, don't build on it
type: feedback
---

Confirmed live during ELITEA-2604 (analysis pass, then again on the
verify/finish pass). The icon picker's "Uploaded" gallery
(`agent-icon-picker-uploaded-{index}`) is a shared, project-scoped list
(icons from every skill/agent in the project accumulate there — see the
AFS's precondition note). Neither index 0 nor the LAST index reliably
corresponds to "the icon this test just uploaded/applied".

**First fix attempt (superseded, do not repeat):** `ProjectIconItem.jsx`
(shared by both the Default and Uploaded galleries in `SelectIconDialog.jsx`)
tracked selection only via a CSS border/background style with no queryable
DOM signal — added `data-selected={isSelected}` alongside the existing
`data-testid` (`EliteaAI/EliteaUI@e7ff6c06`), and a
`SkillFormPage.delete_selected_uploaded_icon()` method locating
`[data-testid^="agent-icon-picker-uploaded-"][data-selected="true"]`.

**This does NOT actually fix it.** Confirmed live (verify/finish pass,
2026-08-12) via Playwright MCP against a real skill: the "Uploaded" gallery's
infinite-scroll loader (`ListInfiniteMoreLoader.jsx` + the `getSkillIcons`
RTK Query `merge`) gets **permanently stuck** after ANY mutation
(upload/replace/delete) invalidates the list while the dialog's local `page`
state is already > 0 — exactly what a test doing multiple edit-mode
upload/replace cycles (Parts B/C of ELITEA-2604) naturally produces by the
time it reaches a delete step. Reopening the gallery after that point renders
only 1 item (not the just-applied one) even with 56 total uploaded icons in
the project; the `infinite-loader-trigger` element stays present (more data
IS available) but never fires again for that dialog instance. Root cause:
`hasTriggeredRef` in `ListInfiniteMoreLoader` only resets when the merged
list's SIZE changes — if a post-mutation refetch collapses the list, the size
never changes again, so it can't recover. Filed as
`EliteaAI/elitea-testing-public#1459`.

**Consequence:** `delete_selected_uploaded_icon()` + its supporting locators
were REMOVED from `SkillFormPage` (unused/unreliable, would have shipped an
orphan testid). ELITEA-2604's final test uses the "Default" tile
(`select_default_icon_tile()`, `agent-icon-picker-default-icon`) for its
delete/revert-to-default step instead — unaffected by this bug since it
doesn't touch the Uploaded gallery's pagination at all.

**Any future case that needs "delete/target a specific uploaded gallery
icon" must first check whether #1459 is fixed** — until then, don't rebuild
on `data-selected`/the delete-button testid (`agent-icon-picker-uploaded-
{index}-delete-button`, still live in EliteaUI source via
`EliteaAI/EliteaUI@1553565f`, just unused) without also handling the
stuck-loader case (e.g. verifying the target is actually rendered before
relying on it, not just waiting on a selector that may never appear).
