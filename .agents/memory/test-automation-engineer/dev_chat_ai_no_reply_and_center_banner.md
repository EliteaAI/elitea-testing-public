---
name: dev_chat_ai_no_reply_and_center_banner
description: DEV chat gave no AI reply in sandbox (even existing tests); center "Got it" announcement dialog blocks clicks
type: project
---

- 2026-10-19 (ELITEA-3366): in this sandbox, any chat message to DEV got no AI reply (WS connects, reply never arrives; existing test_send_text_message also fails). Env fault, not spec: check an existing AI-reply test first before debugging a new one.
- Sandbox has no `.env.test`; run with `APP_PREFIX=/app` env + `-o addopts="--tb=short"` (pytest-rerunfailures is not installed in .venv).
- DEV shows a centered announcement dialog (`platform-banner-center`, "Got it") that BasePage.dismiss_banner_if_present misses; `ChatPage.dismiss_center_banner_if_present()` handles it. Top banner shares `platform-banner-close` testid, so scope it.
- Skill chip: `ChatPage.generated_entity_chip` + `open_generated_entity_chip()` (hover first).
