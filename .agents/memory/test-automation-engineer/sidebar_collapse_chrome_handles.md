---
name: Sidebar and BUCKETS panel collapse chrome
description: Both collapse toggles are one element with data-collapsed; sidebar nav items already carry testids
type: reference
aliases: [sidebar collapse, collapse toggle, icon-only sidebar, buckets panel collapse, sidebar-menu-item]
tags: [area/ui-chrome, area/artifacts]
created: 2026-08-21
updated: 2026-08-21
---

## The two collapse toggles (added ELITEA-1807, EliteaAI/EliteaUI@9062dff0)

- `artifacts-buckets-panel-toggle-button` — BUCKETS left panel (`BucketHeader.jsx`)
- `sidebar-collapse-toggle-button` — global nav sidebar (`[fsd]/widgets/sidebar-root/ui/Sidebar.jsx`)

Each is **one element whose icon flips** (`<<`↔`>>`, `<`↔`>`) with untagged SVG
icons, so state rides `data-collapsed="true|false"` on the same node — the PR
#581 shape. `BasePage.toggle_sidebar()` / `ArtifactsPage.toggle_buckets_panel()`
click and then `expect(...).to_have_attribute("data-collapsed", expected)`, so
they never need a sleep and return the post-toggle state.

## Collapse means two different DOM things — do not mix them up

- BUCKETS collapsed → heading / storage selector / footer are **unmounted**
  (`count == 0`, all gated on `!collapsed`), bucket ROWS stay in the DOM and go
  **invisible** (`display: collapsed ? 'none' : 'flex'`).
- Sidebar collapsed → entries stay **visible** (icons), only the label
  `<Typography>` unmounts (`showLabel={!sideBarCollapsed}`) → `text_content()` is `''`.

## Sidebar nav items already have testids

`SidebarBody.jsx` has long passed `testId={`sidebar-menu-item-${value}`}` —
values `chat, agents, pipelines, skills, toolkits, mcps, credentials,
applications, artifacts`. The 2026-08-02 artifacts digest row claiming "sidebar
entries have NO testid" was stale; corrected 2026-08-21. `Settings` and the
Agent HUB button got `sidebar-settings-button` / `sidebar-agent-hub-button` in
the same run (the former via a caller-supplied `testId` prop on the SHARED
`SidebarButton`).

Live labels: `toolkits` → **"Toolkits & Indexes"**, agent hub → **"Catalog"**
(case texts saying "Toolkits"/"Agent HUB" are stale — clarification
EliteaAI/elitea-testing-public#1619).

Related: [[project_briefing]]
