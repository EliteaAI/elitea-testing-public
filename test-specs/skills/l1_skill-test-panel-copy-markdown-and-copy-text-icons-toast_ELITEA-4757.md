# Test Case: Skill test panel — Copy markdown / Copy text icons visible, clickable, confirmed by toast

## Metadata
- **TMS ID**: ELITEA-4757
- **Linked Story**: EliteaAI/elitea_issues#5838 (copy split); manual source ELITEA-4751
- **Priority**: l1 (source: critical)
- **Environment Explored**: DEV https://dev.elitea.ai/app (live, 2026-11-20), scratch pytest probe via `SkillsListPage`/`SkillFormPage`/`SkillDetailPage` + `skill_api` (APP_PREFIX=/app). Playwright MCP browser unavailable in sandbox (no chrome) — probe through the framework instead.
- **Status**: ready-for-automation
- **Siblings (not targets)**: ELITEA-4755 (agent, `tests/ui/agents/test_agent_test_chat_copy_icons.py`), ELITEA-4756 (pipeline, `tests/ui/pipelines/test_pipeline_test_chat_copy_icons.py`) — same observable, different page object/panel/steps; own spec. ELITEA-2442 (`test_skill_test_panel_response_actions.py`) is NOT coverage: it targets the removed `chat-copy-button` and the old toast.

## Preconditions
- Authenticated (`auth_state`). Fresh skill created through UI/API (instructions `reply echo`), deleted in `finally` via `skill_api.delete_skill`. Case's "potential-bug" is only an example; creating own avoids data dependency.

## Test Data
- Message `run` (any text).

## Test Steps
1. Create skill (`SkillsListPage.navigate_to_create` -> `SkillFormPage.fill_form(name, instructions="reply echo", description)` -> `save_and_wait_for_navigation`); `SkillDetailPage.verify_on_detail_page()`; `skill_test_button` visible+enabled. (Case says "open from Skills menu": direct post-create landing is acceptable transit; list->open covered elsewhere.)
2. `open_test_skill_panel()` -> `test_panel` visible; chat input visible.
3. `send_test_message("run")` + `wait_for_test_response(initial_count=0, timeout>=60000)`. Response shown (assert response message non-empty).
4. Both `chat-copy-markdown-button` and `chat-copy-text-button` (last / only one in `skill-test-panel`) visible and enabled, no hover needed.
5. Hover markdown icon -> `[role=tooltip]` last text `Copy markdown`.
6. Click -> `toast-message` text `Markdown copied to clipboard.` (`toast-alert` data-severity=info). Wait toast count 0 (<=20s) before step 8.
7. Hover text icon -> tooltip `Copy text`.
8. Click -> toast `Text copied to clipboard.`.

## Expected Results
As case; exact strings confirmed live, no case-text drift.

## Coverage Map
**Axis 1**
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 open skill, Test visible | detail page, Test button | step 1 | button visible/enabled | asserted (post-create landing as transit) |
| 2 click Test | panel + input | step 2 | panel, input visible | asserted |
| 3 send message | output shown | step 3 | response non-empty | asserted |
| 4 icons visible | both visible | step 4 | visible x2 | asserted |
| 5 hover M | tooltip Copy markdown | step 5 | tooltip text | asserted |
| 6 click M | toast Markdown copied to clipboard. | step 6 | toast text | asserted |
| 7 hover copy | tooltip Copy text | step 7 | tooltip text | asserted |
| 8 click copy | toast Text copied to clipboard. | step 8 | toast text | asserted |
| Pass: "clickable" | enabled | steps 4/6/8 | to_be_enabled | asserted |
| Precondition "Bugs & Features project / potential-bug" | - | Preconditions | - | out-of-scope: fresh skill in default project |
**Axis 2**: enabled-check grounded in "visible and clickable". Nothing else.

## Concrete Handles (verified live on DEV)
| Element | Rung | Handle | suggested_testid | Provenance |
|---|---|---|---|---|
| Test Skill button | testid | `SkillDetailPage.test_skill_button` (`skill-test-button`) | - | existing |
| Panel | testid | `SkillDetailPage.test_panel` (`skill-test-panel`) | - | existing |
| Send/input/open | - | `open_test_skill_panel()`, `send_test_message()`, `wait_for_test_response()` | - | existing methods |
| Copy markdown icon | testid | `chat-copy-markdown-button` | - | testid on DEV ✓ (count 1, also 1 inside `skill-test-panel`, visible, enabled) |
| Copy text icon | testid | `chat-copy-text-button` | - | testid on DEV ✓ (`SkillDetailPage.copy_text_button` already exists) |
| Toast | testid | `toast-message`, `toast-alert[data-severity=info]` | - | testid on DEV ✓ |
| Tooltip | role | `role=tooltip` (2 matched in DOM while hovering -> use `.last`, as AgentDetailPage.open_tooltips) | `chat-copy-tooltip` | ladder — last open one |

Gap: `SkillDetailPage` has `copy_text_button` but NO `chat_copy_markdown_button`, no `toast_alert`/`toast_message` (only `version_toast_message`; check it is `toast-message`), no open-tooltips descriptor. Implementer adds class-level declarations mirroring `AgentDetailPage` (agent_detail_page.py:199, 506, 514-520, 3091-3121); `chat_copy_text_button` may reuse/alias `copy_text_button`. `copy_action_button` (`chat-copy-button`) is dead on DEV — leave it. Scope via `.last` on declared locators (message collection, not sibling pick).

## Network / Side channels
Clipboard write is client-side; toast is the observable (do not read clipboard). No console errors seen.

## Known Defects
None. Case-text drift: none.

## Blocked Steps
None.

## Automation Hints
- Marker pair: tms ELITEA-4757 + allure.issue (case file under automated-full-regression-ui/skills/); markers p1, skills, regression.
- Viewport 1600x1400; dismiss banner if present.
- Wait first toast gone (count 0) before clicking the second icon.
- Cleanup skill in `finally`; skill name <=32 chars.
- Run with `APP_PREFIX=/app` if `.env.test` absent in sandbox. Transit (create skill + panel methods) worked; no regression signal.
