---
name: Skill double-invocation — assert chip count, not chip presence
description: ELITEA-2609 — explicit ~mention + autonomous context-match on the same message invokes a skill exactly once; the assertion must be .count()==1, not .to_be_visible()
type: project
---

Confirmed live (ELITEA-2609, 2026-08-12): sending `~{skill-name} {text that
ALSO independently matches that skill's own description trigger}` — i.e. an
explicit `~mention` AND an autonomous context-match co-occurring on ONE
message — invokes the skill exactly ONCE. No double-injection defect.
Product is correct.

**Assertion-shape gotcha for any "invoked exactly once" / "no
double-injection" test on this surface**: a chip-*presence* assertion
(`expect(chip).to_be_visible()`) does NOT falsify double-injection — it
would still pass even if the skill fired twice and produced two
`chat-answer-tool-chip` elements reading `"Skill: {name}"`. The load-bearing
assertion is `.locator(CHAT_ANSWER_TOOL_CHIP_SELECTOR).count() == 1` (or
`to_have_count(1)`), scoped inside `get_outer_thought_accordion()`.

Also prefer a **markdown/structured** transform (heading + list) over a flat
prose transform (e.g. plain uppercase) as the deterministic skill
instructions when testing this specific scenario: a double-injection defect
on a structured response would show as a duplicated heading/list block,
which is visually/structurally distinctive. "Still all-uppercase" text is
compatible with either 1 or 2 invocations and can't distinguish them on its
own — the chip count is what actually proves it.

Full AFS:
`test-specs/skills/lextend_skill-explicit-autonomous-invocation-coexistence_ELITEA-2609.md`.
Digest: `test-specs/skills/_surface.md` § "Explicit `~mention` + autonomous
context-match on the SAME message".
