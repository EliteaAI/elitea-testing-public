---
name: Run the real suite against dev.elitea.ai without touching .env.test
description: The only non-destructive way to reproduce a DEV CI failure locally — a throwaway -p plugin, because shell exports cannot win
type: reference
aliases: [reproduce CI failure locally, run tests against dev, devtarget plugin, APP_PREFIX /app, dotenv beats env]
tags: [area/tooling, type/technique]
created: 2026-08-28
updated: 2026-08-28
---

## The problem

`automation/.env.test` pins `ELITEA_URL=http://localhost:5173`, and it is a
**symlink to the shared master file** — it must not be repointed. Worse,
`config.py`'s `settings_customise_sources` orders `dotenv_settings` **above**
`env_settings`, so `ELITEA_URL=... pytest ...` is silently ignored. `_ENV_FILE`
is hardcoded, so there is no env-file override hook either.

## The technique

A throwaway pytest plugin that mutates the already-constructed `settings`
singleton. `-p` plugins load before `conftest.py` reads `settings.elitea_url`,
so this wins:

```python
# /tmp/devtarget.py
from config import settings
settings.elitea_url = "https://dev.elitea.ai"
settings.app_prefix = "/app"          # empty on localhost, /app on deployed
```

```bash
cd automation
PYTHONPATH=/tmp:$PYTHONPATH HEADLESS=true ../.venv/bin/pytest <node-id> \
  -p devtarget -p no:cacheprovider -v
```

Nothing else is needed: `.env.test` already carries
`ELITEA_API_BASE=https://dev.elitea.ai/api/v2` and the matching
`ELITEA_PROJECT_ID`, and `auth_state` does the real Keycloak login on any
non-localhost host.

## Why it matters

It turns "green locally, red in CI" from a guess into a measurement — the
difference between class **A** (drift) and class **D** (env/flake) in
`adjust-automated-test`. Used on #1897 to prove the product was fine on DEV
(`3 passed, 2 skipped`) before writing a line of the repair brief.

Declare it as a throwaway in the report; never commit the plugin.

## Also worth knowing when reproducing on a deployed env

Ad-hoc Playwright scripts need the banner/NPS dismissal that `conftest.py`'s
autouse `dismiss_banner_after_navigation` fixture does for real tests — a
high-z-index MUI banner **intercepts pointer events** and every `click()` times
out with "subtree intercepts pointer events". Copy
`BasePage.dismiss_banner_if_present()`'s JS, or you will misread an overlay as a
product bug.

Related: [[js_click_on_disabled_button_is_a_silent_noop]]
