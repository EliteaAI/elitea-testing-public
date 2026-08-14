# Test Case: Agent Hub — filter agents by single category

## Metadata
- **TMS ID**: ELITEA-2352
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst/Implementer**: test-automation-engineer (agent, combined analyst+implementer dispatch — surface pre-mapped by ELITEA-2350's `_surface.md` digest)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP. All 5 steps reproduced live. Zero console errors. One case-text drift (CLARIFICATION, filed — see § Known Defects: no "reload category items" icon exists anywhere in the product). One `data-*` state-attribute gap (chip "selected" state had no accessible/stable signal at all) — implementer work via `add-data-testid`-style JSX edit, done this dispatch (new `data-selected` attribute).
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075 + ELITEA-2350) already covers the page heading, category filter-rail chips (`CATEGORY_FILTER_CHIP`/`is_category_filter_chip_visible()`), content-list category headings (`CATEGORY_HEADING`/`is_category_section_visible()`), and agent cards (`AGENT_CARD_PREFIX`/`get_agent_card_count()`). **Not a target for `extend-existing`/`already-covered`**: the only merged spec touching this page besides ELITEA-2075's unrelated LLM-override flow is `test_agent_hub_page_loads_private_project.py` (ELITEA-2350), which asserts the filter-rail chips are *visible* but never clicks one, never asserts a selected/active state, and never asserts the filtered content — none of this case's own distinctive observables (click-to-filter, selection state, filtered result set) are covered there. Fresh (if narrow) coverage per the skill's own boundary call.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- Agent Hub (Catalog) page freshly navigated to (no category filter pre-selected) — the filter state is a page-level array (`selectedTagNames` in `AgentsTab.jsx`) that persists across chip clicks within a session, so the test must start from an unfiltered page load, not a page some earlier test already filtered.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Live "Business Analyst" category agents (existing project data, confirmed live): "Elitea Feature Story Generator", "User Story Creator", "AI Platform Design Advisor", "Business Analyst" — 4 cards total in this project/environment (the case's own list — "AI Platform Design Advisor, User Story Creator, Business Analyst" — is an "e.g." subset of these; all three named examples ARE present, plus one more).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.wait_for_page_load()`).
2. Click on the "Business Analyst" category filter-rail chip (`CategoryRail.jsx`, right-hand rail — NOT a top tab; see ELITEA-2350's AFS § "Category filter rail vs. category content-list headings" for the case-text's "tabs" wording nuance, which is a wording nuance only, not a drift).
   - **Verify**: click succeeds; no console errors.
3. Verify the selected chip is highlighted/active.
   - **IMPLEMENTER FINDING (testid/state-attribute gap, closed this dispatch):** the chip had **no accessible, stable "selected" signal at all** before this implementation — no `aria-selected`, no `aria-pressed`, no `data-*` state attribute; the only visual differentiator was a computed CSS background-color style (`styles.selectedChip` vs `styles.chip` in `CategoryRail.jsx`), and Playwright's own accessibility-tree `[active]` marker on the element turned out to be **pure DOM-focus state, not app selection state** — confirmed live: after clicking a *second* chip (`DevOps`), `[active]` moved to the newly-focused element even though `Business Analyst` remained the actually-filtered category in app state; conversely, `[active]` also disappeared from a still-selected chip the instant focus moved to an unrelated element (the search input), while the filtered content stayed correctly on Business Analyst. Asserting Playwright's `[active]`/focus signal would have been a false correlation to the underlying "selected" business state (would flake depending on click order / subsequent focus moves), so per `.agents/testing.md` § Locator policy ("state is specced as a `data-*` attribute filter, never as a state-dependent testid") a new `data-selected="true"/"false"` attribute was added directly on the existing chip testid (`CategoryRail.jsx`, additive — the chip's own `data-testid` is unchanged), driven by the exact same `selectedCategories.includes(category)` expression already used for the chip's style. Confirmed live: `data-selected` flips `"false"` → `"true"` on click and — unlike the focus-based signal — persists correctly across subsequent focus changes.
   - **Verify**: `[data-testid="catalog-agent-category-filter-chip-business-analyst"][data-selected="true"]` matches (chip is selected).
4. Verify only Business Analyst agents are displayed.
   - **Verify**: exactly one content-list category section is rendered (`catalog-category-heading-business-analyst`, no other `catalog-category-heading-*` present) — confirmed live via `page.locator('[data-testid^="catalog-category-heading-"]').allTextContents()` returning exactly `["Business Analyst"]` after the single-chip click (the "Trending" default section is replaced, not merely supplemented — single-category filtering is exclusive for this test's one-click scenario; the *multi*-select accumulation behavior noted below is out of scope for this case).
   - **Verify**: all 4 live Business Analyst agent cards are present by name — "Elitea Feature Story Generator", "User Story Creator", "AI Platform Design Advisor", "Business Analyst" — including the case's own 3 named examples (as a subset, per its "e.g." wording).
5. Verify the section header "Business Analyst" appears above the results, with "reload category items" icon next to it.
   - **CASE-TEXT DRIFT (CLARIFICATION, filed — not a defect)**: the "Business Analyst" content-list heading (`catalog-category-heading-business-analyst`) IS present and correctly positioned above the filtered results — that half of the case holds. The **"reload category items" icon does not exist anywhere in the live product** — confirmed both visually (screenshot) and via source: `AgentCategorySection.jsx`'s `headerContainer` renders only a `Typography` title, zero icon elements, and a full-file grep for reload/refresh icon components (`RestartAlt`, `SyncIcon`, `ReplayIcon`, `Autorenew`, `RefreshIcon`, `CachedIcon`) under `src/[fsd]/features/agent-hub` and `src/[fsd]/shared/ui/category` returns 0 hits. The Catalog's only refresh mechanism is a fully automatic, throttled background refresh (`useCatalogAutoRefresh`) with no manual-trigger UI element. Filed as [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212) (same drift family as #1208 from ELITEA-2350). Automation asserts the heading only; does not assert a "reload" icon (reverse-masking guard — asserting a non-existent element's presence would either always fail on a non-defect, or if written as an absence-assertion, would silently assert nothing meaningful about the case's real intent).

## Expected Results
- Clicking a single category filter-rail chip filters the Agent Hub content to that category's agents only.
- The clicked chip shows a stable, accessible "selected" signal (`data-selected="true"`).
- The category section header appears above the filtered results with the category name.
- Zero console errors during the interaction.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click "Business Analyst" category filter tab | Control responds; expected next state is shown | step 2 | chip click succeeds, no console errors | asserted |
| 3 Verify the selected tab is highlighted/active | Condition holds as described | step 3 | `data-selected="true"` on the clicked chip (new state attribute, see finding) | asserted |
| 4 Verify only Business Analyst agents are displayed | Condition holds as described | step 4 | exactly one `catalog-category-heading-*` present (`business-analyst`); all 4 live agent names present | asserted |
| 5 Verify the section header "Business Analyst" appears above the results with "reload category items" icon next to it | Condition holds as described | step 5 | `catalog-category-heading-business-analyst` visible + correctly positioned; icon claim NOT asserted (case-text drift, see clarification) | asserted *(icon-claim half is drift, see clarification — heading half is asserted against the live text)* |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 2` asserts zero console errors during the click interaction — *added: standard side-channel regression guard per this skill's own discipline.*
- `step 4` asserts the exact card-name set (not just a count) — *added: a bare "at least 1 card" check (as ELITEA-2350 used for the unfiltered view) would not actually prove the FILTER worked; asserting the specific live Business Analyst agent names is the only way to prove the filter is correct, not merely non-empty.*
- `step 4` asserts exactly one content-list section renders (not "at least the Business Analyst one") — *added: proves the filter actually excludes other categories' content, the case's own "ONLY Business Analyst agents" wording made explicit as a countable assertion.*
- (nothing else added beyond the case's own 5 steps.)

## Cleanup

None — read-only filter interaction, no state created. The single-select click leaves `selectedTagNames`/`selectedCategories` non-empty in the SPA's in-memory state for the rest of the browser session, but this does not persist across a fresh `page` fixture (function-scoped `page` per test in this project's fixtures) — no explicit cleanup needed.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Category filter-rail chip | `AgentHubPage.CATEGORY_FILTER_CHIP` template (`catalog-agent-category-filter-chip-{slug}`) | none | on-`automation/testids` ✓ (ELITEA-2350, not yet on `main` — human cherry-pick pending) |
| Category filter-rail chip **selected state** | **NEW this dispatch**: `data-selected="true"/"false"` attribute on the SAME chip element (`CategoryRail.jsx`), driven by `selectedCategories.includes(category)` — same slugify convention, combined as `[data-testid="catalog-agent-category-filter-chip-{slug}"][data-selected="true"]` | none (state via `data-*` attribute per `.agents/testing.md` § Locator policy; NOT a state-dependent testid) | on-`automation/testids` ✓ (this dispatch, `EliteaAI/EliteaUI@9b93f67c`), NOT yet on `main` |
| Content-list category heading | `AgentHubPage.CATEGORY_HEADING` template (`catalog-category-heading-{slug}`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` (`[data-testid^="catalog-agent-card-"]`) | none | on-main ✓ (pre-existing, ELITEA-2075) |

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?...` with a tag/category filter query param — same endpoint family as the unfiltered load (ELITEA-2350's AFS), now filtered server-side or client-side by the selected category (not distinguished further — out of scope for this UI-level case).
- No 4xx/5xx observed during the filter interaction.

## Known Defects Found During Exploration
- **[CLARIFICATION, filed]** [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212) — case text claims a "reload category items" icon appears next to the filtered section header; no such icon exists anywhere in the live product or its source (confirmed via source grep — 0 hits for reload/refresh icon components). Same drift family as #1208 (ELITEA-2350's "Welcome to Agent HUB" header text) — stale TMS case text, not a product defect.
- None else found — zero console errors, zero 4xx/5xx, filter behavior itself works correctly and matches the case's core intent (single-category filtering).

## Blocked Steps
None — all 5 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- **No new page object needed beyond one new method** — reuse `AgentHubPage` as-is for navigation/heading/chip-visibility/content-heading/card-count; add ONE new method, `is_category_filter_chip_selected(category_label, timeout)`, mirroring `is_category_filter_chip_visible()`'s slugify + template-format pattern but locating `f"{CATEGORY_FILTER_CHIP.format(slug)}[data-selected=\"true\"]"` — actually implemented as a combined locator string built from the existing `CATEGORY_FILTER_CHIP` template plus a `[data-selected="true"]` suffix, to keep the testid-inventory single-sourced.
- **Click method**: add `click_category_filter_chip(category_label)` to `AgentHubPage`, using the same `_slugify_category()` module helper already defined in the page object file.
- Selector policy: testid-only + `data-*` state attribute, no fallback (`.agents/testing.md` § Locator policy). The `data-selected` addition follows the exact precedent already documented there ("Testid = stable identity; state via `data-*` attributes").
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.agents` (matches ELITEA-2350's marker set for this same page).
