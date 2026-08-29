---
name: MUI required-field labels carry two asterisks — assert innerText
description: to_have_text on a `required` StyledInputEnhancer label reads "X * *" via textContent; pass use_inner_text=True
type: feedback
aliases: [required asterisk, Emails *, double asterisk, MuiFormLabel-asterisk, use_inner_text]
tags: [area/ui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

Any field rendered through `Input.StyledInputEnhancer` with `required` produces a
`<label>` holding **two** asterisks:

```html
<label ...><div><span>Emails *</span></div>
  <span aria-hidden="true" class="MuiFormLabel-asterisk" style="display:none"> *</span></label>
```

`StyledInputEnhancer` renders the visible `X *` itself, and MUI independently adds
its own hidden asterisk span. Playwright's `expect(...).to_have_text()` compares
**textContent** by default, which concatenates both:

```
AssertionError: Locator expected to have text 'Emails *'
Actual value: Emails * *
```

## The fix

```python
expect(page_obj.invite_emails_label).to_have_text("Emails *", use_inner_text=True)
```

`innerText` returns only what is rendered, which is also the observable a layout
case actually means ("marked as required with *").

## Where it bit

ELITEA-2295 (Settings -> Users, Invite-users dialog, `users-invite-emails-label`),
2026-08-29. Expect the same on any other `required` StyledInputEnhancer field —
this is a component-level fact, not a Users-page one.

Related: [[project_switch_race_settings_users]]
