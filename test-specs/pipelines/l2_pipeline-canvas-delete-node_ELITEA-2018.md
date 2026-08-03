# Test Case: Pipeline Canvas — Delete Node

## Metadata
- **TMS ID**: ELITEA-2018
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login needed)
- **Analyst**: qa-engineer (Sage), cluster analysis session with ELITEA-2030/2031/2032
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline exists with 3 nodes connected by edges: `LLM 1 → Code 1 → END`.
  - **Case-text drift (filed as `EliteaAI/elitea-testing-public#1137`, clarification):**
    the case's own Step 1 implies that adding "LLM" then "Code" via the canvas
    "+" menu auto-creates the connecting edges. Confirmed live it does **not** —
    each node added via the menu lands disconnected (0 edges) regardless of
    order. Seed this precondition via
    `PipelineAPI.create_pipeline_with_nodes()` with explicit `transition`
    fields instead (`LLM 1.transition = "Code 1"`, `Code 1.transition = "END"`)
    — reliable, avoids a flaky UI drag-connect as unscored setup.

## Test Data
### reuse-existing
- none — pipeline is created fresh per test via the API.

### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline `autotest_{test_name}` with nodes `LLM 1 → Code 1 → END`, created via
  `PipelineAPI.create_pipeline_with_nodes(entry_point="LLM 1", nodes=[...])`
  (see Automation Hints for the exact node dicts — confirmed live, this exact
  shape produces 3 nodes / 2 edges on first canvas load).

## Test Steps
1. Navigate to the pipeline's canvas (`PipelineDetailPage.navigate()` +
   `wait_for_canvas()`).
   - **Verify**: 3 nodes present (`get_node_ids()` → `["END", "LLM 1", "Code 1"]`,
     order not guaranteed — assert as a set/count of 3), 2 edges present
     (`get_edge_count() == 2`).
2. Select the Code node — no separate "select" action needed; the node's
   3-dot menu is opened directly (see step 3).
3. Delete it via the node's 3-dot header menu → "Delete" → confirm the
   "Delete confirmation" dialog (`PipelineDetailPage.delete_node("Code 1")` —
   existing method, already does menu-open → Delete click → dialog confirm).
   - **Verify**: no error toast; dialog closes.
4. Verify Code node is removed from canvas.
   - **Verify**: `get_node_ids()` no longer contains `"Code 1"`.
5. Verify edges connected to Code node are also removed.
   - **Verify**: `get_edge_count() == 0` (confirmed live: deleting the
     middle node removes BOTH its edges — `LLM 1→Code 1` AND `Code 1→END` —
     and does **not** auto-reconnect `LLM 1→END` in its place; `LLM 1` is
     left with no outgoing edge until a human/test explicitly reconnects it).
6. Verify LLM and END nodes remain.
   - **Verify**: `get_node_ids()` is exactly `{"END", "LLM 1"}` (2 nodes).
7. Save, then reload — verify deletion persists.
   - **Verify**: Save button (`[data-testid="agent-save-button"]`) is enabled
     immediately after the delete (confirmed live — node/edge deletion is
     treated as an unsaved canvas change) → click it → `page.reload()` →
     `wait_for_canvas()` → `get_node_ids()` is still exactly `{"END", "LLM 1"}`.

## Expected Results
- Code node and both its edges are removed from the canvas immediately on
  confirming the delete dialog.
- LLM 1 and END remain, node count 2, edge count 0.
- State survives Save + full page reload.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Create pipeline LLM→Code→END (3 nodes+edges) | pipeline created with nodes+edges | Preconditions (API seed) | step 1: node/edge counts on first canvas load | clarification *(see Preconditions — UI add-node does not auto-wire edges, `#1137`)* |
| 2 Select the Code node | node selected/highlighted | step 3 | implicit in `delete_node()`'s menu-open — no separate visual "selected" state exists for the 3-dot-menu delete flow (unlike the edge case, nodes don't need a canvas click-select before their menu opens) | asserted *(folded into step 3)* |
| 3 Delete it (Delete key or node menu → Delete) | delete action triggered | step 3 | 3-dot menu → Delete → confirm dialog | asserted *(case offers 2 alternatives — "press Delete key" is NOT wired for nodes in the current page object; the always-available menu path is used)* |
| 4 Verify Code node removed | Code node gone from canvas | step 4 | `get_node_ids()` excludes `"Code 1"` | asserted |
| 5 Verify edges connected to Code node removed | all edges to/from Code node gone | step 5 | `get_edge_count() == 0` | asserted |
| 6 Verify LLM and END remain | both present | step 6 | `get_node_ids() == {"END", "LLM 1"}` | asserted |
| 7 Save — verify persists after reload | Code gone, LLM+END present after reload | step 7 | node ids after `page.reload()` | asserted |

### Axis 2 — Analyst additions

- step 7 asserts the Save button is *enabled* right after the delete (before
  clicking it) — *added: confirms the app actually registers node/edge
  deletion as a dirty-state change (not a no-op that silently no-ops Save),
  a real signal any regression in the deletion pipeline would flip.*
- step 5 explicitly asserts the edge count is exactly 0 (not just "the two
  known edges are gone") — *added: rules out a stray/duplicate edge left
  behind by the deletion, which the case's "all edges... are gone" wording
  implies but doesn't operationalize into a count.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` (handled by the fixture teardown).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Canvas wrapper | `PipelineDetailPage.canvas_wrapper` (existing `LocatorDescriptor`) | — |
| Node's 3-dot menu / Delete / confirm dialog | `PipelineDetailPage.delete_node(node_id)` — existing method, reused as-is (internally: `button.MuiIconButton-colorTertiary` positional + `get_by_role("menuitem", name="Delete")` + `components.mui.Dialog` confirm — pre-existing tech debt raw handles, NOT newly added by this case; do not re-derive) | — |
| Node count / ids | `PipelineDetailPage.get_node_count()` / `get_node_ids()` (existing) | — |
| Edge count | `PipelineDetailPage.get_edge_count()` (existing) | — |
| Save button | `[data-testid="agent-save-button"]` (confirmed on `main`, digest § Confirmed testids) | — |

## Network Behavior
- Save fires `PUT .../application/prompt_lib/{project}/{id}` (same endpoint
  documented for the LLM-node AFS, ELITEA-2004) — 201 on success. Not
  independently re-verified this session; reuse that AFS's confirmed
  Network Behavior note if the implementer wants to assert the response
  code explicitly.

## Known Defects Found During Exploration
- none found (product behaves correctly — deletion removes exactly the
  target node + its edges, no orphaned edges, persists on reload).
- **Case-text drift, filed as clarification**: `EliteaAI/elitea-testing-public#1137`
  — Step 1 implies node-adding auto-wires edges; it doesn't. See Preconditions.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: `automation/pages/pipeline_detail_page.py` — `add_node()`,
  `get_node_count()`, `get_node_ids()`, `delete_node()`, `get_edge_count()`
  all already exist and are reused unmodified; no new page-object method
  needed for this case.
- Seed the precondition via a new small fixture in
  `automation/fixtures/data_fixtures.py` (or inline node list, project
  convention — follow the existing `build_hitl_runtime_nodes()` /
  `hitl_runtime_pipeline` pattern) using:
  ```python
  nodes = [
      {"id": "LLM 1", "type": "llm", "input": [], "input_mapping": {
          "chat_history": {"type": "fixed", "value": []},
          "system": {"type": "fixed", "value": ""},
          "task": {"type": "fixed", "value": "hi"},
      }, "output": ["messages"], "structured_output": False,
       "transition": "Code 1"},
      {"id": "Code 1", "type": "code", "input": [], "output": [],
       "code": "print('hi')", "transition": "END"},
  ]
  pipeline_api.create_pipeline_with_nodes(
      name=..., description=..., entry_point="LLM 1", nodes=nodes,
  )
  ```
  Confirmed live (2026-08-03): this produces exactly 3 nodes / 2 edges on
  first canvas load, no manual UI wiring needed.
- `helpers._navigate_to_canvas(page, pipeline_id)` is the existing shared
  navigation helper — reuse it, don't re-navigate manually.
