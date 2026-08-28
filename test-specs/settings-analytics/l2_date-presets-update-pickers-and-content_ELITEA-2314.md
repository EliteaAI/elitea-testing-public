# Test Case: Predefined date presets update the From/To pickers and refresh all content

## Metadata
- **TMS ID**: ELITEA-2314
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`).
  All Analytics testids this case uses are already on `main` (bulk promotion
  EliteaAI/EliteaUI@bf4a13ad); no new testid is needed for this case.
- **User set**: `${TEST_USER}` (dev-token auth state on localhost — no manual login)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w06`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture — localhost skips login via `VITE_DEV_TOKEN`).
- A project is selected (any). The case asserts date-range mechanics, not specific data values,
  so it holds for a project with or without analytics activity.

## Test Data
### reuse-existing
- None. Read-only: the test only clicks preset toggles and reads the From/To picker inputs.

## Test Steps
1. Navigate to Settings → Analytics (`AnalyticsPage.navigate()`).
   - **Verify**: URL contains `/settings/analytics`, page settles out of its loading state.
2. Verify the default preset state.
   - **Verify**: `Last 24h` is the only preset with `aria-pressed="true"`, and the From/To picker
     inputs (`dd/MM/yyyy HH:mm`) are **1 day** apart (±2 min render tolerance).
   - **Case-text drift**: the case says "Last 7d is active by default and From/To reflect a 7-day
     range". Live default is **Last 24h / 1 day** (`AnalyticsContainer.jsx:76`,
     `useState(1)`), already filed for this feature family as elitea-testing-public#1185.
     Reverse-masking guard: this AFS asserts the live contract and covers the 7-day range by
     clicking `Last 7d` explicitly in step 3.
3. Click `Last 7d`.
   - **Verify**: the analytics GET re-fires with a `date_from` ~7 days before `date_to`; `Last 7d`
     becomes the only pressed preset; From/To are 7 days apart.
4. Click `Last 24h`.
   - **Verify**: same three things for a 1-day span (this is the case's own step 3).
5. Click `Last 30d`.
   - **Verify**: same three things for a 30-day span (case step 4).
6. Click `Last 90d`.
   - **Verify**: same three things for a 90-day span (case step 5).
7. Across every preset click in steps 3–6, verify exactly one preset is highlighted at a time
   (case step 6): the clicked preset has `aria-pressed="true"` and the other three have
   `aria-pressed="false"`.
8. **Verify the Overview content actually re-rendered for each preset** (implementer amendment,
   fix round 3). The case's "data refreshes" was originally dispositioned as the refetch alone,
   which a response that never reaches the DOM satisfies — while this AFS's own § Expected
   Results already promised "the Overview KPI row re-renders after the fetch settles". After
   every preset click in steps 3–6 the Overview content is matched against **that preset's own
   captured response**: all 8 KPI cards (each formatted through the product's own `fmtNum` /
   `fmtCost`), the Top 5 AI Adopters leaderboard (row count, conditional container, and the top
   row's email + score), the Model Usage Breakdown (row count + its null-for-empty branch), and
   the Daily Activity chart's rendered X axis (ticks ⊆ the response's `daily_activity` dates,
   last tick == the last date, span within the thinning slack). Strengthening only — no
   assertion was removed or weakened.

## Expected Results
- Each preset click updates BOTH picker inputs so that `to - from` equals the preset's day count
  (±2 min), with `to` ≈ now.
- Each preset click refreshes content: a new
  `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=…&date_to=…` fires, its
  `date_from` matches the newly displayed From value (to the minute), and the Overview KPI row
  re-renders after the fetch settles.
- Preset highlighting is mutually exclusive at all times (exactly one `aria-pressed="true"`).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics | Page loads | step 1 | `step 1`: URL + settled load state | asserted |
| 2 "Last 7d" active by default, From/To reflect a 7-day range | Condition holds | step 2 + step 3 | `step 2`: live default (Last 24h / 1 day) asserted; `step 3`: the 7-day range asserted after an explicit `Last 7d` click | clarification *(case text stale — live default is Last 24h; family issue elitea-testing-public#1185)* |
| 3 Click "Last 24h" — highlights, From/To 24h, data refreshes | Control responds | step 4 + step 8 | `step 4`: aria-pressed + 1-day span + refetch with matching date_from; `step 8`: Overview content matched against that response | asserted |
| 4 Click "Last 30d" — From/To 30 days, data refreshes | Control responds | step 5 + step 8 | `step 5`: same three assertions, 30-day span; `step 8`: Overview content matched against that response | asserted |
| 5 Click "Last 90d" — From/To 90 days, data refreshes | Control responds | step 6 + step 8 | `step 6`: same three assertions, 90-day span; `step 8`: Overview content matched against that response | asserted |
| 6 Only one preset highlighted at a time | Condition holds | step 7 | asserted after EVERY preset click in steps 3–6 (exactly-one-pressed check) | asserted |

**Axis 2 — Analyst additions.**
- Asserting that the refetch's `date_from` query parameter **matches the displayed From value**
  (not merely that "a request fired") — *added: this is what makes "data refreshes" a real check
  rather than a coincidence; the request is captured live via `expect_response`, so the oracle is
  the system's own request, never a fabricated payload.*
- Asserting the Overview KPI row is present again after each refetch — *added: proves the content
  re-rendered, not just that a network call happened; the spinner branch unmounts the KPI row
  while `isFetching`, so this catches a stuck-loading regression.*

## Cleanup
None — read-only. The last click leaves the page on `Last 90d`; the `page` fixture is per-test,
so no state leaks.

## Concrete Handles (discovered during exploration)

All pre-existing (ELITEA-2310), all on `main`:

| Element | Locator | PROVENANCE | Notes |
|---|---|---|---|
| Preset toggles | `AnalyticsPage.preset_last_24h/7d/30d/90d` (`analytics-date-preset-{1,7,30,90}`) | on-main ✓ | state read via native `aria-pressed`, never a state-switched testid |
| From input | `AnalyticsPage.date_from_input` (`analytics-date-from-input`) | on-main ✓ | `input_value()` → `dd/MM/yyyy HH:mm` |
| To input | `AnalyticsPage.date_to_input` (`analytics-date-to-input`) | on-main ✓ | same format |
| Overview KPI row | `AnalyticsPage.overview_kpi_row` (`analytics-overview-kpi-row`) | on-main ✓ | presence-after-refetch check |

## Network Behavior
- `GET /api/v2/elitea_core/analytics/prompt_lib/{project_id}?date_from=<ISO>&date_to=<ISO>` fires on
  mount and again on **every** preset click. Live-observed 200 OK for all four presets
  (2026-08-28, project 471).
- `date_from`/`date_to` are ISO-8601 UTC; the picker displays **local** time, so the comparison
  must convert (the page object exposes the parsed picker values and the captured request params).

## Known Defects Found During Exploration
- None. The only divergence is the stale case text covered by elitea-testing-public#1185
  (default preset / default range), already filed for this case family.

## Blocked Steps
None.

## Automation Hints
- Clicking the ALREADY-active preset is a no-op by design (`handleDatePresetChange` returns early
  when MUI's exclusive `ToggleButtonGroup` emits `null`), so the test must not start by clicking
  `Last 24h` — it clicks `Last 7d` first, which is also how the case's step-2 "7-day range" claim
  gets honest coverage.
- ±2 min tolerance on span comparisons: `from`/`to` are constructed from two separate `new Date()`
  calls and the picker only displays minutes.
