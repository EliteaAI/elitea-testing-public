# Test Case: Upload Flow – Duplicate Handling: Cancel Stops Entire Upload Including Non-Duplicate Files

## Metadata
- **TMS ID**: ELITEA-1832
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: ready-for-automation — case executed end-to-end twice
  (2/2 identical runs), all 15 case steps pass, no defects. Not already-covered
  and not extend-existing — see § Overlap check below.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_multi_file.py`
(`TestArtifactMultiFileDownload`, ELITEA-1327) and `automation/pages/artifacts_page.py`
were read before this run. That test exercises: an **agent** creating multiple
files via the Artifact toolkit in one tool call, then verifying all files are
visible/downloadable at bucket root and in a sub-folder. It never drives the
**manual upload** UI (no `upload_files_button` interaction anywhere in that
file), never encounters a duplicate filename, and never touches the
"Resolve duplicates" modal. `ArtifactsPage` has bucket/file-list/download
helpers (`navigate_to_bucket`, `file_exists`, `get_file_names`, `download_file`,
`navigate_into_folder`) but **no upload method at all** — confirmed by reading
the full file (`automation/pages/artifacts_page.py`, 316 lines).

Verdict: **zero behavioral overlap** with ELITEA-1832 (manual multi-file
upload → client-side duplicate detection → "Resolve duplicates" modal →
Cancel semantics). Fresh scenario, `ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing `sample.txt` but **not** containing `sample.png`.
  **This bucket does not pre-exist as a stable fixture** — see § Test Data.
  Confirmed live: searched all 5 available projects (`Private` 73 buckets,
  `UI Testing` 0, `Elitea Testing Team` 6, `Elitea Development` 16,
  `Bugs & Features` 140 — including the in-app "Search buckets" feature for
  the literal string `bucket-1`, which returned "No buckets found") — no
  bucket named `bucket-1` (or any bucket already shaped like this
  precondition) exists anywhere. The case's `bucket-1` name is a **case-text
  placeholder**, not a literal fixture name to reuse.
- The current total file count in that bucket is noted before the upload
  attempt (baseline for the step-14 unchanged-count assertion).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture
  (`automation/fixtures/data_fixtures.py:455`) — function-scoped, creates a
  uniquely-named bucket via `ArtifactAPI.create_bucket()`
  (`automation/api/client.py:1178`) and deletes it via
  `ArtifactAPI.delete_bucket()` (`automation/api/client.py:1205`) in teardown.
  Do **not** hardcode the literal name `bucket-1` — it does not exist and the
  project's existing convention (this fixture, plus ~65 pre-existing
  `autotest-*` buckets observed live in the `Private` project from prior
  runs) is fresh-per-test bucket names.
- **`sample.txt` (the duplicate seed file)**: must be uploaded into the fresh
  bucket *before* the test's real action, so it becomes step 3's "current
  file count" baseline and step 9's duplicate match. `ArtifactAPI` currently
  has **no upload method** — confirmed by reading `automation/api/client.py`
  class `ArtifactAPI` (lines 1143–1270): only `create_bucket`, `delete_bucket`,
  `list_bucket_files`, `get_file` exist. Two viable approaches, implementer's
  judgment call (does not block `ready-for-automation`):
  1. **Recommended** — add a small `ArtifactAPI.upload_file(bucket_name,
     file_key, content, content_type=None)` helper that does a `requests`
     `PUT` to the same endpoint the browser itself uses (confirmed live via
     network capture during this run):
     `PUT {ELITEA_URL}/artifacts/s3/{bucket_name}/{file_key}?project_id={project_id}`
     → `200 OK`, raw body = file bytes. This seeds the precondition in one
     fast HTTP call, no browser dependency, and keeps `list_bucket_files`'s
     existing shape untouched.
  2. Alternative — perform the seed upload through the UI itself (drive
     `upload_files_button` once with only `sample.txt` selected, confirm it
     lands, *then* start the real multi-file (`sample.txt` + `sample.png`)
     upload that triggers the duplicate flow). Slower (two upload round-trips
     through the browser) but requires no API-client change.
- **`sample.png` (the new, non-duplicate file)**: a small valid PNG, content
  irrelevant to the assertions (only presence/name/duplicate-detection
  matters). **Implementer Phase 2 finding — amends this section:** the
  project's ACTUAL convention for upload-test files is pytest's `tmp_path`
  fixture (files written on the fly per-test), not checked-in static
  fixtures — confirmed by reading `test_chat_interface.py::test_attach_files_button_sends_file_with_message`
  (`tmp_path / "test_automation_file.txt"`, `.write_text(...)`) and
  `test_support_assistant_smoke.py` (same pattern). No
  `automation/fixtures/files/` directory exists anywhere in the repo. Use
  `tmp_path` for both `sample.txt` and `sample.png` (the PNG built in-memory
  as minimal valid bytes via `struct`/`zlib`), not a new checked-in fixtures
  directory.

No `reuse-existing` fixture applies — this case requires a bucket in a very
specific, narrow state (`sample.txt` present, `sample.png` absent) that isn't
safe to share across parallel/serial test runs without risking cross-test
pollution (another test's `sample.png` upload would break this test's
precondition). Fresh-per-test is the only safe strategy here, consistent with
the project's `pytest-xdist`-aware "data-dependent tests: serial mode" note
in `.agents/testing.md` § Test data strategy.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts`.
   - **Verify**: Artifacts page loads — left panel shows "Buckets" heading
     (`artifacts-buckets-heading`), right panel shows the file-list toolbar.
2. Select the fresh precondition bucket (via `navigate_to_bucket(bucket_name)`
   — direct URL navigation `?bucket={bucket_name}` is more reliable than
   clicking the left-panel list item, per the existing page-object docstring).
   - **Verify**: right-panel header shows the bucket name; file table shows
     exactly `sample.txt`.
3. Note the current total file count (`1` in this run, freshly seeded).
4. Click the upload icon in the toolbar (`artifacts-upload-files-button`).
   - **Verify**: the native file-picker/file-chooser opens immediately
     (confirmed live: `browser_file_upload`'s modal-state fires the instant
     the button is clicked — no loading delay, no intermediate spinner).
5. (Folded into step 4's verify — same observable, the case lists it as a
   separate step but there is nothing additional to check.)
6. Select both `sample.txt` (the duplicate) and `sample.png` (the new file)
   in the file-picker and confirm/open.
   - **Verify**: both files are accepted — confirmed live via the very next
     step's modal correctly listing both a Path field state.
7. Verify the "Upload files to ..." modal opens with the Path field
   pre-filled with the bucket name.
   - **Verify**: confirmed live — modal title "Upload files to ...", Path
     input shows `{bucket_name}/` as a read-only prefix segment before an
     editable textbox (see § Concrete Handles — this modal currently has
     **zero** `data-testid` attributes anywhere in its DOM).
8. Click "Upload".
   - **Verify**: triggers duplicate detection — confirmed live this is a
     **client-side, no-network-round-trip check**: `browser_network_requests`
     filtered on `artifacts` showed no new request at all between clicking
     "Upload" and the "Resolve duplicates" modal appearing (the frontend
     already holds the bucket's current file listing in memory from the
     `GET /artifacts/s3/{bucket}?project_id=...&format=json` call made when
     the bucket was opened in step 2, and diffs the selected filenames
     against it locally).
9. Verify the "Resolve duplicates" modal opens listing `sample.txt` as the
   duplicate file.
   - **Verify**: confirmed live — modal title "Resolve duplicates", body text
     "This file already exists in this bucket. Choose how to handle
     duplicates.", and the duplicate filename rendered split across two
     spans (`sample` / `.txt`). Four action buttons: Cancel, Skip, Replace,
     Keep both (this case only exercises Cancel; Skip/Replace/Keep-both are
     out of this case's scope — see § Coverage Map Axis 1 disposition).
10. Click "Cancel".
    - **Verify**: confirmed live, 2/2 runs — no network request fires at all
      (neither an upload PUT for `sample.png` nor for `sample.txt`); the
      dialog closes; the file table and left-panel bucket-file-count are
      unchanged.
11. Verify the "Resolve duplicates" modal is closed.
    - **Verify**: confirmed live — `[role="dialog"]` no longer present in the
      accessibility tree/DOM immediately after the click.
12. Verify NO success notification is displayed.
    - **Verify (partial — see caveat)**: no toast/snackbar/alert element was
      present in the DOM at the point this was checked (searched
      `[data-testid]` for `toast`/`snackbar`/`success`/`notif` substrings —
      zero matches; also no `[role="alert"]` / `.MuiAlert-root` /
      `.MuiSnackbar-root` present). **Caveat**: this app does have a
      generic, reusable success-toast testid used elsewhere
      (`toast-message`, seen in `automation/pages/skills_list_page.py:59` and
      `automation/pages/skill_detail_page.py:96`) which is documented
      elsewhere in the codebase as auto-dismissing quickly
      (`automation/pages/mcp_form_page.py:931` comment). During this
      exploration a **separate, successful, non-duplicate** single-file
      upload (`throwaway.txt`, used only to probe this behavior, deleted
      afterward) also showed no toast by the time a snapshot was taken —
      consistent with either (a) no toast is shown for artifact uploads at
      all, or (b) it auto-dismissed before the snapshot fired. The
      implementer should assert absence with a short bounded wait
      (`page.wait_for_timeout` is discouraged project-wide — instead assert
      `expect(locator_for(toast-message-if-any)).to_have_count(0)` polled for
      ~1–2s) rather than a single instantaneous DOM check, to make this
      assertion robust regardless of which of (a)/(b) is true.
13. Verify `sample.png` is NOT listed in the file table.
    - **Verify**: confirmed live — file table shows only `sample.txt` (67 B),
      `"1 - 1 of 1"` pagination label.
14. Verify the total number of files in the bucket remains the same as noted
    in step 3.
    - **Verify**: confirmed live — count unchanged (`1`, matching step 3's
      baseline) both via the UI pagination label and via the underlying
      `GET /artifacts/s3/{bucket}?project_id=...&format=json` JSON response
      (`"keyCount": 1`).
15. Verify the original `sample.txt` is unchanged with its original
    "Last update" timestamp.
    - **Verify (via API, not UI)**: the Artifacts file table has **no visible
      "Last update"/timestamp column** in this UI (columns are Name / Type /
      Size / Actions only — confirmed via full-table snapshot and via the
      per-file dot-menu, which only offers Download/Delete, no
      Properties/Details view). The underlying data **is** available: the
      same `GET /artifacts/s3/{bucket}?project_id=...&format=json` endpoint
      the frontend already calls returns a `lastModified` ISO-8601 field per
      file (confirmed live: `"lastModified": "2026-07-18T23:53:14.000Z"`,
      unchanged byte-for-byte before and after the cancelled upload attempt,
      across 2/2 runs). `ArtifactAPI.list_bucket_files()`
      (`automation/api/client.py:1226`) currently **drops** this field
      (`return [item["key"] for item in contents if "key" in item]`) — the
      implementer needs either a small enhancement to return full per-file
      metadata dicts (`key`, `lastModified`, `size`), or a new
      `get_file_metadata(bucket_name, file_key)` method, to assert this step.
      This is the load-bearing technique for step 15 — there is no UI-only
      way to verify it.

## Expected Results
- Clicking "Cancel" in the "Resolve duplicates" modal aborts the entire
  upload operation — **zero network requests fire**, including for the
  non-duplicate `sample.png`.
- No success notification/toast is shown.
- `sample.png` never appears in the bucket's file list.
- The bucket's total file count is identical before and after the cancelled
  attempt.
- `sample.txt`'s content, size, and `lastModified` timestamp (via the S3
  JSON listing endpoint) are byte-identical before and after.
- No console errors during the flow (confirmed: 0 new errors attributable to
  this flow across both runs — the only console errors seen during this
  session were leftovers from unrelated project-switching exploration
  earlier in the same browser context, not from the case's own steps).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains `sample.txt`, not `sample.png` | Precondition state exists | Test Data + Test Step 2 | Fresh bucket seeded with `sample.txt` only, confirmed via file table + JSON listing (`keyCount: 1`) | asserted |
| Precondition: note current total file count | Baseline recorded | Test Step 3 | `1` (freshly seeded bucket) | asserted |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | `artifacts-buckets-heading` visible | asserted |
| Step 2: Click bucket-1 (has sample.txt, not sample.png) | Bucket selected | Test Step 2 | Right panel shows bucket name + file table | asserted |
| Step 3: Note current file count | Count recorded | Test Step 3 | `1` | asserted |
| Step 4: Click upload icon | File explorer opens | Test Step 4 | `browser_file_upload` modal-state fires immediately | asserted |
| Step 5: Verify file explorer opens immediately | File explorer open | Test Step 4 (folded) | Same observable as step 4 | asserted *(decomposed — no separate action)* |
| Step 6: Select both files, click Open | Both files selected | Test Step 6 | Modal in step 7 correctly reflects both files pending | asserted |
| Step 7: Verify "Upload files to ..." modal, Path pre-filled | Modal open, Path = bucket name | Test Step 7 | Live DOM inspection — Path shows `{bucket}/` prefix | asserted |
| Step 8: Click Upload | Duplicate detection triggered | Test Step 8 | Confirmed **client-side** (no network request) via `browser_network_requests` diff | asserted |
| Step 9: Verify "Resolve duplicates" modal lists sample.txt | Modal shows sample.txt as duplicate | Test Step 9 | Live DOM: title + filename spans (`sample` / `.txt`) | asserted |
| Step 10: Click Cancel | Cancel completes | Test Step 10 | Dialog closes, zero network requests (2/2 runs) | asserted |
| Step 11: Verify modal closed | Modal closed | Test Step 11 | `[role="dialog"]` absent from DOM | asserted |
| Step 12: Verify NO success notification | No toast shown | Test Step 12 | No `toast`/`snackbar`/`alert` element present at check time | asserted *(with fidelity caveat — see step 12 notes; recommend a short polled wait, not instantaneous check)* |
| Step 13: Verify sample.png NOT in file table | sample.png absent | Test Step 13 | File table shows only `sample.txt` | asserted |
| Step 14: Verify file count unchanged | Count == step 3 baseline | Test Step 14 | UI pagination `"1 - 1 of 1"` + JSON `keyCount: 1` | asserted |
| Step 15: Verify sample.txt unchanged incl. "Last update" timestamp | File + timestamp intact | Test Step 15 | `lastModified` field from S3 JSON listing endpoint, identical across 2 runs (`2026-07-18T23:53:14.000Z`) — **no UI-visible timestamp exists**, this is an API-level assertion | asserted |
| Expected Final State: bucket contents/count identical to pre-attempt state | Full-state equivalence | Test Steps 13–15 | Combination of file-list, count, and timestamp checks | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | Console checked clean (session leftovers excluded, see Expected Results) | asserted |
| Pass criterion: "No files uploaded; bucket state unchanged; no success notification shown" | Composite pass condition | Test Steps 10–15 | Same evidence as above, restated as the case's holistic pass bar | asserted |

### Axis 2 — Observables asserted beyond the case
- **Client-side-only duplicate detection (no network round-trip on "Upload"
  click, and none on "Cancel" click either)** — *added: this is the strongest,
  most specific proof that Cancel truly aborts the whole operation rather
  than e.g. silently uploading then rolling back; a network-level assertion
  is far stronger evidence than a DOM-only check.*
- **`lastModified` timestamp equality via the S3 JSON listing endpoint**
  (`GET /artifacts/s3/{bucket}?project_id=...&format=json`) — *added: the
  case's own step 15 asks for this but the UI provides no visible field for
  it; without this API-level technique the case's step 15 would be
  unautomatable via UI alone.*
- **Console-message check immediately after Cancel** — *added: standard
  silent-error guard; zero errors attributable to the flow itself.*
- **2/2 identical reproduction** (ran the full duplicate→Resolve→Cancel flow
  twice in the same session with a fresh isolated interaction each time) —
  *added: establishes this isn't a timing-flaky observation before handing
  off as `ready-for-automation`.*

## Cleanup
1. Delete the seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)`
   (`automation/api/client.py:1205`) in the `artifact_bucket` fixture's own
   teardown (automatic if that fixture is reused, per its existing
   implementation).
2. No other entities are created by this case (no Agent, no Toolkit, no
   Credential).
3. **This exploration run's artifacts** (not part of the automated test):
   bucket `autotest-elitea1832-dupcancel` was created manually in the
   `Private` project (id 399) to verify the case live, containing only
   `sample.txt` (67 B) at time of hand-off. Left in place — matches existing
   project convention of ~65 other un-deleted `autotest-*` buckets already
   present in that project from prior automated runs; harmless, and safe for
   the implementer or lead to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-elitea1832-dupcancel")` if desired.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this
project's locator policy (`.agents/testing.md` § Locator policy) is
**testid-only, no fallback ladder** — `LocatorDescriptor(testid=...)` with no
`fallback=`/`locator=`. The table below reflects that: "existing" testids are
usable as-is; "needs-adding" testids must be added via the `add-data-testid`
skill before automation can proceed on that element (missing testid ⇒ add
it, never drop to a role/CSS handle).

| Element | testid | Status | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | existing | left panel |
| Create bucket button | `artifacts-create-bucket-button` | existing | |
| Search buckets button | `artifacts-search-buckets-button` | existing | confirmed live — "No buckets found" state also present |
| Upload files button (toolbar) | `artifacts-upload-files-button` | existing | confirmed live via `getByTestId` in generated code |
| File list container | `artifacts-file-list` | existing | scopes file/folder rows |
| File row | `artifacts-file-row` | existing | one per file |
| Per-file actions (dot) menu button | `artifact-actions-{filename}-menu-button` | existing | **dynamic testid**, filename-templated — confirmed live as `artifact-actions-sample.txt-menu-button`; follow the project's class-constant templating pattern (`.agents/testing.md` § Locator policy "Dynamic testids") when wiring this into a page object, not an inline f-string in a method body |
| Delete-confirmation dialog's Delete button | `delete-confirm-button` | existing | confirmed live, reusable across the app |
| **"Upload files to ..." modal — entire dialog** | `artifacts-upload-path-dialog` | **added** | via `BaseModal`'s existing `data-testid` prop, lands on the `MuiDialog-root`/`MuiModal-root` wrapper (ancestor of the `[role="dialog"]` Paper) — confirmed live, sufficient for visibility/hidden scoping |
| "Upload files to ..." modal — Path input | `artifacts-upload-path-input` | **added** | on the `<TextField>` root; `text_content()` includes the bucket/prefix `startAdornment` text used for step 7's assertion |
| "Upload files to ..." modal — Cancel button | none | **implementer scope call — NOT added** | this test's actions/assertions never touch the Upload-path dialog's OWN Cancel button (only its Upload button, and the Resolve-duplicates dialog's Cancel) — per `.agents/testing.md`'s operator-confirmed scope ruling ("testids go ONLY on elements tests actually touch... blanket-adding... corrupts the metric"), left out. Follow-up for a future case that exercises it. |
| "Upload files to ..." modal — Upload button | `artifacts-upload-path-upload-button` | **added** | on the "Upload" `Button.BaseBtn` |
| **"Resolve duplicates" modal — entire dialog** | `artifacts-resolve-duplicates-dialog` | **added** | same `BaseModal`/`data-testid` mechanism as the Upload-path dialog |
| "Resolve duplicates" modal — duplicate filename display | `artifacts-resolve-duplicates-filename` | **added** | on the per-row `filenameRow` Box in `DuplicateDialogContent.jsx` — repeated testid per row, same pattern as the existing `artifacts-file-row` |
| **"Resolve duplicates" modal — Cancel button (this case's core element)** | `artifacts-resolve-duplicates-cancel-button` | **added** | on the "Cancel" `Button.BaseBtn` |
| "Resolve duplicates" modal — Skip button | none | **implementer scope call — NOT added** | this test never clicks Skip/Replace/Keep-both and never asserts on them; per the same scope ruling as above, left out rather than "add while the UI team is in this component" — that phrasing is scope creep against the operator-confirmed rule. Flagged as a follow-up in the PR description for whichever case first exercises these buttons. |
| "Resolve duplicates" modal — Replace button | none | **implementer scope call — NOT added** | see Skip button row above |
| "Resolve duplicates" modal — Keep both button | none | **implementer scope call — NOT added** | see Skip button row above |
| Success toast (if fired) | `toast-message` (generic, app-wide) | existing elsewhere, **not directly confirmed for the artifacts-upload flow in this run** | seen in `automation/pages/skills_list_page.py:59`, `skill_detail_page.py:96`; likely the same component but its firing for a successful artifacts upload auto-dismissed before this run's snapshot could confirm it — see Test Step 12 caveat |

## Network Behavior
- Opening a bucket: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id={id}&format=json`
  → `200 OK`. Response shape: `{name, prefix, delimiter, maxKeys, keyCount,
  isTruncated, contents: [{key, lastModified, etag, size, storageClass}]}`.
  This is the source of the step-15 `lastModified` assertion.
- A normal (non-duplicate) file upload: `PUT {ELITEA_URL}/artifacts/s3/{bucket}/{file_key}?project_id={id}`
  → `200 OK`. Confirmed live for the precondition-seeding upload.
- **Clicking "Upload" in the "Upload files to ..." modal when a duplicate is
  present fires NO network request** — the "Resolve duplicates" modal is
  driven entirely by a client-side diff against the already-fetched bucket
  listing.
- **Clicking "Cancel" in the "Resolve duplicates" modal fires NO network
  request** — confirmed 2/2 runs via `browser_network_requests` filtered on
  `artifacts`, comparing the request list immediately before and after the
  click.

## Known Defects
None found. Live product behavior matches the case's expected behavior
exactly across 2/2 identical runs: Cancel aborts the entire upload
(including the non-duplicate `sample.png`), no success notification appears,
and the bucket's file list/count/`sample.txt` metadata are unchanged.

## Blocked Steps
None blocking. One **fidelity caveat**, not a blocker (see Test Step 12): the
"no success notification" assertion (step 12) was only confirmed as "no
toast present at check time," not as "toast never fires and this was
witnessed" — because a plausibly-related toast for a *separate* successful
upload (used only to probe this behavior) had already auto-dismissed by the
time it was checked in this session. Recommend the implementer use a short
polled-absence wait (not `page.wait_for_timeout` alone) rather than a single
instantaneous check, so the assertion is robust either way.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`)
  with upload-flow methods — it currently has zero upload-related methods
  (`upload_files_button` `LocatorDescriptor` exists at line 66 but nothing
  calls it yet).
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`)
  for the bucket; consider extending `ArtifactAPI` (`automation/api/client.py:1143`)
  with an `upload_file()` helper per § Test Data above, to seed `sample.txt`
  fast and independent of the browser.
- Wait strategy: after clicking "Upload" (duplicate case) and after clicking
  "Cancel", there is genuinely **no network response to wait on** (confirmed
  no requests fire) — wait on the dialog's visibility state transition
  instead (`expect(dialog_locator).to_be_hidden()` after Cancel), not a
  network-idle wait, which would simply time out doing nothing useful here.
- The "Upload files to ..." and "Resolve duplicates" dialogs share the exact
  same underlying MUI dialog component (same `aria-labelledby="variables-dialog-title"` /
  `aria-describedby="alert-dialog-description"` ids on both) — scope any
  dialog-content selector by the dialog's own testid (once added) rather
  than by the shared `role="dialog"` alone, since a generic `[role="dialog"]`
  locator cannot disambiguate which of the two states is currently open
  before the dedicated testids exist.
