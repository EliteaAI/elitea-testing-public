---
name: Elitea AI-provider form — secret-field, delete-dialog and section-protection traps
description: Four live-verified traps on Settings -> AI Providers create/edit forms that each cost a turn or would silently corrupt a project
type: reference
aliases: [pgvector, connection string, SecretField, delete-confirm-name-input, isLastInSection, vector storage undeletable, toolkit-field-connection_string]
tags: [area/settings-ai-providers, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## 1. A testid on a MUI TextField root is NOT on the input

Two live instances on this surface, same shape, different fixes:

- `toolkit-field-connection_string-input` is a **DIV** (the TextField root). The native
  `<input type="password">` is `…-input-field`, derived by `SecretField.jsx:77`
  (`` `${inputProps['data-testid']}-field` ``). Type into the `-field` one. Same
  derivation gives `-helper-text` (:88) and `-toggle-{secret,password}` (:342).
- `delete-confirm-name-input` (shared `DeleteEntityModal`) is also a DIV wrapper.
  `AiProviderFormPage.delete_current_configuration()` works only because it **clicks
  the wrapper first** (MUI focuses the inner input) before `press_sequentially`. A bare
  `fill()`/`press_sequentially` types nowhere and the Delete button stays disabled.

Generalisation: when a `-input` testid resolves to a DIV, look for a derived `-field`
sibling before reaching for a raw CSS chain — this app derives one consistently.

## 2. A direct `goto` to a schema-driven create route can silently WIPE an early fill

`/settings/create-ai-provider/{type}` fetches `GET /configurations/available/?section=…`
and **remounts** the form. A Display Name typed in that gap read back **empty** and Save
stayed disabled. Sharper than the known "wait for the field" note: the field can already
be present and still lose the value. If a value reads back empty right after a goto,
**re-fill** rather than hunt for a typo.

## 3. `isLastInSection` — the first Vector Storage in a project is permanently undeletable

`CredentialsControls.jsx:51,63`: `isProtectedSection = section === 'vectorstorage' ||
section === 'embedding'`; delete is disabled when `own total + shared total <= 1`.
Embedding has 3 **shared** configs so it never bites. **Vector Storage has none**, so
0 -> 1 cannot be undone through the UI. Any spec creating a vector storage must guard
that the section is already non-empty, or a failing run leaves permanent residue.
Project 400 now carries a deliberate seed `Autotest PGVector Seed`.

## 4. Default-selector option keys are NOT uniform across sections

`select-option-{key}<<>>{project_id}` — `{key}` is `data.name` for LLM/embedding/image/
ASR/TTS but **`elitea_title`** for vector storage (pgvector configs have no `data.name`;
the API returns `"name": null`). Same mismatch is the root cause of the missing
`Default` badge on vector-storage cards (#1987). Also: renaming a vector storage
re-derives and **persists** a new `elitea_title`, so its option testid changes — never
cache one across an edit. Conversely, a duplicate model `name` is safe because the
`<<>>{project_id}` half disambiguates.

Related: [[elitea_settings_ai_providers]]
