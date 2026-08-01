# Test Case: Remote MCP — Test Settings Panel — Select and Run Tool

## Metadata
- **TMS ID**: ELITEA-1937
- **Linked Story**: none
- **Priority**: l3 — TMS frontmatter says `priority: medium`. Used the sibling
  same-priority case ELITEA-1947 (`priority: medium` → `l3_`) as the l-number
  precedent (see the ELITEA-1934 AFS in this same batch for a note on this
  TMS's not-fully-consistent `priority` → `l`-number history).
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI`
  @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN`
  auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-01 (cluster dispatch with
  ELITEA-1934, shared login/navigation/discovery — steps executed and
  observed individually per case)
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- A Remote MCP with discovered tools is available.
  - **Fixture substitution (same precedent as ELITEA-1933's AFS):** the case's
    own example tool, `tavily_search`, requires an API-key credential this
    session doesn't have provisioned. Used the confirmed-working, no-OAuth
    `https://mcp.deepwiki.com/mcp` fixture instead (3 tools:
    `read_wiki_structure`, `read_wiki_contents`, `ask_question`) — same
    fixture ELITEA-1933 used, re-confirmed live this session. `read_wiki_structure`
    was selected as the exercised tool (simpler schema — a single required
    `repoName: string`, vs. `ask_question`'s `anyOf` array/string
    `repoName` + `question` — no functional difference for what this case
    tests, which is the select→run→see-result mechanism, not any specific
    tool's own correctness).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Toolkit Name: `autotest_mcp_run_tool` (recommend suffixing with a per-run
  unique token per the same open question noted at ELITEA-1922/1933).
- URL: `https://mcp.deepwiki.com/mcp`.
- Tool to select: `read_wiki_structure` (substituted for `tavily_search` — see
  Preconditions).
- Test query parameter: `repoName = "AsyncFuncAI/deepwiki-open"` (a real,
  DeepWiki-indexed GitHub repo — confirmed live to return a real, non-empty
  wiki-structure result, proving the tool genuinely executed against a live
  remote MCP server, not a canned/empty response).

## Test Steps

1. Create a Remote MCP (`autotest_mcp_run_tool` / `https://mcp.deepwiki.com/mcp`),
   click Load Tools, wait for the 3-tool fixture to load (same flow as
   ELITEA-1933 steps 1–7).
   - **Verify**: 3 tool pills render (`ask_question`, `read_wiki_contents`,
     `read_wiki_structure`).
2. Verify the right-side "Test Settings" region is present.
   - **Verify (CLARIFICATION — see Known Defects, issue #1086):** on a
     freshly-loaded MCP detail page with NO tool yet selected, the region
     shows `TestToolsEmptyState`, NOT a "Test Settings" panel — its own
     content is "Test toolkit" / "Choose a tool from the list to configure
     parameters and run the test." plus a "Select Tool" button
     (`[data-testid="toolkit-test-empty-tool-select"]`). The literal "Test
     Settings" heading only appears AFTER a tool is chosen (step 5 below).
     Confirmed live and via source (`TestTools.jsx`'s `!selectedTool` branch).
3. Click the empty-state "Select Tool" button
   (`[data-testid="toolkit-test-empty-tool-select"]`); verify it opens a
   popover listing all 3 discovered tools.
   - **Verify**: popover renders `menuitem`-role options "Ask question",
     "Read wiki contents", "Read wiki structure" — each with a
     `[data-testid="select-option-{tool_value}"]` (e.g.
     `select-option-read_wiki_structure`), confirmed live.
4. Select "Read wiki structure"
   (`[data-testid="select-option-read_wiki_structure"]`).
   - **Verify**: the panel now shows the heading "Test Settings"; a "Tool"
     combobox (`[data-testid="toolkit-test-tool-select"]`) displaying "Read
     wiki structure"; a "Model" section showing a non-empty default model
     name (confirmed live: "Anthropic Claude 4.5 Sonnet" — model-specific,
     assert non-empty only, not the exact string, same discipline as
     ELITEA-1866); a `repoName *` parameter field
     (`[data-testid="toolkit-test-param-repoName"]`); a Run button.
5. Verify a "chat area"/welcome message is shown.
   - **Verify (CLARIFICATION — issue #1086, NOT a defect):** case text implies
     a persistent welcome message ("Welcome! Select a tool from the Test
     Settings panel and click 'RUN TOOL' to see the results here.") is
     visible in a chat area at this point. **Confirmed live this does NOT
     happen** — after a tool is selected but before Run is clicked, the panel
     shows ONLY the settings form (step 4's fields); there is no separate
     chat/results region and `[data-testid="chat-message-list"]` does not
     exist in the DOM yet. Confirmed via source
     (`TestTools.jsx`'s 3-state machine: empty-state → settings-form →
     run-results; no state shows a welcome message between tool-selection
     and running). This step is therefore satisfied by the EMPTY-STATE
     message from step 2 (the only "chat-adjacent" copy shown pre-run), not
     by a post-selection welcome message — the case's own step ordering
     (select tool, THEN check welcome message) doesn't correspond to any
     live product state.
6. Fill the `repoName` parameter field
   (`[data-testid="toolkit-test-param-repoName"]`) with
   `AsyncFuncAI/deepwiki-open`; click the Run button
   (`[data-testid="toolkit-test-run-tool-button"]`, visible text "Run Test" —
   see Known Defects, issue #1087, for a case-text-vs-button-label note).
   - **Verify**: button is disabled until `repoName` is filled (confirmed
     live: `disabled` attribute flips to enabled only once the required field
     has a value).
7. Verify a response appears from the selected tool.
   - **Verify**: the panel is REPLACED by a "Run Results" view (back-arrow +
     heading "Run Results"); `[data-testid="chat-message-list"]` now exists
     and contains a result item reading `✅ read_wiki_structure (<duration>s)`
     followed by the real DeepWiki wiki-structure content for
     `AsyncFuncAI/deepwiki-open` (confirmed live: a real, multi-section page
     list — "Available pages for AsyncFuncAI/deepwiki-open:" followed by ~7
     top-level sections). This proves the tool genuinely executed against
     the live remote MCP server, not a mock.

## Expected Results
- The Test Settings panel's Tool dropdown lists all discovered tools and lets
  the user pick one, rendering that tool's parameter schema.
- The Model selector shows a non-empty default model.
- Running the tool (after filling its required parameters) produces a real
  result from the remote MCP server, displayed in a dedicated "Run Results"
  view that reuses the app's generic `chat-message-list` component.
- **Two CLARIFICATIONS found** (case text vs. live product — see Known
  Defects) and **one testid gap with a possible regression on an already-
  merged spec** (see Known Defects, issue #1088) — none block this case's own
  automation; all are documented dispositions in the Coverage Map below.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: Remote MCP with discovered tools available | precondition met | step 1 | step 1 | asserted — **fixture substituted (DeepWiki, not Tavily) — see Preconditions note** |
| 1 Open a Remote MCP detail page with discovered tools | detail page loads | step 1 | step 1 | asserted |
| 2 Verify right-side "Test Settings" panel is visible | panel displayed | step 2 | step 2 | asserted — **CLARIFICATION: pre-selection the region is the EMPTY STATE, not literally "Test Settings" — filed as #1086, see step 2's own note** |
| 3 Verify LLM model selector shows a default model | default model shown | step 4 | step 4 | asserted — non-empty only; **testid gap flagged as #1088 (regression risk on ELITEA-1866)** |
| 4 Verify "Tool" label and combobox dropdown present | dropdown visible | step 4 | step 4 | asserted |
| 5 Click the Tool combobox dropdown | dropdown opens | step 3 | step 3 | asserted — **case's step 4/5 correspond to this AFS's step-3 empty-state selector, since a fresh MCP starts with NO tool selected (EL-5947 gating) — see step 2/3 notes** |
| 6 Verify dropdown lists all available tools | all 3 tools listed | step 3 | step 3 | asserted |
| 7 Select a tool (e.g. "tavily_search") | tool selected | step 4 | step 4 | asserted — **substituted `read_wiki_structure` for `tavily_search`, see Preconditions** |
| 8 Verify welcome message in chat area | welcome message shown | step 5 | step 5 | asserted — **CLARIFICATION, NOT a defect: no chat area / welcome message exists between tool-selection and Run — filed as #1086** |
| 9 Type a test query and click "RUN TOOL" | execution triggered | step 6 | step 6 | asserted — **case says "RUN TOOL", live button reads "Run Test" — filed as #1087 (INFO, cosmetic copy mismatch); located via stable testid regardless of label text** |
| 10 Verify response appears in chat area | response displayed | step 7 | step 7 | asserted — real DeepWiki content confirmed, proving live execution |
| Expected Final State: tool executes, response visible in chat area | — | step 7 | step 7 | asserted |
| Pass/Fail criteria: all steps complete, tool runs, response appears | — | all steps | all steps | asserted — no BLOCKING defect; two clarifications + one testid-gap/regression-risk flag, none prevent completing the case's own observable |

### Axis 2 — Analyst additions

- `step 6` asserts the Run button is DISABLED until the required `repoName`
  field is filled — *added: the case's own step 9 ("type a test query and
  click RUN TOOL") implies this ordering is required but never states the
  button is gated on it; worth guarding since a regression that lets Run fire
  with empty required params would silently break every tool this panel
  supports.*
- `step 7` asserts the result text contains BOTH the tool name (`read_wiki_structure`)
  and real, non-canned content (the actual DeepWiki page list for the
  specific repo requested) — *added: a weaker assertion (e.g. just "some text
  appeared") would pass even if the MCP server were unreachable and the UI
  silently rendered an error string instead of a real result; asserting
  specific expected content proves genuine end-to-end execution, same
  discipline as ELITEA-1866's `{'total': 0, 'rows': []}` exact-match.*
- No console-error assertion added beyond the already-tracked #291/#549
  warnings reproduced again this session (see Known Defects), plus one NEW
  non-gating MUI warning observed (`Tooltip` wrapping a disabled `button`
  child) — generic MUI pattern-warning, not specific to this case's own
  functionality; `expect.soft()` recommended if ever asserted, not filed as
  its own issue (low value, high-volume pattern across the app).

## Cleanup

1. This case creates a persistent MCP toolkit entity (confirmed via `201
   Created`, `id: 2140` this session, name `autotest_mcp_run_tool`).
2. Delete it in test teardown via `ToolkitAPI.delete_toolkit(toolkit_id)`,
   same pattern as ELITEA-1933/1934.
3. Not deleted during this analysis session (no analyst cleanup authority —
   same as ELITEA-1934/1933 precedent). Flag to implementer: `id 2140`,
   `Private` project — harmless residue.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Empty-state "Select Tool" button | `[data-testid="toolkit-test-empty-tool-select"]` (existing, added ELITEA-1933, already in `mcp_form_page.py`/`toolkit_test_settings_page.py`) | none |
| Tool dropdown option (per tool, empty-state popover) | `[data-testid="select-option-{tool_value}"]` (existing, shared dropdown-option pattern) | none |
| Test Settings panel's Tool select (after a tool is chosen) | `[data-testid="toolkit-test-tool-select"]` (existing, same testid `mcp_form_page.py`'s `test_tool_select` and `toolkit_test_settings_page.py`'s `tool_select` both already declare) | none |
| Model selector (name + trigger) | **NO TESTID** — confirmed via source: `TestToolSettings.jsx` renders `<LLMModelSelector variant="field" .../>`, and `LLMModelSelector.jsx` only applies `data-testid="model-selector-button"`/`"model-selector-name"` in its `variant === 'default'` branch, NOT `'field'` (the one actually used here). **`automation/pages/toolkit_test_settings_page.py`'s existing `model_selector_button`/`model_selector_name` `LocatorDescriptor`s reference testids that do NOT exist in this rendered variant** — filed as issue #1088 (possible regression on the already-merged ELITEA-1866 spec, which asserts these same locators). Flag to `add-data-testid`: add the testid pair to the `'field'` variant branch of `LLMModelSelector.jsx`. | `page.locator('div').filter(has_text=re.compile(...)).first` scoped near the "Model" label text — fragile, not recommended for new code; better to unblock via `add-data-testid` first given the regression angle |
| Tool parameter field (`repoName`) | `[data-testid="toolkit-test-param-repoName"]` (existing dynamic-testid family, `TEST_PARAM_FIELD`/`TOOL_PARAM` class constants already in both page objects) | none |
| Run button | `[data-testid="toolkit-test-run-tool-button"]` (existing, `run_tool_button` in `toolkit_test_settings_page.py`) — **visible text is "Run Test", not "RUN TOOL"** (issue #1087, cosmetic only; testid is stable regardless) | none |
| Run Results container | `[data-testid="chat-message-list"]` (existing, shared `ChatMessageList.jsx` — same testid `toolkit_test_settings_page.py`'s `result_message_list` already declares) — only present AFTER Run is clicked, not before | none |
| Run Results item | `[data-testid="chat-message-list"] li.MuiListItem-root` (existing `RESULT_MESSAGE_ITEM` scoped class constant already in `toolkit_test_settings_page.py`) | none |
| Empty-state message (pre tool-selection) | **NO TESTID** on the message text itself — confirmed live text: "Test toolkit" / "Choose a tool from the list to configure parameters and run the test." (a DIFFERENT string from the `indexChat.helpers.js` "Welcome!..." copy — see Known Defects #1086). Out of this case's touched-element scope for a NEW testid request (the existing `empty_state_tool_select` testid on the button is sufficient to drive the flow; asserting this exact text is optional Axis-2 value, not load-bearing for the case's own pass/fail). | `page.get_by_text("Choose a tool from the list", exact=False)` if the implementer chooses to assert it |

## Network Behavior

- Same MCP-creation + Load-Tools network sequence as ELITEA-1933/1934
  (`POST tools/prompt_lib`, `POST mcp_sync_tools/prompt_lib?await_response=true`).
- Tool execution itself: no distinct REST endpoint was captured/attributed
  this session — the "Run Test" action's completion is proven by the DOM
  (`chat-message-list` populating with the ✅ result), not a captured network
  response body. Recommend the implementer capture the actual request during
  Phase 3 (likely a WebSocket message given `useToolkitChat`'s naming, or a
  `POST` to a toolkit-run endpoint) if a stronger network-level wait is
  wanted beyond the DOM-content wait `ToolkitTestSettingsPage.wait_for_tool_result()`
  already implements (regex `[✅❌]` content match, no fixed sleep).

## Known Defects Found During Exploration

- **[CLARIFICATION #1086]** Case text (steps 7–8) implies a persistent
  welcome message is visible in a chat/results area once a tool is selected
  but before Run is clicked. Confirmed live and via source
  (`TestTools.jsx`) that no such state exists on the Remote MCP surface — the
  panel shows only the settings form between tool-selection and run. Live
  product state machine is intentional and consistent (reverse-masking guard
  applies — case text is stale, not the product).
- **[INFO #1087]** The Run button's live text is "Run Test"
  (`TestToolSettings.jsx:128`), while the case text (and two other in-app
  copy sources — the welcome-message string and the interactive product tour)
  all say "RUN TOOL". Cosmetic copy inconsistency; doesn't affect automation
  (testid-based locate) or the case's own functional pass/fail.
- **[MINOR #1088]** The Test Settings panel's model selector
  (`LLMModelSelector` in its `'field'` variant) has NO `data-testid` on the
  model name/button — a real gap for THIS case's step 3, and a possible
  regression on the already-merged ELITEA-1866 spec, which asserts the same
  (non-existent-in-this-variant) testids. Flagged to the lead for
  verification against a fresh ELITEA-1866 run — this analysis session did
  not re-run that suite, only traced the shared component via source.
- **[Pre-existing, tracked, no new issue]** Issues #291 (React dev-mode
  console warnings on the MCP create form) and #549 (MUI Tabs invalid-value
  console error on the MCP detail page) both reproduced again this session,
  unrelated to this case's functionality — same as the ELITEA-1933 session.
- **[New, non-gating, not filed]** A MUI `Tooltip`-wrapping-a-disabled-button
  console warning was observed while the Run button was disabled
  (pre-`repoName`-fill). Generic MUI anti-pattern warning present wherever a
  disabled button carries a tooltip across this app — low signal-to-noise to
  track as its own issue; `expect.soft()` if a future test wants to assert
  zero console errors on this route.

## Blocked Steps

None. All case steps executed to completion against the live local
environment (with the fixture substitution noted in Preconditions).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- **Reuse `automation/pages/mcp_form_page.py`** (`McpFormPage`) for MCP
  creation + Load Tools (identical to ELITEA-1933/1934's flow — zero new
  methods needed there).
- **Reuse `automation/pages/toolkit_test_settings_page.py`**
  (`ToolkitTestSettingsPage`) for the Test Settings panel + Run flow — this
  is the SAME page object ELITEA-1866 already uses for the Artifact-toolkit
  surface (confirmed live: identical testids power both surfaces, same
  underlying `TestTools.jsx`/`TestToolSettings.jsx` components). No new page
  object needed; this case is a straightforward composition of
  `McpFormPage` (left/creation side) + `ToolkitTestSettingsPage` (right/test
  side), same pattern `test_toolkit_creation_create_bucket_verify_list_files.py`
  already establishes for the Artifact surface.
- **Do NOT reuse `model_selector_button`/`model_selector_name` as-is** until
  issue #1088 is resolved (testid doesn't exist in the `'field'` variant
  actually rendered here) — either wait for the testid fix, or use the
  interim locator noted in Concrete Handles, and flag the assertion as
  `expect.soft()` with `# Known defect: #1088` per the no-masking policy if
  the implementer chooses to proceed before the fix lands.
- **`select_tool_from_empty_state(tool_key)`** (existing method on
  `ToolkitTestSettingsPage`) is the correct entry point for step 3–4 — do NOT
  attempt to click `tool_select` directly on a fresh MCP detail page (it
  isn't mounted yet, confirmed live and via source, EL-5947 gating).
- **`run_tool()` + `wait_for_tool_result()`** (existing methods) are directly
  reusable for step 6–7 — `wait_for_tool_result()` already polls on the
  `[✅❌]` regex content match rather than a fixed sleep or message count,
  exactly what this case needs.
- Test data: fill `repoName` via the plain `<input>` inside
  `[data-testid="toolkit-test-param-repoName"]` — standard MUI text-field
  fill discipline (`click()` + `press_sequentially()`, not `fill()` — React
  onChange). `ask_question`'s `repoName` (array/string `anyOf`) is more
  complex to automate (a CodeMirror-style array editor) — prefer
  `read_wiki_structure`'s plain-string `repoName` for this case unless a
  future case specifically needs to test the `anyOf` shape.
