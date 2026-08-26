---
name: Running the suite against DEV without editing .env.test
description: Exporting ELITEA_URL does NOT retarget the suite — .env.test outranks env vars, so the run silently stays on localhost
type: feedback
---

## The trap

`automation/config.py` overrides `settings_customise_sources` (~line 234) to put
`dotenv_settings` **before** `env_settings`. So:

```bash
ELITEA_URL=https://dev.elitea.ai pytest ...   # ← does NOTHING
```

The run silently keeps using `.env.test`'s `ELITEA_URL=http://localhost:5173`.
It does not error. And because a local dev server is often live on :5173, **the
test still passes** — so a "DEV verification" can be entirely fake and look green.

## Don't edit `.env.test`

It is a symlink to the shared master file in the parent workspace, and `.env*` is
outside the lead's editable paths anyway.

## What works: a throwaway `-p` plugin outside the repo

Load-order is the whole trick — `-p` plugins import **before** `conftest.py` pulls
in the fixture modules, and those modules snapshot the value into module constants
(`fixtures/session_fixtures.py:21` and `fixtures/api_fixtures.py:27` both do
`ELITEA_URL = settings.elitea_url`). Mutating the settings object first is enough.

```python
# /tmp/devenv_harness/devenv.py  — NOT in the repo
import os, sys
sys.path.insert(0, os.environ["AUTOMATION_DIR"])
import config
config.settings.elitea_url = os.environ["DEV_ELITEA_URL"]
config.settings.app_prefix = os.environ.get("DEV_APP_PREFIX", "/app")
```

```bash
cd automation && AUTOMATION_DIR=$PWD DEV_ELITEA_URL=https://dev.elitea.ai \
  DEV_APP_PREFIX=/app PYTHONPATH=/tmp/devenv_harness HEADLESS=true \
  ../.venv/bin/pytest -p devenv <node-id> -v -p no:cacheprovider --log-cli-level=INFO
```

Zero repo files touched. `elitea_auth_url` then resolves to `https://dev.elitea.ai`
and `auth_state` takes the **real Keycloak/API** branch instead of the localhost
`VITE_DEV_TOKEN` bypass. `.env.test`'s `ELITEA_API_BASE` already points at the DEV
backend and `ELITEA_PROJECT_ID=399` is a DEV project, so nothing else needs changing.

## Always prove the target

`--log-cli-level=INFO` on every DEV run; the log must show all three:

```
session_fixtures.py:117 Authenticating via API against https://dev.elitea.ai
api_auth.py:115         Login successful - redirected to https://dev.elitea.ai/app/
base_page.py:145        Navigating to https://dev.elitea.ai/app/pipelines/all/<id>?viewMode=owner
```

A green result on its own is NOT evidence of the target — check `lsof -nP -iTCP:5173`
before believing it. (Established #1776 / ELITEA-2037, 2026-08-26: 4/4 green vs DEV.)
