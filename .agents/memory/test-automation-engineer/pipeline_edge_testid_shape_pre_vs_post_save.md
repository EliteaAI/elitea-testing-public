---
name: Pipeline edge testid shape differs pre-Save vs post-Save
description: A drag-created edge's data-testid carries a ReactFlow handle-id suffix (no --- separator) until Save+reload re-parses it from YAML
type: feedback
---

## What happened (ELITEA-2047 implementation, 2026-08-08)

After `connect_nodes(code_id, printer_id)` on an UNSAVED pipeline, the new
edge's real `data-testid` was
`rf__edge-xy-edge__Code 1source-Printer 1target` — NOT the clean
`rf__edge-xy-edge__Code 1---Printer 1` shape `PipelineDetailPage.EDGE_TESTID`
/ `wait_for_edge()` / `edge_testid_present()` / `get_edge_locator()` expect.
`wait_for_edge()` timed out at 0 matches (24 retries) despite the edge
being genuinely present and correctly connecting the two nodes (confirmed
via a debug print of every `[data-testid^="rf__edge-"]` in the DOM).

This is a KNOWN, already-documented shape difference —
`wait_for_edge_present()`'s own docstring (added for a Decision-node case)
explains it: "their pre-save testid drops the `---` separator entirely,
e.g. `Decision 1nodes-bug_respondertarget` vs the post-reload
`Decision 1---bug_responder`". I didn't read that docstring closely enough
on the first pass and lost 2 debug cycles rediscovering it independently.

## Rule

- **Before Save** (right after a canvas drag-connect): use
  `wait_for_edge_present(source_id, target_id)` — loose prefix+substring
  match, tolerates both shapes.
- **After Save + a reload/re-navigate** (pipeline re-parsed from its saved
  YAML `transition:`/`interrupt_after:` fields): the clean `---`-only shape
  is live — `wait_for_edge()` / `EDGE_TESTID` / `get_edge_locator()` are
  valid again.
- If in doubt which shape is live, `wait_for_edge_present()` always works
  (it's the general-case tolerant matcher) — only reach for the exact-shape
  methods when you specifically need the literal testid string (e.g. keying
  a NEW dynamic testid off it, as `EDGE_LABEL` does for the interrupt pill).
