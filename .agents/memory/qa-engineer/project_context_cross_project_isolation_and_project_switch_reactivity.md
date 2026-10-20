---
name: Project Context cross-project isolation + reactive project switch
description: Settings > Project Context re-queries reactively on BasePage.switch_project() with no reload; use ProjectAPI.list_projects() to discover a second project at runtime, never hardcode one; ProjectContextAPI already takes a project_id override for cross-project checks
type: feedback
---

## Reactive re-query on project switch — no page reload needed

`ProjectContextContent.jsx`'s `useProjectContextQuery` is keyed purely by
`useSelectedProjectId()` (confirmed via source read — zero cross-project
special-casing). Calling `BasePage.switch_project(other_id)` while already on
`/settings/project-context` correctly flips the SAME page instance from one
project's content/empty-state to the other's, with no `page.goto()` /
reload needed in between. Confirmed live (ELITEA-3315): Project A's populated
editor content → Project B's "Still no Project Context" empty-state,
immediately after `switch_project()` returns.

## Discovering a second project — never hardcode

Any case needing a SECOND project (cross-project isolation, fork-to-project,
multi-project assertions) should resolve it at runtime via
`ProjectAPI.list_projects()` (`GET
/api/v2/projects/project/default/1?check_public_role=true`), excluding the
active project id and `settings.public_project_id` from candidates —
exactly the pattern `test_pipeline_fork_to_different_project.py`'s
`_resolve_source_project_id()` already established. This environment
resolves to project `470` ("Elitea Automation") alongside the active
`575` ("Private") — but a different CI matrix cell's acting user may have a
different second membership, so never hardcode `470` (or any other id) as
"the second project".

## ProjectContextAPI already supports a project_id override

`ProjectContextAPI.__init__` accepts an explicit `project_id` param (not
just `ELITEA_PROJECT_ID`/the shared fixture's default) — instantiate a
SECOND client scoped to the other project for cross-project verification
rather than mutating the shared session-scoped `project_context_api`
fixture (which stays pinned to `ELITEA_PROJECT_ID` for every other test
using it).

## No testid on the Settings "enabled" toggle (saved view)

`EnableToggleCard.jsx`'s `Switch.BaseSwitch` (the top-of-page enable/disable
toggle on the Settings → Project Context SAVED view, distinct from the chat
Modules-panel toggles which DO have `modules-toggle-{tool_key}` testids) has
ZERO testid/aria-label/name — `role="switch"` only. No case so far needs to
click/read it directly (asserted via the API's own `enabled` field instead).
`suggested_testid="project-context-enabled-toggle"` for whichever future
case first touches it.

See `test-specs/chat-interface/l1_project-context-isolated-to-current-project_ELITEA-3315.md`
and `test-specs/chat-interface/_surface.md` § Project Context — cross-project
isolation + project switch for the full writeup.
