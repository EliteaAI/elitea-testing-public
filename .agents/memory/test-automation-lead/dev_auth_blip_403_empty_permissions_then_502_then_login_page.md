---
name: DEV auth blip — 403 access_denied with current_permissions [] → 502s → Keycloak login page at a precondition
description: A gate invocation whose API call returns 403 with an EMPTY permission set for a user that created entities seconds earlier, followed by 502 Bad Gateway on every teardown call and the next attempts landing on the sign-in page, is a DEV auth/gateway blip — re-gate, never the signature
type: feedback
aliases: [current_permissions empty, 403 access_denied gate, 502 bad gateway teardown, keycloak login page screenshot, session bounced, dev auth blip]
tags: [area/merge-gate, area/dev-env, type/diagnosis]
created: 2026-09-18
updated: 2026-09-18
---

## Signature (2026-09-18 11:31–11:34Z, #2349 gate A)
- run 1: Steps 1–9 PASSED, Step 10 `PUT /configurations/configuration/399/<id>` →
  `403 {"error":"access_denied","required":[…],"current_permissions":[]}` — for the SAME user that
  created the credential + toolkit ~30 s earlier; then `502 Bad Gateway` on every cleanup-fixture GET.
  `reruns.json {}` because `HTTPError` is not in `--only-rerun`.
- run 2: 3 attempts `broken` at Step 3 `wait_for_page_load` (name textbox 15 s) — the failure
  screenshot is the **Keycloak sign-in page**. The session cookie was bounced; nothing rendered.
- run 3 (11:34Z) and the full re-gate 3/3: clean, 43 s each, 13 allure steps.

## Read it as
Environment, at a precondition, never a member of a sanctioned-RED set → **re-gate from scratch**.
Cheap tells: `current_permissions: []` (an authenticated user has never zero), 502 on unrelated
endpoints in teardown, and the screenshot. Open the screenshot FIRST (the #2074 rule) — the
assertion message names a textbox, not the login page.

## Also
Run 1's `finally` cleanup got the same 403, so scratch entities can leak — sweep by prefix
(`autotest_toolkit_*`, `autotest_tk_cred_*` / `tk_jira_*`) with the Bearer `APIClient`
(`.get()` returns a `requests.Response`; credentials list is `{"total","items",…}`, tools is `{"rows"…}`).
This time the retry's cleanup had already removed them (0 leftovers).
