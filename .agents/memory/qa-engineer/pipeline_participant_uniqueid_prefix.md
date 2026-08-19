---
name: Pipeline participant uniqueId prefix differs from agent's
description: chat-participant-row uses "pipeline_" not "application_" for pipeline participants; version text is a literal name, not "ver"/"vX.Y"
type: feedback
---

## Context

ELITEA-2208/2470 analysis (chat `#` hash-search, select-a-pipeline flow),
2026-08-19 — direct pipeline-flow sibling of the ELITEA-2207/2469 agent-flow
family analysed the same session.

## The fact

`getChatParticipantUniqueId()` (`EliteaUI/src/[fsd]/features/chat/participants/lib/helpers/participants.helpers.js`)
resolves a participant's `entity_name` to `ChatParticipantType.Pipelines`
(`'pipeline'`, singular) whenever `entity_settings.agent_type === 'pipelines'`
— distinct from an agent's `'application'`. So a pipeline participant's row
testid is `chat-participant-row-pipeline_{pipeline_id}_{project_id}`, NOT
`chat-participant-row-application_{pipeline_id}_{project_id}`. Live-confirmed
via a real hover interaction: `chat-participant-row-pipeline_8056_399`.

`ChatPage.get_agent_participant_row()` / `remove_agent_participant()`
(added for ELITEA-2207/2469) both hardcode the `application_` prefix and
CANNOT resolve a pipeline participant's row as-is. Any future case touching
a pipeline participant's row/removal needs an additive generalization on
these two methods (optional `entity_type` param, or a sibling
`get_pipeline_participant_row()`/`remove_pipeline_participant()`) — same
shape as the `agent_project_id` optional param ELITEA-2207/2469 already
added to the same methods for a different reason (Agent-Hub-sourced agents).

Also: a pipeline's PARTICIPANTS-popover-row "version" text is its own
version's literal NAME (e.g. "base", "prod") — not the "ver"/"vX.Y"
auto-generated shape agents show. Don't reuse the agent family's
`re.match(r"v(er\b|\d)", ...)` regex for a pipeline row; assert only that a
non-empty version-text remainder exists after the name.

## Where the full writeup lives

`test-specs/chat-interface/_surface.md` § ELITEA-2208/2470 (exploration
digest, comprehensive) and
`test-specs/chat-interface/lextend_hash-search-select-pipeline-adds-participant-and-responds_ELITEA-2208.md`
(AFS, Automation Hints).
