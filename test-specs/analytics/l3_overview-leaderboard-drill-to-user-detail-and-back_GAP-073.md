# Test Case: Analytics — Overview: clicking a Top 5 AI Adopters row drills into the user detail and Back returns to Overview

## Metadata
- **TMS ID**: GAP-073 (coverage-gap ledger case, board `cov60`; no onetest TMS
  entry — local-file-backed per campaign decision, `.agents/automation-board/campaigns/cov60.md`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399. Driven via an isolated `browser-verify` (CDP)
  Chrome instance on a dedicated port/profile — the shared Playwright MCP
  browser (lane 0) was already held by a concurrent session at dispatch time,
  so this run fell back to an isolated instance per
  `.agents/role-overrides.md` § browser lane discipline. Viewport was the
  CDP headless default (756×469) — irrelevant here: the KPI row is
  `repeat(auto-fit, minmax(9rem,1fr))` (wraps at any width) and the
  leaderboard is single-column; no breakpoint-sensitive assertion in this case.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture normally
  skips login via `VITE_DEV_TOKEN`; this exploration hit the dev server
  directly with no separate login step needed, confirming the same bypass).
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — all 7 steps executed end-to-end
  against the live system and PASS exactly as the case's own Pass/Fail
  criteria describe. No defects found; the case text matches live behavior
  precisely (including the exact prose of the cross-tab handler names in
  the case's own Steps column — confirmed against source, not just guessed).

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- The `Private` project has AI activity in the last-30-days range so the
  "Top 5 AI Adopters" leaderboard renders >= 1 row. **Confirmed live**: with
  the `Last 30d` preset, the leaderboard renders exactly **1 row** —
  `testbot@elitea.ai` (2.4K LLM · 871 Tool · 786 Agent = 4.1K AI events).
  This is incidental shared-suite activity data (other automated tests'
  agent/tool/LLM runs against this dev project), not a seeded fixture —
  nothing to create or clean up. The default preset on page load is
  `Last 24h` (`selectedDatePreset` initial state = `1`) — the test MUST
  select `Last 30d` explicitly (case's own Test Data table already says so)
  or the leaderboard may render 0 rows depending on when tests last ran
  against this shared project.

## Test Data
### reuse-existing
- Date range preset: `Last 30d` (`DATE_FILTER_PRESETS` value `30`,
  `AnalyticsContainer.jsx:30`) — click target text is literally `"Last 30d"`.
- `user_email` of the first leaderboard row — captured at runtime, not
  hardcoded (confirmed live value at analysis time: `testbot@elitea.ai`,
  but this is shared-suite data that will drift; the AFS/test must read it
  from the DOM, never assert the literal string).

## Test Steps
1. Navigate to `${BASE_URL}/settings/analytics` (confirmed live route — the
   case text says "Navigate to the Analytics page"; the actual path is a
   **Settings sub-route**, not a top-level `/analytics`: `AnalyticsContainer`
   is mounted at `path="analytics"` nested under `RouteDefinitions.Settings`
   = `/settings`, `ProtectedRoutes.jsx:359-362`). The Overview tab (index 0)
   is active by default. Select the `Last 30d` date preset.
   - **Verify — PASSES.** KPI row renders (`TEAM 11 of 11 active members`,
     `AI ACTIVE 1 ↑9.1% 9.1% adoption`, `LLM CALLS 2.4K`, `TOOL RUNS 871`,
     `CHAT MSG 1.5K`, `AGENT RUNS 786`) and the "Top 5 AI Adopters" card
     renders with 1 leaderboard row (`testbot@elitea.ai`).
2. Capture the email text of the first leaderboard row.
   - **Verify — PASSES.** Captured `testbot@elitea.ai` for the Step 4
     title assertion below.
3. Click the first leaderboard row.
   - **Verify — PASSES.** The Users tab (`[role=tab]` index 3, `aria-selected`
     confirmed flips `false→true` on the "Users" tab specifically, all
     other tabs stay `false`) becomes active and renders the clicked
     user's detail view directly — confirmed via source
     (`AnalyticsContainer.handleOverviewUserClick` → `setPendingUserId(userId)`
     + `setActiveTab(3)`; `AnalyticsUsers` receives `initialUserId={pendingUserId}`,
     lazily seeds `selectedUserId` from it on mount, so it renders
     `AnalyticsUserDetailed` on the FIRST render — the User Activity list
     never flashes).
4. Assert the user-detail title text equals the captured email, and the six
   user KPI cards are visible.
   - **Verify — PASSES.** Title text = `testbot@elitea.ai` (exact match to
     Step 2's captured value). Six KPI cards render with labels exactly
     `LLM Calls` / `Tool Calls` / `Chat Msg` / `Agent Runs` / `Active Days` /
     `Errors` (`AnalyticsUserDetailed.jsx:64-90`) — live values at analysis
     time: `2.4K` / `871` / `1.5K` / `786` / `31` / `1.8K` respectively
     (values are shared-suite live data, not asserted literally by this
     case — only visibility + label are).
5. Assert the Users tab did NOT land on the User Activity list.
   - **Verify — PASSES.** The strings `"User Activity"` and `"Search by
     email"` are absent from the page text while on this view — confirmed
     via full-page `textContent` diff. Structurally guaranteed, not just
     incidentally true: `AnalyticsUsers.jsx`'s `if (selectedUserId) return
     <AnalyticsUserDetailed .../>` is an early return — the User Activity
     list JSX (table header + `StyledSearchInput`) is never constructed at
     all when a `selectedUserId` is set, so this isn't a visibility toggle
     that could regress into "both render" — it's mutual exclusion by
     control flow.
6. Click the detail Back arrow (the `IconButton` beside the user-email title,
   `AnalyticsUserDetailed.jsx:49-55`, `ArrowBackIcon`).
   - **Verify — PASSES.** `handleBack` in `AnalyticsUsers.jsx` checks
     `cameFromExternal` (a `useState(() => !!initialUserId)` lazy initializer
     — captures whether we arrived via the cross-tab click, frozen at mount,
     immune to later `pendingUserId` clears) → true → calls
     `onBackToSource()` = `handleBackToOverview` → `setPendingUserId(null)` +
     `setActiveTab(0)`.
7. Assert the Overview tab is active again with KPI cards + leaderboard
   visible.
   - **Verify — PASSES.** `[role=tab]` "Overview" flips back to
     `aria-selected="true"`; full KPI row + Top 5 AI Adopters leaderboard
     (same 1 row, `testbot@elitea.ai`) re-render identically to Step 1 —
     confirmed NOT the Users list (no "User Activity"/"Search by email"
     text either).

## Expected Results
- Leaderboard row click switches to the Users tab and renders that user's
  detail directly (title = clicked email, six KPI cards visible), bypassing
  the User Activity list entirely.
- Detail Back button returns to the Overview tab (KPI cards + leaderboard),
  not to the Users list — proving the `cameFromExternal` / `onBackToSource`
  branch fires, distinct from the native Users-tab drill-down whose Back
  returns to the list (`cameFromExternal=false` path, out of scope for this
  case — see Axis 2).
- No console errors during the full cycle.

## Coverage Map

### Axis 1 — case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: leaderboard row click → Users tab pre-loaded on that user's detail; Back → Overview (not Users list) | full round-trip works | Steps 1–7 | title + KPI-visibility + absence assertions at each step (content-based proxy — see Axis 2 note on tab-selection state) | asserted |
| Precondition: project has AI activity in range so leaderboard renders >= 1 row | leaderboard >= 1 row | Preconditions / Step 1 | live-confirmed 1 row (`testbot@elitea.ai`) with `Last 30d` | asserted |
| Precondition: testids added (leaderboard rows, back button+title, TEAM KPI card) | — | N/A | **none exist yet** — see § Concrete Handles; this precondition is actually the implementer's own work item, not a pre-existing fact | disposition: `clarification` (see Axis 2 — case-text treats testids as already-added; live repo has zero) |
| Test Data: date preset `Last 30d` ensures >= 1 row | — | Step 1 | leaderboard renders 1 row after preset click | asserted |
| Test Data: starting tab Overview (index 0) | default tab | Step 1 | Overview active on load | asserted |
| Test Data: user email captured at runtime | — | Step 2 | captured value used in Step 4 assertion | asserted |
| Test Data: expected user KPI cards (LLM Calls, Tool Calls, Chat Msg, Agent Runs, Active Days, Errors) | all six visible | Step 4 | six KPI cards with matching labels, confirmed live | asserted |
| 1 Navigate; wait for KPI cards + leaderboard | both visible | Step 1 | `analytics-overview-kpi-team` (needs-adding) + leaderboard row visible | asserted |
| 2 Capture first leaderboard row's email | recorded | Step 2 | DOM read of leaderboard row text | asserted |
| 3 Click first leaderboard row | switches to Users tab (index 3), renders detail directly | Step 3 | `analytics-user-detail-title` visible immediately after the click (content-based proxy for the tab switch — **corrected 2026-07-24, fix-round finding on PR #1061**: no `[role=tab][aria-selected]` assertion exists in the shipped test; see Axis 2 note) | asserted |
| 4 Assert title = captured email + six KPI cards visible | title + 6 cards | Step 4 | title text match + 6 KPI cards labels | asserted |
| 5 Assert Users tab did NOT land on User Activity list | list header/search absent | Step 5 | absence of "User Activity"/"Search by email" text | asserted |
| 6 Click detail Back arrow | `cameFromExternal` branch fires → Overview | Step 6 | verified at Step 7 (KPI/leaderboard re-render + list-text absence) | asserted |
| 7 Assert Overview tab active again (KPI + leaderboard) | back on Overview, not Users list | Step 7 | `analytics-overview-kpi-team` + leaderboard-row visibility re-render + users-list-title/search-input absence (content-based proxy — **corrected 2026-07-24**: no `[role=tab][aria-selected]` assertion exists in the shipped test; see Axis 2 note) | asserted |
| Expected Final State: back on Overview with KPI + leaderboard, no data created/modified, no cleanup | — | Step 7 | same as above; read-only exploration | asserted |
| Pass criteria (leaderboard clickable, correct user/detail, bypasses list, Back → Overview not list) | — | Steps 3–7 | as above | asserted |
| Fail criteria (row not clickable / wrong user / list shown / Back → wrong place) | none observed | Steps 3–7 | none of the fail conditions triggered | asserted |

### Axis 2 — analyst additions

- **Route correction (case-text drift, not a defect — reverse-masking
  guard):** the case says "Navigate to the Analytics page" without
  specifying the path. Live confirmed route is `/settings/analytics`
  (Analytics is a Settings sub-route, not top-level) — added as an explicit
  Step 1 detail because a literal `/analytics` navigation 404s
  ("Page not found", confirmed live). Filed as a case-text clarification
  rather than reclassifying the case, per `.agents/testing.md` §
  Reverse-masking guard — the live product is correct, the case's phrasing
  was just underspecified. See § Known Defects — no product defect, just
  a clarification note.
- **Preconditions row "testids added"** is aspirational in the case text,
  not a verified live fact — confirmed via source read
  (`AnalyticsOverview.jsx`, `AnalyticsUserDetailed.jsx`, `AnalyticsUsers.jsx`,
  `KpiCard.jsx`) that **zero** `data-testid` attributes exist anywhere in
  this flow today. Not softened to a defect (testid gaps are implementer
  work per `.agents/role-overrides.md` § Analyst slot, not a MINOR note) —
  captured plainly in § Concrete Handles with full naming + provenance so
  the implementer's `add-data-testid` pass has an exact work order.
- Zero console errors across the full 7-step cycle — confirmed via
  `browser-verify get-console` (project convention: never skip the
  side-channel check even when the UI looks fine).
- Confirmed the tab-selection state (`[role=tab][aria-selected]`) rather
  than relying on visual/text-only cues for "which tab is active" — a more
  robust automation signal than eyeballing which panel rendered, and it's
  what a Playwright `expect(tab).to_have_attribute('aria-selected', 'true')`
  would assert. **Correction added 2026-07-24 (fix-round finding on PR
  #1061):** this bullet describes what was confirmed manually during
  *analysis* (a live source read + DOM check), NOT an automated assertion
  the shipped test performs. The source case's own "Testids to add" list
  (`.agents/automation-board/batches/cov60/cases/GAP-073/source.md`) never
  requested a tab-selection testid, and neither did this AFS's § Concrete
  Handles table — so no `[role=tab][aria-selected]` locator exists under
  the testid-only locator policy (`.agents/testing.md` § Locator policy;
  a raw `[role=tab]` selector would itself be a locator-policy violation).
  The shipped test instead proves the tab switch through a **content-based
  proxy**: Step 3 asserts `analytics-user-detail-title` is visible
  immediately after the click, and Step 4/5 assert the title equals the
  captured email + six KPI cards render + the native Users-list is absent.
  This is a structurally valid substitute, not a weaker one — per source,
  `AnalyticsUserDetailed` only renders when `AnalyticsUsers` is mounted
  under the Users tab (`activeTab === 3`) AND `selectedUserId`/
  `pendingUserId` is set; there is no code path that renders the user-detail
  title while any other tab is active. Declared improvisation (no canon
  pattern requests a testid here beyond what the source case specified) —
  reviewer's remedy option (b) taken over (a) to avoid adding a testid/scope
  the source case's own "Testids to add" list never asked for.
- **NOT exercised by this case (documented, not silently skipped):** the
  *native* Users-tab drill-down path (clicking a row in the User Activity
  list, `AnalyticsUsers.jsx`'s own `handleUserClick`) — that path sets
  `cameFromExternal=false` at mount (no `initialUserId`), so its Back button
  takes `else { setSelectedUserId(null) }` and returns to the list, NOT to
  Overview. This is the *other* branch of the same `handleBack` — a
  distinct, valid case (not covered by GAP-073's objective, which is
  specifically the cross-tab `cameFromExternal=true` path) and a candidate
  for a follow-up case if not already covered elsewhere.
- **Open dedup question (fix-round finding, PR #1061, 2026-07-24) — NOT
  resolved by this amendment, flagged for analyst reconsideration.** The
  standing foundation smoke check
  (`automation/tests/ui/smoke/test_foundation_cov60_surfaces_smoke.py::test_analytics_overview_leaderboard_drill_to_user_detail_and_back`,
  merged in PR #1048/commit `534de62a`, an ancestor of this branch)
  exercises a near-identical flow with near-identical assertions. The
  reviewer's finding is that this may have been a Rule-6 dedup miss —
  GAP-073 arguably should have been classified `extend-existing` against
  that foundation test, folding in only the genuinely incremental
  assertions (the Step 7 `row_count >= 1` re-check and the whole-cycle
  console-error check) rather than shipping as a second full spec. This
  AFS predates the foundation test's own existence, so the original
  `ready-for-automation` classification was not wrong *at authoring time*
  — but re-litigating it now, after the foundation test merged, is a
  scope/coverage-classification decision reserved for the analyst
  (`.agents/role-overrides.md`; the implementer contract's re-scoping
  boundary), not something the implementer can resolve by unilaterally
  deleting or trimming either spec. Both specs are left fully intact,
  independently green, pending that determination.

## Cleanup
None required. Read-only exploration (date-preset selection, tab
navigation, row clicks) — nothing created, edited, or deleted.

## Concrete Handles (discovered during exploration)

**No page object exists yet for Analytics** — brand-new surface (confirmed:
`find automation -iname "*analytics*"` → no hits in `automation/pages` or
`automation/tests`). Recommend `automation/pages/analytics_page.py`, class
`AnalyticsPage`, extending `BasePage`. Sibling GAP-070/071/072/074 (Agents/
Tools tab search, pagination, Tools drill-down) will extend the same page
object — see `test-specs/analytics/_surface.md` for the full-family context
gathered during this run.

**Testid-only policy** (`.agents/testing.md` § Locator policy,
`.agents/role-overrides.md`) — **zero testids exist today**; every handle
below is `needs-adding`. Two components in this flow are **shared** across
multiple Analytics tabs — `KpiCard.jsx` (`ui/components/KpiCard.jsx`, used
by `AnalyticsOverview`, `AnalyticsUserDetailed`, `AnalyticsAgentDetailed`,
`AnalyticsToolDetailed`) and `SearchInput.jsx` (`@/components/SearchInput`,
used by `AnalyticsUsers`/`AnalyticsAgents`/`AnalyticsTools`) — per
`.agents/testing.md` § Locator policy "Shared components never hardcode
feature-scoped testids", both need an optional `testId` prop threaded
through and wired ONLY at the call sites this case actually touches (scope
rule — do not blanket-add to every KPI card / every SearchInput call site,
only the ones below).

| Element | Recommended Locator | Fallback | Status |
|---|---|---|---|
| Overview TEAM KPI card | `testid needed: analytics-overview-kpi-team` — `KpiCard.jsx` gets an optional `testId` prop (`data-testid={testId}` on the root `Box`), wired ONLY at the `label="TEAM"` call site in `AnalyticsOverview.jsx:31-35` | N/A — testid-only policy, no fallback rung | needs-adding |
| Leaderboard row (first / Nth) | `testid needed: analytics-overview-leaderboard-row` — static testid on the `Box` at `AnalyticsOverview.jsx:139-151` (the `.map((u,i) => <Box key={i} ... onClick={...}>`); every row gets the SAME testid (this case only needs `.first()` — no per-row dynamic suffix required for THIS case; a future case addressing a specific row by index/rank would need `[data-testid="analytics-overview-leaderboard-row"]:nth-of-type(n)` or a dynamic `-{rank}` suffix, out of scope here) | N/A | needs-adding |
| User-detail Back button | `testid needed: analytics-user-detail-back-button` — on the `IconButton` at `AnalyticsUserDetailed.jsx:49-55` (`onClick={onBack}`) | N/A | needs-adding |
| User-detail title (email) | `testid needed: analytics-user-detail-title` — on the `Typography` at `AnalyticsUserDetailed.jsx:56-61` showing `{data.user_email}` | N/A | needs-adding |
| User-detail KPI card: LLM Calls | `testid needed: analytics-user-detail-kpi-llm-calls` — `KpiCard.jsx` `testId` prop wired at `AnalyticsUserDetailed.jsx:65-68` (`label="LLM Calls"`) | N/A | needs-adding |
| User-detail KPI card: Tool Calls | `testid needed: analytics-user-detail-kpi-tool-calls` — same pattern, `AnalyticsUserDetailed.jsx:69-72` | N/A | needs-adding |
| User-detail KPI card: Chat Msg | `testid needed: analytics-user-detail-kpi-chat-msg` — same pattern, `AnalyticsUserDetailed.jsx:73-76` | N/A | needs-adding |
| User-detail KPI card: Agent Runs | `testid needed: analytics-user-detail-kpi-agent-runs` — same pattern, `AnalyticsUserDetailed.jsx:77-80` | N/A | needs-adding |
| User-detail KPI card: Active Days | `testid needed: analytics-user-detail-kpi-active-days` — same pattern, `AnalyticsUserDetailed.jsx:81-84` | N/A | needs-adding |
| User-detail KPI card: Errors | `testid needed: analytics-user-detail-kpi-errors` — same pattern, `AnalyticsUserDetailed.jsx:85-89` | N/A | needs-adding |
| User-activity list title (for Step 5's absence check) | `testid needed: analytics-users-list-title` — on the `Typography` "User Activity" at `AnalyticsUsers.jsx:81-86` | N/A | needs-adding |
| User-activity search box (for Step 5's absence check) | `testid needed: analytics-users-list-search-input` — `SearchInput.jsx` `testId` prop wired at the `AnalyticsUsers.jsx:94-99` call site | N/A | needs-adding |

**Why the two absence-check testids (Step 5) matter even though the branch
is structurally mutually-exclusive (early return, not a visibility
toggle):** per canon ruling #511 extension (`.agents/testing.md`), absence
assertions on a testid ARE references, and the locator-only policy means
Step 5's "User Activity"/"Search by email" check must resolve via
`to_have_count(0)` on a real testid, not a raw `get_by_text()` — the latter
is banned regardless of whether the assertion is positive or negative.

**Scope note (role-overrides § Every role — locator policy):** the other
five Overview KPI cards (`AI ACTIVE`, `LLM CALLS`, `TOOL RUNS`, `CHAT MSG`,
`AGENT RUNS`) are NOT touched by this case's own assertions (only `TEAM` is
named in the case text and actually asserted at Steps 1/7) — do **not**
add testids to them here; that's scope for whichever case exercises those
specific cards.

Dynamic-pattern note: none of this case's testids need runtime
parameterization (the leaderboard row testid is intentionally static, per
above) — all are plain string constants, no `.format()` templating needed.

## Network Behavior
- `GET` (via `useProjectAnalyticsQuery`, `analyticsApi.js`) — fires on
  Overview/Health tab mount with `projectId`/`dateFrom`/`dateTo`; refetches
  when the date preset changes (Step 1's "Last 30d" click). Populates
  `kpis`, `top_ai_users`, `daily_activity`, `models` in one response.
- `GET` (via `useAnalyticsUserDetailQuery`) — fires when `AnalyticsUserDetailed`
  mounts with a `userId` (Step 3's drill-down); returns `kpis`, `models`,
  `tools`, `agents`, `daily_activity` for that user. `AnalyticsUserDetailed`
  shows a `CircularProgress` while `isFetching` and "No data found." if the
  response is empty — neither branch was hit in this run (data returned
  successfully both times).
- No request fires on the Step 6 Back click — purely client-side state
  reset (`setPendingUserId(null)` + `setActiveTab(0)`), confirmed by the
  Overview KPI/leaderboard re-rendering with IDENTICAL values to Step 1
  (no refetch, same cached RTK-Query result for the still-selected `Last 30d`
  range).

## Known Defects Found During Exploration
None found. The case's literal steps and expected results all match live
behavior exactly — see § Coverage Map Axis 2 for the one case-text
clarification (route path) that isn't a product defect.

## Blocked Steps
None. All 7 steps executed and passed.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- New page object: `automation/pages/analytics_page.py`, class
  `AnalyticsPage`, extending `BasePage`. Suggested methods:
  - `navigate_to_analytics()` → `self.navigate("/settings/analytics")`
  - `select_date_preset(label: str)` → click the matching `TabGroupButton`
    entry (this case: `"Last 30d"`) — no testid captured for these preset
    buttons in this run (out of scope — case doesn't assert on them beyond
    clicking); a future case touching the date filter directly should add
    testids there rather than reuse a text-based click
  - `first_leaderboard_email() -> str` → read text from
    `self.leaderboard_row.first` (an appropriate sub-locator inside the row
    for just the email span — implementer's choice of exact sub-selector,
    scoped under the `analytics-overview-leaderboard-row` testid parent)
  - `click_first_leaderboard_row()` → `.first().click()` on the leaderboard
    row locator
  - `user_detail_title_text() -> str` / `user_detail_kpi_visible(card: str) -> bool`
    → keyed off the six `analytics-user-detail-kpi-*` testids
  - `click_user_detail_back()` → click `analytics-user-detail-back-button`
  - `is_overview_active()` / `is_users_list_visible()` → assert on
    `[role=tab][aria-selected]` + the `analytics-users-list-title` absence
    (**note added 2026-07-24, fix-round on PR #1061:** the shipped test does
    NOT implement `is_overview_active()` this way — no tab testid was ever
    requested by the source case, so `[role=tab][aria-selected]` would be a
    raw, non-testid locator under this project's testid-only policy. The
    shipped test instead re-checks `analytics-overview-kpi-team` +
    `overview_leaderboard_row` visibility and `is_users_list_showing()`
    absence, which is the content-based proxy described in Axis 2)
- Wait strategy: Playwright's own auto-retrying `expect(...)` after the date
  preset click and after each tab-switching click is sufficient — no fixed
  `sleep`; the RTK-Query refetch on preset change and the user-detail fetch
  on drill-down are both ordinary awaited network responses (no WebSocket
  involved on this surface, unlike Chat).
- Test-data approach: read-only against the live `Private` project's
  `Last 30d` AI activity — do not hardcode "1 row" / "testbot@elitea.ai" as
  invariants; assert `leaderboard_row.count() >= 1` and read the first
  row's email at runtime (case's own Test Data table already specifies
  this), matching the pattern used in `test-specs/hubs/l3_category-show-more-show-less-pagination_GAP-054.md`
  for similarly volatile shared-suite data.
- Full surface context (route map, shared-component testId-prop mechanism,
  sibling Agents/Tools drill-down notes for GAP-070–074): `test-specs/analytics/_surface.md`.
