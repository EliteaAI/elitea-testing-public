---
name: Missing .env.test needs APP_PREFIX=/app
description: When automation/.env.test is absent, shell env supplies ELITEA_URL but not APP_PREFIX; set APP_PREFIX=/app inline or UI tests time out on skill-name-input
type: project
---

Symptom: every UI test times out waiting for the first form testid (e.g. `skill-name-input`) on dev.elitea.ai.
Cause: no `.env.test` in the sandbox; `ELITEA_URL` is in shell env but `APP_PREFIX` defaults to "". Fix: `APP_PREFIX=/app HEADLESS=true ../.venv/bin/pytest ...`. ruff is not installed in `.venv`.
