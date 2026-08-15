---
name: Participants-add endpoint rejects reasoning_effort "none" that agent-create silently accepts
description: POST .../applications/... accepts llm_settings.reasoning_effort="none"; POST .../participants/... for that same agent 400s (enum only allows low/medium/high) — asymmetric validation between the two endpoints
type: feedback
---

## Context

Found during ELITEA-2177/2178/2465 analyst cluster pass (chat conversation
starters — add/remove agent participant mid-conversation), localhost:5173,
project `Private` (id 399). Distinct from the already-documented
`agent_create_400_temperature_reasoning_conflict.md` finding (#524) — that
one is about `temperature` + non-`'none'` `reasoning_effort` conflicting at
CREATE time. This one is about the literal string `"none"` specifically,
and it fails a DIFFERENT endpoint.

## Finding

Creating a disposable agent via `AgentAPI.create_agent_full()` (or a raw
`POST .../elitea_core/applications/prompt_lib/{project}`) with
`llm_settings.reasoning_effort: "none"` succeeds — `201 Created`, the value
persists on the agent's `version_details.llm_settings.reasoning_effort`
field untouched, no validation error at create time.

Adding that SAME agent as a chat participant
(`POST .../elitea_core/participants/prompt_lib/{project}/{conversation_id}`,
fired by the composer's "+ → Agents → select" flow) then returns `400`:

```json
{"error": "1 validation error for EntitySettingsApplication\nllm_settings.reasoning_effort\n  Input should be 'low', 'medium' or 'high' [type=literal_error, input_value='none', input_type=str]"}
```

The participants-add endpoint validates against a stricter Pydantic literal
enum (`low`/`medium`/`high` only — no `none`, no null-equivalent string) that
agent-creation's own endpoint does not enforce. An agent created with the
`"none"` workaround (the pattern several prior AFS/memory entries recommend
for avoiding the temperature-conflict 400 at create — see
`agent_create_400_temperature_reasoning_conflict.md`'s "none" + no-temperature
shape) is therefore silently **uncreatable as a chat participant** until
fixed or worked around.

## Workaround (confirmed working)

Omit `reasoning_effort` from the create payload entirely (don't set the key
at all — leave it `null`/absent) rather than setting the literal string
`"none"`. Confirmed live: an agent created with `llm_settings` carrying no
`reasoning_effort` key at all adds cleanly as a chat participant, no 400.

```python
"llm_settings": {
    "max_tokens": -1,
    "model_name": settings.default_model_name,
    "model_project_id": settings.elitea_project_id,
    # reasoning_effort intentionally OMITTED — "none" 400s participants-add
},
```

## For future sessions

- If a test needs to create an agent AND add it as a chat/conversation
  participant (not just use it standalone via its own detail page), do NOT
  reuse the `reasoning_effort: "none"` workaround from the create-time
  temperature-conflict pattern verbatim — it will 400 at the participant-add
  step instead. Omit the field, or set a valid `low`/`medium`/`high` value.
- This is a real backend inconsistency (asymmetric endpoint validation) —
  worth a product ticket if it recurs or blocks a case outright, but wasn't
  filed separately this pass since a workaround exists and no case's own
  subject was blocked by it (both #524's known-defect umbrella and this note
  cover agent-creation LLM-settings quirks; a human triaging #524 may want to
  fold this in as a related finding rather than a wholly separate ticket).
