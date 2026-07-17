# Test Case: Remote MCP — Load Tools (Tools Discovery)

## Metadata
- **TMS ID**: ELITEA-1933
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server, confirmed "Elitea is connected" in the sidebar after page load)
- **Analyst**: qa-engineer (agent), session 2026-07-17
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`; on deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: Private`, project id `399` in this session — read from `${ELITEA_PROJECT_ID}`).
- A valid, reachable remote MCP server URL with a genuinely loadable tool set. **This case's own precondition text ("e.g. Tavily SSE endpoint") does not resolve to a usable fixture without an API key/credential** — per prior analyst memory (`mcp_pipeline_node_toolkit_tool_switch_quirks.md`, ELITEA-1954 session), the public, auth-free `https://mcp.deepwiki.com/mcp` endpoint (3 tools: `read_wiki_structure`, `read_wiki_contents`, `ask_question`, streamable-HTTP MCP protocol, not literally SSE) is the confirmed-working, no-OAuth fixture used for this run and recommended for automation. Placeholder URLs (`mcp.example.com`) never load tools — do not use as a "Load Tools" fixture.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Toolkit Name: `autotest_tools_discovery` — recommend suffixing with a per-run unique token (e.g. `f"autotest_tools_discovery_{uuid4().hex[:8]}"`); uniqueness constraints were not explored in this session (same open question noted in the ELITEA-1922 AFS).
- URL: `https://mcp.deepwiki.com/mcp` (public, auth-free, always has exactly 3 tools available — stable fixture).

### reuse-existing
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/create`, click the Remote MCP type card (`[data-testid="toolkit-type-card-mcp"]`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/create/mcp`; "New Remote MCP" tab is shown; Toolkit Name / Url fields are visible; Tools accordion shows the empty-state message (see step 4, visible even before Name/URL are filled).
2. Fill Toolkit Name (`[data-testid="toolkit-form-name-input"]`) with `autotest_tools_discovery`.
   - **Verify**: field displays the typed value.
3. Fill Url (`[data-testid="toolkit-field-url-input"]`) with `https://mcp.deepwiki.com/mcp`.
   - **Verify**: field displays the typed value; Save button (`[data-testid="toolkit-form-save-button"]`) becomes enabled.
4. Click Save.
   - **Verify**: `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` returns `201 Created`; page navigates to `${BASE_URL}/mcps/all/{id}?name=autotest_tools_discovery`; `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}?` returns `200`; detail page title (`[data-testid="toolkit-detail-title"]`) shows the toolkit name.
5. On the detail page, verify the Tools section (Configuration accordion, "TOOLS" sub-heading) shows the empty-state text.
   - **Verify**: text content is exactly `No tools to display for now. To get tools from MCP press button "Load Tools"` (curly quotes in the live product; case text uses straight quotes — cosmetic, not a mismatch). Confirmed via live snapshot before any tool load.
6. Click the "Load Tools" element (no testid — see Concrete Handles; located this session via a text-exact locator on the Tools section, e.g. `get_by_text("Load Tools", exact=True)` scoped inside the region under the "TOOLS" heading).
   - **Verify**: `GET /api/v2/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{id}` and `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/${PROJECT_ID}?await_response=true` both fire and return `200`; a transient success toast "Successfully fetched 3 tools" appears (role="alert", auto-dismisses — do not assert on it as a persistent element, it is gone by the time a slow assertion would check).
7. Wait for the sync request to resolve.
   - **Verify**: same network wait as step 6 covers this — the tools list is populated synchronously with the `mcp_sync_tools` response resolving, not a separate polling step. The "Not Connected"/"Login" indicator near the view toggler also flips to "Connected!"/"Logout".
8. Verify discovered tools appear as pill buttons in the Tools section, each showing the tool name.
   - **Verify**: exactly 3 pills render with text `read_wiki_structure`, `read_wiki_contents`, `ask_question` (MUI `Chip` components, `role="button"` via `MuiChip-clickable`, no `data-testid`). All 3 show a checkmark icon by default (i.e. `selected_tools` starts fully populated with every discovered tool — see Axis 2).
9. Click a discovered tool pill (e.g. `ask_question`).
   - **Verify (CLARIFICATION — case text step 8 vs. live product, filed as issue #595):** clicking a Tools-section pill toggles that tool's checkmark (its `selected_tools` membership) — it does **not** open a details/schema panel. The case text's "shows tool details or schema on click" is satisfied by a **different** UI affordance: selecting the same tool name from the "Test Settings" panel's "Tool" dropdown (`#simple-select-Tool`, native MUI `id`, no testid; options use the shared `[data-testid="select-option-{value}"]` pattern, e.g. `select-option-ask_question`) renders that tool's parameter schema as live input fields (for `ask_question`: `repoName *` — a CodeMirror array-input, `question *` — a text field). Automation should assert schema-on-select via the Test Settings dropdown, not via a Tools-section pill click.
10. Switch to "Raw Json" view (`[data-testid="toolkit-raw-json-view-toggle"]`); read the JSON via `.cm-line` node text (CodeMirror virtualizes rendering — do not `textContent` the container directly without scrolling the `.cm-scroller` into view of every line first, see Automation Hints).
    - **Verify**: `settings.available_mcp_tools` is an array of 3 objects, each with `label`, `value`, `args_schema` (a JSON-schema `properties`/`required`/`type` object) and `description` keys — confirmed shapes: `read_wiki_structure`/`read_wiki_contents` both require `repoName: string`; `ask_question` requires `repoName` (string or array of strings, `anyOf`) and `question: string`.
11. Verify `settings.selected_tools` in the same Raw Json payload.
    - **Verify**: array contains all 3 discovered tool names — `["read_wiki_structure", "read_wiki_contents", "ask_question"]` — matching the checkmarked state observed in step 8's pills (all default-selected after Load Tools, before any manual pill-toggle).

## Expected Results
- The Remote MCP successfully discovers and loads tools from the live remote server (`mcp_sync_tools` returns 200, toast confirms count).
- All discovered tools render as pills in the Form view's Tools section.
- `available_mcp_tools` (label/value/args_schema per tool) and `selected_tools` (tool-name array) are both populated and correct in the Raw Json view.
- Tool schema is inspectable via the Test Settings "Tool" dropdown selection (not via the Tools-section pill click — case-text clarification, not a defect).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, valid remote MCP server URL available | form loads, URL usable | steps 1–3 | step 3 (URL accepted) | asserted — **case's own example fixture (Tavily) requires a credential this session didn't have; substituted the confirmed auth-free `mcp.deepwiki.com` fixture, see Preconditions note** |
| 1 Create Remote MCP named "autotest_tools_discovery" | form loads | steps 1–2 | step 2 | asserted |
| 2 Fill URL with valid remote MCP server URL | field accepts/displays URL | step 3 | step 3 | asserted |
| 3 Save the MCP | detail page loads | step 4 | step 4: 201 + navigation | asserted |
| 4 Verify Tools empty-state message | exact message shown | step 5 | step 5 | asserted — exact text match confirmed live (curly-quote variant) |
| 5 Click "Load Tools" | loading initiates | step 6 | step 6: network fires | asserted |
| 6 Wait for tools to load | tools load from remote server | step 7 | step 7: network resolves + Connected status | asserted |
| 7 Verify discovered tools appear as buttons with names | pills visible with names | step 8 | step 8 | asserted |
| 8 Verify each tool is clickable (shows details/schema on click) | click shows tool details/schema | step 9 | step 9 | asserted — **CLARIFICATION, not defect: schema shows via Test Settings dropdown selection, not the Tools-section pill click; filed as issue #595, see Known Defects** |
| 9 Switch to Raw Json, verify available_mcp_tools populated with label/value/args_schema | array shape correct | step 10 | step 10 | asserted |
| 10 Verify selected_tools contains discovered tool names | array populated | step 11 | step 11 | asserted |
| Expected Final State: all discovered tools visible in Form view and reflected in Raw JSON; both arrays populated | — | steps 8–11 | steps 8–11 | asserted |
| Pass/Fail criteria: all steps complete without errors; tools discovered, displayed, and in Raw JSON | — | all steps | all steps | asserted — no blocking errors encountered; two known/tracked console warnings only (see Known Defects), neither tied to this feature's functional correctness |

### Axis 2 — Analyst additions

- `step 8` asserts all 3 tools are checkmarked (`selected_tools`-included) immediately after Load Tools, with no manual selection — *added: the case text doesn't specify the default selection state; worth guarding since a regression that silently loads tools into `available_mcp_tools` but leaves `selected_tools` empty would still pass the case's literal steps 7–10 but break every downstream consumer (agents/pipelines) that reads `selected_tools`.*
- `step 6` notes the transient "Successfully fetched 3 tools" toast — *added: a quick positive-confirmation signal worth a soft assertion, but explicitly NOT the primary wait condition (see Automation Hints — wait on the network response, not the toast, since the toast auto-dismisses and is not itself proof of DOM update).*
- `step 10` documents the CodeMirror virtualized-rendering gotcha for reading the full Raw Json payload — *added: this session's first `textContent()` read on the Raw Json editor silently truncated after ~30 lines (JSON well past `available_mcp_tools[0]`) with no error — a naive implementer assertion against a truncated read would either false-fail or (worse) false-pass on a coincidentally-valid partial JSON prefix. Flagged so the implementer doesn't rediscover this the hard way.*
- No console-error assertion added — the app has two pre-existing, already-tracked React dev-mode warnings (issue #291, `key`-prop + `<p>`-in-`<p>` on `/mcps/create`) and one already-tracked MUI Tabs warning (issue #549, fires on `/mcps/all/{id}` detail-page load) that occurred during this session's normal navigation, unrelated to the Load Tools feature itself. `expect.soft()` recommended if a future test asserts zero console errors on these routes — do not block this case's own assertions on them.

## Cleanup

1. This case creates a persistent MCP toolkit (server-side `tool` entity, confirmed via `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` → `201 Created`, `id: 1362` this session).
2. Delete it in test teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)` client (`automation/api/client.py`, confirmed present by the ELITEA-1922 AFS precedent — calls `DELETE {ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${PROJECT_ID}/{toolkit_id}`).
3. During manual exploration, one MCP toolkit was created on the local DEV backend (id `1362`, name `autotest_tools_discovery`, URL `https://mcp.deepwiki.com/mcp`) and was **not deleted** by this analysis session (analyst does not have automation authoring/cleanup authority — `.agents/memory/qa-engineer/analyst_slot_has_no_git_commit_authority.md` and the ELITEA-1922 AFS precedent apply the same reasoning to API-level cleanup). Flag to the implementer: delete id `1362` via `DELETE ${ELITEA_API_BASE}/elitea_core/tool/prompt_lib/${ELITEA_PROJECT_ID}/1362` before the automated test's own fixture data starts accumulating, or treat it as harmless residue (a `Private`-project-scoped Remote MCP, name won't collide unless the implementer's generated names aren't uniquified).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Remote MCP type-selector card | `[data-testid="toolkit-type-card-mcp"]` (existing, confirmed live) | none |
| Toolkit Name input | `[data-testid="toolkit-form-name-input"]` (existing) | none |
| Url input | `[data-testid="toolkit-field-url-input"]` (existing) | none |
| Save button (create form) | `[data-testid="toolkit-form-save-button"]` (existing) | none |
| Tools section empty-state text | no testid on the container; text is unique enough (`get_by_text("No tools to display for now...")`) — **MISSING TESTID**, flag to `add-data-testid`: recommend `toolkit-tools-empty-state` on the message `<generic>` wrapper | `get_by_text("No tools to display for now", exact=False)` scoped inside the "Tools" accordion region — acceptable interim per stop+flag (see below), not a precedent for new code elsewhere |
| "Load Tools" button | **NO TESTID** — plain `MuiBox`-nested `<span>` with no `id`/testid anywhere in its 5-level ancestor chain (confirmed live via DOM walk, all ancestors `data-testid: null`). **Flag to `add-data-testid`**: recommend `toolkit-load-tools-button` on the clickable wrapper. This gap was already noted by a prior analyst (ELITEA-1954 session) and remains unaddressed as of this session — still needs the EliteaUI fix. | `get_by_text("Load Tools", exact=True)` scoped inside the region under the "Tools" `<h3>` — interim only |
| Discovered tool pill (per tool) | **NO TESTID** — MUI `Chip` (`MuiChip-clickable`), no `data-testid`, no stable `id`. **Flag to `add-data-testid`**: recommend a dynamic `toolkit-tool-chip-{tool_name}` (class-level template constant per `.agents/testing.md` § dynamic-testid pattern) on each `Chip`. | `get_by_role("button", name=tool_name, exact=True)` scoped inside the Tools region — interim only; NOT unique across a toolkit with a tool named e.g. "Save" that collides with the page's own Save button, so scope it tightly |
| Tool select dropdown (Test Settings panel) | `#simple-select-Tool` — native MUI `id`, **no `data-testid`** (same gap already flagged at ELITEA-1954 for the pipeline-node MCP surface; this is the chat/test-settings surface's equivalent control, same underlying gap). Flag to `add-data-testid`: recommend `toolkit-test-tool-select`. | `page.locator("#simple-select-Tool")` — interim only |
| Tool dropdown option (per tool) | `[data-testid="select-option-{value}"]` (existing, shared dropdown-option pattern confirmed live, e.g. `select-option-ask_question`) | none needed — already compliant |
| Raw Json view toggle | `[data-testid="toolkit-raw-json-view-toggle"]` (existing) | none |
| Raw Json editor content | `[data-testid="toolkit-raw-json-editor-content"]` (existing) — **read via `.cm-line` node aggregation after scrolling, not a single `text_content()` call**, see Automation Hints | none |
| Detail page title heading | `[data-testid="toolkit-detail-title"]` (existing) | none |

**Stop+flag note:** the three missing-testid items above (Load Tools button, tool pills, Tool select dropdown) are all inside `EliteaUI/src` (`ToolBase.jsx` / a chat "Test Settings" panel component) — none are third-party widgets. Per `.agents/testing.md` § Locator policy, these are ordinary `add-data-testid` work, not a permanent stop+flag exception; the interim text/role/id-based locators above are documented so the implementer isn't blocked on a testid PR merging first, but should be replaced with real testids as soon as they land on `automation/testids`.

## Network Behavior
- `POST /api/v2/elitea_core/tools/prompt_lib/${PROJECT_ID}` — fires on Save click; `201 Created`; response body's `id` needed for teardown and the expected detail-page URL.
- `GET /api/v2/elitea_core/tool/prompt_lib/${PROJECT_ID}/{id}?` — fires on detail-page load; `200`; confirms persisted config before any Load Tools interaction.
- `GET /api/v2/elitea_core/toolkits/prompt_lib/${PROJECT_ID}?mcp=true` — fires on Load Tools click (part of the connect sequence, precedes the sync call); `200`.
- `GET /api/v2/elitea_core/toolkit_available_tools/prompt_lib/${PROJECT_ID}/{id}` (×2, one before Load Tools returning empty, one after) — `200`.
- `POST /api/v2/elitea_core/mcp_sync_tools/prompt_lib/${PROJECT_ID}?await_response=true` — **the actual tools-discovery call**, fires on Load Tools click; `200`; this is the response to wait on before asserting the Tools pills/Raw JSON are populated, not a fixed timeout or the toast's appearance/disappearance.

## Known Defects Found During Exploration

**No blocking defect found in the Load Tools / tools-discovery feature itself.** All 11 AFS steps completed against the live local environment; tools were discovered, displayed, and correctly reflected in both the Form view (pills) and Raw Json view (`available_mcp_tools` + `selected_tools`).

- **[INFO] Case-text ambiguity on step 8 ("click a tool shows details/schema")** — filed as `EliteaAI/elitea-testing-public#595` (label `bug`, `[INFO]` severity, reverse-masking guard applied — live product is correct, case text under-specifies *which* UI element). See AFS step 9 for the resolved behavior. Recommend `expect.soft()`-free — this is a real functional assertion the implementer should make against the correct element (Test Settings dropdown), not a soft/skippable one.
- **[MINOR] MUI Tabs invalid-value console error on the MCP detail page** — already tracked as `EliteaAI/elitea-testing-public#549` (filed during a prior ELITEA-1929 session, reproduced again this session on `/mcps/all/1362`, no new issue filed — dedup confirmed via `gh issue list`). No functional impact; `expect.soft()` if ever asserted.
- **[MINOR] Pre-existing React dev-mode console warnings on `/mcps/create`** — already tracked as `EliteaAI/elitea-testing-public#291` (`key`-prop + `<p>`-in-`<p>` warnings), reproduced again this session, no new issue filed (dedup).

## Blocked Steps

None. All case steps were executed to completion against the live local environment using a substituted (case-text-diverging but functionally equivalent) fixture URL — see Preconditions note.

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (per `.agents/testing.md`).
- **Reuse `automation/pages/mcp_form_page.py`** (`McpFormPage`) for all Configuration-accordion fields (`name_input`, `url_input`, `save_and_wait_for_created`, `switch_to_raw_json_view`, `get_raw_json`, `navigate_to_detail`, etc.) — this case only needs the new Tools-section methods layered on top of the existing class, not a new page object.
- **`get_raw_json()` in `McpFormPage` currently reads `raw_json_editor_content.text_content()` in one call** — per this session's discovery (Axis 2), that silently truncates on a payload as large as `available_mcp_tools` for 3 tools (CodeMirror virtualizes rendering, only ~30 lines are in the DOM at a time). **This method needs strengthening before this case can safely reuse it**: scroll the `.cm-scroller` (or send `Control+End` after clicking into the editor) and aggregate all `.cm-line` node texts across the full scroll range, not a single `text_content()` read. Flag to the lead/implementer — this is a latent gap in existing shared page-object code, not specific to this case, and will silently under-read any future case with a large Raw Json payload too.
- New methods needed on `McpFormPage` (or a small mixin): `click_load_tools()`, `get_tools_empty_state_text()`, `get_discovered_tool_names()`, `click_tool_pill(name)` (toggles selection, does NOT open schema — name accordingly, e.g. `toggle_tool_selected(name)` to avoid the case-text's misleading "click shows details" framing), `select_test_tool(name)` (Test Settings dropdown — this is what actually renders schema fields).
- Wait strategy for Load Tools: wait for the `POST .../mcp_sync_tools/prompt_lib/{project}?await_response=true` response (`200`) before asserting pills/Raw JSON, not the toast (auto-dismisses, unreliable timing) and not a fixed timeout.
- Fixture recommendation: `https://mcp.deepwiki.com/mcp` (public, auth-free, stable 3-tool set) rather than a Tavily/credentialed endpoint, unless the suite already provisions an MCP credential elsewhere — avoids adding a new secret dependency just for this case.
