---
name: Support Assistant renders no partial text (agent-mode delivery)
description: The widget never streams tokens — status messages then one atomic body; typewriter is dead code
type: project
aliases: [support assistant streaming, token streaming, partial text, agent_response, useTypewriter, isAnimating]
tags: [area/support-assistant, type/product-behaviour]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

The Elitea Support Assistant widget **never renders partial response text**. The assistant bubble
stays at 0 characters for the whole generation window (72-87 s measured), then the complete answer
appears in a single render frame, together with the copy button.

Verified live 2026-08-22 on `localhost:5173`, twice, sampling every 150 ms: 0 → 474 chars and
0 → 707 chars in one sample each.

## Why (source, `../elitea_assistant`)

- It is an **agent**, so the backend sends `agent_llm_chunk` → `chat.hook.ts:258-266` maps it to a
  **statusMessage only, never content** — then one terminal `agent_response` assigns the whole body
  (`:268-281`).
- The token-append branch (`chunk`/`AIMessageChunk` → `content: m.content + chunk`, `:238-250`) is
  unreachable on this surface.
- `AnimatedMessage` + `useTypewriter` (3 chars / 16 ms) is **dead code**: `isAnimating` is only ever
  assigned `false` (`:71`, `:302`), never `true`.

## What to do with it

A TMS case asking to observe progressive/token arrival, "tokens lost", or "stream resumes from where
it was" on this surface is **case-text drift**, not a defect (reverse-masking guard). Assert the live
contract instead: in-flight = Stop-generation button + status message; no-restart = exactly one
`support_predict` WebSocket frame + unchanged assistant message-item count; no-loss = rendered text
never decreases. Worked example: ELITEA-2426 AFS + clarification issue #1662.

Related: [[.agents/knowledge]] · surface digest `test-specs/support-assistant/_surface.md` notes 70-74
