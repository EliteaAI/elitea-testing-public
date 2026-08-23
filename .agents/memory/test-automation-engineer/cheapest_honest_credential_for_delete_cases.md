---
name: Cheapest honest credential to create in a UI test
description: Github type + Display Name only — Save enables with no token, so no GIT_HUB_TOKEN dependency and no secret typed
type: feedback
aliases: [create credential without token, credential test data, GIT_HUB_TOKEN skip]
tags: [area/credentials, type/test-data]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

On `/credentials/create-credential/github` the Base Url ships **pre-filled** and
**Anonymous** is the default auth method, so filling the Display Name alone enables
Save and `POST /configurations/configurations/{project}` returns 200. Confirmed live
2026-08-22 (ELITEA-1964).

## Why it matters

Every other credential spec (`test_credential_create.py`, `test_credential_pin_unpin.py`,
…) opens with `if not settings.git_hub_token: pytest.skip(...)` because it selects
**Token** auth. When the credential is only a *vehicle* (a delete case, a list-count
case, a cleanup fixture), Token auth buys nothing and costs a skip path plus typing a
real secret into the UI. Use Display Name + default Anonymous auth instead.

Related: [[credentials_list_never_reaches_networkidle]]
