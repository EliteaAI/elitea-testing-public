# Test Case: Overview tab displays all KPI cards with correct labels and non-empty values

## Metadata
- **TMS ID**: ELITEA-2311
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2311/2322/2323/2324/2325)
- **Status**: ready-for-automation
- **Case-text drift filed**: elitea-testing-public#1948 (six cards -> eight; `AGENT RUNS` -> `AGENT & PIPELINE RUNS`; TEAM subtitle is split across three elements; adoption badge is conditional)

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected (the Analytics page's
  `Project: {name}` badge renders only when one is).
- No seeding required — the assertions below are oracle-driven (see § Fidelity) and hold for a
  project with zero activity as well as one with data.

## Test Data
### reuse-existing
Whatever the selected project already has. The test drives the **`Last 30d`** preset because a
30-day window is the cheapest way to exercise the `adoption_rate > 0` branch of the AI ACTIVE badge
(live 2026-08-28, project "Elitea Testing Team": `Last 24h` -> all-zero KPIs and **no** badge;
`Last 30d` -> `AI ACTIVE 2`, badge `↑11.1%`). Both branches are asserted conditionally on the
captured response, so neither range can make the test fail dishonestly.

## Test Steps

1. Navigate to Settings -> Analytics (case step 1). The Overview tab is selected by default
   (`activeTab` initial state `0`).
   - **Verify**: `analytics-tab-overview` has `aria-selected="true"`; the Overview KPI row
     (`analytics-overview-kpi-row`) is visible; the page's own GET
     (`/api/v2/elitea_core/analytics/prompt_lib/{project_id}`) resolved 200.
2. Click the `Last 30d` preset (`analytics-date-preset-30`), **capturing the resulting
   `analytics/prompt_lib/` response body** as the oracle for every value assertion below.
   - **Verify**: the response is 200 and carries a `kpis` object.
3. Verify the KPI card set (case steps 2-8).
   - **Verify**: exactly **8** cards (`analytics-overview-kpi-card`), and their labels
     (`analytics-overview-kpi-label`) in rendered order are exactly:
     `["TEAM", "AI ACTIVE", "LLM CALLS", "TOOL RUNS", "CHAT MSG", "AGENT & PIPELINE RUNS",
     "TOKENS", "COST"]`.
   - **Verify**: their subtitles (`analytics-overview-kpi-subtitle`) in the same order are
     `["active members", "{rate}% adoption", "event_type = llm", "event_type = tool",
     "user messages sent", "agents and pipelines interactions", "total LLM tokens consumed",
     "estimated USD cost"]`, where `{rate}` is `kpis.adoption_rate` from the captured response.
4. Verify the TEAM card's `X of Y` shape (case step 3).
   - **Verify**: card 1's value (`analytics-overview-kpi-value`) equals `fmtNum(kpis.unique_users)`
     and its suffix (`analytics-overview-kpi-value-suffix`) equals
     `f"of {fmtNum(kpis.total_project_users)}"`.
5. Verify the AI ACTIVE adoption badge (case step 4) — **conditional on the captured response**.
   - **Verify**: if `kpis.adoption_rate > 0`, card 2's badge (`analytics-overview-kpi-badge`) is
     visible, its text equals `f"↑{kpis.adoption_rate}%"`, and its computed `color` equals the
     theme's `palette.status.published` green (live `rgb(43, 212, 141)`).
   - **Verify**: if `kpis.adoption_rate == 0`, the badge is **absent**
     (`to_have_count(0)` on the badge testid) — the product's own documented branch.
6. Verify no card renders a degenerate value (case step 9, Expected Final State).
   - **Verify**: for all 8 cards, the value text is non-empty after strip and does not match
     (case-insensitively) `undefined`, `nan`, `null`, `-`; same for all 8 subtitles.
   - **Verify**: each card's value equals the corresponding formatted field of the captured
     response body (`unique_users`, `ai_active_users`, `llm_calls`, `tool_runs`, `chat_msgs`,
     `agent_runs`, `total_tokens` via `fmtNum`; `total_llm_cost` via `fmtCost`) — this is the
     assertion that actually proves the UI carried the backend's numbers through faithfully,
     rather than merely that *some* text is present.
7. No console errors throughout (use `utils/console_errors.collect_console_errors`).

## Expected Results
- The Overview tab renders 8 KPI cards with the exact label/subtitle tuple above; every value is a
  formatted rendering of the corresponding field of the analytics response, never blank,
  `undefined` or `NaN`; the AI ACTIVE green badge appears exactly when `adoption_rate > 0`.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings -> Analytics -> Overview | Page/section loads | step 1 | tab `aria-selected`, KPI row visible, 200 response | asserted |
| 2 Six KPI cards shown with correct labels/subtitles | Condition holds | steps 2-3 | exact 8-label + 8-subtitle tuple | **clarification** — live has EIGHT cards, not six (#1948); AFS asserts the live set |
| 3 TEAM — "X of Y active members" | Expected UI state | step 4 | value + suffix + subtitle, vs response `unique_users` / `total_project_users` | asserted *(rendered as three elements, not one string — #1948)* |
| 4 AI ACTIVE — value + adoption % in green + "% adoption" subtitle | Expected UI state | step 5 | badge presence/text/colour conditional on `adoption_rate > 0`; subtitle always | asserted *(badge is conditional — #1948)* |
| 5 LLM CALLS — numeric value + "event_type = llm" | Expected UI state | steps 3, 6 | subtitle tuple + value vs `kpis.llm_calls` | asserted |
| 6 TOOL RUNS — numeric value + "event_type = tool" | Expected UI state | steps 3, 6 | subtitle tuple + value vs `kpis.tool_runs` | asserted |
| 7 CHAT MSG — numeric value + "user messages sent" | Expected UI state | steps 3, 6 | subtitle tuple + value vs `kpis.chat_msgs` | asserted |
| 8 AGENT RUNS — numeric value + "agents and pipelines interactions" | Expected UI state | steps 3, 6 | subtitle tuple + value vs `kpis.agent_runs` | asserted *(label is `AGENT & PIPELINE RUNS` — #1948)* |
| 9 / Expected Final State — no card shows "undefined", "NaN" or blank | Condition holds | step 6 | degenerate-value guard across all 8 values + subtitles | asserted |

**Axis 2 — Analyst additions.**
- **Value-vs-response equality** (step 6, second bullet) — *added: "not blank / not NaN" alone
  passes on a card that renders a stale or wrong number. Comparing against the captured response
  body is the same oracle pattern the sibling AFS in this feature use and costs nothing extra
  (`.agents/testing.md` § Fidelity policy — "capture the real response and assert the UI against
  it").*
- **The two extra cards (TOKENS, COST)** — *added: they are part of the rendered set, so a count
  assertion of 8 must name them; leaving them out would let a regression drop one silently.*
- **Badge absence assertion in the zero branch** (step 5) — *added: makes the conditional-render
  contract test-enforced in both directions, and satisfies the #277 same-element-pair discipline
  for a conditionally-rendered testid.*
- **Console-error check** (step 7) — *standing project convention.*

## Cleanup
None — read-only. The test leaves the `Last 30d` preset selected; the page holds no persisted
state, and each test navigates fresh.

## Concrete Handles (discovered during exploration)

| Element | Locator | PROVENANCE |
|---|---|---|
| Overview tab | `analytics-tab-overview` | on-main ✓ |
| `Last 30d` preset | `analytics-date-preset-30` | on-main ✓ |
| KPI row | `analytics-overview-kpi-row` | on-main ✓ |
| KPI card (×8, repeated) | `analytics-overview-kpi-card` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) — awaiting human cherry-pick to `main` |
| KPI value (×8, repeated) | `analytics-overview-kpi-value` | on-`automation/testids` only (EliteaAI/EliteaUI@22ff73c0) |
| KPI label (×8, repeated) | **testid needed: `analytics-overview-kpi-label`** | needs-adding — new `labelTestId` prop on `components/KpiCard.jsx`, wired at the 8 `AnalyticsOverview.jsx` call sites ONLY |
| KPI subtitle (×8, repeated) | **testid needed: `analytics-overview-kpi-subtitle`** | needs-adding — new `subtitleTestId` prop on `KpiCard.jsx`, same 8 call sites |
| TEAM value suffix (`of Y`) | **testid needed: `analytics-overview-kpi-value-suffix`** | needs-adding — new `valueSuffixTestId` prop on `KpiCard.jsx`, wired at the TEAM call site (the only card passing `valueSuffix`) |
| AI ACTIVE adoption badge | **testid needed: `analytics-overview-kpi-badge`** | needs-adding — new `badgeTestId` prop on `KpiCard.jsx`, wired at the AI ACTIVE call site (the only Overview card passing `badge`) |

**Implementer notes on the testid work.**
- `KpiCard.jsx` already carries the `testId` / `valueTestId` prop pair (added for ELITEA-2313). The
  four new props follow the identical shape — `data-testid={labelTestId}` etc. — i.e. attribute-only
  edits, **no new DOM node, no new hook, no replaced MUI built-in** (`add-data-testid` § Step 5.5).
- `KpiCard` is a SHARED component (also consumed by `AnalyticsCosts`, `AnalyticsTokens`,
  `AnalyticsUserDetailed`, `AnalyticsAgentDetailed`, `UsageSummary`). Wire the new props **only at
  `AnalyticsOverview.jsx`'s 8 call sites** — leave the other consumers untouched
  (`.agents/testing.md` § Locator policy, shared-component rule + #511 scope rule).
- Repeated testids are the established pattern in this feature (`analytics-users-row`,
  `analytics-agents-row`); address individual cards with `.nth(i)` off the class-level descriptor.
- Page object: extend `automation/pages/analytics_page.py` (it already owns the tabs, presets and
  `overview_kpi_row`). New class-level `LocatorDescriptor` fields only — no locators in methods.

## Fidelity Declaration
No substitutions. Every asserted value is produced by the live system; the analytics GET's own
response body is captured live and used as the oracle for the numbers (`.agents/testing.md`
§ Fidelity policy — "capture the real response and assert the UI against it"). No `page.route`,
no `route.fulfill`, no `page.evaluate`-injected state.

## Network Behavior
- `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` — fires on
  page load and once per preset click. 200 OK, ~200-600 ms. Body carries
  `{kpis, top_ai_users, daily_activity, models, health}`.
- Wait on that response (`expect_response`), never on `networkidle` — see
  `.agents/testing.md` § Known issues (#1847: this app holds a persistent Socket.IO polling
  transport open, so `networkidle` is a race).

## Blocked Steps
None.

## Known Defects
- elitea-testing-public#1948 — case-text drift (clarification, not a product defect).
- elitea-testing-public#1951 — analytics count labels are not pluralised (MINOR, does not touch
  this case's assertions).

## Live Observations (2026-08-28, project "Elitea Testing Team")

`Last 24h` (default): TEAM `6` of `7`; every other KPI `0` / `$0.00`; **no** adoption badge.

`Last 30d`: TEAM `18` of `18`; AI ACTIVE `2` + badge `↑11.1%` (`rgb(43, 212, 141)`), subtitle
`11.1% adoption`; LLM CALLS `218`; TOOL RUNS `4`; CHAT MSG `306`; AGENT & PIPELINE RUNS `0`;
TOKENS `3.6M`; COST `$0.3182`. Zero console errors in both ranges.


## Implementation notes (ELITEA-2311, 2026-08-28 — implementer)

- **Shipped as** `automation/tests/ui/admin/test_analytics_overview_kpi_cards.py`
  (`TestAnalyticsOverviewKpiCards::test_overview_tab_kpi_cards`). Every handle in
  § Concrete Handles was added as specced; the four new `KpiCard.jsx` props
  (`labelTestId`/`subtitleTestId`/`valueSuffixTestId`/`badgeTestId`) are attribute-only and
  wired at `AnalyticsOverview.jsx`'s 8 call sites only — EliteaAI/EliteaUI@bc50bd9d.
- **The test runs against the `auth_state` fixture's project, not the analyst's exploration
  project** ("Elitea Testing Team"), so § Live Observations' numbers do not reproduce — which is
  exactly why every value assertion is oracle-driven off the captured response instead of
  hardcoded. Both branches of the adoption badge stay conditional on `kpis.adoption_rate`.
- `fmtNum` / `fmtCost` are ported into the spec as module-level helpers (suite-local; Hard Rule 7
  says extract to `utils/` on the third consumer, and this is the first).
