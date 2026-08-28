# Date filter — presets + From/To pickers

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

## Date filter (presets + From/To pickers) — confirmed live 2026-08-28, ELITEA-2314..2319

**⚠️ The "Tabs: SEVEN" note above is now STALE.** The live tab bar has **EIGHT** tabs, in this
order: `Overview, Costs, Tokens, Agents & Pipelines, Tools, Users, Health, Guide` — a **Tokens**
tab (`AnalyticsTokens`, `activeTab === 2`, testid `analytics-tab-tokens`) was added after
ELITEA-2310 shipped and is **on `main`**. Consequences the next agent must know:
`AnalyticsPage.get_tabs_in_order()` still returns seven Locators and has no `tab_tokens` field, and
ELITEA-2310's merged spec still asserts a 7-label tuple — see elitea-testing-public issue filed
from the ELITEA-2314..2319 run. `needsOverview` is still `activeTab === 0 || activeTab === 6`
(Overview / Health), which is correct for the 8-tab indexing.

- **Presets fire one `analytics/prompt_lib/` GET per click**, `date_from = now - Ndays`,
  `date_to = now`; the four spans were live-verified (1/7/30/90 days, ±minutes). Clicking the
  ALREADY-active preset is a deliberate no-op (`handleDatePresetChange` returns early on MUI's
  exclusive-`ToggleButtonGroup` `null`), so a test that starts by clicking the default preset
  observes nothing.
- **Editing either picker switches the control to `Custom`**: a FIFTH chip appears
  (`PRESETS_WITH_CUSTOM`) and is `aria-pressed="true"` while all four predefined presets go
  `false`. It now carries `analytics-date-preset-custom` (added 2026-08-28).
- **Picker mechanics** (`@mui/x-date-pickers` v7 `DateTimePicker`, `format dd/MM/yyyy HH:mm`,
  `ampm: false`): the field is a plain editable `<input>` (`input_value()` works). The action bar
  is `['clear','accept']` with `okButtonLabel: 'Apply'` — the confirm button reads **"Apply"**, not
  "Ok" as several case texts say. **Selecting a day fires the data GET immediately** (`onChange`);
  **Apply only closes the popper and fires nothing** — wait on the response around the day click.
- **Constraint pair**: From has `maxDateTime={dateTo}`, To has `minDateTime={dateFrom}`. Live: with
  To = 23/08, the From calendar renders 24..31 disabled and "Next month" disabled; with From =
  10/08, the To calendar renders 1..9 disabled and "Previous month" disabled. This is the whole
  mechanism behind ELITEA-2316 — there is no error message, the prevention is the disabled state.
- **New testids (EliteaAI/EliteaUI@22ff73c0, `automation/testids`, awaiting human cherry-pick to
  `main`)**: `analytics-date-preset-custom`, `analytics-date-{from,to}-open-button`,
  `analytics-date-{from,to}-popper`, `analytics-overview-kpi-card`, `analytics-overview-kpi-value`,
  `analytics-overview-daily-chart-container`, `analytics-overview-leaderboard(-row)`,
  `analytics-overview-model-usage-table(-row)`, `analytics-tools-details-title`,
  `analytics-tools-count`, `analytics-tools-table-header`, `analytics-tools-row`,
  `analytics-tools-loading-indicator`.
- **Inside the popper everything is MUI-internal** — day cells (`button.MuiPickersDay-root`), the
  month header, the month-nav arrows and the Clear/Apply buttons cannot carry an app testid without
  overriding MUI slot components (a functional change). They are reached as **scoped raw handles
  inside the `analytics-date-{from,to}-popper` testid**, the `.agents/testing.md` § Locator policy
  #579 exception 1, declared in `AnalyticsPage`'s method docstrings.
- **Overview content is data-conditional**: `ModelUsageTable` returns `null` for an empty `models`
  list, and the leaderboard renders "No AI activity data." instead of rows when `top_ai_users` is
  empty. Live 2026-08-28, project 471 "Elitea Testing Team": `Last 7d` → all-zero KPIs, no
  leaderboard rows, no Model Usage table; `Last 30d` → LLM CALLS 218, leaderboard + 4 model rows.
  **Do not write "the numbers must differ" assertions** — assert the rendered content against the
  captured response body instead (`.agents/testing.md` § Fidelity policy).
- **Daily Activity X-axis** renders `MM-DD` labels (`tickFormatter: d => d?.slice(5)`) and recharts
  THINS them (30-day range showed 10 ticks, 07-31…08-28, skipping days) — assert the span and the
  last tick, never a tick-per-day count.
- **Date filter state survives every tab switch** (it lives in `AnalyticsContainer`, above the tab
  bodies): live-verified across Agents & Pipelines → Tools → Users → Health → Guide → Overview, all
  six holding From `29/07/2026 18:27` / To `28/08/2026 18:27` with `Last 30d` pressed.
- **⚠️ Dev-server gotcha (cost ~15 min this run):** Vite's file watcher did NOT see edits to
  `../EliteaUI/src` (OneDrive-backed clone) — the server kept serving the pre-edit module for both
  the plain and `?t=` URLs even after `touch`, so new testids were invisible in the browser while
  present on disk. **Restarting the dev server fixed it.** Verify a new testid via
  `curl -s 'http://localhost:5173/src/%5Bfsd%5D/.../File.jsx' | grep <testid>` before concluding the
  testid is wrong.

### Resolved/added during ELITEA-2314..2319 implementation (2026-08-28)

- **Wide-range analytics queries are SLOW.** `Last 30d`/`Last 90d` on the `auth_state` fixture's
  project (id **399**, the one the pytest session lands on — distinct from the project a
  Playwright-MCP browser session shows) regularly need **more than 15 s** to answer, while
  `Last 24h`/`Last 7d` come back in a few seconds. `NAVIGATION_TIMEOUT` (15 s) is NOT enough:
  `AnalyticsPage` now has `DATA_QUERY_TIMEOUT = 60_000` for every range-changing wait. A
  `TimeoutError: … waiting for event "response"` on a preset click is this, not a missing request.
- **Recharts axis ticks need `all_text_contents()`, never `all_inner_texts()`** — SVG `<text>`
  nodes have no `innerText`, so `all_inner_texts()` yields `None` entries and blows up on `.strip()`.
- **MUI keeps the outgoing month grid mounted during a picker month transition** — right after a
  "Previous month" click the same day number resolves to 2-4 nodes (measured: 4 across a 3-month
  walk), a strict-mode violation. `AnalyticsPage.get_picker_day_cell()` now waits for the match to
  settle to exactly one (`expect(...).to_have_count(1)`) — a condition wait, not a sleep.
- **Response ≠ render on every tab**: `expect_response` returning does not mean rows exist yet.
  `AnalyticsPage.wait_for_tab_settled(surface)` (public, additive sibling of the private
  `_wait_for_*_settled` helpers) closes the gap for overview/users/agents/tools.

### Resolved/added during ELITEA-2314..2319 fix round 1 (2026-08-28)

- **`wait_for_tab_settled(surface)` now genuinely exists** on `AnalyticsPage` (surface-keyed
  `_loading_indicator()` + a `wait_for(state="hidden")`). The previous round documented it here
  and called it from five spec sites without ever defining it — a spec in that state raises
  `AttributeError` on the first call, so it cannot have been run. Pinned by
  `tests/unit/test_analytics_date_filter_spec_invariants.py`, which AST-walks both specs and
  checks every `analytics_page.<attr>` against the page object's real MRO members.
- **Recharts tick labels are YEAR-LESS (`date.slice(5)` → `"MM-DD"`).** Never difference them
  arithmetically: a Last-30d window straddling New Year renders `12-11…01-10`, which
  month-arithmetic scores as **-331 days**. Resolve each tick back to the full `YYYY-MM-DD` entry
  of the response's own series first (`_response_dates` / `_chart_tick_span_days` in
  `test_analytics_date_filter_content_refresh.py`).
