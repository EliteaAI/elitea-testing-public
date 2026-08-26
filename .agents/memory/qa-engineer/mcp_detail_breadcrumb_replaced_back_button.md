---
name: MCP detail page has a breadcrumb trail, not a back button
description: /mcps/all/:id renders Breadcrumbs instead of BackButton — the branch is route-based, so back-button never exists there
type: reference
aliases: [back button MCP detail, breadcrumb-item, breadcrumbs testid, EditToolkit back arrow, detail to list navigation]
tags: [area/mcp, area/toolkits, type/handle]
created: 2026-08-24
updated: 2026-08-24
---

## The fact

`src/pages/Toolkits/EditToolkit.jsx:390-403` renders **either** `<Breadcrumbs/>` **or**
`<BackButton/>` + the `toolkit-detail-title` `<Typography>` — never both.
`useHasBreadcrumbTrail()` (`src/[fsd]/shared/lib/hooks/useBreadcrumbTrail.hooks.js:35`)
decides purely from the **route** (`resolveBreadcrumbTrail(pathname).length > 0`), and
`/mcps/all/:id` declares a trail (`breadcrumb.constants.js:48`).

⇒ **`data-testid="back-button"` never exists on the MCP detail page**, regardless of how the
user got there (card click and deep link both verified live 2026-08-24, project 399).
Verified by DOM probe (`querySelector` → `null`) AND by reading the branch condition.

`toolkit-detail-title` still exists but is now emitted by the breadcrumb constants as the last
crumb — same testid, different owner.

| Handle | Testid | Where |
|---|---|---|
| Trail nav | `breadcrumbs` | detail pages only — **absent on `/mcps/all`** |
| Parent link ("MCPs") | `breadcrumb-item` | exactly 1 on the MCP detail page |
| Current crumb | `toolkit-detail-title` | last crumb, not a link |

All three on `origin/main` ✓. Breadcrumbs are recent (`1facc163`, EL-6293, 2026-08-21) — same
redesign era as EL-6277's Test-route refactor.

## Why it matters

Any case text saying "click the back arrow on the detail page" is stale for this surface.
`AgentDetailPage.back_button` / `SkillDetailPage.back_button` still bind `back-button` for
THEIR routes — do not generalise in either direction without checking
`resolveBreadcrumbTrail(pathname)` for the route in question.

Filed as CLARIFICATION
[#1731](https://github.com/EliteaAI/elitea-testing-public/issues/1731).

Related: [[mcp_list_filter_survives_detail_roundtrip_scroll_does_not]]
