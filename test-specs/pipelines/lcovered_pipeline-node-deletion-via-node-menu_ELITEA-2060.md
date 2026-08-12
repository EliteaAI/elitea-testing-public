# Test Case: Pipeline — Node Deletion via Node Menu

## Metadata
- **TMS ID**: ELITEA-2060
- **Linked Story**: none
- **Priority**: high (per source case; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), session 2026-08-09
- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A pipeline with multiple connected nodes exists.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/pipelines/test_pipeline_canvas_delete_node.py`
(TMS ELITEA-2018, AFS `test-specs/pipelines/l2_pipeline-canvas-delete-node_ELITEA-2018.md`),
merged to `origin/automation/base` at commit `5259179a`
("test: (ELITEA-2018/2030/2031/2032) pipeline canvas node/edge CRUD").

**Re-confirmed live this session** (2026-08-09, same repo state, localhost:5173):

```
cd automation && HEADLESS=true ../.venv/bin/pytest tests/ui/pipelines/test_pipeline_canvas_delete_node.py -v -p no:cacheprovider
...
tests/ui/pipelines/test_pipeline_canvas_delete_node.py::test_delete_middle_node_removes_its_edges_and_persists PASSED [100%]
============================== 1 passed in 22.36s ==============================
```

**Behavioural-equivalence argument.** ELITEA-2060's seven steps describe the exact same
interaction and observable that `test_pipeline_canvas_delete_node.py` already exercises
and asserts, verified against the live JSX (`EliteaUI/src/[fsd]/features/pipelines/
flow-editor/ui/nodes/BaseNode/NodeCardHeader.jsx` + `useDeleteItems.hooks.js`):

- **"Two small buttons on the node header" (case Step 3)** = the node header's
  `Expand/Collapse` `IconButton` + the `DotMenu` trigger `IconButton` (both rendered
  with `color="tertiary"`, both visible whenever the node is expanded —
  `NodeCard.jsx:13` defaults `isExpanded` to `true`, so both buttons are visible on
  canvas load with no separate "select" step required; this matches ELITEA-2018's own
  Coverage Map note that no distinct selected-state exists before the menu-open flow).
- **"Click the delete button (trash icon) on the node" (case Step 4)** = open the
  second header button (the 3-dot `DotMenu` trigger), then click the "Delete" menu
  item — which itself renders a `DeleteIcon` (trash glyph) beside the "Delete" label
  (`NodeCardHeader.jsx:218-227`) — then confirm the "Are you sure to delete this node"
  dialog that `handleDeleteNode` always raises (`useDeleteItems.hooks.js:101-111`).
  This is exactly `PipelineDetailPage.delete_node(node_id)`, reused unmodified by the
  covering spec.
- **No separate quick-action trash icon exists outside the DotMenu** — confirmed by
  source grep: `DeleteIcon` is referenced only once in the pipelines flow-editor
  (`NodeCardHeader.jsx`), inside the dropdown menu item, not as a standalone header
  button. The case's "(trash icon)" phrasing describes the Delete menu item's icon,
  not a third, undiscovered control.

| ELITEA-2060 step | Covered by (`test_pipeline_canvas_delete_node.py`) |
|---|---|
| 1. Open a pipeline with multiple nodes → canvas shows multiple nodes | Step 1, `:38-46` — navigates to the fixture pipeline (`LLM 1 → Code 1 → END`, 3 nodes/2 edges) and asserts node/edge counts on first canvas load |
| 2. Hover/select a non-entry-point node → highlighted/selected | folded into Step 2/3 (`:49-51`) — deletes "Code 1" (a non-entry-point middle node); no separate select action needed (see behavioural-equivalence note above — `isExpanded` defaults true) |
| 3. Locate the node's action buttons (two small buttons on header) → visible | `PipelineDetailPage.delete_node()` (`automation/pages/pipeline_detail_page.py:2988-3026`) queries exactly `button.MuiIconButton-colorTertiary` on the node and clicks the second (`btns[1]`) — confirms exactly 2 header icon buttons exist |
| 4. Click the delete button (trash icon) → deletion triggered | same method — 3-dot menu → "Delete" menuitem (trash icon) → confirm dialog | `:49-51` |
| 5. Verify node removed from canvas | Step 4, `:54-58` — `get_node_ids()` excludes `"Code 1"` |
| 6. Verify edges to/from that node removed | Step 5, `:60-66` — `get_edge_count() == 0` |
| 7. Verify Save button becomes enabled | Step 7, `:74-77` — `pipeline_page.save_button.is_enabled()` asserted True immediately after the delete, before clicking it |

The covering spec additionally proves Save + full-page-reload persistence
(`:78-87`) — a strict superset of what ELITEA-2060 asks for; ELITEA-2060's case does
not require the reload check, so no gap exists in the other direction either.

**Scope note (no gap, so no `extend-existing`).** ELITEA-2060's preconditions ("a
pipeline with multiple connected nodes") and steps are generic — no node type, node
count, or position (entry/middle/end) is specified beyond "non-entry-point". The
covering spec's fixture (`LLM 1 → Code 1 → END`, deleting the middle "Code 1" node) is
a concrete instance of exactly this generic scenario: a non-entry-point node with edges
on both sides, deleted via the identical UI mechanism. No case element goes unassessed
by the covering spec's assertions.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Open a pipeline with multiple nodes — Pipeline canvas is displayed with multiple nodes
2. Hover over or select a non-entry-point node on the canvas — Node is highlighted or selected
3. Locate the node's action buttons (two small buttons on the node header) — Action buttons are visible on the node
4. Click the delete button (trash icon) on the node — Node deletion is triggered
5. Verify node is removed from canvas — Node no longer appears on the canvas
6. Verify edges to/from that node are removed — All edges connected to the deleted node are gone
7. Verify "Save" button becomes enabled — Save button is active indicating unsaved changes

## Expected Results
- The node and all its connected edges are removed from the canvas via the node's
  3-dot header menu → Delete → confirm flow; the Save button becomes enabled to
  reflect the unsaved change — proven live by `test_pipeline_canvas_delete_node.py`
  (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open pipeline with multiple nodes | canvas shows multiple nodes | `test_pipeline_canvas_delete_node.py` Step 1 | `:38-46` | already-covered |
| Step 2 — select non-entry-point node | node highlighted/selected | same, Step 2/3 | `:49-51` | already-covered |
| Step 3 — locate node's action buttons (2 header buttons) | buttons visible | `PipelineDetailPage.delete_node()` | `automation/pages/pipeline_detail_page.py:2988-3014` | already-covered |
| Step 4 — click delete (trash icon) | deletion triggered | same | `:3016-3025` | already-covered |
| Step 5 — node removed from canvas | node gone | same test, Step 4 | `:54-58` | already-covered |
| Step 6 — edges to/from node removed | edges gone | same test, Step 5 | `:60-66` | already-covered |
| Step 7 — Save button becomes enabled | Save active | same test, Step 7 | `:74-77` | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_pipeline-canvas-delete-node_ELITEA-2018.md`'s Coverage Map — exact edge count
  (not just "the known edges"), Save-enabled-before-click as a dirty-state signal) —
  none needed here.

## Cleanup
N/A — no new test written; nothing new to clean up. (Covering spec's own fixture,
`pipeline_llm_code_end`, creates and deletes its dedicated pipeline per test.)

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — see
`l2_pipeline-canvas-delete-node_ELITEA-2018.md` § Concrete Handles and
`test-specs/pipelines/_surface.md`. No new handles were needed for this traceability
pass.

## TMS linkage
Link ELITEA-2060 to ELITEA-2018 in the TMS (both ways) so the audit trail resolves:
ELITEA-2060's `already-covered` disposition points at ELITEA-2018's automated test;
ELITEA-2018's case gains a "also satisfies ELITEA-2060" back-reference.
