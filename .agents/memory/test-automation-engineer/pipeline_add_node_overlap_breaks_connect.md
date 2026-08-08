---
name: Pipeline add_node overlap breaks connect_nodes
description: Two back-to-back add_node() calls spawn the 2nd node exactly on top of the 1st on the ReactFlow canvas
type: feedback
---

## What happened (ELITEA-2047 implementation, 2026-08-08)

`PipelineDetailPage.add_node()` always drops a freshly-added node at the
SAME default canvas position — confirmed live via screenshot: calling
`add_node("Code")` then (after filling Code's Value field) `add_node("Printer")`
placed Printer 1 fully overlapping Code 1. `connect_nodes()` computes its
drag path from each node's handle `getBoundingClientRect()`; with both
nodes' handles occupying nearly the same screen position, the drag either
silently fails (`wait_for_edge`/`wait_for_edge_present` times out at 0
matches) or, at insufficient separation, still overlaps enough to fail.

## Fix

New `PipelineDetailPage.move_node(node_id, dx, dy)` — drags a node by pixel
offset from its own header area (not a handle, so it's a plain node-move,
not a connection-drag). Call it on the SECOND node right after
`wait_for_node_on_canvas()`, BEFORE `fit_view()` + `connect_nodes()`.

**Offset that worked:** `dx=450, dy=100` (horizontal separation, comfortably
clear of the node's full width ~320-400px). **What did NOT work:**
`dy=250` vertical-only — a Code node with its Value field filled in is
taller than 250px (~380-400px expanded), so the two nodes still overlapped
after the move. Prefer horizontal separation (`dx` alone) over vertical —
node card widths are more predictable than heights, which grow with filled
content (multi-line Value, chips, etc).

## When this applies

Any UI test that adds TWO OR MORE nodes via `add_node()` in sequence and
then needs to `connect_nodes()` them, when neither node already has an
edge anchoring a different layout position (tests seeding topology via
`PipelineAPI.create_pipeline_with_nodes()` / a fixture don't hit this —
only nodes added live through the canvas UI in the same test).
