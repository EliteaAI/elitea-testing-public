---
name: The -p devenv DEV-gate plugin needs PYTHONPATH to PREPEND automation/, not replace it
description: PYTHONPATH=/tmp alone makes the plugin fail with "No module named config" — pytest imports -p plugins before conftest puts rootdir on sys.path
type: feedback
aliases: [devenv plugin import error, no module named config, PYTHONPATH dev gate, -p devenv fails, dev gate plugin]
tags: [area/gating, area/dev-env, type/gotcha]
created: 2026-09-10
updated: 2026-09-10
---

## The failure

The out-of-repo DEV-gate plugin (`/tmp/devenv.py`, loaded `-p devenv`) starts with `import config`.
Run it as `PYTHONPATH=/tmp pytest -p devenv …` and every invocation dies at collection:

```
ImportError: Error importing plugin "devenv": No module named 'config'
```

**Why:** pytest imports `-p` plugins during `consider_preparse`, *before* conftest/rootdir handling
puts `automation/` on `sys.path`. Setting `PYTHONPATH=/tmp` **replaces** the path rather than adding
to it, so `config` (which lives in `automation/`) is invisible at that moment. That import order is
the whole point of the plugin — it must beat conftest so the module-level `ELITEA_URL =
settings.elitea_url` captures DEV — so it cannot be fixed by loading later.

## The fix

```bash
AUT=<abs path to>/automation
export PYTHONPATH="/tmp:$AUT"     # PREPEND — both dirs, plugin dir first
```

## Why it cost a full gate cycle, and the guard that makes it free

The 3-run loop happily executed 3 collection errors and reported nothing green — the mistake is
cheap to make and silent in the tail. The same guard that catches a failed `.env.test` swap catches
this: **assert the framework's own resolver before running anything.**

```bash
TARGET=$(../.venv/bin/python -c "import devenv, config; print(config.settings.app_base_url)" | tail -1)
[ "$TARGET" = "https://dev.elitea.ai/app" ] || { echo "REFUSING"; exit 2; }
```

This imports the plugin the same way pytest will, so a broken plugin fails the guard instead of
three gate runs. Generalises the rule in [[env_test_is_a_symlink_so_sed_i_silently_no_ops]]: **a
target-environment swap is not done until the resolver says so** — and the guard should exercise the
same import path the run will.
