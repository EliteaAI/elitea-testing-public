---
name: /mcps/create type-picker pollutes console-error assertions
description: Seeding an MCP through the UI create flow trips `assert not console_errors` on known defect #656 — register the listener after setup
type: feedback
aliases: [CategorySection key prop, ToolkitTypeSelector warning, console errors mcp create]
tags: [area/ui, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

The `/mcps/create` toolkit-type picker emits a React dev-mode `console.error` on every mount:
`Each child in a list should have a unique "key" prop` from
`src/[fsd]/shared/ui/category/CategorySection.jsx` via `ToolkitTypeSelector.jsx`.
Already tracked as elitea-testing-public#656 (`[MINOR][ELITEA-1868]`).

Consequence: any MCP test that seeds its own MCP through the **UI create flow** and also asserts
`assert not console_errors` fails on its own scaffolding, not on the surface under test. Register
the console listener **after** setup (documented in the test) — the case's own flow starts at the
detail page. Not masking: the defect stays filed, and the case's steps stay fully covered.

Related: [[dotmenu_menu_item_testids_and_unmount]]
