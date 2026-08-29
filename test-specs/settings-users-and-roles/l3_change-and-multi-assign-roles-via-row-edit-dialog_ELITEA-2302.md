# Test Case (FAMILY): Change / multi-assign a user's roles via the row Edit-roles dialog

## Metadata
- **TMS ID**: ELITEA-2302 (family member), ELITEA-2303 (family member)
- **Family AFS**: yes — ONE parameterized spec, one row per case, each row
  asserting its OWN expected values.
- **Source cases**: `.agents/automation/settings-w09/cases/ELITEA-2302.md`,
  `.agents/automation/settings-w09/cases/ELITEA-2303.md`
- **Linked Story**: none
- **Priority**: l3 (both `priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Why one family
Both cases are the SAME flow through the SAME dialog — seed a disposable user,
open its row Edit-roles dialog, manipulate the Roles multi-select, Save, verify
the Role column, reload and verify persistence. They differ only in the
manipulation and therefore in the expected role set:

| Param | ELITEA-2302 | ELITEA-2303 |
|---|---|---|
| `case_id` | ELITEA-2302 | ELITEA-2303 |
| `seeded_role` | `viewer` (the case names a viewer user) | `viewer` |
| `remove_seeded_chip` | **True** — click the × on the `viewer` chip | False |
| `roles_to_select` | `["editor"]` | `["editor", "admin"]` |
| `expected_roles` | `{"editor"}` (viewer replaced) | `{"viewer", "editor", "admin"}` (added to the existing one) |
| `expected_chip_count_before_save` | 1 | 3 |

ELITEA-2303's case text says "Select two roles from the Roles dropdown (e.g.
"editor" and "admin")" and never removes the seeded one, so its expected set
legitimately includes the seeded `viewer` — the multi-select ADDS. That is the
per-case expected value, asserted per row, not flattened.

## Preconditions
- Logged in, `admin` in project 400 — both the "+" invite button
  (`PERMISSIONS.users.create`) and the per-row Edit/Delete icons
  (`PERMISSIONS.users.edit` / `.delete`) are permission-gated.
- **Project 400 is the ONLY project this account can mutate** (digest §
  Project-topology constraint).

## Test Data
### seed-and-cleanup (mandatory)
- ONE disposable user per test invocation, invited with role `viewer`:
  `elitea-role-edit-{case}-{uuid8}@example.com`. An invited row appears
  immediately with full row actions — no acceptance step (digest, live
  re-confirmed 2026-08-29).
- **Never mutate a pre-existing row.** `Test Bot` is the acting account (losing
  its `admin` would strand the automation) and `Levon Dadayan` is a real human.
- **Cleanup: the seeded user is deleted in a `finally` block** regardless of
  outcome, via the per-row delete flow (`AdminUsersPage.delete_user_row`).

## Test Steps (parameterized; `{}` = per-case parameter)
1. Navigate to Settings -> Users (project 400).
   - **Verify**: at least one user row renders. Capture the row count.
2. Seed: invite ONE disposable user with role `{seeded_role}`.
   - **Verify**: the invite POST resolves **200**, the table gains exactly one
     row, and the seeded row's Role cell reads `{seeded_role}`.
3. Click the Edit (pencil) icon on the SEEDED row.
   - **Verify**: `users-row-edit-roles-dialog` is visible; the Roles field shows
     exactly one chip, `select-value-chip-{seeded_role}`; Save is **disabled**
     (nothing changed yet).
4. *(ELITEA-2302 only — `remove_seeded_chip`)* Click the × on the
   `{seeded_role}` chip.
   - **Verify**: zero chips remain **and Save is STILL disabled** — an empty
     role set is not saveable (`disabled={!selectedRoles.length || …}`).
5. Select `{roles_to_select}` in the Roles dropdown (open, click each option,
   Escape to close the menu — the menu does not auto-close in `multiple` mode).
   - **Verify**: the chips rendered are exactly `{expected_roles}` (as a SET,
     by chip testid) and their count is `{expected_chip_count_before_save}`;
     Save is now **enabled**.
6. Click Save.
   - **Verify**: the driving `PUT /admin/users/default/{projectId}` resolves
     **200**, the dialog unmounts, and the users list re-fetches.
7. **Verify** the seeded user's Role column now lists exactly
   `{expected_roles}` — the cell text is comma-joined (`"editor, admin"`), so
   split on `,` and compare as a SET (backend order is not part of the
   contract).
8. Reload the page.
   - **Verify** the seeded user's Role column still lists exactly
     `{expected_roles}` — the change persisted server-side.
9. **Verify** no unexpected console errors across the flow (excluding the known
   `#1971` project-switch URL).

## Expected Results
- ELITEA-2302: a `viewer` user's chip can be removed and `editor` chosen; the
  Role column becomes exactly `editor` and survives a reload.
- ELITEA-2303: two further roles can be added; the Role column lists all
  assigned roles and survives a reload.
- The seeded user is removed afterwards; no pre-existing row is touched.

## Coverage Map — ELITEA-2302

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated icons render | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible | asserted |
| 2 Click the Edit (pencil) icon on a user with "viewer" role | Control responds; expected next state is shown | steps 2-3 | `step 2`: seeded viewer row exists with role `viewer`; `step 3`: dialog visible, chip == `viewer` | asserted (subject SEEDED — see Test Data for why a pre-existing row must not be mutated) |
| 3 In the Roles dropdown remove "viewer" by clicking the × on the chip | expected UI state | step 4 | `step 4`: 0 chips, Save still disabled | asserted |
| 4 Select "editor" from the dropdown | Control responds | step 5 | `step 5`: chips == {editor}, Save enabled | asserted |
| 5 Confirm the change | Operation completes; state updates and confirmation is shown | step 6 | `step 6`: PUT 200, dialog unmounts, list refetches | asserted |
| 6 Verify the user's Role column updates to "editor" | Condition holds | step 7 | `step 7`: role cell set == {editor} | asserted |
| 7 Reload the page — verify the role change persists | expected UI state | step 8 | `step 8`: role cell set == {editor} after reload | asserted |
| Expected Final State: reload — role change persists | (restates step 7) | step 8 | same as row above | asserted |

## Coverage Map — ELITEA-2303

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible | asserted |
| 2 Click the Edit (pencil) icon on any user | Control responds | steps 2-3 | `step 3`: dialog visible on the seeded row | asserted (subject SEEDED, per Test Data) |
| 3 Select two roles from the Roles dropdown (e.g. "editor" and "admin") | Control responds | step 5 | `step 5`: both options clicked | asserted |
| 4 Verify both roles appear as chips in the Roles field | Condition holds | step 5 | `step 5`: chip set == {viewer, editor, admin}, count 3 — BOTH newly selected roles present as chips | asserted |
| 5 Confirm the change | Operation completes; state updates | step 6 | `step 6`: PUT 200, dialog unmounts, list refetches | asserted |
| 6 Verify the user's Role column shows both assigned roles | Condition holds | step 7 | `step 7`: role-cell set == {viewer, editor, admin} — a superset assertion would let a dropped role pass, so it is an exact set | asserted |
| 7 Reload the page — verify multi-role assignment persists | expected UI state | step 8 | `step 8`: role-cell set unchanged after reload | asserted |
| Expected Final State: reload — multi-role assignment persists | (restates step 7) | step 8 | same as row above | asserted |

**Axis 2 — Analyst additions (both members):**
- Step 3 asserts Save is **disabled on open** — *added: it is the guard that
  makes "the dialog was opened" non-destructive, and it is what step 5's
  enabled-assertion is measured against.*
- Step 4 (2302) asserts Save stays disabled at **zero** roles — *added: removing
  the only chip is the case's own action, and the empty-set gate
  (`!selectedRoles.length`) is a real product rule the case walks straight
  past.*
- Steps 6/7 assert the **PUT status and the refetch**, not just the rendered
  cell — *added: "Confirm the change" has a driving request; a UI-only check
  cannot distinguish "saved" from "optimistically rendered".*
- Step 7/8 compare role sets **exactly**, not as a superset — *added: "shows
  both roles" passes trivially on a superset; an exact set catches a dropped or
  spurious role.*
- Step 9 no-console-errors side-channel check — *standard discipline, with the
  `#1971` URL exclusion the digest mandates.*
- The subject is a **seeded** disposable user rather than an existing row —
  *the case says "a user with viewer role" / "any user"; project 400's only
  non-seeded rows are the acting account and a real human, and mutating either
  is unacceptable (digest § Project-topology constraint). Seeding is the
  faithful, safe reading, and ELITEA-2304 established the pattern.*

## Cleanup
Mandatory, in a `finally`: delete the seeded user via its row Delete icon +
`delete-confirm-button` (`AdminUsersPage.delete_user_row`, four merged callers).
Verified live 2026-08-29: after cleanup the table returns to exactly the rows it
had before.

## Concrete Handles (discovered during exploration)

Same table as `l3_edit-roles-dialog-layout-and-current-role_ELITEA-2301.md`
(shared dialog), plus:

| Element | Testid | Provenance (verified 2026-08-29) |
|---|---|---|
| "+" invite button | `users-invite-button` | pre-existing (ELITEA-2292) |
| Invite emails textarea | `users-invite-emails-input` | pre-existing (ELITEA-2304) |
| Invite Roles combobox | `users-invite-role-select-combobox` | pre-existing (ELITEA-2304) |
| Invite confirm | `users-invite-confirm-button` | pre-existing (ELITEA-2304) |
| Row Delete icon | `user-row-delete-button` | pre-existing (ELITEA-2292) |
| Delete confirm | `delete-confirm-button` | pre-existing shared `Modal.DeleteEntityModal` |

## Network Behavior (live-captured 2026-08-29)
- Invite: `POST /api/v2/admin/users/default/400` -> **200**, +1 row.
- Save in the ROW dialog: `PUT /api/v2/admin/users/default/400` (body
  `{id, roles}` — single-user shape via `useEditUser`, not the batch `ids`
  shape) -> **200**, then a users-list refetch. Success toast:
  `The user has been edited successfully` (severity `success`, auto-hides after
  3 s — assert it only immediately after the response resolves, if at all).
- Cleanup delete: `DELETE /api/v2/admin/users/default/400?id[]=<id>` -> **204**.

## Known Defects Found During Exploration
None on this flow. Both role manipulations, the PUT, and the post-reload
persistence behaved exactly as the cases describe.
