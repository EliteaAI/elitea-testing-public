---
name: Agent export via menu (implementer)
description: AgentDetailPage.export_agent_via_menu() — VERSION-group Export menuitem has no data-testid, resolved by accessible name; agent name field also enforces MAX_NAME_LENGTH=32 like the skill name field
type: feedback
---

## Context

Implemented ELITEA-1794 (Export Agent with attached Skills),
`automation/tests/ui/skills/test_export_agent_with_attached_skills.py`.

## Findings

1. **New page-object method**: `AgentDetailPage.export_agent_via_menu()` —
   calls the existing `open_actions_menu()` then clicks
   `get_by_role("menuitem", name="Export")` and captures the resulting
   `page.expect_download()`. Mirrors
   `SkillDetailPage.export_base_version_via_menu()`, but the Agent's Export
   menuitem carries **no** `data-testid` (confirmed against
   `ExportApplicationButton.jsx` / `useExportApplicationMenu()` in
   EliteaUI source — the skill export item does have one,
   `export-version-menuitem`; the agent one doesn't) — resolved by
   accessible name only.

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
