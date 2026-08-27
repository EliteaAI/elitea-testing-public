# Test Case: Token can be created without an expiration date

## Metadata
- **TMS ID**: ELITEA-2283
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2283.md` (intake snapshot)
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

The merged suite reads the `never` expiration state only off **pre-existing live data**
(and only incidentally — no merged test asserts it at all today; the surface digest
records `never` and `warning` as the two unexercised branches). Nothing anywhere creates
a token *with* the `Never` unit, and nothing asserts that the create form's numeric value
input disappears when `Never` is chosen. ELITEA-2280's merged test asserts the
**defaults** (`Days`/`30`) are unchanged, which is the opposite of this case.

## Preconditions
- Logged-in user; `/settings/tokens` reachable.
- No specific existing data required (the case creates its own token).

## Test Data
### create-and-destroy
- One token named `autotest-token-{uuid4().hex[:8]}`, expiration unit **`Never`**.
- **Mandatory cleanup** (`finally:`): delete the created token. A `Never` token never
  expires, so a leaked one pollutes shared live data permanently — this cleanup matters
  more here than in any sibling case.
- Do **not** reuse or touch the 5 persistent tokens (`for_ui_tests`, `Levon`, `Marian`,
  `New`, `uautomate`); three are `never` tokens that other analyses rely on as stable
  read-only data, and two are irrecoverably `Expired` fixtures for ELITEA-2284.

## The product's actual no-expiration contract (source + live confirmed)

- The unit dropdown's `Never` option comes from `EXPIRATION_MEASURES`
  (`src/common/constants.js:492`), testid `select-option-never` (runtime-composed by the
  shared `SingleSelectMenuItem.jsx:117`).
- **Selecting `Never` UNMOUNTS the numeric value input.** Confirmed live:
  `create-personal-token-expiration-value-input` had count **0** after choosing `Never`
  (it is not merely hidden or disabled). This is the form's own expression of "no
  expiration date", and it is the strongest available proof that the case's step 2 took
  effect *before* Generate is clicked.
- Generate → `POST /api/v2/auth/token/` → **200** with **`expires: null`**.
- `calculateExpiryInDays(null)` returns **-1** (`src/common/utils.jsx:703-705`) →
  `ExpiryInDays.jsx` renders the `data-expiration-state="never"` branch: green
  `SuccessIcon` (`theme.palette.status.published`, `#2BD48D`) + the literal label
  **`Never`**.

### Live observations (2026-08-27, real interactions)

| Step | Observed |
|---|---|
| Typed name, opened unit dropdown, clicked `Never` | combobox text → `Never` |
| Numeric value input | **count 0** — unmounted |
| Generate | `POST /auth/token/` → **200**, body `expires: null` |
| Success dialog | `generated-token-dialog-token-name` == the entered name |
| Closed dialog → `/settings/tokens` | row `afs2283-never` present, value `...IHMQ`, expiration label **`Never`**, state **`never`**, icon fill `#2BD48D` (green) |
| Table total | 7 rows (5 persistent + 2 created in this session) |

Console across the whole session: **0 errors**.

## Test Steps

1. **Step 1 — Navigate to Settings → Personal Tokens and click "+".**
   `PersonalTokensPage.navigate()` → `click_add_button()` (waits for
   `**/settings/create-personal-token`).
   - **Verify**: `create-personal-token-page-title` text == `New Token`.
   - **Capture** `rows_before = token_row.count()` on the list page *before* clicking "+"
     (needed by step 4's non-vacuity check).

2. **Step 2 — Enter a token name and select "Never".**
   - `fill_name(token_name)` — **verify** `name_input.input_value() == token_name` (the
     case's "field accepts the input and displays the entered value").
   - Open the unit dropdown and click `select-option-never`.
   - **Verify**: the combobox text == `Never`.
   - **Verify (Axis 2)**: `expect(expiration_value_input).to_have_count(0)` — the numeric
     value input **unmounts**. This is the case's real subject ("without an expiration
     date") made observable at the form level, before any network call.
   - **Verify**: `generate_button` is enabled (a valid name + `Never` is a complete form).

3. **Step 3 — Click "Generate" and close the success dialog.**
   - `click_generate()` → **verify** `response.status == 200`.
   - **Verify (Axis 2)**: the response body's `expires` is **`None`** — the backend's own
     statement that no expiration was set, independent of any rendering.
   - **Verify**: `generated-token-dialog-title` text == `New token generated!` and
     `generated-token-dialog-token-name` text == `token_name`.
   - `close_dialog()` (waits for `**/settings/tokens`).

4. **Step 4 — Verify the token appears in the table.**
   - **Verify**: `expect(get_row_by_name(token_name)).to_have_count(1)` with
     `ROW_WAIT_TIMEOUT` — the table refetches after a create and is briefly **unmounted**
     (`TokensTable.jsx:150` renders a spinner while `isFetchingTokens`), so a bare
     `count()` read immediately after landing returns 0. Use the auto-retrying `expect`.
   - **Verify**: that row's `token-name-cell` text == `token_name`.
   - **Verify (Axis 2)**: `expect(token_row).to_have_count(rows_before + 1)` — the row was
     *added*, not merely matched.

5. **Step 5 — Verify the Expiration column shows "Never" (not a blank cell or error).**
   - **Verify**: `get_row_expiration_status(row, state="never")` has count **1**
     (`[data-testid="token-expiration-status"][data-expiration-state="never"]`).
   - **Verify**: that element's text == exactly `Never` — the case explicitly rules out a
     blank cell, so assert the literal string, never a truthiness check.
   - **Verify (absence)**: the row has **no** `expired` state element
     (`get_row_expiration_status(row, state="expired")` count **0**) — "not an error
     state" is half the case's own expected result, and only an absence assertion states
     it. (Absence assertions are first-class references per `.agents/testing.md`
     § Locator policy, ruling #511.)
   - Do **not** assert the SVG fill hex; `data-expiration-state` is the stable handle.

6. **Axis 2 — No console errors** across the flow (0 observed live).

7. **Cleanup (`finally:`, unwrapped)** — delete the created token (row trash icon →
   `fill_delete_confirm_name(token_name)` → `confirm_delete()` → wait for count 0).

## Handles Reference

| Element | Handle (testid) | Page-object member | PROVENANCE |
|---|---|---|---|
| Add (+) button | `personal-tokens-add-button` | `PersonalTokensPage.click_add_button()` | on-main ✓ |
| Create page title | `create-personal-token-page-title` | `CreatePersonalTokenPage.page_title` | on-main ✓ |
| Name input | `create-personal-token-name-input` | `name_input` / `fill_name()` | on-main ✓ |
| Unit dropdown (clickable) | `create-personal-token-expiration-measure-select-combobox` | `expiration_measure_combobox` | on-main ✓ |
| `Never` option (dynamic) | `select-option-never` | `EXPIRATION_MEASURE_OPTION_SELECTOR.format("never")` — the class-level template specced in the ELITEA-2282 AFS | on-main ✓ (runtime-composed, shared `SingleSelectMenuItem.jsx:117`, identical on both refs) |
| Numeric value input (asserted ABSENT) | `create-personal-token-expiration-value-input` | `expiration_value_input` | on-main ✓ |
| Generate button | `create-personal-token-generate-button` | `generate_button` / `click_generate()` | on-main ✓ |
| Success dialog title | `generated-token-dialog-title` | `dialog_title` | on-main ✓ |
| Success dialog name | `generated-token-dialog-token-name` | `dialog_token_name` | on-main ✓ |
| Dialog close (X) | `generated-token-dialog-close-button` | `dialog_close_button` / `close_dialog()` | on-main ✓ |
| Token row | `token-row` | `token_row` / `get_row_by_name()` | on-main ✓ |
| Row name cell | `token-name-cell` | `get_row_name_cell()` | on-main ✓ |
| Expiration status (state-filtered) | `[data-testid="token-expiration-status"][data-expiration-state="{}"]` | `TOKEN_EXPIRATION_STATUS_SELECTOR` / `get_row_expiration_status()` | on-main ✓ |
| Row delete icon | `token-action-delete-button` | `get_row_action_icon()` | on-main ✓ |

Provenance verified 2026-08-27 after `cd ../EliteaUI && git fetch origin`, two-stage
`git grep` against `origin/main` **and** `origin/automation/testids` — all `YES`/`YES`.

**Shared page-object work with ELITEA-2282:** both cases need
`EXPIRATION_MEASURE_OPTION_SELECTOR` + `select_expiration_measure(measure)` on
`CreatePersonalTokenPage`. Whichever case is implemented first adds them; the second
reuses them. (Specced in full in the ELITEA-2282 AFS § Handles Reference.)

## Automation Hints

- Target file: **`automation/tests/ui/admin/test_personal_token_create_and_verify.py`**
  as a new test method, or a dedicated module shared with ELITEA-2282's expiration
  scenario. Implementer's call.
- Markers: `ui`, `admin`, `p2`, `regression`.
- Every step wrapped in `with allure.step("Step N — …"):`; cleanup unwrapped in `finally:`.
- Never `sleep`: `expect(...)` polling and `expect_response` cover every wait, including
  the post-create refetch window.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | covered |
| Step 1 — Navigate + click "+" | Page loads | Step 1 | URL wait + `New Token` title | covered |
| Step 2 — Enter a token name and select "Never" | Field accepts input and displays it | Step 2 | name `input_value()`, combobox text `Never` (+ value input unmounts, Generate enabled) | covered |
| Step 3 — Click Generate, close the success dialog | Control responds | Step 3 | `POST` 200 + `expires: null` + dialog title/name + navigation back | covered |
| Step 4 — Verify the token appears in the table | Condition holds | Step 4 | row count 1 + name-cell text (+ total row count +1) | covered |
| Step 5 — Expiration column shows "Never", not blank/error | Condition holds | Step 5 | `never` state count 1, text == `Never`, `expired` state absent | covered |
| Expected Final State — same as step 5 | — | Step 5 | same | covered |

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| Numeric value input **unmounts** on `Never` | The case's subject is "without an expiration date"; this is the form's own expression of that state, observable before any network call, and it would catch a regression where `Never` is selectable but the form still submits a period. |
| `POST` response `expires` is `null` | Independent ground truth from the system that no expiry was stored — a DOM label alone cannot distinguish "no expiry" from "a label bug". Produced by the product, no substitution. |
| Total row count == `rows_before + 1` | Non-vacuity: proves a row was added rather than matching a leftover with a colliding name (duplicate names ARE allowed here — see ELITEA-2288). |
| `expired` state absent on the row | The case explicitly requires "not ... an error"; only an absence assertion states that, and absence assertions are first-class references (#511). |
| No console errors | Standard side-channel axis; 0 observed live. |

## Known Defects
None. The product satisfied every step of this case exactly as written.

## Blocked Steps
None.
