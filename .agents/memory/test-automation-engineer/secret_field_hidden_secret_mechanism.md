---
name: SecretField behaviour when its bound secret is hidden
description: A credential bound to {{secret.X}} silently drops to Password mode when X is hidden — the stored value is untouched
type: reference
aliases: [hidden secret credential, isHiddenSecret, SecretField secret mode, secret dropdown absence]
tags: [area/settings-secrets, area/toolkits-credentials]
created: 2026-08-28
updated: 2026-08-28
---

## Source-read mechanism (NOT yet live-confirmed)

`EliteaUI/src/[fsd]/shared/ui/secret-field/SecretField.jsx` (read 2026-08-28
while triaging ELITEA-2345/2346):

- `savedSecretsOptions` is built purely from `useSecretsListQuery(projectId)` →
  `GET /api/v2/secrets/secrets/default/{project_id}`. Hiding a secret removes it
  from that list (the Secrets table reads the same endpoint), so a hidden secret
  simply **cannot** appear as a `select-option-{{secret.<name>}}` in ANY
  secret-mode dropdown. That is the whole mechanism behind
  "hidden secret absent from the secret selection dropdown".
- `isHiddenSecret = isError || !data?.some(i => i.secret_name === value)` (line 128).
  `handleSwitchToSecretTab` only flips the field to Secret mode when
  `isSecret && !isHiddenSecret`. So a saved credential whose field holds
  `{{secret.X}}` where X is now hidden **stays in Password mode** and
  `updateRawPassword` puts the *bare secret name* (regex capture group of
  `/^{{secret\.([A-Za-z0-9_]+)}}$/`) into the password input.
- Nothing in this path mutates the credential. The persisted value stays
  `{{secret.X}}` — the honest oracle for "the credential is not broken" is the
  readback `GET /configurations/configuration/{project}/{id}`, not the UI mode.

## Product gaps found the same session

- **There is no "AI Configuration" page and no "+" to create a model
  configuration.** `/settings/ai-providers` renders `ConfigurationsPanel.jsx`
  with zero add/create affordance (grepped: no `addButton`, no create handler).
  ELITEA-2346's step 2 as written has no product counterpart.
- Hiding is irreversible (no un-hide UI, per the secrets digest). Any test that
  hides must use a run-unique secret it created itself, and permanently accretes
  one hidden secret per run in the shared project unless DELETE-by-name still
  works on a hidden secret (unproven).
