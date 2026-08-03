# Test Case: Chat – Edit Generated Table in Canvas Mode – Open Editor and Verify Table Display

## Metadata
- **TMS ID**: ELITEA-2086
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private")
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — all 11 case steps executed live against the real app, twice (reproducible across two independent AI generations). No product defect found. The entire table-canvas component tree (`MarkdownTableBlock.jsx`, `Canvas.jsx`, `CanvasEditHeader.jsx`, `MarkdownTableEditor.jsx`, `EditingPlaceholder.jsx`) has **zero `data-testid` anywhere** — confirmed via full-file reads and `git grep -c "data-testid\|testId"` returning 0 against both `origin/main` and `origin/automation/testids`. This case needs substantial `add-data-testid` work; see § Concrete Handles.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation with an LLM — satisfied via the existing `conversation_id` fixture (`navigate_to_chat(conversation_id=...)`); do NOT drive a raw `+Chat` click + short wait (known hang risk, issue #1085, already documented in `_surface.md` § In-chat "Create New X" canvas family).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test
- **New conversation** via the `conversation_id` fixture; cleaned up by the fixture's own teardown.
- Message text is the case's own literal Test Data: `"generate a table of top 10 IT companies"`.

## Test Steps

1. Navigate to Chats and open a conversation.
   - **Verify**: `ChatPage.navigate_to_chat(conversation_id=...)`; conversation view displayed (message input visible).
2. Send the message "generate a table of top 10 IT companies".
   - **Verify**: `ChatPage.send_message()`, then `wait_for_ai_response(initial_count=...)` + `wait_for_message_content_stable()` (NOT a fixed sleep — generation took 7–8s live, both runs). A markdown table renders inside the AI answer.
3. Verify the table shows columns such as Rank, Company, HQ, Primary Focus Areas.
   - **Verify**: confirmed live, **both runs**: columns are `Rank`, `Company`, `Headquarters`, `Primary Business` (+ a 5th column `Market Cap (Approx.)` in one run). **Case-text drift, not a defect**: the case says "HQ"/"Primary Focus Areas" (paraphrase) and "such as" (illustrative, not exhaustive) — live text is `Headquarters`/`Primary Business`, and a 5th column may or may not appear. **Column set is AI-generated and not fixed** — assert on the *presence* of a stable core (`Rank`, `Company`, a headquarters-type column, a business/focus column), never an exact fixed column list or count.
4. Verify the table shows company data (e.g. Microsoft, Apple, Alphabet, Amazon, etc.).
   - **Verify**: confirmed live, both runs: 10 data rows; company set both times included Apple, Microsoft, Alphabet, Amazon (plus NVIDIA, Meta, Tesla, …). **Row order is AI-generated and NOT stable across generations** (run 1: Apple first; run 2: Microsoft first) — assert by set-membership (a company name is *present somewhere* in the Company column), never by a fixed row index.
5. Locate the pencil/edit icon in the top right corner of the table.
   - **Verify**: confirmed live — a small pencil-style `IconButton` (MUI `EditIcon`, `MarkdownTableBlock.jsx`) sits in a toolbar `Box` aligned `justifyContent: flex-end` directly above the table (i.e., top-right of the table block, matching the case's description), with an MUI `Tooltip` reading exactly `"Edit table"`. **NO `data-testid`** — see § Concrete Handles for the current interim handle and the testid to add.
6. Click the pencil/edit icon.
   - **Verify**: confirmed live, both runs — canvas panel opens on the right with heading text exactly `"Edit table"` (a plain `Typography` inside `CanvasEditHeader.jsx`, **no testid**). Simultaneously the LEFT (conversation) pane shows an `EditingPlaceholder` reading `"Table editing..."` in place of the table (case step 2 of the sibling case ELITEA-2087 covers this indicator in detail — same component, confirmed here too).
7. Verify the canvas displays the table in an editable grid format with all columns and rows.
   - **Verify**: confirmed live — an MUI X `DataGrid` (`.MuiDataGrid-root`) renders inside the canvas with all 10 rows and all columns from step 3, plus a leading checkbox-selection column (`data-field="__check__"`, MUI's built-in `GRID_CHECKBOX_SELECTION_COL_DEF`).
8. Verify sortable column headers with sort icons are present.
   - **Verify**: confirmed live — `.MuiDataGrid-columnHeader[data-field="<field>"]` elements are present for every column (standard MUI DataGrid, sortable by default, no explicit `sortable={false}` set anywhere in `MarkdownTableEditor.jsx`). **Locator caveat, confirmed live**: `.MuiDataGrid-columnHeader`'s own `innerText` extraction returned empty strings both runs — the visible label text lives one level deeper, at `.MuiDataGrid-columnHeaderTitle` (or read the `data-field` attribute directly, which is more stable than any text extraction). Implementer: use `data-field`, not header text, to identify a column.
9. Verify row checkboxes appear on the left for selecting rows.
   - **Verify**: confirmed live — leftmost column, `data-field="__check__"`, one `<input type="checkbox">` per row (MUI DataGrid default `checkboxSelection`).
10. Verify pagination controls show "1-10 of 10" and "Rows per page: 50".
    - **Verify**: confirmed live, both runs, exact text: `"Rows per page: 50"` and `"1–10 of 10"` (MUI DataGrid's built-in `.MuiTablePagination-root` footer — `pageSizeOptions`/default page size configured in `MarkdownTableEditor.jsx`, not custom-built).
11. Verify a "Download as xlsx" button appears at the bottom right.
    - **Verify**: confirmed live — a `SplitButton` (`src/components/SplitButton.jsx`, shared with the un-edited table's own download control in `MarkdownTableBlock.jsx`) reading `"Download as xlsx"` with a dropdown chevron for other formats (`downloadTableOptions`), bottom-right of the grid.

## Expected Results
- All 11 steps pass cleanly as specced above, reproduced across two independent live runs with different AI-generated content. No product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation with LLM | — | step 1 | `conversation_id` fixture + `navigate_to_chat()` | asserted |
| 1 Navigate to Chats, open conversation → Conversation view displayed | conversation displayed | step 1 | message input visible | asserted |
| 2 Send message → table generated | table rendered | step 2 | markdown table element present in last AI message | asserted |
| 3 Verify columns → table structure correct | columns present | step 3 | column header set (by `data-field`, core subset) | asserted — case-text drift noted, not a defect |
| 4 Verify company data → table data present | data present | step 4 | company-name set membership, 10 rows | asserted |
| 5 Locate pencil/edit icon → visible | edit icon visible | step 5 | icon visible in table toolbar | asserted — testid needed |
| 6 Click pencil icon → canvas opens, heading "Edit table" | canvas opens | step 6 | canvas heading text == "Edit table" | asserted — testid needed |
| 7 Verify editable grid, all columns/rows | grid shown | step 7 | `.MuiDataGrid-root` row/column count == source table | asserted |
| 8 Verify sortable headers with sort icons | sortable headers | step 8 | `data-field` header presence (DataGrid default-sortable) | asserted |
| 9 Verify row checkboxes | checkboxes visible | step 9 | `data-field="__check__"` checkbox count == row count | asserted |
| 10 Verify pagination "1-10 of 10" / "Rows per page: 50" | pagination correct | step 10 | exact text match | asserted |
| 11 Verify "Download as xlsx" button | download button visible | step 11 | `SplitButton` text == "Download as xlsx" | asserted |
| Expected Final State: canvas opens with sortable headers, checkboxes, pagination, download | — | steps 6–11 | — | asserted |
| Pass/Fail: "editor does not open or missing required elements" is FAIL condition | — | all steps | side-channel console/network checks throughout | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 3/4 explicitly assert AI-generated content by **set membership / presence**, not fixed values or row order — *added: the underlying content is non-deterministic across generations (confirmed live, two runs produced different row orders and a differing 5th column), a fixed-value assertion would be flaky by construction, not a test bug when it fails.*
- Step 6 additionally asserts the `EditingPlaceholder` appears in the conversation pane the instant the canvas opens — *added: this is the shared precondition state ELITEA-2087 depends on ("following ELITEA-2086"), worth confirming here too since it's observed on this case's own executed path.*
- No new console errors or failed network requests observed across either full run of this case.

## Cleanup
1. Delete the created conversation via the `conversation_id` fixture's own teardown (or `conversation_api.delete_conversation(id)` if driven manually).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep -c "data-testid\|testId"` on both `origin/main` and `origin/automation/testids` — **all rows below returned 0 on both**.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Table's own "Edit table" pencil icon | **NO TESTID** | needs-adding | `testid needed: chat-table-edit-button` on `MarkdownTableBlock.jsx`'s `IconButton` (the `onEdit` branch). Current interim (pre-testid) reachable handle, observed live both runs: `[aria-label="Edit table"] button` — do **not** ship this as the production locator; it is not a literal `data-testid` and its origin (MUI `Tooltip` behavior) was not independently verified as stable. |
| Canvas heading (dynamic: "Edit table"/"Edit diagram"/"Edit code") | **NO TESTID** | needs-adding | `testid needed: chat-canvas-title` on `CanvasEditHeader.jsx`'s title `Typography`. Same shared chrome used by ELITEA-2087 (this same case) and ELITEA-2088 (diagram) — one testid, dynamic text content asserted per case. Same shape already precedented by `agent-canvas-title`/`mcp-canvas-title` (ELITEA-2085/2166). |
| Canvas close (X) button | **NO TESTID** | needs-adding | `testid needed: chat-canvas-close-button` on `CanvasEditHeader.jsx`'s close `IconButton` (first button in the header row, no aria-label, no text). Same shared chrome as above. Not exercised by THIS case's steps (ELITEA-2087 closes it) — do not add unless this case's own test actually calls it. |
| Conversation-pane editing indicator ("Table editing..."/"Diagram editing...") | **NO TESTID** | needs-adding | `testid needed: chat-canvas-editing-indicator` on `EditingPlaceholder.jsx`'s wrapping `Box`. Shared component (also used by ELITEA-2087/2088) — text content (`title` prop) is the per-case assertion signal. |
| Editable DataGrid — container | **NO TESTID** | needs-adding | `testid needed: chat-table-canvas-grid` on `MarkdownTableEditor.jsx`'s DataGrid wrapper `Box`. **Declared improvisation (canon gap)**: MUI X `DataGrid` is a third-party grid widget whose per-cell/per-row DOM (`.MuiDataGrid-cell[data-field=...]`, `.MuiDataGrid-row`, `.MuiDataGrid-columnHeader[data-field=...]`) is library-rendered, not raw app JSX — closely analogous to `.agents/testing.md` § Locator policy's #579 sanctioned-exception categories (ReactFlow subtree / CodeMirror per-line nodes) but not a literal match to either (DataGrid is neither an "editor" nor entirely outside app control — each cell DOES render app data). Recommend treating it the SAME way: add ONE real testid on the DataGrid's containing `Box`, then scope all `data-field`/`.MuiDataGrid-row` raw selectors as children of that testid parent, exactly like `mcp_form_page.py:121`'s CodeMirror pattern. **Flagging for reviewer/lead sign-off** per the Declared-improvisation protocol — this is not a 1:1 precedent match. |
| DataGrid cells (per-column) | raw `data-field` attribute (MUI-provided, not custom) | n/a | `.MuiDataGrid-cell[data-field="Company"]` etc. — scope inside `chat-table-canvas-grid` per the declared improvisation above. `data-field` values match the table's own generated column names (non-fixed — read them at runtime, don't hardcode "Company"/"Rank" as guaranteed). |
| Row checkboxes | raw `data-field="__check__"` (MUI built-in) | n/a | Same scoping as DataGrid cells above. |
| Pagination footer | **NO TESTID** | needs-adding | `testid needed: chat-table-canvas-pagination` on the `.MuiTablePagination-root` container (MUI-default text content is the actual assertion — "Rows per page: 50" / "1–10 of 10" — the testid is only needed to scope the query when multiple grids could theoretically be on screen). |
| "Download as xlsx" split button | **NO TESTID** | needs-adding | `testid needed: chat-table-download-button` (trigger) via a caller-supplied `testId` prop threaded to `SplitButton.jsx` (shared component, `src/components/` — per the shared-component testid rule, cannot hardcode a feature name inside `SplitButton` itself). Same component also renders the non-edit table's own download button (`MarkdownTableBlock.jsx`) — only add the testid at the ONE call site this case's test touches (`MarkdownTableEditor.jsx`'s usage, inside the canvas), per canon ruling #511 (scope = the test's own executed path). |

## Network Behavior
- No dedicated network call opens the canvas (client-side state transition only, confirmed live — no new request fires on the pencil-icon click in either run).
- AI generation itself: standard chat WebSocket flow, no anomalies observed.
- No 4xx/5xx observed at any point in this session's execution of this case's own 11 steps.

## Known Defects Found During Exploration
None.

## Blocked Steps
None. All 11 case steps were executed and observed end-to-end live, twice.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Do not assert exact table content or row order** — AI-generated per the case's own prompt, confirmed non-deterministic live across two runs (different first row, different 5th-column presence). Assert structure (column-set superset, row count == 10, company-name set membership) instead.
- **Wait strategy**: `wait_for_ai_response()` + `wait_for_message_content_stable()` (existing `ChatPage` methods) after sending the message — table generation took 7–8s live both runs, well within the existing defaults; no fixed sleep needed.
- **Shared chrome across this case's family**: `chat-canvas-title` / `chat-canvas-close-button` / `chat-canvas-editing-indicator` are the SAME three testids ELITEA-2087 (same case's continuation) and ELITEA-2088 (mermaid) will also need — add them ONCE, they are not per-case duplicates. Coordinate with whichever case's implementation lands first; do not re-request them.
- The DataGrid-scoping declared improvisation (`chat-table-canvas-grid` + scoped `data-field` selectors) needs explicit reviewer sign-off since it is not a 1:1 match to an existing sanctioned exception — see § Concrete Handles.
