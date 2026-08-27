# Test Case: Duplicate token names are allowed

## Metadata
- **TMS ID**: ELITEA-2288
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2288.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: none — the product matches the case text on every step.
- **Testid work**: **NONE.** Every handle below is already on `EliteaAI/EliteaUI` `main`.

## Why this is NOT already covered

Every merged personal-token test creates at most one token with a `uuid4`-suffixed unique
name — by construction they can never observe the duplicate-name behaviour. Nothing in
the suite asserts that a second create with an identical name succeeds, that both rows
render, or that their masked values differ. Fresh implementation.

## Preconditions
- Logged-in user; `/settings/tokens` reachable.
- No specific existing data required (the case creates both tokens itself).

## Test Data
### create-and-destroy
- **Two** tokens created through the real UI create flow, both with the **same** name.
- ⚠️ **Do NOT hardcode the case's literal `"duplicate-test"`.** Use
  `dup_name = f"duplicate-test-{uuid4().hex[:8]}"` for *both* creates. The case's intent
  is "two tokens sharing one name"; the literal string is illustrative. A literal name
  makes the test collide with any leftover from an earlier failed run — and since this
  very case proves duplicates are permitted, a leftover would silently make the row-count
  assertion read 3 instead of 2 and fail a correct product. (The name still satisfies
  `TOKEN_NAME_PATTERN = /^[a-zA-Z0-9_-]*$/`.)
- Defaults (`Days`/`30`) are fine; expiration is irrelevant to this case.
- **Mandatory cleanup** (`finally:`): delete **both** rows. Deleting by name is
  inherently ambiguous here — see § Automation Hints for the safe loop.

## The product's actual duplicate-name contract (live confirmed)

- The create form performs **no uniqueness check**: with an existing token of the same
  name, the Generate button was enabled and `create-personal-token-name-error` had
  count **0** on the *second* create too.
- Both creates returned `POST /api/v2/auth/token/` → **200**, with distinct identities:

  | Create | `id` | `uuid` | token tail |
  |---|---|---|---|
  | 1st | `12903` | `622c8e9d-ba52-4882-9e27-bba98fc3ca8a` | `pahA` |
  | 2nd | `12904` | `3f7841ac-94eb-4893-8767-4a9b8539f482` | `5d7w` |

- The table then rendered **two** rows named `duplicate-test`, with masked values
  `...pahA` and `...5d7w` — the value cell is `'...' + row.token.slice(-4)`
  (`TokensTable.jsx` `renderCell`), so distinct tokens ⇒ (near-certainly) distinct masked
  values. No error toast, no console error.
- Deletion is per-row by `uuid` (`DELETE /v2/auth/token/{uuid}`), so the two rows are
  independently deletable even though they share a name (verified live in cleanup: both
  deleted, 204 each).

### ⚠️ The masked-value collision caveat (Axis-1 step 5, read this before asserting)

The masked value is only the **last 4 characters** of a JWT, so two distinct tokens can
in principle share the same 4-char tail (~1 in 1.7 M for base64url characters). Asserting
`value_a != value_b` is the case's own expected result and is the right assertion — but
the test must **not** treat a rare collision as a product defect. Mitigation, in order:

1. Assert the two rows' **`token-value-cell` texts differ** (the case's step 5).
2. Additionally assert (Axis 2) that the two **full token strings captured from the two
   success dialogs** differ — those are 100+ chars and produced by the system, so this is
   the robust statement of "each token has a distinct value", and it makes any future
   masked-value collision diagnosable rather than mysterious.

## Test Steps

1. **Step 1 — Navigate to Settings → Personal Tokens.**
   `PersonalTokensPage.navigate()`.
   - **Verify**: `personal-tokens-page-title` text == `Personal Tokens`.
   - **Capture** `rows_before = token_row.count()`.
   - **Verify (guard)**: `expect(get_row_by_name(dup_name)).to_have_count(0)` — the
     generated name must not already exist, or every later count is off by one.

2. **Step 2 — Create a token with name `dup_name`.**
   - `click_add_button()` → `fill_name(dup_name)` → `click_generate()`.
   - **Verify**: `response.status == 200`.
   - **Capture** `token_1 = get_dialog_token_value_text()` (the full token string from
     the success dialog — needed by step 5's Axis-2 assertion).
   - **Verify**: `generated-token-dialog-token-name` text == `dup_name`.
   - `close_dialog()`.
   - **Verify**: `expect(get_row_by_name(dup_name)).to_have_count(1)` with
     `ROW_WAIT_TIMEOUT` (auto-retrying — the table unmounts during the post-create
     refetch; a bare `count()` here reads 0).

3. **Step 3 — Create a second token with the SAME name `dup_name`.**
   - `click_add_button()` → `fill_name(dup_name)`.
   - **Verify (Axis 2, before submitting)**: `create-personal-token-name-error` has count
     **0** and `generate_button` is **enabled** — the form offers no
     duplicate-name objection. This is where a uniqueness regression would first appear,
     and it is observable before any network call.
   - `click_generate()` → **verify** `response.status == 200` (the case's "operation
     completes successfully" — a `409`/`400` here is exactly what this case exists to
     catch).
   - **Capture** `token_2 = get_dialog_token_value_text()`.
   - `close_dialog()`.

4. **Step 4 — Verify both tokens appear in the table without error.**
   - **Verify**: `expect(get_row_by_name(dup_name)).to_have_count(2)` with
     `ROW_WAIT_TIMEOUT`.
   - **Verify**: `expect(token_row).to_have_count(rows_before + 2)` — proves two rows were
     *added*, so the count-of-2 cannot be satisfied by a leftover plus one new row.
   - **Verify**: both matched rows' `token-name-cell` texts == `dup_name`
     (`expect(rows.locator(TOKEN_NAME_CELL_SELECTOR)).to_have_text([dup_name, dup_name])`).
   - **Verify (absence / "without error")**: no error toast is present — assert the app's
     generic `toast-message` has count 0 at this point (`CreatePersonalTokenPage.toast_message`
     already exists; the only toast this flow ever raises is the Copy confirmation, which
     this test never triggers).

5. **Step 5 — Verify each token has a distinct masked token value.**
   - Read both rows' `token-value-cell` texts into `masked_1`, `masked_2`.
   - **Verify**: both match the mask shape `^\.\.\..{4}$` (i.e. `...` + 4 chars) — a blank
     or unmasked cell must not pass as "distinct".
   - **Verify**: `masked_1 != masked_2` (the case's expected final state).
   - **Verify (Axis 2)**: `token_1 != token_2` — the full token strings captured from the
     two success dialogs, and each masked value equals `'...' + token_N[-4:]`, which ties
     each row to the token that actually created it. See § the collision caveat.

6. **Axis 2 — No console errors** across the flow (0 observed live).

7. **Cleanup (`finally:`, unwrapped)** — delete **both** rows; see § Automation Hints.

## Handles Reference

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Page title | `personal-tokens-page-title` | `PersonalTokensPage.page_title` | on-main ✓ |
| Add (+) button | `personal-tokens-add-button` | `click_add_button()` | on-main ✓ |
| Name input | `create-personal-token-name-input` | `CreatePersonalTokenPage.name_input` / `fill_name()` | on-main ✓ |
| Name validation error (asserted ABSENT) | `create-personal-token-name-error` | `name_error` | on-main ✓ |
| Generate button | `create-personal-token-generate-button` | `generate_button` / `click_generate()` | on-main ✓ |
| Success dialog token value | `generated-token-dialog-token-value` | `dialog_token_value` / `get_dialog_token_value_text()` | on-main ✓ |
| Success dialog token name | `generated-token-dialog-token-name` | `dialog_token_name` | on-main ✓ |
| Dialog close (X) | `generated-token-dialog-close-button` | `dialog_close_button` / `close_dialog()` | on-main ✓ |
| Token row (repeatable) | `token-row` | `token_row` / `get_row_by_name()` | on-main ✓ |
| Row name cell | `token-name-cell` | `TOKEN_NAME_CELL_SELECTOR` / `get_row_name_cell()` | on-main ✓ |
| Row masked value cell | `token-value-cell` | `TOKEN_VALUE_CELL_SELECTOR` / `get_row_value_cell()` | on-main ✓ |
| Toast (asserted ABSENT) | `toast-message` | `CreatePersonalTokenPage.toast_message` | on-main ✓ |
| Row delete icon | `token-action-delete-button` | `get_row_action_icon()` | on-main ✓ |
| Delete dialog name field / confirm | `delete-confirm-name-input` / `delete-confirm-button` | `fill_delete_confirm_name()` / `confirm_delete()` | on-main ✓ |

Provenance verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`, two-stage
`git grep` against `origin/main` **and** `origin/automation/testids` — all `YES`/`YES`.
**No new page-object fields are required** for this case.

## Automation Hints

- Target file: **`automation/tests/ui/admin/test_personal_token_create_and_verify.py`**
  as a new test method, or a dedicated `test_personal_token_duplicate_names.py`.
- Markers: `ui`, `admin`, `p2`, `regression`.
- **`get_row_by_name(dup_name)` deliberately resolves TWO rows here.** Any single-row
  operation must index (`.nth(0)` / `.first`) — a bare call on a 2-match locator raises
  Playwright's strict-mode error. This is the one place in this surface where the
  repo's usual "row by name" idiom is not one-to-one; say so in the docstring.
- **Cleanup loop (verified live, deletes both):**
  ```python
  rows = tokens_page.get_row_by_name(dup_name)
  while rows.count() > 0:
      row = rows.first
      tokens_page.get_row_action_icon(row, "token-action-delete-button").click()
      tokens_page.delete_confirm_dialog.wait_for(state="visible", timeout=10_000)
      tokens_page.fill_delete_confirm_name(dup_name)   # name matches either row — fine,
      tokens_page.confirm_delete()                     # the DELETE is by the row's uuid
      # the table unmounts during the refetch — wait for it to come back before re-counting
      tokens_page.token_row.first.wait_for(state="visible", timeout=ROW_WAIT_TIMEOUT)
  ```
  The type-to-confirm field matches on the *name*, so both rows accept the same typed
  value; the actual `DELETE` targets the clicked row's `uuid`. Confirmed live: two
  sequential deletes, `204` each, table settled at 6 then 5 rows.
- Never `sleep`; the post-create/post-delete refetch is covered by `expect(...)` polling
  and the `wait_for(state="visible")` on the returning table.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | covered |
| Step 1 — Navigate to Settings → Personal Tokens | Page loads | Step 1 | `navigate()` + title + name-not-already-present guard | covered |
| Step 2 — Create a token named `duplicate-test` | Operation completes, confirmation shown | Step 2 | `POST` 200 + dialog name + row count 1 | covered (name is uuid-suffixed — see § Test Data) |
| Step 3 — Create a second token with the same name | Operation completes, confirmation shown | Step 3 | no name error + Generate enabled + `POST` 200 | covered |
| Step 4 — Both tokens appear in the table without error | Condition holds | Step 4 | row count 2 + total `rows_before+2` + both name cells + no toast | covered |
| Step 5 — Each token has a distinct masked value | Condition holds | Step 5 | mask shape + `masked_1 != masked_2` (+ full-token Axis-2 tie-in) | covered |
| Expected Final State — same as step 5 | — | Step 5 | same | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| Second create shows **no** name-validation error and keeps Generate enabled | The case's subject is that duplicates are *allowed*; a uniqueness regression would most likely land as client-side validation, which the `POST`-status assertion alone would never see (the request would never be sent). |
| `POST` status **200** on both creates | "Operation completes successfully" is the case's own expected result for steps 2-3; without the response a 409 that the UI swallowed could still leave the earlier row on screen and look like success. |
| Total row count == `rows_before + 2` | Non-vacuity: with duplicate names permitted, a leftover row of the same name would otherwise satisfy "count == 2" with only one new create. |
| Masked values match `^\.\.\..{4}$` | "Distinct" must not be satisfied by two differently-broken cells; this pins the documented mask format (`'...' + token.slice(-4)`). |
| Full dialog token strings differ, and each masked value == `'...' + token[-4:]` | Ties each rendered row to the token the system actually issued, and makes the (astronomically rare) 4-char-tail collision diagnosable instead of a false defect. Both values are produced by the system — no substitution. |
| No error toast / no console errors | The case says "without error"; the UI's only error channel here is the toast, and console is the standard side-channel axis. 0 observed live. |

## Known Defects
None. The product satisfied every step of this case exactly as written.

## Blocked Steps
None.
