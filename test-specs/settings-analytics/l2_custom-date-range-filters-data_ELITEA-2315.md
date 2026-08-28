# Test Case: Custom From/To date range filters data

## Metadata
- **TMS ID**: ELITEA-2315
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w06`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture).
- A project is selected (any) — the case asserts that the pickers drive the query, not specific
  data values.

## Test Data
### reuse-existing
- No seeded data. The custom range is computed **relative to today** at run time (From = the 10th
  of the currently displayed month or, when today is before the 12th, a day ≥ 10 days back — see
  § Automation Hints for the exact rule), so the test never hardcodes a calendar date.

## Test Steps
1. Navigate to Settings → Analytics.
   - **Verify**: page loads and settles.
2. Click the **From** calendar icon (`analytics-date-from-open-button`) and select a past day in
   the open calendar (case step 2).
   - **Verify**: the picker popper (`analytics-date-from-popper`) opens; after the day click the
     From input displays the selected day (same `dd/MM/yyyy HH:mm` format, time part unchanged).
3. Click **Apply** in the popper (case step 3 — the case says "Ok"; the live button label is
   **"Apply"**, `localeText.okButtonLabel`).
   - **Verify**: the popper closes.
4. Click the **To** calendar icon (`analytics-date-to-open-button`) and select a day AFTER the
   From value (case step 4).
   - **Verify**: popper opens; the To input displays the selected day after the click.
5. Click **Apply** (case step 5).
   - **Verify**: the popper closes.
6. Verify the From and To fields display the selected values (case step 6) — both inputs parse to
   the exact days chosen in steps 2 and 4, and From < To.
7. Verify the charts and tables update to reflect the custom range (case step 7):
   - the analytics GET re-fired with `date_from`/`date_to` equal to the two selected values;
   - the Overview content re-rendered against **that response**: the 8 KPI values, the leaderboard
     row count and the Model Usage Breakdown row count all match the captured response body
     (`kpis`, `top_ai_users`, `models`), and the Daily Activity chart's rendered X-axis ticks are a
     subset of the response's `daily_activity` dates;
   - the `Custom` preset chip (`analytics-date-preset-custom`) is now rendered and pressed, and all
     four predefined presets are `aria-pressed="false"`.

## Expected Results
- Both pickers accept a custom value through the calendar UI and display it.
- The custom range drives the query: the request parameters equal the displayed values.
- Rendered Overview content is consistent with the response returned for that custom range.
- The date-filter control switches to the `Custom` state (5th chip appears, pressed).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics | Page loads | step 1 | `step 1` | asserted |
| 2 Click "From" calendar icon, select a past date/time | Control responds | step 2 | `step 2`: popper open + input shows the chosen day | asserted |
| 3 Click "Ok" to confirm | Control responds | step 3 | `step 3`: popper closes on **Apply** | clarification *(live label is "Apply", not "Ok" — `localeText.okButtonLabel: 'Apply'`, `AnalyticsContainer.jsx`)* |
| 4 Click "To" calendar icon, select a date after From | Control responds | step 4 | `step 4`: popper open + input shows the chosen day | asserted |
| 5 Click "Ok" to confirm | Control responds | step 5 | `step 5`: popper closes on **Apply** | clarification *(same label drift)* |
| 6 From and To fields display the selected values | Condition holds | step 6 | `step 6`: both parsed values equal the selections, From < To | asserted |
| 7 Charts and tables update to reflect the custom range | Condition holds | step 7 | `step 7`: request params == displayed values; KPI values / leaderboard rows / model rows / chart ticks all matched against the CAPTURED response body | asserted |

**Axis 2 — Analyst additions.**
- Asserting the `Custom` chip appears and is pressed — *added: it is the visible state change the
  product makes when a picker is edited (`selectedDatePreset = 'custom'`), free to assert with the
  new `analytics-date-preset-custom` testid, and it catches a regression where a custom edit
  silently leaves a predefined preset highlighted.*
- Asserting rendered content **against the captured response** rather than "values changed" —
  *added deliberately per `.agents/testing.md` § Fidelity policy: the response is the oracle, so
  the assertion is deterministic without fabricating anything and without depending on the project
  having activity in the chosen window (live-observed: a 7-day window in project 471 returns all
  zeros and no Model Usage table at all — a "values must differ" assertion would be flaky-by-data).*

## Cleanup
None — read-only; no data mutated.

## Concrete Handles (discovered during exploration)

| Element | Locator | PROVENANCE | Notes |
|---|---|---|---|
| From/To inputs | `analytics-date-from-input` / `analytics-date-to-input` | on-main ✓ (ELITEA-2310) | |
| From/To calendar icon buttons | `analytics-date-from-open-button` / `analytics-date-to-open-button` | **added this case** — EliteaAI/EliteaUI@22ff73c0 on `automation/testids` | `DateTimePicker slotProps.openPickerButton` |
| Picker popper roots | `analytics-date-from-popper` / `analytics-date-to-popper` | **added this case** — EliteaAI/EliteaUI@22ff73c0 | `slotProps.popper` `data-testid`; scoping parent for the MUI-internal day cells + Apply button |
| Calendar day cell | scoped raw handle **inside** the popper testid: `popper.locator('button.MuiPickersDay-root')` filtered by exact text | n/a — MUI internal (`PickersDay`) | `.agents/testing.md` § Locator policy **#579 exception 1** (third-party widget subtree). A testid cannot be placed without overriding MUI's `day` slot, which is a functional change (zero-functional-impact rule). Declared in the page-object method docstring. |
| Apply button | scoped raw handle inside the popper testid, by exact text `Apply` | n/a — MUI internal (`PickersActionBar`) | same #579 exception; `slotProps.actionBar` reaches only the container, never the individual buttons |
| `Custom` preset chip | `analytics-date-preset-custom` | **added this case** — EliteaAI/EliteaUI@22ff73c0 | rendered only while `selectedDatePreset === 'custom'` |
| Overview content | `analytics-overview-kpi-value`, `analytics-overview-leaderboard(-row)`, `analytics-overview-model-usage-table(-row)`, `analytics-overview-daily-chart-container` | **added this case** — EliteaAI/EliteaUI@22ff73c0 | shared with ELITEA-2317 |

## Network Behavior
- Selecting a day fires the analytics GET **immediately** (`onChange` → state → RTK-Query), i.e.
  BEFORE Apply is clicked; Apply only closes the popper and fires no request. Live-confirmed
  2026-08-28 (`browser_network_requests`: the `date_from=2026-08-10…` request appears at day-click
  time, and no further request follows the Apply click).
- Therefore the test waits for the response around the **day click**, not around Apply.

## Known Defects Found During Exploration
- None (the "Ok" vs "Apply" label is case-text drift, recorded above, not a product defect).

## Blocked Steps
None.

## Automation Hints
- Time part is preserved when only the day is picked, so the assertion compares the **date** part
  and keeps the time from the pre-existing value.
- **Deterministic day choice with no month navigation.** The test first clicks `Last 90d`, which
  sets From ≈ 90 days back. The From popper therefore opens on a month roughly three months in the
  past, where every day is before `maxDateTime` (= To = now) and hence selectable: pick **day 15**
  of that displayed month. The To popper opens on the *current* month (To is still ≈ now) and the
  To picker has only a `minDateTime` (no max), so **day 10 of the current month** is always
  selectable and always after the chosen From. Both days exist in every month, so no
  "Previous month" navigation and no calendar-boundary branch is ever needed.
- The month/year actually displayed is read back from the popper's own header (scoped raw handle,
  same #579 exception) so the expected From value is derived from what the product showed, not from
  a date the test computed independently.
- Binding rule (supersedes the "10th of the month" wording in § Test Data): From = day 15 of the
  month the From popper opens on after `Last 90d`; To = day 10 of the month the To popper opens on
  (the current month).
