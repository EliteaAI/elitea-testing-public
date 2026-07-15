---
name: ELITEA-1793 participant-removal testid map + dynamic-testid grep gotcha
description: PR #52 rework — reuse map for switch-participant/mention-list testids, 5 new testid specs for the chat participant-removal flow, and a durable methodology lesson about template-constructed testids evading literal grep
type: feedback
---

## Context

Analyst-slot rework of ELITEA-1793 ("ghost skill after agent participant
removed", issue #35) — PR #52 added 9 raw non-testid methods to
`automation/pages/chat_page.py` for the chat participant-removal + mention-
popper flow. Amended `test-specs/skills/l3_ghost-skill-not-shown-after-agent-participant-removed_ELITEA-1793.md`
in place with a testid-only Handles Reference + PROVENANCE column.

## Reuse cases confirmed (implementer missed these — testids already existed)

- `is_switch_agent_button_visible()` → use existing `switch_participant_button`
  field (`chat-switch-participant-button`, `AgentEditorPanel.jsx:219`, draft
  EliteaUI#541 — added for ELITEA-1736).
- `open_mention_skill_popper()` / `is_skill_in_mention_popper()` → use existing
  `mention_skill_list` field + `MENTION_SKILL_ITEM` class constant
  (`skill-mention-list` / `skill-mention-item-{name}`,
  `MentionSkillList.jsx:56,81`, draft EliteaUI#540 — added for ELITEA-1735).

## 5 new testids specced (participant-removal flow had zero prior testid coverage)

| Testid | Location | Shape |
|---|---|---|
| `skill-mention-list-empty` | `MentionSkillList.jsx:67` (empty-state `Box`) | static |
| `chat-participants-badge-{section}` | `CollapsedPerticapantsList.jsx:218` | dynamic, only `.format("agents")` used by this case |
| `chat-participants-popper` | `CollapsedParticipantsDropdown.jsx:136` (`Paper`) | static (only one entity-type section open at a time) |
| `chat-participant-row-{uniqueId}` | `ParticipantItem.jsx:250` (`contentWrapper` Box) | dynamic via existing `getChatParticipantUniqueId()` helper |
| `chat-participant-remove-button` | `DeleteParticipantButton.jsx:75` | static, scoped via the row's dynamic testid |

Deliberately did NOT testid `EditParticipantButton.jsx` ("Edit agent") — this
case never clicks it (scope rule: testid only what the test touches).

## Durable lesson: template-constructed testids evade a literal `git grep`

A plain `git grep -n "agent-actions-menu-button"` (and `delete-agent-menuitem`)
came back **empty** on both `origin/main` and `origin/automation/testids` —
looking exactly like a "needs-adding" gap, even though `automation/pages/agent_detail_page.py`
already uses both as `LocatorDescriptor(testid=...)` from an earlier,
already-reviewed case.

Root cause: these testids are NOT literal strings in JSX — they're
constructed at runtime by a generic component from a prop:

```js
// DotMenu.jsx:346
data-testid={id ? `${id}-menu-button` : undefined}
// DotMenu.jsx:57
data-testid={testId ? `${testId}-menuitem` : undefined}
// ... testId={item.key} at the call site (DotMenu.jsx:391/452)
```

fed by `id="agent-actions"` (`ApplicationControls.jsx:219`) and
`key: 'delete-agent'` (`DeleteApplicationButton.jsx:63`) — both on `main`.

**Lesson: before concluding a testid "doesn't exist" from an empty literal
grep, check whether the consuming component builds `data-testid` from a
prop/variable (`${id}-...`, `${testId}-...`) rather than a literal string —
trace the prop back to its call site instead of trusting the negative grep.**
This generalizes beyond `DotMenu`: any shared dropdown/menu/list component in
this codebase may follow the same `id`/`key`-templated pattern
(`ControlsDropdown.jsx` wraps `DotMenu` for agent/skill/toolkit/credentials
controls alike).

## Also confirmed out of scope for this rework

`automation/components/mui.py`'s `Dialog` helper (`[role="dialog"]` +
`button:has-text(...)`) is pre-existing shared framework infra reused across
~15+ flows, not new code PR #52 introduced — retrofitting it to testid is a
framework-wide change outside a single-case rework's scope. Left as-is.
