---
name: Clicking the whole FOLDER_ITEM to collapse can miss (lands on body, not header)
description: FOLDER_ITEM scopes both header AND body as descendants; a plain .click() targets the bounding-box CENTER, which for an EXPANDED folder (taller box, body visible) can fall inside the conversation-list body instead of the header toggle. Click the scoped FOLDER_EXPAND_ICON for the collapse direction.
type: feedback
---

## What happened (ELITEA-2148, 2026-08-15)

`expand_folder()` safely clicks the WHOLE `get_folder_item(folder_id)`
container because a COLLAPSED row's bounding box is just the header — the
click center always lands on it regardless of exact geometry. A first-draft
`collapse_folder()` mirrored that same "click the whole row" shape (also
matching what the AFS's own exploration pass suggested, based on a single
ambient-folder manual check). It failed live: `Locator.wait_for` timed out
waiting for `data-expanded="false"` — the click landed but didn't toggle.

Root cause: `FOLDER_ITEM` scopes BOTH the header (icon/name/expand-arrow/
dot-menu) AND the body (conversation list / empty-state) as descendants
(this is intentional — same testid = stable identity, PR #581 ruling). When
EXPANDED, the container's bounding box grows to include the body content, so
Playwright's plain `.click()` (bounding-box CENTER) can fall inside the body
instead of the header toggle — not always (depends on body height vs header
height), which is why it can pass in ad-hoc manual exploration on one folder
and still fail in the shipped test.

## Fix

For the COLLAPSE direction specifically, click the scoped `FOLDER_EXPAND_ICON`
(always inside the header, unaffected by body height) instead of the whole
row:

```python
def collapse_folder(self, folder_id, timeout=5000):
    self.get_folder_item(folder_id).locator(self.FOLDER_EXPAND_ICON).click()
    self.page.locator(f'{self.FOLDER_ITEM.format(folder_id)}[data-expanded="false"]').wait_for(
        state="visible", timeout=timeout
    )
```

`expand_folder()` itself stays as-is (whole-row click is safe there — the
COLLAPSED state never has this problem).

## Generalize

Any toggle whose container ALSO scopes variable-height content (a
disclosure/accordion where testid = the whole disclosure, not just its
header) needs its collapse-direction click aimed at a header-scoped
sub-element, not the container as a whole — the container's center point is
only a safe click target while the container is at its SMALLEST size.
