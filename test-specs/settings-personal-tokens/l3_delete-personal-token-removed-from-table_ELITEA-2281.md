# Test Case: Delete a personal token and verify it is removed from the table

## Metadata
- **TMS ID**: ELITEA-2281
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2281.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: none — the product matches the case text on every step.
- **Testid work**: **NONE.** Every handle below is already on `EliteaAI/EliteaUI` `main`
  (verified with a fresh `git fetch origin` 2026-08-27 — see § Handles Reference).

## Why this is NOT already covered

`tests/ui/admin/test_personal_token_create_and_verify.py` (ELITEA-2280, merged) *does*
delete a token — but only in its `finally:` **cleanup** block (lines 223-240), which is
explicitly documented there as *"not an AFS case step"*. It is un-`allure.step`ped, it
asserts nothing about the confirmation dialog, and it never reloads the page. This case's
own observables — the confirmation dialog appears and gates on the typed name, the row
disappears from a settled table, and the deletion **survives a page reload** — are
asserted nowhere in the merged suite. Fresh implementation.

## Preconditions
- Logged-in user on `/settings/tokens` with the table in its **populated** branch.
- **The token this case deletes must be created by the test itself.** The 5 persistent
  live tokens (`for_ui_tests`, `Levon`, `Marian`, `New`, `uautomate`) are shared data;
  two of them (`Marian`, `New`) are irrecoverably `Expired` and the merged
  `test_expired_token_shows_expired_icon_and_label` (ELITEA-2284) reads its `expired`
  branch off them — deleting any of them is irreversible destruction of another test's
  fixture. Case step 2 says "locate an existing token"; the honest reading is "a token
  that exists at that moment", which the test's own freshly-created token satisfies.

## Test Data
### create-and-destroy
- One token created via the real UI create flow (`PersonalTokensPage.click_add_button()`
  → `CreatePersonalTokenPage.fill_name(...)` → `click_generate()` → `close_dialog()`),
  named `autotest-token-{uuid4().hex[:8]}` — the same shape ELITEA-2280 already uses.
  Defaults (`Days` / `30`) are fine; this case does not care about expiration.
- A unique name is load-bearing twice over: the row locator must resolve exactly one
  row, and the delete dialog's type-to-confirm field matches on the name (ELITEA-2288
  proves duplicate names are allowed, so a literal name could collide with leftovers).
- **No cleanup block is needed for the happy path** — deleting the token *is* the case.
  A `finally:` guard should still delete the token if the test dies before step 5, so a
  failed run does not leak a row into shared data.

## The product's actual delete contract (source + live confirmed)

- The trash icon is `DeleteEntityButton` (`token-action-delete-button`) →
  `Modal.DeleteEntityModal` (`src/[fsd]/shared/ui/modal/DeleteEntityModal.jsx`), the
  shared delete-with-confirmation modal used app-wide. Full testid set already exists.
- `shouldRequestInputName` is **true** here: the confirm button stays **disabled** until
  the typed text matches the token name **exactly** (verified live: `afs2282-day`
  → still disabled; `afs2282-days7` → enabled).
- Confirm fires `DELETE /api/v2/auth/token/{uuid}` → **204**, the dialog closes itself,
  and `TokensTable` calls `refetch()`.

### ⚠️ The refetch window — the trap this case must not fall into

`TokensTable.jsx:150` renders `!isFetchingTokens ? <table> : <spinner>`, so **during the
post-delete refetch the ENTIRE table unmounts and `token-row` count is 0 for a moment.**
Measured live: immediately after the 204, `token_row.count()` read **0**, then settled at
8 (from 9).

Consequence: `expect(deleted_row).to_have_count(0)` **passes vacuously** during that
window — it would pass even if the delete had silently failed, because *every* row is
absent. The non-vacuous shape, and the one this AFS requires:

```python
expect(tokens_page.token_row).to_have_count(rows_before - 1, timeout=ROW_WAIT_TIMEOUT)
expect(tokens_page.get_row_by_name(token_name)).to_have_count(0)
```

The first assertion waits for the table to come *back* with one fewer row (so it cannot
pass while the table is unmounted); the second then pins *which* row went.

### Live observations (2026-08-27, real clicks)

| Moment | Observed |
|---|---|
| Before delete | 9 rows, target row `afs2282-days7` present |
| Dialog opened | `delete-confirm-title` = `Delete confirmation`; `delete-confirm-message` = `Are you sure to delete the afs2282-days7? Enter the name to complete the action.`; `delete-confirm-cancel-button` = `Cancel`; `delete-confirm-button` = `Delete`, **disabled** |
| Typed partial `afs2282-day` | Delete still **disabled** |
| Typed exact `afs2282-days7` | Delete **enabled** |
| Confirm clicked | `DELETE /v2/auth/token/92b31fef-dbcb-444e-8a0a-cee7e6db0443` → **204**; dialog count 0 |
| Immediately after | **0 rows** (refetch window — see the trap above) |
| Settled | **8 rows**, target absent |
| After `page.reload()` | `GET /auth/token/` → 200, payload has **8** names, target absent; 8 rows rendered |

Console across the whole session: **0 errors** (68 entries, all `INFO`/`LOG`).

## Test Steps

1. **Setup (not a case step, wrap in its own allure.step "Setup")** — navigate to
   `/settings/tokens` and create one token via the UI create flow; return to
   `/settings/tokens` via `close_dialog()`. Capture `rows_before = token_row.count()`
   after `expect(get_row_by_name(token_name)).to_have_count(1)`.

2. **Step 1 — Navigate to Settings → Personal Tokens.**
   `PersonalTokensPage.navigate()` (already waits for the token-list GET **and** the
   first `token-row`, so the populated branch is proven, not assumed).
   - **Verify**: `personal-tokens-page-title` text == `Personal Tokens`.

3. **Step 2 — Locate an existing token in the table.**
   - **Verify**: `get_row_by_name(token_name)` has count **1**.
   - **Verify**: that row's `token-name-cell` text == `token_name`.

4. **Step 3 — Click the trash icon in the Actions column.**
   `get_row_action_icon(row, "token-action-delete-button").click()`.

5. **Step 4 — Verify a confirmation dialog appears.**
   - **Verify**: `delete-confirm-dialog` is visible.
   - **Verify**: `delete-confirm-title` text == `Delete confirmation`.
   - **Verify**: `delete-confirm-message` text == `Are you sure to delete the
     {token_name}? Enter the name to complete the action.` (build the expected string
     from `token_name`; do not hardcode a name).
   - **Verify**: `delete-confirm-button` is **disabled** before anything is typed —
     this is the "confirmation" the case step is really about.
   - **Verify**: `delete-confirm-cancel-button` is visible with text `Cancel`.

6. **Step 5 — Confirm deletion.**
   - Type a **prefix** of the name first (`token_name[:-2]`) and **verify**
     `delete-confirm-button` is still disabled (proves the gate is a real exact-match
     gate, not decoration), then type the remaining characters.
   - `fill_delete_confirm_name(token_name)` already waits for the button to enable.
   - Click Delete **inside** `page.expect_response(...)` on the `DELETE` to
     `/auth/token/` and **verify** `response.status == 204` — the side-channel proof
     that the deletion actually reached the backend.
   - **Verify**: `delete-confirm-dialog` has count 0 (the dialog closes itself).

7. **Step 6 — Verify the token is removed from the table.**
   - **Verify**: `expect(token_row).to_have_count(rows_before - 1)` — *first*, and with
     `ROW_WAIT_TIMEOUT`; this is the assertion that survives the refetch window.
   - **Verify**: `expect(get_row_by_name(token_name)).to_have_count(0)`.

8. **Step 7 — Reload the page; verify the deleted token does not reappear.**
   - `page.reload()` wrapped in `page.expect_response(<GET /auth/token/>)`; **verify**
     the GET's status is 200.
   - Re-wait for the first `token-row` to be visible (the page shows a
     `CircularProgress` for ~2-2.5 s on every load — never a fixed delay).
   - **Verify**: `expect(get_row_by_name(token_name)).to_have_count(0)`.
   - **Verify**: `expect(token_row).to_have_count(rows_before - 1)` — persistence, not
     just a client-side cache eviction.
   - **Verify (Axis 2)**: the GET response body contains no entry whose `name` ==
     `token_name` — an *independent ground truth* read straight off the API response,
     so a purely-cosmetic DOM removal cannot pass this case.

9. **Axis 2 — No console errors** across the whole flow
   (`capture_console_errors()` / `utils/console_errors.collect_console_errors`;
   0 observed live).

## Handles Reference

All handles are **already declared** on `PersonalTokensPage` /
`CreatePersonalTokenPage` — this case adds **no new page-object fields and no new
testids**.

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Token row (repeatable) | `token-row` | `PersonalTokensPage.token_row` | on-main ✓ |
| Row name cell | `token-name-cell` | `TOKEN_NAME_CELL_SELECTOR` / `get_row_name_cell()` | on-main ✓ |
| Row delete (trash) icon | `token-action-delete-button` | `get_row_action_icon(row, ...)` | on-main ✓ |
| Delete dialog root | `delete-confirm-dialog` | `delete_confirm_dialog` | on-main ✓ |
| Delete dialog title | `delete-confirm-title` | **needs a `LocatorDescriptor`** (testid exists) | on-main ✓ |
| Delete dialog message | `delete-confirm-message` | **needs a `LocatorDescriptor`** (testid exists) | on-main ✓ |
| Delete dialog cancel | `delete-confirm-cancel-button` | **needs a `LocatorDescriptor`** (testid exists) | on-main ✓ |
| Delete dialog name field | `delete-confirm-name-input` | `delete_confirm_name_input` / `fill_delete_confirm_name()` | on-main ✓ |
| Delete dialog confirm | `delete-confirm-button` | `delete_confirm_button` / `confirm_delete()` | on-main ✓ |
| Page title | `personal-tokens-page-title` | `page_title` | on-main ✓ |
| Add (+) button | `personal-tokens-add-button` | `add_button` / `click_add_button()` | on-main ✓ |
| Create-form name input | `create-personal-token-name-input` | `CreatePersonalTokenPage.name_input` | on-main ✓ |
| Generate button | `create-personal-token-generate-button` | `generate_button` / `click_generate()` | on-main ✓ |
| Dialog close (X) | `generated-token-dialog-close-button` | `dialog_close_button` / `close_dialog()` | on-main ✓ |

Provenance verified 2026-08-27 with `cd ../EliteaUI && git fetch origin` followed by the
two-stage `git grep` from `.agents/workflow.md` § Closure record against **both**
`origin/main` and `origin/automation/testids`. Every row above: `main:YES testids:YES`.

Three testids (`delete-confirm-title`, `-message`, `-cancel-button`) exist in the shared
`DeleteEntityModal.jsx` but have **no `LocatorDescriptor` yet** on
`PersonalTokensPage` — the implementer declares them as class-level fields (no EliteaUI
change).

## Automation Hints

- Target file: **`automation/tests/ui/admin/test_personal_token_create_and_verify.py`**
  is the natural home (it already owns the create + delete-cleanup flow and the page
  objects), as a new test method — or a new `test_personal_token_delete.py`. The
  implementer decides; nothing in this AFS depends on the choice.
- Markers: `ui`, `admin`, `p2`, `regression` (match the file's `pytestmark`).
- Every step wrapped in `with allure.step("Step N — …"):`; the Setup block gets its own
  step, and the `finally:` safety-net delete stays unwrapped (same shape as ELITEA-2280).
- **Never `sleep`.** The two waits that matter are `expect(...).to_have_count(...)`
  (auto-retrying, survives the refetch window) and `page.expect_response(...)`.
- The `DELETE` response is `204` with an empty body — do not call `.json()` on it.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (localhost `VITE_DEV_TOKEN`) | fixture | covered |
| Step 1 — Navigate to Settings → Personal Tokens | Page loads | Step 2 | `navigate()` + title assertion | covered |
| Step 2 — Locate an existing token in the table | No error, expected UI state | Step 3 (+ Setup creates it) | row count == 1, name-cell text | covered |
| Step 3 — Click the trash icon in the Actions column | Control responds | Step 4 | click via `get_row_action_icon` | covered |
| Step 4 — Verify a confirmation dialog appears | Condition holds | Step 5 | dialog visible + title + message + disabled confirm + cancel | covered |
| Step 5 — Confirm deletion | Operation completes, state updates | Step 6 | exact-match gate + `DELETE` 204 + dialog closes | covered |
| Step 6 — Verify the token is removed from the table | Condition holds | Step 7 | settled `to_have_count(rows_before-1)` + named row count 0 | covered |
| Step 7 — Reload; deleted token does not reappear | No error, expected state | Step 8 | reload + GET 200 + row absent + API payload absent | covered |
| Expected Final State — deleted token does not reappear after reload | — | Step 8 | same | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| `DELETE …/auth/token/{uuid}` → **204** | The case says "confirm deletion"; without the response the test cannot distinguish a real delete from a UI-only row removal. Side-channel check per the skill's step 3. |
| Confirm button disabled before/at a partial name | The case's step 4 says only "a confirmation dialog appears". The *point* of this dialog is the exact-name gate; asserting mere visibility would pass against a dialog whose gate had regressed to always-enabled. |
| Total row count == `rows_before - 1` (settled) | Non-vacuity guard for the refetch window documented above — the case's own step 6 assertion is otherwise satisfiable while the table is unmounted. |
| Deleted name absent from the reload **GET payload** | Independent ground truth (API, not a second DOM read) that the deletion persisted server-side, per `.agents/testing.md` § Merge gate's "verified against an independent ground truth" discipline. |
| No console errors across the flow | Standard side-channel axis; 0 observed live. |

## Known Defects
None. The product satisfied every step of this case exactly as written.

## Blocked Steps
None.
