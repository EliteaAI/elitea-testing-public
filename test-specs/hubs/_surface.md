# Surface digest: ELITEA Catalog (Agent Hub / Skill Hub)

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface (written during GAP-054 analysis, 2026-07-24,
project `Private`/`${ELITEA_PROJECT_ID}`=399, local `http://localhost:5173`).
`module: hubs` in the coverage-gap ledger covers this whole feature area
(~14 GAP-* cases in batch `cov60`: Agent Hub / Skill Hub detail modals,
export/fork, filters, likes, "My Liked", category pagination). **Zero
existing page object, zero existing tests, zero existing testids** for this
surface as of this digest (confirmed: `grep -rln catalog automation/pages
automation/tests` → no hits) — every hubs-module case is greenfield here.

## Route + navigation

- Page: `EliteaCatalog` component, route **`/elitea-catalog`**
  (`EliteaUI/src/routes.js:78`). No project id in the path — this is a
  project-agnostic route by design (backed by a truly public API endpoint,
  see below).
- Tab selection is a **query param**, not a sub-route: `?tab=agents`
  (default if absent/invalid) or `?tab=skills`
  (`EliteaUI/src/[fsd]/pages/elitea-catalog/EliteaCatalog.jsx:29-32`).
  Navigate directly to `${BASE_URL}/elitea-catalog?tab=agents` /
  `?tab=skills` — no need to click the tab control first.
- `AgentsTab` renders `AgentCategorySection` instances (one per non-empty
  category); `SkillsTab` renders `SkillCategorySection` instances. The two
  section components are **byte-for-byte identical** (only
  `AgentCard`/`SkillCard` differ) — same props, same hooks, same bug
  surface (see § Known defect below).

## Viewport / breakpoint gotcha — DEFAULT vs LARGE_SCREEN display count

`INITIAL_CARD_DISPLAY_COUNT` (`EliteaUI/src/common/constants.js:41`):
`DEFAULT: 6`, `LARGE_SCREEN: 8`. Which applies is gated by
`useMediaQuery(theme.breakpoints.up('prompt_list_xl'))` —
**`prompt_list_xl` = 1800px** (`EliteaUI/src/MainTheme.js:99`). This repo's
own headless viewport (`automation/conftest.py`: `1366×768`) is well under
1800px, so **`DEFAULT=6` always applies in the automated suite** — don't
special-case LARGE_SCREEN unless a test explicitly resizes past 1800px wide.
Confirmed live via `browser-verify` at both 756×469 and 1366×768: same
`DEFAULT=6` initial count both times.

## Category data model — which categories can ever show "Show more"

- **`AgentsTab`** (`useAgentHubData.hooks.js`): all regular category buckets
  (tag-name categories + the `Other` catch-all) are populated from ONE bulk
  fetch (`fetchAllAndCategorize`, `ALL_AGENTS_LIMIT=1000`) and
  `totalCount` is set to `rows.length` — i.e. **`items.length === totalCount`
  ALWAYS for these buckets**. Only `Trending` / `My Liked` use a real
  paginated fetch (`PAGE_SIZE=20`) with a server-declared `total` that can
  exceed what's been fetched so far.
- Confirmed via `GET /elitea_core/public_applications/prompt_lib/` (public,
  project-agnostic endpoint — no project id param) at intake time,
  `statuses=published&agents_type=classic`: **`total: 43`** published
  classic agents system-wide. Client-side bucketing by category tag
  (first matching active-category tag wins, `bucketAppsByCategory`):
  `{"Other": 35, "Business Analyst": 3, "Quality Assurance": 1, "DevOps": 1,
  "Development": 2, "Elitea": 1}` = 43. `Project Management`,
  `Knowledge & Documentation`, `Epam` categories exist
  (`GET /elitea_core/agent_categories/prompt_lib/${ELITEA_PROJECT_ID}`) but
  are currently **empty** (0 items) — `AgentsTab` doesn't render a section
  for an empty bucket, so don't expect to find them live.
- **These counts are LIVE, MUTABLE data** (the `Other` bucket is largely
  test-fixture cruft — `test_agent1/2/3`, `CreateABug`, `Testing Export`,
  `Pytest: Quality Agent`, etc. — dumped there by other automated suites
  that don't set a category tag), **not a seeded fixture** — re-verify the
  count before relying on ">12 items" as a precondition if this digest goes
  stale. As of this writing `Other` (35) and `Trending` (43, all-published
  universe) are both comfortably >12 and the only two candidates for a
  ">initial count" category; every named-tag category (BA/DevOps/
  Development/Elitea/QA) currently has ≤3 items — pick `Other` for
  determinism (regular bucket, no network fetch involved at all) unless a
  case specifically needs the Trending/paginated-fetch code path.

## KNOWN DEFECT (filed, confirmed live 2×) — "Show more" permanently locks after first click

**[EliteaAI/elitea-testing-public#1016](https://github.com/EliteaAI/elitea-testing-public/issues/1016)**
— `AgentCategorySection.jsx` / `SkillCategorySection.jsx`'s toggle binds
BOTH its label and its `onClick` handler to `isExpanded`
(`displayCount > initialDisplayCount`), never to `canShowMore`
(`hasMoreLocally || items.length < totalCount`). Net effect: the FIRST
"Show more" click takes `displayCount` from `initial` → `initial*2` (6→12
default) and the label flips to "Show less" **permanently** from that point
— clicking again only ever collapses back to `initial`, never advances
further, **regardless of how many more items remain**. Confirmed live twice
(fresh navigations) on `Other` (35 total, plateaus at 12) and once on
`Trending` (43 total, same plateau at 12). **Any category with more than
`2 × initialDisplayCount` items (12 default / 16 large-screen) has the
majority of its items permanently unreachable via this control** — this is
NOT a data-availability gap, it's a code defect in the label/handler
ternary. Screenshots in the issue. Any hubs-module case whose steps assume
"click Show more repeatedly to reveal everything" will hit this — the
correct case design (per GAP-054's own literal steps) is ONE expand + ONE
collapse cycle, which behaves correctly and is NOT affected.

**Corollary — the network `onLoadMore`/loading-skeleton branch
(`isLoadingMore`, `Skeleton` placeholders) is structurally unreachable
through user interaction for ANY category in the current codebase**: it only
fires when `handleShowMore` is called with `newDisplayCount > items.length`,
which requires calling `handleShowMore` a SECOND time without an
intervening collapse — impossible per the defect above. Don't spend time
trying to reach this branch via clicking; it needs either a direct
unit/component-level test bypassing the UI toggle, or a product fix to
#1016 first. Any hubs-module case whose steps include this branch should
mark it `blocked` (reason: #1016), not chase test-data volume.

## No page object / testids yet

- No `automation/pages/*.py` file covers `/elitea-catalog` yet. Recommend
  `automation/pages/catalog_page.py`, class `CatalogPage`, with a
  `navigate_to_tab(tab: str)` helper (`self.navigate(f"/elitea-catalog?tab={tab}")`).
- Category sections need **dynamic, per-category testids** (this component
  renders N times on one page) — canonical pattern
  (`.agents/testing.md` § Locator policy):
  ```python
  CATALOG_CATEGORY_SECTION = '[data-testid="catalog-category-section-{}"]'
  CATALOG_CATEGORY_GRID = '[data-testid="catalog-category-grid-{}"]'
  CATALOG_CATEGORY_SHOW_MORE_BUTTON = '[data-testid="catalog-category-show-more-button-{}"]'
  ```
  suffix = category name lowercased + hyphenated (`Other` → `other`,
  `Business Analyst` → `business-analyst`). Add to whichever of
  `AgentCategorySection.jsx` / `SkillCategorySection.jsx` your case's test
  actually exercises — they're separate files/components, so per the
  testid-scope rule (`.agents/role-overrides.md`), only add to the one(s)
  your test touches. GAP-054 (Agents tab, `Other` category) only touches
  `AgentCategorySection.jsx`.
- `AgentCard.jsx` / `SkillCard.jsx` root is a single MUI `<Card>` per item —
  counting `grid.locator(':scope > *')` gives an exact card count (no
  further DOM wrapping to worry about).

## Skills tab — currently almost no test data

Live count at intake: **exactly 1** published skill total
(`figma-code-analysis`, tagged `Business Analyst`, likes=2, also appears
under `Trending`). Far short of the 6-item threshold to render a "Show
more" at all. Any hubs-module case whose precondition needs "a Skills-tab
category with multiple items" is currently **blocked on test data** — note
this per-case rather than re-discovering it; check the live count again
before assuming it's still true.

## Search / query params

`EliteaCatalog` keeps a separate `agentQuery`/`skillQuery` local state per
tab (not URL-synced) — switching tabs does not preserve the other tab's
search text, and reloading the page clears both (session-only, in-memory).
