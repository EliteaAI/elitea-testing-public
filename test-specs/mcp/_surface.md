# Surface digest: Remote MCP Detail Page (`/mcps/all/{id}`)

Confirmed handles/waits/quirks from live exploration. This is a cache for
same-surface analysts and the implementer — it does NOT replace live
execution; verify handles as you use them, and update this file (create or
edit) after your own run. Lives on the base branch — commit alongside your
AFS, never on a case branch.

First digest for this surface (written during ELITEA-1937 analysis,
2026-07-23/24, project `Private`/399, local `http://localhost:5173`).
Extended during ELITEA-1934 analysis (2026-07-24, same environment) with the
create-form + Tools-section + toast + connection-status findings below —
those sections cover `/mcps/create`/`/mcps/create/mcp` in addition to the
`/mcps/all/{id}` detail page this digest started with; kept as one file since
`McpFormPage` covers both routes with the same class.

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

---

## Create-form flow (`/mcps/create` → `/mcps/create/mcp`) — ELITEA-1934 addition

`McpFormPage` covers create AND detail with the same class (shared
`ToolBaseProperty.jsx` schema-driven field renderer, per ELITEA-1922). Core
create-form handles, all existing/on-main, no gap:

| Purpose | Testid |
|---|---|
| Remote MCP type-selector card | `toolkit-type-card-mcp` |
| Toolkit Name input | `toolkit-form-name-input` |
| Url input | `toolkit-field-url-input` |
| Save button (create form) | `toolkit-form-save-button` |

- **Toolkit Name truncates silently at 32 chars** (`MAX_NAME_LENGTH`,
  `EliteaUI/src/common/constants.js`) — generated names must stay under this
  (e.g. `f"autotest_x_{uuid4().hex[:8]}"`, not a full 32-char uuid suffix).
- **Save button enable rule is dirty-based, not completeness-based** — flips
  enabled the instant ANY field is touched (ELITEA-1921 finding,
  CLARIFICATION #633). Only assert the pristine (disabled) and
  both-required-filled (enabled) states.
- Save never validates URL reachability — an unreachable/invalid URL still
  saves successfully (`201`) and round-trips unchanged onto the detail page;
  validation only happens at Load-Tools/sync time, not save time (confirmed
  live, ELITEA-1934).
- `VITE_DEV_TOKEN` auto-auth works even on a **brand-new, never-before-used
  Chrome profile** — not tied to any pre-existing cookie/localStorage state.

## Tools section (Configuration accordion, "TOOLS" sub-heading) — added ELITEA-1933

| Purpose | Testid |
|---|---|
| Tools empty-state message | `toolkit-tools-empty-state` — exact text `No tools to display for now. To get tools from MCP press button "Load Tools"` (curly quotes live) |
| "Load Tools" button | `toolkit-load-tools-button` — label flips to `"Loading..."` in flight, reverts to `"Load Tools"` once the sync response resolves, confirmed on BOTH the success path and the failure path (ELITEA-1934) |
| Discovered tool pill (dynamic) | `toolkit-tool-chip-{tool_name}` (`McpFormPage.TOOL_CHIP`), state via `data-selected` attribute |

`click_load_tools(project_id)` waits on the real `POST
.../mcp_sync_tools/prompt_lib/{project}?await_response=true` response and
returns its parsed JSON body — **reusable as-is for BOTH the success path
(ELITEA-1933: `result.tools` populated) and the failure path (ELITEA-1934:
`result.success === false`, `result.error` set)**. HTTP status is **always
`200`** in both cases — failure is communicated inside the body, never via a
4xx/5xx. Don't write a second click/wait method for a "failure" variant;
assert on the returned dict differently instead.

**Failure fixture** (new, ELITEA-1934): `https://nonexistent.invalid/mcp` —
the `.invalid` TLD is IANA-reserved for exactly this purpose, so DNS-
resolution failure is deterministic (no network mocking needed, confirmed
2/2 identical across two independent attempts). Exact server response:
`{"result": {"success": false, "error": "Failed to sync MCP tools: DNS
resolution failed. Please check the server hostname in the URL.",
"server_url": "<url>"}}`.

## Error/success toast — `[data-testid="toast-message"]` (existing, SHARED)

`EliteaUI/src/components/Toast.jsx:66` — a generic `Box` inside the MUI
`Alert`, already used by `artifacts_page.py`, `skills_list_page.py`, and
`skill_detail_page.py` (each declares its OWN named `LocatorDescriptor`
field pointing at this same testid string — follow that per-page-object-
field convention). **Not previously noted for this surface** — the
ELITEA-1933 AFS only warned "don't assert on the success toast, it
auto-dismisses" but never looked for a stable handle; it exists.
Auto-hide durations (`TOAST_DURATION_DEFAULTS`,
`EliteaUI/src/common/constants.js`): `success`/`info` 3000ms, `warning`
7000ms, `error` **10000ms** — error toasts give a much wider assertion
window, no realistic race risk asserting right after the triggering network
call resolves.

## Connection status widget — GAP, needs `add-data-testid`

`EliteaUI/src/[fsd]/features/mcp/ui/McpAuthStatus.jsx` (lines 128–152) — the
globe-icon + "Not Connected"/"Connected!" text + Login/Logout button strip
near the Form/Raw Json toggle. **Zero testids anywhere in this widget**
(confirmed via a 6-level DOM ancestor walk, ELITEA-1934). Ordinary
feature-scoped app component (structurally similar siblings exist
independently in `openapi`/`sharepoint` feature folders as separate files,
not the same shared React instance, so a feature-scoped testid here is
fine). Recommended shape (not yet added by any case as of 2026-07-24):

| Purpose | Recommended testid |
|---|---|
| Status container (text + icon) | `toolkit-connection-status`, state via `data-connected="true"/"false"` (mirrors the existing `data-selected` pattern on tool chips) |
| Login/Logout button | `toolkit-connection-auth-button` |

Only flips to Connected on a **successful** sync
(`McpAuthHelpers.setConnectionVerified(...)` fires only in the hook's
success branch, `useGetRemoteMcpTools.hooks.js:110-119`) — a failed sync
leaves it exactly as it was before the attempt (confirmed: stays "Not
Connected" across 2 independent failed attempts in the same session).

## Raw Json editor gotcha (CodeMirror virtualization)

`McpFormPage.get_raw_json()` reads `.text_content()` in one call — silently
**truncates on any payload beyond ~30 rendered lines** (CodeMirror only
keeps a viewport-sized window of `.cm-line` nodes in the DOM). For a small
payload (no `available_mcp_tools`, or ≤1 tool), `get_raw_json()` is fine.
For 2+ discovered tools' full schemas, use **`get_raw_json_full()`** instead
(scrolls the real scrollable ancestor in steps, aggregates `.cm-line` text
by stable `offsetTop`, double-`rAF` condition-waits between scroll steps —
see its docstring). Added as a NEW method rather than modifying
`get_raw_json()` in place, per the additive-only-on-shared-caller-files
rule — 3 existing specs call the small-payload version unmodified.

## Known pre-existing console noise on this surface (not this feature's bugs)

- `#291` — React `key`-prop + `<p>`-in-`<p>` dev-mode warnings on
  `/mcps/create`. Fires on every navigation to the create form.
- `#549` — MUI Tabs invalid-value console error on `/mcps/all/{id}` detail
  pages. Intermittent (did not reproduce in the ELITEA-1934 session; did in
  ELITEA-1929's).

Both already tracked — don't re-file; exclude from any "no new console
errors" assertion on this surface.

## Analyst tooling note — browser-lane isolation

The batch's assigned CDP-port-based "isolated" browser lane is only as
isolated as whatever actually holds that port at session start — **verify
via `list-targets` (single target, expected URL) before trusting any
observation**, and don't assume a port number in a dispatch prompt guarantees
exclusivity in practice. If a page-info/screenshot ever shows unexpected
content mid-flow with no navigation issued by your own session, that's a
signal of lane contamination (a leftover or concurrently-driven Chrome
instance), not a product bug — abandon it and relaunch a fresh, uniquely
ported + uniquely profiled instance (`chrome --remote-debugging-port=<N>
--user-data-dir=<fresh scratch dir>`) rather than debugging further on a
compromised instance. (First observed ELITEA-1934, 2026-07-24 — port 9223
had a pre-existing, mid-navigation Chrome instance that was clobbered by an
apparent concurrent process partway through that session.)
