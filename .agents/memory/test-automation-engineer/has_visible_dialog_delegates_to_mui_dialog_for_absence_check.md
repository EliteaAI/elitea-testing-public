---
name: has_visible_dialog delegates to mui Dialog for absence check
description: Asserting a MUI dialog does NOT appear, testid-compliant pattern
type: feedback
---

When a case needs to assert a MUI dialog **did not appear** (e.g. ELITEA-2438
— an invalid file upload should be rejected before the "Import parameters"
dialog ever renders), the naive first instinct is
`page.get_by_role("dialog")` / `.count() == 0` written directly in the test —
this trips the reviewer's mechanical grep (`get_by_role` is not a
`[data-testid=` selector) and is `CHANGES_REQUESTED` per
`.agents/role-overrides.md`.

The dialog itself often has no dedicated testid (MUI's generic
`role="dialog"` wrapper, per `mui_dialog_needs_its_own_testid_not_role_dialog.md`).
The compliant fix is NOT to add a testid to every dialog just to check
absence — it's to reuse the existing `components/mui.py` `Dialog` helper
(already used by page objects like `SkillsListPage.import_skill()` via
`Dialog.wait_for()`), which lives outside `automation/pages/` and
`automation/tests/` so it's outside the mechanical grep's scope by design
(it's the shared low-level component layer, not a "new raw handle in a page
object/test").

Pattern (added to `SkillsListPage`, generalizes to any page object):

```python
def has_visible_dialog(self, timeout: int = 500) -> bool:
    """Return True if a MUI dialog is visible — delegates to
    components.mui.Dialog rather than a new raw role selector."""
    try:
        Dialog.wait_for(self.page, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False
```

Keep the timeout short (e.g. 500ms) and call it only AFTER already waiting on
whatever positive signal proves the flow settled (e.g. an error toast) — this
avoids both a race (checking too early) and needlessly slowing the test down
(polling the full default 5s for something that should already be settled).

Assert with `assert not page_obj.has_visible_dialog(timeout=500), "..."`.
