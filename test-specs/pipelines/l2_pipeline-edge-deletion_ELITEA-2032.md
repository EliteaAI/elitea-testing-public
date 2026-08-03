# Test Case: Pipeline — Edge Deletion

## Metadata
- **TMS ID**: ELITEA-2032
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), cluster analysis session with ELITEA-2018/2030/2031
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline with an edge connecting two nodes exists: `LLM 1 → Printer 1`
  (seeded via explicit `transition: "Printer 1"` on `LLM 1`, `transition:
  "END"` on `Printer 1` — see Automation Hints).

- **Case-text drift (filed as `EliteaAI/elitea-testing-public#1136`,
  clarification, same root cause as ELITEA-2031's sibling finding):** the
  case's Step 5 expects "the source node's transition field is cleared /
  empty or set to no target" — but there is no visible "transition field"
  in the node config panel to read (see ELITEA-2031's AFS for the full
  finding). The verifiable equivalent, confirmed live: after deleting the
  edge, the source node's underlying `transition` YAML property does not
  become empty/absent — it resets to the literal value `END` (confirmed via
  the YAML editor view; matches the product's own
  `deletionOperations.helpers.js::clearNodePropertyAndSetEnd` — every node
  always has SOME transition, defaulting to the terminal `END` state when
  no explicit target is set). This AFS asserts `transition: END`, not an
  empty/absent field.

## Test Data
- (none required, per the case's own Test Data table)

### generate-per-test (in test setup, cleaned up in its own teardown)
- Pipeline `autotest_{test_name}` with `LLM 1 → Printer 1 → END` (see
  Automation Hints for exact node dicts).

## Test Steps
1. Navigate to the pipeline's canvas.
   - **Verify**: `edge_exists("LLM 1", "Printer 1")` is `True`;
     `get_edge_count() == 2` (`LLM 1→Printer 1`, `Printer 1→END`).
2. Click on the `LLM 1→Printer 1` edge on the canvas (edges are clickable
   `.react-flow__edge` groups — locate via the confirmed live testid
   `rf__edge-xy-edge__LLM 1source-Printer 1target`, then click it).
   - **Verify**: the edge's `class` attribute gains `selected`
     (confirmed live: `react-flow__edge react-flow__edge-custom nopan
     selected selectable`).
3. Delete the edge via the `Delete` keyboard key.
   - **Verify**: a confirmation dialog appears — `role="dialog"`, text
     "Delete confirmation — Are you sure to delete the&nbsp;&nbsp;node? It
     can't be restored." (confirmed live; **UI copy says "node" even
     though an edge, not a node, is being deleted** — see Known Defects,
     filed as a MINOR clarification-adjacent copy note, not blocking).
     Click "Delete" to confirm (`components.mui.Dialog.click_button(dialog,
     "Delete")` — existing helper).
4. Verify the edge is removed from canvas.
   - **Verify**: `edge_exists("LLM 1", "Printer 1")` is `False`;
     `get_edge_count() == 1` (only `Printer 1→END` remains).
5. Verify the source node's transition is cleared.
   - **Verify**: open the YAML view (`[data-testid="pipeline-yaml-view"]`)
     and read `[data-testid="pipeline-yaml-editor"]`'s text — `LLM 1`'s
     node block shows `transition: END` (confirmed live — resets to END,
     not to an empty/absent value; see Preconditions clarification note).
6. Save — verify edge removal persists after reload.
   - **Verify**: `page.reload()` → `wait_for_canvas()` →
     `edge_exists("LLM 1", "Printer 1")` still `False`,
     `get_edge_count() == 1`. (No explicit extra Save needed beyond the
     dialog confirm — the delete-edge confirm dialog commits the change
     the same way `delete_node()`'s confirm does; verify via the existing
     Save-button-enabled check before reload, matching the pattern used in
     the delete-node/edge-creation siblings.)

## Expected Results
- The `LLM 1→Printer 1` edge is permanently removed.
- `LLM 1`'s transition resets to `END` (not an empty/absent value).
- State survives Save + full page reload.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open pipeline with edges | canvas shows connected nodes+edges | step 1 | step 1: `edge_exists()` True, edge count 2 | asserted |
| 2 Click an edge (clickable group) | edge selected/highlighted | step 2 | step 2: `selected` class present | asserted |
| 3 Delete the edge (delete key / context action) | deletion triggered | step 3 | step 3: Delete key → confirm dialog → confirm | asserted *(case offers "delete key or context action" — Delete key is the confirmed-working path; no separate right-click context menu was found for edges, so only the Delete-key path is automated)* |
| 4 Verify edge removed from canvas | edge gone | step 4 | step 4: `edge_exists()` False, count 1 | asserted |
| 5 Verify transition field cleared | field empty/no target | step 5 | step 5: YAML shows `transition: END` | clarification *(no literal "field" exists to read as empty — real observable is the YAML property resetting to the terminal END value, which is this domain's equivalent of "no explicit target"; `#1136`)* |
| 6 Save — verify persists after reload | no edge after reload | step 6 | step 6: `edge_exists()` False post-reload | asserted |

### Axis 2 — Analyst additions

- step 2 asserts the `selected` CSS class explicitly — *added: the case's
  "edge is selected/highlighted" expected result has no other observable
  hook; this confirms the click actually registered as a selection (not a
  miss) before the Delete key is trusted to act on the right target.*
- step 3 asserts the confirmation dialog's exact text — *added: documents
  the "node" vs "edge" copy discrepancy live (see Test Steps note) so a
  future reader isn't confused by a screenshot/log mentioning "node" for
  what is actually an edge deletion; not asserted as a failure, just
  captured for traceability.*
- step 4 asserts the edge count is exactly 1 (not just "the specific edge
  is gone") — *added: rules out the deletion accidentally taking the
  sibling `Printer 1→END` edge with it.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` (fixture teardown).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Edge to click | `page.locator('[data-testid="rf__edge-xy-edge__LLM 1source-Printer 1target"]')` — literal ReactFlow-generated testid (third-party widget, sanctioned per stop+flag exception #1) for this specific source→target pair; generalize via a new small page-object method (see Automation Hints) rather than hardcoding the string in the test | — |
| Delete-confirmation dialog | `components.mui.Dialog.wait_for(page)` / `.click_button(dialog, "Delete")` (existing helper, already used by `delete_node()`) | — |
| Edge existence / count post-delete | `PipelineDetailPage.edge_exists()` / `get_edge_count()` (existing) | — |
| YAML view + editor | `[data-testid="pipeline-yaml-view"]` / `[data-testid="pipeline-yaml-editor"]` (confirmed working testids per `_surface.md` § YAML editor digest, ELITEA-2028) | — |

**New page-object method needed** (small, testid-based — not a raw-handle
addition): the existing `edge_exists()`/`edge_testid_present()` only
return `bool`. This case needs to actually **click** a specific edge, so
add e.g. `get_edge_locator(source_id, target_id, handle_suffix=None) ->
Locator`, mirroring `edge_exists()`'s own prefix/substring search over
`.react-flow__edge` but returning the matched `Locator` (via `.nth(i)`)
instead of `True`/`False`, for the caller to `.click()`. This reuses the
SAME testid-matching logic already in the file — no new selector class,
no raw CSS/role handle.

## Network Behavior
- No dedicated network call for the click-select or the Delete-key trigger
  (client-side ReactFlow state + a local confirm dialog) — the edge
  removal persists via the same pipeline Save endpoint
  (`PUT .../application/prompt_lib/{project}/{id}`) as any other canvas
  edit; confirm this fires by waiting for network idle (`wait_for_network()`)
  before the reload in step 6, per project convention (never a raw sleep).

## Known Defects Found During Exploration
- **[MINOR, not filed separately]** the delete-confirmation dialog's copy
  says "Are you sure to delete the&nbsp;&nbsp;node? It can't be restored."
  for an EDGE deletion (double space where a node-type word would go,
  wrong noun "node"). Cosmetic only — does not affect the deletion
  mechanism. Not worth its own ticket per the light-dedup/strict-per-bug
  balance (a copy nit, not a functional defect); documented here and in
  Test Steps step 3 for traceability. Flag to the lead if a UI-copy
  backlog exists to route it to.
- **Case-text drift, filed as clarification**: `EliteaAI/elitea-testing-public#1136`
  — Step 5 describes a config-panel "transition field" that doesn't exist;
  see Preconditions.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: `automation/pages/pipeline_detail_page.py` — extend with
  `get_edge_locator()` (see Concrete Handles) alongside the existing
  `connect_nodes()`/`edge_exists()`/`get_edge_count()`/`EDGE_TESTID`.
- Seed via `PipelineAPI.create_pipeline_with_nodes()`:
  ```python
  nodes = [
      {"id": "LLM 1", "type": "llm", "input": [], "input_mapping": {
          "chat_history": {"type": "fixed", "value": []},
          "system": {"type": "fixed", "value": ""},
          "task": {"type": "fixed", "value": "hi"},
      }, "output": ["messages"], "structured_output": False,
       "transition": "Printer 1"},
      {"id": "Printer 1", "type": "printer",
       "input_mapping": {"printer": {"type": "fixed", "value": "done"}},
       "transition": "END"},
  ]
  ```
  This differs from ELITEA-2031's seed (which explicitly points BOTH
  nodes at END, to avoid a pre-existing edge) — here the edge under test
  must already exist, so `LLM 1.transition` is seeded directly at
  `"Printer 1"`.
- Share the same fixture shape as ELITEA-2031 where practical (both use an
  `LLM 1 + Printer 1` pair) — consider a single parametrized fixture
  taking the desired `LLM 1` transition value, rather than two near-
  duplicate fixtures, if the implementer finds the overlap worth
  collapsing. Not required — flagged as an option, not a mandate.
