---
name: dev_chat_ai_no_reply_and_center_banner
description: Sandbox DEV chat gives no AI reply; centered "Got it" dialog blocks clicks; scripted-probe tips
type: project
---

- 2026-10-19 (ELITEA-3366, 3367): any chat message on DEV got no reply or "Unknown error" in this sandbox, even with no modules. Env fault: send "Say hello" first before debugging a case.
- Playwright MCP chrome is missing here; use scripted sync-playwright probes with `.playwright-mcp/dev-storage-state.json` and `APP_PREFIX=/app`.
- The centered announcement dialog ("Got it") can reappear after navigation and intercepts clicks; click it in a short loop with waits before the plus menu.
- Ask User card handles are source-only (ClarifyingQuestionControl.jsx): placeholder "Your option", Continue/Skip button, no testids.
