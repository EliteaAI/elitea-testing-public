---
name: MUI Menu stays open across nested actions — its backdrop intercepts clicks outside the Paper
description: An open MUI Menu (no explicit close) leaves a full-page invisible MuiBackdrop-root that swallows clicks on elements outside the Menu's own Paper — re-clicking the same toggle, or clicking an element rendered as a page-level sibling (not inside the Menu), times out.
type: feedback
---

Confirmed live on `RunStateNodeGroup.jsx`'s history-toggle Menu
(`id="runNodes-history-menu"`, ELITEA-2454), but the pattern is generic to any
MUI `<Menu>`/`<Popover>` that has no explicit auto-close wired to a sibling
action:

- Opening the Menu once leaves it open across UNRELATED actions performed
  afterward (e.g. opening/closing a separate dialog spawned by clicking a
  menu item) — there is no auto-close on those actions, only on `onClose`
  (backdrop click / Escape / explicit close call).
- While open, MUI renders a full-page `<div class="MuiBackdrop-root
  MuiBackdrop-invisible MuiModal-backdrop">` that intercepts pointer events
  everywhere EXCEPT the Menu's own Paper content. Two symptoms follow:
  1. **Clicking a page-level sibling element that sits outside the Menu**
     (e.g. the group's "current/last" item, rendered as a `Box` sibling next
     to the `<Menu>`, not inside it) times out — Playwright's actionability
     check correctly reports the backdrop as the element receiving events.
     Fix: dispatch the click via `locator.evaluate("el => el.click()")`
     instead of `locator.click()` — this invokes the element's own handler
     directly without going through the browser's real hit-test/backdrop.
  2. **Re-clicking the same toggle that opened the Menu** (thinking it's
     idempotent/safe to call again) ALSO times out for the same reason — the
     toggle itself is now covered by its own Menu's backdrop.
     Fix: don't re-click blindly. Make the "open" page-object method check
     whether the Menu is already open first (a live, cheap signal — e.g. a
     reused child testid rendering >1 times only while the Menu is mounted)
     and skip the click when it is.

Elements INSIDE the Menu's own Paper (its `MenuItem`s) are never covered by
their own backdrop — only elements *outside* it are affected. So a plain
`.click()` on a menu item is fine; the fix is only needed for (1) sibling
elements outside the Menu and (2) the toggle itself on a second open call.
