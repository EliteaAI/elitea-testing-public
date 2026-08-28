# Test Case (extension): User-detail "Daily Activity" tooltip shows per-series values and updates between points

## Metadata
- **TMS ID**: ELITEA-2329
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: qa-engineer, batch `settings-w06` (cluster ELITEA-2326/2327/2328/2329)
- **Status**: extend-existing
- **Covering spec (merged to `origin/automation/base`)**:
  `automation/tests/ui/admin/test_analytics_user_detail_view.py:235-253`
  (`TestAnalyticsUserDetailView::test_users_tab_row_click_opens_detail_view`, Step 8) — verified
  present on `origin/automation/base` with `git show origin/automation/base:<path>`, and unmodified
  by this batch's trunk (`git diff --stat origin/automation/base...tests/batch-settings-w06` touches
  only `pages/analytics_page.py`).
- **Case-text drift**: none. ELITEA-2329's text matches the live product exactly.

## Behavioural overlap — what the covering spec already proves

ELITEA-2313's merged spec drives the case's entire path and most of its observable. Its Step 8 already:
navigates Settings -> Analytics -> Users tab, clicks a user row (case step 1), takes the
`analytics-user-detail-chart-container` bounding box and drives a **real `page.mouse.move()`** to its
centre (case step 2 — honest input, not a synthetic dispatch), then asserts the
`analytics-user-detail-chart-tooltip` becomes visible, that its text contains **at least one** of
`LLM` / `Tool` / `Chat Msg` / `Agent`, and that its first line is a non-empty date label
(the "date and values" half of case step 3). It runs green today.

So ELITEA-2329 is **not** a fresh spec — writing one would re-derive the same navigation, the same
row-click, the same chart handle and the same hover. What it adds is a small number of assertions the
covering spec deliberately kept loose.

## Gap assertions — what the covering spec does NOT cover

Append these to Step 8 of `test_users_tab_row_click_opens_detail_view` (or split Step 8 into 8a/8b
inside the same test — the implementer's call; do not create a second spec that repeats the setup).

1. **Per-series completeness, not "at least one" (case step 3).**
   The current assertion is `any(series in tooltip_text for series in ("LLM","Tool","Chat Msg","Agent"))`
   — it passes on a tooltip that lost three of its four series. The case asks for "values for **each**
   event type series".
   - **Assert**: the tooltip's series lines are exactly, in order,
     `["LLM", "Tool", "Chat Msg", "Agent"]` (`AnalyticsUserDetailed.jsx:250-286`, `<Area name=...>`;
     this chart renders **no legend**, so the tooltip is the only place these names exist in the DOM).
   - **Assert**: the number of series lines equals the number of rendered `.recharts-area-area`
     paths inside the chart container (live: 4).

2. **The values are the right values (case step 3, the "values" half).**
   The covering spec asserts nothing about the numbers at all.
   - **Assert**: the tooltip's label line equals one of the `date` values in the captured
     `analytics_user_detail/prompt_lib/` response's `daily_activity` array; bind that entry as
     `point`.
   - **Assert**: each series line equals `f"{name}: {fmt_num(point[key])}"` for the mapping
     `LLM -> llm`, `Tool -> tool`, `Chat Msg -> chat`, `Agent -> agent`
     (`AnalyticsUserDetailed.jsx:250/260/270/280`).
   - This needs the user-detail response body captured on the row click.
     `AnalyticsPage.open_user_detail_by_row()` already waits on that response — extend it (or add a
     `*_capturing_*` sibling, matching the existing `navigate_capturing_analytics` /
     `select_date_preset_capturing_analytics` convention) to **return the parsed body**.

3. **The tooltip updates on a different data point (case step 4 / Expected Final State).**
   Not covered at all today — the covering spec hovers exactly once.
   - **Assert (precondition)**: `len(daily_activity) >= 2`, from the captured response.
   - Drive a second real `page.mouse.move()` to a clearly different fractional x of the chart
     container (live: 25% then 75% of the width landed on different days).
   - **Assert**: the tooltip is still visible, its label line **differs** from the first hover's, the
     new label is also a `date` present in `daily_activity`, and its series values again equal
     `fmt_num(...)` of that entry. (Asserting only "the text changed" would pass on garbage.)

4. **Axis 2 — the tooltip unmounts on mouse-out.** Not in ELITEA-2329's text, but one extra mouse
   move, live-verified here, and it catches a stuck-tooltip regression. ELITEA-2326 asserts the same
   thing for the Overview chart on the same shared `ChartTooltip`.
   - **Assert**: after moving the cursor off the container, `analytics-user-detail-chart-tooltip`
     reaches **count 0** (`ChartTooltip` returns `null` when `!active`, so the node unmounts rather
     than merely hiding). Live-confirmed: count 1 while hovering -> 0 after moving away.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | fixture | already covered |
| Step 1 — Analytics -> Users tab -> click a user row | page/section loads | covering spec Steps 1-3 | `test_analytics_user_detail_view.py` (title, KPI cards, detail response) | already covered |
| Step 2 — Hover a data point on the Daily Activity multi-series area chart | no error, expected UI state | covering spec Step 8 | real `page.mouse.move()` to the container centre; tooltip becomes visible | already covered |
| Step 3 — Tooltip shows the date and values for **each** event type series | condition holds | **gap 1 + gap 2** | exact series list == `["LLM","Tool","Chat Msg","Agent"]`; label == a response `date`; each value == `fmt_num(point[key])` | **partially covered** — today only "≥1 series present" + "first line non-empty"; the gap assertions close it |
| Step 4 / Expected Final State — Move to a different data point, tooltip updates | no error, expected UI state | **gap 3** | second real mouse move; label differs AND is a real response date AND values re-match | **not covered today** |

### Axis 2 — observables asserted beyond the case
| Observable | Why |
|---|---|
| Series-line count == rendered `.recharts-area-area` count | Ties the tooltip's contents to what the chart actually drew, so a dropped `<Area>` fails instead of silently shrinking the tooltip. |
| Tooltip unmounts on mouse-out (gap 4) | Same shared `ChartTooltip` mechanism as ELITEA-2326 asserts; one extra mouse move; catches a stuck tooltip. |
| No console errors | Already asserted by the covering spec; unchanged. |

## Concrete Handles (all pre-existing — no testid work for this case)

| Element | Handle (testid) | PROVENANCE |
|---|---|---|
| Users tab | `analytics-tab-users` | on `automation/testids` only |
| User row | `analytics-users-row` | on `automation/testids` only |
| User-detail title | `analytics-user-detail-title` | **on `main` ✓** |
| Daily Activity chart title | `analytics-user-detail-chart-title` | **on `main` ✓** |
| Daily Activity chart container | `analytics-user-detail-chart-container` | **on `main` ✓** |
| Daily Activity chart **tooltip** | `analytics-user-detail-chart-tooltip` | **on `main` ✓** |

_Verified 2026-08-28 with a fresh `cd ../EliteaUI && git fetch origin` plus the two-stage grep from
`.agents/workflow.md` § Closure record._ **This is the only case in the settings-w06 chart-tooltip
cluster that needs no new testid** — `AnalyticsUserDetailed.jsx:246` already passes
`testId="analytics-user-detail-chart-tooltip"` into the shared `ChartTooltip`.

Rendered-series count uses the page object's existing `RECHARTS_AREA_SERIES` constant
(`pages/analytics_page.py:194`) scoped inside the chart-container testid parent — the already-declared
`.agents/testing.md` § Locator policy #579 exception 1. No new exception is introduced. The area
`<path>` nodes mount one animation tick after the container appears — wait on `.first` attached,
never a sleep.

`fmt_num()` (the Python port of `AnalyticCommonHelpers.fmtNum`) currently lives in
`tests/ui/admin/test_analytics_overview_kpi_cards.py:62`; with ELITEA-2326 and the 2327/2328 family
spec it passes its third consumer, so per Hard Rule 7 extract it to `automation/utils/` and import it
here rather than copying it.

## Fidelity Declaration
**No substitutions.** Both hovers are real `page.mouse.move()` CDP input events, and every asserted
value comes from the live `analytics_user_detail/prompt_lib/` response captured off the wire. No
`page.route`, no `route.fulfill`, no `page.evaluate`-dispatched events, no injected state. (The
covering spec's Step 8 is already written this way; the extension keeps that discipline.)

## Network Behavior
`GET /api/v2/elitea_core/analytics_user_detail/prompt_lib/{project_id}?user_id={id}&date_from=...&date_to=...`
fires once per row click; 200 OK. **Hovering fires no request.** Never wait on `networkidle` (#1847).

## Blocked Steps
None. All four case steps were executed live end-to-end.

## Known Defects
None found for this case. Standing caveat from `_surface/detail-views.md`: a user with **no
`user_email`** renders a blank detail-view title (elitea-testing-public#1192) — pick a row with an
email. Live 2026-08-28 the first row of project "Private" was `testbot@elitea.ai`, which the covering
spec already relies on.

## Live Observations (2026-08-28, localhost:5173, project "Private", `Last 30d`)
- Users tab -> first row `testbot@elitea.ai` -> detail title `testbot@elitea.ai`.
- Chart title `Daily Activity`, subtitle `Events by type per day`, container `1212x220`,
  **4** `.recharts-area-area` paths, **no legend**.
- hover at 25% width -> tooltip testid count **1**, text
  `2026-08-05 / LLM: 11 / Tool: 5 / Chat Msg: 4 / Agent: 11`
- hover at 75% width -> `2026-08-22 / LLM: 0 / Tool: 0 / Chat Msg: 0 / Agent: 0`  (tooltip updated;
  note zeros are still rendered — the series lines do not disappear on a zero day)
- mouse moved off the container -> tooltip testid count **0** (node unmounted)
- Zero console errors across the whole walk.
- Minor harness note: immediately after clicking the Users tab, `analytics-users-row.count()` can
  return 0 while `.first` still resolves via auto-waiting — wait on the row locator before counting.
