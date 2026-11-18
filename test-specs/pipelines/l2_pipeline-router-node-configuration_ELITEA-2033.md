# Test Case: Pipeline — Router Node Configuration

## Metadata
- **TMS ID**: ELITEA-2033
- **Priority**: l2
- **Environment Explored**: DEV (`https://dev.elitea.ai/app`), scripted Playwright (Python) with `.playwright-mcp/dev-storage-state.json` (MCP Chrome binary unavailable in sandbox), 2026-11-18
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer, 2026-11-18 (supersedes the 2026-08-04 localhost AFS — Pipelines 2.0 re-analysis; the old spec file was removed from main in 3fcc1478, nothing on main covers this case)
- **Status**: ready-for-automation

## Preconditions
- Authenticated on DEV. Pipeline with state var `input` and two target nodes named `approve` and `reject`.
- **CLARIFICATION (case text vs product):** `input` is a built-in state variable (the Router Input select lists exactly `input`, `messages`) — no creation needed. "Target nodes" must be created and RENAMED to `approve`/`reject`: Routes is a picklist of existing node ids (+ `END`), not a freeform tag field. Rename = panel Name input (`pipeline-node-panel-name-input`), commit on Enter/blur.

## Test Data
- generate-per-test: empty pipeline (`pipeline_id` fixture), two Printer nodes renamed `approve`, `reject`, one Router node (`Router 1`).
- Condition: `{% if 'yes' in input %}approve{% else %}reject{% endif %}`; Routes: approve, reject; Input: `input`; Default output: `END`.

## Test Steps
0. **Setup**: open pipeline; add Printer x2 ("+ Node" -> Printer) and rename to `approve`, `reject` (verify `get_node_ids()` contains both, bare names, no type prefix).
1. "+ Node" -> Router. **Verify** card `pipeline-node-card-Router 1` on canvas (node data-id `Router 1`); panel opens automatically on add.
2. Click the `Router 1` card (`open_node_panel_by_card`, force click) -> panel bound to Router 1 (`pipeline-node-panel-name-input` value `Router 1`). **Verify** visible: Condition (`pipeline-router-node-condition-input`, textarea), Routes (`pipeline-router-node-routes-select`), Default output (`pipeline-router-node-default-output-select`) in the Basic section; Input (`pipeline-router-node-input-select`) inside the collapsed-by-default **Advanced** section (toggle `pipeline-node-panel-advanced-section-toggle`, `aria-expanded`).
   - Case text says Input is a panel field; live it lives under Advanced (expand first). Not a defect.
3. Click Condition, `press_sequentially` the Jinja text. **Verify** `input_value()` equals it (plain MUI textarea, not CodeMirror).
4. Open Routes, click `select-option-approve` then `select-option-reject` (multi-select; popover stays open), Escape. **Verify** field text `approvereject`; Axis-2: canvas edges `rf__edge-xy-edge__Router 1---approve` and `...---reject` exist immediately (before Save).
5. Expand Advanced, open Input, click `select-option-input`, Escape. **Verify** field text `input`.
6. Default output: DEV shows `END` already on a fresh node (display fallback). Open it; options `select-option-approve|reject|END`; click `select-option-END`. **Verify** text `END`.
   - OBSERVED: clicking END is a no-op (value unchanged => MUI fires no onChange): no `Router 1default_output---END` edge appears before save and YAML `default_output` stays `''`. Do NOT assert pre-save default edge or YAML default_output. Assert only the displayed value `END` (case expectation "Default output is set to END").
7. Close panel, click `agent-save-button`. **Verify** no console errors; for a pipeline created through the fixture the save is `PUT .../elitea_core/application/prompt_lib/{pid}/{id}` (use `save_and_wait_for_update`; the first save of a UI-created pipeline is a `POST .../applications/prompt_lib/{pid}` 201).
8. `page.goto(canonical_url)` (reload, `?viewMode=owner`), click Router 1 card. **Verify** Condition value, Routes text `approvereject`, Default output `END`, Input (expand Advanced) `input`.
9. **Verify** canvas edges after reload: `rf__edge-xy-edge__Router 1---approve` and `---reject` present (case step 9). Observed also present after reload: `rf__edge-xy-edge__Router 1default_output---END` (no separator before `default_output`) — optional Axis-2 assertion; do not require it pre-save.

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition (input var, approve/reject nodes) | exist | step 0 | node ids | asserted — CLARIFICATION above |
| 1 add Router | card "Router 1" | step 1 | node id/card visible | asserted |
| 2 open panel, 4 controls | shown | step 2 | 4 visibility asserts | asserted (Input under Advanced) |
| 3 Condition | accepted | step 3 | input_value | asserted |
| 4 Routes approve+reject | both added | step 4 | field text + edges | asserted (picklist, not freeform) |
| 5 Input=input | set | step 5 | field text | asserted |
| 6 Default output END | END | step 6 | displayed text | asserted (see no-op observation) |
| 7 Save | no errors | step 7 | console + response | asserted |
| 8 reload restores | all 4 | step 8 | UI values | asserted |
| 9 edges to approve/reject | present | step 9 | edge testids | asserted |

Axis 2: immediate (pre-save) routes edges (step 4); zero console errors across steps (side channel).

## Known Defects
- Default output "END" click is a silent no-op on a fresh node (value equals fallback, so no onChange; YAML `default_output: ''`). Previously tracked as #1036 (that number no longer resolves in the current tracker — `gh issue view 1036` fails; lead should check for a renumbered equivalent). Consequence is benign for this case (display is END before and after reload; edge appears after reload), so no soft-assert needed unless the lead wants the pre-save edge asserted.

## Handles Reference (verified on DEV 2026-11-18)
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Condition textarea | testid | `pipeline-router-node-condition-input` | — | testid on DEV ✓ (existing `router_node_condition_input`) |
| Routes select | testid | `pipeline-router-node-routes-select` | — | testid on DEV ✓ (existing) |
| Default output select | testid | `pipeline-router-node-default-output-select` | — | testid on DEV ✓ (existing) |
| Input select | testid | `pipeline-router-node-input-select` | — | testid on DEV ✓ (existing; in Advanced) |
| Advanced toggle | testid | `pipeline-node-panel-advanced-section-toggle` | — | testid on DEV ✓ (`node_panel_advanced_toggle`) |
| Panel name input / close / save | testid | `pipeline-node-panel-name-input`, `pipeline-node-panel-close`, `agent-save-button` | — | testid on DEV ✓ |
| Options | testid | `select-option-{value}` | — | testid on DEV ✓ |
| Router card | testid | `pipeline-node-card-Router 1` | — | testid on DEV ✓ |
| Edges | testid | `rf__edge-xy-edge__{src}---{dst}` (default: `{src}default_output---{dst}`) | — | ReactFlow-injected ✓ (`edge_exists` / `get_edge_locator`) |

## Automation Hints
- Page object already has the four `router_node_*` descriptors (pipeline_detail_page.py ~1250). Missing: methods to configure Router (e.g. `configure_router_node(...)`, `expand_router_advanced_section`) — mirror the Decision methods (`expand_decision_node_advanced_section`, `select_decision_node_input_variables`, ~line 9940) and the existing Decision spec `automation/tests/ui/pipelines/test_pipeline_decision_node_configuration.py` (same Step-0 rename pattern, `edit_node_name`, `open_node_panel`).
- DEV `platform-banner-center` dialog intercepts clicks on load — close via `platform-banner-close`/corner button (existing page-object handling); use tall viewport.
- Popovers: Escape then wait for popovers closed (`_wait_for_open_popovers_closed`) between selects.
- Cleanup: `pipeline_id` fixture deletes the pipeline. Probe pipeline 4301 (id, project 575) created during analysis — delete if still present.
