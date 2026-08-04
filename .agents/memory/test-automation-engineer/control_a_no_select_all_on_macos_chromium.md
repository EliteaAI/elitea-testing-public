---
name: Control+a doesn't select-all on macOS Chromium
description: press("Control+a") is a no-op here — use select_text() + wait-for-selection-applied, not raw Ctrl+A, to clear a pre-populated field
type: feedback
---

## What happened

`pipeline_detail_page.py`'s `edit_node_name()` cleared a node's name field via
`name_input.press("Control+a")` then `press("Backspace")` then `.type(new_name)`.
On this dev machine (macOS, Chromium via Playwright), `Control+a` verifiably does
**not** select-all: direct DOM inspection right after the keypress showed
`selectionStart`/`selectionEnd` both unchanged from wherever the cursor already
was (position 9,9 on a 9-char value, i.e. no-op). Backspace then only deleted the
LAST character, so `Backspace` + `.type("approve")` on `"Printer 1"` produced
`"Printer approve"` instead of `"approve"` — the rename silently corrupted the id
(ELITEA-2033, 2026-08-04).

## Fix

Use the SAME reliable, OS-independent pattern already established elsewhere in
this file (`_fill_node_field_value`, used by the LLM-node section fields):

```python
name_input.select_text()
self._wait_for_field_selection_applied(name_input)  # polls selectionStart/End, not a sleep
name_input.press("Backspace")
name_input.type(new_name)
```

`Locator.select_text()` is a real Playwright API method, not a synthetic
keypress — it doesn't depend on the browser's/OS's keybinding table.

## Why this matters broadly

Any NEW method that needs to clear a pre-populated MUI text field is at risk of
copying the `press("Control+a")` pattern from older code in this file (it existed
in `edit_node_name` for a while, unnoticed, because nothing exercised a rename
where the char count shrank enough to make the corruption obvious). Grep for
`press("Control+a")` before trusting it works — verify via a live DOM read of
`selectionStart`/`selectionEnd` on this machine/browser combo if in doubt.
