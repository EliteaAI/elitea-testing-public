---
name: reasoning_effort none agent silently no-ops chat send
description: A disposable test agent created with llm_settings.reasoning_effort:"none" leaves the embedded/standalone chat composer populated but sends nothing when Send is clicked — zero console/network errors, no POST .../conversations/... at all. Safe only for save/reload-only tests.
type: feedback
---

## What happened (ELITEA-1886, 2026-08-07)

Several existing tests (`test_agent_remove_variable.py`, and this AFS's own
suggested payload) create a disposable agent via `AgentAPI.create_agent_full()`
with:

```python
"llm_settings": {
    "max_tokens": -1,
    "reasoning_effort": "none",
    "model_name": settings.default_model_name,   # "gpt-5.2"
    "model_project_id": settings.default_model_project_id,
}
```

This shape exists specifically to dodge the open `#524` defect (`temperature`
+ a non-`"none"` `reasoning_effort` 400s on the project's reasoning-capable
default model). It works fine for tests that only Save/reload and never
actually send a chat message.

**But it does NOT support an actual chat predict round trip.** Built a test
that: (1) pre-fills the composer via a conversation-starter chip click, (2)
clicks `chat-send-button`. On a `reasoning_effort:"none"` agent, the composer
stayed populated with the pre-filled text — **no `POST
.../elitea_core/conversations/prompt_lib/{project}` fired at all**, no
console error, no failed network response. Silent client-side no-op.
`wait_for_chat_response()` then legitimately timed out after the full 60s
because there was never a new message to wait for.

## Root cause (not fully RCA'd — workaround confirmed, not the "why")

Not confirmed whether this is a UI-side guard (composer refuses to submit for
a `reasoning_effort:"none"` participant) or a backend rejection the frontend
swallows. Not filed as a defect — no case currently asserts against
`reasoning_effort:"none"` sending an actual message, so no known-affected
case to file against. Worth a fresh RCA if a future case needs this exact
combo.

## Fix

Use plain `AgentAPI.create_agent(name, description, instructions)` instead —
it uses `_default_llm_settings()`: `reasoning_effort: "medium"`,
`temperature: None` (the "matches UI-created agent defaults" shape, per that
function's own docstring). Confirmed working immediately, and matches the
pattern `test_agent_embedded_chat_send_message.py` (a merged, passing test
that DOES send + wait for a real response) already uses.

## Rule of thumb

- Test only Saves/reloads, never sends a chat message → either payload shape
  is fine; `reasoning_effort:"none"` is the #524-safe minimal shape.
- Test sends a chat message and asserts a response → use plain
  `AgentAPI.create_agent()` (or an explicit `reasoning_effort:"medium"` /
  `temperature:None` payload). Diagnose fast via Playwright MCP against a
  known-working agent (e.g. the shared fixture `elitea-1736-conversation-agent`,
  id 6732) with `browser_network_requests` filtered to `conversations` — a
  missing POST after the Send click is the tell, not a console/network error.
