---
name: Agent Hub category filters — pattern and reusable methods
description: Filter-chip click/selected/heading pattern; all use same AgentHubPage methods
type: reference
---

## Pattern (all single-category filters)

Agent Hub (Catalog) category filters follow a consistent pattern:

1. **Navigate** → `AgentHubPage.navigate()`
2. **Click filter chip** → `AgentHubPage.click_category_filter_chip(category_label)` (auto-slugifies)
3. **Verify selection state** → `AgentHubPage.is_category_filter_chip_selected(category_label)` (checks `data-selected="true"` attribute)
4. **Verify section header** → `AgentHubPage.is_category_section_visible(slug)` (slug is lowercase, hyphen-separated)
5. **Verify agent cards render** → `AgentHubPage.get_agent_card_count() >= 1`

## Pre-existing testids (all categories reuse same format)

- Filter chip: `catalog-agent-category-filter-chip-{slug}` (e.g., `catalog-agent-category-filter-chip-trending`, `catalog-agent-category-filter-chip-business-analyst`)
- Section heading: `catalog-category-heading-{slug}` (e.g., `catalog-category-heading-trending`)
- Agent cards: `catalog-agent-card-{id}` (dynamic per agent, shared pattern across all categories)

## Implemented cases (all follow this pattern)

- **ELITEA-2350** — page loads, all categories visible (p1)
- **ELITEA-2352** — Business Analyst filter (p2)
- **ELITEA-2353** — Multiple categories (p1)
- **ELITEA-2364** — My Liked filter (p1)
- **ELITEA-2366** — Trending filter (p2) ← this session
- **ELITEA-2367** — Empty state when no results (p1)

## Case-text drift (shared across all)

All category-filter cases mention a "reload category items" icon next to the section header → **does not exist in live product** (no render, no source code, confirmed via component grep). Asserts heading text only (reverse-masking guard). CLARIFICATION filed issue #1212.

## Key methods on AgentHubPage

```python
click_category_filter_chip(category_label: str, timeout: int = 10000)
  # Slugifies label automatically (e.g., "Business Analyst" → "business-analyst")

is_category_filter_chip_selected(category_label: str, timeout: int = 10000) -> bool
  # Checks data-selected="true" attribute, NOT Playwright's [active] marker (see memory entry
  # "a11y [active] = focus, not selection")

is_category_section_visible(category_slug: str, timeout: int = 10000) -> bool
  # Slug is LOWERCASED, HYPHENATED (NOT the display label)
  # E.g., is_category_section_visible("business-analyst"), NOT is_category_section_visible("Business Analyst")

get_agent_card_count() -> int
  # Returns count of currently-rendered cards (respects filtering)
```

## Implementation notes for future cases

1. **Slug derivation:** Page object's `_slugify_category()` matches EliteaUI's client-side logic: `lowercase, non-alnum runs → '-'`
2. **State assertion:** Use `data-selected` attribute via `is_category_filter_chip_selected()`, never Playwright's `[active]` (it reflects focus, not selection state)
3. **Heading verification:** Pass the SLUG (lowercase, hyphens) to `is_category_section_visible()`, not the display label
4. **Agent count:** No hardcoded expected count — just assert `>= 1` because the Catalog's agent list is live, mutable, shared data
5. **Console errors:** All tests use `capture_console_errors()` to verify zero noise during filter interaction
6. **Allure.step wrapping:** Required for every step in the case — 5-6 steps per category-filter case
