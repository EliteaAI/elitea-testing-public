# Test Case: Toolkit test result — Copy markdown / Copy text icons visible, clickable, confirmed by toast

## Metadata
- **TMS ID**: ELITEA-4758
- **Linked Story**: EliteaAI/elitea_issues#5838 (copy split); manual source ELITEA-4752
- **Priority**: l1 (source: critical)
- **Environment Explored**: DEV https://dev.elitea.ai/app (live, 2026-11-20), scratch pytest probe through `ToolkitDetailPage` / `ToolkitTestSettingsPage` + `toolkit_api` (Playwright MCP browser unavailable in sandbox: no chrome). Probe deleted, not committed.
- **Status**: ready-for-automation
- **Siblings (not targets)**: ELITEA-4755 agent (`tests/ui/agents/test_agent_test_chat_copy_icons.py`), 4756 pipeline, 4757 skill. Same observable, different page objects/steps -> own spec. Nothing existing covers the toolkit surface (grep "Copy markdown" over tests/pages: agent/skill only).

## Preconditions
- Authenticated (`auth_state`). Fresh Artifact toolkit created via `toolkit_api.create_artifact_toolkit(name, desc, bucket_name)` (all 16 tools selected, incl. `list_files`); deleted in `finally` via `toolkit_api.delete_toolkit(id)`. Case's "alita" toolkit / Bugs & Features project is an example; own data avoids dependency. Name short + uuid suffix.

## Test Steps
1. `ToolkitDetailPage.navigate_to_toolkit(id)` + `wait_for_config_surface()`; `test_button` visible (case: "open from Toolkits & Indexes list" - direct URL is transit; Run History button not asserted in probe, add visibility check only if a handle exists, else out-of-scope).
2. `open_test_surface()` -> URL `/toolkits/*/{id}/test`; `ToolkitTestSettingsPage.start_search` visible (Test Toolkit page, tool chips on left).
3. Select tool: `get_tool_chip("List files").click()` -> `tool_select` contains List files, `run_tool_button` visible (model selector `model_selector_name` visible).
4. `run_tool()`; `wait_for_tool_result(timeout=90000)` contains `list_files`. (Result is a model turn, ~up to 60s; sized as in ELITEA-1866.)
5. `chat-copy-markdown-button` and `chat-copy-text-button` each count 1 inside `chat-message-list`, visible, enabled, no hover needed.
6. Hover markdown icon -> `role=tooltip` text `Copy markdown`.
7. Click -> `toast-message` `Markdown copied to clipboard.` (`toast-alert` data-severity=info). Wait toast count 0 (<=20s).
8. Hover text icon -> tooltip `Copy text`.
9. Click -> toast `Text copied to clipboard.`.

## Coverage Map
**Axis 1**
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 open toolkit; Test + Run History visible | page opens | step 1 | test_button visible | asserted (Test); Run History: no handle verified -> out-of-scope unless implementer finds testid/role on DEV |
| 2 click Test | Test Toolkit page | step 2 | URL + start_search | asserted |
| 3 select List files | params, Model, Run Test | step 3 | chip, run_tool_button, model name | asserted |
| 4 Run Test | result card w/ list_files + JSON | step 4 | result text contains list_files | asserted |
| 5 icons visible | both visible | step 5 | visible x2 | asserted |
| 6 hover M | tooltip Copy markdown | step 6 | tooltip text | asserted |
| 7 click M | toast Markdown copied to clipboard. | step 7 | toast text | asserted |
| 8 hover copy | tooltip Copy text | step 8 | tooltip text | asserted |
| 9 click copy | toast Text copied to clipboard. | step 9 | toast text | asserted |
| Pass: "clickable" | enabled | steps 5/7/9 | to_be_enabled | asserted |
**Axis 2**: enabled check grounded in "visible and clickable". Nothing else.

## Concrete Handles (verified live on DEV)
| Element | Rung | Handle | suggested_testid | Provenance |
|---|---|---|---|---|
| Test button | testid/existing | `ToolkitDetailPage.test_button`, `open_test_surface()` | - | existing |
| Tool chip / run / result | existing | `ToolkitTestSettingsPage.get_tool_chip`, `run_tool_button`, `run_tool()`, `wait_for_tool_result()` | - | existing, transit worked |
| Copy markdown | testid | `chat-copy-markdown-button` (aria-label "Copy markdown", enabled, inside `chat-message-list`, count 1) | - | testid on DEV ✓ |
| Copy text | testid | `chat-copy-text-button` (aria-label "Copy text", count 1) | - | testid on DEV ✓ |
| Toast | testid | `toast-message`, `toast-alert[data-severity=info]` | - | testid on DEV ✓ |
| Tooltip | role | `role=tooltip` (single match while hovering; use `.last`) | `chat-copy-tooltip` | ladder |

Gap: `ToolkitTestSettingsPage` has none of these. Implementer declares class-level `chat_copy_markdown_button`, `chat_copy_text_button`, `toast_alert`, `toast_message`, `open_tooltips` mirroring `AgentDetailPage` (agent_detail_page.py:199, 502-525). Scope to `chat-message-list` via declared `result_message_list`/ScopedLocator, no positional picks.

## Network / Side channels
Clipboard write is client-side; toast is the observable (do not read clipboard). No console errors seen in probe.

## Known Defects
None. Case-text drift: none (Run History button not checked live).

## Blocked Steps
None.

## Automation Hints
- Marker pair: tms ELITEA-4758 + allure.issue (case file under automated-full-regression-ui/<toolkits dir>/, find real file name in TMS repo); markers p1, toolkits, regression.
- Wait first toast gone before clicking second icon.
- Run with `APP_PREFIX=/app`. Probe total ~25s.
