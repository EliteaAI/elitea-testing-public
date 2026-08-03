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
| Add node ("+") button | `PipelineDetailPage.add_node(node_type)` — existing method (internally `button.MuiIconButton-colorPrimary` positional, pre-existing tech debt, reused unmodified) | — |
| Menu + menu items | `page.locator('[role="menu"]')` / `page.get_by_role("menuitem")` — same raw handles already used inside the existing `add_node()` method; reading the list for step 3 is a NEW read-only use of an EXISTING selector shape (no new selector class introduced) | — |
| Node appears on canvas | `PipelineDetailPage.wait_for_node_on_canvas("llm")` (existing) | — |
| Node count | `PipelineDetailPage.get_node_count()` (existing) | — |

**Testid gap, not blocking**: the Add-node "+" button and its 11 menu items
carry zero `data-testid`s (confirmed via menu `inner_html()` dump — plain
MUI `MenuItem`/`ListItemText`, no `data-testid` anywhere). This is a
pre-existing gap already tolerated by the merged HITL-add test
(`test_pipeline_nodes.py::TestAddNode`), which uses the same raw
`role="menuitem"` + text-match pattern. Per `.agents/role-overrides.md`
scope rule ("testids go ONLY on elements tests actually touch" + "existing
code is not precedent, but don't force a new raw handle where a testid
could be added"), this case's implementer has the choice to either (a)
reuse the existing raw-handle `add_node()` method as-is (fastest, matches
the current file's own precedent for the SAME menu), or (b) run
`add-data-testid` to wire testids onto the "+" button and the 11 menu
items (cleaner, but touches `NodeAddMenu`-equivalent shared JSX and is a
larger footprint for a single AFS). Recommend (a) for this case since (b)
is a cross-cutting improvement better scoped to its own task — flagging
for the lead rather than deciding unilaterally.

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
- Page object: `automation/pages/pipeline_detail_page.py` — `add_node()`,
  `wait_for_node_on_canvas()`, `get_node_count()` all exist; reuse as-is.
- `helpers._navigate_to_canvas(page, pipeline_id)` for setup navigation.
- For step 3 (reading the full menu item list), extend `add_node()`'s
  existing menu-open logic rather than duplicating the "+..click, wait 300ms"
  sequence — e.g. a small `get_add_node_menu_items() -> list[str]` method
  that opens the menu, reads `get_by_role("menuitem")` texts, and leaves
  the menu open for the caller to either click an item or press Escape.
