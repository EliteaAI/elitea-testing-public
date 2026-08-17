---
name: dnd-kit drag gesture needs a settle-check, not just scroll-into-view
description: raw page.mouse drag on @dnd-kit items needs two guards — off-screen AND stale-position overlap
type: feedback
---

For any `@dnd-kit/core` PointerSensor drag driven via raw `page.mouse.move/down/up`
(no actionability check, unlike `.click()`), two DISTINCT failure modes exist and
BOTH must be guarded before every `mouse.move()`/`mouse.down()`:

1. **Off-screen** — `bounding_box()` is viewport-relative. An item below the fold
   (this repo's shared DEV account routinely carries 65+ folders ahead of the chat
   conversation list) reports a real-but-unreachable y; `mouse.move()` there
   silently never activates the drag (no error, just a later timeout waiting for
   the drag-activation signal). Fix: `locator.scroll_into_view_if_needed()` first.

2. **Stale-position overlap (subtler, reproduces AFTER scrolling)** — even when
   `bounding_box()` correctly matches `getBoundingClientRect()` for YOUR element,
   a DIFFERENT, stale-positioned row can visually sit on top of that exact pixel
   (confirmed via `document.elementFromPoint` returning an unrelated element).
   Reproduced dragging a conversation OUT of a just-expanded folder in this repo's
   chat sidebar. A raw `page.mouse` sequence has no actionability check, so it
   silently presses the WRONG element. Fix: poll
   `document.elementFromPoint(cx, cy) === el || el.contains(hit)` until it settles
   before pressing/moving (`ChatPage._wait_for_pointer_target()`,
   `pages/chat_page.py`) — a real condition-wait, not a sleep.

Also: for `@dnd-kit` items built like `DraggableConversationItem.jsx`/
`DraggableFolderItem.jsx` in this codebase, the `isDragging` opacity style
(0.5 while dragging) lives on the draggable wrapper Box, which is the
**parent** of the testid'd element, not the testid'd element itself — read via
`el => getComputedStyle(el.parentElement).opacity`.

Reusable primitives: `ChatPage.start_conversation_drag()` /
`move_drag_over_target()` / `release_drag()` / `abort_drag()` /
`_wait_for_pointer_target()` (ELITEA-2142/2143/2145, PR #1543). Any new
drag-and-drop page-object method should reuse these, not raw
`bounding_box()` + `mouse.move()`.
