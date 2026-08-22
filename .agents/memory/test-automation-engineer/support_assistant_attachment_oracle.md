---
name: Support Assistant refuses to echo identifiers from attachments
description: Plant an ordinary-prose fact and ask a comprehension question; a "repeat this token" oracle is refused by the assistant's guardrail
type: project
aliases: [attachment oracle, support assistant guardrail, plant a token, ZEPHYR token, content-grounding assertion]
tags: [area/support-assistant, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The refusal

Asking the Support Assistant to repeat an opaque identifier that was planted inside an
uploaded file is refused by a guardrail:

- `The secret project codename is ZEPHYR-4417.` -> *"I can't help extract or repeat secret
  codename values from attachments."*
- Neutralised to `Build identifier: <TOKEN>` -> *"I can't help extract or repeat secret
  identifiers from attachments."*

So the trigger is **relaying an opaque identifier out of an attachment**, not the word
"secret". Wording changes do not get around it.

## What works

Plant an ordinary-prose FACT and ask a comprehension question:

- file: `The project mascot is the {word}.` (per-run word from a small list)
- prompt: *"According to the attached file, what is the project mascot? Answer with the
  single word."*

Same oracle strength (the word exists only inside the upload) and no guardrail collision.
Green twice consecutively in ELITEA-2421.

## Why it matters beyond one case

The assistant genuinely DOES read attachments — it answers about their content. A refusal is
not evidence the attachment pipeline is broken, and it must not be filed as one (that error
is how false bug #1584 happened). It is also **non-deterministic**: the same token oracle
worked once during analysis and refused twice hours later, so any assertion built on the
model's willingness is a merge-gate flake risk.

Related: [[project_briefing]] · surface digest `test-specs/support-assistant/_surface.md`
quirks 39/48.
