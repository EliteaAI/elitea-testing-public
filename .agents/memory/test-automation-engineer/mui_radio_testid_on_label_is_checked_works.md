---
name: MUI radio testid on label — is_checked() still works
description: Playwright's Locator.is_checked() resolves correctly on a MUI FormControlLabel data-testid even though the testid sits on the <label> wrapper, not the nested <input type="radio">/<input type="checkbox"> — no unwrap or raw-selector chaining needed
type: feedback
---

## What

EliteaUI's `RadioButtonGroup.jsx` (and other MUI `FormControlLabel`-based
controls) put `data-testid` on the outer `<label>` element:

```html
<label data-testid="toolkit-field-auth-radio-token" class="MuiFormControlLabel-root">
  <span class="MuiRadio-root">
    <input type="radio" value="Token" ...>
    ...
  </span>
  ...label text...
</label>
```

Naively this looks like a problem: Playwright's `Locator.is_checked()` docs
say it "throws if the element is not a checkbox or radio input," and the
testid-located element is a `<label>`, not the `<input>` itself.

## What actually happens (live-verified, ELITEA-1962)

`page.get_by_test_id("toolkit-field-auth-radio-token").is_checked()` works
correctly — returns `False` before click, `True` after. Verified with a
standalone script against the real page:

```python
radio = page.get_by_test_id("toolkit-field-auth-radio-token")
radio.is_checked()   # False
radio.click()
radio.is_checked()   # True
```

Playwright's `is_checked()` implementation walks to the associated form
control when the target is a `<label>` (same mechanism the browser uses to
resolve label-click-to-toggle-input). No unwrap, no `role="radio"` /
`aria-checked` needed on the label itself.

## Why this matters

Under this project's testid-only locator policy (no fallback rung), the
temptation when a testid lands on a wrapping `<label>` instead of the raw
`<input>` is to either (a) chain a raw CSS selector off the testid-located
element to reach the real `<input>` (`self.field.locator("input")` —
explicitly forbidden by `.claude/rules/page-objects.md`'s "no raw selector
chained off an existing field" rule) or (b) escalate for a new testid on the
input itself. Neither is needed for checked-state assertions — test first
before assuming a workaround is required.

## Where reused

`automation/pages/credential_create_page.py::CredentialCreatePage.auth_radio()`
— `assert create_page.auth_radio("token").is_checked()` in
`test_credential_create.py` (ELITEA-1962). Applies to any MUI
`FormControlLabel`-wrapped radio/checkbox where the testid sits on the label
(check with a quick outerHTML dump before assuming a raw-selector escalation
is needed).
