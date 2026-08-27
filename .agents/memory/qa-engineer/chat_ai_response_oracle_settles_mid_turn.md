---
name: ChatPage.wait_for_ai_response can settle mid-turn
description: The shared chat oracle's Copy-button signal flickers ON during an agentic turn, so AI-prose assertions can read a narration instead of the answer
type: feedback
aliases: [wait_for_ai_response, chat oracle, copy button flicker, get_last_message_text, mid-turn settle, agentic narration]
tags: [area/chat, type/flake]
created: 2026-08-28
updated: 2026-08-28
---

## The defect

`ChatPage.wait_for_ai_response(initial_count)` (`pages/chat_page.py:2273`) returns when the
message at `initial_count + 1` has a **visible `Copy to clipboard` button** and a body that
`_is_transient_message()` doesn't recognise. Both are satisfiable **mid-turn**:

- `_extract_message_body()` (`:2143`) collects every `<p>`/`<li>`, so streamed narration prose
  counts as content.
- `_is_transient_message()` (`:2400`) knows only six literals (`waking the agent`, `thinking`,
  + ellipsis variants) plus a `"Thought for X"` pattern. An agentic narration like
  *"Let me read the file directly…"* is not in that set → treated as a finished answer.

## Measured (2026-08-28, ELITEA-0500, localhost, 3 instrumented runs)

The Copy button appears **and disappears again** during the tool-call phase — every run:

| Run | appears | body at that instant | gone by |
|---|---|---|---|
| 1 | 11.3 s | `Attachments: read_multiple_fi…` | 12.3 s |
| 2 | 11.1 s | `Attachments: read_multiple_fi…` | 11.7 s |
| 3 | 10.7 s | `Thought for less than a second` | — |

Run 3 instrumented the oracle's exact condition and showed `copyVisible=True` at t=10.7 s,
blocked **only** by the `"Thought for …"` match. Swap in narration prose and the oracle returns.

## Second, independent bug in the same flow

The wait settles index `initial_count + 1`; `get_last_message_text()` (`:2243`) reads
`messages_container.last`. Nothing ties the assertion to the element the wait settled on.

## Why it matters

Shared oracle → suite-wide. Any chat spec asserting AI prose through it can go red on a
narration (ELITEA-2201's merged test included). Presents as an unreproducible CI red:
6 localhost runs of the ELITEA-0500 test were green while DEV was red.

## The corrected oracle — measured, works

Settle on the product's own signals, not a string blocklist: `chat-stop-generation-button`
NOT visible + Copy button visible on idx `initial_count+1`, both **stable >=1.2 s across >=2
polls**; read `get_message_text_at(initial_count+1)`, never `.last`. Measured on the
ELITEA-0500 attach flow: **8/8 settled, 8/8 correct final text, 18.5-21.1 s (mean 19.8 s)**.

Better still where a frame carries the fact: chat tool lifecycle rides **`chat_predict_attachment`**
frames — `response_metadata.tool_name` + `tool_output` (the real tool result). This flow emits
**no `agent_tool_end` and no `agent_llm_chunk`**, so don't build a wait on those.

## What to do

Don't add a longer timeout or another transient string — the blocklist is the bug. Prefer a
**positive** end-of-turn signal (absence of `chat-stop-generation-button`, or a turn-complete
socket.io frame via `utils/websocket_frames.py`), require it **stable across ≥2 polls / >1 s**
(defeats the ~0.6 s flicker), and read via `get_message_text_at(initial_count + 1)`.

Related: [[llm_trigger_side_flakes_are_never_sanctioned_red]]
AFS: `test-specs/chat-interface/lextend_attach-files-send-with-message-oracle-repair_ELITEA-0500.md`
