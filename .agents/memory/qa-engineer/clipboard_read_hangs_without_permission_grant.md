---
name: Clipboard read hangs without permission grant
description: navigator.clipboard.readText() hangs forever in a context without clipboard-read granted — not a product bug
type: feedback
---

## What happened

While analysing ELITEA-2280 (Personal Tokens — create + copy-to-clipboard),
an exploratory Playwright MCP `browser_evaluate` call did
`await navigator.clipboard.readText()` to verify the Copy button actually
placed the token on the clipboard. The call **hung for the full 1800s MCP
idle timeout** — no error, no rejection, just silence — because the MCP
browser's context was never granted the `clipboard-read` permission. The
browser was silently waiting on a permission prompt that a headless/MCP
context never shows.

## The fix / the pattern

Grant the permission **at context creation**, not at call time:

```python
context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
```

`automation/conftest.py`'s `context` fixture (line ~279) already does this
for the whole pytest suite — so `page.evaluate("navigator.clipboard.readText()")`
is safe inside any real test. The hang only bites **ad-hoc/scratch browser
sessions** — a bare Playwright MCP call, a manual script, an isolated CLI
session — that weren't created with the grant.

## Why this matters going forward

If a clipboard-related test assertion ever times out, **check the calling
context's granted permissions first** before assuming a product regression
in the copy-to-clipboard feature. This is a framework/environment gotcha,
not evidence of a broken Copy button — confirmed live the Copy button and
the underlying `handleCopy()` call both work correctly; only the *read-back
verification* needs the permission grant to not hang.
