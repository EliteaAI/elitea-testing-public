---
name: delete_confirm_warning_icon_579_shape1_pattern
description: How to assert the delete-confirm dialog's warning-icon color (ELITEA-2193) — scoped raw handle, mirrors DELETE_DIALOG_BACKDROP
type: feedback
---

`DeleteEntityModal`'s title (`ChatPage.delete_confirm_title`, testid
`delete-confirm-title`) can render a warning `<svg>` icon
(`Modal.DeleteEntityModal`'s `titleIcon={ModalConstants.MODAL_ICON_TYPE.warning}`
prop) with computed `fill: rgb(233, 121, 18)` (orange). The icon itself is
MUI's own icon-component render output — not app JSX with a placeable
testid — so it qualifies for the **#579-shape-1 sanctioned exception**
(third-party-internal node scoped off a real app testid parent), exactly
like the already-merged `DELETE_DIALOG_BACKDROP` (`.MuiBackdrop-root`,
ELITEA-2116) chained off `delete_confirm_dialog`.

Pattern (added to `pages/chat_page.py`, right after
`dismiss_delete_dialog_via_outside_click()`):

```python
# Scoped raw handle — #579-shape-1 sanctioned exception (comment explains why)
DELETE_CONFIRM_TITLE_ICON = "svg"

def get_delete_confirm_title_icon(self, timeout: int = 5000):
    icon = self.delete_confirm_title.locator(self.DELETE_CONFIRM_TITLE_ICON)
    icon.wait_for(state="visible", timeout=timeout)
    return icon
```

Test asserts (NOT the page object — page objects don't own assertions):

```python
warning_icon = chat.get_delete_confirm_title_icon(timeout=UI_ELEMENT_TIMEOUT)
expect(warning_icon).to_have_css("fill", "rgb(233, 121, 18)")
```

Precedent for the `to_have_css("fill"/"color", ...)` shape (not `.evaluate()` —
that would draw a substitution-grep hit needing justification):
`tests/ui/admin/test_analytics_*` already use `to_have_css("color", ...)` for
KPI-value color assertions. Reuse the SAME idiom for `fill` on an SVG.

Live-verified accessible name for the SAME dialog's trigger button: hovering
a non-owner row's delete icon (`ChatPage.hover_participant_user_row()`)
exposes accessible name exactly `"Remove user"` —
`DeleteParticipantButton.jsx`'s `removeLabel = 'Remove ' + (entityType ||
'participant')` with `entityType` resolved to `'user'` for a Users-section
row. `expect(button).to_have_accessible_name("Remove user")` — no new
testid needed, `hover_participant_user_row()` already existed (ELITEA-2172).
