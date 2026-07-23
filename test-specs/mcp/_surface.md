# Surface digest: Remote MCP Detail Page (`/mcps/all/{id}`)

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface (written during ELITEA-1937 analysis,
2026-07-23/24, project `Private`/399, local `http://localhost:5173`).

## Fast fixture setup — API, not UI creation

`automation/pages/mcp_form_page.py` already covers the full **UI** creation +
Load-Tools flow (ELITEA-1933). For any case whose precondition is just "a
Remote MCP with discovered tools is available" (not "create one via the
UI"), the faster and equally-valid path is API-level:

```python
api = ToolkitAPI(browser_cookies=[])  # ELITEA_API_TOKEN Bearer auth works, no cookies needed
tools = api.sync_mcp_tools("https://mcp.deepwiki.com/mcp")   # real handshake, no credential needed
created = api.create_remote_mcp_toolkit(name=..., description=..., url=..., tools=tools)
# created["id"] -> McpFormPage(page).navigate_to_detail(created["id"], project_id)
```

Confirmed live: the resulting toolkit renders in the Form view with the Tools
section pills already populated/selected (`ask_question`, `read_wiki_contents`,
`read_wiki_structure` for the deepwiki fixture) and the Test Settings "Tool"
dropdown lists all 3 immediately — **no "Load Tools" click needed**, the
`available_mcp_tools`/`selected_tools` settings created via the API already
populate the client-side render (same mechanism ELITEA-1954's pipeline-MCP-node
memory documented). `ToolkitAPI.delete_toolkit(id)` cleans it up afterward
(confirmed 204).

**deepwiki fixture recap** (public, auth-free, stable — same one ELITEA-1933
uses): `https://mcp.deepwiki.com/mcp`, 3 tools:
- `read_wiki_structure(repoName: string)` — **plain text input** for `repoName`, simplest for a deterministic RUN TOOL test.
- `read_wiki_contents(repoName: string)` — same shape, single plain-text param.
- `ask_question(repoName: string|string[] anyOf, question: string)` — `question` is
  a plain textbox, but `repoName`'s `anyOf` schema renders as a **CodeMirror
  array editor** (bracket `[`/`]` UI), not a plain input — more fragile to
  automate. **Prefer `read_wiki_structure`/`read_wiki_contents` over
  `ask_question`** for any case that just needs ONE working RUN TOOL
  round-trip; reserve `ask_question` for a case that specifically wants to
  exercise the array-editor param renderer.

## Test Settings panel + RUN TOOL — same shared component as the Artifact-toolkit page

`/mcps/all/{id}` renders the **identical** `TestToolSettings.jsx`/
`ChatMessageList.jsx` pair as `/toolkits/all/{id}` (confirmed via testid
provenance grep, both `main` and `automation/testids` — see table below). This
means `automation/pages/toolkit_test_settings_page.py` (written for
ELITEA-1866, Artifact toolkits) is the **pattern to port**, not duplicate
from scratch, onto `McpFormPage` — same testids, same replace-in-place
message-list behavior, same RUN TOOL disabled-until-valid gating.

| Purpose | Testid | main | automation/testids | Notes |
|---|---|---|---|---|
| Model selector button/current-name | `model-selector-button` / `model-selector-name` | ✅ | ✅ | Shared `LLMModelSelector.jsx` widget — assert non-empty text only, never an exact model name (project-configured default, confirmed `Anthropic Claude 4.5 Sonnet` this session, case-text's "e.g. GPT-5.4-mini" is just an example) |
| Tool dropdown (native MUI id, no testid on the id itself — options ARE testid'd) | native `#simple-select-Tool` (click target) | — | — | Same gap ELITEA-1933/1954 already flagged; not re-flagged. Existing `McpFormPage.test_tool_select` `LocatorDescriptor(testid="toolkit-test-tool-select")` resolves the SAME element by testid (confirmed: the wrapping element carries `toolkit-test-tool-select`, `#simple-select-Tool` is the native MUI id on the same node) — use the LocatorDescriptor, not the CSS id, in real page-object code. |
| Tool dropdown option (dynamic) | `select-option-{tool_name}` | ✅ | ✅ | Shared `SingleSelectMenuItem.jsx` — same family used by the type-picker and pipeline MCP node. |
| Tool-run parameter field (dynamic, by schema key) | `toolkit-test-param-{fieldKey}` | — | ✅ | Text-type fields: testid is on a WRAPPER, the real `<input>` is nested — locate via `.locator('input[type="text"]')` off the testid'd wrapper (or give the input itself a dedicated method, don't chain a raw selector in a spec). |
| RUN TOOL button | `toolkit-test-run-tool-button` | — | ✅ | Disabled until all required schema fields are filled — confirmed live (single required field → enables the instant it has a non-empty value, no debounce). |
| "Load Tools" button | `toolkit-load-tools-button` | — | ✅ | Still renders even when `available_mcp_tools` was populated via the API (not the UI Load-Tools click) — cosmetic-only in that case, doesn't need clicking. |
| Result/welcome message list | `chat-message-list` | ✅ | ✅ | Same component as every chat surface in the app. **Content REPLACES in place, never appends** — confirmed twice this session (2 separate fixtures): message count is 1 before AND after RUN TOOL. Use `RESULT_MESSAGE_ITEM = '[data-testid="chat-message-list"] li.MuiListItem-root'` (scoped sub-selector, matches `toolkit_test_settings_page.py`'s existing constant) and poll for the ✅/❌ prefix, never a message-count delta. |

## RUN TOOL network/execution mechanics (new finding, not documented by ELITEA-1866/1933)

Clicking RUN TOOL does **not** hit a dedicated single "run this tool" REST
endpoint. Confirmed live via full network capture: it silently creates a
**hidden/ephemeral conversation** (`POST
.../elitea_core/conversations/prompt_lib/{project}` → `201`) and adds a
participant (`POST .../elitea_core/participants/prompt_lib/{project}/{id}` →
`200`), then the actual tool execution + response streams over the SAME
WebSocket channel the regular chat page uses (not captured as discrete HTTP
requests by the browser network log). **Wait on the message-list content**
(the ✅/❌ prefix, per `wait_for_tool_result()`'s pattern below), never on a
specific REST response — there is no synchronous "tool run" response to
`expect_response()` against.

```python
# Confirmed working end-to-end, read_wiki_structure, repoName="facebook/react":
# chat message renders: "✅ read_wiki_structure (2.880s)" + "Available pages for facebook/react:" + a real nested wiki TOC.
# Zero console errors either fixture session (1 pre-existing, unrelated MUI
# "Tooltip on a disabled button child" warning — see .agents/memory/test-automation-engineer/mui_form_field_quirks.md,
# a widespread pre-existing pattern, not specific to this feature; non-blocking).
```

## Page-object gap (as of this analysis)

`automation/pages/mcp_form_page.py` has the Tool-select/schema-field-visible
half already (`test_tool_select`, `select_test_tool()`,
`is_test_param_field_visible()` — added ELITEA-1933) but is **missing** the
model-selector, RUN TOOL, and result-message methods that
`toolkit_test_settings_page.py` already has for the Artifact-toolkit
surface. Porting those 5 items (2 locators + `fill_test_param()`,
`run_tool()`, `get_welcome_message_text()`, `wait_for_tool_result()`) onto
`McpFormPage` is the implementer's job for ELITEA-1937 — **zero new
`add-data-testid` work required**, every testid above already exists on
`automation/testids` (some already on `main`).
