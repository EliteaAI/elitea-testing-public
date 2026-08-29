# Test Case: Invite user who is already a project member shows appropriate error

## Metadata
- **TMS ID**: ELITEA-2309
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2309.md`
- **Linked Story**: none
- **Priority**: l3 (`priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in and holding `admin` in project 400 — the "+" invite button is gated
  behind `PERMISSIONS.users.create`, and 400 is the only project this account
  can mutate (surface digest § Project-topology constraint).

## Test Data

### generate-per-test
- ONE disposable address, `elitea-invite-dup-<uuid4-hex-8>@example.com`, invited
  ONCE at the start of the test with role `viewer` — **that invite is what makes
  it "an existing project member"**, which is the case's step 2.

  *Why not an already-listed member?* The case says "note the email of an
  existing project member". The only pre-existing members of project 400 are
  `Test Bot` (the acting account itself) and `Levon Dadayan` (a real human
  admin) plus two orphaned seed rows. Re-inviting either real account risks a
  role overwrite on the account the whole suite authenticates as, and the
  orphan rows are leftovers nobody guarantees. Creating the "existing member"
  the test then re-invites is the same observable through a disposable subject,
  and it makes the case self-contained instead of dependent on live project
  topology. **Declared** per `.agents/role-overrides.md` § declared-improvisation
  protocol — this shapes *how* the precondition is reached, not *what* is
  verified.

### stable-existing
- None. The baseline row count is captured at runtime; nothing about the
  pre-existing rows is asserted.

## Test Steps

1. Navigate to Settings → Users.
   - **Verify**: at least one user row is visible.
   - Capture the baseline row count `N`.
2. **Precondition / case step 2** — invite the disposable address once with role
   `viewer`.
   - **Verify**: the POST resolves 200 OK, the row count becomes `N + 1`, and
     the address matches exactly ONE row. It is now a project member, and it is
     the email the rest of the case "notes".
   - Capture the post-seed row count `M = N + 1`.
3. Click "+" and enter that same (now-existing) member's email.
   - **Verify**: `users-invite-dialog` is visible and the Emails field displays
     the address.
4. Select a role (`viewer`) and click Invite.
   - **Verify**: the driving `POST /api/v2/admin/users/default/400` resolves
     **400 Bad Request** — the product refuses the duplicate at the API, not
     merely in the UI.
5. **Verify** an error is shown indicating the user is already a member:
   `toast-alert` carries `data-severity="error"` and `toast-message` reads
   exactly `user <email> already exists in project <project id>` — the string
   `buildErrorMessage()` surfaces from the backend, with the project id taken
   from `settings.users_team_project_id` (never a hardcoded `400`).
6. **Verify** no duplicate entry appears in the table:
   - the row count is still `M` (unchanged from step 2);
   - the address still matches exactly ONE row;
   - that row's Role cell still reads `viewer`.

## Expected Results
- Re-inviting an existing project member is rejected: HTTP 400, an error toast
  naming the address and the project, and no second row.
- The existing member's own row is untouched.

## Coverage Map

**Axis 1 — Source-case elements:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated "+" renders | asserted |
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` visible | asserted |
| 2 Note the email of an existing project member | Action completes without error and produces the expected UI state | step 2 | `step 2`: seeded address is present exactly once, count `N+1` | asserted |
| 3 Click "+" and enter the existing member's email | Control responds; expected next state is shown | step 3 | `step 3`: dialog visible + field value == the address | asserted |
| 4 Select any role and click Invite | Control responds; expected next state is shown | step 4 | `step 4`: POST resolves 400 | asserted |
| 5 Verify an error or warning is shown indicating the user is already a member | Condition holds as described | step 5 | `step 5`: `toast-alert[data-severity="error"]` + exact `toast-message` text | asserted |
| 6 Verify no duplicate entry appears in the table | Condition holds as described | step 6 | `step 6`: row count == `M`, address count == 1 | asserted |
| Expected Final State: no duplicate entry in the table | (restates step 6) | step 6 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- **Step 4's HTTP-400 assertion** — *added*: the case only asks for "an error or
  warning". Binding it to the driving response proves the rejection is the
  product's, at the API boundary, rather than a UI-side guess — and gives the
  toast assertion a deterministic anchor.
- **Step 5's exact message text** — *added*: "an error is shown" would pass on
  ANY error toast, including one about something else entirely. The message
  names the address and the project, so asserting it is what makes the step
  actually about *this* duplicate. String observed live 2026-08-29.
- **Step 6's role-unchanged assertion** — *added*: "no duplicate row" is
  necessary but not sufficient — a rejected invite that silently overwrote the
  existing member's role would still leave one row. Cheap, since the row is
  already resolved.
- **No console-error step** — *deliberately omitted, declared*: this case's own
  subject IS a 400 response, which the browser logs as a console error. Adding
  a console assertion would require excluding the very request under test, which
  is noise, not signal. Omission is recorded here so its absence reads as a
  decision rather than an oversight.

## Cleanup
**Mandatory.** Step 2 creates a REAL, persistent member of the shared live
project 400. The seeded address is deleted in a `finally` block via the
row-level Delete icon → confirm (`DELETE …?id[]=<id>` → **204**), with the same
per-row isolate-and-aggregate discipline ELITEA-2304's teardown uses. The
duplicate invite in step 4 creates nothing (that is the case's point), so there
is exactly one row to remove.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| "+" invite button | `users-invite-button` | pre-existing (ELITEA-2292) |
| Dialog root | `users-invite-dialog` | pre-existing — EliteaAI/EliteaUI@8f559586 |
| Emails input | `users-invite-emails-input` | pre-existing (ELITEA-2304) |
| Roles combobox / option | `users-invite-role-select-combobox` / `select-option-viewer` | pre-existing |
| Invite (confirm) button | `users-invite-confirm-button` | pre-existing (ELITEA-2304) |
| Error toast | `toast-alert` (+ `data-severity="error"`) / `toast-message` | pre-existing shared `Toast.jsx` |
| User row + Email/Role cells | `user-row` / `user-column-value-email` / `user-column-value-roles` | pre-existing (ELITEA-2292) |
| Row Delete icon + confirmation | `user-row-delete-button` / `delete-confirm-button` | pre-existing |

**No new testid is needed.**

## Network Behavior
- Seed invite: `POST /api/v2/admin/users/default/400` → **200 OK**.
- Duplicate invite: the SAME endpoint → **400 Bad Request**; the UI then still
  issues a users-list refetch GET (200), and the dialog closes anyway
  (live-observed — the dialog does not stay open on failure).
- Cleanup: `DELETE …/admin/users/default/400?id[]=<id>` → **204**.

## Known Defects Found During Exploration
None. The duplicate rejection is correct and its message is specific.

**Product-behaviour note (not a defect, worth knowing):** the Invite dialog
**closes** on the 400 as well as on success, so the user loses the typed input
on a failed invite. The case does not assert dialog state, so nothing here
depends on it; recorded in the surface digest.

## Blocked Steps
None.

## Automation Hints
- `AdminUsersPage.invite_users()` already awaits the POST regardless of status,
  so it serves step 4 unchanged and returns the 400 response.
- **The error toast lives 10 000 ms** (`TOAST_DURATION_DEFAULTS.error`), far
  more forgiving than the 3 s success toast — but assert it before the table
  reads anyway, for symmetry with the sibling family spec.
- Build the expected message from `settings.users_team_project_id`; a hardcoded
  `400` would silently rot if the env key changes.
- Do NOT assert an absolute row count — capture and compare.

### Implementation notes (2026-08-29)

- Ran green first invocation alongside the ELITEA-2296/2297 family spec
  (3 passed in 57.31 s, `reruns.json == {}`).
- Page object: the seed step reuses `invite_users([email], "viewer")`
  unchanged; the duplicate submit uses the new additive `submit_invite()`,
  which returns the POST regardless of status (400 here).
