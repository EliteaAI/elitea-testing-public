---
name: Skill-builder chip — hover-to-reveal Open button, no auto-participant, rephrased description
description: ELITEA-3366 analysis — generated-entity-chip's "Open entity" button only appears on hover (cold click times out); a chat-created Skill is never auto-added as a participant (source-traced, local-state-only handler); Description field is AI-rephrased, not verbatim; chip label is the raw slug name, not "Skill: {Name}".
type: feedback
tags: [area/chat, area/skills, type/locator-gotcha]
created: 2026-10-19
---

## What happened

Analysing ELITEA-3366 (skill creation from chat → chip → Canvas) live against
DEV, 6 independent runs.

## Key findings

1. **`[data-testid="generated-entity-chip"]`'s "Open entity" button
   (`aria-label="Open entity"`, no testid) is hover-revealed** — a plain
   `.click()` without a preceding `.hover()` on the chip times out (element
   exists, `is_visible()` is false until hover). Same `isHovering` state
   pattern as several other hover-revealed controls already documented in
   this project (bucket-row DotMenu, agent card actions).
2. **Chip label is the raw created-entity `name` field, no `"Skill: "`
   prefix** — `GeneratedEntityChip.jsx`'s `label={entity.entity_name}` is a
   bare pass-through. Case authors across this ELITEA-33xx family (chat
   skills/project-context builder) write `"Skill: {Display Name}"` in their
   Expected Results — that's case-text drift, not a defect. Assert the
   actual created entity's `name`, read via the Skill API or the opened
   canvas's own `skill-name-input-field`, never a literal prefixed string.
3. **A chat-created Skill is NEVER auto-added as a chat participant** —
   confirmed both live (no participant UI) and by tracing
   `GeneratedEntityChip` → `ChatBox.jsx`'s `onEntityCreated` →
   `useEditSkill.hooks.js`'s `onShowSkillEditor` on `origin/main`: for
   `entity_type === 'skill'` the whole chain is local React state only, no
   `addNewParticipants` call anywhere. Contrast with Agent creation
   (ELITEA-2166), which DOES auto-add + auto-activate via a different hook
   (`useAgentCreation.js`) — don't assume parity across entity types in this
   "created-entity chip" family; check the specific `entity_type` branch in
   `ChatBox.jsx`'s `onEntityCreated` before asserting either way.
4. **Description field in the created Skill is AI-rephrased, not a verbatim
   copy of what the chat message stated** — Instructions WAS byte-exact in
   all 6 runs, Description never was. Assert topical content (substring/
   keyword match), not exact string equality, for Description in this
   family.
5. The AI invokes `post_elitea_core_skills` TWICE per successful creation
   turn (2× `chat-answer-model-chip` reading the same tool name) — not
   investigated further, not case-relevant, just surprising if you're
   counting tool-call chips as a signal elsewhere.

Full detail + Concrete Handles table:
`test-specs/chat-interface/l1_skill-creation-happy-path-with-chip-and-canvas_ELITEA-3366.md`
and `test-specs/chat-interface/_surface.md`'s own new section.

Related: [[searchbar_activation_is_submit_not_live_filter]] (another
hover/activation-mode gotcha family), [[case_describes_nonexistent_control_is_defect_not_clarification]]
(the reverse-masking boundary this case's chip-label finding sits just
inside of — live product correct, case text imprecise, so clarification
not defect).
