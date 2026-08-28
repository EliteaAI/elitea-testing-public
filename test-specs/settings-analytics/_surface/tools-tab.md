# Tools tab — Most Popular Tools chart + Tool Details table

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

_Session context for the 2026-08-28 entries: project "Elitea Testing Team", preset `Last 30d` unless stated; zero console errors across the whole Overview -> Tools -> Users -> Health -> Guide walk._

### Tools tab (`AnalyticsTools.jsx`, ELITEA-2322)
- Chart `Most Popular Tools`, subtitle `Top {N} by usage` where N = `min(len(rows), 20)`; the whole
  chart is behind `toolChartData.length > 0` — absent on a project with no tool calls.
- Bar fills come from `AnalyticsCommonConstants.CHART_COLORS[i % len]` -> distinct while
  N <= len(CHART_COLORS). Live: `#10A37F`, `#4285F4`.
- Table `Tool Details`, count `{total} tools`, header `Tool | Calls | Users | Avg Latency | Errors`
  (DOM text is title-case; uppercase is `text-transform` CSS — same as Users/Health).
- Search placeholder `Search by tool name`; `src/components/SearchInput.jsx` already has the
  `testId` prop, so wiring it is **call-site only**.
- Pagination: `TablePagination`, options `[10,20,50]`, default 20, range `1–2 of 2`.
- **Still missing testids**: `analytics-tools-chart-title`, `-search-input`, `-row-errors`,
  `-pagination-rows-select`, `-pagination-range`. Copy the `slotProps` shape verbatim from
  `AnalyticsUsers.jsx:213-220`.
- No `errors > 0` tool row in this project — the errors-red branch is source-confirmed only. Spec it
  as a two-directional invariant (red iff `errors > 0`), not a one-way "is red".


**Resolved/added during ELITEA-2322 implementation (2026-08-28):** all five missing testids exist
(EliteaAI/EliteaUI@bc50bd9d) plus `analytics-tools-pagination-rows-menu` on the MUI rows-per-page
menu list (EliteaAI/EliteaUI@aad6227c) so the option set can be read through an app-testid parent.
Two live facts the digest did not have:
- **The `CHART_COLORS` palette has 10 entries and the fill is `CHART_COLORS[i % 10]`** — with more
  than 10 tools the colours REPEAT by design. The fixture project has 34 tools (20 plotted), so
  "each bar has a distinct colour" is false there; filed as case-text drift #1952 and asserted as
  distinct-within-10 + exact palette cycling.
- **Recharts mounts the bar `<path>` nodes one animation tick AFTER the chart container is
  visible** (measured: 0 bars on a container-visible wait). Wait on the first bar node itself.
- The fixture project DOES have tool rows with `errors > 0`, so the errors-red positive branch is
  live-exercisable there (unlike the analyst's exploration project).
