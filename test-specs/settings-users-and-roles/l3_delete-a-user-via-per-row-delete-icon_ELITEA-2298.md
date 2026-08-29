# Test Case: Delete a user via per-row Delete icon

## Metadata
- **TMS ID**: ELITEA-2298
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2298.md`
- **Linked Story**: none
- **Priority**: l3 (case frontmatter `priority: medium`). **pytest marker: `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in and holding `admin` in project 400 — the per-row Delete icon is
  gated behind `PERMISSIONS.users.delete` (`UsersTable.jsx` `renderActions`),
  and 400 is the only project this account can mutate (surface digest
  § Project-topology constraint).

## Test Data

### generate-per-test
- ONE disposable member, `elitea-del-row-<uuid4-hex-8>@example.com`, invited
  with role `viewer` at the start of the test and then deleted BY the case
  itself.

  *Why a seeded subject rather than "any user row" as the case text says?*
  The four rows project 400 actually holds are the acting account
  (`testbot@elitea.ai` — deleting it destroys the suite's only mutable
  project), a real human admin (`levon_dadayan@epam.com`), and two orphaned
  seed rows nobody guarantees. "Any user row" is only safe if the row is one
  the test created. Same observable, disposable subject. **Declared** per
  `.agents/role-overrides.md` § declared-improvisation protocol — this shapes
  *how* the subject is obtained, not *what* is verified.

### stable-existing
- None. The baseline row count is captured at runtime; nothing about the
  pre-existing rows is asserted beyond "unchanged in count".

## Test Steps

1. Navigate to Settings → Users.
   - **Verify**: at least one user row is visible.
   - Capture the baseline row count `N`.
2. **Precondition** — invite the disposable address with role `viewer`.
   - **Verify**: the POST resolves 200 OK, the row count becomes `N + 1`, and
     the address matches exactly ONE row.
3. Click that row's trash icon (`user-row-delete-button`, scoped INSIDE the
   row — never a page-level handle).
   - **Verify**: no `DELETE` has fired yet (the icon only opens a dialog) —
     asserted against the **request log**, not the table. A passive
     `page.on("request")` observer (`utils.request_capture.collect_requests`)
     is registered before the first click and read once the dialog has
     rendered; that render is the anchor proving the product finished reacting.
     A row read cannot make this claim: a row outlives a `DELETE` in flight.
4. **Verify** a confirmation dialog appears:
   - `delete-confirm-dialog` is visible;
   - `delete-confirm-title` reads exactly `Delete confirmation`;
   - `delete-confirm-message` contains `Are you sure to delete the selected user`
     (the singular branch — `DeleteUserButton.jsx` passes
     `users.length > 1 ? …users : …user `);
   - both `delete-confirm-button` (`Delete`) and
     `delete-confirm-cancel-button` (`Cancel`) are visible.
5. Confirm deletion — click `delete-confirm-button`.
   - **Verify**: the driving `DELETE /api/v2/admin/users/default/400?id[]=<id>`
     resolves **204 No Content**;
   - **Verify**: a success confirmation is shown — `toast-alert` carries
     `data-severity="success"` (asserted FIRST, before any table read: the
     success toast auto-hides after 3 000 ms);
   - **Verify**: the dialog is gone;
   - **Verify**: the request log now holds **exactly one** `DELETE` — the
     positive control for step 3's absence assertion, which would otherwise
     pass vacuously if the observer were never wired.
6. **Verify** the user is removed from the table: the seeded address matches
   ZERO rows and the row count is back to `N`.
7. Reload the page — **verify** the user does not reappear: after the users-list
   GET resolves, the seeded address still matches ZERO rows and the count is `N`.

## Expected Results
- The per-row trash icon opens a confirmation dialog and deletes nothing on its own.
- Confirming issues one `DELETE` (204), shows a success toast, and removes exactly
  that row.
- The removal is server-side, so it survives a full page reload.

## Coverage Map

**Axis 1 — Source-case elements:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — the permission-gated row actions render | asserted |
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` visible, count captured | asserted |
| 2 Click the trash icon in the Actions column of any user row | Control responds; expected next state is shown | step 3 | `step 3`: click + request log empty (no DELETE issued) | asserted |
| 3 Verify a confirmation dialog appears | Condition holds as described | step 4 | `step 4`: dialog visible + title/message/buttons | asserted |
| 4 Confirm deletion | Operation completes successfully; state updates and confirmation is shown | step 5 | `step 5`: DELETE 204 + success toast + dialog gone + request log holds exactly one DELETE | asserted |
| 5 Verify the user is removed from the table | Condition holds as described | step 6 | `step 6`: address count 0, row count back to `N` | asserted |
| 6 Reload the page — verify the user does not reappear | Action completes without error and produces the expected UI state | step 7 | `step 7`: post-reload address count 0, row count `N` | asserted |
| Expected Final State: the user does not reappear after reload | (restates step 6) | step 7 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- **Step 3's "no DELETE yet" assertion** — *added*: the case only says the
  control "responds". Proving the icon is non-destructive on its own is the
  half of the confirm-dialog contract the case never states, and it is what
  distinguishes this flow from a one-click delete. It is a **request-log**
  assertion by construction — the observable that separates "issued nothing"
  from "issued something that has not landed yet".
- **Step 5's "exactly one DELETE" count** — *added*: an absence assertion is
  unfalsifiable without a positive control, so the step that genuinely issues
  the request doubles as proof the observer was wired.
- **Step 5's HTTP-204 assertion** — *added*: "operation completes successfully"
  is only trustworthy if the driving request is the one that succeeded. It also
  gives the toast and table assertions a deterministic anchor instead of a wait.
- **Step 4's exact dialog texts** — *added*: "a confirmation dialog appears"
  would pass on any modal. Title + singular message text tie it to THIS dialog
  and THIS branch. Texts observed live 2026-08-29.
- **Row-count invariant in steps 6-7** — *added*: "the user is removed" is
  satisfied by a table that lost the row *and* three others. Comparing against
  the captured baseline makes the delete provably surgical.
- **Console-error step** — *added* (project convention on this surface),
  excluding the ONE `#1971` URL by exact match.

## Cleanup
The case's own step 4 IS the deletion, so the happy path leaves nothing behind.
A `finally` block still removes the seeded address if the test dies before
step 5 (isolate-and-aggregate, same discipline as ELITEA-2296/2304), because
the seed creates a REAL, persistent member of shared live project 400.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| User row | `user-row` | pre-existing (ELITEA-2292) |
| Row Email / Role cells | `user-column-value-email` / `user-column-value-roles` | pre-existing |
| Row Delete (trash) icon | `user-row-delete-button` | pre-existing (`UsersTable.jsx` `renderActions`) |
| Confirmation dialog root | `delete-confirm-dialog` | pre-existing shared `DeleteEntityModal.jsx` |
| Dialog title | `delete-confirm-title` | pre-existing shared |
| Dialog message | `delete-confirm-message` | pre-existing shared |
| Dialog Delete button | `delete-confirm-button` | pre-existing shared |
| Dialog Cancel button | `delete-confirm-cancel-button` | pre-existing shared |
| Success toast | `toast-alert` (+ `data-severity`) / `toast-message` | pre-existing shared `Toast.jsx` |
| Invite controls (seeding) | `users-invite-button` / `-emails-input` / `-role-select-combobox` / `-confirm-button` | pre-existing |

**No new testid is needed.**

## Network Behavior
- Seed invite: `POST /api/v2/admin/users/default/400` → **200 OK**, followed by
  a users-list refetch GET.
- Opening the dialog: **no request at all** (live-confirmed).
- Confirm: `DELETE /api/v2/admin/users/default/400?id[]=<user id>` → **204 No
  Content** (live-observed: `?id[]=1019`), followed by a users-list refetch GET.
- Reload: the usual pair — users-list GET + roles GET, both 200.

## Known Defects Found During Exploration
None on this flow. The per-row delete is clean: one DELETE, one toast, the row
disappears, and the page keeps working.

*(The header BATCH delete — a different control, ELITEA-2299 — is NOT clean:
see #1974 / #1975. The per-row instance escapes #1974's render loop because its
own row unmounts when the refetch removes it, which breaks the effect's
dependency cycle. Worth knowing, since both controls are the same component.)*

## Blocked Steps
None.

## Automation Hints
- `AdminUsersPage.delete_user_row()` already does click-then-confirm in ONE
  call, which cannot express step 3's "dialog appeared, nothing deleted yet".
  Split it additively: `open_delete_dialog_for_row(row)` +
  `confirm_delete()` — leave `delete_user_row()` byte-identical, it has merged
  callers (ELITEA-2296/2304 teardowns).
- Assert the success toast in the same step the DELETE resolves; 3 000 ms is
  short enough that a table read first will miss it.
- Do NOT assert an absolute row count — capture the baseline and compare.
- Reload via `page.reload()` and wait on the users-list GET, never on
  `networkidle` (`#1847`).

### Implementation notes (2026-08-29)

- Shipped as `automation/tests/ui/admin/test_user_delete_via_row_icon.py`;
  **green on the first invocation** (`reruns.json == {}`).
- Page object (all additive; `delete_user_row()` left byte-identical for its
  four merged teardown callers): `open_delete_dialog_for_row()`,
  `confirm_delete()`, `reload_and_wait()`, plus the four
  `delete_confirm_*` descriptors.
- Step 6's reload waits on the users-list GET via `reload_and_wait()` — not on
  `networkidle`, which is `#1847`.

### Fix round 1 (2026-08-29, PR #1976 review)
- Step 3's "no `DELETE` yet" clause had shipped as a table read
  (`expect(get_row_by_text(email)).to_have_count(1)`), which the AFS's own
  wording never authorised: a row survives an in-flight `DELETE`. Now asserted
  against the request log, with step 5's exactly-one-`DELETE` count as its
  positive control.
- The observer is the new shared helper `automation/utils/request_capture.py`
  (`collect_requests(page, method="DELETE")`) — passive, capture-only, no
  interception. ELITEA-2300 had already hand-rolled the same listener inline; it
  now uses the shared helper too, so there is one shape rather than two.
- Regression coverage: `automation/tests/unit/test_request_capture_backs_absence_claims.py`
  pins both the helper's behaviour and the source-level requirement that a spec
  claiming "no DELETE was issued" asserts it against the log AND carries a
  positive control. Verified red against pre-fix `HEAD`.
