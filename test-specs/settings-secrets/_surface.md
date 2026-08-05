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
