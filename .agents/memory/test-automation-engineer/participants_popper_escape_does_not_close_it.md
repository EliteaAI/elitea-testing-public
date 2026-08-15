---
name: chat-participants-popper (Users section) does not close on Escape — only an outside click does
description: ChatPage.dismiss_participants_popover() presses Escape only. Confirmed live (100% reproducible, 3/3 pytest runs + live browser check) that Escape has NO effect on chat-participants-popper's "users" instance — it stays visible indefinitely. Only a real click outside its DOM subtree (MUI ClickAwayListener) closes it.
type: feedback
---

## What happened (ELITEA-2172 implementation)

A new read-only page-object method (`ChatPage.hover_participant_user_row()`)
needed to reliably close-then-reopen the "Users" participants popover
(`chat-participants-popper`) between two hover checks in the same test. The
existing shared idiom, copied from `open_remove_user_dialog()`:

```python
if self.participants_popper.is_visible():
    self.dismiss_participants_popover()  # page.keyboard.press("Escape")
    self.participants_popper.wait_for(state="hidden", timeout=timeout)
```

failed **deterministically, 3/3** local pytest runs, always at the exact
same line: `participants_popper.wait_for(state="hidden")` timed out after
10s / 24 polls, every poll finding the popper still `visible`.

Live-confirmed via Playwright MCP (`browser_evaluate` on
`getComputedStyle(popper).visibility/display` before/after each probe):
- Click the badge to open the popper → `visible/block`.
- Press `Escape` → still `visible/block` (no change at all, not even a
  transient delay).
- Click `document.body` (a real outside click) → closes it (confirmed
  `not found` / closed on the next read).

## Why existing merged tests never hit this

`dismiss_participants_popover()` is called by several merged tests
(ELITEA-2167/2168) purely as a best-effort cleanup gesture — **none of them
ever wait for the popper to become hidden afterward**. The next UI action in
those tests is typically a click on a DIFFERENT part of the page (a modal
button, another badge), which itself acts as the real outside click that
closes the popper as a side effect. So the Escape call is silently a no-op
in every existing usage, and nothing catches it because nothing asserts on
it.

This is the exact same root cause and shape as the already-documented
`ChatPage.close_modules_panel()` gotcha ("Escape does NOT close it... only a
click outside the popper... does") — a DIFFERENT popper, same MUI
`ClickAwayListener` behavior (listens for outside clicks, not Escape, for
this component).

## The fix

Don't call `dismiss_participants_popover()` when you actually need to know
the popper is closed. Use a real outside click instead — reuse
`close_modules_panel()`'s exact technique: click a corner of
`chat_messages_scroll_container` (already a class-level `LocatorDescriptor`,
top-left corner is reliably clear of the popper, which anchors top-right):

```python
if self.participants_popper.is_visible():
    self.chat_messages_scroll_container.click(position={"x": 10, "y": 10})
    self.participants_popper.wait_for(state="hidden", timeout=timeout)
```

## Actionable pattern

`dismiss_participants_popover()` (Escape-only) is fine as a **best-effort,
unverified** cleanup gesture at the end of a test flow where nothing checks
the popper's state afterward. The moment you need a GUARANTEE the popper
actually closed (e.g. a "close-if-already-open" guard before reopening
fresh, or any `wait_for(state="hidden")` after calling it), Escape is not
sufficient — use a real outside click on a known-safe, non-interactive
coordinate instead. Don't assume a shared dismiss helper's name ("dismiss")
implies it's verified effective; check whether any EXISTING caller actually
asserts on the resulting state before trusting it for a NEW use that does.
