# Test Case: Chat – Pipeline Flow Editor – Add LLM Node, Discard Changes, and Verify Node is Removed

## Metadata
- **TMS ID**: ELITEA-2078
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`, matches `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer / test-automation-engineer combined slot (agent) — same session analysed and implemented, per batch triage (surface already mapped: `test-specs/chat-interface/_surface.md` § "In-chat 'Create New X' canvas family — Pipeline/MCP" and § "ELITEA-2076/2077" sections applied)
- **Status**: **ready-for-automation** — all 10 case steps plus the precondition were executed live against `localhost:5173` via a live browser session before this AFS was written (pipeline id 9423, version id 9734). Every asserted value below (node-menu label set, dirty-state gating of Discard, confirm-dialog text, post-discard node count/id) is a live-confirmed observable.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- **The "test-pipeline" canvas is open with "Configuration" and "Flow Editor" tabs (following ELITEA-2077).** Automated by replicating ELITEA-2077's own steps live in this test's Setup block (ELITEA-2077 is not yet automated as a standalone spec in this batch — same "replicate precondition live" approach ELITEA-2079's AFS already used for the identical precondition): open a fixture-created conversation, `+` menu → Pipelines → "+ Create New Pipeline", fill Name "test-pipeline" / Description "A test pipeline for conversation", Save. Confirmed live: this transitions the canvas to edit mode with Configuration (active) + Flow Editor tabs, matching the case's stated precondition exactly.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment.

### generate-per-test
- **New conversation** — created via the `conversation_id` API fixture, cleaned up via `conversation_api.delete_conversation(id)`.
- **New pipeline** — Name `test-pipeline`, Description `A test pipeline for conversation` (setup replicating ELITEA-2077's precondition, not itself the case under test). Cleaned up via `pipeline_api.delete_pipeline(id)` (API), keyed off the numeric `id` returned by the create-mode Save's `201` response body — does NOT cascade-delete from conversation deletion (same rule as ELITEA-2076/2077/2079's AFS's).
- No other data — this case adds and discards an LLM node with zero further configuration (System/Task/Chat History left at defaults); the node is never persisted.

## Test Steps

1. Verify the "test-pipeline" canvas is open with "Configuration" and "Flow Editor" tabs.
   - **Verify**: `PipelineCanvasPage.title` (`pipeline-canvas-title`) == `"test-pipeline"`; `PipelineCanvasPage.subtitle` (`pipeline-canvas-subtitle`) == `"base"`; `configuration_tab` visible with `aria-selected="true"`; `flow_editor_tab` visible — confirmed live (canvas in edit mode).
2. Click on the "Flow Editor" tab.
   - **Verify**: `PipelineCanvasPage.click_flow_editor_tab()`; `PipelineDetailPage.wait_for_canvas()` resolves — ReactFlow canvas (`canvas_wrapper`, `rf__wrapper`) becomes visible, confirmed live (grid canvas background is this same ReactFlow pane's default styling, not a separately-testid'd element).
3. Verify "Flow" and "Yaml" sub-tabs appear; "Flow" tab is active; only "End" node is visible.
   - **Verify**: `flow_view_button` visible; `yaml_view_button` visible; `is_flow_view_active()` == `True`; `get_node_count()` == `1`; `get_node_ids()` == `["END"]` — confirmed live immediately after the Flow Editor tab opens on a freshly-created pipeline (identical starting state to ELITEA-2079's own Step 1, same underlying `EditorPanel`).
4. Click the "+ Add node" button in the top right.
   - **Verify**: `get_add_node_menu_items()` — opens the menu (clicking `add_node_button`, `pipeline-add-node-button`) and leaves it open, returning the rendered labels for step 5's assertion.
5. Verify the menu shows node types including: Agent, MCP, Code, Printer, Custom, Router, Decision, State modifier, Human-in-the-loop, Toolkit, LLM.
   - **Verify**: `set(get_add_node_menu_items())` == the case's own 11-item set — confirmed live, exact match (menu renders these 11 labels alphabetically: Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit; source-traced to `AddNodeMenu.jsx`'s `getVisibleNodeTypes()` filtering out the deprecated/invisible types — Tool, Function, Pipeline, Condition, Loop, LoopFromTool, End, Ghost, Default). No case-text drift — the product's visible set matches the case's list exactly.
6. Click on "LLM" from the menu.
   - **Verify**: `select_add_node_menu_item("llm")` (internal type key, per `ADD_NODE_MENU_ITEM_BY_TYPE`) — clicks the already-open menu's LLM item.
7. Verify the LLM node appears with icon, label, and connection ports.
   - **Verify**: `wait_for_node_on_canvas("LLM")` resolves a node id starting with `"LLM"` (confirmed live: `"LLM 1"`); `get_node_count()` == `2`; the node's `rf__node-LLM*` testid (ReactFlow-injected, sanctioned #579 exception, scoped under `canvas_wrapper`) is visible — confirmed live: the node renders with its own header (label + two icon-header buttons) and a "Trigger" input-mapping field, i.e. visible and selectable/configurable, matching the case's Expected Result column ("LLM node is visible and selectable").
8. Click the "Discard" button without saving.
   - **Verify**: `PipelineCanvasPage.is_discard_enabled()` == `True` BEFORE the click (confirmed live: the canvas header's Discard/Save buttons are disabled immediately after Step 3's fresh-canvas state, and become enabled only once the LLM node is added — `PipelineEditor.jsx`'s `totalDirty = isDirty || isYamlDirty`, with `isYamlDirty` driven by `EditorPanel`'s `useIsPipelineYamlCodeDirty()`); `click_discard()` opens `discard_confirm_modal`, confirmed live to contain the text `"Are you sure you want to discard changes?"`.
9. Click "Discard" or "Yes" to confirm.
   - **Verify**: `confirm_discard()` clicks the modal's own Discard button (`pipeline-canvas-discard-confirm-button`) and waits for the modal to detach — confirmed live: resolves cleanly, zero `POST`/`PUT` network calls fire (Discard is a purely client-side Redux `resetPipeline()`/`resetPipelineEditor()`, same "no network call" finding ELITEA-2076's AFS already documented for the header-form Discard, now confirmed to extend to a Flow-graph addition too).
10. Verify only the "End" node remains on the canvas.
    - **Verify**: `get_node_count()` == `1`; `get_node_ids()` == `["END"]` — confirmed live: identical to the Step 3 starting state. Additionally, `is_discard_enabled()` == `False` again (form no longer dirty), corroborating "reverted to last saved state" from the case's Expected Final State.

## Expected Results
All 10 steps pass cleanly as specced above. Zero product defects found — this flow behaves exactly as the case describes, confirmed by live execution of every step (plus the precondition) against `http://localhost:5173` this session (pipeline id 9423, version id 9734).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: "test-pipeline" canvas open with Configuration/Flow Editor tabs (following ELITEA-2077) | — | Setup | live replication of ELITEA-2077's create+save flow | asserted |
| 1 Verify canvas open with Configuration/Flow Editor tabs → Canvas is in edit mode | canvas in edit mode | step 1 | title/subtitle text + tab visibility/`aria-selected` | asserted |
| 2 Click Flow Editor tab → Flow Editor opens with grid canvas background | flow editor initialized | step 2 | `canvas_wrapper` visible via `wait_for_canvas()` | asserted |
| 3 Verify Flow/Yaml sub-tabs appear, Flow active, only End node visible → Flow editor initialized correctly | sub-tabs + active state + node count correct | step 3 | `flow_view_button`/`yaml_view_button` visible + `is_flow_view_active()` + `get_node_count()`/`get_node_ids()` | asserted |
| 4 Click "+ Add node" → Node type selector menu opens | menu opens | step 4 | `get_add_node_menu_items()` opens menu | asserted |
| 5 Verify menu shows Agent/MCP/Code/Printer/Custom/Router/Decision/State modifier/Human-in-the-loop/Toolkit/LLM → All node types listed | menu item set correct | step 5 | `set(get_add_node_menu_items())` equality | asserted |
| 6 Click "LLM" → LLM node added to canvas | node added | step 6 | `select_add_node_menu_item("llm")` | asserted |
| 7 Verify LLM node appears with icon, label, connection ports → LLM node visible and selectable | node visible | step 7 | `wait_for_node_on_canvas("LLM")` + `get_node_count()==2` + testid-scoped node visible | asserted |
| 8 Click Discard without saving → Confirmation dialog appears | dialog appears | step 8 | `is_discard_enabled()` before + `click_discard()` + modal text | asserted |
| 9 Click Discard/Yes to confirm → Canvas updates; LLM node removed | node removed | step 9 | `confirm_discard()` resolves; no network call | asserted |
| 10 Verify only End node remains → Canvas reverted to last saved state | only End node remains | step 10 | `get_node_count()==1` + `get_node_ids()==["END"]` + `is_discard_enabled()==False` | asserted |
| Expected Final State: "LLM node removed after discarding; only End node remains, matching last saved state" | — | step 10 | — | asserted |
| Pass/Fail: "Any step produces an error or unexpected result... LLM node persists after discarding, or canvas does not revert" | — | all steps | side-channel console/network checks throughout + step 10's node-count/id assertions | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 5's node-type set is asserted as an exact `set()` equality (not merely "includes each") — *added: the case's own wording is "including", but the live product renders EXACTLY these 11 types (source-traced to `AddNodeMenu.jsx`'s `getVisibleNodeTypes()`); asserting the exact set is a stronger, still-honest check (catches a type silently added or removed) and matches the case's own enumerated list one-for-one, so there's no reverse-masking risk — the live set and the case's list are identical.*
- Step 8 adds a pre-click assertion that `is_discard_enabled()` is `False` immediately after Step 3 (fresh canvas) and only becomes `True` once the LLM node is added — *added: confirms the case's own implicit assumption that Discard is meaningfully gated on unsaved changes (not simply always-clickable), and is directly load-bearing for why the confirmation dialog in step 8 is a genuine confirm-before-discard step rather than a no-op — same reasoning ELITEA-2076's AFS already documented for the header-form Discard, now confirmed to extend to Flow-graph dirty state via `PipelineEditor.jsx`'s `isYamlDirty`.*
- Step 9's "zero network call" observation is asserted as a side-channel check (network capture shows no `POST`/`PUT` between the Add-node click and the post-discard state) — *added: Discard reverting via a real network round-trip (re-fetching last-saved state) vs. a purely client-side Redux reset are both consistent with the case's stated behavior, but only the live network trace disambiguates which; confirms this is a genuine client-side revert with no residual server-side draft.*
- Step 10 adds `is_discard_enabled()==False` as corroborating evidence for "reverted to last saved state" — *added: the case's stated pass criterion is the node count/id, which the primary assertion already covers; the dirty-flag reset is additional evidence the form itself agrees nothing is pending, not a substitute for the node-count check.*
- Console/network side-channel checked throughout (the `secrets/secrets/default` 403 noise filter, same idiom as ELITEA-2076/2077/2079) — confirmed clean across the whole live session's own actions (zero unexpected console errors, zero unexpected failed 4xx/5xx requests tied to this flow's own actions).

## Cleanup
1. Delete the created pipeline via `pipeline_api.delete_pipeline(id)` (API, keyed off the `id` from Setup's create-mode `201` response).
2. Delete the created conversation via `conversation_api.delete_conversation(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main` / `origin/automation/testids`; all handles below are **pre-existing** (ELITEA-2030/2076/2077/2079's own implementations) — this case adds **zero new testids**.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Canvas header title (post-save) | `pipeline-canvas-title` | on-`automation/testids` (ELITEA-2076) | Existing `PipelineCanvasPage.title`. |
| Canvas header subtitle/version tag | `pipeline-canvas-subtitle` | on-`automation/testids` (ELITEA-2077) | Existing `PipelineCanvasPage.subtitle`. |
| Post-save tab bar | `pipeline-canvas-tab-configuration` / `pipeline-canvas-tab-flow` | on-main ✓ | Existing `PipelineCanvasPage.configuration_tab` / `flow_editor_tab`. |
| Flow/Yaml view toggle | `pipeline-flow-view` / `pipeline-yaml-view` | on-main ✓ | Existing `PipelineDetailPage.flow_view_button` / `yaml_view_button`. |
| ReactFlow canvas wrapper | `rf__wrapper` | on-main ✓ (#579 sanctioned, ReactFlow-injected) | Existing `PipelineDetailPage.canvas_wrapper`. |
| Add-node trigger | `pipeline-add-node-button` | on-main ✓ (ELITEA-2030) | Existing `PipelineDetailPage.add_node_button`. |
| Add-node menu | `pipeline-add-node-menu` | on-main ✓ (ELITEA-2030) | Existing `PipelineDetailPage.add_node_menu`. |
| Add-node menu items (per internal type) | `pipeline-add-node-menu-item-{type}` | on-main ✓ (ELITEA-2030) | Existing `ADD_NODE_MENU_ITEM_BY_TYPE` template constant; `select_add_node_menu_item("llm")` formats it. Confirmed live: 11 items rendered (`agent`, `code`, `custom`, `decision`, `hitl`, `llm`, `mcp`, `printer`, `router`, `state_modifier`, `toolkit`). |
| Added LLM node | `rf__node-LLM {n}` (prefix match) | on-main ✓ (#579 sanctioned, ReactFlow-injected) | `RF_NODE_TESTID_PREFIX`, scoped under `canvas_wrapper`. Confirmed live: node id `"LLM 1"`. |
| Canvas header Discard button | `pipeline-canvas-discard-button` | on-`automation/testids` (ELITEA-2076) | Existing `PipelineCanvasPage.discard_button` / `is_discard_enabled()` / `click_discard()`. Confirmed live: disabled pre-add, enabled post-add. |
| Discard confirmation modal | `pipeline-canvas-discard-confirm-modal` | on-`automation/testids` (ELITEA-2076) | Existing `PipelineCanvasPage.discard_confirm_modal`. Confirmed live text: `"Are you sure you want to discard changes?"`. |
| Discard confirm button (in modal) | `pipeline-canvas-discard-confirm-button` | on-`automation/testids` (ELITEA-2076) | Existing `PipelineCanvasPage.discard_confirm_button` / `confirm_discard()`. |

## Network Behavior
- `POST /api/v2/elitea_core/applications/prompt_lib/399` → `201 Created` on the Setup's create-mode Save; response body `{"id": 9423, ...}` (confirmed live this session).
- `GET .../version/prompt_lib/399/{id}/{version_id}`, `GET .../version_validator/prompt_lib/399/{id}/{version_id}`, `GET .../application_skills/prompt_lib/399/{version_id}`, `GET .../application/prompt_lib/399/{id}`, `GET .../pipeline_trigger/prompt_lib/399/pipeline/{version_id}/trigger` → `200 OK`, fired hydrating the post-save edit-mode canvas (Setup + Steps 1-2).
- **Zero `POST`/`PUT` requests fire between adding the LLM node (step 6) and the post-discard state (step 10)** — confirmed live via network capture: Discard is a purely client-side Redux reset (`resetPipeline()`/`resetPipelineEditor()`), no server round-trip.
- No 4xx/5xx observed at any point in this session's live execution of this case's own steps.

## Known Defects Found During Exploration
None. This flow behaves exactly as the case describes — confirmed by live execution.

## Blocked Steps
None. All 10 case steps plus the precondition were executed and observed end-to-end live this session (pipeline id 9423, version id 9734).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: compose `ChatPage` (canvas entry point) + `PipelineCanvasPage` (canvas chrome: title/subtitle/tabs/discard) + `PipelineDetailPage` (Flow Editor: add-node menu, node count/ids, view toggle) on the SAME `page` — identical composition pattern to `test_pipeline_discard_changes_clears_canvas.py` (ELITEA-2076), `test_pipeline_create_save_basic_configuration.py` (ELITEA-2077), and `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py` (ELITEA-2079). Zero new page-object work needed — every method/testid this case touches already exists.
- **Prefer the testid-based Add Node menu methods over the legacy `add_node()`**: `add_node()` (pre-ELITEA-2030) still chains a raw `button.MuiIconButton-colorPrimary` CSS handle + `get_by_role("menuitem", name=...)` — kept for its existing caller (ELITEA-2079) but NOT the compliant shape for new code. Use `get_add_node_menu_items()` (opens + returns the label list, satisfying this case's own step 4+5 in one call) and `select_add_node_menu_item("llm")` (testid-based, keyed by the INTERNAL type — `"llm"`, not `"LLM"`) instead.
- Wait strategy: no fixed sleeps — `wait_for_node_on_canvas()` / `wait_for_canvas()` / `discard_confirm_modal.wait_for(state=...)` poll for real conditions, matching every sibling spec on this surface.
- No product defect found in this flow — a plain-additive spec, no soft-assert/known-defect handling needed.
