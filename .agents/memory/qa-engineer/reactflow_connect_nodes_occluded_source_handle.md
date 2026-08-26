---
name: ReactFlow connect_nodes silently fails when a neighbour node card overlays the source handle
description: Drag-connect starts a node-drag (or opens a MUI Select) on the overlapping neighbour instead of a connection — 10s wait_for_edge_present timeout, no error
type: feedback
---

`PipelineDetailPage.connect_nodes()` (`automation/pages/pipeline_detail_page.py:5913`)
computes the drag start as `sy = handleRect.y + handleRect.height - 2` — the handle's
**bottom 2px sliver**. At the zooms this suite actually runs at, that sliver is
routinely covered by the *next* node's card.

Measured live (localhost:5173, headless 1366x768, ELITEA-2016 / issue #1810, 2026-08-26):

- The pipeline flow pane is only **403 x 621 px** (left properties panel + right chat
  panel both open), so `fit_view()` settles at zoom **0.19-0.23**. A node card is
  ~89-106 px wide, a source handle only **4.5-5.4 px tall**.
- `document.elementsFromPoint(sx, sy)` at the computed start put the intended handle
  **5th** in the stack; index 0-2 were `MuiBox`/`react-flow__node` owned by the
  NEIGHBOURING printer node, overlapping by as little as **0.09 px**.
- Consequence: `mouse.down()` lands on the neighbour's card, ReactFlow starts a
  **node drag** of the neighbour (observed displacement (-182, -87) px), no edge is
  created, and `wait_for_edge_present()` times out after 10 s with a bare
  `Page.wait_for_function: Timeout` and no clue.

Two more things that make this expensive to diagnose:

1. **It is layout-nondeterministic.** `move_node(node, dx, dy)` displaces by SCREEN
   pixels while the canvas zoom drifts as nodes are added, so the same code produces
   different flow-space spacing run to run (zoom 0.225 -> handle clear -> PASS;
   zoom 0.188 -> 0.09 px overlap -> FAIL). Same machine, same target, same commit.
2. **`connect_nodes()`'s stray-menu cleanup checks `[role="menu"]` only.** A MUI
   `Select` popup (the Printer node's F-String/Variable/Fixed value-type control,
   `agentTaskTypeOptions` in `flowEditor.constants.js:152`) renders
   `role="listbox"`, so when the mousedown lands on it the menu is NEVER dismissed
   and stays open over the canvas, poisoning every later interaction.

**Before blaming the environment on a drag-connect failure**, probe
`document.elementsFromPoint(sx, sy)` at the computed start and print each element's
`closest('[data-id]')` owner. If the owner is not the source node, it is this, not
DEV, not timing, and not a product bug.
