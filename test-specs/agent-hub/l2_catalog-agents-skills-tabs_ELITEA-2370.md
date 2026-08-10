---
case_id: ELITEA-2370
title: "Catalog — default view opens on Agents tab and user must click Skills to navigate to Skills"
priority: high
type: functional
module: agent-hub
feature: Catalog
status: ready-for-automation
afs_format: 2
---

# ELITEA-2370 AFS — Catalog Default Tab & Tab Navigation

**TMS Case:** [ELITEA-2370](../../../.agents/automation/agent-hub-2351w2/cases/ELITEA-2370.md)  
**Module:** agent-hub · **Priority:** high · **Type:** functional

**Objective:** Verify that Catalog page opens with Agents tab as the default, and clicking the Skills tab correctly switches the view.

---

## Preconditions

- User is logged in to the Elitea platform (satisfied by `auth_state` fixture on localhost)
- Navigation to `/elitea-catalog` is accessible

---

## Test Data

| Field | Value |
|-------|-------|
| (none required) | — |

---

## Coverage Map

| Axis 1 — AFS Coverage | Original-Case Element | Disposition | Assertion/Method |
|---|---|---|---|
| Page load | "Navigate to Catalog" (step 1) | navigate | `assert_page_loads()` — verify page title and heading |
| Default tab state | "Agents tab selected by default" (steps 2–3) | asserted | `assert_agents_tab_selected()` — verify `[role='tab']` with "Agents" text has `aria-selected=true` |
| Agents content | "Main content area displays Agents content" (step 5) | asserted | `assert_agents_content_visible()` — verify agent card grid is present |
| Skills tab visibility | "Skills tab visible with icon" (step 4) | asserted | `assert_skills_tab_visible()` — verify `[role='tab']` with "Skills" text is present and enabled |
| Tab click | "Click Skills tab" (step 6) | navigate | `click_skills_tab()` — click the Skills tab element |
| Tab state after click | "Skills tab becomes active" (step 7) | asserted | `assert_skills_tab_selected()` — verify Skills tab has `aria-selected=true` |
| Content switch | "Main content switches to Skills" (step 8) | asserted | `assert_skills_content_visible()` — verify Skills content replaces Agents content |
| Right panel filters | "Right panel shows FEATURED and CATEGORIES" (step 9) | asserted | `assert_filter_panel_visible()` — verify category filter rail and filter chips are present |

---

## Concrete Handles

| Element | Selector | Handle Type | Status | Notes |
|---|---|---|---|---|
| Page heading | `[data-testid="catalog-page-heading"]` | testid | on-automation/testids | Text: "Welcome to ELITEA Catalog!" |
| Agents tab | `[role="tab"]:has-text("Agents")` | role + text | pre-existing | aria-selected toggles between true/false |
| Skills tab | `[role="tab"]:has-text("Skills")` | role + text | pre-existing | aria-selected toggles between true/false |
| Agent card grid | `[data-testid^="catalog-agent-card-"]` | testid | pre-existing | Multiple cards; count varies (≥1) |
| Category filter chips | `[data-testid^="catalog-agent-category-filter-chip-"], [data-testid^="catalog-skill-category-filter-chip-"]` | testid | pre-existing/pending | Right-panel filter rail on Skills tab |
| Right panel container | `[class*="category"], [class*="sidebar"], [class*="filter"]` | class-based | observed | Layout element for filter section |

---

## Known Defects & Clarifications

**Case-text drift (recurring in ELITEA-2350+ family):**  
Case text refers to "Agent HUB", but live product labels it "Catalog" everywhere (sidebar, page heading, browser title). No UX defect — just terminology difference.

**Right panel on Skills tab:**  
The digest notes that the Skills tab features a category filter rail in the right panel. This was confirmed to exist and be interactive during live exploration (ELITEA-2350+ family diagnostics). If the filter panel is not visible under all conditions, cite [#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212) (recurring "no reload icon" / "missing filter panel" family pattern).

---

## Axis 2 — Scope & Additions

**No additions beyond original case scope.** All assertions directly map to original-case steps and expected results. No helper setup beyond `navigate_to_catalog()`.

---

## Classification

**Status: `ready-for-automation`**  
- All steps executed live and passed
- Handles are pre-existing or on `automation/testids`
- No blocking ambiguities or product defects
- One new test per case

---

## Implementation Notes

- **Framework:** Playwright + pytest (follow `.agents/testing.md`)
- **Page object:** `AgentHubPage` (extend existing; add `click_skills_tab()` method if not present)
- **Markers:** `@pytest.mark.p2` (priority: high → p2) + `@pytest.mark.agent_hub` + `@pytest.mark.regression`
- **Run command:** `pytest tests/ui/agent-hub/test_catalog_navigation.py::TestCatalogTabs::test_default_agents_and_skills_switch -v`
- **Fixture:** `auth_state` (login skipped on localhost via `VITE_DEV_TOKEN`)

---

## References

- **AFS format:** spec-format.md v2
- **Surface digest:** `test-specs/agent-hub/_surface.md` (current, 2026-08-10)
- **Related cases:** ELITEA-2350 (team page variant), ELITEA-2366 (Trending category filter), ELITEA-2362 (Skills tab + agent chip)
- **Known issues:** [#1208](https://github.com/EliteaAI/elitea-testing-public/issues/1208) (page naming), [#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212) (reload icon)
