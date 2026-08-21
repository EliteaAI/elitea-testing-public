---
name: Sidebar nav entries are permission/flag filtered
description: Hardcoded sidebar-item lists in tests are env/project-dependent — SidebarBody.jsx filters entries by permissions and the MCP flag
type: reference
aliases: [sidebar menu items, sidebar-menu-item testid, SidebarBody filter, MCPs missing from sidebar]
tags: [area/navigation, type/gotcha]
created: 2026-08-21
updated: 2026-08-21
---

## What

`EliteaUI/src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx` (~lines 184-203,
verified on `origin/automation/testids` 2026-08-21) filters the nav sections
before render:

- `mcps` is dropped when `isMcpVisible` is false (feature flag);
- `skills` is dropped on a **public** selected project without
  `PERMISSIONS.skills.publish`;
- every remaining entry is dropped unless the user holds one of
  `PERMISSION_GROUPS[value]` (with `mcps` mapped to `toolkits`).

Each surviving entry gets `testId={`sidebar-menu-item-${i.value}`}` and
`showLabel={!sideBarCollapsed}` — so on collapse the entry stays visible and only
its label `<Typography>` unmounts (`SidebarMenuItem.jsx:44,67`).

## Why it matters to a reviewer

A test that hardcodes the full nav list and asserts each entry visible (e.g.
ELITEA-1807's `SIDEBAR_NAV_ENTRIES`) is **green on the local dev project and can
red on another project/env** for permission reasons, not a product defect. When
reviewing such a test, flag the coupling; when triaging a red, check the project's
permissions and the MCP flag before calling it a regression.

Related: [[579_claim_check_component_already_forwards_testid_prop]]
