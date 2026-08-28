# Test Case: Date filter is retained when switching between tabs

## Metadata
- **TMS ID**: ELITEA-2319
- **Linked Story**: none
- **Priority**: l1 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: `${TEST_USER}` (dev-token auth state on localhost)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w06`
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (`auth_state` fixture); a project is selected.

## Test Data
### reuse-existing
- None — structural assertions only.

## Test Steps
1. Navigate to Settings → Analytics and click `Last 30d` (case step 1).
   - **Verify**: `Last 30d` is the only pressed preset; record the exact From/To input values.
2. Click each tab in sequence: **Agents & Pipelines, Tools, Users, Health, Guide, Overview**
   (case step 2 — the live tab label is "Agents & Pipelines"; the tab bar also contains Costs and
   Tokens, which this case's sequence does not include).
   - **Verify** after EACH click: the clicked tab is `aria-selected="true"`.
3. Verify `Last 30d` remains highlighted throughout all tab switches (case step 3): after each of
   the six clicks, `analytics-date-preset-30` has `aria-pressed="true"` and the other three
   predefined presets are `aria-pressed="false"`.
4. Verify From/To values stay consistent with the Last 30d range on every tab (case step 4): after
   each click, both picker inputs still read **exactly** the values recorded in step 1, and their
   span is 30 days (±2 min).

## Expected Results
- Tab switching changes only the tab body; the date-filter state (preset highlight + both picker
  values) is unchanged on all six tabs.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Analytics and click "Last 30d" | Page loads | step 1 | `step 1`: preset pressed + From/To recorded, 30-day span | asserted |
| 2 Click each tab in sequence: Agents, Tools, Users, Health, Guide, Overview | Control responds | step 2 | `step 2`: `aria-selected` asserted after each of the six clicks | asserted *(live label "Agents & Pipelines" used for the Agents tab)* |
| 3 "Last 30d" remains highlighted throughout | Condition holds | step 3 | `step 3`: exactly-one-pressed check after each click | asserted |
| 4 From/To stay consistent with the Last 30d range on every tab | Condition holds | step 4 | `step 4`: byte-exact input values vs the step-1 snapshot + 30-day span, after each click | asserted |

**Axis 2 — Analyst additions.**
- Asserting **byte-exact** From/To equality against the step-1 snapshot rather than "still a 30-day
  span" — *added: a re-derived range (e.g. a remount recomputing `now`) would still be a 30-day
  span but would be a real regression of "retained"; exact equality is the honest reading of the
  case's "stay consistent".*
- Asserting `aria-selected` on each clicked tab — *added: it is what makes "on every tab" mean the
  tab actually switched, using the handles ELITEA-2310 already established.*

## Cleanup
None — read-only.

## Concrete Handles (discovered during exploration)
All pre-existing and on `main`: `analytics-tab-{agents-pipelines,tools,users,health,guide,overview}`,
`analytics-date-preset-{1,7,30,90}`, `analytics-date-{from,to}-input`.

## Network Behavior
- Switching tabs fires each tab's own data GET with the SAME `date_from`/`date_to` (the filter
  state lives in `AnalyticsContainer`, above the tab bodies). Health/Overview reuse the cached
  Overview query; Guide fires nothing.

## Known Defects Found During Exploration
- None — live-verified 2026-08-28 across all six tabs: From `29/07/2026 18:27` / To
  `28/08/2026 18:27` and `Last 30d` pressed on every one of them.

## Blocked Steps
None.

## Automation Hints
- The tab bar now has EIGHT tabs (Overview, Costs, **Tokens**, Agents & Pipelines, Tools, Users,
  Health, Guide) — `Tokens` was added after ELITEA-2310 was written. This case only walks the six
  the case names, but the page object's `get_tabs_in_order()` and the merged ELITEA-2310 spec still
  assume seven; see the Run Report finding.
