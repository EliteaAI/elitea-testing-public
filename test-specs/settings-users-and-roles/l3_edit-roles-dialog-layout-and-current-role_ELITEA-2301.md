# Test Case: Edit roles dialog opens with correct layout and current role pre-selected

## Metadata
- **TMS ID**: ELITEA-2301
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2301.md`
- **Linked Story**: none
- **Priority**: l3 (case frontmatter `priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in, `admin` in project 400 — the per-row Edit (pencil) icon is
  permission-gated (`PERMISSIONS.users.edit`) and absent otherwise.
- At least one user row exists (self-guaranteed — the acting admin is always a
  project member).

## Test Data
### reuse-existing
- `${USERS_TEAM_PROJECT_ID}` = `400`; the **FIRST rendered user row**, used
  **read-only** as the Edit-dialog subject. The dialog is opened and dismissed
  via its Close (×); **no role is ever changed and Save is never clicked**
  (Save stays disabled until a role actually changes —
  `EditUserRolesDialog.jsx`: `disabled={!selectedRoles.length || !hasChangedRoles}`).
- The subject row's current role is **read at runtime** from its Role cell and
  used to build the expected chip/checkmark handles. Never hardcoded — project
  400's rows and roles drift (see the digest's live-data note).

## Test Steps
1. Navigate to Settings -> Users (project 400).
   - **Verify**: at least one user row renders.
   - Capture the FIRST row's Role-cell text as `current_role`.
2. Click the Edit (pencil) icon on the first user row.
   - **Verify**: `users-row-edit-roles-dialog` becomes visible.
3. **Verify** the dialog title is exactly `Edit roles`
   (`users-row-edit-roles-title`).
4. **Verify** the dialog description is exactly
   `Select the roles to define user permissions for this project.`
   (`users-row-edit-roles-description`).
   - ⚠️ The case text quotes `Select the roles to define permissions for this
     project.` — **without the word "user"**. The product string is the ground
     truth (source: `EditUserRolesDialog.jsx`); the case text is stale. Filed as
     a case-text clarification (§ Known Defects). Asserting the case's version
     would be reverse-masking.
5. **Verify** the Roles multi-select shows the subject's current role as a
   **chip**: exactly ONE chip is rendered, its testid is
   `select-value-chip-{current_role}` and its text is `current_role`; the chip
   carries a remove (×) control (`select-value-chip-{current_role}-remove`).
6. Open the Roles dropdown.
   - **Verify** the currently assigned role option carries the checkmark:
     `select-option-{current_role}` contains exactly one
     `select-option-selected-icon`, **and** every other role option contains
     none — i.e. exactly ONE checkmark is mounted in the whole menu.
7. Close the menu (Escape — consumed by the MUI Menu, dialog stays open), then
   **verify** the Close (×) button `users-row-edit-roles-close-button` is
   visible and click it.
   - **Verify**: the dialog unmounts (`to_have_count(0)`).
8. **Verify** the first row's Role cell still reads `current_role` — the
   read-only visit mutated nothing.
9. **Verify** no unexpected console errors across the flow (excluding the known
   `#1971` project-switch URL).

## Expected Results
- The row-level "Edit roles" dialog renders title, description, a Roles
  multi-select pre-loaded with the user's current role as a removable chip, the
  matching option checkmarked in the dropdown, and a Close (×) in the title bar.
- Dismissing via × leaves the user's role unchanged.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — the permission-gated Edit icon renders | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` count > 0 | asserted |
| 2 Click the Edit (pencil) icon on any user row | Control responds; expected next state is shown | step 2 | `step 2`: `users-row-edit-roles-dialog` visible | asserted |
| 3 Verify the "Edit roles" dialog opens with: | Condition holds as described | steps 3-7 | the four sub-rows below | asserted |
| 4 Title "Edit roles" | expected UI state | step 3 | `step 3`: title text == `Edit roles` | asserted |
| 5 Description: "Select the roles to define permissions for this project." | expected UI state | step 4 | `step 4`: description text == the LIVE string (`…define user permissions…`) | asserted (case text stale — clarification filed) |
| 6 Roles multi-select dropdown showing the user's current role as a chip ("editor ×") | expected UI state | step 5 | `step 5`: exactly 1 chip, testid + text == `current_role`, remove (×) present | asserted |
| 7 Currently assigned role shown with a checkmark in the dropdown list | expected UI state | step 6 | `step 6`: checkmark inside `select-option-{current_role}` only, total checkmark count == 1 | asserted |
| 8 Close (×) button in the top right | expected UI state | step 7 | `step 7`: close button visible, click unmounts the dialog | asserted |
| Expected Final State: Close (×) button in the top right | (restates step 8) | step 7 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- Step 6 asserts **exactly one** checkmark in the whole menu, not merely "the
  current role has one" — *added: "pre-selected" means the others are NOT; a
  second checkmark would be a real defect the case's wording implies but does
  not state.*
- Step 7 asserts the Close button **works** (dialog unmounts), not just that it
  exists — *added: the case lists it as a layout element, but a dead × is a
  defect, and clicking it is also this case's non-destructive exit.*
- Step 8 asserts the row's role is **unchanged** — *added: this case opens a
  MUTATING dialog purely to read it; the unchanged assertion is what proves the
  read was non-destructive (same discipline as ELITEA-2305).*
- Step 9 no-console-errors side-channel check — *standard discipline for this
  surface, with the `#1971` URL exclusion the digest mandates.*
- The chip/checkmark expectations are derived from the row's **runtime** role
  rather than the case's literal `editor` example — *the case says "any user
  row" and "(e.g., "editor ×")"; project 400's data drifts, so the runtime
  derivation is what the case actually means.*

## Cleanup
None required — read-only. Save is never clicked and stays disabled by
construction; step 8's unchanged-role assertion is the cleanliness proof.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| User row | `user-row` | pre-existing (ELITEA-2292) |
| Row Edit (pencil) icon | `user-row-edit-button` | pre-existing (ELITEA-2292) |
| Row Role cell | `user-column-value-roles` | pre-existing (ELITEA-2292) |
| Row Edit-roles dialog root | `users-row-edit-roles-dialog` | pre-existing (EliteaAI/EliteaUI@8f559586, ELITEA-2295) |
| Row Edit-roles dialog title | `users-row-edit-roles-title` | **NEW** — EliteaAI/EliteaUI@65194eb1 (call-site-only: `EditUsersButton.dialogTitleTestId`, already supported) |
| Row Edit-roles description | `users-row-edit-roles-description` | **NEW** — same commit (new `descriptionTestId` pass-through prop on `EditUserRolesDialog`, landing on its existing description `Typography`) |
| Row Edit-roles Close (×) | `users-row-edit-roles-close-button` | **NEW** — same commit (new `closeButtonTestId` pass-through -> `BaseModal.closeButtonTestId`, already supported) |
| Row Edit-roles Save | `users-row-edit-roles-save-button` | **NEW** — same commit (call-site-only: `saveButtonTestId`, already supported) |
| Roles combobox | `users-row-edit-roles-select-combobox` | pre-existing (EliteaAI/EliteaUI@8f559586) |
| Selected-role chip | `select-value-chip-{role}` | **NEW** — same commit; GENERIC shared-component testid on `SingleSelect`'s multi-value `Chip`, mirroring the existing `select-option-{value}` mechanism in `SingleSelectMenuItem.jsx` |
| Chip remove (×) icon | `select-value-chip-{role}-remove` | **NEW** — same commit, same mechanism (on the `Chip`'s `deleteIcon`) |
| Role options | `select-option-admin` / `-editor` / `-viewer` | pre-existing shared `SingleSelectMenuItem` mechanism |
| Option checkmark | `select-option-selected-icon` | pre-existing, rendered INSIDE the selected option |

**⚠️ `select-option-` prefix gotcha** (digest): the checkmark's testid also
matches the bare prefix, so any option COUNT must use
`[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])`
— `AdminUsersPage.ROLE_OPTION_ANY_SELECTOR`.

## Network Behavior
Opening the dialog, reading its options and dismissing via × fire **no**
request (`rolesOptions` comes from the page-mount `GET /admin/roles/default/400`
already in the RTK-Query cache). Live-verified 2026-08-29.

## Known Defects Found During Exploration
- **Case-text drift (not a product defect)**: the case quotes the dialog
  description as `Select the roles to define permissions for this project.`
  while the product renders `Select the roles to define user permissions for
  this project.` (`EditUserRolesDialog.jsx`). Product is correct; the TMS case
  text needs updating. Filed as **#1977** (`question`-labelled clarification, the #40 pattern).
