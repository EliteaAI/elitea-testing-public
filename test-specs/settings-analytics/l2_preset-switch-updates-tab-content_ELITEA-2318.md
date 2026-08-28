# Test Case: Switching preset filters updates content on Agents, Tools, and Users tabs

## Metadata
- **TMS ID**: ELITEA-2318
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w06`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.

## Test Data
### reuse-existing
- Whatever the selected project already has. As in ELITEA-2317, every content assertion uses the
  per-tab response body as its oracle, so the test is valid for an empty project too.

## Test Steps
1. Navigate to Settings → Analytics, confirm the page is on its **default** `Last 24h` preset,
   then open the **Agents & Pipelines** tab (case step 1 — the case says "Agents tab under
   Last 24d"; the live tab is "Agents & Pipelines" and the live preset label is "Last 24h").
   — **Implementer amendment (2026-08-28):** the original wording said "click `Last 24h`".
   Clicking the ALREADY-active preset is a deliberate product no-op (MUI's exclusive
   `ToggleButtonGroup` emits `null` and `handleDatePresetChange` returns early), so no request
   fires and a response wait around that click times out. Since `Last 24h` IS the default, the
   step asserts that state instead of clicking it — same precondition, no fabricated interaction.
   - **Verify**: the tab is selected and its own GET (`analytics_agents/prompt_lib/`) resolves.
2. Capture the Agents tab state under `Last 24h` (case step 2): presence/absence of the
   "Most Active Agents & Pipelines" bar chart and the "Chat Messages" area chart, the
   "Agent & Pipeline Activity" row count and the `{N} agents & pipelines` count label.
   - **Verify** against the 24h response: rendered row count == `len(rows)` (page-capped at 20),
     count label == `total`, and each chart is present **iff** its data array is non-empty
     (`agentChartData.length > 0` / `chat_daily.length > 0`).
   - **Verify the Chat Messages chart's DATA, not just its presence** (implementer amendment,
     fix round 1): when `chat_daily` is non-empty, the chart's rendered X-axis tick labels are a
     subset of that response's `chat_daily` dates, its last tick equals the last `chat_daily`
     date, and the axis span is within `CHART_TICK_EDGE_SLACK_DAYS` (10) of the span
     `chat_daily` itself covers. The `AreaChart` renders `date.slice(5)` of that very array
     (`AnalyticsAgents.jsx`), so tick labels and response dates are directly comparable.
3. Click `Last 30d` (case step 3).
   - **Verify**: the Agents GET re-fires with `date_from` ≈ 30 days back, 200 OK.
4. Verify both charts update their data (case step 4): each chart is again present iff the 30-day
   response's corresponding array is non-empty, the bar chart's subtitle (`Top {N} by runs`)
   equals the 30-day response's chart-series length, and the Chat Messages chart's axis is
   re-asserted against the **30-day** `chat_daily` series exactly as in step 2 — which is what
   makes "update their data" a real check: a chart still drawing the 24h series (one point,
   span 0) fails the span comparison against a ~30-day `chat_daily`.
5. Verify the Agent Activity table updates (case step 5): rendered row count == the 30-day
   response's `len(rows)`, count label == its `total`.
6. Repeat for the **Users** and **Tools** tabs (case step 6): for each tab, open it (its own GET
   resolves under the currently selected preset), assert the rendered rows/count match that
   response, then switch presets, assert the tab re-fetched and now matches the new response.
   - Users tab: `analytics-users-row` / `analytics-users-count` (`{N} users`). The Users tab
     renders **no chart** (`AnalyticsUsers.jsx` has table + pagination only), so there is
     nothing chart-shaped to repeat there.
   - Tools tab: `analytics-tools-row` / `analytics-tools-count` (`{N} tools`), plus the
     "Tool Details" section title.
   - **Verify the Tools tab's chart DATA, not just its table** (implementer amendment,
     fix round 2): the "Most Popular Tools" `BarChart` (`AnalyticsTools.jsx`, rendered iff
     `toolChartData.length > 0`) is asserted under BOTH presets exactly as the Agents charts
     are — present iff the response carried rows, subtitle `Top {N} by usage` equal to
     `min(len(rows), 20)`, and its rendered X-axis tick labels equal to that response's first
     20 `tool_name`s **in order**. The XAxis has `dataKey="tool_name"` and `interval={0}`, so
     every charted series renders exactly one tick — a chart still drawing the previous
     range's tools fails the comparison, which presence alone cannot catch.
   - The steps being repeated are case steps 2/4/5, so every surface a tab actually has —
     table, count label, and (Tools only) chart — is asserted against that tab's own response.

## Expected Results
- Each of the three data tabs issues its own range-scoped request when the preset changes and
  re-renders its table (and, on the Agents tab, its two charts) consistently with that response.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Analytics → Agents tab under "Last 24d" | Page loads | step 1 | `step 1`: tab selected + agents GET resolved under `Last 24h` | clarification *(no "Last 24d" preset exists — the live presets are Last 24h/7d/30d/90d, and the live tab is "Agents & Pipelines"; same stale-case-text family as elitea-testing-public#1185/#1195)* |
| 2 Note the Chat Messages chart and Most Active Agents bar chart data | Completes | step 2 | `step 2`: both charts' presence + the Chat Messages chart's rendered X ticks/axis span vs the 24h response's `chat_daily` + table rows/count, all against the 24h response | asserted |
| 3 Click "Last 30d" | Control responds | step 3 | `step 3`: refetch with 30-day `date_from` | asserted |
| 4 Both charts update their data | Condition holds | step 4 | `step 4`: presence-iff-data for both charts + bar-chart subtitle series count + the Chat Messages chart's X ticks/axis span re-asserted against the 30-day `chat_daily` | asserted |
| 5 Agent Activity table updates | Condition holds | step 5 | `step 5`: row count + count label vs the 30-day response | asserted |
| 6 Repeat the steps for Users and Tools tabs | Completes | step 6 | `step 6a` (Users): rows + count label vs its own response under 30d and again under 24h — the tab renders no chart, so steps 2/4's chart half has no counterpart here. `step 6b` (Tools): rows + count label **and** the "Most Popular Tools" chart's presence-iff-data, `Top {N} by usage` subtitle and X-axis tick list vs its own response, under 24h and again under 30d | asserted |

**Axis 2 — Analyst additions.**
- Asserting **presence-iff-data** for the two Agents charts rather than unconditional presence —
  *added: both charts are conditionally rendered, so an unconditional assertion would fail
  honestly-correct product behaviour on a quiet project (live-observed: project 471 has 0
  agents/pipelines, so the bar chart is absent while the Chat Messages chart renders).*
- Asserting the Chat Messages chart's rendered AXIS against the response's `chat_daily` rather
  than only its presence — *added in fix round 1 after review: presence is invariant under a
  stale render, so "both charts update their data" (case step 4) was not actually being checked.
  The tick labels come from recharts' own SVG (#579-scoped handle inside
  `analytics-agents-chat-chart-container`) and are compared to the SYSTEM's response — no
  fabricated expectation.*
- Asserting the **Tools** tab's "Most Popular Tools" chart on its rendered X-axis tick list —
  *added in fix round 2 after review: case step 6 repeats steps 2/4/5, which include chart data,
  and the Tools tab has a chart of its own. It was previously neither asserted nor declared out
  of scope — the same defect class as the fix-round-1 chat-chart finding. Its ticks are read from
  recharts' own SVG (#579-scoped handle inside `analytics-tools-chart-container`) and compared to
  the SYSTEM's response rows — no fabricated expectation. The Users tab genuinely has no chart,
  which is now stated rather than left implicit.*
- Asserting the count LABEL as well as the row count — *added: catches a stale-count regression
  (label frozen while rows re-render) with a handle the tab already has.*

## Cleanup
None — read-only.

## Concrete Handles (discovered during exploration)

| Element | Locator | PROVENANCE |
|---|---|---|
| Agents tab content | `analytics-agents-row`, `analytics-agents-count`, `analytics-agents-activity-title`, `analytics-agents-chart-title/-subtitle/-container`, `analytics-agents-chat-chart-title/-container`, `analytics-agents-loading-indicator` | on-main ✓ (ELITEA-2320) |
| Users tab content | `analytics-users-row`, `analytics-users-count`, `analytics-users-loading-indicator` | on-main ✓ (ELITEA-2312) |
| Tools tab content | `analytics-tools-details-title`, `analytics-tools-count`, `analytics-tools-table-header`, `analytics-tools-row`, `analytics-tools-loading-indicator` | **added this case** — EliteaAI/EliteaUI@22ff73c0 on `automation/testids` (the Tools tab had ZERO testids) |
| Tools tab chart | `analytics-tools-chart-subtitle`, `analytics-tools-chart-container` | **added this case, fix round 2** — EliteaAI/EliteaUI@b74c4d90 on `automation/testids` (the "Most Popular Tools" chart had no handles at all) |
| Tabs / presets | `analytics-tab-*`, `analytics-date-preset-*` | on-main ✓ (ELITEA-2310) |

## Network Behavior
- Three distinct endpoints, one per tab, each carrying `date_from`/`date_to`:
  `…/analytics_agents/prompt_lib/{pid}`, `…/analytics_users/prompt_lib/{pid}`,
  `…/analytics_tools/prompt_lib/{pid}` (all with `limit`/`offset`/`search`/`sort_*`).
- Each fires on tab mount and again on a preset change while the tab is open.

## Known Defects Found During Exploration
- None new. The "Agents tab"/"Last 24d"/"Most Active Agents" naming drift is the already-filed
  family clarification elitea-testing-public#1195.

## Blocked Steps
None.

## Automation Hints
- The Tools tab renders `{total} tools` and a `TablePagination` with `rowsPerPage` default 20, so
  the rendered row count equals `min(total, rowsPerPage)` — assert against `len(rows)` from the
  response (the page slice the API returned), never against `total`.
- Live-observed 2026-08-28 (project 471): Agents tab has 0 rows and no bar chart even under 30d,
  while the Chat Messages chart renders — exactly the branch the presence-iff-data assertion
  covers.
