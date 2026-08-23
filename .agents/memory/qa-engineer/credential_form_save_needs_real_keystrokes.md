---
name: Credential form Save is gated on formik dirty — fill() does not enable it
description: Playwright fill() on the credential Display Name sets the value but leaves formik non-dirty, so Save/Discard stay disabled; press_sequentially flips it
type: feedback
aliases: [credential save disabled, formik dirty, useFormDirtyExcluding, set_display_name]
tags: [area/credentials, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

`credential-form-save-button` is `disabled={hasErrors || shouldDisableSave}` and
`shouldDisableSave = !useFormDirtyExcluding()` (`CredentialsTabBar.jsx:115`).

Observed live 2026-08-23 (ELITEA-1981): filling every field of a SharePoint
create form with Playwright `fill()` — including Display Name, whose value the ID
field correctly mirrored — left **both** Save and Discard disabled. A single
`press_sequentially('x')` into Display Name enabled both immediately.

So `CredentialCreatePage.set_display_name()`'s select-all + type is load-bearing,
not stylistic. Do not "optimise" it to `fill()`, and if a create test mysteriously
can't click Save, check this before suspecting validation.

Related: [[mui_keepmounted_dialog_presence_is_not_open]]
