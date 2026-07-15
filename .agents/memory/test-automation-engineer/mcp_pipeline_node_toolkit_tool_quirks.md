---
name: MCP pipeline node Toolkit/Tool quirks (implementer)
description: BaseToolNode.jsx testid gating pattern (nodeType-conditional), MUI Select DOM/role quirks (testid on wrapper not combobox, role=option not menuitem, zero-width-space empty display), list_all_toolkits() empty-list environment quirk, and the API-only recipe for provisioning a real-tool-list MCP toolkit + pre-configured pipeline MCP node (from ELITEA-1954)
type: feedback
---

## Context

ELITEA-1954 (MCP Integration in Pipeline — change MCP node Toolkit and Tool).
`BaseToolNode.jsx` is shared by Function/Agent/MCP pipeline nodes; only the MCP
node's Toolkit/Tool/Input/Output selects + Input-mapping Value fields needed
testids for this case.

## Testid gating pattern for shared node components

When a shared component (`BaseToolNode`) serves multiple node types but only
one type is under test, gate the testid at the PARENT that knows the node
type, not inside the child select component itself:

```jsx
// BaseToolNode.jsx
const isMcpNode = nodeType === FlowEditorConstants.PipelineNodeTypes.Mcp;
<FlowEditorSelect.ToolSelect ... data-testid={isMcpNode ? 'pipeline-mcp-node-toolkit-select' : undefined} />
```

Keeps other node types (Function/Agent) untagged — correct per this project's
"testid scope is load-bearing" policy (`.agents/testing.md` § Locator policy).

## MUI `<Select>` DOM/role gotchas (native Select, NOT the Popper search-widget pattern)

- **`data-testid` passed to `<Select>` lands on the OUTER wrapper div**
  (`.MuiInputBase-root`), not the inner clickable combobox div
  (`#simple-select-{Label}`, `.MuiSelect-select`). `get_by_test_id(x).click()`
  still works — the wrapper's bounding box fully contains the combobox.
- **Menu items have `role="option"`, NOT `role="menuitem"`.**
  `.claude/rules/mui-patterns.md`'s "use role=menuitem not option" guidance is
  about the OTHER dropdown pattern (Popper-based search widget — agent
  toolkit add, etc.), a different component. Conflating the two silently
  matches zero elements — verify live before assuming.
- **Empty-select display text is `​` (zero-width space), not `""`.**
  Same gotcha as `user_profile_settings_page.get_current_voice`. Strip it
  before asserting reset-to-empty:
  `(el.text_content() or "").replace("​", "").strip()`.

## `ToolkitAPI.list_all_toolkits()` / `list_toolkits()` returns empty on this environment

Confirmed via BOTH Bearer token and real cookie session: `GET
tools/prompt_lib/{project}` returns `{"rows": [], "total": 0}` regardless of
params, even though individual toolkits genuinely exist and `GET
tool/prompt_lib/{project}/{id}` works fine for them. A real API/environment
quirk, not a client bug. **Don't rely on listing to discover a known
pre-existing toolkit by name** — use a fixed id (config setting, e.g.
`remote_github_mcp_toolkit_id`), not a search.

**Update (ELITEA-1944, 2026-07-15): this quirk also breaks UI list pages,
not just the API client.** `/mcps/all` (and presumably any other list page
backed by the same `tools/prompt_lib/{project}` endpoint) renders from that
same list endpoint — confirmed live that a toolkit created via raw
`ToolkitAPI.create_toolkit()` (201, individually GET-able by id) NEVER
appears on `/mcps/all`, and with zero visible MCPs the app auto-redirects
`/mcps/all` -> `/mcps/create`. **Any test that needs to seed MCP/toolkit
test data so it's visible in the UI must create it through the UI form
flow** (e.g. `McpFormPage.select_remote_mcp_type()` /
`.fill_name()`/`.fill_url()`/`.save_and_wait_for_created()`), never via
`ToolkitAPI.create_toolkit()` — the raw-API path is fine for delete-by-id
cleanup (unaffected by the quirk) but not for creating data a UI test will
later read back.

## Provisioning an MCP toolkit with a REAL, non-empty Tool dropdown — API-only recipe

A plain `create_toolkit(type="mcp", settings={"url": ...})` produces a toolkit
whose pipeline-node Tool dropdown NEVER populates — `GET
toolkit_available_tools/prompt_lib/{project}/{id}` returns `{"tools": [],
"args_schemas": {}}` even for known-good toolkits. Root cause
(`useFunctionInputMapping.hooks.js`): for any toolkit where `isMcpToolkit()`
is true, `isSchemaResolved` short-circuits to `true` and the Tool dropdown's
options come straight from `settings.selected_tools` /
`settings.available_mcp_tools` — the live-fetch path is never hit for MCP
toolkits.

Recipe (`ToolkitAPI.sync_mcp_tools` + `create_remote_mcp_toolkit` in
`api/client.py`):

1. `POST mcp_sync_tools/prompt_lib/{project}?await_response=true` with body
   `{"url": ..., "timeout": 60, "ssl_verify": true}` — **omit `sid`/
   `mcp_tokens`/`toolkit_type` entirely rather than passing `null`; explicit
   `null` 500s.** Returns `{"result": {"success": true, "tools": [{"name",
   "description", "inputSchema"}, ...]}}`. This is the same endpoint the UI's
   "Load Tools" button calls (`EliteaUI/src/api/toolkits.js`).
2. Create the toolkit with `settings.selected_tools = [tool names]` and
   `settings.available_mcp_tools = [{"label", "value", "args_schema"
   (=inputSchema), "description"}, ...]` baked in at creation time.

## Attaching toolkits to a pipeline + pre-configuring an MCP node — API-only recipe

`versions[0].tools` in the pipeline create/update payload requires **FULL
toolkit JSON objects**, not `{"id": ...}` references — confirmed empirically
(400 "Missing 'type'", then "Missing 'settings'" when only partial fields are
given). Fetch via `ToolkitAPI.get_toolkit(id)`, pass the full dicts.

The MCP node's YAML `toolkit_name` field must equal `cleanString(toolkit.name)`
— strips everything except `[a-zA-Z0-9_.-]`, replaces `.` with `_`
(`EliteaUI toolkits.helpers.js: genToolkitName`/`cleanString`), e.g. `"Remote
Github"` → `"RemoteGithub"`. `PipelineAPI.create_pipeline_with_mcp_node()`
wraps this whole flow (YAML node + `tools` list) in one call.

Input-mapping YAML/testid keys are the RAW tool-schema parameter names
(`repoName`, `question` — lowercase/camelCase), NOT the case text's
capitalized display labels ("RepoName", "Question" — those are just
`capitalizeFirstChar(key)` applied for display, computed in
`InputMapping.jsx`).

## Review fix-pass addendum (2026-07-15, PR #513 CHANGES_REQUESTED)

A fresh adversarial reviewer caught 4 raw-handle/testid-gap violations that
slipped past the original implementer session:

- `open_mcp_node_toolkit_select`/`open_mcp_node_tool_select` waited on raw
  `page.locator('[role="listbox"]')`, and `get_open_listbox_option_names`
  enumerated via raw `[role="listbox"] [role="option"]` — both fixed by a
  new `SELECT_OPTION_PREFIX = '[data-testid^="select-option-"]'` constant
  (prefix-match sibling of the already-used `SELECT_OPTION` template). Safe
  because MUI portals only one listbox to `<body>` at a time, so a
  page-wide prefix match unambiguously enumerates the currently-open one.
- The "Input mapping (required N)" accordion heading (`InputMapping.jsx` →
  `BasicAccordion.jsx`) had **zero data-testid anywhere** — a genuine gap,
  not a missed-existing-handle case. `BasicAccordion.jsx` had no way to
  testid an individual accordion-section heading at all before this.

**New reusable seam: per-accordion-item `testId`.** Added an optional
`testId` field to each `items[]` entry consumed by `BasicAccordion.jsx`,
applied as `data-testid={testId}` on `StyledAccordionSummary` — additive,
`undefined` for the ~19 other callers that don't pass it (no other caller
touched). `InputMapping.jsx` threads this through as a new
`requiredHeadingTestId` prop, applied only to the *required*-count
accordion item (not the optional one) — mirrors the existing
`valueTestIdPrefix` passthrough pattern. `BaseToolNode.jsx` wires it with
the same `isMcpNode` gate as the other 4 MCP testids:
`requiredHeadingTestId={isMcpNode ? 'pipeline-mcp-node-input-mapping-heading' : undefined}`.
Any future case needing to assert a specific accordion section (required
vs optional, or a specific index) can reuse this `items[i].testId` seam
instead of `get_by_text` on the title string.

**Git worktree gotcha**: cherry-picking a new commit onto an
already-existing local branch name (one previously used by an earlier
`git worktree add <branch>` for the same case, now removed) fails with
`fatal: a branch named '...' already exists` even though no worktree
currently has it checked out. Fix: cherry-pick onto detached HEAD in a
fresh worktree, then `git branch -f <name> HEAD` to force the local ref
forward, `git checkout <name>`, then push — no need to delete/recreate the
branch.

## Reusable API additions

- `ToolkitAPI.get_toolkit(id)`, `sync_mcp_tools(url, timeout, ssl_verify)`,
  `create_remote_mcp_toolkit(name, description, url, tools)`
- `PipelineAPI.create_pipeline_with_mcp_node(name, description, tools,
  toolkit_name=, tool=, input_mapping=, node_id=)`
- `config.py: remote_github_mcp_toolkit_id` (default 3) — the environment's
  fixed pre-existing "Remote Github" MCP, unreachable via listing.
