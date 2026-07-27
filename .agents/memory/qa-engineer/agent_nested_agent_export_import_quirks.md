---
name: Agent nested-agent export/import quirks
description: ELITEA-1902 — exporting an Agent with a nested Agent dependency (not Skill) produces a .zip of multiple .agent.md files, not a single .md; import-preview's Nested-entities cards had zero testids until this run; both entities always recreated with new IDs, never linked by reference
type: feedback
---

## Export shape depends on WHAT is attached, not just whether anything is

Confirmed live (localhost, ELITEA-1902): exporting an Agent via the
actions-overflow "Export" (VERSION group, `agent-actions-export-menuitem`,
`export_agent_via_menu()`) produces:

- **A single `{name}.agent.md` file** when the Agent has no dependencies, or
  only an attached Skill / external toolkit (ELITEA-1794/1795/1894 — the
  established pattern before this case).
- **A `.zip` archive** the moment the Agent has a **nested Agent**
  dependency (attached via the Tools-section "+Agent" picker,
  `agent-add-agent-button` / `open_agent_picker()`, ELITEA-1887). The zip
  contains one `{name}.agent.md` per entity (main + every nested agent).
  The main entity's frontmatter additionally carries a `nested_agents:
  [{name: ...}]` YAML key never present in a Skill-only export.

Don't assume `.suggested_filename.endswith(".md")` for every export test —
branch on whether a nested Agent (not Skill) is attached. This is NOT
case-text drift; the ELITEA-1902 TMS case correctly said ".zip" and it's
right.

## Import preview: Nested-entities cards had ZERO testids (closed this run)

`IWModalDetails.jsx` renders three blocks in the Import-preview dialog:
Main entity, Nested entities (non-Skill — i.e. nested Agents/Pipelines),
Skills. Before this session, only Main entity and Skills passed
`titleTestId`/`toggleTestId`/`instructionsTestId` into `IWModalEntityCard`
— the Nested-entities `.map()` passed `entity` and nothing else, so a
nested Agent's name/instructions were completely unassertable via testid.
Fixed by mirroring the Skill block exactly: added
`agent-import-preview-nested-agent-name` +
`agent-import-preview-nested-agent-instructions`, reused the ALREADY-SHARED
`agent-import-preview-card-toggle` (multiple cards intentionally share this
one testid — `IMPORT_PREVIEW_COLLAPSED_TOGGLE_SELECTOR` already handles
multiple DOM matches). Pushed to `automation/testids`
(EliteaAI/EliteaUI@74f72323). If working any future case that touches the
Nested-entities import-preview block (Pipeline nesting, etc.), this fix is
already live — don't re-discover the gap.

## Import always recreates, never links by reference

Confirmed (mirrors ELITEA-1795's Skill finding, now proven for the
Agent-nested-Agent shape too): importing a `.zip` with a main+nested Agent
pair creates TWO brand-new Agent entities with new distinct IDs — never
links back to the pre-existing source Agents by ID, even if an Agent with
the exact same name already exists in the project. The "Import Complete"
dialog's Agents list (`agent-import-complete-list-agents`) names both.

## Nested-agent attach shares the toolkit-card rendering

The imported main agent's Tools section shows its nested agent via the
SAME `agent-toolkit-card` testid the Toolkit-attach flow uses (confirmed
by design — existing code comment at
`automation/pages/agent_detail_page.py:106-109`). No separate
"agent-card" testid exists for a sub-agent attachment; filter
`toolkit_card` by the nested agent's name text, exactly like a toolkit
assertion.

## No `attach_agent()` convenience method exists yet

`AgentDetailPage` has `open_agent_picker()` (deliberately doesn't select —
built for the ELITEA-1887 self-attachment-exclusion check) and
`get_agent_picker_menuitem()`, but no wrapper that opens the picker AND
selects an agent in one call, unlike `add_toolkit()`/`add_mcp()`. Any
future case needing to attach a nested agent should add one:
`open_agent_picker()` + `Popper.select_menuitem(popper, agent_name, page)`.
The attach auto-persists (Save returns to disabled immediately), same as
toolkit/MCP attach.
