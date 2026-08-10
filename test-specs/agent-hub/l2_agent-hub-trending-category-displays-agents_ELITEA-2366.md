# Test Case: Agent Hub — Trending category displays agents

## Metadata
- **TMS ID**: ELITEA-2366
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP. All 5 steps reproduced live. Zero console errors. One case-text drift (CLARIFICATION, filed per ELITEA-2352/#1212 precedent — see § Known Defects).
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`) already covers category chips and agent cards (`navigate()`, `CATEGORY_HEADING`/`is_category_section_visible()`, `AGENT_CARD_PREFIX`/`get_agent_card()`). This case uses the same surface; no new page object needed. **Not a target for `extend-existing`/`already-covered`**: ELITEA-2350's merged spec asserts only the default *all-category* view; this case asserts the *filtered Trending-only* view — a distinct observable (the filter activation and its effect on the category list), not an extension of the same test.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" or any project containing agents (confirmed live).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to the ELITEA Catalog page (`/elitea-catalog`).
   - **Verify**: URL is `/elitea-catalog`; page title contains "ELITEA Catalog" (confirmed live: `"ELITEA Catalog - project_user_659"`).
   - **Verify**: sidebar `project-selector-trigger-combobox` shows the active project (confirmed live: "Project: Private").

2. Click the **Trending category filter chip**.
   - **Verify**: the click succeeds; the page remains at `/elitea-catalog` (no navigation).
   - **Verify**: Trending chip updates to [active] state (confirmed live via ref=f7e186: `button "Trending" [active]`).
   - **Testid handle**: `catalog-agent-category-filter-chip-trending` (pre-existing, applied live by Playwright MCP's `getByTestId`)

3. Verify the Trending tab is highlighted/active.
   - **Verify**: the Trending filter chip carries the `[active]` state indicator (confirmed live after step 2 click).
   - **State assertion handle**: `[data-testid="catalog-agent-category-filter-chip-trending"][data-selected="true"]` (conditional attribute — see Handles Reference).

4. Verify agents are displayed under the Trending section.
   - **Verify**: at least one `catalog-agent-card-{id}` (dynamic testid per `AgentCard.jsx`) visible below the "Trending" content-list heading (confirmed live: 6 cards rendered — Business Analyst, Assistant for ELITEA Documentation, Reflexion, Quality Engineering Sidekick, API Testing Buddy, Linux Solution Mentor — plus a "Show more" expander).
   - **Testid handle**: `catalog-agent-card-{id}` (pre-existing dynamic per ELITEA-2350).

5. Verify the section header "Trending" appears above the results.
   - **Verify**: text "Trending" appears as a content-list section heading above the agent cards (confirmed live: generic element at position [240,219,1159,24] with text "Trending").
   - **Testid handle**: `catalog-category-heading-trending` (pre-existing, per ELITEA-2350 and ELITEA-2352).

---

## Handles Reference

| Element | Primary Handle | Fallback | State/Filter | PROVENANCE |
|---|---|---|---|---|
| Trending category filter chip (right-hand rail) | `catalog-agent-category-filter-chip-trending` — testid applied live | none (raw handle forbidden) | `[data-selected="true"]` when active | on-automation/testids (pre-existing, per ELITEA-2350) |
| Agent card grid item (per agent) | `catalog-agent-card-{id}` (dynamic, `AgentCard.jsx`) | none (raw handle forbidden) | none (state not asserted) | on-main ✓ (pre-existing, ELITEA-2350) |
| "Trending" section heading (content-list) | `catalog-category-heading-trending` (pre-existing, `AgentCategorySection.jsx`) | none | none | on-main ✓ (pre-existing, ELITEA-2075) |
| "Show more" expander (category section) | testid needed: `catalog-trending-show-more-expander` (or use accessible name "Show more" via `getByText()` + scoped to section) | none (raw handle forbidden) | none | needs-adding |

---

## Coverage Map — Test Steps vs. Observable Requirements

| Case Step | Observable (from case text) | Covered by | Asserted at | Disposition |
|---|---|---|---|---|
| 1 | Navigate to Agent Hub; URL loads | browser step 1 — `page.goto('/elitea-catalog')` + URL assertion | test step 1 | ✅ asserted |
| 2 | Click Trending category filter tab; control responds | browser step 2 — click `catalog-agent-category-filter-chip-trending` | test step 2 | ✅ asserted |
| 3 | Verify tab is highlighted/active | browser state after step 2 — [active] state indicator | test step 3 | ✅ asserted via `data-selected="true"` attribute |
| 4 | Verify agents are displayed under Trending section | browser step 4 — locate ≥1 `catalog-agent-card-*` card under `catalog-category-heading-trending` | test step 4 | ✅ asserted (count: 6 cards confirmed live) |
| 5 | Verify section header "Trending" appears above results with "reload category items" next to it | browser step 5 — verify "Trending" text present + positioned above cards (reload icon NOT asserted per case-text drift) | test step 5 | ✅ heading asserted; ⚠️ reload icon **omitted** (see Known Defects) |

---

## Known Defects / Case-Text Drift

**[CLARIFICATION, filed]** [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212) — case text claims "reload the category items" icon appears next to the section header; **no such icon exists anywhere in the live product** (confirmed via source grep for reload/refresh icon components in `src/[fsd]/features/agent-hub/` and `src/[fsd]/shared/ui/category/` — 0 hits; visual confirmation: screenshot shows only "Trending" heading text, no adjacent icon). Same drift family as #1208 (ELITEA-2350). The Catalog has only automatic background refresh (`useCatalogAutoRefresh`), no manual-trigger UI element. **Automation asserts the heading only; does NOT assert a reload icon** (reverse-masking guard — asserting a non-existent element would either always fail on a non-defect, or if written as an absence-assertion, would assert nothing meaningful about case intent).

---

## Test Implementation Notes

- **Page navigation**: use `AgentHubPage.navigate()` to reach `/elitea-catalog`.
- **Filter activation**: click via `catalog-agent-category-filter-chip-trending` testid.
- **Wait strategy**: after click, use `page.wait_for_selector('[data-testid="catalog-agent-card-"]')` to ensure cards are rendered (no fixed sleep).
- **Assertion: heading presence**: assert `page.locator('[data-testid="catalog-category-heading-trending"]').is_visible()` and text equals "Trending".
- **Assertion: agent cards**: assert `page.locator('[data-testid^="catalog-agent-card-"]').count() >= 1`.
- **State assertion**: filter chip's `data-selected` attribute OR `[data-testid="catalog-agent-category-filter-chip-trending"]` has `[aria-pressed="true"]` if the chip is a button (verify via live DOM inspection).
- **Step reporting**: wrap each step in `with allure.step("Step N — …"):` per `.agents/testing.md`.

---

## Evidence

- **Screenshot (step 2-5 completion)**: `.playwright-mcp/after-trending-click-snapshot.md` — shows Trending chip [active], "Trending" heading visible, 6 agent cards rendered, "Show more" expander visible. No reload icon present.

---

## Related Cases / Coverage Gaps

- **ELITEA-2350** (agent hub page load, private project) — merged spec (`test_agent_hub_page_loads_private_project.py`) asserts the default *all-category* view; does **not** assert filter activation or category-specific results.
- **ELITEA-2352** (filter by single category) — merged spec asserts the Business Analyst category filter; same pattern as this case (Trending filter instead).
