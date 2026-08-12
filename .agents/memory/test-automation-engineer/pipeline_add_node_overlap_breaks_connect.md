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

## N>2 nodes (ELITEA-2016 implementation, 2026-08-09): don't scale offsets up

Placing 3+ nodes (Decision + 3 Printer branch targets) with LARGE,
monotonically-increasing offsets (tried `dx=350, dy=200*(i+1)` →
150/400/600px) made `fit_view()`/`fit_canvas_view()` zoom out so far to fit
the resulting bounding box that connection handles became sub-pixel —
`connect_nodes()`'s 15-step mouse drag missed them (`wait_for_edge_present`
timeout on a branch→END connect, AFTER the Decision→branch connects had
already succeeded at the same zoom — so it's a real precision miss, not a
uniform failure).

**Fix:** keep offsets modest and per-node-distinct regardless of node
count — `dx=280` constant, `dy=90*(i+1)` (90/180/270px total span) kept
`fit_view()`'s resulting zoom level large enough for every connect
(Decision→3 branches, 3 branches→END, Decision default_output→END — 7
edges total) to land. Call `fit_view()` ONCE, right after all nodes are
placed and moved, before any `connect_nodes()` call — not per-node.
Scaling offsets up "for more separation" is the wrong instinct; the
proven single-node pattern's magnitude (`dx=450,dy=100`) is closer to
correct than proportionally growing it per additional node.
