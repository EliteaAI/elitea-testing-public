# Test Case: Upload Flow – Duplicate Handling: Keep Both Saves Both Files with copy Suffix

## Metadata
- **TMS ID**: ELITEA-1831
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster dispatch with ELITEA-1828, ELITEA-1829)
- **Status**: ready-for-automation — case executed live end-to-end, all 12 case
  steps confirmed (with a case-text CLARIFICATION on the exact copy-naming
  format — see below), no defects. Not `already-covered` and not
  `extend-existing` — see § Overlap check below.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py`
(`TestArtifactUploadDuplicateCancel`, ELITEA-1832, **merged to
`origin/automation/base`**, commit `9dcb2805`) shares this case's setup/
navigation/upload-trigger prefix (single duplicate file, "Upload files to
..." modal, click Upload, "Resolve duplicates" modal lists `sample.txt`)
almost exactly.

**Not `extend-existing`**: 1832's test diverges at the button click (Cancel)
and its remaining assertion chain proves the opposite outcome (Cancel: bucket
unchanged, one file; Keep both: bucket gains a second, renamed file with a
distinct timestamp). Same boundary-call reasoning as ELITEA-1828/1829's AFS —
this is `ready-for-automation`, a NEW test method reusing 1832's page-object
methods/fixtures for speed.

**Cluster note (differs in STEPS from siblings):** shares the setup prefix
with ELITEA-1828/1829 but diverges into a different button (Keep both) and a
different final-state assertion chain (two files, one renamed with a "copy"
suffix, both with distinct timestamps) — own AFS, not a family AFS.
`family_afs: false`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing `sample.txt`.
  Same "case-text placeholder bucket name" finding as ELITEA-1828/1829/1832
  — use the `artifact_bucket` fixture, not a literal `bucket-1`.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: `artifact_bucket` fixture (`automation/fixtures/data_fixtures.py:455`).
  **Known gotcha:** the fixture's teardown `delete_bucket()` 404s in this
  environment (tracked, `#636` /
  `.agents/memory/qa-engineer/artifact_bucket_fixture_delete_silently_fails_404.md`)
  — already wrapped in try/except-and-warn; does not fail the test.
- **`sample.txt` (the duplicate seed file)**: seed via
  `ArtifactAPI.upload_file(bucket_name, "sample.txt", content, content_type="text/plain")`
  before the real upload attempt. Capture its `lastModified`/`size` via
  `ArtifactAPI.get_file_metadata()` immediately after seeding.
- **Local `sample.txt` for the file-picker**: pytest `tmp_path`, same content
  as the seeded file (content irrelevant to the assertions).

## Test Steps

1. Navigate to `${BASE_URL}/artifacts`.
   - **Verify**: Artifacts page loads (`artifacts-buckets-heading` visible).
2. Select the bucket containing `sample.txt`, via `navigate_to_bucket(bucket_name)`.
   - **Verify**: file table shows `sample.txt`.
3. Click the upload icon (`artifacts-upload-files-button`).
   - **Verify**: native file explorer opens immediately (confirmed live, same
     as ELITEA-1828/1829/1832).
4. (Folded into step 3's verify — same observable, no separate action.)
5. Select `sample.txt` (same name as the existing file) and confirm.
   - **Verify**: confirmed live via the next step's modal.
6. Verify the "Upload files to ..." modal opens with the Path field
   pre-filled with the bucket name.
   - **Verify**: `get_upload_path_prefix_text()` contains the bucket name.
7. Click "Upload".
   - **Verify**: confirmed live — triggers duplicate detection, **zero
     network requests** (client-side diff, same mechanism as siblings).
8. Verify the "Resolve duplicates" modal opens listing "sample.txt" as the
   duplicate file.
   - **Verify**: `get_resolve_duplicates_filenames()` returns
     `['sample.txt']`.
9. Click "Keep both".
   - **Verify**: confirmed live — fires exactly ONE `PUT
     .../artifacts/s3/{bucket}/{copy_name}?project_id=...` request, where
     `{copy_name}` is the RENAMED copy (see step 11's CLARIFICATION on the
     exact naming format) — **no** PUT for the literal `sample.txt` path
     (the original is never re-uploaded/overwritten).
   - **New testid added this run**: `artifacts-resolve-duplicates-keep-both-button`
     (see § Concrete Handles) — no testid existed for this button before this
     cluster's analysis.
10. Verify a success notification is displayed: "Your file(s) have been
    successfully uploaded!"
    - **Verify**: confirmed live — `success_toast_message` shows this exact
      text after Keep both (same toast, same text ELITEA-1829's Skip path
      also confirmed — the toast wording is upload-outcome-generic, not
      per-button).
11. Verify the file table contains two entries: the original "sample.txt"
    and a new entry with "copy" added to the name (e.g. "sample-copy.txt").
    - **Verify — CLARIFICATION on exact naming format (reverse-masking
      guard, `.agents/testing.md`/`test-case-analysis` SKILL.md § Classify
      findings)**: confirmed live the app does NOT produce `sample-copy.txt`
      (hyphenated, no space) as the case text's example suggests. The actual
      renamed copy is **`sample - Copy.txt`** — space, hyphen, space,
      capitalized "Copy", extension preserved (`{baseName} - Copy{extension}`).
      The case text itself hedges this with "(or similar with 'copy' in
      name)", so this is NOT a product defect — it's the case-text's
      illustrative example being imprecise about the exact separator/casing.
      Live product behavior is correct and internally consistent; the
      assertion in automation should match the pattern
      `f"{base} - Copy{ext}"`, not a literal hardcoded `sample-copy.txt`
      string. Filed as a case-text CLARIFICATION (see § Known Defects).
    - Both `sample.txt` and `sample - Copy.txt` are present, confirmed via
      `ArtifactAPI.list_bucket_files()` returning both keys.
12. Verify both files have their own distinct "Last update" timestamps.
    - **Verify (via API, not UI — same technique as 1829/1832)**: no
      UI-visible timestamp column exists; `ArtifactAPI.get_file_metadata()`
      for both keys shows DIFFERENT `lastModified` values (confirmed live
      this run: the original's timestamp is from the seed upload, the copy's
      is ~26s later from the Keep-both action — genuinely distinct, not a
      flaky near-tie).

## Expected Results
- Clicking "Keep both" uploads the new file under a renamed key —
  **confirmed live format: `{baseName} - Copy{extension}`** (e.g.
  `sample - Copy.txt`, NOT the case text's literal `sample-copy.txt`
  example) — exactly one PUT request fires, for the renamed copy; none for
  the original `sample.txt` path.
- A success toast "Your file(s) have been successfully uploaded!" appears.
- Both the original `sample.txt` and the renamed copy exist in the bucket's
  listing, each with its own distinct `lastModified` timestamp.
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket has sample.txt | Precondition state exists | Test Data + Test Step 2 | Fresh bucket seeded with `sample.txt` | asserted |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click bucket-1 | Bucket selected | Test Step 2 | File table shows `sample.txt` | asserted |
| Step 3: Click upload icon | File explorer opens | Test Step 3 | File-chooser fires immediately | asserted |
| Step 4: Verify file explorer opens immediately | File explorer open | Test Step 3 (folded) | Same observable | asserted *(decomposed)* |
| Step 5: Select sample.txt, click Open | "Upload files to ..." modal opens | Test Step 5 | Modal visible next step | asserted |
| Step 6: Verify Upload modal, Path pre-filled | Modal open, Path = bucket name | Test Step 6 | `get_upload_path_prefix_text()` | asserted |
| Step 7: Click Upload | Duplicate detection triggered | Test Step 7 | Zero network requests (client-side) | asserted |
| Step 8: Verify Resolve-duplicates modal shows sample.txt | Modal lists sample.txt | Test Step 8 | `get_resolve_duplicates_filenames()` == `['sample.txt']` | asserted |
| Step 9: Click Keep both | Keep-both action completes | Test Step 9 | Exactly one PUT for the renamed copy key, none for `sample.txt` | asserted |
| Step 10: Verify success notification | Toast shown | Test Step 10 | `success_toast_message` exact text | asserted |
| Step 11: Verify two entries, copy has "copy" in name | Original + renamed copy present | Test Step 11 | `list_bucket_files()` has both keys | **clarification** *(exact format `sample - Copy.txt`, not the case text's `sample-copy.txt` example — see step 11 note)* |
| Step 12: Verify distinct timestamps | Different lastModified per file | Test Step 12 | `get_file_metadata()` for both keys, values differ | asserted |
| Expected Final State: both files exist, copy has "copy" in name, distinct timestamps | Full-state composite | Test Steps 11–12 | Combination of listing + metadata checks | asserted |
| Pass criterion: "Two entries with distinct timestamps; copy has copy in name" | Composite pass bar | Test Steps 9–12 | Same evidence as above | asserted |

### Axis 2 — Observables asserted beyond the case
- **Network-level proof that Keep-both uploads exactly ONE new object, under
  the renamed key, and never re-touches the original `sample.txt` path** —
  *added: network-level assertion is stronger evidence than a DOM-only
  "two rows exist" check, and directly proves the rename semantics (a
  same-path overwrite would also produce "two rows" transiently if the UI
  were buggy, but the network layer disambiguates).*
- **Console-message check** — *added: standard silent-error guard.*

## Cleanup
1. Bucket deletion via the `artifact_bucket` fixture's own teardown (best
   effort — known 404, see § Test Data gotcha; does not fail the test).
2. No other entities are created by this case.

## Concrete Handles (discovered during exploration)

**Locator policy note:** testid-only, no fallback ladder. The Keep-both
button's testid was added live during this cluster's analysis (same pattern
as ELITEA-1828/1829's) — committed + pushed to `automation/testids`
(`EliteaAI/EliteaUI@918b8b22`).

| Element | testid | Status | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | |
| Upload files button (toolbar) | `artifacts-upload-files-button` | existing | |
| "Upload files to ..." modal + Path input + Upload button | `artifacts-upload-path-dialog` / `-input` / `-upload-button` | existing (ELITEA-1832) | |
| "Resolve duplicates" modal — entire dialog | `artifacts-resolve-duplicates-dialog` | existing (ELITEA-1832) | |
| "Resolve duplicates" modal — duplicate filename | `artifacts-resolve-duplicates-filename` | existing (ELITEA-1832) | |
| **"Resolve duplicates" modal — Keep both button (this case's core element)** | `artifacts-resolve-duplicates-keep-both-button` | **added this run** (same commit as ELITEA-1828/1829's) | on `DuplicateResolutionDialog.jsx`'s Keep-both `Button.BaseBtn`. `EliteaAI/EliteaUI@918b8b22`. |
| Success toast | `toast-message` (generic, app-wide) | existing elsewhere | Confirmed PRESENT with the exact text "Your file(s) have been successfully uploaded!" on the Keep-both path — same wording ELITEA-1829's Skip path also confirmed. |

## Network Behavior
- Clicking "Upload" (duplicate present): zero network requests (client-side
  diff), same as siblings.
- Clicking "Keep both": fires exactly **one** `PUT
  {ELITEA_URL}/artifacts/s3/{bucket}/sample%20-%20Copy.txt?project_id={id}`
  (URL-encoded space) → `200 OK`. **No** PUT fires for the literal
  `sample.txt` key — confirmed live via `capture_requests_matching("artifacts")`
  filtered to PUT/POST methods around the Keep-both click.

## Known Defects Found During Exploration
None found (no product defect). One **case-text CLARIFICATION**: the case's
own Test Data table names `sample-copy.txt` as "the expected copy name...(or
similar with 'copy' in name)" — the hedge already signals the author wasn't
asserting an exact literal string. Live product behavior renames to
`{baseName} - Copy{extension}` (e.g. `sample - Copy.txt` — space, hyphen,
space, capitalized "Copy"), which the case's own hedge already accommodates.
Per `.agents/profile.md` § Bug filing this is filed as a lightweight
CLARIFICATION note (not a `bug`), so the TMS case's Test Data table can be
updated to the exact observed format for future readers — filed as
[EliteaAI/elitea-testing-public#1102](https://github.com/EliteaAI/elitea-testing-public/issues/1102)
(label `question`, per the #40 pattern).

## Blocked Steps
None blocking. Same environmental gotcha as ELITEA-1828/1829/1832: the
`artifact_bucket` fixture's teardown 404s (tracked, `#636`) — does not fail
this test.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`)
  with:
  - `resolve_duplicates_keep_both_button = LocatorDescriptor(testid="artifacts-resolve-duplicates-keep-both-button")`
    (reuse the SAME class field ELITEA-1828's implementer adds if that PR
    merges first)
  - `click_resolve_duplicates_keep_both_button()` — mirror
    `click_resolve_duplicates_cancel_button()`'s shape (plain `.click()`,
    caller wraps `capture_requests_matching` around it).
- Fixtures: `artifact_bucket`; `ArtifactAPI.upload_file()` +
  `get_file_metadata()` + `list_bucket_files()` (all already exist).
- Test file: new file, e.g.
  `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_keep_both.py`
  — a NEW test class/method (see § Overlap check).
- **Copy-name assertion**: do NOT hardcode `"sample-copy.txt"` — assert the
  pattern `f"{base_name} - Copy{extension}"` (confirmed live format), or
  read back whichever of the two non-`sample.txt` keys
  `list_bucket_files()` returns and assert it CONTAINS `"copy"`
  case-insensitively plus preserves the original extension, per the case's
  own hedged wording.
- Wait strategy: after clicking "Keep both", wait on
  `wait_for_resolve_duplicates_dialog_closed()` (already exists); poll for
  the second file-table row via Playwright's auto-retrying `expect()`, not a
  fixed sleep.
