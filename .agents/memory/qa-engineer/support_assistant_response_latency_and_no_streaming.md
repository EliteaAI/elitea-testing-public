---
name: Support Assistant response latency and absence of text streaming
description: Replies take 33-135s and render ATOMICALLY — no progressive text growth; transient observables are the typing indicator and Stop generation button
type: reference
aliases: [support assistant streaming, assistant response timeout, elitea-assistant-typing-indicator]
tags: [area/support-assistant, type/timing]
created: 2026-08-22
updated: 2026-08-22
---

## Measured live 2026-08-22 (localhost:5173, widget on `/chat`)

Three real sends, sampled at 500ms:

| Prompt | Time to reply |
|---|---|
| "Hello" | ~35-60s |
| "What page am I currently on in ELITEA?" | 60-135s |
| Long explain-agents-pipelines-toolkits prompt | 33s |

`AI_RESPONSE_TIMEOUT = 120_000` in `test_support_assistant_smoke.py` is **not generous** — the
context question landed between the 60s and 135s marks. Anything asserting a Support Assistant
reply needs ≥120s and should wait on the message-count change, never a fixed sleep.

## There is NO progressive text streaming — do not spec one

The assistant message element does **not** exist during generation and then appears **fully
formed in a single 500ms sample** (0 → 1450 chars). Sampling every 500ms across the whole
generation caught exactly two states, never an intermediate length. So a case asking to observe
"a response arriving progressively" **cannot** be satisfied against this widget — route it rather
than fabricating it.

What IS genuinely observable while generating (both confirmed live):
- `.elitea-assistant-typing-indicator` (3 × `.elitea-assistant-typing-dot`) — present at 500ms
- `button[aria-label="Stop generation"]` — replaces the send button during generation only
- the Expand/Collapse control stays present and usable throughout

Note `AnimatedMessage.tsx` + the EL-6280 "fix text animation" commit describe a CSS reveal of
already-complete text, not token streaming — the distinction that matters when reading the source.

Related: [[support_assistant_launcher_click_quirk]]
