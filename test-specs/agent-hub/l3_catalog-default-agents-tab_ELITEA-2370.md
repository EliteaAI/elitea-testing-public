---
tms_case_id: ELITEA-2370
title: "Catalog — default view opens on Agents tab and user must click Skills to navigate to Skills"
priority: 3
feature: agent-hub
status: ready-for-automation
family_afs: false
---

# ELITEA-2370: Catalog default view and tab navigation

**Objective:** Verify the Catalog page loads with Agents tab selected by default, and that clicking the Skills tab activates it and switches the view content.

## Preconditions

- User is authenticated and logged in to Elitea.

## Test Data

| Field | Value |
|-------|-------|
| (none) | — |

## Coverage Map — Axis 1 (Original case requirements)

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Click "Catalog" in left sidebar | Page navigates to Catalog | Step 1 | `chat_page.goto_catalog()` or direct navigation | asserted |
| "Welcome to ELITEA Catalog!" page loads | Page heading visible and correct | Steps 2 | `page_heading.to_have_text()` or `get_text()` | asserted |
| Agents tab selected by default | Agents tab aria-selected=true | Step 3 | `agents_tab.get_attribute("aria-selected") == "true"` | asserted |
| Skills tab visible + lightning bolt icon | Skills tab visible with icon | Step 4 | `skills_tab.is_visible()` + icon query | asserted |
| Main content displays Agents content by default | Agents tab content (e.g. cards or empty state) rendered | Step 5 | main element contains "agent" text OR "no agents" text | asserted |
| Click the "Skills" tab | Skills tab receives click | Step 6 | `skills_tab.click()` | asserted |
| Skills tab becomes active/highlighted | Skills tab aria-selected=true after click | Step 7 | `skills_tab.get_attribute("aria-selected") == "true"` | asserted |
| Main content switches to Skills | Skills tab content rendered (e.g. skill cards or empty state) | Step 8 | main element contains "skill" text | asserted |
| Right panel shows FEATURED + CATEGORIES filters | Filter-rail chips visible on right (Trending, My Liked, category chips) | Step 9 | `filter_chips.count >= 11` (FEATURED 2 + CATEGORIES 9) | asserted |

## Coverage Map — Axis 2 (Observations beyond the case)

| Observable | Why | Where |
|---|---|---|
| Agents tab testid is `catalog-agents-tab` | Stable handle for test targeting | `catalog-agents-tab` locator |
| Skills tab testid is `catalog-skills-tab` | Stable handle for test targeting | `catalog-skills-tab` locator |
| Page heading testid is `catalog-page-heading` | Stable handle for verifying page load | `catalog-page-heading` locator |
| Filter chips use `catalog-agent-category-filter-chip-*` in Agents view | Testid pattern for right panel | Agents tab assertion |
| Filter chips use `catalog-skill-category-filter-chip-*` in Skills view | Different testid prefix per tab (feature-scoped) | Skills tab assertion |
| 11 total filter chips visible (2 FEATURED + 9 CATEGORIES) | Expected count per project's configured filters | Right panel count check |
| Main content text contains "agent" or "skill" depending on active tab | Tab switching reflected in DOM content | Primary content-switch signal |

## Preconditions Detail

User must be authenticated via `auth_state` fixture (localhost login skipped via `VITE_DEV_TOKEN`).

## Steps

### Step 1 — Navigate to Catalog

**Action:** Navigate to `/elitea-catalog` (or click "Catalog" in sidebar if available).

**Expected:** Page loads successfully.

### Step 2 — Verify page heading

**Action:** Locate element with `data-testid="catalog-page-heading"`.

**Expected:** Text reads "Welcome to ELITEA Catalog!"

### Step 3 — Verify Agents tab selected by default

**Action:** Locate `[data-testid="catalog-agents-tab"]`, read `aria-selected` attribute.

**Expected:** `aria-selected="true"`

### Step 4 — Verify Skills tab visible with icon

**Action:** Locate `[data-testid="catalog-skills-tab"]`, check visibility and presence of child icon (svg or Icon component).

**Expected:** 
- Element is visible (not hidden/display:none)
- Contains an icon child element

### Step 5 — Verify main content displays Agents content

**Action:** Locate `main` element, read full text content.

**Expected:** Text contains "agent" (case-insensitive) or "no agents" (empty state is still Agents-tab content).

### Step 6 — Click Skills tab

**Action:** Click `[data-testid="catalog-skills-tab"]`.

**Expected:** Click succeeds, page responds to interaction.

### Step 7 — Verify Skills tab active after click

**Action:** Read `aria-selected` attribute on `[data-testid="catalog-skills-tab"]` after click.

**Expected:** `aria-selected="true"`

### Step 8 — Verify main content switches to Skills

**Action:** Read text content of `main` element after Skills tab click.

**Expected:** Text contains "skill" (case-insensitive) or "no skill" (Skills empty state).

### Step 9 — Verify right panel shows FEATURED + CATEGORIES filters

**Action:** 
1. Count all `[data-testid^="catalog-agent-category-filter-chip-"]` in Agents tab view (11 expected).
2. Count all `[data-testid^="catalog-skill-category-filter-chip-"]` in Skills tab view (11 expected).
3. Verify "FEATURED" and "Categories" section headers visible in right panel.

**Expected:** 
- Agents view: ≥11 agent-category filter chips visible.
- Skills view: ≥11 skill-category filter chips visible.
- Both views show "FEATURED" and "Categories" labels/headers.

## Known Defects

None at analysis time (2026-08-10).

## Notes

- **Page navigation:** The Catalog page can be reached via `/elitea-catalog` route directly, or via sidebar "Catalog" link if present (linked to `href="/elitea-catalog"`).
- **Tab behavior:** Switching tabs updates both the `aria-selected` state AND the main content area. Both signals should flip together; if only one flips, it's a defect.
- **Filter chips:** Right panel filter chips change their testid prefix between tabs (`catalog-agent-...` vs `catalog-skill-...`) because each tab's `CatalogBody` / `CategoryRail` component is feature-scoped. This is not a defect — it's by design for accessibility and CSS scoping.
- **Empty state:** If agents or skills are not loaded in the project, the main content will show "No agents found" or "No skills found" text instead of cards. This is still valid Agents/Skills "content" for the purposes of the test.

## Handles Reference

| Element | Locator | Fallback | Status |
|---|---|---|---|
| Page heading | `[data-testid="catalog-page-heading"]` | `page.get_by_text("Welcome to ELITEA Catalog")` | on-main ✓ |
| Agents tab | `[data-testid="catalog-agents-tab"]` | `page.get_by_role("tab", {name:"Agents"})` | on-main ✓ |
| Skills tab | `[data-testid="catalog-skills-tab"]` | `page.get_by_role("tab", {name:"Skills"})` | on-main ✓ |
| Agent filter chips | `[data-testid^="catalog-agent-category-filter-chip"]` | N/A (dynamic) | on-automation/testids ✓ (ELITEA-2352) |
| Skill filter chips | `[data-testid^="catalog-skill-category-filter-chip"]` | N/A (dynamic) | on-automation/testids ✓ (ELITEA-2352) |
| Main content | `main` | `page.locator("main")` | standard HTML |
