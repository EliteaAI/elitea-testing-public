---
name: Chat folder pin/unpin remounts row and resets expand state
description: Pinning/unpinning a chat folder moves its row between list partitions (a remount, not a reorder) — data-expanded resets to false even if the folder was expanded beforehand; a synchronous post-click read can miss this and report a false "still expanded".
type: feedback
---

## What happens

In `FolderAccordion.jsx` / `Folders.jsx`, pinned and unpinned folders render via
separate `renderFoldersSection({isPinned: true/false})` calls. Toggling a folder's
pin state (`chat-folder-menu-pin-menuitem`, `PATCH .../folder/prompt_lib/{project_id}
/{folder_id}`) moves its row between these two partitions — this is a genuine
**remount**, not an in-place DOM reorder. Any local component state (expand/collapse)
resets to its default (`data-expanded="false"`) on the settled render, **even if the
folder was expanded immediately before the pin/unpin click**. This is true in BOTH
directions (pin AND unpin).

## The trap: a synchronous post-click read lies

A bare `page.evaluate()` / `get_attribute()` read taken immediately after the pin
click can still see the STALE (pre-remount) DOM node reporting `data-expanded="true"`
— React hasn't finished the remount yet. This produced a false conclusion during
exploration (ELITEA-2152/2153, 2026-08-15): "pinning doesn't collapse an
already-expanded folder." The implementer's pytest run, using a **polling, web-first
assertion** (`expect(locator).to_have_attribute("data-expanded", "true",
timeout=...)`), caught the real settled value: `false`.

**Lesson: a single synchronous read right after an action proves only "not yet
false" — never trust it as evidence of the SETTLED state on this surface (or any
surface with structural list moves).** Use `expect().to_have_attribute()` /
`to_have_count()` / other auto-retrying assertions, or genuinely time-separate a
manual re-check, before writing a persistence claim into an AFS.

## The fix

`ChatPage.expand_folder()` gained an additive `force: bool = False` parameter
(chat_page.py, ELITEA-2152/2153). Re-expand explicitly after a pin/unpin action:

```python
chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT, force=True)
```

`force=True` is REQUIRED specifically for a folder that is CURRENTLY pinned (the
`DraggableFolderItem` `isDragDisabled={isPinned}` disabled-ancestor gotcha, already
documented for the dot-menu button in ELITEA-2130's AFS, applies to a plain click on
the WHOLE row too — not just the dot-menu button).

## Also fixed this session (same PR)

- **Creation-order rule for a deterministic Y-baseline**: a folder created MORE
  RECENTLY renders ABOVE an older one, under the default
  `sort_by=updated_at&sort_order=desc` folder-list query. An earlier AFS draft had
  this backwards.
- **Y-position equality needs a tolerance, not `==`**: `getBoundingClientRect()`
  reads of the SAME unmoved element can differ by a fraction of a pixel between two
  calls (observed: `138.71875` vs `138`). Use `abs(a - b) < ~2.0`, not exact equality
  — a real reflow moves a row by a full row height (~41px), far above this tolerance.
