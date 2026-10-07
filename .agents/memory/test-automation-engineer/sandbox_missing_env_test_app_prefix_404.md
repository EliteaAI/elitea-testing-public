---
name: A sandbox with no master .env.test defaults APP_PREFIX to "" — silent client-side 404, not a backend timeout
description: When .env.test is entirely absent (not just unsymlinked), shell env vars DO work via pydantic-settings — but APP_PREFIX is commonly missing from that shell set, and its code default ("") makes every navigate() hit DEV's own in-SPA "Page Not Found" (HTTP 200, so curl/response-status checks look healthy)
type: feedback
aliases: [APP_PREFIX missing, no env.test, sandbox missing secrets, false bucket-list timeout, SPA 404 looks like backend timeout]
tags: [area/environment, type/pitfall]
created: 2026-10-06
updated: 2026-10-07
---

## The trap

Some sessions run in a workspace where `<parent>/.env` / `<parent>/.env.test`
(the master secrets CLAUDE.md describes) **do not exist at all** — not merely
unsymlinked, genuinely absent (`ls /opt/work_dir/` shows only the three sibling
repo clones, no env files). In that situation `automation/.env.test` can't even
be a symlink target.

**Correction to [[dev_env_run_harness_and_goto_flake]]'s "export ELITEA_URL does
nothing" claim: that is only true when `.env.test` exists and wins via dotenv
ordering.** When the file is simply absent, `pydantic-settings` falls through to
plain environment variables normally — `ELITEA_URL`, `TEST_USER_EMAIL/PASSWORD`,
`ELITEA_API_TOKEN`, `ELITEA_API_BASE`, `ELITEA_PROJECT_ID` worked fine from the
shell in this situation. The one that was missing from the shell's own export
set was **`APP_PREFIX`** — and `config.py`'s code default for it is `""`
(the localhost value), not `/app`.

## What this actually looks like

Every `BasePage.navigate()` call then goes to `https://dev.elitea.ai/artifacts`
(no `/app`). The web **server** still answers `HTTP 200` for that path (confirm
with a bare `curl` — it will mislead you into thinking the backend is fine) —
it's React Router's **own client-side 404** page that renders ("Page Not Found" /
"Go to Elitea" button), because the SPA's routes are only registered under the
`/app` basename. Any `page.on("response", ...)` wait keyed to a specific XHR
fragment (e.g. this project's `navigate_to_artifacts()` waiting on
`/artifacts/s3/`) then times out with "the request never completed" — which
reads exactly like a slow/overloaded backend (and this project's own
`testing.md` documents a real such flake for that same endpoint), sending you
down the wrong investigation path. The tell: **pull the failure screenshot
first** — it's the branded 404 page, not a loading spinner or blank tab.

## The fix

```bash
export APP_PREFIX=/app
```

Verify before re-running anything:
```python
from config import settings
print(settings.app_base_url)   # must include /app
```

This is a shell-only fix — nothing in the repo changes, nothing is committed.

**Update 2026-10-07 (ELITEA-1862 adjustment session) — `.venv/` itself can be
entirely absent, not just incomplete,** and the fix is still trivial:
```bash
python3 -m venv .venv
.venv/bin/pip3 install -e ".[reporting]"   # binary is `pip3`, there is no plain `pip`
```
In this sandbox flavor that was the WHOLE fix — every dependency (playwright,
pytest, pytest-rerunfailures, allure-pytest, ruff, …) came back `Requirement
already satisfied` on the very first `pip3 install -e ".[reporting]"`, no
`ensurepip`, no per-package install, no network wait. **Don't assume you need
the `ensurepip`/manual-`pytest-rerunfailures` workaround below pre-emptively —
try the two lines above first and check `pip3 list | grep rerun` before doing
any extra work.** The earlier caution (next paragraph) still applies if THAT
turns out false in some other sandbox flavor.

If `.venv` is also missing `pip`/plugins in the same kind of bare sandbox,
`python -m ensurepip --upgrade` bootstraps pip, and `pytest-rerunfailures` may
need an explicit `pip install` too — `pytest.ini`'s `addopts` uses `--reruns` /
`--only-rerun` but **that package is not declared anywhere in `pyproject.toml`**
(neither base deps nor the `reporting` extra), so a fresh
`pip install -e ".[reporting]"` per CLAUDE.md does not alone give you a working
`pytest` invocation in a from-scratch venv. Flag it to the lead; don't silently
add it to `pyproject.toml` from an implementer dispatch (shared-file / out of
this case's scope).

Related: [[dev_env_run_harness_and_goto_flake]], [[project_briefing]]
