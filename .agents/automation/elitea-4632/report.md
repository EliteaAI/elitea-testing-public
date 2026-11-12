# Batch elitea-4632 report

**Totals:** blocked 1

| Case | Outcome | Note |
|---|---|---|
| ELITEA-4632 | blocked | gate red: playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. waiting for get_by_test_id("skill-information-section") to be visible — 'Step failed: Navigate to skill detail'. Pyte |

## Findings

### clarification
- Case text differs from the live product: breadcrumbs are Skills / skill / Run History / Analytics (no run id); the header shows date, version and model only; there is no Cost Breakdown section; Cost by Model has no tokens; the formula (prompt+completion) x rate is imprecise because input and output rates differ. The AFS asserts the live contract. (`test-specs/skills/l2_skill-run-analytics-costs-accuracy_ELITEA-4632.md`)
- The TMS case file name is ELITEA-4632_skill-run-analytics-cost-accuracy.md (cost, not costs). The @allure.issue link uses the real name and tms_backwrite check passes. (`ELITEA-4632`)

### note
- Costs and Tokens data appear about 10-40 s after a run (empty-state testids run-analytics-costs-empty / run-analytics-tokens-empty). Poll with run-analytics-refresh-button, budget about 120 s, no networkidle waits.
- KPI cards and the Cost by User / Cost by Model tables have no testid on DEV. The implementer needs a unique ladder handle under run-analytics-page; prefer asserting via the analytics_costs API payload plus one UI text check.
- The Playwright MCP Chrome was missing in the original analysis session; exploration used the repo's Python Playwright with storage state.
- automation/.env.test is missing in this tree (the symlink is dangling or absent). Without APP_PREFIX=/app the ELITEA-4631 spec also fails with a 404 page at skill-information-section. Gate agents must set APP_PREFIX=/app or restore the env file.
- The Run Analytics header first renders 'Version: … · Model: …' before data loads. The spec waits with web-first assertions. The first costs payload can be empty for about 10-40s, so wait_for_costs_data refreshes until total_tokens > 0.
- The unit's locator delta is not verified. The unit adds 2 xpath ScopedLocators (both hinted), 1 role rung (hinted), plus testid fields. Neither ruff nor a base-vs-branch locator_inventory delta was run. The lead should re-run the scan and lint on the trunk.
- Mechanical ladder grep over automation/pages and automation/tests, run via the diff against main: the only hits are the declared KPI_CARD_VALUE and TABLE_CELLS xpath fields. Both are class-level, carry description= and suggested_testid=, and no rung-1 to rung-4 selector fits them. These are compliant. The positional pick is `.all()[index]`, which the grep pattern cannot catch (see blocking[]). (`automation/pages/run_analytics_page.py:76`)
- Lint: the line-length check at 120 chars finds line 123 in the spec (the Step 10 allure.step title) and line 32 in run_analytics_page.py (122 chars, the run_history_rows description). Both would fail ruff E501. Wrap them. The import block in the spec also has no blank line between `from playwright...` and `from pages...`, so ruff I001 may fire. Run `ruff check`. (`automation/tests/ui/skills/test_skill_run_analytics_costs.py:123`)
- `tab_health` is declared but never used. Step 11 only switches to Tokens and back. The case step says Health or Tokens, so this is acceptable. Either delete the dead locator or add a Health round-trip. The Tokens tab content is never asserted either. The AFS marks it optional, so I did not block on it. (`automation/pages/run_analytics_page.py:50`)
- Triangulation of the 15 case steps against the AFS Coverage Map and the code. Rows 1-6 and 8-15 map to a real assertion at their own step. Row 7: the run id and status are absent from the live header, which is a documented clarification. The AFS has no row for the case's 'Cost reconciles with usage events' pass criterion. The spec reconciles against the analytics_costs API payload, which is a reas… [clipped; full text in the unit's receipt under .agents/automation/_returns/] (`test-specs/skills/l2_skill-run-analytics-costs-accuracy_ELITEA-4632.md`)
- Step 8 and Step 12 compare the UI total with `format_cost`, which is a Python copy of the UI formatting rule. This is fine because the rule is documented in the AFS. Note the risk: any change to the product's rounding turns the test red. No masking was found: there are no skips and no soft asserts. The only skip-like path is the poll timeout, which raises. (`automation/tests/ui/skills/test_skill_run_analytics_costs.py:130`)
- automation/.env.test is missing in this checkout (the symlink to ../../.env.test is absent). APP_PREFIX defaults to empty, so every DEV route 404s: ELITEA-4631's spec fails identically with it missing. I ran with APP_PREFIX=/app in the shell, which is only a stopgap, since .env.test normally overrides shell env. The gate agent needs the env file restored.
- .venv has no ruff, so lint could not be run on this branch. pytest.ini also passes --reruns flags, so run with --reruns=0 when debugging.
- After page.go_back() from the analytics page, no run-history row has data-selected=true, so the selected/unselected attribute cannot identify a row. Rows must be told apart by their rendered text.
- Prior blocker 1 (positional pick) is fixed. open_analytics_for_run now resolves the row with run_history_rows.filter(has_text=^row_text$), using the text captured earlier from get_run_history_row_texts(). The test asserts the two row texts differ, so the pick is unique. RUN_ROW_MENU_BUTTON is a class-level ScopedLocator on the testid rung, resolved with .within(row). The mechanical grep is clean f… [clipped; full text in the unit's receipt under .agents/automation/_returns/] (`automation/pages/skill_detail_page.py:1464`)
- Prior blocker 2 (sleep) is fixed. wait_for_costs_data has no wait_for_timeout and no sleep. Each iteration clicks refresh and blocks on page.expect_response for the analytics_costs call, then checks kpis.total_tokens > 0. On success it adds expect(costs_empty).to_have_count(0) and a visible TOTAL COST card. Failure raises TimeoutError at the 150s deadline. This is a condition wait. (`automation/pages/run_analytics_page.py:61`)
- Nit: the poll loop has no inter-poll delay. If the refresh button is not disabled while loading, it re-fetches back-to-back for up to 150s. If the gate shows DEV load or flakiness, add an expect-based condition on the empty placeholder between polls. Not blocking. (`automation/pages/run_analytics_page.py:68`)
- Nit: RUN_ROW_MENU_BUTTON duplicates the testid already declared as run_history_row_menu_button. It is a scoped variant, so it is legitimate, but a reader could consolidate the two. (`automation/pages/skill_detail_page.py:185`)
- Triangulation, case to AFS to diff, holds on all 15 steps. Case-text drift is recorded as clarifications and not asserted against: breadcrumb form, run header with no id or status, no Cost Breakdown section, and the rate formula. Case steps 1-2 are covered by Step 2 (two rows), 3-4 by Step 3, 5 by Step 4, 6 by Step 5 (breadcrumbs), 7 by Step 6, 8 by Step 7, 9 by Step 8 (TOTAL COST against the API)… [clipped; full text in the unit's receipt under .agents/automation/_returns/]
- The new ScopedLocator xpath declarations (KPI_CARD_VALUE, TABLE_CELLS) are non-positional and anchored on label text. They carry suggested_testid and a description saying why rungs 1-4 failed. There is no `locator=` or `fallback=`. This is acceptable ladder rung 5. (`automation/pages/run_analytics_page.py:41`)

## Gate

- Verdict: red (runs: 0, seconds: [85.81])
- Failure: `automation/tests/ui/skills/test_skill_run_analytics_costs.py::TestSkillRunAnalytics::test_skill_run_analytics_costs_accuracy` — playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. waiting for get_by_test_id("skill-information-section") to be visible — 'Step failed: Navigate to skill detail'. Pytest ran 1 failed, 2 reruns, 83s. (cases: ELITEA-4632)
