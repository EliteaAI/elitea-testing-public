---
name: Browser title project-name suffix is not "Private"
description: document.title's "- <project>" suffix is the real project name, not the sidebar's "Private" label — capture dynamically
type: reference
---

Confirmed live 2026-08-09 (ELITEA-2062 analysis) on the local dev env: every
route's `document.title` (`useBrowserPageTitle.js`) ends in
`" - {projectName}"` where `projectName` = `useSelectedProjectName()` →
`../EliteaUI/src/hooks/useSelectedProject.jsx` → the loaded project's real
Redux `name` field, defaulting to the literal `"Private"` ONLY before that
object loads. On this environment's active project it resolved to
`"project_user_659"`, NOT `"Private"` — even though the sidebar's project
combobox displays `"Project: Private"` (a different, apparently-static
label).

**Implication:** any test asserting a full page title string must capture
the project-name suffix dynamically at runtime (e.g. split the dashboard's
own title on `" - "`) rather than hardcoding `"Private"`. An existing merged
test, `automation/tests/ui/agents/test_agent_hub_page_loads_private_project.py`,
hardcodes `EXPECTED_PROJECT_NAME = "Private"` — this may already be a latent
false-negative risk (untested by this session, out of scope to fix) if that
test's target project's real `name` field ever diverges from the literal
string "Private". Worth a look if that test ever flakes on the title
assertion.

This applies to EVERY surface `useBrowserPageTitle.js` covers (chat, agents,
pipelines, toolkits, mcps, credentials, artifacts, settings, skills, apps) —
not just pipelines.
