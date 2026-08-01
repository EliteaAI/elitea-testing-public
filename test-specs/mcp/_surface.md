# Surface digest — Remote MCP (`/mcps/...`)

> Handle cache from live exploration. Verify each handle as you use it — this
> is a cache, not a source of truth. Last updated: 2026-08-02 (ELITEA-1934 /
> ELITEA-1937 implementer session, fix round 2 — testid gaps resolved via
> `add-data-testid`; originally created 2026-08-01, analyst session, cluster
> dispatch, `approved-top10` batch).

## Confirmed-stable handles (testid-based)

| Handle | Testid | Notes |
|---|---|---|
| Remote MCP type card | `toolkit-type-card-mcp` | `/mcps/create` type picker |
| Toolkit Name input | `toolkit-form-name-input` | shared create/detail |
| Url input | `toolkit-field-url-input` | shared create/detail |
| Save (create form) | `toolkit-form-save-button` | |
| Load Tools button | `toolkit-load-tools-button` | |
| Discovered tool pill (dynamic) | `toolkit-tool-chip-{tool_name}` | `data-selected` attr for checked state |
| Empty-state "Select Tool" button | `toolkit-test-empty-tool-select` | ONLY entry point into Test Settings — panel does not mount until a tool is chosen (EL-5947, gates BOTH MCP and Artifact surfaces) |
| Dropdown option (dynamic) | `select-option-{tool_value}` | shared pattern, MCP tool picks + empty-state tool picks |
| Test Settings Tool select (post-selection) | `toolkit-test-tool-select` | |
| Tool parameter field (dynamic) | `toolkit-test-param-{fieldKey}` | schema-property-keyed |
| Run button | `toolkit-test-run-tool-button` | **visible text is "Run Test", not "RUN TOOL"** — issue #1087, cosmetic only, locate via testid |
| Run Results container | `chat-message-list` | only exists in DOM AFTER Run is clicked — shared `ChatMessageList.jsx`, same testid the Artifact-toolkit surface uses |
| Run Results item | `chat-message-list li.MuiListItem-root` | scoped class constant, not a fresh testid |
| Raw Json view toggle | `toolkit-raw-json-view-toggle` | |
| Raw Json editor content | `toolkit-raw-json-editor-content` | CodeMirror virtualizes — use `get_raw_json_full()`, not `get_raw_json()`, for payloads >~30 lines |
| Detail title heading | `toolkit-detail-title` | shows "Edit Toolkit" placeholder until real data lands — poll text, don't trust visibility alone |
| Connection-status indicator ("Not Connected"/"Connected!") | `toolkit-connection-status` | `McpAuthStatus.jsx`, wrapping `Typography` — added via `add-data-testid` for ELITEA-1934 (2026-08-02). Live on `automation/testids` (EliteaUI@a467c0ac); **not yet on `main`** — human cherry-pick pending, see PR closure record. |
| Error toast (mcp_sync_tools failure) | `toast-message` | reuses the existing app-wide `Toast.jsx` component (same as `artifacts_page.py`/`skills_list_page.py`/`skill_detail_page.py`) — confirmed live, no new testid needed. Already on `main`. |
| Model selector (name + trigger) in Test Settings panel, `variant="field"` branch | `model-selector-name` (+ `model-selector-button`) | `LLMModelSelector.jsx` — the pair now applies in the `"field"` branch too (previously `"default"`-only), fixed via `add-data-testid` for ELITEA-1937 (2026-08-02, closes #1088). Live on `automation/testids` (EliteaUI@a467c0ac); **not yet on `main`**. `toolkit_test_settings_page.py`'s pre-existing `model_selector_name`/`model_selector_button` `LocatorDescriptor`s are correct as-is. |

## Confirmed testid GAPS (flag to `add-data-testid`, don't build raw fallbacks into new code without a stop+flag reason)

None currently open for this surface — the three gaps found during the
ELITEA-1934/1937 analysis session (connection-status indicator, error toast,
model-selector `"field"` variant / #1088) were all resolved during that same
batch's implementation (2026-08-02); see Confirmed-stable handles above.

## State machine — `TestTools.jsx` (governs BOTH Remote MCP and Artifact toolkit Test Settings panels — same shared component)

Three mutually-exclusive states, driven by `selectedTool` + `hasRealMessages || isRunning`:

1. `!selectedTool` → `TestToolsEmptyState` — "Test toolkit" / "Choose a tool
   from the list to configure parameters and run the test." + the
   `toolkit-test-empty-tool-select` button. **This is NOT the "Welcome!
   Select a tool..." string** — that string exists in `indexChat.helpers.js`
   but isn't reachable from this flow (confirmed via source read).
2. `selectedTool && !hasRealMessages && !isRunning` → `TestToolSettings` — the
   plain form (Tool/Model/params/Run button). **No chat/welcome area exists
   in this state** — don't expect `chat-message-list` to be present yet.
3. `selectedTool && (hasRealMessages || isRunning)` → "Run Results" view —
   `ChatMessageList` (`chat-message-list` testid) replaces the settings form
   entirely (not a side-by-side column). A back-arrow button returns to
   state 2/3 (`handleClearChat`).

**Gotcha for anyone writing/reviewing a Test Settings assertion:** there is
NO state where a tool is selected, nothing has run, AND a welcome/chat message
is visible. If a case's own text implies otherwise, it's very likely
case-text drift (see #1086) — verify against this state machine before
concluding a defect.

## Fixtures

- **Public, auth-free, stable MCP server**: `https://mcp.deepwiki.com/mcp` — 3
  tools (`read_wiki_structure`, `read_wiki_contents`, `ask_question`).
  `read_wiki_structure`/`read_wiki_contents` need only a plain-string
  `repoName`; `ask_question` additionally needs `question` and its `repoName`
  is an `anyOf` (string-or-array) — more complex to automate, prefer the
  other two unless the `anyOf` shape is specifically under test. Confirmed
  live to return real content for `repoName: "AsyncFuncAI/deepwiki-open"`.
- **Guaranteed-unresolvable URL for negative/DNS-failure cases**:
  `https://nonexistent.invalid/mcp` — deterministic DNS failure, no
  flakiness risk from a transient real-domain hiccup.
- Tavily-based fixtures (`tavily_search` etc., referenced in some TMS case
  texts) require an API-key credential not provisioned in this environment —
  substitute the DeepWiki fixture and note it in the AFS Preconditions, same
  precedent set at ELITEA-1933.
