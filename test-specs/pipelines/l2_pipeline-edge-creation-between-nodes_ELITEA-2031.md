# Test Case: Pipeline — Edge Creation Between Nodes

## Metadata
- **TMS ID**: ELITEA-2031
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: N/A on localhost — `VITE_DEV_TOKEN` auto-auths, no login/credentials needed (`${TEST_USER}` only relevant on deployed envs)
- **Analyst**: qa-engineer (agent), session 2026-07-24 (browser lane: isolated `browser-verify` CDP instance, port 9223 — NOT the shared Playwright MCP)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed envs: standard Keycloak login via `${TEST_USER}`).
- A pipeline exists with at least 2 nodes: an `LLM` node and a `Printer` node, both initially transitioning to `END`.
- **Active project must be one the dev-token identity can create/delete applications in** (`Private`/`399` or `UI Testing`/`400` — confirmed full-CRUD; `Elitea Testing Team`/`471` lacks `models.applications.applications.create` and 403s — see `.agents/memory/qa-engineer/fork_agent_flow_and_localhost_dev_token_permission_scoping.md`). The existing `pipeline_id`/`pipeline_with_llm_id` fixtures already create in the configured `${ELITEA_PROJECT_ID}` (`399`, "Private") — no change needed if reusing them, but a raw scratch script (as used during this analysis) must explicitly pick 399/400.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline (`autotest_<test-name>`) with exactly 2 nodes, both transitioning to `END`: `LLM 1` (type `llm`) + `Printer 1` (type `printer`). Created via the **existing** `PipelineAPI.create_pipeline_with_nodes(name, description, entry_point="LLM 1", nodes=[...])` (`automation/api/client.py:759-815`) — no new API-client method needed. Teardown: `PipelineAPI.delete_pipeline(pid)`.

  ```python
  nodes = [
      {
          "id": "LLM 1", "type": "llm", "input": [],
          "input_mapping": {
              "chat_history": {"type": "fixed", "value": []},
              "system": {"type": "fixed", "value": ""},
              "task": {"type": "fixed", "value": ""},
          },
          "output": [], "structured_output": False,
          "transition": "END",
      },
      {
          "id": "Printer 1", "type": "printer", "input": [], "output": [],
          "final_message": "",
          "transition": "END",
      },
  ]
  ```
  Confirmed live this session (pipeline id `5771`, project `399`/"Private", deleted after analysis): this payload renders exactly `LLM 1` + `Printer 1` on the canvas, both showing an edge to `END` initially (`rf__edge-xy-edge__LLM 1---EliteAPipelineEnd`, `rf__edge-xy-edge__Printer 1---EliteAPipelineEnd`).

### reuse-existing
- `${ELITEA_PROJECT_ID}` (`.env.test`, `399`/"Private").

## Test Steps

1. Navigate to the fixture pipeline's detail page (`PipelineDetailPage.navigate(pipeline_id)`, existing method — includes `?viewMode=owner`), zoom/fit the canvas (existing `zoom_in()`/`fit_view()` methods — canvas is heavily zoomed-out by default per `_surface.md`).
   - **Verify**: `get_node_count()` returns `3` (LLM 1 + Printer 1 + the `END` node — implementer-exploration correction, see Concrete Handles: `get_node_count()` counts every `.react-flow__node` element, and END renders as one of them; confirmed live via `get_node_ids()` returning `['END', 'LLM 1', 'Printer 1']`, and matches the established precedent in `test_save_multi_node_pipeline`, a merged sibling test, where 1 custom node + END == 2 nodes).
   - **Verify**: `edge_exists("LLM 1", "END")` is `True` and `edge_exists("Printer 1", "END")` is `True` (both via the `"EliteAPipelineEnd"` aliasing form — see Concrete Handles) — establishes the pre-edit baseline so Step 4's "new edge, old edge gone" comparison is meaningful.
2. **Case-text drift (see Known Defects / Clarification below): there is no "transition/routes field" in the LLM node's configuration panel** for this node type. Confirmed both by source (`LLMNode.jsx` renders only SYSTEM/TASK/CHAT HISTORY/Input/Output/Toolkits/Interrupt-before/after/Structured-output — no Transition/Route field) and by live DOM enumeration of a freshly-added LLM node's panel (zero Transition/Route field anywhere). A visible "Route"/"Routes" **select** field genuinely exists in the product, but only on **HITL** and **Router** node types (`RouteSelect.jsx`) — not on ordinary flow-through node types like LLM/Printer. **Automate the real mechanism instead**: drag a canvas connection from the LLM node's own bottom/source handle to the Printer node's top/target handle (existing `connect_nodes("LLM 1", "Printer 1")` method, no `source_handle` needed since LLM has only one source handle) — this is the live, correct, working way to set an ordinary node's transition target, and is exactly what "Set the transition of the LLM node to point to the Printer node" cashes out to for this node type.
   - **Verify (added)**: no explicit UI assertion for this step beyond the connect action itself — this step exists to document why Step 3 uses `connect_nodes()` rather than a form-field interaction.
3. Perform the connection: `pipelines.connect_nodes("LLM 1", "Printer 1")`.
   - **Verify**: `edge_exists("LLM 1", "Printer 1")` is `True` immediately after the drag (client-side, no network wait needed — matches ELITEA-2028's confirmed finding that node-graph edits are synchronous client-side state until the pipeline's own Save is clicked).
   - **Verify (added)**: switch to Yaml view (`switch_to_yaml_view()`) and confirm `get_yaml_content()` shows `LLM 1`'s node block ending `transition: Printer 1` — the underlying data-model proof that the drag correctly updated the node's `transition`, not merely a visual line. Switch back (`switch_to_flow_view()`) before continuing.
4. Verify the edge line appears on canvas connecting LLM Output to Printer Input, and that the OLD `LLM 1 → END` edge is gone (not merely superseded by an additional one).
   - **Verify**: `edge_exists("LLM 1", "Printer 1")` is `True` (existing method — matches live, confirmed testid `rf__edge-xy-edge__LLM 1source-Printer 1target` immediately after the drag, a **different id shape** than the eventual post-reload YAML-derived form — see Concrete Handles).
   - **Verify (added)**: `edge_exists("LLM 1", "END")` is `False` (via the `"EliteAPipelineEnd"` aliasing form) — confirms the drag replaced the node's transition target rather than adding a second one.
   - **Verify (added)**: `edge_exists("Printer 1", "END")` is still `True` — confirms the edit was scoped to only the `LLM 1` node, `Printer 1`'s own untouched edge is unaffected.
5. Save and reload — verify the edge persists.
   - **Verify**: `is_save_enabled()` is `True` before clicking Save (content edit occurred).
   - **Verify**: `save_and_wait_for_update(project_id, pipeline_id)` — waits on the real `PUT .../application/prompt_lib/{project_id}/{pipeline_id}` → `201` response (existing method, network-verified, not a fixed timeout).
   - **Verify**: after a hard reload (`page.reload()` + `wait_for_canvas()`), `edge_exists("LLM 1", "Printer 1")` is `True` — note the persisted edge now carries the **YAML-derived triple-dash testid shape** (`rf__edge-xy-edge__LLM 1---Printer 1`), not the drag-time shape from Step 4 — `edge_exists()`'s own substring matching already handles this transparently (see Concrete Handles), no test-code change needed.
   - **Verify (added)**: `edge_exists("Printer 1", "END")` is still `True` post-reload — the untouched edge survived the reload too.
   - **Verify (added)**: `is_save_enabled()` is `False` immediately after reload — dirty-state correctly cleared once persisted.
6. **Verify (added, standard side-channel discipline)**: zero `error`-level console messages across the whole flow (confirmed clean live this session — filter to `level == "error"`; the ambient `warning`-level ReactFlow `nodeTypes/edgeTypes` ambient message, if present, is unrelated per `_surface.md`).

## Expected Results
- An LLM node's transition target is set by dragging a canvas connection to another node (there is no in-panel "transition/routes" field for this node type — that only exists for HITL/Router nodes).
- The drag immediately updates both the canvas edge and the underlying YAML `transition:` value, client-side, with no network call.
- The new edge (`LLM 1 → Printer 1`) appears and the old edge (`LLM 1 → END`) disappears — not merely superseded by an additional edge.
- The untouched node's own edge (`Printer 1 → END`) is unaffected throughout.
- Save flips from disabled to enabled because of the edit; clicking Save persists it via a `201` PUT.
- After a hard reload, the edge is still present (now under the YAML-derived edge-testid shape) and Save reads disabled again (clean state).
- No console errors at any step.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: pipeline with ≥2 nodes (LLM + Printer) exists | pipeline available for the test | Test Data (fixture) | step 1: `get_node_count() == 2`, both baseline edges present | asserted |
| 1 Open pipeline with 2 nodes | canvas displayed with both nodes | step 1 | `get_node_count()`, baseline `edge_exists()` checks | asserted |
| 2 Locate transition/routes field in LLM node panel | field visible | step 2 | **case-text drift — no such field exists for this node type; documented + re-sequenced to the real mechanism** | *clarification (see Known Defects)* |
| 3 Set the transition of LLM node to Printer | transition updated to target Printer | step 3 | `connect_nodes()` + YAML-view `transition: Printer 1` re-read | asserted *(via the real mechanism, not a field)* |
| 4 Verify edge line appears connecting LLM Output to Printer Input | edge drawn on canvas | step 4 | `edge_exists("LLM 1", "Printer 1")` True | asserted *(enriched — see Axis 2)* |
| 5 Save and reload — verify edge persists | edge present after reload | step 5 | `save_and_wait_for_update()` (201) + post-reload `edge_exists()` | asserted |
| Expected Final State: edge connecting LLM to Printer visible and persists after save/reload | — | steps 3–5 | as above | asserted |
| Pass/Fail: all steps complete without errors; edge appears and persists | — | all steps | steps above + step 6 console check | asserted |

### Axis 2 — Analyst additions

- **Baseline check that both nodes start wired to `END`** (step 1) — *added: without this, "the new edge appears" isn't contrasted against a known starting state, and a regression that left a stray pre-existing `LLM 1 → Printer 1` edge (e.g. from stale fixture reuse) would go undetected.*
- **Assert the underlying YAML `transition:` value, not just the visual edge** (step 3) — *added: the case's step 3 says "transition field is updated," which is a data-model claim; reading only the canvas edge would leave open whether the drag genuinely changed `transition` vs. some other client-side-only visual state.*
- **Assert the STALE edge is gone, not just that the new edge exists** (step 4) — *added: same rationale as ELITEA-2028's identical enrichment — a buggy implementation that ADDS an edge without removing the old one would still satisfy the case's literal step-4 wording.*
- **Assert the untouched node's own edge is unaffected** (steps 4 and 5) — *added: confirms the edit is scoped to the one node/edge touched, not a side-effect of a wholesale re-layout, and that this holds across the reload too.*
- **Save/reload dirty-state checks (`is_save_enabled()` before Save, `False` after reload)** — *added: cheap, same mechanism the sibling ELITEA-2028 case already established, confirms the "no edit" case doesn't false-negative pass.*
- **Zero console errors** (step 6) — *added: standard side-channel discipline; confirmed clean live.*

## Cleanup
1. This session created one throwaway pipeline directly via `PipelineAPI` (id `5771`, project `399`/"Private") to confirm the live behavior described above — **deleted by this analyst session** (`PipelineAPI.delete_pipeline`).
2. Implementer teardown: the fixture's own `PipelineAPI.delete_pipeline(pid)` teardown — no manual cleanup needed in the test body.

## Concrete Handles (discovered during exploration)

Provenance verified this session via `cd ../EliteaUI && git fetch origin` immediately before checking (`.agents/role-overrides.md` § Analyst slot). All handles below are **pre-existing, already-merged page-object methods** — this case needs **zero new testids and zero new page-object code**, only a new test using the existing API.

| Element | Recommended Locator / Method | Provenance | Notes |
|---|---|---|---|
| Canvas wrapper | existing `PipelineDetailPage` implicit via `wait_for_canvas()` (testid `rf__wrapper`) | **on-main ✓** — `@xyflow/react` library-owned | Reused as-is |
| Node count | existing `PipelineDetailPage.get_node_count()` | **on-main ✓** | Reused as-is; **implementer-exploration correction**: counts `LLM 1` + `Printer 1` + `END` = `3`, not `2` — `get_node_count()` counts every `.react-flow__node` in the DOM (`END` included), confirmed live via `get_node_ids()` == `['END', 'LLM 1', 'Printer 1']` on this exact fixture. Matches the merged `test_save_multi_node_pipeline` precedent (1 custom node + END == 2 nodes) |
| Connect gesture | existing `PipelineDetailPage.connect_nodes(source_id, target_id, source_handle=None)` (`pipeline_detail_page.py:1198`) | **on-main ✓** — pure Playwright mouse choreography, no app testid needed beyond the node/handle attributes it already scopes into (`[data-id="…"]`, `[data-handlepos="…"]`) | Reused as-is — same method the merged `test_add_human_in_the_loop_node_and_connect_to_end` already uses for HITL→END; here called with no `source_handle` since LLM has a single, unambiguous source handle |
| Edge existence (drag-time shape) | existing `PipelineDetailPage.edge_exists("LLM 1", "Printer 1")` | **on-main ✓** — library-owned (`@xyflow/react`) | Confirmed live testid immediately after drag: `rf__edge-xy-edge__LLM 1source-Printer 1target` (user-dragged shape, per the existing docstring's `{source}{handle}-{target}{handle}` format) |
| Edge existence (post-reload/YAML-derived shape) | same `edge_exists("LLM 1", "Printer 1")` call — **no code change needed** | **on-main ✓** | Confirmed live: after Save + reload, the SAME edge now carries testid `rf__edge-xy-edge__LLM 1---Printer 1` (triple-dash, no handle suffix — YAML/transition-derived shape per the ELITEA-2018 digest finding). `edge_exists()`'s `testid.startswith(expected_prefix) and f"-{target_id}" in testid` matching already covers both shapes transparently — verified live, no method change required. |
| Old edge must be gone (LLM 1 → END) | `edge_exists("LLM 1", "END")` **and** `edge_exists("LLM 1", "EliteAPipelineEnd")` | N/A (ReactFlow-owned) | Per the ELITEA-2018 digest, the END node's edge-endpoint id is the literal `EliteAPipelineEnd`, NOT `"END"` — `edge_exists(x, "END")` is a **false negative** for a YAML-derived END edge. Check the `"EliteAPipelineEnd"` form to get a real answer. |
| Untouched edge (Printer 1 → END) | `edge_exists("Printer 1", "EliteAPipelineEnd")` | N/A (ReactFlow-owned) | Same aliasing caveat as above |
| Yaml view toggle / editor | existing `PipelineDetailPage.switch_to_yaml_view()` / `switch_to_flow_view()` / `is_yaml_view_active()` / `get_yaml_content()` (testids `pipeline-yaml-view`/`pipeline-flow-view`/`pipeline-yaml-editor`) | **on-main ✓** — the view-toggle testids are runtime-templated (`GroupedButton.jsx:57`, false negative under literal `git grep`, confirmed by source + live match per the ELITEA-2028 AFS) | Reused as-is; only used for the added Step-3 data-model verification, no editing needed for this case (unlike ELITEA-2028, which edits the YAML directly — this case edits via canvas drag only) |
| Save button / state | existing `PipelineFormPage.save_button` (testid `agent-save-button`) / `is_save_enabled()` / `save_and_wait_for_update(project_id, pipeline_id)` | **on-main ✓** — shared with agent forms, used by multiple already-merged pipeline + agent tests | `save_and_wait_for_update()` waits on the real `201` PUT response, not a fixed timeout — reused as-is from the merged ELITEA-1954 spec |

## Network Behavior
- The canvas drag-connect (Step 3) is **100% client-side** — no request fires (confirmed live via network capture during the drag; matches ELITEA-2028's identical finding for node-graph edits in general). Only the pipeline's own **Save** click persists it (`PUT /elitea_core/application/prompt_lib/{project}/{pipeline_id}` → `201`), which `save_and_wait_for_update()` already waits on directly.

## Known Defects Found During Exploration

**No product defect.** The edge-creation-and-persistence FEATURE itself works correctly end-to-end (drag → client-side edge + YAML update → Save → 201 → reload → edge persists → old edge correctly replaced, not duplicated → untouched edge unaffected → zero console errors).

**Case-text clarification filed:** `EliteaAI/elitea-testing-public#1031` — the case's steps 2-3 describe "a transition/routes field... visible in the LLM node panel," which does not exist for LLM (or Printer) node types; that field genuinely exists in the product but only for HITL/Router nodes (`RouteSelect.jsx`). The real, correct mechanism for LLM/Printer-family nodes is the canvas drag-connect gesture (or direct YAML editing, per the sibling `ELITEA-2028` case) — both produce the identical `transition:`-value observable the case actually cares about. Classified per the reverse-masking guard (`.agents/testing.md`): `ready-for-automation`, asserting the live/correct mechanism, not a defect against the product.

## Blocked Steps

None. All case steps were executed to completion against the live local environment (pipeline id `5771`, project `399`, deleted after analysis).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`). **No `add-data-testid` pass needed for this case** — every element/method it touches already exists and is already on `main`.
- Suggested location: `automation/tests/ui/pipelines/test_pipeline_nodes.py` (same file as the merged `test_add_human_in_the_loop_node_and_connect_to_end` — both are "connect two nodes via canvas drag" tests, natural sibling coverage) — **or** `automation/tests/ui/pipelines/test_pipeline_advanced.py` alongside the ELITEA-2028 YAML-edit-transition test once that one is implemented (same underlying `transition:` mechanism, complementary UI entry points: drag vs. YAML edit). Either location is acceptable; prefer `test_pipeline_nodes.py` since it already hosts the sibling `connect_nodes()`-based test and this case needs no YAML-editing helper.
- **Merged-target dedup check performed:** `test_add_human_in_the_loop_node_and_connect_to_end` (merged, `test_pipeline_nodes.py`) is the only existing spec that uses `connect_nodes()` — but it connects **HITL → END** (not LLM → Printer), and only asserts `edge_exists()` once, in-memory, immediately after the drag (no Save click, no reload, no old-edge-gone check, no YAML data-model check). It does not cover an ordinary-node-to-ordinary-node connection nor persistence-after-save-and-reload. The other close sibling, `ELITEA-2028`'s AFS ("YAML edit syncs transition to Flow view"), is **not yet implemented** (status `ready-for-automation`, no test code on `automation/base`) — per the merged-target rule, an unimplemented AFS can never be an `extend-existing`/`already-covered` target, however similar the underlying mechanism. This case is therefore genuinely new coverage: `ready-for-automation`, not `extend-existing`/`already-covered`.
- **Exact drag technique confirmed live this session** (via `browser-verify`/CDP; identical CDP-level mouse choreography to what `connect_nodes()` already implements in Playwright terms — mousedown on source handle, N-step mousemove, mouseup on target handle): dragging `[data-id="LLM 1"] [data-handlepos="bottom"]` → `[data-id="Printer 1"] [data-handlepos="top"]` produced the edge on the first attempt, no stray "create new node" context menu (the failure mode `connect_nodes()`'s existing Escape-dismiss logic already guards against).
- Wait strategy: no network wait needed for the connect step itself (see Network Behavior); `save_and_wait_for_update()` already wraps the one real network call in this test.
- Console-error check: filter to `level == "error"` only (per `_surface.md`'s existing ambient-warning guidance for this surface).
