---
name: Pipeline Add-node menu — Custom hidden since EL-6616
description: The canvas "+" picker lists 10 types (no Custom) since EliteaAI/EliteaUI@0cd5e792; specs that add a Custom node via the menu cannot, but YAML-seeded Custom nodes still render
type: project
aliases: [custom node deprecated, add node menu 10 items, EL-6616, pipeline-add-node-menu-item-custom]
tags: [type/project, area/pipelines]
created: 2026-09-16
updated: 2026-09-16
---

## The fact
`AddNodeMenu.jsx` `getVisibleNodeTypes()` filters `PipelineNodeTypes` against
`DeprecatedConstants.DeprecatedOrInvisibleNode`; EL-6616 (EliteaAI/EliteaUI@0cd5e792, 2026-09-11,
on `main` and `automation/testids`) added `Custom` to `DeprecatedNodes`. Live-verified 2026-09-16 on
DEV and localhost: menu = `Agent, Code, Decision, Human-in-the-loop, LLM, MCP, Printer, Router,
State modifier, Toolkit` (10, DOM order); `[data-testid="pipeline-add-node-menu-item-custom"]` count 0.

## Consequences
- `PipelineDetailPage.add_node("Custom")` and `select_add_node_menu_item("custom")` cannot succeed —
  ELITEA-2036 (`test_pipeline_custom_node_configuration.py`, #2319) dies at its Step 1 for this reason.
- A Custom node seeded via YAML (`nodes: [{id: "Custom 1", type: custom, transition: END}]`,
  `PipelineAPI.create_pipeline_with_nodes`) still renders, with a "Deprecated!" badge whose tooltip is the
  authored EL-6616 tip (`NodeCardHeader.jsx:307` → `DeprecatedTips[type]`). That is the honest way to
  reach an existing Custom node if a case still needs one.
- Absence assertion shape: `ADD_NODE_MENU_ITEM_BY_TYPE.format("custom")` + `to_have_count(0)`, asserted
  AFTER the positive menu/list check (EL-6460 breadcrumb precedent) — no new testid or field needed.

Related: [[dev_repro_without_secrets_in_context]] · [[ui_flow_assumption_gate]]
