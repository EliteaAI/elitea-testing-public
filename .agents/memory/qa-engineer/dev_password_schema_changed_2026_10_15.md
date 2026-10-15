---
name: DEV password schema changed 2026-10-15 — sandbox .env.test is stale
description: DEV now needs TEMPLATE+'0' for every user; this sandbox's TEST_USER_PASSWORD/API token predate the cutover and both fail live
type: project
---

## What changed

Commit `13e68be3` (2026-10-15 11:05 +03:00, "ci: drop dev-vm workflow, use '0' password
suffix on DEV") moved `dev.elitea.ai`'s password schema to match stage2: **every** user
(1-9, ADMIN, User B) now authenticates with `TEST_USER_PASSWORD_TEMPLATE + "0"`, via
`password_suffix_override: '0'` passed into `test-ui-dev.yml` → `test-ui-custom.yml`.
Previously DEV used a per-user suffix (dev-vm realm pattern).

## Symptom this produces

`cd automation && ../.venv/bin/python scripts/dev_storage_state.py` fails with:

```
RuntimeError: Login failed: Login failed: 200 https://ai-auth.elitea.ai/...authenticate?...
```

(form re-renders on the Keycloak login page — status 200, not a redirect — the same
signature Keycloak gives for both "no such user" and "wrong password"; the response alone
can't distinguish them.) This is the SAME symptom a stale/wrong credential always produces —
don't assume the first time you see it that it's this specific cause; this entry just
documents the one confirmed-live instance so far (2026-10-15 sandbox).

## Why this sandbox hit it

This clone's `automation/.env.test` was last written 2026-10-07 07:24 — 8 days BEFORE the
schema-change commit landed. It carries a flat `TEST_USER_PASSWORD` with no
`TEST_USER_PASSWORD_TEMPLATE` key and no documented suffix convention, so there is no way to
mechanically derive `TEMPLATE + "0"` from what's on disk — the file predates the concept.

**Also confirmed stale in the same file:** `ELITEA_API_TOKEN` — every direct
`Authorization: Bearer <token>` call to `https://dev.elitea.ai/api/v2/...` 302-redirects to
`/access_denied` (checked `GET /projects/all` and `GET /pipelines/all/575`). Don't assume the
Bearer-token path is a working fallback when browser login fails on this sandbox — check it
independently; it was dead too, same day, same root era.

## What to do if you hit this

1. Don't guess passwords or mutate `.env.test` speculatively — a wrong-password 200 and a
   stale-template 200 look identical from here.
2. Check whether `.env.test` has been refreshed since 2026-10-15 11:05 (`stat
   automation/.env.test` vs this commit's timestamp). If it predates the commit, that's your
   answer — it's a credentials-refresh gap, not a product/test defect, and not something an
   analyst session can fix (the master `.env.test` lives in the parent-folder secrets file,
   outside this repo).
3. Report as a blocker (environment/credentials gap), not as a product-bug or test-bug
   finding. Don't spend more than ~2 dev_storage_state.py attempts chasing it.
