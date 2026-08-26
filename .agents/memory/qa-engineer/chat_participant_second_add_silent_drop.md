---
name: Chat participant second-add silent drop (Agent/Pipeline)
description: Second Agent/Pipeline chat-participant add is silently dropped in both orders; no observable settle condition exists
type: project
aliases: [participant silent no-op, agent pipeline coexistence, "#1279", chat participants panel race]
tags: [area/chat, type/product-defect]
created: 2026-08-26
updated: 2026-08-26
---

## The fact

Adding an Agent **and** a Pipeline as participants of the same Elitea conversation drops
whichever is added **second** — silently, in **both orders**, 13 of 16 live repetitions
(2026-08-26, localhost:5173 / DEV backend, real pytest + page objects). Tracked as
EliteaAI/elitea-testing-public#1279; my evidence is commented there.

## Why it matters to a test

- **No honest wait fixes it.** The first participant's row being visible,
  `chat-switch-participant-button` being visible, and `networkidle` all resolve together at
  ~1.7-2.2 s; the measured gap between them and the failing second add was 0.00 s in 6/6
  runs. Only a fixed wall-clock delay (~1500 ms) helps, that is a banned `sleep`, and it
  still failed 1 of 4.
- **A console-error assertion cannot detect it.** The silent-drop runs have a clean
  console. The `version/prompt_lib` 400 + `icon_meta` TypeError fires only on the runs that
  SUCCEED - it is a symptom of the working path.
- Toolkit and MCP participants are unaffected (back-to-back Toolkit->MCP adds are reliable,
  ELITEA-2203's merged spec proves it). The race is specific to the version-carrying
  Agent/Pipeline types.

## Related gotcha

A brand-new, UNSENT conversation is not persisted (URL stays `/chat`, no id) - a reload
clears every participant. Persistence checks must come after the first Send.

Related: [[project_briefing]]
