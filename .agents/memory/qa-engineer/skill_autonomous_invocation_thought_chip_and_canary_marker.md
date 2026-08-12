---
name: Skill autonomous invocation — thought-process chip + canary-marker technique
description: chat-answer-tool-chip reads "Skill: {name}" for skill invocations; use a canary marker (not a plausible real transform) to prove an unattached skill was never invoked
type: reference
---

## Thought-process chip for skill invocation (ELITEA-2607 analysis, 2026-08-12)

`ActionView.jsx` (`../EliteaUI/src/components/Chat/ActionView.jsx:196-217`)
special-cases `action.toolMeta.toolkit_name === 'skills'`: the
`chat-answer-tool-chip` inside `chat-answer-thought-accordion` reads exactly
`"Skill: {skill-name}"` instead of the usual `"{toolkit}: {tool}"` toolkit-call
form. Confirmed live: attach one skill to a fresh agent, send a message
matching its description trigger with NO `~mention`, and the accordion (already
auto-expanded) shows the chip. Existing handles already scope this correctly —
`AgentDetailPage.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR` /
`CHAT_ANSWER_TOOL_CHIP_SELECTOR` (`automation/pages/agent_detail_page.py:189-191`).
No new testid needed for this class of assertion.

## Canary-marker technique for "skill X was never invoked" security assertions

When a case requires proving a specific skill (or tool/toolkit) was NEVER
invoked — not just "the response looks normal" — do NOT give that skill a
plausible real-world instruction (e.g. "translate to Spanish"). A correct real
transform is indistinguishable from the base LLM answering the same prompt
with ZERO skill involvement (an LLM can translate "hello" → "hola" from its own
general knowledge without any skill firing), so the assertion can't
distinguish "skill fired correctly" from "skill never fired, LLM answered
anyway" — it proves nothing either way.

Instead, give the untested/should-never-fire skill an instruction whose output
could ONLY come from that skill's own instructions actually executing — a
canary marker, e.g. "respond ONLY with the exact literal string
ZZ<UNIQUE>_FIRED_ZZ". Assert the marker is absent (case-insensitive substring
match — an LLM could echo it in altered case if it partially leaked) from the
response, AND that no `chat-answer-tool-chip` for that skill's name appears in
the thought accordion. Two independent negative checks (text + chip) catch a
UI-vs-backend disagreement the same way the project's existing dual-checks
(DOM + API ground truth) do elsewhere in the suite.

Live-verified (2026-08-12, project 399, localhost): unattached skill with a
canary-marker instruction, adversarial prompt explicitly inviting it by name
("...use your translator skill if you have one") — canary never appeared, no
chip for it, agent replied "I don't have a translator skill available."
Security invariant holds; this is NOT a defect pattern to watch for, just the
correct technique for testing it.
