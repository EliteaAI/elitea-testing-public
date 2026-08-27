---
name: The chat HITL resume is REJECTED on the wire, not silently dropped
description: chat_continue_predict omits llm_settings; the backend errors and the UI swallows it (#1834)
type: project
aliases: [socket_validation_error, hitl resume drops the turn, llm_settings with model_name is required]
tags: [area/chat-hitl, type/product-defect]
created: 2026-08-27
updated: 2026-08-27
---

## Fact

Three specs in `tests/ui/chat/test_hitl_sensitive_action_authorization.py`
(ELITEA-2212/2213/2214) recorded the HITL resume as "the turn dies silently, no
error". That was an **instrumentation gap**, not silence.

The initial `chat_predict` carries `llm_settings.model_name`. The resume,
`chat_continue_predict`, **omits `llm_settings` entirely**, and ~50 ms later the
backend sends three `socket_validation_error` frames:

- `llm_settings with model_name is required` (×2)
- `Continue execution failed: llm_settings with model_name is required`

Byte-identical for `action: "reject"` and `action: "block_with_comment"` — one
root cause (#1834), not a per-path bug. The **frontend swallows it**: no console
error, no toast, no message-state change, `beforeunload` stays armed. Hence the
DOM-only reading of "silent".

## Consequences for tests

- Assert on the **event name** `socket_validation_error`, never the message text
  — a reworded-but-still-broken build must not turn the assertion green.
- The resume DOES carry the user's data: `hitl_decisions[0].value` holds the
  typed Block-with-Comment reason verbatim (`tool_call_id` is `""`). That is the
  only place in the system where the reason is currently observable — the
  conversation JSON has no trace of it and there is no reply.
- "File still in the bucket" proves nothing on its own: a REJECTED resume leaves
  byte-identical evidence to a correctly blocked one.

Related: [[playwright_sync_events_need_a_playwright_call_to_dispatch]]
