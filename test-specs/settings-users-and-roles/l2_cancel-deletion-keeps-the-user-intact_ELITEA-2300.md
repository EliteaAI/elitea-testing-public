# Test Case: Cancel deletion keeps the user intact

## Metadata
- **TMS ID**: ELITEA-2300
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2300.md`
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: high`). **pytest marker: `@pytest.mark.p1`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in and holding `admin` in project 400 — the per-row Delete icon is
  permission-gated and 400 is the only project this account can mutate
  (surface digest § Project-topology constraint).

## Test Data

### generate-per-test
- ONE disposable member, `elitea-del-cancel-<uuid4-hex-8>@example.com`, invited
  with role `viewer`.

  *Why seeded rather than "any user row"?* The case is non-destructive by
  design, so an existing row would be safe — but the assertion is "the user
  remains in the table **unchanged**", and only a row whose every field the test
  itself established can be compared field-by-field without hardcoding a real
  person's name or a live `last_login` datetime that changes under the test.
  A seeded row has three known, stable values (name `""`, last login `-`, role
  `viewer`). **Declared** per `.agents/role-overrides.md`
  § declared-improvisation protocol — shapes *how* the subject is obtained,
  not *what* is verified.

### stable-existing
- None asserted by identity. The baseline row count is captured at runtime.

## Test Steps

1. Navigate to Settings → Users.
   - **Verify**: at least one user row is visible.
   - Capture the baseline row count `N`.
2. **Precondition** — invite the disposable address with role `viewer`.
   - **Verify**: the POST resolves 200 OK and the address matches exactly ONE
     row; the row count is `N + 1`.
   - Capture that row's three rendered field values (Name, Last login, Role) —
     the "unchanged" comparison of case step 5 needs a before-image taken from
     the product, not from the test's assumptions.
3. Click that row's trash icon (`user-row-delete-button`, scoped inside the row).
4. **Verify** a confirmation dialog appears:
   - `delete-confirm-dialog` visible;
   - `delete-confirm-title` reads exactly `Delete confirmation`;
   - `delete-confirm-message` contains `Are you sure to delete the selected user`;
   - `delete-confirm-cancel-button` reads exactly `Cancel`.
5. Click `Cancel`.
   - **Verify**: the dialog is gone (`delete-confirm-dialog` count 0).
6. **Verify the user remains in the table unchanged**:
   - the address still matches exactly ONE row;
   - that row's Name / Last login / Role cells still equal the before-image
     captured in step 2;
   - the row count is still `N + 1`;
   - **no `DELETE` request was ever issued** during the whole test — the
     strongest form of "nothing was deleted", and the one a table read alone
     cannot give (a table can look right while a delete is in flight);
   - no toast was raised.

## Expected Results
- Cancelling the confirmation dismisses the dialog, issues no request, and
  leaves the target row and the rest of the table exactly as they were.

## Coverage Map

**Axis 1 — Source-case elements:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated row actions render | asserted |
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` visible | asserted |
| 2 Click the trash icon on any user row | Control responds; expected next state is shown | step 3 | `step 3`: click on the seeded row's icon | asserted |
| 3 Verify a confirmation dialog appears | Condition holds as described | step 4 | `step 4`: dialog visible + title/message/Cancel | asserted |
| 4 Click Cancel / close the dialog | Control responds; expected next state is shown | step 5 | `step 5`: dialog count 0 | asserted |
| 5 Verify the user remains in the table unchanged | Condition holds as described | step 6 | `step 6`: row count 1, three cells == before-image, row count `N+1`, zero DELETEs, no toast | asserted |
| Expected Final State: the user remains in the table unchanged | (restates step 5) | step 6 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- **"No DELETE request was issued"** — *added*, and the most load-bearing
  assertion in the case: "the user remains in the table" is a UI read, and a UI
  read cannot distinguish "nothing happened" from "a delete fired and the table
  has not refreshed yet". Live-verified: cancelling produces no request at all.
- **Field-by-field before/after comparison** — *added*: the case says
  "unchanged", which a mere presence check does not prove. Three cells, captured
  from the product before the dialog and compared after.
- **"Close (×) as well as Cancel"** — *not* added. The case step says
  "Click Cancel / close the dialog"; the two are separate controls
  (`delete-confirm-cancel-button` vs `delete-confirm-close-button`) and the case
  reads as one action with two names, not two required paths. Cancel is asserted;
  the × is left to a case that names it. Recorded so the omission is a decision.
- **Console-error step** — *added* (project convention on this surface),
  excluding the ONE `#1971` URL by exact match.

## Cleanup
**Mandatory.** Unlike ELITEA-2298/2299, this case deliberately does NOT delete
its subject — so the seeded member survives the test body and MUST be removed in
a `finally` block (row Delete → confirm, `DELETE …?id[]=<id>` → 204), with the
isolate-and-aggregate discipline ELITEA-2296/2304 use. The two orphaned
`elitea-batch-edit-test2-*` rows already sitting in project 400 are what a
missing teardown looks like.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| User row | `user-row` | pre-existing (ELITEA-2292) |
| Row Name / Last login / Role / Email cells | `user-row-name` / `user-column-value-last_login` / `user-column-value-roles` / `user-column-value-email` | pre-existing |
| Row Delete (trash) icon | `user-row-delete-button` | pre-existing |
| Confirmation dialog + title + message | `delete-confirm-dialog` / `delete-confirm-title` / `delete-confirm-message` | pre-existing shared `DeleteEntityModal.jsx` |
| Dialog Cancel button | `delete-confirm-cancel-button` | pre-existing shared |
| Toast | `toast-alert` | pre-existing shared `Toast.jsx` |
| Invite controls (seeding) | `users-invite-*` | pre-existing |

**No new testid is needed.**

## Network Behavior
- Seed invite: `POST …/admin/users/default/400` → **200 OK** + refetch GET.
- Opening the dialog: **no request**.
- Cancel: **no request** — live-verified against the full request log
  (only the seed POST and the list GETs appear).
- Cleanup: `DELETE …?id[]=<id>` → **204**.

## Known Defects Found During Exploration
None. The cancel path is clean and genuinely inert.

## Blocked Steps
None.

## Automation Hints
- Split the existing `delete_user_row()` additively — this case needs
  `open_delete_dialog_for_row(row)` and `cancel_delete()`; leave
  `delete_user_row()` byte-identical (merged callers).
- Count DELETEs with a `page.on("request", …)` listener registered before the
  first click — a passive observer, no interception, no substitution.
- Capture the before-image with `.inner_text()` reads, then compare with
  `expect(...).to_have_text(...)` so the after-read still auto-retries.

### Implementation notes (2026-08-29)

- Shipped as `automation/tests/ui/admin/test_user_delete_cancel_keeps_user.py`;
  **green on the first invocation** (`reruns.json == {}`).
- Page object (additive): `open_delete_dialog_for_row()`, `cancel_delete()`
  (waits for the dialog to detach), plus the `delete_confirm_*` descriptors.
- The "no DELETE was issued" assertion is a `page.on("request", …)` listener
  registered before the first click — a passive observer, no interception, no
  substitution.
- The before-image is asserted against the documented invitee null shapes
  (Name `""`, Last login `"-"`) at capture time, so a change in how the product
  renders a never-logged-in user surfaces here rather than silently rebasing
  the comparison.

### Fix round 1 (2026-08-29, PR #1976 review)
- The inline `page.on("request", ...)` DELETE observer this case shipped was the
  correct shape; it is now the shared helper
  `automation/utils/request_capture.py` (`collect_requests(page)`), extracted so
  ELITEA-2298 — whose own "no `DELETE` yet" clause had shipped as a table read —
  uses the same one. Behaviour is unchanged: passive, capture-only, no URL
  filtering.
- Step 5's absence assertion gained a **positive control** in the cleanup block:
  the teardown delete must appear in the log. Without it, `assert not
  delete_requests` would pass vacuously if the listener were never wired.
- Regression coverage: `automation/tests/unit/test_request_capture_backs_absence_claims.py`.
