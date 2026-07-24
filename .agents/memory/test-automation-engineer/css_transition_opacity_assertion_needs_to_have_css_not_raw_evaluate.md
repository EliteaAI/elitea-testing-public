---
name: A CSS-transitioned style property needs to_have_css, not a raw evaluate() read right after the triggering click
description: GridTableHeader.jsx's active-header opacity indicator animates via `transition: opacity 0.2s ease` — reading getComputedStyle() immediately after the click that activates it can catch a mid-transition value; Playwright's own auto-retrying expect(locator).to_have_css() waits it out for free.
type: feedback
---

GAP-035 (artifacts file-table column-header sort): the AFS's own § Concrete
Handles section suggested asserting a header cell's "active" state by reading
its computed `opacity` via `getComputedStyle()`/Playwright `evaluate()` —
`GridTableHeader.jsx`'s `styles.headerCell(isActive, ...)` sets
`opacity: isActive ? 1 : 0.7` on the same Box that carries the testid.

R1 built exactly that: a page-object method
(`get_column_header_opacity(header) -> float`) wrapping
`header.evaluate("el => window.getComputedStyle(el).opacity")`, called once
right after `click_column_header()`. It failed non-deterministically-looking
but was actually deterministic given timing: the assertion caught
`opacity=0.707665` instead of the expected `1.0` — barely a few milliseconds
into the SAME element's own `transition: opacity 0.2s ease`. Row order
(read via `get_file_names()`, a live DOM structural read) settled fine in the
same window; only the *animated* CSS property was still mid-flight.

**Fix:** drop the custom evaluate-based method and helper float entirely.
Assert directly on the `LocatorDescriptor` field from the test with
Playwright's own auto-retrying CSS assertion:

```python
expect(artifacts_page.name_column_header).to_have_css(
    "opacity", "1", timeout=UI_ELEMENT_TIMEOUT,
)
```

`to_have_css` polls the computed style until it matches (or times out) —
the exact condition-based-wait idiom this project's Hard Rule 5 (no sleeps,
framework-native waits only) already mandates, just not one I'd reached for
before for a plain numeric CSS property. No custom page-object method
needed at all; the field is used directly, matching the codebase's existing
convention of calling `expect(artifacts_page.some_locator).to_be_enabled()`
etc. straight from spec files.

**Generalizable takeaway:** any assertion on a CSS property that has its own
`transition`/animation on the SAME element the click just mutated is a race
risk for a one-shot `evaluate()` read, no matter how synchronous the
underlying React state update looks. Reach for `expect(locator).to_have_css(name, value)`
first — it's strictly more correct AND less code than a custom
evaluate-plus-`pytest.approx()` helper, and it removes an entire class of
"opacity/color/transform sampled mid-animation" flakes before they can occur.
Cross-reference: `mui_patterns.md`'s documented fixed-wait workarounds for
CSS transitions/animations are the OLDER, pre-`to_have_css`-idiom answer to
the same problem — reach for the auto-retrying assertion instead when the
thing you're waiting on is itself a CSS property (not, say, a modal's
opening animation gating a subsequent unrelated interaction).
