---
name: Guardrails config is writable by REST under the "administration" mode, not "prompt_lib"
description: Sensitive/blocked tool config is reachable by the standard test user — no Admin UI, no deployed env
type: reference
aliases: [guardrails, sensitive_tools, sensitive action, HITL precondition, plugin_config_values, admin config]
tags: [area/chat, area/guardrails, type/endpoint]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

The Elitea guardrails config (blocked toolkits/tools, `sensitive_tools`, the sensitive-action
message template) is readable AND writable by the **standard test user's `ELITEA_API_TOKEN`**
— but only under the `administration` mode segment:

| Request | Result |
|---|---|
| `GET/PUT {ELITEA_API_BASE}/admin/plugin_config_values/administration/guardrails` | **200** |
| `GET {ELITEA_API_BASE}/admin/plugin_config_values/prompt_lib/guardrails` | **403** `{"ok": false, "error": "access_denied"}` |

`PUT` returns `{"saved": true, "requires_restart": []}` and takes effect **immediately** —
mid-conversation, no restart, no re-attach, no new conversation.

PUT the **full** values object: `GET` it, mutate one key, PUT it back wrapped as
`{"values": {...}}`. Restore the captured original on teardown — never a hardcoded `{}`,
which would silently wipe anyone else's config. `sensitive_tools` is keyed by toolkit
**TYPE** and is **org-wide** while set.

## Why it matters

A whole test module (`tests/ui/chat/test_hitl_sensitive_action_authorization.py`,
ELITEA-2211..2214) was written, merged and then **never executed** because its fixture drove
the Admin UI at `/admin/app/configuration#guardrails`, which is Page404 on localhost
(issue #1140) — the Admin UI is a separate deployed application, there is no `/admin` route
in `EliteaUI/src/routes.js`. The prior analysis concluded "environment limitation, needs
deployed-env CI" after probing exactly one interface.

## The lesson

**"The UI for this doesn't exist here" is not the same as "this can't be configured here."**
Before declaring a precondition unreachable, probe the API under **every plausible mode /
scope segment**, not just the one the UI happens to use. Here one path segment
(`prompt_lib` → `administration`) was the difference between a blocked case and a fully
local, fully honest test. A 403 on one variant is not a closed avenue.

Related: [[chat_bare_chat_restores_last_conversation]]
