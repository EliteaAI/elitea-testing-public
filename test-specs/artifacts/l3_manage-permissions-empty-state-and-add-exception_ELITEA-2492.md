# Test Case: Manage Permissions — Empty State Display and Add Exception Flow

## Metadata
- **TMS ID**: ELITEA-2492 ("Empty State Display and Add Exception Flow")
- **Linked Story**: `EliteaAI/elitea_issues#5912` (case `requirements:`)
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`); acting user is the standard `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot, batch `artifacts-w06`, 2026-08-23)
- **Status**: **blocked** — steps 12-20 (the *write* half: add an exception, verify the table, edit it back, verify the empty state returns) cannot be executed honestly by the acting user: **every bucket-permission write returns `403`**, in every Team project reachable from this account. See § Blocked Steps (`EliteaAI/elitea-testing-public#1701`). Steps 1-11 were executed live and are fully specced below.
- **Defects filed**: `#1700` (product bug — a failed save is displayed as a *successful* one), `#1701` (access blocker / clarification)

## Preconditions
- Acting user is logged in (localhost `auth_state`, no explicit login step).
- **A Team project with at least one bucket that has ZERO permission exceptions.**
  Satisfied read-only by `Elitea Testing Team` (**id 471**, `settings.elitea_team_project_id`):
  bucket `abc-test` rendered `Exceptions – 0` live on 2026-08-23.
  Never hardcode the bucket: resolve it at run time by opening candidate buckets and
  taking the first whose header reads `Exceptions – 0` (in project 406 the first three
  buckets had 2 / 4 / 7 exceptions, so "first row" is NOT a safe assumption).
- **An admin identity able to WRITE bucket permissions** — **NOT SATISFIABLE** (§ Blocked Steps).
- Steps 1-11 seed nothing and mutate nothing (workflow skill Hard Rule 10): they are pure
  observation of the Manage Permissions modal's empty state.
- The `Manage permissions` bucket-menu item does not exist in a personal/private project
  (ELITEA-2491) — the case is Team-project-only by construction.

## Test Data
### existing-stable (read-only)
| Field | Value | Note |
|---|---|---|
| Team project | `471` — `Elitea Testing Team` | `settings.elitea_team_project_id`, never a literal |
| Bucket | first bucket whose modal header reads `Exceptions – 0`, resolved at run time | e.g. `abc-test` in 471 on 2026-08-23 |
| "User B" | first option in the Add-exceptions Users dropdown, read at run time | **`settings.test_user_b_email` is EMPTY on this machine** — do not depend on it (see § Findings 3) |

## Concrete Handles

### Steps 1-11 — the implementable half

| Element | Handle | Provenance |
|---|---|---|
| Buckets page heading (page-load gate) | `artifacts-buckets-heading` | pre-existing — `on-main ✓` |
| Project selector trigger | `project-selector-trigger-combobox` (`BasePage.project_selector_trigger`) | pre-existing |
| Project option | `select-option-{project_id}` (`BasePage.SELECT_OPTION`) | pre-existing |
| Bucket row | `artifacts-bucket-row-{name}` (`ArtifactsPage.BUCKET_ROW`) | pre-existing |
| Bucket row 3-dot menu button (hover-gated) | `bucket-menu-{name}-menu-button` (`ArtifactsPage.BUCKET_MENU_BUTTON`) | pre-existing, composed at runtime in `DotMenu.jsx` |
| **"Manage permissions" menu item** | **`testid needed: bucket-menu-manage-permissions-menuitem`** | **needs-adding — SHARED with ELITEA-2491**, see below |
| **Manage Permissions dialog** | **`testid needed: bucket-permissions-dialog`** | needs-adding — `ManagePermissionsModal.jsx`, `Modal.BaseModal` already accepts `data-testid` (`BaseModal.jsx:32,128`) |
| **"Default Permissions" section label** | **`testid needed: bucket-permissions-default-label`** | needs-adding — `DefaultPermissionsBanner.jsx` `<Typography>` |
| Default-permissions banner message | `credential-warning-banner`, **scoped inside the dialog**: `[data-testid="bucket-permissions-dialog"] [data-testid="credential-warning-banner"]` | **pre-existing** (shared `credential-warning` banner) — live inner text is exactly `All users have read/write permissions by default.` No UI change needed |
| **"Exceptions – N" section header** | **`testid needed: bucket-permissions-exceptions-heading`** | needs-adding — `BucketAccessTable.jsx` section-header `<Typography>` (≈L454) |
| **Empty-state illustration** | **`testid needed: bucket-permissions-empty-state-icon`** | needs-adding — `renderEmptyState()`'s `<Box component={NoPermissionsIcon}>` (≈L418); attribute-only, no new node |
| **Empty-state title** | **`testid needed: bucket-permissions-empty-state-title`** | needs-adding — `renderEmptyState()` title `<Typography>` (≈L422) |
| **Empty-state helper text** | **`testid needed: bucket-permissions-empty-state-subtitle`** | needs-adding — `renderEmptyState()` subtitle `<Typography>` (≈L429) |
| **"Add Exceptions" CTA** | **`testid needed: bucket-permissions-add-exceptions-button`** | needs-adding — `renderEmptyState()`'s `Button.BaseBtn` (≈L436); `BaseBtn` spreads `restProps` onto MUI `Button`, so a plain `data-testid` is enough |
| **Add-exceptions dialog** | **`testid needed: bucket-add-exception-dialog`** | needs-adding — `AddBucketUserDialog.jsx` `Modal.BaseModal` |

**The shared testid.** `bucket-menu-manage-permissions-menuitem` is the SAME add ELITEA-2491
specifies (`BucketItem.jsx`'s `menuItems` entry has no `key`, and `DotMenu.jsx:422` derives the
item testid from `item.key`; fix = add `key: 'bucket-menu-manage-permissions'`). Whichever case
is implemented first adds it; the other reuses it. Do **not** also key the sibling `Share` item
(canon #511 — no test on this path calls it).

**Do NOT touch shared components for this case.** The small `+` toolbar button
(`shared/ui/button/AddButton.jsx`) carries no testid, but it renders only when exceptions
already exist and is on no executed path here (canon #511). Leave it.

### Steps 12-20 — handles observed live, but ONLY under the `#1700` false-success render
These were exercised on the real UI; the table they populate, however, reflects an exception the
backend **rejected**. They are recorded so the case is implementable the moment `#1701` is
resolved — **not** as an invitation to assert against the current false state.

| Element | Handle | Provenance |
|---|---|---|
| Users autocomplete input (Add dialog) | **`testid needed: bucket-add-exception-users-input`** | needs-adding — `Autocomplete.UserSearchSelect` call site in `AddBucketUserDialog.jsx` |
| User option in that dropdown | **`testid needed: bucket-add-exception-user-option-{email}`** (dynamic) | needs-adding — options render with no testid today (16 options live, all untagged) |
| Permissions select (Add dialog) | **`testid needed: bucket-add-exception-permission-select`** → `SingleSelect` emits `…-combobox` on the display node (`SingleSelect.jsx:660-661`) | needs-adding |
| Permission options | `select-option-read` (`Read-only`), `select-option-no_access` (`No access`) | **pre-existing** — live-confirmed; the Add dialog offers exactly these two (`Read/write (default)` appears only in the Edit dialog) |
| Save / Cancel (Add dialog) | **`testid needed: bucket-add-exception-save-button` / `-cancel-button`** | needs-adding — `Button.BaseBtn` in `actions` |
| Exceptions table column headers | **`testid needed:`** pass `columnTestIdPrefix="bucket-permissions-exceptions"` to `GridTableHeader` → `bucket-permissions-exceptions-column-header-{name,email,access}` | needs-adding — the prop already exists (`GridTableHeader.jsx:19,47`), only the call site is missing it |
| Select-all checkbox | **`testid needed:`** `selectAllCheckboxTestId="bucket-permissions-exceptions-select-all-checkbox"` | needs-adding — prop exists (`GridTableHeader.jsx:20,29`) |
| Exception row | **`testid needed:`** `data-testid={`bucket-permissions-exception-${row.email}`}` on `GridTableRow` | needs-adding — prop exists (`GridTableRow.jsx:38,58`) |
| Row cells (Email / Permissions) | **`testid needed:`** `dataCellTestIdPrefix={`bucket-permissions-exception-${row.email}`}` → `…-column-value-email`, `…-column-value-access` | needs-adding — prop exists (`GridTableRowDataCell.jsx:21-23`) |
| Row checkbox | **`testid needed:`** `checkboxTestId={`bucket-permissions-exception-${row.email}-checkbox`}` | needs-adding — prop exists (`GridTableRow.jsx:39,71`) |
| Row "Edit exception" button | **`testid needed: bucket-permissions-exception-{email}-edit-button`** | needs-adding — `renderActions()` `Button.BaseBtn` (≈L341) |
| Edit-exception dialog + its select / Save | **`testid needed: bucket-edit-exception-dialog`, `bucket-edit-exception-permission-select`, `bucket-edit-exception-save-button`** | needs-adding — `EditBucketUserDialog.jsx`; the `Read/write (default)` option is the pre-existing `select-option-read_write` |

## Test Steps

One `allure.step` per numbered step. Existing page-object methods reach the surface:
`BasePage.switch_project()`, `ArtifactsPage.navigate_to_artifacts()`, `wait_for_page_load()`,
`get_rendered_bucket_names()`, `open_bucket_menu()`. `ArtifactsPage.open_manage_permissions()`
exists but is **pre-policy raw-handle code** (`get_by_role("menuitem", …)`, `[role="dialog"]:has-text(…)`)
— once `bucket-menu-manage-permissions-menuitem` + `bucket-permissions-dialog` exist, migrate that
method to testids rather than adding a second one (tech debt #25/#42, do not extend it).

| # | Action | Expected (live-confirmed 2026-08-23 unless marked) |
|---|--------|-----------------------------------------------------|
| 1 | Navigate to `/artifacts`; wait for `artifacts-buckets-heading` | Artifacts page loads |
| 2 | `switch_project(settings.elitea_team_project_id)` (471) | Bucket list reloads (11 rows live) |
| 3 | Resolve a bucket whose Manage-Permissions header reads `Exceptions – 0`; hover its row, click `bucket-menu-{name}-menu-button` | Dot-menu opens |
| 4 | Click `bucket-menu-manage-permissions-menuitem` | `bucket-permissions-dialog` is visible |
| 5 | Assert `bucket-permissions-default-label` has text `Default Permissions`, **and** the dialog-scoped `credential-warning-banner` has text `All users have read/write permissions by default.` | both present |
| 6 | Assert `bucket-permissions-exceptions-heading` has text `Exceptions – 0` | count is 0. **Note the character: an EN DASH `–` (U+2013), not a hyphen** |
| 7 | Assert `bucket-permissions-empty-state-icon` is visible | illustration rendered (`file-lock.svg`) |
| 8 | Assert `bucket-permissions-empty-state-title` has text `No exceptions added yet` | exact match |
| 9 | Assert `bucket-permissions-empty-state-subtitle` has text `All users have read/write permissions by default.` | exact match — same sentence as the banner, deliberately asserted on the empty-state node so the two are distinguishable |
| 10 | Assert `bucket-permissions-add-exceptions-button` is visible and enabled, text `Add Exceptions` | enabled |
| 11 | Click it | `bucket-add-exception-dialog` is visible, containing the `Users` and `Permissions` labels and a **disabled** `Save` (nothing selected yet) |
| 12-20 | Select a user, pick `Read-only`, Save, verify the table replaces the empty state, `Exceptions – 1`, the row, the four columns, then edit back to `Read/write (default)` and verify the empty state returns | **BLOCKED — see § Blocked Steps** |

Whole-dialog oracle for steps 5-10 (cheap and complete), live-verified:

```
Manage Permissions
Default Permissions
All users have read/write permissions by default.
Exceptions – 0
No exceptions added yet
All users have read/write permissions by default.
Add Exceptions
```

Side channel: assert no unexpected console errors using the suite's existing filter, **not** a bare
`assert not console_messages` — this surface emits the project's known background `404`/`403` noise
plus a React `Invalid value for prop sx on <svg>` warning from `UserSearchSelect`'s checked-icon
(fires only when the Users dropdown is opened, i.e. from step 11 on).

## Expected Results
1. A bucket with no exceptions shows: the `Default Permissions` label + info banner, an
   `Exceptions – 0` header, the empty-state illustration, `No exceptions added yet`, the helper
   sentence, and an enabled `Add Exceptions` CTA.
2. The CTA opens the `Add exceptions` dialog (Users autocomplete + Permissions select + Cancel/Save,
   Save disabled until both are chosen).
3. (Blocked) Saving an exception replaces the empty state with the exceptions table, `Exceptions – 1`,
   the user listed with `Read-only`, columns Checkbox / Name / Email / Permissions; editing the user
   back to `Read/write (default)` removes the exception and restores the empty state.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition — Admin logged in (Team project) | — | localhost `auth_state` transit | — | **partially blocked** — the account authenticates but is not permission-admin (§ Blocked Steps) |
| Precondition — bucket with NO exceptions | — | run-time resolution of an `Exceptions – 0` bucket | Step 3 | covered |
| Precondition — at least one other user in the project | — | 16 users offered live in project 471 | Step 11 | covered |
| Step 1 — Login as Admin | Login successful | `auth_state` (transit) | implicit | covered (transit) |
| Step 2 — Navigate to Artifacts | Page loads | Step 1 | `artifacts-buckets-heading` | covered |
| Step 3 — Select bucket with no exceptions | Bucket selected | Step 3 | row resolved | covered |
| Step 4 — Open Manage Permissions modal | Modal opens | Step 4 | `bucket-permissions-dialog` visible | covered |
| Step 5 — "Default Permissions" section | shows the sentence | Step 5 | label + banner testids | covered |
| Step 6 — "Exceptions – 0" header | count 0 | Step 6 | `bucket-permissions-exceptions-heading` | covered |
| Step 7 — empty-state illustration | visible | Step 7 | `bucket-permissions-empty-state-icon` | covered |
| Step 8 — empty-state message | `No exceptions added yet` | Step 8 | `…-empty-state-title` | covered |
| Step 9 — helper text | the default-permissions sentence | Step 9 | `…-empty-state-subtitle` | covered |
| Step 10 — CTA present | visible + enabled | Step 10 | `…-add-exceptions-button` | covered |
| Step 11 — click CTA | Add modal opens | Step 11 | `bucket-add-exception-dialog` visible | covered |
| Step 12 — select User B | user selected | — | — | **blocked** (`#1701`) |
| Step 13 — select "Read-only" | permission selected | — | — | **blocked** |
| Step 14 — click Save | Modal closes | — | — | **blocked** — the dialog *does* close, but the write is rejected (`403`) |
| Step 15 — empty state replaced by table | table visible | — | — | **blocked** — currently produced by the `#1700` optimistic-render defect, not by a real save |
| Step 16 — "Exceptions – 1" | count 1 | — | — | **blocked** — same false source |
| Step 17 — User B listed with `Read-only` | row correct | — | — | **blocked** — same false source |
| Step 18 — columns Checkbox/Name/Email/Permissions | all present | — | — | **blocked** — column set was observed live (Name, Email, Permissions + row checkbox + an unlabelled actions column) but only inside the false table |
| Step 19 — edit User B to "Read & Write" to clean up | user removed | — | — | **blocked**; also **case-text drift**: the live option is `Read/write (default)`, and the mechanism is "edit to default = remove" (`handleEditConfirm`: `isRemoval = permission === READ_WRITE`) |
| Step 20 — empty state returns | empty state displayed | — | — | **blocked** |
| Pass criterion — empty state shows all four elements | — | Steps 7-10 | | covered |
| Pass criterion — CTA opens the Add modal | — | Step 11 | | covered |
| Pass criterion — table replaces empty state after adding | — | — | | **blocked** |
| Pass criterion — empty state restored after removing all | — | — | | **blocked** |

### Axis 2 — observables asserted beyond the case
| Extra observable | Why |
|---|---|
| Save is **disabled** in the Add dialog until a user *and* a permission are chosen | live-confirmed guard (`AddBucketUserDialog.jsx:126`); it is the cheapest proof the dialog is functional, and it costs nothing on the unblocked half |
| Exact `Exceptions – 0` string incl. the EN DASH | a hyphen-based assertion would fail forever; pinning it stops the next author re-deriving it |
| Filtered console side channel | silent errors are the ones that ship — and this surface has known noise, so the filter is part of the contract |

## Fidelity Declaration

**No substitution of any kind in the implementable half.** Every step 1-11 observable is produced by
the live product: real project switch, real hover + dot-menu click, real modal render, real DOM read.
No `page.route`, no `evaluate`, no injected state, no API-seeded precondition.

Two exploration-only diagnostics are recorded and must **not** appear in the implemented test:
`page.evaluate` DOM dumps used to enumerate testids/labels, and one `fetch()` probe (which failed —
the dev-token auth is axios-side, so a bare `fetch` cannot reach the API). Neither produced an
assertion.

**Explicitly refused:** seeding the exception through the API (or mocking the `POST/PUT`) to make
steps 15-18 pass. The case's own observable *is* "the table replaced the empty state after the user
saved" — reading it off a substituted write is terminal substitution (`.agents/testing.md` § Fidelity
policy). It goes to a human (`#1701`), not around.

## Blocked Steps

**Steps 12-20 cannot be executed — filed as `EliteaAI/elitea-testing-public#1701`.**

Verified live, 2026-08-23:

| Project | Bucket | Action | Result |
|---|---|---|---|
| 471 `Elitea Testing Team` | `abc-test` (0 exceptions) | Add exception → Save | `POST /api/v2/artifacts/s3_credentials/default/471` → **403** |
| 406 `Bugs & Features` | `abcde` (0 exceptions) | Add exception → Save | `PUT /api/v2/artifacts/bucket_permissions/default/406` → **403** |
| 400 `UI Testing` | — | — | no buckets at all |
| 399 `Private` | — | — | `Manage permissions` is not in the menu (ELITEA-2491) |

Reads are fine (`GET bucket_permissions/default/<id>` → 200), which is why steps 1-11 stand. Both
attempts produced the toast `Failed to update access`, and re-opening the modal showed
`Exceptions – 0` — nothing persisted.

**To unblock, a human must choose one of:**
- **Grant the automation user bucket-permission admin rights** in project 471 → the full 20 steps
  become executable (and `#1700` becomes assertable as a *fixed* behaviour rather than a masked one).
- **Provision a separate admin identity** (`TEST_ADMIN_*` + fixture) for permission cases.
- **Re-scope ELITEA-2492** to its display half (steps 1-11) and split the write half into its own
  case gated on admin access → this AFS is implementable as-is with the blocked rows removed.

## Findings

1. **PRODUCT BUG — a failed exception save is displayed as a successful one** (`#1700`).
   The `403` above produces the correct error toast **and** an optimistic row: the empty state is
   replaced, the header flips to `Exceptions – 1`, the user is listed with `Read-only`. Re-opening
   the modal shows `Exceptions – 0`. Root cause read from source:
   `BucketAccessTable.jsx` `handleAccessChange` catches the mutation error and only toasts (never
   re-throws), so `handleAddConfirm`'s `Promise.allSettled` results are always `fulfilled`,
   `failedUserIds` is always empty, and the `setOptimisticUsers` rollback never runs. Deterministic:
   3/3 attempts, 2 projects, 2 different endpoints. **This is also why steps 15-18 must not be
   automated against the current behaviour — they would go green on a broken flow.**
2. **Access blocker** (`#1701`) — § Blocked Steps.
3. **Merged permission tests are probably red/unrunnable on this machine.**
   `automation/tests/ui/artifacts/test_bucket_permissions_api.py` (ELITEA-2493/2494, merged on
   `automation/base`, last touched `ef5182f8e`) drives this same write path as *setup*, and also
   requires `TEST_USER_B_EMAIL`/`TEST_USER_B_PASSWORD` — both **empty** in this machine's
   `.env.test` (`settings.test_user_b_email == ""`). Worth a health check before the next artifacts
   batch; not fixed here (out of this case's scope).
4. **Case-text drift, minor — "Read & Write" vs `Read/write (default)`** (step 19). Also worth
   knowing: removal is *not* a delete action — editing an exception to `Read/write (default)` is
   what removes it (`isRemoval = permission === PERMISSION_OPTIONS.READ_WRITE`), and the Add dialog
   deliberately offers only `Read-only` / `No access`. Not filed separately: it is inside the blocked
   half and `#1701` already carries the re-scope decision.
5. **The section header uses an EN DASH** — `Exceptions – 0`, U+2013. A hyphen assertion never matches.
6. **`Exceptions – N` counts optimistic rows too** (`usersWithAccess = server rows + optimisticUsers`),
   which is the mechanism behind finding 1 — so the header is not an independent oracle for "the
   write succeeded". When `#1701` unblocks the write half, assert persistence by **re-opening the
   modal**, not just by reading the header after Save.
7. **No `Delete`/`Remove` affordance exists in the exceptions table** — only `Edit exception`
   (per row) and `Edit selected` (bulk). Any future case text saying "delete the exception" is drifted.

## Live-execution evidence (2026-08-23, localhost:5173)

```
===== project 471, bucket abc-test — steps 1..11 =====
modal text:
  Manage Permissions
  Default Permissions
  All users have read/write permissions by default.
  Exceptions – 0
  No exceptions added yet
  All users have read/write permissions by default.
  Add Exceptions
testids present in the dialog today: credential-warning-banner  (everything else untagged)
Add-exceptions dialog: 'Add exceptions' / 'Select users, then assign their bucket permissions.'
  / Users / Permissions / Cancel / Save   — zero testids
Users dropdown: 16 options, none carrying a testid
Permissions options: [('Read-only','select-option-read'), ('No access','select-option-no_access')]

===== the write half (blocked) =====
471: POST /api/v2/artifacts/s3_credentials/default/471      -> 403   toast 'Failed to update access'
406: PUT  /api/v2/artifacts/bucket_permissions/default/406  -> 403   toast 'Failed to update access'
UI after either 403:  'Exceptions – 1' + row  <user> / <email> / Read-only     <-- #1700
modal re-opened:      'Exceptions – 0' + empty state                          <-- nothing persisted
```

Evidence (uploaded to the `evidence` release store):
- ![empty state](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2492-step-05-10-empty-state.png)
- ![optimistic row after 403](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2492-step-14-optimistic-row-after-403.png)
