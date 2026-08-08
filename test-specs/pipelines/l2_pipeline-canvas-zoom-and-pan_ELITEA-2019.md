# Test Case: Pipeline Canvas — Zoom and Pan

## Metadata
- **TMS ID**: ELITEA-2019
- **Linked Story**: none
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN` — no explicit login needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, pipelines-remaining wave-04
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost `auth_state` fixture).
- A pipeline exists with multiple nodes on canvas. Reused the existing
  `pipeline_llm_code_end` fixture (`LLM 1 -> Code 1 -> END`, 3 nodes / 2 edges,
  already proven live for ELITEA-2018) rather than adding a new fixture — Rule
  7 (reuse before create); this case makes no assertion about node TYPE or
  edge wiring, so any already-proven multi-node pipeline satisfies it.

## Test Data
### reuse-existing
- none required beyond the seeded pipeline above.

## Test Steps
1. Navigate to the pipeline's canvas (`PipelineDetailPage.navigate()` +
   `wait_for_canvas()`).
   - **Verify**: 3 nodes present (`get_node_count() == 3`).
2. Click Fit View (`fit_canvas_view()` — pre-existing method) and verify all
   nodes are visible within the canvas viewport.
   - **Verify**: every node's bounding box is fully contained within the
     `canvas_wrapper` (`rf__wrapper`) bounding box (new helper
     `all_nodes_within_viewport()` — see Concrete Handles).
3. Zoom in using the canvas Zoom In control.
   - **Verify**: canvas scale increases (new `get_canvas_viewport_transform()`
     `["scale"]` compared before/after) AND a node's rendered bounding-box area increases
     (`get_node_bounding_box(node_id)` before/after on the same node) —
     confirmed live this session: scale 0.206152 -> 0.247382, Decision-node
     box 97.1x87.8px -> 116.5x105.4px on one Zoom In click.
4. *(Folded into step 3 — the case's step 3/4 split ["zoom in" / "verify
   nodes appear larger"] is one observable, decomposed as one AFS step per
   the Coverage Map below.)*
5. Pan the canvas by dragging on empty canvas space.
   - **Verify**: canvas viewport translate offset changes AND the same
     node's bounding-box position (x/y) shifts by the drag delta — confirmed
     live this session: dragging by (+100, +150) screen px moved the
     viewport transform from `translate(12.9193px, 348.199px)` to
     `translate(112.919px, 498.199px)` — an EXACT (+100, +150) match — and
     the probed node's bounding box moved by the identical delta.
6. *(Folded into step 5 — same case-authoring split as steps 3/4.)*
7. Click Fit View again and verify the canvas returns to the all-nodes-visible
   state.
   - **Verify**: same `all_nodes_within_viewport()` check as step 2 passes
     again AND the viewport transform returns to the SAME fit-to-view value
     step 2 produced — confirmed live this session: after zoom-in + pan away
     from the step-2 baseline, clicking Fit View again returned the
     transform to the EXACT step-2 value (`translate(12.9193px, 348.199px)
     scale(0.118012)`), not merely "some fit state" — Fit View is
     deterministic for a static node layout, a stronger assertion than "all
     nodes visible" alone.

## Expected Results
- Fit View (step 2) brings every node inside the canvas viewport bounds.
- Zoom In increases both the ReactFlow viewport's `scale` and a node's
  on-screen bounding-box size.
- Dragging the empty canvas pans the viewport by the exact drag delta; a
  node's bounding-box position shifts by the same delta.
- Fit View (step 7), clicked again after zoom+pan, restores the exact
  transform step 2 produced (all nodes visible again).
- No console errors, no network requests fire for any of these interactions
  (pure client-side ReactFlow viewport state — confirmed live, see Network
  Behavior).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline with multiple nodes on canvas | canvas loads with nodes visible | step 1 | `step 1`: `get_node_count() == 3` | asserted |
| 2 Use Fit View — verify all nodes visible | canvas adjusts, all nodes visible | step 2 | `step 2`: `all_nodes_within_viewport()` | asserted |
| 3 Zoom in using zoom controls or scroll | zoom level increases, nodes larger | step 3 | `step 3`: scale + node bbox area increase | asserted *(decomposed with case step 4)* |
| 4 Verify zoom level changes (nodes appear larger) | nodes visibly larger | step 3 | same assertion as step 3 | asserted *(folded — one observable, case split it into two rows)* |
| 5 Pan the canvas by dragging | viewport position changes | step 5 | `step 5`: transform translate + node bbox position delta | asserted *(decomposed with case step 6)* |
| 6 Verify viewport position changes | canvas scrolled/panned | step 5 | same assertion as step 5 | asserted *(folded — one observable, case split it into two rows)* |
| 7 Click Fit View again — verify all-nodes-visible restored | all nodes visible again | step 7 | `step 7`: `all_nodes_within_viewport()` + exact-transform-match vs step 2 | asserted |

### Axis 2 — Analyst additions

- step 3/step 7 assert the exact numeric `scale`/`translate` values (via
  `get_canvas_viewport_transform()`), not just "nodes look
  bigger"/"looks fit" — *added: confirmed live that Fit View is fully
  deterministic for a static node layout (returns the identical transform
  both times), which makes an exact-match assertion possible and a much
  stronger regression guard than a qualitative "all nodes visible" check
  alone.*
- step 5 asserts the node's bounding-box position shifts by the **exact**
  drag delta (not just "some change") — *added: confirmed live the ReactFlow
  pane's pan tracks mouse delta 1:1 (px-perfect), so this is a real,
  reproducible invariant, not an approximation.*
- step 3/5/7 assert zero console errors and zero new network requests during
  the whole zoom/pan/fit-view sequence — *added: confirmed live these are
  pure client-side ReactFlow viewport operations (no XHR/fetch fires); a
  regression that accidentally triggers a save/persist call on viewport
  change would be a real, novel defect this guards against.* **Implemented
  in R1 fix round** (`capture_console_errors()` +
  `capture_requests_matching("prompt_lib")`, both `BasePage` methods,
  registered right after the step-2 baseline so the canvas's own
  initial-load fetch is excluded, asserted cumulatively at steps 3, 5, and 7)
  — R1's shipped diff omitted this clause entirely despite the claim above;
  see `.agents/memory/qa-engineer/afs_claims_need_full_sweep_and_grep.md`
  (ELITEA-2019 entry) for the review finding.

## Cleanup
1. `pipeline_api.delete_pipeline(pid)` — handled by the `pipeline_llm_code_end`
   fixture's teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Canvas wrapper | `PipelineDetailPage.canvas_wrapper` (existing `LocatorDescriptor`, testid `rf__wrapper`) | — |
| Zoom/Fit-View control panel | `PipelineDetailPage.canvas_controls` (existing `LocatorDescriptor`, testid `rf__controls`) | — |
| Fit View button | `PipelineDetailPage.fit_canvas_view()` (existing method — already scopes `button[title="Fit View"]` under `canvas_controls`, #579 sanctioned exception) | — |
| Zoom In / Zoom Out buttons | **NEW** `PipelineDetailPage.zoom_in_canvas()` / `zoom_out_canvas()` — same pattern as `fit_canvas_view()`: `self.canvas_controls.locator('button[title="Zoom In"]'/'button[title="Zoom Out"]').click()`, #579 sanctioned exception (ReactFlow's own `Controls` component, no app testid placeable on the individual button — confirmed via source, `EliteaUI/src/[fsd]/features/pipelines/flow-editor/ui/FlowEditor.jsx` renders the third-party `@xyflow/react` `Controls` component directly). **Do NOT reuse the pre-existing raw `zoom_in()`/`zoom_out()` methods at the bottom of `pipeline_detail_page.py`** (`self.page.locator('button[title="..."]')`, unscoped, tracked tech debt) — they are page-level, not scoped to `canvas_controls`, and would fail the reviewer's mechanical grep as a new raw handle if a NEW call site were added referencing them; the new scoped methods are additive, existing raw ones are left untouched. | — |
| Canvas pane (pan target) | **NEW** `PipelineDetailPage.pan_canvas(dx, dy)` — drags via `self.canvas_wrapper.locator(".react-flow__pane")`'s bounding box (#579 sanctioned exception, same class the pre-existing `_deselect_all()` already uses page-level — this new method scopes it under `canvas_wrapper` instead, per the "parent must have a real testid" discipline), starting from a point inset 15% from the wrapper's top-left corner (empty after Fit View's default padding, confirmed live) and using `page.mouse.move/down/up` in interpolated steps — same technique as the existing `move_node()`. | — |
| Canvas viewport transform (scale + translate, for numeric assertions) | **NEW** `PipelineDetailPage.get_canvas_viewport_transform()` — read `self.canvas_wrapper.locator(".react-flow__viewport")`'s `style` attribute (#579 sanctioned exception, ReactFlow-injected inline style, no app testid possible on a CSS transform value) and regex-parse `translate(<tx>px, <ty>px) scale(<s>)` into a single `{"tx": float, "ty": float, "scale": float}` dict (one method, not the two originally proposed — `get_canvas_zoom_scale()`/`get_canvas_pan_offset()` were the analyst's planned split; the implementer shipped one combined getter instead, since scale+translate parse off the same style string in one regex pass — amended here to match, per Rule 11/Phase 2 amend-in-PR). Confirmed live shape this session (both browsers, different viewport sizes): `translate(Npx, Mpx) scale(S)`. | — |
| Node bounding box (size + position, for zoom/pan proof) | **NEW** `PipelineDetailPage.get_node_bounding_box(node_id)` — `self.page.locator(self.RF_NODE_TESTID.format(node_id)).bounding_box()` (existing `RF_NODE_TESTID` class constant, #579 sanctioned exception, already used internally by `move_node()`) exposed as a public getter; none existed before this case. | — |
| "All nodes visible" check | **NEW** `PipelineDetailPage.all_nodes_within_viewport()` — for every id in `get_node_ids()`, `get_node_bounding_box(id)` must be fully contained within `canvas_wrapper.bounding_box()` (with a small tolerance, confirmed live via containment check on all 5 nodes of a Decision+3-Printer-branch pipeline after Fit View). | — |
| Node count | `PipelineDetailPage.get_node_count()` (existing) | — |

## Network Behavior
- **None** — confirmed live via console/network capture across the whole
  zoom-in -> pan -> Fit-View sequence: zoom, pan, and Fit View are pure
  client-side `@xyflow/react` viewport transforms (CSS `transform` on
  `.react-flow__viewport`); no XHR/fetch fires for any of them, no Save is
  implied or required. (Distinct from node CONFIGURATION changes elsewhere
  in this suite, which DO trigger `PUT .../application/prompt_lib/{project}/{id}`
  on Save — viewport zoom/pan is not persisted state at all, confirmed live:
  it isn't part of `pipeline_settings` and a reload resets it to the default
  Fit View, out of scope for this case's steps.)

## Known Defects Found During Exploration
- None. Zoom, pan, and Fit View all behave exactly as the case describes,
  confirmed live via two independent browser sessions (Playwright MCP +
  CDP/`browser-verify`) — Fit View recomputes a deterministic transform,
  Zoom In/Out change scale symmetrically (Zoom Out clamps at ReactFlow's
  default `minZoom` — observed `scale(0.1)` with the Zoom Out button then
  disabled; not asserted by this case, noted for awareness only), pan
  tracks the mouse drag delta exactly.
- Console messages captured across the (long-lived, multi-feature)
  Playwright MCP session included several PRE-EXISTING, unrelated warnings
  (a `validateDOMNesting` React warning inside the Import-wizard dialog,
  already tracked at `EliteaAI/elitea-testing-public#570`; a CORS error
  against the Run-Details endpoint, already documented in this surface's
  digest; a `svg-pan-zoom`/mermaid `resetZoom` exception from an earlier,
  unrelated exploration) — none of these were triggered by, or related to,
  the zoom/pan/Fit-View interactions this case covers.

## Blocked Steps
- none.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Fixture: `pipeline_llm_code_end` (existing, `automation/fixtures/data_fixtures.py`)
  — reused unmodified.
- Page object: `automation/pages/pipeline_detail_page.py`. Six NEW methods
  shipped (all listed in Concrete Handles above): `zoom_in_canvas()`,
  `zoom_out_canvas()`, `pan_canvas(dx, dy)`, `get_canvas_viewport_transform()`
  (combined scale+translate getter — replaces the two originally-planned
  `get_canvas_zoom_scale()`/`get_canvas_pan_offset()` split; amended here per
  Rule 11/Phase 2 amend-in-PR), `get_node_bounding_box(node_id)`,
  `all_nodes_within_viewport()` — all additive, all scoped through existing
  testid `LocatorDescriptor`s (`canvas_wrapper`/`canvas_controls`) or the
  existing `RF_NODE_TESTID` #579-sanctioned class constant. Zero new
  `add-data-testid` work — every element involved already has a testid
  (the panel container, the wrapper, the node containers); only the
  individual Zoom In/Zoom Out buttons and the pan-target pane are
  library-internal DOM with no app-JSX hook possible (same #579 class as
  the pre-existing `fit_canvas_view()`).
- `helpers._navigate_to_canvas(page, pipeline_id)` is the existing shared
  navigation helper — reuse it, don't re-navigate manually.
- Live-confirmed numeric example (2026-08-08, Decision+3-Printer pipeline,
  1400x1000 viewport): Fit View baseline `translate(12.9193px, 348.199px)
  scale(0.118012)` -> Zoom In -> scale increases -> drag (+100,+150) ->
  `translate(112.919px, 498.199px) scale(<unchanged by pan>)` -> Fit View
  -> back to the EXACT baseline. Use relative/delta assertions in the test
  (don't hardcode these exact pixel values — they depend on node layout and
  viewport size, which differ for the `pipeline_llm_code_end` fixture's
  3-node layout); the pattern (scale increases on zoom, translate shifts by
  the exact drag delta on pan, Fit View is an idempotent deterministic
  reset) is what's being asserted, not these specific numbers.
