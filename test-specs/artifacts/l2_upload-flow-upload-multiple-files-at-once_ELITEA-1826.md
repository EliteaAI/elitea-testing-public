# Test Case: Upload Flow – Upload Multiple Files at Once

## Metadata
- **TMS ID**: ELITEA-1826
- **Linked Story**: [EliteaAI/elitea-testing-public#224](https://github.com/EliteaAI/elitea-testing-public/issues/224) (tracking issue)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399, freshly synced
  against `origin/main` this session — 0 behind). Every claim below was reproduced live
  this run.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all 10 case steps
  + all 3 preconditions verified), zero defects, zero testid gaps (fully covered by the
  existing testid inventory — nothing needed adding this run), zero console errors. Not
  `already-covered` / not `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` was read in full before this run (1163 lines), plus
the three existing artifact upload/multi-file specs
(`test_artifacts_create_bucket_upload_file.py`/ELITEA-1808,
`test_artifacts_upload_duplicate_cancel.py`/ELITEA-1832,
`test_artifacts_multi_file.py`/ELITEA-1327) were read in full.

- **ELITEA-1327** (`test_artifacts_multi_file.py`) — an **agent** creates multiple files
  server-side via the Artifact toolkit in one tool call; the test only verifies the
  agent-created files are visible/downloadable. It never drives the manual upload UI at
  all (no `upload_files_button`/native-file-chooser interaction anywhere in that file).
  Zero overlap — different creation mechanism entirely.
- **ELITEA-1808** (`test_artifacts_create_bucket_upload_file.py`) — drives a **single**
  file (`test.txt`) through the **bucket-row 3-dot menu's "Upload files" item** (left
  panel, before a bucket is opened), not the toolbar. Confirmed live both entry points
  converge on the identical `artifacts-upload-path-dialog` modal/endpoint, but the entry
  point AND the single-vs-multi-file selection are both different from this case.
- **ELITEA-1832** (`test_artifacts_upload_duplicate_cancel.py`) — this is the closest
  sibling: it DOES drive the same **toolbar** `upload_files_button` with **multiple**
  files selected simultaneously via `expect_file_chooser()` + `set_files([...])` (the
  exact mechanism this case also needs), and does reach the "Upload files to ..." dialog
  with the Path pre-filled. **However**, its own test (read in full, `automation/tests/
  ui/artifacts/test_artifacts_upload_duplicate_cancel.py:116-294`) is deliberately built
  around the **duplicate-detection → Resolve-duplicates modal → Cancel** path: one of its
  two selected files (`sample.txt`) is a pre-seeded duplicate, and the test's terminal
  assertions (steps 10-15) all verify the upload was **aborted** — zero network requests
  fire on both the "Upload" click (client-side duplicate diff) and the "Cancel" click, no
  success toast, `sample.png` never lands in the table. **That test never reaches a
  completed multi-file upload.** This case (ELITEA-1826) is the opposite/complementary
  scenario — a clean multi-file batch with **no duplicates**, where the Upload click
  actually fires the PUT requests, a success toast appears, and all files land in the
  table with metadata. Confirmed live this run: clicking "Upload" on 3 brand-new files
  fires **three separate `PUT .../artifacts/s3/{bucket}/{filename}?project_id=...`
  requests** (not client-side-only, unlike the duplicate path) — this is a materially
  different code path/observable than what ELITEA-1832 exercises, not a small gap that
  could be grafted onto that test (whose whole structure is duplicate-then-cancel).

Verdict: **zero behavioral overlap** — the plain multi-file-at-once happy path (no
duplicates, no bucket-creation-form, upload actually completes) is untested by any
existing spec. `ready-for-automation`, fresh implementation.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists (the case's `bucket-1` is a **case-text placeholder**, not a literal
  fixture name — confirmed live again this run: the left-panel bucket list showed 167
  buckets, including every `autotest-*` bucket from prior cases' runs, and none named
  exactly `bucket-1`; same finding as ELITEA-1808/ELITEA-1832). Use the existing
  `artifact_bucket` pytest fixture (`automation/fixtures/data_fixtures.py:455`) — fresh,
  empty, function-scoped, deleted in its own teardown.
- Test files `sample1.txt`, `sample1.png`, `sample1.md` are available for upload —
  generate via `tmp_path` in test setup (§ Test Data).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the `artifact_bucket` fixture (see § Preconditions) — do **not**
  hardcode `bucket-1`.
- **File names — confirmed live this run these are NOT placeholders, unlike the bucket
  name.** The case's own step 10 asserts the exact literal strings `"sample1.txt"`,
  `"sample1.png"`, `"sample1.md"` must appear in the file table — this is a real,
  intentional assertion target, not a stand-in. Unlike bucket names (which share one
  flat, ~167-bucket namespace in the `Private` project and therefore collide across
  parallel/repeated runs unless uniquified), files live **scoped to their own bucket**;
  since `artifact_bucket` mints a fresh, uniquely-named bucket per test, there is no
  collision risk in reusing these literal filenames verbatim across parallel or repeated
  test runs. Use the literal names directly.
- **File content/format** — generate via `tmp_path` (project convention, no checked-in
  `automation/fixtures/files/` directory exists — same finding as ELITEA-1832):
  - `sample1.txt` — small fixed text content (byte count irrelevant beyond being
    stable/non-empty for the size-column assertion).
  - `sample1.md` — small fixed markdown content.
  - `sample1.png` — a minimal valid PNG built in-memory. **Reuse, don't reinvent**: the
    exact in-memory PNG-builder helper already exists at
    `test_artifacts_upload_duplicate_cancel.py:75-91` (`_minimal_png_bytes()`, a bare
    1×1 PNG via `struct`/`zlib`) — either import/share it or copy the same technique;
    confirmed live this run it uploads and renders correctly as `"PNG Image"` in the
    Type column.
- **Confirmed live Type-column mapping** (useful for the Test Step 10 assertion): `.txt`
  → `"Text"`, `.md` → `"Markdown"`, `.png` → `"PNG Image"`.

No `reuse-existing` fixture applies — same reasoning as ELITEA-1832/1839/1840: a bucket
in a specific pre-upload state isn't safe to share across parallel/serial runs.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts` (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible (`ArtifactsPage.wait_for_page_load()`
     already does this).
2. Select the fresh precondition bucket via `navigate_to_bucket(bucket_name)` — direct URL
   navigation `?bucket={bucket_name}` (case step 2; more reliable than clicking the
   left-panel list item, per the existing page-object docstring / ELITEA-1832 precedent).
   - **Verify**: right-panel header shows the bucket name; `is_bucket_empty()` is
     `True` (baseline — confirms the fixture handed over a genuinely empty bucket).
3. Click `artifacts-upload-files-button` (case step 3 — "upload icon in the top-right
   corner of the main panel").
   - **Verify**: the native file-chooser fires immediately (case step 4) — confirmed
     live via `expect_file_chooser()`, no loading delay, same immediacy as
     ELITEA-1832/ELITEA-1808's precedent.
4. Select all three files — `sample1.txt`, `sample1.png`, `sample1.md` — **in one call**
   to `ArtifactsPage.upload_files([txt_path, png_path, md_path])` (case step 5 — "use
   Ctrl+click or Shift+click"; confirmed live and by the ELITEA-1832 AFS this is the
   correct Playwright equivalent: `file_chooser.set_files([...])` with a list IS genuine
   simultaneous multi-select, there is no OS-dialog automation in Playwright and none is
   needed).
   - **Verify**: folded into step 5's verify below (same observable — the very next
     dialog correctly reflects all three files pending, matching the case's own folding
     of step 5 into step 6's confirm).
5. Click "Open" is mechanically the same action as step 4's `set_files()` call (case step
   6 — there is no separate native "Open" click to drive in Playwright terms).
   - **Verify**: `wait_for_upload_path_dialog()` — the "Upload files to ..." modal opens
     (case step 6/7).
6. Verify the "Upload files to ..." modal's Path field is pre-filled with the bucket name
   (case step 7).
   - **Verify**: `get_upload_path_prefix_text()` contains `{bucket_name}/` — confirmed
     live: `"autotest-elitea1826-multifile-841841/"` for this run's bucket. One shared
     Path prefix for all three files (not three separate path fields) — confirmed live.
7. Click `artifacts-upload-path-upload-button` (case step 8).
   - **Verify**: fires **three separate** `PUT ${ELITEA_URL}/artifacts/s3/{bucket}/{file}
     ?project_id=${PROJECT_ID}` requests (one per file), all → `200 OK` — confirmed live
     via `browser_network_requests`: `.../sample1.txt`, `.../sample1.png`,
     `.../sample1.md`, all 200. This is the load-bearing proof the upload actually
     completed (as opposed to ELITEA-1832's duplicate path, which fires zero requests).
8. Verify a success notification is displayed with the exact text "Your file(s) have
   been successfully uploaded!" (case step 9).
   - **Verify**: `success_toast_message` (`toast-message` testid) becomes visible with
     that exact text. **Confirmed live this run via an independent technique** (a
     `MutationObserver` installed on `document.body` before triggering the upload,
     to catch the toast even if it auto-dismisses before a single-shot snapshot would):
     the toast fires and its `textContent` is byte-identical to the case's expected
     string, both for the 3-file batch and for a follow-up single-file upload in the
     same bucket. This is a **positive** assertion (unlike ELITEA-1832's step 12, which
     asserts absence) — use Playwright's auto-retrying `expect(locator).to_be_visible()`
     / `to_contain_text(...)` called **immediately** after the Upload click, not a
     single instantaneous DOM read (the toast is short-lived, same auto-dismiss
     characteristic ELITEA-1832 documented, but `expect()`'s polling window is what
     catches it — confirmed live it stays mounted long enough for at least one
     MutationObserver-detected paint).
9. Verify all three files — `sample1.txt`, `sample1.png`, `sample1.md` — are listed in
   the file table with Name, Type, Size, and Last-update values populated (case step 10).
   - **Verify**: `get_total_file_count_from_pagination() == 3` (confirmed live: pagination
     label read `"1 - 3 of 3"` after the batch landed — a stronger signal than checking
     each file individually, since it also catches a partial-upload count mismatch).
   - **Verify**: `set(get_file_names()) == {"sample1.txt", "sample1.png", "sample1.md"}`.
   - **Verify per file** via `get_file_row_text(filename)` (existing ELITEA-1808 method —
     reads the whole row's text since `ArtifactTable.jsx` has no per-cell testid):
     - `sample1.txt` → confirmed live row text `"sample1.txtText57 B19-07-2026, 12:04 PM"`
     - `sample1.png` → confirmed live row text `"sample1.pngPNG Image73 B19-07-2026, 12:04 PM"`
     - `sample1.md` → confirmed live row text `"sample1.mdMarkdown66 B19-07-2026, 12:04 PM"`
     Assert Name + Type substring + a `\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)` timestamp
     regex on the trailing segment (pattern only, never an exact clock value) — same
     established pattern as ELITEA-1808 Test Step 16. Size is content-dependent (assert
     it's non-zero/matches the generated content's byte count, not a hardcoded value).
   - **Viewport note (reconfirms ELITEA-1808's finding, not a new discovery):** the
     "Last update" column only rendered in this run's DOM at a 1600×900 viewport: at the
     default 1200×822 MCP viewport the same rows read
     `"sample1.txtText57 B"` with **no** trailing timestamp (responsive layout clips the
     column, it is not conditionally omitted from the DOM based on data). Confirmed by
     resizing the SAME page mid-run and re-reading the SAME rows — the timestamp
     appeared with no other change. Automation should not depend on viewport size for
     this assertion; explicitly set a viewport ≥1600px wide (or otherwise confirm the
     column is present) before asserting the timestamp segment.

## Expected Results
- Clicking the toolbar `artifacts-upload-files-button` opens the native file chooser
  immediately; selecting 3 files there is one Playwright `set_files()` call.
- The "Upload files to ..." modal opens with ONE shared Path field pre-filled with the
  bucket name — not one field per file.
- Clicking "Upload" fires three concurrent `PUT .../artifacts/s3/{bucket}/{file}` requests
  (one per file), all `200 OK` — a fundamentally different, non-duplicate code path from
  ELITEA-1832's client-side-only duplicate detection.
- A success toast with the exact text "Your file(s) have been successfully uploaded!"
  appears (auto-dismisses quickly — assert via `expect()`'s auto-retry, not a
  single-shot read).
- All three files appear in the file table with Name/Type/Size/Last-update populated,
  and `get_total_file_count_from_pagination() == 3`.
- No console errors during the flow (confirmed: 0 errors across the whole run, including
  a second follow-up single-file upload used to independently verify the toast).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Precondition: bucket "bucket-1" exists | Bucket available | Preconditions + Test Data | `artifact_bucket` fixture (fresh, unique name — "bucket-1" confirmed live as a case-text placeholder, no such literal bucket exists among 167 in the project) | asserted |
| Precondition: sample1.txt/png/md available for upload | Files exist locally | Preconditions + Test Data | `tmp_path`-generated files (PNG via the existing `_minimal_png_bytes()` helper) | asserted |
| Step 1: Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click "bucket-1" in bucket list | Bucket is selected | Test Step 2 | `navigate_to_bucket()` + `is_bucket_empty() == True` baseline | asserted |
| Step 3: Click upload icon top-right | System file explorer opens | Test Step 3 | `expect_file_chooser()` fires on `artifacts-upload-files-button` click | asserted |
| Step 4: Verify file explorer opens immediately | File explorer open | Test Step 3 (folded) | same observable as step 3, no loading delay confirmed live | asserted *(decomposed)* |
| Step 5: Select all 3 files via Ctrl/Shift+click | All three files selected | Test Step 4 | `upload_files([txt, png, md])` — `set_files()` with a list IS genuine simultaneous multi-select | asserted |
| Step 6: Click "Open" | "Upload files to ..." modal opens | Test Step 5 | `wait_for_upload_path_dialog()` | asserted *(decomposed — `set_files()` IS the confirm, no separate native click to drive)* |
| Step 7: Verify modal opens with Path pre-filled with "bucket-1" | Modal open, correct path | Test Step 6 | `get_upload_path_prefix_text()` contains `{bucket_name}/` | asserted *(generated unique bucket name, not literal "bucket-1")* |
| Step 8: Click "Upload" in modal | Upload completes for all 3 files | Test Step 7 | 3× `PUT .../artifacts/s3/{bucket}/{file}` → 200, confirmed live via network capture | asserted |
| Step 9: Verify success notification "Your file(s) have been successfully uploaded!" | Success notification appears | Test Step 8 | `success_toast_message` exact-text match, confirmed live via MutationObserver capture (exact string match, not paraphrased case text) | asserted |
| Step 10: Verify all three files listed with Name/Type/Size/Last-update populated | All three files appear with metadata | Test Step 9 | `get_total_file_count_from_pagination() == 3` + `get_file_row_text()` per file (Name/Type/Size/timestamp regex) | asserted |
| Expected Final State: all 3 uploaded in one operation, correct metadata | Composite pass condition | Test Steps 7, 9 | combination of network + table assertions | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | console-error check (0 errors, confirmed across 2 upload actions in this run) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Network-level proof of 3 concurrent PUT requests, each 200 OK** — *added: stronger,
  more specific signal than a DOM-only check that the upload "completed" — also proves
  this is NOT the client-side-only duplicate-detection path ELITEA-1832 exercises,
  useful cross-case context distinguishing the two scenarios.*
- **`get_total_file_count_from_pagination() == 3`** — *added: catches a partial-upload
  regression (e.g. 2 of 3 files silently failing) that per-file `file_exists()` checks
  alone could miss if not cross-checked against a total.*
- **Console-error check across the full flow, including a second independent
  single-file upload** — *added: standard silent-error guard, consistent with sibling
  cases' precedent; the second upload was originally added only to verify the toast
  (see below) but doubled as an extra clean console-error sample.*
- **Independent MutationObserver-based confirmation that the toast fires with the EXACT
  case-specified string** — *added: the case's step 9 gives an exact expected string;
  rather than trust a single snapshot (which could miss a fast-dismissing toast and
  wrongly suggest case-text drift, the ELITEA-1832-step-12 failure mode in reverse),
  this run independently proved the toast both fires AND matches verbatim, ruling out
  reverse-masking in either direction for this specific assertion.*
- **Viewport-dependent "Last update" column re-confirmed on a live, fresh page** (not
  just cited from ELITEA-1808's AFS) — *added: re-verifying a prior finding rather than
  trusting it by reference is cheap and catches drift; confirmed unchanged.*

## Cleanup
1. Delete the bucket via the `artifact_bucket` fixture's own teardown
   (`ArtifactAPI.delete_bucket()`). **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)):** this delete
   call 404s on both URL-format attempts in the current dev environment, so the bucket
   will likely leak — not new to this case, out of scope to fix here.
2. No other entities are created by this case (no Agent, no Toolkit, no Credential).
3. **This exploration run's artifacts** (not part of the automated test): bucket
   `autotest-elitea1826-multifile-841841` was created via the live UI "New Bucket" form
   in the `Private` project (id 399) to reach this case's precondition state, containing
   `sample1.txt` (57 B), `sample1.png` (73 B), `sample1.md` (66 B), and one extra
   `toastcheck.txt` (29 B, used only for the independent toast-text verification, see
   Test Step 8). Left in place — matches this project's existing convention of ~167
   un-deleted `autotest-*` buckets already present from prior runs; safe to delete at
   any time via `ArtifactAPI.delete_bucket("autotest-elitea1826-multifile-841841")`.
4. Local exploration screenshot (repo root, untracked):
   `ELITEA-1826-step10-file-table-with-metadata.png`.
5. Local temp upload source files (untracked, harmless to leave or delete):
   `.playwright-mcp/sample1.txt`, `.playwright-mcp/sample1.png`,
   `.playwright-mcp/sample1.md`, `.playwright-mcp/toastcheck.txt`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator
policy (`.agents/testing.md` § Locator policy) is **testid-only, no fallback ladder** —
`LocatorDescriptor(testid=...)` with no `fallback=`/`locator=`.

**Zero testid gaps this run** — every element this case touches already has a
policy-compliant testid on `automation/testids`, and `ArtifactsPage` already has every
method needed (see § Automation Hints). No `add-data-testid` work was required.

| Element | testid | Status | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | left panel |
| Upload files button (toolbar) | `artifacts-upload-files-button` | existing | this case's own entry point (case step 3) — top-right of the main panel |
| "Upload files to ..." modal — dialog / Path input / Upload button | `artifacts-upload-path-dialog` / `artifacts-upload-path-input` / `artifacts-upload-path-upload-button` | existing (ELITEA-1832) | confirmed live: ONE shared Path field for all 3 selected files, not per-file |
| File list container / file row | `artifacts-file-list` / `artifacts-file-row` | existing | |
| Success toast (generic, app-wide) | `toast-message` | existing elsewhere, **confirmed live for THIS flow specifically this run** | ELITEA-1832 only confirmed its *absence* on the duplicate path; this run independently confirmed its *presence* with the exact expected text on the successful-upload path |

## Network Behavior
- **Bucket open**: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id=${PROJECT_ID}
  &format=json` → `200 OK` on `navigate_to_bucket()`.
- **File upload (no duplicates)**: **three separate**
  `PUT {ELITEA_URL}/artifacts/s3/{bucket}/{file_key}?project_id=${PROJECT_ID}` requests
  fire from the single "Upload" click — one per selected file, all → `200 OK`. Confirmed
  live:
  `PUT http://localhost:5173/artifacts/s3/autotest-elitea1826-multifile-841841/sample1.txt?project_id=399`,
  `.../sample1.png?project_id=399`, `.../sample1.md?project_id=399` — all 200.
  This is the key structural difference from ELITEA-1832's duplicate path (zero network
  requests, client-side diff only).
- **Bucket listing refetch** after upload: `GET {ELITEA_URL}/artifacts/s3/{bucket}
  ?project_id=${PROJECT_ID}&format=json` → `200 OK`, powers the file-table re-render.
- No unexpected requests observed between the Upload click and the file-table update;
  zero console errors across the full flow (2 independent upload actions this run).

## Known Defects Found During Exploration
**None found.** Live product behavior matches the case's expected behavior exactly:
multi-file selection is genuine (3 files via one `set_files()` call), the Path field is
correctly shared/pre-filled, the upload completes with 3× 200 OK PUTs, the success toast
fires with the EXACT case-specified text (independently verified via MutationObserver,
not just visually inspected), and all three files land in the table with correct
Name/Type/Size/Last-update metadata. Zero console errors.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: `automation/pages/artifacts_page.py`'s `ArtifactsPage` **already has every
  method this case needs** — no new page-object methods required:
  `navigate_to_artifacts()`, `navigate_to_bucket()`, `is_bucket_empty()`, `upload_files()`
  (toolbar entry point + multi-file `set_files()`), `wait_for_upload_path_dialog()`,
  `get_upload_path_prefix_text()`, `click_upload_path_upload_button()`, `file_exists()`,
  `get_file_names()`, `get_file_row_text()`, `get_total_file_count_from_pagination()`,
  `success_toast_message` (`LocatorDescriptor`).
- **Do NOT use `click_upload_path_upload_button_and_capture_response()`** (the
  ELITEA-1808-added variant) for this case — confirmed live it only wraps
  `page.expect_response()` for a **single** matching PUT via `expect_response`'s
  first-match semantics, but this case's Upload click fires **three concurrent** PUTs.
  Using it here would either miss two of the three responses or race unpredictably on
  which one it captures. Two viable approaches instead:
  1. **Recommended** — use the plain `click_upload_path_upload_button()`, then rely on
     the file-table condition waits (`file_exists()` per name / pagination count) as the
     completion signal — this project's established preference for condition-based UI
     waits over network races on multi-request flows (see ELITEA-1808's own documented
     rejection of `capture_requests_matching()` for positive multi-request assertions —
     `status: None` race).
  2. If a network-level assertion is wanted too, register three separate
     `page.expect_response()` matchers (one per filename) around the click, or read
     `browser_network_requests`/an equivalent post-hoc network log filtered on
     `artifacts/s3` and assert exactly 3 matching 200s appear.
- **Toast assertion**: call `expect(artifacts_page.success_toast_message).to_be_visible()`
  / `.to_contain_text("Your file(s) have been successfully uploaded!")` **immediately**
  after `click_upload_path_upload_button()` — Playwright's auto-retrying `expect()` is
  what catches this (confirmed live via MutationObserver the toast auto-dismisses on a
  similar timescale to what ELITEA-1832 documented for the *absence* case); do not gate
  this behind a `page.wait_for_timeout()` first, and do not treat a single-shot
  `text_content()` read as reliable — the timing risk cuts both ways (a slow read after
  the dismiss would falsely suggest the toast never fires, mirroring ELITEA-1832's own
  documented caveat but in the positive direction).
- **Viewport**: set the browser viewport to at least 1600×900 (or otherwise confirm)
  before asserting the "Last update" timestamp segment in Test Step 9/10 — confirmed
  live this run the column is present in the DOM but visually clipped/hidden at the
  narrower ~1200px MCP default viewport, matching ELITEA-1808's finding. If the project's
  default test viewport is already ≥1600px wide this is moot; verify against
  `automation/config.py`'s configured viewport before assuming either way.
- Fixtures: `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`) for the bucket;
  `tmp_path` for all three files, reusing `_minimal_png_bytes()` from
  `test_artifacts_upload_duplicate_cancel.py:75-91` for the PNG (share it — e.g. move to
  a small shared test-data helper — rather than re-copy the function a third time if a
  future artifacts case needs a PNG again).
- Suggested test file: `automation/tests/ui/artifacts/test_artifacts_upload_multiple_files.py`.
