---
name: MUI Switch data-testid lands on the SwitchBase span, carries Mui-checked
description: Passing data-testid as a prop to MUI Switch/BaseSwitch lands it on the inner SwitchBase <span>, which also carries the Mui-checked class — read state from the SAME element, no need to dig for the nested <input>.
type: feedback
---

## The situation

ELITEA-2042 (STATE panel per-row toggle testid). `BaseSwitch.jsx`
(`src/[fsd]/shared/ui/switch/BaseSwitch.jsx`) spreads `...restProps` onto the
underlying `<MuiSwitch>`. Passing `data-testid={...}` as a prop does NOT land
it on the outer `.MuiSwitch-root` span, nor directly on the `<input
type="checkbox">` — it lands on the `.MuiSwitch-switchBase` span (the
`SwitchBase` component's root), confirmed live via `outerHTML` capture. That
same span ALSO carries the `Mui-checked` class when the switch is on.

## Why it matters

This means a single `page.locator('[data-testid="..."]')` call gives you
both the click target AND the checked-state signal — no need to
`.locator("input")` into a nested element to read `checked`. Simpler
implementation:

```python
def is_state_variable_toggle_checked(self, name: str) -> bool:
    locator = self.page.locator(self.STATE_VARIABLE_TOGGLE.format(name))
    return "Mui-checked" in (locator.get_attribute("class") or "")
```

Verified live via `browser_evaluate` before writing the page-object method
(both direct class-string check AND `.locator("input").checked` agreed —
either works, but the class check avoids an extra nested-element hop).

## Reusable check

Before writing a `MuiSwitch`/`BaseSwitch` testid-state-read method, dump the
element's live `outerHTML`/`className` via a `browser_evaluate`/CDP probe
rather than assuming the testid lands on the root or that you need to reach
into a child `<input>` — confirm where React actually attached it first.
