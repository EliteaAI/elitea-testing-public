# Test Case: Skill Run Analytics - navigation from Run History and Costs accuracy

## Metadata
- **TMS ID**: ELITEA-4632
- **Priority**: l2 (TMS: critical regression)
- **Environment Explored**: DEV `https://dev.elitea.ai/app`, project Private (575), `autotest_user_admin`
- **Analyst**: qa-engineer (Sage), batch elitea-4632
- **Status**: ready-for-automation
- **Dedup / reuse**: no merged spec covers Run Analytics (`grep -ri analytics` hits only settings-analytics page, a different surface). Reuses ELITEA-4631 run-history spec/page-object (`automation/tests/ui/skills/test_skill_run_history_restore_chat.py`, on origin/main) for transit only. Same SkillDetailPage; separate observable, so not extend-existing (different page, different asserts).
- **Tooling note**: Playwright MCP chrome missing; explored with repo Python Playwright + storage state (headless).

## Case-text drift (CLARIFICATIONS - product is correct, assert live contract)
1. Breadcrumbs: case says `Skills > [Skill] > Run [ID] > Analytics`; live: `Skills / <skill name> / Run History / Analytics` (3 `breadcrumb-item` + `breadcrumb-current`="Analytics"). No run id in breadcrumb.
2. Run header (`run-analytics-run-info`): live text `Run: DD Mon YYYY, hh:mm AM/PM · Version: base · Model: <display name>`. No run id, no status.
3. Cost sections: live = 5 KPI cards (TOTAL COST, INPUT/OUTPUT TOKEN COST, CACHE READ/WRITE COST), "Cost by User" table, "Cost by Model" table, "Cost by Paid Tool". No "Cost Breakdown" section; token usage is NOT in Cost by Model (it is on the Tokens tab).
4. Formula `(prompt+completion tokens) x rate` is imprecise: cost = input_tokens x input_rate + output_tokens x output_rate (rates differ). Verified on DEV (Haiku 5.5): input $0.10/M, output $0.50/M (79 in/18 out -> 7.9e-6 + 9e-6 = 1.69e-5 OK; 51/128 -> 5.1e-6 + 6.4e-5 = 6.91e-5 OK). Do NOT hard-code rates in the test: assert internal consistency instead (below).
5. Costs are not instantly available: right after the run the page shows `run-analytics-costs-empty` ("No analytics data is available for this run."); data appears after the usage pipeline ingests (~10-40 s). `run-analytics-refresh-button` re-fetches. Tokens tab same (`run-analytics-tokens-empty`). Health tab already had data (llm, 2 events) earlier.
6. Preconditions (existing skill with history) -> test creates skill via API + runs prompts itself.

## Test Data (generate-per-test)
- `skill_api.create_skill(name=f"autotest-4632-{ts}"[:32], description=..., instructions="Convert the user text to UPPERCASE and reply with only that.")`; delete in finally.
- Run A: send `hello one` in test panel. Run B: click `chat-clear-button` (starts a new conversation; if "Switch" confirmation dialog `role=button name=Switch` is shown because a response is still streaming, click it - wait for response complete first to avoid), then send a clearly longer message (token counts differ). History then has 2 rows (row 0 = newest).

## Test Steps
1. Create skill; open detail (`SkillDetailPage.navigate`), dismiss platform banner, open test panel, run A, then clear chat and run B (wait_for_test_response each).
2. Open Run History: `skill-run-history-button` (test-panel header) or overflow menu -> `open_run_history()`. NOTE: if leaving the detail page while a response streams, a "Switch" warning dialog appears (observed) - ensure response finished (`wait_for_test_response`) plus a short settle; handle dialog button "Switch" via role if present.
3. Wait for 2 `run-history-list-item`. Hover row 0, click its `run-history-menu-menu-button`, click `role=menuitem name="Analytics"`.
4. Verify URL matches `/skills/all/{id}/history/analytics?run=\d+&history_run_id=\d+`; `run-analytics-page` visible.
5. Breadcrumbs: `breadcrumb-item` texts [Skills, <skill name>, Run History]; `breadcrumb-current` = "Analytics". Clicking the "Run History" crumb is optional (not executed).
6. `run-analytics-run-info` text contains `Run:`, `Version: base`, `Model:` (after data load: non-empty model name; before load shows `Model: -`).
7. Click `run-analytics-tab-costs` (default active). Poll: click `run-analytics-refresh-button` until `run-analytics-costs-empty` is gone (condition wait, timeout ~120 s, no sleeps beyond polling interval).
8. Verify TOTAL COST card shows `$` amount > 0; capture the `analytics_costs` response (`GET /api/v2/usage/analytics_costs/prompt_lib/575?run_id=<uuid>&root_entity_type=skill&root_entity_id={id}&root_entity_project_id=575`) with `page.expect_response`.
9. Reconcile with API payload (JSON `kpis`, `by_model[]`, `by_user`?): `kpis.total_cost == input_cost + output_cost + cache_read_cost + cache_creation_cost` (abs tol 1e-9); `kpis.total_tokens == total_input_tokens + total_output_tokens (+cache)`; `sum(by_model[].total_cost) == kpis.total_cost`; `sum(by_model[].total_tokens) == kpis.total_tokens`; per model `total_cost == input_cost+output_cost+cache costs`. Cost by Model table row for the model shows its `display_name` and SHARE 100.0% (single-model run); Cost by User table has the test user email, SHARE 100.0%.
10. UI vs API: TOTAL COST card text equals the formatted `kpis.total_cost` (live format: 5 decimals e.g. `$0.00007`, values below 1e-5 render `< $0.00001`; derive expected via same rule or compare to 5-dp rounding, not equality of raw float).
11. Tab switch: click `run-analytics-tab-tokens` then `run-analytics-tab-costs`; URL query unchanged (same run/history_run_id); Costs total card unchanged vs step 8. (Tokens/Health content is optional; Health showed a table "Health by Event Type" with llm rows.)
12. Isolation: go back to Run History (browser back), open Analytics for row 1 (the other run), wait for data, capture its `analytics_costs`; assert its `run_id` differs, its kpis (total_tokens and total_cost) differ from run A's, and the UI total equals ITS payload, not run A's. Observed: run B tokens 179 vs 97, cost 6.91e-5 vs 1.69e-5.

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `skill-run-history-button`, `skill-controls-menu-button`, `skill-run-history-menu-item`, `run-history-list-item`, `run-history-menu-menu-button` | - | testid on DEV ✓ (existing in SkillDetailPage, ELITEA-4631) |
| role | `menuitem` name "Analytics" (inside open row menu) | `run-history-analytics-menuitem` | ladder - no testid on DEV; unique within menu (same pattern as Restore chat) |
| testid | `run-analytics-page`, `run-analytics-run-info`, `run-analytics-refresh-button`, `run-analytics-export-button`, `run-analytics-costs-info-button`, `run-analytics-tab-costs`, `run-analytics-tab-tokens`, `run-analytics-tab-health`, `run-analytics-costs-empty`, `run-analytics-tokens-empty`, `analytics-costs-tool-spend` | - | testid on DEV ✓ |
| testid | `breadcrumbs`, `breadcrumb-item` (x3, scope in `breadcrumbs`), `breadcrumb-current` | - | testid on DEV ✓ |
| ladder | KPI cards (TOTAL COST etc.), "Cost by User" / "Cost by Model" tables | `run-analytics-costs-total-card`, `run-analytics-costs-by-model-table`, `run-analytics-costs-by-user-table` | NO testid on DEV (cards are MuiBox with a labelSmall span, tables render cells without testids). Implementer must pick a unique rung under `run-analytics-page` (e.g. text "TOTAL COST" scope via xpath description / role=table name?) - verify; if only xpath works declare with description. Prefer asserting totals via the API payload + one UI text check. No positional picks. |
| testid | `chat-clear-button`, `chat-message-input`, `chat-send-button`, `skill-test-button` | - | testid on DEV ✓ |
| role | button "Switch" in unsaved-response warning dialog | `skill-switch-run-confirm-button` | ladder - no testid; appears only when leaving mid-stream |

Need new page object: `RunAnalyticsPage` (or methods on SkillDetailPage) with class-level locators above.

## Coverage Map (Axis 1)
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1-2 Run History + completed run row | list shows runs | Steps 2-3 | covered (created by test) |
| 3-4 3-dot menu -> Analytics | navigates | Step 3-4 | covered |
| 5 page loads for run | analytics page | Step 4 | covered |
| 6 breadcrumbs | path | Step 5 | covered with live crumbs (clarification 1) |
| 7 run header metadata | id/timestamp/status/version | Step 6 | covered partially: timestamp, version, model; run id & status not shown (clarification 2) |
| 8 Costs tab | active | Step 7 | covered |
| 9 Total Cost card | $ amount | Steps 8,10 | covered |
| 10 Cost breakdown by model | per model cost | Step 9 | covered via Cost by Model table (clarification 3) |
| 11 Cost by User | attributed to user | Step 9 | covered (user email, 100%) |
| 12 Cost by Model tokens | cost+tokens | Step 9 | covered for cost; tokens come from API payload / Tokens tab (clarification 3) |
| 13 manual formula | matches | Step 9 | covered as rate-agnostic internal reconciliation (clarification 4) |
| 14 tab switch keeps context | no mixing | Step 11 | covered (Tokens; Health optional) |
| 15 different run no leakage | own data | Step 12 | covered |
Axis 2 extras: data-ingestion lag handling (Step 7) - grounded: empty state observed for ~30 s after run; API payload capture - grounded: ground truth for numbers.

## Known Defects
None. Network: analytics_run_detail and analytics_costs 200. Observation (not a defect, not filed): URL query after opening the second row showed `run=1971&history_run_id=1970` (`run` is the selected-in-history pointer, `history_run_id` the analytics subject) - assert on data, not on `run`.
Also observed: the "Costs are estimated..." note and the costs-info popover (`run-analytics-costs-info-button`).

## Blocked Steps
None. Risk: ingestion lag makes the spec slow (budget 120 s poll); `networkidle` waits are risky on this page. A second concern: Haiku model availability on DEV default model (model name asserted only as non-empty).

## Adjustment (card #2941, 2026-11-12) - Expected-result change: cost display format
- **Cause:** DEV product `fmtCost` (EliteaUI `analyticsCommon.helpers.js`) now renders costs in tiers; the 0.0001 <= |v| < 0.01 tier rounds UP to 4 decimals (0.000512 -> `$0.0006`). The page-object mirror `RunAnalyticsPage.format_cost` still used the old "< $0.00001 else 5 decimals" rule.
- **Change:** `format_cost` ported faithfully (None/NaN -> `-`; 0 -> `$0.00`; <1e-5 -> `< $0.00001`; <1e-4 -> 5 dp; <0.01 -> ceil to 4 dp; <1 -> 4 dp; <1000 -> 2 dp; K / M suffixes; sign prefix).
- **Nature preserved:** the test still asserts exact UI text equals the formatted API value (KPI total, Cost by Model cell, tab-switch context); no assertion weakened. Only the expected-format rule moved to match the product.
