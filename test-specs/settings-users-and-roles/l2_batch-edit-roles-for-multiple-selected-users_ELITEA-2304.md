# Test Case: Batch edit roles for multiple selected users

## Metadata
- **TMS ID**: ELITEA-2304
- **Source case**: `.agents/automation/elitea-2304-batch-edit-roles/cases/ELITEA-2304.md`
  (snapshot; TMS module `settings-users-and-roles`)
- **Linked Story**: none
- **Priority**: l2 (high, per case frontmatter `priority: high`). **pytest
  marker: `@pytest.mark.p1`** — project convention TMS `high` → AFS `l2_`
  filename prefix → pytest `p1` (same mapping as the sibling
  `l2_users-page-layout-and-components_ELITEA-2292.md`; see
  `.agents/memory/qa-engineer/priority_marker_drift_afs_vs_pytest_mark.md`).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `UI Testing` /
  `${ELITEA_PROJECT_ID}` = 400)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`
  — Admin permissions confirmed live in project 400 only; see Preconditions)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (localhost dev-token auth) with
  Admin role / `PERMISSIONS.users.edit` for the active project — this gates
  the header batch-Edit button's very rendering (`checkPermission(PERMISSIONS.users.edit)`
  in `Users.jsx`), not just its enabled state.
- **Live-discovered project-topology constraint (critical for automation
  safety — read before writing the test):** the acting test account
  (`${TEST_USER_EMAIL}` = `testbot@elitea.ai`, "Test Bot") holds `admin` role
  **only in project 400 ("UI Testing")**. Confirmed live across every other
  project reachable from the sidebar selector: `Elitea Testing Team` (471,
  15 users) → Test Bot is `viewer`; `Bugs & Features` (406, 29 users) → Test
  Bot not even listed on the first page; `Elitea Development` (25, 23 users)
  → Test Bot is `viewer`. In every one of those, the Users page header
  renders **no** batch-Edit/Delete buttons at all (permission-gated out) and
  each row's own Actions cell is empty (no per-row Edit/Delete icons either)
  — confirmed live, not merely disabled. **Project 400 is therefore the
  ONLY reachable project where this case's flow can even be attempted.**
- **Project 400 has exactly 2 pre-existing users** (per the ELITEA-2292
  sibling AFS's Preconditions): `Levon Dadayan` (`admin`) and `Test Bot`
  (`admin`, = the acting account itself). This is a genuine test-data gap
  against the case's own two demands together: "select two or more" AND
  "verify **unselected** users' roles remain unchanged" jointly require **at
  least 3 users** in the only project where the flow is reachable, one of
  which is the acting account whose own role must never be touched by an
  automated batch-edit (mutating the test runner's own admin role would
  strand every subsequent test in this project). **Resolution (seed
  minimally, confirmed live — see Test Data):** invite exactly 2 disposable
  users via the existing "Invite users" dialog (each becomes a normal row
  with a checkbox, editable role, and a per-row Delete icon — confirmed
  live, no email-acceptance step required for them to appear as edit/delete
  -able rows), batch-edit **only those two**, and assert the two
  **pre-existing** users (`Levon Dadayan`, `Test Bot`) — never selected —
  keep their original roles. This also means Test Bot's own role is
  **never selected and never touched** by this test, at any point.

## Test Data
### seed-minimal (see Preconditions — resolves the 2-user data-gap)
- Invite 2 disposable users into project 400 via the existing "Invite
  users" dialog, both with initial role **`editor`** (chosen deliberately
  distinct from the target role `viewer` so the edit is visibly a change,
  and distinct from `admin` so neither could be mistaken for a pre-existing
  admin row): e.g. `elitea-batch-edit-test1@example.com`,
  `elitea-batch-edit-test2@example.com` (fictitious `example.com` domain —
  no real mailbox needed; confirmed live the invited row appears
  immediately with Last login = `-`, and full Edit/Delete row actions — no
  acceptance/login step required for THIS case's flow).
  **Amendment (implementer exploration, 2026-08-05):** the invited row's
  **Name cell is EMPTY**, not "the email itself" as originally assumed —
  the invited email appears only in the row's Email column
  (`user-column-value-email`). Row lookup for the seeded users must
  therefore match on email text against the whole row (`user_row.filter
  (has_text=email)`), not on the Name cell. The driving invite request is
  confirmed live: `POST /api/v2/admin/users/default/400`, 200 OK.
- Batch-edit target role: **`viewer`**.
### reuse-existing (read-only — never selected, never mutated)
- `Levon Dadayan` (`levon_dadayan@epam.com`, role `admin`) — asserted
  unchanged.
- `Test Bot` (`testbot@elitea.ai`, role `admin`, = the acting test account)
  — asserted unchanged. **Never select this row.**

## Test Steps
1. Navigate to `${BASE_URL}/settings/users` on project 400 (reuse
   `AdminUsersPage.navigate()`'s existing two-hop project-switch flow from
   the ELITEA-2292 sibling — same precondition applies here: the env's
   default project is this user's private project, which hides Settings →
   Users entirely).
   - **Verify**: `user-row` (`.first()`) visible — confirms the table
     rendered past the loading spinner.
2. Seed test data: open "Invite users" (testid `users-invite-button`),
   enter the 2 disposable emails (comma-separated per the dialog's own
   label text), select role `editor`, click Invite.
   - **Verify**: the users table now lists 4 rows total (2 pre-existing +
     2 newly invited), each new row showing its email as the Name, `-` as
     Last login, and role `editor`.
3. Select the checkboxes on the **2 newly invited** rows only (never the
   `Levon Dadayan` or `Test Bot` rows).
   - **Verify**: both checkboxes become checked.
4. **Verify** the header batch-Edit (pencil) button (testid
   `users-header-edit-button`) is now **enabled** (was disabled with 0
   rows selected — confirmed live and in source,
   `disabled={!selectedUsers.length}` in `Users.jsx`; case text implies
   "two or more" is the activation threshold, but the live code enables on
   ANY non-empty selection — see Axis 2 note. This case's own flow selects
   2, which is well within the enabling condition either way, so the
   observation stands regardless of the exact threshold).
5. Click the header batch-Edit button.
   - **Verify**: the "Edit roles" dialog opens (testid
     `users-edit-roles-dialog`, visible), with title text (testid
     `users-edit-roles-title`) exactly `"Edit roles"`.
6. Select the role **`viewer`** in the dialog's Roles select (testid
   `users-edit-roles-select` / its MUI combobox child
   `users-edit-roles-select-combobox`; option testid
   `select-option-viewer`, the pre-existing shared
   `select-option-{value}` pattern — confirmed live, same mechanism as the
   project selector and the Invite-users role select).
   - **Verify**: the Save button (testid `users-edit-roles-save-button`)
     transitions from disabled to enabled (component logic:
     `disabled={!selectedRoles.length || !hasChangedRoles}` in
     `EditUserRolesDialog.jsx` — confirmed live).
7. Click Save (confirm the change).
   - **Verify**: the driving `PUT /api/v2/admin/users/default/400` request
     resolves 200 OK with body `{"msg": "roles updated"}` (confirmed live),
     the dialog closes, and the users list re-fetches
     (`GET /api/v2/admin/users/default/400?...` fires again, 200 OK).
8. **Verify** both selected (invited) users now show role `viewer` in the
   Role column (testid `user-column-value-roles`, scoped to each of their
   rows).
9. **Verify** the 2 unselected, pre-existing users — `Levon Dadayan` and
   `Test Bot` — still show role `admin` (unchanged) in the same Role
   column testid, scoped to their own rows.

## Expected Results
- The header batch-Edit button is disabled with nothing selected and
  becomes enabled once 2 (or more) rows are checked.
- Clicking it opens the "Edit roles" dialog; selecting a role and saving
  issues a single `PUT` that updates ONLY the selected users' roles.
- After save, the selected rows show the newly assigned role (`viewer`)
  and the unselected rows are provably unaffected (`Levon Dadayan` and
  `Test Bot` both remain `admin`).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | AFS step 1 | `step 1`: `user-row` visible | asserted |
| 2 Select checkboxes on two or more user rows | Control responds; expected next state is shown | AFS steps 2–3 (decomposed: seed data, then select) | `step 2`: 4 rows present; `step 3`: 2 checkboxes checked | asserted |
| 3 Verify the Edit (pencil) icon in the header becomes active | Condition holds as described | AFS step 4 | `step 4`: `users-header-edit-button` enabled | asserted |
| 4 Click the header Edit icon | Control responds; expected next state is shown | AFS step 5 | `step 5`: dialog opens | asserted |
| 5 Verify the "Edit roles" dialog opens | Condition holds as described | AFS step 5 | `step 5`: `users-edit-roles-dialog` visible, title text exact | asserted |
| 6 Select a new role (e.g., "viewer") | Control responds; expected next state is shown | AFS step 6 | `step 6`: `select-option-viewer` selected, Save enables | asserted |
| 7 Confirm the change | Operation completes successfully; state updates and confirmation is shown | AFS step 7 | `step 7`: `PUT .../admin/users/default/400` 200 OK, dialog closes, list refetches | asserted |
| 8 Verify all selected users now show "viewer" in the Role column | Condition holds as described | AFS step 8 | `step 8`: both invited rows' `user-column-value-roles` == "viewer" | asserted |
| 9 Verify unselected users' roles remain unchanged | Condition holds as described | AFS step 9 | `step 9`: `Levon Dadayan` + `Test Bot` rows' `user-column-value-roles` == "admin" | asserted |
| Expected Final State: Verify unselected users' roles remain unchanged | (restates step 9) | AFS step 9 | same as row above | asserted *(no separate row needed)* |

## Axis 2 — Analyst additions
- **Step 2 (seed data) is an addition the case text doesn't mention at
  all** — *added: the case assumes "two or more user rows" already exist
  as safely-selectable data, but live exploration found project 400 (the
  only project where this flow is reachable — see Preconditions) has
  exactly 2 pre-existing users, one of which is the acting test account
  itself. Without seeding, the only way to reach "two selected" is to
  include Test Bot's own row, which would mutate the test runner's own
  admin permissions — an unacceptable side effect for a shared automation
  account. Seeding 2 disposable invited users resolves this without ever
  touching the 2 pre-existing rows, and doubles as the concrete mechanism
  by which step 9's "unselected users" assertion becomes meaningful (a
  real control group that was never selected, not merely never re-checked
  after the same action).*
- **Step 4's "two or more" framing is looser in the live implementation
  than the case text implies** — *added, not a defect: `Users.jsx` disables
  the header Edit button via `disabled={!selectedUsers.length}` — i.e. ANY
  non-empty selection (including exactly 1) enables it, not specifically
  "two or more." This case's own steps select 2, so the assertion as
  written is satisfied either way; documented here so the implementer
  doesn't misread the case text as "assert exactly-1 leaves it disabled."*
- **Step 7 adds the driving `PUT` request + response-body assertion**
  beyond the case's generic "Operation completes successfully" wording —
  *added: this is the most direct machine-checkable proxy for "confirm the
  change," confirmed live (`{"msg": "roles updated"}`, 200 OK).*
- **Cleanup is load-bearing, not optional** — see § Cleanup. Because this
  case mutates real project data (even disposable seeded data), the
  automated test MUST delete the 2 seeded rows in a `finally`/fixture
  teardown so re-runs start from the same 2-user floor. This mirrors
  `.agents/testing.md` § Test data strategy ("seed minimally + clean up
  loudly only when the observable requires fresh state").

## Cleanup
- Delete the 2 seeded users via their row-level Delete (trash) icon
  (testid `user-row-delete-button`, pre-existing) → confirm in the generic
  `Modal.DeleteEntityModal` dialog (testid `delete-confirm-button`,
  pre-existing, confirmed live: driving request
  `DELETE /api/v2/admin/users/default/400?id[]={id}` → `204 No Content`).
  Must run even if an earlier assertion fails (`try`/`finally` or an
  equivalent pytest fixture teardown) — this project's user list is shared,
  reused, real data (`Levon Dadayan`/`Test Bot` are never touched, but the
  2 seeded rows must not accumulate across runs).
- Levon Dadayan's and Test Bot's roles are **never mutated** by this test,
  so nothing to revert for them.

## Concrete Handles (discovered during exploration)

Locator policy is testid-only (`.agents/role-overrides.md` / `.agents/testing.md`
§ Locator policy). All handles below are real testids confirmed live against
`http://localhost:5173` on 2026-08-05.

| Element | PROVENANCE | testid | Notes |
|---|---|---|---|
| Users table row / row checkbox / Name / Role cells / navigate() flow | on `automation/testids` only (awaiting human promotion to `main`) — `EliteaAI/EliteaUI@e54a8bd7` | `user-row`, `user-row-checkbox`, `user-row-name`, `user-column-value-roles` | Pre-existing, added under ELITEA-2292; reused as-is (`AdminUsersPage`) |
| Header batch-Edit button | on `automation/testids` only — `EliteaAI/EliteaUI@e54a8bd7` | `users-header-edit-button` | Pre-existing (`AdminUsersPage.header_edit_button`) |
| Row-level Delete icon | on `automation/testids` only — `EliteaAI/EliteaUI@e54a8bd7` | `user-row-delete-button` | Pre-existing; used for this case's cleanup only |
| Invite users "+" button | on `automation/testids` only — `EliteaAI/EliteaUI@e54a8bd7` | `users-invite-button` | Pre-existing (`AdminUsersPage.invite_button`) |
| Delete-confirmation Save button | on `automation/testids` only (pre-existing generic shared component, exact originating commit not traced — not in this case's diff) | `delete-confirm-button` | Generic `Modal.DeleteEntityModal` confirm button; used for cleanup only |
| Role-select menu options (`admin`/`editor`/`viewer`) | pre-existing generic mechanism, `SingleSelectMenuItem.jsx` — always renders `data-testid={option.testId ?? 'select-option-' + option.value}`, no new work needed | `select-option-{role}` e.g. `select-option-editor`, `select-option-viewer` | Same mechanism already used by the project selector and both role selects (Invite-users, Edit-roles) — reused, not newly added |
| **Edit roles dialog root** | **NEW — added this case, on `automation/testids` only** — `EliteaAI/EliteaUI@435ff111` | `users-edit-roles-dialog` | `Modal.BaseModal`'s pre-existing `data-testid` prop, threaded through `EditUserRolesDialog` → `EditUsersButton` → wired ONLY at `Users.jsx`'s header (`isBatchEdit`) call site — never at the per-row call site (this case never opens the row-level Edit dialog) |
| **Edit roles dialog title** | **NEW — added this case** — `EliteaAI/EliteaUI@435ff111` | `users-edit-roles-title` | `Modal.BaseModal`'s pre-existing `titleTestId` prop, same threading as above |
| **Edit roles — Roles select** | **NEW — added this case** — `EliteaAI/EliteaUI@435ff111` | `users-edit-roles-select` (root) / `users-edit-roles-select-combobox` (MUI `SelectDisplayProps` child, auto-generated by `SingleSelect.jsx`'s existing `${dataTestId}-combobox` suffix logic) | `Select.SingleSelect`'s pre-existing `data-testid` prop, newly threaded through `EditUserRolesDialog` |
| **Edit roles — Save button** | **NEW — added this case** — `EliteaAI/EliteaUI@435ff111` | `users-edit-roles-save-button` | New `data-testid` on `EditUserRolesDialog`'s own custom Save `Button.BaseBtn` (the dialog does not use `BaseModal`'s default `onConfirm`/`confirmButtonTestId` mechanism — it passes a custom `actions` node) |
| **Invite-users — Emails input** | **NEW — added by the implementer, on `automation/testids` only** — `EliteaAI/EliteaUI@ed2ddbb9` | `users-invite-emails-input` | **Amendment (implementer exploration, 2026-08-05): the analyst's "reused generic elements only, nothing new added there" claim for `InviteUserDialog` was WRONG** — live verification found the dialog had ZERO testids threaded from its `Users.jsx` call site (no `data-testid`/`titleTestId`/role-select-testid/confirm-button-testid props were ever passed, unlike `EditUserRolesDialog` above which already got this treatment). Added via `inputProps={{ 'data-testid': emailsInputTestId }}` on `Input.StyledInputEnhancer` — passing a bare `data-testid` prop lands on `MuiTextField`'s outer wrapper `<div>`, not the actual `<textarea>`; the `inputProps` → `slotProps.htmlInput` path is required to land it on the editable node itself (confirmed live: `TEXTAREA`, not `DIV`) |
| **Invite-users — Roles select** | **NEW — added by the implementer** — `EliteaAI/EliteaUI@ed2ddbb9` | `users-invite-role-select` (root) / `users-invite-role-select-combobox` (same `SelectDisplayProps` auto-suffix mechanism as the Edit-roles select) | `Select.SingleSelect`'s pre-existing `data-testid` prop, newly threaded through `InviteUserDialog` |
| **Invite-users — Invite (confirm) button** | **NEW — added by the implementer** — `EliteaAI/EliteaUI@ed2ddbb9` | `users-invite-confirm-button` | New `data-testid` on `InviteUserDialog`'s own custom Invite `Button.BaseBtn` (same custom-`actions`-node shape as the Edit-roles Save button) |

**Scope discipline note (canon ruling #511):** the dialog's Cancel button
was intentionally left WITHOUT a testid — this case's steps never click
Cancel, so wiring `cancelButtonTestId` would be an unreferenced addition.
The `EditUserRolesDialog` component accepts the prop capability generically
(consistent with `BaseModal`'s own existing `cancelButtonTestId` pattern)
but it is simply never passed a value at this case's call site.

Not touched by this case (no testid requested — scope discipline):
- The per-row `EditUsersButton`/`EditUserRolesDialog` instance (single-user
  edit) — this case only ever opens the HEADER batch-edit instance.
- `InviteUserDialog`'s Cancel button and dialog-root/title testids — this
  case's steps never click Cancel and never assert the dialog's own
  visibility/title (only the 3 fields it actually types/selects/clicks
  into: emails, role, Invite), so none of those got a testid — same scope
  discipline as the Edit-roles dialog's Cancel button above.

## Network Behavior
- `GET /api/v2/admin/users/default/400?limit=20&offset=0` — user list,
  refetches after every mutating action (invite, batch-edit, delete).
  Confirmed live: 200 OK throughout.
- `POST /api/v2/admin/users/default/400` — the invite-users call.
  **Confirmed live by the implementer, 2026-08-05** (the analyst's pass
  hadn't captured it): 200 OK.
- `PUT /api/v2/admin/users/default/400` — the batch-edit-roles call.
  Confirmed live: 200 OK, response body `{"msg": "roles updated"}`.
- `DELETE /api/v2/admin/users/default/400?id[]={user_id}` — per-user
  delete (cleanup only, one call per seeded user). Confirmed live: `204 No
  Content`.
- 0 console errors observed during the full flow (invite → select → edit
  roles → save → verify → cleanup).

## Known Defects Found During Exploration
None. The batch-edit-roles flow reproduces as authored on this build: header
Edit button enables on selection, "Edit roles" dialog opens with a role
select, Save issues a single batch `PUT` that updates only the selected
users, and unselected users are provably unaffected. One case-text framing
note (not a defect) is recorded in Axis 2 (the "two or more" activation
threshold is actually "any non-empty selection" in the live code).

## Blocked Steps
None — the environment/data gap identified in Preconditions was resolved
within this case's own scope (seed 2 disposable users; see Test Data /
Axis 2), so nothing is blocked.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: extend the existing `automation/pages/admin_users_page.py`
  (`AdminUsersPage`, from ELITEA-2292) rather than creating a new file —
  add:
  - `LocatorDescriptor(testid="users-edit-roles-dialog")` → `edit_roles_dialog`
  - `LocatorDescriptor(testid="users-edit-roles-title")` → `edit_roles_dialog_title`
  - `LocatorDescriptor(testid="users-edit-roles-select-combobox")` → `edit_roles_select_combobox`
  - `LocatorDescriptor(testid="users-edit-roles-save-button")` → `edit_roles_save_button`
  - A class-level template constant for the role-option testid, matching
    the existing `SELECT_OPTION = '[data-testid="select-option-{}"]'`
    already on `AdminUsersPage` (reuse it — don't redefine) for
    `select-option-viewer` / `select-option-editor`.
  - Helper methods: `select_users_by_row(indices_or_emails)` (checks
    specific row checkboxes — NOT select-all), `open_edit_roles_dialog()`,
    `select_role_in_dialog(role_name)`, `save_edit_roles()`,
    `get_role_cell_for_row(row_locator)` (reuse the existing
    `USER_COLUMN_VALUE_ROLES_SELECTOR` pattern, scoped per-row rather than
    always `.first`).
  - Invite-flow helpers: `open_invite_dialog()` (via existing
    `invite_button`), `invite_users(emails: list[str], role: str)` — needs
    3 NEW `LocatorDescriptor`s (see Concrete Handles amendment above):
    `invite_emails_input` (`users-invite-emails-input`),
    `invite_role_select_combobox` (`users-invite-role-select-combobox`),
    `invite_confirm_button` (`users-invite-confirm-button`).
- Test data: parametrize the 2 seed email addresses per test run (e.g. with
  `request.node.name` or a UUID suffix) to avoid collisions if tests run
  more than once without a clean DB — the case doesn't require identical
  emails across runs, only that they're disposable and distinct from
  existing rows.
- Selecting specific rows (not select-all): locate each seeded user's row
  by matching the known seed email against the WHOLE row's text (e.g.
  `user_row.filter(has_text=email)`), then click that row's own checkbox
  — never rely on row order/position. **Amendment (implementer
  exploration): match on email, not Name** — the invited row's Name cell
  is empty (see Test Data amendment above), so a Name-cell match would
  never find it.
- Wait strategy: after Save, wait for the `PUT` response (`page.expect_response`
  matching `/admin/users/default/` + method PUT) before asserting on the
  refreshed Role cells — no `page.wait_for_timeout`, per
  `.agents/conventions.md`.
- Cleanup: implement as a pytest fixture (`seeded_batch_edit_users` or
  similar in `automation/fixtures/`) that invites the 2 users, yields their
  identifying info, and deletes them in teardown regardless of test
  outcome — per `.claude/rules/ui-tests.md` § Test Data Lifecycle and
  `.claude/rules/api-patterns.md` § Anti-Patterns (fixtures live in
  `automation/fixtures/`, never inline in the test file).
