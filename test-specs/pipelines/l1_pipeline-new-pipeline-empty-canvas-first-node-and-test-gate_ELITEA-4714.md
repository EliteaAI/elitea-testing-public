# Test Case: Pipeline — New Pipeline Empty Canvas, First Node and Test Pipeline Gate

## Metadata
- **TMS ID**: ELITEA-4714 (priority: critical -> l1)
- **Linked Story**: EliteaAI/elitea_issues#7154, #7155, #7156
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scripted Python Playwright probes, headless; the Playwright MCP browser was unavailable — needs a Chrome binary that is not installed). UI source cross-checked on `EliteaUI origin/main`.
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), 2026-11-18
- **Status**: ready-for-automation
- **surface_key**: pipelines-flow-editor-empty-canvas

## Preconditions
- Logged in (auth_state). Editor+ role.
- At least one agent in the project (picker listed 35 rows on DEV). Self-establish one via `agent_id` fixture and pick it **by name** — never "first row".
- Banner overlays (`platform-banner-center` dialog, then `platform-banner-corner`) can intercept clicks on DEV: close with `platform-banner-close` right after list load. The corner banner covers the panel footer at viewport height <=1000; use a tall viewport or dismiss it before clicking `pipeline-node-panel-delete`.

## Test Data
- First node: Agent (the `agent_id` fixture agent, picked by name). Task: `Say hello`. Second node: Printer.
- Created via UI (`sidebar-create-button`); the default name is "Pipeline N". **Cleanup:** the pipeline is saved in Step 3, so after the test delete it by id (read the id from the URL after save: `/pipelines/all/<id>?...`) via `pipeline_api.delete_pipeline(id)` in a finally/fixture teardown.

## Test Steps (executed live 2026-11-18; every step observed)
1. Pipelines list -> click `sidebar-create-button`. URL `/pipelines/create?viewMode=owner`; Flow view; `agent-name-input` pre-filled "Pipeline N"; `pipeline-empty-state` visible with text "Start by adding your first node to the canvas!" + `pipeline-empty-state-add-node-button` ("Add Node").
2. Hover `pipeline-test-button`. **Disabled** (`is_disabled()` True). Tooltip: "Save the pipeline to test it" (no trailing period; case text has one — soft).
3. Click `agent-save-button`; wait for URL to become `/pipelines/all/<id>`. Hover Test button: still disabled; tooltip "Add and configure at least one node connected to End." (matches).
4. Click empty-state Add Node. `pipeline-add-node-menu-item-*` count **10**, DOM order: Agent, Code, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit (each item text = label + description line; compare by the first line). Menu container testid is `pipeline-node-type-selector`.
5. Press Escape: items 0, empty-state still visible.
6. Re-open, click outside (e.g. at 60,500): items 0, empty-state still visible.
7. Re-open, click `pipeline-add-node-menu-item-agent`. Empty-state gone (count 0). Nodes on canvas: `END`, `Agent 1` (`rf__node-Agent 1`, class `react-flow__node-agent`). `pipeline-node-entrypoint-badge` count 1 (text "Entrypoint"). **No edge** (END not connected). Node panel auto-opens (`pipeline-node-panel-name-input` = "Agent 1").
8. `pipeline-node-summary` text = "Not configured" (via `pipeline-node-not-configured`). **Case-text drift:** `pipeline-node-summary-primary` does NOT exist while unconfigured; it appears only once an agent is picked.
9. Hover Test button: disabled; tooltip `Configure node "Agent 1": Select an agent` (double quotes, no trailing period; case uses single quotes + period — soft).
10. Panel `pipeline-agent-node-agent-select` -> click -> `pipeline-agent-node-agent-select-option` rows (select the target by text) -> card summary-primary shows the agent name after Save (right after the pick the summary still said "Not configured" at 2 s; panel select shows the name immediately). **Do not assert summary-primary before Save/settle; assert the panel select value, then summary-primary with a waiting `to_have_text` after the Step 12 Save.**
11. Hover Test button: disabled; tooltip `Configure node "Agent 1": Fill in the required input: task`.
12. Task field `[data-testid="pipeline-agent-node-input-mapping-value-task"]` (existing `fill_agent_node_input_mapping_value`, click + press_sequentially). Then the Test button flips to ENABLED already before Save (the config is valid in client state; tooltip empty). Click `agent-save-button`: no alert toast, 1 edge appears (`.react-flow__edge` count 1). Card `summary-primary` = agent name, `summary-secondary` = "Say hello", badge still present.
13. `pipeline-test-button` is_enabled True (hard assertion) — after Save. Also true before Save (see 12); assert after Save only.
14. Drag from `pipeline-node-add-from-output-Agent 1-source` (16x16 handle) with real mouse (down, move in steps ~+260/+300 px to empty canvas, up). `pipeline-connection-dropdown-menu` appears, text "Create new node / No other nodes created yet" (with only Agent 1 + END, the node list is empty; END is not offered); `pipeline-connection-dropdown-create` present.
15. Click `pipeline-connection-dropdown-create` -> 10 type items -> click `pipeline-add-node-menu-item-printer`. Nodes END, Agent 1, **Printer 1**; edge `rf__edge-xy-edge__Agent 1source-Printer 1`.
16. Click `rf__node-Agent 1` (force) -> panel name "Agent 1" -> `pipeline-node-panel-delete` -> confirm dialog (`[role=dialog]`: "Are you sure to delete the Agent 1 node? It can't be restored."), button `delete-confirm-button` -> Agent 1 removed; nodes END, Printer 1. Test button disabled, tooltip "Set an entry point to test the pipeline." (matches). Existing `PipelineDetailPage.delete_node(node_id)` encapsulates this.
17. Same for Printer 1 -> nodes list empty (END also vanishes from canvas), `pipeline-empty-state` visible again with the original text + Add Node button.
Side channels: console errors 0 across the run. No failing requests observed.

## Expected Results
As in the case; hard assertions: Test button disabled in steps 2–11 (and 16), enabled in 13; entry badge on first node, no edge before configuration; empty-state returns. Tooltips soft (`pytest` soft check/`expect.soft`-style that records but does not fail on wording; the **disabled state** is hard).

## Coverage Map

### Axis 1 — Case coverage
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline | canvas, name prefilled, empty card + text + button | step 1 | empty-state visible + text, name matches `Pipeline \d+` | asserted |
| 2 Test disabled + tooltip | disabled; soft tooltip | step 2 | `is_disabled`; tooltip soft | asserted |
| 3 Save, tooltip | still disabled; soft tooltip | step 3 | disabled; tooltip soft | asserted |
| 4 Node-type list | 10 types | step 4 | exact ordered list of first-line labels | asserted |
| 5 Esc | selector closes, card remains | step 5 | items 0, empty-state visible | asserted |
| 6 click outside | closes | step 6 | items 0 | asserted |
| 7 Select Agent | Agent 1 + Entrypoint, End not connected, card gone | step 7 | badge on Agent 1, edge count 0, empty-state count 0 | asserted |
| 8 summary "Not configured" | `pipeline-node-summary-primary` shows it | step 8 | `pipeline-node-summary` text (primary testid absent) | clarification — case names the wrong testid |
| 9, 11 tooltips | soft | steps 9, 11 | disabled hard, text soft | asserted |
| 10 pick agent | summary shows name | step 10 | panel select value; summary-primary after Save | asserted |
| 12 task + Save, connected to End | saved, edge | step 12 | edge count 1 | asserted |
| 13 enabled | enabled | step 13 | `to_be_enabled` | asserted |
| 14 drag from Output | dropdown w/ "+ Create new node" | step 14 | menu + create item visible | asserted |
| 15 Printer | Printer 1 connected | step 15 | node + edge present | asserted |
| 16 delete Agent 1 | removed, tooltip | step 16 | node gone, disabled, tooltip soft | asserted |
| 17 delete Printer 1 | empty-state back | step 17 | empty-state visible | asserted |

### Axis 2 — Analyst additions
- Step 7 asserts `END` exists with 0 edges — grounds the case's "End appears but NOT connected".
- Step 13: also assert disabled-state ordering (disabled at Step 11 before task fill) — the gate flip is the point of the case.

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Sidebar create | 1 | `sidebar-create-button` | — | testid on DEV ✓ (`PipelinesListPage.click_create_pipeline`) |
| Name input | 1 | `agent-name-input` | — | testid on DEV ✓ |
| Save | 1 | `agent-save-button` | — | testid on DEV ✓ |
| Empty-state card / button | 1 | `pipeline-empty-state`, `pipeline-empty-state-add-node-button` | — | testid on DEV ✓ (FlowEmptyState.jsx:40,59) |
| Test Pipeline button | 1 | `pipeline-test-button` (existing `test_pipeline_button`) | — | testid on DEV ✓. Disabled state is on the inner `<button>`; tooltip is on the wrapping `<span title="…">` and renders as `[role="tooltip"]` after hover (hover with `force=True`). Tooltip read: `role=tooltip` inner text. No testid on the tooltip — rung 2 `role=tooltip` is unique while one hover is active (declare with `suggested_testid="pipeline-test-button-tooltip"`). |
| Node-type selector | 1 | `pipeline-node-type-selector` | — | testid on DEV ✓ |
| Type items | 1 | `[data-testid^="pipeline-add-node-menu-item-"]`, `…-agent`, `…-printer` | — | testid on DEV ✓ (existing `ADD_NODE_MENU_ITEM_*`) |
| Node card / badge / summary | 1 | `rf__node-{id}`, `pipeline-node-entrypoint-badge`, `pipeline-node-summary`, `pipeline-node-summary-primary/secondary`, `pipeline-node-not-configured` | — | testid on DEV ✓ |
| Panel name / delete / close | 1 | `pipeline-node-panel-name-input`, `-delete`, `-close` | — | testid on DEV ✓ (existing fields) |
| Agent picker | 1 | `pipeline-agent-node-agent-select`, `…-option` (`AGENT_NODE_PICKER_OPTION`) | — | testid on DEV ✓; existing `open_agent_node_picker` / `pick_agent_node_application` |
| Task value | 1 | `pipeline-agent-node-input-mapping-value-{}` (`AGENT_NODE_INPUT_MAPPING_VALUE`) | — | testid on DEV ✓ |
| Output handle | 1 | `pipeline-node-add-from-output-{node}-source` | — | testid on DEV ✓ — real mouse drag; handle box 16x16 |
| Connection dropdown | 1 | `pipeline-connection-dropdown-menu`, `-create` | — | testid on DEV ✓ |
| Delete confirm | 1 | `delete-confirm-button` | — | testid on DEV ✓ (existing `delete_node`) |
| Edges | — | `.react-flow__edge` (third-party ReactFlow, terminal css rung) | — | n/a |

Reuse: `PipelineDetailPage.delete_node`, `open_agent_node_picker`, `pick_agent_node_application`, `fill_agent_node_input_mapping_value`, `add_node`, `PipelinesListPage.click_create_pipeline`. New page-object work: empty-state card/button fields, tooltip read helper, output-handle drag + connection-dropdown create helper (check for an existing edge-creation helper from ELITEA-2031 first).

## Network Behavior
Save creates the pipeline (POST applications), URL moves from `/pipelines/create` to `/pipelines/all/<id>`. Node edits are client state until Save.

## Known Defects Found During Exploration
- none.

## Case-text clarifications (soft, not defects)
- Step 8 names `pipeline-node-summary-primary`; unconfigured node renders only `pipeline-node-summary` ("Not configured"); primary appears after configuration.
- Tooltip wording differs slightly from the case: no trailing period on "Save the pipeline to test it"; `Configure node "Agent 1": …` uses double quotes and no period. (Source: pipelineReadiness.helpers.js, PipelineEditorWorkspace.jsx:17.)
- Step 13: the Test button becomes enabled once the config is valid, before Save; the case's "after Save" is still true.
- Step 14: dropdown shows "No other nodes created yet" (END not listed).
- Step 17: END node disappears from the canvas too when the last node is removed.

## Blocked Steps
- none.
