# Test Case: Personal Tokens page loads with correct layout and components

## Metadata
- **TMS ID**: ELITEA-2277
- **Source case**: `.agents/automation/elitea-2277-personal-tokens/cases/ELITEA-2277.md`
  (snapshot; TMS module `settings-personal-tokens`)
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter `priority: medium`). **pytest
  marker: `@pytest.mark.p2`** — project convention TMS `medium` → AFS `l3_`
  filename prefix → pytest `p2` (confirmed against `test-specs/artifacts/l3_
  bucket-name-validation-invalid-name-formats_ELITEA-1811.md`, same `medium`
  label; see `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth).
- Active project has **at least one existing personal token** — the page
  renders `EmptyStatePage` ("No tokens yet") instead of the table when the
  token list is empty (`PersonalTokens.jsx:293-305`), which would make case
  steps 5–6 (table columns, per-row action icons) inapplicable. Confirmed
  live: `${ELITEA_PROJECT_ID}` (399, "Private") already carries 5 persistent
  tokens (`for_ui_tests`, `Levon`, `Marian`, `New`, `uautomate`) — this is
  reused, real leftover test data, not seeded by this case. **Risk** (same
  class as the `settings-notifications` digest's live-data risk): if this
  project's tokens are ever bulk-deleted, the test needs a precondition
  fixture (create one token via UI/API before asserting table layout) —
  flagged for the implementer, not blocking `ready-for-automation` today
  since the data is currently present and stable.
- Active project must **not** be the "Public" project AND must have at least
  one configured LLM model/configuration — `TokensSection`/`TokensTable`'s
  `showDownload` prop (`PersonalTokens.jsx:265`:
  `!!model.configuration_uid && selectedProjectId !== PUBLIC_PROJECT_ID`)
  gates whether the VSCode/JetBrains/eye icons render at all; when false,
  only the trash icon shows (1 icon, not 4). Confirmed live on `${ELITEA_PROJECT_ID}`
  (399, "Private") — a default model auto-resolves from that project's
  configurations, so `showDownload` is `true` and all 4 icons render on
  every observed row.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399` ("Private" project, non-Public, has
  configured models) — confirmed via the sidebar project badge.
- 5 existing personal tokens under this project (see Preconditions) — used
  read-only; this case never creates or deletes a token.

## Test Steps
1. Navigate to `${BASE_URL}/settings/tokens` (bare path — project convention,
   `.agents/testing.md` "page objects call `navigate(...)` with bare paths";
   confirmed reachable directly without clicking through the Settings
   drawer, same pattern as `/settings/notifications` and
   `/settings/project-context`).
   - **Verify**: the tokens table body (testid `token-row`, ≥1 match) becomes
     visible — confirms the page loaded past the loading spinner AND the
     empty-state precondition did not trigger.
2. **Verify** the page header title (testid `personal-tokens-page-title`)
   has exact text `"Personal Tokens"`.
3. **Verify** a search input (testid `personal-tokens-search-input`) is
   present, with placeholder text exactly `"Search tokens..."`.
4. **Verify** an add-token button (testid `personal-tokens-add-button`) is
   present and enabled (button is disabled only while models are still
   fetching or zero configurations exist — neither holds once the page has
   finished loading per step 1's precondition).
5. **Verify** the tokens table header shows **exactly four** columns, via
   the four column-header testids in this exact order: `personal-token-column-header-name`
   ("Token name"), `personal-token-column-header-token` ("Token value"),
   `personal-token-column-header-expires` ("Expiration"),
   `personal-token-column-header-actions` ("Actions") — and assert no fifth
   column-header element exists (`[data-testid^="personal-token-column-header-"]`
   count == 4).
6. For the **first** token row (testid `token-row`, `.first()`):
   - **Verify** exactly 4 action-icon elements are present, matched by
     `[data-testid^="token-action-"]` scoped to that row's actions cell,
     count == 4.
   - **Verify** each of the 4 named testids is individually visible:
     `token-action-preview-button` (eye), `token-action-vscode-button`
     (VSCode), `token-action-jetbrains-button` (JetBrains),
     `token-action-delete-button` (trash).
   - **Verify no console error** was raised by the page load (side-channel
     check — confirmed live: 0 console errors, 0 warnings on this run).

## Expected Results
- Page loads with header "Personal Tokens", a "Search tokens..." input, and
  an add-token button, all in the top-right region per the case's layout
  description.
- Tokens table renders exactly 4 columns: Token name, Token value,
  Expiration, Actions.
- Every visible token row's Actions column shows exactly 4 icons: eye
  (Preview settings), VSCode (Download VScode settings), JetBrains
  (Download Jetbrains settings), trash (Delete token) — confirmed live on
  all 5 existing rows, not just the first.
- No console errors at any step.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Personal Tokens | Target page/section loads successfully | AFS step 1 | `step 1`: `token-row` testid becomes visible | asserted |
| 2 Verify the page header shows "Personal Tokens" | Condition holds as described | AFS step 2 | `step 2`: `personal-tokens-page-title` exact text | asserted |
| 3 Verify a "Search tokens..." input is present in the top right | Condition holds as described | AFS step 3 | `step 3`: `personal-tokens-search-input` visible + placeholder text | asserted |
| 4 Verify a "+" button is present in the top right | Condition holds as described | AFS step 4 | `step 4`: `personal-tokens-add-button` visible + enabled | asserted |
| 5 Verify the tokens table has exactly four columns: Token name, Token value, Expiration, Actions | Condition holds as described | AFS step 5 | `step 5`: 4 named column-header testids + count == 4 | asserted |
| 6 Verify each token row in Actions column shows exactly four icons: eye, VSCode, JetBrains, trash | Condition holds as described | AFS step 6 | `step 6`: count == 4 + 4 named testids visible, on first row | asserted *(live-observed on all 5 rows during exploration; automation asserts the first row per the case's own "each token row" wording read as "the pattern holds," not "iterate every row" — see Axis 2 note)* |
| Expected Final State: Verify each token row in Actions column shows exactly four icons | (restates step 6) | AFS step 6 | `step 6` | asserted *(no separate row needed — identical to step 6)* |

## Axis 2 — Analyst additions
- `step 1` asserts `token-row` visibility as a **precondition proof**, not
  just a navigation check — *added: distinguishes "page loaded, table
  present" from "page loaded, empty state shown instead" (two different
  live code paths in `PersonalTokens.jsx`), which the case text doesn't
  address but materially changes what steps 5–6 can even observe.*
- `step 5`/`step 6` both add an explicit **count assertion** (`== 4`), not
  just presence of the 4 named testids — *added: the case's own wording is
  "exactly four" twice; asserting only presence of 4 named things would pass
  even if a 5th unnamed icon/column also rendered, which is exactly the
  failure mode "exactly" is meant to catch.*
- `step 6` adds a **no-console-error** side-channel check — *added: standard
  practice per `test-case-analysis` § 3 "Check the side channels," confirmed
  live there is none on this build.*
- Row-scope note: case step 6 says "each token row" (plural); this AFS
  automates the **first row** and documents (Preconditions + Expected
  Results) that all 5 observed rows showed the identical icon set during
  live exploration — a full per-row loop is a reasonable Gap-assertion
  extension a future case could add if row-level divergence (e.g. a token
  whose owner lacks delete permission) becomes a real scenario, but nothing
  in the live app suggests per-row divergence exists for these 4 icons
  today (`showDownload` is a single page-level boolean, not per-row).

## Cleanup
None — this case is read-only against existing token data; no entities are
created, modified, or deleted.

## Concrete Handles (discovered during exploration)

All new testids — **none exist yet in this component tree** (confirmed via
`grep -rn "data-testid\|testId" "src/[fsd]/features/settings/ui/personal-tokes/"`
→ zero hits, and no title/search/add-button testid threading exists yet in
the shared `DrawerPageHeader.jsx`). Locator policy is testid-only
(`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy) —
implementer adds all of these via `add-data-testid`.

| Element | File | Recommended testid | How to add |
|---|---|---|---|
| Page header title ("Personal Tokens") | `DrawerPageHeader.jsx` (shared — used by 14 other settings/index pages) — `<Typography variant="headingSmall" ...>{title}</Typography>` | `personal-tokens-page-title` | Thread a new `titleTestId` prop through `DrawerPageHeader` (`data-testid={titleTestId}` on the `Typography`), pass `titleTestId="personal-tokens-page-title"` at the `PersonalTokens.jsx` call site (`renderTokensContent`'s `<DrawerPageHeader title="Personal Tokens" ... />`). Per `.agents/testing.md` "shared components never hardcode feature-scoped testids" — the testid is caller-supplied, not hardcoded in the shared component. |
| Search input ("Search tokens...") | `DrawerPageHeader.jsx` → `Input.SimpleSearchBar` (`src/[fsd]/shared/ui/input/SimpleSearchBar.jsx`) | `personal-tokens-search-input` | `SimpleSearchBar.jsx:59` **already** reads `props['data-testid']` and wires it onto the native `<input>` via `inputProps` — only `DrawerPageHeader.jsx` needs a new `slotProps.searchInput.testId` destructure, passed as `data-testid={testId}` on the `<Input.SimpleSearchBar>` JSX. Call site: `PersonalTokens.jsx`'s `slotProps.searchInput` object gains `testId: 'personal-tokens-search-input'`. |
| Add-token button ("+") | `DrawerPageHeader.jsx` — `<IconButton ... onClick={onAdd}><PlusIcon .../></IconButton>` | `personal-tokens-add-button` | Thread a new `slotProps.addButton.testId` prop through `DrawerPageHeader` (`data-testid={testId}` on the `IconButton`), pass `testId: 'personal-tokens-add-button'` in `PersonalTokens.jsx`'s `slotProps.addButton` object (alongside the existing `onAdd`/`disabled`/`tooltip`/`tourId` keys). |
| Table column headers (4) | `TokensTable.jsx` → `GridTableHeader` (`src/[fsd]/entities/grid-table/ui/GridTableHeader.jsx`) | `personal-token-column-header-name`, `-token`, `-expires`, `-actions` | `GridTableHeader.jsx` **already** accepts a `columnTestIdPrefix` prop and generates `{prefix}-column-header-{field}` per column (confirmed in source, same mechanism `notification-table` would use). `TokensTable.jsx`'s `<GridTableHeader columns={visibleColumns} ... />` call just needs `columnTestIdPrefix="personal-token"` added — no new component code, a call-site wire only (same "cheaper than a real add" pattern as ELITEA-2257's `GridTableRow`/`GridTableBody` `data-testid`). |
| Token table row | `TokensTable.jsx` → `<GridTableRow>` | `token-row` | `GridTableRow.jsx` **already** accepts `'data-testid': dataTestId` (confirmed in source) but `TokensTable.jsx`'s call site doesn't pass one. Add `data-testid="token-row"` (static, one value repeated per row — same pattern as `notification-row` in `notification_center_page.py`'s docstring) to the `<GridTableRow key={row.id} ... />` call. |
| Eye icon ("Preview settings") | `TokensTable.jsx` → `TokenActionsCell` — `<IconButton variant="elitea" size="small" color="tertiary" onClick={onPreview}><OpenEyeIcon .../></IconButton>` | `token-action-preview-button` | `data-testid="token-action-preview-button"` directly on the `IconButton` JSX. |
| VSCode icon ("Download VScode settings") | `TokensTable.jsx` → `TokenActionsCell` — `<Box sx={styles.downloadBox} onClick={onVsCodeDownload}><VsCodeIcon .../></Box>` | `token-action-vscode-button` | `data-testid="token-action-vscode-button"` directly on the `Box` JSX. |
| JetBrains icon ("Download Jetbrains settings") | `TokensTable.jsx` → `TokenActionsCell` — `<Box sx={styles.downloadBox} onClick={onDownload}><JetBrainsIcon .../></Box>` | `token-action-jetbrains-button` | `data-testid="token-action-jetbrains-button"` directly on the `Box` JSX. |
| Trash icon ("Delete token") | `TokensTable.jsx` → `TokenActionsCell` — `<DeleteEntityButton name={token.name} onDelete={onClickDelete} title="Delete token" ... />` | `token-action-delete-button` | `DeleteEntityButton.jsx` **already** accepts a `testId` prop (`data-testid={testId}` on its wrapping `Box`, confirmed in source) — `TokenActionsCell` just needs `testId="token-action-delete-button"` added to the existing `<DeleteEntityButton>` call. |

Not touched by this case (no testid requested — scope discipline,
`.agents/role-overrides.md` "touches" = actually invoked on this test's
executed path):
- `SettingsPreview` panel content (opens on eye-icon click; this case only
  verifies the icon's presence, never clicks it)
- `GeneratedTokenDialog` (the create-token flow; this case never clicks the
  add button)
- `GridTablePagination` controls (5 rows fit on one page; case doesn't
  exercise pagination)
- Token name/value/expiration **cell content** testids (case verifies
  column *headers*, not per-cell values — no assertion on token name/value/
  expiration text is in scope here)

## Network Behavior
- `GET /api/v2/auth/token/` — token list fetch (`useTokenListQuery`), fires
  on page mount. Confirmed live: 200 OK, 0 console errors/warnings on this
  run.
- `GET` model/configurations list (`useListModelsQuery`) — fires on mount,
  drives `showDownload` gating (see Preconditions). Not asserted directly by
  this case; its *effect* (all 4 icons visible) is what step 6 asserts.

## Known Defects Found During Exploration
None. All 6 case steps reproduce as authored on this build: header text,
search placeholder, add button, exactly 4 table columns, and exactly 4
action icons per row (confirmed on all 5 existing rows, not just the first)
— see embedded evidence below.

Evidence: `test-results/screenshots/ELITEA-2277-step-06-page-layout-and-actions-icons.png`
(viewport screenshot — header "Personal Tokens", search input, add button,
4-column table, 5 rows each showing 4 action icons).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: no existing page object covers Settings → Personal Tokens.
  Create `automation/pages/personal_tokens_page.py` (new file) — do not bolt
  onto `user_profile_settings_page.py` (different route family,
  `/user-settings/profile` + `/settings/personalization`, pre-policy
  `fallback=`-based tech debt; do not pattern-match its locator style).
- Column-header count assertion: `page.locator('[data-testid^="personal-token-column-header-"]')`
  — Playwright supports attribute-prefix CSS selectors directly; no need for
  4 separate `LocatorDescriptor`s plus a manual count loop, though each
  individual header can also be its own `LocatorDescriptor(testid=...)`
  field for the per-column text assertions.
- Action-icon count assertion: scope the prefix-selector to the first row —
  `self.first_token_row.locator('[data-testid^="token-action-"]')` — via a
  `LocatorDescriptor` for `token-row` combined with `.first()` and `.locator()`
  chaining (this chaining is locating WITHIN an already-testid-scoped
  element, which is the sanctioned pattern for dynamic/count-based checks,
  not a raw free-floating selector).
- Wait strategy: wait for `token_row` (`.first()`) to be visible before any
  column/action assertions — no `page.wait_for_timeout`, per
  `.agents/conventions.md`.
