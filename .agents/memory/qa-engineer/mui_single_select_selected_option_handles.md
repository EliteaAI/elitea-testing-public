---
name: MUI single-select — how to handle the selected option (checkmark) in EliteaUI
description: Shared SingleSelectMenuItem renders the checkmark with no testid; customRenderOption already receives isSelected, so state belongs on the feature's own option Box as data-selected
type: reference
aliases: [checkmark indicator, selected option, SingleSelectMenuItem, project dropdown checkmark, select-option testid]
tags: [area/locators, area/mui]
created: 2026-08-24
updated: 2026-08-24
---

## The shape (verified live 2026-08-24, EliteaUI `automation/testids`)

Every single-select in EliteaUI renders through `src/[fsd]/shared/ui/select/SingleSelectMenuItem.jsx`:

- The MUI `MenuItem` gets `data-testid={option.testId ?? \`select-option-${option.value}\`}` — for
  the project dropdown that resolves to `select-option-399`, i.e. a **numeric, environment-specific
  backend id**. Never bind a spec to it.
- The selected row additionally renders `<ListItemIcon><CheckedIcon/></ListItemIcon>` — **no
  testid**. This is the visible "checkmark indicator" TMS cases keep asking about.
- `renderContent()` calls `customRenderOption(option, isSelected)` — **the second argument already
  exists** and most feature call sites ignore it.

## What that means for a case asserting "selected / checkmark"

1. Selection **state** goes on the feature's own option node as a `data-*` attribute — e.g.
   `data-selected={isSelected ? 'true' : 'false'}` on the existing
   `project-selector-option-{label}` Box in `SidebarProjectSelect.jsx`. Attribute-only, no new DOM
   node, no hook; matches `.agents/testing.md` § Locator policy (state via `data-*`, never a
   state-named testid). Handle: `[data-testid="project-selector-option-X"][data-selected="true"]`.
2. The **icon itself** needs a testid in the SHARED component, so the name must be generic —
   `select-option-selected-icon`, never `project-selector-…` (shared components never carry
   feature-scoped testids). It renders once per open single-select, so `to_have_count(1)` is a real
   invariant (two selected rows = a defect a per-row check cannot see).
3. `aria-selected` / `Mui-selected` exist on the MenuItem but are only reachable through the
   env-specific `select-option-{id}` handle — not a usable primary handle.

Related: [[_surface digest for onboarding]] · first used in the ELITEA-2240 AFS.
