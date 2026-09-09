---
name: Hardcoded count assertions silently mix product STRUCTURE with product DATA
description: Before pinning any N-visible-things count, split what the frontend hardcodes from what the backend serves — pin the first, derive the second from the response
type: feedback
aliases: [chip count, filter rail count, to_have_count drift, hardcoded count, 11 chips, category rail, count assertion]
tags: [area/assertions, area/agent-hub, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The failure mode

A "verify the layout is intact" step gets automated as `assert count == N`. That single
number almost always spans two things that change for unrelated reasons:

- **Product STRUCTURE** — frontend constants/JSX. Changes only when the UI team ships a
  feature. A red test here is *correct and informative*.
- **Product DATA** — whatever the backend serves. Changes when an admin edits content, at
  any time, with no code change. A red test here is *pure noise*.

Pinned together, they are indistinguishable, and the failure message names neither.

Worked case: Agent Hub catalog filter rail, `assert chip_count == 11` (ELITEA-2367, card
#2079). Went red when `EliteaAI/EliteaUI@18170f71` (EL-6238, 2026-09-07) added a third
Featured chip. Real split: 3 frontend constants + the trailing "Other" constant, versus 8
backend category tags from `GET /elitea_core/agent_categories/prompt_lib/{id}`.
**Bumping 11 → 12 repeats the bug** — it re-pins the data half. Two specs paid for this
(#2079, #2099).

## The shape that works

1. Derive the data half from **the response the page itself fetched** —
   `page.expect_response(...)` around `navigate()`. This is `.agents/testing.md`
   § Fidelity policy's named pattern ("the response is the oracle"), so it is **not**
   substitution and owes no Fidelity Declaration. Never `page.route` — that would be a
   terminal substitution.
2. Pin the structure half by **exact testid**, as a named constant with a source pointer
   in its comment, so the next UI change is a one-line edit not an archaeology dig.
3. Assert **both** an exact count (catches duplicate/dropped items — set equality alone
   cannot) **and** set membership, with a failure message naming `missing:` / `unexpected:`.
4. ⚠️ **`to_have_count` matches ATTACHED elements, including hidden ones.** A count +
   membership check passes on a collapsed/`display:none` container. If the step is about
   *layout integrity*, add explicit **head and tail** visibility assertions — that is what
   makes it have teeth.

## The tell to watch for

An assertion whose expected value appears **nowhere in the TMS case text** and was an
analyst Axis-2 addition. That is exactly where an unexamined constant hides. Ask what
*produces* the number before writing it down.

Related: [[[../../../test-specs/agent-hub/_surface.md|agent-hub surface digest]]]
