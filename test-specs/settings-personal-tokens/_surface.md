# Settings → Personal Tokens surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → Personal
Tokens surface (`/settings/tokens`, renders `PersonalTokens.jsx`). Not a
substitute for execution — verify a handle as you use it. One writer at a
time; first confirmed by: qa-engineer analyst, ELITEA-2277, 2026-08-05.
Extended by: qa-engineer analyst, ELITEA-2280, 2026-08-05 (create-token flow
+ delete-confirmation cleanup flow).

## Create-token flow (`/settings/create-personal-token`, `CreatePersonalToken.jsx`)
- The add-button (`personal-tokens-add-button`) does NOT open an inline
  dialog — confirmed live: it navigates to a separate route,
  `/settings/create-personal-token`. Full page: title "New Token" (via the
  same `DrawerPageHeader` + `titleTestId` mechanism as "Personal Tokens"),
  Name input (Formik, validates `[a-zA-Z0-9_-]` only, required), Expiration
  period = `SingleSelect` (`measure`, default `"days"`, options `never/days/
  weeks/hours/minutes` — `EXPIRATION_MEASURES` in `src/common/constants.js:485`)
  + a numeric value input (`expiration`, default `30` —
  `DEFAULT_TOKEN_EXPIRATION_DAYS`, `constants.js:484`). Generate button
  disabled until name is non-empty and valid.
- Generate → `POST /api/v2/auth/token/` (200, body
  `{name, expires: {measure, value}}`) → opens `GeneratedTokenDialog` (NOT a
  route, an in-page MUI `Dialog`) showing title "New token generated!",
  attention-styled warning text, the entered name above the full token
  string, and a Copy button. Also triggers an immediate `GET
  /api/v2/auth/token/` refetch, so the table is current before the dialog
  even closes.
- Copy button: `handleCopy(token)` (writes to OS/browser clipboard) +
  `toastInfo('The token has been copied to the clipboard.')` + button text
  flips to "Copied!" (disabled ~5s, `COPY_DISABLED_DURATION`).
- Dialog close: a `Box`-wrapped `CancelIcon` with `onClick={onClose}` (no
  accessible role/name — testid is the only viable handle) — closing
  triggers `onCancel()` → `navigate(-1)`, landing back on `/settings/tokens`.
  **Escape key does the same** (the dialog's own `onKeyDown` handles
  `Escape` → `onClose`, and `Enter` → triggers Copy) — either is valid, AFS
  specs the icon click as primary since it doesn't depend on focus state.
- **Clipboard-read gotcha (costly, flag forward):**
  `page.evaluate("navigator.clipboard.readText()")` against a browser
  context that was NOT created with the `clipboard-read` permission granted
  hangs indefinitely — it does not reject, it just never resolves (silently
  waiting on a permission prompt that headless/MCP contexts never show).
  This bit an exploratory MCP session directly (a bare `browser_evaluate`
  call to read the clipboard hung for the full 1800s idle timeout). The
  pytest suite's `context` fixture already grants `["clipboard-read",
  "clipboard-write"]` at context creation (`automation/conftest.py:279`) —
  so the pytest suite itself is fine — but ANY ad-hoc/scratch browser
  session (Playwright CLI, a manual script, a different MCP browser
  instance) attempting the same clipboard read will hang unless it also
  grants the permission at context-creation time. Never diagnose this as a
  product regression before checking the calling context's granted
  permissions first.

## Table row cell content (`TokensTable.jsx` `renderCell`)
- Name cell: `Text.EllipsisTypography` showing `row.name` verbatim.
- Value cell: `Text.EllipsisTypography` showing `'...' + row.token.slice(-4)`
  (masked, last 4 chars of the actual token string).
- Expiration cell: `ExpiryInDays` sub-component, 4 mutually-exclusive
  branches by `calculateExpiryInDays(expires)`: `>7d` → green `SuccessIcon`
  (`theme.palette.status.published`, confirmed hex `#2BD48D`) + `"in N
  days"`; `1-7d` → amber `AttentionIcon` (`status.onModeration`) + `"in N
  days"`; `expiryInDays === -1` (no expiry / "Never") → green `SuccessIcon`
  + `"Never"`; else → gray `RemoveIcon` (`icon.fill.disabled`) + `"Expired"`.
  **Update (ELITEA-2284, 2026-08-05): the testid is now IN PLACE on all 4
  branches** — `token-expiration-status` + `data-expiration-state`
  (`active|warning|never|expired`), confirmed in
  `TokensTable.jsx` and wired in `automation/pages/personal_tokens_page.py`
  (`TOKEN_EXPIRATION_STATUS_SELECTOR`, `get_row_expiration_status(row,
  state=...)`). `active` state is exercised by the merged
  `test_personal_token_create_and_verify.py` (ELITEA-2280) Step 12;
  `expired` state is exercised by its ELITEA-2284 extension
  (`test_expired_token_shows_expired_icon_and_label`). `warning`/`never`
  states remain unexercised by any test as of this session — flag if a
  future case needs them. **No live stable data currently exhibits the
  `active` state without test-created mutation** — every persistent
  non-expired token in the live project (399) has no expiry ("Never"); only
  a freshly-created token (finite expiration) shows `active`/"in N days".
- `EllipsisTypography` and `BaseBtn`/plain MUI `Button` all spread unknown
  props (including `data-testid`) straight through to the underlying DOM
  node — for these, a `data-testid` can be added directly at ANY call site
  without touching the shared component's source at all. Same is true of
  `SingleSelect` (already accepts a `data-testid` prop, wires it onto both
  the Select root and `SelectDisplayProps` as `${id}-combobox`) and
  `Input.InputBase`'s native `<input>` via its existing `inputProps` object
  (same mechanism `SimpleSearchBar` already uses, per the ELITEA-2277 entry
  above) — check for one of these "already-generic" mechanisms before
  assuming a shared component needs a code change for a new testid.

## Delete-confirmation flow — zero testid work needed (shared, pre-existing)
`DeleteEntityButton` → `Modal.DeleteEntityModal` (`src/[fsd]/shared/ui/modal/
DeleteEntityModal.jsx`) already ships with a FULL testid set, confirmed live
in this exact flow: `delete-confirm-dialog` (root), `delete-confirm-title`,
`delete-confirm-message`, `delete-confirm-name-input` (only rendered when
`shouldRequestInputName` — true by default; deleting a personal token
requires typing its exact name before the confirm button enables),
`delete-confirm-cancel-button`, `delete-confirm-button`. Reusable as-is by
ANY future case that needs to delete-and-confirm something built on this
shared modal — check here before requesting new testids for a delete flow.

## Route & component tree
- `/settings/tokens` (bare path, `APP_PREFIX` empty on localhost) routes to
  `TokensSettings` = `src/[fsd]/pages/settings/PersonalTokens.jsx` via
  `ProtectedRoutes.jsx:352-353`. Reachable directly, no drawer-click needed —
  same pattern as `/settings/notifications` and `/settings/project-context`.
- Component tree: `PersonalTokens.jsx` → `DrawerPageHeader` (shared, title +
  search + add-button) + `TokensSection` → `TokensTable.jsx` (built on the
  shared `grid-table` components, same family as `NotificationTable.jsx`) +
  `SettingsPreview` (opens in a `react-split` pane on eye-icon click) +
  `GeneratedTokenDialog` (opens via a separate route, `CreatePersonalToken.jsx`,
  on add-button click — `onAddPersonalToken` navigates to
  `RouteDefinitions.CreatePersonalToken`, doesn't open an inline modal).

## Three page states (important — case authors/testers must account for these)
1. **Loading** (`isFetching || isFetchingTokens`): a `CircularProgress` only.
2. **Empty** (`tokens.length === 0`): `EmptyStatePage` ("No tokens yet" /
   "Create your first API token") — the table, its columns, and the 4 action
   icons DO NOT EXIST in this state. A case asserting table layout needs at
   least one token present first.
3. **Populated** (`tokens.length > 0`): the table renders, per below.

## `showDownload` gating — the icon-count precondition
`TokensSection`'s `showDownload` prop = `!!model.configuration_uid &&
selectedProjectId !== PUBLIC_PROJECT_ID` (`PersonalTokens.jsx:265`). This is
a **single page-level boolean**, not per-row — every row shows the same set
of icons. When `true` (default model resolved + non-Public project): all 4
icons (eye, VSCode, JetBrains, trash) render on every row. When `false`
(Public project, or zero model configurations): only the trash icon renders
(1 icon). Confirmed live on `${ELITEA_PROJECT_ID}` (399, "Private") —
`showDownload` is `true`, all 5 existing rows show all 4 icons identically.

## Live data available (Private project / `${ELITEA_PROJECT_ID}` = 399)
5 persistent personal tokens observed 2026-08-05: `for_ui_tests`, `Levon`,
`Marian` (expired), `New` (expired), `uautomate`. Real leftover test data,
not a fixture — same risk class as `settings-notifications`'s live-history
dependency: if bulk-deleted, a test relying on "table has rows" precondition
needs its own setup (create a token via UI/API first). Prefer reading this
existing data over seeding for read-only layout assertions.

## Testid status — ZERO in the personal-tokes component tree (confirmed 2026-08-05)
`grep -rn "data-testid\|testId" "src/[fsd]/features/settings/ui/personal-tokes/"`
→ no hits. `DrawerPageHeader.jsx` (shared across 14+ settings pages) also has
NO testid threading today for title/search/add-button — any case touching
those needs new props added (see below), not a hardcoded testid in the
shared file.

## Reusable shared-component testid mechanisms (cheaper than a real add)
Two `grid-table` primitives already accept testid props that `TokensTable.jsx`
simply doesn't wire yet — same "wire an existing prop" pattern documented in
`test-specs/settings-notifications/_surface.md`:
- `GridTableHeader` accepts `columnTestIdPrefix` → generates
  `{prefix}-column-header-{field}` per column. Confirmed in source
  (`GridTableHeader.jsx`).
- `GridTableRow` accepts `'data-testid': dataTestId` (static, one value
  repeated per row — confirmed in source, `GridTableRow.jsx`).
- `DeleteEntityButton` accepts a `testId` prop (`data-testid={testId}` on its
  wrapping `Box`) — confirmed in source (`DeleteEntityButton.jsx`), same
  component used across the app's other delete-with-confirmation flows.
- `SimpleSearchBar` (`src/[fsd]/shared/ui/input/SimpleSearchBar.jsx:59`)
  already reads `props['data-testid']` and wires it onto the native
  `<input>` via `inputProps` — but `DrawerPageHeader.jsx` doesn't forward
  `slotProps.searchInput.testId` to it yet (a `DrawerPageHeader` prop-thread
  gap, not a `SimpleSearchBar` gap).

## `DrawerPageHeader.jsx` gaps (shared component, used by 14+ settings pages)
No `titleTestId` prop, no `slotProps.addButton.testId` prop, no
`slotProps.searchInput.testId` forwarding — all three need adding. Since
this is a SHARED component (`.agents/testing.md` § "shared components never
hardcode feature-scoped testids"), the fix is caller-supplied testid props,
not a hardcoded value. Once added, every OTHER page built on
`DrawerPageHeader` (`SecretsContent`, `ProjectGeneralContent`,
`AIProvidersContent`, `Users.jsx`, `EnvironmentSettings.jsx`, indexes pages,
etc.) can reuse the same props — future cases on those surfaces should check
this digest / grep the component before re-requesting the same prop-thread.

## Gotchas
- The add-button's `onAdd` handler **navigates to a separate route**
  (`RouteDefinitions.CreatePersonalToken`, `/settings/create-personal-token`
  presumably) — it does NOT open an inline dialog on this page. A future
  case that clicks "+" should expect a navigation, not a modal.
- `TOKENS_COLUMNS` (`TokensTable.jsx`) is a static 4-entry config array
  (`name`, `token`, `expires`, `actions`) — no responsive column-hiding logic
  observed for this table (unlike some other grid-table consumers); a
  narrower/mobile viewport was not tested live, flag if a future case needs
  responsive-breakpoint coverage.
- Console: 0 errors, 0 warnings on page load with 5 populated rows.
