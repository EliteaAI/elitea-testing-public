# Health tab — Requests vs Errors chart + Health by Event Type table

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

_Session context for the 2026-08-28 entries: project "Elitea Testing Team", preset `Last 30d` unless stated; zero console errors across the whole Overview -> Tools -> Users -> Health -> Guide walk._

### Health tab (`AnalyticsHealth.jsx`, ELITEA-2324)
- **ZERO testids** on the file.
- Shares the **Overview endpoint** (`analytics/prompt_lib/`) — `needsOverview = activeTab === 0 ||
  activeTab === 6`. Switching to Health on an unchanged range is an RTK-Query **cache hit** and may
  fire NO request; capture the body around the preset click instead.
- Chart `Requests vs Errors` / subtitle `Total requests trend with error overlay`, two `Area` series
  (`#29B8F5` `Total Requests`, `#D71616` `Errors`). **There is no Legend** — the series NAMES exist
  in the DOM only inside the recharts hover tooltip. `Locator.hover()` on the chart works
  (live text: `2026-08-13 | Total Requests: 129 | Errors: 0`); `components/ChartTooltip.jsx` already
  has a `testId` prop, so wire `content={<ChartTooltip testId="analytics-health-chart-tooltip" />}`.
- Table `Health by Event Type`, columns `Event Type | Total | Errors | Error Rate | Avg Latency`
  (matches the case text exactly). **Rows are DATA-DRIVEN**, one per entry of the response's
  `health` array — live 5 rows (`llm, api, tool, socketio, rpc`), **no `agent`** row when agent runs
  are 0. The case's fixed six-row list is stale: filed elitea-testing-public#1949.
- Empty `health` -> the whole tab renders `No health data available.` instead of chart + table.
- Errors cell red iff `errors > 0` (live: `api` 947 -> `rgb(215, 22, 22)`); there is also an
  `error_rate > 5` red rule (not exercised — live max 2.92%). **This tab is the one place in the
  feature where the errors-red POSITIVE branch has live data.**


**Resolved/added during ELITEA-2324 implementation (2026-08-28):** the tab is no longer testid-free
— all 8 handles exist (EliteaAI/EliteaUI@bc50bd9d). Confirmed live: opening Health on an unchanged
range fires NO request (cache hit), `Locator.hover()` on `analytics-health-chart-container` raises
the tooltip naming both series, and the two area series are `<path class="recharts-curve
recharts-area-area">` which — like the Tools bar chart — mount one animation tick after the
container appears (wait on the first series node, never a sleep). Fixture-project rows: `api, llm,
rpc, socketio, tool` (5, still no `agent`).
