# Test Case: Fork Skill End-to-End

## Metadata
- **TMS ID**: ELITEA-2602
- **Linked Story**: none
- **Priority**: l2 (high, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (dev-token identity on localhost)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- Source project `Private` (id `399`) and target project `UI Testing` (id
  `400`) are both accessible — both are known-good full-CRUD projects for the
  dev-token identity (`.agents/memory/qa-engineer/fork_agent_flow_and_localhost_dev_token_permission_scoping.md`),
  confirmed live this session for skills too (fork POST 201, delete 204 in
  both).
- A valid PNG/JPG icon file under 500KB is available
  (`test-data/images/skill-fork-test-icon.png`, 1.8KB, created this session —
  no pre-existing test icon fixture existed in the repo).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Source skill name: kebab-case, e.g. `el-2602-forkable-skill-${suffix}` —
  lowercase letters/digits/hyphens only (live client-side validation, same
  rule as ELITEA-1737).
- Source skill description: 100+ characters, e.g. "Detailed description for
  fork testing purposes covering more than one hundred characters so that it
  satisfies the case's length requirement fully."
- Source skill instructions: any non-empty string, e.g. "Comprehensive
  instructions for the skill behavior used to verify the fork end-to-end
  flow ELITEA-2602."
- **Tags — MUST use underscores, NOT the case's literal hyphenated example
  values.** The case's Test Data table specifies `test-tag`, `fork-demo` —
  both contain hyphens, which the live Tags field silently rejects (0
  network calls, input cleared, no chip created — confirmed live this
  session; same root cause as `.agents/memory/qa-engineer/skill_tags_field_hyphen_rejected_and_chip_delete_icon_only.md`
  / issue #1445). **Use `test_tag` and `fork_demo` instead** (confirmed live:
  chips commit correctly). See § Known Defects — new occurrence commented on
  #1445, not re-filed.
- Custom icon: `test-data/images/skill-fork-test-icon.png` (created this
  session — 32×32 valid PNG, 1.8KB).
- Modified instructions (post-fork, on the FORKED copy): e.g. "Updated
  instructions after forking to test independence — ELITEA-2602."

No `reuse-existing` or `generate-shared-with-cleanup` data applies — this is
inherently a fresh-state round trip.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create` (source project `Private`/399).
   - **Verify**: form loads (`skill-name-input-field` visible).
2. Fill Name, Description, Instructions via the standard form fields; commit
   two tags via Enter (`test_tag`, `fork_demo` — NOT the case's literal
   hyphenated values, see Test Data note).
3. Click the skill icon avatar **twice** — the FIRST click only mounts the
   hover-triggered edit-pencil overlay (same confirmed quirk as the Agent
   icon picker, `.agents/memory/qa-engineer/agent_form_dual_component_and_icon_picker_quirks.md`);
   the SECOND click actually opens the `SelectIconDialog`
   (`agent-icon-picker-dialog`, shared component — literal `agent-` prefix,
   entity-agnostic).
4. Click the dialog's Upload button (accessible name "Upload a bmp, ico,
   gif, jpeg, jpg, png, tiff or webp image (less than 500KB)" — **no
   testid, see § Concrete Handles gap**); upload the test icon file via the
   native file chooser.
   - **Verify**: toast "The image has been uploaded"; the icon avatar in the
     form now shows the uploaded image (no explicit "select" click needed —
     upload auto-applies the icon).
5. Click Save.
   - **Verify**: URL settles on `/skills/all/{sourceSkillId}`; note the
     source skill ID (e.g. `1494` this session) and its base version ID
     (e.g. `1552`).
6. Open the skill's overflow menu (`skill-controls-menu-button`).
   - **Verify**: menu shows a "Fork" item in the VERSION group
     (`fork-menuitem`), enabled.
7. Click "Fork".
   - **Verify**: Fork wizard dialog opens (`agent-import-preview-dialog`);
     the "Main entity" card shows the skill's name and "Type: skill"
     (`agent-import-preview-name`); a "Show details" toggle
     (`agent-import-preview-card-toggle`) is present. This particular skill
     has only one Main-entity card (no "Nested entities" section — no
     attached toolkits/sub-skills, same data-driven pattern as ELITEA-1893/
     ELITEA-2051, not a missing-UI bug).
8. Expand the "Main entity" card via the toggle.
   - **Verify**: Description and Instructions text become visible, matching
     the source skill's values verbatim. **Tags are NOT shown in this
     preview** (confirmed live via `dialog.textContent` DOM check, with two
     committed tag chips present on the source) — case-text overstatement,
     not a defect; see § Known Defects (filed as clarification #1455, same
     omission confirmed for Agent/Pipeline Fork's identical shared
     component).
9. Click the target-Project selector (`agent-import-wizard-project-select-combobox`).
   - **Verify**: the dropdown lists other accessible projects
     (`Bugs & Features`, `Elitea Development`, `Elitea Testing Team`,
     `UI Testing`) — **the current/source project (`Private`, 399) is
     correctly excluded** from the option list.
10. Select the target project `UI Testing` (400) — dynamic option testid
    `select-option-400`.
    - **Verify**: the Fork confirm button becomes enabled
      (`agent-fork-confirm-button`, was disabled before a target was
      chosen).
11. Click "Fork" (`agent-fork-confirm-button`).
    - **Verify**: `POST /api/v2/elitea_core/fork/prompt_lib/400` → 201
      Created, response body's `result.skills[0].id` is the new forked
      skill's ID (e.g. `8` this session). Dialog re-renders as "Fork
      Complete" (`agent-import-complete-dialog`), listing "1 skills:
      {source-skill-name}". **One pre-existing, already-tracked console
      error fires** (`validateDOMNesting` `<p>`-in-`<p>` on
      `IWModalSucceedContent.jsx`) — see § Known Defects, issue #570,
      confirmed for Skills as a THIRD entity type after Agent/Pipeline; not
      a new finding, handle via the existing soft-assert pattern.
12. Click "Got it" (`agent-import-complete-got-it-button`).
    - **Verify**: navigates to `/skills/all/{forkedSkillId}?viewMode=owner&name=...`
      in the target project (URL/page title show `UI Testing`).
13. On the forked skill's detail page, verify via `GET
    /api/v2/elitea_core/skill/prompt_lib/400/{forkedSkillId}` (or the
    rendered form):
    - `name`, `description`, `version_details.instructions` all match the
      source verbatim.
    - `version_details.tags` = `[test_tag, fork_demo]` (both preserved,
      rendered as `skill-tag-chip` elements).
    - `version_details.meta.icon_meta.url` matches the SOURCE skill's icon
      URL exactly (same file — icon is referenced, not re-uploaded per
      fork); the icon `<img alt="elitea">` renders identically in the UI.
    - `version_details.meta.parent_entity_id` = source skill ID,
      `parent_project_id` = 399, `parent_version_id` = source base version
      ID — **lineage metadata confirmed present** (case step 17's
      requirement).
    - Detail page's Information accordion shows a "Forked from: {source
      skill name}" traceability link (`Go to original skill`, no testid —
      shared `IconLinkWithToolTip.jsx` pattern from ELITEA-2051, needs
      adding if a test asserts it directly).
14. Edit the forked skill's instructions field (replace with the "Modified
    Instructions" test data) and click Save.
    - **Verify**: `PATCH`/save succeeds, form's dirty-state clears (Save
      button disabled again).
15. Switch the sidebar project selector back to `Private` (399) — **direct
    URL navigation to the source skill's detail route while a DIFFERENT
    project is selected 404s** (`GET
    .../skill/prompt_lib/{currentlySelectedProjectId}/{id}` — confirmed
    live, `select-option-399` must be clicked first, see § Automation
    Hints).
16. Navigate to the source skill's detail page (`/skills/all/{sourceSkillId}`).
    - **Verify**: instructions field shows the ORIGINAL text, unchanged —
      confirms independence (case steps 19–20). No cross-propagation from
      the fork's edit.

## Expected Results
- Forked skill exists in the target project with all fields preserved
  (name, description, instructions, tags, custom icon).
- Lineage metadata (`parent_entity_id`, `parent_project_id`,
  `parent_version_id`) is present on the forked version's `meta`.
- Editing the fork's instructions does not change the original's
  instructions, and vice versa (independence confirmed both ways this
  session — only the fork→original direction is in the case's own steps,
  but the reverse holds structurally since they are now separate skill
  records).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create skill w/ name, desc, instructions, tags, icon | all fields populated | steps 1–4 | step 5 save + step 13 GET | asserted |
| 2 Save the skill | saved successfully | step 5 | step 5 URL settle | asserted |
| 3 Open overflow menu | menu appears | step 6 | step 6 | asserted |
| 4 Verify Fork option present/enabled | visible, clickable | step 6 | step 6 | asserted |
| 5 Click Fork | wizard opens | step 7 | step 7 | asserted |
| 6 Verify Main entity card shows details | name, description, expandable | step 7 | step 7 | asserted |
| 7 Expand Main entity card | full details visible (instructions, tags, etc.) | step 8 | step 8 | asserted *(amended: tags NOT shown in preview — case-text overstatement, clarification #1455, not a defect; description+instructions ARE shown)* |
| 8 Verify project dropdown present | dropdown with projects | step 9 | step 9 | asserted |
| 9 Verify current project excluded | Project A not in dropdown | step 9 | step 9 | asserted |
| 10 Select target project | Project B selected | step 10 | step 10 | asserted |
| 11 Click Fork/Confirm | operation completes, success shown | step 11 | step 11 | asserted |
| 12 Navigate to Project B Skills | list loads | step 12 | step 12 | asserted |
| 13 Locate forked skill | appears in list | step 12 | step 12 (direct nav via Got-it) | asserted *(decomposed — Got-it navigates directly onto the card, list-locate not separately exercised)* |
| 14 Open forked skill, verify all fields | name/desc/instructions match | step 13 | step 13 | asserted |
| 15 Verify tags preserved | both tags present | step 13 | step 13 | asserted |
| 16 Verify custom icon preserved | same icon displayed | step 13 | step 13 | asserted |
| 17 Check lineage metadata | parent_entity_id, parent_project_id, parent_version_id | step 13 | step 13 | asserted |
| 18 Edit forked instructions, save | saved successfully | step 14 | step 14 | asserted |
| 19 Navigate back to Project A, open original | original loads | steps 15–16 | step 16 | asserted |
| 20 Verify original instructions UNCHANGED | no cross-propagation | step 16 | step 16 | asserted |

### Axis 2 — Analyst additions

- step 11 asserts the fork POST's exact response shape
  (`result.skills[0].id`) — *added: needed to derive the forked skill's ID
  for step 13's verification, and it's the only reliable source (the "Got
  it" navigation URL also carries the ID as a path segment, a redundant
  cross-check).*
- step 11 notes the pre-existing #570 console error explicitly — *added: so
  the implementer applies the established soft-assert pattern instead of
  either masking it or letting it fail the whole test as a NEW unexplained
  error.*
- step 15 documents the project-switch-before-cross-project-navigation
  requirement — *added: discovered live (a naive direct URL nav 404s); this
  is a genuine navigation gotcha any implementation must handle, not
  optional.*

## Cleanup
1. Delete the forked skill in the target project (`UI Testing`/400) via UI
   delete flow (`skill-delete-menu-item` → type-to-confirm dialog).
2. Delete the source skill in `Private`/399 the same way.
3. Both confirmed via live `DELETE` returning 204 this session — no cleanup
   permission gaps encountered for skills in either project (unlike the
   agent-delete gap noted for project 471 in the fork memory entry — not
   applicable here since this case uses 399→400).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skill name input | `getByTestId('skill-name-input-field')` | none needed (pre-existing) |
| Skill description input | `getByTestId('skill-description-input-field')` | none needed |
| Instructions editor | `getByTestId('skill-instructions-editor-content')` | none needed |
| Tags input | `getByTestId('skill-tags-input-field')` | none needed |
| Tag chip (collection) | `getByTestId('skill-tag-chip')` | none needed |
| Tag chip delete icon (per-tag) | `[data-testid="skill-tag-chip-delete-{tagName}"]` (class constant, dynamic) | none needed |
| Skill icon avatar (form) | **testid needed: `skill-form-icon-button`** — `EntityIcon` in `CreateSkillForm.jsx` passes NO `data-testid` prop at all (confirmed via source read); mirrors the Agent flow's `agent-form-icon-button` (ELITEA-1899 rework, both `CreateAgentForm.jsx`/`ApplicationEditForm.jsx`) which this Skill call site never received | interim: `page.locator('.MuiBox-root').filter(...)` — brittle, do NOT ship; add the testid |
| Icon picker dialog | `getByTestId('agent-icon-picker-dialog')` (shared, literal `agent-` prefix, entity-agnostic — confirmed live for Skills) | none needed |
| Icon picker upload button | **testid needed: `agent-icon-picker-upload-button`** (or entity-agnostic equivalent) — `SelectIconDialog.jsx`'s `headerActions` `IconButton` has no `data-testid`, only a tooltip accessible name; confirmed via source read, same gap for every entity type that uses this dialog | interim used during THIS exploration only: `getByRole('button', {name: /Upload a bmp/})` — do NOT ship, add the testid |
| Icon picker close button | `getByTestId('agent-icon-picker-close-button')` | none needed |
| Save button (create form) | `getByTestId('skill-save-button')` | none needed |
| Skill controls overflow menu | `getByTestId('skill-controls-menu-button')` | none needed |
| Fork menuitem | `getByTestId('fork-menuitem')` — **note: generic testid, not entity-scoped** (`SkillControls.jsx`'s `key: 'fork'` in its own `useForkSkill`-driven menu item, NOT the shared `ForkEntityButton.jsx`/`useForkEntityMenu()` hook Agent/Pipeline/Toolkit use — Skill Fork is a separately-implemented menu entry that happens to render via the same `DotMenu`/`ControlsDropdown`, confirmed via source read of `SkillControls.jsx`) | none needed — unique within this menu, functionally sufficient despite the naming inconsistency |
| Fork wizard dialog | `getByTestId('agent-import-preview-dialog')` (pre-fork) / `agent-import-complete-dialog` (post-fork) — shared, do not assert a single fixed testid across the action | none needed |
| Fork wizard Main-entity name | `getByTestId('agent-import-preview-name')` | none needed |
| Fork wizard card-details toggle | `getByTestId('agent-import-preview-card-toggle')` | none needed |
| Fork wizard project select trigger | `getByTestId('agent-import-wizard-project-select-combobox')` | none needed |
| Fork wizard project option (dynamic) | `[data-testid="select-option-{projectId}"]` (class constant, dynamic — e.g. `select-option-400`) | none needed |
| Fork confirm button | `getByTestId('agent-fork-confirm-button')` | none needed |
| Fork Complete "Got it" button | `getByTestId('agent-import-complete-got-it-button')` | none needed |
| Sidebar project switcher trigger | `getByTestId('project-selector-trigger-combobox')` | none needed |
| Sidebar project option (dynamic) | `[data-testid="select-option-{projectId}"]` (same dynamic template as the fork wizard's — shared `Select`) | none needed |
| Skill delete menuitem | `getByTestId('skill-delete-menu-item')` | none needed |
| Delete-confirm name input | `getByTestId('delete-confirm-name-input')` (wrapper) → real `<input id="name">` inside it | none needed |
| Delete-confirm button | `getByTestId('delete-confirm-button')` | none needed |
| "Forked from" traceability link | **testid needed** — `IconLinkWithToolTip.jsx`, `aria-label="Go to original skill"`, no testid (same gap ELITEA-2051 found on the Pipelines dashboard-card variant; here it's the DETAIL page's Information-accordion row, a separate, correctly-existing occurrence — don't conflate the two per the ELITEA-2051 case-text gotcha) | interim: `getByRole('link', {name: /Go to original/})` if a test needs to assert this row directly; not required by this case's pass criteria |

## Network Behavior
- `POST /api/v2/elitea_core/upload_skill_icon/prompt_lib/{projectId}` — 200,
  fires on file-chooser selection (before Save).
- `POST /api/v2/elitea_core/skills/prompt_lib/{projectId}` — 201, fires on
  Save (skill creation).
- `GET /api/v2/elitea_core/skill_export_fork/prompt_lib/{sourceProjectId}/{skillId}/{versionId}`
  — 200, fires when the Fork wizard opens (pre-loads the preview data).
- `POST /api/v2/elitea_core/fork/prompt_lib/{targetProjectId}` — 201, fires
  on Fork confirm. Response: `{"result": {"agents": [], "toolkits": [],
  "skills": [{"id": <newId>, "name": ..., "reused": false, "index": 0}]},
  "errors": {...}}`.
- `GET /api/v2/elitea_core/skill/prompt_lib/{projectId}/{skillId}` — 200,
  the source of truth for all field/lineage assertions (§ Concrete Handles
  doesn't need to touch the DOM for tags/icon/lineage — this response is
  more reliable and faster).
- `DELETE` skill endpoint — 204, on cleanup.

## Known Defects Found During Exploration
- **[Case-text drift, not a bug]** Test Data's `test-tag`/`fork-demo` values
  contain hyphens, silently rejected by the live Tags field (0 network
  calls). Same root cause as issue #1445 (filed for ELITEA-2433's
  `regression-v1`) — commented the new occurrence there rather than
  re-filing (dedup rule). Use `test_tag`/`fork_demo` in automation.
- **[Case-text drift, not a bug]** Case step 7 expects the expanded
  Main-entity card to show "instructions, tags, etc." but tags are never
  rendered in the Fork preview for any entity type (Agent/Pipeline/Skill
  all share the component). Filed as clarification:
  https://github.com/EliteaAI/elitea-testing-public/issues/1455.
- **[MINOR, already tracked]** `validateDOMNesting` `<p>`-in-`<p>` React
  console warning fires on the Fork Complete dialog
  (`IWModalSucceedContent.jsx`) — pre-existing issue #570, confirmed
  live for Agents (ELITEA-1893) and Pipelines (ELITEA-2051); now confirmed
  for Skills too (third entity type, same shared component, same cause).
  Not a new finding — handle with the same soft-assert +
  `# Known defect: #570` pattern the other two fork tests already use.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- No `SkillAPI` client exists yet in `automation/api/` — unlike
  `PipelineAPI`/`AgentAPI`, skill creation for this test currently must go
  through the UI form (matches the case's own intent — it explicitly tests
  the create-form icon/tag UI, so API-shortcutting the SOURCE skill's
  creation would under-test the case anyway).
- Reuse `SkillDetailPage`/`SkillFormPage`/`SkillsListPage` from
  `automation/pages/` — all the non-Fork handles above already exist as
  `LocatorDescriptor` fields; only the Fork-specific ones (all shared with
  `AgentDetailPage`'s existing fields) need new fields added to
  `SkillDetailPage`, mirroring `AgentDetailPage`'s `fork_menuitem` /
  `fork_wizard_dialog` / `fork_project_select_trigger` /
  `fork_confirm_button` / `fork_complete_got_it_button` /
  `FORK_PROJECT_OPTION` block (`agent_detail_page.py:343-473`) — copy the
  pattern, note the Skill menuitem testid is `fork-menuitem` (generic),
  NOT `agent-actions-fork-menuitem`.
- **Cross-project navigation**: use the sidebar project-switcher
  (`project-selector-trigger-combobox` → `select-option-{id}`) BEFORE any
  direct URL navigation to a detail page in a different project — a bare
  `page.goto()` to another project's skill ID 404s (the currently-selected
  project scopes the GET). Mirrors `PipelinesListPage.switch_project()`'s
  existing pattern (`test_pipeline_fork_to_different_project.py`) — a
  `SkillsListPage.switch_project()` (or reuse of a shared/base-page helper)
  should exist or be added.
- Two test icon files needed system-wide checking: none existed in the
  repo before this session; `test-data/images/skill-fork-test-icon.png`
  (created this analysis run, 1.8KB PNG) is a suitable disposable fixture —
  add it to the repo as committed test data (not `.gitignore`d) for reuse
  by this and any future icon-upload case.
- Two-click icon-avatar quirk (mount-then-activate) is an automation-only
  Playwright artifact per the existing Agent-icon memory entry — script
  TWO `.click()` calls on the same locator with a short pause between, do
  not treat as a product bug.
