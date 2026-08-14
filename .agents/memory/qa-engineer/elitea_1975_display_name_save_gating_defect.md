---
name: ELITEA-1975 Display Name Save-gating defect
description: Create-Credential form's Save button doesn't re-disable when Display Name (label) is cleared, though it correctly re-disables for every other required field — root cause in validateRequiredFields() only checking schema.required, which never includes label/elitea_title
type: feedback
---

## What happened

Analyzed ELITEA-1975 (Create Credential — Required Fields Validation) against
the live Create-Credential form (`/credentials/create-credential/{type}`,
localhost:5173). Found a confirmed, reproducible (2/2, two fresh page loads,
native Playwright `.fill()` only) defect: clearing the Display Name field
after all required fields were filled does **not** re-disable the Save
button, while clearing any other required field (Base Url, Api Key,
Username on Jira type) correctly does. Filed as GitHub issue #526.

## Root cause (source-confirmed)

`EliteaUI/src/[fsd]/features/toolkits/lib/helpers/toolBase.helpers.js`'s
`validateRequiredFields()` only iterates `schema.required` — the
type-specific config schema (e.g. Jira's `base_url`/`api_key`/`username`).
The generic `label` (Display Name) field is never part of any credential
type's `schema.required`, so it never gets a `toolErrors.label` entry.
`CredentialTabBar.jsx`'s Save-disable logic
(`hasErrors || shouldDisableSave`, line 223) never sees Display Name as
invalid. The disabled auto-derived `elitea_title` (ID) field is *also*
explicitly excluded from this validation while auto-managed
(`enableEditEliteaTitle || prop !== 'elitea_title'` filter, same helper).

## Credential-type selection gotcha for this case family

GitHub credential type's `Base Url` field ships with a live default
(`https://api.github.com`) already populated — so testing "fill only
Display Name → Save stays disabled" against GitHub type gives a **false
result** (Save enables immediately, since Base Url already counts as
filled). Use **Jira type** instead — all three of its required fields
(`Base Url *`, `Api Key *`, `Username *`) start genuinely empty with no
default. This is a case-authoring ambiguity, not a product bug — flagged as
a CLARIFICATION in the AFS, not filed separately.

## Testids already live (per EL-1971 landing)

`credential-form-save-button` and `toolkit-type-card-{type}` (e.g.
`toolkit-type-card-github`) are confirmed live on `automation/testids` —
no `add-data-testid` round-trip needed for a future automated version of
this case. Field testids follow the existing
`toolkit-field-{k}-input`/`toolkit-field-{k}-input-field` pattern (the
`-input-field` variant applies to secret/password-toggler-wrapped fields
like Jira's `api_key`).

## AFS

`test-specs/toolkits-credentials/l1_create-credential-required-fields-validation_ELITEA-1975.md`
