# Test Case: Skill Run History page display and Restore chat from history

## Metadata
- **TMS ID**: ELITEA-4631
- **Priority**: l2 (TMS: critical regression)
- **Environment Explored**: DEV `https://dev.elitea.ai/app`, project Private (575), `autotest_user_admin`
- **Analyst**: qa-engineer (Sage), analyst slot, batch elitea-4631
- **Status**: ready-for-automation
- **Dedup / reuse**: no skill spec covers run history. Agent/pipeline history specs (ELITEA-1877, 2011) share the
  `run-history-*` list component but are different pages/entities - reuse handles only, not coverage.
- **Tooling note**: Playwright MCP chrome binary missing; explored with repo Python Playwright + storage state.

## Case-text drift (CLARIFICATIONS - product is correct, assert live contract)
1. Case: "Run History tab / Usage section" - live: overflow menu item "Run History" (or test-panel header button) -> `/history` route.
2. Case: columns "Status icon, Date/Time, Version, User, Actions" - live: **Date, Version, Duration** + hover 3-dot menu. No status icon, no user column.
3. Case steps 5 (green/red/orange icons) - **not present in Skill history UI**; error/stopped runs not representable. Out-of-scope for automation; recorded below.
4. Case step 6 "relative time" - live absolute `DD-MM-YYYY, hh:mm AM/PM`.
5. Case step 11 "new chat opens OR restored" - live: navigates to skill detail `?run={id}` with the test panel restored (test-panel runs; chat-sourced runs open /chat/{id} per source).
6. Preconditions (existing skill with history) -> test creates its own skill + 2 runs.

## Test Data (generate-per-test)
- `skill_api.create_skill(name=f"autotest-4631-{ts}", description=..., instructions="Convert the user text to UPPERCASE and reply with only that.")` (name <=32, lowercase/digits/hyphen). Delete in finally via `skill_api.delete_skill`.
- Send `hello one` in the test panel (fresh skill: one panel session == one conversation == one history row).

## Test Steps
1. Create skill via API; open `/skills/all/{id}` (`SkillDetailPage.navigate`), dismiss platform banner; `open_test_skill_panel()`; send "hello one", `wait_for_test_response()` (response `HELLO ONE`, ~3s).
2. Open Run History: overflow menu (`skill-controls-menu-button`) -> `skill-run-history-menu-item`.
   - Verify URL ends `/skills/all/{id}/history`; breadcrumb shows skill name.
3. Verify table: `run-history-header` text contains Date, Version, Duration; exactly 1 `run-history-list-item`.
4. Verify row: text matches `^\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)` , version cell `base`, duration matches `\d+(\.\d+)? s`.
5. Verify row `data-selected="true"` and right panel `chat-message-item` contains `hello one` and `HELLO ONE`.
6. Hover row, click `run-history-menu-menu-button`; verify menuitems (role) include "Restore chat" (also Share link, Delete, Analytics).
7. Click "Restore chat" -> URL matches `/skills/all/{id}\?run=\d+`; test panel shows prior messages (`hello one` / `HELLO ONE`).
8. Send "hello two" in restored panel; `wait_for_test_response`; verify new response `HELLO TWO` appended AFTER the historical messages (count grows 2 -> 4).

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `skill-controls-menu-button` | - | testid on DEV ✓ (SkillDetailPage.controls_menu_button) |
| testid | `skill-run-history-menu-item` | - | testid on DEV ✓ (new to page object) |
| testid | `skill-run-history-button` | - | testid on DEV ✓ (test-panel header; alternative entry) |
| testid | `run-history-header` | - | testid on DEV ✓ |
| testid | `run-history-list-item` + `data-selected` | - | testid on DEV ✓ (exists as constant in agent/pipeline pages) |
| testid | `run-history-menu-menu-button` (hover-revealed, scope within selected row) | - | testid on DEV ✓ |
| role | `menuitem` name "Restore chat" | `run-history-restore-chat-menuitem` | ladder - no testid on DEV; role+name unique inside the open menu |
| testid | `skill-test-button`, `chat-message-input`, `chat-send-button`, `skill-test-last-response`, `chat-message-item` | - | testid on DEV ✓ (existing SkillDetailPage methods) |
| testid | `platform-banner-close` | - | testid on DEV ✓ (dismiss corner banner if present; it intercepts clicks) |

Reuse: `SkillDetailPage.open_test_skill_panel/send_test_message/wait_for_test_response`, `skill_api` fixture; add `open_run_history()` and history helpers to SkillDetailPage (class-level locators). Wait for list item after navigation; no sleeps.

## Coverage Map (Axis 1)
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1-3 navigate to skill history | Run History page | Steps 1-2 | covered (entry via overflow menu) |
| 4 columns | table columns | Step 3 | covered with live columns Date/Version/Duration; Status/User **clarification** |
| 5 status icons | green/red/orange | - | out-of-scope: no status icons exist in Skill history UI (clarification) |
| 6 date format | readable | Step 4 | covered (absolute format) |
| 7 version | badge | Step 4 | covered |
| 8-9 3-dot menu, Restore Chat | menu | Step 6 | covered |
| 10-12 restore + context | prior messages | Step 7 | covered |
| 13-14 send & respond | continues | Step 8 | covered |
Axis 2 extras: run-detail panel shows selected run's messages (Step 5) - grounded: first row is auto-selected and is the run's transcript.

## Known Defects
None. Console/network: all conversation GETs 200.

## Blocked Steps
None.
