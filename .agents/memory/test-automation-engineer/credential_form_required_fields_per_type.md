---
name: Credential create form — required-field set differs per credential type
description: Which fields gate the Save button on /credentials/create-credential/{type}; github can never be gated by an auth field, jira/confluence can
type: reference
---

Captured live on `dev.elitea.ai` (deployed EliteaUI `main`) 2026-08-28 by reading
`input.required` off each form's DOM (#1897 / ELITEA-1140 repair brief § Finding 3).

| type | required fields | can a missed auth field disable Save? |
|---|---|---|
| github | `label`, `elitea_title`, `base_url` — **`base_url` ships pre-filled** | **No** — Save enables after Display Name alone; Access Token is `required: false` |
| jira | `label`, `elitea_title`, `base_url`, `username` | **Yes** |
| confluence | `label`, `elitea_title`, `base_url`, `username` | **Yes** |
| gitlab | `label`, `elitea_title`, `url` | yes (param currently skipped) |
| bitbucket | `label`, `elitea_title`, `url`, `username` | yes (param currently skipped) |

`api_key` / `access_token` / `private_token` / `password` are `required: false`
on **every** form.

This is why a parameterized create-credential test can fail on `[jira]` and
`[confluence]` while `[github]` passes in the same run — it is not luck and it is
not a product asymmetry, it is the required-field set.

## Secret field names differ per type (tracked as #1936)

`toolkit-field-api_key-input-field` is jira/confluence only. GitHub's is
`access_token`, GitLab's is `private_token`, Bitbucket's is `password` — a
helper that hardcodes `name="api_key"` for all of them is wrong for three of
five types.

## Page object

`pages/credential_create_page.py` (`CredentialCreatePage`, testid-only) already
covers all of it: `navigate_to_type()`, `set_display_name/base_url/username/
api_key/access_token()`, `select_auth_method()`, `save_button`. Prefer it over
raw `get_by_role` fills — the setters use `press_sequentially(delay=20)`, which
is React-safe where the deprecated `.type()` is not.
