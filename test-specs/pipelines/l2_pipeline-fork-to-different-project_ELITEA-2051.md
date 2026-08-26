# Test Case: Pipeline — Fork to a different project

## Metadata
- **TMS ID**: ELITEA-2051
- **Linked Story**: none
- **Priority**: l2 (source case frontmatter: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` on localhost).
- At least two projects are accessible to the user. Confirmed live: five
  projects available in the project selector — `Private` (id `399`,
  home/default project), `Bugs & Features` (id `406`), `Elitea Development`
  (id `25`), `Elitea Testing Team` (id `471`), `UI Testing` (id `400`).
- A pipeline exists in a project OTHER than the fork target, accessible to
  the user (the case's "pipeline from another project"). This AFS forks
  FROM `UI Testing` (400) INTO `Private` (399, the user's default/home
  project) — the inverse project-pair direction from the sibling Agent case
  (ELITEA-1893 forks Private → UI Testing), but the mechanic is identical:
  Fork always operates from whichever project is currently selected into a
  user-chosen target, so which project is "source" and which is "target" is
  a test-data choice, not a product behavior difference. `UI Testing` (400)
  is used as source here (rather than creating a disposable one, see
  below) purely to also exercise navigating there via the project switcher,
  matching the case's "from another project" framing more literally than a
  same-project fork would.

## Test Data

### reuse-existing (source, read-only — Fork never mutates its source)
- Source pipeline: `Pipeline UI Testing` (id `4`, base version id `5`,
  project `UI Testing`/400) — pre-existing, single-version, description
  "This is a nested pipeline for UI testing", Step Limit `25`, one Tool
  node ("Tool 1", flagged `Deprecated!` in the canvas — pre-existing
  environment state, unrelated to this case), no toolkits/skills/nested
  agents attached. Confirmed live via the Fork wizard's Main-entity preview
  card AND via the pipeline detail page's own General/Advanced sections
  (byte-identical name/description/step-limit both places).
  - **Implementer note (same Hard-Rule-10 read-only-by-default reasoning as
    ELITEA-1893's AFS, applied to a DIFFERENT concern):** relying on a
    hardcoded pipeline id (`4`) that happens to exist in one environment's
    `UI Testing` project is an environment coupling most sibling
    Fork/Export/Import tests in this suite avoid by creating their own
    source entity per run. Since Fork's source is read-only end-to-end
    (this case's steps never mutate the source, only the *forked copy*),
    the implementer SHOULD create a fresh, disposable source pipeline via
    `pipeline_api.create_pipeline(name=..., description=...)` in project
    400 at the top of every run (mirrors ELITEA-1893's `el-1893-agent-{uuid8}`
    pattern) instead of depending on id `4` — this AFS reused the
    pre-existing pipeline live to save exploration time, but the automated
    test should NOT hardcode it.

### generate-per-test (created fresh by the implementation itself)
- Forked pipeline — created fresh by the Fork action in each run; deleted
  via the UI's type-to-confirm delete flow in the test's own cleanup
  (confirmed live this session: `DELETE
  /api/v2/elitea_core/application/prompt_lib/399/{forked-id}` → `204 No
  Content`).

## Test Steps

(Live-executed and confirmed this session: source pipeline `Pipeline UI
Testing`, id `4`, project `UI Testing`/400 → forked into `Private`/399 →
new pipeline id `8243`, version id `8499` → deleted via UI cleanup.)

1. Navigate to a pipeline that lives in a project OTHER than the fork
   target (`Pipeline UI Testing`, id `4`, project `UI Testing`/400) — via
   the project switcher (`project-selector-trigger-combobox`) then the
   Pipelines dashboard card/row.
   - **Verify**: pipeline detail page loads; `get_name()` returns
     `Pipeline UI Testing`; `get_pipeline_id()` returns `4`.
2. Click the three-dot Actions menu button (`agent-actions-menu-button`).
   **Verify**: the menu opens (`agent-actions-menu`), showing a VERSION
   group with `Fork` (`pipeline-actions-fork-menuitem`) enabled.
3. Click the `Fork` menuitem. **Verify**: the Fork wizard dialog opens
   (`agent-import-preview-dialog`), titled "Fork parameters", showing a
   Project selector (placeholder "Select project", combobox testid
   `agent-import-wizard-project-select-combobox`) and the Main-entity
   preview card (name `agent-import-preview-name` = "Pipeline UI Testing",
   "Type: pipeline"). The `Fork` confirm button
   (`agent-fork-confirm-button`) is **disabled** before a target project is
   selected.
4. Click the Project selector and choose a target project DIFFERENT from
   the source (`Private`/399, dropdown option `select-option-399`).
   **Verify**: the combobox now shows "Private"; the hidden field shows
   `399`; the `Fork` confirm button becomes **enabled**.
5. Verify the entity-preview card shows the main pipeline (and any nested
   dependencies). **Verify**: exactly one entity-preview card renders
   (`agent-import-preview-card-toggle.count() == 1` — this source pipeline
   has no attached toolkits/skills/nested agents/pipelines, so correctly no
   "Nested entities" section, same data-driven behavior ELITEA-1893's AFS
   documented for Agent Fork). The card additionally shows a
   "Pipeline Diagram:" preview (testid `chat-mermaid-diagram-svg-container`)
   — **NEW handle, not present in the Agent-entity Fork wizard** (agents
   have no pipeline diagram to preview) — see § Known Defects for a
   rendering issue found on this preview.
6. Click `Fork` (`agent-fork-confirm-button`). **Verify**: network call
   `POST /api/v2/elitea_core/fork/prompt_lib/399` → `201 Created`
   (confirmed live). Dialog re-renders in-place as "Fork Complete"
   (same `agent-import-complete-dialog` container swapping from
   `agent-import-preview-dialog`, per the shared `ImportWizardModal`
   mechanism ELITEA-1893's AFS documents), showing `Forked: 1 pipelines:
   Pipeline UI Testing` — the count line's value list carries testid
   `agent-import-complete-list-pipelines` (the **pipelines** variant of the
   `agent-import-complete-list-{entityKey}` family ELITEA-1893's AFS
   predicted but did not itself confirm — confirmed live here).
7. Click `Got it` (`agent-import-complete-got-it-button`). **Verify**:
   navigates to `/pipelines/all/{new-pipeline-id}?viewMode=owner&name=Pipeline%20UI%20Testing`.
   Confirmed live: new pipeline id `8243` (source was `4` — **different,
   satisfying case Step 7's "new unique Pipeline ID"**), new version id
   `8499` (source base version was `5`). The project selector combobox now
   shows "Private" — confirms navigation lands the user inside the TARGET
   project (399), not merely at a URL referencing the new id.
8. **Verify forked pipeline has a new unique Pipeline ID** (case Step 7 —
   executed together with Step 7 above since both are asserted from the
   same post-navigation state): `forked_pipeline_id != source_pipeline_id`
   (`8243 != 4`, confirmed).
9. **Verify forked pipeline shows "Forked from" link on the dashboard
   card** (case Step 6). Navigate to the Pipelines dashboard
   (`/pipelines/all`, Card list view — the default) in project `Private`
   (399). **Verify**: the forked pipeline's card shows a "Forked from"
   link — confirmed live via DOM: `<a aria-label="Forked from - Original
   pipeline" href=".../400/pipelines/all/4/5?viewMode=owner">` (icon-only
   link, tooltip text is the dynamic "Forked from - {sourceName}" —
   `sourceName` loads lazily on tooltip hover via `loadSourceName`, so
   don't assert the tooltip text without triggering `hover`/`onOpen`
   first). **This link has NO `data-testid`** — see § Concrete Handles,
   `testid needed`. **CLARIFICATION on case wording**: the "Forked from"
   attribution does NOT appear on the pipeline DETAIL page's dashboard-card
   equivalent by that name — it appears on the **Pipelines LIST page's
   card** (Card list view). The detail page separately shows a `Forked
   from:` row inside its "Information" accordion (testid
   `agent-information-section`, no dedicated sub-testid on the row itself)
   with a "Go to original pipeline" text link — this is a SEPARATE, ALSO
   accurate rendering of the same fact, not the one the case names. Both
   are live-confirmed; the case's literal "dashboard card" phrase resolves
   to the LIST page's card, not the detail page — not a defect, just
   requires checking the right page (see § Known Defects note below; not
   filed, correctly interpretable from case text + product behavior, no
   CLARIFICATION ticket needed since "dashboard card" unambiguously means
   the list/card view once observed).

## Expected Results
- Forking `Pipeline UI Testing` (id 4, `UI Testing`/400) via the
  three-dot menu → Fork wizard, into a different target project
  (`Private`/399), succeeds: the wizard shows the correct entity card
  (main entity only, since this source pipeline has no nested
  dependencies), the `Fork` action returns `201 Created`, and clicking
  `Got it` navigates the user into the target project, onto the newly
  forked pipeline.
- The forked pipeline has a new unique Pipeline ID (`8243 != 4`) and
  Version ID (`8499 != 5`).
- The forked pipeline's Name/Description/Step Limit match the source
  exactly.
- The Pipelines dashboard (list, Card view) shows a "Forked from" icon-link
  on the forked pipeline's card, pointing back to the original pipeline's
  URL.
- The pipeline detail page's Information section ALSO shows a "Forked
  from:" row with a "Go to original pipeline" link (bonus, beyond case
  text — same underlying fact, different surface).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | N/A (localhost `auth_state`) | `auth_state` fixture; session active throughout | asserted |
| Precondition: a pipeline from another project is accessible | Pipeline reachable | Test Step 1 | Navigated via project switcher to `UI Testing`/400, opened `Pipeline UI Testing` (id 4) | asserted |
| 1 Navigate to a pipeline from a different project | Pipeline is displayed | step 1 | `get_name()`/`get_pipeline_id()` match | asserted |
| 2 Click three-dot menu → "Fork" | Fork modal opens | steps 2–3 | `agent-actions-menu` visible, then `agent-import-preview-dialog` visible | asserted |
| 3 Verify fork modal opens and fork parameters are displaying | Fork modal shows project selection and fork options | step 3 | dialog title "Fork parameters", project selector + Main-entity card both visible | asserted |
| 4 Select a target project and click "Fork" | Fork request is submitted | steps 4–6 | `select-option-399` clicked, Fork button enabled, `POST .../fork/prompt_lib/399` → 201 | asserted |
| 5 Verify a forked copy is created in user's own project | Forked pipeline appears in the user's project | step 7 | navigation to `/pipelines/all/8243...`, project selector shows "Private" | asserted |
| 6 Verify forked pipeline shows "Forked from" link on the dashboard card | Dashboard card shows attribution | step 9 | list-page card's `aria-label="Forked from - Original pipeline"` link, confirmed live | asserted — **CLARIFICATION note: "dashboard card" = the Pipelines LIST page's card, not the detail page (both correctly show the fact, on different surfaces) — see step 9** |
| 7 Verify forked pipeline has a new unique Pipeline ID | Forked pipeline ID differs from original | step 8 | `8243 != 4` | asserted |
| Expected Final State: pipeline forked with new unique ID + "Forked from" attribution | — | steps 6–9 | steps 6–9 | asserted |
| Pass/Fail: all steps complete without errors; new unique ID; "Forked from" attribution present | — | all steps | all steps + console-error check (see Axis 2) | asserted |

### Axis 2 — Analyst additions

- **Source pipeline's own General/Advanced fields re-verified against the
  Fork wizard's preview** (Name, Description, Step Limit) — *added: proves
  the wizard's Main-entity card is data-driven from the live source, not a
  static/stale render — same class of check ELITEA-1893's AFS ran for
  Agent Fork, applied here.*
- **Entity-preview card count == 1 (no "Nested entities" section)** —
  *added: confirms the wizard's card rendering correctly reflects a
  dependency-free source (data-driven, not a missing-UI defect) — same
  reasoning ELITEA-1893's AFS documented for the Agent case, now confirmed
  independently true for a Pipeline source too.*
- **`agent-import-complete-list-pipelines` testid (the `pipelines` variant
  of the shared `{entityKey}` family)** — *added: ELITEA-1893's AFS
  predicted this testid pattern for "a future case that forks a pipeline"
  but never confirmed it live. This case confirms it exists exactly as
  predicted — closes that open prediction.*
- **`chat-mermaid-diagram-svg-container` — the Fork wizard's "Pipeline
  Diagram" mermaid preview, unique to Pipeline-entity Fork (Agents don't
  render one)** — *added: this preview showed a "Diagram syntax error
  detected" message live (see § Known Defects) — worth a permanent record
  even though the case doesn't ask for a diagram-preview assertion, so this
  isn't silently rediscovered as a "new" bug later.*
- **Console-error check across the whole Fork flow** — *added: zero-cost
  given the live session was already open. The SAME known, filed defect
  (#570, `validateDOMNesting` `<p>`-in-`<p>` warning on the Fork/Import
  Complete dialog) reproduced 1/1 here too — see § Known Defects; this
  extends #570's confirmed blast radius to the Pipeline entity, not a new
  defect.*
- **Forked pipeline's detail-page "Forked from:" Information-section row**
  — *added: a second, independently-live-confirmed surface for the same
  underlying fact the case's dashboard-card step names — worth recording so
  the implementer knows BOTH surfaces exist and picks the right one (list
  card) for the case's literal step, without concluding the detail-page row
  is the intended target.*

## Cleanup
1. Delete the forked pipeline via the UI's three-dot menu → "Delete
   pipeline" → type-to-confirm dialog (confirmed live this session:
   `DELETE /api/v2/elitea_core/application/prompt_lib/399/{forked-id}` →
   `204 No Content`).
2. The source pipeline (`Pipeline UI Testing`, id 4, project 400) is
   READ-ONLY throughout this case (Fork never mutates its source) —
   **if the implementer follows the Test Data recommendation and creates a
   fresh disposable source pipeline instead of reusing id 4**, that source
   also needs `pipeline_api.delete_pipeline()` cleanup in a `finally`
   block (mirrors ELITEA-1893's source-agent cleanup). This analyst
   session itself reused the pre-existing id-4 pipeline and left it
   untouched — no residue from the source side.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy.

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Three-dot Actions menu button | `agent-actions-menu-button` | on-main ✓ | existing `PipelineDetailPage.actions_menu_button` (via `open_actions_menu()` — note: current `open_actions_menu()` uses a positional-JS-evaluate fallback, not this testid directly; a testid-based click is safe here, confirmed live) |
| Actions menu container | `agent-actions-menu` | on-main ✓ | confirmed live |
| Fork menuitem | `pipeline-actions-fork-menuitem` | on-main ✓ | existing `PipelineDetailPage.fork_menuitem` field (per ELITEA-2049's AFS) — **entity-scoped, DIFFERENT from Agent's `agent-actions-fork-menuitem`** (`ForkEntityButton.jsx`'s `FORK_MENU_ITEM_KEY_BY_ENTITY` map) |
| Fork wizard dialog (pre-fork) | `agent-import-preview-dialog` | on-main ✓ | shared `ImportWizardModal` component — same testid family as Agent Fork (ELITEA-1893) and Pipeline Import (ELITEA-2012, `PipelinesListPage.import_preview_dialog`) |
| Fork wizard dialog (post-fork) | `agent-import-complete-dialog` | on-main ✓ | same container swaps testid in place — do not assert a single fixed testid persisting across the fork action |
| Fork wizard Project selector trigger | `agent-import-wizard-project-select-combobox` (outer wrapper: `agent-import-wizard-project-select`) | on-main ✓ | confirmed live — identical to `AgentDetailPage.fork_project_select_trigger`'s testid value; **NEW field needed on `PipelineDetailPage`** (does not yet exist there) |
| Fork wizard project dropdown option | `select-option-{projectId}` | on-main ✓ | confirmed live: `select-option-399` fired; same dynamic-testid family already in `PipelineDetailPage.SELECT_OPTION` / `AgentDetailPage.FORK_PROJECT_OPTION` |
| Fork wizard Main-entity card name | `agent-import-preview-name` | on-main ✓ | confirmed live, text "Pipeline UI Testing" |
| Fork wizard Main-entity card toggle | `agent-import-preview-card-toggle` | on-main ✓ | confirmed live, count()==1 for a dependency-free source |
| **Fork wizard Pipeline Diagram mermaid preview** | `chat-mermaid-diagram-svg-container` | on-main ✓ | **NEW handle, Pipeline-entity-only** (no Agent-entity equivalent) — confirmed live; see § Known Defects for a "Diagram syntax error detected" message observed on this preview |
| **Fork confirm button** | `agent-fork-confirm-button` | on-main ✓ | confirmed live — same shared `IWModalForkButton.jsx` component/testid Agent Fork uses (literal `agent-` prefix is naming tech debt, not entity-scoped — static-source-confirmed: the button's `mainEntityName`-based fork dispatch has no per-entity testid branch) |
| Fork-complete "Forked: N pipelines: ..." value | `agent-import-complete-list-pipelines` | on-main ✓ | confirmed live — the **pipelines** variant of the `agent-import-complete-list-{entityKey}` family; matches `PipelinesListPage.import_complete_pipelines_list`'s existing testid exactly (same shared component reused by both Import and Fork) |
| "Got it" button (post-fork) | `agent-import-complete-got-it-button` | on-main ✓ | confirmed live, drives navigation to the forked pipeline |
| Forked-pipeline detail page — "Forked from:" row | none observed | needs-adding (bonus handle, beyond case scope for the DETAIL page — the case's actual target is the LIST page's card, see below) | inside `agent-information-section` accordion; no dedicated sub-testid on the row |
| **Pipelines LIST page card — "Forked from" link (case's actual target, Step 6/9)** | **none — testid needed** | needs-adding | Confirmed live via DOM: `<a aria-label="Forked from - Original pipeline" href="{origin}/{sourceProjectId}/pipelines/all/{sourceId}/{sourceVersionId}?viewMode=owner">`, `getAttribute('data-testid')` → `null`. Root cause (static, `EliteaUI/src/components/Fork/IconLinkWithToolTip.jsx`): the `Link` component renders no `data-testid` at all. This component is SHARED (also rendered by `DataTableNameCell.jsx`/`DataTableRow.jsx` for Table view, and by `Card.jsx` for Card view — Agents/Skills/Pipelines all route through it), so the fix should thread a caller-agnostic generic prop (e.g. `data-testid="entity-card-forked-from-link"`, mirroring the existing generic `entity-card-name` sibling testid on the same card) rather than a feature-scoped one — this is a shared leaf component per `.agents/testing.md`'s "shared components never hardcode feature-scoped testids" rule. Implementer: add via `add-data-testid`. |
| Project selector (sidebar) | `project-selector-trigger-combobox` | on-main ✓ | existing pattern on `ChatPage`/`AnalyticsPage`/`AdminUsersPage` (`switch_project()` method) — **NEW field/method needed on `PipelineDetailPage`/`PipelinesListPage`** (neither currently has it) — same testid, same shared sidebar component |
| Project dropdown option (sidebar) | `select-option-{projectId}` | on-main ✓ | confirmed live: `select-option-400` (switch to UI Testing) |
| Delete pipeline menuitem (cleanup) | `delete-agent-menuitem` | on-main ✓ | existing, per ELITEA-2022's AFS lineage |
| Delete-confirmation dialog (cleanup) | `delete-confirm-dialog` / `delete-confirm-message` / `delete-confirm-button` | on-main ✓ | existing `PipelineDetailPage` fields |
| Delete-confirmation Name input (cleanup) | `delete-confirm-name-input` | on-main ✓ (confirmed live) | **NEW field needed on `PipelineDetailPage`** (exists on `AgentDetailPage` already) — wraps an inner `#name` `<input>`, fill via `.locator('#name').fill(...)` |
| Fork network call | `POST /api/v2/elitea_core/fork/prompt_lib/{target-project-id}` → `201 Created` | n/a (network) | confirmed live: `POST .../fork/prompt_lib/399` → 201; body shape per `IWModalForkButton.jsx`'s `agents`-keyed `main_entity` payload (pipelines are backend-classified as `agents` with `agent_type: 'pipeline'` — confirmed via static read of `useForkEntity.jsx`/`IWModalForkButton.jsx`'s `forkFuncMap`, which has no separate `pipelines` key) |
| Cleanup (delete) network call | `DELETE /api/v2/elitea_core/application/prompt_lib/{project-id}/{pipeline-id}` → `204 No Content` | n/a (network) | confirmed live: `DELETE .../application/prompt_lib/399/8243` → 204 |
| Export/probe network call (Fork's data-fetch, fires on menu click before the wizard shows) | `GET /api/v2/elitea_core/export_import/prompt_lib/{source-project-id}/{source-id}?fork=true&follow_version_ids={version-id}` → `200 OK` | n/a (network) | confirmed live: `GET .../export_import/prompt_lib/400/4?fork=true&follow_version_ids=5` → 200 — this is what populates the wizard's Main-entity preview card BEFORE the user picks a target project |

## Network Behavior
- Clicking `Fork` on the actions menu fires `GET
  /api/v2/elitea_core/export_import/prompt_lib/{source-project}/{source-id}?fork=true&follow_version_ids={version-id}`
  (200) — this populates the wizard's preview card. No project selection is
  required for this call; it fires immediately.
- Selecting a target project and clicking the wizard's `Fork` button fires
  `POST /api/v2/elitea_core/fork/prompt_lib/{target-project-id}` (201) —
  body carries `{ main_entity: 'agents', applications: [...] }` (pipelines
  are backend-classified as `agents` with `agent_type: 'pipeline'`).
- Cleanup fires `DELETE
  /api/v2/elitea_core/application/prompt_lib/{project-id}/{pipeline-id}`
  (204).

## Known Defects Found During Exploration

1. **MINOR — `<p>` nested inside `<p>` (invalid HTML) on the Fork Complete
   dialog — SAME known defect as ELITEA-1893, now confirmed to also fire
   for the Pipeline entity.** Already filed:
   [EliteaAI/elitea-testing-public#570](https://github.com/EliteaAI/elitea-testing-public/issues/570).
   Root cause unchanged (`IWModalSucceedContent.jsx`, shared by both
   Agent and Pipeline Fork). Not filed again (same root cause, same
   component, same issue) — this AFS records the reproduction so the
   implementer's soft-assertion pattern (per ELITEA-1893's
   `test_fork_agent_to_different_project.py`'s `soft_failures` +
   `# Known defect: #570` comment) is reused here too, not re-derived.
   Reproduced 1/1 live.

2. **Possible defect, NOT filed this session — flagged for investigation,
   not confirmed as a genuine repro.** The Fork wizard's "Pipeline
   Diagram:" preview (`chat-mermaid-diagram-svg-container`) showed a
   "Diagram syntax error detected" message instead of rendering the
   source pipeline's actual flow (Start → Tool 1 → END) as a diagram, for
   the specific source pipeline used this session (`Pipeline UI Testing`,
   id 4). **No console error accompanied this** (0 console errors at the
   time, confirmed via `browser_console_messages`) — the mermaid parse
   failure is caught and shown as an in-UI fallback message, not a crash.
   Not filed as a defect because: (a) this is a PREVIEW-only surface not
   named anywhere in the case text (Axis 2, not Axis 1 — see above), (b)
   a single-pipeline repro does not by itself rule out the source
   pipeline's own diagram data being the actual cause (e.g. the
   "Deprecated!" tool node, or a stale/malformed `pipeline_settings`
   payload on this specific pre-existing test-data pipeline) rather than a
   general Fork-preview defect, and (c) the pristine-repro gate
   (`.claude/skills/test-case-analysis/references/defect-filing.md`) calls
   for isolating root cause before filing, which this session's turn
   budget did not cover. **Flagged for the implementer/next analyst**: if
   automating with a FRESH `pipeline_api.create_pipeline()`-created source
   (as this AFS's Test Data section recommends) still shows "Diagram
   syntax error detected" in the Fork preview, that would isolate it to a
   general Fork-preview defect (not this specific pipeline's data) and
   should be filed then, with that reproduction as evidence.

## Blocked Steps
None. All 7 case steps automate cleanly against the live product. Two
testid gaps exist (`agent-import-wizard-project-select` on
`PipelineDetailPage` — a pure page-object addition, testid already on
main; and the Pipelines-list "Forked from" link — a genuine
`add-data-testid` gap) — neither blocks automating the rest of the case;
the "Forked from" assertion can be written directly against the confirmed
`aria-label`/`href` pair as an interim fallback ONLY if the testid work is
deferred, though per this project's testid-only locator policy adding the
testid is the correct default (case Step 6 genuinely touches this
element, earning it a real testid per `.agents/testing.md`).

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches every other pipeline spec).
- Reuse `pipeline_api.create_pipeline()` / `pipeline_api.delete_pipeline()`
  (with an explicit `project_id="400"` `PipelineAPI` instance, or a second
  `PipelineAPI(browser_cookies=..., project_id="400")`) for the source
  pipeline per the Test Data recommendation above — do NOT hardcode source
  id `4`.
- Add new `LocatorDescriptor` fields to `PipelineDetailPage` mirroring
  `AgentDetailPage`'s existing Fork-wizard fields exactly (same testids,
  confirmed shared components — see § Concrete Handles):
  `fork_wizard_dialog`, `fork_complete_dialog`, `fork_main_entity_name`,
  `fork_entity_card_toggle`, `fork_project_select_trigger`,
  `fork_confirm_button`, `fork_complete_pipelines_list` (testid
  `agent-import-complete-list-pipelines` — note the **pipelines** suffix,
  NOT `-agents` like `AgentDetailPage.fork_complete_agents_list`),
  `fork_complete_got_it_button`, and the `FORK_PROJECT_OPTION` dynamic
  template. Add matching `open_fork_wizard()` / `select_fork_target_project()`
  / `confirm_fork()` / `confirm_fork_complete()` actions, same shapes as
  `AgentDetailPage`'s (`automation/pages/agent_detail_page.py:3466-3554`).
  Do NOT reuse the existing `fork_pipeline_via_menu()` stub (role/text-based,
  `"Fork"|"Duplicate"|"Clone"` label matching, no wizard-flow support) — it
  is legacy tech debt, unrelated to this AFS's testid-based flow, and out
  of this case's touched scope to fix.
- Add `project_selector_trigger` (`project-selector-trigger-combobox`) +
  a `switch_project(project_id)` method to `PipelineDetailPage` (or
  `PipelinesListPage`, whichever the test navigates through first) —
  mirror `ChatPage.switch_project()` / `AnalyticsPage.switch_project()`
  exactly (same testid, same shared sidebar component, `SELECT_OPTION`-style
  dynamic option template already exists elsewhere in this codebase).
- Add `delete_confirm_name_input` (testid `delete-confirm-name-input`,
  inner `#name` input) to `PipelineDetailPage` — exists on
  `AgentDetailPage` already; `PipelineDetailPage.delete_pipeline_via_menu()`
  currently uses the generic `Dialog.type_to_confirm()` helper instead,
  which still works but doesn't use a testid-scoped field. Either approach
  is fine for cleanup (both testid-anchored); prefer the explicit field for
  consistency with the Fork-specific assertions this test adds.
- Add `PipelinesListPage.forked_from_link` (collection locator, one per
  card showing a "Forked from" attribution) once the `add-data-testid` gap
  above is closed — testid TBD by the implementer's `add-data-testid` run
  (suggested: `entity-card-forked-from-link`, matching the existing
  `entity-card-name` sibling's naming convention).
- Console-error check: reuse ELITEA-1893's `soft_failures` +
  `# Known defect: #570` pattern verbatim (see
  `automation/tests/ui/agents/test_fork_agent_to_different_project.py`,
  Step 6b) — attach the console listener BEFORE clicking Fork (confirm),
  not after the dialog opens, since Playwright console listeners are
  forward-looking only.
- Wait strategy: `page.expect_response()` on the fork POST (`/elitea_core/fork/prompt_lib/{target_id}`,
  method POST) exactly like ELITEA-1893's test — don't use a fixed
  timeout for the 201.

---

## 2026-08-26 — Adjustment (issue #1800)

**Analyst:** qa-engineer (Sage), investigation slot · **Trigger:** GHA run
[32931571484](https://github.com/EliteaAI/elitea-testing-public/actions/runs/32931571484),
cell `dev-stable - pipelines` (user3, `dev.elitea.ai`) — failed 3/3 identically at Step 4
with `Locator.wait_for: Timeout 10000ms exceeded — waiting for
locator("[data-testid=\"select-option-399\"]")`.

### Verdict

**Test-data / portability defect — a test-code regression, introduced by
`e42e71536` (2026-08-25, "fix: update SOURCE_PROJECT_ID to use environment variable
for flexibility").** NOT a product bug, NOT environment drift, NOT a case-text
problem. No defect ticket filed (nothing in the product misbehaves); the fix is
entirely inside the test's two project constants.

The commit inverted the AFS's project pair. It made the **SOURCE** env-derived
(`SOURCE_PROJECT_ID = settings.elitea_project_id`) and left the **TARGET** hardcoded
to `399`, relabelling `399`'s comment as *"shared test project (fixed across
environments)"* — a factually false description. `399` is **`project_user_659`,
`owner_id: 659` — the local operator's own personal ("Private") project**, which is
exactly what `ELITEA_PROJECT_ID` already resolves to on this machine. The result:

* **on localhost** — `SOURCE == TARGET == 399`, and the product deliberately excludes
  the currently-selected project from the Fork target list, so `select-option-399`
  can never render. **The merged test is red on localhost too** (reproduced this
  session — see below), i.e. this was never a DEV-only failure.
* **on DEV as `autotest_user_3`** — `SOURCE = TEST_USER_PROJECT_3` (that user's own
  "Private" project, per `.github/workflows/test-ui-custom.yml:506`), while `399` is a
  *different user's* private project that user3 has no membership in. Doubly absent.

### Evidence

**1 — What `ELITEA_PROJECT_ID` / the three project ids actually are (product API, not
code comments).** `GET {ELITEA_API_BASE}/projects/project/default/1?check_public_role=true`
— the identical request the UI itself issues (captured live:
`GET http://localhost:5173/api/v2/projects/project/default/1?check_public_role=true => [200]`),
as the local acting user:

```
{"id": 400, "name": "UI Testing",           "owner_id": 7}
{"id": 471, "name": "Elitea Testing Team",  "owner_id": 7}
{"id":  25, "name": "Elitea Development",   "owner_id": 7}
{"id": 399, "name": "project_user_659",     "owner_id": 659}   <-- the acting user's OWN project
{"id": 406, "name": "Bugs & Features",      "owner_id": 7}
```

Resolved settings on this machine (`from config import settings`):
`elitea_project_id = 399` · `elitea_team_project_id = 471` · `users_team_project_id = 400`.

`ProjectSelect.jsx:99-104` renders the project whose id equals `user.personal_project_id`
with the literal label **"Private"** — which is why `399` shows as "Private" locally and
why the AFS (correctly) called it *"the user's own/default project"*.

**2 — Local reproduction (clean process).**

```
cd automation && HEADLESS=true ../.venv/bin/pytest \
  tests/ui/pipelines/test_pipeline_fork_to_different_project.py -v -p no:cacheprovider

tests/ui/pipelines/test_pipeline_fork_to_different_project.py:203 ->
pages/pipeline_detail_page.py:2468: in select_fork_target_project
E   playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E     - waiting for locator("[data-testid=\"select-option-399\"]") to be visible
```

Byte-identical to the DEV failure. **The test is red everywhere, not just on DEV.**

**3 — The product's own rule (source, not inference).**
`EliteaUI/src/[fsd]/entities/import-wizard/lib/hooks/useForkProjectIds.hooks.js`
(introduced `7515f444`, 2026-04-08 — long predating this test, so no product change is
involved):

```js
const excludedProjectIds = useMemo(
  () => (isForking ? [PUBLIC_PROJECT_ID, selectedProjectId] : []),
  [isForking, selectedProjectId],
);
```

consumed by `IWModalContent.jsx:105` (`filterIds={excludedProjectIds}`) →
`ProjectSelect.jsx:107` (`const excludedIds = filterIds.map(id => +id)`).
**When forking, the target dropdown = the acting user's project memberships MINUS the
public project MINUS the currently-selected (source) project.** There is no permission
or role filter beyond that.

**4 — Live walk of the Fork wizard, both directions (localhost:5173, acting user).**
Option inventory read straight off the open dropdown:

| Source project selected | `select-option-*` testids actually rendered |
|---|---|
| **399 "Private"** (what the merged test does) | `select-option-406`, `select-option-25`, `select-option-471`, `select-option-400` — **`select-option-399` ABSENT** |
| **400 "UI Testing"** (what the AFS specified) | `select-option-399` ("Private"), `select-option-406`, `select-option-25`, `select-option-471` — **`select-option-399` PRESENT** |

Control: the **sidebar** project switcher (no fork exclusion) does render
`select-option-399` "Private" alongside all five — so the option's absence in the Fork
wizard is the exclusion rule, not a missing testid or a membership problem.

![Fork target dropdown with project 399 selected — 399 absent](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2051-localhost-fork-dropdown-from-project-399.png)
![Fork target dropdown with project 400 selected — 399 present](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2051-localhost-fork-dropdown-from-project-400.png)

**5 — The DEV failure screenshot corroborates the same mechanism.**
[ELITEA-2051-step4-fork-project-selector.png](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2051-step4-fork-project-selector.png):
the sidebar reads **`Project: Private`** (so `SOURCE_PROJECT_ID` resolved to user3's own
private project, exactly as it does locally), and the open Fork dropdown offers exactly
one option — **"Elitea Automation"**. Therefore `autotest_user_3` belongs to precisely two
projects: its own private one and "Elitea Automation" — **neither `399` nor `400` nor
`471`**. Consequence for the fix: **no fixed project id can serve as the source on both
localhost and DEV.**

**6 — Regression provenance.** `git log` on the test file:

```
e42e71536 2026-08-25 fix: update SOURCE_PROJECT_ID to use environment variable for flexibility
736f6dafd 2026-08-21 test: enable all pipeline tests by replacing 'new' marker with 'new_verified'
6e1b11283 2026-08-09 test: pipelines-remaining wave-02 ... (#1343)   <-- original green delivery
```

`e42e71536` diff:

```diff
-# Source project — "UI Testing" (400): the AFS's chosen "pipeline from
-# another project", also exercised via the project switcher per case Step 1.
-SOURCE_PROJECT_ID = 400
-# Target/fork-into project — "Private" (399): the suite default project,
-# i.e. the user's own/home project (case's "user's own project").
+# Source project — user's home project from ELITEA_PROJECT_ID env var.
+# The test user's project (varies per environment).
+SOURCE_PROJECT_ID = settings.elitea_project_id
+# Target/fork-into project — shared test project (fixed across environments).
 TARGET_PROJECT_ID = 399
```

The commit is on `origin/main` and `origin/automation/base` (`git branch -r --contains
e42e71536`). CI runs `main`, which is why the nightly went red.

**7 — Contract check: which constant *should* be env-derived.** TMS case ELITEA-2051's
Test Data table says **`Target project | User's private project`**, its objective says
*"a pipeline from another project can be forked into the user's own project"*, and Step 5
asserts *"a forked copy is created in **user's own project**"*. So `ELITEA_PROJECT_ID`
(= `TEST_USER_PROJECT_<n>` in CI = the acting user's own project) is the **TARGET**, and
the source must be some *other* project the acting user can reach. `e42e71536` assigned
it to the source.

**8 — Sibling test, for shape reference.**
`tests/ui/agents/test_fork_agent_to_different_project.py:57-62` runs the INVERSE direction
of the same mechanic and is already correctly shaped for it:
`SOURCE = settings.elitea_project_id` (user's own) / `TARGET = int(settings.users_team_project_id)`.
`e42e71536` appears to have half-copied that pattern onto a case whose direction is
reversed. **Note (not verified here):** that sibling test would hit the same DEV wall from
the other side — `users_team_project_id` defaults to `"400"` and `USERS_TEAM_PROJECT_ID`
is **not** passed by `.github/workflows/test-ui-custom.yml`, so on DEV it resolves to a
project user-N is not a member of. It did not appear in run 32931571484's `agents` cell
junit, so its DEV status is unknown — flagged, not claimed.

### Fix specification (for the implementer — do not weaken any assertion)

Triage class per `adjust-automated-test` § Step 2: **D (test data / config)**. Nothing on
the **preserve-the-nature rail** moves: every assertion, every `allure.step`, every
observable and the step order stay byte-for-byte as they are. Only *which project ids the
test uses* and *how they are resolved* changes. **Expected-result changes: none.**

**F1 — Restore the case's direction, env-derived on the correct side.**
In `automation/tests/ui/pipelines/test_pipeline_fork_to_different_project.py`:

```python
# Target/fork-into project — the acting user's OWN ("Private") project, per the
# TMS case's Test Data table ("Target project | User's private project") and its
# Step 5 ("forked copy is created in user's own project"). ELITEA_PROJECT_ID is
# that project on every environment: locally 399 (`project_user_659`), and in CI
# TEST_USER_PROJECT_<n> for the suite's own autotest_user_<n>
# (.github/workflows/test-ui-custom.yml:506).
TARGET_PROJECT_ID = settings.elitea_project_id
```

`SOURCE_PROJECT_ID` becomes a **runtime-discovered fixture value**, not a module constant
— no fixed id is valid on both localhost and DEV (evidence 5).

**F2 — Add a project-list read to the API layer** (`automation/api/client.py`), mirroring
`PipelineAPI`'s constructor exactly (cookie session, Bearer fallback) so the identity
matches the browser's:

```python
class ProjectAPI:
    """Read the acting user's project memberships.

    Same endpoint the UI's own project selector uses (`src/api/project.js`) —
    GET /projects/project/default/{public_project_id}?check_public_role=true —
    verified live 2026-08-26 against localhost:5173's own network trace.
    """
    def list_projects(self) -> list[dict]: ...
```

**F3 — Add one documented config key** (`automation/config.py`), used ONLY as that URL's
path segment:

```python
# Public ("Public") project id — the path segment the projects-list endpoint takes for
# its check_public_role probe. Mirrors EliteaUI's VITE_PUBLIC_PROJECT_ID (= 1 on the
# DEV backend, confirmed live 2026-08-26 from the UI's own request). Config-driven so a
# deployed env with a different public project id needs no code change.
public_project_id: int = 1
```

No `.env.test` key and **no GHA workflow secret is required** — the default is correct on
every environment that shares the DEV backend, and CI passes nothing today.

**F4 — Source-project resolution (module-level helper or a test-local fixture; keep it in
the test file unless a second spec needs it).** Deterministic, live-verified this session
against the real API — it returns `400` locally, i.e. **byte-identical behaviour to the
pre-`e42e71536` test on localhost**:

```python
projects   = ProjectAPI(browser_cookies=_browser_cookies).list_projects()
candidates = [p for p in projects
              if int(p["id"]) not in (TARGET_PROJECT_ID, settings.public_project_id)]
preferred  = int(settings.users_team_project_id)          # 400 "UI Testing" by default
source     = next((p for p in candidates if int(p["id"]) == preferred), None) \
             or (sorted(candidates, key=lambda p: int(p["id"]))[0] if candidates else None)
```

* `preferred` keeps localhost pinned to the AFS's documented source (`UI Testing`/400) so
  the local run is unchanged; on DEV, where the user is not in 400, it falls through.
* the `sorted(...)[0]` fallback makes the pick deterministic run-to-run (no
  "whatever the API returned first").
* **no candidate ⇒ the case's own precondition ("a pipeline from a DIFFERENT project")
  cannot be met.** Spec: `pytest.fail("ELITEA-2051 precondition unmet: acting user
  <id> belongs to only one project (<id>); the case requires a second project to fork
  FROM.")` — a loud, legible red rather than a silent skip. See § Open questions.

**F5 — Docstring / comment corrections (mandatory, they are what misled `e42e71536`).**
The module docstring currently hardcodes *"project 400, 'UI Testing'"* and *"(399,
'Private', the user's own/default project)"*. Rewrite so both sides are described by
ROLE, never by a literal id:

* source — *"a project OTHER than the target, discovered at runtime from the acting
  user's own project memberships (the same list the UI's project selector renders);
  locally this resolves to `UI Testing`/400"*;
* target — *"the acting user's own ('Private') project, `ELITEA_PROJECT_ID` —
  `TEST_USER_PROJECT_<n>` in CI"*;
* and delete the false *"shared test project (fixed across environments)"* comment
  outright. **399 is not shared and is not fixed** — it is one specific user's private
  project.

Also fix the in-test `allure.step` strings that name literal ids ("Step 1 — ... in project
'UI Testing' (400)", "Step 4 — ... (399, 'Private')"): they must interpolate the resolved
ids, not assert a hardcoded environment. **This is a label change only — the assertions
inside those steps are untouched.**

**F6 — Re-verification required before the PR is raised.**

1. Merge gate per `.agents/testing.md` § Merge gate: **3 separate consecutive clean-process
   invocations** of
   `tests/ui/pipelines/test_pipeline_fork_to_different_project.py::TestPipelineForkToDifferentProject::test_pipeline_fork_to_different_project`
   on localhost. Expect the same green the original `#1343` delivery had, with the
   `#570` `validateDOMNesting` soft-failure signature if it still fires — that is the
   pre-existing sanctioned-RED condition, unrelated to this adjustment, and must NOT be
   "fixed" here.
2. Confirm from the run log that the resolved pair is **source 400 → target 399** locally
   (log both ids at Step 1 — `logger.info` already does for the source; add the target).
3. `TARGET_PROJECT_ID` is interpolated into two network assertions
   (`/elitea_core/fork/prompt_lib/{TARGET_PROJECT_ID}` 201 and
   `/elitea_core/application/prompt_lib/{TARGET_PROJECT_ID}/{id}` 204) — verify both
   still match the real traffic after the swap. They are the case's own observables and
   must keep asserting `201` / `204` exactly.
4. **DEV is only provable by a CI run.** After merge to `automation/base` and promotion to
   `main`, the next `UI Tests DEV Stable` nightly (or a `workflow_dispatch` with
   `suite: pipelines`) is the verification. See § Unverified.

### Coverage Map — unchanged

No row of Axis 1 or Axis 2 changes. The case's observables (Fork wizard shape, 201 on the
fork POST, new unique Pipeline/Version ids, Name/Description/Step-Limit equality, the
"Forked from" dashboard-card attribution, 204 on delete) are all preserved verbatim. This
adjustment changes only **which two projects** the flow runs between and **how they are
resolved** — the case's own Test Data table (`Target project | User's private project`) is
now honoured, where the merged code contradicted it.

### Unverified / open questions (for the lead)

1. **DEV as `autotest_user_3` was NOT queried directly.** `TEST_USER_PROJECT_3` and
   `TEST_USER_TOKEN_3` are GitHub Actions secrets and are not reachable from this
   machine, so user3's project list is **inferred** — from the failure screenshot's
   single-option dropdown plus the product's exclusion rule — not read from the API.
   Confidence is high (the mechanism is source-confirmed and the screenshot is
   unambiguous), but the claim *"user3 belongs to exactly two projects"* remains
   inference. **What the human may do, if certainty is wanted before the fix ships:**
   read `TEST_USER_PROJECT_3` from the repo secrets, or dispatch
   `UI Tests DEV Stable` with `suite: pipelines` after the fix and read the log.
2. **Does `autotest_user_<n>` have *create* permission in its second project?** The fixed
   test creates the source pipeline there via the API. Every DEV user is a member of
   "Elitea Automation", but whether that membership carries pipeline-create rights is
   unknown from here. If it does not, the fixed test will fail at Step 1 with a `4xx` on
   `create_pipeline` — a **different, legible** failure that names the real gap, not the
   current misleading locator timeout. This is the one residual risk in F4 and it can
   only be closed by a DEV run.
3. **`pytest.fail` vs `pytest.skip` for an unmeetable precondition (F4).** I specced a
   loud `fail` so a single-project CI user can never silently drop this case's coverage;
   the suite does have `skip`-on-missing-test-data precedent (`GIT_HUB_TOKEN`). If the
   lead prefers `skip`, that is a policy call, not a technical one — flagging rather than
   deciding.
4. **The sibling `test_fork_agent_to_different_project.py` is likely to have the mirror
   problem** (evidence 8) — `users_team_project_id` defaults to `400` and is never passed
   in CI. Not in scope for #1800 and not verified; worth its own card so the same fix
   shape lands on both fork tests at once.
