---
name: Chat participants (multi-type) default-project data gap, and the mcp-vs-pipeline misconfig-warning asymmetry (#684)
description: The suite's default project (399/Private) has zero pipelines and zero MCPs, breaking any case that needs all four participant types; which projects do have them; a real defect where a broken pipeline crashes silently instead of showing the same warning UI MCPs correctly show
type: feedback
---

Discovered analysing ELITEA-2094 (chat-interface, "add Agent+Pipeline+Toolkit+MCP, verify
PARTICIPANTS panel", localhost:5173) — the first case to need all four participant types
simultaneously.

- **`${ELITEA_PROJECT_ID}` (399, "Private") — the suite's default project everywhere else —
  has ZERO pipelines and ZERO MCPs.** Confirmed live: `/pipelines/all` shows "No pipelines
  yet"; plus-menu → MCPs → "No MCPs available" / `/mcps/create` redirect. It does have agents
  and toolkits. Any future case needing a pipeline or MCP participant in the DEFAULT project
  will hit this same gap — don't assume 399 satisfies a "pipelines/MCPs exist" precondition.
  **Fix**: seed via API (`PipelineAPI.create_pipeline_with_llm_node(...)`,
  `ToolkitAPI.create_remote_mcp_toolkit(...)`) into 399 rather than switching projects — keeps
  the test isolated instead of depending on shared fixtures.
- **Project inventory as of this session** (via the sidebar project-switcher, which — new
  finding — renders each option with its own `select-option-{project_id}` testid): "Private"
  (399, 0 pipelines/0 MCPs), "Bugs & Features", "Elitea Development", "UI Testing" (400, 1
  pipeline, 0 MCPs), "Elitea Testing Team" (471, rich data across all 4 types — dozens of
  agents/pipelines, ~19 toolkits, 1 MCP). If a future analyst pass needs a project with
  existing fixture data for a quick manual check (not automated seeding), 471 is currently the
  richest.
- **`chat-participants-badge-{section}` uses SINGULAR "mcp"**, unlike the other three
  (`-agents`, `-pipelines`, `-toolkits` are all plural). Confirmed live via DOM query. A
  templated `PARTICIPANTS_BADGE.format(section)` call with `"mcps"` will silently return an
  empty/wrong selector — the existing `chat_page.py` docstrings already say `"mcp"` correctly;
  this is a live confirmation, not new code, but worth knowing before extending that surface.
- **[#684, MAJOR, filed]**: a specific pipeline (project 471, "HelloPipeline" — one of two
  same-named pipelines, id `106`/version `151`) has an orphaned/broken version record
  server-side (`GET version/prompt_lib/471/106/151` → 400). Adding it as a chat participant
  throws an uncaught `TypeError: Cannot read properties of undefined (reading 'icon_meta')` at
  `ChatBox.jsx:1516` — with **no warning UI shown at all**, the badge renders as if healthy.
  Sending a message through it then fails with "An unexpected error occurred while processing
  your request." Contrast: a genuinely misconfigured **MCP** in the same project correctly
  shows a yellow/orange warning-triangle badge + a clear in-popper "Server is disconnected!
  Reconnect it to use. Log in." message — pipelines don't get the same graceful treatment.
  Isolated via clean-room contrast, 2/2 reproductions in separate fresh conversations, real
  clicks only (no synthetic input): the pipeline's own duplicate-named sibling (2nd
  "HelloPipeline" entry, different id) added cleanly; a different, uniquely-named pipeline
  ("GenerateStory") added cleanly. Only that one entity/version pair is broken — not "any
  pipeline," not "duplicate names" generally. **Do not use this specific pipeline as a test
  fixture** — use `create_pipeline_with_llm_node` to seed a fresh, working one instead.
- **A separate MUI `Popover2`/`anchorEl` console error encountered while cleaning up test
  conversations was correctly judged self-inflicted, not filed**: it only fired when a
  conversation's hover-only three-dot menu button (`#conversation-menu-action`) was clicked via
  raw `element.click()` through `page.evaluate()`, bypassing the real hover step the app expects
  to mount the button's anchor first. A real hover+click (or the existing
  `open_conversation_menu()` page-object method, which already does the hover) doesn't trigger
  it. Reusable checkpoint: any console error that only appears after a synthetic
  `element.click()`/`dispatchEvent()` bypass of a hover-reveal control needs a same-session
  real-interaction re-check before it's trusted as a product defect.
- Full AFS: `test-specs/chat-interface/l2_add-agent-pipeline-toolkit-mcp-participants-panel_ELITEA-2094.md`.
