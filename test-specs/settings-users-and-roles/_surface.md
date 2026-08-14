# Surface digest — Settings → Users and Roles

Confirmed live 2026-08-05 against `http://localhost:5173` (EliteaUI
`automation/testids`, DEV backend, project "UI Testing" / `${ELITEA_PROJECT_ID}`
= 400). One writer at a time — see `test-case-analysis` § 2b for the
update contract.

## Route
- `/settings/users` (bare path, reachable directly — same pattern as
  `/settings/tokens`, `/settings/notifications`).
- Route registered `src/[fsd]/app/routes/ProtectedRoutes.jsx:359-362` →
  `<Users />` (`src/[fsd]/pages/settings/Users.jsx`).

## Component tree
- `Users.jsx` (page) → `DrawerPage` + `DrawerPageHeader` (shared header:
  title/search/add-button) + `extraContent` (`EditUsersButton` batch-edit,
  `DeleteUserButton` batch-delete) + `UsersTable`.
- `UsersTable.jsx` → shared grid-table primitives:
  `GridTableContainer`/`GridTableHeader`/`GridTableBody`/`GridTableRow`/
  `GridTablePagination` (same stack `TokensTable.jsx`/`SecretsTable.jsx`
  use) + per-row `EditUsersButton`/`DeleteUserButton` (same components as
  the header, different props: no `isBatchEdit`/`useSecondaryButton`).
- Columns (`USERS_COLUMNS`, `UsersTable.jsx`): `name` (sortable), `email`
  (sortable, hides <600px), `last_login` (sortable, hides <800px), `roles`
  → label "Role" (not sortable, hides <1000px), `actions` (not sortable).
  `name` and `actions` are rendered OUTSIDE `GridTableRowDataCell` (name via
  `GridTableRowNameCell`, actions via `GridTableRowActionsCell`) — only
  `email`/`last_login`/`roles` go through `GridTableRowDataCell`.

## Testid state (as of 2026-08-05 exploration)
**Zero testids exist in this component tree today** (`Users.jsx`,
`UsersTable.jsx`, `EditUsersButton.jsx`, `DeleteUserButton.jsx` — confirmed
via grep, no hits). BUT the shared `DrawerPageHeader.jsx`/`GridTableHeader.jsx`/
`GridTableRow.jsx`/`GridTableRowNameCell.jsx` components already carry
testid-prop plumbing (added for `PersonalTokensPage`'s ELITEA-2277 work) —
most of this surface's testids are **call-site-only** additions, no shared
component edit needed:

| Prop (shared component) | Already wired? | Generates |
|---|---|---|
| `DrawerPageHeader.titleTestId` | yes | `data-testid` on header `Typography` |
| `DrawerPageHeader.slotProps.searchInput.testId` | yes | `data-testid` on `SimpleSearchBar` |
| `DrawerPageHeader.slotProps.addButton.testId` | yes | `data-testid` on add `IconButton` |
| `GridTableHeader.selectAllCheckboxTestId` | yes | `data-testid` on select-all checkbox |
| `GridTableHeader.columnTestIdPrefix` | yes | `{prefix}-column-header-{field}` per column |
| `GridTableRow.'data-testid'` | yes | `data-testid` on the row `Box` |
| `GridTableRow.checkboxTestId` | yes | `data-testid` on row checkbox |
| `GridTableRow.nameCellTestId` | yes | `data-testid` on the name cell |
| `GridTableRowDataCell` (email/last_login/roles) | **NO — no testid prop of any kind** | needs new `dataCellTestIdPrefix` prop threaded `GridTableRow` → `GridTableRowDataCell`, mirroring `columnTestIdPrefix`'s `{prefix}-column-header-{field}` shape as `{prefix}-column-value-{field}` |
| `EditUsersButton` / `DeleteUserButton` (feature components, used both header-batch and per-row) | **NO** | needs a new `testId` prop on each, `data-testid={testId}` on the `IconButton` — used TWICE per component (header instance + row instance), each needs its own testid value passed at its own call site |

## Live data observed
- 2 users in project 400 ("UI Testing"): `Levon Dadayan`
  (`levon_dadayan@epam.com`, role `admin`, last_login
  `2026-08-04T11:00:34`), `Test Bot` (`testbot@elitea.ai`, role `admin`,
  last_login `2026-08-05T00:05:24`). This floor is self-guaranteed — the
  acting admin is always a project member — unlike personal-tokens'
  deletable-data risk.
- Last-login format: `YYYY-MM-DDTHH:MM:SS`, no timezone offset/millis, on
  this build.
- Driving fetches: `GET /api/v2/admin/users/default/{projectId}?limit=20&offset=0`,
  `GET /api/v2/admin/roles/default/{projectId}?limit=20&offset=0` — both
  200 OK, fire on every page mount (`refetchOnMountOrArgChange: true`).

## Gotchas
- `EditUsersButton`/`DeleteUserButton` are DUAL-USE components — rendered
  once in the page header (`isBatchEdit`/`useSecondaryButton`, disabled
  until a row is selected) and once per row (plain instance). A future
  testid prop addition must thread a distinct value at EACH call site, or
  header and row instances collide on the same testid.
- Header batch Edit/Delete buttons are correctly DISABLED on initial page
  load (`disabled={!selectedUsers.length}`) — don't assert `is_enabled()`
  there, assert `is_disabled()`. Note (ELITEA-2304): the enabling condition
  is ANY non-empty selection (`disabled={!selectedUsers.length}`), not
  specifically "two or more" — a single selected row already enables it.
- The case source text's per-step "Expected Result" column is largely
  generic/templated boilerplate ("Action completes without error and
  produces the expected UI state" repeated across ~10 rows) — don't treat
  it as literal per-element intent; the live component behavior is the
  ground truth (see ELITEA-2292 AFS § Axis 2 for the worked example on the
  header Delete button).
- **Project-topology constraint (ELITEA-2304, critical for any write-flow
  case on this surface): the acting test account (`testbot@elitea.ai`) has
  `admin` role, and therefore the header/row Edit-Delete UI at all, ONLY in
  project 400 ("UI Testing").** Confirmed live across every other project
  reachable from the sidebar selector — `Elitea Testing Team` (471, 15
  users), `Bugs & Features` (406, 29 users), `Elitea Development` (25, 23
  users) — Test Bot holds `viewer` (or isn't listed on page 1) in all three,
  and the Users page renders **no** batch-Edit/Delete buttons and **no**
  per-row action icons at all there (permission-gated out entirely, not
  merely disabled). Any case needing 3+ safely-mutable users for a
  write-flow (this surface's only write-capable project has exactly 2,
  one of which is the acting account) must seed disposable users via
  "Invite users" rather than relying on existing project-471/406/25 data —
  those projects are unreachable for mutation regardless of user count.
- **Inviting a user works instantly for edit/delete purposes, no
  acceptance needed** (ELITEA-2304): a freshly-invited row appears
  immediately in the table with Name = the invited email, Last login =
  `-`, the selected initial role, and full row-level Edit/Delete actions —
  confirmed live, no login/acceptance step required. Safe, fast seed
  mechanism for any case needing extra mutable user rows on this surface.
- **Edit-roles dialog (`EditUserRolesDialog.jsx`, shared by both the header
  batch-edit and per-row edit instances) had ZERO testids before ELITEA-2304**
  — confirmed via full-file read. Added: `dialogTestId`/`titleTestId` (thread
  onto `Modal.BaseModal`'s pre-existing `data-testid`/`titleTestId` props),
  `roleSelectTestId` (thread onto `Select.SingleSelect`'s pre-existing
  `data-testid` prop — auto-generates a `-combobox` suffix testid too, per
  `SingleSelect.jsx`'s existing `SelectDisplayProps` logic), and
  `saveButtonTestId` (new `data-testid` on the dialog's own custom Save
  `Button.BaseBtn` — this dialog passes a custom `actions` node to
  `BaseModal`, so `BaseModal`'s own `confirmButtonTestId`/`onConfirm`
  mechanism is bypassed and doesn't apply). Wired ONLY at `Users.jsx`'s
  header (`isBatchEdit`) `EditUsersButton` call site — the per-row instance
  in `UsersTable.jsx`'s `renderActions` still has no dialog testids (no
  case has exercised the row-level edit dialog yet).
- Role-select options (`admin`/`editor`/`viewer`) need NO new testid work —
  `SingleSelectMenuItem.jsx` unconditionally renders
  `data-testid={option.testId ?? 'select-option-' + option.value}` on every
  menu item regardless of grouped/flat mode, and `Users.jsx`'s
  `rolesOptions` already maps `{label: name, value: name}` — so
  `select-option-admin`/`-editor`/`-viewer` are live for free, same
  mechanism the project selector and Invite-users dialog already use.
- Batch-edit-roles driving request: `PUT /api/v2/admin/users/default/{projectId}`,
  response body `{"msg": "roles updated"}`, 200 OK — single call for however
  many users are selected (not one call per user).
- Per-user delete (row-level, used for cleanup of seeded users):
  `DELETE /api/v2/admin/users/default/{projectId}?id[]={user_id}` → `204 No
  Content`. Confirmation dialog is the generic `Modal.DeleteEntityModal`
  (testid `delete-confirm-button`, pre-existing, shared with other delete
  flows on this surface and elsewhere).

## AFS on file
- `l2_users-page-layout-and-components_ELITEA-2292.md` — page layout +
  header components + table columns/sortability + row content shape.
- `l2_batch-edit-roles-for-multiple-selected-users_ELITEA-2304.md` —
  header batch-edit-roles flow: select 2+ rows → header Edit enables →
  "Edit roles" dialog → select role → Save → selected rows update,
  unselected rows provably unchanged. Introduced the `users-edit-roles-*`
  dialog testids (see Gotchas above) and the seed-2-disposable-users
  pattern for write-flow cases on this surface.
- `l3_invite-user-invalid-email-validation_ELITEA-2307.md` — Invite-users
  dialog client-side email-format validation (no invite ever submitted).

## Confirmed handles (as of ELITEA-2307 analysis, 2026-08-05)

`InviteUserDialog.jsx` (`src/components/InviteUserDialog.jsx`) source-read +
live-confirmed:

- **Validation is BLUR-gated, not live-as-you-type.** `onChange={handleChange}`
  only updates the `emails`/`inputText` state; `onBlur={handleBlur}` is what
  calls `parseEmails()` and sets `error`/`helperText`. Typing `notanemail` or
  `user@` alone shows NO error (live-confirmed, snapshot right after
  `.fill()`); pressing `Tab` immediately surfaces
  `Invalid email: {email}` as a `<FormHelperText>` paragraph directly below
  the Emails field. Same "touched"-gating family as the Artifacts bucket-name
  form above — don't assert right after fill, blur first.
- Error text: exact, deterministic `Invalid email: {email}` — built by
  `validateEmails()` in the same file (regex-based, one shared prefix, emails
  joined by `, ` when multiple are invalid).
- **Error `<FormHelperText>` has ZERO testid today** — confirmed via
  `document.querySelectorAll('p')` filter live: `class="MuiFormHelperText-root
  Mui-error MuiFormHelperText-sizeSmall css-..."`, `data-testid: null`.
  `testid needed: users-invite-emails-error-text` — thread a new
  `emailsErrorTestId` prop the same way `emailsInputTestId` already threads
  (`Users.jsx`'s `InviteUserDialog` call site), landing on the
  `<FormHelperText>` node itself (a NEW prop — unlike `emailsInputTestId`,
  which uses `inputProps` to reach the nested `<textarea>`, this one is a
  direct prop on the JSX element being tagged, no `slotProps` indirection
  needed).
- Invite (confirm) button (`users-invite-confirm-button`, pre-existing) stays
  disabled while `error` is true (`disabled={!emails.length ||
  !selectedRoles.length || error}`) — no request ever fires for an
  invalid-email attempt; don't reuse `AdminUsersPage.invite_users()` (it
  awaits a POST response) for this path.
