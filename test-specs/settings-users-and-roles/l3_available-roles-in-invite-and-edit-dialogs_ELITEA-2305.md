# Test Case: Available roles in Invite and Edit dialogs are admin, editor, and viewer

## Metadata
- **TMS ID**: ELITEA-2305
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2305.md`
- **Linked Story**: none
- **Priority**: l3 (`priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in, `admin` in project 400 — both the "+" invite button
  (`PERMISSIONS.users.create`) and the per-row Edit icon
  (`PERMISSIONS.users.edit`) are permission-gated and absent otherwise.
- At least one user row exists (self-guaranteed — the acting admin).

## Test Data
### reuse-existing
- `${USERS_TEAM_PROJECT_ID}` = `400`; the FIRST rendered user row, used
  read-only as the Edit-dialog subject. **The dialog is opened and dismissed;
  no role is ever changed and Save is never clicked.**

## Test Steps
1. Navigate to Settings -> Users.
   - **Verify**: at least one row renders.
2. Click "+" to open the Invite-users dialog.
   - **Verify**: `users-invite-dialog` is visible.
3. Open the Roles dropdown in the Invite dialog.
   - **Verify**: **exactly three** role options are offered, with texts
     `admin`, `editor`, `viewer` in that order, addressed by
     `select-option-admin` / `-editor` / `-viewer`.
4. Close the dialog (Close × button) and confirm it unmounted.
5. Click the Edit (pencil) icon on the FIRST user row and open the Roles
   dropdown in the "Edit roles" dialog.
   - **Verify**: `users-row-edit-roles-dialog` is visible.
6. **Verify** the SAME three options: exactly three, texts `admin`,
   `editor`, `viewer`.
   - **Verify** explicitly that the Edit dialog's option list is **equal to**
     the Invite dialog's option list captured in step 3 — the case's word
     "same" asserted as an actual equality, not two independent checks that
     happen to agree.
7. Dismiss the Edit dialog without saving.
   - **Verify**: the dialog unmounts and the first row's Role cell text is
     unchanged from before step 5 (nothing was mutated).
8. **Verify** no unexpected console errors across the flow.

## Expected Results
- Both dialogs offer exactly the three project roles admin / editor /
  viewer, and the two lists are identical.
- No role is changed; the table is left as found.
- No console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated controls render | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible | asserted |
| 2 Click "+" to open Invite users dialog | Control responds; expected next state is shown | step 2 | `step 2`: `users-invite-dialog` visible | asserted |
| 3 Open the Roles dropdown — verify exactly three options: admin, editor, viewer | Target page/section loads successfully | step 3 | `step 3`: option count == 3 AND texts == `[admin, editor, viewer]` | asserted |
| 4 Close the dialog | Action completes without error and produces the expected UI state | step 4 | `step 4`: Close clicked, dialog count 0 | asserted |
| 5 Click Edit on any user row — open the Roles dropdown | Control responds; expected next state is shown | step 5 | `step 5`: `users-row-edit-roles-dialog` visible, roles menu opened | asserted |
| 6 Verify the same three options: admin, editor, viewer | Condition holds as described | step 6 | `step 6`: count == 3, texts == `[admin, editor, viewer]`, AND list equals step 3's captured list | asserted |
| Expected Final State: Verify the same three options: admin, editor, viewer | (restates step 6) | step 6 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- Step 6 asserts the two lists are **equal to each other**, not merely each
  equal to a literal — *added: the case's operative word is "the SAME three
  options"; comparing both against a hardcoded triple would still pass if the
  product's two dialogs had drifted apart AND the case text had gone stale
  together. Comparing them to each other is what the case actually claims.*
- Steps 3/6 assert **exactly three**, not "the three are present" — *added:
  the case enumerates; a fourth role would be a real regression.*
- Step 7 asserts the row's Role cell is **unchanged** — *added: this case
  opens a MUTATING dialog purely to read it. The unchanged assertion is what
  proves the read was non-destructive, and it converts an invisible
  side-effect bug into a failing test.*
- Step 8 no-console-errors side-channel check — *standard discipline;
  confirmed 0 errors live.*

## Cleanup
None required — the Edit dialog is dismissed without saving (Save stays
disabled until a role actually changes, and this case never changes one).
Step 7's unchanged-role assertion is the cleanliness proof.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| "+" invite button | `users-invite-button` | pre-existing (ELITEA-2292) |
| Invite dialog root | `users-invite-dialog` | **NEW** — EliteaAI/EliteaUI@8f559586 (ELITEA-2295) |
| Invite dialog Close (×) | `users-invite-close-button` | **NEW** — same commit |
| Invite Roles combobox | `users-invite-role-select-combobox` | pre-existing (ELITEA-2304) |
| Row Edit (pencil) icon | `user-row-edit-button` | pre-existing (ELITEA-2292) |
| **Row** Edit-roles dialog root | `users-row-edit-roles-dialog` | **NEW** — EliteaAI/EliteaUI@8f559586 (call-site-only wiring of `EditUsersButton`'s already-supported `dialogTestId` at `UsersTable.jsx`'s `renderActions` — only the HEADER batch-edit instance was wired, by ELITEA-2304) |
| **Row** Edit-roles Roles combobox | `users-row-edit-roles-select-combobox` | **NEW** — same commit (`roleSelectTestId`; `SingleSelect` auto-appends `-combobox`) |
| Role options | `select-option-admin` / `-editor` / `-viewer` | pre-existing shared `SingleSelectMenuItem` mechanism |
| Row Role cell | `user-column-value-roles` | pre-existing (ELITEA-2292) |

**⚠️ `select-option-` prefix gotcha (live-discovered on THIS case).** The
row-Edit dialog opens with the user's current role already selected, and
`SingleSelect` then renders a checkmark carrying
`select-option-selected-icon` — which a naive
`[data-testid^="select-option-"]` count matches, yielding **4** where the
case expects 3. Live evidence, row-Edit dialog with `admin` preselected:
`['select-option-admin', 'select-option-selected-icon', 'select-option-editor', 'select-option-viewer']`.
The compliant handle is the exclusion constant
`[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])`,
used for BOTH dialogs so the two counts are measured identically.

## Network Behavior
Opening either dialog and reading its options fires **no request**
(`rolesOptions` is derived from the page-mount `GET /admin/roles/default/400`
already in the RTK-Query cache). Dismissing without saving fires no PUT.

## Known Defects Found During Exploration
None. Both dialogs offer exactly admin/editor/viewer.

## Blocked Steps
None.

## Automation Hints
- Page object: add `open_row_edit_roles_dialog(row)`,
  `close_row_edit_roles_dialog()`, `get_invite_role_option_texts()`,
  `get_row_edit_role_option_texts()` to `AdminUsersPage`.
- The Roles menu is a MUI popover: click the combobox, read the options,
  close with `Escape` (the Menu consumes it; the dialog stays open —
  confirmed live, already in `_surface.md`).
- Dismiss the Edit dialog with `Escape` a second time (there is no wired
  Cancel/Close testid at the ROW call site, and the case never requires one —
  canon ruling #511 scope discipline: only add the testids the executed path
  actually calls). Assert `to_have_count(0)` on the dialog root afterwards.
