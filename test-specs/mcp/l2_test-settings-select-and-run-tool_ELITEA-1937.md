# Test Case: Remote MCP — Test Settings Panel — Select and Run Tool

## Metadata
- **TMS ID**: ELITEA-1937
- **Linked Story**: none
- **Priority**: l2 (source frontmatter: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost: `auth_state`/`VITE_DEV_TOKEN` skips login)
- **Analyst**: qa-engineer (agent), session 2026-07-23/24
- **Status**: **ready-for-automation** — case executed end-to-end live, twice
  (two separate fixture toolkits, ids `1738` and `1739`, both cleaned up via
  API after exploration). All 10 case steps + Preconditions + Expected Final
  State verified against the real system. **Zero product defects; zero new
  testid work required** (every handle this case touches already exists on
  `automation/testids`, several already promoted to `main` — see Concrete
  Handles § Provenance).

## Overlap check vs existing automation

`automation/tests/ui/toolkits/test_mcp_load_tools_discovery.py` (ELITEA-1933,
merged to `automation/base`) creates a Remote MCP against the same
`mcp.deepwiki.com` fixture, clicks Load Tools, and selects a tool in the SAME
Test Settings "Tool" dropdown this case uses — but it stops at asserting the
tool's parameter **schema renders** (`is_test_param_field_visible`). It never
fills a parameter, never clicks RUN TOOL, never reads a response from the
chat/result panel, and never touches the model selector. Those are exactly
this case's own stated objective ("...selecting a tool from the dropdown and
**executing it**, with the **result displayed in the chat area**") — the
defining, unique observable of ELITEA-1937 has **zero** overlap with
ELITEA-1933's assertions; only incidental setup (open detail page, tool
dropdown present, tool selectable) overlaps, and that overlap is on the
*scaffolding*, not the *observable-under-test*.

Per the merged-target/Rule-6 guidance ("when in doubt, classify
ready-for-automation — a duplicate fresh spec is visible and cheap; a false
extend is invisible and expensive") and because bolting a RUN TOOL/response
assertion onto ELITEA-1933's Load-Tools-discovery-focused test would blur
that test's single responsibility, this is classified **ready-for-automation**
as its own small, focused spec — not `extend-existing` against ELITEA-1933.
The new spec should still **reuse**, not reimplement: `ToolkitAPI.
create_remote_mcp_toolkit()` + `sync_mcp_tools()` for fixture setup (faster
and a more literal match for this case's own precondition — "a Remote MCP
with discovered tools **is available**", not "create one via the UI") and
`McpFormPage.navigate_to_detail()` to land on it directly. See test-specs/mcp/_surface.md
for the full recap (written this session, first digest for this surface).

`automation/pages/toolkit_test_settings_page.py` (ELITEA-1866, Artifact
toolkits) already implements the identical model-selector/RUN TOOL/
result-message pattern against the SAME shared `TestToolSettings.jsx`/
`ChatMessageList.jsx` components (confirmed via testid provenance — same
testids, same DOM shape) for a **different** page (`/toolkits/all/{id}` vs
this case's `/mcps/all/{id}`). Per page-object rules (one class per page,
no cross-page inheritance between unrelated entity types), the correct move
is to **port the pattern** (same 4 methods + 2 locators) onto `McpFormPage`,
not inherit from `ToolkitTestSettingsPage` — see Automation Hints.

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Project context set (`Private`, id `399` this session).
- A Remote MCP with discovered tools is available — **confirmed live**: the
  case's own example fixture ("Web Search"/`tavily_search`) requires an API
  credential this environment doesn't have (same gap ELITEA-1933's AFS
  documented); substituted the confirmed-working, auth-free
  `https://mcp.deepwiki.com/mcp` fixture (3 tools: `read_wiki_structure`,
  `read_wiki_contents`, `ask_question`), created via
  `ToolkitAPI.create_remote_mcp_toolkit()` (settings pre-populated from a real
  `sync_mcp_tools()` handshake — no "Load Tools" UI click needed, confirmed
  live the Tools section pills and Test Settings dropdown are already
  populated on first render).

## Test Data

### generate-per-test (API-level, cleaned up in test teardown)
- Toolkit name: any unique per-run token, e.g. `f"autotest_1937_{uuid4().hex[:8]}"`.
- URL: `https://mcp.deepwiki.com/mcp` (public, auth-free, stable 3-tool set —
  same fixture ELITEA-1933 uses; case's own "tavily_search" example needs a
  credential not available in this environment).
- Tool to select for the RUN TOOL step: **`read_wiki_structure`** (NOT the
  case's literal `tavily_search` example, and NOT `ask_question` either —
  `ask_question`'s `repoName` param is `anyOf` string/array and renders as a
  CodeMirror array editor, confirmed live, more fragile to automate than
  `read_wiki_structure`'s plain-text `repoName`). Test query value used this
  session: `repoName = "facebook/react"`.

### reuse-existing
- `${TEST_USER}` — only relevant on deployed envs; localhost skips login.

## Test Steps

1. Set up a Remote MCP with discovered tools via `ToolkitAPI` (API-level, not
   UI) and navigate to its detail page (`McpFormPage.navigate_to_detail(id, project_id)`).
   - **Verify**: detail page loads; page title contains the toolkit name
     (`get_detail_heading_text()`); URL is `${BASE_URL}/mcps/all/{id}`.
2. Verify the right-side "Test Settings" panel is visible.
   - **Verify**: the Tool dropdown (`toolkit-test-tool-select` testid) is
     visible — confirmed live, renders immediately on page load (no Load
     Tools click needed since tools were seeded via API). The panel's static
     "Test Settings" heading is a bare `<Typography>` with no testid
     (`TestToolSettings.jsx:125`, confirmed via `../EliteaUI/src`) and is not
     independently asserted — the dropdown's visibility is the panel's
     testid-backed presence signal (implementer amendment, fix round R1:
     the AFS previously claimed both were asserted; only the dropdown is).
3. Verify the LLM model selector shows a default model.
   - **Verify**: `model-selector-name` testid's text is non-empty. Confirmed
     live: `"Anthropic Claude 4.5 Sonnet"` this session — **assert non-empty
     only, never an exact model string** (project-configured default; the
     case's own "e.g. GPT-5.4-mini" is an illustrative example, not a literal
     expectation — matches prior precedent, see `.agents/memory/qa-engineer/`
     agent Save-As-Version / model-selector entries).
4. Verify the "Tool" label and combobox dropdown are present.
   - **Verify**: `toolkit-test-tool-select` (the `LocatorDescriptor` already on
     `McpFormPage`) is enabled. **Amended (fix round R2, implementer):** the
     AFS previously said "is visible" here, but the shipped test has always
     asserted `to_be_enabled()` for this step, not visibility — the dropdown's
     visibility was already confirmed two steps earlier at step 2 (same
     locator, no intervening navigation/state change), so this step's own
     testid-backed signal is that the control is interactive (enabled), not a
     redundant re-check of presence. The adjacent "Tool" text label carries no
     testid and is not independently asserted (incidental static copy next to
     the already-testid'd control, not a separately "touched" element).
5. Click the Tool combobox dropdown.
   - **Verify**: dropdown opens. **Amended (fix round R1, implementer):** the
     `test_tool_select` testid resolves to the MUI wrapper `<div>`, which
     carries **no `aria-expanded` attribute — confirmed live, it reads
     `null`**, so that signal does not exist on this element and cannot be
     asserted. The actual testid-backed open signal used is a known option
     (`get_test_tool_option(TOOL_NAME)`) becoming visible — the same handle
     steps 6/7 use — rather than an `aria-expanded` flip or a generic
     `listbox`/search-box role check.
6. Verify the dropdown lists all available tools for this MCP.
   - **Verify**: exactly 3 options render, matching the fixture's 3 tools —
     `select-option-ask_question`, `select-option-read_wiki_contents`,
     `select-option-read_wiki_structure` (confirmed live via
     `[data-testid^="select-option-"]` count == 3, same prefix-count pattern
     `toolkit_test_settings_page.py.TOOL_OPTION_ANY_SELECTOR` already uses).
7. Select a tool (`read_wiki_structure`).
   - **Verify**: the combobox's displayed value updates to the selected tool's
     label ("Read wiki structure"); its parameter schema renders — one
     required field, `repoName` (`toolkit-test-param-repoName`, plain text
     input).
8. Verify the welcome message in the chat area.
   - **Verify**: `chat-message-list`'s text **contains** `"Welcome! Select a
     tool from the Test Settings panel and click 'RUN TOOL' to see the
     results here."` — confirmed live, still showing at this point (tool
     SELECTION alone does not clear/replace it; only clicking RUN TOOL does —
     see step 10). **Amended (fix round R1, implementer):** not an exact-
     equality match — the message-list CONTAINER's `text_content()` prepends
     sender/timestamp header metadata (confirmed live: `"Elitealess than a
     minute ago..."` precedes the welcome text; per
     `.claude/rules/mui-patterns.md` § Extracting Message Text), so the
     assertion is substring containment (`EXPECTED_WELCOME_MESSAGE in
     welcome_text`) — same reason `ToolkitTestSettingsPage`'s own consuming
     test (`test_toolkit_creation_create_bucket_verify_list_files.py`)
     asserts containment, not equality, for the identical shared component.
9. Type a test query in the tool parameters and click "RUN TOOL".
   - **Verify**: filling `repoName` with `"facebook/react"` enables the
     previously-disabled RUN TOOL button (`toolkit-test-run-tool-button`) —
     confirmed live, enables instantly on the field having a non-empty value,
     no debounce. Click it.
10. Verify the response appears in the chat area from the selected tool.
    - **Verify**: `chat-message-list`'s content is **replaced in place** (not
      appended — message count stays 1) with a result **containing** `"✅
      read_wiki_structure (N.NNNs)"` followed by real tool output (confirmed
      live: `"Available pages for facebook/react:"` + a real nested wiki
      table-of-contents list, 8 top-level sections). Poll for the ✅/❌ prefix
      via `expect(...).to_contain_text(re.compile(r"[✅❌]"))`, never a fixed
      sleep or a message-count delta (the count never changes) — matches
      `ToolkitTestSettingsPage.wait_for_tool_result()`'s existing pattern
      exactly. **Amended (fix round R1, implementer):** not literally
      "starting with" the ✅ prefix — the message-list container prepends the
      same sender/timestamp header metadata step 8 documents (confirmed
      live: `"...Thought for 1 secautotest_1937_...: "` precedes the actual
      `"✅ tool_name (N.NNNs)"` result), so the assertion searches for the
      pattern (`re.search(rf"✅ {re.escape(TOOL_NAME)} \(\d", result_text)`)
      rather than anchoring at the string start.

## Expected Results
- The Test Settings panel renders with a default model, a working Tool
  dropdown listing every tool the MCP discovered, and a welcome message in
  the chat area before any tool has run.
- Selecting a tool renders its parameter schema; filling the required
  field(s) enables RUN TOOL.
- Clicking RUN TOOL executes the tool (via a hidden conversation +
  WebSocket predict cycle, not a synchronous REST call — see Network
  Behavior) and the chat area's message list is replaced in place with a
  ✅/❌-prefixed real result.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, Remote MCP with discovered tools available | detail page usable, tools present | step 1 | step 1 | asserted — **case's own example fixture (tavily_search) needs an unavailable credential; substituted the confirmed-working deepwiki fixture, same substitution ELITEA-1933's AFS already made** |
| 1 Open a Remote MCP detail page with discovered tools | detail page loads | step 1 | step 1 | asserted |
| 2 Verify Test Settings panel visible | panel displayed | step 2 | step 2 | asserted |
| 3 Verify LLM model selector shows a default model | default model shown | step 3 | step 3 | asserted — non-empty text only, case's example model name is illustrative not literal |
| 4 Verify Tool label + combobox present | dropdown enabled (visibility already proven at step 2) | step 4 | step 4 | asserted — `to_be_enabled()`, not a redundant visibility re-check (amended fix round R2) |
| 5 Click the Tool combobox dropdown | dropdown opens | step 5 | step 5 | asserted |
| 6 Verify dropdown lists all available tools | all MCP tools listed | step 6 | step 6 | asserted — exactly 3, matching fixture |
| 7 Select a tool | tool selected in dropdown | step 7 | step 7 | asserted |
| 8 Verify welcome message in chat area | welcome message shown | step 8 | step 8 | asserted — substring containment, not exact-equality (message-list container prepends sender/timestamp header metadata — **amended fix round R1**) |
| 9 Type a test query and click RUN TOOL | tool execution triggered | step 9 | step 9 | asserted — RUN TOOL enable-on-fill + click |
| 10 Verify response appears in chat area from the selected tool | tool response displayed | step 10 | step 10 | asserted — ✅ success pattern found via unanchored `re.search`, not a string-start prefix match (same header-metadata-prepended reason as step 8 — **amended fix round R1**), content-poll not count-poll |
| Expected Final State: selected tool executes successfully, response visible in chat | — | step 10 | step 10 | asserted |
| Pass/Fail criteria: all steps complete without errors; tool runs and response appears | — | all steps | all steps | asserted — zero console errors either exploration run (one pre-existing, unrelated, already-documented MUI Tooltip-on-disabled-button warning, see Known Defects) |

### Axis 2 — Analyst additions

- `step 10` asserts the message-list **replaces in place** (count stays 1
  before/after RUN TOOL) rather than appending — *added: the case's own
  steps don't specify this, but a regression that appended instead of
  replaced would break any test written against a "count == 2" assumption
  instead of a content-poll; confirmed live across BOTH exploration fixtures
  (ids 1738 and 1739), so this is a stable, reproducible platform behavior,
  not a one-off.*
- Network Behavior section documents that RUN TOOL creates a hidden
  conversation + participant and streams the result over the same WebSocket
  channel chat uses, rather than hitting a single synchronous "run tool" REST
  endpoint — *added: without this, an implementer's first instinct would be
  to `expect_response()` on a specific POST the way `click_load_tools()`
  does for `mcp_sync_tools`; there is no such single response to wait on here,
  only the message-list content itself.*
- No console-error assertion added as a case step — one pre-existing,
  already-known (`.agents/memory/test-automation-engineer/
  mui_form_field_quirks.md`), non-blocking MUI dev-mode warning ("Tooltip on
  a disabled button child") fires during normal RUN TOOL-button-disabled
  navigation; this is a widespread pattern across many disabled+tooltip'd
  buttons in this MUI-based app, not specific to this feature. `expect.soft()`
  recommended if a future test asserts zero console warnings on this route.

## Cleanup

1. This case creates a persistent MCP toolkit entity server-side
   (`POST /api/v2/elitea_core/tools/prompt_lib/{project}` → `201`). Delete it
   in test teardown via the existing `ToolkitAPI.delete_toolkit(toolkit_id)`
   client (confirmed reliable, `204`, same as ELITEA-1933/1922 precedent).
2. Both toolkits created during THIS analysis session (ids `1738`, `1739`)
   were deleted via the API before this AFS was written — no residue left on
   the local DEV backend.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Fallback |
|---|---|---|---|
| Model selector current-name | `LocatorDescriptor(testid="model-selector-name")` | **on-main ✓** (confirmed via fresh `git fetch origin` + `git grep` both refs) | none |
| Model selector button group | `LocatorDescriptor(testid="model-selector-button")` | **on-main ✓** | none |
| Tool dropdown (Test Settings panel) | existing `McpFormPage.test_tool_select` = `LocatorDescriptor(testid="toolkit-test-tool-select")` | **on-automation/testids only** (awaiting human promotion to `main`) | none — native MUI id `#simple-select-Tool` resolves the same element but is NOT the compliant page-object handle, use the testid |
| Tool dropdown option (dynamic) | existing `McpFormPage.SELECT_OPTION` template = `[data-testid="select-option-{}"]` | **on-main ✓** | none |
| Tool-run parameter field (dynamic, by schema key) | existing `McpFormPage.TEST_PARAM_FIELD` template = `[data-testid="toolkit-test-param-{}"]`; text-type fields need `.locator('input[type="text"]')` chained off the wrapper (give this its own method, don't chain in a spec) | **on-automation/testids only** | none |
| RUN TOOL button | **NEW field needed on `McpFormPage`** — `LocatorDescriptor(testid="toolkit-test-run-tool-button")` (identical testid `ToolkitTestSettingsPage.run_tool_button` already uses on the sibling toolkit-detail page) | **on-automation/testids only** — testid itself already exists app-wide, just not yet wired as a field on THIS page object | none |
| Result/welcome message list | **NEW field needed on `McpFormPage`** — `LocatorDescriptor(testid="chat-message-list")` (identical testid `ToolkitTestSettingsPage.result_message_list` already uses) | **on-main ✓** | none |
| Result message item (scoped) | **NEW class constant needed** — `RESULT_MESSAGE_ITEM = '[data-testid="chat-message-list"] li.MuiListItem-root'` (identical to `ToolkitTestSettingsPage.RESULT_MESSAGE_ITEM`) | n/a (scoped sub-selector, not a standalone testid) | none |

**No `add-data-testid` work required anywhere in this case** — every testid
above already exists (some on `main`, the rest on `automation/testids`,
confirmed via fresh `git fetch origin` this session). The only implementer
work is wiring 2 new `LocatorDescriptor` fields + 1 scoped constant + 4 new
methods onto `McpFormPage` (mirroring `ToolkitTestSettingsPage`'s existing,
already-reviewed pattern) — no EliteaUI-side changes at all.

## Network Behavior

- `POST /api/v2/elitea_core/tools/prompt_lib/{project}` — fires on fixture
  creation (API-level, not a UI action in this case); `201 Created`.
- `GET /api/v2/elitea_core/tool/prompt_lib/{project}/{id}?` — fires on detail
  page load; `200`.
- `GET /api/v2/elitea_core/toolkit_available_tools/prompt_lib/{project}/{id}`
  (×2) — fires on detail page load; `200`; confirms the API-seeded tool list
  matches what the Test Settings dropdown renders.
- **RUN TOOL has no single synchronous "run" response to wait on.** Clicking
  it fires `POST /api/v2/elitea_core/conversations/prompt_lib/{project}` →
  `201 Created` (a hidden/ephemeral conversation) then
  `POST /api/v2/elitea_core/participants/prompt_lib/{project}/{conversation_id}`
  → `200 OK`; the actual tool execution + result streams over the same
  WebSocket channel the regular chat page uses (not visible as a discrete
  HTTP request in the browser network log). **Wait on the message-list
  content** (✅/❌ prefix), never a specific `expect_response()` call.

## Known Defects Found During Exploration

**No blocking or new defect found.** All 10 case steps + Preconditions +
Expected Final State completed against the live local environment, twice
(two separate fixture toolkits), with zero console errors either run.

- **[INFO, not filed]** One pre-existing, already-known MUI dev-mode console
  warning ("Tooltip on a disabled button child") fired during normal
  navigation on this page (RUN TOOL button while disabled, wrapped in a
  Tooltip) — already documented in
  `.agents/memory/test-automation-engineer/mui_form_field_quirks.md` as a
  widespread pattern across this MUI-based app, not specific to this feature
  or this button. Not re-filed (no new information, no functional impact,
  and filing it here would be noise against an already-known, non-blocking
  pattern rather than a new finding).
- Case-text's example tool (`tavily_search`) and example model
  (`GPT-5.4-mini`) are both illustrative ("e.g.") — substituted a
  confirmed-working fixture tool and asserted the live default model
  non-empty rather than by exact name. Not a defect, not filed —
  matches the same substitution ELITEA-1933's AFS already made and the
  established "assert non-empty, never exact model name" convention.

## Blocked Steps

None. All case steps were executed to completion against the live local
environment.

## Fix Round R1 — AFS amendments (2026-07-24, implementer)

Reviewer finding [Important]: the implementation (`test_mcp_test_settings_run_tool.py`)
diverges from three AFS claims that were confirmed wrong live during Phase 2
Explore, but the AFS text wasn't updated to match in the original PR. Fixed in
this fix round — three amendments folded into the step text above (step 2,
step 5, step 8, step 10), each marked "Amended (fix round R1, implementer)":

1. **Step 5** — AFS claimed `aria-expanded` flips to `true` on dropdown open.
   Confirmed live: `test_tool_select`'s testid resolves to the MUI wrapper
   `<div>`, which has no `aria-expanded` attribute at all (reads `null`). The
   implementation (and now the AFS) uses a known option becoming visible as
   the open signal instead.
2. **Step 8** — AFS claimed the welcome message text is *exactly* the case
   string. Confirmed live: the message-list container's `text_content()`
   prepends sender/timestamp header metadata, so the implementation (and now
   the AFS) asserts substring containment, not equality.
3. **Step 10** — AFS claimed the result text *starts with* the ✅ prefix.
   Confirmed live: the same header-metadata prepending applies here too, so
   the implementation (and now the AFS) uses an unanchored `re.search` for
   the ✅/❌ pattern, not a "starts with" check.

Also folded in the reviewer's [Nit]: **step 2** overstated that the panel's
static "Test Settings" heading is independently verified — it has no testid
(confirmed via `../EliteaUI/src`) and the implementation only asserts the Tool
dropdown's visibility; the AFS now says so explicitly.

No scope change — all three corrections were already true of the live product
and already reflected in the shipped test code; this fix round brings the AFS
prose in line with that confirmed reality (the reverse-masking guard: the case
text/AFS is the hypothesis, the live product is ground truth).

**Addendum (2026-07-24, implementer, same fix round R1 continuation):** the
above three amendments corrected the step-text prose for steps 2/5/8/10 but
left the Coverage Map (Axis 1) table cells for steps 8 and 10 unsynced — those
rows still read "exact text match confirmed live" (step 8) and "✅-prefixed"
(step 10), contradicting the just-amended prose two paragraphs above. No test
code or behavior change (`test_mcp_test_settings_run_tool.py:130` already
asserts substring containment; `:153` already uses unanchored `re.search`) —
pure Coverage Map text sync so the table matches the prose it's supposed to
summarize. Re-ran green locally to confirm (see Run Report in the PR).

## Fix Round R2 — AFS amendment (2026-07-24, implementer)

Reviewer finding [Important]: R1 fixed the identical AFS-vs-code drift class
for steps 2/5/8/10 but missed **step 4** — the AFS text and its Coverage Map
cell said the step verifies the dropdown **is visible**, while the shipped
test (`test_mcp_test_settings_run_tool.py:98-99`, unchanged since the original
PR) has always asserted `expect(form.test_tool_select).to_be_enabled(...)`, a
different check. Fixed in this fix round — step 4's text and Coverage Map row
now describe the enabled-state check the code actually performs, and note that
the same locator's visibility was already proven two steps earlier at step 2
with no intervening navigation/state change (confirmed live, this session),
so asserting `to_be_enabled()` at step 4 is a distinct, meaningful check
(control is interactive, not merely present) rather than a redundant repeat of
step 2. No test code or behavior change — pure AFS text/Coverage-Map sync,
same reverse-masking-guard treatment R1 applied to steps 2/5/8/10 (the live
product + shipped code are ground truth; the AFS prose is corrected to match,
not the other way around). Re-ran green locally to confirm (see Run Report in
the PR).

## Automation Hints

- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- **Reuse `automation/pages/mcp_form_page.py`** (`McpFormPage`) — this case
  only needs the Test Settings panel's model-selector/RUN TOOL/result-message
  methods layered on top of the existing class (which already has
  `test_tool_select`, `select_test_tool()`, `TEST_PARAM_FIELD`,
  `is_test_param_field_visible()` from ELITEA-1933), not a new page object.
- **Port, don't inherit, from `automation/pages/toolkit_test_settings_page.py`**
  (`ToolkitTestSettingsPage`, ELITEA-1866) — it implements the identical
  pattern against the SAME shared components for a different page
  (`/toolkits/all/{id}`). Per page-object rules (one class per page/route,
  no cross-entity inheritance), copy the shape of these 4 methods + 2
  locators onto `McpFormPage` rather than making `McpFormPage` inherit from
  it:
  - `model_selector_button` / `model_selector_name` `LocatorDescriptor`s
    (testids `model-selector-button` / `model-selector-name`, already on
    `main`).
  - `run_tool_button` `LocatorDescriptor` (testid
    `toolkit-test-run-tool-button`).
  - `result_message_list` `LocatorDescriptor` (testid `chat-message-list`) +
    `RESULT_MESSAGE_ITEM` scoped constant.
  - `fill_test_param(field_key, value)` — **new**, doesn't exist on either
    page object yet (`ToolkitTestSettingsPage` only has
    `is_param_field_visible()`, no fill method); needs to
    `.locator('input[type="text"]')` off the `TEST_PARAM_FIELD`-templated
    wrapper for text-type fields (confirmed shape live: the testid sits on a
    wrapper `<div>`, not the `<input>` itself).
  - `run_tool()` — click `run_tool_button`, mirrors
    `ToolkitTestSettingsPage.run_tool()` exactly.
  - `get_welcome_message_text()` / `wait_for_tool_result()` — mirror
    `ToolkitTestSettingsPage`'s existing methods verbatim (same testids, same
    replace-in-place behavior, same ✅/❌-prefix poll).
  - Consider a shared mixin/base for these 4+2 items if a THIRD entity type
    (Application? Skill?) ever grows a Test Settings panel — out of scope to
    build preemptively for this one case, flag to the lead if it recurs a
    third time.
- **Fixture setup — API, not UI.** Use `ToolkitAPI.sync_mcp_tools(url)` +
  `ToolkitAPI.create_remote_mcp_toolkit(name, description, url, tools)` (both
  already exist in `automation/api/client.py`) instead of driving
  `McpFormPage`'s create-form + Load-Tools UI flow — faster, deterministic,
  and a more literal match for this case's "a Remote MCP with discovered
  tools is available" precondition. Land on the detail page via
  `McpFormPage.navigate_to_detail(toolkit_id, project_id)` (existing method).
- Tool choice for the RUN TOOL step: **`read_wiki_structure`**, single
  required plain-text field (`repoName`) — avoids `ask_question`'s CodeMirror
  array-editor `repoName` variant (more automation surface for no case
  benefit; this case doesn't require exercising the array-editor shape).
- Wait strategy for RUN TOOL: poll the message-list content for the ✅/❌
  prefix (`expect(locator).to_contain_text(re.compile(r"[✅❌]"))`), never a
  fixed sleep and never a message-count delta (count stays 1, confirmed twice
  live) — mirrors `ToolkitTestSettingsPage.wait_for_tool_result()` exactly,
  reuse its implementation shape.
- See `test-specs/mcp/_surface.md` (written this session) for the fuller
  recap, reusable by any future MCP-surface case.

## Redispatch confirmations

- **2026-07-24 (analyst redispatch, third dispatch overall per board
  History — `analysis` → `ready-for-automation` → `implementing` →
  `analysis`)**: Variant-B bounded re-verification, no PR/review verdict in
  between (`env -u GITHUB_TOKEN gh pr list --state all --limit 200 --json
  number,headRefName` → no ELITEA-1937 entry). Ground truth checked:
  - Fresh `cd ../EliteaUI && git fetch origin` + `git grep` re-confirmed
    every Concrete-Handles PROVENANCE row unchanged: `model-selector-name`,
    `model-selector-button`, `select-option-{}`, `chat-message-list` still
    `main:YES`; `toolkit-test-tool-select`, `toolkit-test-param-{}`,
    `toolkit-test-run-tool-button` still `main:no / testids:YES`. Zero
    drift.
  - **One live end-to-end spot-check** on a THIRD fresh fixture toolkit
    (id `1747`, `ToolkitAPI.create_remote_mcp_toolkit()` against the same
    deepwiki URL, deleted via `delete_toolkit(1747)` after), via an
    isolated `browser-verify` CDP instance (own port `9223`, own
    `--user-data-dir`, per browser-lane discipline — shared Playwright MCP
    lane not used): navigated to the detail page, confirmed model-selector
    text still `"Anthropic Claude 4.5 Sonnet"` non-empty, welcome message
    still the exact case-text string, dropdown still lists exactly 3
    `select-option-*` entries, selected `read_wiki_structure`, filled
    `repoName="facebook/react"` (confirmed RUN TOOL flips from
    `disabled=true` to `disabled=false` the instant the field has a
    non-empty value — no debounce, matching the AFS claim), clicked RUN
    TOOL, and confirmed the result renders `"✅ read_wiki_structure
    (1.151s)"` + real `"Available pages for facebook/react:"` wiki-TOC
    content, message-list item count still exactly **1** (replace-in-place
    reconfirmed a third independent time), zero new console errors (only
    the same pre-existing, already-known MUI Tooltip-on-disabled-button
    warning). **Zero drift found** — AFS content stands unchanged,
    classification unchanged (`ready-for-automation`).
  - **Implementer worktree finding (flag for the orchestrator, not an
    analyst action):** `.claude/worktrees/wf_e44028a9-dec-32` (branch
    `tests/ELITEA-1937-mcp-test-settings-select-run-tool`) holds a
    **substantial, uncommitted, policy-compliant** implementer diff on
    `automation/pages/mcp_form_page.py` — all 4 methods
    (`fill_test_param`, `run_tool`, `get_welcome_message_text`,
    `wait_for_tool_result`) + 2 `LocatorDescriptor` fields
    (`run_tool_button`, `result_message_list`, plus the already-ported
    `model_selector_button`/`model_selector_name`) + the
    `TEST_PARAM_TEXT_INPUT`/`RESULT_MESSAGE_ITEM` scoped constants, exactly
    matching this AFS's Automation Hints — testid-only, no raw
    `get_by_*`/`page.locator()` violations spotted. **The only thing
    missing is the `test_*.py` spec file itself and a commit** — the
    page-object porting work described in this AFS is essentially done,
    sitting unsaved in the worktree. This is the case's board History
    bouncing `implementing` → `analysis` with **real, non-trivial progress
    already produced** (distinct from the zero-artifact bounce pattern
    logged elsewhere in `.agents/memory/qa-engineer/
    analyst_redispatch_on_already_complete_case_check_board_git_then_bounded_spotcheck.md`
    for other cases this session) — the correct next dispatch is the
    **implementer, resuming that exact worktree**, not another analyst
    pass. Did not touch the worktree (analyst slot has no git commit
    authority and no mandate to edit implementer-owned files).
