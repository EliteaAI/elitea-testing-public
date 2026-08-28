# Test Case: Hovering the Overview "Daily Activity" chart shows a tooltip with the date and every series value

## Metadata
- **TMS ID**: ELITEA-2326
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2326/2327/2328/2329)
- **Status**: ready-for-automation
- **Case-text clarification filed**: elitea-testing-public#1954 (the case says "both series (Events
  and Users)"; the live chart has four series and none is named "Events")

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.
- The `Daily Activity` chart itself is **unconditional** on this tab (unlike the Agents/Tools bar
  charts) — `AnalyticsOverview.jsx:151` renders the `<AreaChart>` regardless of data. What the test
  DOES need is **at least two entries in `daily_activity`**, otherwise "move to a different data
  point" has no second point to move to. The test drives `Last 30d` and asserts this precondition
  against the captured response so an empty project fails loudly with a clear message rather than a
  confusing tooltip-never-changes timeout.
- **`Active Users` is a conditional series** (`!isPersonalProject`, `AnalyticsOverview.jsx:212-221`,
  and the same condition gates the right-hand `users` `<YAxis>`). The expected series list is
  therefore *derived*, never hardcoded — see step 3.

## Test Data
### reuse-existing
Whatever activity the fixture project already has in the last 30 days. Live 2026-08-28:
- project "Elitea Testing Team" (non-personal) — 4 area series, tooltip
  `2026-08-06 / LLM Calls: 5 / Tool Runs: 0 / Agent & Pipeline Runs: 0 / Active Users: 1`
- project "Private" (personal) — 3 area series, tooltip
  `2026-08-08 / LLM Calls: 62 / Tool Runs: 15 / Agent & Pipeline Runs: 65`

## Test Steps

1. Navigate to Settings -> Analytics (Overview is the default tab) and click the `Last 30d` preset,
   **capturing the resulting `analytics/prompt_lib/` response body** as the oracle for every value
   asserted below (`AnalyticsPage.select_date_preset_capturing_analytics`) — case step 1.
   - **Verify**: the Overview tab is selected (`aria-selected="true"`), the response is 200, and
     `analytics-overview-daily-chart-container` is visible.
   - **Verify (precondition)**: `len(response["daily_activity"]) >= 2`.
2. Hover a data point on the `Daily Activity` area chart — case step 2.
   - Compute the plot x for the point at index `i1` from the container's bounding box and drive a
     **real `page.mouse.move()`** to it (never a synthetic event dispatched by the test). Use a
     fractional x well inside the plot (e.g. 25% of the container width) rather than an exact
     datum-pixel — Recharts snaps to the nearest category, and the assertions below read whichever
     date it actually landed on out of the response, so no pixel maths has to be exact.
   - **Verify**: `analytics-overview-daily-chart-tooltip` becomes visible.
3. Verify the tooltip content — case step 3, and the point where the case text is stale (#1954).
   - Read the tooltip's lines. Line 1 is the **label**; lines 2..N are `"{series name}: {value}"`.
   - **Verify**: line 1 equals one of the `date` values in `response["daily_activity"]`. Bind that
     entry as `point` — it is the oracle for the rest of this step.
   - **Verify**: the series lines are exactly, in this order, the series the product renders:
     `LLM Calls`, `Tool Runs`, `Agent & Pipeline Runs`, and — **only when the chart renders 4 area
     paths** — `Active Users`. Derive the expectation from the rendered series count (see
     § Concrete Handles), so the same spec is honest in a personal and a non-personal project.
   - **Verify**: each series' value equals `fmt_num(point[<dataKey>])` for the mapping
     `LLM Calls -> llm_calls`, `Tool Runs -> tool_runs`, `Agent & Pipeline Runs -> agent_runs`,
     `Active Users -> active_users`. This is what makes the assertion honest: the numbers come from
     the captured response, not from the test.
4. Move to a different data point and verify the tooltip updates — case step 4.
   - Drive a second real `page.mouse.move()` to a clearly different fractional x (e.g. 75%).
   - **Verify**: the tooltip is still visible and its **label line differs** from step 3's.
   - **Verify**: the new label is also a `date` present in `response["daily_activity"]`, and the new
     series values again equal `fmt_num(...)` of that entry's fields. (Asserting only "the text
     changed" would pass on a tooltip that changed to garbage.)
5. Move the cursor away from the chart and verify the tooltip disappears — case step 5 /
   Expected Final State.
   - Drive a real `page.mouse.move()` OFF the chart container.
     **Implementer amendment (2026-08-28): the pointer must TRAVEL, not teleport.** A single-jump
     move worked for this area chart but left the sibling BAR charts' tooltips stuck active
     (ELITEA-2327/2328), so `AnalyticsPage.move_mouse_off_chart()` moves with `steps=20` to the page
     header — the stream of intermediate `mousemove`s a real mouse emits, i.e. a MORE faithful
     gesture, and the same helper is now used by all four cases in this cluster.
   - **Verify**: `analytics-overview-daily-chart-tooltip` reaches **count 0** — `ChartTooltip`
     returns `null` when `!active`, so the element unmounts entirely rather than merely hiding.
     Live-confirmed on the already-testid'd sibling tooltip (`analytics-user-detail-chart-tooltip`:
     count 1 while hovering -> 0 after moving away).
6. No console errors throughout (`utils/console_errors.collect_console_errors` — the URL-annotated
   collector, per `.agents/testing.md`).

## Expected Results
- Hovering the Overview `Daily Activity` chart raises a tooltip whose first line is the hovered
  day's date and whose remaining lines are every rendered series with the value the backend
  reported for that day.
- Moving to another data point re-renders the tooltip against the new day.
- Moving off the chart removes the tooltip from the DOM.
- No console errors.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | covered |
| Step 1 — Navigate to Settings -> Analytics -> Overview | page/section loads | step 1 | tab `aria-selected`, response 200, chart container visible | covered |
| Step 2 — Hover a data point on the Daily Activity area chart | no error, expected UI state | step 2 | tooltip becomes visible | covered |
| Step 3 — Tooltip shows the date and numeric values for both series (Events and Users) | condition holds | step 3 | label == a response `date`; series lines == the rendered series; values == `fmt_num(point[...])` | covered **with clarification #1954** — live has four series (`LLM Calls`, `Tool Runs`, `Agent & Pipeline Runs`, `Active Users`), three on a personal project, and none named "Events". The live contract is asserted, not the stale text (reverse-masking guard). |
| Step 4 — Move to a different data point, tooltip updates | no error, expected UI state | step 4 | label differs AND is a real response date AND values re-match | covered |
| Step 5 / Expected Final State — Move cursor away, tooltip disappears | no error, expected UI state | step 5 | tooltip count == 0 | covered |

### Axis 2 — observables asserted beyond the case
| Observable | Why |
|---|---|
| Tooltip values equal `fmt_num()` of the captured response fields | The case says "numeric values" without saying which. Reading them off the response is the only way to assert they are *correct* rather than merely present, and it keeps the test honest (the product produces every asserted number). |
| The series list is derived from the rendered area-path count | Makes the one spec correct in both the personal-project (3 series) and non-personal (4 series) branch, instead of silently passing only in whichever project the fixture happens to select. |
| No console errors | Standing convention on this surface; the whole Analytics walk was clean live. |

## Cleanup
None — read-only. No entity is created, and the date preset is per-session UI state.

## Concrete Handles (discovered during exploration)

| Element | Handle (testid) | PROVENANCE | Notes |
|---|---|---|---|
| Overview tab | `analytics-tab-overview` | on `automation/testids` only | default tab; already in `AnalyticsPage` |
| `Last 30d` preset | `analytics-preset-last-30d` | on `automation/testids` only | already in `AnalyticsPage` |
| Daily Activity chart container | `analytics-overview-daily-chart-container` | **on `automation/testids` only** (awaiting human cherry-pick to `main`) | verified 2026-08-28 with a fresh `git fetch origin` + the two-stage grep |
| Daily Activity chart tooltip | `analytics-overview-daily-chart-tooltip` | **added 2026-08-28 — EliteaAI/EliteaUI@c926ba66, on `automation/testids`** (awaiting human cherry-pick to `main`) | call-site-only, see below |

### testid needed: `analytics-overview-daily-chart-tooltip`
`AnalyticsOverview.jsx:174` currently renders `<RechartsTooltip content={<ChartTooltip />} />`.
`components/ChartTooltip.jsx` **already has a `testId` prop** (it puts it straight on the tooltip
`Box`), so this is **call-site-only wiring — no shared-component change**:

```jsx
<RechartsTooltip content={<ChartTooltip testId="analytics-overview-daily-chart-tooltip" />} />
```

Exactly the shape already merged for `analytics-user-detail-chart-tooltip`
(`AnalyticsUserDetailed.jsx:246`, on `main`) and `analytics-health-chart-tooltip`. Add it at the
**`AnalyticsOverview` call site only** — `ChartTooltip` is shared with Costs, Tokens, Agents, Tools,
UserDetailed, AgentDetailed and must not gain a feature-scoped default.

### Rendered-series count (for step 3's derivation)
The `<Area>` `<path>` nodes are Recharts-internal library DOM and cannot carry an app testid, so a
**scoped raw handle under the real testid parent** is used — the existing, already-declared
`.agents/testing.md` § Locator policy #579 exception 1, and the page object already owns the
constant:

- `RECHARTS_AREA_SERIES = ".recharts-area-area"` (`pages/analytics_page.py:194`), used as
  `self.overview_daily_chart_container.locator(RECHARTS_AREA_SERIES)` — same shape as the merged
  `get_health_chart_area_series_count()`. **No new exception is being introduced.**
- The paths mount **one animation tick after the container becomes visible** (documented for the
  Health/Tools charts and re-confirmed here) — wait on `.first` being attached, never a sleep.

### Number formatting
`ChartTooltip` renders `{entry.name}: {formatValue(entry.value)}` with no `formatter` prop at this
call site, so values go through `AnalyticCommonHelpers.fmtNum`. A Python port already exists as
`fmt_num()` in `tests/ui/admin/test_analytics_overview_kpi_cards.py:62` (on this batch trunk).
**This spec plus the ELITEA-2327/2328 family spec take `fmt_num` past its third consumer**, so per
Hard Rule 7 it should now be extracted to `automation/utils/` and imported by all consumers rather
than copied a third time. **Done (2026-08-28): `automation/utils/analytics_format.py`; the Overview
KPI spec now imports it.**

## Fidelity Declaration
**No substitutions.** Every asserted value is produced by the system: the tooltip text is rendered by
the product in response to a **real `page.mouse.move()`** (a genuine CDP input event, the same
gesture a user makes), and the oracle it is compared against is the live
`analytics/prompt_lib/` response body captured off the wire. No `page.route`, no `route.fulfill`,
no `page.evaluate`-dispatched events, no injected state.

> Note for the implementer: during exploration a *synthetic* `mouseover` dispatch was used ONCE on
> this surface in a prior session (ELITEA-2313) purely to learn that Recharts listens on the plot
> `<svg>`. That is exploration-only. The automated test must use `page.mouse.move()` /
> `Locator.hover()` — never `page.evaluate`.

## Network Behavior
- `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` fires on
  page load and on each preset change; 200 OK.
- **Hovering fires no request at all** — the tooltip is a pure client-side render over data already
  in the RTK-Query cache. Do not wait on a response after a hover.
- Never wait on `networkidle` (#1847 — persistent Socket.IO polling transport).

## Blocked Steps
None. All five case steps were executed live end-to-end.

## Known Defects
None found for this case. One case-text clarification: elitea-testing-public#1954.

## Live Observations (2026-08-28, localhost:5173)
- **project "Elitea Testing Team", `Last 30d`** — legend `LLM CallsTool RunsAgent & Pipeline
  RunsActive Users`, 4 `.recharts-area-area` paths, container box `582x200`.
  - hover at 30% width -> `2026-08-06 / LLM Calls: 5 / Tool Runs: 0 / Agent & Pipeline Runs: 0 /
    Active Users: 1`
  - hover at 70% width -> `2026-08-21 / LLM Calls: 1 / Tool Runs: 0 / Agent & Pipeline Runs: 0 /
    Active Users: 1`  (tooltip updated)
  - mouse moved 250 px above the container -> tooltip wrapper not visible, inner text empty, zero
    child nodes (the `ChartTooltip` `Box` unmounted)
- **project "Private" (personal), `Last 30d`** — legend `LLM CallsTool RunsAgent & Pipeline Runs`,
  3 area paths, single `<YAxis>`; hover -> `2026-08-08 / LLM Calls: 62 / Tool Runs: 15 /
  Agent & Pipeline Runs: 65`. Confirms the `!isPersonalProject` branch.
- Zero console errors across the whole Overview -> Agents -> Tools -> Users -> user-detail walk.

## Implementation notes (2026-08-28, test-automation-engineer)
- Spec: `automation/tests/ui/admin/test_analytics_overview_daily_chart_tooltip.py`
  (`TestAnalyticsOverviewDailyChartTooltip::test_overview_daily_chart_hover_tooltip`).
- Live run on the fixture project ("Private", personal) rendered **3** area series, so the
  derived-series branch of step 3 is the one actually exercised locally; the 4-series
  (non-personal) branch stays source- and analysis-confirmed.
- `AnalyticsPage.hover_chart_at_fraction()` calls `scroll_into_view_if_needed()` before measuring the
  container — added after the user-detail chart (ELITEA-2329) was found below the fold.
