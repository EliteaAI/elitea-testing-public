---
name: Subagent skill isolation confound
description: Master's own unconditional-trigger skill can fire on delegation turns, confusing whole-message text assertions — assert the nested-accordion chip instead
type: project
---

When testing "does a subagent bleed the parent/master's skills into its own
execution" (ELITEA-2608 shape), the isolation MECHANISM is correct: a
subagent's nested thought-accordion details container
(`chat-answer-nested-agent-accordion-details-{agent_name}`, ELITEA-1951's
existing handles) only ever shows the subagent's OWN attached skill's
`chat-answer-tool-chip` (`"Skill: {name}"`), never the master's — confirmed
live for both a skill-attached and a skill-free subagent.

**Confound:** if the master agent ALSO has its own skill attached with an
unconditional/unscoped trigger description ("Format all output in
UPPERCASE" — no "only when..." clause), the LLM reads that as "always" and
can autonomously invoke it on the master's OWN top-level turn — even one that
purely delegates-and-relays to a subagent — producing a transformed
whole-message rendered response. This chip appears in the OUTER
thought-accordion region (sibling to the nested accordion's summary
heading), never inside the nested details container — that placement is the
disambiguator. It is NOT a bleed/isolation bug; it's the master's own,
independent, correctly-scoped-to-itself autonomous skill invocation (the
same behavior ELITEA-2607 already proves works), just confusing to a
whole-message-text assertion.

**Fix for future tests in this shape:** give any master/parent-level skill a
narrowly-scoped, intent-specific trigger description (mirror ELITEA-2607's
`"Use this skill ONLY when..."` convention) so it has no reason to fire on a
plain delegation turn, AND always treat the nested-accordion chip
presence/absence as the PRIMARY, deterministic assertion — never rely on the
whole-message text alone to prove subagent-level isolation.

Full case: `test-specs/skills/l3_subagent-skills-isolation_ELITEA-2608.md`.
