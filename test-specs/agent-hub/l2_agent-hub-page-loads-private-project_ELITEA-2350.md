# Test Case: Agent Hub — page loads successfully for Private project

## Metadata
- **TMS ID**: ELITEA-2350
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector already reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP. All 5 steps reproduced live (screenshot: `test-results/screenshots/ELITEA-2350-step-05-page-loaded.png`). Zero console errors. One case-text drift (CLARIFICATION, filed — see § Known Defects). One `testid needed` gap (category filter chips) — implementer work via `add-data-testid`, not a fallback-worthy substitute.
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075) already covers this exact page (`navigate()`, `page_heading`, `search_input`, `CATEGORY_HEADING`/`is_category_section_visible()`, `AGENT_CARD_PREFIX`/`get_agent_card()`) — reused as-is, no new page object needed. **Not a target for `extend-existing`/`already-covered`**: the only merged spec touching this page, `test_agent_hub_participant_readonly_canvas_llm_override.py` (ELITEA-2075), asserts only the heading, the search input, and the "trending" **content-list** category heading (`catalog-category-heading-trending`) as an incidental precondition of a much larger, unrelated LLM-override flow — it does not assert the **filter-rail** category chip list (this case's step 4, the most distinctive requirement) or explicit agent-card presence (step 5). That gap is most of this case's own distinctive observable, not "a small number of missing assertions" on the same observable — per the SKILL's own boundary call, this is fresh (if narrow) coverage, not an extension of an unrelated 14-step flow test. `ready-for-automation` also matches the project's default-to-reuse guidance when in doubt.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" — confirmed live via the sidebar `project-selector-trigger-combobox` reading "Project: Private" (this project's default `${TEST_USER}` project on localhost; no explicit switch performed or required).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`) from the left sidebar while the active project is "Private".
   - **Verify**: URL is `/elitea-catalog`; page title is `"ELITEA Catalog - Private"` (confirmed live via `useBrowserPageTitle`, includes the active project name — an extra, free confirmation that we are in the Private project context).
   - **Verify**: sidebar `project-selector-trigger-combobox` text still reads "Project: Private" (unchanged by navigation).
2. Verify the page loads with the Catalog heading.
   - **CASE-TEXT DRIFT (CLARIFICATION, filed — not a defect)**: case text says `"Welcome to Agent HUB"`; live heading text is **`"Welcome to ELITEA Catalog!"`** (`catalog-page-heading`, `EliteaCatalog.jsx`). Same root cause as the ELITEA-2075 AFS's step-1 nav-label drift (`AgentHub`/`/agents-hub` is only a legacy redirect source in `routes.js`, never a rendered label) — filed as its own ticket this session since it wasn't previously filed as a standalone issue (see § Known Defects). Assert the live heading text.
3. Verify the search bar is visible at the top center.
   - **Verify**: `catalog-search-input` (pre-existing testid) visible, placeholder `"Search for agents"` (Agents tab is the default/selected tab — confirmed live via `tab "Agents" [selected]`).
4. Verify category filter tabs are displayed.
   - **CASE-TEXT MATCH (no drift)**: the case's literal 11-item list — Trending, My Liked, Business Analyst, DevOps, Development, Elitea, Epam, Knowledge & Documentation, Project Management, Quality Assurance, Other — matches the live product **exactly**, confirmed live (see snapshot below). They render as MUI `Chip` filter buttons in a right-hand rail (`CategoryRail.jsx`, shared with the Skills tab), split into a "Featured" group (Trending, My Liked — static, `AgentHubConstants.TRENDING_CATEGORY`/`MY_LIKED_CATEGORY`) and a "Categories" group (the other 9 — dynamic, from the backend tag list), NOT top tabs as the case's "tabs" wording implies (the only actual MUI `tab` role elements on this page are "Agents"/"Skills"). This is a wording nuance, not a functional drift — the case's own pass criterion ("category filter tabs are displayed") holds either way; no clarification filed for it (functionally correct, would be pedantic to file).
   - **Verify**: all 11 chip labels visible in the rail (`Featured` section: Trending, My Liked; `Categories` section: Business Analyst, DevOps, Development, Elitea, Epam, Knowledge & Documentation, Project Management, Quality Assurance, Other).
5. Verify agent cards are displayed in the main content area.
   - **Verify**: at least one `catalog-agent-card-{id}` (pre-existing dynamic testid, `AgentCard.jsx`) visible under the "Trending" content-list heading (`catalog-category-heading-trending`, pre-existing). Confirmed live: 6 cards rendered by default (Business Analyst, Assistant for ELITEA Documentation, Reflexion, API Testing Buddy, Quality Engineering Sidekick, Code Review Assistant) plus a "Show more" expander.

## Expected Results
- Agent Hub (Catalog) page loads without error for a user in the "Private" project context.
- Heading, search bar, category filter rail (all 11 entries), and agent cards in the main content area are all visible.
- Zero console errors during load.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub from a Private project context | Target page/section loads successfully | step 1 | URL `/elitea-catalog`; page title `"ELITEA Catalog - Private"`; `project-selector-trigger-combobox` text | asserted |
| 2 Verify "Welcome to Agent HUB" header | Condition holds as described | step 2 | `catalog-page-heading` visible, live text asserted | asserted *(label drift, see clarification — asserts the LIVE text, not the stale case string)* |
| 3 Verify search bar visible at top center | Condition holds as described | step 3 | `catalog-search-input` visible | asserted |
| 4 Verify category filter tabs displayed (11 named) | Condition holds as described | step 4 | 11 `Chip` labels in `CategoryRail` (Featured + Categories sections) visible | asserted |
| 5 Verify agent cards displayed in main content area | Condition holds as described | step 5 | ≥1 `catalog-agent-card-{id}` visible | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 1` asserts the browser page title (`"ELITEA Catalog - Private"`) in addition to the URL — *added: it embeds the active project name, giving a second, independent confirmation of the "Private project context" precondition the case's own title hinges on, at zero extra cost (no new interaction, already-rendered `document.title`).*
- `step 1` asserts `project-selector-trigger-combobox` text unchanged post-navigation — *added: makes the case's own "for Private project" qualifier a first-class assertion instead of an implicit assumption baked into the test's setup.*
- `step 2`/`step 5` capture zero console errors during the whole page load — *added: standard side-channel check per this skill's own discipline; nothing surfaced (see Concrete Handles / Known Defects), but the assertion belongs in the shipped test as a regression guard.*
- (nothing else added beyond the case's own 5 steps.)

## Cleanup

None — read-only page-load verification, no state created.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `LocatorDescriptor(testid="catalog-page-heading")` — pre-existing, `AgentHubPage.page_heading` | none (testid-only policy) | on-main ✓ (pre-existing, ELITEA-2075) |
| Search input | `LocatorDescriptor(testid="catalog-search-input")` — pre-existing, `AgentHubPage.search_input` | none | on-main ✓ (pre-existing, ELITEA-2075) |
| "Agents" tab (top, selected by default) | `LocatorDescriptor` — **testid needed**: `EliteaCatalog.jsx`'s `BaseTab` for `value="agents"` has no `data-testid` today (only the page-level heading/search do) | none | needs-adding |
| Category content-list heading ("Trending", etc., in the main list) | `AgentHubPage.CATEGORY_HEADING` template (`catalog-category-heading-{slug}`) — pre-existing, `AgentCategorySection.jsx`. Slug = `String(category).toLowerCase().replace(/[^a-z0-9]+/g, '-')` (confirmed via source) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Category **filter-rail** chips (Trending / My Liked / Business Analyst / DevOps / Development / Elitea / Epam / Knowledge & Documentation / Project Management / Quality Assurance / Other) | **testid needed** — `CategoryRail.jsx` (`src/[fsd]/shared/ui/category/CategoryRail.jsx`) renders each as a bare MUI `Chip` with **zero** `data-testid`/`testId` anywhere in the file (confirmed via full-file read + `git grep -c "data-testid\|testId"` = 0 on both `origin/main` and `origin/automation/testids`). This component is SHARED between `AgentsTab.jsx` (this case) and `SkillsTab.jsx` (skill-hub) via `CatalogBody.jsx` → `CategoryRail.jsx` — per `.agents/testing.md` § Locator policy ("shared components never hardcode feature-scoped testids"), the compliant shape is a caller-supplied `testId`/`<part>TestId` prop threaded `AgentsTab`/`SkillsTab` → `CatalogBody` → `CategoryRail`, NOT a hardcoded testid inside `CategoryRail.jsx` itself. Recommend: `chipTestIdPrefix` prop on `CategoryRail`, with `AgentsTab`'s call site passing `"catalog-agent-category-filter-chip"` (this case's own naming, `{section}-{element}-{param}` per the dynamic-testid convention, section = call site) → renders `data-testid="catalog-agent-category-filter-chip-{slug}"` per chip (same slugify function as the content-list headings, for consistency). `SkillsTab`'s own call site is out of scope for this case — leave its prop value to whichever case exercises the Skills tab's category rail. | none (fallback-worthy raw handle is forbidden here — this is a first-party JSX element, not a #579 third-party exception) | needs-adding |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` (`[data-testid^="catalog-agent-card-"]`) — pre-existing, `AgentCard.jsx` | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Sidebar project selector trigger | `LocatorDescriptor(testid="project-selector-trigger-combobox")` — pre-existing, duplicated across `admin_users_page.py`/`analytics_page.py`/`chat_page.py` per established convention (app-wide chrome, not scoped to one page) | none | on-main ✓ (pre-existing, ELITEA-2095) |

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?...` — Catalog agent list load (same endpoint family the ELITEA-2075 AFS documents for trending/liked/full variants). No new endpoint discovered this session.
- No 4xx/5xx observed during page load.

## Known Defects Found During Exploration
- **[CLARIFICATION, filed]** [EliteaAI/elitea-testing-public#1208](https://github.com/EliteaAI/elitea-testing-public/issues/1208) — case text says the header reads "Welcome to Agent HUB"; live product shows "Welcome to ELITEA Catalog!" (`catalog-page-heading`). Live product is internally consistent (nav label, page `<title>`, and heading all say "Catalog"/"ELITEA Catalog") — this is stale case text, not a product defect (reverse-masking guard). Same root cause as the un-filed drift noted inline in the ELITEA-2075 AFS; filed as its own ticket here since no standalone issue existed for it yet. Automation asserts the live text.
- None else found — zero console errors, zero 4xx/5xx, category filter list matches the case text exactly (no drift there).

## Blocked Steps
None — all 5 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools available and used this dispatch.
- **No new page object needed** — reuse `AgentHubPage` (`automation/pages/agent_hub_page.py`) as-is for steps 1–3 and 5. Add ONE new `LocatorDescriptor`/template constant to `AgentHubPage` once the `catalog-agent-category-filter-chip-{slug}` testid exists (step 4) — e.g. `CATEGORY_FILTER_CHIP = '[data-testid="catalog-agent-category-filter-chip-{}"]'`, mirroring the existing `CATEGORY_HEADING` template pattern in the same file.
- **Project-context assertion**: compose with `ChatPage.get_selected_project_text()` (`automation/pages/chat_page.py`) for the `project-selector-trigger-combobox` read in step 1 — same reuse-by-composition pattern ELITEA-2075 used for `AgentDetailPage`/`AgentFormPage` — rather than adding a 4th duplicate `LocatorDescriptor` to `AgentHubPage`. Either is policy-compliant (the testid is already duplicated 3×); composition avoids a 4th duplicate.
- **Category chip list assertion**: assert all 11 labels as a **set**, not a fixed order/index — `Featured` (Trending, My Liked) and `Categories` (the other 9) are two visually distinct rail sections; assert set-membership within each section rather than a single flat ordered list, so a future reorder within a section doesn't false-fail.
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy). The one `testid needed` row above (category filter chips) is implementer work via `add-data-testid` in the SHARED `CategoryRail.jsx` — follow the shared-component prop-threading discipline (`.agents/testing.md` § Locator policy "Shared components never hardcode feature-scoped testids"), not a hardcoded testid in the shared file itself.
- Marker suggestion: `@pytest.mark.p1` (high priority), `@pytest.mark.regression`, feature marker (new — this is the first `agents_hub`/`agent_hub` area test beyond ELITEA-2075's chat-focused one; consider adding a dedicated marker if the project wants one, or reuse an existing `agents`/`chat` marker — implementer's call, flag to lead if a new marker is warranted).
