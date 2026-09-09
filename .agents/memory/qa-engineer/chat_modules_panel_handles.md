---
name: Chat Modules panel handles
description: Modules panel switches carry stable modules-toggle-<name> testids on main; display titles drift and broke ELITEA-0501
type: reference
aliases: [modules panel, internal tools panel, CHAT_INTERNAL_TOOLS, modules-toggle, plus menu modules]
tags: [area/chat, type/handles]
created: 2026-09-09
updated: 2026-09-09
---

## What DEV renders (live-verified 2026-09-09, dev.elitea.ai, project 399)

Plus menu -> Modules. Exactly 10 `role="switch"`, in this order:

| # | Accessible name | data-testid |
|---|---|---|
| 1 | Image Creation | `modules-toggle-image_generation` |
| 2 | Data Analysis | `modules-toggle-data_analysis` |
| 3 | Agent & Pipeline Builder | `modules-toggle-internal_mcp` |
| 4 | Skill Builder | `modules-toggle-skill_builder` |
| 5 | Project Context Builder | `modules-toggle-project_context_builder` |
| 6 | Ask User | `modules-toggle-ask_user` |
| 7 | Planner | `modules-toggle-planner` |
| 8 | Python Sandbox | `modules-toggle-pyodide` |
| 9 | Swarm Mode | `modules-toggle-swarm` |
| 10 | Smart Tools Selection | `modules-toggle-lazy_tools_mode` |

## Prefer the testid — it is keyed on the internal name, not the title

`PlusChatButton.jsx:297` renders `data-testid={`modules-toggle-${tool.name}`}`; on
`origin/main` since `EliteaAI/EliteaUI@bf4a13ad` (2026-08-12), so no promotion gap.
`tool.name` (`internal_mcp`, `lazy_tools_mode`, `pyodide`) is stable, while
`tool.title` is marketing copy that DOES get rewritten — `EliteaAI/EliteaUI@79fd2a55`
(EL-6540, 2026-09-08) renamed "Agents & Pipeline Builder" -> "Agent & Pipeline
Builder" and "Smart Tool Selection" -> "Smart Tools Selection", which is what turned
`test_internal_tools_panel_shows_all_tools` red. A title-keyed locator will break
again on the next copy edit; a testid-keyed one will not.

## Conditional rendering (`useAvailableInternalTools.hooks.js`)

- `agentOnly: true` -> **Attachments** is agent-only, never in chat.
- `internal_mcp` + `skill_builder` + `project_context_builder` share ONE gate:
  `useIsMcpVisible()` = `mcp_exposure_enabled !== false && mcp_in_menu_enabled !== false`
  from `GET /api/v2/elitea_core/platform_settings/prompt_lib`. Both `true` on DEV.
  They appear or vanish as a group of three — never individually.
- `image_generation` has its OWN independent gate: `toolkitSchemas['ImageGenServiceProvider_ImageGen']`
  must be present. This is the one entry that can vanish while the other nine stay.

Related: [[agent_internal_tools_testid_map_is_dead]]
