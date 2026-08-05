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
3. Verify the date filter bar shows exactly four preset toggle buttons, in order: "Last 24h", "Last 7d", "Last 30d", "Last 90d".
4. Verify the "Last 24h" preset button is the one shown pressed/active by default (`aria-pressed="true"`; the other three are `aria-pressed="false"` or absent).
5. Verify the From and To date/time inputs are present and, with the default "Last 24h" preset selected, are exactly 24 hours apart (From = now − 1 day, To = now).
6. Verify all seven Analytics tabs are visible, in order: "Overview", "Costs", "Agents & Pipelines", "Tools", "Users", "Health", "Guide".
7. Verify the "Overview" tab is selected by default (`aria-selected="true"`; MUI tab indicator under it).
8. Verify the page does not remain in a permanent loading state: the loading spinner (shown only while the Overview/Health-feeding analytics query is in flight) is not present/visible once the page has settled, and the Overview tab's content (KPI row) is rendered.

## Expected Results
- Page renders at `/settings/analytics` with header, date filter bar, and tab bar all visible.
- Default preset is "Last 24h" (`selectedDatePreset` initial state = `1`), not "Last 7d" — the From/To pickers reflect a 1-day span, not a 7-day span.
- Seven tabs are present (not six) — "Costs" and "Agents & Pipelines" are real, separate tabs the case text omits/mislabels. See § Known Defects (case-text clarification).
- "Overview" tab is selected/underlined by default.
- No permanent loading state: `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` resolves 200 and the Overview KPI content renders; no console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics | Target page/section loads successfully | step 1 | `step 1`: URL + no error | asserted |
| 2 Page header shows "Analytics" + project name badge | Condition holds | step 2 | `step 2`: title + badge text | asserted |
| 3 Date filter bar shows four preset buttons: Last 24h/7d/30d/90d | Condition holds | step 3 | `step 3`: 4 toggle buttons, exact labels/order | asserted |
| 4 "Last 24d" is active/highlighted by default | Condition holds | step 4 | `step 4`: "Last 24h" is the pressed preset | clarification *(case says "Last 24d" — typo for "Last 24h", the label step 3 itself lists; live default preset IS "Last 24h")* |
| 5 From/To pickers present, reflect the Last 7d range | Condition holds | step 5 | `step 5`: pickers present, reflect the actual default (Last 24h / 1-day span) | clarification *(case's "Last 7d" contradicts its own step 4 default and the live product — default range is 1 day, matching "Last 24h")* |
| 6 Six tabs visible: Overview, Agents, Tools, Users, Health, Guide | Condition holds | step 6 | `step 6`: all seven live tabs asserted (Overview, Costs, Agents & Pipelines, Tools, Users, Health, Guide) | clarification *(product has 7 tabs incl. "Costs" and "Agents & Pipelines" — case's 6-tab list is stale; reverse-masking guard: live product is correct)* |
| 7 Overview tab active/underlined by default | Condition holds | step 7 | `step 7`: `aria-selected` on Overview tab | asserted |
| 8 Page does not remain in permanent loading state | Condition holds | step 8 | `step 8`: spinner absent + KPI content rendered after wait | asserted |

Case-text drift filed as clarification issue **elitea-testing-public#1185** ("[Clarification][ELITEA-2310] Case text says six tabs/Last 24d/Last 7d default; live product has seven tabs, Last 24h default (1-day range)") — bundles rows 4, 5, 6 above (all three drifts trace to the same root cause: the case was authored against a stale spec). Live product is the correct source per the reverse-masking guard (`test-case-analysis` SKILL.md § Classify findings); this AFS asserts the **live** contract in steps 3–6, not the case's stale numbers.

**Axis 2 — Analyst additions.**
- `step 1` asserts no error on load (beyond the case's bare "loads successfully") — *added: cheap smoke check, catches a routing regression.*
- `step 8` asserts absence of the loading spinner AND presence of Overview KPI content (case only asks for "not a permanent loading state") — *added: a spinner disappearing without content appearing would itself be a silent-failure state (e.g. `isError` branch swallowed); both halves needed to prove the page actually settled into a working state, not just past the spinner.*
- `step 3`/`step 6` assert exact **order** of presets/tabs, not just presence — *added: order is part of the visible UI contract and is cheap to assert while the handle is already captured.*

## Cleanup
None — read-only page load, no data created or mutated.

## Concrete Handles (discovered during exploration)

**Provenance note:** `AnalyticsContainer.jsx` is currently **identical** on `EliteaAI/EliteaUI` `main` and `automation/testids` (same blob SHA `b143fe3f...`) — the whole Analytics surface is already on `main`. **Zero pre-existing testids** on the elements this case touches except the (unused-by-this-case) `analytics-export-button`. Every handle below needs adding via `add-data-testid`.

| Element | Recommended Locator | PROVENANCE | Notes |
|---|---|---|---|
| Page title "Analytics" | `LocatorDescriptor(testid="analytics-page-title")` | needs-adding | `AnalyticsContainer.jsx:195-198` — `<Typography variant="headingSmall">Analytics</Typography>`, static text |
| Project name badge | `LocatorDescriptor(testid="analytics-project-badge")` | needs-adding | `AnalyticsContainer.jsx:202-205` — `<Box sx={styles.projectLabel}>`, conditional on `projectName` truthy |
| Preset button — Last 24h | `LocatorDescriptor(testid="analytics-date-preset-1")` | needs-adding | `AnalyticsContainer.jsx:36` `DEFAULT_PRESETS` item `{label:'Last 24h', value:1}` → wire via `item.buttonProps={'data-testid': 'analytics-date-preset-1'}` (spread onto `ToggleButton` in `TabButtonItem.jsx`); state via native `aria-pressed` attribute, not a state-dependent testid |
| Preset button — Last 7d | `LocatorDescriptor(testid="analytics-date-preset-7")` | needs-adding | same pattern, `value:7` |
| Preset button — Last 30d | `LocatorDescriptor(testid="analytics-date-preset-30")` | needs-adding | same pattern, `value:30` |
| Preset button — Last 90d | `LocatorDescriptor(testid="analytics-date-preset-90")` | needs-adding | same pattern, `value:90` |
| From date/time input | `LocatorDescriptor(testid="analytics-date-from-input")` | needs-adding | `AnalyticsContainer.jsx:242` `<DateTimePicker>` (From) — wire via `slotProps.textField.inputProps={'data-testid': ...}` (currently shared `datePickerCommonProps` object; From/To need their own `slotProps` to carry distinct testids) |
| To date/time input | `LocatorDescriptor(testid="analytics-date-to-input")` | needs-adding | `AnalyticsContainer.jsx:254` `<DateTimePicker>` (To), same pattern |
| Tab — Overview | `LocatorDescriptor(testid="analytics-tab-overview")` | needs-adding | `AnalyticsContainer.jsx:274-284` — `<BaseTab>` spreads `...restProps` onto `MuiTab`, which forwards unknown DOM attrs; map the label list to a `{label, testid}` pair or a `{section}-{element}-{param}` template keyed by a slugified label |
| Tab — Costs | `LocatorDescriptor(testid="analytics-tab-costs")` | needs-adding | same |
| Tab — Agents & Pipelines | `LocatorDescriptor(testid="analytics-tab-agents-pipelines")` | needs-adding | same |
| Tab — Tools | `LocatorDescriptor(testid="analytics-tab-tools")` | needs-adding | same |
| Tab — Users | `LocatorDescriptor(testid="analytics-tab-users")` | needs-adding | same |
| Tab — Health | `LocatorDescriptor(testid="analytics-tab-health")` | needs-adding | same |
| Tab — Guide | `LocatorDescriptor(testid="analytics-tab-guide")` | needs-adding | same |
| Loading spinner (Overview/Health data fetch) | `LocatorDescriptor(testid="analytics-loading-indicator")` | needs-adding | `AnalyticsContainer.jsx:288-291` — `<Box sx={styles.loadingState}><CircularProgress size={32} /></Box>`, rendered only while `needsOverview && isFetching`; used for an absence assertion (`to_have_count(0)` / `not_to_be_visible()`) after the analytics request settles, per `.agents/testing.md` § Locator policy (absence assertions count as references) |
| Overview tab KPI row (step 8 — proof of rendered content, not just spinner-gone) | `LocatorDescriptor(testid="analytics-overview-kpi-row")` | needs-adding | **Implementer amendment (Phase 2, 2026-08-05):** `AnalyticsOverview.jsx:29-32` — `<Box sx={styles.kpiRow} data-tour={ANALYTICS_TOUR_TARGET_IDS.kpiCards}>`; not in the original Concrete Handles table — step 8's "KPI content is rendered" clause had no named handle. Added so the assertion is a real locator check, not implied by the spinner's absence alone. |

Uniqueness verified (2026-08-05, `git fetch origin` fresh):
`git grep -- "<testid>" origin/main -- src/` → **0 hits** for all 15 new testids above, plus `analytics-overview-kpi-row` (added during implementation, also 0 hits) — 16 new testids total; `analytics-export-button` (not used by this case) already exists on `main`.

## Network Behavior
- `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=...&date_to=...` — fires on mount with the default 1-day range; wait for this to resolve (200) before asserting the loading spinner is gone / KPI content is visible. Confirmed 200 OK in exploration, no console errors.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Case text drift (not a product defect — reverse-masking guard applies): case claims 6 tabs (Overview, Agents, Tools, Users, Health, Guide), "Last 24d" default, and a "Last 7d" default range; live product has 7 tabs (Overview, **Costs**, **Agents & Pipelines**, Tools, Users, Health, Guide), default preset is "Last 24h" (matching the case's own step 3 list), and the default range is 1 day (24h), not 7 days. Filed: **elitea-testing-public#1185**. This AFS's steps 3–6 assert the live contract; automation should NOT reproduce the case's stale numbers.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- No existing page object for Analytics — this is the first case in `settings-analytics`; create `pages/analytics_page.py` (new).
- Wait strategy: wait for the `analytics/prompt_lib/...` GET response (Playwright `wait_for_response` / project's response-wait helper), not a fixed timeout, before asserting spinner-gone + KPI content — mirrors the WebSocket-wait convention in `.agents/testing.md` (network condition wait, never `sleep`).
- Date-span assertion (step 5): compare `datetime.fromisoformat`-parsed From/To input values; assert `(To - From)` is close to `timedelta(hours=24)` (allow a small tolerance for render-time drift, e.g. ±2 minutes) rather than exact-equality, since the picker values are computed at component-mount time.
- Tabs/presets are **static** arrays (`DEFAULT_PRESETS`, the 7-label list) — no dynamic data dependency, safe to assert exact order/count.
