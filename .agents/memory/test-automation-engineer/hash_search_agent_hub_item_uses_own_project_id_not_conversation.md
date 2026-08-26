---
name: Hash-search Agent-Hub item uses its own project id, not the conversation's
description: application_{agent_id}_{project_id} uses the agent's OWN home project (entity_meta.project_id), not settings.elitea_project_id
type: feedback
---

## What

`getChatParticipantUniqueId()` (EliteaUI `participants.helpers.js`) builds a
participant's unique id as `{entity_name}_{entity_meta.id}_{entity_meta.project_id}`
— the LAST segment is the participant's OWN home project, not the current
conversation's project.

For an agent added via the `#` hash-search dropdown, this matters because the
dropdown mixes CURRENT-project and Agent-Hub ("Public") sourced agents in one
result set (see ELITEA-2206). When a test resolves the FIRST agent-type card
dynamically (per the AFS's own "don't hardcode a name" resilience requirement),
that first card is routinely Agent-Hub-sourced — its `entity_meta.project_id`
is the PUBLIC project constant (`VITE_PUBLIC_PROJECT_ID`, `1` in this env), NOT
`settings.elitea_project_id` (`399` in this env).

Live-confirmed (ELITEA-2207/2469 session): `chat-hash-search-item-1_6` ("AA")
→ real participant row testid `chat-participant-row-application_6_1`, NOT
`application_6_399`.

## Why it bites

`ChatPage.get_agent_participant_row()` / `remove_agent_participant()` /
`hover_agent_participant_row()` all originally hardcoded
`settings.elitea_project_id` when building the unique id — correct only when
the selected agent's home project equals the conversation's project. An
exploration session that happens to pick a same-project agent (e.g. one of the
account's own custom agents) will NOT surface this bug; only a genuinely
dynamic "first agent card" selection reliably hits it, because the account's
'#' results tend to list Agent-Hub agents first.

## Fix pattern

`get_agent_participant_row()` gained a backward-compatible optional
`agent_project_id` param (default unchanged = `settings.elitea_project_id`).
Read the item's own project id off its hash-search card testid
(`chat-hash-search-item-{project_id}_{id}` — parse with
`ChatPage.get_hash_search_item_ids(item)`) and pass it explicitly whenever the
selected participant may be Agent-Hub-sourced.

## Where

`automation/pages/chat_page.py` — `get_agent_participant_row()`,
`get_hash_search_item_ids()`. Origin: ELITEA-2207/2469 implementation,
2026-08-19.
