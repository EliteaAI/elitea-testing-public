# Surface digest — settings-analytics

> Handle cache from live exploration, not a source of truth. Verify a handle
> as you use it. One writer at a time (analyst, whoever is active this
> session) — see `test-case-analysis` § 2b.

## Where it lives

- URL: `/settings/analytics` (route registered under `Settings` parent route,
  `EliteaUI/src/[fsd]/app/routes/ProtectedRoutes.jsx:364`)
- Source: `EliteaUI/src/[fsd]/features/settings/ui/analytics/` —
  `AnalyticsContainer.jsx` (page shell: header, date filter, tab bar, tab
  routing) + one component per tab (`AnalyticsOverview`, `AnalyticsCosts`,
  `AnalyticsAgents`, `AnalyticsTools`, `AnalyticsUsers`, `AnalyticsHealth`,
  `AnalyticsGuide`) + `AnalyticsUserDetailed`/`AnalyticsAgentDetailed`/
  `AnalyticsToolDetailed` drill-down views.
- **Confirmed (2026-08-05, `git fetch origin` fresh): `AnalyticsContainer.jsx`
  is byte-identical on `main` and `automation/testids`** (same blob SHA) —
  the whole Analytics feature is already on `main`, not testids-only.

## Confirmed live behaviour (2026-08-05, localhost, project "UI Testing")

- **Tabs: SEVEN**, in this order: `Overview, Costs, Agents & Pipelines, Tools,
  Users, Health, Guide` — role `tablist` → 7 `tab` children. (Several sibling
  TMS cases in this family, e.g. ELITEA-2311/2320, describe "six tabs" /
  "Agents tab" — that phrasing is stale; the live tab set is the one above.
  See elitea-testing-public#1185.)
- **Date presets: four**, `Last 24h / Last 7d / Last 30d / Last 90d`
  (`TabGroupButton` + `TabButtonItem`, `DEFAULT_PRESETS` array,
  `AnalyticsContainer.jsx:35-39`). Default selected = **Last 24h**
  (`selectedDatePreset` initial state = `1`) → default From/To span is
  **1 day**, not 7. A 5th "Custom" preset appears only after the user edits
  a picker directly (`isCustomRange` branch) — not present on initial load.
- **Overview tab is selected by default** (`activeTab` initial state = `0`).
- **KPI cards on Overview: EIGHT**, not six — `TEAM, AI ACTIVE, LLM CALLS,
  TOOL RUNS, CHAT MSG, AGENT & PIPELINE RUNS, TOKENS, COST`
  (`AnalyticsOverview.jsx`). Same stale-case-text pattern as the tab count —
  flag if you hit a case claiming "six KPI cards" (e.g. ELITEA-2311).
- Loading state: `CircularProgress` shown only while `needsOverview &&
  isFetching` (`needsOverview` = Overview or Health tab active). Resolves
  quickly (~200 OK observed on `GET /api/v2/elitea_core/analytics/
  prompt_lib/{project_id}?date_from=...&date_to=...`), no console errors.
- Project badge (`Project: {name}`) only renders when a project is selected
  (`projectName` truthy) — precondition, not always-visible chrome.

## Testids

**Zero pre-existing testids** on anything in `AnalyticsContainer.jsx` except
`analytics-export-button` (Export to Excel icon button, already on `main`).
Header title, project badge, date presets, From/To pickers, and all 7 tabs
have NO testid — every case touching them needs `add-data-testid` work. Full
naming set + PROVENANCE for ELITEA-2310's touched elements:
`test-specs/settings-analytics/l2_analytics-page-default-load_ELITEA-2310.md`
§ Concrete Handles. Reuse those exact names for sibling cases that touch the
same elements (tabs, presets, title, badge) — don't re-derive/rename.

Shared-component wiring notes for the implementer:
- `TabButtonItem.jsx` (preset buttons) spreads `{...item.buttonProps}` onto
  its `ToggleButton` — pass `buttonProps: {'data-testid': '...'}` per preset
  item in `DEFAULT_PRESETS`.
- `BaseTab.jsx` spreads `{...restProps}` onto MUI `Tab`, which forwards
  unknown props to the underlying DOM button — pass `data-testid` directly
  on each `<BaseTab>` in the `.map()` at `AnalyticsContainer.jsx:278-284`.
- Date pickers currently share one `datePickerCommonProps` object between
  From and To — needs splitting (or a per-field override) so From/To can
  carry distinct testids via `slotProps.textField.inputProps`.

## No page object yet

`pages/analytics_page.py` does not exist — ELITEA-2310 is the first case in
this feature area. First implementer creates it.

## Users tab (`AnalyticsUsers.jsx`) — confirmed live 2026-08-05, ELITEA-2312

- **Confirmed (fresh `git fetch origin`): `AnalyticsUsers.jsx` is byte-identical
  on `main` and `automation/testids`** (blob `c7b6ff4b68aec5e6f8b72e433cbe8c62126e5d04`
  on both) — like the rest of the Analytics feature, already fully on `main`.
- **Zero pre-existing testids** on `AnalyticsUsers.jsx` or the shared
  `src/components/SearchInput.jsx` it renders — every element this tab's cases
  touch needs `add-data-testid` work (10 new testids specced in ELITEA-2312's
  AFS: title, count, search input via a new `testId` prop on the shared
  component, table-header row, repeated row/errors-cell testids, and 4
  `TablePagination` `slotProps` wirings).
- **Table has 9 columns**, not the 8 several sibling case texts describe:
  `User, Active Days, LLM Calls, Tool Calls, Agent/Pipeline Runs, Chat Msg,
  Errors, Total Tokens, Total Cost` — no "Events" column exists. Same
  stale-case-text family as the tab/KPI counts above. Filed
  elitea-testing-public#1188.
- **Errors column color rule** (`AnalyticsUsers.jsx:144-151`):
  `color: u.errors > 0 ? palette.status.rejected : undefined` — red only when
  `errors > 0`; `errors === 0` renders default text color (confirmed live:
  `rgb(255, 255, 255)`). Case texts describing "red when ≥ 0" are stale — same
  issue #1188.
- **Search input live-filters** on every keystroke (`onChange` → `search`
  state → query param), no debounce/Enter/blur needed — confirmed live
  (typing "testbot" narrowed 3→1 row, updated count + pagination label).
- **Pagination**: MUI `TablePagination`, `rowsPerPageOptions=[10,20,50]`,
  default `rowsPerPage=20`. With ≤20 total users it's a single page — both
  prev/next arrows disabled, range label `"1–{total} of {total}"`.
- **Data endpoint**: `GET /api/v2/elitea_core/analytics_users/prompt_lib/
  {project_id}?date_from=...&date_to=...&limit=...&offset=...&sort_by=total_events&sort_order=desc`
  — distinct from the Overview/Health endpoint (`.../analytics/prompt_lib/...`,
  no `_users`); fires on tab mount and on every search-input change. 200 OK,
  no console errors, in both cases observed.
- **No positive-case (`errors > 0`) live data available** in the "UI Testing"
  exploration project — all 3 users observed have `errors: 0`. The red-color
  branch is source-confirmed but not live-exercised; ELITEA-2312's AFS
  documents this as a Blocked Step, not a defect. A future case/project with
  a genuine error-attributed analytics row should extend the test to cover it.
