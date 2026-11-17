---
name: env_test_missing_set_app_prefix
description: When automation/.env.test is absent, every chat page 404s unless APP_PREFIX=/app is exported
type: feedback
---
On factory machines without `automation/.env.test`, `config.settings.app_prefix` defaults to "" so `/chat/<id>` 404s and every chat test fails at `chat-message-input` (looks like drift, is not). Control: run an unrelated chat test first; fix: `export APP_PREFIX=/app` (ELITEA_URL is already in env). Found on #2969 (ELITEA-2184/2187 adjust, class A copy-button split).
