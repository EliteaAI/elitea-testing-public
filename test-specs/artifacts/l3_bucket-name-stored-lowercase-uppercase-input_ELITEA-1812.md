# Test Case: Bucket Name Is Always Stored and Displayed in Lowercase

## Metadata
- **TMS ID**: ELITEA-1812
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend), project `Private` / project_id `399`
- **User set**: `${TEST_USER}` (on localhost, `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot · **Date**: 2026-08-23
- **Status**: **ready-for-automation** — all 6 case steps executed live end-to-end,
  every expected result held. No product defect, no blocked step, **zero new testids
  needed** (every handle below already exists; provenance verified against a freshly
  fetched `origin/main` / `origin/automation/testids`).
- **Cluster**: analysed in one live session with ELITEA-1816. **Separate AFS by design**
  — see § Overlap check.

## Overlap check vs existing automation

Not `already-covered`, not `extend-existing`. Checked by behaviour before executing
(`grep -rniE "lowercase|read.?only" test-specs/artifacts/ automation/tests/ui/artifacts/`,
plus a read of every bucket-creation spec):

- `automation/tests/ui/artifacts/test_artifacts_create_bucket_upload_file.py` (ELITEA-1808),
  `…_55char_name_and_delete.py` (ELITEA-1817), `…_duplicate_bucket_name.py` (ELITEA-1809),
  `…_bucket_name_validation_invalid_formats.py` (ELITEA-1811),
  `…_bucket_retention_edit_persistence.py` (ELITEA-1810, merged onto this batch's trunk):
  all five drive the same New-Bucket form, all five use an **already-lowercase generated
  name** (`autotest-…`). None types an uppercase character, and no spec anywhere asserts
  a case transformation between what is typed and what is stored/displayed.
- `grep -rn "upper\|lower" automation/tests/ui/artifacts/` → the only hits are unrelated
  (`ArtifactTable` search-filter code, not test assertions).

Verdict: the case-conversion axis is untested. `ready-for-automation`.

**Why not folded into ELITEA-1816's spec** (which shares steps 1–4 and 7): the two cases
differ in **steps**, not only in data — 1816 continues into the bucket dot-menu, the Edit
form, a read-only-name assertion and a Cancel, 11 extra steps this case never performs.
Per `test-case-analysis` § Cluster dispatches the merge test is *data-only difference*, so
they stay separate specs. They may share a file and page-object helpers.

## Preconditions
- User logged in (localhost: `auth_state` fixture skips login).
- A project is selected (`Private`, id 399 in this run).
- **No pre-seeded bucket** — creating the bucket **is** case steps 2–4, so do NOT reuse the
  `artifact_bucket` API fixture: seeding via the API would substitute the very producer
  (the create request) whose case-handling this case observes.

## Test Data

### generate-per-test
- **Bucket name (typed)**: the case's literal `BUCKET-TEST` is a case-text placeholder —
  a fixed name collides with the 900+ buckets already leaked into project 399 (#636) and
  with re-runs. Generate an **all-uppercase** unique name of the same shape:
  `f"AUTOTEST-1812-{ts}"` (e.g. `AUTOTEST-1812-182449`). It must satisfy the form's yup
  schema (`^[a-zA-Z][a-zA-Z0-9-]*$`, ≤ 56 chars) — uppercase **is** schema-valid, which is
  precisely why the conversion happens server-side rather than being rejected client-side.
- **Expected stored/displayed name**: `typed_name.lower()` — derive it, never hardcode.
- Retention is **left at its default** (`Years / 1`) — this case never touches it.

## Test Steps

Every step below was executed live in this order (probe: `/tmp/probe_1812_1816.py`,
2026-08-23 18:24 local); "observed" values are what the running system produced.

1. **(case 1)** Navigate to `${BASE_URL}/artifacts`; wait for `artifacts-buckets-heading`.
   - Observed: Artifacts page loads, bucket list rendered.
   - *Timing note*: `wait_for_page_load()`'s default 15 s `networkidle` wait **timed out
     on the first navigation of a cold session** in this run; 45 s was comfortable. See
     § Automation Hints.
2. **(case 2)** Click `artifacts-create-bucket-button` — this **is** the folder/create icon
   above the bucket list (`BucketHeader.jsx`, `NewFolder` icon, tooltip "Create bucket").
   - Verify: `page.url` ends with `/artifacts/create-bucket` — a full page navigation,
     **not a modal**. Observed: `http://localhost:5173/artifacts/create-bucket`.
   - Verify: `artifacts-bucket-form-heading` reads **`New Bucket`**.
     **Amended during ELITEA-1812 implementation (2026-08-23, review round 1):** the URL
     alone does NOT satisfy the case's expected result ("'New Bucket' form opens" ) —
     `/artifacts/create-bucket` is a SINGLE route serving BOTH forms
     (`CreateBucket.jsx:214` renders `currentBucket ? 'Edit bucket' : 'New Bucket'`, as
     ELITEA-1816's AFS Step 11 establishes), so a regression that opened the edit form on
     this route would still pass a URL-only assertion. The heading text is the
     discriminator.
3. **(case 3)** Enter the uppercase name via `ArtifactsPage.fill_bucket_name(name)`
   (click + `select_text()` + `type()` — the field is pre-filled `new-bucket`; a bare
   `fill()` / `Control+A` does **not** work on this MUI field).
   - Verify: `artifacts-bucket-name-input`'s `input_value() == "AUTOTEST-1812-182449"`
     — **the field accepts and preserves uppercase as typed; no live lowercasing occurs
     in the input.** Observed exactly that.
4. **(case 4)** Click `artifacts-bucket-save-button` inside
   `page.expect_response(POST …/artifacts/buckets/default/{project_id})`
   (`ArtifactsPage.click_bucket_save_button()` already wraps this).
   - Verify: response status `200` **and** the response JSON's `name` field equals
     `typed_name.lower()`.
   - Observed: `200`, body
     `{"message": "Created", "id": "p--399.autotest-1812-182449", "name": "autotest-1812-182449"}`
     — the **backend** is the producer of the lowercase form (the React form sends
     `values.name.trim()` unchanged; there is no `toLowerCase()` anywhere in
     `src/pages/Artifacts/CreateBucket.jsx`).
   - Verify: the save leaves the create route and lands back on the Artifacts list.
     **Amended during ELITEA-1812 implementation (2026-08-23):** the AFS originally
     expected `/artifacts?bucket=<lowercase name>` (the form's
     `PENDING_BUCKET_SESSION_KEY` auto-select). Live, the save lands on the **bare
     `/artifacts` root** — an auto-retrying `to_have_url` polled 87 times over 45 s and
     never saw a `?bucket=` param. The spec therefore asserts the route only
     (`/artifacts` with an optional query), and the "bucket is saved" claim rests on the
     POST assertions above. Consequence for step 5: the sidebar click is a same-route
     navigation, so its assertion is "the Artifacts root with the bucket list rendered",
     not "the `?bucket=` param was cleared".
5. **(case 5)** Click the sidebar's Artifacts entry — `sidebar-menu-item-artifacts`
   (`BasePage.SIDEBAR_MENU_ITEM.format("artifacts")`) — to return to the Artifacts root.
   - Verify: `page.url` is the `/artifacts` root (no `?bucket=` param) and
     `artifacts-buckets-heading` is visible again.
   - *(The live probe used `ArtifactsPage.navigate_to_artifacts()` — a direct URL nav — as
     transit; the sidebar click is the case's own step and is the shape to automate. The
     sidebar testid is confirmed present, see § Concrete Handles.)*
     **Confirmed during implementation (2026-08-23):** the sidebar click itself was
     executed live and works — `sidebar_menu_item("artifacts").click()` keeps the app on
     the `/artifacts` root with `artifacts-buckets-heading` visible.
6. **(case 6)** Verify the bucket is listed **in lowercase**:
   - `artifacts-bucket-row-{lower}` present (**observed: present**) — the row testid is
     itself derived from the stored name (`data-testid={\`artifacts-bucket-row-${name}\`}`,
     `BucketItem.jsx:243`), so its presence is a name assertion, not just an existence one.
   - `artifacts-bucket-row-{TYPED_UPPERCASE}` **absent**, count 0 (**observed: absent**) —
     the negative half; without it, a UI that rendered both forms would pass.
   - The row's `text_content()` equals the lowercase name **exactly** (observed:
     `"autotest-1812-182449"`), and contains **no** uppercase character
     (`row_text == row_text.lower()`).

## Expected Results

- The Name field accepts uppercase input verbatim (no client-side transformation).
- `POST …/artifacts/buckets/default/{project_id}` → `200`, response `name` is all-lowercase.
- The bucket list renders exactly one row, named in all lowercase; no uppercase-named row
  exists.

## Coverage Map

### Axis 1 — Case element → Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` fixture | setup | covered (setup) |
| Test-data row "Input bucket name = BUCKET-TEST" | — | § Test Data | generated uppercase name | covered (placeholder → generated, documented) |
| Test-data row "Expected stored name = bucket-test" | — | Test Step 6 | `typed.lower()` derived | covered |
| Step 1 Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible | covered |
| Step 2 Click folder/create icon | "New Bucket" form opens | Test Step 2 | URL == `/artifacts/create-bucket` **and** form heading == `New Bucket` (the route is shared with the edit form — URL alone does not discriminate) | covered |
| Step 3 Enter uppercase name | field accepts the input | Test Step 3 | `input_value() == typed` (uppercase preserved) | covered |
| Step 4 Click Save | bucket is saved | Test Step 4 | `POST` → 200 | covered |
| Step 5 Click "Artifacts" | navigation to Artifacts root | Test Step 5 | sidebar item click → `/artifacts` root | covered |
| Step 6 Bucket listed as lowercase | listed lowercase | Test Step 6 | row testid present (lower) + absent (upper) + row text == lower | covered |
| Expected final state / Pass criterion "stored **and** displayed lowercase regardless of input case" | — | Test Steps 4 + 6 | POST response `name` (stored) + row text (displayed) | covered — **both halves**, deliberately |
| Fail criterion "any step produces an error" | — | Axis 2 | console-error assertion | covered |

### Axis 2 — Observables asserted beyond the case

| Observable | Why |
|---|---|
| `POST` response body's `name` field | the case claims the name is **stored** lowercase, not merely displayed so; the DOM alone cannot distinguish "stored lowercase" from "stored uppercase, rendered lowercased by CSS/JS". The response is the storage layer's own statement and is the only honest oracle for the "stored" half |
| Absence of an uppercase-named row (count 0) | the positive assertion alone passes on a UI that rendered *both* forms, or that kept the uppercase row from a previous state; the negative half is what makes the conversion claim exclusive |
| `input_value()` still uppercase at step 3 | pins **where** the conversion happens (server, not the field). If a future release adds client-side lowercasing, this assertion fails loudly instead of the test silently still passing for a different reason |
| No unexpected console errors across the run | project convention; verified live — the run produced **zero** product console errors (the single 404 observed was the analyst's own deliberate `/api/v1/…` probe of a non-existent API version, not a product request) |

## Concrete Handles

All testid-only. **Zero new testids required** (the form-heading testid below already exists, added for ELITEA-1810). Provenance verified 2026-08-23 after
`cd ../EliteaUI && git fetch origin`, two-stage grep per `.agents/workflow.md`.

| Element | Testid | Page-object member | PROVENANCE |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | `wait_for_page_load()` | on-main ✓ |
| Create-bucket (folder) icon | `artifacts-create-bucket-button` | `click_create_bucket_button()` | on-main ✓ |
| Bucket name input | `artifacts-bucket-name-input` | `fill_bucket_name()` / `bucket_name_input` | on-main ✓ |
| Save button | `artifacts-bucket-save-button` | `click_bucket_save_button()` | on-main ✓ |
| Bucket row (dynamic) | `artifacts-bucket-row-{name}` | `ArtifactsPage.BUCKET_ROW` class constant, `bucket_row(name)` / `bucket_exists(name)` | on-main ✓ (`BucketItem.jsx:243`) |
| Sidebar → Artifacts | `sidebar-menu-item-artifacts` | `BasePage.SIDEBAR_MENU_ITEM` | on-`automation/testids` only (awaiting human promotion to main) |
| Bucket form heading (New Bucket / Edit bucket) | `artifacts-bucket-form-heading` | `get_bucket_form_heading_text()` | on-`automation/testids` only — EliteaAI/EliteaUI@c91c2aac; awaiting human cherry-pick (added for ELITEA-1810; **adopted here in review round 1** so Step 2 discriminates the create form from the edit form on the shared route) |

**Dynamic-testid discipline**: the bucket row is addressed through the existing UPPER_CASE
class constant `BUCKET_ROW = '[data-testid="artifacts-bucket-row-{}"]'` — never an inline
`get_by_test_id(f"…")` (`.agents/testing.md` § Locator policy).

## Automation Hints

- **File**: new spec `automation/tests/ui/artifacts/test_artifacts_bucket_name_lowercase.py`.
  ELITEA-1816's spec may live in the same file (it shares steps 1–4/7) — that is the
  implementer's call; the two tests must not share a bucket.
  **Implemented (2026-08-23) as TWO separate spec files** — this one, and
  `test_artifacts_bucket_name_readonly_in_edit_mode.py` for ELITEA-1816 — per the
  dispatch's "separate specs, one per case" instruction. They share the page object, not
  the file, and each generates its own bucket.
- **Markers**: `@pytest.mark.p3`, `@pytest.mark.artifacts`, `@pytest.mark.regression`, `ui`.
- **Existing page-object methods cover every interaction** — `click_create_bucket_button`,
  `fill_bucket_name`, `click_bucket_save_button` (already wraps `expect_response` on the
  POST and returns the `Response`, so `response.json()["name"]` is available),
  `bucket_exists`, `bucket_row`, `wait_for_bucket_in_list`. **No new page-object method is
  strictly required**; a small `sidebar_menu_item("artifacts").click()` via the existing
  `BasePage` accessor covers step 5.
- **Cold-session `networkidle`**: the first `/artifacts` load of a fresh browser session
  exceeded `wait_for_page_load()`'s default 15 s once in this session (45 s passed). If the
  implementer sees a `networkidle` timeout on the *first* navigation only, raise that one
  call's timeout rather than treating it as a product issue.
- **Do not assert against a hardcoded `bucket-test`** — derive the expectation from the
  generated name (`name.lower()`), so the assertion still means "the system lowercased it".
- Steps wrapped `with allure.step("Step N — …")`, one per case step (project convention).

## Cleanup

- Delete the created bucket at teardown via the bucket dot-menu → Delete →
  `confirm_delete_bucket()` (UI delete works; the API fixture's teardown is the one that
  404s — #636). If deletion fails, the test must still pass: the name is unique per run.
- **This analysis run leaked one bucket**, `autotest-1812-182449`, into project 399 —
  recorded here deliberately; project 399's bucket count is already ~967 (#636).

## Known Defects / Clarifications

- **None found.** Every case step's expected result held exactly as authored.
- Worth knowing (no action): the lowercase conversion is **backend** behaviour. The React
  form (`CreateBucket.jsx`) sends `values.name.trim()` verbatim, and the yup schema
  (`^[a-zA-Z][a-zA-Z0-9-]*$`) explicitly permits uppercase — so a future backend change
  would break this case with no front-end diff to point at.
