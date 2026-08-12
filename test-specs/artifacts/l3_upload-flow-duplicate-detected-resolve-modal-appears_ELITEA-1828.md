# Test Case: Upload Flow – Duplicate File Detected and Resolve Duplicates Modal Appears

## Metadata
- **TMS ID**: ELITEA-1828
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster dispatch with ELITEA-1829, ELITEA-1831)
- **Status**: ready-for-automation — case executed live end-to-end, all 10 case
  steps confirmed, no defects. Not `already-covered` and not `extend-existing`
  — see § Overlap check below.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py`
(`TestArtifactUploadDuplicateCancel`, ELITEA-1832, **merged to
`origin/automation/base`**, commit `9dcb2805`) already drives the IDENTICAL
setup/navigation/upload-trigger prefix this case needs: navigate to Artifacts
→ select bucket → click upload icon → native picker → "Upload files to ..."
modal (Path pre-filled) → click Upload → "Resolve duplicates" modal opens
listing the duplicate filename. Its own test asserts the modal opens and the
duplicate filename, then clicks **Cancel** and verifies the abort semantics
(zero network requests, bucket unchanged) — it does **not** assert the modal's
message text, and does **not** assert that Skip/Replace/Keep-both are present
(the covering AFS explicitly logs those three buttons as "implementer scope
call — NOT added", ELITEA-1832 AFS § Concrete Handles).

**Considered `extend-existing`** (targeting the merged 1832 spec) since the
setup/navigation/modal-open prefix is byte-identical. Rejected as a boundary
call (`test-case-analysis` SKILL.md § Classify findings): this case's own tail
NEVER clicks any action button — it stops at inspecting the already-open
modal — while 1832's existing test method's very next steps click Cancel and
assert the abort. Splicing this case's assertions into 1832's test would mean
either (a) truncating that test before its Cancel-click (destroying 1832's own
coverage) or (b) duplicating the entire setup into a second test method in the
same file — which is a fresh test method, not "appending gap assertions to an
existing test". That crosses into "near-rewrite" per the SKILL's own boundary
guidance, so this is `ready-for-automation` — a NEW test method that reuses
1832's page-object methods and fixtures for speed, not an edit to 1832's test.

**Cluster note (differs in STEPS from siblings, not just data):** ELITEA-1829
(click Skip) and ELITEA-1831 (click Keep-both) share this same setup/modal-open
prefix but diverge into different button clicks and different final-state
assertions — per `test-case-analysis` SKILL.md § Execute ("differ in steps →
one AFS per case"), this is emitted as its own AFS, not merged into a family
AFS with 1829/1831. `family_afs: false`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing a file named `sample.md`.
  **This bucket does not pre-exist as a stable fixture** — same finding as
  ELITEA-1832's AFS: `bucket-1` is a case-text placeholder, not a literal
  fixture name. Use the `artifact_bucket` fixture (fresh-per-test bucket).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: `artifact_bucket` fixture (`automation/fixtures/data_fixtures.py:455`)
  — function-scoped, creates a uniquely-named bucket via `ArtifactAPI.create_bucket()`.
  **Known gotcha (see § Blocked Steps / Automation Hints):** the fixture's own
  teardown `delete_bucket()` call 404s in this environment (tracked, `#636` /
  `.agents/memory/qa-engineer/artifact_bucket_fixture_delete_silently_fails_404.md`)
  — the fixture already wraps this in try/except-and-warn, so it does not fail
  the test; do not add a hard assertion on cleanup succeeding.
- **`sample.md` (the seed/duplicate file)**: seed into the fresh bucket via
  `ArtifactAPI.upload_file(bucket_name, "sample.md", content, content_type="text/markdown")`
  (`automation/api/client.py:1292`, added for ELITEA-1832, reused here)
  *before* the test's real action, so it becomes the duplicate-detection
  target. Content is irrelevant to the assertions.
- **Local `sample.md` for the file-picker**: pytest's `tmp_path` fixture
  (project convention, confirmed in ELITEA-1832's test and
  `test_chat_interface.py`) — same byte content as the seeded file (content
  match isn't required for duplicate detection, which is filename-based, but
  keeping them identical avoids an unrelated confound).

## Test Steps

1. Navigate to `${BASE_URL}/artifacts`.
   - **Verify**: Artifacts page loads (`artifacts-buckets-heading` visible).
2. Select the fresh precondition bucket via `navigate_to_bucket(bucket_name)`
   (direct URL nav, per the existing page-object docstring/precedent).
   - **Verify**: file table shows `sample.md`.
3. Click the upload icon (`artifacts-upload-files-button`).
   - **Verify**: confirmed live — the native file-picker/file-chooser modal
     state fires immediately (no loading delay), same as ELITEA-1832's
     confirmed behavior.
4. (Folded into step 3's verify — same observable; the case lists it as a
   separate step but there is nothing additional to check, same folding
   ELITEA-1832's AFS already applied.)
5. Select a local file named `sample.md` (same name as the existing file) and
   confirm.
   - **Verify**: confirmed live — the "Upload files to ..." modal opens next
     (step 6 folds this observable in).
6. Verify the "Upload files to ..." modal opens with the Path field
   pre-filled with the bucket name.
   - **Verify**: confirmed live — `get_upload_path_prefix_text()` contains
     the bucket name as a `{bucket_name}/` prefix.
7. Click "Upload".
   - **Verify**: confirmed live — triggers duplicate detection with **zero
     network requests** (client-side diff against the already-fetched bucket
     listing, same mechanism ELITEA-1832 already proved 2/2).
8. Verify the "Resolve duplicates" modal opens with the message: "This file
   already exists in this bucket. Choose how to handle duplicates."
   - **Verify**: confirmed live — exact byte-identical message text (this
     case has exactly ONE duplicate file, so the component's singular-form
     message renders: `DuplicateDialogContent.jsx`'s `label` useMemo produces
     `"This file already exists in this bucket. Choose how to handle
     duplicates."` when `duplicateFilenames.length === 1`, vs a plural
     `"{N} files already exist..."` form for multiple — confirmed by reading
     the component source). **New testid added this run** (see § Concrete
     Handles) — `artifacts-resolve-duplicates-message-text` — to assert this
     exact string directly rather than substring-matching the whole dialog's
     `text_content()`.
9. Verify the duplicate file name "sample.md" is listed in the modal.
   - **Verify**: confirmed live — `get_resolve_duplicates_filenames()`
     returns `['sample.md']`.
10. Verify the modal contains four buttons: "Cancel", "Skip", "Replace",
    "Keep both".
    - **Verify**: confirmed live — all four buttons present with the exact
      labels, PLUS a 5th unnamed icon-only button (the dialog's own [X] close
      control, `onClose`-wired, out of this case's scope — the case's own
      pass bar only names the four action buttons). **New testids added this
      run** for Skip/Replace/Keep-both (Cancel already had one from ELITEA-1832)
      — see § Concrete Handles.

## Expected Results
- After selecting a same-named file and clicking Upload, the "Resolve
  duplicates" modal opens (client-side detection, zero network requests).
- Modal message text is exactly "This file already exists in this bucket.
  Choose how to handle duplicates." (singular form — one duplicate file).
- The duplicate filename "sample.md" is listed.
- All four action buttons (Cancel, Skip, Replace, Keep both) are present and
  visible.
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains sample.md | Precondition state exists | Test Data + Test Step 2 | Fresh bucket seeded with `sample.md`, confirmed via `file_exists` | asserted |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click bucket-1 (has sample.md) | Bucket selected, sample.md visible | Test Step 2 | File table shows `sample.md` | asserted |
| Step 3: Click upload icon | File explorer opens | Test Step 3 | `browser`'s file-chooser modal-state fires immediately (confirmed live) | asserted |
| Step 4: Verify file explorer opens immediately | File explorer open | Test Step 3 (folded) | Same observable as step 3 | asserted *(decomposed — no separate action)* |
| Step 5: Select sample.md, click Open | "Upload files to ..." modal opens | Test Step 5 | Modal visible next step | asserted |
| Step 6: Verify Upload modal, Path pre-filled | Modal open, Path = bucket name | Test Step 6 | `get_upload_path_prefix_text()` contains bucket name | asserted |
| Step 7: Click Upload | Duplicate detection triggered | Test Step 7 | Confirmed **client-side** (zero network requests) via `capture_requests_matching` | asserted |
| Step 8: Verify Resolve-duplicates modal + message | Modal + exact message text | Test Step 8 | New testid `artifacts-resolve-duplicates-message-text`, exact string match | asserted |
| Step 9: Verify duplicate filename listed | "sample.md" shown | Test Step 9 | `get_resolve_duplicates_filenames()` == `['sample.md']` | asserted |
| Step 10: Verify all 4 buttons present | Cancel/Skip/Replace/Keep both visible | Test Step 10 | New testids for Skip/Replace/Keep-both + existing Cancel testid, all `.is_visible()` | asserted |
| Expected Final State: modal shown with correct message/filename/buttons | Full-state composite | Test Steps 8–10 | Combination of message/filename/button assertions | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | Console checked clean | asserted |

### Axis 2 — Observables asserted beyond the case
- **Client-side-only duplicate detection (zero network requests on the
  "Upload" click)** — *added: same reasoning ELITEA-1832 already established
  — this is stronger evidence than a DOM-only "modal appeared" check, and
  keeps this test's own proof independent of trusting the covering test.*
- **Console-message check** — *added: standard silent-error guard.*
- **Exact singular-form message text (not just substring/plural-agnostic
  match)** — *added: confirmed live via `DuplicateDialogContent.jsx` source
  that the message wording depends on `duplicateFilenames.length` (singular
  vs plural "N files"); this case has exactly one duplicate, so asserting the
  literal singular string is a real product-contract check, not an
  arbitrary strengthening.*

## Cleanup
1. Bucket deletion via the `artifact_bucket` fixture's own teardown (best
   effort — known 404, see § Test Data gotcha; does not fail the test).
2. No other entities are created by this case.

## Concrete Handles (discovered during exploration)

**Locator policy note:** testid-only, no fallback ladder (`.agents/testing.md`
§ Locator policy). Handles below marked "added" were added live during this
analysis run (same "analyst adds testids during exploration" pattern
ELITEA-1832's own AFS established) — committed + pushed to `automation/testids`
(`EliteaAI/EliteaUI@918b8b22`).

| Element | testid | Status | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | |
| Upload files button (toolbar) | `artifacts-upload-files-button` | existing | |
| "Upload files to ..." modal | `artifacts-upload-path-dialog` | existing (ELITEA-1832) | |
| "Upload files to ..." modal — Path input | `artifacts-upload-path-input` | existing (ELITEA-1832) | |
| "Upload files to ..." modal — Upload button | `artifacts-upload-path-upload-button` | existing (ELITEA-1832) | |
| "Resolve duplicates" modal — entire dialog | `artifacts-resolve-duplicates-dialog` | existing (ELITEA-1832) | |
| "Resolve duplicates" modal — duplicate filename | `artifacts-resolve-duplicates-filename` | existing (ELITEA-1832) | |
| **"Resolve duplicates" modal — message text** | `artifacts-resolve-duplicates-message-text` | **added this run** | on `DuplicateDialogContent.jsx`'s `label` `<Typography>` — page-local/single-consumer, hardcoded directly in JSX, no caller-prop threading needed. `EliteaAI/EliteaUI@918b8b22`. |
| "Resolve duplicates" modal — Cancel button | `artifacts-resolve-duplicates-cancel-button` | existing (ELITEA-1832) | this case only asserts visibility, never clicks it |
| **"Resolve duplicates" modal — Skip button** | `artifacts-resolve-duplicates-skip-button` | **added this run** | on `DuplicateResolutionDialog.jsx`'s Skip `Button.BaseBtn`. This case only asserts visibility (never clicks — ELITEA-1829 is the click-Skip case). `EliteaAI/EliteaUI@918b8b22`. |
| **"Resolve duplicates" modal — Replace button** | `artifacts-resolve-duplicates-replace-button` | **added this run** | Same file/mechanism. Visibility-only in ALL THREE cluster cases (1828/1829/1831) — no case in this cluster clicks Replace; flagged as a follow-up for a future case exercising it. `EliteaAI/EliteaUI@918b8b22`. |
| **"Resolve duplicates" modal — Keep both button** | `artifacts-resolve-duplicates-keep-both-button` | **added this run** | Same file/mechanism. This case only asserts visibility (never clicks — ELITEA-1831 is the click-Keep-both case). `EliteaAI/EliteaUI@918b8b22`. |
| "Resolve duplicates" modal — unnamed [X] close button | none | **out of scope, not added** | 5th button in the dialog (`onClose` icon button), not one of the case's 4 named buttons — the case's own pass bar doesn't mention it; left untouched per the testid-scope ruling. |

## Network Behavior
- Clicking "Upload" when a duplicate is present fires **zero** network
  requests (confirmed live via `capture_requests_matching("artifacts")`,
  same client-side mechanism ELITEA-1832 already proved 2/2).

## Known Defects Found During Exploration
None found. Live product behavior matches the case's expected behavior
exactly: the "Resolve duplicates" modal opens with the exact singular-form
message, the duplicate filename, and all four named action buttons visible.

## Blocked Steps
None blocking. One environmental gotcha, not specific to this case: the
`artifact_bucket` fixture's teardown `delete_bucket()` call 404s in this
environment (tracked defect, `.agents/memory/qa-engineer/
artifact_bucket_fixture_delete_silently_fails_404.md`, informs issue `#636`)
— already wrapped in try/except by the fixture, does not fail this or any
other artifacts test; do not assert on cleanup success.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`)
  with visibility-only accessors for the three new button testids (no new
  click methods needed for THIS case — e.g.
  `resolve_duplicates_skip_button = LocatorDescriptor(testid="artifacts-resolve-duplicates-skip-button")`,
  same shape for Replace/Keep-both, plus
  `resolve_duplicates_message_text = LocatorDescriptor(testid="artifacts-resolve-duplicates-message-text")`).
  ELITEA-1829/1831 will add the corresponding CLICK methods for Skip/Keep-both
  respectively — don't duplicate those descriptors, reuse the same class
  fields this case adds.
- Fixtures: `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`);
  `ArtifactAPI.upload_file()` (`automation/api/client.py:1292`) to seed
  `sample.md`.
- Test file: new file, e.g.
  `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_detected_modal.py`
  — a NEW test class/method, not an edit to
  `test_artifacts_upload_duplicate_cancel.py` (see § Overlap check).
- Wait strategy: after clicking "Upload", wait on
  `wait_for_resolve_duplicates_dialog()` (condition-based, already exists) —
  no network response to wait on (confirmed zero requests fire).
