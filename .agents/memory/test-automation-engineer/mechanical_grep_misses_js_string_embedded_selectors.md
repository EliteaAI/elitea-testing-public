---
name: Mechanical grep misses JS-string-embedded selectors
description: The reviewer's/self-check locator grep only matches Python .locator(/get_by_* calls — a raw querySelector baked into a page.wait_for_function() JS string is invisible to it.
type: feedback
---

## What happened

`PipelineDetailPage.confirm_fork_complete()` (ELITEA-2051) used
`self.page.wait_for_function("""(expected) => { const el =
document.querySelector('[data-testid="copy-id"]'); ... }""", ...)` to poll for
a stale-copy-id race after the Fork "Got it" navigation. This duplicated the
existing `copy_id_button` `LocatorDescriptor` field via a raw selector — a
policy violation — but it survived the implementer's own self-check AND round
1 of review because both used the standard mechanical grep:

```
git diff ... | grep -nE '^[+].*(get_by_role|get_by_label|get_by_text|...|page\.locator|\.locator\()'
```

That pattern only matches **Python** locator calls. A `document.querySelector`
sitting inside a triple-quoted JS string passed to `page.evaluate()` /
`page.wait_for_function()` doesn't contain `.locator(` or `get_by_*` — it's
just a string literal to the grep. Zero hits, but the raw handle is very much
there.

## Fix pattern

Where the observable can be expressed as a plain Playwright assertion, prefer
`expect(locator).to_have_text(...)`/`to_have_attribute(...)`/etc. over
`wait_for_function` entirely — it's both simpler and keeps the handle in
Python where the grep (and everyone reading the diff) can see it:

```python
from playwright.sync_api import expect
expect(self.copy_id_button).to_have_text(str(forked_pipeline_id), timeout=timeout)
```

`wait_for_function` is still the right tool for genuinely JS-only conditions
(polling multiple computed properties, a condition no Playwright assertion
expresses) — but even then, build the selector from a `LocatorDescriptor`'s
underlying testid string / a class-level `[data-testid=` constant referenced
in a comment, and grep the DIFF FOR `document.querySelector\(` /
`querySelectorAll\(` too when self-checking a page object that uses
`wait_for_function`/`evaluate`. The standard grep pattern doesn't cover this
by itself.

## Broader lesson

Before claiming "mechanical grep: 0 hits" on a page-object diff that contains
ANY `wait_for_function`/`evaluate` block, also grep that diff for
`querySelector`/`querySelectorAll` as a second pass — the two greps cover
different surfaces (Python locator API vs raw JS DOM API) and neither
substitutes for the other.
