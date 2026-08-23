# Test Case: Save and Cancel Active with Valid Values; Cancel Does Not Create the Bucket

## Metadata
- **TMS ID**: ELITEA-1815
- **Linked Story**: none
- **Priority**: l3 (source frontmatter `priority: medium` → `l3` per this folder's
  convention — siblings ELITEA-1809/1811/1812/1816/1817)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend; dev server confirmed `200` at run start)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot — cluster dispatch with ELITEA-1813, ONE live
  session, **both cases executed individually**
- **Status**: **ready-for-automation** — every step executed live 2026-08-23 via a
  `playwright.sync_api` scratch probe driving the project's own `ArtifactsPage` methods.
  Every expected result held **exactly as authored** — no defect, no clarification, no new
  testid, no new page-object method.
- **Family**: NO — see ELITEA-1813's spec § Why this is a separate spec (opposite
  expectations on Save and on the validation message; two extra retention steps here).

## Overlap check vs existing automation

Checked by behaviour before classifying:

- `test_artifacts_bucket_retention_edit_persistence.py:542-553` (ELITEA-1810, merged)
  cancels the **Edit bucket** form for an existing bucket and asserts no `PUT` fires. This
  case cancels the **create** form and asserts no `POST` fires **and** that the named
  bucket never appears. Different mode, different request, different final assertion —
  not coverage.
- `test_artifacts_bucket_name_validation_invalid_formats.py` (ELITEA-1811/1814, merged)
  touches the same form but never sets a retention policy, never asserts the Cancel path,
  and its Save assertion is about an invalid name.
- `test_artifacts_create_bucket_upload_file.py` (ELITEA-1808) is the positive create path
  (Save, not Cancel).
- Nothing merged asserts "valid values ⇒ Save enabled" or "Cancel on the create form
  creates nothing".

⇒ `ready-for-automation` (fresh spec).

## Preconditions

- User logged in (`auth_state`).
- **No bucket named `bucket-cancel-test` exists** in the target project. Verified live
  before the run (`artifacts-bucket-row-bucket-cancel-test` count `0`); the case never
  creates it, so the precondition self-sustains across runs. The spec asserts this
  absence at the start too — otherwise step 9 could pass against a bucket that already
  existed, or fail for a leftover the case did not create.

## Test Data

| Field | Value | Note |
|---|---|---|
| Bucket name | `bucket-cancel-test` | literal from the case; safe to hardcode **because nothing is ever created** — do NOT swap in a generated name, the case's point is that this exact name stays absent |
| Retention measure | `days` (renders `Days`) | option value is lowercase, label is capitalized by `capitalizeFirstChar` |
| Retention value | `3` | |
| Form defaults observed live | name `new-bucket`, measure `Years`, value `1` | baseline for asserting the changes took |

### reuse-existing
- None.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   **Verify**: `artifacts-buckets-heading` visible (`wait_for_page_load(timeout=60000)`).
   **Also verify** `artifacts-bucket-row-bucket-cancel-test` count `0` (precondition).
2. Click `artifacts-create-bucket-button` (case step 2).
   **Verify**: URL ends `/artifacts/create-bucket` **and**
   `get_bucket_form_heading_text() == "New Bucket"` (shared route with the edit form).
3. Enter the valid name (case step 3) via `fill_bucket_name("bucket-cancel-test")`.
   **Verify**: `bucket_name_input.input_value() == "bucket-cancel-test"`.
   *(The field is pre-filled `new-bucket`; `fill_bucket_name` already does the
   click + `select_text()` + `type()` dance that this MUI/formik field requires — a bare
   `fill()` or `Control+A` does not take.)*
4. Select retention measure `days` (case step 4) via `select_retention_measure("days")`.
   **Verify**: `bucket_retention_measure_combobox` text == `Days`
   (observed live: `Years` → `Days`).
5. Set the retention value to `3` (case step 5) via `set_retention_value("3")`.
   **Verify**: `bucket_retention_value_input.input_value() == "3"` (the field is
   pre-populated with `1`, so the select-all inside `set_retention_value` is what stops
   `1` + `3` → `13`).
6. Verify both buttons (case step 6):
   `expect(bucket_save_button).to_be_visible()` + `to_be_enabled()`,
   `expect(bucket_cancel_button).to_be_visible()` + `to_be_enabled()`.
   **Also verify** `artifacts-bucket-name-helper-text` count `0` — with valid values there
   is no validation message (the mirror of ELITEA-1813, and what makes "highlighted/active"
   mean *valid*, not merely *rendered*).
7. Arm a request capture on `artifacts/buckets` (any method), then click Cancel
   (case step 7).
   **Verify**: the form is gone — `artifacts-bucket-form-heading` count `0` — and the URL
   is the bare `${BASE_URL}/artifacts` (observed live; `onCancel` is a plain
   `navigate(-1)`).
   **Verify**: captured requests == `[]` (observed live: empty).
8. Click the sidebar's **Artifacts** item (case step 8) —
   `BasePage.SIDEBAR_MENU_ITEM.format("artifacts")` via `sidebar_menu_item("artifacts")`.
   **Verify**: URL is the Artifacts root and `wait_for_page_load()` passes.
   *(Cancel already lands on `/artifacts`, so this step is a re-navigation; keep it — it is
   the case's own step and it proves the root is reachable in the post-Cancel state.)*
9. Verify `bucket-cancel-test` is absent (case step 9). Assert all three:
   - `[data-testid="artifacts-bucket-row-bucket-cancel-test"]` count `0`,
   - via the bucket search box (`open_bucket_search()` → `search_buckets(NAME)` →
     `get_visible_bucket_count() == 0`; the panel filters client-side with a 300 ms
     debounce), then `close_bucket_search()`,
   - the step-7 capture stayed `[]` (no POST ever fired).

## Expected Results

- With a valid name and a valid retention policy, **both** Save and Cancel are visible and
  enabled, and no validation helper text is rendered.
- Cancel closes the form, fires **no** request at all, and returns to the bucket list.
- `bucket-cancel-test` never appears in the bucket list — neither by direct row lookup nor
  through the search filter.

## Coverage Map

### Axis 1 — Case element → Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | setup | covered (setup) |
| Test-data "Bucket name = bucket-cancel-test" | — | Test Step 3 | exact literal typed and asserted | covered |
| Test-data "Retention policy = days" | — | Test Step 4 | combobox text == `Days` | covered |
| Test-data "Retention value = 3" | — | Test Step 5 | `input_value() == "3"` | covered |
| Step 1 Navigate to Artifacts | page loads | Test Step 1 | `artifacts-buckets-heading` visible | covered |
| Step 2 Click folder/create icon | New Bucket form opens | Test Step 2 | URL + heading text `New Bucket` | covered |
| Step 3 Enter valid name | field accepts it | Test Step 3 | `input_value()` | covered |
| Step 4 Select "days" | `days` selected | Test Step 4 | combobox text | covered |
| Step 5 Set value "3" | field shows `3` | Test Step 5 | `input_value()` | covered |
| Step 6 Save + Cancel visible/active/clickable | both active | Test Step 6 | `to_be_visible()` + `to_be_enabled()` on both | covered |
| Step 7 Click Cancel | form closes | Test Step 7 | heading count 0 + URL `/artifacts` | covered |
| Step 8 Click "Artifacts" | navigation to Artifacts root | Test Step 8 | sidebar item click → root URL + page load | covered |
| Step 9 `bucket-cancel-test` NOT in the list | absent | Test Step 9 | row count 0 + search-filtered count 0 | covered |
| Expected final state "no bucket created, no side effects" | — | Test Steps 7 + 9 | zero captured requests + two-way absence | covered |
| Fail criterion "any step produces an error" | — | Axis 2 | console-error assertion | covered |

### Axis 2 — Observables asserted beyond the case

| Observable | Why |
|---|---|
| `bucket-cancel-test` absent **before** the form is opened (Step 1) | step 9's absence assertion is meaningless if the name could already have been taken by a leftover; this makes the final assertion a real delta |
| Absence of any `artifacts/buckets` request across Cancel (Step 7) | "no bucket in the list" cannot distinguish *not created* from *created but not rendered* on a ~968-row client-filtered list. The network is the honest oracle, and it localises a Cancel regression to step 7 rather than to step 9 |
| No validation helper text with valid values (Step 6) | the case says the Save button is "highlighted/active" — the absence of an error is the other half of "the form is in a valid state", and it is the exact mirror of ELITEA-1813's assertion |
| Search-filter absence in addition to the direct row lookup (Step 9) | the direct `artifacts-bucket-row-{name}` lookup is a negative assertion on a huge list; the search filter narrows the list to whatever matches, so `0 visible rows` proves absence independently of rendering/scroll behaviour |
| Form defaults changed (`Years`→`Days`, `1`→`3`) rather than merely read | proves steps 4–5 actually mutated the form; a test that never changed the defaults would still satisfy a naive "value is present" read |
| No unexpected console errors | project convention. Observed live: only the pre-existing Vite `Module "stream" has been externalized` **warning** (flow-unrelated, every artifacts case reports it) — zero errors |

## Concrete Handles

All testid-only; **zero new testids required**. Provenance verified 2026-08-23 after
`cd ../EliteaUI && git fetch origin`, two-stage grep per `.agents/workflow.md`.

| Element | Testid | Page-object member | PROVENANCE |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | `wait_for_page_load()` | on-main ✓ |
| Create-bucket (folder) icon | `artifacts-create-bucket-button` | `click_create_bucket_button()` | on-main ✓ |
| Bucket form heading | `artifacts-bucket-form-heading` | `get_bucket_form_heading_text()` | on-`automation/testids` only (awaiting human cherry-pick to main) |
| Name input | `artifacts-bucket-name-input` | `fill_bucket_name()` / `bucket_name_input` | on-main ✓ |
| Retention measure combobox | `artifacts-bucket-retention-measure-select-combobox` | `bucket_retention_measure_combobox` | on-main ✓ (suffix auto-derived by `SingleSelect.jsx` from `artifacts-bucket-retention-measure-select`) |
| Retention option `Days` | `select-option-days` | `BasePage.SELECT_OPTION` via `select_retention_measure("days")` | on-main ✓ (`SingleSelect.jsx:416`, runtime-composed) |
| Retention value input | `artifacts-bucket-retention-value-input` | `set_retention_value()` / `bucket_retention_value_input` | on-main ✓ |
| Save button | `artifacts-bucket-save-button` | `bucket_save_button` | on-main ✓ |
| Cancel button | `artifacts-bucket-cancel-button` | `click_bucket_cancel_button()` | on-`automation/testids` only (awaiting human cherry-pick to main) |
| Name helper text (absence assertion) | `artifacts-bucket-name-helper-text` | `bucket_name_helper_text` | on-main ✓ |
| Bucket row (dynamic) | `artifacts-bucket-row-{name}` | `ArtifactsPage.BUCKET_ROW` constant | on-main ✓ |
| Bucket search input / clear | `artifacts-bucket-search-input` / `artifacts-bucket-search-clear-button` | `open_bucket_search()` / `search_buckets()` / `close_bucket_search()` | on-main ✓ |
| Sidebar → Artifacts | `sidebar-menu-item-artifacts` | `BasePage.SIDEBAR_MENU_ITEM` / `sidebar_menu_item("artifacts")` | on-`automation/testids` only (runtime-composed in `SidebarBody.jsx:272`; awaiting human cherry-pick to main) |

**Dynamic-testid discipline**: the bucket row, the select option and the sidebar item are
all addressed through existing UPPER_CASE class constants — never an inline
`get_by_test_id(f"…")` (`.agents/testing.md` § Locator policy).

## Automation Hints

- **File**: new spec
  `automation/tests/ui/artifacts/test_artifacts_bucket_cancel_with_valid_values.py`.
- **Markers**: module-level `pytestmark = [pytest.mark.ui, pytest.mark.regression,
  pytest.mark.new]` + `@pytest.mark.p3` on the test — the shape every sibling
  `tests/ui/artifacts/*.py` spec uses. **There is no `artifacts` marker** in
  `automation/pytest.ini`; don't add one (it would raise an unregistered-marker warning).
- **No new page-object method is needed.** Every interaction already exists:
  `click_create_bucket_button`, `get_bucket_form_heading_text`, `fill_bucket_name`,
  `select_retention_measure`, `set_retention_value`, `click_bucket_cancel_button`,
  `open_bucket_search` / `search_buckets` / `close_bucket_search`,
  `get_visible_bucket_count`, `capture_requests_matching`, `sidebar_menu_item`.
- **Never call `click_bucket_save_button()`** — this case must not create a bucket. The
  Save button is only ever *asserted on*, never clicked.
- `capture_requests_matching("artifacts/buckets")` must be `.stop()`-ed in a `finally`
  (the helper's own docstring warns that leaked listeners hang later tests).
- **Cold-session `networkidle`**: pass `timeout=60000` on the first
  `wait_for_page_load()` — project 399 renders ~968 bucket rows and the first navigation of
  a fresh session has exceeded the 15 s default before.
- The bucket-search filter debounces 300 ms (a product constant, documented in
  `artifacts_page.py`); use the auto-retrying `expect(...).to_have_count(0)` rather than a
  one-shot `get_visible_bucket_count()` read where possible.
- Steps wrapped in `with allure.step("Step N — …")`, one per case step.

## Cleanup

- **None required** — nothing is created (verified live: zero `artifacts/buckets` requests
  across the whole probe). Notably this case is one of the few artifacts cases that leaks
  **no** bucket into project 399's ~968-bucket pile (`#636`).

## Known Defects / Clarifications

- **None.** Every case step's expected result held exactly as authored — the only nuance
  worth carrying forward is documentational: the create and edit forms share the
  `/artifacts/create-bucket` route, so the form-heading text is the only observable that
  distinguishes them (already handled in Test Step 2).
