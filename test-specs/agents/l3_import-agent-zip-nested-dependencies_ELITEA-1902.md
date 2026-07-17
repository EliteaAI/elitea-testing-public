# Test Case: Import agent .zip with nested agent dependencies — creates
main + all nested agents and links them

## Metadata
- **TMS ID**: ELITEA-1902
- **Linked Story**: none
- **Priority**: l3 (medium — case authored as "high" priority in the source
  TMS file, but sibling export/import cases in this batch are filed at l3;
  kept consistent with the batch's existing naming convention — see
  `test-specs/skills/l3_import-agent-recreates-skills-with-new-ids_ELITEA-1795.md`,
  itself sourced from a `priority: high` TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399), model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation — case executed end-to-end live against
  localhost:5173 in this session, all 6 case steps pass, one testid gap
  found and closed (see § Testid work below), no product defects.

## Relationship to neighbouring import/export specs (dedup check)

Three specs already exist in this area, and none of them cover this case's
core claim (a nested **Agent** dependency, not a Skill, and the resulting
**.zip** archive shape):

- `test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md` /
  `automation/tests/ui/skills/test_export_agent_with_attached_skills.py` —
  export of an Agent with an attached **Skill**; asserts a single `.md`
  download with a `skills:` YAML block.
- `test-specs/skills/l3_export-agent-no-nested-dependencies_ELITEA-1894.md` /
  `automation/tests/ui/skills/test_export_agent_no_nested_dependencies.py` —
  the deliberate baseline/inverse of ELITEA-1794 (**no** nested Skill or
  Agent dependency at all, only an external toolkit); asserts a single `.md`
  download with **no** `skills:` key and no leaked credentials.
- `test-specs/skills/l3_import-agent-recreates-skills-with-new-ids_ELITEA-1795.md` /
  `automation/tests/ui/skills/test_import_agent_recreates_skills_with_new_ids.py` —
  round-trips ELITEA-1794's export back through Import and asserts the
  re-created **Skill** gets a new unique ID and is correctly linked.

ELITEA-1902 is the **Agent-nested-Agent** analogue of ELITEA-1795, and is
observably distinct at the file-format level, confirmed live in this run:
exporting an Agent that has **zero** attached Skills but **one** nested
Agent dependency produces a **`.zip`** archive containing two
`{name}.agent.md` files (one per entity) — not the single `.md` file every
prior export scenario produces. This is not case-text drift (see § Reverse-
masking note below) — it is a genuine, confirmed product behavior:
single-file export for a Skill-only (or no-dependency) Agent, multi-file zip
export the moment a nested **Agent** dependency exists. No existing spec
exercises the zip path, the Nested-entities import-preview section for an
Agent-type entity, or the "main agent's Tools section re-shows the newly
created nested Agent as an attached sub-agent tool" assertion.

Verdict: **not already-covered, not extend-existing** — fresh,
independently valuable scenario (`ready-for-automation`).

## Reverse-masking note (case-text check)

The source TMS case's Step 1 says the export "produces a .zip" file. This
was **initially suspicious** given every neighbouring export case in this
repo (ELITEA-1794, ELITEA-1795, ELITEA-1894) downloads a single `.agent.md`
file — but live execution in this session confirms the case text is
**correct, not stale**: an Agent with a nested Agent dependency really does
export as `el-1902-main-agent-a1b2c3d4.agent.zip`, unzipping to two
`.agent.md` files (main + nested). No reverse-masking correction needed;
the case text matches the live product exactly for this scenario.

## Testid work performed (analyst-slot, per `.agents/testing.md`)

**Gap found**: the Import-preview dialog's "Nested entities" block
(`EliteaUI src/[fsd]/entities/import-wizard/ui/ImportWizardModal/IWModalDetails.jsx`,
the `nestedEntities.map(...)` render, previously ~lines 83-95) rendered each
nested-Agent `IWModalEntityCard` with **no** `titleTestId` / `toggleTestId`
/ `instructionsTestId` props at all — unlike the sibling "Skills" block a
few lines below it, which already passed
`agent-import-preview-skill-name` / `agent-import-preview-card-toggle` /
`agent-import-preview-skill-instructions`. Confirmed live via
`document.querySelectorAll('[data-testid]')` on the open preview dialog for
an Agent-with-nested-Agent import: the Main entity card and (in other
scenarios) Skill cards had their testids; the Nested-Agent card had zero.
This made Step 3 of the case ("verify the import wizard lists entity cards
for the main agent AND all nested dependencies") impossible to assert for
the nested-Agent case specifically. Per `.agents/testing.md` ("Missing
testid on the target? That is work to do, not a reason to rung down") this
is testid work, not a product defect to file.

**Fix applied** (via `add-data-testid`, committed + pushed to
`automation/testids`, commit `74f72323`, mirrors the existing Skill-card
pattern exactly):

```jsx
{nestedEntities.map((entity, index) => (
  <IWModalEntityCard
    key={index}
    entity={entity}
    titleTestId="agent-import-preview-nested-agent-name"
    toggleTestId="agent-import-preview-card-toggle"
    instructionsTestId="agent-import-preview-nested-agent-instructions"
  />
))}
```

`toggleTestId` intentionally reuses the shared `agent-import-preview-card-toggle`
testid already used by the Main-entity and Skill cards — this is existing,
established precedent (multiple cards on screen already share this one
testid; `automation/pages/agents_list_page.py`'s
`IMPORT_PREVIEW_COLLAPSED_TOGGLE_SELECTOR` + `expand_import_preview_details()`
already iterate over every match).

**Verified live in the same session** (Vite HMR, no reload needed):
`document.querySelector('[data-testid="agent-import-preview-nested-agent-name"]').textContent`
returned the nested Agent's name verbatim, and the `...instructions`
sibling returned the nested Agent's instructions text verbatim.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Agents section is available in the project.
- An Agent exists with a nested Agent dependency attached via the Tools
  section's "+ Agent" picker (`agent-add-agent-button`, ELITEA-1887) —
  created fresh in this run (no such fixture pre-exists disposably in the
  project). See § Test Data.

## Test Data

### generate-per-test (created via UI in this run, cleaned up via UI
`delete_agent_via_menu()` / `agent_api.delete_agent()` in `finally`)

- **Nested (dependency) Agent**: created first. In this run:
  id `5117`, name `el-1902-nested-agent-a1b2c3d4`, description "Nested
  dependency agent for ELITEA-1902 import test.", instructions "You are the
  nested dependency agent ELITEA_1902_NESTED_MARKER used to verify import
  of nested agent dependencies." (planted marker `ELITEA_1902_NESTED_MARKER`
  for verbatim-content assertions).
- **Main Agent**: created second, then the nested Agent above is attached
  to it via the Tools section's "+ Agent" picker (`open_agent_picker()` +
  `Popper.select_menuitem(popper, nested_agent_name, page)` — the picker
  itself already exists as a page-object method (ELITEA-1887,
  `automation/pages/agent_detail_page.py:1096`); **no dedicated
  `attach_agent()` convenience method exists yet** — the implementer should
  add one wrapping `open_agent_picker()` + `Popper.select_menuitem()`,
  mirroring `add_toolkit()` / `add_mcp()`'s shape). In this run: id `5118`,
  name `el-1902-main-agent-a1b2c3d4`, description "Main agent for
  ELITEA-1902 import test (has nested agent dependency).", instructions
  "You are the main agent ELITEA_1902_MAIN_MARKER that delegates to a
  nested agent dependency." (planted marker `ELITEA_1902_MAIN_MARKER`).
  **The attach auto-persists** (Save button returns to disabled
  immediately after the picker selection resolves) — same auto-persist
  behavior already documented for `add_toolkit()` / `add_mcp()`.
- Recommended for automation: two short random-suffixed names (mirrors
  every sibling spec's `uuid.uuid4().hex[:8]` pattern) to avoid collisions
  across parallel/serial runs.

## Steps

| # | Action | Expected Result | Observed live |
|---|--------|-----------------|-----------------|
| 1 | Export the main Agent (with the nested Agent attached) via the actions overflow menu's "Export" (VERSION group) — `export_agent_via_menu()`, `automation/pages/agent_detail_page.py:2571` | A `.zip` file is downloaded | Confirmed: `el-1902-main-agent-a1b2c3d4.agent.zip` downloaded (NOT `.md` — see § Reverse-masking note). `download.suggested_filename.endswith(".zip")` |
| 2 | Unzip and inspect the archive's contents | Archive contains one `.agent.md` per entity (main + nested) | Confirmed: `el-1902-main-agent-a1b2c3d4.agent.md` + `el-1902-nested-agent-a1b2c3d4.agent.md`. Main entity's frontmatter carries a `nested_agents: [{name: el-1902-nested-agent-a1b2c3d4}]` key (new structural detail, not present in any Skill-only export) |
| 3 | Navigate to Agents list; click "Import" (`agents-import-button`); upload the `.zip` (native file chooser, `agents_list_page.import_agent()` already handles `.md`; needs to accept `.zip` too — confirmed the SAME upload flow accepts a `.zip` without any UI change) | `.zip` uploaded and processed; "Import parameters" preview dialog opens | Confirmed: `import_preview_dialog` (`agent-import-preview-dialog`) visible after upload |
| 4 | Verify the import wizard lists entity cards for the main agent AND all nested dependencies | Main entity card + a "Nested entities" section card, both showing name/description/instructions | Confirmed (**after the testid fix above**): `agent-import-preview-name` == `"el-1902-main-agent-a1b2c3d4"`; new `agent-import-preview-nested-agent-name` == `"el-1902-nested-agent-a1b2c3d4"`; new `agent-import-preview-nested-agent-instructions` == the nested Agent's instructions verbatim (incl. the `ELITEA_1902_NESTED_MARKER` marker) |
| 5 | Confirm the dialog's Import button (`agent-import-confirm-button`) | Import completes; "Import Complete" success dialog | Confirmed: `import_complete_dialog` (`agent-import-complete-dialog`) visible |
| 6 | Verify the main agent and all nested agents are created in the project | Success dialog's Agents list names both entities; both appear in the Agents dashboard | Confirmed: `import_complete_agents_list` (`agent-import-complete-list-agents`) text == `"el-1902-nested-agent-a1b2c3d4, el-1902-main-agent-a1b2c3d4"` — **"2 agents:"** label, i.e. the import creates TWO new Agent entities (main + nested), neither linked to the pre-existing source Agents by ID |
| 7 (case step 6) | Click "Got it" (`agent-import-complete-got-it-button`); open the imported main agent — verify the nested agent is correctly linked | Auto-navigates to the new main Agent's detail page; its Tools section shows the nested Agent attached as a sub-agent | Confirmed: navigated to a NEW main Agent id `5119` (distinct from source `5118`); Tools section shows an `agent-toolkit-card` (the "+Agent" attach shares the toolkit-card rendering, per existing code comment at `agent_detail_page.py:106-109`) with text `el-1902-nested-agent-a1b2c3d4` / `base`. Following that card into its own detail page confirmed a NEW nested Agent id `5120` (distinct from source `5117`) with the marker instructions text verbatim — the import **recreates** both entities with brand-new IDs, the same "always-new, never-linked-by-ID" pattern ELITEA-1795 already established for Skills |

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Export an agent with nested agent dependencies | `.zip` downloaded containing main + nested agents | This AFS Step 1-2 | `download.suggested_filename.endswith(".zip")`; unzip and read both `.agent.md` members; main's frontmatter `nested_agents[0].name` | ready-for-automation |
| Step 2: Navigate to Agents → Import, upload the `.zip` | File uploaded and processed | This AFS Step 3 | `import_preview_dialog.is_visible()` after `agents_list_page.import_agent(zip_path)` | ready-for-automation |
| Step 3: Import wizard lists entity cards for main agent AND all nested dependencies | Cards shown for both | This AFS Step 4 (required the testid fix — see § Testid work) | `agent-import-preview-name` + new `agent-import-preview-nested-agent-name`/`...-instructions` | ready-for-automation (testid gap closed this run) |
| Step 4: Confirm the import | Import completes | This AFS Step 5 | `import_complete_dialog.is_visible()` | ready-for-automation |
| Step 5: Main agent and all nested agents created in the project | All entities appear in Agents dashboard | This AFS Step 6 | `import_complete_agents_list` text contains both names; "2 agents:" count label | ready-for-automation |
| Step 6: Open main agent — verify nested agents correctly linked | Main agent's config shows nested agents as attached dependencies | This AFS Step 7 | New main agent's Tools section `agent-toolkit-card` shows the nested agent's name+version; drilling into that card's own detail page confirms a distinct new agent id with verbatim content | ready-for-automation |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Zero console errors during export/import/attach flow, EXCEPT one pre-existing unrelated React `validateDOMNesting` dev-warning on the Import-Complete dialog's Tooltip (see § Known Defects) | Guards against silent regressions the case didn't ask for |
| Imported main + nested agent IDs are both NEW/distinct from the source IDs (not merely linked by reference) | This is the load-bearing "recreates, doesn't reference" claim the sibling ELITEA-1795 (Skills) already established — worth re-proving for the Agent-nested-Agent shape specifically since it's a structurally different code path (zip vs single md) |
| Source main + nested agents are unaffected by the import (import is purely additive) | Mirrors the Axis-2 addition already established in `test_import_agent_recreates_skills_with_new_ids.py` — the import must not mutate the originals |
| `.zip` vs `.md` export-shape distinction itself | Confirms/documents a real, non-obvious product behavior (single-file export switches to zip archive the moment a nested Agent — not just a Skill — is attached) that the next analyst/implementer working this area needs to know |

## Stable handles (selectors)

All testid-only, no fallback, per `.agents/testing.md` § Locator policy.

| Element | testid | Page object | Notes |
|---|---|---|---|
| "+ Agent" tools-section button | `agent-add-agent-button` | `AgentDetailPage.add_agent_button` | Existing (ELITEA-1887) |
| Agent picker popper | (MUI popper, no dedicated testid — resolved via `components.mui.Popper.wait_for()`) | `AgentDetailPage.open_agent_picker()` | Existing (ELITEA-1887); returns popper `Locator` |
| Agent-actions export menuitem | `agent-actions-export-menuitem` | `AgentDetailPage.export_agent_menuitem` / `export_agent_via_menu()` | Existing (ELITEA-1794) — download is a `.zip` this time, not `.md`; caller must branch on `download.suggested_filename` suffix |
| Agents-list Import button | `agents-import-button` | `AgentsListPage.import_button` / `import_agent()` | Existing (ELITEA-1795); `import_agent(path)` already accepts any file path — no change needed for `.zip` |
| Import preview dialog | `agent-import-preview-dialog` | `AgentsListPage.import_preview_dialog` | Existing |
| Import preview — Main entity name | `agent-import-preview-name` | `AgentsListPage.import_preview_name` | Existing |
| Import preview — **Nested Agent name** | `agent-import-preview-nested-agent-name` | **NEW** — add `AgentsListPage.import_preview_nested_agent_name = LocatorDescriptor(testid="agent-import-preview-nested-agent-name")` | Added this run (commit `74f72323` on `automation/testids`) |
| Import preview — **Nested Agent instructions** | `agent-import-preview-nested-agent-instructions` | **NEW** — add `AgentsListPage.import_preview_nested_agent_instructions = LocatorDescriptor(testid="agent-import-preview-nested-agent-instructions")` | Added this run; visible only once its card's "Show details" toggle is expanded (mirrors the Skill-card pattern; reuse `expand_import_preview_details()`) |
| Import preview card toggle (shared) | `agent-import-preview-card-toggle` | `AgentsListPage.import_preview_card_toggle` / `IMPORT_PREVIEW_COLLAPSED_TOGGLE_SELECTOR` | Existing; now also rendered for the Nested-Agent card (shared testid, multiple DOM matches — already handled) |
| Import confirm button | `agent-import-confirm-button` | `AgentsListPage.import_confirm_button` | Existing |
| Import complete dialog | `agent-import-complete-dialog` | `AgentsListPage.import_complete_dialog` | Existing |
| Import complete — Agents list | `agent-import-complete-list-agents` | `AgentsListPage.import_complete_agents_list` | Existing; text lists BOTH main+nested agent names, comma-separated, prefixed "N agents:" |
| Import complete — Got it button | `agent-import-complete-got-it-button` | `AgentsListPage.import_complete_got_it_button` / `confirm_import_complete()` | Existing; returns the new main agent's id (int) — reuse as-is |
| Imported agent's attached sub-agent card | `agent-toolkit-card` (shared with Toolkit attachments — confirmed by design, see `agent_detail_page.py:106-109` comment) | `AgentDetailPage.toolkit_card` / `is_toolkit_attached()` | Existing; filter by nested agent's name text, same pattern as toolkit assertions |
| Delete agent (cleanup) | (type-to-confirm dialog, `delete-confirm-name-input`) | `AgentDetailPage.delete_agent_via_menu(agent_name)` | Existing (`agent_detail_page.py:2544`); prefer `agent_api.delete_agent(agent_id)` in test `finally` for speed/reliability, matching every sibling spec's cleanup pattern |

## Known Defects
None product-blocking. Two non-blocking observations:

1. **Testid gap (closed this run, not filed as a defect)** — see § Testid
   work above. Per policy this is testid backfill work, not a tracked bug.
2. **Pre-existing, unrelated React dev-mode console warning**: clicking
   "Import" (confirm) surfaces one console error —
   `Warning: validateDOMNesting(...): <div> cannot appear as a descendant
   of <p>` — sourced from `IWModalSucceedContent.jsx:30`'s info-icon
   `Tooltip` (a `<div>`-containing tooltip body nested inside a `<p>` label
   in the "Imported:" header). This fires on EVERY successful import (not
   specific to the nested-Agent scenario) and is a React dev-only DOM-
   nesting warning, not a user-visible defect — no visual or functional
   symptom observed, dialog renders and functions correctly. Judged
   INFO-severity / not worth filing per `.agents/profile.md` § Bug filing
   (would be noise against a non-blocking, framework-level nit); flagging
   here for the implementer's awareness only — if the automated test
   asserts zero-console-errors during Import Complete like sibling specs
   do, it will need to explicitly filter this one known warning message
   (grep it out) or the assertion will be permanently red for reasons
   unrelated to this case.

## Cleanup
Delete, in this order (children/dependents first is not required here since
Agent-to-Agent attachment has no cascading-delete constraint observed, but
mirroring sibling specs' safety pattern anyway): imported nested agent
(id `5120` this run) → imported main agent (id `5119`) → source nested
agent (id `5117`) → source main agent (id `5118`). All four cleaned up via
UI `delete_agent_via_menu()` (type-to-confirm dialog) in this session;
recommend `agent_api.delete_agent(id)` in the automated test's `finally`
block for speed, matching every sibling spec's convention. Also delete the
locally-downloaded `.zip` file (`download_path.unlink(missing_ok=True)`).

## Blocked Steps
None.
