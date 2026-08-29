---
name: A failing chat turn is silent on HTTP and console — only Socket.IO carries the error
description: Classify chat failures from chat_message_sync meta.error frames, never from console/HTTP silence
type: project
aliases: [chat error, meta.error, chat_message_sync, socket error, invalid model credential]
tags: [area/chat]
created: 2026-08-30
updated: 2026-08-30
---

Confirmed again on ELITEA-2416 (a chat turn against an LLM model whose credential cannot
authenticate): **no failed HTTP request, no console error.** The failure arrives only as
a Socket.IO `chat_message_sync` frame with a non-empty `meta.error`, ~8 s after send.

So "does the chat hang?" is answered by waiting for that frame — a positive, bounded
statement — not by a timeout on an absent bubble. Collector:
`automation/utils/websocket_frames.py` / `ChatPage.capture_websocket_frames()`. Pump with
`page.wait_for_timeout`, never `time.sleep` (the sync API only dispatches WS events while
inside a Playwright call).

Assert on the frame's **field**, not its text — the text is backend-authored and changes.

Same lesson as the HITL `socket_validation_error` root-cause already in
`.agents/testing.md`; this is a second, independent surface confirming it.

Chat handle traps found the same day: `model-selector-button` is a `role="group"` wrapper
(clicking it does nothing — click `model-selector-name`); `model-selector-option-{name}`
is keyed by the model's `name` field so duplicate names collide (select by display text);
`chat-input` is a wrapper, type into its inner `textarea`.

Related: [[ai_provider_credential_form_live_facts]]
