---
case_id: ELITEA-2366
title: Agent Hub — Trending category displays agents
status: ready-for-automation
priority: p2
feature: agent-hub
surfaces: ui
type: functional
tags: [agents, catalog, trending]
---

# ELITEA-2366 — Agent Hub — Trending category displays agents

**Status:** `ready-for-automation` — Live product execution complete. All steps testable on live surface.

---

## Objective

Verify that Agent Hub (Catalog) Trending category displays agents. The section loads successfully when the Trending filter is selected, agents are shown in the correct category section, and the section header is visible.

---

## Preconditions

- User is logged in to the Elitea platform
- Catalog page is accessible at `/elitea-catalog`

---

## Coverage Map

### Axis 1 — Case Flow Steps

| Step | Coverage | Disposition | Evidence |
|------|----------|-------------|----------|
| Navigate to Agent Hub (Catalog page) | page load, route `/elitea-catalog` | observed | ✓ heading "Welcome to ELITEA Catalog!" visible |
| Click Trending category filter chip | filter activation, state change | observed | ✓ filter applies, page shows only Trending section |
| Verify Trending filter is active | filter state assertion | asserted | ✓ `data-selected="true"` on filter chip |
| Verify agents displayed under Trending | content render, card visibility | asserted | ✓ agent cards visible |
| Verify section header "Trending" appears | header render, section structure | asserted | ✓ section header "Trending" visible |

---

## Concrete Handles

All testid-based per `.agents/testing.md`.

| Handle | Selector | Provenance | Status |
|--------|----------|-----------|--------|
| Catalog heading | `[data-testid="catalog-page-heading"]` | ELITEA-2075 | ✓ on automation/testids |
| Trending filter chip | `[data-testid="catalog-agent-category-filter-chip-trending"]` | ELITEA-2352 | ✓ on automation/testids |
| Trending section header | `[data-testid="catalog-category-heading-trending"]` | pre-existing | ✓ on automation/testids |
| Agent card (by ID) | `[data-testid="catalog-agent-card-{id}"]` | ELITEA-2075 | ✓ on automation/testids |

---

## Known Findings

### CLARIFICATION — Case-text drift: "Reload category items" icon

The case text claims a "Reload the category items" icon next to the section header. **This icon does NOT exist on the live product.** The section header renders only the category name ("Trending"), with no adjacent icons. 

Confirmed via:
- Live DOM inspection (2026-08-10)
- Source: `AgentCategorySection.jsx` renders `Typography` title only
- Grep for reload icons: 0 matches
- Filed: [#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212)

**This spec will NOT assert the reload icon.** Case-text correction noted for future reference.

---

## Execution Plan

- Single test: Navigate → Click Trending filter → Assert header + agents visible
- No seed/cleanup needed (uses live stable data)
- Assertions: Section header present, agents > 0, filter `data-selected="true"`

