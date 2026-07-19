# Test Case: Download Flow – Download Multiple Selected Files as ZIP via Download Icon

## Metadata
- **TMS ID**: ELITEA-1840
- **Linked Story**: [EliteaAI/elitea-testing-public#222](https://github.com/EliteaAI/elitea-testing-public/issues/222) (tracking issue — "Found while working #222" for any defect filed from this case)
- **Priority**: l2 (high — as authored in the source TMS case; matches this folder's high→l2 convention, e.g. sibling ELITEA-1839)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend,
  project `Private` / `${ELITEA_PROJECT_ID}`=399). Every code citation below was verified against a **fresh
  `git fetch origin`** in `../EliteaUI` and its provenance (on `main`? on `automation/testids`?) recorded
  per-handle in § Concrete Handles.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end **twice** with clean, native-input-only runs
  (2/2 identical: same 2-of-4 selection count/identity, same enabled/disabled toolbar-button transition, same
  ZIP filename, same exact 2-file ZIP content, 0 console errors both times), plus a third **instrumented**
  run (network-delayed, JS-evaluate clicks, not counted as one of the 2 confirmation runs) used solely to
  capture the ZIP-progress dialog's live DOM structure for § Concrete Handles — the dialog completes in under
  ~1s with only 2 small files, too fast to inspect without an artificial delay. No product defects found.
  Six `testid needed:` gaps (one per-row checkbox pattern + five dialog-internals) block full policy-compliant
  automation until the implementer adds them (see § Concrete Handles) — additive, well-precedented changes
  (the checkbox gap needs a new caller-supplied prop on a shared component per the project's shared-component
  testid ruling; the dialog-internals gaps are simple `data-testid` prop additions to existing JSX elements),
  not an environment/access/data blocker, so this does **not** downgrade the status to `blocked`.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_multi_file.py` (`TestArtifactMultiFileDownload`, ELITEA-1327) and
`automation/tests/ui/artifacts/test_artifacts_download_single_file_dropdown.py` (ELITEA-1839) were both read
before this run, along with `automation/pages/artifacts_page.py` in full.

- **ELITEA-1327** only calls the legacy, non-testid-compliant `ArtifactsPage.download_file()` (per-file dropdown
  spot-check, `size > 0` only). It never touches a checkbox, never touches the toolbar
  `artifacts-download-files-button`, and never triggers the ZIP flow at all (its selections are always exactly
  one file). Zero behavioral overlap.
- **ELITEA-1839** exercises the *single-file dropdown* download path and explicitly asserts the **absence** of
  `artifacts_page.zip_download_progress_dialog` (`test_artifacts_download_single_file_dropdown.py:167`) — the
  architecturally opposite scenario from this case. It never checks a checkbox and never clicks
  `artifacts-download-files-button`.
- `artifacts_page.py`'s existing `download_files_button` and `zip_download_progress_dialog`
  `LocatorDescriptor`s (added defensively during ELITEA-1839, per that AFS's own note) are declared but **never
  actually exercised** anywhere yet — this case is the first to click the toolbar button and assert the
  dialog's actual (populated) contents rather than its absence.

Verdict: **zero behavioral overlap**. Fresh scenario, `ready-for-automation`. (A further sibling case,
`ELITEA-1841` — "download-flow-all-files-select-all-checkbox-zip" — exists in the TMS folder for the
select-all-checkbox variant; out of this case's scope, not touched here.)

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing a subfolder with at least 4 files, including two specific ones to select.
  **This bucket does not pre-exist as a stable fixture — `bucket-1`/`a1` are case-text placeholders**, not
  literal fixture names, matching the identical established finding from siblings ELITEA-1832 and ELITEA-1839
  (both searched all 5 available projects live, zero `bucket-1` matches). **Re-confirmed live in this run**:
  the full bucket list was scanned after creating this case's own fixture bucket (152 buckets present in
  `Private` at the time) — no bucket named literally `bucket-1` exists anywhere. Use the existing
  `artifact_bucket` pytest fixture (`automation/fixtures/data_fixtures.py:455`), not a hardcoded name.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture — function-scoped, creates a uniquely-named
  bucket via `ArtifactAPI.create_bucket()` and deletes it via `ArtifactAPI.delete_bucket()` in teardown. Do
  **not** hardcode `bucket-1`.
- **Subfolder + 4 files**: seed all four directly via
  `ArtifactAPI.upload_file(bucket_name, key, content, content_type=...)`
  (`automation/api/client.py:1282`) — confirmed live in this run (again, matching ELITEA-1839's finding):
  uploading to a nested key auto-creates the `a1` folder node in both panels; no separate "create folder" call
  is needed. Two files are the ones the test selects and expects in the ZIP; the other two exist purely to
  prove exclusion (case steps 13–14):
  - `a1/sample.txt` — selected, expected in ZIP
  - `a1/sample.png` — selected, expected in ZIP
  - `a1/extra1.txt` — NOT selected, must NOT appear in ZIP
  - `a1/extra2.txt` — NOT selected, must NOT appear in ZIP
- **Content constants** (confirmed live, this run — arbitrary but fixed, for byte-equality assertions on the
  two selected files):
  - `sample.txt` → `b"Sample content for ELITEA-1840 ZIP test - sample.txt\n"` (53 bytes)
  - `sample.png` → `b"\x89PNG\r\n\x1a\nFAKE_PNG_BYTES_FOR_ELITEA_1840_TEST"` (43 bytes — a fake-but-valid-PNG-signature
    byte string; the app never renders it, so exact PNG validity doesn't matter, only content-equality does)
  - `extra1.txt` / `extra2.txt` → any distinct fixed content (this run used 40-byte placeholder strings) — their
    content is never asserted, only their **absence** from the resulting ZIP.

No `reuse-existing` fixture applies — same reasoning as ELITEA-1832/1839: a bucket in this specific state isn't
safe to share across parallel/serial runs.

## Test Steps

1. Navigate directly to `${BASE_URL}/artifacts?bucket={bucket_name}&folder=a1` via
   `ArtifactsPage.navigate_to_bucket_folder()` (folds case steps 1–2 into one navigation; reuse this existing
   method **as-is**, including its built-in retry-once mitigation for the known product race — see next bullet).
   - **Known product race, already filed, already mitigated in the page object — do not rediscover it**:
     [EliteaAI/elitea-testing-public#638](https://github.com/EliteaAI/elitea-testing-public/issues/638) — direct
     `?bucket=&folder=` URL navigation can silently land on the wrong bucket (Redux project-id resolution race).
     `navigate_to_bucket_folder()` already re-checks the live URL's `bucket` param and retries once. Not
     observed to fire in either of this case's 2 clean confirmation runs, but the mitigation stays live per its
     own docstring.
   - **Verify**: right-panel breadcrumb shows `{bucket_name} > a1`; file table shows exactly 4 rows —
     `extra1.txt`, `extra2.txt`, `sample.png`, `sample.txt` — and pagination reads `"1 - 4 of 4"` (case step 3).
     Confirmed live 2/2 clean runs.
2. Locate the checkbox for the `sample.txt` row and click it. Verify it becomes checked (case step 4).
3. Locate the checkbox for the `sample.png` row and click it. Verify it becomes checked (case step 5).
4. Verify **exactly 2** checkboxes are checked in total, and that `extra1.txt`/`extra2.txt`'s checkboxes remain
   **unchecked** — query **all** row checkboxes' `checked` state independently (not just the two just clicked),
   confirming this is an independently checkable observable per the task's own guidance (case step 6). Confirmed
   live 2/2 runs via `Array.from(document.querySelectorAll('input[type="checkbox"]')).map(cb => cb.checked)` →
   `[false, false, true, true]` for `[extra1, extra2, sample.png, sample.txt]`, both runs identical.
5. Verify the toolbar `artifacts-download-files-button` transitions from `disabled` (0 selected, confirmed at
   Test Step 1's page-load state) to enabled/clickable once 2 files are selected (case step 7). Confirmed live
   2/2 runs.
6. Click `artifacts-download-files-button` (case step 8).
7. Verify the ZIP-preparation dialog appears (case step 9), with:
   - **Title**: exactly `` `Preparing ${bucket_name}.zip` `` — confirmed live both runs, e.g.
     `"Preparing autotest-elitea1840-download-1784445632.zip"`.
   - **Body label**: `"Downloading files..."` text, present.
   - **Progress bar**: an MUI `LinearProgress` element, `role="progressbar"`, determinate
     (`aria-valuenow`/`aria-valuemin="0"`/`aria-valuemax="100"`), value = `(current/total)*100`.
   - **File counter**: `"{current} of {total} files"` text — confirmed live as `"0 of 2 files"` immediately
     after click, before the first file resolves.
   - **Cancel button**: present, labelled "Cancel". (Not clicked — out of this case's scope, see § Automation
     Hints for the Cancel/cancel-flow scope boundary.)
   - **Also present but NOT requested by the case**: an always-rendered dialog-header Close (✕) icon button
     (`aria-label="Close"`), part of the shared `BaseModal` chrome, not the case's "Cancel" action button —
     new finding this run, not mentioned in prior static-analysis notes. Not asserted (out of case scope), but
     documented here so the implementer doesn't confuse it with the required Cancel button.
8. Verify the counter and current-file label update as each file is processed (case step 10). **Confirmed live
   via an instrumented run** (network-delayed via a `window.fetch` wrapper for exploration purposes — the
   idiomatic Playwright equivalent for the implementer is `page.route()` with an added delay, see § Automation
   Hints): captured an intermediate frame showing `"1 of 2 files"` and, **critically, `"Current: a1/sample.png"`
   — the current-file label shows the FULL relative key including the subfolder prefix** (`a1/sample.png`, not
   just `sample.png`), confirmed via live DOM query and a screenshot
   (`ELITEA-1840-step9-10-11-zip-progress-dialog-delayed.png`). The current-file `Typography` only renders when
   `progress.filename` is truthy — absent from the DOM at `"0 of 2"`. With only 2 small (< 60 byte) files and no
   artificial delay, this transition happens in well under 1 second — the 2 clean, non-instrumented confirmation
   runs never captured an intermediate frame (dialog closed before the next tool round-trip), which is expected
   and consistent with the source's synchronous-fetch-then-blob for-loop, not a defect.
9. Verify the progress bar's value advances forward as files are processed (case step 11) — same instrumented
   evidence as Test Step 8: `aria-valuenow` moved from `0` (at "0 of 2") toward `50` (visually ~50% filled at
   "1 of 2", per the same screenshot).
10. Verify upon completion: the dialog closes, a success toast reading `"ZIP downloaded successfully"` appears
    (reuse the existing generic `success_toast_message`/`toast-message` handle, confirmed by prior sibling
    ELITEA-1832's AFS and re-observed visually this run — see screenshot
    `ELITEA-1840-step9-zip-progress-dialog.png`), and a ZIP file named exactly `` `{bucket_name}.zip` `` is
    downloaded (case step 12). Confirmed live 2/2 clean runs: Playwright's `expect_download()` **does capture
    the client-side blob-URL-anchor download as a normal download event** — no special handling needed, and
    this resolves the pre-supplied context's open question about whether `expect_download()` would catch it.
11. Verify the downloaded ZIP's internal file list is **exactly** `["sample.png", "sample.txt"]` — flattened to
    the ZIP root, **not** nested under `a1/`, since `downloadArtifactsAsZip` strips `currentPrefix` from each
    entry's path before adding it to the archive (case step 13). Confirmed live 2/2 clean runs via
    `zipfile.ZipFile(download.path()).namelist()`.
12. Verify neither `extra1.txt` nor `extra2.txt` appears anywhere in the ZIP's namelist (case step 14). Confirmed
    live 2/2 clean runs — namelist was exactly the 2-element list above both times, no extras present.

## Expected Results
- Selecting exactly 2 files via checkbox enables the toolbar `artifacts-download-files-button`; the remaining
  files' checkboxes stay independently unchecked.
- Clicking the button opens `artifacts-zip-download-progress-dialog` with title `Preparing {bucket}.zip`, a
  determinate progress bar, a `"{current} of {total} files"` counter, a `"Current: {full-relative-key}"` label
  (shown only once a file is in flight), and a Cancel button.
- The dialog auto-closes ~500ms after the last file resolves; a `"ZIP downloaded successfully"` toast fires; a
  ZIP file named exactly `{bucket}.zip` downloads via a client-side JSZip-built blob-URL anchor click (no
  dedicated server-side ZIP endpoint — confirmed via Network Behavior below).
- The ZIP contains exactly the 2 selected files, flattened to the ZIP root, byte-identical to what was seeded;
  no unselected file is present.
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket "bucket-1" with subfolder "a1" containing ≥4 files incl. sample.txt/sample.png | Precondition state exists | Test Data + Test Step 1 | `artifact_bucket` fixture + 4× `ArtifactAPI.upload_file()`; proven by Test Step 1's file-count/name assertions | asserted |
| Step 1: Navigate to Artifacts section | Artifacts page loads | Test Step 1 | Folded into the direct bucket+folder navigation; page-load proven via Test Step 1's breadcrumb + file-table assertions | asserted *(decomposed/folded)* |
| Step 2: Click bucket-1, navigate to a1 | Subfolder a1 selected | Test Step 1 | Same navigation call; breadcrumb `{bucket} > a1` asserted | asserted *(folded)* |
| Step 3: Verify file table shows ≥4 files incl. sample.txt/sample.png | Files visible | Test Step 1 | 4-row table + `"1 - 4 of 4"` pagination confirmed live | asserted |
| Step 4: Click checkbox for sample.txt, verify checked | sample.txt checked | Test Step 2 | Checkbox `checked` state confirmed live | asserted |
| Step 5: Click checkbox for sample.png, verify checked | sample.png checked | Test Step 3 | Checkbox `checked` state confirmed live | asserted |
| Step 6: Verify 2 selected, remaining unchecked | Exactly 2 checked | Test Step 4 | All-checkbox-state query, independently confirmed live both runs | asserted |
| Step 7: Verify Download files icon becomes active/enabled | Icon enabled | Test Step 5 | `disabled` attribute observed dropping after selection | asserted |
| Step 8: Click Download files icon | ZIP prep modal appears | Test Step 6 | Click fires `onDownloadFiles` → `startZipDownload` (confirmed via source + live dialog appearance) | asserted |
| Step 9: Verify "Preparing bucket-1.zip" modal — title, progress bar, counter, current-file label, Cancel | Modal shows all elements | Test Step 7 | Each element confirmed live via DOM query + screenshot | asserted |
| Step 10: Verify counter/current-file label update as each file processed | Counter/label update in real time | Test Step 8 | Confirmed via instrumented (network-delayed) run — intermediate `"1 of 2 files"` / `"Current: a1/sample.png"` frame captured | asserted |
| Step 11: Verify progress bar advances forward | Bar moves forward | Test Step 9 | `aria-valuenow` observed at 0 then ~50 in the same instrumented run | asserted |
| Step 12: Verify modal closes + ZIP downloaded on completion | ZIP downloaded, modal closes | Test Step 10 | Toast + `expect_download()` capture confirmed live 2/2 clean runs | asserted |
| Step 13: Verify ZIP contains exactly sample.txt + sample.png | Exact 2-file match | Test Step 11 | `zipfile.namelist()` confirmed live 2/2 clean runs | asserted |
| Step 14: Verify unselected files NOT in ZIP | No unselected files in ZIP | Test Step 12 | Same `zipfile.namelist()` check — extras absent both runs | asserted |
| Expected Final State: ZIP named `bucket-1.zip` containing exactly the 2 files; modal shows correct indicators and closes | Composite pass condition | Test Steps 6–12 | Combination of all above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | 0 console errors confirmed both clean runs (only the pre-existing, flow-unrelated Vite `stream.Stream` warning present, same as ELITEA-1839's finding) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Content byte-equality on the 2 selected files (not just presence/`size > 0`)** — *added: the case's own
  step 13 asks for "exactly" the 2 files; byte-equality against the known seed is the strongest available
  signal that the ZIP entries aren't truncated/corrupted, consistent with sibling ELITEA-1839's precedent.*
- **Current-file label shows the full relative key (`a1/sample.png`), not the base filename** — *added: this is
  a previously-unconfirmed implementation detail (the pre-supplied static-analysis notes didn't specify whether
  `progress.filename` is base-name or full-key); asserting the exact string, not just "contains the filename",
  catches a future regression to base-name-only.*
- **Selection state and toolbar-button enabled state both persist after the ZIP download completes** — *added:
  observed live (checkboxes for sample.png/sample.txt remained checked, button remained enabled, post-download)
  — not required by the case, but worth guarding since a regression that silently clears selection could look
  like "it still works" in a naive test that re-selects every time.*
- **Console-message check immediately after the flow completes** — *added: standard silent-error guard,
  consistent with ELITEA-1832/1839's precedent.*
- **2/2 identical clean reproduction**, each run starting from a fresh page navigation — *added: rules out
  session/DOM-state carryover before handing off as `ready-for-automation`, matching the family's established
  bar.*
- **Network Behavior confirms client-side ZIP packaging (no dedicated backend ZIP endpoint)** — *added: exactly
  2 sequential GETs to the same single-file endpoint ELITEA-1839 already exercises, confirmed live both clean
  runs — strengthens the "no server-side ZIP work" architectural claim beyond just reading the source.*

## Cleanup
1. Delete the seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)` in the `artifact_bucket` fixture's own
   teardown. **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636))**: this call 404s in the current dev
   environment (re-confirmed live this run — both URL-format attempts 404'd), so the bucket actually leaks; not
   this case's concern, do not re-file.
2. No other entities are created by this case.
3. **This exploration run's own artifact** (not part of the automated test): bucket
   `autotest-elitea1840-download-1784445632` was created via direct API call in the `Private` project (id 399),
   containing `a1/{sample.txt, sample.png, extra1.txt, extra2.txt}`. Left in place per this repo's existing
   convention (~150+ pre-existing un-deleted `autotest-*` buckets already present in `Private`); safe to delete
   any time via `ArtifactAPI.delete_bucket("autotest-elitea1840-download-1784445632")` (will itself 404 per #636
   — a human/script would need the S3-console-level cleanup #636 describes).
4. Local exploration screenshots (repo root, untracked), attached as evidence for this AFS:
   `ELITEA-1840-step4-6-two-files-checked-download-enabled.png`,
   `ELITEA-1840-step9-zip-progress-dialog.png` (completion toast),
   `ELITEA-1840-step9-10-11-zip-progress-dialog-delayed.png` (instrumented mid-flight frame — title, progress
   bar ~50%, "1 of 2 files", "Current: a1/sample.png", Cancel button).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md` § Analyst slot) is **testid-only, no
fallback ladder**, and scoped sub-selectors must themselves be `[data-testid="…"]`-based class constants — a
scoped raw-tag/CSS selector (e.g. `dialog.locator("h2")`) is **not** compliant even when scoped inside a real
testid. Every element below that the case requires an assertion on therefore needs its own testid if it doesn't
already have one. Every row's Provenance was checked against a fresh `git fetch origin` in `../EliteaUI`
(`origin/main` vs `origin/automation/testids` checked independently — the gaps below are present on **both**,
not automation/testids drift).

| Element | testid | Provenance | Status | Notes |
|---|---|---|---|---|
| Toolbar "Download files" (bulk) button | `artifacts-download-files-button` | on-main ✓, on-testids ✓ | existing, reuse | Already declared as `ArtifactsPage.download_files_button`; confirmed live enabled/disabled toggling on 0→2 selection |
| ZIP-download progress dialog (outer) | `artifacts-zip-download-progress-dialog` | on-testids ✓, **on-main ✗** | existing (testids-branch only), reuse | Already declared as `ArtifactsPage.zip_download_progress_dialog`; added defensively in PR #639/ELITEA-1839, not yet cherry-picked to `main` by a human — dev server (this exploration's target) already serves it |
| File row (per file, used to scope the checkbox click) | `artifacts-file-row` | on-main ✓, on-testids ✓ | existing, reuse | Already declared; one per file/folder row (ELITEA-1839) |
| **Per-row checkbox** | `testid needed: artifacts-file-checkbox-{filename}` | **confirmed missing on both `origin/main` and `origin/automation/testids`** | **needs-adding** | Root cause (confirmed live via DOM query — the `<input type="checkbox">` and its wrapping span both have `data-testid: null`): `GridTableRow.jsx` (`src/[fsd]/entities/grid-table/ui/GridTableRow.jsx:64`) renders `<Checkbox.BaseCheckbox checked={isSelected} onChange={handleCheckboxChange} .../>` with **no `data-testid`/`testId` prop threaded through at all** — `BaseCheckbox` (`src/[fsd]/shared/ui/checkbox/BaseCheckbox.jsx`) does forward arbitrary `...restProps` to the underlying MUI `Checkbox`, so a prop WOULD work once wired. `GridTableRow` is a **shared component** (7 consumers: `SecretsTable`, `TokensTable`, `UsersTable`, `BucketAccessTable`, `DataTable`, `NotificationTable`, and this case's `ArtifactTable`) — per the project's shared-component testid ruling, the fix is a new caller-supplied prop (e.g. `checkboxTestId`), the same pattern `GridTableRow` already uses for its own `'data-testid': dataTestId` prop, threaded to `<Checkbox.BaseCheckbox data-testid={checkboxTestId} .../>`. Wire it **only** at `ArtifactTable.jsx`'s call site (~line 532, inside the `paginatedRows.map()` block) as `checkboxTestId={`artifacts-file-checkbox-${row.id}`}` — `row.id` = the file's base name (`item.name`), same identity semantics as the existing `ARTIFACT_ACTIONS_MENU_BUTTON` dynamic template. Do **not** add a testid at the other 6 call sites (out of this case's scope — testid-scope rule: only wire testids for elements a test actually touches). |
| ZIP dialog title | `testid needed: artifacts-zip-download-progress-title` | confirmed missing on both branches | **needs-adding** | `ZipDownloadProgressDialog.jsx:56-59` passes `title={\`Preparing ${bucket \|\| 'artifacts'}.zip\`}` into `<BaseModal>`; `BaseModal` renders this as an `<h2 class="MuiDialogTitle-root">` with no testid. Add `data-testid="artifacts-zip-download-progress-title"` — confirm `BaseModal`'s title-rendering path accepts a `titleTestId`-style prop (consistent with the project's `testId`/`<part>TestId` naming convention) or add it directly if `BaseModal` doesn't already support per-part testids. |
| ZIP dialog "Downloading files..." label | none requested | — | out-of-scope, not needed | Case step 9 doesn't ask for this label specifically to be independently verified (only title/progress-bar/counter/current-file/Cancel); left unassigned unless a future case needs it. |
| ZIP dialog progress bar | `testid needed: artifacts-zip-download-progress-bar` | confirmed missing on both branches | **needs-adding** | `ZipDownloadProgressDialog.jsx:21-25`, MUI `<LinearProgress variant="determinate" value={...} />`, `role="progressbar"`, no testid. Add `data-testid="artifacts-zip-download-progress-bar"` directly on the `LinearProgress` element; assert via its `aria-valuenow` attribute for the "advances forward" check (case step 11), not visual width. |
| ZIP dialog file counter | `testid needed: artifacts-zip-download-progress-counter` | confirmed missing on both branches | **needs-adding** | `ZipDownloadProgressDialog.jsx:27-32`, `<Typography variant="caption">{progress.current} of {progress.total} files</Typography>`, no testid. Add `data-testid="artifacts-zip-download-progress-counter"`. |
| ZIP dialog current-file label | `testid needed: artifacts-zip-download-progress-current-file` | confirmed missing on both branches | **needs-adding** | `ZipDownloadProgressDialog.jsx:33-41`, conditionally rendered `<Typography>Current: {progress.filename}</Typography>` (only when `progress.filename` is truthy — absent from DOM at `current=0`). Add `data-testid="artifacts-zip-download-progress-current-file"` on this conditional element; the implementer's assertion for "updates as each file is processed" must account for its absence in the first frame. **Confirmed live: text is `Current: {full relative key}` e.g. `Current: a1/sample.png`, not the base filename** — see § Axis 2. |
| ZIP dialog Cancel button | `testid needed: artifacts-zip-download-progress-cancel-button` | confirmed missing on both branches | **needs-adding** | `ZipDownloadProgressDialog.jsx:45-53`, `<Button.BaseBtn variant="elitea" color="alarm" onClick={onCancel}>Cancel</Button.BaseBtn>`, no testid. Add `data-testid="artifacts-zip-download-progress-cancel-button"`. This case only needs the button's **visibility** asserted (case step 9) — it is never clicked (Cancel-flow testing is out of this case's scope, see § Automation Hints). |
| ZIP dialog Close (✕) button | none requested | — | out-of-scope, not needed | New finding this run (not in prior static-analysis notes): `BaseModal`'s standard header close icon (`aria-label="Close"`), always present alongside the Cancel action button, no testid. Not part of the case's required elements — do not add a testid for it under this case; note only. |
| Success toast (app-wide generic) | `toast-message` | on-main ✓ (per ELITEA-1832) | existing, reuse | Already declared as `ArtifactsPage.success_toast_message`; visually confirmed showing "ZIP downloaded successfully" this run (screenshot), not re-verified via fresh DOM query since it auto-dismisses quickly and the handle is already established by a prior sibling AFS |

## Network Behavior
- Opening the bucket/subfolder: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id={id}&format=json` → `200 OK`.
  Fires once per navigation, before the file table renders.
- **Each selected file's download** (fired **sequentially**, confirmed both via source read —
  `downloadArtifactsAsZip` in `src/common/utils.jsx:444` uses a synchronous `for` loop with `await fetch(...)`
  per iteration, not `Promise.all` — and via live network-request ordering):
  `GET {ELITEA_URL}/api/v2/artifacts/artifact/default/{project_id}/{bucket}/{url-encoded-key}` → `200 OK` ×2,
  e.g. `.../artifact/default/399/autotest-elitea1840-download-1784445632/a1%2Fsample.png` then
  `.../a1%2Fsample.txt`. This is the **exact same single-file endpoint** ELITEA-1839's dropdown-download case
  already exercises — confirming there is **no dedicated server-side ZIP-building endpoint**; the ZIP is
  assembled entirely client-side via JSZip after these GETs resolve (`zip.generateAsync({type:'blob'})`), then
  triggered as a browser download via a `document.createElement('a')` + blob-URL `.click()` — which Playwright
  **does** capture as a normal `download` event (confirmed live, resolving the pre-supplied context's open
  question).
- **No other network request fires between the toolbar-button click and the ZIP download completing** —
  confirmed live 2/2 clean runs via `browser_network_requests` filtered on `artifact`: exactly the 2 GETs above,
  no POST/PUT, no ZIP-specific endpoint.
- No console errors either clean run (one pre-existing, flow-unrelated Vite `stream.Stream` module-externalization
  warning present both times, identical to ELITEA-1839's finding — not caused by this flow).

## Known Defects Found During Exploration
None found at the analyst pass (2/2 clean identical runs + 1 instrumented handle-discovery run). Live product
behavior matched the case's expected behavior exactly: 2-file selection enables the toolbar button, the ZIP
dialog shows the correct title/progress bar/counter/current-file/Cancel elements, the dialog auto-closes and a
correctly-named ZIP downloads on completion, and the ZIP contains exactly the 2 selected files (flattened, byte-
identical) with the 2 unselected files correctly excluded. No CLARIFICATION filed either — the case's
`bucket-1`/`a1` placeholder naming was already established as intentional TMS-authoring shorthand by prior
sibling runs, re-confirmed (not re-derived) this run.

## Blocked Steps
None. The six `testid needed:` rows in § Concrete Handles are implementer work items (per
`.agents/role-overrides.md` § Analyst slot: not softened into a MINOR defect or a note; the AFS is the work
order), not analyst-side blockers — they are additive, well-precedented frontend changes (one new
caller-supplied prop on a shared component for the checkbox; five simple `data-testid` prop additions to
existing JSX elements in `ZipDownloadProgressDialog.jsx`), not an environment/access/data blocker.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`) — already has
  `download_files_button` and `zip_download_progress_dialog` declared (added defensively during ELITEA-1839,
  never yet exercised). Add:
  - A dynamic template constant for the per-row checkbox, following the project's existing
    `ARTIFACT_ACTIONS_MENU_BUTTON` pattern: `ARTIFACT_FILE_CHECKBOX = '[data-testid="artifacts-file-checkbox-{}"]'`.
  - Five new static `LocatorDescriptor`s for the dialog internals:
    `zip_download_progress_title`, `zip_download_progress_bar`, `zip_download_progress_counter`,
    `zip_download_progress_current_file`, `zip_download_progress_cancel_button` (testids per § Concrete Handles).
  - New methods, e.g. `select_file_checkbox(filename)`, `get_checkbox_states()` (returns `{filename: bool}` for
    ALL visible rows, not just the ones clicked — needed for case step 6's independent "remaining unchecked"
    check), and `download_selected_files_as_zip()` (clicks the toolbar button, wrapped in
    `page.expect_download()`).
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`) and
  `ArtifactAPI.upload_file()` (`automation/api/client.py:1282`) to seed all 4 files — no browser-driven upload
  needed (confirmed live, § Test Data).
- Navigation: reuse `ArtifactsPage.navigate_to_bucket_folder()` as-is (built-in issue #638 retry mitigation) —
  do not hand-roll a separate navigation helper.
- **Observing the intermediate progress frame (case steps 10–11) is the one genuinely non-obvious part of this
  case.** With only 2 small files, the real flow completes in well under 1 second — too fast for a naive
  Playwright script to reliably catch an intermediate `"1 of 2 files"` frame. This run confirmed (via a
  `window.fetch` wrapper used only for exploration) that adding a delay to the artifact-download GET requests
  reliably surfaces the intermediate state. The idiomatic Playwright equivalent for the actual test is
  `page.route()` intercepting the `**/artifact/default/**` pattern and delaying `route.continue_()` by a short,
  fixed amount (e.g. 500ms–1s) for **this test only** — this is a standard timing-control technique, not a
  defect-masking or synthetic-input concern (it delays a network response, not a fake input event). Without
  this, case steps 10–11 can only be proven architecturally (the sequential for-loop + `onProgress` callback
  in `useZipDownload.hooks.js`/`downloadArtifactsAsZip` guarantee the counter *would* increment per file), which
  is a materially weaker assertion than actually observing it — recommend the route-delay approach.
- "Not corrupted" assertion on the 2 ZIP entries: compare each entry's bytes to the exact seeded content
  constants (byte-for-byte), not `size > 0` (§ Test Data, § Axis 2) — use Python's `zipfile` module against
  `download.path()`.
- Cancel-button flow (aborting an in-flight ZIP download) is **out of this case's scope** — the case only
  requires the Cancel button's visibility, not its behavior. Don't test cancel behavior beyond that, and be
  careful not to let a slow/flaky test accidentally trigger it (e.g. via an errant click during dialog
  exploration).
- Select-all-checkbox variant is a **separate** sibling case (ELITEA-1841, already present in the TMS folder) —
  do not fold select-all coverage into this case's implementation.
