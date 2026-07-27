---
name: Bug #524 (agent-create 400) confirmed NOT to affect skill create
description: Agent-creation's temperature/reasoning_effort 400 conflict (#524) does not reach the Skill entity's create endpoint — different endpoint, different payload shape, no temperature/reasoning_effort fields at all. Skills-module cases are not blocked by #524.
type: project
---

## Context

`blocker_524_blocks_all_agent_creation.md` (existing memory) documents that
open bug `EliteaAI/elitea-testing-public#524` blocks **agent** creation
end-to-end — both the UI form and `AgentAPI.create_agent()` — because the
platform's default LLM settings send `temperature` together with
`reasoning_effort` on a reasoning-capable model, and the API rejects that
combination with a 400.

## What was checked for #73 (ELITEA-1990)

Dispatched the analyst with an explicit instruction to check whether the
Skill "Build with AI" flow shares this dependency (skills can indirectly
create/reference agent-like entities). Confirmed via two independent live
runs against the real DEV backend:

- Skill creation goes through `POST
  /api/v2/elitea_core/skills/prompt_lib/{projectId}` — a **different**
  endpoint from the Agent entity's `/applications/prompt_lib/{projectId}`.
- The Skill create payload (from `GenerateSkillModal.jsx handleApprove`) is
  `{name, description, versions: [{name, instructions}]}` — **no**
  `temperature` / `reasoning_effort` fields present at all.
- Both live runs returned `201 Created`, zero console/network errors.

## Action for future dispatches

Before parking a **skills-module** case as blocked on #524 (per the
existing blocker-524 memory's "check before dispatching" guidance), know
that skill creation itself is confirmed clean — #524 only applies to cases
whose flow actually creates an **Agent** (or hits `AgentAPI.create_agent()`
/ the `agent_id` fixture). A case that merely *attaches* an existing agent,
or that only touches Skills, does not need to be parked on #524 without
further evidence.
