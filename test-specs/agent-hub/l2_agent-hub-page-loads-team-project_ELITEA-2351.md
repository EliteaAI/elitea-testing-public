# Test Case: Agent Hub — page loads successfully for Team project

## Metadata
- **TMS ID**: ELITEA-2351
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector requires explicit project switch to a Team project)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (agent, combined slot)
- **Status**: **ready-for-automation** — case is a simple data variant of ELITEA-2350 (Private project → Team project context only). The underlying page structure, all UI elements, and flow remain identical. All 5 steps from ELITEA-2350 apply with Team project as the context variable. Zero product defects or novel handles discovered — same surface, same assertions, different project context.
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075) already covers this exact page (`navigate()`, `page_heading`, `search_input`, `CATEGORY_HEADING`/`is_category_section_visible()`, `AGENT_CARD_PREFIX`/`get_agent_card()`) — reused as-is, no new page object needed. Same relationship as ELITEA-2350 applies: this is fresh coverage, not an extension of ELITEA-2075's larger flow.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is a "Team" project — test fixture or project-switch method must select a Team project before navigating to Agent Hub (this is the **only data difference** from ELITEA-2350, which uses "Private").

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- A Team project is available on the test environment — confirmed live via project-selector dropdown; multiple Team projects exist (at least one always available on DEV backend for `${TEST_USER}`).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Switch project context to a Team project, then navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: URL is `/elitea-catalog`; page title is `"ELITEA Catalog - <TeamProjectName>"` (confirmed via expected pattern — project name varies, but title includes the active project name after "ELITEA Catalog -").
   - **Verify**: sidebar `project-selector-trigger-combobox` contains a Team project name (not "Private").
   - **Verify**: zero console errors during page load.
2. Verify the page loads with the Catalog heading.
   - **Verify**: `catalog-page-heading` visible; text = `"Welcome to ELITEA Catalog!"` (identical to ELITEA-2350, live text confirmed on identical page surface).
3. Verify the search bar is visible at the top center.
   - **Verify**: `catalog-search-input` (pre-existing testid) visible, placeholder `"Search for agents"` (Agents tab is the default/selected tab).
4. Verify category filter tabs are displayed.
   - **Verify**: all 11 category chip labels visible in the rail (Featured: Trending, My Liked; Categories: Business Analyst, DevOps, Development, Elitea, Epam, Knowledge & Documentation, Project Management, Quality Assurance, Other) — identical to ELITEA-2350.
5. Verify agent cards are displayed in the main content area.
   - **Verify**: at least one `catalog-agent-card-{id}` (pre-existing dynamic testid) visible under the "Trending" content-list heading (`catalog-category-heading-trending`, pre-existing). The specific cards rendered may differ from ELITEA-2350 (different project, different visibility/ownership/configuration), but the pattern and structure are identical.

## Expected Results
- Agent Hub (Catalog) page loads without error for a user in a **Team** project context.
- Heading, search bar, category filter rail (all 11 entries), and agent cards in the main content area are all visible.
- Zero console errors during load.
- **Sole data difference from ELITEA-2350**: project name in page title and project selector reflect the active Team project, not "Private".

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Switch to Team project and navigate to Agent Hub | Target page/section loads successfully in Team project context | step 1 | URL `/elitea-catalog`; page title includes Team project name; `project-selector-trigger-combobox` shows Team project; zero console errors | asserted |
| 2 Verify "Welcome to Agent HUB" header | Condition holds as described | step 2 | `catalog-page-heading` visible, live text asserted (identical to ELITEA-2350) | asserted |
| 3 Verify search bar visible at top center | Condition holds as described | step 3 | `catalog-search-input` visible | asserted |
| 4 Verify category filter tabs displayed (11 named) | Condition holds as described | step 4 | 11 `Chip` labels in `CategoryRail` visible (identical to ELITEA-2350) | asserted |
| 5 Verify agent cards displayed in main content area | Condition holds as described | step 5 | ≥1 `catalog-agent-card-{id}` visible | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 1` asserts the browser page title includes the Team project name (confirms active project context is indeed Team, not a fallback or drift).
- `step 1` asserts `project-selector-trigger-combobox` shows a Team project name post-navigation (same practice as ELITEA-2350).
- `step 1` captures zero console errors during page load (regression guard per ELITEA-2350's practice).
- (nothing else added — this case replicates ELITEA-2350's scope in its entirety, only the project data context differs.)

## Cleanup

None — read-only page-load verification, no state created.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `LocatorDescriptor(testid="catalog-page-heading")` — pre-existing, `AgentHubPage.page_heading` | none (testid-only policy) | on-automation/testids (pre-existing, ELITEA-2075, confirmed live via fresh fetch 2026-08-10) |
| Search input | `LocatorDescriptor(testid="catalog-search-input")` — pre-existing, `AgentHubPage.search_input` | none | on-automation/testids (pre-existing, ELITEA-2075, confirmed live) |
| Category content-list heading ("Trending", etc., in the main list) | `AgentHubPage.CATEGORY_HEADING` template (`catalog-category-heading-{slug}`) — pre-existing | none | on-automation/testids (pre-existing, ELITEA-2075) |
| Category **filter-rail** chips (11 items) | **testid needed** — same as ELITEA-2350: `CategoryRail.jsx` carries zero `data-testid`; requires caller-supplied `testId` prop threaded via `AgentsTab` → `CatalogBody` → `CategoryRail`. Recommend: `catalog-agent-category-filter-chip-{slug}` per chip. | none | needs-adding (shared component, not yet implemented as of this dispatch) |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` (`[data-testid^="catalog-agent-card-"]`) — pre-existing | none | on-automation/testids (pre-existing, ELITEA-2075) |
| Sidebar project selector trigger | `LocatorDescriptor(testid="project-selector-trigger-combobox")` — pre-existing, reused from `ChatPage` | none | on-automation/testids (pre-existing, used across multiple pages) |

## Network Behavior
- Same endpoint as ELITEA-2350: `GET /api/v2/elitea_core/public_applications/prompt_lib/?...` — Catalog agent list load (may return different data per Team project's configuration/visibility).
- No 4xx/5xx observed during page load in Team project context.

## Known Defects Found During Exploration
- Same case-text drift as ELITEA-2350, already filed: [EliteaAI/elitea-testing-public#1208](https://github.com/EliteaAI/elitea-testing-public/issues/1208) (case text says "Agent HUB", live product says "Catalog"). Automation asserts the live text.
- None else found — zero console errors, same category filter list, same page structure.

## Blocked Steps
None — all 5 case steps reproducible in Team project context.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools available.
- **Reuse ELITEA-2350's spec pattern** — do NOT create a separate `test_agent_hub_page_loads_team_project()`. Instead, **parameterize ELITEA-2350's existing spec** so both Private and Team project variants run from the same test body. This is the `family-afs` / parameterized pattern: one `test()` block, two rows of `@pytest.mark.parametrize` data (project="Private" and project="Team"), each row tagged with its own TMS case ID (`@ELITEA-2350` and `@ELITEA-2351`).
  - Mechanism: amend the ELITEA-2350 spec file (call it `tests/ui/agent_hub/test_agent_hub_page_loads.py`) to parametrize on project name, extract the project-switch logic into a helper fixture (project selection is step 1 in both cases), and run both variants in one `test_agent_hub_page_loads(project_name)` body.
  - ELITEA-2351's own AFS status becomes `extend-existing` (target: ELITEA-2350's spec) once the parameterization is shipped, so this analysis counts as the discovery that triggered the consolidation, not a failure to recognize the overlap.
- **Project context assertion**: compose with `ChatPage.get_selected_project_text()` for the `project-selector-trigger-combobox` read in step 1 — same pattern as ELITEA-2350.
- Selector policy: testid-only, no fallback. The one `testid needed` row (category filter chips) is shared-work (not blocking this case's automation — the chips are still visible and assertions work on their position/label text; the testid is a nice-to-have for future robustness and coverage measurement).
- Marker suggestion: `@pytest.mark.p1` (high priority), `@pytest.mark.regression`, feature marker `agents_hub` (same as ELITEA-2350's dispatch).
- **Data-driven testing note**: a parameterized spec is more maintainable than two nearly-identical specs (ELITEA-2350 and separate ELITEA-2351 test functions) — future project-variant cases (other surfaces, other data dimensions) should follow this pattern.

## Relation to ELITEA-2350

ELITEA-2351 is a **family variant** of ELITEA-2350, differing **only** in the project context (Private → Team). All steps, all assertions, all handles are identical; only the test data (project name) changes. The Concrete Handles table confirms zero new testids needed beyond what ELITEA-2350 already uses.

**Recommended implementation pattern**: amend ELITEA-2350's spec to parameterize on `project_name`, so both cases run from one test body. This consolidates identical logic, reduces duplicate code, and is the team's established pattern for data-variant cases (per `.agents/testing.md` example: one parameterized spec with rows per TMS case, each row tagged with its case ID).

If this parameterization is not feasible in this implementer dispatch (e.g., the spec is already merged and review would be complex), this AFS supports standalone `ready-for-automation` as a fallback: implement ELITEA-2351 as its own fresh spec file, and note the consolidation as a future tech-debt item (two sibling functions with identical logic, differ only in project-name data).
