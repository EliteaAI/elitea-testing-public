# Test Case: Users page loads with correct layout and components

## Metadata
- **TMS ID**: ELITEA-2292
- **Source case**: `.agents/automation/elitea-2292-users-page-layout/cases/ELITEA-2292.md`
  (snapshot; TMS module `settings-users-and-roles`)
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter `priority: high`). **pytest
  marker: `@pytest.mark.p1`** — project convention TMS `high` → AFS `l2_`
  filename prefix → pytest `p1` (confirmed pattern against `test-specs/settings-personal-tokens/l3_personal-tokens-page-layout-and-components_ELITEA-2277.md`,
  which used TMS `medium` → `l3_` → `p2`; see
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `UI Testing` /
  `${ELITEA_PROJECT_ID}` = 400)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`
  — confirmed Admin permissions live: header edit/delete/invite controls and
  the users table all rendered, which are gated behind `PERMISSIONS.users.*`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth) with
  Admin role / `PERMISSIONS.users.view` (and `.edit`/`.delete`/`.create` for
  the header-level action buttons — all four permission checks gate
  independently in `Users.jsx`; the acting admin user satisfies all of them).
- Active project has **at least one user** — in practice this floor is
  self-guaranteed (the acting admin account is always a member of its own
  project's user list), unlike the personal-tokens case's data-deletable
  risk. Confirmed live: `${ELITEA_PROJECT_ID}` (400, "UI Testing") carries 2
  users (`Levon Dadayan`, `Test Bot`), both role `admin` — reused, real
  existing data, not seeded by this case. If the list were ever empty,
  `GridTableContainer`'s `emptyMessage="No users"` would render instead of
  the table (`UsersTable.jsx` → `isEmpty={sortedUsers.length === 0 &&
  !isFetching}`), which would make steps 4–6 (columns, row content)
  inapplicable — flagged for the implementer as a theoretical risk, not
  blocking `ready-for-automation` since it cannot occur under a real login.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `400` ("UI Testing" project) — confirmed via the
  sidebar project badge and the live `GET /api/v2/admin/users/default/400`
  request.
- 2 existing users under this project (see Preconditions) — used read-only;
  this case never creates, edits, or deletes a user.

## Test Steps
1. Navigate to `${BASE_URL}/settings/users` (bare path — project convention,
   `.agents/testing.md` "page objects call `navigate(...)` with bare paths";
   confirmed reachable directly, same pattern as `/settings/tokens` and
   `/settings/notifications`).
   - **Verify**: the users table body (testid `user-row`, `.first()`)
     becomes visible — confirms the page loaded past the loading spinner AND
     the empty-state precondition did not trigger.
2. **Verify** the page header title (testid `users-page-title`) has exact
   text `"Users"`.
3. **Verify** the header-level components, all present in the top-right
   region:
   - Search input (testid `users-search-input`) visible, with placeholder
     text **exactly** `"Search "` (trailing space — confirmed live and in
     `Users.jsx` source: `placeholder: 'Search '`).
   - Header batch-Edit (pencil) button (testid `users-header-edit-button`)
     visible **and disabled** (no rows selected on initial load —
     `disabled={!selectedUsers.length}` in `Users.jsx`, confirmed live).
   - Header batch-Delete (trash) button (testid `users-header-delete-button`)
     visible **and disabled** (same reason).
   - Invite-users "+" button (testid `users-invite-button`) visible **and
     enabled**.
4. **Verify** the table header shows a select-all checkbox (testid
   `user-select-all-checkbox`), present and unchecked.
5. **Verify** the table header shows **exactly five** field columns, via the
   `[data-testid^="user-column-header-"]` prefix selector (count == 5), with
   these individual testids and exact label text, in this order:
   `user-column-header-name` ("Name"), `user-column-header-email` ("Email"),
   `user-column-header-last_login` ("Last login"),
   `user-column-header-roles` ("Role"), `user-column-header-actions`
   ("Actions"). For the three sortable columns (Name, Email, Last login),
   **verify a sort-indicator `<svg>` is present**, scoped inside that
   column's own testid box (`.locator("svg")` chained off the testid-scoped
   element — locating within an already-testid-scoped element, not a raw
   page-level selector). For the two non-sortable columns (Role, Actions),
   **verify no such `<svg>` is present** inside their testid box.
6. For the **first** user row (testid `user-row`, `.first()`):
   - **Verify** a row checkbox (testid `user-row-checkbox`) is present.
   - **Verify** the Name cell (testid `user-row-name`) has non-empty text.
   - **Verify** the Email cell (testid `user-column-value-email`) text
     matches an email pattern (`.+@.+\..+`).
   - **Verify** the Last login cell (testid `user-column-value-last_login`)
     text matches the ISO-datetime pattern observed live —
     `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$` (no timezone offset/millis in
     this build's rendering, confirmed against both existing rows:
     `2026-08-04T11:00:34`, `2026-08-05T00:05:24`).
   - **Verify** the Role cell (testid `user-column-value-roles`) has
     non-empty text (confirmed live: `admin` on both existing rows).
   - **Verify** the row-level Edit (pencil) icon (testid
     `user-row-edit-button`) and Delete (trash) icon (testid
     `user-row-delete-button`) are both visible.
7. **Verify no console error or warning** was raised by the page load
   (side-channel check — confirmed live: 0 console errors, 0 warnings on
   this run), and the driving API calls resolved 200 OK: `GET
   /api/v2/admin/users/default/400?limit=20&offset=0` and `GET
   /api/v2/admin/roles/default/400?limit=20&offset=0` (both confirmed live).

## Expected Results
- Page loads with header "Users", a `"Search "`-placeholder input, disabled
  header Edit/Delete buttons (no selection), and an enabled "+" invite
  button, all in the top-right region per the case's layout description.
- Table header shows a select-all checkbox plus exactly 5 field columns:
  Name (sortable), Email (sortable), Last login (sortable), Role
  (non-sortable), Actions (non-sortable).
- Every visible user row shows: a row checkbox, non-empty name, an
  email-shaped email, an ISO-datetime-shaped last-login value, a non-empty
  role label, and both Edit/Delete action icons.
- No console errors or warnings; both driving list-fetch requests return 200
  OK.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as a user with Admin role | User is authenticated and lands on the expected landing page | `auth_state` fixture (localhost dev-token) | implicit precondition — confirmed live: header/table render, which are permission-gated | asserted |
| 2 Navigate to Settings → Users | Target page/section loads successfully | AFS step 1 | `step 1`: `user-row` testid becomes visible | asserted |
| 3 Verify the page header shows "Users" | Condition holds as described | AFS step 2 | `step 2`: `users-page-title` exact text | asserted |
| 4 Verify header-level components are present (parent bullet) | Condition holds as described | AFS step 3 (decomposed into 4 sub-checks) | `step 3` | asserted |
| 5 Search input field | Action completes without error and produces the expected UI state | AFS step 3 | `step 3`: `users-search-input` visible + exact placeholder | asserted |
| 6 Edit (pencil) icon button (header) | Action completes without error and produces the expected UI state | AFS step 3 | `step 3`: `users-header-edit-button` visible + disabled | asserted |
| 7 Delete (trash) icon button (header) | Operation completes successfully; state updates and confirmation is shown | AFS step 3 | `step 3`: `users-header-delete-button` visible + disabled — *"operation completes"/"confirmation shown" not applicable: this case only verifies the button's presence/state on page load, it never clicks it (that would be a delete-flow case, out of scope here — see Axis 2 note)* | asserted (presence/state only) |
| 8 "+" button to invite users | Action completes without error and produces the expected UI state | AFS step 3 | `step 3`: `users-invite-button` visible + enabled | asserted |
| 9 Verify the users table has the following columns (parent bullet) | Condition holds as described | AFS steps 4–5 (decomposed) | `step 4`/`step 5` | asserted |
| 10 Checkbox (for batch selection) | Action completes without error and produces the expected UI state | AFS step 4 | `step 4`: `user-select-all-checkbox` present + unchecked | asserted |
| 11 Name (sortable ↕) | Action completes without error and produces the expected UI state | AFS step 5 | `step 5`: `user-column-header-name` text + scoped sort-icon present | asserted |
| 12 Email (sortable ↕) | Action completes without error and produces the expected UI state | AFS step 5 | `step 5`: `user-column-header-email` text + scoped sort-icon present | asserted |
| 13 Last login (sortable ↕) | Action completes without error and produces the expected UI state | AFS step 5 | `step 5`: `user-column-header-last_login` text + scoped sort-icon present | asserted |
| 14 Role | Action completes without error and produces the expected UI state | AFS step 5 | `step 5`: `user-column-header-roles` text + scoped sort-icon ABSENT | asserted |
| 15 Actions (per-row Edit pencil + Delete trash icons) | Action completes without error and produces the expected UI state | AFS step 5 (header) + AFS step 6 (per-row icons) | `step 5`: `user-column-header-actions` text + scoped sort-icon ABSENT; `step 6`: `user-row-edit-button`/`user-row-delete-button` visible | asserted |
| 16 Verify each row shows: name, email, last login in ISO datetime format, role label, and action icons | Condition holds as described | AFS step 6 | `step 6`: `user-row-name`/`user-column-value-email`/`user-column-value-last_login`/`user-column-value-roles` content + action icons, on the first row *(live-observed identical shape on both existing rows during exploration — see Axis 2 note, same row-scope reasoning as ELITEA-2277)* | asserted |
| 17 Verify the page does not show any errors or permanent loading state | Condition holds as described | AFS step 1 (loading) + AFS step 7 (errors) | `step 1`: table renders past spinner; `step 7`: 0 console errors/warnings + both list fetches 200 OK | asserted |
| Expected Final State: Verify the page does not show any errors or permanent loading state | (restates step 17) | AFS step 1 + AFS step 7 | same as row 17 | asserted *(no separate row needed — identical to step 17)* |

## Axis 2 — Analyst additions
- `step 1` asserts `user-row` visibility as a **precondition proof**, not
  just a navigation check — *added: distinguishes "page loaded, table
  present" from "page loaded, empty state shown instead" (the
  `GridTableContainer` `emptyMessage="No users"` code path), which the case
  text doesn't address but would change what steps 4–6 can even observe.
  Unlike the personal-tokens sibling case, this floor is effectively
  guaranteed (the acting admin is always a project member), so it is
  documented rather than flagged as an operational risk.*
- `step 3` asserts the header Edit/Delete buttons are **disabled** on
  initial load — *added: the case's own expected-result text for step 7
  ("Operation completes successfully; state updates and confirmation is
  shown") is generic boilerplate that does not match what this LAYOUT case
  actually exercises (it never clicks Delete); the live, correct behavior —
  disabled with nothing selected — is what a layout assertion should
  capture instead. Case-text drift, not a defect (reverse-masking guard,
  `test-case-analysis` § Classify findings) — the case's per-step
  "Expected Result" column reads as templated placeholder text repeated
  across nearly every row (steps 5–15 all say some variant of "Action
  completes without error and produces the expected UI state"), not
  authored per-element intent.*
- `step 5` adds an explicit **sort-indicator presence/absence** check on
  each column header — *added: the case's own wording literally marks three
  columns "(sortable ↕)" and two without that marker; asserting only the
  header text would miss a regression that silently drops sortability (or
  wrongly adds it to Role/Actions).*
- `step 5` adds an explicit **count assertion** (`== 5`) on the field-column
  testids — *added: same "exactly N" discipline as the personal-tokens
  sibling AFS; catches a 6th unnamed column slipping in undetected.*
- `step 6` adds **content-shape assertions** (email pattern, ISO-datetime
  pattern) rather than just presence — *added: the case's own wording
  explicitly calls out "last login in ISO datetime format" as a format
  requirement, not just "a value is shown."*
- `step 7` adds a **no-console-error/warning** side-channel check plus the
  two driving fetches' status codes — *added: standard practice per
  `test-case-analysis` § 3 "Check the side channels," confirmed live there
  are none on this build, and it is the most direct machine-checkable proxy
  for the case's own "does not show any errors" wording.*
- Row-scope note (same reasoning as ELITEA-2277's sibling AFS): case step 16
  says "each row" (plural); this AFS automates the **first row** and
  documents that both of the 2 existing rows showed the identical
  cell-content shape during live exploration. A full per-row loop is a
  reasonable future Gap-assertion extension, not required today.

## Cleanup
None — this case is read-only against existing user data; no entities are
created, modified, or deleted.

## Concrete Handles (discovered during exploration)

Locator policy is testid-only (`.agents/role-overrides.md` / `.agents/testing.md`
§ Locator policy) — every row below is a testid the implementer must ensure
exists, either by wiring an **already-supported** shared-component prop
(call-site only, no shared-component edit) or by adding **new** support.

| Element | File | Recommended testid | How to add |
|---|---|---|---|
| Page header title ("Users") | `DrawerPageHeader.jsx` (shared, same component `PersonalTokensPage`/`SecretsPage` use) — `titleTestId` prop **already threaded** (`data-testid={titleTestId}` on the `Typography`) | `users-page-title` | Call-site only: pass `titleTestId="users-page-title"` on `Users.jsx`'s `<DrawerPageHeader title="Users" ... />`. |
| Search input | `DrawerPageHeader.jsx` → `slotProps.searchInput.testId` **already threaded** onto `Input.SimpleSearchBar`'s `data-testid` | `users-search-input` | Call-site only: add `testId: 'users-search-input'` to `Users.jsx`'s `slotProps.searchInput` object (alongside existing `search`/`onChangeSearch`/`placeholder`). |
| "+" invite button | `DrawerPageHeader.jsx` → `slotProps.addButton.testId` **already threaded** onto the add `IconButton`'s `data-testid` | `users-invite-button` | Call-site only: add `testId: 'users-invite-button'` to `Users.jsx`'s `slotProps.addButton` object (alongside `onAdd`/`tooltip`/`tourId`). |
| Header batch-Edit (pencil) button | `EditUsersButton.jsx` (feature component, used both as header batch-edit `extraContent` and per-row edit — **no testid support today**, confirmed via grep) | `users-header-edit-button` | Add a new `testId` prop to `EditUsersButton`, `data-testid={testId}` on its `IconButton`; pass `testId="users-header-edit-button"` at `Users.jsx`'s `extraContent` call site (the `isBatchEdit` instance). |
| Header batch-Delete (trash) button | `DeleteUserButton.jsx` (feature component, used both as header batch-delete `extraContent` and per-row delete — **no testid support today**, confirmed via grep) | `users-header-delete-button` | Add a new `testId` prop to `DeleteUserButton`, `data-testid={testId}` on its `IconButton`; pass `testId="users-header-delete-button"` at `Users.jsx`'s `extraContent` call site (the `useSecondaryButton` instance). |
| Table select-all checkbox | `GridTableHeader.jsx` (shared) — `selectAllCheckboxTestId` prop **already threaded** onto `Checkbox.BaseCheckbox`'s `data-testid` | `user-select-all-checkbox` | Call-site only: add `selectAllCheckboxTestId="user-select-all-checkbox"` to `UsersTable.jsx`'s `<GridTableHeader ... />` call. |
| Table column headers (5) | `GridTableHeader.jsx` (shared) — `columnTestIdPrefix` prop **already threaded**, generates `{prefix}-column-header-{field}` per column | `user-column-header-name`, `-email`, `-last_login`, `-roles`, `-actions` | Call-site only: add `columnTestIdPrefix="user"` to `UsersTable.jsx`'s `<GridTableHeader ... />` call — identical mechanism `personal-token-column-header-*` already uses. |
| User table row | `GridTableRow.jsx` (shared) — `'data-testid'` prop **already threaded** | `user-row` | Call-site only: add `data-testid="user-row"` to `UsersTable.jsx`'s `<GridTableRow key={row.id} ... />` call — static value repeated per row (same pattern as `token-row`). |
| Row checkbox | `GridTableRow.jsx` (shared) — `checkboxTestId` prop **already threaded** onto `Checkbox.BaseCheckbox`'s `data-testid` | `user-row-checkbox` | Call-site only: add `checkboxTestId="user-row-checkbox"` to the same `<GridTableRow>` call. |
| Row Name cell | `GridTableRow.jsx` → `GridTableRowNameCell.jsx` (shared) — `nameCellTestId` prop **already threaded** onto the name `Typography`/tooltip element | `user-row-name` | Call-site only: add `nameCellTestId="user-row-name"` to the same `<GridTableRow>` call. |
| Row Email / Last login / Role cells | `GridTableRowDataCell.jsx` (shared, renders every non-name/non-actions data column) — **no testid support today**, confirmed via full-file read (no `data-testid`, no prefix prop of any kind) | `user-column-value-email`, `user-column-value-last_login`, `user-column-value-roles` | **New shared-component work**: thread a `dataCellTestIdPrefix` prop `GridTableRow.jsx` → `GridTableRowDataCell.jsx`, generating `data-testid={dataCellTestIdPrefix ? \`${dataCellTestIdPrefix}-column-value-${column.field}\` : undefined}` on the cell's wrapping `Box` — mirrors `GridTableHeader.jsx`'s existing `columnTestIdPrefix` → `{prefix}-column-header-{field}` mechanism exactly, applied to data cells instead of header cells. Then pass `dataCellTestIdPrefix="user"` at `UsersTable.jsx`'s `<GridTableRow>` call. **This is a shared-component change** (affects every other `GridTableRow` consumer only additively — the prop is optional and `undefined` when unset, so `SecretsTable`/`TokensTable`/`BucketAccessTable` are unaffected). |
| Row Edit (pencil) icon | `EditUsersButton.jsx` — same component as the header instance, per-row usage in `UsersTable.jsx`'s `renderActions` (no `isBatchEdit`) | `user-row-edit-button` | Same new `testId` prop as the header instance (see above); pass `testId="user-row-edit-button"` at `UsersTable.jsx`'s `renderActions` call site. |
| Row Delete (trash) icon | `DeleteUserButton.jsx` — same component as the header instance, per-row usage in `UsersTable.jsx`'s `renderActions` (no `useSecondaryButton`) | `user-row-delete-button` | Same new `testId` prop as the header instance; pass `testId="user-row-delete-button"` at `UsersTable.jsx`'s `renderActions` call site. |

**Sort-indicator icons (Name/Email/Last login)**: NOT a separate testid.
`GridTableHeader.jsx` already renders a `SortArrows` `<svg>` inside the
column's header `Box` only when `column.sortable && onSort` is true
(confirmed in source, `GridTableHeader.jsx:56-60`). Locate it via
`.locator("svg")` chained off the already-testid-scoped
`user-column-header-{field}` element — the sanctioned "locating within an
already-testid-scoped element" pattern (`.agents/testing.md`), not a raw
page-level selector.

Not touched by this case (no testid requested — scope discipline,
`.agents/role-overrides.md` "touches" = actually invoked on this test's
executed path):
- `InviteUserDialog` content (opens on "+" click; this case only verifies
  the button's presence/enabled state, never clicks it)
- `EditUserRolesDialog` / delete-confirmation `Modal.DeleteEntityModal`
  content (open on Edit/Delete click; this case never clicks either)
- `GridTablePagination` controls (2 rows fit on one page; case doesn't
  exercise pagination)
- Row hover state (`isHovered` styling) — not asserted by this case

## Network Behavior
- `GET /api/v2/admin/users/default/400?limit=20&offset=0` — user list
  (`useUserListQuery`), fires on page mount. Confirmed live: 200 OK.
- `GET /api/v2/admin/roles/default/400?limit=20&offset=0` — role list
  (`useRoleListQuery`), fires on page mount (drives the role-options list
  used by the Edit-role dialog; not directly rendered by this case's
  assertions). Confirmed live: 200 OK.
- `GET /api/v2/projects/project/default/400?check_public_role=true` —
  project-context fetch, fires on any settings-drawer page load, not
  specific to Users. Confirmed live: 200 OK.
- 0 console errors, 0 console warnings on this run.

## Known Defects Found During Exploration
None. All 17 case steps reproduce as authored on this build: header text,
search placeholder, header Edit/Delete/Invite buttons, select-all checkbox,
5 table columns with correct sortability, and both existing rows' content
(name, email, ISO last-login, role, action icons) — see embedded evidence
below. (One case-text drift noted and handled per the reverse-masking guard,
not a defect — see Axis 2's step-3 note on the generic per-step
"Expected Result" boilerplate.)

Evidence: `test-results/screenshots/ELITEA-2292-step-01-users-page-layout.png`
(viewport screenshot — header "Users", search input, disabled Edit/Delete
buttons, enabled "+" button, 5-column table, 2 rows each showing name,
email, ISO last-login, role "admin", and both action icons).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: no existing page object covers Settings → Users. Create
  `automation/pages/admin_users_page.py` (new file). Reuse the
  `PersonalTokensPage` (`automation/pages/personal_tokens_page.py`) as the
  closest structural reference — same shared `DrawerPageHeader`/
  `GridTableHeader`/`GridTableRow` component stack, same
  prefix-selector-for-count pattern.
- Column-header count assertion:
  `page.locator('[data-testid^="user-column-header-"]')` count == 5 (same
  prefix-selector mechanism as `personal-token-column-header-*`).
- Sort-indicator assertion: `self.column_header_name.locator("svg")` (and
  siblings for email/last_login) expected count == 1; `self.column_header_roles.locator("svg")`
  / `self.column_header_actions.locator("svg")` expected count == 0.
- Row-cell assertions: scope everything off `self.user_row.first` (or a
  dedicated `first_user_row` `LocatorDescriptor`-style helper matching
  `PersonalTokensPage.get_first_row_action_icon`'s pattern) — never a raw
  `nth-child`/CSS positional selector.
- Wait strategy: wait for `user_row` (`.first()`) to be visible before any
  column/row assertions — no `page.wait_for_timeout`, per
  `.agents/conventions.md`.
- ISO datetime regex: `re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$",
  text)` — confirmed live format on this build has no timezone
  offset/milliseconds.
- Header Edit/Delete buttons: assert `is_visible()` AND `is_disabled()` (NOT
  `is_enabled()`) — they are correctly disabled with nothing selected.
