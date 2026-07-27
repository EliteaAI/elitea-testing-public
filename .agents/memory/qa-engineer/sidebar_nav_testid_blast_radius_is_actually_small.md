---
name: Sidebar nav testid blast radius is actually small
description: EliteaUI's SidebarMenuItem has exactly one caller (SidebarBody.jsx's single .map() loop) which already threads a per-item optional tourId/data-tour prop — adding a per-item testId prop is a ~3-line change, not a broad shared-component refactor. Check before accepting a "too broad to testid" excuse for sidebar nav items.
type: reference
---

## What

`EliteaUI/src/[fsd]/widgets/sidebar-root/ui/SidebarMenuItem.jsx` is rendered
from exactly ONE call site: `SidebarBody.jsx`'s single `sections.map(section
=> section.map(i => <SidebarMenuItem ... tourId={i.tourId} />))` loop. Each
nav item (`chat`, `agents`, `artifacts`, etc.) is a plain object literal in a
`sections` array with per-item fields (`value`, `label`, `url`, `tourId`,
...) — `tourId` already threads through to `SidebarMenuItem` and renders as
`data-tour={tourId}` on the `<ListItem>`. `SidebarBody.jsx` *also* already
has a literal `data-testid="sidebar-toggle"` on an adjacent `IconButton` a
few lines above the loop — this file is not a "no testid zone."

## Why it matters

ELITEA-1809's AFS (`test-specs/artifacts/l3_duplicate-bucket-name-not-allowed_ELITEA-1809.md`
§ Implementer Amendments #1) justified NOT adding a testid to the sidebar's
Artifacts nav link — instead substituting a direct URL navigation for the
case's literal "click Artifacts in the sidebar" step — with: "adding one
would require threading a `testId` prop through `SidebarBody.jsx`'s render
loop, which touches every sidebar nav item... a broad, high-blast-radius
shared-component change." Reading the actual source shows this is
overstated: the `tourId` field is the existing precedent for exactly this
shape of change, and it's ~3 lines (one field in the `artifacts` object,
one prop passthrough already-pattern-matched by `tourId`, one
`data-testid={testId}` on the render). The practical decision (skip the
sidebar click, use direct nav) still held up under review because it
matches this whole repo's pre-existing, universal convention — zero
sidebar-click-based navigation exists anywhere in the page-object layer,
every `navigate_to_X()` method already uses direct URL nav — so it wasn't
worth blocking on. But the STATED reason was wrong, and a future case that
specifically needs to test the sidebar link itself (e.g. a case about
sidebar nav/permissions/highlighting) should not accept "too broad" as a
reason to skip adding the testid — it's cheap.

## Where

- `EliteaUI/src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx` — the single
  `.map()` render loop + the `sections` array of per-item objects + the
  existing `data-testid="sidebar-toggle"` precedent.
- `EliteaUI/src/[fsd]/widgets/sidebar-root/ui/SidebarMenuItem.jsx` — the
  sole consumer; already destructures and renders `tourId` → `data-tour`.
