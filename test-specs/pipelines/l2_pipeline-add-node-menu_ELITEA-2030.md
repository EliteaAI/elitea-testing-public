# Test Case: Pipeline — Add Node Menu

## Metadata
- **TMS ID**: ELITEA-2030
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), cluster analysis session with ELITEA-2018/2031/2032
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline is open in Flow view (empty pipeline is sufficient — the menu's
  option set does not depend on existing canvas content).

## Test Data
### reuse-existing
- Expected node types (confirmed live, exact match to the case's own Test
  Data table): `Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP,
  Printer, Router, State modifier, Toolkit` (11 items, DOM order).

### generate-per-test (in test setup, cleaned up in its own teardown)
- Empty pipeline via the existing `pipeline_id` fixture.

## Test Steps
1. Navigate to the pipeline's canvas.
   - **Verify**: `PipelineDetailPage.canvas_wrapper` visible.
2. Click the "Add node" ("+") button.
   - **Verify**: a menu (`role="menu"`) becomes visible.
3. Read all `role="menuitem"` labels inside the menu.
   - **Verify**: labels equal, in order,
     `["Agent", "Code", "Custom", "Decision", "Human-in-the-loop", "LLM",
     "MCP", "Printer", "Router", "State modifier", "Toolkit"]` — 11 items,
     confirmed live 2026-08-03 (exact match, no extras, no omissions).
4. Click "LLM".
   - **Verify**: menu closes; an LLM node (`.react-flow__node-llm`) appears
     on canvas via `wait_for_node_on_canvas("llm")`.
5. Verify the new LLM node's configuration panel is open by default.
   - **Verify**: the node's config fields (SYSTEM/TASK/CHAT HISTORY
     Type+Value, Input/Output, Toolkits, Interrupt before/after, Structured
     output — per the `_surface.md` LLM-node digest, ELITEA-2004) are
     immediately visible in the node's rendered DOM — **no click-to-expand
     step exists**; every node type on this canvas renders its full config
     inline/always-expanded (confirmed pattern across LLM/HITL/MCP/Toolkit
     nodes, `_surface.md`). "Panel open" is satisfied by the node simply
     being present.
6. Re-open the Add node menu, then press Escape.
   - **Verify**: `page.locator('[role="menu"]').count() == 0` after Escape
     (confirmed live) and node count unchanged (no node was added).

## Expected Results
- The Add node menu lists exactly the 11 node types the case specifies, no
  more, no fewer.
- Selecting LLM adds one LLM node with its full config immediately visible.
- Escape dismisses the menu without adding a node.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: expected node types list | matches live menu | step 3 | step 3: exact list equality | asserted |
| 1 Open pipeline in Flow view | canvas displayed | step 1 | step 1: canvas wrapper visible | asserted |
| 2 Click "Add node" button | popup menu appears | step 2 | step 2: `role="menu"` visible | asserted |
| 3 Verify all 11 node types listed | all 11 present | step 3 | step 3: exact list match | asserted |
| 4 Click "LLM" | LLM node added | step 4 | step 4: node visible via `wait_for_node_on_canvas` | asserted |
| 5 New LLM node visible, config panel open | node visible + panel open | step 5 | step 5: node config fields present in DOM (always-inline, no separate "open" trigger) | asserted *(the case's phrasing implies a click-to-open interaction that doesn't exist for any node type on this canvas — not a defect, just this app's uniform node-config pattern; documented so the implementer doesn't go looking for a nonexistent "expand" control)* |
| 6 Escape / click-outside dismisses menu without adding | menu closes, no node added | step 6 | step 6: menu count 0 + node count unchanged | asserted |

### Axis 2 — Analyst additions

- step 3 asserts DOM *order* of the 11 menu items, not just set membership —
  *added: catches a future menu reorder even though the case doesn't
  require a specific order; cheap to assert since the list was read in DOM
  order anyway, and a stable order is worth guarding.*
- step 6 additionally asserts the node count is unchanged after Escape (the
  case only asserts "menu closes") — *added: rules out a race where Escape
  both closes the menu AND leaves a stray node behind, which "menu
  dismisses" alone wouldn't catch.*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` (fixture teardown).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Add node ("+") button | `PipelineDetailPage.add_node_button` (Steps 2-3, 4, 6 — new testid-backed `LocatorDescriptor`, `pipeline-add-node-button`, opened via `get_add_node_menu_items()`) | — |
| Menu + menu items | `PipelineDetailPage.get_add_node_menu_items()` / `select_add_node_menu_item()`, testid-based via `pipeline-add-node-menu` + `pipeline-add-node-menu-item-{type}` (added to `AddNodeMenu.jsx` via `add-data-testid`, on `automation/testids`) | — |
| Node appears on canvas | `PipelineDetailPage.wait_for_node_on_canvas("llm")` (existing) | — |
| Node count | `PipelineDetailPage.get_node_count()` (existing) | — |

**Testid gap CLOSED (implementer amendment, review round 1).** The original
exploration below is kept for its provenance value, but its own
recommendation did not survive review:

> ~~Testid gap, not blocking: the Add-node "+" button and its 11 menu items
> carry zero `data-testid`s... Recommend (a) [reuse the existing raw-handle
> `add_node()` method as-is]... flagging for the lead rather than deciding
> unilaterally.~~

`.agents/role-overrides.md` § Every role — locator policy states the
escalation test is **OR, not AND**: a missing testid ALONE is enough to
require `add-data-testid`, regardless of whether reusing a raw handle would
also work and regardless of an AFS's own "not blocking" framing — an AFS
recommendation doesn't waive the hard-override. Reviewer flagged this in
round 1; testids were added onto `AddNodeMenu.jsx`'s trigger button, `Menu`,
and each `MenuItem` (keyed by internal node type) instead.

**Step 4 update (fix round 4).** `add_node()` (Step 4, pre-existing tech debt
shared with `test_pipeline_nodes.py::TestAddNode`) was initially left
untouched as out of this case's scope. Round 3 review flagged the companion
`select_add_node_menu_item()` method as dead code (zero callers anywhere in
the branch — canon ruling #511, a method isn't "exercised" by merely
existing). Rather than delete it, round 4 wired it into this test's own
Step 4 (`get_add_node_menu_items()` to open + `select_add_node_menu_item("llm")`
to select), closing the dead-code finding AND completing the testid-clean
sweep for this case's own steps. `add_node()` itself is untouched and
remains correct, in-use tech debt for every OTHER pipeline test that calls
it — this is a same-file, same-case change, not a re-scope of that debt.

## Network Behavior
- None — pure client-side canvas/menu interaction, no XHR involved in
  opening the menu, listing items, or adding a node (node creation is
  local ReactFlow state until Save).

## Known Defects Found During Exploration
- none found.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: `automation/pages/pipeline_detail_page.py` — `wait_for_node_on_canvas()`,
  `get_node_count()` exist, reuse as-is; Step 4 uses the testid-based
  `get_add_node_menu_items()` + `select_add_node_menu_item("llm")` pair
  (round 4 — see Concrete Handles § Step 4 update), not `add_node()`.
- `helpers._navigate_to_canvas(page, pipeline_id)` for setup navigation.
- For step 3 (reading the full menu item list), extend `add_node()`'s
  existing menu-open logic rather than duplicating the "+..click, wait 300ms"
  sequence — e.g. a small `get_add_node_menu_items() -> list[str]` method
  that opens the menu, reads `get_by_role("menuitem")` texts, and leaves
  the menu open for the caller to either click an item or press Escape.
