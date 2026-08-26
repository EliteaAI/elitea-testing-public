---
name: ReactFlow pipeline canvas — drag geometry rules (hit-test the handle, fit the drag to the pane)
description: connect_nodes/move_node on the pipeline flow editor; why screen-px offsets and bottom-sliver drag starts fail silently
type: feedback
---

Two coupled traps on `PipelineDetailPage`'s ReactFlow canvas
(`automation/pages/pipeline_detail_page.py`). Both fail **silently** — no
exception, just a `wait_for_edge_present` timeout 10 s later. Measured live
on localhost:5173, headless, 2026-08-26 (ELITEA-2016 / issue #1810).

**1. A drag start inside a handle must be HIT-TESTED, not computed.**
The old `connect_nodes()` started at `handleRect.y + height - 2` — the
handle's bottom 2 px sliver. Source handles are only ~2-8 px tall at the
zooms this suite runs at, and that sliver is routinely covered by a
neighbouring node's card (a **0.09 px** horizontal overlap was enough).
`mouse.down()` then grabs the neighbour, ReactFlow starts a NODE drag, no
edge is created, and the neighbour is displaced (measured: -83, -152 px).
Fix (merged): walk candidate points inside the handle's own rect, centre
first, and take the first whose `document.elementFromPoint(...)
.closest('[data-handleid]')` really is that handle; raise naming the
occluder if none is. In practice the centre always wins.

**2. A node drag may not span more than ~35% of the flow pane.**
The flow pane is only ~**403 x 621 px** with both side panels open, while a
node card is ~**471 x 237 FLOW units**. At the editor's default zoom 0.75
barely one card width is on screen, so any real layout needs a drag longer
than the pane — and once the pointer nears a pane edge ReactFlow's
`autoPanOnNodeDrag` pans the viewport, adding an arbitrary extra
displacement. Symptom: nodes flung far apart, `fit_view()` settling at
zoom ~0.1, every handle ~2 px tall. `move_node()` takes SCREEN px, so its
flow-space result also drifts with whatever zoom happens to be in force.
Fix (merged): `move_node_by_flow_offset()` takes FLOW units, zooms out
until `offset * scale` fits ~35% of the pane, then converts.

**Diagnosis shortcut:** before blaming DEV, timing or a product bug for a
drag-connect failure, evaluate `document.elementsFromPoint(sx, sy)` at the
computed start and print each element's `closest('[data-id]')`. If the top
owner is not the source node, it is this.

**Bonus:** `connect_nodes()`'s stray-popup cleanup used to probe
`[role="menu"]` only, so a MUI **Select listbox** opened by a misfired
mousedown was never dismissed and stayed over the canvas. It now uses
`is_popup_menu_visible()` (`POPUP_MENU_TESTIDS`) OR `SELECT_OPTION_PREFIX`
— both already existed in the same file. Escape stays CONDITIONAL: sending
it unconditionally regressed `test_three_node_chain` (pristine-HEAD control
confirmed it), because it fires after *successful* connections too.
