---
name: Agent export via menu (implementer)
description: AgentDetailPage.export_agent_via_menu() — SUPERSEDED by the ELITEA-1794 testid rework; the Export menuitem's missing data-testid was a missing `key` field, not a missing feature — DotMenu.jsx already wires testId=item.key for every menu item; agent name field also enforces MAX_NAME_LENGTH=32 like the skill name field
type: feedback
---

## Context

Implemented ELITEA-1794 (Export Agent with attached Skills),
`automation/tests/ui/skills/test_export_agent_with_attached_skills.py`.
**Amended 2026-07-15** after the testid-only rework (PR #53 review finding,
PR https://github.com/EliteaAI/elitea-testing-public/pull/285).

## Findings

1. **SUPERSEDED — root cause of the "no data-testid" finding below**: the
   Agent-actions overflow menu (`ApplicationControls.jsx` → `DotMenu.jsx`)
   already has a generic `testId: item.key` → `data-testid="${key}-menuitem"`
   convention wired into `BasicMenuItem`/`ActionWithDialog` — every other
   menu item in the array (`delete-agent`, Skill's `export-version`, etc.)
   gets its testid for free just by having a `key` field on the menu-item
   object. `useExportApplicationMenu()`'s menu item
   (`ExportApplicationButton.jsx`) was the *only* item in the array with no
   `key` at all — a one-line omission, not a missing feature. Fix: add
   `key: 'agent-actions-export'` → renders
   `data-testid="agent-actions-export-menuitem"`.
   `AgentDetailPage.export_agent_via_menu()` now resolves it via a
   class-level `LocatorDescriptor(testid="agent-actions-export-menuitem")`
   (`export_agent_menuitem` field) instead of
   `get_by_role("menuitem", name="Export")`.
   **Reusable pattern**: for any future "menuitem has no testid" case
   anywhere `ControlsDropdown`/`DotMenu`/`SkillControls`-style menus are
   used, check whether the item object is missing a `key` field *before*
   reaching for a bespoke `data-testid` prop — the wiring is usually
   already there.
   Testid draft PR: https://github.com/EliteaAI/EliteaUI/pull/549.

2. **Agent name field also enforces `MAX_NAME_LENGTH=32`** (React
   `inputProps={{ maxLength: MAX_NAME_LENGTH }}` in
   `CreateAgentForm.jsx`), same silent truncation behavior already
   documented for the Skill name field in `mui_form_field_quirks.md`
   (ELITEA-1737). A uuid-suffixed generated agent name over 32 chars gets
   silently truncated in the DOM — no validation error — so any later
   lookup by the untruncated name (e.g. `attach_skill()`'s popper search
   for a co-created skill, or an assertion on `get_name()`) will fail
   looking like a product defect but is actually a test-data-length bug.
   Applies the same fix: keep generated agent names short
   (`el-1794-agent-{8hex}` ~22 chars was safe).

3. Confirmed the exported `.agent.md` frontmatter's nested
   `skills[0].instructions` field is the full verbatim text (not
   truncated, not a reference) by asserting a planted unique marker
   string is present — see qa-engineer's
   `agent_export_with_attached_skills_quirks.md` for the analyst-side
   findings on the export surface itself.

## Where used

`test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md`,
`automation/pages/agent_detail_page.py::export_agent_via_menu()`.
