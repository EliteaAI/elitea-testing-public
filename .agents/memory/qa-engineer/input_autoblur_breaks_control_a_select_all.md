---
name: Input.InputBase autoBlur breaks Control+a select-all
description: MUI Input.InputBase's default enableAutoBlur refocuses ~10ms after each keystroke, racing Control+a and silently resetting cursor to position 0 — use Home+Shift+End instead
type: feedback
---

## The situation

While analyzing ELITEA-2286 (Personal Tokens create-form Name-field
validation), tried to clear a filled `Input.InputBase` field (project's
shared MUI TextField wrapper, `src/[fsd]/shared/ui/input/InputBase.jsx`)
via `Control+a` then `Backspace`/`Delete`, live via Playwright MCP. The
field's text was NOT cleared — only a single leading character was removed
(`"my token"` → `"y token"`), as if the selection never happened and the
cursor was sitting at position 0.

## Root cause

`InputBase.jsx`'s `enableAutoBlur` prop defaults to `true`. Its `onChange`
handler calls `useAutoBlur()`'s returned function after every keystroke,
which does:

```js
timerRef.current = setTimeout(() => {
  document.activeElement.blur();
  document.activeElement.focus();
}, 10);
```

This is a REAL DOM blur+refocus cycle (used to touch Formik fields for
validation, not a rendering artifact) that fires ~10ms after every change.
If a `Control+a` keypress lands during or shortly after this refocus, the
selection is lost and the cursor resets — the exact race observed live.

## The fix

Use a keyboard-only line-select instead of the modifier-key shortcut:

```python
locator.click()
page.keyboard.press("Home")
page.keyboard.press("Shift+End")
locator.press_sequentially(new_text, delay=20)
```

`Home` + `Shift+End` reliably selects the full line without depending on a
modifier combo that can race the autoBlur timer; typing over the selection
replaces it in one step. Confirmed live, ELITEA-2286 AFS exploration
session, 2026-08-05.

## Why this is preventive beyond this one case

`Input.InputBase` is the shared text-input wrapper used across the whole
EliteaUI app (not just Personal Tokens) — `enableAutoBlur` defaults `true`
everywhere it's used without an explicit override. Any future analyst/
implementer session that needs to CLEAR an already-filled field built on
this component (not just type into an empty one) will hit the same
`Control+a` unreliability unless warned first.

Same root cause is also WHY validation errors on these fields appear
without any explicit blur/Tab step — the auto-blur cycle is what sets
Formik's `touched.<field>` as a side effect. Don't add a defensive extra
blur step "just in case"; it's already happening automatically within
~10ms, well inside Playwright's default `expect()` polling window.
