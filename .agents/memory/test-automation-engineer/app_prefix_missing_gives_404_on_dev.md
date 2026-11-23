---
name: APP_PREFIX unset gives 404 on DEV
description: No .env.test on host and only APP_PREFIX_DEV exported; prefix empty so every UI spec 404s at agent-information-section
type: project
---

Symptom: every agent UI spec fails at `Navigate to agent` waiting on `agent-information-section`; the failure screenshot is the Elitea 404 page. Cause: `config.py` reads `APP_PREFIX`, but the shell only exports `APP_PREFIX_DEV` (and there is no `automation/.env.test`). Fix: prefix pytest with `APP_PREFIX=/app`. Check the failure screenshot before debugging handles.
