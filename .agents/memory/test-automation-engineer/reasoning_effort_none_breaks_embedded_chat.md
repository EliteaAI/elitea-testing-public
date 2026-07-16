---
name: reasoning_effort none breaks embedded chat conversation creation
description: The established "reasoning_effort:none + no temperature" #524-workaround pattern (used by several existing agent-creation fixtures) avoids the agent-creation 400, but breaks embedded-chat conversation creation with a 500 whenever the test actually opens the chat. Use reasoning_effort:"low" instead for any test that sends a chat message.
type: feedback
---

## What happened (ELITEA-1897, 2026-07-16)

The existing `_build_dedicated_agent_payload()`-style helpers in this repo
(`test_agent_management.py`, `test_agent_remove_variable.py`,
`test_agent_save_as_version.py`, and others from ELITEA-1884/1888/1872/1869/1870)
all use `llm_settings: {"reasoning_effort": "none"}` with `temperature` omitted
entirely, to avoid the open #524 defect (`temperature` + a non-`"none"`
`reasoning_effort` 400s on agent *creation*). This pattern works fine for all
of those tests because none of them ever open the embedded chat — they only
save/reload the Instructions field or attach skills.

ELITEA-1897 is the first test in this lineage to actually send a message in
the embedded chat after creating the agent this way, and it surfaced a new,
deterministic product defect: **`POST .../conversations/prompt_lib/{project}`
(the call that opens the embedded chat panel) returns 500 Internal Server
Error whenever the agent's `llm_settings.reasoning_effort` is `"none"`.**
Filed as https://github.com/EliteaAI/elitea-testing-public/issues/560.

## How it was isolated

Held the agent's `model_name`/`model_project_id` fields constant (fully
omitted both times) and flipped only `reasoning_effort`:
- `"none"` → conversation POST 500s. Reproduced twice, deterministic.
- `"medium"` → conversation POST 201s, chat opens and responds normally.
- `"low"` → conversation POST 201s, chat opens and responds normally.

Also ruled out `settings.default_model_name`/`default_model_project_id`
(`config.py`'s stale `"gpt-5.2"`/`0` defaults, which don't resolve to a real
model in this project) as the cause — the 500 occurred identically whether
those fields were set or omitted. Only `reasoning_effort` mattered.

## The follow-on gotcha: "medium" is too slow

`reasoning_effort: "medium"` avoids both #524 and #560, but drives noticeably
slower "thinking" latency on this project's default reasoning-capable model —
observed live to still be spinning past a 30s `AI_RESPONSE_TIMEOUT` wait (a
genuine latency finding, not a hang/defect). `reasoning_effort: "low"` (fast,
minimal-step reasoning per the UI's own `ReasoningSlider` tooltip) avoids all
three problems: no #524, no #560, and responds well within a normal 30s wait.

## Rule of thumb for future agent-creation-via-API tests

- Test only saves/reloads Instructions, attaches a toolkit/skill, or otherwise
  never opens the embedded chat → `reasoning_effort: "none"` (existing
  pattern) is still fine.
- Test sends a message in the embedded chat and waits for a real AI response
  → use `reasoning_effort: "low"` instead. Omit `temperature` and the model
  fields (`model_name`/`model_project_id`) entirely either way — the backend
  applies its own valid default (same as what the plain UI create-form path
  does, which never sets `llm_settings` model fields).
