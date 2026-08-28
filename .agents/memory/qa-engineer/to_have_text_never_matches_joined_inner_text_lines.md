---
name: to_have_text compares textContent with NO separators — joining inner_text lines makes the assertion vacuous
description: not_to_have_text(" ".join(lines)) can never match a multi-child element, so the "wait until it changes" helper silently waits zero time
type: feedback
aliases: [not_to_have_text no-op, wait for text change, elementText concatenation, tooltip settle wait, useInnerText]
tags: [area/playwright, type/assertion-strength]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

`expect(locator).to_have_text("...")` / `not_to_have_text("...")` read the element with
**`elementText()`**, not `innerText` — verified in the shipped driver bundle
(`playwright/driver/package/lib/coreBundle.js`):

```js
} else if (expression === "to.have.text") {
  received = options.useInnerText ? element.innerText : elementText(new Map(), element).full;
```

and `elementText()` concatenates child element text with **no separator at all** (no space, no
newline) — it only appends `child.nodeValue` for text nodes and recurses into elements.

So for a container of block/flex children (a Recharts `ChartTooltip`: label + one line per series):

- `inner_text()` -> `"2026-08-06\nLLM Calls: 5\nTool Runs: 0"` (CSS-aware, line-broken)
- `to_have_text` sees -> `"2026-08-06LLM Calls: 5Tool Runs: 0"`

`not_to_have_text(" ".join(inner_text_lines))` therefore compares two strings that can **never**
be equal, so the negative assertion passes on its **first poll**. A helper built on it as a
"wait until the content changes" settle is a **no-op**: it returns instantly and the caller reads
whatever is on screen at that microsecond.

Failure mode is a flake, not a false green (the caller still asserts what it changed *to*), which
is exactly why it survives a green run and a 3x gate.

## The compliant shapes

- `not_to_have_text("".join(previous_lines))` — matches `elementText` concatenation, or
- pass a `re.Pattern`, or
- `expect(locator).not_to_have_text(previous_text, use_inner_text=True)` if the innerText form is
  what you want to compare.

Whichever you pick, **prove it can match** — a negative assertion whose expected value is
unreachable is indistinguishable from a passing wait.

Related: [[inner_text_is_css_aware_use_text_content_for_dom_labels]]
