# Test Case: Import Agent with attached Skills recreates Skills with new IDs

## Metadata
- **TMS ID**: ELITEA-1795
- **Linked Story**: none
- **Priority**: l3 (medium — case authored as "high" priority, but sibling cases in
  this batch are filed at l3; kept consistent with the batch's existing naming
  convention, see `test-specs/skills/l3_*`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation — case executed end-to-end, all 8 case steps
  confirmed live. Core claim holds: import creates a brand-new Skill entity with a
  new unique ID (distinct from the source Skill's ID) and full verbatim content,
  and the imported Agent is correctly linked to that new Skill. No product defect
  found. One UI-only async-timing quirk observed and documented (not a defect —
  see Known Defects).

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills and Agents sections are available in the project.
- An Agent `.md` export file exists, previously exported from an Agent with ≥1
  attached Skill (ELITEA-1794's flow). No suitable pre-existing export file was
  available, so this run generated a fresh one: created a disposable Skill +
  Agent via UI, attached the Skill, and exported the Agent via the agent-actions
  overflow menu (`Export` menuitem, `VERSION` group) — identical flow to
  ELITEA-1794, reused here as the precondition-setup step rather than reusing a
  stale fixture file (a stale file's source Skill/Agent may no longer exist,
  which would make ID-uniqueness comparison unverifiable).
- The Agent import feature is available. **Confirmed live**: an "Import" button
  exists in the Agents list page toolbar (`/agents/all`), to the left of the
  table/card view toggle. **Amended 2026-07-15 (testid-rework)**: it now carries
  the `agents-import-button` data-testid (see Handles Reference for provenance).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Source Skill name: kebab-case, e.g. `el-1795-skill-a1b2c3d4` — **must be
  lowercase letters/digits/hyphens only** (client-side Skill-name validation,
  same constraint documented for ELITEA-1794/1789/1792/1739/1737/1735).
- Source Skill description: any non-empty string, e.g. `"Test skill for
  ELITEA-1795 import-recreates-skill verification."`
- Source Skill instructions: any non-empty string under the 2500-char limit,
  **must contain a unique marker substring** so the imported Skill's content can
  be asserted as verbatim, not merely "non-empty" — used in this run: `"You are
  el-1795-skill-a1b2c3d4. This exact instruction sentence
  ELITEA_1795_MARKER_TEXT must appear verbatim in the imported Skill, not merely
  referenced."` (grep the imported Skill's instructions field for
  `ELITEA_1795_MARKER_TEXT`).
- Source Agent name: e.g. `el-1795-agent-a1b2c3d4`; description and a short
  generic instructions string (asserted for round-trip fidelity, not the case's
  focus).
- **Import file**: the `.agent.md` file downloaded from the source Agent's
  export (ELITEA-1794 flow) — not a static fixture. Using a freshly generated
  file (rather than a checked-in fixture) is required here because the case's
  core assertion is "new Skill ID differs from the **source** Skill's ID" — a
  stale fixture's embedded source-Skill reference would be meaningless once the
  original Skill is gone.

No `reuse-existing` or shared fixture applies — this is a fresh-state flow: one
source Skill + one source Agent (setup precondition, ELITEA-1794's flow) + one
imported Agent + one imported Skill (this case's own observable), 4 entities
total, all created and torn down within the run.

## Test Steps

1. **(Precondition setup, mirrors ELITEA-1794 Test Steps 1–5)** Create a Skill
   via `${BASE_URL}/skills/create` (Name/Description/Instructions, with the
   planted marker), save. Create an Agent via `${BASE_URL}/agents/create?viewMode=owner`
   (Name/Description/Instructions), save. Attach the Skill to the Agent via the
   Skills accordion's add-skill button (`getByRole('button', { name: 'Skill',
   exact: true })`) → "Search skills..." popper → select by name. Open the
   agent-actions overflow menu (`agent-actions-menu-button`) → click `Export`
   menuitem (`VERSION` group, no dedicated testid).
   - **Verify**: Skill created (id `302` in this run); Agent created (id `4712`
     in this run); Skill attached (counter "0/5"→"1/5 skills added.", card shows
     name + `base` version); Export triggers a browser download —
     `el-1795-agent-a1b2c3d4.agent.md` in this run. Downloaded file's raw YAML
     frontmatter contains `skills: [{name, description, version: base,
     instructions}]` with the full planted marker text embedded verbatim
     (confirmed by reading the file directly) — same embedding behavior
     documented in ELITEA-1794.
2. Navigate to `${BASE_URL}/agents/all`. Click the "Import" button in the page
   toolbar (`agents-import-button`, see Handles Reference).
   - **Verify** (case step 1): a native OS file chooser opens (confirmed via
     Playwright MCP's "Modal state: [File chooser]" signal).
3. Select the exported Agent `.md` file from Step 1 in the file chooser.
   - **Verify** (case step 2, partial — the "Import parameters" preview dialog):
     a modal titled "Import parameters" opens showing a Project selector
     (defaults to the currently active project, `Private` in this run), a "Main
     entity" section previewing the Agent's name/type/description/instructions
     (behind "Show details" toggles), and a "Skills" section previewing the
     embedded Skill's name/type/description/instructions/version — **all
     populated directly from the uploaded file's content**, before any import
     API call fires. Confirmed the Skill preview shows the full planted marker
     text verbatim, proving the dialog parses the embedded Skill content
     client-side from the file, not from a live lookup by ID.
4. Click the "Import" button inside the dialog (distinct from the page-toolbar
   "Import" button in Step 2 — this one carries its own
   `agent-import-confirm-button` data-testid, so no dialog-scoping workaround
   is needed).
   - **Verify** (case step 2, continued): import completes without error. A
     minor unrelated console warning fired during this transition — `Warning:
     validateDOMNesting(...): <p> cannot appear as a descendant of <p>` inside
     `IWModalSucceedContent.jsx` (the "Import Complete" success dialog's own
     internal markup) — a pre-existing cosmetic React nesting issue in that
     dialog's JSX, unrelated to the import's data-correctness and not asserted
     against by this case's pass/fail criteria. Noting it as an observation
     (see Known Defects), not filing it as a defect for this case.
5. Observe the "Import Complete" dialog.
   - **Verify** (case step 2 completion): dialog shows "Imported: 1 agents:
     el-1795-agent-a1b2c3d4" and "1 skills: el-1795-skill-a1b2c3d4" — confirming
     both a new Agent and a new Skill entity were created (not merely an Agent
     linking to the pre-existing Skill by ID). Click "Got it"
     (`agent-import-complete-got-it-button`) — this auto-navigates to the
     newly imported Agent's detail page.
6. **(Case step 3)** Verify the imported Agent appears in the Agents list with a
   name matching the exported Agent.
   - **Verify**: post-import navigation lands on
     `/agents/all/{new-agent-id}?viewMode=owner&name=el-1795-agent-a1b2c3d4` — new
     Agent id `4713` in this run (distinct from source Agent id `4712`). The
     Agents list (`/agents/all`) shows two cards both named
     `el-1795-agent-a1b2c3d4` (source + imported) confirming the name-match
     criterion.
7. **(Case step 4)** Open the imported Agent and inspect the attached Skills.
   - **Verify**: on first paint immediately after navigation, the Skills
     accordion showed **"0/5 skills added."** — this is an **async-timing
     artifact**, not a data defect (see Known Defects for the full
     verification). After allowing the page's secondary
     `GET /api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}`
     fetch to resolve (confirmed via `browser_network_requests` — this call
     returns `200 OK` with `{"skills": [{"name": "el-1795-skill-a1b2c3d4",
     "skill_id": 303, "version_id": 309, "version_name": "base", ...}],
     "max_skills": 5}`), a fresh re-navigation/reload correctly rendered "1/5
     skills added." with the Skill's card (name + `base` version). **An
     automated test must wait on this specific network response (or poll the
     skills counter/card) rather than asserting immediately after the
     post-import redirect** — asserting on the very first paint is a race and
     will be flaky.
8. **(Case steps 5–6)** Navigate to the Skills section (`${BASE_URL}/skills/all`)
   and locate the newly created Skill; verify its ID is new/unique, distinct
   from the source Skill's ID.
   - **Verify**: two Skill cards named `el-1795-skill-a1b2c3d4` exist in the
     list (source + imported). Opened each: source Skill resolves to id `302`
     (`/skills/all/302`); imported Skill resolves to id `303`
     (`/skills/all/303`) — **confirmed distinct, unique ID**, matching the
     `application_skills` API response's `skill_id: 303` from Step 7. This is
     the case's core claim and it holds.
9. **(Case step 7)** Verify the new Skill's instructions and content match the
   exported content.
   - **Verify**: imported Skill (id 303) detail page shows Name
     `el-1795-skill-a1b2c3d4` (exact match), Description `"Test skill for
     ELITEA-1795 import-recreates-skill verification."` (exact match),
     Instructions containing the full planted marker text
     `ELITEA_1795_MARKER_TEXT` verbatim (exact match to the source Skill's
     instructions) — all fields populated from the imported file's embedded
     content, not left blank or defaulted.
10. **(Case step 8)** Verify the imported Agent can be saved without errors.
    - **Verify**: edited the imported Agent's Description field
      (`agent-description-input`) and clicked the version-level `Save` button.
      Save completed cleanly — `Save` button returned to `[disabled]` state
      (indicating a successful save with no pending changes), edited value
      persisted, and `browser_console_messages(level: "error")` returned zero
      errors for this interaction.

## Handles Reference

> **Amended 2026-07-15 (ELITEA-1795 testid-rework, PR review of automation PR
> #54, framework-alignment audit `elitea-testing-public#37`).** Per
> `.agents/role-overrides.md` § Analyst slot, every primary handle below is now
> a testid, and a **Provenance** column records whether that testid is live on
> `EliteaUI` `main`, only on the shared `automation/testids` integration branch
> pending a draft PR, or still missing entirely. Rows still resolving via
> role/text (`Agent add-skill button`) are pre-existing, out-of-scope tech debt
> shared with ELITEA-1735/1789/1792/1794 — flagged `needs-adding`, not fixed
> here.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Skill Name / Description fields | same as ELITEA-1794 (`Name *` / `Description *` textboxes) | on-main ✓ | |
| Skill Instructions editor | `skill-instructions-editor-content` | on-automation/testids only (draft EliteaUI#526) | CodeMirror; not yet on `main` — pre-existing dependency this case has always had (same gap tracked for ELITEA-1737/1794); this means the case remains localhost-green-only, not yet promotable, independent of this rework |
| Agent Name / Description / Instructions fields | `agent-name-input` / `agent-description-input` / `agent-instructions-input` | on-main ✓ | same as ELITEA-1794 |
| Agent add-skill button | no testid; `getByRole('button', { name: 'Skill', exact: true })` | needs-adding | matches ELITEA-1794/1789/1792's amended handle; out of this case's scope |
| Agent actions (overflow) menu | `agent-actions-menu-button` | on-main ✓ | opens VERSION/AGENT grouped menu |
| "Export" menuitem | `agent-actions-export-menuitem` | on-automation/testids only (draft EliteaUI#549) | same as ELITEA-1794's own rework |
| **Agents list "Import" button (this case's core element)** | `agents-import-button` | on-automation/testids only (draft EliteaUI#552) | Added via `add-data-testid` as an optional `testId` prop on the shared `ToolbarImportButton` component (also used by the Pipelines list, left unwired there — out of this case's scope), wired from `Applications.jsx`. Clicking opens a native file chooser directly (no intermediate menu) |
| File chooser | native OS dialog, handled via Playwright's `page.on('filechooser')` / MCP `browser_file_upload` | n/a (not a UI handle) | Accepts `.md` files |
| **Import parameters dialog (this case's core element)** | `agent-import-preview-dialog` | on-automation/testids only (draft EliteaUI#552) | `ImportWizardModal`'s `Modal.BaseModal` carries this testid only while showing the "Import parameters" step (state-dependent — see "Import Complete success dialog" row below for the succeed-state value). Shows Project selector, "Main entity" (Agent) preview, and "Skills" preview sections, each with "Show details" toggles and "Full screen view" buttons per field |
| Import-dialog Main-entity name preview | `agent-import-preview-name` | on-automation/testids only (draft EliteaUI#552) | `IWModalEntityCardWrapper`'s `titleTestId` prop, wired from `IWModalDetails` for the Main-entity card only |
| Import-dialog Skill name preview | `agent-import-preview-skill-name` | on-automation/testids only (draft EliteaUI#552) | Same mechanism, wired for the Skill-entity card(s); shared testid across every Skill card in the preview (this case attaches exactly one, asserted via `.first`) — confirms client-side parse of the uploaded file's embedded skill content before any import API call |
| Import-dialog "Show details"/"Hide details" toggle | `agent-import-preview-card-toggle` | on-automation/testids only (draft EliteaUI#552) | **Amended 2026-07-16 (EliteaUI PR #581 review fix `e0407b70`):** testid is now ALWAYS present; `data-expanded` carries the state. Expand-all loops filter `[data-testid="agent-import-preview-card-toggle"][data-expanded="false"]` (page-object constant `IMPORT_PREVIEW_COLLAPSED_TOGGLE_SELECTOR`) — the original "rendered only while collapsed / click until none remain" mechanism is gone and that pattern is outlawed (`.agents/testing.md` § Locator policy) |
| Import-dialog Skill instructions preview | `agent-import-preview-skill-instructions` | on-automation/testids only (draft EliteaUI#552) | `IWModalEntityCard`'s `instructionsTestId` prop, wired only for Skill cards (not Main entity, since this case doesn't assert the Agent's own instructions preview) |
| Import-dialog scoped Import (confirm) button | `agent-import-confirm-button` | on-automation/testids only (draft EliteaUI#552) | Distinct testid from the page-toolbar's `agents-import-button`, so no dialog-scoping workaround is needed (previously both shared the accessible name "Import") |
| **"Import Complete" success dialog** | `agent-import-complete-dialog` | on-automation/testids only (draft EliteaUI#552) | Same `Modal.BaseModal` as the preview dialog, switched to this testid once import succeed/fork data lands — its mere visibility is the semantic equivalent of the "Import Complete" heading being shown |
| Import-Complete Agents/Skills name lists | `agent-import-complete-list-agents` / `agent-import-complete-list-skills` | on-automation/testids only (draft EliteaUI#552) | `IWModalSucceedContent`'s per-category container, dynamic `agent-import-complete-list-{key}` (agents/skills/toolkits/pipelines); asserted via substring-in-text-content rather than locating by the literal name |
| Import-Complete "Got it" button | `agent-import-complete-got-it-button` | on-automation/testids only (draft EliteaUI#552) | Auto-navigates to the new Agent's detail page on click |
| Imported Agent detail page Skills counter | same as ELITEA-1794/1789/1792 pattern — accordion region text `"{n}/5 skills added."` | on-main ✓ | **Timing-sensitive** — see Known Defects; do not assert immediately after the post-import auto-navigation |
| `application_skills` API endpoint (wait-condition for the timing issue) | `GET /api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}` → `200 OK`, body `{"skills": [{"name", "skill_id", "version_id", "version_name", ...}], "max_skills": n}` | n/a (network call, not a UI handle) | Implementer waits on this URL pattern via `page.expect_response` before asserting the imported Agent's attached Skill, instead of asserting on first paint |
| Skill controls (overflow) menu / Delete-skill menu item / Delete-agent menu item / Delete-confirmation dialog | same testids as ELITEA-1794 (`skill-controls-menu-button`, `skill-delete-menu-item`, `delete-agent-menuitem`, `delete-confirm-name-input` → inner `#name`, `getByRole('button', {name:'Delete'})` scoped to dialog) | on-main ✓ (except `delete-confirm-name-input`: on-automation/testids only, draft EliteaUI#525; and the dialog's own Delete button: needs-adding) | |

## Expected Results
- Importing an Agent `.md` file with embedded Skill content via the Agents list
  "Import" button completes without error, after a preview ("Import parameters")
  dialog and a confirmation click.
- A **new** Agent entity is created (new unique Agent ID, distinct from the
  source) with a name matching the exported Agent's name.
- A **new** Skill entity is created (new unique Skill ID, distinct from the
  source Skill's ID) — the import does **not** merely link the new Agent to the
  pre-existing source Skill by ID.
- The new Skill's name, description, and instructions match the exported
  content verbatim (confirmed via a planted marker string).
- The imported Agent is correctly linked to the newly created Skill (confirmed
  both via the Agent detail page's Skills section, once its async fetch
  resolves, and via the underlying `application_skills` API response).
- The original source Skill and source Agent are unaffected by the import (both
  remain unchanged, independently addressable by their own IDs).
- The imported Agent can be edited and saved without error.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: an Agent `.md` export file exists from an Agent with ≥1 attached Skill | Export file available for import | Test Step 1 | Fresh Skill+Agent created, attached, exported (mirrors ELITEA-1794); file downloaded and content-verified before use | asserted |
| Step 1: Navigate to Agents, trigger Import action | Import dialog/file picker shown | Test Step 2 | "Import" button in Agents list toolbar clicked; native file chooser opened (Playwright MCP modal-state signal) | asserted |
| Step 2: Select file and confirm import | Import completes without errors | Test Steps 3–5 | File selected → "Import parameters" preview dialog → dialog "Import" click → "Import Complete" success dialog confirms 1 agent + 1 skill imported | asserted |
| Step 3: Verify imported Agent appears in Agents list | New Agent entry present, name matches | Test Step 6 | New Agent id 4713 (distinct from source 4712) at `/agents/all/4713`; Agents list shows two `el-1795-agent-a1b2c3d4` cards | asserted |
| Step 4: Open imported Agent, inspect attached Skills | Skill from export listed as attached | Test Step 7 | Skills counter/card correctly show "1/5 skills added." + skill card, once the async `application_skills` fetch resolves (see Known Defects for the first-paint timing caveat) | asserted, with a documented timing caveat |
| Step 5: Navigate to Skills section, locate new Skill | New Skill entry exists with same name | Test Step 8 | Two `el-1795-skill-a1b2c3d4` cards in Skills list; imported one resolves to id 303 | asserted |
| Step 6: Verify new Skill has new unique ID, different from source | New ID ≠ source ID | Test Step 8 | Source Skill id 302 vs imported Skill id 303 — confirmed distinct via direct navigation to both detail pages | asserted — this is the case's core claim and it holds |
| Step 7: Verify new Skill's instructions/content match exported content | Content correctly populated | Test Step 9 | Imported Skill (303) Name/Description/Instructions match source verbatim, including the planted marker `ELITEA_1795_MARKER_TEXT` | asserted |
| Step 8: Verify imported Agent can be saved/used without errors | Agent functional, saves cleanly | Test Step 10 | Description edited + saved; Save button returned to disabled; zero console errors | asserted |
| Test Data: literal example names ("Export Test Agent", "Formatter") | literal names as written | N/A — case-text drift, not a defect | Live Name fields enforce kebab-case (Skill) / general validation (Agent); used `el-1795-agent-a1b2c3d4` / `el-1795-skill-a1b2c3d4` instead | clarification (reverse-masking, same pattern as ELITEA-1794/1789/1792/1739/1737/1735) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| "Import parameters" preview dialog's content-parsing behavior (Skill instructions shown verbatim, including the marker, before any import API call) | Proves the dialog parses the uploaded file's embedded Skill content client-side, not via a live lookup — reinforces that the export/import round trip carries full content, not references |
| `application_skills` API response body (`skill_id`, `version_id`, `version_name`) | Gives the implementer a concrete, non-UI-dependent assertion surface for "Agent is linked to the new Skill" that's immune to the first-paint timing race documented in Known Defects |
| Original source Skill (302) and source Agent (4712) unaffected after import | Confirms the import is purely additive — no mutation of the source entities — a plausible-but-unstated regression risk worth a positive check |
| Console warning during "Import Complete" dialog transition (`validateDOMNesting` `<p>`-in-`<p>`) | Documented as an observation so the implementer doesn't mistake it for import-correctness noise; not asserted against since it's cosmetic and pre-existing in `IWModalSucceedContent.jsx` |
| Agents list "Import" button + Import-flow dialogs now testid-only | **Amended 2026-07-15 (testid-rework)**: the 19 raw role/text handles this flow originally required were replaced with `data-testid`s (see Handles Reference — `agents-import-button`, `agent-import-preview-dialog`, `agent-import-preview-name`, `agent-import-preview-skill-name`, `agent-import-preview-card-toggle`, `agent-import-preview-skill-instructions`, `agent-import-confirm-button`, `agent-import-complete-dialog`, `agent-import-complete-list-agents`/`-skills`, `agent-import-complete-got-it-button`) via EliteaUI draft PR #552 |

## Known Defects

**None filed.** One quirk investigated and ruled out as a non-defect:

- **Skills counter shows "0/5 skills added." immediately after the post-import
  auto-navigation, before correctly showing "1/5" on reload.** Investigated via
  `browser_network_requests`: the Agent detail page fires two separate fetches —
  the main Agent GET (`/api/v2/elitea_core/application/prompt_lib/{project}/{agent-id}`)
  and a secondary Skills-specific GET
  (`/api/v2/elitea_core/application_skills/prompt_lib/{project}/{agent-id}`) — and
  renders the Skills accordion from whichever has resolved first. The secondary
  call lags the main page paint by roughly 1–2 seconds in this local run. On a
  fresh reload (or after waiting for that specific network response), the
  Skills section correctly shows "1/5 skills added." with the Skill's card,
  and the API response itself (`{"skills": [{"skill_id": 303, ...}], "max_skills":
  5}`) was already correct even during the "0/5" UI flash — confirming the data
  layer was never wrong, only the UI's initial paint lagged behind an async
  fetch. **This is a UI-timing quirk, not a data-correctness defect** — the
  case's actual pass criterion ("Skill from export is listed as attached") is
  satisfied once the page has fully loaded. Filed here as a Known Defects
  entry (not a tracker ticket, per the reverse-masking guard — the live
  behavior is a timing characteristic, not a broken contract) so the
  implementer builds the correct wait condition (poll the skills counter, or
  `page.waitForResponse` on the `application_skills` endpoint) rather than
  asserting on first paint and producing a flaky test.

## Cleanup

Four entities created per run: source Skill, source Agent, imported Skill,
imported Agent. All four were deleted live in this run.

1. **Delete both Agents first, then both Skills** — same recommended order as
   ELITEA-1794 (delete the entities with attached-state dependencies first).
2. **Agent deletion** (both source id 4712 and imported id 4713): UI overflow
   menu (`agent-actions-menu-button`) → "AGENT" group → "Delete agent"
   (`delete-agent-menuitem`) → type-to-confirm dialog (`delete-confirm-name-input`
   → inner `#name` field, type the exact Agent name) → click "Delete"
   (`getByRole('button', {name:'Delete'})` scoped to the dialog — becomes
   enabled only once the typed name matches exactly).
   **For automated cleanup, prefer the existing `agent_api` fixture**
   (`AgentAPI.delete_agent(agent_id)` in `automation/api/client.py:452`), same
   as ELITEA-1794/1735/1789/1792.
3. **Skill deletion** (both source id 302 and imported id 303): UI overflow menu
   (`skill-controls-menu-button`) → "SKILL" group → "Delete skill"
   (`skill-delete-menu-item`) → same type-to-confirm dialog → click "Delete".
   **For automated cleanup, use the existing `skill_api` fixture**
   (`SkillAPI.delete_skill(skill_id)` in `automation/api/client.py:1227`).
4. **Downloaded export file**: the `.playwright-mcp/` (or test-runner temp-dir)
   download artifact (`el-1795-agent-a1b2c3d4-agent.md` in this run) is local
   test-runner output, not a product-side entity — no server-side cleanup
   needed, but an automated test should clean up its own download path in
   teardown (mirrors ELITEA-1794/ELITEA-1737's `download_path.unlink(missing_ok=True)`
   pattern).
5. **Recommended teardown fixture shape**: function-scoped, tracking IDs as they
   become known (source skill id, source agent id, imported agent id, imported
   skill id — the latter two aren't known until mid-test, after the import
   completes) in a list, deleting agents first then skills in the `finally`
   block, each deletion in its own `try/except` (mirrors
   ELITEA-1794/1737/1738/1739/1789/1792's `cleanup_skill_ids`-style pattern, but
   generalized to also track agent IDs since this case creates two of each
   entity type).

## Blocked Steps
None — case executed end-to-end, all 8 case steps confirmed live, no blockers.
