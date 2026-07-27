---
name: Agent import recreates Skills with new IDs quirks
description: Agent import creates a brand-new Skill entity (new unique ID) from embedded content, correctly links it to the new Agent — but the Agent detail page's Skills counter lags on first paint due to an async fetch race; Import button has no testid
type: feedback
---

## Context

Found during ELITEA-1795 (Import Agent with attached Skills recreates Skills
with new IDs) analyst pass, localhost:5173 — the import-sibling of ELITEA-1794
(export).

## Findings

1. **Agent import entry point**: an "Import" button in the `/agents/all` list
   page toolbar (left of the table/card view toggle). **No `data-testid`**
   (confirmed via `element.getAttribute('data-testid')` → `null`) — unlike the
   Skills list's `skills-import-button`. Resolve via `getByRole('button', {
   name: 'Import' })` scoped to the Agents list toolbar until a testid is
   added. `agents_list_page.py` has zero import support as of this writing.

2. **Clicking Import opens a native OS file chooser directly** — no
   intermediate menu, unlike Skill export/Agent export which live behind an
   overflow menu.

3. **"Import parameters" preview dialog** (distinct component from the Skill
   import flow's own dialog): shows a Project selector (defaults to the
   currently active project), a "Main entity" section (Agent
   name/type/description/instructions, behind "Show details" toggles), and a
   "Skills" section (each embedded Skill's name/type/description/instructions/
   version). **All parsed client-side from the uploaded file's content before
   any import API call fires** — confirmed by finding a planted marker
   substring in the Skill preview text pre-confirm.

4. **"Import Complete" success dialog** lists `"{n} agents: {name}"` and
   `"{n} skills: {name}"` — confirms the import created BOTH a new Agent and a
   new Skill entity (not merely an Agent linked to the pre-existing source
   Skill by ID). Clicking "Got it" auto-navigates to the new Agent's detail
   page.

5. **CORE CLAIM CONFIRMED**: the imported Skill gets a genuinely new, unique
   ID, distinct from the source Skill's ID (302 source vs 303 imported in this
   run) — confirmed via direct navigation to both Skill detail pages AND via
   the `application_skills` API response. Content (name/description/
   instructions, including a planted marker) matches the source verbatim. The
   original source Skill and source Agent are unaffected by the import.

6. **UI-timing race, NOT a data defect — investigate before filing**:
   immediately after the post-import auto-navigation, the imported Agent's
   Skills accordion shows **"0/5 skills added."** even though the Skill IS
   correctly linked. Root cause (confirmed via `browser_network_requests`): the
   Agent detail page fires the Skills-specific `GET
   /api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}` as a
   separate, slower async fetch than the main Agent GET — the response body
   already carries the correct link (`{"skills": [{"skill_id": 303, ...}]}`)
   even while the UI still shows "0/5". A fresh reload (or waiting for that
   specific response) correctly renders "1/5 skills added." with the skill's
   card. **An automated test must wait on this network response (or poll the
   skills counter/card), never assert on first paint after the post-import
   redirect** — asserting immediately is a guaranteed flake, and mistaking this
   for a broken Agent-Skill link would be a false-positive defect report.

## Where used

`test-specs/skills/l3_import-agent-recreates-skills-with-new-ids_ELITEA-1795.md`
(Test Steps 2–7, Handles Reference, Known Defects).
