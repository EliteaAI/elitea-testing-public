---
name: MCP dashboard Types filter (Local/Remote)
description: Chips are hardcoded, state lives only in a CSS class, and the Local chip does not filter (#1737)
type: reference
aliases: [tags-panel-chip, Types filter, MCP type filter, tags-panel-clear-all]
tags: [area/mcp, type/handle-cache]
created: 2026-08-24
updated: 2026-08-24
---

## Handles

- `tags-panel-chip-{Local|Remote}` (dynamic, `Categories.jsx:336`) — shared with the
  Credentials Types panel (`CredentialsListPage.TYPE_FILTER_CHIP`). On `main`.
- `tags-panel-clear-all` (`Categories.jsx:299`) — rendered ONLY while a chip is
  selected, so its presence is the product's own "a filter is active" signal;
  unmounted otherwise (`to_have_count(0)`).

## Gotchas

- On `/mcps/all` the chip list is **hardcoded** to Local + Remote (`useLoadToolkits`
  `tagList`, `isMCP` branch) — NOT data-derived, unlike Credentials' panel.
- Chip selection state exists ONLY as an emotion class hash (`css-1oy09ev` selected
  vs `css-16qy5qb` idle) — no `aria-selected`, no `data-*`. Assert via the URL param
  `?tags[]=<Name>` plus `tags-panel-clear-all`.
- The chips mount LATER than `McpListPage.navigate()`'s load signal — clicking
  immediately fails with "does not match any elements". Wait for the chip.
- Type filtering is server-side (`&toolkit_type=mcp`); the search box on the same
  page is client-side.

## Defects / environment

- **#1737** — the `Local` chip applies visibly but does not filter: empty resolved
  type set ⇒ query sent with no `toolkit_type` ⇒ all Remote MCPs stay listed.
- **#1738** — no Local (pre-built `mcp_*`) MCP exists or can be created in DEV;
  `/mcps/create` offers only "Remote MCP". Any case naming ADO/FileSystem/
  PlaywrightMCP is unsatisfiable here.

Related: [[project_briefing]]
