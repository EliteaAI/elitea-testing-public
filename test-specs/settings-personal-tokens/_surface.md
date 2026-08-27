# Settings → Personal Tokens surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → Personal
Tokens surface (`/settings/tokens`, renders `PersonalTokens.jsx`). Not a
substitute for execution — verify a handle as you use it. One writer at a
time; first confirmed by: qa-engineer analyst, ELITEA-2277, 2026-08-05.
Extended by: qa-engineer analyst, ELITEA-2280, 2026-08-05 (create-token flow
+ delete-confirmation cleanup flow). Extended by: qa-engineer analyst,
ELITEA-2286, 2026-08-05 (Name-field client-side validation: `useAutoBlur`
mechanism, reliable field-clearing technique, `beforeunload` nav-blocker
gotcha). Extended by: qa-engineer analyst, ELITEA-2278/2279/2287 cluster,
2026-08-27 (table sorting semantics + the sort-direction trap; search-box live
filtering; the two distinct empty states; the in-page-`fetch` console trap) —
see the three sections at the end.

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

## Name-field client-side validation (`CreatePersonalToken.jsx`, ELITEA-2286)
- `TOKEN_NAME_PATTERN = /^[a-zA-Z0-9_-]*$/` (line 18), enforced via a yup
  `.matches()` schema with message `"Only alphanumeric characters,
  underscore and hyphen are allowed"` + `.required('Name is required')`.
  A space fails the same branch as any other disallowed character — no
  separate "space" handling in the code, confirmed live.
- **No explicit blur/Tab needed to see the error or the disabled Generate
  button appear.** `Input.InputBase` (`enableAutoBlur` prop, default
  `true`) wraps `onChange` so `useAutoBlur.js` fires a REAL
  `document.activeElement.blur(); .focus()` cycle ~10ms after every
  keystroke — this is what sets Formik's `touched.name` (plain
  `handleChange` alone never touches a field). The error paragraph +
  `isGenerateDisabled` (`!name || (touched.name && Boolean(errors.name))`)
  both reflect within about one render tick of typing an invalid char.
  Automation should just `expect(...)`-poll, no manual blur step.
- **Field-clearing gotcha: `Control+a` is UNRELIABLE on this input**
  (confirmed live) — the same `useAutoBlur` refocus cycle above can race a
  `Control+a` select-all keypress and silently reset the cursor to
  position 0 before the shortcut lands, so a `Control+a` + `Backspace`
  sequence was observed removing only the leading character instead of the
  whole field. **Reliable technique, confirmed live:** `press("Home")` then
  `press("Shift+End")` (keyboard-only line-select) immediately followed by
  `press_sequentially(new_text)` — typing over the active selection
  replaces it in one step.
- **`beforeunload` dialog on navigate-away with unsaved changes** —
  `useNavBlocker` (`CreatePersonalToken.jsx:84-86`, keyed off `hasChanged`)
  blocks a raw `page.goto()`/reload once any form field differs from its
  initial value; confirmed live (hit directly while re-navigating during
  exploration — the navigation call hung until the dialog was handled).
  Any case that needs to leave this page mid-form needs
  `page.on("dialog", ...)` handling or should use the page's own
  close-icon/back-button flow instead of a raw navigation.
- **Validation-error paragraph testid** (`create-personal-token-name-error`)
  — did NOT exist before ELITEA-2286 (confirmed by source read of
  `CreatePersonalToken.jsx` as of ELITEA-2280/2284's sessions, which never
  touched the Name field's error state). `Input.InputBase`'s `helperText`
  prop accepts any `ReactNode` — wrap the existing `getNameHelperText()`
  call in a small element carrying the testid at the `CreatePersonalToken.jsx`
  call site; zero `InputBase.jsx` change needed, same "wire an existing
  generic prop" pattern as every other handle on this page.

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

## Empty state — reachability, and what it actually renders (ELITEA-2250, 2026-08-24)
- **Tokens are USER-scoped, not project-scoped** — `useTokenListQuery({ skip:
  !user.personal_project_id })` takes no project id (`PersonalTokens.jsx:32`).
  Verified live: switching projects does not change the list. So the empty state
  needs a *user* with zero tokens; there is no project trick.
- Live inventory **unchanged since 2026-08-05** (re-verified 2026-08-24): 5 tokens —
  `for_ui_tests` (never), `Levon` (never), `Marian` (**expired**), `New` (**expired**),
  `uautomate` (never). The two expired rows **cannot be recreated** (create only
  offers future expirations) and ELITEA-2284's merged
  `test_expired_token_shows_expired_icon_and_label` reads its `expired` branch off
  them → deleting all tokens to reach the empty state is irreversible destruction,
  not a precondition. `auth_state_user_b` `pytest.skip`s on localhost by design
  (`session_fixtures.py:133`). ELITEA-2250 is therefore parked **blocked**.
- **What the empty branch renders** (source-confirmed, `PersonalTokens.jsx:296-306`):
  `EmptyStatePage` with title `No tokens yet` (testid **`empty-state-title`**, already
  on `main`), description `Create your first API token.`, an illustration `<img>`, and
  a `Create` button (`BaseBtn` + plus icon) whose `onCreateClick` navigates to
  `/settings/create-personal-token`. The Create button and description have **no
  testid** — they need caller-supplied props on the shared `EmptyStatePage`
  (`src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx`), which is used by
  many empty states app-wide.
- **The empty branch returns BEFORE `DrawerPage`** — in it, `personal-tokens-page-title`,
  `personal-tokens-search-input`, `personal-tokens-add-button`, the table and all
  action icons **do not exist**. Assert their absence, not their invisibility.
- **Mount timing**: a `CircularProgress` (`role="progressbar"`, no testid) covers the
  page for ~2-2.5 s on every load before either branch renders (measured 2026-08-24,
  500 ms sampling: rows appear at 2.5 s). Wait on the branch, never on a delay.

## Table sorting — `useTableSort`, and the direction trap (ELITEA-2279, 2026-08-27)
- `TokensTable.jsx` uses the shared `useTableSort({ defaultField: 'name',
  defaultDirection: 'asc' })`. **The table arrives already sorted name-ascending**, so
  the FIRST click on the Token-name header flips to **descending** — the toggle is
  `prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'`
  (`grid-table/lib/hooks/useTableSort.hooks.js:11-16`). Confirmed live with real clicks.
  Any case text claiming "first click = ascending" is stale (ELITEA-2279 steps 2-5).
- Sortable columns are exactly **`name` and `expires`** (`TOKENS_COLUMNS`,
  `TokensTable.jsx:27-32`); `token` and `actions` are not — their header cells have
  `cursor: default` and render **no** sort icon.
- **Sort-icon testids already exist, for free**: `columnTestIdPrefix="personal-token"`
  makes `GridTableHeader` emit BOTH `personal-token-column-header-{field}` and
  `personal-token-sort-icon-{field}` (sortable columns only). So
  `personal-token-sort-icon-name` / `-expires` are live handles — **no testid work for a
  sorting case**. (This is the orphan-testid situation tracked by issue #1705;
  ELITEA-2279 is the first case to reference them on an executed path.)
- **Expiration sort semantics:** `expires` is `null` for "Never" tokens and a date string
  otherwise. `sortData` puts `null` **last in asc, first in desc**
  (`useTableSort.hooks.js:45-47`). So the stable, data-independent invariant is
  *dated rows before Never rows (asc), reversed (desc)* — assert that, not a literal name
  order. Live asc: `Marian, New, Levon, uautomate, for_ui_tests`; desc: exact reverse
  grouping.
- String comparison is **case-insensitive** (`.toLowerCase()`, lines 50-53) — with
  `Levon`/`Marian`/`New` capitalised and `for_ui_tests`/`uautomate` not, a
  case-**sensitive** `sorted()` expectation fails against a correct product.
- ⚠️ **Never assert the sort-arrow rotation.** It is a CSS `transform` behind a
  `transition: transform 0.2s ease` (`GridTableHeader.jsx:132-137`); captured
  mid-animation live as `matrix(0.907747, 0.419517, ...)`. Same for the active-column
  `opacity 1 vs 0.7` cue, which `&:hover` also changes. **Row order is the observable.**
- Sorting is **client-side** — no request fires on a header click. Wait on the reordered
  DOM, never on a response.

## Search box — live filtering, and the two empty states (ELITEA-2287, 2026-08-27)
- `PersonalTokens.jsx:31,248-255` → `DrawerPageHeader` `slotProps.searchInput`
  (`onChangeSearch: setSearch`) → `SimpleSearchBar`'s native `onChange`. **Per-keystroke,
  no Enter, no submit button, no debounce.** This is NOT the Enter-activated
  `SearchBar.jsx` of issue #44 — don't apply that lesson here.
- Filter (`TokensSection.jsx:19-22`):
  `token.name.toLowerCase().includes(search.toLowerCase())` — substring, **name only**
  (never the token value or expiration), **case-insensitive**. Live: `AUTO` → `uautomate`.
- **Escape clears the field** (`SimpleSearchBar.jsx:28-33` → `DrawerPageHeader.jsx:37`
  `onChangeSearch('')`). `Control/Meta+A` + `Backspace` also works reliably here — the
  digest's "`Control+a` is unreliable" warning is scoped to the **create-token Name
  field** (`useAutoBlur`); `SimpleSearchBar` is a plain MUI `InputBase` with no auto-blur.
- The input is `autoFocus` (100 ms `setTimeout` after mount, `SimpleSearchBar.jsx:39-46`).
- **TWO DIFFERENT EMPTY STATES — do not conflate:**
  1. **Zero tokens exist** → `PersonalTokens.jsx` returns `EmptyStatePage`
     (`empty-state-title` = "No tokens yet") **before** `DrawerPage`; the page header,
     search box, table and rows all cease to exist.
  2. **Search matches nothing** → the page header and search box **stay**;
     `GridTableContainer.isEmpty` renders the message `"No tokens"` and the four
     `personal-token-column-header-*` **unmount**. `empty-state-title` is **absent**
     (confirmed live). ⇒ **Searching cannot be used to fake state 1** (the ELITEA-2278 /
     2250 shortcut trap).
  `GridTableContainer` has no testid on that message and takes no testid prop — a
  `emptyMessageTestId` caller-supplied prop is the compliant add if a case needs it.
- **Sort state survives a search clear** (observed: expiration-desc order retained after
  Escape). Compare name **sets** across a clear, not ordered lists, unless the sort is
  also pinned.

## Gotcha — an ad-hoc in-page `fetch()` to the API poisons the console (2026-08-27)
`page.evaluate(() => fetch('/api/v2/auth/token/'))` from a Playwright/MCP session does
**not** carry the app's RTK-Query auth headers on localhost. The dev proxy redirects it to
`https://dev.elitea.ai/forward-auth/auth_oidc/login?target_to=...`, which is then blocked
by CORS — emitting **two console errors** (a CORS error + `net::ERR_FAILED`) that look
exactly like a product defect to a "no console errors" assertion. The page itself was
clean (0 product console errors) across this entire session. To read the token payload,
capture the app's own `GET /auth/token/` response via `page.expect_response`, never a
hand-rolled `fetch`.
