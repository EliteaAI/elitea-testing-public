---
name: Credentials console-noise filters #518/#554 name CLOSED issues as OPEN
description: Both console filters the credentials specs copy forward point at issues closed 2026-08-11 — one of them masks a crash of the component under test
type: feedback
aliases: [is_known_518_warning, is_known_554_warning, credentials console filter, CredentialsList crash filter, prompt_lib 404 filter]
tags: [area/credentials, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The fact (verified 2026-08-22 via `gh issue view`)

Every credentials spec (`test_credential_create.py`, `test_credential_delete.py`,
`test_credential_search_by_name.py`, and now ELITEA-1966/1973) copies forward two
console-noise filters whose docstrings assert the issues are **OPEN**. Both are
**CLOSED**:

- **#518** — "Credentials list page crashes intermittently: 'Cannot refetch a query
  that has not been started yet'" — closed `COMPLETED` 2026-08-11, reason
  **NOT REPRODUCIBLE** (22 attempts, 0 repros). The filter swallows a React
  error-boundary crash of `<CredentialsList>` — the component every credentials
  spec is testing. If it fires now it is a **regression**, not noise, and the
  filter makes the test green anyway. Treat a new copy of this filter as masking.
- **#554** — prompt_lib 404 — closed 2026-08-11 with the product owner's verdict
  "reproducible only on local UI / test-client artifact, not a backend defect,
  no action items needed". Filtering it is defensible; the "OPEN" label is not.

## Reviewer move

Don't accept "already-filed, OPEN #N" in a console-filter docstring at face value —
`env -u GITHUB_TOKEN gh issue view <n> --repo EliteaAI/elitea-testing-public --json
state,stateReason` costs one call. A filter for a closed-as-not-reproducible defect
is a weakened assertion pointing away from a defect, and the precedent argument
("three merged specs do it") is convention, not authority (`role-overrides.md`
§ precedent is not authority).

## Round-2 addendum (2026-08-22) — the second, structural #518 vector

Removing the console filter is only half of it. `CredentialsListPage.navigate()`
calls `recover_from_credentials_list_crash()` (`pages/credentials_list_recovery.py`),
which detects the "Unexpected Application Error!" boundary and silently **reloads**
— premised on the same closed #518. It does not hide the crash from a spec whose
console listener is attached *before* `navigate()` (the console error still fails
the side-channel assert), but any spec that attaches later, or has no console
assertion at all, goes green through a real crash. Two merged specs
(`test_credential_create.py:53`, `test_credential_delete.py:40`) still carry the
`_is_known_518_warning` filter as well. Suite-health follow-up, not a per-case
blocker: when reviewing a credentials spec, check BOTH vectors.
