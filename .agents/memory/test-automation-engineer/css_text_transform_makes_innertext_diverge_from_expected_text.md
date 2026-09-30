---
name: CSS text-transform makes innerText diverge from the string to assert
description: to_have_text compares textContent, so a case text quoting the UPPERCASE rendering must still be asserted in source casing
type: feedback
aliases: [text-transform uppercase, DOCUMENTATION vs Documentation, to_have_text casing, innerText uppercase, case text uppercase]
tags: [area/playwright, type/gotcha]
created: 2026-09-30
updated: 2026-09-30
---

## The trap

A TMS case quotes what the tester SAW — `DOCUMENTATION`, `RELEASE NOTES`. If that
uppercase comes from CSS `text-transform: uppercase` (very common on MUI typography
variants like `variant="subtitle"`), the DOM never contains those characters:

```
textContent : 'Documentation'      <- what expect(...).to_have_text() compares
innerText   : 'DOCUMENTATION'      <- the CSS-rendered form the case text quotes
computed text-transform: 'uppercase'
```

Verified live 2026-09-30 on `help-center-card-documentation-title`:
`to_have_text('Documentation')` **PASSES**, `to_have_text('DOCUMENTATION')` **FAILS**.

## The rule

Assert the **source** casing, and say why in a comment — otherwise the next reader
"fixes" it to match the case text and turns a green assertion red. The uppercase in the
case text is not a different string; it is the same string with a style applied.

Cheap probe before writing the assertion:

```python
print(loc.text_content(), loc.inner_text(), loc.evaluate("e => getComputedStyle(e).textTransform"))
```

Same root cause family as [[negative_text_wait_needs_use_inner_text]] (Playwright text
matchers read `textContent`), but the divergence here is **CSS**, not child-node
separators — and it bites a POSITIVE assertion, where that entry covers a negative wait.
`use_inner_text=True` would let you assert the uppercase form, but source casing is the
better contract: it survives a restyle that is not a behaviour change.
