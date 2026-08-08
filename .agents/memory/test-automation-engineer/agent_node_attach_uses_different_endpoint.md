---
name: Agent node attach uses different endpoint
description: Pipeline Tools-section Agent attach persists via /application_relation/, not /tool/ like Toolkit/MCP
type: feedback
---

Confirmed live 2026-08-08 (ELITEA-2038 analysis+implementation): the pipeline
detail form's TOOLS section renders 4 "+ X" buttons (Toolkit/MCP/Agent/
Pipeline) that all look identical and share the same `ToolMenu.jsx` /
`UnifiedDropdown` popper component (same `toolkit-menu-item` testid on every
row). Despite the shared UI, **Agent (and Pipeline-as-tool) attach fires a
genuinely different mutation** from Toolkit/MCP:

- Toolkit/MCP attach → `PATCH .../elitea_core/tool/prompt_lib/{project}/` →
  `201`, via `ToolMenu.jsx`'s generic toolkit-attach path.
- Agent (or nested-pipeline) attach → `PATCH .../elitea_core/application_relation/
  prompt_lib/{project}/{agent_id}/{agent_version_id}` → `201`, via
  `useAgentPipelineAssociation.hooks.js`'s `updateApplicationRelation` RTK
  mutation (`handleAssociateAgent`).

Both auto-persist immediately on popper selection (same *behavior*), so a
page-object method waiting on the wrong endpoint string doesn't fail loudly —
it just times out on `page.expect_response()`, which reads as a flaky/slow
step rather than a wrong-assumption bug. `PipelineDetailPage.select_mcp_in_popper()`
(Toolkit/MCP) and `select_agent_in_popper()` (Agent, added ELITEA-2038) are
deliberately separate methods for exactly this reason — don't try to
generalize them into one "select_in_popper(kind, ...)" without threading the
endpoint through.

Also: `AgentNode.jsx` is its OWN component (not a `BaseToolNode.jsx` caller
like Toolkit/MCP/Custom), so its testids live behind a local
`AGENT_NODE_TESTID_PREFIX` constant, not `BaseToolNode.jsx`'s
`TEST_ID_PREFIX_BY_NODE_TYPE` map. Its Input-mapping schema has exactly one
required key (`task`, "Task"), Type defaults to **"F-String"** (not "Fixed"
like every sibling tool-parameter field), and `CommonInterruptSettings`
never renders "Structured output" at all (`showStructuredOutput={false}`).

Full trace: `test-specs/pipelines/l2_pipeline-agent-node-integration_ELITEA-2038.md`
and the "Agent node" section of `test-specs/pipelines/_surface.md`.
