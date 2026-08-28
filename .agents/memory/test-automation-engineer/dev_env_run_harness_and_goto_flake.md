---
name: Running a spec against DEV — the -p plugin harness, and its Page.goto flake
description: ELITEA_URL export does nothing; use an out-of-repo pytest plugin. Expect ~40% raw goto timeouts.
type: reference
aliases: [dev.elitea.ai run, devenv harness, deployed env locally, goto timeout dev]
tags: [area/test-execution, area/environment]
created: 2026-08-28
updated: 2026-08-28
---

## Targeting DEV from a local run

**`export ELITEA_URL=...` does NOTHING** — `config.py` orders dotenv before env
vars, so `.env.test` wins and the run silently stays on localhost. `.env.test`
is a symlink to a shared master and is off-limits. Use an out-of-repo pytest
plugin instead:

```python
# /tmp/devenv_harness/devenv.py — NOT in the repo
import os, sys
sys.path.insert(0, os.environ["AUTOMATION_DIR"])
import config
config.settings.elitea_url = os.environ["DEV_ELITEA_URL"]
config.settings.app_prefix = os.environ.get("DEV_APP_PREFIX", "/app")
```
```bash
cd automation && AUTOMATION_DIR=$PWD DEV_ELITEA_URL=https://dev.elitea.ai \
  DEV_APP_PREFIX=/app PYTHONPATH=/tmp/devenv_harness HEADLESS=true \
  ../.venv/bin/pytest -p devenv "<node-id>" -v -p no:cacheprovider --log-cli-level=INFO
```

**A green result is not evidence of the target.** Prove it from the INFO log
every run: `Authenticating via API against https://dev.elitea.ai`, `redirected
to https://dev.elitea.ai/app/`, and a `Navigating to https://dev.elitea.ai/app/...`
line.

## The Page.goto flake (measured 2026-08-28, ELITEA-2051 / PR #1931)

Local machine → dev.elitea.ai, 8 invocations of one pipelines spec: **4 of 8 died
on a raw `playwright…TimeoutError: Page.goto` at a precondition**, at one of two
shared sites:

- `fixtures/api_fixtures.py:104` — `pg.goto("/")`, hardcoded 15 000 ms nav
  timeout, followed by a `networkidle` wait (the discouraged pattern behind #1847)
- `pages/base_page.py:146` — `navigate()`, 30 000 ms

Confirmed **pre-existing and version-independent** by a matched control: pristine
`main` code showed the identical `base_page.py:146` timeout. dev.elitea.ai itself
answered every `curl` in ~0.6 s throughout, so this is browser-side SPA-bundle
load latency from a local machine against a deployed env, not a server problem.

**Response: re-run.** It is upstream of every assertion a case makes, so it can
never be a member of a sanctioned-RED set and 2-of-3 is never acceptable. Budget
roughly double the invocations you would need on localhost when gating against DEV
from a laptop. One more tell: the failure *screenshot* also times out
(`Page.screenshot: Timeout 10000ms exceeded`) when the browser is this wedged.
