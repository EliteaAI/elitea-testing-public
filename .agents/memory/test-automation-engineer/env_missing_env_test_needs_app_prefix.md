---
name: Missing .env.test means no APP_PREFIX - agent detail 404s
description: In a container with no automation/.env.test, config app_prefix is empty and goto lands on 404; run with APP_PREFIX=/app
type: feedback
---

When `automation/.env.test` is absent, `settings.app_prefix` is "" (shell only exports `APP_PREFIX_DEV=/app`), so page-object navigation hits `https://dev.elitea.ai/agents/...` and DEV serves a 404 page. Symptom: `Navigate to agent` times out on `agent-information-section`, screenshot shows "404 Page Not Found". Fix: prefix the run with `APP_PREFIX=/app` (do not edit files). Also `ruff` is not installed in `.venv`.
