# Test Case: Catalog — Category section "Show more"/"Show less" pagination expands and collapses cards

## Metadata
- **TMS ID**: GAP-054 (coverage-gap ledger case, board `cov60`; no onetest TMS
  entry — local-file-backed per campaign decision, `.agents/automation-board/campaigns/cov60.md` #6)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399, viewport 1366×768 (matches
  `automation/conftest.py` headless default)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — all 7 of the case's core steps
  executed end-to-end against the live system and PASS exactly as the case's
  own Pass/Fail criteria describe (single expand + single collapse cycle).
  Step 8 (the network-driven loading-skeleton branch) is `blocked` — see
  § Blocked Steps — but does not invalidate the rest of the case (tail-only,
  per `.agents/testing.md` § Merge gate "Analysis-time entry" allowance). A
  genuine, confirmed, reproducible product defect was found DURING
  exploration (not asked for by the case's own steps) and filed as
  [#1016](https://github.com/EliteaAI/elitea-testing-public/issues/1016) —
  see § Known Defects; it does not block this case's steps and no
  masking/soft-assert was needed since the case's own literal wording never
  conflicts with it.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A category on the Agents tab holds more than `INITIAL_CARD_DISPLAY_COUNT.DEFAULT`
  (6) items. **Confirmed live**: the `Other` category (the catch-all bucket
  for published agents with no matching named-category tag) currently holds
  **35** items — comfortably >12, so the test's exact-count assertions
  (6 → 12 → 6) are robust to normal fluctuation in this incidental,
  non-fixture-seeded bucket (see § Test Data — this is LIVE, mutable data,
  not seeded; re-verify the count is still >12 if this AFS goes stale).
  Viewport must stay below the `prompt_list_xl` breakpoint (1800px) so
  `INITIAL_CARD_DISPLAY_COUNT.DEFAULT=6` applies, not `LARGE_SCREEN=8`
  (`test-specs/hubs/_surface.md` § Viewport gotcha) — the suite's own
  1366×768 headless default already satisfies this.

## Test Data
### reuse-existing
- The `Other` category on the Agents tab (`${BASE_URL}/elitea-catalog?tab=agents`),
  read-only. Live count at analysis time: **35** total items (bucketed via
  `GET /elitea_core/public_applications/prompt_lib/?statuses=published&agents_type=classic`,
  `total: 43` system-wide, client-bucketed by category tag — `Other` = 43
  minus the 8 items claimed by named categories). This is incidental
  test-fixture cruft from other automated suites (`test_agent1/2/3`,
  `CreateABug`, `Testing Export`, `Pytest: Quality Agent`, etc.), not a
  seeded fixture — nothing to create or clean up for this case. No new data
  generated.

## Test Steps
1. Navigate to `${BASE_URL}/elitea-catalog?tab=agents`.
   - **Verify — PASSES.** Page loads (`Page Title: "ELITEA Catalog - Private"`);
     category sections render: `Trending`, `Business Analyst`, `DevOps`,
     `Development`, `Elitea`, `Quality Assurance`, `Other` (the 3 currently
     empty categories — `Project Management`, `Knowledge & Documentation`,
     `Epam` — correctly render no section). The `Other` category's grid
     renders **exactly 6 cards** (`INITIAL_CARD_DISPLAY_COUNT.DEFAULT`).
2. Assert the `Other` category's toggle reads **"Show more"** (not expanded;
   `canShowMore` true since 6 of 35 items are visible).
   - **Verify — PASSES.** Toggle text = `"Show more"`.
3. Click the `Other` category's toggle.
   - **Verify — PASSES.** `displayCount` increases from 6 to 12
     (`handleShowMore`: `6 + INITIAL_CARD_DISPLAY_COUNT.DEFAULT`); grid now
     renders 12 cards. `Other` is a regular (non-paginated) bucket —
     `totalCount === items.length` always for it (`fetchAllAndCategorize`
     sets `total = rows.length`), so `onLoadMore` is never invoked and no
     network request fires on this click — confirmed via console/DOM
     inspection, purely client-side re-slice.
4. Assert the grid now shows more than the initial 6 cards.
   - **Verify — PASSES.** Card count = 12 (`min(displayCount=12, totalCount=35)`
     = 12). Reproduced identically across 2 independent fresh-navigation
     attempts.
5. Assert the toggle now reads **"Show less"** (`isExpanded` true:
   `displayCount(12) > initialDisplayCount(6)`).
   - **Verify — PASSES.** Toggle text = `"Show less"`.
6. Click the `Other` category's toggle again (now reads "Show less").
   - **Verify — PASSES.** `handleShowLess` resets `displayCount` to 6.
7. Assert the grid collapses back to exactly the initial 6 cards, and the
   toggle label flips back to "Show more" (`canShowMore` still true — 6 of
   35 visible).
   - **Verify — PASSES.** Card count = 6; toggle text = `"Show more"`.
   - **Enrichment (see Axis 2):** clicked the toggle a 3rd time to confirm
     it re-expands to exactly 12 again (not, e.g., 18) — reproduced
     identically both fresh-session attempts. This is the live evidence
     behind the known defect below, but is captured here as a plain
     data point, not asserted as a live in-test check (see Axis 2 for why).
8. (Loading branch) While `isLoadingMore` is true, assert the toggle is
   hidden and `Skeleton` placeholders render.
   - **BLOCKED — see § Blocked Steps.** Not a data-availability gap:
     structurally unreachable through user interaction in the current code,
     because of the very defect filed as #1016 (see § Known Defects) — the
     toggle can never be clicked a second time in the "expand" direction
     without an intervening collapse, so `handleShowMore`'s
     `newDisplayCount > items.length` condition (the gate for `onLoadMore`)
     can never be satisfied via clicking, on ANY category (paginated or not).

## Coverage Map

### Axis 1 — case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: category with more items than initial count exposes "Show more", reveals cards, collapses via "Show less" | full cycle works | Steps 1–7 | card-count + toggle-text assertions each step | asserted |
| Precondition: category holds more entities than `INITIAL_CARD_DISPLAY_COUNT` | such a category exists | Preconditions / Step 1 | `Other` = 35 live, confirmed via API + DOM | asserted |
| Test Data: `INITIAL_CARD_DISPLAY_COUNT.DEFAULT=6` / `LARGE_SCREEN=8` at `prompt_list_xl` | correct count applies per viewport | Step 1 | 6 cards rendered at 1366×768 (< 1800px breakpoint) | asserted |
| Test Data: `shouldShowButton = (canShowMore \|\| isExpanded) && !isLoadingMore` | toggle visibility gate | Steps 2, 5, 7 | toggle present/visible at each step | asserted |
| Test Data: `displayCount += initialDisplayCount` per Show more | +6 per click | Step 3→4 | card count 6→12 | asserted |
| 1 Open category section exceeding initial count | grid renders exactly initial N | Step 1 | card count = 6 | asserted |
| 2 Assert toggle reads "Show more" | visible, correct label | Step 2 | toggle text | asserted |
| 3 Click "Show more" | `handleShowMore` fires; cards render; loading branch if network needed | Steps 3–4 (expand) / Step 8 (loading sub-branch) | card count 6→12 / — | asserted (expand) / **blocked** (loading sub-branch, #1016) |
| 4 Assert grid shows more than N cards | count > 6 | Step 4 | card count = 12 | asserted |
| 5 Assert toggle reads "Show less" | label flips | Step 5 | toggle text | asserted |
| 6 Click toggle (now "Show less") | `handleShowLess` fires | Step 6 | — (state transition, asserted at Step 7) | asserted |
| 7 Assert grid collapses to exactly initial N cards | count = 6 | Step 7 | card count = 6 | asserted |
| 8 (Loading branch) toggle hidden while `isLoadingMore` | not shown mid-fetch | — | — | **blocked** — see § Blocked Steps (#1016, not a data gap) |
| Expected Final State: expanded then collapsed, label tracked state throughout | full cycle correct | Steps 1–7 | all of the above | asserted |
| Pass criteria: "Show more reveals additional cards and flips label; Show less returns to exactly initial count" | — | Steps 3–7 | card counts + toggle text at each transition | asserted |
| Pass criteria: "control hidden while in-flight load is loading more" | — | — | — | **blocked** (#1016) |
| Fail criteria: negative conditions (no reveal / no toggle / no collapse) | none observed | Steps 3–7 | — | asserted (none of the fail conditions triggered) |

### Axis 2 — analyst additions

- Step 7's "enrichment" (3rd click re-expanding to exactly 12, never 18) is
  recorded as a **plain observation**, not encoded as a live in-test
  assertion — *reason: proving the defect robustly would require asserting
  against the exact live total (35, or 43 for Trending), which is
  incidental shared-suite cruft that other automated tests continually
  create/delete; coupling this test's pass/fail to that volatile shared
  count is a flakiness risk out of proportion to this case's own scope. The
  filed issue (#1016) plus this AFS's plain-observation note are the
  honest record; a dedicated regression test with controlled fixture data
  (seed exactly N>12 agents into an isolated throwaway category) is a
  reasonable follow-up but is new scope, not an "enrichment" of this case.*
- Zero console errors/warnings check across all 7 steps (project
  convention — never skip the side-channel check even when the UI looks
  fine) — clean both fresh-session runs, confirmed via `browser-verify get-console`.
- Confirmed the exact same click-and-observe sequence twice in independent
  fresh navigations (not a single lucky run) — *added: this component's
  behavior is genuinely surprising (a "show more" that can only ever expand
  once), so a single observation risked being a fluke; reproduced
  identically both times before trusting it enough to file #1016.*

## Cleanup
None required. Read-only exploration against existing published agents
(`Other` category) — nothing created, edited, or deleted.

## Concrete Handles (discovered during exploration)

**No page object exists yet for `/elitea-catalog`** — this is a brand-new
surface (confirmed: `grep -rln catalog automation/pages automation/tests` →
no hits). Recommend `automation/pages/catalog_page.py`, class `CatalogPage`.

**Testid-only policy** (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) — no fallback rung. `AgentCategorySection.jsx`
renders once per category on one page, so the container/grid/toggle need
**dynamic, per-category testids** (canonical pattern, not a static id —
a static `catalog-category-section` would match all 7 rendered sections
ambiguously):

| Element | Recommended Locator | Fallback | Status |
|---|---|---|---|
| `Other` category section container | `testid needed: catalog-category-section-other` (dynamic pattern: `[data-testid="catalog-category-section-{}"]`.format("other")) | N/A — testid-only policy, no fallback rung permitted | needs-adding |
| `Other` category grid (cards container) | `testid needed: catalog-category-grid-other` (`[data-testid="catalog-category-grid-{}"]`.format("other")) | N/A | needs-adding |
| `Other` category Show more/less toggle | `testid needed: catalog-category-show-more-button-other` (`[data-testid="catalog-category-show-more-button-{}"]`.format("other")) | N/A | needs-adding |
| Card count (within the grid) | `grid_locator.locator(':scope > *')` `.count()` — confirmed `AgentCard.jsx`'s root is a single MUI `<Card>` per item, no extra DOM wrapping | N/A | confirmed via live count |

**Testids to add — `AgentCategorySection.jsx` ONLY.** Per the testid-scope
rule (`.agents/role-overrides.md` § Every role — locator policy: "scope is
exactly the elements the case's test touches"), this test only exercises
the Agents tab / `AgentCategorySection.jsx`. `SkillCategorySection.jsx` is a
byte-for-byte identical **separate file/component** that this test never
renders (Skills tab currently has only 1 skill total — far short of the
threshold to even show a "Show more", see `test-specs/hubs/_surface.md` §
Skills tab) — do **not** add matching testids there for this case; that's
follow-up work for whichever future hubs-module case actually exercises the
Skills tab with sufficient data. (This deliberately narrows the original
case-source note "add in both AgentCategorySection.jsx and
SkillCategorySection.jsx" — declared here per
`.agents/role-overrides.md` § Declared-improvisation protocol: the raw case
text pre-dated live verification of testid-scope and Skills-tab data
availability.)

Dynamic testid naming, class-level constants (per `.agents/testing.md` §
Locator policy "Dynamic testid — canonical pattern"):
```python
# class level, e.g. in a new CatalogPage
CATALOG_CATEGORY_SECTION = '[data-testid="catalog-category-section-{}"]'
CATALOG_CATEGORY_GRID = '[data-testid="catalog-category-grid-{}"]'
CATALOG_CATEGORY_SHOW_MORE_BUTTON = '[data-testid="catalog-category-show-more-button-{}"]'
```
Suffix = category name lowercased + hyphenated (this case: `"other"`, from
`AgentHubConstants.OTHER_CATEGORY = 'Other'`).

## Network Behavior
- `GET /elitea_core/applications/prompt_lib/${ELITEA_PROJECT_ID}?...` (or
  the public equivalent the Agents tab actually calls,
  `fetchAllAndCategorize` → `useLazyPublicApplicationsListQuery`) — fires
  once on Step 1 navigate, populates ALL category buckets (including
  `Other`) in one bulk response. No further network call fires on Steps 3
  or 6 (client-side re-slice only) — this is the concrete evidence that
  `Other` is a regular (non-paginated) bucket, not the `Trending`/`My Liked`
  paginated path.

## Known Defects Found During Exploration
- **[MAJOR] [#1016](https://github.com/EliteaAI/elitea-testing-public/issues/1016)**
  — `AgentCategorySection.jsx` / `SkillCategorySection.jsx`'s "Show more"
  toggle binds its label AND `onClick` handler to `isExpanded` alone, never
  to `canShowMore`. The FIRST expand click permanently flips the control to
  "Show less"-only — a second `handleShowMore` call (and, for
  Trending/My-Liked, its network `onLoadMore` branch) is structurally
  unreachable without an intervening collapse, and collapsing+re-expanding
  always returns to the SAME `initial×2` ceiling. Confirmed live twice
  (fresh navigations) on `Other` (35 total → plateaus at 12) and once on
  `Trending` (43 total → same plateau). Does **not** block this case's own
  literal steps (single expand/collapse cycle passes cleanly, matching the
  case's own Pass/Fail criteria exactly) — filed as a bonus finding, not
  masked, not soft-asserted in this test (see Axis 2 for why no live
  assertion was added).

## Blocked Steps
- **Step 8** ("(Loading branch) while `isLoadingMore` is true, assert the
  toggle is hidden") — structurally unreachable via user interaction in the
  current codebase, root-caused to defect #1016 (not a test-data
  availability gap — even `Trending`, whose paginated fetch COULD in
  principle leave `items.length < totalCount`, can never have
  `handleShowMore` called a second time to trigger `onLoadMore`, because
  the toggle locks to "collapse" after the first click). Unblocks when
  #1016 is fixed upstream; the implementer should skip this assertion
  entirely rather than attempt to force it via non-UI means (no direct
  Redux-store manipulation / no synthetic prop injection — out of scope
  for an E2E UI test).

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- New page object: `automation/pages/catalog_page.py`, class `CatalogPage`,
  extending `BasePage`. Suggested methods:
  - `navigate_to_tab(tab: str)` → `self.navigate(f"/elitea-catalog?tab={tab}")`
  - `category_grid(category_slug: str)` → `self.page.locator(self.CATALOG_CATEGORY_GRID.format(category_slug))`
  - `category_show_more_button(category_slug: str)` → same pattern
  - `get_category_card_count(category_slug: str) -> int` → `.locator(':scope > *').count()` on the grid locator
  - `toggle_show_more(category_slug: str)` → click the show-more-button locator
- Wait strategy: Playwright's own `expect(...).to_have_count(n)` auto-retry
  is sufficient after each click — no explicit network wait needed for the
  `Other` category (purely client-side re-slice, confirmed above); avoid
  fixed `sleep`/`wait_for_timeout` per `.claude/rules/ui-tests.md`.
- Suggested test-data approach: read-only against the live `Other` bucket.
  Before asserting exact counts, consider a quick pre-test sanity check
  (`assert get_category_card_count('other') >= 6`, or query the same public
  API endpoint) rather than hardcoding "35" anywhere — this AFS's exact
  counts (35 total / 12 expanded) are a snapshot, not a seeded invariant;
  only "> 12" is actually required for this test's assertions to hold.
- Category-slug helper: lowercase + hyphenate the category display name
  (`"Other"` → `"other"`) — if a shared slugify helper doesn't already
  exist in `automation/utils/`, a simple inline `.lower().replace(' ', '-')`
  is sufficient for this fixed, known set of category names (no unicode/
  punctuation edge cases in practice).
- Full surface context (viewport gotcha, category data model, the #1016
  defect writeup, Skills-tab data gap): `test-specs/hubs/_surface.md` — read
  it before implementing, it was written as part of this analysis.
