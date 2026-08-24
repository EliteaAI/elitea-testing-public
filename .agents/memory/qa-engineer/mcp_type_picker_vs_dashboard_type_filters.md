---
name: MCP type picker vs MCP dashboard — two different "Local/Remote" filters
description: Two unrelated Local/Remote filters exist on the MCP surface; conflating them wastes a probe and mis-files defects
type: reference
aliases: [mcp type picker, category-filter-tab, tags-panel-chip, choose the MCP type, allowEmptyCategory]
tags: [area/mcp, type/ui-quirk]
created: 2026-08-24
updated: 2026-08-24
---

## The two filters are NOT the same component

| Surface | Component | Chip testid | Filtering |
|---|---|---|---|
| `/mcps/all` dashboard | `components/Categories.jsx` | `tags-panel-chip-{Type}` | server-side (`?tags[]=`, `toolkit_type=`); has `tags-panel-clear-all` |
| `/mcps/create` type picker | `[fsd]/shared/ui/filter/CategoryFilter.jsx` | `category-filter-tab` — **shared by BOTH chips, non-unique, no state attribute** | pure client-side re-grouping, **no network request**, no clear-all |

Dashboard bug #1737 ("Local chip doesn't filter") does **not** apply to the type picker,
and the type-picker clarification #1742 does not apply to the dashboard. They are
siblings, never duplicates.

## The type picker's Local section vanishes under its own Local filter

`ToolkitTypeSelector.jsx` passes `allowEmptyCategory={isMCP}`; `GroupedCategory.jsx:56-62`
keeps an empty category **only while `!selectedCategories.length`**. So selecting `Local`
unmounts the Local heading + empty-state message + Documentation link and renders
`catalog-no-results-title` = `No MCPs found` instead. Coherent-by-design ⇒ CLARIFICATION
(#1742), not a bug. Chips are also **multi-select** with no clear-all.

Related: [[mcp_detail_form_raw_json_projection]]
