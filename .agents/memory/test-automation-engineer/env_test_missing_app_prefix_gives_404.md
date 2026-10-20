---
name: env_test_missing_app_prefix_gives_404
description: Without automation/.env.test, APP_PREFIX defaults to "" and every nav 404s; export APP_PREFIX=/app
type: project
---

In the factory container `automation/.env.test` may not exist; `config.py` defaults `app_prefix=""`, so
`navigate_to_chat` lands on dev.elitea.ai/chat = "404 Page Not Found" and times out on `chat-message-input`.
Fix: `export APP_PREFIX=/app` before pytest (ELITEA_URL, creds are already in the shell env). Check the
failure screenshot in `automation/screenshots/` first when every nav test times out.
