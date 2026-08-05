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
  there, assert `is_disabled()`.
- The case source text's per-step "Expected Result" column is largely
  generic/templated boilerplate ("Action completes without error and
  produces the expected UI state" repeated across ~10 rows) — don't treat
  it as literal per-element intent; the live component behavior is the
  ground truth (see ELITEA-2292 AFS § Axis 2 for the worked example on the
  header Delete button).

## AFS on file
- `l2_users-page-layout-and-components_ELITEA-2292.md` — page layout +
  header components + table columns/sortability + row content shape.
  No prior AFS existed for this surface before this run.
