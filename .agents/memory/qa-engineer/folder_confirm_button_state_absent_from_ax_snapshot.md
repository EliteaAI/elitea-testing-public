---
name: Folder confirm button state absent from AX snapshot
description: FolderItem.jsx's checkmark has no data-* state attr; MUI empty-title Tooltip makes it vanish from Playwright a11y snapshots when valid — testid-only locating is functionally required, not just policy, on this element.
type: feedback
---

While analysing ELITEA-2458 (chat folder rename checkmark validation), found
that `FolderItem.jsx`'s confirm (checkmark) `Box` has **no `data-*` state
attribute** — only a CSS `fill`/`cursor` difference driven by
`isFolderSaveEnabled`. Worse: a Playwright `browser_snapshot` of this element
is **inconsistent across states**. When the wrapping MUI `Tooltip`'s `title`
is a non-empty string (invalid-name states), the element gets an accessible
name from the tooltip text and shows up clearly. When `title=''` (any
valid-name state, changed or not), MUI attaches no accessible-name, and the
element is either an unlabeled `generic` (indistinguishable from a sibling
Cancel button by role/name alone) or gets pruned from a scoped snapshot
entirely when its computed `cursor` isn't `pointer`.

Practical consequence, confirmed by an actual accidental misclick during
manual exploration: relying on snapshot refs / role-based targeting for an
element like this WILL occasionally hit the wrong sibling. The fix isn't
"be more careful with refs" — it's `page.locator('[data-testid="..."]')`
directly, every time, regardless of what the snapshot currently shows. This
generalizes: any MUI element wrapped in a `Tooltip` whose `title` can be an
EMPTY STRING (not just conditionally absent) is a candidate for this same
gotcha — worth a source read (`title={cond ? '' : text}` pattern) before
assuming a role/label locator will work reliably across all of an element's
states, even when just prototyping/exploring live.

See `test-specs/chat-interface/_surface.md` § "Folder rename editor" and
`test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`
for the full write-up.
