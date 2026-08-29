# Test Case: Batch delete multiple users using checkboxes

## Metadata
- **TMS ID**: ELITEA-2299
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2299.md`
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: high`). **pytest marker: `@pytest.mark.p1`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation — **sanctioned-RED**, see § Known Defects
  and `.agents/testing.md` § Merge gate → *Analysis-time entry*.

## Preconditions
- Logged in and holding `admin` in project 400 — the header batch-Delete icon
  and the row checkboxes are permission-gated, and 400 is the only project this
  account can mutate (surface digest § Project-topology constraint).

## Test Data

### generate-per-test
- TWO disposable members, `elitea-del-batch-<uuid4-hex-8>-{1,2}@example.com`,
  invited together (one comma-separated invite, one POST) with role `viewer`
  and then deleted BY the case itself.

  *Why seeded subjects?* Identical reasoning to ELITEA-2298: the only rows
  project 400 holds are the acting account, a real human admin, and two
  orphaned seed rows. A batch delete needs two rows it is safe to destroy, so
  the test creates them. **Declared** per `.agents/role-overrides.md`
  § declared-improvisation protocol — shapes *how* the subjects are obtained,
  not *what* is verified.

### stable-existing
- The rows already present are used ONLY as the "all other users remain
  unaffected" control: their email set is captured at runtime before the delete
  and compared afterwards. No identity, count or datetime is hardcoded.

## Test Steps

1. Navigate to Settings → Users.
   - **Verify**: at least one user row is visible.
   - **Verify**: with nothing selected, the header Delete icon
     (`users-header-delete-button`) is **disabled** — the "becomes active"
     claim of case step 3 needs a proven starting state.
   - Capture the baseline row count `N`.
2. **Precondition** — invite the two disposable addresses with role `viewer`.
   - **Verify**: the POST resolves 200 OK and the row count becomes `N + 2`.
   - Capture the set of *other* emails `O` (every rendered email except the two
     seeded ones) — this is the control set for case step 8.
3. Select the checkboxes on the two seeded rows
   (`user-row-checkbox`, scoped inside each row — never select-all).
   - **Verify**: both seeded rows read checked and every other row reads
     unchecked.
4. **Verify** the header Delete icon has become **enabled**.
5. Click the header Delete icon.
   - **Verify**: no `DELETE` has fired yet.
6. **Verify** a confirmation dialog appears:
   - `delete-confirm-dialog` visible;
   - `delete-confirm-title` reads exactly `Delete confirmation`;
   - `delete-confirm-message` reads exactly
     `Are you sure to delete the selected users?` — the **plural** branch, which
     is what proves the dialog knows a multi-row selection is in play.
7. Confirm deletion — click `delete-confirm-button`.
   - **Verify**: the driving `DELETE …?id[]=<id1>&id[]=<id2>` resolves
     **204 No Content**;
   - **Verify**: a success toast (`data-severity="success"`) is shown.
8. **Verify only the selected users are removed, in place** —
   `expect.soft`, **Known defect: #1974**. Expected (asserted as the CORRECT
   behaviour): the table re-renders with `N` rows and neither seeded address
   present. Actual today: the page enters an unbounded React re-render loop and
   the table stays empty forever. This assertion is the visible signal and flips
   green when #1974 ships.
9. Reload the page, then **verify the data truth** (hard assertions — the
   deletion itself is correct even while the UI is stuck):
   - neither seeded address matches any row;
   - the rendered email set equals the control set `O` captured in step 2 —
     i.e. **all other users remain unaffected**, none removed and none added;
   - the row count is back to `N`.

## Expected Results
- The header Delete icon is inert until at least one row is selected, and active
  once rows are selected.
- Confirming deletes exactly the selected users in one `DELETE` (204) and shows a
  success confirmation.
- Every non-selected user survives, unchanged.
- **Not met today:** the table does not recover in place after the confirm
  (#1974).

## Coverage Map

**Axis 1 — Source-case elements:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated controls render | asserted |
| 1 Navigate to Settings → Users as Admin | Target page/section loads successfully | step 1 | `step 1`: `user_row` visible | asserted |
| 2 Select checkboxes on two or more user rows | Control responds; expected next state is shown | step 3 | `step 3`: both seeded rows checked, others unchecked | asserted |
| 3 Verify the Delete (trash) icon in the header becomes active | Condition holds as described | steps 1 + 4 | `step 1`: disabled with no selection; `step 4`: enabled after | asserted |
| 4 Click the header Delete icon | Control responds; expected next state is shown | step 5 | `step 5`: click + no DELETE yet | asserted |
| 5 Verify a confirmation dialog appears | Condition holds as described | step 6 | `step 6`: dialog visible + title + plural message | asserted |
| 6 Confirm deletion | Operation completes successfully; state updates and confirmation is shown | step 7 | `step 7`: DELETE 204 + success toast | asserted |
| 7 Verify only the selected users are removed | Condition holds as described | steps 8 + 9 | `step 8` soft (in place, #1974) + `step 9` hard (after reload) | asserted (partly soft — defect-linked) |
| 8 Verify all other users remain unaffected | Condition holds as described | step 9 | `step 9`: rendered email set == control set `O` | asserted |
| Expected Final State: all other users remain unaffected | (restates step 8) | step 9 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- **Step 1's "disabled with no selection"** — *added*: "becomes active" is a
  transition, and a transition needs both ends. Asserting only the enabled end
  would pass on a button that was always enabled.
- **Step 5's "no DELETE yet"** — *added*: proves the header icon is
  non-destructive on its own, the same contract the per-row icon has
  (ELITEA-2298 step 3).
- **Step 7's HTTP-204 assertion** — *added*: anchors "operation completes
  successfully" to the driving request, and gives the toast a deterministic
  moment to be asserted at (success toasts live 3 000 ms).
- **Step 6's exact plural text** — *added*: singular-vs-plural is the product's
  own signal that a multi-row selection reached the dialog. Text observed live.
- **Step 9's SET comparison rather than a count** — *added*: "all other users
  remain unaffected" is not proven by a row count; a count survives a swap.
  Comparing the email set catches removal AND accidental addition.
- **No console-error step** — *deliberately omitted, declared*: #1974 floods the
  console with thousands of `Maximum update depth exceeded` errors from the same
  root cause step 8 already asserts. A console assertion here would be a second
  red for one defect, not extra signal. Re-add it when #1974 ships. Omission
  recorded so its absence reads as a decision, not an oversight.

## Cleanup
The case's own step 7 IS the deletion. A `finally` block still removes whichever
seeded address survives if the test dies earlier (isolate-and-aggregate, per-row
delete, same discipline as ELITEA-2296/2304) — the seeds are REAL, persistent
members of shared live project 400.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| Header batch Delete icon | `users-header-delete-button` | pre-existing (ELITEA-2292) |
| Row checkbox | `user-row-checkbox` | pre-existing (ELITEA-2292) |
| User row + Email cell | `user-row` / `user-column-value-email` | pre-existing |
| Confirmation dialog + title + message | `delete-confirm-dialog` / `delete-confirm-title` / `delete-confirm-message` | pre-existing shared `DeleteEntityModal.jsx` |
| Dialog Delete / Cancel buttons | `delete-confirm-button` / `delete-confirm-cancel-button` | pre-existing shared |
| Success toast | `toast-alert` (+ `data-severity`) | pre-existing shared `Toast.jsx` |
| Invite controls (seeding) | `users-invite-*` | pre-existing |

**No new testid is needed.**

## Network Behavior
- Seed invite (2 addresses, one comma-separated submit):
  `POST /api/v2/admin/users/default/400` → **200 OK**, ONE call.
- Selecting rows / opening the dialog: **no request**.
- Confirm: ONE `DELETE /api/v2/admin/users/default/400?id[]=<id1>&id[]=<id2>`
  → **204 No Content** (`DeleteUserButton` maps the whole selection into a
  single call).
- Afterwards the stuck page issues users-list refetch GETs in a loop (#1974); a
  reload settles it and the subsequent list GET returns the correct set.

## Known Defects Found During Exploration

- **#1974 — [BUG] Users batch delete leaves the page in an infinite React
  re-render loop; table stuck empty until reload.** Deterministic, single-cause,
  structural (`DeleteUserButton.jsx`'s success `useEffect` calls
  `setSelectedUsers([])` while `users` is in its own dependency array, so a new
  array identity re-triggers it forever). Handled per the no-masking decision
  tree: `expect.soft()` on the CORRECT expected behaviour + `# Known defect:
  #1974`, then a reload so the rest of the case is still verified. This makes
  the spec **sanctioned-RED** — merge-gate criteria (a)+(b)+(c) all hold, and
  the case stays `blocked-on-#1974`, not `automated`.
- **#1975 — [MINOR] the batch-delete success toast uses the SINGULAR text**
  (`The user user has been successfully deleted.`) for a multi-user delete,
  because the same effect has already emptied `users` by the time the message is
  built. The case only asks that "confirmation is shown", so step 7 asserts the
  toast's presence and `success` severity, NOT its wording — asserting the
  current wording would freeze a bug into the contract, and soft-asserting the
  correct wording would add a second red for a cause #1974 already covers.

## Blocked Steps
None — every case step is exercised; step 7's in-place half is defect-linked
rather than skipped.

## Automation Hints
- `select_user_row(row)` and `is_row_checkbox_checked(row)` already exist
  (ELITEA-2304). Add `batch_delete_selected()` additively: click the header
  Delete, wait for the dialog, confirm, return the DELETE response.
- The stuck page after step 7 means **no locator assertion on the table can be
  trusted until the reload** — do the soft assertion with a short timeout so the
  known red costs seconds, not the full default wait.
- Build the control set `O` from the rendered email cells at runtime; never
  hardcode `Levon Dadayan` / `Test Bot` / the orphaned seed rows.
