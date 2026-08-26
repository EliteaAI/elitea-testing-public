---
name: Project Context fixture 503 is an environment red
description: 11 UI specs erroring at once on a 503 from the project_context API is a DEV outage, never a batch regression
type: reference
aliases: [503 project context, fixture setup error 503, all UI specs error at once, elitea_core project_context 503]
tags: [area/environment, type/noise]
created: 2026-08-26
updated: 2026-08-26
---

## Signature

```
ERROR tests/ui/admin/test_project_context_*.py::... -
  requests.exceptions.HTTPError: 503 Server Error: Service Unavailable for url:
  https://dev.elitea.ai/api/v2/elitea_core/project_context/prompt_lib/399/project-context
```

Observed once during the settings-w03 hardening gate (2026-08-26): **11 errors, 0
failures**, whole invocation dead in 21s (a healthy run is ~150s). The 20 unit guard
tests in the same invocation passed — they touch no backend.

## How to read it

Three tells separate this from a code red, and all three must hold:

- **ERROR, not FAILED.** The exception is raised in `clean_project_context` /
  `project_context_seed` fixture setup, so no test body ever executed. Reporting it as a
  failing case sends the lead hunting a bug that does not exist.
- **Every backend-touching spec at once**, and only those. A real defect in one spec
  cannot take out eleven.
- **Run duration collapses** (21s vs ~150s) — the suite died at setup, it did not run.

Response: it is an environment fact. Restart the N-consecutive streak and re-run; the
very next run went 31/31 green with zero code changes. Do **not** investigate the specs,
and do **not** weaken the fixture to tolerate a 503 — that would mask a real backend
outage on the next campaign.

Related: [[watcher_blind_on_onedrive_restart_dev_server]]
