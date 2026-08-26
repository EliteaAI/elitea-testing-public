---
name: SecretField vault dropdown (Secret/Password toggle)
description: How the credential/toolkit secret field's Secret-mode vault dropdown behaves and which handles it exposes
type: project
aliases: [secret field, secret password toggle, saved secrets dropdown, vault dropdown, select-group-header]
tags: [area/credentials, area/toolkits, type/handles]
created: 2026-08-22
updated: 2026-08-22
---

## What it is

`EliteaUI/src/[fsd]/shared/ui/secret-field/SecretField.jsx` — rendered for every
schema property marked secret (GitHub `access_token` under Token auth, Jira/
Confluence `api_key`, …). Two mutually-exclusive modes behind a
`ToggleButtonGroup`; **`password` is the default**.

| Mode | Element | Handle |
|---|---|---|
| password | native `<input type="password">` | `toolkit-field-{key}-input-field` |
| secret | MUI Select over the project vault | `toolkit-field-{key}-input-combobox` |

Toggle buttons: `toolkit-field-{key}-input-toggle-{secret,password}` — carry
`aria-pressed`, so mode state is assertable testid-only.

## Traps that each cost a run

- **Group headers render BEFORE the vault list resolves.** `useSecretsListQuery`
  is `skip`-gated on the mode, so the menu opens with `select-group-header-Create`
  / `select-group-header-Saved Secrets` present and an EMPTY body. Wait on the
  first saved-secret OPTION. `networkidle` is unusable on credentials routes.
- **Assert the headers' underlying strings** `Create` / `Saved Secrets`. The
  all-caps rendering is CSS `text-transform`; Playwright `to_have_text` reads
  `textContent` and never sees it — but a browser-console `innerText` probe DOES
  return `CREATE` / `SAVED SECRETS`, which is how you get it wrong.
- **Switching modes CLEARS the value** (`handleToggleTab`).
- **The CREATE option's label is project-scope-dependent**:
  `personal_project_id === selectedProjectId ? 'New Private Secret' : 'New Project Secret'`.
  Testid `select-option-__create_private_secret__` is the same in both.
- **Clicking the CREATE option opens a NEW TAB** —
  `window.open('/{projectId}/settings/secrets?createSecret=1', '_blank')`.
  `?createSecret=1` auto-opens the inline create row and disables `secrets-add-button`.
- **The dropdown does NOT close after a create-action click** (#1047
  `skipNextCloseRef`) — convenient, but assert it rather than assume it.
- A saved option's value is `{{secret.<name>}}`; the combobox displays the bare
  name. The bound value lives on MUI's hidden `MuiSelect-nativeInput`, which has
  **no testid** and cannot get one via `SingleSelect`'s `inputProps` pass-through
  (tried live, reverted) — would need `slotProps.htmlInput`.

Related: [[daily/2026-08-22]] · `test-specs/toolkits-credentials/_surface.md`
