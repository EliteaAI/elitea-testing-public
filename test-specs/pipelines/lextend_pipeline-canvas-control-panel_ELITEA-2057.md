# Test Case: Pipeline — Canvas Control Panel

## Metadata
- **TMS ID**: ELITEA-2057
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, pipelines-remaining wave-04
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/pipelines/test_pipeline_canvas_zoom_and_pan.py`
  (`test_canvas_zoom_pan_and_fit_view`, ELITEA-2019 — already merged onto this
  batch's trunk `tests/batch-pipelines-remaining-w4`). AFS:
  `test-specs/pipelines/l2_pipeline-canvas-zoom-and-pan_ELITEA-2019.md`.

## Why extend-existing, not a fresh spec

ELITEA-2057's case text asks for ALL 6 canvas control-panel buttons (Zoom In,
Zoom Out, Fit View, Toggle Interactivity, Toggle cards size, Auto-arrange).
Live exploration (2026-08-08, same pipeline id 8401 the ELITEA-2019 session
probed) confirmed all 6 buttons are children of the SAME `canvas_controls`
(`rf__controls`) ReactFlow `Controls` instance — `FlowEditor.jsx`'s
`StyledControls` renders ReactFlow's own 4 default buttons (Zoom In/Out, Fit
View, Toggle Interactivity) plus 2 app-code children appended in the same
render tree (Toggle cards size, Auto-arrange, both via `ControlButton`).

Of the case's 6 buttons, **3 are already asserted** by the merged
`test_canvas_zoom_pan_and_fit_view` (ELITEA-2019): Zoom In (exact scale +
node-bbox-area increase), Fit View (exact deterministic transform match,
asserted twice), and implicitly the panel's presence. **Zoom Out is NOT**
— the existing test's page object has a `zoom_out_canvas()` method but no
test ever calls it (confirmed by reading the merged spec; the ELITEA-2019
AFS's own "Known Defects" section notes this explicitly: "Zoom Out clamps
at minZoom... not asserted by this case, noted for awareness"). Toggle
Interactivity, Toggle cards size, and Auto-arrange are entirely new
surfaces with zero existing coverage. Duplicating the Zoom In/Fit View
assertions in a second spec would be redundant maintenance burden for no
new signal — extending the covering spec with the genuine gaps is the
correct shape (Rule 7 — reuse before create, applied at the spec level).

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline exists with multiple nodes on canvas. Reuses the SAME
  `pipeline_llm_code_end` fixture the covering test already uses (Rule 7) —
  this case makes no assertion about node TYPE, so any already-proven
  multi-node pipeline satisfies it.

## Test Data
### reuse-existing
- none required beyond the seeded pipeline above.

## Test Steps (gap only — steps 1/3/5 are already asserted by the covering test)

1. *(Already asserted — covering test step 1: navigate + node count.)*
2. Verify the control panel is visible with all 6 buttons: Zoom In, Zoom
   Out, Fit View, Toggle Interactivity, Toggle cards size, Auto-arrange.
   - **Verify**: `is_control_panel_fully_visible()` returns `True` (NEW
     page-object method — checks all 6 button locators, each scoped under
     `canvas_controls`).
3. *(Already asserted — covering test steps 3/4: Zoom In increases scale +
   node bbox area.)*
4. Click Zoom Out — verify canvas zoom level decreases.
   - **Verify** (NEW — the existing `zoom_out_canvas()` method is unused by
     any test): viewport `scale` decreases (`get_canvas_viewport_transform()`
     before/after) AND the probe node's bounding-box area decreases
     (`get_node_bounding_box()` before/after) — mirrors the existing Zoom In
     assertion shape (ELITEA-2019 step 3), symmetric direction.
5. *(Already asserted — covering test step 7: Fit View restores the exact
   step-2 transform.)*
6. Click Toggle Interactivity — verify nodes become non-draggable, click
   again to re-enable.
   - **Verify** (NEW `toggle_canvas_interactivity()` method): confirmed live
     this session — a probe node's bounding box is UNCHANGED after
     `move_node(probe_id, dx, dy)` while interactivity is toggled off (drag
     attempted via real `page.mouse` events through the existing `move_node`
     method, same technique `pan_canvas`/`connect_nodes` already use — a
     drag that would otherwise move the node by the exact delta produces
     zero displacement); toggling again restores normal drag behavior (the
     SAME `move_node(probe_id, dx, dy)` call now DOES shift the bounding box
     by the delta).
7. Click Toggle cards size — verify node cards change between
   compact/expanded view.
   - **Verify** (NEW `toggle_canvas_cards_size()` method): the probe node's
     rendered height (`get_node_bounding_box()`) shrinks by more than half
     after one click (confirmed live: a Decision node went 87.8px -> 9.5px)
     and returns to the exact original height after a second click.
8. Click Auto-arrange — verify nodes reposition to an auto-arranged layout.
   - **Verify** (NEW `auto_arrange_canvas()` method): confirmed live this
     session — the layout is fully deterministic for a static graph (same
     determinism class as Fit View, ELITEA-2019 step 7): dragging a probe
     node away from its arranged position via `move_node()` and then
     clicking Auto-arrange restores its bounding box to the EXACT original
     position (px-perfect match), not merely "some rearrangement".

## Expected Results
- All 6 control-panel buttons are visible (Zoom In, Zoom Out, Fit View,
  Toggle Interactivity, Toggle cards size, Auto-arrange).
- Zoom Out decreases both the ReactFlow viewport's `scale` and a node's
  on-screen bounding-box area (symmetric with the already-asserted Zoom In).
- Toggle Interactivity disables node dragging while active; toggling again
  restores it — round-trip, not one-way.
- Toggle cards size collapses every node card's rendered height; toggling
  again restores the exact original height — round-trip, deterministic.
- Auto-arrange recomputes node positions deterministically; a node dragged
  away from its arranged position returns to the EXACT same position after
  clicking Auto-arrange.
- No console errors, no network requests fire for any of these interactions
  (pure client-side ReactFlow/app-state operations, same class as the
  already-documented zoom/pan/Fit-View — confirmed live via console+network
  capture across the whole sequence).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline with nodes in Flow view | canvas displayed | covering test step 1 (ELITEA-2019) | `test_canvas_zoom_pan_and_fit_view` step 1: `get_node_count() == 3` | already-asserted |
| 2 Locate Control Panel with 6 named buttons, all visible | all control panel buttons visible | this AFS step 2 | new test, step 2: `is_control_panel_fully_visible()` | asserted |
| 3 Click Zoom In — verify canvas zooms in | zoom level increases | covering test steps 3/4 (ELITEA-2019) | `test_canvas_zoom_pan_and_fit_view` step 3/4: scale + node bbox area increase | already-asserted |
| 4 Click Zoom Out — verify canvas zooms out | zoom level decreases | this AFS step 4 | new test, step 4: scale + node bbox area decrease | asserted |
| 5 Click Fit View — verify all nodes fit within viewport | all nodes visible within viewport | covering test steps 2 & 7 (ELITEA-2019) | `test_canvas_zoom_pan_and_fit_view` steps 2/7: `all_nodes_within_viewport()` + exact-transform match | already-asserted |
| 6 Click Toggle Interactivity — verify nodes become non-draggable (or re-enable) | node dragging behavior toggles | this AFS step 6 | new test, step 6: `move_node()` produces zero displacement while off, exact delta while on | asserted |
| 7 Click Toggle cards size — verify node cards change between compact/expanded view | node card size changes | this AFS step 7 | new test, step 7: node bbox height shrinks then restores exactly | asserted |
| 8 Click Auto-arrange — verify nodes reposition to an auto-arranged layout | nodes repositioned in organized layout | this AFS step 8 | new test, step 8: dragged node returns to exact original position | asserted |

### Axis 2 — Analyst additions

- Step 4 (Zoom Out) asserts BOTH the numeric scale decrease AND the node
  bbox area decrease — *added: mirrors the existing, stronger Zoom In
  assertion shape from ELITEA-2019 rather than a bare "zoomed out"
  qualitative check, and closes a real pre-existing gap (the method existed,
  unused, since ELITEA-2019).*
- Step 6 (Toggle Interactivity) asserts the FULL round trip (off then back
  on), not just "click once and observe a change" — *added: confirmed live
  that a single click's effect is only meaningful when contrasted with the
  restored state; a one-shot click assertion couldn't distinguish "toggled
  off" from "always was off".*
- Step 7 (Toggle cards size) asserts the exact height is restored on the
  second click, not just "some height change" — *added: confirmed live the
  toggle is a deterministic boolean flip (`expandAll` state in
  `FlowEditor.jsx`), so an exact round-trip is a real, reproducible
  invariant, same reasoning as the existing Fit-View-determinism assertion
  in ELITEA-2019.*
- Step 8 (Auto-arrange) asserts the EXACT restored position (px-perfect),
  not merely "nodes moved" — *added: confirmed live this session that
  `onReLayout` recomputes a deterministic layout (dagre-style, not
  randomized) — dragging a node away and re-clicking Auto-arrange returned
  it to the identical starting bounding box, the same determinism class
  already documented for Fit View in ELITEA-2019.*
- All 4 new steps assert zero console errors and zero `prompt_lib`-related
  network requests — *added: confirmed live these are pure client-side
  ReactFlow/app-state operations (no XHR/fetch fires for any of Zoom
  Out/Toggle Interactivity/Toggle cards size/Auto-arrange), same class as
  the already-documented zoom/pan/Fit-View behavior. Implemented via the
  SAME `capture_console_errors()`/`capture_requests_matching("prompt_lib")`
  pattern the covering test already uses (registered once, asserted
  cumulatively).*

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` — handled by the `pipeline_llm_code_end`
   fixture's teardown (same as the covering test — no new cleanup needed).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Control panel container | `PipelineDetailPage.canvas_controls` (existing `LocatorDescriptor`, testid `rf__controls`) — confirmed live to wrap ALL 6 buttons in one DOM node, not two separate control groups | — |
| Toggle Interactivity button | **NEW** `PipelineDetailPage.toggle_canvas_interactivity()` — `self.canvas_controls.locator('button[title="Toggle Interactivity"]')`, #579 sanctioned exception (ReactFlow's own default `Controls` button, has its own real `title`/`aria-label` DOM attribute, confirmed live) | — |
| Toggle cards size button | **NEW** `PipelineDetailPage.toggle_canvas_cards_size()` — `self.canvas_controls.locator('span[aria-label="Toggle cards size"] button')`, #579 sanctioned exception (app-code `ControlButton` appended inside the SAME third-party `Controls` render tree; accessible name lives on the wrapping MUI Tooltip `<span>`, NOT the inner `<button>` — confirmed live via DOM inspection, `outerHTML` dump) | — |
| Auto-arrange button | **NEW** `PipelineDetailPage.auto_arrange_canvas()` — `self.canvas_controls.locator('span[aria-label="Auto-arrange"] button')`, same #579 exception/provenance as Toggle cards size | — |
| Control panel visibility check | **NEW** `PipelineDetailPage.is_control_panel_fully_visible()` — checks all 6 button locators above (plus the pre-existing Zoom In/Out/Fit View selectors) are visible under `canvas_controls` | — |
| Node drag test (interactivity on/off proof) | `PipelineDetailPage.move_node(node_id, dx, dy)` (existing, added for ELITEA-2047) — reused as-is; confirmed live it drags from the node's header area, clear of inner form-field inputs, which is essential (dragging from mid-node on a Printer-type node hits a textarea and never moves the node regardless of interactivity state — a false-negative trap discovered live this session) | — |
| Node bounding box (height for cards-size, position for auto-arrange) | `PipelineDetailPage.get_node_bounding_box(node_id)` (existing, added for ELITEA-2019) — reused as-is | — |

## Network Behavior
- **None** — confirmed live via console/network capture: Zoom Out, Toggle
  Interactivity, Toggle cards size, and Auto-arrange all fire zero
  `prompt_lib`-matching requests and zero console errors. Dragging a node
  (via `move_node`, used as the interactivity/auto-arrange probe) DOES
  enable the pipeline's `Save`/`Discard` buttons (confirmed live: dirty-state
  flips true after a manual node drag) — noted for awareness, not part of
  this case's assertions (no Save is performed by this test; the probe
  pipeline's own `pipeline_llm_code_end` fixture teardown deletes it
  regardless of dirty state).

## Known Defects Found During Exploration
- None. All 4 new-coverage buttons (Zoom Out, Toggle Interactivity, Toggle
  cards size, Auto-arrange) behave exactly as the case describes, confirmed
  live via Playwright MCP + CDP (`browser_run_code_unsafe`) on pipeline 8401
  (Decision + 3 Printer nodes, same pipeline ELITEA-2019 probed).
- **Methodology gotcha, not a product defect** (recorded for the next
  analyst on this surface, also filed to role memory): dragging via a
  node's mid-body coordinates on a Printer-type node (mostly `Value`/`Final
  Message` text inputs) silently fails to move the node — Playwright's
  mouse-down lands on an input field, not the ReactFlow node wrapper, so
  the resulting zero-displacement looks identical to "interactivity is
  off" but is actually a false negative from the drag start point, not the
  interactivity state. `move_node()`'s existing header-area drag point
  (`box.y + 12`) avoids this; a bare `page.mouse` drag from the bounding
  box CENTER does not.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Fixture: `pipeline_llm_code_end` (existing, `automation/fixtures/data_fixtures.py`)
  — reused unmodified, same as the covering test.
- Page object: `automation/pages/pipeline_detail_page.py`. Four NEW methods
  (all listed in Concrete Handles above): `is_control_panel_fully_visible()`,
  `toggle_canvas_interactivity()`, `toggle_canvas_cards_size()`,
  `auto_arrange_canvas()` — all additive, all scoped through the existing
  `canvas_controls` `LocatorDescriptor`. Zero new `add-data-testid` work —
  every element involved already has a testid (the panel container); only
  the individual buttons are library-internal DOM with no app-JSX hook
  possible (same #579 class as the pre-existing Zoom/Fit-View methods).
- **Extend, don't duplicate**: the new test is APPENDED to
  `test_pipeline_canvas_zoom_and_pan.py` as a second `test()` function,
  tagged with `@allure.issue(...)` pointing at ELITEA-2057 — the existing
  `test_canvas_zoom_pan_and_fit_view` body stays byte-identical (additive-
  only contract, `.agents/testing.md` / skill Hard Rule 3).
- `helpers._navigate_to_canvas(page, pipeline_id)` is the existing shared
  navigation helper — reuse it, don't re-navigate manually.

**Resolved during ELITEA-2057 implementation (Phase 2 amend-in-PR, 2 fix
rounds):**
1. The Toggle-Interactivity round-trip delta assertion needed `abs=6.0`
   (not `abs=1.0`, unlike `get_canvas_viewport_transform()`'s px-perfect
   pan/zoom matches) — a NODE drag (via `move_node`) absorbs a few px into
   ReactFlow's own node-drag-activation threshold before 1:1 tracking
   starts (observed 56px delivered for a 60px request); this is a real,
   distinct-from-pan-canvas interaction detail, not flakiness — see
   `_surface.md`.
2. Step 7 (Toggle cards size)'s "expanded" baseline must be established via
   `auto_arrange_canvas()`, NOT a plain `fit_canvas_view()` — Toggle cards
   size internally calls the SAME `onReLayout` (position recompute)
   Auto-arrange uses, so a baseline captured on manually-dragged positions
   (left over from step 6) doesn't share a basis with the post-toggle
   measurements. Full root-cause writeup: `_surface.md`
   § Toggle cards size.
