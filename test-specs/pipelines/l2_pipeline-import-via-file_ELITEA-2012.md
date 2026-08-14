# Test Case: Pipeline Import via File

## Metadata
- **TMS ID**: ELITEA-2012
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer, analyst session 2026-08-08
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard
  Keycloak login via `${TEST_USER}`).
- A project exists with access to the Pipelines feature — matches the case's stated precondition
  exactly, no drift.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline created via UI (or `PipelineAPI`) with: Name, Description, one chat starter, and an
  LLM node.

| Field | Value |
|-------|-------|
| Name | `ELITEA-2012 Import Test Pipeline` (or a unique per-run name) |
| Description | `AFS analysis pipeline for ELITEA-2012 import-via-file round trip verification.` |
| Chat starter | `What can this pipeline do?` |
| LLM node — System (Type=Fixed) | `You are a helpful assistant for import/export testing.` |
| **LLM node — Task (Type=Variable, Value=`input`)** | **MANDATORY — see Known Defects note below; a Fixed/empty Task makes execution (step 8) fail for reasons unrelated to import** |

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.
- `${ELITEA_PROJECT_ID}` (`.env.test`) — this session's live-exploration browser was on project
  "Private" (id 399), matching `.env.test`.

## Test Steps

1. Create a pipeline with name, description, one chat starter, and an LLM node (System filled,
   **Task mapped to Type=Variable/Value=`input`** — see Test Data). Save.
   - **Verify**: pipeline created — `PUT .../application/prompt_lib/{project}/{pipeline_id}`
     returns 2xx (observed live: 201); `get_pipeline_id()` returns the numeric id (observed
     live: `8230`); canvas shows the LLM node wired `LLM 1 → END`.
2. Export the pipeline via the three-dot actions menu → "Export" (VERSION section).
   - **Verify**: a file downloads. **CLARIFICATION (case-text drift, filed
     [#1334](https://github.com/EliteaAI/elitea-testing-public/issues/1334)):** the case says
     "JSON file downloads" — live product downloads a **Markdown file**
     (`<slugified-name>.pipeline.md`) containing YAML frontmatter (name/description/model/
     max_tokens/agent_type/step_limit/conversation_starters/entry_point/nodes/pipeline_settings).
     Confirmed live: `elitea-2012-import-test-pipeline.pipeline.md`, 1090 bytes, full content
     captured in this session's evidence. Assert the download fires (`page.expect_download()`),
     not a `.json` extension/MIME type.
3. Delete the original pipeline via the three-dot menu → PIPELINE section → "Delete pipeline"
   (type-to-confirm dialog).
   - **Verify**: `DELETE .../application/prompt_lib/{project}/{pipeline_id}` returns 204 (or 2xx);
     the app auto-redirects to `/pipelines/all` (confirmed live, consistent with the
     ELITEA-2022-documented redirect behavior); the pipeline no longer appears in
     `get_card_names()`.
4. Navigate to the Pipelines dashboard → click "Import".
   - **Verify**: the Import icon button is present in the dashboard toolbar (tooltip text
     "Import") and, clicked, opens a **native OS file chooser directly** (no intermediate menu)
     — confirmed live via `page.expect_file_chooser()`. **Testid needed** — see Concrete Handles.
5. Upload the exported `.pipeline.md` file via the file chooser.
   - **Verify**: the "Import parameters" preview dialog renders (`agent-import-preview-dialog`,
     shared component — existing testid, confirmed live-resolving for pipelines with zero new
     testid work) showing: Main entity name = the original name, "Type: pipeline", Description
     matching, a "Pipeline Diagram" preview (Start → LLM 1 → END), Chat starters matching, and
     "Other: Step Limit: 25" matching. Click the dialog's "Import" (confirm) button
     (`agent-import-confirm-button`, existing shared testid).
     **Implementer amendment (Phase 2 exploration, ELITEA-2012 implementation):** confirmed via
     source read (`IWModalEntityCard.jsx`/`IWModalEntityCardWrapper.jsx`) that the Type/
     Description/Chat-starters/Step-limit fields inside this shared dialog carry NO `data-testid`
     at this call site (the wrapper supports an unwired `subtitleTestId` prop; the Description/
     Chat-starters/Step-limit `Typography` nodes have no testid hook at all) — only the dialog
     itself and the Main-entity-name title (`agent-import-preview-name`) are testid-backed. Per
     this AFS's own "zero additional testid work needed" scoping and the suite's established
     pattern for this exact shared dialog (`test_import_agent_valid_md_file.py`, ELITEA-1901,
     which likewise asserts only dialog + Main-entity-name in the preview and defers full field
     verification to the post-import detail page), the implementation asserts dialog rendering +
     Main entity name here and verifies Description/Chat-starters/Step-limit/node-structure
     equivalence on the imported pipeline's detail page instead (Step 7) — via UI fields plus
     `pipeline_api.get_pipeline()` API readback for node structure, which is also the more durable
     check per this AFS's own Automation Hints. Same case requirement (config preserved), verified
     via the testid-backed, durable handle instead of untestid-able dialog-internal DOM text.
6. Verify imported pipeline has a new unique ID.
   - **Verify**: the "Import Complete" dialog (`agent-import-complete-dialog`, shared testid)
     shows "1 pipelines: <name>"; click "Got it" (`agent-import-complete-got-it-button`) navigates
     to the new pipeline's detail page; `get_pipeline_id()` returns a value **different** from the
     pre-delete id. Confirmed live: original id `8230` → imported id `8231`.
7. Verify name, description, chat starters, and node structure are preserved.
   - **Verify**: Name, Description, Chat starter text, Step limit all match the original
     (confirmed live via the General/Chat-starters accordion fields). Node structure matches:
     one LLM node (`LLM 1`) wired to `END`, System value preserved exactly
     (`You are a helpful assistant for import/export testing.`), Task Type/Value preserved.
     Recommend asserting via `pipeline_api.get_pipeline(pipeline_id)["version_details"]
     ["instructions"]` (parsed YAML) rather than re-deriving from DOM/canvas — matches this
     suite's established pattern (`test_pipeline_yaml_editor_invalid_syntax.py`) and sidesteps
     the pipeline-YAML-tab truncation gotcha (`EliteaAI/elitea-testing-public#1025`) — not hit in
     this session (19-line YAML, well under the ~32-34-line truncation threshold) but the API
     readback is the more robust default regardless of document length.
8. Verify pipeline can be executed after import.
   - **Verify**: send a chat message via the embedded chat; the run completes and produces a
     real (non-error) AI response. **Confirmed live** on the imported pipeline (id 8231) once
     the Task field was correctly mapped to `Type=Variable, Value=input` (see Known Defects
     Found During Exploration — the failure mode is a general LLM-node config requirement, NOT
     an import defect).

## Expected Results
- Export downloads a `.pipeline.md` Markdown file (not JSON — case-text drift, see step 2).
- Delete removes the original pipeline and auto-redirects to `/pipelines/all`.
- Import (via the dashboard's Import button → native file chooser → upload → preview dialog →
  confirm) creates a NEW pipeline with a unique id different from the original.
- All original configuration — name, description, chat starters, step limit, and node
  structure (LLM node, System/Task mapping, edges) — is preserved exactly.
- The imported pipeline executes successfully via chat (given a correctly-mapped Task field).
- No console errors block any step (one pre-existing, tracked, non-blocking React DOM-nesting
  warning on the "Import Complete" dialog — see Known Defects).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, project with Pipelines access | met | Preconditions | n/a (localhost auto-auth) | asserted — no drift |
| 1 Create a pipeline with name, description, chat starters and configure a LLM node | Pipeline is created with all specified fields | step 1 | step 1: `get_pipeline_id()`, PUT 2xx, canvas node wiring | asserted |
| 2 Export the pipeline via three-dot menu → Export | JSON file downloads to local machine | step 2 | step 2: `page.expect_download()` | asserted — **CLARIFICATION #1334: file is `.pipeline.md` (YAML frontmatter), not JSON; product is correct, case text is stale** |
| 3 Delete the original pipeline | Pipeline is deleted and no longer appears in the list | step 3 | step 3: DELETE 2xx/204 + `get_card_names()` no longer lists it | asserted |
| 4 Navigate to Pipelines dashboard → Import | Import option is available on the dashboard | step 4 | step 4: Import button visible, opens native file chooser | asserted — **testid needed, see Concrete Handles** |
| 5 Upload the exported file | File is uploaded successfully | step 5 | step 5: preview dialog renders with matching fields | asserted |
| 6 Verify imported pipeline has a new unique ID | Pipeline ID is different from the original | step 6 | step 6: `get_pipeline_id()` before/after comparison (8230 → 8231 observed) | asserted |
| 7 Verify name, description, chat starters, and node structure are preserved | All fields match the original pipeline's configuration | step 7 | step 7: field-by-field comparison, recommend API-readback for node structure | asserted |
| 8 Verify pipeline can be executed after import | Pipeline executes without errors | step 8 | step 8: chat message → non-error AI response | asserted — **see Known Defects: requires Task field mapped (Type=Variable/Value=input), a general LLM-node execution precondition unrelated to import, not a defect** |
| Expected Final State: new unique ID, config preserved, executable | — | steps 6–8 | steps 6–8 | asserted |
| Pass/Fail: all steps complete without errors; ID differs; config preserved; executable | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- Step 2 additionally asserts the exact downloaded filename pattern
  (`<slugified-name>.pipeline.md`) and full YAML content shape — *added: gives the implementer a
  concrete parse target for the "upload it back" step, since the case text's "JSON file" wording
  can't be used as-is.*
- Step 8 additionally documents the Task-field-mapping precondition and its failure signature
  (`Error code: 400 ... "messages.0: user messages must have non-empty content"`) — *added:
  without this, the implementer would burn a debug cycle misattributing a genuine but
  import-unrelated LLM-node config gap to the import feature itself. Reproduced and isolated
  live this session (see Known Defects).*
- No console-error assertion was in the original case text; added it throughout as a
  side-channel check. One benign, pre-existing, already-tracked React DOM-nesting warning fires
  on the "Import Complete" dialog (`EliteaAI/elitea-testing-public#570`) — noted, not asserted
  against (cosmetic-only, shared across Agent/Skill/Pipeline import, not specific to this case).
- **Not asserted (deliberately out of this case's scope):** the "Pipeline Diagram" preview
  thumbnail's own internal rendering (mermaid-like SVG inside the Import parameters dialog) —
  the case's assertions are satisfied by the preview's text fields (name/description/chat
  starters/step limit) and the post-import canvas state; the diagram thumbnail itself carries no
  case-required observable and touches no new element the implementer needs to add a testid for.

## Cleanup

1. This session's live exploration created pipeline id `8230`, exported it, deleted it, imported
   it as id `8231`, fixed its Task-field mapping, executed it via chat, then **deleted id `8231`**
   at the end of the session — no test data left behind. Confirmed via post-delete auto-redirect
   (landed on an unrelated pre-existing pipeline, `mcp_probe_redirect`, id 8227).
2. Implementer teardown: delete the pipeline created in step 1 (already removed by step 3) AND
   the imported pipeline created in step 6 — both need cleanup since step 3 only removes the
   pre-import copy.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Pipelines dashboard "Import" button | `[data-testid="pipelines-import-button"]` (NEW — see below) | **testid needed** — `ToolbarImportButton.jsx` (`src/[fsd]/entities/import-wizard/ui/ToolbarImportButton.jsx`) already accepts an optional `testId` prop (`data-testid={testId}`) and forwards it; the Pipelines call site (`src/pages/Pipelines/Pipelines.jsx:272`, `<ToolbarImportButton />`) passes NONE. The Agents call site already wires `testId="agents-import-button"` for the identical shared component (ELITEA-1795, `EliteaUI` draft PR #552) — thread the SAME mechanism with `testId="pipelines-import-button"`. Low-risk, mechanical, no new component code. Confirmed on `origin/main` AND `origin/automation/testids` (both lack the prop): `git grep "ToolbarImportButton" origin/main -- src/pages/Pipelines/Pipelines.jsx` → `<ToolbarImportButton />` (no prop). | none needed — add the testid |
| Import parameters preview dialog | `[data-testid="agent-import-preview-dialog"]` | **on-main ✓** — shared `ImportWizardModal` component (Agent/Skill/Pipeline all route through it); confirmed live-resolving for a pipeline import with ZERO pipeline-specific testid work needed. Existing `AgentsListPage.import_preview_dialog` field reusable pattern (new `PipelinesListPage`/`PipelineDetailPage` field can point at the same testid). | none needed |
| Import parameters dialog's confirm "Import" button | `[data-testid="agent-import-confirm-button"]` | **on-main ✓** — same shared component; used directly and successfully this session (`page.getByTestId('agent-import-confirm-button').click()`). | none needed |
| "Import Complete" success dialog | `[data-testid="agent-import-complete-dialog"]` | **on-main ✓** — same shared component. | none needed |
| "Import Complete" dialog's "Got it" button | `[data-testid="agent-import-complete-got-it-button"]` | **on-main ✓** — same shared component; used directly and successfully this session. | none needed |
| Actions menu (three-dot) button | `[data-testid="agent-actions-menu-button"]` | **on-main ✓** — already an `PipelineDetailPage.actions_menu_button` `LocatorDescriptor` field. | none needed |
| Actions menu "Export" item | `[data-testid="agent-actions-export-menuitem"]` | **on-main ✓ (confirmed live)** — resolves correctly, BUT the pre-existing `export_pipeline_via_menu()` method (`pipeline_detail_page.py:1812`) uses a raw `page.get_by_role("menuitem", name="Export")` instead of this testid, and does NOT capture the download (no `page.expect_download()`). **Implementer note:** add a NEW `LocatorDescriptor(testid="agent-actions-export-menuitem")` field + a new action method wrapping `page.expect_download()` — do not extend/reuse the existing raw-handle method (tracked tech debt #25/#42, not precedent). | none needed |
| Actions menu "Delete pipeline" item | `[data-testid="delete-agent-menuitem"]` | **on-main ✓** — confirmed live; NOT `delete-pipeline-menuitem` (shared `deleteApplicationMenuItem` object per the existing `_surface.md` ELITEA-2022 gotcha entry — only the visible label switches). Existing `PipelineDetailPage.delete_pipeline_via_menu()` method already implements this flow (`delete_confirm_dialog`/`delete_confirm_button` fields at lines 174-183) — reusable as-is. | none needed |
| Delete-confirm name-to-type input | `[data-testid="delete-confirm-name-input"]` (contains `#name`) | **on-main ✓** — existing pattern from `delete_pipeline_via_menu()`. | none needed |
| Delete-confirm submit button | `[data-testid="delete-confirm-button"]` | **on-main ✓** — existing `PipelineDetailPage.delete_confirm_button` field. | none needed |
| LLM node System Value | `[data-testid="pipeline-llm-node-system-value"]` | **on-main ✓** — existing `PipelineDetailPage.llm_node_system_value` field. | none needed |
| LLM node Task Type select | `[data-testid="pipeline-llm-node-task-type-select"]` | **on-main ✓** — existing `PipelineDetailPage.llm_node_task_type_select` field. | none needed |
| LLM node Task Value (Fixed textbox OR Variable combobox — same testid both states) | `[data-testid="pipeline-llm-node-task-value"]` | **on-main ✓** — existing `PipelineDetailPage.llm_node_task_value` field; confirmed via source (`LLMNode.jsx:30`, `SimpleLLMInputItem.jsx:120/132` — `dataTestId`/`data-testid={valueFieldTestId}` on both the Select and TextField render branches, same testid regardless of Type). | none needed |
| Pipeline ID display / copy button | `[data-testid="copy-id"]` | **on-main ✓** — existing `PipelineDetailPage.copy_id_button` field / `get_pipeline_id()` method, reused unmodified. | none needed |
| Chat message send button | `[data-testid="chat-send-button"]` | **on-main ✓** — confirmed live. | none needed |
| Chat message input | `[data-testid="chat-message-input"]` | **on-main ✓** — confirmed live. | none needed |
| Dynamic Select option (shared `select-option-{value}` convention) | `[data-testid="select-option-{}"]` | **on-main ✓** — established codebase-wide dynamic testid convention (`SELECT_OPTION`/`FORK_PROJECT_OPTION`/`PUBLISH_CATEGORY_OPTION` constants in `admin_users_page.py`/`agent_detail_page.py`/`analytics_page.py`); used live to select Task Type="Variable" (`select-option-variable`) and Value="input" (`select-option-input`) — no new work needed, just reuse the existing template constant pattern. | none needed |

## Network Behavior
- `POST .../elitea_core/applications/prompt_lib/{project}` — pipeline creation (step 1).
- `PUT .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — Save (step 1); returns
  201 Created (observed live).
- `DELETE .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — delete (step 3).
- Export (step 2) triggers a client-side file download — no new XHR observed beyond the page's
  already-loaded pipeline data (the export handler builds the `.md` content from in-memory
  Formik values, per `ExportApplicationButton.jsx`'s `useExportApplication` hook).
- Import (step 5) parses the uploaded file client-side (`useImport.hooks.js`'s
  `handleMarkdownFile`/`parseMdFrontmatter`) and, on confirm (step 6), fires
  `POST .../elitea_core/applications/prompt_lib/{project}` to create the new pipeline —
  confirmed live via the resulting new pipeline id (8231).
- `GET .../elitea_core/application/prompt_lib/{project}/{pipeline_id}` — fires on the imported
  pipeline's detail-page load (step 6/7); recommend using this response's
  `version_details.instructions` (parsed YAML) for step 7's node-structure assertion.

## Known Defects Found During Exploration

**Not an import defect — a general LLM-node execution precondition, isolated and confirmed live
this session:** an LLM node whose Task field is left at its default (`Type=Fixed`, empty Value)
produces `Error code: 400 - {'error': {'message': '{"message":"messages.0: user messages must
have non-empty content"}...'}}"` when a chat message is sent — the node has no source mapped
into the LLM's user-message content, so the request to the model has an empty user turn. This is
identical regardless of whether the pipeline was ever exported/imported (the SAME empty-Task
configuration existed on the pre-export original, id 8230, before it was ever touched by
export/import) — confirmed by reproducing the failure, then fixing ONLY the Task mapping
(`Type=Variable, Value=input`) on the already-imported pipeline (id 8231) without re-importing,
and observing a successful, coherent AI response on the very next message. **Classification:
test-construction requirement, not a product defect** — the AFS's Test Data / step 1 now mandates
the Task mapping so the implementer's automated test doesn't rediscover this. No ticket filed
(not a defect).

**Pre-existing, already-tracked, non-blocking:** the "Import Complete" success dialog
(`IWModalSucceedContent.jsx`, shared by Agent/Skill/Pipeline import) emits a benign React
`validateDOMNesting` console warning (`<div>` cannot appear as a descendant of `<p>`) — already
tracked as [EliteaAI/elitea-testing-public#570](https://github.com/EliteaAI/elitea-testing-public/issues/570)
(filed against Agent/Skill import); this session added a comment confirming the same warning
also fires for Pipeline import (same shared component). Cosmetic-only, not asserted against.

**Case-text drift, filed as clarification:**
[EliteaAI/elitea-testing-public#1334](https://github.com/EliteaAI/elitea-testing-public/issues/1334)
— case Step 2 says "JSON file downloads"; live product downloads a `.pipeline.md` Markdown file
(YAML frontmatter). The round trip works correctly end-to-end (Import accepts exactly what Export
produces — `.md`/`.zip`, never JSON); only the case's wording is stale.

## Blocked Steps

None. All 8 steps were executed live end-to-end against `http://localhost:5173`, including a
full create → export → delete → import → verify → execute round trip, plus an additional live
isolation pass (fixing the Task mapping) to distinguish the execution failure from an import
defect.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **One new testid needed**: `pipelines-import-button` on `ToolbarImportButton`'s Pipelines call
  site — thread the existing `testId` prop (already wired for Agents via ELITEA-1795/`EliteaUI`
  PR #552), no new component code. Everything downstream of the click (file chooser → preview
  dialog → confirm → complete dialog) reuses testids that ALREADY resolve correctly for pipelines
  with zero additional work, because Agent/Skill/Pipeline import all share one
  `ImportWizardModal` component tree.
- **File download handling**: use `with page.expect_download() as download_info:` around the
  Export menu-item click; `download_info.value.path()` gives a local path to feed straight into
  `page.expect_file_chooser()` + `file_chooser.set_files(path)` for the Import step — no
  intermediate disk-write/read needed beyond what Playwright's download API already provides.
- **File upload handling**: Import's button click opens a native OS file chooser DIRECTLY (no
  intermediate menu, unlike Export which is a three-dot-menu item) — same pattern as
  `AgentsListPage.import_agent()`; reuse `page.expect_file_chooser()` + `set_files()`.
- **Verify node structure via `pipeline_api.get_pipeline(pipeline_id)["version_details"]
  ["instructions"]`** (parsed with `yaml.safe_load`) rather than the `pipeline-yaml-editor` DOM
  tab, matching this suite's established pattern for verifying node config and sidestepping the
  YAML-tab truncation gotcha (`#1025`) — not hit by this case's short YAML, but the API readback
  is simpler and more robust regardless.
- **Task field mapping is mandatory test data**, not implementation detail — see Known Defects.
  Use `Type=Variable`, `Value=input` (selected via the shared `select-option-{}` dynamic testid
  convention: `select-option-variable` then `select-option-input`).
- Wait strategy: wait for the relevant `PUT`/`DELETE`/`POST` response before proceeding to the
  next step — not fixed timeouts. AI chat responses arrive over WebSocket ~2-10s after send; use
  a condition wait on the response text/Run-History status, not a sleep.
