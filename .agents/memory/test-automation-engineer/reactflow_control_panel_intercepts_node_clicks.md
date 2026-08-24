---
name: ReactFlow Control Panel intercepts clicks on a node's lower config rows
description: rf__controls (bottom-left) steals the pointer from Input-mapping selects; fix with move_node(dx=450)
type: reference
aliases: [rf__controls intercepts, Fit View intercepts pointer events, node config click intercepted]
tags: [area/pipelines, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## Symptom

`Locator.click: Timeout … exceeded` with Playwright naming
`<div data-testid="rf__controls">` / its "Fit View" button as the subtree that
"intercepts pointer events". Hits the LOWER rows of a node's inline config
(Input-mapping Type/Value selects), never the upper ones — a freshly-added node
spawns just above the bottom-left control panel and grows down over it once the
Input-mapping section renders.

## Fix

`pipeline_page.move_node(node_id, dx=450, dy=0)` immediately after
`wait_for_node_on_canvas(...)`. Precedent already in the suite:
`test_pipeline_interrupt_before_after_toggles.py:87`. Do NOT reach for
`click(force=True)` — the event still lands on the topmost element.

Related: [[mcp_node_input_mapping_variable_branch]]
