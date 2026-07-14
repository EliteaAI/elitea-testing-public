---
name: ELITEA-1735 handles-only rework testid map
description: Full testid inventory (existing + needs-adding) for the agent-skills attach/mention flow, verified live against origin/main + origin/automation/testids on 2026-07-14; the "patient zero" case for the amend-testid-away anti-pattern.
type: feedback
---

## Context

PR #39 (ELITEA-1735) shipped with several non-testid handles because an earlier
analyst pass amended a testid request away ("the accessible name IS stable, no
testid needed" for the agent add-skill button). Per `.agents/role-overrides.md`
§ Implementer slot, amending a testid request away is out of contract — satisfy
it or escalate to the lead, never re-scope down. This case is the canonical
example cited in role-overrides.md itself ("the ELITEA-1735 pattern").

Phase 3 reworked the AFS's Handles Reference to be testid-only, fully
live-verified. Recording the map here so future cases touching the same
components (SkillMenu, ApplicationSkills, SkillCard, MentionSkillList,
ClearChatButton) don't re-derive it.

## Confirmed on `origin/main` (git grep, fresh fetch, this run)

- `chat-message-input` — `src/ComponentsLib/Chat/UserInput.jsx:360` (`slotProps.htmlInput`)
- `chat-send-button` — `src/[fsd]/features/chat/ui/chat-button/SendButton.jsx:76`
- `skill-test-last-response` — `src/[fsd]/features/chat/ui/chat-box/ApplicationAnswer.jsx:593` (conditional: last message only, else `chat-answer-content`)
- `toolkit-menu-item` — `src/components/UnifiedDropdown.jsx:303,339` — shared popper item testid, generic name but confirmed live for the SKILL-attach flow specifically (not just Toolkits) by attaching a real skill and reading `data-testid` off the resulting live DOM node.

All four also present on `origin/automation/testids` (same lines).

## Confirmed needs-adding (no hit on main or automation/testids, no open PR)

- Agent add-skill button (`SkillMenu.jsx`, `BaseBtn` "+ Skill") — has visible
  text "Skill" (so `getByRole('button',{name:'Skill'})` DOES technically
  resolve) but zero `data-testid`/`aria-label`. Accessible-name stability is
  irrelevant to policy — spec `testid needed: agent-add-skill-button` anyway.
- Skills section container Box (`ApplicationSkills.jsx`) — `testid needed: agent-skills-section`
- Skills counter Typography ("N/5 skills added.") — `testid needed: agent-skills-counter`
- Attached skill card (`SkillCard.jsx`) — `testid needed: skill-card-{skill_id}` (dynamic, `skill_id` in scope)
- Clear-the-chat button (`ClearChatButton.jsx`, 5 consumers) — `testid needed: chat-clear-button`. Confirmed live ambiguity: `RunHistoryContainer.jsx:77` has an unrelated button with the IDENTICAL literal `aria-label="clear the chat"` — a `get_by_label(...).first` handle works only by DOM order, not contract.
- Mention popper container (`MentionSkillList.jsx`) — `testid needed: skill-mention-list`. Plain `<Box>`, no role, no testid, confirmed live via `element.evaluate`.
- Mention popper item (`MentionToolItem.jsx`, shared with `InstructionsSlashSuggestionList.jsx` via `MentionToolList.jsx`) — `testid needed: skill-mention-item-{skill-name}` via an additive optional `testId` prop (only the skill-mention consumer passes it).
- Delete-confirmation "Delete" button — still role/name (`getByRole('button',{name:'Delete'})`) with no testid anywhere; out of ELITEA-1735's own touch-scope (cleanup-only use), flagged but not blocking.

## Verification method used

Created a throwaway Skill (id 382) + Agent (id 4742) in project 399, attached
the skill via the live "+ Skill" flow, typed `~` in chat to trigger the
mention popper, read `data-testid`/`role` off every live DOM node via
`browser_evaluate`, then deleted both entities through the UI (agent first,
then skill) to leave no residue. `git fetch origin` in `../EliteaUI` ran
immediately before every git grep against `origin/main`/`origin/automation/testids`.
