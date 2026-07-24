---
name: A keydown-gate case naming specific navigation keys needs those exact keys pressed and asserted
description: When a case text says "navigation keys (Backspace/Arrow/Tab) remain functional" for an isValidKeyInput-style keydown allowlist, "the field still accepts a digit after a rejected keystroke" does NOT cover it — that only re-exercises the digit-gate branch. Each named navigation key needs its own direct press + a functional assertion proving it wasn't blocked.
type: feedback
---

## The gap (GAP-003, caught at review)

`ApplicationAdvanceSettings.jsx`'s `isValidKeyInput` has a `navigationKeys`
allowlist (`Backspace`, `Delete`, `Tab`, `Escape`, `Enter`, `Arrow*`, `Home`,
`End`) that returns `true` (no `preventDefault()`) for those keys, separately
from the digit-vs-clamp branch. The case text and `source.md`'s Automation
Notes both name this as its own coverage-target arm ("Navigation keys
(Backspace/Arrow/Tab) remain functional"). The first-pass test's Step 6 only
did: reject `a`/`b`/`-`, then type `"7"` and `"42"` to prove the field "isn't
stuck." **That proves the digit-gate branch recovers after a reject — it
proves NOTHING about Backspace/Arrow/Tab specifically.** The only incidental
touch of a navigation key was `clear_step_limit()`'s own `Delete` press,
buried in a helper method, never attributed to this requirement.

## Why "field still works afterward" doesn't substitute

"Digit typed after reject still works" and "named navigation key isn't
blocked" are different code paths in `isValidKeyInput` — the allowlist
check (`navigationKeys.includes(key)`) short-circuits BEFORE the digit/clamp
logic even runs. A bug that broke the navigation-keys allowlist specifically
(e.g. someone tightens `navigationKeys` to `['Backspace']` only, silently
dropping Tab/Arrow support) would ship green under "digit still works," and
red only under a direct Tab/Arrow assertion.

## The fix — press each named key, assert an effect specific to it

```python
# Backspace: an OBSERVABLE effect (char removed) proves it isn't blocked
detail_page.press_step_limit_key("Backspace")
assert detail_page.get_step_limit() == "2"   # was "25"

# ArrowLeft: prove the CARET actually moved — a following keypress lands
# BEFORE the remaining digit only if ArrowLeft wasn't blocked
detail_page.press_step_limit_key("ArrowLeft")
detail_page.press_step_limit_key("9")
assert detail_page.get_step_limit() == "92"  # not "29" — proves caret moved

# Tab: prove focus actually left the field — the standard Playwright
# assertion for this exact question
detail_page.press_step_limit_key("Tab")
expect(detail_page.step_limit_input).not_to_be_focused()
```

A NEW page-object method was needed for this: `type_step_limit()`/
`clear_step_limit()` both call `.click()` before pressing, and re-clicking
an already-focused text input can reset the caret to wherever the click
lands — which would silently break the ArrowLeft assertion (the "9" could
land at the click's position, not where ArrowLeft moved it, and the test
would pass or fail for the wrong reason). `press_step_limit_key(key)` —
just `self.step_limit_input.press(key)`, no click — preserves caret/focus
state across a sequence of calls.

## The general lesson

When a case names SPECIFIC keys/branches a keydown gate must allow through,
each one needs: (1) a direct press of exactly that key, (2) an assertion
whose truth is CONTINGENT on that specific key's allowed behavior (not just
"nothing broke") — pick an effect that could only be produced if the browser's
native/default handling for that key actually fired.
