# Test Case: Upload Flow – Duplicate Handling: Skip Skips Duplicate and Saves Non-Duplicate Files

## Metadata
- **TMS ID**: ELITEA-1829
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster dispatch with ELITEA-1828, ELITEA-1831)
- **Status**: ready-for-automation — case executed live end-to-end, all 13 case
  steps confirmed, no defects. Not `already-covered` and not `extend-existing`
  — see § Overlap check below.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py`
(`TestArtifactUploadDuplicateCancel`, ELITEA-1832, **merged to
`origin/automation/base`**, commit `9dcb2805`) shares this case's setup/
navigation/upload-trigger prefix (multi-file select: one duplicate + one new
file, "Upload files to ..." modal, click Upload, "Resolve duplicates" modal
lists the duplicate) almost exactly — its own test even seeds the SAME
`sample.txt`/`sample.png` file-name pair for the identical reason (a
duplicate + a non-duplicate in one batch).

**Not `extend-existing`**: 1832's test diverges at the button click (Cancel)
and its entire remaining assertion chain proves the OPPOSITE outcome of this
case (Cancel: nothing uploads, count unchanged; Skip: the non-duplicate DOES
upload, a success toast appears, count increases by one). Splicing a
Skip-branch assertion chain into 1832's Cancel-branch test isn't a "gap
assertion" append — it's a second, independently-outcomed test. Per
`test-case-analysis` SKILL.md § Classify findings boundary guidance, this is
`ready-for-automation`: a NEW test method, reusing 1832's established
page-object methods/fixtures/file-naming convention for speed (see
`_surface.md`-style reuse — the setup steps below are copied verbatim from
1832's proven pattern, not re-derived).

**Cluster note (differs in STEPS from siblings):** shares the setup prefix
with ELITEA-1828/1831 but diverges into a different button (Skip) and a
different final-state assertion chain (non-duplicate uploads, duplicate
skipped with metadata unchanged) — own AFS, not a family AFS.
`family_afs: false`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing `sample.txt` but **not** containing `sample.png`.
  Same "case-text placeholder bucket name" finding as ELITEA-1832/1828 —
  use the `artifact_bucket` fixture (fresh-per-test bucket), not a literal
  `bucket-1`.
- The current total file count in that bucket is noted before the upload
  attempt (baseline for the post-Skip count assertion) — `1` for a
  freshly-seeded bucket.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: `artifact_bucket` fixture (`automation/fixtures/data_fixtures.py:455`).
  **Known gotcha:** the fixture's teardown `delete_bucket()` 404s in this
  environment (tracked, `#636` /
  `.agents/memory/qa-engineer/artifact_bucket_fixture_delete_silently_fails_404.md`)
  — already wrapped in try/except-and-warn by the fixture; does not fail the
  test.
- **`sample.txt` (the duplicate seed file)**: seed via
  `ArtifactAPI.upload_file(bucket_name, "sample.txt", content, content_type="text/plain")`
  (`automation/api/client.py:1292`) before the real upload attempt, so it
  becomes both the baseline file-count target and the duplicate match.
  Capture its `lastModified`/`size` via `ArtifactAPI.get_file_metadata()`
  (`automation/api/client.py:1328`) immediately after seeding, for the
  post-Skip unchanged-timestamp assertion.
- **`sample.png` (the new, non-duplicate file)**: pytest `tmp_path`
  (project convention, confirmed via ELITEA-1832's test) — content
  irrelevant, only presence/name matters. A minimal valid-enough byte
  sequence is sufficient (confirmed live: the native file-chooser/upload
  endpoint does not validate PNG structure — a small placeholder byte
  string was accepted in this exploration run without error).

No `reuse-existing` fixture applies — same narrow-state reasoning as
ELITEA-1832's AFS (a bucket with exactly `sample.txt` present, `sample.png`
absent isn't safe to share across parallel/serial runs).

## Test Steps

1. Navigate to `${BASE_URL}/artifacts`.
   - **Verify**: Artifacts page loads (`artifacts-buckets-heading` visible).
2. Select the bucket containing `sample.txt` but NOT `sample.png`, via
   `navigate_to_bucket(bucket_name)`.
   - **Verify**: file table shows exactly `sample.txt`; `sample.png` absent.
3. Click the upload icon (`artifacts-upload-files-button`).
   - **Verify**: native file explorer opens immediately (confirmed live, same
     as ELITEA-1832/1828).
4. (Folded into step 3's verify — same observable, no separate action.)
5. Select both `sample.txt` (duplicate) and `sample.png` (new) in the
   file-picker and confirm.
   - **Verify**: confirmed live via the very next step's modal correctly
     reflecting both files pending.
6. Verify the "Upload files to ..." modal opens with the Path field
   pre-filled with the bucket name.
   - **Verify**: `get_upload_path_prefix_text()` contains the bucket name.
7. Click "Upload".
   - **Verify**: confirmed live — triggers duplicate detection, **zero
     network requests** (client-side diff, same mechanism as 1828/1832).
8. Verify the "Resolve duplicates" modal opens listing "sample.txt" as the
   duplicate file.
   - **Verify**: `get_resolve_duplicates_filenames()` returns
     `['sample.txt']` (only the actual duplicate is listed — `sample.png`
     never appears in this modal, confirmed live).
9. Click "Skip".
   - **Verify**: confirmed live — fires exactly ONE `PUT
     .../artifacts/s3/{bucket}/sample.png?project_id=...` request (the
     non-duplicate's upload) and **no** PUT for `sample.txt` — Skip uploads
     only the non-duplicate file, leaving the duplicate entirely untouched.
   - **New testid added this run**: `artifacts-resolve-duplicates-skip-button`
     (see § Concrete Handles) — no testid existed for this button before this
     cluster's analysis.
10. Verify a success notification is displayed: "Your file(s) have been
    successfully uploaded!"
    - **Verify**: confirmed live — `success_toast_message` (generic app-wide
      `toast-message` testid) shows this exact text after Skip.
11. Verify "sample.png" is listed in the file table as a newly uploaded file.
    - **Verify**: confirmed live — `file_exists("sample.png")` returns
      `True` after Skip.
12. Verify only one "sample.txt" entry exists in the file table (the
    original, not replaced).
    - **Verify**: confirmed live — the bucket's file listing
      (`ArtifactAPI.list_bucket_files()`) contains exactly one `sample.txt`
      key (no `sample (1).txt`/duplicate-suffixed variant), and the UI file
      table shows a single `sample.txt` row.
13. Verify the "Last update" timestamp for "sample.txt" has NOT changed.
    - **Verify (via API, not UI — same technique ELITEA-1832 established)**:
      the Artifacts file table has no UI-visible timestamp column
      (confirmed, same as 1832's finding); `ArtifactAPI.get_file_metadata()`'s
      `lastModified` field is byte-identical before and after the Skip
      action (confirmed live this run: unchanged across the Skip operation).

## Expected Results
- Clicking "Skip" uploads ONLY the non-duplicate file (`sample.png`) —
  exactly one PUT request fires, for `sample.png`; none for `sample.txt`.
- A success toast "Your file(s) have been successfully uploaded!" appears.
- `sample.png` appears in the file table.
- Exactly one `sample.txt` entry remains, with its original `lastModified`
  timestamp and size unchanged (confirmed via the S3 JSON listing endpoint —
  there is no UI-visible timestamp column).
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket has sample.txt, not sample.png | Precondition state exists | Test Data + Test Step 2 | Fresh bucket seeded with `sample.txt` only | asserted |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click bucket-1 | Bucket selected | Test Step 2 | File table shows only `sample.txt` | asserted |
| Step 3: Click upload icon | File explorer opens | Test Step 3 | File-chooser fires immediately | asserted |
| Step 4: Verify file explorer opens immediately | File explorer open | Test Step 3 (folded) | Same observable | asserted *(decomposed)* |
| Step 5: Select both files, click Open | Both files selected | Test Step 5 | Modal in step 6 reflects both pending | asserted |
| Step 6: Verify Upload modal, Path pre-filled | Modal open, Path = bucket name | Test Step 6 | `get_upload_path_prefix_text()` | asserted |
| Step 7: Click Upload | Duplicate detection triggered | Test Step 7 | Zero network requests (client-side) | asserted |
| Step 8: Verify Resolve-duplicates modal shows sample.txt | Modal lists sample.txt only | Test Step 8 | `get_resolve_duplicates_filenames()` == `['sample.txt']` | asserted |
| Step 9: Click Skip | Skip action completes | Test Step 9 | Exactly one PUT (sample.png), none for sample.txt | asserted |
| Step 10: Verify success notification | Toast shown | Test Step 10 | `success_toast_message` exact text | asserted |
| Step 11: Verify sample.png in file table | sample.png present | Test Step 11 | `file_exists("sample.png")` True | asserted |
| Step 12: Verify only one sample.txt entry | No duplicate row | Test Step 12 | `list_bucket_files()` has exactly one `sample.txt` key | asserted |
| Step 13: Verify sample.txt timestamp unchanged | lastModified preserved | Test Step 13 | `get_file_metadata()` `lastModified` identical before/after | asserted |
| Expected Final State: sample.png uploaded, sample.txt unchanged, one entry | Full-state composite | Test Steps 11–13 | Combination of presence/count/metadata checks | asserted |
| Pass criterion: "Non-duplicate uploaded; duplicate skipped, timestamp unchanged" | Composite pass bar | Test Steps 9–13 | Same evidence as above | asserted |

### Axis 2 — Observables asserted beyond the case
- **Network-level proof that Skip uploads exactly the non-duplicate file and
  nothing else** (exactly one PUT, for `sample.png`, zero for `sample.txt`)
  — *added: a network-level assertion is stronger evidence than a DOM-only
  "file appears in table" check, and directly proves Skip's semantics rather
  than inferring them from the final UI state alone.*
- **`sample.txt` size equality (not just `lastModified`)** — *added: guards
  against a silent content-preserving-but-metadata-touching regression that
  a timestamp-only check could miss.*
- **Console-message check** — *added: standard silent-error guard.*

## Cleanup
1. Bucket deletion via the `artifact_bucket` fixture's own teardown (best
   effort — known 404, see § Test Data gotcha; does not fail the test).
2. No other entities are created by this case.

## Concrete Handles (discovered during exploration)

**Locator policy note:** testid-only, no fallback ladder. The Skip button's
testid was added live during this cluster's analysis (same pattern ELITEA-1832
and this cluster's own ELITEA-1828 AFS established) — committed + pushed to
`automation/testids` (`EliteaAI/EliteaUI@918b8b22`).

| Element | testid | Status | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | |
| Upload files button (toolbar) | `artifacts-upload-files-button` | existing | |
| "Upload files to ..." modal + Path input + Upload button | `artifacts-upload-path-dialog` / `-input` / `-upload-button` | existing (ELITEA-1832) | |
| "Resolve duplicates" modal — entire dialog | `artifacts-resolve-duplicates-dialog` | existing (ELITEA-1832) | |
| "Resolve duplicates" modal — duplicate filename | `artifacts-resolve-duplicates-filename` | existing (ELITEA-1832) | |
| **"Resolve duplicates" modal — Skip button (this case's core element)** | `artifacts-resolve-duplicates-skip-button` | **added this run** (same commit as ELITEA-1828's) | on `DuplicateResolutionDialog.jsx`'s Skip `Button.BaseBtn`. `EliteaAI/EliteaUI@918b8b22`. |
| Success toast | `toast-message` (generic, app-wide) | existing elsewhere | ELITEA-1832 confirmed its ABSENCE on the Cancel path; **this case confirms its PRESENCE with the exact text "Your file(s) have been successfully uploaded!" on the Skip path** — both live-verified, not mutually exclusive (matches the note already in `artifacts_page.py`'s `success_toast_message` docstring, which anticipated exactly this). |
| File row (for count/presence checks) | `artifacts-file-row` | existing | |

## Network Behavior
- Clicking "Upload" (duplicate present): zero network requests (client-side
  diff), same as ELITEA-1828/1832.
- Clicking "Skip": fires exactly **one** `PUT
  {ELITEA_URL}/artifacts/s3/{bucket}/sample.png?project_id={id}` → `200 OK`.
  **No** PUT fires for `sample.txt` — confirmed live via
  `capture_requests_matching("artifacts")` filtered to PUT/POST methods
  around the Skip click.

## Known Defects Found During Exploration
None found. Live product behavior matches the case's expected behavior
exactly: Skip uploads only the non-duplicate file, shows the success toast,
and leaves the duplicate's content/metadata/count untouched.

## Blocked Steps
None blocking. Same environmental gotcha as ELITEA-1828/1832: the
`artifact_bucket` fixture's teardown 404s (tracked, `#636`) — does not fail
this test.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`)
  with:
  - `resolve_duplicates_skip_button = LocatorDescriptor(testid="artifacts-resolve-duplicates-skip-button")`
    (reuse the SAME class field ELITEA-1828's implementer adds — don't
    duplicate if that PR merges first; if this PR merges first, ELITEA-1828's
    implementer reuses this one)
  - `click_resolve_duplicates_skip_button()` — mirror
    `click_resolve_duplicates_cancel_button()`'s shape exactly (a plain
    `.click()`, no network wait wrapped in — the caller captures requests via
    `capture_requests_matching` around the click, same idiom ELITEA-1832
    already established for Cancel).
- Fixtures: `artifact_bucket`; `ArtifactAPI.upload_file()` +
  `get_file_metadata()` + `list_bucket_files()` (all already exist, added for
  ELITEA-1832).
- Test file: new file, e.g.
  `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_skip.py` —
  a NEW test class/method (see § Overlap check for why this isn't an edit to
  1832's file).
- Wait strategy: after clicking "Skip", wait on
  `wait_for_resolve_duplicates_dialog_closed()` (already exists) — the
  success toast and `sample.png` row appear shortly after; use
  Playwright's auto-retrying `expect()` on `file_exists`/toast visibility,
  not a fixed sleep.
