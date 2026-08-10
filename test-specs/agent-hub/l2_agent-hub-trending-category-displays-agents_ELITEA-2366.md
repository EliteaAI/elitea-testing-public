---
status: ready-for-automation
priority: medium
family_afs: false
afs_version: 1.0
tms_id: ELITEA-2366
tms_link: "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agent-hub/ELITEA-2366.md"
---

# ELITEA-2366: Agent Hub — Trending category displays agents

**AFS Status:** `ready-for-automation`  
**Implementer Instructions:** The case text refers to a "Reload the category items" icon which does **not exist** in the live product (verified 2026-08-10, filed as [#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212)). Test only the assertions that match live product: section header "Trending" appears, and agents are displayed under it. The "reload" step is omitted per reverse-masking guard — case-text drift → CLARIFICATION, not a product defect.

---

## Preconditions

- User is logged in to the Elitea platform via test auth state
- Default project is "Private"

---

## Test Coverage

| Case Element | Observable | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Navigate to Agent Hub | Page loads successfully | `ChatPage.navigate("/elitea-catalog")` + wait for page heading | test body, Step 1 | `ready` |
| Step 2: Click "Trending" filter (implicit: verify default view shows it) | Filter button present, clickable | inspect filter rail for "Trending" button | Step 2 | `ready` |
| Step 3: Verify tab is highlighted/active | "Trending" button shows selected state (`data-selected="true"`) | click "Trending" + read `data-selected` | Step 3 | `ready` |
| Step 4: Verify agents display under Trending | ≥1 agent card renders in Trending section | query `catalog-agent-card-*` within Trending section | Step 4 | `ready` |
| Step 5 — CASE-TEXT DRIFT: "Reload the category items" icon | Icon exists next to header | [#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212): CONFIRMED ABSENT — no reload/refresh icon exists anywhere on the page; only automatic background refresh via `useCatalogAutoRefresh` (no manual UI trigger) | test description, class docstring | `disposition: clarification filed as #1212` |
| **CORRECTED Step 5:** Section header "Trending" appears above results | "Trending" text visible in section header container | read `catalog-category-heading-trending` text content | Step 5 (amended) | `ready` |

---

## Concrete Handles

| Element | Locator | Fallback | Provenance | Status |
|---|---|---|---|---|
| Page heading | `get_by_text("Welcome to ELITEA Catalog!")` | `data-testid="catalog-page-heading"` | pre-existing, on-automation/testids | on-testids ✓ |
| "Trending" filter button | `button >> text="Trending"` (in filter rail) | inspect filter-rail section "Featured", first button | _surface.md: Featured section lists `Trending` / `My Liked` as static chips | standard MUI Chip |
| Trending section header | `data-testid="catalog-category-heading-trending"` | `get_by_text("Trending")` within content area | _surface.md § Category filter rail vs. category content-list headings; slugify: `String("Trending").toLowerCase()` = `trending` | pre-existing, on-testids ✓ |
| Trending section container | `page.locator("div:has-text('Trending')").first()` parent `generic` | nth section by role | none — section structure via DOM nesting | generated, not testid'd |
| Agent card (dynamic) | `data-testid="catalog-agent-card-{id}"` | `get_by_role("button").filter(has=...)` | _surface.md: `AgentCard.jsx` wires testid; id = application.id | pre-existing; e.g. `catalog-agent-card-1`, `catalog-agent-card-8` |
| Filter button selected state | `[data-selected="true"]` on Trending button | CSS computed style (background color) | _surface.md (ELITEA-2352): `data-selected` attribute added; flips on click | live, confirmed ELITEA-2352, pending main merge |

---

## Observed Product Behavior

1. **Page loads with "Trending" category as the default view.** The Trending section header and 6 agent cards render immediately (Business Analyst, Assistant for ELITEA Documentation, Reflexion, Quality Engineering Sidekick, API Testing Buddy, Scalpel) plus a "Show more" expander.

2. **Filter rail (right column):** "Featured" section lists two buttons: "Trending" and "My Liked". "Trending" button is present and clickable. Clicking it cycles the `data-selected` attribute (confirmed ELITEA-2352 flow).

3. **Section header styling:** The "Trending" text is a plain Typography element in the section header container. **NO reload/refresh icon exists next to it.** Full source inspection (`AgentCategorySection.jsx`) confirms only a `Typography` renders in `headerContainer` — zero icon elements. This is the same root cause as #1212 ("Business Analyst" instance).

4. **Only automatic refresh exists:** The page's sole refresh mechanism is `useCatalogAutoRefresh()` (throttled background polling) — no manual UI trigger anywhere on the surface.

5. **Agent cards:** Each card carries `data-testid="catalog-agent-card-{id}"`. Like button shows `data-liked="true"/"false"` (ELITEA-2355). Card onclick opens the agent preview modal.

---

## Expected Results

**Step 1:** Page `/elitea-catalog` loads with heading "Welcome to ELITEA Catalog!" visible. ✓

**Step 2:** "Trending" filter button is present in the filter rail's "Featured" section. ✓

**Step 3:** Clicking the Trending button (if not already selected) sets `data-selected="true"` on it. ✓

**Step 4:** Trending section displays with header "Trending" and ≥1 agent card visible under it (minimum: Business Analyst visible or any agent id from the live Trending list). ✓

**Step 5 (amended):** Section header text "Trending" is visible and readable above the agent card grid. **NO reload icon is asserted** (case-text drift filed as #1212 — this spec asserts only what exists in the live product).

---

## Known Defects

- **#1212** — "Reload category items" icon claimed in case text does not exist in product. Automatic background refresh only; no manual UI trigger. Cited by ELITEA-2365 (same family, "My Liked" section drift). Do not re-file.
- **#1215** — Like/unlike clicks fire a Redux console error (`non-serializable value`). Minor, non-blocking; already tracked. Relevant if test likes/unlikes an agent.

---

## Test Execution Notes

- **Auth:** Use default `auth_state` (Keycloak skipped on localhost via `VITE_DEV_TOKEN`).
- **Project:** Test runs under `project_user_659` ("Private" project, default for `${TEST_USER}`).
- **Wait strategy:** Page heading "Welcome to ELITEA Catalog!" is the readiness signal (content is populated after this text appears).
- **No teardown needed:** The test is read-only; no agent liking, no state mutation, no cleanup.

---

## Clarification Issue

**Related:** [#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) — case text across this family (ELITEA-2356 through ELITEA-2369) uses "CONVERSATION STARTERS" and "Start conversation"; live product reads "CHAT STARTERS" and "Start Chat" (`AgentConversationStarters.jsx`, `AgentModal.jsx`). Cite instead of re-filing.
