---
name: MCP node input-mapping Type select has no testid; scope by row label
description: Pipeline MCP node mapping Type/Variable-value selects: no testid on DEV, use ScopedLocator xpath keyed by display label
type: reference
---

BaseToolNode.jsx gives `typeTestIdPrefix` to Toolkit nodes only, so MCP-node rows expose only `id="simple-select-Type"` (duplicated per row). Handle: `ScopedLocator(xpath=".//div[.//span[normalize-space(text())='{}'] and count(.//*[@id='simple-select-Type'])=1]//*[@id='simple-select-Type']")` within `pipeline-node-panel-basic-section`, arg = display label (raw key with first letter capitalised). Variable-mode Value select is a `role=combobox` in the same row (id `simple-select-[object Object]`); the text Value input disappears in that mode. Methods live on `PipelineDetailPage` (`select_mcp_node_input_mapping_type`, `…_variable_value`). If DEV ever adds the MCP testid, swap to rung 1.

Env gotcha: a shell without `APP_PREFIX=/app` (no `automation/.env.test` present) makes every pipeline spec 404 at navigate (`wait_for_detail_page_load` timeout) — not a product regression.
