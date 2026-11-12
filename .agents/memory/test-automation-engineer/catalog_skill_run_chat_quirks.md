---
name: catalog_skill_run_chat_quirks
description: Catalog Skills-tab Run -> chat (ELITEA-4633): sender label, no Copy button, sidebar id differs, APP_PREFIX env
type: project
---

- Skill-run reply: sender label is "Elitea to Message" (not "Skill: code-reviewer"); no Copy button, so `wait_for_ai_response` times out. Use expect on reply text + "Thought for".
- Reply text may legitimately contain the word "error" - never substring-assert absence of it.
- Sidebar item `chat-conversation-item-{id}` can carry a different id than the URL id (second conversation persisted on send); match by name `Run <skill>` via `get_conversation_item_rows().filter(has_text=)` and delete all by name in cleanup.
- Sandbox has no .env.test: pass `APP_PREFIX=/app` on the command line or navigation to /elitea-catalog never finds the heading.
