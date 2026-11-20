# Test Case: Remote MCP test result — Copy markdown / Copy text icons visible, clickable, confirmed by toast

## Metadata
- **TMS ID**: ELITEA-4759
- **Linked Story**: EliteaAI/elitea_issues#5838 (copy split); manual source ELITEA-4753
- **Priority**: l1 (source: critical)
- **Environment Explored**: DEV https://dev.elitea.ai/app (live, 2026-11-20), scratch pytest probe through `ToolkitDetailPage` / `ToolkitTestSettingsPage` + `toolkit_api`/`sync_mcp_tools_with_retry` (Playwright MCP browser unavailable in sandbox: no chrome). Probe deleted, not committed.
- **Status**: ready-for-automation
- **Siblings (not targets)**: ELITEA-4758 toolkit (`tests/ui/toolkits/test_toolkit_test_result_copy_icons.py`, merged on trunk/main), 4755 agent, 4756 pipeline, 4757 skill. 4758 covers the Artifact toolkit under `/toolkits/...`; the MCP surface is a different entry (`/mcps/all/{id}`) and different data (remote MCP tool). Not `already-covered` and not `extend-existing` (a separate spec with its own MCP fixture is simpler than param'ing 4758; implementer MAY parametrize if cheap — own call, keep case ids per-param per toolkit pattern).

## Preconditions
- Authenticated (`auth_state`).
- Fresh Remote MCP via existing fixture `mcp_toolkit_with_tools` (fixtures/data_fixtures.py:1723; DeepWiki `https://mcp.deepwiki.com/mcp`, 3 tools, auto-deleted). Yields `{"id","name","tools"}`.
- Case text's "connected MCP `test` / Epam Onehub Core, Current user id" is an example; DeepWiki fixture substitutes (declared substitution, same precedent as ELITEA-1933/1937). Tool: `read_wiki_structure` with `repoName=AsyncFuncAI/deepwiki-open` (2-3 s run, no model turn).

## Test Steps (all executed live)
1. `ToolkitDetailPage.navigate("/mcps/all/{id}")` (bare path, prefix auto-added; NOTE: `ToolkitDetailPage.navigate_to_toolkit` goes to `/toolkits/all/` — do not use) ; wait `toolkit-test-button` visible (testid on DEV, count 1). Page type label MCP.
   - **Case drift (clarification)**: case says banner "Connected!". Fixture MCP shows `toolkit-connection-status` = "Not Connected" (DeepWiki needs no OAuth; a `Login` button `toolkit-connection-login-button` renders) yet Test works and tools run. Do NOT assert Connected!. Assert only Test button visible.
2. `open_test_surface()` -> URL `/app/mcps/all/{id}/test`; `ToolkitTestSettingsPage.start_search` visible; 3 tool chips (`get_tool_chips()` count 3).
3. `get_tool_chip("Read wiki structure").click()` -> `tool_select` contains "Read wiki structure", `run_tool_button` count 1, `model_selector_name` count 1 (all visible).
4. `fill_param_field("repoName", "AsyncFuncAI/deepwiki-open")` (required; the param testid is on a wrapper div, plain `.fill` on `toolkit-test-param-repoName` FAILS, use the page-object method), `run_tool(timeout=15000)`; `wait_for_tool_result(timeout=90000)` text contains `read_wiki_structure` (observed "✅ read_wiki_structure (2.891s) Available pages for AsyncFuncAI/deepwiki-open").
5. `is_result_copy_icon_enabled("markdown")` and `("text")` both True (testids `chat-copy-markdown-button` / `chat-copy-text-button`, count 1 each).
6. `hover_result_copy_icon("markdown")` -> "Copy markdown".
7. `click_result_copy_icon("markdown")` -> toast "Markdown copied to clipboard."; wait `toast-message` gone (<=20s) before next.
8. `hover_result_copy_icon("text")` -> "Copy text".
9. `click_result_copy_icon("text")` -> toast "Text copied to clipboard.".

## Coverage Map
**Axis 1**
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 open MCP; Connected! banner; Test visible | page opens, Test visible | step 1 | test_button visible | asserted for Test; Connected! banner = case drift (fixture shows Not Connected), clarification, not asserted |
| 2 click Test | Test Toolkit page w/ tool list | step 2 | URL + start_search + chips | asserted |
| 3 select tool | Tool, Model, Run Test shown | step 3 | tool_select, run button, model name | asserted (tool = read_wiki_structure, substitutes Current user id) |
| 4 Run Test | result card with tool name + value | step 4 | result contains tool name | asserted |
| 5 icons visible | both visible | step 5 | enabled x2 | asserted |
| 6/8 hover | tooltips | steps 6, 8 | tooltip text | asserted |
| 7/9 click | toasts | steps 7, 9 | toast text | asserted |
| Pass: clickable | enabled | step 5 | enabled | asserted |
**Axis 2**: required-param fill (needed to run tool). Nothing else.

## Concrete Handles (verified live on DEV)
| Element | Rung | Handle | suggested_testid | Provenance |
|---|---|---|---|---|
| Test button | testid | `ToolkitDetailPage.test_button` (`toolkit-test-button`) | - | testid on DEV ✓ |
| Tool chip/select/param/run/result | existing | `ToolkitTestSettingsPage` `get_tool_chip`, `tool_select`, `fill_param_field`, `run_tool_button`, `run_tool`, `wait_for_tool_result` | - | existing, worked |
| Copy markdown / text | testid | `chat-copy-markdown-button`, `chat-copy-text-button`; page-object methods `is_result_copy_icon_enabled`/`hover_result_copy_icon`/`click_result_copy_icon` already on `ToolkitTestSettingsPage` (from 4758) | - | testid on DEV ✓ |
| Toast | testid | `toast-message` (`ToolkitTestSettingsPage.toast_message`) | - | testid on DEV ✓ |

No new page-object work expected; only a small MCP navigation step (bare-path `navigate("/mcps/all/{id}")` through `ToolkitDetailPage`, or `McpFormPage.navigate_to_detail(id, project_id)` which waits on the GET). Note `McpFormPage.navigate_to_detail` + `ToolkitDetailPage.open_test_surface` share testid `toolkit-test-button`.

## Side channels
Clipboard is client-side; toast is the observable. No page errors seen in probe.

## Known Defects
None.

## Blocked Steps
None.

## Automation Hints
- tms ELITEA-4759 + allure.issue `https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/mcp/ELITEA-4759_mcp-test-result-copy-markdown-and-copy-text-actions.md`; markers ui, mcp, p1, regression (confirm `mcp` marker exists in pytest.ini; else toolkits).
- Suggested file: `tests/ui/mcp/test_mcp_test_result_copy_icons.py` (or beside 4758). Run with `APP_PREFIX=/app`. Wait first toast gone before second click. `sync_mcp_tools_with_retry` inside the fixture can hit 503; fixture already retries.
