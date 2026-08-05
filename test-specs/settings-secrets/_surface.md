# Settings → Secrets surface — exploration digest

Handle cache for live-confirmed handles/quirks on the Settings → Secrets
surface (`/settings/secrets`, renders `SecretsContent.jsx` / `SecretsTable.jsx`).
Not a substitute for execution — verify a handle as you use it. One writer at a
time; first confirmed by: qa-engineer analyst, ELITEA-2336, 2026-08-05.

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
