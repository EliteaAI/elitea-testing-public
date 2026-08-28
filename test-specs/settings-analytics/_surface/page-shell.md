# Page shell — route, tabs, presets, project badge

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

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

- **Tabs: EIGHT** (this line said SEVEN until 2026-08-28 — a `Tokens` tab was added and is on `main`).
  ⚠️ The historical list below is kept for context; the CURRENT order is: `Overview, Costs, Tokens,
  Agents & Pipelines, Tools, Users, Health, Guide` (testids `analytics-tab-{overview,costs,tokens,
  agents-pipelines,tools,users,health,guide}`). `AnalyticsPage.get_tabs_in_order()` still returns
  seven Locators and has no `tab_tokens` field. Superseded detail:
- ~~**Tabs: SEVEN**~~, in this order: `Overview, Costs, Agents & Pipelines, Tools,
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
