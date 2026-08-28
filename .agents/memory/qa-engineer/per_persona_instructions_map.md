---
name: User instructions are stored per-persona, not globally
description: Elitea's AI-Personality "User instructions" field is a map keyed by persona — pin the persona before typing or the read-back is nondeterministic
type: feedback
aliases: [personality_instructions, user instructions, default user instructions, persona slot]
tags: [area/settings, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The trap

`/settings/ai-personality` shows one `User instructions` textarea, so it reads as a single
global field. It is not. `AIPersonalityPersonalization.jsx` writes
`personality_instructions.<persona>` — a **map keyed by persona** — and the textarea renders
only the slot of the *currently selected* persona. The field is **absent from the DOM
entirely when the persona is `none`**.

Server shape (`GET/PUT /api/v2/social/author/`):

```json
"personality_instructions": {"bare":"","cynical":"","generic":"","nerdy":"…","none":"","qa":"","quirky":""}
```

## What it means for a spec

- **Pin the persona before typing**, and read back under the same persona. Otherwise the
  assertion depends on whatever the previous run left selected.
- **Teardown must restore two things** — the persona label AND the slot's original text.
  Restoring only the persona leaves text in a slot that a later run (or another case, e.g.
  a conversation-snapshot case) will read as its own baseline.
- The per-persona **placeholder** (`No custom instructions for the <Label> persona yet…`)
  is a cheap check that the field is showing the slot you think it is.

Verified live 2026-08-29 (cluster ELITEA-2381/2382/2383/2384): text saved under `Nerdy` read
back empty after switching to `Quirky`, and reappeared on switching back.

Related: [[persona_snapshot_lives_on_the_conversation_record]]
