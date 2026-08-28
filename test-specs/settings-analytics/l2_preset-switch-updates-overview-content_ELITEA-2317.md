# Test Case: Switching preset filters updates KPI cards, charts, and tables on Overview tab

## Metadata
- **TMS ID**: ELITEA-2317
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w06`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected; Overview is the default tab.

## Test Data
### reuse-existing
- Whatever analytics data the selected project already has. **No assertion depends on the project
  having activity** — every content assertion is made against the response body returned for the
  range under test (§ Axis 2), so an all-zero project passes exactly as a busy one does.

## Test Steps
1. Navigate to Settings → Analytics and click `Last 7d` (the case's "Overview tab under Last 7d").
   - **Verify**: Overview tab is selected; the analytics GET for the 7-day range resolves; the page
     settles out of loading.
2. Capture the Overview state under `Last 7d` (case step 2 — "note the values"):
   - the 8 KPI card values (`analytics-overview-kpi-value`), read in DOM order;
   - the Daily Activity chart's rendered X-axis tick labels;
   - the leaderboard row count and the Model Usage Breakdown row count.
   - **Verify** each against the captured 7-day response body: KPI values equal the formatted
     `kpis.*` fields; leaderboard row count equals `len(top_ai_users)` (and the container is absent
     when that list is empty); model-usage row count equals `len(models)` (container absent when
     empty); every rendered X tick is a `MM-DD` form of one of the response's `daily_activity`
     dates.
3. Click `Last 30d` (case step 3).
   - **Verify**: the analytics GET re-fires with `date_from` ≈ 30 days back and its `date_to`
     ≈ now; the response resolves 200.
4. Verify the KPI card values update (case step 4): the 8 rendered values now equal the **30-day**
   response's `kpis.*` values (same read, new oracle).
5. Verify the Daily Activity chart time axis extends to cover 30 days (case step 5): the rendered
   first and last X ticks span **≥ 20 days** (recharts thins labels, so the span is asserted, not a
   tick-per-day count), the last tick is the response's last `daily_activity` date, and the span is
   strictly larger than the span observed in step 2 under `Last 7d`.
6. Verify the Top 5 AI Adopters table and the Model Usage Breakdown table update (case step 6):
   both render consistently with the 30-day response (row counts equal `len(top_ai_users)` /
   `len(models)`, capped at the product's own top-5 slice), and the leaderboard's first-row email
   and event count equal the response's first entry.

## Expected Results
- Every Overview surface (8 KPI cards, Daily Activity chart, Top-5 leaderboard, Model Usage
  Breakdown) re-renders from the response for the newly selected range.
- The chart's time axis widens with the range.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics → Overview under Last 7d | Page loads | step 1 | `step 1`: tab selected + 7-day GET resolved | asserted |
| 2 Note values of all 6 KPI cards and the Daily Activity chart shape | Completes | step 2 | `step 2`: **8** KPI values + chart ticks captured and each verified against the 7-day response | clarification *(live Overview has EIGHT KPI cards — TEAM, AI ACTIVE, LLM CALLS, TOOL RUNS, CHAT MSG, AGENT & PIPELINE RUNS, TOKENS, COST — not six; same stale-case-text family as elitea-testing-public#1185)* |
| 3 Click "Last 30d" | Control responds | step 3 | `step 3`: preset pressed + refetch with 30-day `date_from` | asserted |
| 4 KPI card values update | Condition holds | step 4 | `step 4`: all 8 values equal the 30-day response's `kpis.*` | asserted |
| 5 Daily Activity chart time axis extends to cover 30 days | Condition holds | step 5 | `step 5`: rendered tick span ≥ 20 days, last tick == response's last date, span > the 7-day span | asserted |
| 6 Top 5 AI Adopters and Model Usage Breakdown tables update | Condition holds | step 6 | `step 6`: row counts == response list lengths; first leaderboard row's email + event count == response's first entry | asserted |

**Axis 2 — Analyst additions.**
- **The response is the oracle, not "the numbers changed".** *Added deliberately per
  `.agents/testing.md` § Fidelity policy → "How to test a NONDETERMINISTIC producer without
  substituting it": every asserted value is produced by the system (captured live from the real
  GET), and the assertion is deterministic regardless of how much activity the project has. A
  literal "values must differ between 7d and 30d" assertion would be data-dependent and would fail
  honestly-green product behaviour on a quiet project (live-observed 2026-08-28: project 471 shows
  all-zero KPIs and NO Model Usage table under 7d, populated content under 30d — the contrast
  exists today and may not exist next month).*
- Asserting the Model Usage Breakdown container is **absent** when the response has no models —
  *added: `ModelUsageTable` returns `null` for an empty list (`ModelUsageTable.jsx:14`), so the
  absence is the product's contract for that branch, and the absence assertion is what makes the
  presence assertion meaningful.*

## Cleanup
None — read-only.

## Concrete Handles (discovered during exploration)

| Element | Locator | PROVENANCE |
|---|---|---|
| KPI cards / values | `analytics-overview-kpi-card` / `analytics-overview-kpi-value` (repeat ×8, `.nth(i)`) | **added this case** — EliteaAI/EliteaUI@22ff73c0 (reuses the shared `KpiCard` `testId`/`valueTestId` props from ELITEA-2313) |
| Daily Activity chart container | `analytics-overview-daily-chart-container` | **added this case** — EliteaAI/EliteaUI@22ff73c0 |
| X-axis tick labels | scoped raw handle inside that container (`.recharts-xAxis .recharts-cartesian-axis-tick-value`) | n/a — recharts internal SVG, **#579 exception 1**, declared in the page-object docstring |
| Top 5 AI Adopters | `analytics-overview-leaderboard` + `analytics-overview-leaderboard-row` | **added this case** — EliteaAI/EliteaUI@22ff73c0 |
| Model Usage Breakdown | `analytics-overview-model-usage-table` + `analytics-overview-model-usage-row` | **added this case** — EliteaAI/EliteaUI@22ff73c0 |
| Presets / KPI row | `analytics-date-preset-*`, `analytics-overview-kpi-row` | on-main ✓ (ELITEA-2310) |

## Network Behavior
- One `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=…&date_to=…` per preset
  click; the body carries `kpis`, `top_ai_users`, `daily_activity`, `models`, `health`.
- Live-observed 2026-08-28 (project 471): 7d → `kpis` all zero, `top_ai_users` empty (leaderboard
  shows "No AI activity data."), `models` empty (no Model Usage table), 8 X ticks 08-21…08-28;
  30d → LLM CALLS 218, 5 leaderboard rows, 4 model rows, X ticks 07-31…08-28.

## Known Defects Found During Exploration
- None. Case-text "6 KPI cards" drift is covered by the existing family clarification
  elitea-testing-public#1185.

## Blocked Steps
None.

## Automation Hints
- **The tick span is measured against the RESPONSE's own dates, never by month arithmetic on the
  year-less labels.** Recharts renders `date.slice(5)` ("MM-DD"), so each rendered tick is
  resolved back to the full `YYYY-MM-DD` entry of `daily_activity` before the two are
  differenced. Differencing the bare `MM-DD` parts is wrong across a year boundary — a Last-30d
  window on e.g. 2027-01-10 renders `12-11…01-10`, which month arithmetic scores as -331 days
  and which would fail the `span >= 20` assertion every January (found in review, fix round 1;
  pinned by `tests/unit/test_analytics_date_filter_spec_invariants.py`).
- KPI value ↔ response field mapping (`AnalyticsOverview.jsx`, DOM order):
  `TEAM=kpis.unique_users`, `AI ACTIVE=kpis.ai_active_users`, `LLM CALLS=kpis.llm_calls`,
  `TOOL RUNS=kpis.tool_runs`, `CHAT MSG=kpis.chat_msgs`, `AGENT & PIPELINE RUNS=kpis.agent_runs`,
  `TOKENS=kpis.total_tokens`, `COST=kpis.total_llm_cost`.
- The first seven are rendered through `AnalyticCommonHelpers.fmtNum` (`>=1e6 → "{x}M"`,
  `>=1e3 → "{x}K"`, `null → "-"`); the test mirrors that 4-line rule to build the expected string
  from the response value. **COST is deliberately NOT mirrored** — `fmtCost` has seven magnitude
  branches and mirroring it would duplicate product logic with a real divergence risk; the COST
  card is asserted as: starts with `$`, and is exactly `$0.00` iff the response's `total_llm_cost` is
  0, non-zero otherwise. Declared as a deliberate assertion-strength choice, not a weakening of a
  case requirement (the case asks that the values update, which the seven mirrored cards prove).
- Wait on the response (`expect_response`) around the preset click, then on the KPI row being
  visible again — the Overview subtree unmounts while `isFetching`.
