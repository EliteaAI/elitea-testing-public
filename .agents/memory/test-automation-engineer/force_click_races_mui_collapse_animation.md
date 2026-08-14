---
name: force=True click races a MUI Collapse expand animation
description: Clicking an item inside a just-expanded MUI Collapse (folder/accordion) with force=True can silently miss — the data-expanded attribute flips before the CSS height transition finishes, and force=True skips Playwright's "stable" wait that would otherwise wait it out. Use plain click().
type: feedback
---

## What happened (ELITEA-2098, 2026-08-14)

`ChatPage.click_conversation_in_folder()` (new method, folder-scoped sibling
of `click_conversation_in_group()`) initially copied the date-group
method's `item.click(force=True)`. Right after `expand_folder()` (which
waits only for `data-expanded="true"` to appear — an attribute flip that is
synchronous with the click handler, NOT gated on the CSS height animation
finishing), the very next `click_conversation_in_folder()` call silently
missed: no navigation, no error, the caller's `wait_for_conversation_url()`
just timed out after 15s with no diagnostic signal pointing at the cause.

Live-reproduced via Playwright MCP against a real seeded folder: a plain
(non-force) `.click()` on the exact same locator, in the exact same
just-expanded state, worked correctly every time. The difference is that
`force=True` explicitly skips Playwright's "stable" actionability check
(element must stop moving before the click dispatches) — during a MUI
Collapse's height transition the item IS moving, so a forced click can
dispatch mid-animation at a screen position the item hasn't settled into.
`click_conversation_in_group()` doesn't have this problem because date-group
sections aren't a collapse/expand surface — there's no animation to race.

## Fix

Drop `force=True` on the folder click; let Playwright's normal actionability
wait out the transition:

```python
item.wait_for(state="visible", timeout=timeout)
item.click()  # NOT force=True — the folder's Collapse animation is still settling
```

## Generalize

`force=True` is not a safe default right after ANY transition — this is the
SECOND distinct root cause under that umbrella in one day:
`chat_send_button_force_click_race.md` (ELITEA-2093, a React internal-state
flap, not a CSS animation) hit the same silent-miss symptom via a different
mechanism. Before reaching for `force=True` on an element whose container
JUST changed state (expanded, appeared, re-rendered, populated
programmatically), try a plain `click()` first — it costs nothing (Playwright
still waits, just with the actionability checks intact) and is the only one
of the two that self-corrects for a still-settling transition. Reserve
`force=True` for the genuinely stable-but-visually-overlaid case
(mui-patterns.md's overlay-interception scenario), not as a first-reach fix
for "element is not clickable."
