---
name: JSX text apostrophe encoding — &apos; renders as U+0027 not U+2019
description: When asserting inner_text() of JSX elements using &apos;, Python expected constants must use straight apostrophe U+0027, not curly U+2019
type: feedback
---

## The pattern

When a JSX element contains HTML entity `&apos;` (e.g. `We&apos;re`, `it&apos;ll`, `let&apos;s`),
Playwright's `inner_text()` returns the rendered text with **straight apostrophe U+0027**,
not the RIGHT SINGLE QUOTATION MARK U+2019.

If the Python expected string constant was written with curly/smart apostrophes (U+2019) —
which happens silently from macOS auto-correct, editor smart-quote conversion, or copy-paste
from rendered text — the assertion fails with a confusing diff where the characters look
the same visually.

## Diagnostic

```python
# Detect the issue before running the test:
s = _EXPECTED_BODY_TEXT
for i, ch in enumerate(s):
    if ord(ch) in (0x0027, 0x2018, 0x2019):
        print(f"[{i}] {ch!r} = U+{ord(ch):04X}")
```

Expected output (correct): U+0027 at apostrophe positions.
Problem output: U+2019 at apostrophe positions.

## Fix

Replace U+2019 → U+0027 in the Python source constant. One-liner:

```python
path = "tests/ui/onboarding/test_onboarding_welcome.py"
src = open(path).read()
open(path, "w").write(src.replace("’", "'"))
```

Or with `Edit` tool: use the old_string with the curly apostrophe (U+2019 character)
and new_string with the straight apostrophe (U+0027).

## Also: em dash is fine

The literal `—` (U+2014) in JSX source renders as U+2014 in `inner_text()`. Only `&apos;`
(→ U+0027) and similar named/numeric HTML entities need attention. The `&amp;`, `&lt;`,
`&gt;` entities render as `&`, `<`, `>` respectively — use those literal chars in constants.

## Origin

ELITEA-2231 onboarding welcome page, 2026-08-14. _EXPECTED_BODY_TEXT had U+2019 (curly)
at positions 2 and 45 (the two `'` apostrophes), causing Step 5 assertion failure despite
the test logic being correct. Fixed before first green run.
