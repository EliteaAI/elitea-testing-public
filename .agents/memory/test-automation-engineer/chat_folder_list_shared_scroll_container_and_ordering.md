---
name: Chat sidebar folder list shares one scroll region and sorts newest-first
description: Conversations.jsx's ref={listRef} container holds folders AND the full pinned/date-grouped conversation list in ONE scroll region, so "scroll to raw max" overshoots past the folder section; folders render NEWEST-created closest to the TOP, not the bottom.
type: feedback
---

## What happened (ELITEA-2146/2147, 2026-08-15)

An AFS assumed "scroll the sidebar/Move-to-submenu list to its raw
`scrollHeight - clientHeight` maximum" would land on the LAST-created seeded
folder. Live-false on two independent counts, both confirmed via bounding
boxes during implementation:

1. **The container is shared.** `Conversations.jsx`'s `ref={listRef}` `Box`
   renders pinned folders, pinned conversations, UNPINNED folders (the normal
   case), then the full `GroupedConversations` date-grouped list — ALL in one
   `overflow-y: scroll` region. On an account with ambient conversation data,
   the container's true scroll extreme sits well past the folder section
   entirely. Scrolling to the literal max landed a target folder at a deeply
   NEGATIVE `getBoundingClientRect().y` (already scrolled hundreds of px past,
   above the viewport) — not at the bottom at all.
2. **Folders sort newest-first.** No explicit `.sort()` in the render path;
   the `folders` store order is used as-is, and empirically (26 seeded
   folders' `y` coordinates, strictly monotonic with creation order) NEWER
   folders render CLOSER TO THE TOP. "Last created" and "bottommost
   on-screen" are opposite ends, not the same one. The Move-to submenu
   (`DotMenu.jsx`'s nested `Menu`, fed by `getMoveConversationToFoldersMenuItems`)
   reuses the SAME `folders` order — same effect there.

## Fix

Don't assume a specific folder ends up at either scroll extreme. Instead,
read live bounding boxes to classify a target folder's position relative to
the container/popover's own bounding box (`"above"` / `"within"` / `"below"`),
pick a genuinely below-the-fold (or above-the-fold) candidate, and scroll
toward it with a check after EVERY real wheel gesture — not a single jump to
the raw scroll maximum:

```python
def get_folder_row_scroll_position(self, folder_id) -> str:
    container_box = self.chat_conversation_list_scroll_container.bounding_box()
    row_box = self.get_folder_item(folder_id).bounding_box()
    top, bottom = container_box["y"], container_box["y"] + container_box["height"]
    if row_box["y"] + row_box["height"] <= top: return "above"
    if row_box["y"] >= bottom: return "below"
    return "within"
```

Also use a wheel delta SMALLER than the container's `clientHeight` for the
scan loop (e.g. 200px against a ~700-830px-tall container) — a delta close to
or larger than `clientHeight` can skip a single ~41px folder row clean between
two checked positions, producing a false "unreachable" result even though the
container/popover position logic above is otherwise correct. Pick the
NEAREST below/above candidate (`min`/`max` by `y`) to keep the scan short.

## Generalize

Any future case that assumes "the Nth-created/last-created item is at a
specific scroll extreme" on this sidebar OR the Move-to submenu needs this
same empirical-positioning treatment — don't re-derive it, grep this file.
`chat_page.py` carries `get_folder_row_scroll_position()` /
`get_move_to_folder_item_scroll_position()` /
`scroll_conversation_list_until_folder_visible()` /
`scroll_move_to_submenu_until_folder_visible()` (ELITEA-2146/2147) — reuse
them, don't reinvent a "scroll to extreme" primitive for this container.
