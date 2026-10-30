---
name: sandbox app prefix unset causes 404
description: In the factory sandbox there is no .env.test and APP_PREFIX is unset, so page objects navigate without /app and DEV returns 404 — prefix pytest with APP_PREFIX=/app
type: feedback
---
Reproducing a CI red locally in the sandbox: `APP_PREFIX` is not exported and there is no `.env.test`, so `settings.app_base_url` = `https://dev.elitea.ai` and every detail page 404s ("Page Not Found" screenshot, `wait_for_function` timeout in `wait_for_detail_page_load`). That is NOT drift. Run `APP_PREFIX=/app HEADLESS=true ../.venv/bin/pytest …` (also for implementer/gate dispatches). `ruff` is not installed in the sandbox venv.
Origin: #2759 / ELITEA-2060 (real cause: canvas node header menu removed; delete moved to node-panel footer `pipeline-node-panel-delete`).
