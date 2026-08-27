---
name: A hidden secret does not break its consumers — the field falls back to Password mode showing the NAME
description: Hiding a referenced secret leaves data.api_key untouched server-side; the UI shape change is intended
aliases: [hidden secret, hide secret, isHiddenSecret, secret fallback, hidden secret credential]
tags: [area/settings, area/credentials, type/product-behaviour]
created: 2026-08-28
updated: 2026-08-28
---

## The behaviour (verified live 2026-08-28, ELITEA-2345)

Hiding a secret that a credential references does **not** rewrite or null the
credential's stored reference. `GET /configurations/configuration/{project}/{id}`
still returns `"data": {"api_key": "{{secret.<name>}}", …}`.

What DOES change is the rendered shape — and it is **intended**, not a defect:

- the `api_key` field renders in **Password** mode
  (`…-toggle-password` `aria-pressed="true"`, combobox absent);
- the native `type="password"` input holds the literal secret **NAME**;
- the form is **not** dirtied — `credential-form-save-button` stays **disabled**
  on load, so nothing is silently rewritten client-side.

Source: `SecretField.jsx` —
`isHiddenSecret = isError || !data?.some(i => i.secret_name === value)`, and
`handleSwitchToSecretTab` only switches to the Secret tab
`if (isSecret && !isHiddenSecret)`.

## Oracles

- **Decisive:** `CredentialAPI.get_credential(id)["data"]["api_key"]` (added
  2026-08-28). `list_credentials` is a list projection — not guaranteed to carry
  `data`.
- **NEVER use `credential-form-test-connection-button`** on a synthetic
  credential: it fails for the fake host regardless of the hide, so it cannot
  distinguish "broken by hiding" from "fake host". A red there is a false defect
  signal.

## Two irreversibility facts that shape any test here

- **Hiding is irreversible via the UI** — there is no unhide affordance. So a
  test MUST create its own run-unique secret and hide THAT one; a fixed literal
  name works exactly once. The hidden row cannot be cleaned up (it stays
  invisible server-side, one per run) — that is inherent, not a leak to fix.
- **Always pair the absence assertion with a CONTROL** (a second, still-visible
  run-unique secret present in the SAME open dropdown, plus
  `saved_secret_options.count() > 0`). A dropdown that failed to load renders
  zero options and passes a bare absence check silently.

Related: [[shared_secretfield_handles_live_in_credential_create_page]]
