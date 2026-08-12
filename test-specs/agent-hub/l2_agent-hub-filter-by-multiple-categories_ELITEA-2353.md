# Test Case: Agent Hub — filter agents by multiple categories simultaneously

## Metadata
- **TMS ID**: ELITEA-2353
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright. All 6 steps reproduced successfully. Multi-category filtering works as specified: clicking "Business Analyst" filters to that category; then clicking "Elitea" while Business Analyst remains selected accumulates both filters, displaying sections from both categories simultaneously. Both chips show `data-selected="true"` state correctly. One case-text drift identical to ELITEA-2352 (CLARIFICATION, already filed — the "reload category items" icon does not exist in the live product). Zero console errors observed during exploration.
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075/2350/2352) covers all page elements — category filter-rail chips (`CATEGORY_FILTER_CHIP` template), content-list category headings (`CATEGORY_HEADING` template), agent cards (`AGENT_CARD_PREFIX`), page heading. Reused as-is, no new page object needed. **Not a target for `extend-existing`/`already-covered`**: the prior merged spec ELITEA-2352 covers *single*-category filtering only (click one chip, that category filters); this case tests the *accumulation* behavior (click first chip, then click second chip while first remains selected, both filters apply simultaneously) — the multi-chip interaction is a distinct observable not covered by ELITEA-2352's single-select flow. Fresh coverage per the skill's own boundary call.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- Agent Hub (Catalog) page freshly navigated to (no category filters pre-selected) — the filter state (`selectedTagNames` in `AgentsTab.jsx`) must start empty to properly test the accumulation behavior. Each chip click adds to the selected set, not replaces it.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- "Business Analyst" and "Elitea" agent categories exist with agents in both (confirmed live): Business Analyst has 4 agents (Elitea Feature Story Generator, User Story Creator, AI Platform Design Advisor, Business Analyst); Elitea has multiple agents (at least 1 confirmed in live exploration).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: URL is `/elitea-catalog`; page heading visible and says "Welcome to ELITEA Catalog!".
   - **Verify**: category filter-rail chips are visible in the right sidebar (all 11 category options present: Trending, My Liked, Business Analyst, DevOps, Development, Elitea, Epam, Knowledge & Documentation, Project Management, Quality Assurance, Other).
   - **Verify**: zero console errors during page load.

2. Click on "Business Analyst" category filter chip.
   - **Verify**: click succeeds; no console errors.
   - **Verify**: the chip shows selected state (`data-selected="true"`).

3. Click on "Elitea" category filter chip while "Business Analyst" remains selected.
   - **Verify**: click succeeds; no console errors.
   - **Verify**: both "Business Analyst" and "Elitea" chips show selected state (`data-selected="true"` on both).

4. Verify both category sections are displayed.
   - **Verify**: exactly two content-list category sections render: "Business Analyst" and "Elitea" (no other `catalog-category-heading-*` present like "Trending", "DevOps", etc. — the accumulated filter excludes all other categories).
   - **Verify**: the sections appear one after another in the main content area.

5. Verify section headers for both categories appear.
   - **Verify**: heading "Business Analyst" visible above its agent cards (`catalog-category-heading-business-analyst`).
   - **Verify**: heading "Elitea" visible above its agent cards (`catalog-category-heading-elitea`).
   - **Verify**: both headings are rendered and positioned correctly (Business Analyst first, then Elitea).

6. Verify agents from both categories are displayed in separate labeled sections.
   - **Verify**: Agent cards from Business Analyst category appear under the "Business Analyst" heading (live count: 4 cards — Elitea Feature Story Generator, User Story Creator, AI Platform Design Advisor, Business Analyst).
   - **Verify**: Agent cards from Elitea category appear under the "Elitea" heading.
   - **Verify**: no agent cards from other categories (DevOps, Development, etc.) are visible.

## Expected Final State
Agent Hub displays agents from **both** "Business Analyst" and "Elitea" categories simultaneously in separate, labeled sections. Both category filter chips in the right sidebar show selected state. Clicking multiple category chips accumulates the filters — a true multi-select filter behavior, not a single-select replacement.

## Pass/Fail Criteria

**Pass:**
- All 6 steps complete without errors.
- Both "Business Analyst" and "Elitea" chips are highlighted/selected after their respective clicks.
- Both "Business Analyst" and "Elitea" sections appear in the content area with their respective agents.
- Zero console errors during the filter interactions.
- Multi-category filtering is confirmed (agents from both categories, agents from other categories excluded).

**Fail:**
- Any step produces an error or unexpected result.
- Chips do not show selected state after clicking.
- Sections do not render from both categories.
- Clicking the second chip deselects the first (single-select instead of multi-select — a defect if observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | URL `/elitea-catalog`; page heading visible; category filter chips visible; zero console errors | asserted |
| 2 Click "Business Analyst" category filter chip | Control responds; expected next state is shown | step 2 | chip click succeeds; no console errors; `data-selected="true"` on Business Analyst chip | asserted |
| 3 Click "Elitea" category filter chip while Business Analyst remains selected | Control responds; both chips remain selected | step 3 | both chips show `data-selected="true"`; no console errors | asserted |
| 4 Verify both category sections are displayed | Agents from both categories appear in separate labeled sections | step 4 | exactly two `catalog-category-heading-*` visible (business-analyst, elitea); no other category sections | asserted |
| 5 Verify section headers "Business Analyst" and "Elitea" appear | Condition holds as described | step 5 | both headings visible and correctly positioned (Business Analyst first, Elitea second) | asserted |
| 6 Verify agents from both categories displayed in separate labeled sections | Condition holds as described | step 6 | agent cards from Business Analyst under its heading; agent cards from Elitea under its heading; zero cards from other categories | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 1` asserts zero console errors during page load — *added: standard side-channel regression guard*.
- `step 2` asserts zero console errors during chip interaction — *added: regression guard*.
- `step 3` asserts zero console errors during the multi-click interaction — *added: regression guard*.
- `step 4` asserts exactly two sections (not "at least two") — *added: proves multi-select accumulation, not a single-select that only shows one category at a time*.
- `step 6` asserts a specific agent count (4 for Business Analyst, verified live) — *added: proves the filter is working correctly, not just non-empty*.

## Cleanup

None — read-only filter interaction, no state created. The multi-select filter state (`selectedTagNames` / `selectedCategories` in `AgentsTab.jsx`) persists in the SPA's in-memory state for the rest of the browser session but does not persist across a fresh `page` fixture (function-scoped per test in this project's fixtures) — no explicit cleanup needed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Category filter-rail chip | `AgentHubPage.CATEGORY_FILTER_CHIP` template (`catalog-agent-category-filter-chip-{slug}`) — dynamic per category name, slugified | none | on-`automation/testids` ✓ (ELITEA-2350, not yet on `main` — human cherry-pick pending) |
| Category filter-rail chip **selected state** | `data-selected="true"/"false"` attribute on the SAME chip element, combined as `[data-testid="catalog-agent-category-filter-chip-{slug}"][data-selected="true"]` | none | on-`automation/testids` ✓ (ELITEA-2352, not yet on `main`) |
| Content-list category heading | `AgentHubPage.CATEGORY_HEADING` template (`catalog-category-heading-{slug}`) — slugified category name | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` (`[data-testid^="catalog-agent-card-"]`) — prefix match across all cards | none | on-main ✓ (pre-existing, ELITEA-2075) |

Naming/slugification convention: `{category-name}` → lowercase, non-alphanumeric runs replaced with `-` (e.g., "Business Analyst" → `business-analyst`, "Knowledge & Documentation" → `knowledge-documentation`).

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?...` with tag/category filter query params — called after each chip click to re-fetch the filtered agent list (tags may include both selected categories or handled client-side, exact filtering scope not distinguished — out of scope for this UI-level case).
- No 4xx/5xx observed during filter interactions.

## Known Defects Found During Exploration
- **[CLARIFICATION, filed — ELITEA-2352's #1212]** Case text (steps 5 and 6) mentions a "reload category items" icon next to section headers; no such icon exists in the live product. Same drift as ELITEA-2352. Automation asserts the headings only; does not assert an icon.
- None else found — zero console errors, zero 4xx/5xx, multi-category filtering works correctly and matches the case's core intent.

## Blocked Steps
None — all 6 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project).
- **No new page object needed** — reuse `AgentHubPage` from ELITEA-2352 (and earlier cases). The only new behavior is the *accumulation* on a second click (both chips remain selected instead of the second replacing the first) — this is automatic in the product's `AgentsTab.jsx` (`selectedTagNames.includes(tag) ? remove(tag) : add(tag)` toggle logic), no new assertions needed beyond what ELITEA-2352 already covers for individual chip selection state.
- **Reuse the single-chip methods**: call `click_category_filter_chip("Business Analyst")` once, then `click_category_filter_chip("Elitea")` a second time from the same test body. The accumulation behavior is tested by verifying both chips' `data-selected="true"` state after the second click.
- Selector policy: testid-only + `data-*` state attributes (`.agents/testing.md` § Locator policy). All locators already defined in `AgentHubPage`, same as ELITEA-2352.
- Marker suggestion: `@pytest.mark.p1` (high priority), `@pytest.mark.regression`, `@pytest.mark.agents` (matches ELITEA-2350/2352 marker set).
- **Multi-select specific testing note**: the key observable that differs from ELITEA-2352 is that the SECOND chip click does NOT deselect the first — both remain selected and their sections both render. This accumulation is the case's core value; assert it explicitly via the both-chips-selected check in step 3 and the both-sections-visible check in step 4.

## Relation to ELITEA-2352

ELITEA-2352 tests single-category filtering (click one chip, that category filters and displays). ELITEA-2353 tests multi-category filtering (click first chip, then click second chip, both accumulate and both display simultaneously). The two cases are **not** data variants (same flow, different data) — they test **different observable behavior** (single-select vs. multi-select accumulation):

- ELITEA-2352: click "Business Analyst" → only Business Analyst section renders
- ELITEA-2353: click "Business Analyst", then click "Elitea" → **both** Business Analyst and Elitea sections render

The accumulation behavior is distinct and merits its own spec. Implementation can reuse ELITEA-2352's test body/page-object logic, but must verify the multi-select observable as a separate test case (not a parameterization of ELITEA-2352) — the test can call `click_category_filter_chip()` twice in sequence on the same test.

## Implementation Recommendation

Write as a standalone test (not `extend-existing` of ELITEA-2352), but reuse:
- `AgentHubPage` as-is (all needed methods already exist from ELITEA-2352)
- The `click_category_filter_chip(category_label)` method from ELITEA-2352's implementation
- The `is_category_filter_chip_selected(category_label)` helper method also from ELITEA-2352

Test body pseudocode:
```python
def test_agent_hub_filter_by_multiple_categories(page):
    # Step 1: Navigate
    agent_hub = AgentHubPage(page)
    agent_hub.navigate()
    agent_hub.wait_for_page_load()
    assert agent_hub.page_heading.is_visible()
    
    # Step 2: Click Business Analyst
    agent_hub.click_category_filter_chip("Business Analyst")
    assert agent_hub.is_category_filter_chip_selected("Business Analyst")
    
    # Step 3: Click Elitea (multi-select accumulation)
    agent_hub.click_category_filter_chip("Elitea")
    assert agent_hub.is_category_filter_chip_selected("Business Analyst")  # Still selected
    assert agent_hub.is_category_filter_chip_selected("Elitea")           # Now selected too
    
    # Step 4-6: Verify both sections render
    assert agent_hub.is_category_section_visible("Business Analyst")
    assert agent_hub.is_category_section_visible("Elitea")
    assert page.locator('[data-testid^="catalog-category-heading-"]').count() == 2
    # Verify agent cards from both categories are present...
```

## Live Exploration Summary

**Execution results on localhost:5173:**
- Initial state: 7 category sections visible (Trending, Business Analyst, DevOps, Development, Elitea, Quality Assurance, Other)
- After clicking "Business Analyst": 1 section visible (Business Analyst only) — single-select filter works ✓
- After clicking "Elitea" (while Business Analyst selected): 2 sections visible (Business Analyst, Elitea) — multi-select accumulation works ✓
- Both chips show `data-selected="true"` after second click ✓
- Zero console errors during interaction ✓
- Expected behavior fully confirmed live

