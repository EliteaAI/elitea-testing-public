# Agent-hub surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Agent Hub / Catalog
surface (`/elitea-catalog`). Not a substitute for execution — verify a handle
as you use it. One writer at a time; last confirmed by: test-automation-engineer
(combined analyst+implementer dispatch), ELITEA-2352, 2026-08-05.

## Category filter-rail chip "selected" state — NO accessible signal existed pre-ELITEA-2352
- Before this dispatch, the filter-rail `Chip` (`CategoryRail.jsx`) had **zero**
  accessible/stable way to detect "selected" state: no `aria-selected`, no
  `aria-pressed`, no `data-*` state attribute — only a computed CSS
  background-color style difference (`styles.selectedChip` vs `styles.chip`).
- **Trap: Playwright's own accessibility-snapshot `[active]` marker on the chip
  is PURE DOM-FOCUS, not the app's selection state** — confirmed live by
  clicking a second chip (focus + `[active]` moved to it, even though the
  first-clicked category remained the actually-filtered one) and by clicking
  an unrelated element like the search input (`[active]` disappeared from the
  still-selected chip). Never assert on `[active]`/focus for this component.
- Fixed this dispatch: added `data-selected="true"/"false"` directly on the
  chip (`EliteaAI/EliteaUI@9b93f67c`, on `automation/testids`, not yet on
  `main`), driven by the same `selectedCategories.includes(category)`
  expression already used for styling. Confirmed live: flips on click,
  persists correctly across focus changes (unlike the `[active]` false
  signal). Combined locator: `[data-testid="catalog-agent-category-filter-chip-{slug}"][data-selected="true"]`.

## Category filtering is actually multi-select at the app-state level (not explored further)
- `handleTagSelect` in `AgentsTab.jsx` toggles `selectedTagNames` as an array
  (add/remove), and `useGroupedCategories`'s own `selectedCategories` follows
  suit — clicking a SECOND chip after a first ADDS its section to the content
  list rather than replacing it (confirmed live: after Business Analyst then
  DevOps, both sections rendered simultaneously). ELITEA-2352 only exercises
  the single-click case, so this wasn't pursued further — relevant to a future
  "filter by multiple categories" sibling case (see below).

## "Reload category items" icon — DOES NOT EXIST (case-text drift, 2nd instance in this family)
- ELITEA-2352's case text (and title) claims a "reload category items" icon
  renders next to the filtered category's section header. **Confirmed absent**
  both visually and via source: `AgentCategorySection.jsx`'s `headerContainer`
  renders only a `Typography` title, and a full-file grep for reload/refresh
  icon components (`RestartAlt`/`SyncIcon`/`ReplayIcon`/`Autorenew`/
  `RefreshIcon`/`CachedIcon`) under `src/[fsd]/features/agent-hub` and
  `src/[fsd]/shared/ui/category` returns 0 hits. The page's only refresh is a
  fully automatic, throttled background refresh (`useCatalogAutoRefresh`) —
  no manual UI trigger anywhere. Filed as
  [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212).
  **Future analysts in this family: expect the same claim to recur** across
  sibling cases (like #1208's "Agent HUB" header text did) — cite #1212 rather
  than re-discovering it.

## Page identity / naming (case-text drift, recurring across the ELITEA-2350..2370+ family)
- The TMS "Agent Hub" family (ELITEA-2350 through at least ELITEA-2370, ~20
  sibling cases filed as GitHub issues #858-#878) all use case text calling
  the surface "Agent HUB". The LIVE product calls it "Catalog" everywhere:
  sidebar nav item text, `<title>` (`"ELITEA Catalog - {project}"` — includes
  the active project name, useful as a free project-context assertion), and
  the page heading `data-testid="catalog-page-heading"` = **"Welcome to
  ELITEA Catalog!"**. `AgentHub`/`/agents-hub` is only a legacy redirect
  source in `routes.js`, never a rendered label. Filed as
  [EliteaAI/elitea-testing-public#1208](https://github.com/EliteaAI/elitea-testing-public/issues/1208)
  (ELITEA-2350); the SAME drift was independently noted (but not filed) in
  the ELITEA-2075 AFS. **Every sibling case in this family will hit the same
  drift** — future analysts: cite #1208 rather than re-discovering/re-filing.
- Route: `/elitea-catalog`. Two tabs at the top (`role=tab`, MUI `BaseTabs`):
  "Agents" (default/selected) and "Skills" — these are the ONLY actual `tab`
  role elements on the page (the case family's "category filter tabs"
  wording refers to a DIFFERENT thing — see below).

## Category filter rail vs. category content-list headings — two different UI elements, same word "category"
- **Content-list headings** (inside the scrollable left column, one per
  rendered category section, e.g. "Trending" above a grid of cards):
  `catalog-category-heading-{slug}` — pre-existing testid,
  `AgentCategorySection.jsx`, already wired into `AgentHubPage.CATEGORY_HEADING`
  / `is_category_section_visible()`. Slug function (confirmed via source):
  `String(category).toLowerCase().replace(/[^a-z0-9]+/g, '-')` — e.g.
  "Business Analyst" → `business-analyst`, "Knowledge & Documentation" →
  `knowledge-documentation` (space + `&` collapse to one hyphen).
- **Filter-rail chips** (right-hand column, `CategoryRail.jsx`, shared between
  `AgentsTab`/`SkillsTab` via `CatalogBody.jsx`): clickable MUI `Chip`s split
  into "Featured" (Trending, My Liked — static constants
  `AgentHubConstants.TRENDING_CATEGORY`/`MY_LIKED_CATEGORY`) and "Categories"
  (Business Analyst, DevOps, Development, Elitea, Epam, Knowledge &
  Documentation, Project Management, Quality Assurance, Other — dynamic, from
  the backend tag list). **Confirmed live, 2026-08-05: this exact 11-item
  list matches the ELITEA-2350 case text verbatim** — no drift here, unlike
  the header text. **ZERO `data-testid`/`testId` anywhere in
  `CategoryRail.jsx`** (confirmed via full-file read +
  `git grep -c "data-testid\|testId"` = 0 on both `origin/main` and
  `origin/automation/testids`) — this is a real, not-yet-added testid gap.
  Because the component is shared across two features (agent-hub, skill-hub),
  it needs a caller-supplied `testId`/`<part>TestId` prop per
  `.agents/testing.md`'s shared-component rule, NOT a hardcoded testid inside
  `CategoryRail.jsx` itself. Recommended shape (not yet implemented as of
  this digest entry): a `chipTestIdPrefix` prop threaded
  `AgentsTab`/`SkillsTab` → `CatalogBody` → `CategoryRail`, each call site
  supplying its own feature-scoped prefix (e.g. agent-hub's own call site:
  `"catalog-agent-category-filter-chip"` → renders
  `catalog-agent-category-filter-chip-{slug}` per chip, same slugify fn as
  the content-list headings for consistency).

## Agent cards
- `catalog-agent-card-{application.id}` — pre-existing dynamic testid,
  `AgentCard.jsx`, already wired into `AgentHubPage.AGENT_CARD_PREFIX` /
  `get_agent_card()`. Default view (no search/filter): 6 cards render under
  "Trending" plus a "Show more" expander (confirmed live, this environment).

## Project context
- Sidebar `project-selector-trigger-combobox` (pre-existing testid, dup'd
  across `admin_users_page.py`/`analytics_page.py`/`chat_page.py`) reads
  "Project: Private" by default for `${TEST_USER}` on localhost — no explicit
  switch needed for "Private project" cases in this family. `ChatPage`
  already exposes `get_selected_project_text()` / `switch_project()` — reuse
  by composition rather than adding a 4th duplicate `LocatorDescriptor`.
  The page `<title>` (`"ELITEA Catalog - {project name}"`) is a free,
  zero-interaction second confirmation of the active project context.

## Known defects (already tracked elsewhere, not re-filed)
- #1043 — Catalog agent-preview modal's "Start Chat" button has no
  `disabled={isFetching}` guard; race condition. Only relevant to cases that
  open an agent's preview modal / start a chat (not this page-load-only
  family member).
- #1016 — Catalog category "Show more" permanently locks to collapse after
  first click. Only relevant to cases that interact with "Show more".

## Sibling family (not yet analysed as of this entry)
ELITEA-2351 ("Team project" variant of this exact case — differs from
ELITEA-2350 only in which project is active, a DATA difference per the
family-vs-separate test) plus ~18 more behavioral cases (filter by
category/multiple categories, like/unlike, open/close modal, search,
start-conversation flows, etc. — GitHub issues #859-#878). A future batch
covering the whole family should re-check whether ELITEA-2350/2351 belong in
one parameterized family AFS (project name as the only variable) rather than
two near-identical specs — this dispatch analysed ELITEA-2350 alone, not as
a cluster, so no family-AFS merge was performed here.
