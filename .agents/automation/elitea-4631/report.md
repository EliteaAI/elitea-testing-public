# Batch elitea-4631

Base `main` · trunk `tests/batch-elitea-4631` · pr_unit `trunk`

**Totals:** blocked 1

| Case | Outcome | Note |
|---|---|---|
| ELITEA-4631 | blocked | gate red: playwright TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. waiting for get_by_test_id("skill-information-section") to be visible. Fails in Step 1 (Open the skill and run one prompt in the te |

AFS: `test-specs/skills/l2_skill-run-history-display-and-restore-chat_ELITEA-4631.md` · branch `tests/ELITEA-4631-skill-run-history` · PR 2930

## Findings

### clarification
- ELITEA-4631: Case text disagrees with the live Skill Run History page in four places (columns Date/Version/Duration only, no status icons, absolute dates, Run History via overflow menu or test-panel header). [clipped in source; full text in `.agents/automation/_returns/`]
- ELITEA-4631: Case text says Run History tab, status icons, Status/User columns. Live DEV shows an overflow-menu 'Run History' item opening /history with Date/Version/Duration only. The test asserts the live contract (per the AFS).
- ELITEA-4631: Case step 5 (status icons) and Status/User columns have no counterpart in the Skill history UI. The lead should make sure a case-text clarification issue is filed or linked. [clipped in source]

### note
- The AFS says the Playwright MCP chrome binary was missing during analysis; exploration used the repo's Python Playwright with storage state. Not rechecked.
- Sandbox has no automation/.env.test. Without APP_PREFIX=/app every navigation 404s and looks like a skill-information-section timeout. Pass APP_PREFIX=/app.
- Local pytest with `-p no:rerunfailures` fails to start because pytest.ini carries --reruns options. Use `--reruns 0`.
- Ladder grep on the full diff returned 2 hits, both `page.locator(self.RUN_HISTORY_SELECTED_ROW)` in skill_detail_page.py, compliant under rule (a). (`automation/pages/skill_detail_page.py`) [clipped in source]
- Declarations sound; rungs match the AFS; non-testid rungs carry `suggested_testid=`; TMS pair present. [clipped in source]
- Per-step assertions match the AFS (Steps 3-8). [clipped in source]
- Nit: Step 2 breadcrumb check uses `page_contains_text(skill_name)` with no wait; weak. (`automation/tests/ui/skills/test_skill_run_history_restore_chat.py:57`)
- Nit: Step 7 asserts message count == 2 right after waiting for the first message; may race. (`automation/tests/ui/skills/test_skill_run_history_restore_chat.py:84`)

## Gate

Verdict: **red** · runs: 0 · timings: 85s

- `automation/tests/ui/skills/test_skill_run_history_restore_chat.py::TestSkillRunHistory::test_skill_run_history_display_and_restore_chat` (ELITEA-4631): playwright TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. waiting for get_by_test_id("skill-information-section") to be visible. Fails in Step 1; identical on the initial attempt and both reruns (3/3 broken). Cleanup step passed.
