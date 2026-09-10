---
name: chat-participant-row callers split by RENDERER — user rows and entity rows are different components
description: PARTICIPANT_ROW's six call sites split across UserMenu.jsx (users, safe) and ParticipantNormalCard.jsx (agents/pipelines/toolkits/mcps); only the latter diverged on main.
type: reference
aliases: [PARTICIPANT_ROW callers, participant row blast radius, remove_agent_participant, UserMenu vs ParticipantNormalCard]
tags: [area/locators, area/chat]
created: 2026-09-10
updated: 2026-09-10
---

## Two renderers, one testid family

`chat-participant-row-*` is emitted by **two** unrelated components, so a change
to one affects only half the callers. Verified 2026-09-10 on
`origin/main` vs `origin/automation/testids`:

| `chat_page.py` method | `unique_id` shape | Renderer |
|---|---|---|
| `hover_agent_participant_row` (:7377) | `application_{id}_{project}` | `ParticipantNormalCard.jsx` |
| `get_agent_participant_row` (:7434) | `{entity_type}_{id}_{project}` | `ParticipantNormalCard.jsx` |
| `remove_agent_participant` (:7481) | `{entity_type}_{id}_{project}` | `ParticipantNormalCard.jsx` |
| `hover_participant_user_row` (:7569) | `user_{user_id}_` | `UserMenu.jsx` |
| (:7664) | `user_{user_id}_` | `UserMenu.jsx` |
| (:7722) | `user_{user_id}_` | `UserMenu.jsx` |

`PARTICIPANT_ROW_PREFIX` (`[data-testid^="chat-participant-row-"]`) is
shape-agnostic and resolves against both.

## Why this matters when scoping exposure

A spec can be exposed through a method you did not expect. `#2013`'s divergence
hit only `ParticipantNormalCard.jsx`, so "user rows are fine" was true — but
`test_team_users_mention_and_remove_participants.py`, which reads as a *users*
spec, **also calls `remove_agent_participant()`** and was therefore exposed.
**Enumerate by method call, never by the spec's apparent subject.**

Specs reaching a `ParticipantNormalCard` method (2026-09-10):
`test_ghost_skill_after_agent_removed.py`,
`test_chat_agent_starters_add_remove.py` (all three),
`test_team_users_mention_and_remove_participants.py`, `test_chat_interface.py`.

## Collision note

Agents **and** pipelines both render through `ParticipantNormalCard`, so any
bare-id row testid collides for agent id `N` + pipeline id `N` in one
conversation — reachable, since these methods already accept
`entity_type="pipeline"`. That is what `getChatParticipantUniqueId()` prevents.

Related: [[testid_value_can_diverge_while_name_matches]]
