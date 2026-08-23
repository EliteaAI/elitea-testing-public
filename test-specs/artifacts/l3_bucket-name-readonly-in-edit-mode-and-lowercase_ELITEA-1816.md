# Test Case: Bucket Name Is Read-Only in Edit Mode and Displayed in Lowercase After Creation

## Metadata
- **TMS ID**: ELITEA-1816
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend), project `Private` / project_id `399`
- **User set**: `${TEST_USER}` (on localhost, `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot · **Date**: 2026-08-23
- **Status**: **ready-for-automation** — all 17 case steps executed live end-to-end, every
  expected result held. No product defect, no blocked step, **zero new testids needed**
  (provenance verified against a freshly fetched `origin/main` / `origin/automation/testids`).
  Two case-text clarifications, both non-blocking — see § Known Defects / Clarifications.
- **Cluster**: analysed in one live session with ELITEA-1812. **Separate AFS by design** —
  see § Overlap check.

## Overlap check vs existing automation

Not `already-covered`, not `extend-existing`. Checked by behaviour before executing.

**The nearest neighbour is ELITEA-1810** —
`automation/tests/ui/artifacts/test_artifacts_bucket_retention_edit_persistence.py`,
merged onto this batch's trunk `tests/batch-artifacts-w04` (`894d64060`). It genuinely
overlaps case steps 8–11, 13, 16–17: it opens the bucket dot-menu, asserts its four item
labels, clicks Rename, asserts the `Edit bucket` heading, reads the retention pair back,
edits retention, clicks Cancel and proves no `PUT` fired.

**It is still not an `extend-existing` target, for two independent reasons:**

1. **The two assertions this case exists for are absent there** — (a) a **mixed-case**
   name being stored/displayed lowercase, and (b) the Name field being **non-editable in
   Edit mode**. ELITEA-1810 creates its bucket with an already-lowercase generated name
   and never touches the Name field after creation. `grep -rn "is_disabled\|is_editable"
   automation/tests/ui/artifacts/` → no hit on the bucket name field anywhere in the suite.
2. **ELITEA-1810's spec is deliberately sanctioned-RED** — it carries two `expect.soft()`
   assertions tied to open defect #1677 (a `Months` retention policy reopens as `Days`),
   so its pytest outcome is FAILED by design until the product is fixed
   (`.agents/testing.md` § Merge gate). Appending ELITEA-1816's assertions to it would make
   this case permanently `blocked-on-#1677` despite having nothing to do with that defect.
   A case must not inherit an unrelated red.

Everything ELITEA-1810 built that *is* reusable — `open_bucket_menu`,
`get_bucket_menu_items_text`, `click_bucket_menu_rename_item`,
`get_bucket_form_heading_text`, `get_retention_measure_text`, `get_retention_value`,
`set_retention_value`, `select_retention_measure`, `click_bucket_cancel_button` — is
**page-object** work and is reused as-is by this case's own spec. Verdict:
`ready-for-automation`.

**Why not folded into ELITEA-1812's spec**: the two cases differ in **steps** (11 extra
steps here), not only in data — `test-case-analysis` § Cluster dispatches keeps those
separate.

## Preconditions
- User logged in (localhost: `auth_state` fixture skips login).
- A project is selected (`Private`, id 399 in this run).
- **No pre-seeded bucket** — creating it with a mixed-case name **is** case steps 2–6, and
  the created name is the subject of steps 7 and 12. Seeding via the `artifact_bucket` API
  fixture would substitute the producer under observation.

## Test Data

### generate-per-test
- **Bucket name (typed)**: the case's literal `BuCkEt-Mix` is a case-text placeholder;
  generate a unique **mixed-case** name of the same shape: `f"AuToTest-1816-{ts}"`
  (e.g. `AuToTest-1816-182606`). Must satisfy the form's yup schema
  (`^[a-zA-Z][a-zA-Z0-9-]*$`, ≤ 56 chars).
- **Expected stored name**: `typed_name.lower()` — derived, never hardcoded.
- **Retention (from the case, used verbatim live)**: `Days` / `1`.
- **Retention edit probe (step 16)**: `Weeks` / `3` — any change proves editability; it is
  discarded by the Cancel at step 17. Deliberately **not** `Months` (defect #1677 makes a
  Months policy round-trip as Days — irrelevant noise for this case).

## Test Steps

Every step below was executed live in this order (probe: `/tmp/probe_1816.py`,
2026-08-23 18:26 local); "observed" values are what the running system produced.

1. **(case 1)** Navigate to `${BASE_URL}/artifacts`; wait for `artifacts-buckets-heading`.
   - Observed: page loads. *(Cold-session `networkidle` note — see § Automation Hints.)*
2. **(case 2)** Click `artifacts-create-bucket-button` (the folder/create icon above the
   bucket list).
   - Verify: `page.url` ends with `/artifacts/create-bucket` (full page nav, not a modal).
   - Verify: `artifacts-bucket-form-heading` reads **`New Bucket`**.
     **Amended during ELITEA-1816 implementation (2026-08-23, review round 1):** Step 11
     below asserts `Edit bucket` on that SAME URL, so a URL-only assertion cannot prove
     the case's "'New Bucket' form opens" — the heading is the discriminator.
3. **(case 3)** Enter the mixed-case name via `ArtifactsPage.fill_bucket_name(name)`
   (click + `select_text()` + `type()`; `fill()`/`Control+A` do not work on this field).
   - Verify: `input_value() == "AuToTest-1816-182606"` — mixed case preserved verbatim in
     the input, **and** the field is **enabled** here (`is_disabled() is False`). Observed
     exactly that. *(This enabled-in-create reading is the control for step 14/15.)*
4. **(case 4)** Open `artifacts-bucket-retention-measure-select-combobox`
   (`open_retention_measure_dropdown()`), click `select-option-days`
   (`BasePage.SELECT_OPTION.format("days")` — the existing class constant).
   - Verify: combobox text == `Days`. Observed: `Days`.
5. **(case 5)** Set `artifacts-bucket-retention-value-input` to `1` via
   `set_retention_value("1")` (select-all + type; the field pre-holds `1`, and a bare type
   would produce `11`).
   - Verify: `input_value() == "1"`. Observed: `1`.
6. **(case 6)** Click `artifacts-bucket-save-button` inside
   `page.expect_response(POST …/artifacts/buckets/default/{project_id})`
   (`click_bucket_save_button()` already wraps this).
   - Verify: status `200`, and the response JSON's `name` == `typed_name.lower()`.
   - Observed: `200`,
     `{"message": "Created", "id": "p--399.autotest-1816-182606", "name": "autotest-1816-182606"}`
     — the **backend** performs the lowercasing (no `toLowerCase()` exists in
     `src/pages/Artifacts/CreateBucket.jsx`; the form posts `values.name.trim()` verbatim).
7. **(case 7)** Verify the bucket is listed in lowercase:
   - `artifacts-bucket-row-{lower}` present (**observed: present**);
   - `artifacts-bucket-row-{TYPED_MIXED_CASE}` count 0 (**observed: absent**);
   - row `text_content()` == the lowercase name exactly (observed
     `"autotest-1816-182606"`), and equals its own `.lower()`.
8. **(case 8)** **Hover** `artifacts-bucket-row-{lower}` first, then click
   `bucket-menu-{lower}-menu-button` (`open_bucket_menu(lower)` does both — the dot-menu
   trigger is hidden until row hover; a bare click times out "element is not visible").
   - Verify: `bucket-menu-{lower}-menu` visible.
9. **(case 9)** Verify the dropdown's items.
   - **Observed live: `Upload files` · `Rename` · `Pin to top` · `Delete`** — four items.
     The case text says the third is "Edit"; the live label is **"Rename"**, and the order
     differs from the case's listing. Already-tracked clarification (#666) — assert the
     **live** labels, in the live order: asserting the stale case text would be
     reverse-masking. See § Known Defects / Clarifications.
   - Assert via `get_bucket_menu_items_text(lower)`, which returns the container's
     concatenated text `"Upload filesRenamePin to topDelete"` (no separators — the items
     are sibling Typographies).
10. **(case 10)** Click `bucket-menu-rename-menuitem` (`click_bucket_menu_rename_item()`).
11. **(case 11)** Verify the Edit form opened.
    - Verify: `page.url` ends with `/artifacts/create-bucket` **and**
      `artifacts-bucket-form-heading`'s text == `Edit bucket` (the same route renders
      `New Bucket` vs `Edit bucket` off `currentBucket`, so the URL alone is not
      sufficient). Observed: `Edit bucket`.
12. **(case 12)** Verify the Name field displays the **lowercase** name.
    - Verify: `artifacts-bucket-name-input`'s `input_value() == typed_name.lower()`.
      Observed: `autotest-1816-182606`.
13. **(case 13)** Verify retention shows `Days` / `1`.
    - Verify: `get_retention_measure_text() == "Days"` and `get_retention_value() == "1"`.
      Observed: `Days` / `1` — **hard assertions, they pass**. (Unaffected by #1677: that
      defect only mangles `Months`, whose day-count is not divisible by 30.)
14. **(case 14)** Attempt to click into the Name field and modify it.
    - Verify: a `click()` on `artifacts-bucket-name-input` **times out** — Playwright's
      actionability check refuses a disabled element ("element is not enabled"). Observed:
      `TimeoutError` at 3 s. Automate as an explicit expected-timeout with a **short**
      timeout (2–3 s), inside a `pytest.raises(PlaywrightTimeoutError)`, so the assertion
      is "the click is refused", not "the test hung".
    - Then send keystrokes anyway (`type("XYZ")` + `press("Backspace")`) — the honest
      version of "try to type or delete characters".
15. **(case 15)** Verify the Name field is read-only and unchanged.
    - *Implementation note (2026-08-23): step 14's `Locator.type()`/`press()` attempts are
      each wrapped in a try/except on `TimeoutError` with the same short 3 s budget — live
      they do not raise, but the assertion that proves "no input is accepted" is this
      step's unchanged `input_value()`, not those calls' outcome, so either behaviour is
      accepted without weakening anything.*
    - Verify **all three**, because each catches a different failure:
      `is_editable() is False`; `is_disabled() is True` (the DOM carries a real `disabled`
      attribute — `get_attribute("disabled") == ""`, and `readonly` is `None`);
      `input_value()` **still** == `typed_name.lower()` after step 14's keystrokes.
      Observed: `False` / `True` / value unchanged.
    - *Mechanism (for the implementer, not an assertion): `CreateBucket.jsx:238` renders
      the field with `disabled={!!currentBucket}` — non-editability is implemented as
      `disabled`, not as `readOnly`. The case's expected observable ("no text cursor
      appears; no input is accepted") holds either way; see § Known Defects.*
16. **(case 16)** Verify the retention controls remain editable in the same Edit form.
    - Open the measure dropdown, click `select-option-weeks` → combobox text == `Weeks`;
      `set_retention_value("3")` → `input_value() == "3"`;
      `artifacts-bucket-retention-value-input`'s `is_editable() is True`.
    - Observed: `Weeks` / `3` / `True`. This is an *actual* edit, not an attribute read —
      "editable" is only proven by a value that actually changed.
17. **(case 17)** Click `artifacts-bucket-cancel-button` (`click_bucket_cancel_button()`).
    - Verify: `page.url` returns to the `/artifacts` list (Cancel is `navigate(-1)`);
      **no** `PUT …/artifacts/buckets/default/*` fired (arm a request listener **before**
      the click — do not infer it from the absence of a toast); the bucket row is still
      present under the lowercase name.
    - Observed: URL `http://localhost:5173/artifacts`, zero PUTs, row present.
    - **Then re-open the Edit form** (hover row → dot-menu → Rename) and verify retention
      is **still `Days` / `1`** — the discarded `Weeks / 3` never reached the server.
      Observed: `Days` / `1`.

## Expected Results

- A mixed-case name is stored and displayed entirely in lowercase (backend conversion).
- The bucket dot-menu offers `Upload files` / `Rename` / `Pin to top` / `Delete`.
- The Edit form shows the lowercase name in a non-editable Name field and the saved
  retention policy (`Days / 1`).
- Retention controls stay editable; Cancel fires no `PUT` and discards the edit.

## Coverage Map

### Axis 1 — Case element → Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | setup | covered (setup) |
| Test data: input `BuCkEt-Mix` / expected `bucket-mix` / retention `Days, 1` | — | § Test Data | generated mixed-case name, `lower()` expectation, `Days/1` | covered (placeholder → generated, documented) |
| Step 1 Navigate to Artifacts | page loads | Test Step 1 | `artifacts-buckets-heading` visible | covered |
| Step 2 Click create-bucket icon | New Bucket form opens | Test Step 2 | URL == `/artifacts/create-bucket` **and** form heading == `New Bucket` (Step 11 asserts `Edit bucket` on the same URL) | covered |
| Step 3 Enter mixed-case name | field accepts input | Test Step 3 | `input_value() == typed` (mixed preserved) + field enabled | covered |
| Step 4 Select retention "Days" | Days selected | Test Step 4 | combobox text | covered |
| Step 5 Enter retention value "1" | field shows 1 | Test Step 5 | `input_value()` | covered |
| Step 6 Click Save | bucket saved | Test Step 6 | `POST` → 200 + response `name` lowercase | covered |
| Step 7 Bucket listed lowercase | lowercase in list | Test Step 7 | row testid present (lower) + absent (mixed) + row text | covered |
| Step 8 Click 3-dot icon | dropdown appears | Test Step 8 | menu container visible (hover first) | covered |
| Step 9 Four options visible | Upload files / Pin to top / **Edit** / Delete | Test Step 9 | live labels `Upload files`+`Rename`+`Pin to top`+`Delete` | covered, with **clarification** (#666) — label is "Rename", order differs |
| Step 10 Click "Edit" | Edit Bucket form opens | Test Step 10 | `bucket-menu-rename-menuitem` click | covered (same clarification) |
| Step 11 Edit form opens | form visible | Test Step 11 | heading text == `Edit bucket` + URL | covered |
| Step 12 Name field displays `bucket-mix` | shows lowercase name | Test Step 12 | `input_value() == typed.lower()` | covered |
| Step 13 Retention is Days / 1 | `Days` + `1` | Test Step 13 | hard assertions on both | covered — passes live |
| Step 14 Try to click + modify Name | no cursor, no input accepted | Test Step 14 | click raises `TimeoutError` (not enabled) + keystrokes sent | covered |
| Step 15 Name field is read-only | read-only | Test Step 15 | `is_editable() False` + `is_disabled() True` + value unchanged | covered — implemented as `disabled` (clarification, observable holds) |
| Step 16 Retention remains editable | editable | Test Step 16 | measure actually changed to `Weeks`, value to `3`, `is_editable() True` | covered |
| Step 17 Click Cancel, form closes without saving | closes, nothing saved | Test Step 17 | URL back to list + **zero PUTs** + reopened form still `Days/1` | covered |
| Expected final state / Pass criteria (lowercase + read-only name + editable retention) | — | Test Steps 6/7, 15, 16 | as above | covered |
| Fail criterion "any step produces an error" | — | Axis 2 | console-error assertion | covered |

### Axis 2 — Observables asserted beyond the case

| Observable | Why |
|---|---|
| `POST` response body's `name` field | the case claims the name is **stored** lowercase; the DOM cannot distinguish "stored lowercase" from "stored mixed, rendered lowercased". The response is the storage layer's own statement |
| Absence of a mixed-case-named row (count 0) | the positive row assertion alone passes on a UI rendering both forms |
| Name field **enabled** in the Create form (step 3) | makes step 15's `is_disabled() is True` mean "Edit mode disables it" rather than "this field is always disabled" — without the control, step 15 would pass for the wrong reason |
| `input_value()` unchanged **after** the typing attempt | `is_editable() is False` is an attribute read; only the unchanged value proves no input was accepted, which is what the case actually asserts |
| Zero `PUT …/artifacts/buckets/*` during Cancel | step 17's "without saving" is otherwise only provable indirectly; asserting the absent request localises a Cancel regression to that step |
| Re-opened Edit form still shows `Days / 1` | the durable half of "without saving" — proves the discarded `Weeks / 3` never reached storage |
| No unexpected console errors across the run | project convention; verified live — **zero** console errors across all 17 steps |

## Concrete Handles

All testid-only. **Zero new testids required.** Provenance verified 2026-08-23 after
`cd ../EliteaUI && git fetch origin`, two-stage grep per `.agents/workflow.md`.

| Element | Testid | Page-object member | PROVENANCE |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | `wait_for_page_load()` | on-main ✓ |
| Create-bucket (folder) icon | `artifacts-create-bucket-button` | `click_create_bucket_button()` | on-main ✓ |
| Bucket name input | `artifacts-bucket-name-input` | `fill_bucket_name()` / `bucket_name_input` | on-main ✓ |
| Retention measure combobox | `artifacts-bucket-retention-measure-select-combobox` | `bucket_retention_measure_combobox` | on-main ✓ (root `…-select` + SingleSelect's `-combobox` suffix) |
| Retention measure options | `select-option-{days\|weeks}` | `BasePage.SELECT_OPTION` class constant | on-main ✓ |
| Retention value input | `artifacts-bucket-retention-value-input` | `bucket_retention_value_input` | on-main ✓ |
| Save button | `artifacts-bucket-save-button` | `click_bucket_save_button()` | on-main ✓ |
| Cancel button | `artifacts-bucket-cancel-button` | `click_bucket_cancel_button()` | on-`automation/testids` only — EliteaAI/EliteaUI@c91c2aac (ELITEA-1810 run); awaiting human cherry-pick to main |
| Form heading (New Bucket / Edit bucket) | `artifacts-bucket-form-heading` | `get_bucket_form_heading_text()` | on-`automation/testids` only — EliteaAI/EliteaUI@c91c2aac; awaiting human cherry-pick |
| Bucket row (dynamic) | `artifacts-bucket-row-{name}` | `ArtifactsPage.BUCKET_ROW` constant | on-main ✓ (`BucketItem.jsx:243`) |
| Bucket dot-menu trigger (dynamic) | `bucket-menu-{name}-menu-button` | `ArtifactsPage.BUCKET_MENU_BUTTON` constant | on-main ✓ (DotMenu `id={\`bucket-menu-${name}\`}`) |
| Bucket dot-menu container (dynamic) | `bucket-menu-{name}-menu` | `ArtifactsPage.BUCKET_MENU_CONTAINER` constant | on-main ✓ |
| "Rename" menu item | `bucket-menu-rename-menuitem` | `click_bucket_menu_rename_item()` | on-`automation/testids` only — the `key: 'bucket-menu-rename'` at `BucketItem.jsx:165` (**DotMenu key-derived**: the runtime testid is `{key}-menuitem`, so the closure-record grep for the full testid string false-negatives — grep the `key:` instead) |

**Dynamic-testid discipline**: rows and menus are addressed through the existing
UPPER_CASE class constants (`BUCKET_ROW`, `BUCKET_MENU_BUTTON`, `BUCKET_MENU_CONTAINER`,
`SELECT_OPTION`) — never an inline `get_by_test_id(f"…")`
(`.agents/testing.md` § Locator policy).

## Automation Hints

- **File**: new spec
  `automation/tests/ui/artifacts/test_artifacts_bucket_name_lowercase.py` (may host
  ELITEA-1812's test too — they must **not** share a bucket).
  **Implemented (2026-08-23) as its own file**,
  `automation/tests/ui/artifacts/test_artifacts_bucket_name_readonly_in_edit_mode.py`,
  per the dispatch's "separate specs, one per case" instruction.
- **Markers**: `@pytest.mark.p3`, `@pytest.mark.artifacts`, `@pytest.mark.regression`, `ui`.
- **One page-object gap** (not a testid gap): `ArtifactsPage` has no accessor for the Name
  field's editability. Add two thin getters next to the existing bucket-form methods —
  `is_bucket_name_input_disabled()` and `is_bucket_name_input_editable()` — over the
  existing `bucket_name_input` descriptor. **Added during implementation (2026-08-23)**,
  exactly as specced, plus a third additive method `delete_bucket_via_menu()` that lifts
  the (now third) repetition of the UI bucket-teardown composition out of the specs. Everything else this case needs already exists
  (`open_bucket_menu`, `get_bucket_menu_items_text`, `click_bucket_menu_rename_item`,
  `get_bucket_form_heading_text`, `open_retention_measure_dropdown`,
  `select_retention_measure`, `get_retention_measure_text`, `get_retention_value`,
  `set_retention_value`, `click_bucket_cancel_button`, `wait_for_bucket_in_list`).
- **Step 14's refused click**: use a **short** explicit timeout (2–3 s) inside
  `pytest.raises(PlaywrightTimeoutError)`. Note that Playwright's deprecated
  `Locator.type()` did **not** raise on the disabled input in this run (it silently did
  nothing) — so the value-unchanged assertion in step 15, not `type()`'s outcome, is what
  proves no input was accepted.
- **Cold-session `networkidle`**: the first `/artifacts` load of a fresh browser session
  exceeded `wait_for_page_load()`'s default 15 s once this session (45 s was comfortable).
  Raise that one call's timeout if seen; it is not a product issue.
- **Retention edit probe must not use `Months`** — defect #1677 would make a `Months`
  policy reopen as `Days`, injecting an unrelated red into this case.
- Steps wrapped `with allure.step("Step N — …")`, one per case step (project convention).

## Cleanup

- Delete the created bucket at teardown via the dot-menu → Delete → `confirm_delete_bucket()`.
  The test must still pass if deletion fails (unique name per run).
- **This analysis run leaked one bucket**, `autotest-1816-182606`, into project 399
  (already ~967 buckets, #636).

## Known Defects / Clarifications

- **No product defect found.** All 17 steps produced their expected result.
- **Clarification (already tracked, #666): the menu item is "Rename", not "Edit".**
  Case steps 9/10 name an "Edit" option; the live menu reads
  `Upload files` / `Rename` / `Pin to top` / `Delete` (the case also lists a different
  order). ELITEA-1810's analysis filed this on
  [#666](https://github.com/EliteaAI/elitea-testing-public/issues/666); this run's
  occurrence was **commented onto #666, not re-filed** (`.agents/profile.md` § Bug filing —
  a real duplicate consolidates evidence on the existing issue). The AFS asserts the live
  labels; asserting the stale case text would be reverse-masking.
- **Clarification (recorded, not filed): "read-only" is implemented as `disabled`.**
  Case steps 14/15 say the Name field is "read-only"; the product renders it
  `disabled={!!currentBucket}` (`CreateBucket.jsx:238`) — a real `disabled` attribute, with
  `readonly` absent. The case's *observable* ("no text cursor appears; no input is
  accepted") holds exactly, so this is terminology, not drift: nothing in the case text
  contradicts the product. Recorded here so the implementer asserts `is_disabled()` /
  `is_editable()` rather than hunting a `readonly` attribute that does not exist. Not
  filed — filing a clarification for a case whose expected result holds would be noise.
