---
name: MUI Menu/Popover click-outside dismissal — safe geometry pattern
description: Reusable technique for testing a MUI Menu/Popover's click-outside dismissal without landing on a foreground menu item or another interactive element — compute a point below the union bounding box of the open menu's own (testid-keyed) items, within a known container's box, then dispatch page.mouse.click(x, y) directly.
type: feedback
---

## The trap (documented in the ELITEA-2030 AFS itself, re-confirmed live)

A naive "click outside" implementation grabs the invisible MUI backdrop
(`.MuiBackdrop-root`) and clicks its own bounding-box CENTER. The backdrop's
box is the FULL VIEWPORT, but the visually smaller popup Paper renders on
top of it — so the backdrop's geometric center frequently coincides with a
real, foreground menu item. The click lands on that item instead of
dismissing the menu (in the AddNodeMenu case, this actually ADDED a node,
the opposite of the intended assertion).

## The fix — verified live via browser-verify/CDP during ELITEA-2030

1. **Get the real test viewport, not whatever the exploration tool
   defaults to.** `chrome-launcher.sh`'s headless default was ~756×469 —
   far smaller than this project's actual pytest-playwright viewport
   (1366×768, `conftest.py`). Geometry computed at the wrong viewport size
   produces confidently-wrong coordinates (a point that's "clearly outside
   the menu" at 756×469 may not be at 1366×768). Always
   `node cdp.mjs viewport <w> <h>` to match `conftest.py` before measuring.

2. **Compute the menu's own footprint from its testid-keyed items**, not
   the backdrop:
   ```python
   items = self.page.locator(self.ADD_NODE_MENU_ITEM_PREFIX)  # or equivalent
   boxes = [items.nth(i).bounding_box() for i in range(items.count())]
   menu_bottom = max(b["y"] + b["height"] for b in boxes if b)
   ```

3. **Pick a point inside a KNOWN container** (e.g. the canvas wrapper) that
   is below `menu_bottom` with margin, clamped to the container's own box:
   ```python
   canvas_box = self.canvas_wrapper.bounding_box()
   x = canvas_box["x"] + canvas_box["width"] / 2
   y = max(menu_bottom + 40, canvas_box["y"] + canvas_box["height"] * 0.75)
   y = min(y, canvas_box["y"] + canvas_box["height"] - 10)
   ```

4. **Dispatch a raw coordinate click**, bypassing locator-based
   actionability (which would otherwise re-target whatever element the
   locator resolves to, not the literal point):
   ```python
   self.page.mouse.click(x, y)
   ```

5. **Verify via `document.elementFromPoint(x, y)`** during exploration
   (not shippable in the test, just for confirming the technique) — for
   AddNodeMenu this confirmed the chosen point resolved to
   `MuiBackdrop-root MuiBackdrop-invisible MuiModal-backdrop`, i.e. exactly
   the true dismiss target, not a menu item or a node.

## Reusable beyond AddNodeMenu

Any MUI `Menu`/`Popover`/`Popper` dismiss-by-click-outside case can reuse
this shape: bound the popup by its own real items (not the backdrop),
target a point in a known, unrelated container below/beside that bound,
raw-coordinate click. Don't reach for a hardcoded pixel offset without
first measuring at the ACTUAL test viewport.

## Locator-shape lesson tied to this

Enumerating "however many items are currently open" for a geometry-only
computation (no assertion) still needs a proper UPPER_CASE class-level
`[data-testid^="…"]` prefix constant — NOT an inline literal in the method
body. It's the same testid family already used for individual per-item
reads, and the existing `SELECT_OPTION`/`SELECT_OPTION_PREFIX` pair in
`pipeline_detail_page.py` is the established precedent to mirror.
