---
name: Chat dnd-kit drag gesture technique
description: How to drive @dnd-kit PointerSensor drags reliably with Playwright for chat conversation<->folder DnD
type: feedback
---

Chat's conversation<->folder drag-and-drop (`src/hooks/chat/useDragAndDrop.js`)
uses `@dnd-kit/core`'s `PointerSensor` (8px activation distance), NOT native
HTML5 `draggable`/`DragEvent`. Confirmed live 2026-08-15 (ELITEA-2142/2143/
2144/2145 analysis):

- **Real Playwright mouse gestures (mousedown → several `mouse.move(...,
  {steps: N})` → mouseup) DO drive the real product code** — confirmed via
  network capture, a genuine `PUT /elitea_core/conversation/prompt_lib/...`
  fires. No substitution needed for this whole feature family.
- **A single big-jump `dragTo()` (or any technique with too few intermediate
  steps) is unreliable** — under-shoots the 8px activation distance or misses
  a collision recompute. Use several `steps` per `mouse.move()` call.
- **Re-measure the target's `boundingBox()` on EVERY iteration, not once
  up front.** Layout shifts during the drag (e.g. a source folder's
  accordion collapsing once its only conversation starts dragging) move
  sibling elements by a few px mid-gesture; a stale captured target rect can
  miss the real element.
- **`@dnd-kit`'s built-in autoscroll did NOT visibly engage** for synthetic
  MCP pointer input (held near a viewport edge for 30+ iterations, ~4-6s,
  page never scrolled) — don't rely on it for a source/target pair that
  needs scrolling into simultaneous view. If both ends can't be resized into
  one viewport (`browser_resize` to a tall height, e.g. 1280x4000, works
  when the intervening content is short enough), the gesture may need a
  different approach (native `Locator.scrollIntoViewIfNeeded()` per element,
  accepting that the drag itself then can't be one continuous unbroken
  gesture across a scroll boundary).
- **A confirmed, reproducible defect exists in the drop-target resolution**
  for folder-to-folder drags — see elitea-testing-public#1541. The visual
  hover-highlight (dashed border, `DroppableFolderItem`'s
  `shouldShowDropFeedback`) can show the CORRECT target right up to release,
  while `handleDragEnd`'s actual `over.id` resolves to `'ungrouped-conversations'`
  instead. Don't assume "highlight was correct" proves "drop landed
  correctly" — assert the actual `PUT` body / resulting folder membership,
  not just the highlight.
- This shared DEV account (localhost:5173) currently carries **65+ orphaned
  chat folders** from insufficiently-cleaned-up prior test sessions — this is
  a KNOWN, already-tracked issue (elitea-testing-public#1309/#1310/#1533,
  `chat-folder-menu-delete-menuitem` testid regressions breaking
  `delete_folder_via_menu()`'s cleanup). It makes the "Today" date-group list
  sit thousands of px below the folder list, which is what defeated a clean
  single-viewport drag test for the Today<->folder direction this session.
  Worth knowing before attempting any Today-section-adjacent drag test on
  this account without first confirming #1309 is fixed.
