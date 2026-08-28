# Overview tab — KPI cards, charts, leaderboard

> Part of the `settings-analytics` exploration digest — index: [`_surface.md`](../_surface.md).
> Handle cache from live exploration, not a source of truth: verify a handle as you use it.

_Session context for the 2026-08-28 entries: project "Elitea Testing Team", preset `Last 30d` unless stated; zero console errors across the whole Overview -> Tools -> Users -> Health -> Guide walk._

### Overview KPI cards (ELITEA-2311)
- **EIGHT cards**, labels in order: `TEAM, AI ACTIVE, LLM CALLS, TOOL RUNS, CHAT MSG,
  AGENT & PIPELINE RUNS, TOKENS, COST` (the "Tabs: SEVEN"-style stale-count family again — the case
  says six and calls #6 "AGENT RUNS"; filed elitea-testing-public#1948).
- Card internals are **three separate elements**: value (`analytics-overview-kpi-value`), an
  optional `valueSuffix` (TEAM only — `of 7`), and the subtitle. The case's `"X of Y active members"`
  is not one string.
- **AI ACTIVE's green badge is CONDITIONAL**: `badge={kpis.adoption_rate > 0 ? ... : undefined}`.
  Live `Last 24h` (all-zero data) -> no badge; `Last 30d` -> `↑11.1%` in `rgb(43, 212, 141)`
  (`palette.status.published`). Assert it conditionally on the response, never unconditionally.
- Existing testids: `analytics-overview-kpi-row` (on main), `analytics-overview-kpi-card` +
  `analytics-overview-kpi-value` (`automation/testids` only, EliteaAI/EliteaUI@22ff73c0).
  **Still missing**: label, subtitle, value-suffix, badge — all four need new props on the SHARED
  `components/KpiCard.jsx` (`labelTestId`/`subtitleTestId`/`valueSuffixTestId`/`badgeTestId`), wired
  at `AnalyticsOverview.jsx`'s 8 call sites ONLY (KpiCard is also consumed by Costs, Tokens,
  UserDetailed, AgentDetailed, UsageSummary).


**Resolved/added during ELITEA-2311 implementation (2026-08-28):** the four missing KPI-card
handles now exist — `analytics-overview-kpi-label`, `-subtitle`, `-value-suffix`, `-badge`, wired as
new attribute-only props on the shared `components/KpiCard.jsx` at `AnalyticsOverview.jsx`'s 8 call
sites only (EliteaAI/EliteaUI@bc50bd9d). The `auth_state` fixture's project — NOT the analyst's
exploration project — is what the suite actually sees, so per-project numbers here are indicative
only; assert values against the captured `analytics/prompt_lib/` body
(`AnalyticsPage.select_date_preset_capturing_analytics` / `navigate_capturing_analytics` return it).
