---
name: Chat Modules panel — the 10 module toggles and their tool keys
description: Modules panel renders 10 switches; EL-6540 renamed 3 titles — current names, order, keys and render gates
type: feedback
aliases: [modules panel, internal tools, modules-toggle, EL-6540]
tags: [area/chat, type/handles]
created: 2026-08-07
updated: 2026-09-09
---

Live-confirmed **2026-09-09** on localhost:5173 (`automation/testids`, 0 behind
`main`) and independently on `dev.elitea.ai` — the Chat `+` → Modules panel renders
**10** `role="switch"` elements. `document.querySelectorAll('[role="switch"]').length`
== 10 with the panel open. Titles come from
`src/[fsd]/shared/lib/constants/internalTools.constants.js`.

Render order — `tool_key` — title (testid is `modules-toggle-{tool_key}`):

1. `image_generation` — **Image Creation**
2. `data_analysis` — Data Analysis
3. `internal_mcp` — **Agent & Pipeline Builder**
4. `skill_builder` — **Skill Builder**
5. `project_context_builder` — **Project Context Builder**
6. `ask_user` — Ask User
7. `planner` — Planner
8. `pyodide` — Python Sandbox
9. `swarm` — Swarm Mode
10. `lazy_tools_mode` — **Smart Tools Selection**

## Renames — EliteaAI/EliteaUI@79fd2a55 (EL-6540, merged 2026-09-08)

| Old | New |
|---|---|
| `Image creation` | `Image Creation` |
| `Agents & Pipeline Builder` | `Agent & Pipeline Builder` |
| `Smart Tool Selection` | `Smart Tools Selection` |

`Skill Builder` and `Project Context Builder` were added earlier and were simply
never in our list. All three renames plus the two additions landed in
`ChatInternalTool` via card #2111 / ELITEA-0501 (2026-09-09). Anything still writing
`Agents & Pipeline Builder` or `Smart Tool Selection` is stale — as of 2026-09-09 that
includes the AFS files `test-specs/chat-interface/l2_chat-search-and-modules-panel_ELITEA-2162.md`
and `l2_agent-hub-participant-readonly-canvas-llm-override_ELITEA-2075.md`.

## Render gates — do NOT assume all 10 always render

- `internal_mcp`, `skill_builder`, `project_context_builder` share ONE gate,
  `useIsMcpVisible()` = `mcp_exposure_enabled !== false && mcp_in_menu_enabled !== false`
  (`GET /api/v2/elitea_core/platform_settings/prompt_lib`; both `true` on DEV).
  They appear or vanish **as a group of three**.
- `image_generation` has an independent **per-project** toolkit gate
  (`ImageGenServiceProvider_ImageGen`) — the only member that can vanish alone.
- The rest are unconditional.

The switches DO carry `modules-toggle-{tool_key}` testids; `ChatPage` still locates
them by accessible name (`get_by_role("switch", name=...)`), which is why a title
rename breaks the test at all. Migrating to the testids is filed as a follow-up.

Related: [[ui_display_string_constants_need_a_source_pointer]]
