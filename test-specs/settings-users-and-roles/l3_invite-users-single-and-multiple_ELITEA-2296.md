# Test Case: Invite users — a single user with a role, and multiple users via comma-separated emails

**FAMILY AFS** — covers **ELITEA-2296** and **ELITEA-2297**, two true
flow-variants of ONE flow (Settings → Users → "+" → Emails → Roles → Invite).
They differ only in *how many* emails are typed, *which* role is chosen, and
*which* success-confirmation string the product emits. Implemented as **one
parameterized spec**, one row per case, each row asserting its OWN expected
values.

## Metadata
- **TMS ID**: ELITEA-2296, ELITEA-2297
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2296.md`,
  `.agents/automation/settings-w09/cases/ELITEA-2297.md`
- **Linked Story**: none
- **Priority**: l3 (both `priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in and holding `admin` in project 400 — the "+" invite button is gated
  behind `PERMISSIONS.users.create`, and project 400 is the ONLY project this
  account can mutate (surface digest § Project-topology constraint).
- `AdminUsersPage.navigate()` performs the project switch; no manual setup.

## Test Data

### Parameter table (one row per case)

| Case | Emails typed into the Emails field | Role selected | Expected success toast | Rows added |
|---|---|---|---|---|
| **ELITEA-2296** | ONE address: `elitea-invite-single-<uuid4-hex-8>@example.com` | `viewer` | `The user has been invited` | 1 |
| **ELITEA-2297** | TWO addresses joined by `", "`: `elitea-invite-multi1-<uuid>@example.com, elitea-invite-multi2-<uuid>@example.com` | `editor` | `The users have been invited` | 2 |

Both strings are the product's own (`Users.jsx`:181 —
`emailCount > 1 ? 'The users have been invited' : 'The user has been invited'`)
and were **observed live** on 2026-08-29, one per flow.

### generate-per-test
- Every address carries a fresh `uuid4().hex[:8]`. The rows are REAL, persistent
  members of a shared live project — see § Cleanup.

### stable-existing
- None. Nothing about the pre-existing rows is asserted: the baseline row count
  and the baseline email set are **captured at runtime** (project 400 currently
  carries 4 rows, two of them orphaned seeds from an earlier run — never
  hardcode a count or an identity here).

## Test Steps

*(Every step runs for both parameter rows; the bracketed values differ per row
as given in the parameter table.)*

1. Navigate to Settings → Users.
   - **Verify**: at least one user row is visible (the populated-table path, not
     the "No users" empty state).
   - Capture the baseline row count `N` and the baseline email set.
2. Click "+".
   - **Verify**: `users-invite-dialog` is visible.
3. Type the case's email(s) into the Emails field.
   - **Verify**: the field displays exactly the typed string (for ELITEA-2297,
     including the comma separator — the case's own subject).
4. Open the Roles dropdown and select the case's role.
   - **Verify**: the Roles combobox displays that role.
5. Click Invite.
   - **Verify**: the driving `POST /api/v2/admin/users/default/400` resolves
     **200 OK**.
6. **Verify** the dialog unmounts (`users-invite-dialog` count 0) **and** a
   success confirmation is shown: `toast-alert` carries
   `data-severity="success"` and `toast-message` reads the case's OWN expected
   string from the parameter table.
7. **Verify** the invited user(s) appear in the Users table:
   - the row count is `N + <rows added>`;
   - each invited address matches **exactly one** row;
   - that row's Role cell reads the case's selected role;
   - that row's Name cell is **empty** and its Last-login cell reads the literal
     `-` (an invited-but-never-logged-in user — live-confirmed, both null
     renderings).
8. **Verify** no unexpected console errors across the flow (excluding the
   known-defect URL — see § Automation Hints).

## Expected Results
- **ELITEA-2296**: one invited address becomes one `viewer` row; the dialog
  closes and the singular success toast is shown.
- **ELITEA-2297**: two comma-separated addresses become two `editor` rows in a
  single submit; the dialog closes and the plural success toast is shown.
- The pre-existing rows are untouched (the count delta is exactly the number of
  invited addresses).
- No console errors beyond the declared known defect.

## Coverage Map

**Axis 1 — Source-case elements (ELITEA-2296):**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated "+" renders | asserted |
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` visible | asserted |
| 2 Click "+" | Control responds; expected next state is shown | step 2 | `step 2`: `users-invite-dialog` visible | asserted |
| 3 Enter a valid email address in the Emails field | Field accepts the input and displays the entered value | step 3 | `step 3`: `input_value() == email` | asserted |
| 4 Click the Roles dropdown and select "viewer" | Control responds; expected next state is shown | step 4 | `step 4`: combobox text == `viewer` | asserted |
| 5 Click Invite | Control responds; expected next state is shown | step 5 | `step 5`: POST 200 OK | asserted |
| 6 Verify the dialog closes and a success confirmation is shown | Condition holds as described | step 6 | `step 6`: dialog count 0 + success toast text | asserted |
| 7 Verify the invited user appears in the Users table with "viewer" role | Condition holds as described | step 7 | `step 7`: row count 1 for the email, Role cell == `viewer` | asserted |
| Expected Final State: invited user in the table with "viewer" role | (restates step 7) | step 7 | same as row above | asserted |

**Axis 1 — Source-case elements (ELITEA-2297):**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated "+" renders | asserted |
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` visible | asserted |
| 2 Click "+" | Control responds; expected next state is shown | step 2 | `step 2`: `users-invite-dialog` visible | asserted |
| 3 Enter two email addresses separated by a comma | Field accepts the input and displays the entered value | step 3 | `step 3`: `input_value() == "a@…, b@…"` (comma preserved) | asserted |
| 4 Select a role (e.g. "editor") | Control responds; expected next state is shown | step 4 | `step 4`: combobox text == `editor` | asserted |
| 5 Click Invite | Control responds; expected next state is shown | step 5 | `step 5`: POST 200 OK | asserted |
| 6 Verify both users appear in the Users table with the assigned role | Condition holds as described | step 7 | `step 7`: count `N+2`, each email exactly 1 row, Role cell == `editor` | asserted |
| Expected Final State: both users in the table with the assigned role | (restates step 6) | step 7 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- **Step 6's success toast for ELITEA-2297** — *added*: ELITEA-2297's case text
  never mentions a confirmation, but the product emits a DIFFERENT string for
  the plural path, and that difference is exactly the observable that
  distinguishes "two addresses were parsed" from "one string was swallowed".
  Asserting the plural text is what makes the comma-separation claim testable
  at the confirmation layer as well as the table layer. Both strings were
  observed live.
- **Step 5's POST-200 assertion** — *added*: the case says "click Invite";
  binding the step to the product's own driving response makes the step's
  success/failure attributable, and gives the row assertions a deterministic
  wait anchor (never a sleep).
- **Step 7's Name-empty / Last-login-`-` assertions** — *added*: the two null
  renderings on this table are a documented trap (empty string vs literal `-`).
  Pinning them turns an incidental observation into a regression guard, at zero
  extra cost since the row is already resolved.
- **Step 7's baseline-relative count** — *added*: proves the invite added
  exactly the invited addresses and disturbed nothing else. Relative, never
  absolute — project 400's row set is shared, live and drifting.
- **Step 8 no-console-errors side-channel check** — standard discipline for
  this surface.

## Cleanup
**Mandatory.** Both parameter rows create REAL, persistent members of the shared
live project 400. Every invited address is deleted in a `finally` block via the
row-level Delete icon → confirm (`DELETE …/admin/users/default/400?id[]=…` →
**204 No Content**), each row isolated in its own `try/except` and the failures
aggregated, exactly as ELITEA-2304's teardown does (that pattern exists because
a non-isolated loop leaked rows — the two `elitea-batch-edit-test2-*` orphans
still in the table are the evidence).

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| "+" invite button | `users-invite-button` | pre-existing (ELITEA-2292) |
| Dialog root | `users-invite-dialog` | pre-existing — EliteaAI/EliteaUI@8f559586 (ELITEA-2295) |
| Emails input | `users-invite-emails-input` | pre-existing (ELITEA-2304) |
| Roles combobox | `users-invite-role-select-combobox` | pre-existing (ELITEA-2304) |
| Role options `viewer` / `editor` | `select-option-viewer` / `select-option-editor` | pre-existing shared `SingleSelectMenuItem` mechanism |
| Invite (confirm) button | `users-invite-confirm-button` | pre-existing (ELITEA-2304) |
| Toast container | `toast-alert` (+ `data-severity="success"`) | pre-existing shared `Toast.jsx` |
| Toast text | `toast-message` | pre-existing shared `Toast.jsx` |
| User row | `user-row` | pre-existing (ELITEA-2292) |
| Row Name / Email / Last-login / Role cells | `user-row-name` / `user-column-value-email` / `user-column-value-last_login` / `user-column-value-roles` | pre-existing (ELITEA-2292) |
| Row Delete icon (cleanup) | `user-row-delete-button` | pre-existing (ELITEA-2292) |
| Delete confirmation | `delete-confirm-button` | pre-existing shared `DeleteEntityModal` |

**No new testid is needed for either case.** The success confirmation rides the
product's shared toast, which already carries `toast-alert` + `data-severity` +
`toast-message`.

## Network Behavior
- Invite: `POST /api/v2/admin/users/default/400` → **200 OK** (one call for
  however many addresses are typed — live-confirmed for both 1 and 2 emails),
  followed by a users-list refetch `GET …/admin/users/default/400?limit=20&offset=0`
  → 200.
- Cleanup delete: `DELETE …/admin/users/default/400?id[]=<id>` → **204**.

## Known Defects Found During Exploration
None on this path. Both flows behave exactly as their case text describes.

## Blocked Steps
None.

## Automation Hints
- Page object: everything already exists on `AdminUsersPage` —
  `navigate()`, `open_invite_dialog()`, `invite_users(emails, role)` (fills,
  selects the role, clicks Invite, returns the POST response),
  `get_row_by_text()`, `get_role_cell_for_row()`, `delete_user_row()`.
  The only additions needed are the shared **toast** locators
  (`toast-alert` / `toast-message` + a `data-severity`-scoped constant, the same
  shape `credential_form_fields.py` and `agent_detail_page.py` already declare).
- **The success toast auto-hides after 3 000 ms** (`TOAST_DURATION_DEFAULTS.success`).
  Assert it IMMEDIATELY after `invite_users()` returns — before the table
  assertions — or it will have unmounted. This is not a flake risk if ordered
  that way: the toast renders in the same tick the POST resolves.
  *(Live-learned the hard way: three MCP round-trips all missed the toast because
  each took longer than 3 s; a DOM MutationObserver was needed to capture it.)*
- Type the ELITEA-2297 string with the space after the comma (`", ".join(...)`)
  — that is the shape the case text shows, and `parseEmails()` trims it.
- Do NOT assert an absolute row count anywhere.

### Console-error assertion — known-defect exclusion
The final step excludes ONE exact URL:
`/api/v2/elitea_core/toolkits/prompt_lib/` (project-id-less), via
`utils.console_errors.exclude_known_defect_urls` with a `# Known defect: #1971`
comment — the same OPEN defect every settings-w09 spec on this surface excludes.
Keyed to the exact URL, never the status code.
