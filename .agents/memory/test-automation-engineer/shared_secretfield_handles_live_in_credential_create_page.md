---
name: Shared SecretField handles live in CredentialCreatePage — reuse it, don't duplicate
description: The vault-dropdown handles work verbatim on credential detail AND Settings→AI Providers forms
type: reference
aliases: [secret field, secret vault dropdown, toolkit-field-api_key-input, AI provider secret dropdown]
tags: [area/credentials, area/settings, type/page-object]
created: 2026-08-28
updated: 2026-08-28
---

## The fact

`src/[fsd]/shared/ui/secret-field/SecretField.jsx` renders EVERY secret field in
Elitea, so the derived testids are identical on all three call sites:

1. `/credentials/create-credential/<type>` (create credential)
2. `/credentials/all/<id>` (edit credential)
3. `/settings/create-ai-provider/<type>` (new AI provider)

Handles: `toolkit-field-{key}-input`, `-input-field` (native password input,
Password mode only), `-input-toggle-secret` / `-toggle-password` (read
`aria-pressed`), `-input-combobox` (Secret mode only),
`select-group-header-Create` / `-Saved Secrets`,
`select-option-{{secret.<name>}}`.

**All of them already live in exactly one page object:
`automation/pages/credential_create_page.py`** (`secret_toggle()`,
`secret_combobox()`, `open_secret_dropdown()`, `saved_secret_option()`,
`saved_secret_options`, the two group-header properties).

## What to do

Instantiate `CredentialCreatePage(page)` for the secret-field block even on a
NON-credential surface (an AI-providers spec, the credential detail route) and
say so in the docstring. Do **not** re-declare those testids on another page
object — one testid, one file (`.agents/conventions.md`).

Verified 2026-08-28 on ELITEA-2345 (detail route) and ELITEA-2346 (AI-provider
form); both green first run.

## The known cleaner end state (not done — flagged to the lead)

Promote the block to `CredentialFormFieldsMixin` (the pattern that file already
used for `FIELD_INPUT` / `AUTH_METHOD_RADIO` / `test_connection_button`) or
extract `automation/components/secret_field.py`. Either is a **non-additive**
edit to a page object with ~20 merged callers, so it needs the shared-file
regression protocol — not a case PR.

## Two gotchas that ride along

- **The field always starts in PASSWORD mode.** The combobox does not exist in
  the DOM until `…-toggle-secret` is clicked. Any case saying "open the secret
  dropdown" needs that hop; the TMS case texts omit it.
- **Flipping the toggle dirties the form**, so leaving the route raises a native
  `beforeunload` dialog that hangs `page.goto()`. One
  `page.on("dialog", lambda d: d.accept())` at the top of the test is enough.

Related: [[hidden_secret_fallback_renders_password_mode_with_the_name]]
