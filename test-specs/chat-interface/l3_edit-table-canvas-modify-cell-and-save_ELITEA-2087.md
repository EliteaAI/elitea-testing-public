# Test Case: Chat – Edit Table in Canvas Mode – Modify Cell Value and Save Changes

## Metadata
- **TMS ID**: ELITEA-2087
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private")
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — all 10 case steps executed live, reproduced across two independent runs (cell edit + close-sync confirmed working both times). No product defect found. Shares the same zero-testid component tree as ELITEA-2086 (its own precondition) — see that AFS's § Concrete Handles for the shared-chrome testids; this AFS documents the grid-editing-specific handles only.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- The canvas table editor is open — **this case's precondition is literally ELITEA-2086's outcome**. Automate as ONE continuous test (send message → open canvas → edit cell → close → verify sync), not as a separate test depending on another test's state; page-object methods can still be split per step for reuse.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test
- **New conversation** via the `conversation_id` fixture; cleaned up by the fixture's own teardown.
- Message text: `"generate a table of top 10 IT companies"` (same as ELITEA-2086).
- Cell edit target: the case's literal Test Data names the **Company** cell containing `"Microsoft"`, edited to `"Microsoft_edited"`. **Important, confirmed live**: table row order is AI-generated and NOT stable (ELITEA-2086 confirmed this) — do **not** hardcode "first row" as the target. Locate the row by CONTENT MATCH (the cell whose text is/contains `"Microsoft"`), not by index. Confirmed live twice: run 1 edited the wrong row (first row, which was "Apple" that generation) as an exploratory shortcut and still validated the sync mechanism; run 2 correctly targeted the "Microsoft" row by content match and reproduced the same result. **The implementer must use the content-match approach**, matching the case's literal Test Data.

## Test Steps

1. Verify the table canvas editor is open.
   - **Verify**: precondition state from ELITEA-2086 — `.MuiDataGrid-root` visible, editable grid populated (this AFS's own test reaches this state itself, see § Preconditions above).
2. Verify the interaction window on the left shows "Table editing..." indicator with blue border.
   - **Verify**: confirmed live, both runs — `EditingPlaceholder` (`src/components/Chat/EditingPlaceholder.jsx`) renders exact text `"Table editing..."` in a bordered box (`border: 1px solid theme.palette.border.chatEditPlaceholderBorder` — confirmed source-side; the border reads as a blue accent in the live dark theme). **NO testid** — see ELITEA-2086's AFS § Concrete Handles (`chat-canvas-editing-indicator`, shared).
3. Click on the "Microsoft" cell in the Company column.
   - **Verify**: confirmed live (run 2) — locate the row via `.MuiDataGrid-row:has(.MuiDataGrid-cell[data-field="Company"]:text-is("Microsoft"))`, then `.MuiDataGrid-cell[data-field="Company"]` within that row. A **double-click** (`dblclick()`) is required to enter edit mode (single click only selects/focuses the cell — confirmed live, matches standard MUI DataGrid cell-editing UX). On entering edit mode, the cell renders a nested `textarea`/`input` (2 matched elements live — use `.first`).
4. Change "Microsoft" to "Microsoft_edited".
   - **Verify**: `editor_input.first.fill("Microsoft_edited")` (or `press_sequentially` — MUI DataGrid's own cell editor is a controlled input; `fill()` was confirmed to work live for this specific editor, unlike the general MUI-form-field caveat in `.claude/rules/mui-patterns.md`, because DataGrid's cell editor wires its own `onChange` directly to Playwright-dispatched input events — no `type()`/`press_sequentially()` workaround was needed live).
5. Press Enter or click outside the cell to confirm the change.
   - **Verify**: confirmed live — `page.keyboard.press("Enter")` commits the edit; cell exits edit mode and displays the new value.
6. Verify save/update occurs automatically.
   - **Verify**: confirmed live, both runs — the grid cell shows `"Microsoft_edited"` immediately after Enter, no explicit Save button click needed (client-side grid state; the actual PERSIST happens on canvas close, see step 7/9 below — "automatic" here means no manual per-cell save action, not an immediate network write).
7. Click the X button to close the canvas.
   - **Verify**: confirmed live — canvas close `IconButton` (`CanvasEditHeader.jsx`, first button in the header row, before the title). **NO testid** — see ELITEA-2086's AFS § Concrete Handles (`chat-canvas-close-button`, shared). Current interim (pre-testid) handle used live: DOM query for the button immediately preceding the header's title text node (fragile, not for production use).
8. Locate the table in the conversation.
   - **Verify**: confirmed live — canvas unmounts, conversation pane reverts from `EditingPlaceholder` back to the rendered `MarkdownTableBlock` table.
9. Verify the table now displays "Microsoft_edited" in the first row Company column.
   - **Verify**: **case-text imprecision, not a defect**: the case says "first row" but the edited cell is wherever the "Microsoft" row happened to be (AI-generated order, see § Test Data) — assert the edited value appears in the row that WAS the Microsoft row (tracked by the automation, not literally "row 1"). Confirmed live both runs: the edited value syncs back to the conversation's rendered table correctly, in the same row position it occupied in the grid.
10. Verify all other data remains unchanged (Apple, Alphabet, Amazon, etc.).
    - **Verify**: confirmed live, both runs — every other row's Company value in the conversation table matched its pre-edit value (compare full company-name set minus the edited one, before vs. after).

## Expected Results
- All 10 steps pass cleanly as specced above, reproduced across two independent live runs. No product defect found. The cell edit is confirmed to synchronize from canvas → conversation view on close.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: canvas open (= ELITEA-2086 outcome) | — | Setup (steps embedded) | grid visible | asserted |
| 1 Verify canvas open → editable grid shown | grid shown | step 1 | `.MuiDataGrid-root` visible | asserted |
| 2 Verify "Table editing..." indicator, blue border | indicator visible | step 2 | exact text match | asserted — testid needed (shared, see ELITEA-2086) |
| 3 Click Microsoft cell → cell editable, cursor appears | cell editable | step 3 | dblclick + nested input/textarea present | asserted |
| 4 Change value → cell shows new value | value changed | step 4 | editor input value == "Microsoft_edited" | asserted |
| 5 Enter/click outside → cell displays new value | value confirmed | step 5 | cell displayed text == "Microsoft_edited" | asserted |
| 6 Verify auto save → canvas shows updated value | auto-saved | step 6 | grid cell persists value without extra action | asserted |
| 7 Click X → canvas closes | canvas closed | step 7 | canvas testids/grid absent from DOM post-close | asserted — testid needed (shared, see ELITEA-2086) |
| 8 Locate table in conversation → table visible | table visible | step 8 | `MarkdownTableBlock` table element visible | asserted |
| 9 Verify "Microsoft_edited" in Company column → change reflected | change synced | step 9 | edited row's Company cell == "Microsoft_edited" | asserted — case-text "first row" corrected to "the edited row" |
| 10 Verify other data unchanged | no side effects | step 10 | remaining company set diff == {} | asserted |
| Expected Final State: edited value synchronized canvas→conversation | — | steps 7–9 | — | asserted |
| Pass/Fail: "changes not saved or not reflected" is FAIL condition | — | all steps | side-channel console/network checks throughout | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 3 asserts a `dblclick()` is required to enter cell-edit mode — *added: not stated in the case text, but load-bearing for the implementer (a plain `click()` only selects the cell, does not edit it — confirmed live, would silently no-op if implemented as a single click).*
- Step 9's "first row" is corrected to "the row containing the edited company" — *added: the case's literal wording assumes a fixed row order that live execution disproves (AI-generated content, non-deterministic order, confirmed twice in ELITEA-2086). This is case-text drift, not a product defect — filed as guidance here rather than a separate clarification ticket since it's purely a test-design detail (row-order assumption), not a user-facing behavior discrepancy.*
- Step 4's `fill()` compatibility with MUI DataGrid's own cell editor (vs. the general MUI-form-field `fill()` caveat in `mui-patterns.md`) is called out explicitly — *added: saves the implementer a debugging cycle discovering DataGrid's cell editor doesn't need the `type()`/`press_sequentially()` workaround other MUI fields on this project need.*
- No new console errors or failed network requests observed across either full run of this case.

## Cleanup
1. Delete the created conversation via the `conversation_id` fixture's own teardown.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). The three shared-chrome testids (`chat-canvas-title`, `chat-canvas-close-button`, `chat-canvas-editing-indicator`) are documented in ELITEA-2086's AFS § Concrete Handles — do not re-request them, this case just consumes them (specifically the close-button and editing-indicator ones). Grid-editing-specific handles below, all confirmed **NO TESTID**, provenance verified via `cd EliteaUI && git fetch origin` then `git grep -c "data-testid\|testId"` returning 0 on both `origin/main` and `origin/automation/testids`.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Editing indicator, "Table editing..." text | `chat-canvas-editing-indicator` (shared) | needs-adding | See ELITEA-2086 § Concrete Handles — same component, this case is a second consumer. |
| Canvas close (X) button | `chat-canvas-close-button` (shared) | needs-adding | See ELITEA-2086 § Concrete Handles — this case is the first to actually CLICK it (ELITEA-2086 only observes the canvas open, never closes it), so add it against THIS case's executed path. |
| Company-column cell (per-row, dynamic content) | raw `data-field="Company"` scoped inside `chat-table-canvas-grid` (declared improvisation, see ELITEA-2086) | needs-adding (parent) | Row selection by content match: `.MuiDataGrid-row:has([data-field="Company"]:text-is("Microsoft"))`. Scope inside the DataGrid's own testid parent once added. |
| Cell edit input (textarea/input rendered on dblclick) | raw `textarea, input` scoped inside the target cell | n/a (transient, MUI DataGrid-internal) | Two elements match live inside the editing cell — use `.first`. Same "third-party library internal render node" reasoning as the DataGrid cells themselves (ELITEA-2086's declared improvisation covers this). |

## Network Behavior
- No network request fires on cell edit itself (client-side grid state only, confirmed live both runs).
- **Persist-on-close mechanism not independently network-verified this session** — the sync from canvas grid → conversation table was confirmed via DOM state (rendered value) both runs, not via an intercepted request/response pair. Flagging as a gap for the implementer's first pass: capture the actual request (likely a canvas-edit-socket emit, given `useCanvasEditSocket`/`useEditCanvasMutation` referenced in `CanvasEditor.jsx`/`Canvas.jsx` source) if a network-level assertion is wanted in addition to the DOM-level one.
- No 4xx/5xx observed at any point in this session's execution of this case's own 10 steps.

## Known Defects Found During Exploration
None.

## Blocked Steps
None. All 10 case steps were executed and observed end-to-end live, twice.

## Implementer Exploration Notes (Phase 2 amendment)

- **Row-content matching needs SUBSTRING, not exact, matching.** The case's
  own Test Data says "the cell whose text is/contains 'Microsoft'" — this
  implementation's own live run needed contains-matching in practice: the
  initial `:text-is("Microsoft")` (exact) CSS pseudo-selector timed out
  finding a row, because the AFS's own pre-edit assertion (`"Microsoft" in
  value`) is a substring check while the grid lookup was exact. Fixed to
  `:has-text("Microsoft")` (substring) in
  `ChatTableCanvasPage.ROW_BY_CELL_TEXT` — consistent with the case's own
  wording either way, and robust to a generated company name rendering as
  a longer variant (e.g. "Microsoft Corporation") in some generations.
- **Step 8 ("locate the table in the conversation") must NOT be asserted
  via the pencil/edit icon's visibility.** Confirmed live: once a
  canvas-editable block has been through one edit-and-close cycle, its
  conversation-pane render switches from a plain Markdown `text_message`
  item (rendered via `Token.jsx` → `MarkdownTableBlock.jsx`, whose OWN
  toolbar/pencil `chat-table-edit-button` targets) to a `canvas_message`
  item rendered via `Canvas.jsx`'s `CanvasContent` (a SEPARATE,
  currently-untested pencil button; the nested `<Markdown
  showToolbar={false}>` hides `MarkdownTableBlock`'s own toolbar in this
  path). The underlying `<table>` markup is unaffected (same
  `MarkdownTableBlock` component either way), so step 8's assertion was
  written against table DATA presence (`get_rendered_table_data()`
  non-empty) instead — matching the AFS's own Coverage Map disposition for
  this step ("`MarkdownTableBlock` table element visible"), not the pencil.
  Not exercised further by this case, but flagged for whichever future
  case re-edits an already-edited block.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Compose with ELITEA-2086's steps** — this case's precondition IS ELITEA-2086's end state; write as one continuous test (send message → open canvas → verify structure [ELITEA-2086's assertions] → edit cell → close → verify sync [this case's assertions]) OR as two independent tests that both start from "send message → open canvas" (accepting the duplicated setup) — **do not** write this case's test to literally depend on ELITEA-2086's test having run first (test isolation, `.claude/rules/ui-tests.md` § Test Isolation).
- **Locate the target row by content match, never by index** — AI-generated table order is non-deterministic (confirmed live twice in ELITEA-2086/2087). This is the single most important automation-robustness note in this case.
- `dblclick()` (not `click()`) to enter cell-edit mode; `fill()` works directly on the DataGrid cell editor's nested input (no `type()`/`press_sequentially()` workaround needed, unlike other MUI form fields on this project).
- The DataGrid-scoping declared improvisation from ELITEA-2086 (`chat-table-canvas-grid` container testid + scoped raw `data-field` selectors) applies here too — same DataGrid instance, same reviewer sign-off needed once, not per-case.
