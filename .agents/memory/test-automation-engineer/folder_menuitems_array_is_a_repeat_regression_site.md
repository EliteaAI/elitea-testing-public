---
name: FolderItem.jsx menuItems array is a repeat regression site
description: FolderItem.jsx/ConversationItem.jsx dot-menu `menuItems` arrays repeatedly lose sibling `key`s to unrelated feature commits — verify testids live before building, don't trust an AFS's "testid added" claim as still-true.
type: feedback
---

## The pattern (2 confirmed instances, different items, same array)

`FolderItem.jsx`'s `menuItems` array literal (feeds `DotMenu`, whose
`testId={item.key}` -> `BasicMenuItem`'s `data-testid={testId}-menuitem`
mechanism is how every dot-menu item gets its testid) has now lost a
sibling item's `key` TWICE, from TWO different unrelated feature commits:

1. **Delete** (`#1309`, 2026-08-07-era): `key: 'chat-folder-menu-delete'`
   added, lost, re-added, lost again by `6bec1451` ("Fix rename
   conversation block behaviour"). Still dead as of this writing.
2. **Rename** (`#1533`, 2026-08-15): `key: 'chat-folder-menu-rename'`
   added by ELITEA-2458 (`0298860f`), lost by `f5e0c325` ("Restore user
   message to input field when Stop is clicked", #764) — a commit that
   replaced the WHOLE `menuItems` array to add a new "New chat" item,
   silently dropping Rename's key in the process. Fixed same-session
   (`be489cee`).

**The mechanism is always the same**: someone edits the array literal for
an unrelated reason (adding an item, restyling, reordering) and rewrites
the whole block instead of touching only their own entry, dropping a
sibling's `key` with no compile-time or lint signal — the item still
renders fine, only its testid silently vanishes.

## What this means for the NEXT case touching this array (or its
`ConversationItem.jsx` sibling)

**Don't trust a prior AFS/digest's "testid X was added, confirmed working"
claim as still-true — re-verify live before building**, even if the
digest is recent and even if it was YOUR OWN prior session that added it.
The cheapest check: before writing any test code that depends on a
dot-menu item's testid, re-run (or re-drive) the flow live once. If it's
already a merged test depending on the same testid, just re-run THAT
test first — a live failure surfaces the regression before you've sunk
time into a new AFS assuming the handle works.

If you find another instance (a THIRD item losing its key, or the same
two regressing a third time): that's a strong signal to escalate a
structural fix to the lead (e.g. a lint rule / PR-template checklist item
on the UI-team side, or converting the array to per-item constants that
are harder to wholesale-replace) rather than just re-patching again —
three independent regressions of the same shape is a process gap, not
bad luck.

## Related, separate gotcha found alongside `#1533`

A PINNED folder's `DraggableFolderItem` wrapper renders a genuinely
HTML-`disabled` ancestor around the row once `isDragDisabled=isPinned` —
a plain Playwright click on the (itself-enabled) dot-menu button times
out ("element is not enabled") for a pinned folder specifically, even
though the button's own `.disabled` DOM property is `false`. The
EXISTING `open_folder_rename_editor()`/`delete_folder_via_menu()` already
use `.click(force=True)`, which bypasses this correctly — no fix needed,
just know it's there before "fixing" it a second time. Playwright MCP's
`browser_click` has no `force` option, so exploring a pinned folder's
dot-menu via MCP needs `browser_evaluate`'s raw `element.click()` instead.
