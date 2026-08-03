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
     `edge_testid_present("LLM 1", "EliteAPipelineEnd")` is `True`,
     `get_edge_count() == 2`. (No explicit extra Save needed beyond the
     dialog confirm — the delete-edge confirm dialog commits the change
     the same way `delete_node()`'s confirm does; verify via the existing
     Save-button-enabled check before reload, matching the pattern used in
     the delete-node/edge-creation siblings.)
   - **⚠️ Implementer amendment (2026-08-03, confirmed live via Save PUT
     response capture):** the AFS as originally written expected
     `get_edge_count() == 1` after reload — this is WRONG and has been
     corrected above. The saved pipeline's `pipeline_settings` field is
     empty (`{}` — confirmed by inspecting the actual `PUT
     .../application/prompt_lib/{project}/{id}` response body), meaning the
     canvas has NO cached layout and re-derives every node/edge purely from
     the `instructions` YAML's `transition` fields on each fresh load. `LLM
     1`'s transition legitimately resets to the literal `END` (step 5,
     unchanged), so a **fresh load renders that as a real `LLM 1 -> END`
     edge**, alongside the pre-existing `Printer 1 -> END` edge — 2 edges
     total, not 1. The pre-reload transient state (step 4, right after the
     in-canvas delete, before Save) genuinely IS 1 edge — `onDelete`'s
     client-side edge-removal only filters the deleted edge out of
     `flowEdges`, it does not proactively add the implicit `LLM 1 -> END`
     edge until the next full YAML→canvas parse (i.e. on reload). Step 4's
     assertion is unaffected; only step 6's is corrected. This is the same
     "every node always has SOME transition, defaulting to END" rule this
     AFS's own Preconditions section already documents — it just wasn't
     carried forward into step 6's edge-count assertion. Not re-filed as a
     `#1136`-family clarification (that thread covers the case's imagined
     "transition field" only) — this is a fresh, distinct finding.

## Expected Results
- The `LLM 1→Printer 1` edge is permanently removed.
- `LLM 1`'s transition resets to `END` (not an empty/absent value).
- State survives Save + full page reload — after reload, `LLM 1` renders a
  real `LLM 1 -> END` edge (2 edges total: `LLM 1->END`, `Printer 1->END`),
  since the canvas re-derives all edges from the saved YAML `transition`
  fields on every fresh load (see Implementer amendment on step 6 above).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open pipeline with edges | canvas shows connected nodes+edges | step 1 | step 1: `edge_exists()` True, edge count 2 | asserted |
| 2 Click an edge (clickable group) | edge selected/highlighted | step 2 | step 2: `selected` class present | asserted |
| 3 Delete the edge (delete key / context action) | deletion triggered | step 3 | step 3: Delete key → confirm dialog → confirm | asserted *(case offers "delete key or context action" — Delete key is the confirmed-working path; no separate right-click context menu was found for edges, so only the Delete-key path is automated)* |
| 4 Verify edge removed from canvas | edge gone | step 4 | step 4: `edge_exists()` False, count 1 | asserted |
| 5 Verify transition field cleared | field empty/no target | step 5 | step 5: YAML shows `transition: END` | clarification *(no literal "field" exists to read as empty — real observable is the YAML property resetting to the terminal END value, which is this domain's equivalent of "no explicit target"; `#1136`)* |
| 6 Save — verify persists after reload | no edge after reload | step 6 | step 6: `edge_exists()` False post-reload; `edge_testid_present("LLM 1", "EliteAPipelineEnd")` True; count 2 | asserted *(implementer-amended edge-count expectation, see step 6 note — the deleted edge specifically is confirmed gone; the count itself is 2 post-reload because LLM 1's reset transition renders as a real edge on a fresh load)* |

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
| Edge to click | `PipelineDetailPage.get_edge_locator("LLM 1", "Printer 1")` (existing method — see corrected format note below) | — |
| Delete-confirmation dialog | `components.mui.Dialog.wait_for(page)` / `.click_button(dialog, "Delete")` (existing helper, already used by `delete_node()`) | — |
| Edge existence / count post-delete | `PipelineDetailPage.edge_exists()` / `get_edge_count()` (existing) | — |
| Old-edge-reappears check post-reload (step 6) | `PipelineDetailPage.edge_testid_present("LLM 1", "EliteAPipelineEnd")` (existing — exact `EDGE_TESTID` template match; correct tool here because this edge is being read right after a reload, i.e. loaded fresh from the saved YAML — see the corrected format note below) | — |
| YAML view + editor | `[data-testid="pipeline-yaml-view"]` / `[data-testid="pipeline-yaml-editor"]` (confirmed working testids per `_surface.md` § YAML editor digest, ELITEA-2028) | — |

**Corrected testid format, 2026-08-04 (fix round 2, reconciled with the
shipped implementation).** This row originally cited the live testid for
the "Edge to click" element as `rf__edge-xy-edge__LLM 1source-Printer
1target` (the `source`/`target`-handle-suffix, no-`---` format) and
proposed a NEW `.react-flow__edge` prefix-scan method to reach it — both
are wrong for this case. The `LLM 1 → Printer 1` edge here is **seeded via
the API and read on a fresh canvas navigate** (Step 1), not live-connected
in-session — per `EliteaUI/src/[fsd]/features/pipelines/flow-editor/lib/
helpers/parsePipeline.helpers.js::handleTransitionNode`, ANY edge parsed
from a node's YAML `transition:` property on a fresh load gets the app's
own `{source}---{target}` id (regardless of whether the target is `END` or
another node — the `source`/`target`-suffix, no-`---` format is specific to
an edge ReactFlow's own `addEdge` auto-ids live, in-session, BEFORE any
Save + reload; see ELITEA-2031's AFS § Concrete Handles for the full
lifecycle explanation, corrected the same day for the identical
mischaracterization). The confirmed-live testid for THIS case's edge is
therefore `rf__edge-xy-edge__LLM 1---Printer 1` — the exact format
`PipelineDetailPage.EDGE_TESTID` already matches. **What actually shipped**
(review round 1): `get_edge_locator(source_id, target_id)` uses the exact
`EDGE_TESTID` template directly (`rf__edge-xy-edge__{source}---{target}`),
not the `.react-flow__edge` prefix/substring scan + `handle_suffix` param
this section originally proposed — simpler than proposed, and correct for
every edge this case touches (all either seeded-and-loaded or read
post-reload, never live-connected-only).

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
