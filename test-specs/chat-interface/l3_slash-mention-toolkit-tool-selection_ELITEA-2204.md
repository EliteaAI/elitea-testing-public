# Test Case: Chat – Slash Commands – Selecting a Toolkit From '/' Shows Its Available Tools

## Metadata
- **TMS ID**: ELITEA-2204
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), batch `approved-next50`, cluster with ELITEA-2202/2203
- **Status**: **ready-for-automation** — executed live end-to-end (Artifact toolkit configured with exactly 4 `selected_tools`, added as a conversation participant, `/` → click toolkit → verify tools list → click a tool → verify composer text). Matches the case's Objective and Pass/Fail criteria, with **one case-text drift found** (CLARIFICATION, not a defect — see § Known Defects / Coverage Map). The tools-list container/items carry **zero testids today** — `add-data-testid` work required (see § Concrete Handles).
- **Cluster note**: analysed together with ELITEA-2202 (empty state) and ELITEA-2203 (participant filtering) in one live session — three **separate AFS files**, see ELITEA-2202's AFS Cluster note for the full rationale. This case is the deepest of the three (two-phase interaction: toolkit selection → tool selection).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation with the target toolkit already added as a participant (reuse ELITEA-2203's toolkit-add flow, or add directly via API + UI participant-add for isolation).

## Test Data

### CLARIFICATION — case's expected tool name is stale (filed, see § Known Defects)
The case's Test Data table lists expected tools as `index_data, list_collections, search_index, stepback_search_index`. Live exploration (and a pre-existing error log in this repo's own `automation/reports/archive/junit_20260722_212653.xml`, from before the suite's `create_artifact_toolkit()` factory was fixed) confirms **`list_collections` is not a valid tool name** — the backend rejects it with `"the following tools are no longer available: 'list_collections'. Please remove them to continue."` The correct, currently-valid tool name for the same capability is **`list_indexes`** (confirmed live: rendered in the tools list exactly as `list_indexes`, and it's what the suite's existing `ToolkitAPI.create_artifact_toolkit()` factory already uses, `automation/api/client.py:1642-1670`). Automate against `list_indexes`, not `list_collections`; case-text clarification filed per § Known Defects.

### generate-per-test (toolkit with an EXACT, case-matching tool set — not the full default factory list)
The existing `artifact_toolkit` fixture (`automation/fixtures/data_fixtures.py:493-534`) hardcodes `create_artifact_toolkit()`'s full 16-tool `selected_tools` list — using it as-is would show 16 tools, not the 4 the case expects. This case needs a **new, narrower fixture** (or a direct `toolkit_api.create_toolkit(toolkit_type="artifact", ...)` call inline) with `settings.selected_tools` restricted to exactly:
```python
["index_data", "list_indexes", "search_index", "stepback_search_index"]
```
plus the same `pgvector_configuration`/`embedding_model`/`bucket` fields `create_artifact_toolkit()` already sets (an Artifact toolkit still needs a bucket — reuse the existing `artifact_bucket` fixture for that part). Confirmed live: the tools list renders EXACTLY these 4, in this order, matching the `selected_tools` array order — no more, no less (`SlashSuggestionList.jsx`'s `availableTools` reads straight from `toolkitDetails.settings.selected_tools` for non-MCP toolkits, no client-side reordering).
- The toolkit must be added as a conversation **participant** (same mechanism as ELITEA-2203) before it's selectable from the `/` dropdown.

## Test Steps

1. Click into the message input, type `/`, then click the toolkit's card in the dropdown (reuse ELITEA-2203's dropdown-item click).
   - **Verify**: the message field shows `/{toolkit_name}` (confirmed live: `/banana-745480`, composer's `input_value()` read directly — no trailing space at this point, `onSlashSelectToolkit`'s replacement is exactly `'/' + toolkit.name`).
   - **Verify**: a NEW list appears titled **`{toolkit_name} available tools`** (confirmed live, CSS-uppercased on screen, DOM text title-case: `"banana-745480 available tools"` — the toolkit's own name is the literal prefix, so assert via the fixture-generated name, not a hardcoded string, and lowercased).
2. Verify the tools list — confirmed live, exactly 4 rows in this order: `index_data`, `list_indexes` (see § Test Data clarification — NOT `list_collections`), `search_index`, `stepback_search_index`.
3. Click `index_data` from the tools list.
   - **Verify**: the message field updates to `/{toolkit_name}/index_data ` (confirmed live: `/banana-745480/index_data` with a **trailing space** — `onSlashCommitMention`'s replacement is `` `${mentionToken} ` `` — assert the trailing space is present, it's part of the confirmed mechanism, not incidental).

## Expected Results
- Selecting a toolkit from the `/` dropdown replaces the typed fragment with `/{toolkit_name}` and opens a second list titled `{toolkit_name} available tools`.
- The tools list shows exactly the toolkit's configured `selected_tools`, in configuration order.
- Selecting a tool replaces the fragment with `/{toolkit_name}/{tool_name} ` (trailing space).
- No console errors during the sequence (confirmed live — none observed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Type '/' and click 'banana' in dropdown | Message field shows '/banana'; tools list 'BANANA AVAILABLE TOOLS' appears | AFS step 1 | `message_input.input_value() == f"/{toolkit_name}"`; tools-list-container `.text_content()` contains `f"{toolkit_name} available tools"` | asserted |
| 2 Verify tools: index_data, list_collections, search_index, stepback_search_index | All tools listed | AFS step 2 | tools-list-container: exactly 4 item-testid matches, names == `["index_data", "list_indexes", "search_index", "stepback_search_index"]` | asserted *(re-based on `list_indexes`, not `list_collections` — CLARIFICATION, see § Known Defects)* |
| 3 Click 'index_data' from tools list | Message field updates to '/banana/index_data' | AFS step 3 | `message_input.input_value() == f"/{toolkit_name}/index_data "` (trailing space asserted) | asserted |

### Axis 2 — Analyst additions
- Step 1 additionally asserts the exact composer VALUE (not just "contains banana") both before and after tool selection, including the confirmed trailing-space behavior after tool selection — *added: the case's Pass criteria say "message field not updated" as a FAIL condition, which implies the exact string matters, not just a substring; the trailing space is a real, confirmed part of the mechanism (`onSlashCommitMention`) and would be silently swallowed by a substring-only check.*
- No console errors during the two-phase selection sequence — *added: standard side-channel check, none observed.*

## Cleanup
- Conversation deleted by the `conversation_id` fixture's teardown.
- Toolkit + bucket deleted by their fixtures' teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Message input | `[data-testid="chat-message-input"]` | **on-main ✓** | pre-existing — read `.input_value()` for both composer-state assertions |
| Slash-mention dropdown container (toolkit-selection phase) | `testid needed: slash-mention-list` | needs-adding (shared handle — see ELITEA-2202's AFS, implement once) | Used to click the toolkit item (same container/items as ELITEA-2203) |
| Per-item card in the toolkit-selection dropdown (dynamic) | `testid needed: slash-mention-item-{project_id}_{toolkit_id}` | needs-adding (shared handle — see ELITEA-2203's AFS) | Click target for step 1 |
| Available-tools list container | `testid needed: slash-mention-tool-list` | needs-adding | `ToolList.jsx` (`EliteaUI/src/[fsd]/features/chat/ui/slash-suggestion-list/ToolList.jsx`) — zero testids today (confirmed via full-file read + `git grep -c` empty on both `origin/main` and `origin/automation/testids`). Static, single instance (one `ToolList` mounts at a time, `phase === 'tool'`) — add directly on `ToolList.jsx:17`'s outer `Box`, no prop-threading needed (this component is NOT shared with any other feature — confirmed via `git grep -rl "ToolList"` inside `EliteaUI/src`, only `SlashSuggestionList.jsx` imports it). Used to read the `"{toolkitName} available tools"` header via `.text_content()` — no separate header testid needed. |
| Per-tool item (dynamic) | `testid needed: slash-mention-tool-item-{tool_name}` | needs-adding | `ToolItem.jsx` — zero testids today (same file-scope confirmation as above; `ToolItem` is ONLY imported by `ToolList.jsx`). Add via `ToolList.jsx:38-48`'s `<ToolItem key={tool.name} ... />` call passing a new `testId={` `slash-mention-tool-item-${tool.name}` `}` prop threaded into `ToolItem.jsx`'s root `Box` (line ~17). Tool names in this environment (`index_data`, `list_indexes`, `search_index`, `stepback_search_index`) are already safe CSS-selector identifiers (snake_case, no spaces/special chars) — no escaping concerns. Template constant for the page object: `SLASH_MENTION_TOOL_ITEM = '[data-testid="slash-mention-tool-item-{}"]'`. |

## Network Behavior
- Selecting a toolkit triggers `GET` toolkit-details (`useToolkitsDetailsQuery`, `{projectId, toolkitId}`) to resolve `settings.selected_tools` — confirmed live via the brief loading state (`isToolsFetching`) before the 4 tools render; not independently captured at the network-tab level this pass (case doesn't require network-level assertions, UI-level tool-list content is sufficient).
- Selecting a tool: no network call — pure client-side text replacement in the composer.

## Known Defects Found During Exploration
- **Case-text drift (CLARIFICATION, not a defect) — filed [#1125](https://github.com/EliteaAI/elitea-testing-public/issues/1125)**: the case's Test Data table names an expected tool `list_collections`, which is **not a valid/available tool name** in this environment — confirmed live (tools list shows `list_indexes` instead) and corroborated by a pre-existing error in this repo's own `automation/reports/archive/junit_20260722_212653.xml` (`"the following tools are no longer available: 'list_collections'. Please remove them to continue."`, dated before the suite's own `create_artifact_toolkit()` factory was fixed to use `list_indexes`). Live product is correct (per the reverse-masking guard, `test-case-analysis` § Classify findings) — the case text is stale. Labelled `question`, title `[Clarification][ELITEA-2204] ...`, per this repo's existing convention (issues #1114/#1119/#1122). Automated against the corrected `list_indexes` name; this case is NOT blocked by the finding.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- **New fixture needed** (or an inline `toolkit_api.create_toolkit()` call, implementer's call on whether it's reusable enough to warrant a shared fixture) — an Artifact toolkit with `selected_tools` restricted to exactly `["index_data", "list_indexes", "search_index", "stepback_search_index"]`, backed by a bucket (reuse `artifact_bucket`). Do NOT reuse `artifact_toolkit` as-is — its factory hardcodes 16 tools, which would make this case's "exactly 4 tools" assertion false against the live default.
- Reuse ELITEA-2203's new `add_toolkit_participant_via_slash_menu(project_id, toolkit_id)` page-object method (see that AFS's Automation Hints) to get the toolkit into the conversation as a participant — this case's own steps start from "toolkit already a participant, type `/`", same precondition shape.
- Composer-value assertions: use `message_input.input_value()` (already used elsewhere in `chat_page.py`, e.g. around token-count parsing) — do not use `.text_content()`/`.inner_text()` on the input, those don't reflect the current controlled-input value.
- Wait strategy: after clicking a toolkit item, wait for `slash_mention_tool_list` (new `LocatorDescriptor`) to become visible before reading its contents — the toolkit-details query has a brief `isToolsFetching` loading state (confirmed live, not long enough to need a generous timeout, but real).
