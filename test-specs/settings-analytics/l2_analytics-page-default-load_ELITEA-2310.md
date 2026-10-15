# Test Case: Analytics page loads with default date range and all tabs visible

## Metadata
- **TMS ID**: ELITEA-2310
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids` — confirmed identical blob to `main` for
  `AnalyticsContainer.jsx`, so this surface is fully on `main` already)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost — no manual login)
- **Analyst**: qa-engineer (analyst slot), batch `elitea-2310`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips login via `VITE_DEV_TOKEN`).
- A project is selected (project badge only renders when `projectName` is truthy — confirmed live: "Project: UI Testing").

## Test Data
### reuse-existing
- No test data required — page loads with the currently-selected project's data (KPI values observed as `0`/`$0.00` in the exploration project, which is fine — the case only asserts structure/loading-state, not specific values).

## Test Steps
1. Navigate to `${BASE_URL}/settings/analytics`.
   - **Verify**: URL is `/settings/analytics`; page loads without error.
2. Verify the page header shows the "Analytics" title text and, when a project is selected, the "Project: {name}" badge.
3. Verify the date filter bar shows exactly four preset toggle buttons, in order: "Today", "Last 7d", "Last 30d", "Last 90d".
4. Verify the "Today" preset button is the one shown pressed/active by default (`aria-pressed="true"`; the other three are `aria-pressed="false"` or absent).
5. Verify the From and To date/time inputs are present and, with the default "Today" preset selected, span the current calendar day: From = start of today (00:00), To = end of today (23:59) — a calendar-day span, NOT a rolling 24-hour-apart pair ending at "now".
6. Verify all ten Analytics tabs are visible, in order: "Overview", "Costs", "Tokens", "Agents & Pipelines", "Skills", "Tools", "Users", "Activity", "Health", "Guide". (The "Skills" tab is permission-gated — `canViewSkills` — and only verified-visible for a user holding that permission; this case's `${TEST_USER}` holds it.)
7. Verify the "Overview" tab is selected by default (`aria-selected="true"`; MUI tab indicator under it).
8. Verify the page does not remain in a permanent loading state: the loading spinner (shown only while the Overview/Health-feeding analytics query is in flight) is not present/visible once the page has settled, and the Overview tab's content (KPI row) is rendered.

## Expected Results
- Page renders at `/settings/analytics` with header, date filter bar, and tab bar all visible.
- Default preset is "Today" (`selectedDatePreset` initial state = `0`), not "Last 24h" and not "Last 7d" — the From/To pickers reflect a calendar-day span (today 00:00:00 → today 23:59:59.999), not a rolling 24h-apart pair and not a 7-day span. **Second drift found during this adjustment (ELITEA-2310, 2026-10-15, product commit `EL-6791` 2026-09-28): the preset label itself changed from "Last 24h" to "Today", and the date math changed from a rolling 24h window to a calendar-day window — this is a deliberate, already-shipped product change, not a regression.**
- Ten tabs are present (not seven) — "Tokens", "Skills", "Activity" are three additional real tabs added since the original automation (`EL-6211`/`EL-5110`/`EL-6929` — see Adjustment section). "Costs" and "Agents & Pipelines" remain real, separate tabs the original case text omitted/mislabeled (prior clarification, elitea-testing-public#1185, unchanged).
- "Overview" tab is selected/underlined by default.
- No permanent loading state: `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` resolves 200 and the Overview KPI content renders; no console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics | Target page/section loads successfully | step 1 | `step 1`: URL + no error | asserted |
| 2 Page header shows "Analytics" + project name badge | Condition holds | step 2 | `step 2`: title + badge text | asserted |
| 3 Date filter bar shows four preset buttons: Last 24h/7d/30d/90d | Condition holds | step 3 | `step 3`: 4 toggle buttons, exact labels/order (now "Today"/"Last 7d"/"Last 30d"/"Last 90d") | clarification *(adjustment 2026-10-15: live product renamed the first preset from "Last 24h" to "Today" — `EL-6791` — count stays 4, order stays the same)* |
| 4 "Last 24d" is active/highlighted by default | Condition holds | step 4 | `step 4`: "Today" is the pressed preset | clarification *(case says "Last 24d" — typo for "Last 24h", itself since superseded; live default preset is now "Today" — `EL-6791`)* |
| 5 From/To pickers present, reflect the Last 7d range | Condition holds | step 5 | `step 5`: pickers present, reflect the actual default (calendar-day span: today 00:00 → today 23:59) | clarification *(case's "Last 7d" already contradicted its own step 4 default pre-adjustment; adjustment 2026-10-15 further found the default range itself changed from a rolling-24h window to a calendar-day window — `EL-6791`)* |
| 6 Six tabs visible: Overview, Agents, Tools, Users, Health, Guide | Condition holds | step 6 | `step 6`: all ten live tabs asserted (Overview, Costs, Tokens, Agents & Pipelines, Skills, Tools, Users, Activity, Health, Guide) | clarification *(product now has 10 tabs — 3 added since original automation: Tokens/`EL-6211`, Skills/`EL-6929` (permission-gated), Activity/`EL-5110`; case's 6-tab list is stale; reverse-masking guard: live product is correct)* |
| 7 Overview tab active/underlined by default | Condition holds | step 7 | `step 7`: `aria-selected` on Overview tab | asserted |
| 8 Page does not remain in permanent loading state | Condition holds | step 8 | `step 8`: spinner absent + KPI content rendered after wait | asserted |

Case-text drift filed as clarification issue **elitea-testing-public#1185** ("[Clarification][ELITEA-2310] Case text says six tabs/Last 24d/Last 7d default; live product has seven tabs, Last 24h default (1-day range)") — bundles rows 4, 5, 6 above (all three drifts trace to the same root cause: the case was authored against a stale spec). Live product is the correct source per the reverse-masking guard (`test-case-analysis` SKILL.md § Classify findings); this AFS asserts the **live** contract in steps 3–6, not the case's stale numbers.

**Axis 2 — Analyst additions.**
- `step 1` asserts no error on load (beyond the case's bare "loads successfully") — *added: cheap smoke check, catches a routing regression.*
- `step 8` asserts absence of the loading spinner AND presence of Overview KPI content (case only asks for "not a permanent loading state") — *added: a spinner disappearing without content appearing would itself be a silent-failure state (e.g. `isError` branch swallowed); both halves needed to prove the page actually settled into a working state, not just past the spinner.*
- `step 3`/`step 6` assert exact **order** of presets/tabs, not just presence — *added: order is part of the visible UI contract and is cheap to assert while the handle is already captured.*

## Cleanup
None — read-only page load, no data created or mutated.

## Concrete Handles (Handles Reference, ladder-verified live on DEV, 2026-10-15 adjustment)

**Provenance note (superseded 2026-10-15):** the original automation (2026-08) added 16 new
testids via `add-data-testid`; all are now deployed and confirmed present on DEV (`testid on
DEV ✓` for every row below — rung 1, no climbing needed). Three rows are **new since the
original automation** (`analytics-tab-tokens`, `analytics-tab-skills`, `analytics-tab-activity`
— added by product commits `EL-6211`/`EL-6929`/`EL-5110`, confirmed present + unique on
`origin/main` via `git grep`), and one row's testid changed in place
(`analytics-date-preset-1` → `analytics-date-preset-0`, `EL-6791`).

| Rung | Element | Handle | Suggested testid | Provenance | Notes |
|---|---|---|---|---|---|
| 1 | Page title "Analytics" | `LocatorDescriptor(testid="analytics-page-title")` | — | testid on DEV ✓ | unchanged |
| 1 | Project name badge | `LocatorDescriptor(testid="analytics-project-badge")` | — | testid on DEV ✓ | unchanged |
| 1 | Preset button — **Today** (was "Last 24h") | `LocatorDescriptor(testid="analytics-date-preset-0")` | — | testid on DEV ✓ | **changed 2026-10-15**: `AnalyticsContainer.jsx:49` `DEFAULT_PRESETS` item is now `{label:'Today', value:0, buttonProps:{'data-testid':'analytics-date-preset-0'}}` (`EL-6791`, commit `425570d5`, 2026-09-28) — old `analytics-date-preset-1` testid no longer exists in the DOM |
| 1 | Preset button — Last 7d | `LocatorDescriptor(testid="analytics-date-preset-7")` | — | testid on DEV ✓ | unchanged |
| 1 | Preset button — Last 30d | `LocatorDescriptor(testid="analytics-date-preset-30")` | — | testid on DEV ✓ | unchanged |
| 1 | Preset button — Last 90d | `LocatorDescriptor(testid="analytics-date-preset-90")` | — | testid on DEV ✓ | unchanged |
| 1 | From date/time input | `LocatorDescriptor(testid="analytics-date-from-input")` | — | testid on DEV ✓ | unchanged; value semantics changed (see Adjustment) |
| 1 | To date/time input | `LocatorDescriptor(testid="analytics-date-to-input")` | — | testid on DEV ✓ | unchanged; value semantics changed (see Adjustment) |
| 1 | Tab — Overview | `LocatorDescriptor(testid="analytics-tab-overview")` | — | testid on DEV ✓ | unchanged |
| 1 | Tab — Costs | `LocatorDescriptor(testid="analytics-tab-costs")` | — | testid on DEV ✓ | unchanged |
| 1 | Tab — **Tokens** (new) | `LocatorDescriptor(testid="analytics-tab-tokens")` | — | testid on DEV ✓ | **new 2026-10-15**: `EL-6211` (#780, pre-dates this adjustment but post-dates the original automation) |
| 1 | Tab — Agents & Pipelines | `LocatorDescriptor(testid="analytics-tab-agents-pipelines")` | — | testid on DEV ✓ | unchanged |
| 1 | Tab — **Skills** (new, permission-gated) | `LocatorDescriptor(testid="analytics-tab-skills")` | — | testid on DEV ✓ | **new 2026-10-15**: `EL-6929` (#1218, 2026-10-12) — rendered only when `canViewSkills` (`checkPermission(PERMISSIONS.skills.list)`) is true; `${TEST_USER}` holds this permission, confirmed visible live |
| 1 | Tab — Tools | `LocatorDescriptor(testid="analytics-tab-tools")` | — | testid on DEV ✓ | unchanged |
| 1 | Tab — Users | `LocatorDescriptor(testid="analytics-tab-users")` | — | testid on DEV ✓ | unchanged |
| 1 | Tab — **Activity** (new) | `LocatorDescriptor(testid="analytics-tab-activity")` | — | testid on DEV ✓ | **new 2026-10-15**: `EL-5110` (#1034, pre-dates this adjustment but post-dates the original automation) |
| 1 | Tab — Health | `LocatorDescriptor(testid="analytics-tab-health")` | — | testid on DEV ✓ | unchanged |
| 1 | Tab — Guide | `LocatorDescriptor(testid="analytics-tab-guide")` | — | testid on DEV ✓ | unchanged |
| 1 | Loading spinner (Overview/Health data fetch) | `LocatorDescriptor(testid="analytics-loading-indicator")` | — | testid on DEV ✓ | unchanged |
| 1 | Overview tab KPI row | `LocatorDescriptor(testid="analytics-overview-kpi-row")` | — | testid on DEV ✓ | unchanged |

Uniqueness re-verified 2026-10-15 (`git fetch origin` fresh, `EliteaUI`):
`git grep -n "analytics-tab-tokens\|analytics-tab-skills\|analytics-tab-activity\|analytics-date-preset-0" origin/main -- src/`
→ exactly one declaration-site hit each in `AnalyticsContainer.jsx` (plus one unrelated test-file
assertion on `analytics-tab-skills` and one unrelated `run-analytics-tab-tokens` — a *different*
testid on a *different* component, `RunAnalyticsView.jsx` — not a collision).

## Network Behavior
- `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` — fires on mount with the default range (now a calendar-day span, not 1 rolling day); wait for this to resolve (200) before asserting the loading spinner is gone / KPI content is visible. Confirmed 200 OK live 2026-10-15, no console errors.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Original case-text drift (not a product defect — reverse-masking guard applies, unchanged from 2026-08): case claims 6 tabs (Overview, Agents, Tools, Users, Health, Guide), "Last 24d" default label, and a "Last 7d" default range. Filed: **elitea-testing-public#1185** (still open/unresolved on the TMS case text — this adjustment does not supersede it, it adds to it).
- **[CLARIFICATION] Second, independent drift (2026-10-15 adjustment, this session):** live product has moved further since the original automation (2026-08) — 10 tabs now (not 7: added Tokens/Skills/Activity), default preset label is "Today" (not "Last 24h"), and default date math is calendar-day (not rolling-24h). Root cause: deliberate, shipped product changes (`EL-6791` 2026-09-28 for the preset/date-math change; `EL-6211`, `EL-5110`, `EL-6929` for the three new tabs, 2026-08 through 2026-10-12) — **not a regression, Class A (UI drift) under `adjust-automated-test`**. See § Adjustment below. The TMS case text (steps 3-6, expected results) needs a second update to reflect this; tracked via the companion TMS PR this adjustment raises (lead-authored, since Expected-result changes = yes).

## Blocked Steps
None.

## Adjustment (2026-10-15, ELITEA-2310, triage Class A — UI drift)

**Triage:** Class A per `adjust-automated-test` Step 2 — the flow still works, the product moved
intentionally and the change already shipped to `main`/DEV. Confirmed via: (1) live DEV
Playwright exploration (headless script, MCP browser unavailable in this sandbox) showing the new
preset/tab labels and testids; (2) frontend source `git show origin/main:...AnalyticsContainer.jsx`
confirming the same `DEFAULT_PRESETS`/`ANALYTICS_TABS` arrays; (3) `git log -S "'Today'"` on that
file resolving to commit `425570d5` 2026-09-28, `feat: [EL-6791] Use calendar-day date presets in
Analytics (#1102)`; (4) `git log --oneline -- AnalyticsContainer.jsx` showing `EL-6211` (#780),
`EL-5110` (#1034), `EL-6929` (#1218) as the three tab-addition commits.

**What changed since the original automation (2026-08):**
1. Preset label + testid: "Last 24h" / `analytics-date-preset-1` → "Today" / `analytics-date-preset-0`. Preset count (4) and the remaining three labels/testids are unchanged.
2. Default date-math: `getPresetRange(days)` (added same commit, `analyticsCommon.helpers.js:15`) now computes `from: startOfDay(subDays(now, max(days-1,0)))`, `to: endOfDay(now)` — for the default `days=0` this is `from = today 00:00:00.000`, `to = today 23:59:59.999` (confirmed live: From input read `15/10/2026 00:00`, To `15/10/2026 23:59`, same calendar day) — a calendar-day span, NOT a rolling 24h-apart pair ending at "now" as the original test asserted.
3. Tab bar grew from 7 to 10: added "Tokens" (after Costs), "Skills" (after Agents & Pipelines, permission-gated on `canViewSkills`), "Activity" (after Users) — confirmed in that exact order live and in `ANALYTICS_TABS` source order. All other tab labels/testids/order unchanged.
4. Everything else probed in this adjustment (page title/badge testids, project badge, loading-indicator/KPI-row testids, the `analytics/prompt_lib` network wait) is **unchanged** — this is a scoped drift to presets + tabs + date-math, not a wholesale rewrite.

**Expected-result changes: YES** — this is the entire point of the adjustment. Three case-text
rows need a second update (on top of the still-open #1185 clarification): step 3's preset label
list, step 4's default-active-preset label, step 5's date-span semantics (calendar-day, not
rolling-24h/7d), and step 6's tab list/count (10, not 6 or 7). See the companion TMS PR this
adjustment raises (opened by the lead, not this implementer, since the lead's own memory on
Expected-result-change TMS PRs applies here).

**No step was deleted, no comparison was weakened.** Steps 3/4/5/6 still assert exact label,
exact order, exact pressed/selected state, and an exact (tolerance-bounded) date math — matching
the live contract at the same precision the original test asserted, per the preserve-the-nature
rail.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: `pages/analytics_page.py` (existing — extended by this adjustment, not replaced).
- Wait strategy: wait for the `analytics/prompt_lib/...` GET response (Playwright `wait_for_response` / project's response-wait helper), not a fixed timeout, before asserting spinner-gone + KPI content — mirrors the WebSocket-wait convention in `.agents/testing.md` (network condition wait, never `sleep`). Unchanged by this adjustment.
- Date-span assertion (step 5) — **rewritten by this adjustment**: the default preset is now "Today" (calendar-day), not "Last 24h" (rolling). Assert `from_dt` is at (or within a small render-time tolerance of) the start of the current calendar day (`00:00`) and `to_dt` is at (or within tolerance of) the end of the current calendar day (`23:59`) — e.g. compare each input's own `date()` component equals today's date, `from_dt.time()` ≈ `00:00` and `to_dt.time()` ≈ `23:59`, rather than asserting a 24h delta between the two. Do NOT just widen the old ±2min tolerance on a 24h-delta check — the premise (rolling window) itself is wrong now, not merely imprecise.
- Tabs/presets are **static** arrays (`DEFAULT_PRESETS`, now a 10-label `ANALYTICS_TABS` list, with "Skills" permission-gated via `canViewSkills`) — no dynamic data dependency for the other 9, safe to assert exact order/count against `${TEST_USER}`'s permission set.
