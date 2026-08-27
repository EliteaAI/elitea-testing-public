# Settings → Secrets surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → Secrets
surface (`/settings/secrets`, renders `SecretsContent.jsx` / `SecretsTable.jsx`).
Not a substitute for execution — verify a handle as you use it. One writer at a
time; first confirmed by: qa-engineer analyst, ELITEA-2336, 2026-08-05. Updated
by ELITEA-2337/2338/2343 analyst sessions (same day).

## Page structure
- Route: `/settings/secrets` (`ProtectedRoutes.jsx`, `path="secrets"`).
- Page title testid `secrets-page-title` — exact text "Secrets"
  (`DrawerPageHeader titleTestId` prop).
- Search input has NO dedicated testid confirmed yet (not exercised by
  ELITEA-2336) — `DrawerPageHeader`'s `slotProps.searchInput` is passed
  `placeholder`/`search`/`onChangeSearch` but no `testId` in
  `SecretsContent.jsx` (contrast with `personal_tokens_page.py`'s
  `personal-tokens-search-input`, which IS wired). Confirm/add if a future
  case needs search.
- Table columns: Name (sortable), Value (hidden below 600px), Actions — no
  `columnTestIdPrefix` wired (contrast `personal-token-column-header-*` on the
  Personal Tokens surface — `SecretsTable.jsx` doesn't pass this prop to
  `GridTableHeader`, so column headers have no testids here).

## Inline create flow (ELITEA-2336, confirmed live)
- The "+" button (`secrets-add-button`) does **NOT** navigate or open a modal —
  it inserts a real inline editable `GridTableRow` at the top of page 1 of the
  same table (confirmed: no `role="dialog"` element renders). This is the
  OPPOSITE pattern from Personal Tokens' add-button, which navigates to a
  separate route (`create_personal_token_page.py`) — don't assume the two
  "+"-button flows behave the same way on sight.
- **Pagination side-effect (non-obvious, filed as clarification #1202):**
  clicking "+" unconditionally resets pagination to page 1 via
  `resetPaginationRef.current?.()` in `SecretsContent.jsx addSecretRow()` —
  confirmed live by navigating to page 2 first, then clicking "+": pagination
  jumped back to "1 - 10 of N" with the new row as page 1's first entry. This
  happens regardless of which page the user was on.
- The pending (unsaved) row is counted in the pagination total immediately —
  confirmed live: "1 - 10 of 103" → "1 - 10 of 104" the instant "+" is
  clicked, before Save/Cancel. Client-side `sortedRows.length` includes
  `isNew` rows.
- The add button becomes `disabled` while ANY row is in edit mode (only one
  row editable at a time — `DrawerPageHeader`'s `addButton.disabled` prop is
  `isFetching || <any row in edit mode>`). Re-enables on Save or Cancel.
- Name/value inputs (edit mode): testids `secret-name-input` /
  `secret-value-input` — `EditSecretInputGridTable.jsx`, only the NAME field
  is editable for `isNew` rows (existing secrets can only re-value, not
  rename — the name cell renders as static text once saved, never re-opens
  the name input).
- Save (✓) / Cancel (✗): testids `secret-row-save-button` /
  `secret-row-cancel-button` (edit-mode-only render).
- **Save**: fires `POST /api/v2/secrets/secrets/default/{project_id}` → `201`
  on success, followed by a `GET` refetch. Saved row settles into
  ALPHABETICAL sort position (`useTableSort` default `{field:'name',
  direction:'asc'}`) — NOT pinned to top like the pending row.
- **Cancel**: purely client-side row removal — confirmed live, ZERO network
  requests fire (verified via before/after `browser_network_requests` diff).
- Masked value rendering: `SecretValueCell.jsx` shows the literal template
  string `"{{secret." + name + "}}"` as a clickable button label (click =
  copy-to-clipboard of the real value via `showSecret` lazy query, NOT
  exercised by ELITEA-2336).

## Delete flow (confirmed live end-to-end, ELITEA-2338, 2026-08-05)
- Row actions: hover/visible IconButtons for Show/Hide (permission-gated) +
  a "more" (dots) menu button — **NEITHER has a testid**, confirmed both live
  (DOM query) and in source (`SecretsTable.jsx:511-518`, plain `IconButton`
  wrapping `DotsMenuIcon` with no `data-testid`). **Testid needed:
  `secret-row-actions-button`** (ELITEA-2338 AFS assigns this; uniqueness
  confirmed, zero existing hits on EliteaUI `main`).
- The dots-menu opens `SecretActionsMenu.jsx` (Edit value / Hide / Delete, in
  that order) — **zero testids on any menu item**, confirmed in source
  (lines 34/50/66) and live (only locatable by `role="menuitem"` + accessible
  name). **Testids needed** (ELITEA-2338 AFS assigns):
  `secret-actions-menu-edit-value` / `secret-actions-menu-hide` /
  `secret-actions-menu-delete`. Only one menu instance is ever open at a time
  (single `anchorEl` state) — static testids, no per-row parameterization
  needed. `Hide` renders only `{!isNew}` — irrelevant in practice since the
  menu only opens on already-saved rows.
- Items are `disabled={isDefault}` (all three, same prop) — a system/default
  secret disables the whole menu. **Always target a freshly-created,
  run-unique secret for delete-flow tests**, never an existing real one — this
  avoids both the `isDefault` gate and corrupting shared project data (100+
  real secrets live, see § Data scale).
- Delete confirmation reuses the SHARED `Modal.DeleteEntityModal` — confirmed
  live + in source (`DeleteEntityModal.jsx`): `delete-confirm-dialog` (root),
  `delete-confirm-message` (body text, exact live text confirmed: `"Are you
  sure to delete the <name>? Enter the name to complete the action."`),
  `delete-confirm-name-input` (empty on open), `delete-confirm-cancel-button`,
  `delete-confirm-button` (**disabled** until typed name exactly matches —
  confirmed live via DOM `disabled` attribute pre/post-type). Zero new testid
  work needed here — all pre-existing, confirmed for a second time
  (ELITEA-2336/2337 also touched this shared modal on other pages).
- **Confirm-delete network contract** (confirmed live): clicking the enabled
  `delete-confirm-button` fires `DELETE
  /api/v2/secrets/secret/default/{project_id}/{name}` → **204 No Content**,
  followed by a `GET` refetch of the list endpoint. A success toast appears
  (exact text `"The <name> secret has been successfully deleted."`) with **no
  testid** — don't gate automation on it; the DELETE response + refetch +
  row-count are the stable proof.
- **Post-delete empty state**: with a search filter active on the deleted
  name, the table renders `"No secrets"` (plain `Typography`, **no
  testid**) instead of the row grid. Assert via `secret_row` count === 0
  scoped to the filter, not the untestidded empty-state text — stays
  testid-only per locator policy. Confirmed live both immediately after
  delete and after a fresh `page.reload()` (genuine server round-trip, not
  client-cache-only).
- **Cleanup shortcut** (still valid for OTHER cases whose own steps don't
  delete their test secret, e.g. ELITEA-2336's save-flow secret): skip the UI
  delete flow entirely and call the API directly —
  `DELETE /api/v2/secrets/secret/default/{project_id}/{name}` → `204`. Same
  endpoint the UI's own delete flow calls (now confirmed twice, live, via
  ELITEA-2338's own full UI-driven flow above — this is no longer an
  inference from a single manual trigger).

## Row-level eye icon (Show/Hide toggle) — confirmed live, ELITEA-2343, 2026-08-05
- **Two distinct "hide" mechanisms exist on the same row — do not conflate.**
  This section covers the ROW-LEVEL toggle (`renderActions`'s "Show/Hide
  secret action" `IconButton`, `SecretsTable.jsx:496-509`), which is
  DIFFERENT from the three-dot menu's "Hide" item (`SecretActionsMenu.jsx`,
  covered above in § Delete flow and by sibling case ELITEA-2344/#852) — the
  menu's Hide calls a server mutation behind a confirmation dialog; this
  toggle does not.
- **Zero testid**, confirmed both live (DOM query) and in source — a bare
  `IconButton` with no `data-testid`, unlike its neighbor
  `secret-row-actions-button`. **Testid needed:
  `secret-row-visibility-toggle-button`** (uniqueness confirmed against both
  `main` and `automation/testids` — zero hits).
- **NOT gated by `isDefault`** — confirmed in source, no `disabled` prop at
  all on this `IconButton` (contrast the three menu items, all
  `disabled={isDefault}`). A default/system secret's value CAN be revealed
  via this toggle. Irrelevant risk-wise (reveal is read-only), but means a
  future case could legitimately target a real secret's row for THIS
  specific interaction, unlike delete/edit.
- **Reveal (click when masked)**: fires `GET
  /api/v2/secrets/secret/default/{project_id}/{name}` → `200 OK` — SAME URL
  shape as the DELETE endpoint (singular "secret"), different HTTP method.
  Confirmed live response body:
  `{"name": "<name>", "secret_name": "{{secret.<name>}}", "is_hidden": false,
  "value": "<plaintext>"}`. The Value cell (`secret-value-cell`) then shows
  `data.value` verbatim (`useSecretVisibility.hooks.js`'s `handleShowSecret`).
- **Hide (click when revealed)**: confirmed live via before/after
  `browser_network_requests` diff — **ZERO** new network requests. Purely
  client-side (`handleHideSecret`: `setRows(... secretValue: row.secret_name)`)
  — restores the exact masked template string the initial list GET already
  supplied, no re-fetch.
- **Icon identity — a usable non-app testid.** The toggle's icon `<svg>`
  carries its own `data-testid` **automatically supplied by
  `@mui/icons-material`** (equal to the icon component's export name) —
  confirmed live via `browser_evaluate`: `VisibilityIcon` (masked/closed-eye
  state) ↔ `VisibilityOffIcon` (revealed/crossed-eye state). Confirmed in
  source that neither `<VisibilityIcon>` nor `<VisibilityOffIcon>` receives
  an app-authored `data-testid` prop at the call site — this is 100% MUI
  library behavior, not `add-data-testid` work. ELITEA-2343's AFS uses this
  as a scoped `[data-testid="VisibilityIcon"]` / `[data-testid="VisibilityOffIcon"]`
  sub-selector chained off the (new) button testid — flagged there as a
  DECLARED IMPROVISATION since no canon pattern explicitly covers a
  vendor-auto-generated testid on a conditionally-swapped child component;
  see that AFS's § Concrete Handles for the full reasoning and the reviewer
  fallback (drop the icon-shape assertion, keep only the Value-cell text
  assertion) if the improvisation is rejected.
  **Resolved during ELITEA-2343 implementation, fix round 2 (reviewer
  finding, PR #1224): the improvisation was REJECTED — read
  `node_modules/@mui/material/utils/createSvgIcon.js` directly: the
  auto-`data-testid` is gated `process.env.NODE_ENV !== 'production'`, so a
  `vite build` (every deployed env) strips it to `undefined` and the
  selector finds nothing there, despite being green on localhost 100% of
  the time (Vite dev server never sets `NODE_ENV=production`). Fixed by
  adding REAL, app-authored `data-testid`s directly on the two icon call
  sites in `SecretsTable.jsx` — `secret-row-visibility-icon-show` on
  `<VisibilityIcon>`, `secret-row-visibility-icon-hide` on
  `<VisibilityOffIcon>` (`EliteaAI/EliteaUI@e6260731`, on
  `automation/testids`). `createSvgIcon`'s own JSX spreads `...props`
  *after* its internal auto-`data-testid`, so an explicit prop overrides it
  in both dev AND prod builds — confirmed by reading the same file. See
  `.agents/memory/qa-engineer/mui_icons_material_auto_testid_on_icon_svg.md`
  for the durable rule this established: never use an MUI-auto
  `data-testid` on an icon `<svg>` as a locator basis, in any capacity —
  always ask for a real app-authored testid at the call site instead.**
- **`open_row_actions_menu()`'s declared-improvisation React-onClick
  workaround was NOT needed this session** — a normal Playwright `.click()`
  opened the three-dot menu successfully (used for this case's own cleanup
  delete). Contrary to ELITEA-2338's implementation-day finding (deterministic
  failure of real clicks). Not resolved either way — keep the existing
  workaround as a safe superset; flagged as a possible non-determinism, not a
  reproduction of the original root cause.
- **Non-determinism reproduced a second time, same session (ELITEA-2344,
  2026-08-05).** Opening the three-dot menu TWICE in one session, same page,
  same button, no reload in between: the FIRST open (to Hide a freshly
  created secret) succeeded with a plain Playwright `.click()`; the SECOND
  open minutes later (to Delete a different freshly created secret, for
  cleanup) did NOT — the button received the click (no error) but no
  `[role="menu"]` ever appeared, and the existing React-`onClick` workaround
  was needed to actually open it. This strengthens (doesn't resolve) the
  non-determinism first documented by ELITEA-2338's implementer and flagged
  as "not needed"/"inconclusive" by ELITEA-2343. Net evidence across all
  three sessions is now split ~50/50 — **implementers should keep using the
  workaround unconditionally**, never simplify to a plain click based on any
  single session's contrary result. Root-cause tracking:
  `EliteaAI/elitea-testing-public#1222` (open).

## Three-dot menu → "Hide" flow (confirmed live, ELITEA-2344, 2026-08-05)
- **Third confirmation mechanism on this page — do not conflate with the
  other two** (row-level eye-icon toggle, § above; shared `DeleteEntityModal`
  used by the menu's Delete item, § Delete flow above). The menu's **Hide**
  item opens a **different, generic, shared `AlertDialog`** component
  (`src/components/AlertDialog.jsx`, NOT `Modal.DeleteEntityModal`) — used
  app-wide beyond Secrets (confirmed via `git grep`: `AttachmentSettingsModal.jsx`,
  `ToolkitsOperationButtons.jsx`, others). Does **not** require typing the
  secret name to confirm (unlike Delete) — a direct confirm click.
- **Live confirmation copy (confirmed via DOM read, differs from the ELITEA-2344
  case's quoted text — filed as clarification `EliteaAI/elitea-testing-public#1226`,
  not a defect):** title `"Hide secret?"`, body
  `Are you sure to hide the secret "<name>"? Once hidden, the secret will no
  longer be visible.`, confirm button text `"Hide"`.
- **Zero testid on the dialog body text** — `StyledDialogContentText` in
  `AlertDialog.jsx` carries only an ARIA `id="alert-dialog-description"`, not
  a `data-testid`. **Testid needed: `alert-dialog-content`** (generic, shared
  component — never scope it to secrets; uniqueness confirmed against both
  `main` and `automation/testids`). The confirm button already has a generic
  pre-existing testid: `alert-dialog-confirm-button` (`AlertDialog.jsx:78`).
- **The row-scoped `id={`alert-dialog-${row.id}`}` prop passed at the
  `SecretsTable.jsx` call site does nothing** — confirmed via source read,
  `AlertDialog.jsx` never destructures or forwards an `id` prop. Harmless in
  practice: MUI only mounts the `open`-gated Dialog instance into the DOM, so
  `document.querySelector('[role="dialog"]')` reliably finds exactly one
  match at a time (confirmed live) — no per-row scoping is actually needed
  for either the body-text or confirm-button locators.
- **Confirm-hide network contract** (confirmed live): clicking
  `alert-dialog-confirm-button` fires
  `POST /api/v2/secrets/hide/default/{project_id}/{name}` → **200 OK**
  (note: `.../hide/...`, NOT the singular `.../secret/...` DELETE-endpoint
  shape used by Delete/reveal), followed by a `GET` refetch of the list
  endpoint. No toast text was confirmed for this flow this session — not
  needed, the POST response + row-count are the stable proof.
- **Post-hide, the secret is gone from the table** (row-count 0 under a
  name-filtered search + unfiltered pagination total drop, confirmed both
  immediately and after a fresh `page.reload()` — genuine server round-trip,
  same double-check shape as ELITEA-2338's delete flow). **No UI affordance
  to "un-hide" was found** — consistent with (though not literally worded
  the same as) the case's "cannot be unhidden" claim.
- **The "+" button genuinely allows recreating a secret with the exact same
  (previously-hidden) name — confirmed as a real create, not just a UI
  affordance check:** typed the identical name into a fresh inline row,
  `secret-row-save-button` was enabled with no `secret-name-error`, and the
  create `POST` resolved **201 Created** (not a 409/400 conflict). The
  backend does not treat a hidden secret's name as still-reserved.

## Three-dot menu → "Edit value" flow (confirmed live, ELITEA-2347, 2026-08-06)
- **Fourth distinct interaction mechanism on this page** (alongside the
  row-level eye-icon toggle, the menu's Hide, and the shared delete modal).
  "Edit value" enters the SAME row-level edit mode the create flow uses
  (`GridRowModes.Edit`, `EditSecretInputGridTable` renders for the Value
  column) but for an EXISTING (`!isNew`) row, NOT a `isNew` one.
- **Name column renders NO input at all in this mode — confirmed live and in
  source.** `SecretsTable.jsx`'s `renderNameCell` guard is literally
  `if (isEditing && row.isNew)` — for an existing row, even while actively in
  edit mode, the Name column renders the exact same `secret-name-cell` static
  `Text.EllipsisTypography` it shows in plain view mode. `secret-name-input`
  count is `0` for an existing row's edit-value mode (confirmed via DOM
  query) — contrast the CREATE flow (ELITEA-2336), where a brand-new row DOES
  render `secret-name-input` live-editable. This is the mechanism behind the
  case's "name field is read-only" claim — there is no disabled/readonly
  input anywhere in this code path, just no input at all.
- **Value field starts EMPTY, not pre-filled with the existing plaintext.**
  Clicking "Edit value" fires `handleEditClick` (`useSecretRowActions.hooks.js`)
  which calls `showSecret` (→ `GET /api/v2/secrets/secret/default/{project_id}/{name}`,
  same endpoint the row-level reveal toggle uses, `200 OK`, confirmed live) —
  but `SecretsTable.jsx`'s WRAPPING `handleEditClick` (lines 221-246)
  immediately clears the fetched value: `secretValue: ''`. Confirmed live:
  `secret-value-input`'s `.inputValue()` === `""` right after entering edit
  mode, before typing anything. The GET's plaintext result is fetched and
  silently discarded — not a bug, just wasted work (possibly a leftover from
  an earlier design that pre-filled the field); don't mistake this GET for
  evidence the field will show the old value.
- **Save fires `PUT /api/v2/secrets/secret/default/{project_id}/{name}`** —
  confirmed live, body `{"value": "<new value>"}`, `200 OK`, response body
  `{"name": "<name>", "secret_name": "{{secret.<name>}}"}` (same shape as the
  create mutation's response). Distinct from every other secrets mutation:
  singular `secret` path segment (like delete/reveal) but `PUT` method
  (unique to this flow).
- **No list-GET refetch after the edit PUT** — confirmed live (network diff)
  AND in source: `useSecretRowUpdate.hooks.js`'s `processRowUpdate`, the
  `else` (non-`isNew`) branch updates `rows` state directly from the mutation
  response and never calls `refetch()` — only the `isNew`/create branch does
  (on a `setTimeout`). An implementer who waits on a list-GET after this PUT
  will wait forever / rely on a timeout instead of a real signal.
- **Reveal after edit is a genuine server round-trip proof, not just local
  state.** Clicking the eye icon after saving fires a FRESH
  `GET /api/v2/secrets/secret/default/{project_id}/{name}` (`200 OK`) and the
  revealed `secret-value-cell` shows exactly the newly-saved value — this is
  the strongest available proof the PUT actually persisted server-side (as
  opposed to only updating optimistic local React state). Confirmed live this
  session end-to-end: created `autotest_edit_2347_a1b2c3d4` = `original-value-123`
  → Edit value → saved `updated-value-456` (PUT 200) → revealed via eye icon →
  text content exactly `"updated-value-456"`.
- **Menu-open non-determinism, fourth data point.** Same three-dot button as
  ELITEA-2338/2343/2344 — this session's FIRST open (for Edit value) needed
  the existing React-`onClick` workaround (plain `.click()` left the button
  "active"/pressed with no menu mounting); the SECOND open (cleanup Delete)
  succeeded with a plain click. Net evidence across all four sessions remains
  mixed — keep using `open_row_actions_menu()`'s workaround unconditionally.
  Tracking: `EliteaAI/elitea-testing-public#1222` (open).
- **Cleanup-only console 404, not reproduced within the case's own steps.**
  After deleting the test secret (post-assertion cleanup), one console error
  fired: `Failed to load resource: 404` for
  `GET .../secret/default/399/<name>` — likely a stray background request
  racing the delete. Did not occur during steps 1-8 of the case itself (only
  during teardown). Not investigated further; flagged so a future session
  doesn't misattribute it to the edit-value flow under test.

## Data scale
- Project `Private` (399) already has 100+ real secrets (e.g. `auth_token`,
  `default_llm_model_name`, `pgvector_project_connstr`, `webhook_secret_v450`,
  …) — never assert an exact total row count; assert presence/absence of a
  run-unique generated name instead.

## Name validation (ELITEA-2337, confirmed live)
- `EditSecretInputGridTable.jsx` (`field === 'name'` branch): validation is
  `SECRET_NAME_PATTERN = /^[A-Za-z0-9_]*$/` — letters, digits, underscore
  ONLY. **Hyphens are rejected here** — this is stricter than the sibling
  Personal Tokens surface, whose own `TOKEN_NAME_PATTERN =
  /^[a-zA-Z0-9_-]*$/` explicitly ALLOWS hyphens. Don't assume the two
  "name validation" surfaces share a character class.
- Error text (exact): `"Only alphanumeric characters and underscore are
  allowed"` — renders via the component's own `helperText`/`error` props on
  every keystroke, **no blur/touched gating** (contrast with Personal
  Tokens' Formik `touched.name` + `useAutoBlur` mechanism — this surface's
  `useMemo` has no such gate, confirmed live: error appears immediately on
  `onChange`, no blur action needed or observed).
- No testid on the error text as of ELITEA-2337's analysis — **testid
  needed**: `secret-name-error` (uniqueness confirmed, no existing hits).
  `helperText` travels through `Input.StyledInputEnhancer` → `Input.InputBase`
  → MUI `TextField` via a `leftProps` spread (same "generic prop, wrap at
  call site" mechanism as the sibling `create-personal-token-name-error`).
- Save (✓) button (`secret-row-save-button`, pre-existing) is
  `disabled={hasValidationErrors}` (`SecretsTable.jsx:355-359,456,460`) —
  this IS the "checkmark enabled" the case text refers to; confirmed live
  the button disables on an invalid name and re-enables once the name is
  replaced with a conforming one (no page reload/re-add needed for the
  recovery — same row, same edit session).
- `Control+a` to select-all-then-replace is **unreliable** on this input
  (confirmed live, same failure mode as the sibling Personal Tokens page):
  use `press("Home")` + `press("Shift+End")` instead.
- Known defect `#1203` (React "Maximum update depth exceeded" on every
  `/settings/secrets` mount, filed by ELITEA-2336's implementer) was **NOT
  observed** during this ELITEA-2337 exploration session (0 console
  errors/warnings across the full negative-validation flow) — contrast with
  the covering test's own automated run, which hit it deterministically
  3/3. Inconclusive whether a fresh automated run of THIS case's own test
  will reproduce it; the implementer should check their own run rather than
  assume either way (see the AFS's § Known Defects decision tree).

## Empty state & project scoping (ELITEA-2249, 2026-08-24, analyst)
- **Secrets are PROJECT-scoped**: `GET /api/v2/secrets/secrets/default/{project_id}`.
  Live counts for the shared `${TEST_USER}`'s 5 selectable projects:
  `Private` 399 → `200`/**120**, `UI Testing` 400 → `200`/**4**,
  `Bugs & Features` 406 / `Elitea Development` 25 / `Elitea Testing Team` 471 →
  **`403`**. There is **no project this user can list AND that is empty**, and the
  project selector has **no create-project affordance** (5 fixed options).
- **A `403` project looks exactly like an empty project.** `SecretsContent.jsx` skips
  the query client-side (`skip: !projectId || !checkPermission(PERMISSIONS.secrets.list)`),
  so no request is issued at all, `data` stays `undefined`, and the table renders the
  ordinary `"No secrets"` empty branch **with the `secrets-add-button` visible and
  enabled**. Filed as bug **#1773**. Never read "table is empty" as "project has no
  secrets" — prove it with the list response (`200` + zero items).
- **`#1203`'s render loop is UNBOUNDED in that skipped state.** Measured 2026-08-24
  over 6 s from a fresh load: project 399 → **5** `Maximum update depth exceeded`
  console errors (bounded mount burst); project 471 → **140 and still climbing**
  (~28k entries over a few minutes). Root cause is the `data: secrets = []` default
  minting a new array on every render → `secretsList`/`filteredSecrets` useMemo chain →
  `useEffect([isFetching, filteredSecrets])` → `setSecretRows` → re-render. New
  occurrence commented on #1203. Any console-error axis on this page must account
  for it, and never dwell on a 403 project.
- **Empty-message handle**: the `"No secrets"` text is a bare
  `<span class="MuiTypography-root …">` inside a `Box`, produced by the SHARED
  `GridTableContainer` (`isEmpty` + `emptyMessage` props, `GridTableContainer.jsx:37-43`)
  — **no testid**, and none can be hardcoded there (shared component). A case needing
  it must thread a caller-supplied prop (e.g. `emptyMessageTestId`) from
  `SecretsTable.jsx`. `secrets-pagination-info` is **absent** when the table is empty.
- ELITEA-2249 is parked **blocked** on the precondition (see
  `l2_secrets-empty-state-no-secrets_ELITEA-2249.md` § Blocked Steps).

## Page layout / search / sort / pagination (ELITEA-2330/2331/2332/2334/2342,
## combined analyst+implementer session, 2026-08-27)

- **The search input NOW has a testid** — `secrets-search-input`, added this session
  (`EliteaAI/EliteaUI@249c0186`, on `automation/testids`). This **supersedes** the
  § Page structure note above ("Search input has NO dedicated testid confirmed yet"):
  `SecretsContent.jsx`'s `slotProps.searchInput` now passes `testId`, the prop
  `DrawerPageHeader` already supported. It lands on the **native `<input>`**
  (`SimpleSearchBar` forwards `data-testid` through `inputProps`), so typing and
  `.input_value()` work directly.
- **Pagination controls now have testids too** — same commit: `pageSizeSelectTestId`,
  `prevButtonTestId`, `nextButtonTestId` wired at `SecretsTable.jsx`'s
  `GridTablePagination` call site →
  `secrets-pagination-page-size-select` (+ `…-select-combobox`, derived automatically by
  `SingleSelect` via `SelectDisplayProps` — the **root is not clickable, the combobox
  node is**), `secrets-pagination-prev-button`, `secrets-pagination-next-button`. All
  four are pure additive props on pre-existing shared components: no DOM node, no hook,
  no state, nothing removed.
- **Rows-per-page OPTIONS need no new testid** — the shared `SingleSelectMenuItem`
  already defaults to `data-testid={option.testId ?? select-option-${option.value}}`, so
  the live options are `select-option-5` / `-10` / `-50` / `-100`. Only one select menu
  is ever mounted (0 such nodes in the DOM when closed, confirmed live), so no scoping is
  needed. Contrast the Notification Center, which threads explicit
  `notifications-page-size-option-{n}` testIds — unnecessary here.
- **Column headers and the sort control DO exist** — this supersedes the § Page structure
  note ("no `columnTestIdPrefix` wired"): `SecretsTable.jsx` passes
  `columnTestIdPrefix="secret"`, so `secret-column-header-{name,secretValue,actions}` and
  `secret-sort-icon-name` all render. Only `name` is `sortable: true`, so it is the ONLY
  column with a sort-icon node (the other two are `to_have_count(0)` — which is how this
  batch references, and therefore justifies, that testid family per canon question #1705).
- **Sort contract (confirmed live + in source).** `useTableSort({ defaultField: 'name',
  defaultDirection: 'asc' })` ⇒ the table arrives **already name-ascending with no
  interaction**; `handleSort` then flips on each click of the same field. Live:
  load → asc (`auth_token` first); click 1 → **desc** (`webhook_secret_v9348` first);
  click 2 → asc. **The case text (ELITEA-2331) has this inverted** — filed as
  clarification **#1901**, sibling of **#1880** (identical drift on Personal Tokens).
  Comparison is case-insensitive (`sortData` lower-cases both sides), and it re-sorts the
  WHOLE dataset, not just the visible page.
  ⚠️ **Sort direction is only expressed as an inline `transform: rotate(180deg)` style on
  the icon** — never assert it; assert the rendered row ORDER, which is the real observable.
- **Pagination contract (confirmed live).** `defaultPageSize: 10`,
  `PAGE_SIZE_OPTIONS: [5, 10, 50, 100]`. Range label is the literal
  `` `${startRow} - ${endRow} of ${totalRows}` `` — an **ASCII hyphen with spaces**
  (`1 - 10 of 121`), not the en dash the case texts use. Prev is `disabled` on page 1,
  next on the last page. `handlePageSizeChange` **resets the page to 0** — confirmed live:
  from page 2, choosing `5` landed on `1 - 5 of 121` with prev disabled again. Zero
  network requests fire on a page change or a page-size change (client-side over the
  already-fetched list).
- **Search contract (confirmed live).** `SecretsContent.jsx`'s
  `secretsList.filter(name.toLowerCase().includes(search.toLowerCase()))` ⇒ per-keystroke,
  substring, case-insensitive, **name-only**, no Enter/submit/debounce, zero network
  requests. The filtered set feeds pagination, so the range label re-totals
  (`pgvector` → `1 - 2 of 2`; `PGVECTOR` → the identical 2 rows). `fill("")` clears it
  correctly — the digest's `Control+a`-unreliable warning is scoped to the create-row Name
  field (`useAutoBlur`), NOT to this plain `InputBase`.
- **Data scale, refreshed**: project `Private` (399) now holds **121** secrets
  (was 120 on 2026-08-24, 103/104 on 2026-08-05). Never assert an absolute total — parse
  it out of `secrets-pagination-info` and compute expectations from it.
- **`#1203` — the live-walk vs automated-run split is now settled for this surface, and
  the burst is much bigger than recorded.** The Playwright-MCP walk of the identical flow
  produced **0** console errors (navigation, sorting, paging, page-resizing, searching),
  while the five automated specs written from that same walk hit it **5/5**, at
  **32-41 occurrences per test** (vs the 5 measured on this same project on 2026-08-24).
  So: never conclude `#1203` is quiescent from a live MCP session — it is not a reliable
  predictor of what an automated run sees. Every spec on this surface keeps the isolated
  soft-failure handling (`_is_known_defect_1203` + `soft_failures`/`pytest.fail()`), which
  makes them **sanctioned-RED on this one signature** until the product fix ships. Counts
  and reasoning commented on `#1203` (2026-08-27).
- **⚠️ Vite did NOT pick up the JSX edits on this machine** (OneDrive-backed checkout):
  after editing + committing, the dev server kept serving the pre-edit transform, and a
  `touch` did not invalidate it either. The new testids appeared only after **restarting
  `npm run dev`**. Verify a fresh testid with
  `curl -s "http://localhost:5173/src/%5Bfsd%5D/.../File.jsx" | grep -c "<testid>"`
  before concluding "the testid does not render" — that check costs one command and
  distinguishes a stale dev server from a wiring mistake.

## Copy-on-click / delete-cancel / name-required / name-uniqueness
## (ELITEA-2335/2339/2340/2341, combined analyst+implementer session, 2026-08-27)

- **Toasts on this surface are testid-locatable and were never used here before.** The
  shared `src/components/Toast.jsx` already carries `toast-alert` (with a
  `data-severity="{error|success|info|warning}"` attribute) and `toast-message`, both
  pre-existing on `main`. Durations are severity-dependent
  (`TOAST_DURATION_DEFAULTS`, `src/common/constants.js:345`): **error 10 s, warning 7 s,
  success 3 s, info 3 s**. Earlier digest entries said "the success toast has no testid,
  don't gate automation on it" — that is **superseded**: it does, app-wide. The 3 s
  info/success window is why a one-shot `text_content()` read misses it (it did, live);
  use a web-first `expect(...).to_have_text(...)` attached immediately after the action,
  or a `MutationObserver` when exploring by hand.

- **Clicking the masked value copies the plaintext (ELITEA-2335, confirmed live).**
  `SecretValueCell.jsx` wraps the `secret-value-cell` label in an MUI `Button` whose
  `onClick` is `handleDirectCopy`: `showSecret` → `GET /api/v2/secrets/secret/default/
  {project_id}/{name}` → 200 → `copyToClipboard(data.value)` → `toastInfo`. Live toast
  text, verbatim: **`The <name> values have been copied.`** (severity `info`). The masked
  cell text does NOT change — copying is not revealing. On **Safari** the handler is
  `undefined` (`isSafari()`) and the tooltip switches to "Use copy icon in actions to copy
  secret" — Chromium is the automated target, so the handler is live there.
  ⚠️ **The Playwright-MCP browser cannot READ the clipboard**
  (`NotAllowedError: Read permission denied`) — but the pytest context can:
  `automation/conftest.py:304` grants `clipboard-read`/`clipboard-write`, and
  `BasePage.get_clipboard_text()` / `clear_clipboard()` already exist. The clipboard
  **write** still demonstrably works in an MCP session (the success toast only fires when
  `copyToClipboard` resolves), so an MCP walk can confirm everything except the readback.

- **Cancelling a delete is purely client-side (ELITEA-2339, confirmed live).**
  `delete-confirm-cancel-button` closes the shared `DeleteEntityModal` with **zero**
  network requests; the row, its name cell and its masked value cell are unchanged, and
  `delete-confirm-button` is `disabled` until the exact name is typed (re-confirmed).
  ⚠️ `delete-confirm-name-input` is on the **MUI `TextField` root `<div>`**, not on the
  native `<input>` — `.fill()` on the testid itself errors with *"Element is not an
  &lt;input&gt;…"*; the page object's `fill_delete_confirm_name()` already handles this,
  but a hand-driven MCP walk must target `[data-testid="delete-confirm-name-input"] input`.

- **An EMPTY secret name is NOT validated (ELITEA-2340) — filed as bug `#1903`.**
  `EditSecretInputGridTable.jsx`'s only validation is
  `field === 'name' && inputValue && !SECRET_NAME_PATTERN.test(inputValue)` — the
  `inputValue &&` guard short-circuits on `''`, so an empty name yields no error, and the
  Save (✓) button (`disabled={hasValidationErrors}`) stays **ENABLED** with no
  `secret-name-error`, even though the component passes `required` to the input. Live:
  `saveDisabled: false`, `nameErrorText: null`, `helperTexts: []`. Siblings on other
  surfaces: `#1004`, `#526` (closed), `#633`. **Not probed:** what a Save click with an
  empty name actually does — `useSecretRowUpdate` drops the row only when name AND value
  are both empty, so it would POST `name: ""` into shared project data and could leave an
  unnamed secret with no deletable URL path. Don't probe it casually.

- **Name uniqueness is enforced SERVER-SIDE only (ELITEA-2341, confirmed live).** Typing an
  existing secret's name leaves Save (✓) **enabled** with no inline error; the create
  `POST /api/v2/secrets/secrets/default/{project_id}` returns **400 Bad Request**, the
  browser logs the usual `Failed to load resource … 400`, and `SecretsTable.jsx`'s
  `isAddingError` effect raises an **error** toast whose live text is exactly
  **`Secret "<name>" already exists`**. The pending row **stays in edit mode** with the
  typed name intact (`useSecretRowUpdate` returns the row untouched on
  `responseResult.error`), and no duplicate row is created.
  ⚠️ **`SecretsPage.click_save_button()` cannot be used for a rejected save** — after
  awaiting the POST it waits for `secrets-add-button` to re-enable, which only happens when
  the row LEAVES edit mode; on a 400 it never does. Use the additive
  `click_save_button_expect_rejection()` variant instead (added by ELITEA-2341).

- **Menu-open non-determinism (`#1222`), fifth and sixth data points:** both three-dot menu
  opens in this session succeeded with a plain MCP `.click()`. Evidence across sessions
  stays mixed — **keep `open_row_actions_menu()`'s React-`onClick` workaround
  unconditionally**; it is a safe superset.

### Implementation-time confirmations (same session, 2026-08-27)
- **Clipboard READBACK works in the pytest context** — `BasePage.get_clipboard_text()`
  returned the plaintext and matched both oracles (the value the create POST persisted and
  the reveal GET's `value`). So the MCP-only `NotAllowedError` above is a limitation of the
  MCP browser context, never of the suite.
- **`#1203` counts for this wave's four specs**: 45 / 35 / 33 / 33 occurrences per test —
  consistent with the 32-41 range recorded for the previous wave, and again **0** in the
  live MCP walk of the identical flows.
- **`SecretsPage.type_value()`** added (additive sibling of `type_name()`): `fill_new_row()`
  always fills BOTH fields, which a "leave the name empty" case cannot use.

## Hidden-secret CONSUMERS — what a hidden secret does downstream
## (ELITEA-2345/2346 cluster analyst session, 2026-08-27, confirmed live)

_This section covers the surfaces that CONSUME secrets, not the Secrets page itself.
Every handle below was read live on `localhost:5173` / project **399**._

### The secret-selection dropdown is ONE shared component, three call sites
`src/[fsd]/shared/ui/secret-field/SecretField.jsx` renders every secret field in the
app. Same derived testids everywhere — do not duplicate selectors per surface:
- `toolkit-field-{key}-input` — the SecretField wrapper `<div>`
- `toolkit-field-{key}-input-field` — the native `type="password"` `<input>`
  (Password mode only)
- `toolkit-field-{key}-input-toggle-secret` / `-toggle-password` — the mode toggle
  (`ToggleButtonGroup`; read `aria-pressed` to know which mode is active)
- `toolkit-field-{key}-input-combobox` — the vault select display node (Secret mode only)
- `toolkit-field-{key}-input-refresh-secrets-button` — SAVED SECRETS group-header refresh
- `select-group-header-Create` / `select-group-header-Saved Secrets` — the two groups
- `select-option-{{secret.<name>}}` — a saved-secret option (the option VALUE is the
  `{{secret.…}}` template, so the testid contains braces)

Confirmed call sites this session:
1. **Create credential** — `/credentials/create-credential/<type>` (e.g. `jira`, field
   key `api_key`).
2. **Edit credential** — `/credentials/all/<id>?viewMode=owner&name=<display name>`.
3. **New AI Provider** — `/settings/create-ai-provider/<type>` (e.g. `open_ai`, field
   key `api_key`). **Same testids** as the credential forms — the existing
   `credential_create_page.py` secret-vault methods work verbatim here despite the name.

**The field always starts in PASSWORD mode.** The vault combobox does not exist in the
DOM until `…-toggle-secret` is clicked. Any case whose steps say "open the secret
dropdown" needs that hop first; the TMS case texts omit it.

### Hiding a secret removes it from the dropdown (the ELITEA-2345/2346 observable)
Measured live, same session, same project: **123** saved-secret options with two
run-unique secrets visible → **122** after hiding one → **121** after hiding both. The
hidden option's testid disappears entirely; every other option stays. Verified on all
three call sites above.
→ Always pair the absence assertion with a **control** (a known-visible secret IS
present / `saved_secret_options` count > 0). An empty or failed-to-load dropdown passes
a bare absence check.

### Hiding a secret does NOT break credentials that reference it — but the UI changes shape
Verified end-to-end: created secret → created a `jira` credential with
`api_key = {{secret.<name>}}` → hid the secret → re-read the credential.
- **Server truth (unchanged):** `GET /api/v2/configurations/configuration/399/<id>` →
  `"data": {"api_key": "{{secret.<name>}}", …}`. The reference survives; nothing is
  nulled or rewritten.
- **UI fallback (intentional):** the field renders in **Password** mode
  (`…-toggle-password` `aria-pressed="true"`, combobox absent) and the native password
  input holds the literal secret **NAME**. Source:
  `SecretField.jsx` — `isHiddenSecret = isError || !data?.some(i => i.secret_name === value)`,
  and `handleSwitchToSecretTab` only switches to the Secret tab `if (isSecret && !isHiddenSecret)`;
  `updateRawPassword()` seeds the password input with `value.match(secretRegex)[1]`.
- **The form is NOT dirtied by the fallback** — `credential-form-save-button` is
  **disabled** on load. Nothing is silently rewritten client-side.
- Raised for a product decision (a keystroke in that field would replace the reference
  with the literal name): `EliteaAI/elitea-testing-public#1907`.
- **Do NOT use `credential-form-test-connection-button` as the "still works" oracle** on
  a synthetic credential — it fails for the fake host regardless of the hide.

### Settings → AI Providers create flow (NOT "AI Configuration")
- Route `/settings/ai-providers`; nav item `settings-nav-item-ai-providers`; title
  `ai-providers-page-title`. **There is no "AI Configuration" section** — TMS case texts
  saying so are stale (`EliteaAI/elitea-testing-public#1906`).
- The page renders `ai-providers-section-*-loading` placeholders first, then the real
  `ai-providers-section-*` testids. Gate on a real section testid, never a fixed delay.
- The "+" is the generic `sidebar-create-button` (label is route-contextual: "AI
  Provider" here). It routes to `/settings/create-ai-provider?viewMode=owner&from=ai-providers`
  — a **type picker**, not a form. Type cards use the same
  `toolkit-type-card-{type}` family as the credentials picker (`toolkit-type-card-open_ai`,
  `…-azure_openai`, `…-ollama`, `…-vertex_ai`, `…-pg_vector`, …).
- Only after the type click (`/settings/create-ai-provider/open_ai`) does the form with
  `toolkit-field-label-input` / `toolkit-field-api_base-input` / `toolkit-field-api_key-input`
  render.

### Two live gotchas that cost real time this session
1. **`beforeunload` blocks `page.goto()`.** A credential or AI-provider form dirtied by
   *anything* (including merely flipping the secret toggle) raises a native
   `beforeunload` dialog on navigation; a bare `page.goto()` hangs until it is handled
   (two 60 s timeouts here). Register `page.on("dialog", lambda d: d.accept())` or
   discard the form first.
2. **`delete-confirm-name-input`'s testid is on the MUI `FormControl` `<div>`, not the
   `<input>`.** `fill()` on the testid errors with *"Element is not an `<input>`"*;
   target the native child. `credential_detail_page.fill_delete_confirm_name()` already
   does this — use it.

### Three-dot menu workaround: reproduced AGAIN (3rd data point)
A plain Playwright `.click()` on `secret-row-actions-button` failed to mount the menu
this session (the `secret-actions-menu-hide` item did not exist afterwards); the
existing React-`onClick` workaround in `secrets_page.open_row_actions_menu()` opened it
first try, twice. Score across sessions: ELITEA-2344 saw 1 success / 1 failure with a
plain click, ELITEA-2343 saw 1 success, this session saw 1 failure. **Keep the
workaround unconditionally** — `EliteaAI/elitea-testing-public#1222`.

### Console noise on the CREDENTIALS routes
`/credentials/create-credential/<type>` logs a React `Each child in a list should have a
unique "key" prop` **console.error** from `CategorySection.jsx` (via
`CredentialTypeSelector.jsx`) — the same defect as
`EliteaAI/elitea-testing-public#656`, second occurrence commented there. It is
**dev-build only** (stripped by `vite build`), so it appears on localhost and not on a
deployed env. `#1203` (Secrets-page "Maximum update depth exceeded") did **not** fire in
this session — still inconclusive, check your own run.

### Implementation-time confirmations — ELITEA-2345/2346 (test-automation-engineer, 2026-08-28)

Both specs went **green on their first run, 0 reruns** (2345: 54.48 s; 2346: 50.24 s),
against `localhost:5173` / project 399. Everything the analyst recorded above held
verbatim. New, implementation-created facts:

- **The AI-provider type picker now has page-object support.**
  `automation/pages/ai_providers_page.py` gained (additively) `create_button`
  (`sidebar-create-button`), `TYPE_CARD_SELECTOR` /`TYPE_CARD_PREFIX_SELECTOR`
  class-constant templates, `type_card()`, `type_cards`, `click_create()` and
  `click_type_card()`. `click_create()` settles on the first rendered type card;
  `click_type_card()` settles on the picker **unmounting** — it deliberately does not
  re-declare `toolkit-field-label-input`, which already lives in
  `CredentialFormFieldsMixin`.
- **`CredentialAPI.get_credential(id)` now exists** (`automation/api/client.py`) —
  `GET /configurations/configuration/{project}/{id}`, the honest server-side oracle for
  "the credential's stored `{{secret.…}}` reference survived the hide". `list_credentials`
  is a list projection and is not guaranteed to carry the `data` block; don't rely on it
  for that assertion.
- **The credential-create POST's response body carries the new credential's `id`** —
  no card-click round-trip is needed to learn it (ELITEA-2345 captures it straight off
  `expect_response`, with a `list_all_credentials()` lookup by `label` kept as an
  explicit fallback).
- **The shared secret-vault handles were REUSED, not duplicated.** Both specs drive the
  `api_key` SecretField through `CredentialCreatePage` — on the credential DETAIL route
  and on the **AI-provider** form alike — because that page object already owns those
  derived testids. Extracting them into a shared `components/secret_field.py` (or
  promoting them to `CredentialFormFieldsMixin`, the pattern that file already used for
  `FIELD_INPUT`/`AUTH_METHOD_RADIO`) is the cleaner end state but is a **non-additive**
  edit to a ~20-caller page object — raised to the lead rather than done inside a case PR.
- **The vault dropdown may not self-close after selecting an option** (consistent with
  `#1047`'s `skipNextCloseRef`). ELITEA-2345 presses `Escape` after the selection so the
  subsequent Save click is unambiguous; cheap and harmless when the menu did close.
- **`page.on("dialog", lambda d: d.accept())` registered once at the top of the test is
  sufficient** for the `beforeunload` gotcha above — no discard-first dance was needed on
  either the credential or the AI-provider form.
- **Neither spec asserts console errors.** It is outside both Coverage Maps, and `#656`
  fires deterministically on `/credentials/create-credential/<type>` on dev builds — an
  unrequested assertion would have made ELITEA-2345 a sanctioned-RED its case never asked
  for. `#1203` was again not observed on `/settings/secrets` in these runs.
- **The three-dot React-`onClick` workaround (`#1222`) was used unconditionally** in both
  specs and opened the menu first try, three times across the two runs. 4th data point.

## Role-scoped access to Secrets, empty-state re-verification, and the network-failure
## error path (ELITEA-2333/2348/2349, combined analyst+implementer session, 2026-08-28)

### Roles are PROJECT-SCOPED — a viewer vantage exists with no new credential
The shared `${TEST_USER}` holds **different roles in different projects**, so
role-differentiated cases are NOT uniformly blocked on a second identity (this
partially supersedes question **#1314**, commented there). Verified live 2026-08-28:

```
GET {ELITEA_API_BASE}/admin/users/prompt_lib/{project_id}   (roles of ${TEST_USER})
  399 Private              -> ['editor', 'viewer']   <- settings.elitea_project_id
  400 UI Testing           -> ['admin']              <- settings.users_team_project_id
  406 Bugs & Features      -> ['viewer']
  25  Elitea Development   -> ['viewer']
  471 Elitea Testing Team  -> ['viewer']             <- settings.elitea_team_project_id
```

`useCheckPermission` reads `state.user.permissions`, refetched **per selected project**
via `GET /auth/permissions/prompt_lib/{id}`. Live: project 400 → 360 permissions
(8 × `configuration.secrets.*`), project **471 → 158 permissions, ZERO containing
`secret`**. Switching the project selector therefore puts the app in a genuine
role-derived permission state — computed by the product, not fabricated by the test.

**Consequence for Secrets:** `src/[fsd]/pages/settings/index.jsx:89` gates the drawer's
`secrets` tab on `PERMISSIONS.secrets.list` and filters the item out
(`index.jsx:174`). Measured live, drawer nav item ids:
- project 399 → `… project-context, **secrets**, analytics, usage …`
- project 471 → `… project-context, users, analytics, usage …` (**no `secrets`**),
  both after an in-session switch AND on a fresh load.

Handle: `settings-nav-item-secrets` (existing `SettingsDrawerPage.SETTINGS_NAV_ITEM`
template) — absence-assertable per canon #511's extension.

### There is NO `Monitor` role in Elitea
`GET {ELITEA_API_BASE}/admin/roles/default/{p}` returns `['admin','editor','viewer']` for
**all five** projects (399/400/406/25/471), and `grep -rni "'monitor'|\"monitor\""
../EliteaUI/src/` has **0 hits**. Any case naming a Monitor role is case-text drift —
filed as clarification **#1909**. Don't go looking for it again.

### Deep-linking `/settings/secrets` on a no-permission project (re-confirmed)
Still exactly **#1773**: `secrets-page-title` + an **enabled** `secrets-add-button` +
`No secrets`, **no** access-denied state, **no** toast, and **zero** secrets requests
(the RTK query is skipped client-side). Console errors on that mount: **144**
`Maximum update depth exceeded` (#1203's unbounded variant) — never dwell there.

⚠️ **Unverified single observation, worth a look if you touch it:** switching projects
*while already on* `/settings/secrets` left the PREVIOUS project's rows rendered in the
MCP browser (399's secrets still listed with 471 selected). Seen once via Playwright MCP,
**not** reproduced in the framework probe (which switched from `/settings/project-general`,
where rows were 0). Could be a mid-transition snapshot. Not filed — verify before claiming.

### Empty-state precondition: STILL unproducible (ELITEA-2333, re-probed not copied)
`GET {ELITEA_API_BASE}/secrets/secrets/default/{p}` → 399: `200`/**121**,
400: `200`/**4**, 406/25/471: **`403`**. No project this user can list AND that is empty;
the selector still offers 5 fixed projects with no create affordance. ELITEA-2333 is
parked `blocked` for the same reason as **ELITEA-2249** — see
`l3_secrets-empty-state-no-secrets_ELITEA-2333.md` § Why this is blocked.

### Network-failure (transport) error path — the observable, confirmed live
Failing the transport of the secrets-list GET (`page.route(..., route.abort("failed"))`
— **case-authorised** by ELITEA-2349's own step 1, "on a throttled or offline
connection") produces, measured live:

| Observable | Value |
|---|---|
| `toast-alert` | visible, class contains `MuiAlert-colorError` |
| `toast-message` | **`Unknown error`** — filed as bug **#1910** |
| page shell | `secrets-page-title` + `secrets-add-button` present, add button **enabled** |
| `secret-row` | 0 |
| stack trace in body | none (`TypeError` / `Uncaught` / `at Object.` / `.jsx:` all absent) |
| toast auto-hide | still present after 10 s; clears on successful reload |
| console errors | 59 × `Maximum update depth exceeded` (#1203, bounded variant) |

Root cause of the bare message: `SecretsContent.jsx` calls
`buildErrorMessage(error)`, and `src/common/utils.jsx:146-184` has **no `FETCH_ERROR` /
`TIMEOUT_ERROR` / `PARSING_ERROR` branch** — every branch misses and it returns
`err?.data` → `undefined`, which the toast provider renders as `Unknown error`. It is a
**shared** helper, so every surface behaves this way on a transport failure.

Recovery after `page.unroute` + `reload()`: list `GET` → `200`/121 items, **10** rows
rendered (default page size), `toast-alert` count back to **0**.

Toast handles are on `main`: `toast-alert` (`src/components/Toast.jsx:60`),
`toast-message` (`:74`), `toast-dismiss-button` (`:71`) — **and `data-severity={severity}`
at `:61`**, which is how toast severity should be asserted here
(`[data-testid="toast-alert"][data-severity="error"]`, wired as
`SecretsPage.TOAST_ALERT_SEVERITY`). Do NOT reach for MUI's `MuiAlert-colorError` class:
a real app attribute exists and the class is library-internal.

`settings-content` (`src/[fsd]/pages/settings/index.jsx:268`) is the Settings content
pane's testid — the right SCOPE for any "no stack trace / not a blank page" check on a
settings surface, instead of a raw `body` handle. Note it is on `automation/testids`
only, **not yet on `main`**.

### Implementation-time note
`SecretsPage.navigate()` waits for `secret_row.first` to be visible, so it is **unusable
for any zero-row state** (error, empty, filtered-to-zero). Use the additive
`navigate_expecting_no_rows()` added by ELITEA-2349 instead of relaxing `navigate()` —
it has many merged callers.
