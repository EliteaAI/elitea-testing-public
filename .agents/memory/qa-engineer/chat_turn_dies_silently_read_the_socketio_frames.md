---
name: A chat turn that "dies silently" — read the Socket.IO frames before saying "no error"
description: HTTP + console being clean does NOT mean no error; Elitea's chat errors arrive as socket_validation_error WS frames the UI swallows.
type: feedback
aliases: [socket_validation_error, hitl resume dropped, turn dies silently, chat_continue_predict, websocket frames chat]
tags: [area/chat, area/hitl, type/investigation-technique]
created: 2026-08-27
updated: 2026-08-27
---

## The lesson

Three consecutive analyst passes (ELITEA-2211, 2212, 2213) concluded that Elitea's HITL
resume "drops the turn **silently** — no console error, no failed request, no error frame."
The first two claims were true. The third was an **instrumentation gap**: nobody was
reading the WebSocket frames.

Elitea's chat runs over Socket.IO. Application errors arrive as
`42["socket_validation_error", {...}]` frames — they are **not** HTTP responses, **not**
console errors, and the frontend swallows them (no toast, no message-state change). So a
clean network tab plus a clean console proves nothing about whether the backend errored.

## What to do instead

Arm `page.on("websocket")` **before the first navigation** (the listener only fires for
sockets opened after it is attached) and read both directions. The proven in-repo helper is
`PipelineDetailPage.capture_websocket_frames()` (`pages/pipeline_detail_page.py`), a
`@contextmanager` yielding parsed `42["event", {...}]` frames tagged with `event` and
`_direction`; slice the window with `before = len(frames)` around the action.

This is **passive observation, not a substitution** (`.agents/testing.md` § Fidelity
policy) — no `route`/`fulfill`, nothing intercepted or rewritten. Precedent:
`pages/support_assistant_page.py` declares exactly this.

## What it found (2026-08-27, ELITEA-2214)

`chat_continue_predict` — the HITL resume — omits `llm_settings` entirely, while the
initial `chat_predict` carries `llm_settings.model_name`. The backend replies within ~50 ms:
`socket_validation_error: "llm_settings with model_name is required"` and
`"Continue execution failed: …"`. Identical for **Authorize, Block and Block with Comment**
(matched control run) — one root cause behind every symptom on #1834 / #1835.

The wire is also the only place a HITL block **comment** is observable: it rides in
`hitl_decisions[0].value`, and is never persisted anywhere.

Related: [[hitl_sensitive_action_module_gotchas]]
