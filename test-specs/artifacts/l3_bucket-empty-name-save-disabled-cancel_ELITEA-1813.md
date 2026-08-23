# Test Case: Bucket Cannot Be Created with an Empty Name Field

## Metadata
- **TMS ID**: ELITEA-1813
- **Linked Story**: none
- **Priority**: l3 (source frontmatter `priority: medium` → `l3` per this folder's
  established convention — siblings ELITEA-1809/1811/1812/1816/1817 all map the same way)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend; dev server confirmed `200` at run start)
- **User set**: `${TEST_USER}` (on localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot — cluster dispatch with ELITEA-1815, ONE live
  session, **both cases executed individually**
- **Status**: **ready-for-automation** — every step executed live 2026-08-23 via a
  `playwright.sync_api` scratch probe driving the project's own `ArtifactsPage` methods
  (so the exercised code path is what the implementer will write). No blocking defect.
  **Zero new testids needed.** One case-text CLARIFICATION filed (#1680) — see
  § Known Defects / Clarifications; it changes *when* step 5's message is asserted, not
  *what* is asserted.
- **Family**: NO. Analysed in one session with ELITEA-1815, but the two differ in
  **steps**, not data — see § Why this is a separate spec from ELITEA-1815.

## Why this is a separate spec from ELITEA-1815

Both cases open the same New Bucket form and end on Cancel, but the middle differs in
STEPS, not in data (`test-case-analysis` § 3 family test):

| | ELITEA-1813 | ELITEA-1815 |
|---|---|---|
| Name field | **cleared** (empty) | filled with a valid name |
| Retention controls | never touched | measure + value both changed (2 extra steps) |
| Save button | asserted **disabled** | asserted **enabled** |
| Validation message | asserted present (`Name is required`) | asserted **absent** |

Opposite expectations on the same two controls is exactly the merge that would let one
case stop being tested silently. Separate specs; shared page object.

## Overlap check vs existing automation

Checked before classifying (grep by behaviour, not case id):

- `automation/tests/ui/artifacts/test_artifacts_bucket_name_validation_invalid_formats.py`
  (ELITEA-1811/1814, merged) — asserts the **format** error and, explicitly, that Save
  stays **ENABLED** for a non-empty invalid name (`:156` `assert
  artifacts_page.bucket_save_button.is_enabled()`). The empty-name branch is the opposite
  disabled-Save branch and the `Name is required` message; neither appears anywhere in
  that spec. Not covered.
- `test_artifacts_bucket_retention_edit_persistence.py:542-553` (ELITEA-1810, merged) —
  Cancel on the **Edit bucket** form (existing bucket, asserts no `PUT`). This case is
  Cancel on the **create** form with the form in an invalid state (asserts no `POST`,
  no bucket). Different mode, different observable. Not covered.
- No other spec references `artifacts-bucket-name-helper-text` or a disabled Save.

⇒ `ready-for-automation` (fresh spec), not `already-covered` / `extend-existing`.

## Preconditions

- User logged in (`auth_state`; localhost path needs no credentials).
- No bucket-state precondition — the case never creates anything.

## Test Data

| Field | Value | Source |
|---|---|---|
| Default name pre-filled by the form | `new-bucket` | `CreateBucket.jsx` `initialValues.name`, confirmed live |
| Expected validation message | `Name is required` | yup `.required('Name is required')`, confirmed live byte-exact |

### reuse-existing
- None. No fixture bucket is needed and none is created.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   **Verify**: `artifacts-buckets-heading` visible (`wait_for_page_load()`).
   **Also capture** the current rendered bucket-row count — it is the step-9 baseline.
2. Click `artifacts-create-bucket-button` (case step 2).
   **Verify**: `page.url` ends `/artifacts/create-bucket` **and**
   `get_bucket_form_heading_text() == "New Bucket"` (the route is shared with the edit
   form — URL alone does not discriminate). Observed live: name pre-filled `new-bucket`,
   Save **enabled** at this point (baseline that step 4's flip is caused by the clear).
3. Clear the Name field (case step 3): click it, `select_text()`, `press("Delete")`.
   **Verify**: `bucket_name_input.input_value() == ""`.
   *(`fill_bucket_name("")` does NOT work — the page object's `type("")` is a no-op that
   leaves the selection intact; the implementer needs the explicit `Delete` press, ideally
   as a new `clear_bucket_name()` page-object method.)*
4. **Without leaving the field**, verify `artifacts-bucket-save-button` is **disabled**
   (case step 4). Assert BOTH:
   - `expect(bucket_save_button).to_be_disabled()`, and
   - the click is genuinely refused — `bucket_save_button.click(timeout=2000)` raises
     Playwright `TimeoutError` (observed live: *"element is not enabled"*). This is the
     "not clickable" half of the case's own wording; a `disabled` attribute alone doesn't
     prove the click is refused.
5. Blur the Name field (`press("Tab")`), then verify the inline message (case step 5).
   **Verify**: `artifacts-bucket-name-helper-text` visible and `text_content().strip() ==
   "Name is required"`; `bucket_name_input` `aria-invalid == "true"`.
   ⚠ **The blur is mandatory and is NOT in the case text** — see #1680. Before the blur the
   helper element does not exist (`count() == 0`, `aria-invalid == "false"`).
   Also assert the *pre-blur* state explicitly (Axis 2) so the gating is pinned, not
   silently worked around.
6. Verify `artifacts-bucket-cancel-button` is visible and enabled (case step 6).
7. Arm a request capture on `artifacts/buckets` (any method), then click Cancel
   (case step 7).
8. **Verify** (case step 8): the form is gone — `artifacts-bucket-form-heading` count `0`
   and `artifacts-bucket-name-input` count `0` — and `page.url` is the bare
   `${BASE_URL}/artifacts` (observed live; no `?bucket=` param).
9. **Verify** (case step 9): the bucket list is displayed again
   (`artifacts-buckets-heading` visible, bucket rows rendered) and **no bucket was
   created** — assert all three:
   - captured `artifacts/buckets` requests == `[]` (observed live: empty),
   - `[data-testid="artifacts-bucket-row-new-bucket"]` count `0` (the default name is the
     only name that could plausibly have been submitted),
   - rendered bucket-row count equals the step-1 baseline
     (`expect(any_bucket_row).to_have_count(baseline)` — auto-retrying, never a bare
     `len()` read on a ~970-row list).

## Expected Results

- Empty Name ⇒ Save is disabled and un-clickable, immediately, with no blur required.
- After the field is blurred, the inline helper text reads exactly `Name is required` and
  the input is `aria-invalid="true"`.
- Cancel is always enabled; clicking it closes the form, fires **no** bucket request, and
  returns to the bucket list with the list unchanged.

## Coverage Map

### Axis 1 — Case element → Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | setup | covered (setup) |
| Test-data "Default name = new-bucket" | — | Test Step 2 | `input_value() == "new-bucket"` | covered |
| Test-data "Validation message = Name is required" | — | Test Step 5 | exact-string assert | covered |
| Step 1 Navigate to Artifacts | page loads | Test Step 1 | `artifacts-buckets-heading` visible | covered |
| Step 2 Click folder/create icon | New Bucket form opens | Test Step 2 | URL + heading text `New Bucket` | covered |
| Step 3 Delete default name | field cleared/empty | Test Step 3 | `input_value() == ""` | covered |
| Step 4 Save disabled / not clickable | Save appears disabled | Test Step 4 | `to_be_disabled()` + click refused (`TimeoutError`) | covered |
| Step 5 Inline "Name is required" visible | message visible | Test Step 5 | helper-text exact string + `aria-invalid` | covered — **with a blur added** (case-text gap, CLARIFICATION #1680) |
| Step 6 Cancel active and clickable | Cancel enabled | Test Step 6 | `to_be_visible()` + `to_be_enabled()` | covered |
| Step 7 Click Cancel | form closes | Test Steps 7–8 | click + form-heading count 0 | covered |
| Step 8 Creation page closed | form no longer visible | Test Step 8 | heading count 0 + name-input count 0 + URL `/artifacts` | covered |
| Step 9 Bucket list shown, no new bucket | no new bucket appears | Test Step 9 | no `artifacts/buckets` request + no `new-bucket` row + row count == baseline | covered |
| Expected final state "No bucket is created" | — | Test Step 9 | three-way assertion above | covered |
| Fail criterion "any step produces an error" | — | Axis 2 | console-error assertion | covered |

### Axis 2 — Observables asserted beyond the case

| Observable | Why |
|---|---|
| Save is **enabled** before the clear (Step 2) | without the baseline, a permanently-disabled Save (e.g. a future regression disabling it outright) would pass step 4 for the wrong reason |
| Helper text **absent** + `aria-invalid="false"` before the blur (Step 5) | pins the product's real `touched`-gating contract instead of quietly papering over it with a blur; if the product ever starts validating on change, this assertion fails loudly and the AFS/case get revisited (it is the assertion #1680 is about) |
| Click on the disabled Save is **refused** | `disabled` in the DOM and "not clickable" are different claims; the case says both |
| Absence of any `artifacts/buckets` request across Cancel | the DOM alone cannot distinguish "no bucket created" from "created but not yet rendered" on a 968-row list; the network is the honest oracle and it localises a Cancel regression to step 7 |
| Bucket-row count unchanged vs. baseline | catches a creation under any *other* name (e.g. a whitespace/default fallback) that a single `new-bucket` row check would miss |
| No unexpected console errors | project convention. Observed live: only the pre-existing, flow-unrelated Vite `Module "stream" has been externalized` **warning** every artifacts case reports — zero errors |

## Concrete Handles

All testid-only; **zero new testids required**. Provenance verified 2026-08-23 with
`cd ../EliteaUI && git fetch origin` + the two-stage grep from `.agents/workflow.md`
(output pasted in § Automation Hints).

| Element | Testid | Page-object member | PROVENANCE |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | `wait_for_page_load()` | on-main ✓ |
| Create-bucket (folder) icon | `artifacts-create-bucket-button` | `click_create_bucket_button()` | on-main ✓ |
| Bucket form heading | `artifacts-bucket-form-heading` | `get_bucket_form_heading_text()` | on-`automation/testids` only (awaiting human cherry-pick to main) |
| Name input | `artifacts-bucket-name-input` | `bucket_name_input` | on-main ✓ |
| Name helper text | `artifacts-bucket-name-helper-text` | `bucket_name_helper_text` | on-main ✓ (`CreateBucket.jsx:244`, `FormHelperTextProps`) |
| Save button | `artifacts-bucket-save-button` | `bucket_save_button` | on-main ✓ |
| Cancel button | `artifacts-bucket-cancel-button` | `bucket_cancel_button` / `click_bucket_cancel_button()` | on-`automation/testids` only (awaiting human cherry-pick to main) |
| Bucket row (dynamic) | `artifacts-bucket-row-{name}` | `ArtifactsPage.BUCKET_ROW` constant / `bucket_row(name)` | on-main ✓ |
| Any bucket row (prefix) | `artifacts-bucket-row-` | `ArtifactsPage.BUCKET_ROW_ANY_SELECTOR` / `any_bucket_row` | on-main ✓ |

**Dynamic-testid discipline**: rows are addressed through the existing UPPER_CASE class
constants — never an inline `get_by_test_id(f"…")` (`.agents/testing.md` § Locator policy).

## Automation Hints

- **File**: new spec
  `automation/tests/ui/artifacts/test_artifacts_bucket_empty_name_validation.py`.
  ELITEA-1815's spec is a separate file (see § Why this is a separate spec).
- **Markers**: module-level `pytestmark = [pytest.mark.ui, pytest.mark.regression,
  pytest.mark.new]` + `@pytest.mark.p3` on the test — the shape every sibling
  `tests/ui/artifacts/*.py` spec uses. **There is no `artifacts` marker** in
  `automation/pytest.ini`; don't add one (it would raise an unregistered-marker warning).
- **New page-object work — one small method**: `clear_bucket_name()` on `ArtifactsPage`
  (click → `select_text()` → `press("Delete")`). `fill_bucket_name("")` cannot be reused:
  `Locator.type("")` is a silent no-op that leaves the text selected but present.
  Everything else already exists (`click_create_bucket_button`,
  `get_bucket_form_heading_text`, `click_bucket_cancel_button`,
  `capture_requests_matching`, `any_bucket_row`, `get_visible_bucket_count`).
- **Do NOT call `click_bucket_save_button()`** anywhere in this spec — it wraps
  `expect_response` on a POST that can never fire here. The disabled-click probe must be a
  raw `bucket_save_button.click(timeout=…)` inside `pytest.raises(PlaywrightTimeoutError)`.
- **Cold-session `networkidle`**: the first `/artifacts` navigation of a fresh session has
  exceeded `wait_for_page_load()`'s default 15 s in this project (project 399 renders ~968
  bucket rows). Pass `timeout=60000` on that first call — used live, comfortable.
- **Never `sleep`** — the pre-blur assertions are `expect(...).to_have_count(0)` /
  `to_be_disabled()`, all auto-retrying.
- Steps wrapped in `with allure.step("Step N — …")`, one per case step (project convention).
- **Provenance grep output** (2026-08-23, after `git fetch origin`):
  ```
  artifacts-buckets-heading                     main:YES  testids:YES
  artifacts-create-bucket-button                main:YES  testids:YES
  artifacts-bucket-name-input                   main:YES  testids:YES
  artifacts-bucket-save-button                  main:YES  testids:YES
  artifacts-bucket-cancel-button                main:no   testids:YES
  artifacts-bucket-form-heading                 main:no   testids:YES
  artifacts-bucket-name-helper-text             main:YES  testids:YES
  artifacts-bucket-row-                         main:YES  testids:YES
  ```

## Cleanup

- **None required** — the case creates nothing, and this analysis run leaked no bucket
  (verified: zero `artifacts/buckets` requests fired across the whole probe).

## Known Defects / Clarifications

- **CLARIFICATION #1680 (filed 2026-08-23, label `question`)** — case step 5 asserts the
  `Name is required` message immediately after step 3's clear, but the message renders only
  once the Name field is **blurred**: `CreateBucket.jsx:243-244` gates both `error` and
  `helperText` on `formik.touched.name`, which Formik sets on blur or submit — and the
  submit path is unreachable here because Save is `disabled` while the name is empty.
  **Not a product defect** (reverse-masking guard: the live behaviour is correct standard
  MUI/Formik, the case text is what's incomplete). The spec adds an explicit blur step and
  asserts the pre-blur state too.
- No product defect found. Every other case step's expected result held exactly as authored.
