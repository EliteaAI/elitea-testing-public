# Test Case: From date cannot be set later than To date

## Metadata
- **TMS ID**: ELITEA-2316
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w06`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.

## Test Data
### reuse-existing
- None — the To value is set relative to today at run time (5 days ago, per the case).

## Test Steps
1. Navigate to Settings → Analytics.
   - **Verify**: page loads and settles.
2. Set the **To** date to 5 days ago (case step 2) via the To calendar icon → day cell → Apply.
   - **Verify**: the To input displays that date and the analytics GET re-fired with a matching
     `date_to`.
3. Attempt to set the **From** date to a date AFTER the current To (case step 3): open the From
   picker and target the day cell for `To + 1 day`.
   - **Verify (the prevention mechanism)**: that day cell is rendered **disabled**
     (`maxDateTime={dateTo}`, `AnalyticsContainer.jsx`), and so is every later day in the month;
     the popper's "Next month" control is disabled as well.
   - **Attempt anyway**: force-click the disabled cell (Playwright `force=True`, bypassing
     actionability so a real click event is dispatched at the element).
4. Verify the picker prevented the selection and no data changed to the incorrect timespan
   (case step 4):
   - the From input still displays its previous value (unchanged);
   - From < To still holds;
   - **no** new analytics GET fired after the force-click (a 1.5 s negative window);
   - the Overview KPI row still renders the values from the last legitimate response.

## Expected Results
- The From picker constrains selection to `<= To`: later days are disabled and un-clickable.
- The From value, the query parameters, and the rendered content are unaffected by the attempt.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Analytics | Page loads | step 1 | `step 1` | asserted |
| 2 Set "To" to 5 days ago | Completes without error | step 2 | `step 2`: input value + refetch with matching `date_to` — the concrete date used is "day 20 of a month ~3 months back" instead of literally 5 days ago (§ Automation Hints), preserving the step's purpose (To moved into the past) without a date-dependent calendar-boundary branch | asserted *(technique substitution, declared)* |
| 3 Attempt to set "From" later than "To" | Completes without error | step 3 | `step 3`: target day disabled (+ later days + Next month), then force-click dispatched | asserted |
| 4 Picker prevents the selection and no data changed to the incorrect timespan | Condition holds | step 4 | `step 4`: From unchanged, From < To, no new request in a negative window, KPI row still rendered | asserted |

**Axis 2 — Analyst additions.**
- Asserting the **negative network window** (no analytics GET in 1.5 s after the attempt) — *added:
  "no data changed to the incorrect timespan" is only really proven if the app never asked for the
  incorrect timespan; the DOM value alone could mask a fired-then-reverted request.*
- Asserting the popper's "Next month" control is disabled — *added: free with the same scoped
  handle, and it proves the constraint is a range bound rather than a single-cell quirk.*

## Cleanup
None — read-only.

## Concrete Handles (discovered during exploration)
Same set as ELITEA-2315 (`analytics-date-{from,to}-open-button`, `analytics-date-{from,to}-popper`,
`analytics-date-{from,to}-input`, plus the #579-scoped day-cell / Apply / month-nav raw handles
inside the popper testid). All added on EliteaAI/EliteaUI@22ff73c0 (`automation/testids`).

## Network Behavior
- Live-observed with To = 23/08 and From = 10/08 (2026-08-28): the From calendar rendered
  `24,25,26,27,28,29,30,31` disabled and "Next month" disabled — the exact `maxDateTime` bound.
- The symmetric constraint holds on the To picker (`minDateTime={dateFrom}` — with From = 10/08 the
  To calendar rendered `1..9` disabled and "Previous month" disabled). Not asserted by this case
  (out of its scope), recorded in the surface digest.

## Known Defects Found During Exploration
- None — the product behaves exactly as the case expects.

## Blocked Steps
None.

## Automation Hints
- **Deterministic, calendar-boundary-free choice of dates (no untested branch).** The test starts
  from `Last 90d`, so the From picker opens on a month **M** roughly three months in the past whose
  every day is selectable. It then:
  1. picks **day 10** in M → From = M-10;
  2. opens the To picker (which opens on the current month) and clicks its "Previous month" control
     until the header reads M (bounded loop, ≤ 4 iterations, count derived by comparing the popper's
     own month header), then picks **day 20** → To = M-20 — i.e. a To earlier than "now", which is
     the case's step-2 intent ("set To into the past");
  3. re-opens the From picker, which now opens on M, and targets **day 21** — always present in
     every month, always after To, therefore always the constrained cell.
  This replaces the case's literal "5 days ago", which lands in the previous month whenever today's
  day-of-month is ≤ 5 and would make the test's own path date-dependent. The case's assertion —
  From cannot be set later than To — is unchanged.
- Force-clicking a disabled MUI button dispatches a DOM click that React never routes to a handler
  — that IS the honest "attempt"; the assertion that matters is the unchanged state afterwards.
