---
name: Hover-to-reveal menu breaks when hovering the whole (now-taller) expandable container
description: A locator.hover() on an accordion/expandable row's outer container lands at its geometric center — safe while collapsed, but once expanded the center shifts into the body and misses a header-scoped hover-reveal trigger, causing a silent, 100%-reproducible cleanup failure (ELITEA-2132, PR #698)
type: feedback
---

## The defect (PR #698, ELITEA-2132, chat folder creation)

`ChatPage.delete_folder_via_menu()` (`automation/pages/chat_page.py:3353`)
calls `item.hover()` where `item = get_folder_item(folder_id)` resolves to
`[data-testid="chat-folder-item-{id}"]` — the WHOLE folder accordion
(`FolderAccordion.jsx`'s `StyledAccordion`), scoping both the header
(icon/name/expand-arrow/dot-menu) AND the body (empty-state/conversation
list) as descendants, by design (so a single testid can locate either).

Playwright's `Locator.hover()` with no `position=` moves the mouse to the
element's bounding-box CENTER. `FolderAccordion.jsx`'s CSS/JS only reveals
the dot-menu (`#Menu`, `display: isHovering ? 'flex' : 'none'`) on hover of
the **header sub-box specifically** (`summaryContainer`, fixed ~49px tall,
its own `onMouseEnter`/`onMouseLeave` feeding `isHovering` state) — NOT the
outer accordion. While the folder is COLLAPSED, the whole element IS just
the header, so the center lands correctly. Once EXPANDED (which this
test's own Step 7 always does, right before cleanup runs), the accordion's
height = header + body, and the geometric center shifts down into the body
— outside the header's hover-reveal zone. The dot-menu never appears,
`menu_button.wait_for(state="visible")` times out every time, and
`delete_folder_via_menu()` throws.

The test's own cleanup wraps this call in `except Exception as exc:
logger.warning(...)` (matches this repo's established try/finally +
try/except cleanup idiom — see `test_conversation_management.py`,
`test_conversation_deletion_flow.py` — so NOT itself a deviation), which
means the test reports PASSED while permanently leaking a real "New
folder" folder into the shared dev project, on every single run, with no
visible signal beyond a WARNING log line.

## How I confirmed it (don't trust a Run Report's "cleanup verified" claim)

Independently re-ran the merged test 3x fresh + 1x with
`--log-cli-level=INFO` against the live `localhost:5173` env — found 7
pre-existing leaked `[data-testid^="chat-folder-item-"]` folders already in
the shared project BEFORE I started (directly contradicting the PR's own
claim "Post-run DOM check confirms zero leftover... cleanup verified
across all runs"), and every one of my 4 runs added another (8 total). The
verbose run's log pinpointed the exact mechanism:
```
ERROR elitea.steps:actions.py:49 Step failed: Delete folder via menu — Locator.wait_for: Timeout 10000ms exceeded.
  - waiting for locator("[data-testid=\"chat-folder-item-8\"]").locator("[data-testid=\"conversation-menu-menu-button\"]") to be visible
WARNING elitea.tests.chat:test_folder_creation.py:262 Failed to delete folder 8: ...
```
pytest still reported the test PASSED. Manually cleaned up all 8 leaked
folders afterward (fixed hover via `item.hover(position={"x": 20, "y":
20})` — lands reliably inside the fixed-height header regardless of
expand state) so the review didn't leave the shared project worse off.

## Reusable pattern for future reviews

Any `locator(container).hover()` where `container`'s bounding box GROWS on
interaction (expand/accordion, "show more", inline-edit-grows-a-textarea,
etc.) is unsafe if the thing you're hovering to reveal is scoped to a
FIXED-size sub-region (usually the header/summary) rather than the whole
container. Symptoms to watch for in review: (1) a hover call on the same
handle used for both header AND body scoping, immediately following a step
that expands/grows that same element; (2) a cleanup wrapped in a
swallow-and-log except — the two combined mean a broken interaction can
ship green indefinitely. Fix: hover a `position=` inside the known-fixed
header region, or hover a locator scoped to the header itself, never the
outer expandable container.
