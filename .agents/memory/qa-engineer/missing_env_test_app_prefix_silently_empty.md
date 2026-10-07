---
name: Missing .env.test in a sandbox silently drops APP_PREFIX, not ELITEA_URL
description: ELITEA-1862 triage, 2026-10-07 — this sandbox has no automation/.env.test at all (only .env.test.example); shell env vars cover ELITEA_URL/API_BASE/PROJECT_ID/credentials but NOT APP_PREFIX, which defaults to "" and 404s every page-object navigate() one segment early.
type: feedback
tags: [area/tooling, type/environment]
created: 2026-10-07
---

## What happened

Diagnosing a CI-reported timeout at "Open file in preview/edit editor"
(ELITEA-1862 adjust triage). First clean-process local repro failed instead at
**Step 1** (`navigate_to_bucket` → `_wait_for_bucket_panel`, 15s timeout
waiting for the bucket name text in `main`) — a step *earlier* than CI's
reported failure, with no locator/DOM explanation.

Root cause: `ls automation/.env.test` → does not exist (only
`.env.test.example` is present in this sandbox — the symlink to the shared
master file described in `retarget_suite_at_dev_without_editing_env_test.md`
simply isn't there this time). `config.py`'s `Settings` falls through to
shell env vars when the dotenv file is absent, and this sandbox's shell DOES
export `ELITEA_URL`, `ELITEA_API_BASE`, `ELITEA_PROJECT_ID`,
`TEST_USER_EMAIL`/`_PASSWORD`, `ELITEA_API_TOKEN` — but **not** `APP_PREFIX`.
`settings.app_prefix` defaults to `""`, so `settings.app_base_url` resolved to
`https://dev.elitea.ai` with no `/app` segment, and every `BasePage.navigate()`
call 404'd before any bucket panel could render — a false, unrelated failure
one step ahead of the real one.

## The fix for this session

Export it explicitly before any pytest/scratch-script run:
```bash
APP_PREFIX=/app HEADLESS=true ../.venv/bin/pytest <node-id> -v -p no:cacheprovider
```
or `os.environ.setdefault("APP_PREFIX", "/app")` before `from config import
settings` in a scratch script. Confirmed: this alone took the repro from a
false Step-1 failure to the real, CI-matching Step-3/4 failure (same error,
same testid, 3/3 identical).

## Why this is worth checking FIRST, every time

`retarget_suite_at_dev_without_editing_env_test.md` describes a DIFFERENT
sandbox state (`.env.test` present as a symlink, pinned to localhost) and its
advice ("shell exports cannot win") is backwards when the file is simply
missing — in THAT case shell exports are all there is, and the one var
nobody thinks to export by hand is `APP_PREFIX` (it's not a secret, so it's
easy to leave out of whatever exported the rest). Before trusting ANY local
UI-navigation failure as drift: `test -f automation/.env.test || echo
MISSING`, and if missing, `env | grep -i app_prefix` — don't assume dev vs
localhost from `ELITEA_URL` alone, check `APP_PREFIX` independently.

Related: [[retarget_suite_at_dev_without_editing_env_test]]
