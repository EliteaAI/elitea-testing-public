---
name: A conversation's persona snapshot is meta.persona on the API record, never in the UI
description: "Settings apply to new conversations only" cases about personality are assertable via meta.persona / instructions on the conversation response — no LLM-tone judgment needed
type: feedback
aliases: [meta.persona, conversation persona, new conversations only, personality snapshot]
tags: [area/chat, area/settings, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The finding

A case like *"personalization settings only apply to new conversations"* looks un-automatable,
because there is **no per-conversation personality indicator in the UI** — `meta.context_strategy`
is the only conversation meta the front end consumes, and judging the assistant's *tone* is
nondeterministic LLM output.

The conversation **record** carries the snapshot, on the two endpoints the normal user path
already hits:

- `POST /api/v2/elitea_core/conversations/prompt_lib/<project>` → **201**, on sending the first message
- `GET  /api/v2/elitea_core/conversation/prompt_lib/<project>/<id>` → **200**, on opening one

Both return `meta.persona` plus a top-level **`instructions`** string already resolved from
that persona's slot.

## Why it is honest, not a substitution

The UI action is the trigger; the response body is the oracle. Nothing is fabricated,
injected, or seeded through a wrong interface — this is the response-as-oracle pattern in
`.agents/testing.md` § Fidelity policy. The `201` also lands **before the model answers**, so
such a spec never waits on an AI response and stays clear of the known LLM trigger-side flake
class.

## Live evidence (2026-08-29)

| Conversation | Default persona at creation | `meta.persona` | `instructions` |
|---|---|---|---|
| `9871` | Quirky (empty slot) | `"quirky"` | `""` |
| `9871` re-opened after the default moved to Nerdy | — | still `"quirky"` | still `""` |
| `9872` | Nerdy (slot held text) | `"nerdy"` | the marker text |

**Generalise it:** before calling a "settings apply to X only" case un-automatable for lack of
a UI surface, check whether the *record* the action creates carries the snapshot. It often does.

Related: [[per_persona_instructions_map]]
