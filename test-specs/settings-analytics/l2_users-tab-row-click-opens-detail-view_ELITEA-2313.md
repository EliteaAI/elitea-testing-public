# Test Case: Clicking a user row in Users tab opens the user detail view

## Metadata
- **TMS ID**: ELITEA-2313
- **Linked Story**: none
- **Priority**: l2 (case priority "medium"; l2 matches the established naming for this
  feature's sibling cases ELITEA-2310/2312 — same "medium" TMS priority)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  `automation/testids` — confirmed identical blob to `main` for
  `AnalyticsUserDetailed.jsx`/`AnalyticsUsers.jsx`/`KpiCard.jsx`/`ChartTooltip.jsx`, all
  under `src/[fsd]/features/settings/ui/analytics/`, so this surface is fully on `main`
  already; verified via `git fetch origin` before exploring)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost — no manual login)
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2313`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips login via `VITE_DEV_TOKEN`).
- The `auth_state` fixture's default project ("Private", project id `399`) has at least
  one user with `errors > 0` and a non-null email in its analytics data for the default
  "Last 24h" range — confirmed live: `testbot@elitea.ai` (`errors: 75`, `llm_events: 38`,
  `agent_events: 42`, `total_tokens: 8.0K`, `total_cost: $0.0505`, 2 models used, 24
  agents/pipelines used). Read-only assertions against this existing data; no test data
  creation required. **Row selection matters**: pick a row whose email is non-null (see
  § Known Defects — a numeric-id-only user renders a BLANK title, which is a genuine
  defect, not the row to build the happy-path assertions on).

## Test Data
### reuse-existing
- No test data required — the case only asserts detail-view structure (title, KPI
  cards, chart, summary panels, back navigation) against whatever the `auth_state`
  fixture's default project ("Private") already has. Exact numeric values are not
  hardcoded as pass/fail criteria except where explicitly noted (e.g. the Errors KPI's
  color threshold).

## Test Steps
1. Navigate to Settings → Analytics, click the "Users" tab, and click on a user row
   with a non-null email and `errors > 0` (reuse `AnalyticsPage.open_users_tab()` +
   `AnalyticsPage.users_rows` from ELITEA-2312; live-observed: row 2, `testbot@elitea.ai`).
   - **Verify**: the Users-tab table panel is replaced by the detail view (no URL change
     — confirmed via source: `AnalyticsUsers.jsx`'s `handleUserClick` sets local
     `selectedUserId` state, which conditionally renders `<AnalyticsUserDetailed>` in
     place; this is a same-page state swap, not a route navigation. Wait on the
     `analytics_user_detail/prompt_lib/` GET response, then on the detail view's own
     loading spinner going hidden, before asserting content — mirrors the
     `_wait_for_users_settled()` pattern from ELITEA-2312).
2. Verify the detail view's title is the user's email (`testbot@elitea.ai` in the live
   fixture) and a back-arrow icon button is present to its left.
3. Verify exactly **ten** KPI cards are shown, in this order: `ACTIVE DAYS, LLM CALLS,
   TOOL CALLS, AGENT & PIPELINE RUNS, CHAT MSG, ERRORS, TOTAL TOKENS, INPUT TOKENS,
   OUTPUT TOKENS, TOTAL COST`.
   — **Case-text drift** (see § Known Defects): the case's step 4 lists **six** KPI
   cards (`LLM Calls, Tool Calls, Chat Msg, Agent Runs, Active Days, Errors`) and omits
   `TOTAL TOKENS, INPUT TOKENS, OUTPUT TOKENS, TOTAL COST` entirely. Live product (and
   source, `AnalyticsUserDetailed.jsx:64-114`) confirms ten cards. Same stale-count
   family as ELITEA-2310 (tabs) / ELITEA-2311 (Overview KPIs) / ELITEA-2312 (table
   columns) — reverse-masking guard applies; this AFS asserts the live ten-card
   contract, not the case's six.
4. Verify the Errors KPI card's value renders in the red/rejected color when
   `errors > 0` (live-verified: `testbot@elitea.ai`, `errors: 75`, computed
   `color: rgb(215, 22, 22)`), and in the default text color for every other card
   (live-verified: `rgb(255, 255, 255)`). Source confirms the same `> 0` threshold as
   the Users-table row (`AnalyticsUserDetailed.jsx:99`:
   `color={kpis.errors > 0 ? palette.status.rejected : undefined}`) — **no case-text
   drift here**, unlike the Users-table Errors column (ELITEA-2312/#1188): this case's
   step 5 says "greater than 0", which matches both source and live behavior exactly.
5. Verify a "Daily Activity" multi-series area chart is shown with subtitle "Events by
   type per day", conditional on `daily_activity.length > 0` (live-observed: chart
   renders with 2 days of data for `testbot@elitea.ai`).
6. Verify three summary panels are shown below the chart: "Models Used", "Tools Used",
   "Agents & Pipelines Used".
   — **Case-text drift** (see § Known Defects): the case's step 7 says "Agents Used";
   live/source (`AnalyticsUserDetailed.jsx:243-283`) is "Agents & Pipelines Used" — same
   naming pattern as the Analytics tab itself ("Agents & Pipelines", ELITEA-2310). Minor
   drift, same family; this AFS asserts the live label.
7. Verify each panel shows a count label (`"{N} models"` / `"{N} tools"` /
   `"{N} agents & pipelines"`) and, when N > 0, a list of items each showing a name and
   a call/run count (live-observed for `testbot@elitea.ai`: Models Used → "2 models" →
   `GPT-5.2: 33`, `Anthropic Claude 4.5 Sonnet: 5`; Agents & Pipelines Used → "24 agents
   & pipelines" → a scrollable list of named entries with run counts). When N = 0, an
   empty-state string is shown instead (live-observed for the same user's Tools Used
   panel: "0 tools" → "No tool usage" — `tool_events: 0` for this user).
8. Verify hovering over the Daily Activity chart shows a tooltip with the date and
   per-series values for that point in time (live-verified via a synthetic
   `mouseover`/`mousemove` dispatch at the chart's horizontal midpoint during
   exploration — the Recharts tooltip wrapper appeared with `visibility: visible`,
   containing the date "2026-08-04" and "LLM:" series text). **Cross-reference**: a
   sibling TMS case, **ELITEA-2329** ("Hovering over user detail Daily Activity chart
   shows per-series values"), is dedicated entirely to this interaction's depth — not
   yet automated (no merged spec to `already-covered`/`extend-existing` against, per
   the merged-target rule). This AFS's step therefore asserts only tooltip
   *presence-on-hover* with the date + at least one series label, deliberately leaving
   exhaustive per-series/multi-point verification to ELITEA-2329 so the two don't
   duplicate effort. **Automation note**: exploration used a synthetic
   `dispatchEvent(MouseEvent)` to confirm the mechanism works; the actual automated
   test MUST use a real Playwright `page.mouse.move()` (or `.hover()`) at coordinates
   computed from the chart container's bounding box — synthetic dispatch is
   exploration-only, per `.agents/role-overrides.md` § pristine-repro gate.
9. Click the back arrow — verify the view returns to the Users-tab "User Activity"
   table (live-verified: same handles as ELITEA-2312's `open_users_tab()` state —
   `analytics-users-table-header` visible again, `analytics-users-activity-title` /
   `analytics-users-count` restored). No new network request fires on back (source:
   `handleBack` just resets local `selectedUserId` state to `null` — the Users-tab
   query result was already cached by RTK-Query from the original tab-mount fetch).

## Expected Results

> **Amendment — 2026-08-28 (ELITEA-2329 `extend-existing`, PR #1956 review round 1).**
> The user-detail KPI row grew from **10 to 16 cards** after this case was automated
> (EliteaAI/EliteaUI@f084ea12 + EliteaAI/EliteaUI@ce8115c6, both EL-6267). Every
> "10 cards" / "the other nine cards" claim below dates from the original analysis and
> has been corrected to the shipped contract (16 cards, 15 non-Errors) — the live set
> and order are pinned by `EXPECTED_KPI_LABELS_IN_ORDER` in
> `automation/tests/ui/admin/test_analytics_user_detail_view.py`. The case-text drift
> filed as elitea-testing-public#1191 is unchanged in kind, only wider in degree
> (6 listed vs 16 live).

- Clicking a user row (with a non-null email) swaps the Users-tab table for the user
  detail view: email title + back arrow, 16 KPI cards (Errors red only when > 0),
  a conditional Daily Activity chart with working hover tooltip, and three summary
  panels (Models/Tools/Agents & Pipelines Used) — all render without console errors.
- The GET `.../analytics_user_detail/prompt_lib/{project_id}?user_id={id}&date_from=...&date_to=...`
  request resolves 200 and the view reflects its response (`kpis`, `models`, `tools`,
  `agents`, `daily_activity`).
- Clicking the back arrow returns to the User Activity table with no new network
  request (cached).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics → Users tab | Target page/section loads successfully | step 1 | reused from ELITEA-2312's `open_users_tab()` | asserted (transit, not this case's own observable) |
| 2 Click on any user row in the User Activity table | Control responds; expected next state is shown | step 1 | `step 1`: table panel replaced by detail view, network+spinner waits | asserted |
| 3 View transitions to user detail page showing email as title with back arrow | Condition holds | step 2 | `step 2`: title text = user's email, back-arrow IconButton present | asserted |
| 4 Six KPI cards shown: LLM Calls, Tool Calls, Chat Msg, Agent Runs, Active Days, Errors | Condition holds | step 3 | `step 3`: live 16-card set + order asserted instead | clarification *(case's 6-card list is stale — omits the token/cost cards; live view has 16 cards (10 at analysis time — see the Amendment above). Same stale-count family as ELITEA-2310/2311/2312. Filed elitea-testing-public#1191)* |
| 5 Errors card value shown in red when greater than 0 | Condition holds | step 4 | `step 4`: both branches asserted live — Errors card red (`rgb(215, 22, 22)`) for `errors=75`, all other 15 cards default color (`rgb(255, 255, 255)`) | asserted *(no case-text drift here — case's ">0" wording matches source and live exactly)* |
| 6 "Daily Activity" multi-series area chart shown with "Events by type per day" subtitle | Condition holds | step 5 | `step 5`: title + subtitle text, chart conditional on `daily_activity.length > 0` | asserted |
| 7 Three summary panels shown: Models Used, Tools Used, Agents Used | Condition holds | step 6 | `step 6`: live labels asserted ("Agents & Pipelines Used", not "Agents Used") | clarification *(case's "Agents Used" is stale — live label matches the tab's own "Agents & Pipelines" naming; minor drift, same family as row 4)* |
| 8 Each panel shows a count label and a list of items with call counts | Action completes without error and produces expected UI state | step 7 | `step 7`: count label + item list (name + count) for N>0, empty-state string for N=0 | asserted |
| 9 Hovering on a diagram shows details for that point in time | Condition holds | step 8 | `step 8`: tooltip presence + date/series label on hover, cross-referenced against sibling case ELITEA-2329 for depth | asserted (shallow — see step 8's cross-reference note) |
| 10 Click the back arrow — verify navigation returns to the User Activity table | Control responds; expected next state is shown | step 9 | `step 9`: table panel handles restored, no new network request | asserted |

**Axis 2 — Analyst additions.**
- `step 3` asserts KPI card **order**, not just presence/count — *added: cheap once the
  per-card handle exists, mirrors ELITEA-2310's tab/preset order assertions and
  ELITEA-2312's column-order assertion; catches a silent reorder regression.*
- `step 4` asserts the **negative** branch (the 15 non-Errors cards stay default-colored) in
  addition to the case's positive branch — *added: a card whose color logic
  accidentally fires for everything (e.g. a copy-paste `color` prop bug) would pass a
  positive-only check while failing this; cheap once the errors-value testid exists.*
- `step 7`'s empty-state assertion (`tool_events: 0` → "No tool usage") is not in the
  case's numbered steps but is directly adjacent to "shows a count label and a list of
  items" — *added: proves the panel's zero-state renders correctly, not just the
  populated-state; free with the same fixture user (`testbot@elitea.ai` has 0 tool
  calls in this range).*
- `step 9`'s "no new network request on back" assertion is not in the case text —
  *added: proves the RTK-Query cache is actually being reused (a regression here would
  silently re-fetch and could reset pagination/search state left in the Users tab);
  cheap to assert via `page.expect_request` NOT firing within a short window.*

## Cleanup
None — read-only navigation into and out of the detail view; no data created or
mutated. If the test file shares a `Page`/`AnalyticsPage` fixture with ELITEA-2312's
test, ensure the detail view is backed out of (click back arrow) before the fixture is
reused by a later test, so no test starts already inside a detail view.

## Concrete Handles (discovered during exploration)

**Provenance note:** `AnalyticsUserDetailed.jsx` is confirmed **identical** on
`EliteaAI/EliteaUI` `main` and `automation/testids` (verified 2026-08-05, fresh
`git fetch origin`) — this surface is already on `main`, like the rest of the
Analytics feature. **Zero pre-existing testids** on `AnalyticsUserDetailed.jsx`,
`AnalyticsUsers.jsx`'s row-click handler (already covered by ELITEA-2312's
`analytics-users-row`), the shared `KpiCard.jsx` component, or the shared
`ChartTooltip.jsx` component. All handles below need adding via `add-data-testid`;
uniqueness to be re-verified by the implementer against fresh `origin/main` at
implementation time (naming below follows the `analytics-user-detail-*` prefix,
distinct from ELITEA-2312's `analytics-users-*` list-view prefix — same feature,
different sub-view).

| Element | Recommended Locator | PROVENANCE | Notes |
|---|---|---|---|
| Back-arrow button | `LocatorDescriptor(testid="analytics-user-detail-back-button")` | needs-adding | `AnalyticsUserDetailed.jsx:57-62` — `<IconButton onClick={onBack}><ArrowBackIcon /></IconButton>`. Add directly (not a shared component's generic prop — this `IconButton` usage is local to this view). |
| Title (user email) | `LocatorDescriptor(testid="analytics-user-detail-title")` | needs-adding | `AnalyticsUserDetailed.jsx:63-68` — `<Typography>{data.user_email}</Typography>`. **Renders BLANK for a user with no email** — see § Known Defects; test data selection (a user WITH an email) works around this for the happy-path assertion, but the blank-title behavior itself is filed as a defect. |
| Loading spinner (this view) | `LocatorDescriptor(testid="analytics-user-detail-loading-indicator")` | needs-adding | `AnalyticsUserDetailed.jsx:26-31` — the `isFetching` early-return `CircularProgress`. Used for an absence assertion (wait `state="hidden"`) before asserting rendered content, mirroring `analytics-users-loading-indicator`'s pattern (absence assertions count as references per `.agents/testing.md`). |
| KPI card (repeated, one per rendered card) | `LocatorDescriptor(testid="analytics-user-detail-kpi-card")` | needs-adding | **Shared `KpiCard.jsx` component** (also used by `AnalyticsOverview`, `AnalyticsCosts`, `AnalyticsAgentDetailed`, `AnalyticsToolDetailed`, `UsageSummary` — per `.agents/testing.md` § Locator policy, shared components take a caller-supplied prop, never a hardcoded testid). Add an optional `testId` prop to `KpiCard`, wired as `data-testid={testId}` on its outer `Box` (`kpiCardStyles().kpiCard`); pass the **same** `testId="analytics-user-detail-kpi-card"` on **every** `<KPICard>` call site (10 at analysis time, 16 live — see the Amendment above) inside `AnalyticsUserDetailed.jsx` only (list pattern, mirrors `analytics-users-row` — `.nth(i)`, count via `.count()`). Do NOT add the prop at the Overview/Costs/AgentDetailed/ToolDetailed/UsageSummary call sites — those are untouched by this case (scope discipline, `.agents/role-overrides.md`). Read each card's own label via `.nth(i).inner_text().split("\n")[0]` (mirrors ELITEA-2312's `get_user_row_identifier` technique) — no positional child selector needed. |
| KPI card value (repeated, one per rendered card) | `LocatorDescriptor(testid="analytics-user-detail-kpi-value")` | needs-adding | **Implementer amendment (Phase 2 exploration, supersedes the analyst's original single `analytics-user-detail-kpi-errors-value` spec below this row).** Same `KpiCard.jsx` — add a second optional prop `valueTestId`, wired as `data-testid={valueTestId}` on the value `Typography` specifically (`kpiCardStyles().kpiValue`, the element carrying the `color` prop). The analyst's original plan wired this **only** on the `ERRORS` call site and proposed reading the other cards' default color off the **outer card `analytics-user-detail-kpi-card` locator itself** — verified during exploration that this doesn't work: `kpiCard`'s own `sx` sets no `color` at all (`KpiCard.jsx` styles), so `getComputedStyle` on the card Box reflects only inherited/ambient color, never the value Typography's explicit `color` prop; asserting on the card box for the negative branch would be a trivially-passing, defect-masking-in-reverse check (always green regardless of a real color-prop bug). Fix: pass `valueTestId="analytics-user-detail-kpi-value"` (same value, repeated) on **every** `<KPICard>` call site, mirroring the `analytics-user-detail-kpi-card` list pattern — `.nth(i)` selects the same index as the corresponding card. Read the Errors card's color via `expect(locator.nth(errors_index)).to_have_css("color", "rgb(215, 22, 22)")` and every other card via the same check against the resolved default-text color — confirmed live via `getComputedStyle` rather than hardcoded (same caution as ELITEA-2312's Errors-column note). |
| Chart title | `LocatorDescriptor(testid="analytics-user-detail-chart-title")` | needs-adding | `AnalyticsUserDetailed.jsx:122-127` — `<Typography>Daily Activity</Typography>`. |
| Chart subtitle | `LocatorDescriptor(testid="analytics-user-detail-chart-subtitle")` | needs-adding | `AnalyticsUserDetailed.jsx:131-136` — `<Typography>Events by type per day</Typography>`. |
| Chart container | `LocatorDescriptor(testid="analytics-user-detail-chart-container")` | needs-adding | `AnalyticsUserDetailed.jsx:141-145` — the `Box` wrapping `<ResponsiveContainer>` (`styles.chartWrapper`). Used for (a) a presence assertion the chart rendered, and (b) computing hover coordinates for step 8 (`.bounding_box()`, hover at the horizontal midpoint) — the Recharts SVG internals themselves are the #579 third-party-widget exception (no testid can be placed on Recharts' internal `<path>`/`<g>` nodes), scoped to this testid parent. |
| Chart tooltip | `LocatorDescriptor(testid="analytics-user-detail-chart-tooltip")` | needs-adding | `AnalyticsUserDetailed.jsx:174` — `<RechartsTooltip content={<ChartTooltip />} />`. **Shared `ChartTooltip.jsx` component** — add an optional `testId` prop wired as `data-testid={testId}` on its outer `Box`; since Recharts injects `active`/`payload`/`label` at render time, thread the prop via a render-function form: `content={props => <ChartTooltip {...props} testId="analytics-user-detail-chart-tooltip" />}` (only at this call site — do not touch the Overview/Health charts' `<ChartTooltip>` usages, untouched by this case). Read via `.inner_text()` after hover and assert it contains the hovered date + at least one series label (e.g. `"LLM"`). |
| Models Used panel | `LocatorDescriptor(testid="analytics-user-detail-models-panel")` | needs-adding | `AnalyticsUserDetailed.jsx:213-241` — the panel's outer `Box` (`styles.chartCard`, second one). Read via `.inner_text()`, split on `"\n"`: line 0 = "Models Used", line 1 = "{N} models", remaining lines alternate name/count per item (or a single "No model usage" line when N=0) — same aggregate-text technique as ELITEA-2312's `get_users_table_column_labels`. |
| Tools Used panel | `LocatorDescriptor(testid="analytics-user-detail-tools-panel")` | needs-adding | `AnalyticsUserDetailed.jsx:242-272` — same pattern, panel 2. |
| Agents & Pipelines Used panel | `LocatorDescriptor(testid="analytics-user-detail-agents-panel")` | needs-adding | `AnalyticsUserDetailed.jsx:273-305` — same pattern, panel 3. |

**Reused from ELITEA-2312** (already on `main`, no new work): `AnalyticsPage.tab_users`,
`AnalyticsPage.open_users_tab()`, `AnalyticsPage.users_rows` (to locate and click a row
— row click itself was explicitly out-of-scope for ELITEA-2312, this case is the first
to exercise it), `AnalyticsPage.users_table_header` / `users_activity_title` /
`users_count` (to confirm the back-navigation lands back on the same table).

Uniqueness check deferred to implementation time (per standard practice — the analyst's
naming follows the established `analytics-user-detail-*` / `analytics-users-*` prefix
split, which is prefix-disjoint from all other `analytics-*` testids catalogued in
`_surface.md` and `analytics_page.py`'s existing fields, so a collision is unlikely but
implementer must re-grep `origin/main` fresh before committing).

## Network Behavior
- `GET /api/v2/elitea_core/analytics_user_detail/prompt_lib/{project_id}?user_id={id}&date_from=...&date_to=...`
  — fires once when a row is clicked (`selectedUserId` set); confirmed live: 200 OK, no
  console errors, response shape `{ kpis, models, tools, agents, daily_activity }`
  (`AnalyticsUserDetailed.jsx:47`).
- No request fires on the back-arrow click (`handleBack` only resets local state) —
  confirmed via source; the Users-tab table's own query (`analytics_users/prompt_lib/`)
  is not re-triggered because it was never unmounted, only hidden.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case-text drift (not a product defect — reverse-masking guard
  applies), same stale-count family as ELITEA-2310/2311/2312 (elitea-testing-public#1188
  is the ELITEA-2312 sibling; filed as its own sibling **elitea-testing-public#1191**
  for this case, per the dedup rule — different object, the detail view's KPI cards,
  not the table's columns): case step 4 lists 6 KPI cards, omitting Total/Input/Output
  Tokens and Total Cost — live view has 16 (10 at analysis time). Case step 7 says "Agents Used"; live label
  is "Agents & Pipelines Used". This AFS's steps 3 and 6 assert the live contract.
- **[POSSIBLE DEFECT — filed separately, not bundled with the #1188 clarification
  family]** `AnalyticsUserDetailed.jsx:66` renders `{data.user_email}` as the detail
  view's title with **no fallback** for a user whose `user_email` is null/empty (a
  numeric-id-only user, e.g. `User 6250` in the live "Private" project fixture — its
  detail-view title rendered as a completely empty `<span>`, confirmed via
  `getComputedStyle`/DOM inspection: `<span class="MuiTypography-root ...
  css-zqcqc4-...></span>` with zero text content). This is inconsistent with the
  Users-table LIST row, which explicitly falls back to `User {id}` when `user_email` is
  falsy (`AnalyticsUsers.jsx:126`: `{u.user_email || \`User ${u.user_id}\`}`) — the
  detail view drops that fallback entirely, leaving the page with an unlabeled title
  and no way to tell which user's data is being viewed except by memory of which row
  was clicked. Filed as a genuine UI defect, not a case-text clarification (the case's
  premise — "showing the user's email as the title" — assumes an email always exists,
  which the live fixture data disproves; the fallback gap is a real product
  inconsistency, not stale case text). See filed issue in § Filed Defects below.
  **Test-data workaround**: this AFS's happy-path assertions (steps 2–9) deliberately
  select a row WITH a non-null email (`testbot@elitea.ai`) to keep the case's own
  numbered steps green; the blank-title defect is tracked separately and does not block
  this case's automation.

### Filed Defects
- **elitea-testing-public#1192** — "`AnalyticsUserDetailed` user-detail title renders
  blank for a user with no email (list view falls back to `User {id}`, detail view
  does not)" — labelled `bug`, links this case (ELITEA-2313) and the originating task.
- **elitea-testing-public#1191** — case-text drift clarification (6 vs 16 KPI cards,
  "Agents Used" vs "Agents & Pipelines Used") — labelled `question`, see § Known
  Defects above (first bullet).

## Blocked Steps
None — all 10 case steps were live-executed to completion (using a row with a
non-null email + `errors > 0` to exercise every branch in one pass; see § Preconditions
for why that row was chosen over the first alphabetical/positional one).

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Extend `pages/analytics_page.py` (created by ELITEA-2310, extended by ELITEA-2312)
  with this case's `LocatorDescriptor` fields, rather than creating a second page
  object — same page, same URL, same class.
- **Suggested new test file**: `automation/tests/ui/admin/test_analytics_user_detail_view.py`
  (sibling to `test_analytics_users_activity_table.py`, not an extension of it — this
  case's observable, the row-click → detail-view → back-arrow flow, was explicitly
  out-of-scope for ELITEA-2312's spec and shares zero assertions with it; a fresh file
  keeps the two flows independently readable/runnable). Implementer's call per
  `.agents/role-overrides.md` if a single file is preferred instead — no architectural
  reason blocks either.
- Wait strategy: wait for the `analytics_user_detail/prompt_lib/...` GET response
  (`page.expect_response` matching URL substring `/elitea_core/analytics_user_detail/prompt_lib/`)
  before asserting detail-view content, then wait for
  `analytics-user-detail-loading-indicator` to hide (mirrors
  `AnalyticsPage._wait_for_users_settled()`'s two-step pattern) — add a new URL-substring
  constant `ANALYTICS_USER_DETAIL_QUERY_URL_SUBSTRING = "/elitea_core/analytics_user_detail/prompt_lib/"`.
- KPI card assertions: use `.count()` on `analytics-user-detail-kpi-card` for the
  card-count check, `.nth(i).inner_text().split("\n")[0]` for each label in order, and the
  dedicated `analytics-user-detail-kpi-errors-value` testid + `to_have_css("color", ...)`
  for the Errors-card color branch (both positive `errors > 0` → red and, on the other
  other cards, default color — read via `analytics-user-detail-kpi-card`'s non-Errors
  `.nth(i)` entries, same `to_have_css` check against the resolved default-text color).
- Chart hover: compute the `analytics-user-detail-chart-container`'s bounding box
  (`.bounding_box()`), then use a **real** `page.mouse.move(x, y)` at (roughly) the
  horizontal midpoint and vertical center, THEN assert
  `analytics-user-detail-chart-tooltip` becomes visible via `expect(...).to_be_visible()`
  and its `.inner_text()` contains the expected date substring + at least one series
  label — do not use `page.evaluate`/synthetic `dispatchEvent` in the shipped test (that
  was exploration-only, per the pristine-repro-gate note in step 8).
  Recharts' hover-tracking listens on the whole plot `<svg>`, so any point inside the
  chart's horizontal data range should trigger a tooltip for the nearest X value —
  no per-datapoint testid is needed for a presence+content check at this depth (leave
  precise per-point verification to ELITEA-2329).
- Back-navigation assertion: after clicking `analytics-user-detail-back-button`, assert
  `analytics-users-table-header` (ELITEA-2312 handle) is visible again AND assert (via
  `page.expect_request` with a short timeout, expecting it NOT to fire, or simply
  checking no new `analytics_users/prompt_lib/` request appears in
  `page.expect_response`'s absence within e.g. 500ms) that no fresh Users-tab query
  fires — the RTK-Query cache from the original tab-mount fetch is reused per source.
- Reuse `AnalyticsPage.open_users_tab()` from ELITEA-2312 to reach the Users tab and
  its rows before this case's own row-click step.
