# Test Case: Download Flow – Download All Files Using Select All Checkbox as ZIP

## Metadata
- **TMS ID**: ELITEA-1841
- **Linked Story**: [EliteaAI/elitea-testing-public#262](https://github.com/EliteaAI/elitea-testing-public/issues/262) (tracking issue — "Found while working #262" for any defect filed from this case)
- **Priority**: l2 (high — as authored in the source TMS case; matches this folder's high→l2 convention, e.g. siblings ELITEA-1839/ELITEA-1840)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend,
  project `Private` / `${ELITEA_PROJECT_ID}`=399). `../EliteaUI` freshly `git fetch origin`'d this run;
  every code citation below is checked against that fetch and its provenance (on `main`? on
  `automation/testids`?) recorded per-handle in § Concrete Handles.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** (fresh sibling spec, NOT extend-existing — see § Coverage Map vs
  ELITEA-1840 for the reasoning). Case executed end-to-end **3 times** against 3 independently seeded buckets:
  2 clean, native-input-only confirmation runs (identical: all 6 rows became checked from one header-checkbox
  click, header checkbox itself landed `Mui-checked` + non-indeterminate, toolbar button
  disabled→enabled, ZIP filename `{bucket}.zip`, ZIP namelist exactly the 6 seeded files flattened to root,
  byte-identical content, `testzip()` clean, exactly 6 GET requests, 0 console errors, post-download
  selection/button-state persistence) + 1 **instrumented** run (network-delayed via a `window.fetch` wrapper,
  exploration-only, not counted as a confirmation run) used to capture the ZIP-progress dialog's full frame
  sequence for § Concrete Handles / § Automation Hints. One `testid needed:` gap (the header "Select all"
  checkbox itself) blocks full policy-compliant automation until the implementer adds it (additive,
  well-precedented — same shared-component caller-prop shape ELITEA-1840 already established for the per-row
  checkbox) — not an environment/access/data blocker, so this does **not** downgrade the status to `blocked`.
  No product defects found.

## Coverage Map vs ELITEA-1840 (dedup / extend-existing analysis)

`automation/tests/ui/artifacts/test_artifacts_download_multiple_files_zip.py`
(`TestArtifactDownloadMultipleFilesZip.test_download_multiple_files_as_zip`) and its AFS
(`test-specs/artifacts/l2_download-flow-multiple-selected-files-as-zip_ELITEA-1840.md`) were read in full
before this run, along with the current `automation/pages/artifacts_page.py`.

**What ELITEA-1840 already proves** (reused here, not re-derived): the ZIP-preparation dialog's full DOM
structure and testids (title `Preparing {bucket}.zip`, determinate progress bar with
`aria-valuemin`/`aria-valuemax`, file counter, current-file label showing the FULL relative key, Cancel
button), the dialog auto-close + `{bucket}.zip` filename download, `expect_download()` capturing the
client-side blob-URL-anchor download, the ZIP-namelist-flattened-to-root + byte-identical-content proof
pattern, the exactly-N-GET-requests-no-server-side-ZIP-endpoint architectural fact, the
`page.route()`-network-delay technique for observing intermediate progress frames, and the
`is_file_checkbox_checked()` "read `Mui-checked` off the testid-anchored span" technique for per-row
checkboxes (already testid'd: `artifacts-file-checkbox-{filename}`, reused as-is here — no new per-row gap).

**What this case exercises that ELITEA-1840 never touches — the reason this is a fresh sibling, not an
extension:**

1. **A categorically different selection mechanism.** ELITEA-1840 always clicks 2 individual row
   checkboxes. This case's core interaction is a **single click on the table-header "Select all" checkbox**
   (`GridTableHeader.jsx`'s `onSelectAll` handler) — a different code path in the product
   (`handleSelectAll` in `ArtifactTable.jsx`, not the per-row `handleCheckboxChange`) and a different user
   gesture entirely.
2. **A brand-new element under test with its own state assertion.** ELITEA-1840 never reads or asserts
   anything about the header checkbox. This case's steps 4-6 require asserting the header checkbox's OWN
   visual state transitions to fully-checked/non-indeterminate — confirmed live this run to be a genuinely
   distinct MUI state (`MuiCheckbox-indeterminate` class present when partially selected, absent + `Mui-checked`
   present when fully selected via the header's own click) that ELITEA-1840's test has zero coverage of.
   This element also has **zero testid today** (§ Concrete Handles) — a wholly new gap, not inherited from 1840.
3. **All 6 rows become checked as a SIDE EFFECT of one click**, not as the direct target of 6 individual
   clicks — a materially different causal chain to verify (assert the effect of `onSelectAll`, not the
   effect of `onChange` on each row).
4. **The progress counter must be shown to progress through the FULL range** (case step 10: "1 of 6" → "6 of
   6", explicitly enumerated in the case text), not spot-checked at a single "1 of N" frame the way ELITEA-1840
   did (justified there because only 2 files meant "progression" was barely distinguishable from a single
   transition). Confirmed live this run via a polled instrumented capture: the dialog cycles through
   `3 of 6 → 4 of 6 → 5 of 6 → 6 of 6` (a full monotonic sequence, not a single frame) — a stronger and
   different assertion shape than 1840's test exercises.
5. **1840's own AFS explicitly flagged this case as future, separate scope**: *"A further sibling case,
   ELITEA-1841 — 'download-flow-all-files-select-all-checkbox-zip' — exists in the TMS folder for the
   select-all-checkbox variant; out of this case's scope, not touched here."* The analyst who wrote 1840
   already judged this to be a distinct scenario, not an extension point.

Given (1)-(3) require exercising an entirely different interaction + a brand-new untested element with its
own testid gap, and (4) requires a materially different (fuller, sequence-based) assertion than 1840's
single-frame spot-check, the delta is not "a small number of missing assertions" appendable to 1840's
existing test — it is a distinct scenario whose selection-mechanism and header-checkbox-state assertions
would force a near-rewrite of 1840's test body if squeezed in. Per the `test-case-analysis` skill's own
boundary guidance ("if the gap is large enough that the extension would be a near-rewrite... treat as
`ready-for-automation` instead"), this case is classified **`ready-for-automation`** as its own test file,
reusing (not re-deriving) every ZIP-dialog/byte-identity/network-architecture fact 1840 already established.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing a subfolder with exactly 6 named files: `Q&A.docx.odt`,
  `Regression test cases.odt`, `sharepoint.docx`, `sample_640x426.gif`, `sample.png`, `sample.txt`.
  **This bucket does not pre-exist as a stable fixture — `bucket-1`/`a1` are case-text placeholders**, not
  literal fixture names, matching the identical established finding from siblings ELITEA-1832/1839/1840
  (all independently searched the live bucket list, zero `bucket-1` matches). **Re-confirmed live in this
  run**: the full bucket list was scanned across 3 separate navigations (279 buckets present in `Private` at
  the time of the last) — no bucket literally named `bucket-1` exists anywhere. Use the existing
  `artifact_bucket` pytest fixture (`automation/fixtures/data_fixtures.py:455`), not a hardcoded name.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture — function-scoped, creates a uniquely-named
  bucket via `ArtifactAPI.create_bucket()` and deletes it via `ArtifactAPI.delete_bucket()` in teardown. Do
  **not** hardcode `bucket-1`. (Same `generate-per-test` classification as ELITEA-1840 — a bucket in this
  specific state isn't safe to share across parallel/serial runs; no `reuse-existing` fixture applies.)
- **Subfolder + exactly 6 files**: seed all six directly via `ArtifactAPI.upload_file(bucket_name, key,
  content, content_type=...)` (`automation/api/client.py:1282`) — confirmed live in this run (matching
  1839/1840's finding): uploading to a nested key auto-creates the `a1` folder node; no separate
  "create folder" call is needed. All 6 are selected via one header-checkbox click and all 6 must appear in
  the resulting ZIP (this case has no "excluded file" counterpart — unlike 1840's 2-selected-of-4 shape,
  select-all means every visible row is included by construction):
  - `a1/Q&A.docx.odt`
  - `a1/Regression test cases.odt`
  - `a1/sharepoint.docx`
  - `a1/sample_640x426.gif`
  - `a1/sample.png`
  - `a1/sample.txt`
- **Content constants** — arbitrary but fixed, distinct per file, for byte-equality assertions (confirmed
  live this run with 3 different content sets across 3 runs, all producing byte-identical ZIP entries each
  time — the implementer should pick one fixed set, e.g.):
  - `Q&A.docx.odt` → `b"Q&A docx odt content for ELITEA-1841 select-all ZIP test\n"`
  - `Regression test cases.odt` → `b"Regression test cases odt content for ELITEA-1841\n"`
  - `sharepoint.docx` → `b"sharepoint docx content for ELITEA-1841\n"`
  - `sample_640x426.gif` → `b"GIF89a" + b"FAKE_GIF_BYTES_FOR_ELITEA_1841_TEST"` (fake-but-valid-signature
    bytes — the app never renders it, only content-equality matters)
  - `sample.png` → `b"\x89PNG\r\n\x1a\nFAKE_PNG_BYTES_FOR_ELITEA_1841_TEST"`
  - `sample.txt` → `b"Sample content for ELITEA-1841 select-all ZIP test - sample.txt\n"`

## Test Steps

1. Navigate directly to `${BASE_URL}/artifacts?bucket={bucket_name}&folder=a1` via
   `ArtifactsPage.navigate_to_bucket_folder()` (folds case steps 1-2 into one navigation; reuse this existing
   method **as-is**, including its built-in retry-once mitigation for the known product race, issue #638 —
   not observed to fire in any of this case's 3 runs, but the mitigation stays live per its own docstring).
   - **Verify**: right-panel breadcrumb shows `{bucket_name} > a1`; file table shows exactly 6 rows; pagination
     reads `"1 - 6 of 6"` (case step 3). Confirmed live 3/3 runs.
   - **Note (transient, already-documented, non-blocking):** the LEFT-PANEL bucket list can briefly show
     "No buckets created yet" / "Buckets: 0" immediately after a fresh page load even though the bucket-list
     API response (confirmed live via network capture) already contains full data — this is the SAME
     self-correcting mid-fetch race ELITEA-1808's AFS already documented ("a stale... state that
     self-corrects within ~1-2s once the list refetch completes") and is unrelated to the right-panel file
     table this case actually touches. Not a defect, not re-filed; a condition-based wait (not a fixed
     sleep) on the right panel's own content is sufficient and is what `navigate_to_bucket_folder()` already
     does via `_wait_for_bucket_panel()`.
2. Verify the toolbar `artifacts-download-files-button` starts `disabled` (0 selected) (folds into Test Step
   1's page-load state, same as ELITEA-1840's precedent).
3. Click the header "Select all" checkbox (case step 4) — see § Concrete Handles for the `testid needed` gap.
   - **Verify**: all 6 file rows become checked (case step 5) — confirmed live 3/3 runs via
     `get_checkbox_states()`-equivalent per-row query (all 6 → `True`), not just the 2 rows a naive
     assumption might check.
   - **Verify**: the header checkbox's own class carries `Mui-checked` and does **not** carry
     `MuiCheckbox-indeterminate` (case step 6 — "not indeterminate") — confirmed live: clicking the header
     checkbox with 0→6 selected lands it directly in the fully-checked state; separately confirmed (via an
     exploratory partial-deselect, not part of the case flow) that MUI DOES apply a distinguishing
     `MuiCheckbox-indeterminate` class when the selection is partial, proving this is a real, observable,
     3-state signal — not a cosmetic no-op assertion.
4. Verify the toolbar `artifacts-download-files-button` transitions from `disabled` to `enabled`, with tooltip
   text exactly `"Download files"` (case step 7 — confirmed live: unlike the delete button's tooltip, which
   switches between "Delete selected files"/"Delete all files" depending on selection completeness, the
   download button's tooltip text is a STATIC `"Download files"` string regardless of partial vs. full
   selection — confirmed via `aria-label` read on the wrapping `<span>`, same no-hover-required technique
   already established for other MUI tooltips in this codebase).
5. Click `artifacts-download-files-button` (case step 8).
6. Verify the ZIP-preparation dialog appears (case step 9), with:
   - **Title**: exactly `` `Preparing ${bucket_name}.zip` `` — confirmed live, e.g.
     `"Preparing autotest-elitea1841-selectall-887278.zip"`.
   - **Progress bar**: MUI `LinearProgress`, `role="progressbar"`, determinate (`aria-valuemin="0"`,
     `aria-valuemax="100"`), value = `(current/total)*100`.
   - **File counter**: `"{current} of {total} files"` text.
   - **Current-file label**: `"Current: {full-relative-key}"` (e.g. `"Current: a1/sample.png"`) — confirmed
     live to show the full relative key including the `a1/` subfolder prefix, same finding as ELITEA-1840.
   - **Cancel button**: present, labelled "Cancel" (visibility-only — never clicked, out of this case's
     scope, same boundary as ELITEA-1840).
   - All handles reused as-is from ELITEA-1840's already-testid'd dialog internals — no new dialog-internal
     gaps for this case.
7. Verify the counter, current-file label, and progress bar advance **through the full range** as each of
   the 6 files is processed (case step 10 — the differentiator from ELITEA-1840's single-frame spot-check).
   **Confirmed live via an instrumented run** (network-delayed via `page.route()`-equivalent, exploration-only
   `window.fetch` wrapper for this analyst pass): a polled capture across the dialog's lifetime recorded the
   FULL monotonic sequence
   `"3 of 6 files" (valuenow=50) → "4 of 6 files" (valuenow=67) → "5 of 6 files" (valuenow=83) → "6 of 6 files"
   (valuenow=100)`, each paired with its own `Current: a1/{filename}` label update — not a single static
   frame. **Implementer caution**: immediately before the dialog unmounts, the counter/progress-bar briefly
   reset to `"0 of 0 files"` / `aria-valuenow="NaN"` for one poll tick (a harmless internal state-reset on
   teardown, not user-visible in the 2 clean non-delayed runs, not a defect) — assert against a captured
   monotonically-increasing SEQUENCE ending at `"6 of 6 files"`/`valuenow="100"`, not the dialog's final
   frame before it closes.
8. Verify upon completion: the dialog closes, and a ZIP file named exactly `` `{bucket_name}.zip` `` is
   downloaded (case step 11). Confirmed live 3/3 runs (2 clean + 1 instrumented) via `expect_download()`
   capturing the client-side blob-URL-anchor download (same architecture ELITEA-1840 already confirmed —
   not re-derived here). The generic app-wide success toast (`toast-message`, reused from
   ELITEA-1832/1840's precedent) was not independently re-confirmed with a fresh DOM query this run — it
   auto-dismisses too quickly to reliably poll after the fact (same admission ELITEA-1840's own AFS makes);
   not required by this case's own step text either (unlike 1840's Expected-Results axis, ELITEA-1841's step
   11 does not name the toast explicitly), so it is not part of this AFS's asserted scope.
9. Verify the downloaded ZIP's internal file list is **exactly** the 6 seeded file names — flattened to the
   ZIP root, **not** nested under `a1/` (case step 12). Confirmed live 3/3 runs via
   `zipfile.ZipFile(download.path()).namelist()`, e.g.
   `['sample.txt', 'sample_640x426.gif', 'sample.png', 'Q&A.docx.odt', 'Regression test cases.odt',
   'sharepoint.docx']` (order not fixed/asserted — the seeded set, as an unordered comparison, is; same
   flattening architecture ELITEA-1840 already confirmed via `downloadArtifactsAsZip` stripping
   `currentPrefix`).
10. Verify all 6 files are accessible and not corrupted inside the ZIP (case step 13). **Reuses ELITEA-1840's
    established proof pattern** (byte-identical content vs. the seeded constants — the strongest available
    signal that entries aren't truncated/corrupted, not merely `size > 0`), extended from 2 files to all 6,
    plus `zipfile.ZipFile.testzip()` returning `None` (no bad CRC) as an additional integrity check — new to
    this case, not present in 1840's implementation, and directly responsive to the case's own "not
    corrupted" wording. Confirmed live 3/3 runs: every entry's bytes matched the seeded content exactly,
    `testzip()` returned `None` every time.

## Expected Results
- Clicking the header "Select all" checkbox checks all 6 file rows in one action and lands the header
  checkbox itself in the fully-checked, non-indeterminate state.
- The toolbar `artifacts-download-files-button` transitions from disabled to enabled, tooltip text
  `"Download files"` (unchanged by selection completeness).
- Clicking the button opens `artifacts-zip-download-progress-dialog` with title `Preparing {bucket}.zip`, a
  determinate progress bar, a `"{current} of {total} files"` counter that progresses through the FULL range
  1→6, a `"Current: {full-relative-key}"` label, and a Cancel button.
- The dialog auto-closes on completion; a ZIP file named exactly `{bucket}.zip` downloads via a client-side
  JSZip-built blob-URL anchor click (no dedicated server-side ZIP endpoint).
- The ZIP contains exactly the 6 seeded files, flattened to the ZIP root, byte-identical to what was seeded,
  each readable and uncorrupted (`testzip()` clean).
- No console errors during the flow.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket "bucket-1" with subfolder "a1" containing exactly 6 named files | Precondition state exists | Test Data + Test Step 1 | `artifact_bucket` fixture + 6× `ArtifactAPI.upload_file()`; proven by Test Step 1's file-count assertion | asserted |
| Step 1: Navigate to Artifacts section in the sidebar | Artifacts page loads | Test Step 1 | Folded into direct bucket+folder navigation; page-load proven via breadcrumb + file-table assertions | asserted *(folded)* |
| Step 2: Click bucket-1, navigate to subfolder a1 | Subfolder a1 selected | Test Step 1 | Same navigation call; breadcrumb `{bucket} > a1` | asserted *(folded)* |
| Step 3: Verify file table displays 6 files | All 6 files listed | Test Step 1 | 6-row table + `"1 - 6 of 6"` pagination confirmed live 3/3 | asserted |
| Step 4: Click "Select all" checkbox in header row | All 6 rows become checked | Test Step 3 | Header-checkbox click, per-row states queried independently | asserted |
| Step 5: Verify all 6 file rows become checked | All rows checked | Test Step 3 | Same per-row query, confirmed live 3/3 | asserted |
| Step 6: Verify header checkbox shows filled/checked (not indeterminate) | Header checkbox fully checked | Test Step 3 | `Mui-checked` present / `MuiCheckbox-indeterminate` absent, read off the (to-be-added) header-checkbox testid | asserted |
| Step 7: Verify Download files icon active/enabled with tooltip "Download files" | Icon enabled, correct tooltip | Test Step 4 | `disabled` attribute drops; `aria-label` read confirmed static `"Download files"` text | asserted |
| Step 8: Click Download files icon | ZIP prep modal appears | Test Step 5 | Click fires `onDownloadFiles`/`startZipDownload`; dialog appearance confirmed live | asserted |
| Step 9: Verify "Preparing bucket-1.zip" modal — title, progress bar, file counter starting "1 of 6 files", current-file label, Cancel button | Modal shows all elements | Test Step 6 | Each element confirmed live via DOM query (reusing ELITEA-1840's already-testid'd dialog internals) | asserted |
| Step 10: Verify counter progresses through all 6 files (e.g. "2 of 6" ... "6 of 6") | Counter updates through all 6 | Test Step 7 | Polled instrumented capture: full monotonic `3 of 6 → 4 of 6 → 5 of 6 → 6 of 6` sequence, each with matching `valuenow`/current-file | asserted |
| Step 11: Verify modal closes + ZIP named "bucket-1.zip" downloaded on completion | ZIP downloaded, modal closes | Test Step 8 | `expect_download()` capture + dialog-hidden check, confirmed live 3/3 | asserted |
| Step 12: Verify ZIP contains all 6 files | All 6 files in ZIP | Test Step 9 | `zipfile.namelist()` exact-set match, confirmed live 3/3 | asserted |
| Step 13: Verify all files accessible and not corrupted inside the ZIP | Files open cleanly from ZIP | Test Step 10 | Byte-identical content vs. seeded constants + `testzip()` returning `None`, confirmed live 3/3 | asserted |
| Expected Final State: all 6 files downloaded as `bucket-1.zip`; progress modal correctly counts through all files; ZIP complete and not corrupted | Composite pass condition | Test Steps 3-10 | Combination of all above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | 0 console errors confirmed 3/3 runs (only the pre-existing, flow-unrelated Vite `stream.Stream` warning present, same as prior siblings' finding) | asserted |
| Fail criterion: "ZIP missing files / corrupted / progress counter incorrect" | Negative-space guard | Test Steps 9-10 | Exact-set namelist match + byte-identity + `testzip()` + full progress sequence together rule this out | asserted |

### Axis 2 — Observables asserted beyond the case
- **Header checkbox's own visual state (`Mui-checked` present, `MuiCheckbox-indeterminate` absent)** —
  *added: the case's own step 6 asks for this, but it is worth flagging as a genuinely new, previously-
  unexercised assertion (no prior artifacts case reads the header checkbox at all) rather than a trivial
  restatement of the per-row check.*
- **Toolbar download-button tooltip text is selection-completeness-INVARIANT** (`"Download files"` whether
  2-of-6 or 6-of-6 are selected) — *added: contrasts with the sibling delete-button tooltip which DOES vary
  ("Delete selected files" vs "Delete all files"); worth guarding since a future regression that made the
  download tooltip vary too would be a silent, easy-to-miss product change.*
- **Full monotonic progress-counter sequence (3-of-6 → 4-of-6 → 5-of-6 → 6-of-6), not a single spot-check
  frame** — *added: directly responsive to case step 10's explicit "progresses through all 6 files" wording,
  and a materially stronger proof than ELITEA-1840's single-frame check (justified there only because 2
  files barely exhibits "progression").*
- **`zipfile.testzip()` returning `None`** — *added: a stronger, purpose-built "not corrupted" signal (CRC
  validation) than byte-equality alone; byte-equality proves content correctness, `testzip()` proves
  structural ZIP integrity — together they fully answer case step 13's two distinct claims ("accessible"
  and "not corrupted").*
- **3/3 identical reproductions** (2 clean + 1 instrumented), each from a fresh bucket + fresh page
  navigation — *added: rules out session/DOM-state carryover before handing off as `ready-for-automation`,
  matching the family's established bar (ELITEA-1840 required 2/2 clean).*
- **The left-panel bucket-list transient-empty race is the SAME already-documented ELITEA-1808 finding, not
  a new defect** — *added: explicitly cross-referenced here so a future implementer doesn't mistake it for
  something new to this case or file a duplicate report.*

## Cleanup
1. Delete each seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)` in the `artifact_bucket` fixture's
   own teardown. **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636))**: this call 404s in the current
   dev environment, so the bucket actually leaks; not this case's concern, do not re-file.
2. No other entities are created by this case.
3. **This exploration run's own artifacts** (not part of the automated test): 3 buckets created via direct
   API calls in the `Private` project (id 399) — `autotest-elitea1841-selectall-887278`,
   `autotest-elitea1841-selectall2-072946`, `autotest-elitea1841-selectall3-303896` — each containing
   `a1/{Q&A.docx.odt, Regression test cases.odt, sharepoint.docx, sample_640x426.gif, sample.png,
   sample.txt}`. Left in place per this repo's existing convention (250+ pre-existing un-deleted `autotest-*`
   buckets already present in `Private`); safe to delete any time via `ArtifactAPI.delete_bucket(...)` (will
   itself 404 per #636 — a human/script would need the S3-console-level cleanup #636 describes).
4. Local exploration screenshot (repo root, untracked), attached as evidence for this AFS:
   `ELITEA-1841-step9-10-zip-progress-dialog-midflight.png` (mid-flight frame — title, progress bar at 50%,
   "3 of 6 files", "Current: a1/sample.png", Cancel button).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md` § Analyst slot) is **testid-only, no
fallback ladder**. Every row's Provenance was checked against a fresh `git fetch origin` in `../EliteaUI`
this run (`origin/main` vs `origin/automation/testids` checked independently).

| Element | testid | Provenance | Status | Notes |
|---|---|---|---|---|
| Toolbar "Download files" (bulk) button | `artifacts-download-files-button` | on-main ✓, on-testids ✓ | existing, reuse | Already declared as `ArtifactsPage.download_files_button`; confirmed live enabled/disabled toggling on 0→6 selection, tooltip text invariant across partial/full selection |
| Toolbar "Download files" tooltip wrapper (aria-label anchor) | `artifacts-download-files-tooltip` | **added (ELITEA-1841, implementer)** — on-testids ✓ (this commit) | **added (ELITEA-1841, implementer)** | **Implementer amendment (Phase 2 exploration):** confirmed live the existing `download_files_button` testid (row above) resolves to the INNER `<button>` (`ArtifactTableToolbar.jsx`), while MUI's `<Tooltip title="Download files">` clones its static `aria-label` onto the WRAPPING `<Box component="span">` one level up — a genuinely different DOM node with zero testid of its own (confirmed live via `element.attributes` dump: the inner button carries only `class`/`tabindex`/`type`/`data-testid`, no `aria-label`). The AFS's original Concrete Handles row for `download_files_button` said "tooltip text invariant... confirmed via aria-label read on the wrapping `<span>`" without flagging that reading it compliantly (testid-only, no raw-selector parent traversal) requires its own testid — this row closes that gap. `ArtifactTableToolbar.jsx` is a page-local, single-consumer component (not shared — confirmed via `grep -rl "ArtifactTableToolbar" src`), so the testid is hardcoded directly in JSX, no caller-prop threading needed (unlike the header checkbox row below, which IS a shared-component case). |
| ZIP-download progress dialog (outer) | `artifacts-zip-download-progress-dialog` | on-testids ✓, on-main pending human cherry-pick (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.zip_download_progress_dialog` |
| ZIP dialog title | `artifacts-zip-download-progress-title` | on-testids ✓ (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.zip_download_progress_title` |
| ZIP dialog progress bar | `artifacts-zip-download-progress-bar` | on-testids ✓ (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.zip_download_progress_bar`; `aria-valuenow` confirmed live progressing 50→67→83→100 across this case's 6-file flow |
| ZIP dialog file counter | `artifacts-zip-download-progress-counter` | on-testids ✓ (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.zip_download_progress_counter`; confirmed live cycling through `3 of 6` → `6 of 6` (full range, not spot-checked) |
| ZIP dialog current-file label | `artifacts-zip-download-progress-current-file` | on-testids ✓ (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.zip_download_progress_current_file`; confirmed live showing full relative key per frame (e.g. `a1/sharepoint.docx`) |
| ZIP dialog Cancel button | `artifacts-zip-download-progress-cancel-button` | on-testids ✓ (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.zip_download_progress_cancel_button`; visibility-only, never clicked |
| File row (per file) | `artifacts-file-row` | on-main ✓, on-testids ✓ | existing, reuse | Already declared |
| Per-row checkbox | `artifacts-file-checkbox-{filename}` | on-testids ✓ (ELITEA-1840) | existing, reuse | Already declared as `ArtifactsPage.ARTIFACT_FILE_CHECKBOX` template + `is_file_checkbox_checked()`; confirmed live all 6 land `Mui-checked` after one header-checkbox click |
| **Header "Select all" checkbox** | `artifacts-select-all-checkbox` | **added (ELITEA-1841, implementer) — on-testids ✓ (this commit), on-main pending human cherry-pick** | **added (ELITEA-1841, implementer)** | Root cause (confirmed live via DOM query — the header checkbox's wrapping `<span class="MuiCheckbox-root">` has `data-testid: null`): `GridTableHeader.jsx` (`src/[fsd]/entities/grid-table/ui/GridTableHeader.jsx:26-32`) renders `<Checkbox.BaseCheckbox checked={isAllSelected} indeterminate={isIndeterminate} onChange={onSelectAll} .../>` with **no `data-testid`/testid-prop threaded through at all**. `GridTableHeader` is a **shared component** (7 consumers: `SecretsTable`, `TokensTable`, `UsersTable`, `BucketAccessTable`, `DataTable`, `NotificationTable`, and this case's `ArtifactTable`) — same shared-component shape as `GridTableRow` (which ELITEA-1840 already extended with a caller-supplied `checkboxTestId` prop for the identical reason). Per the project's shared-component testid ruling, the fix is a new caller-supplied prop (`selectAllCheckboxTestId`), threaded to `<Checkbox.BaseCheckbox data-testid={selectAllCheckboxTestId} .../>`, wired **only** at `ArtifactTable.jsx`'s `<GridTableHeader ...>` call site (`src/pages/Artifacts/component/ArtifactTable.jsx:520-527`) as `selectAllCheckboxTestId="artifacts-select-all-checkbox"` — not at the other 6 call sites (out of this case's scope, same testid-scope rule ELITEA-1840's checkbox fix already followed). **Implementer verification (this run):** committed + pushed to `origin/automation/testids` (`EliteaAI/EliteaUI@2cd4fad5`), then live-verified via Playwright MCP against the running dev server: the testid renders on the same wrapping `<span>` shape as the per-row checkboxes (`Mui-checked`/`MuiCheckbox-indeterminate` classes), starts unchecked/non-indeterminate at 0 selected, and a real click (`browser_click`, not a synthetic JS `.click()`) lands it `Mui-checked` with all 6 row checkboxes independently confirmed `Mui-checked` and the toolbar download button enabled — matching every fact this row and Test Step 3 already claimed. **State-read technique** (per the established `is_file_checkbox_checked()` precedent, ELITEA-1840): read the `class` attribute off the SAME testid-anchored `<span>` — `Mui-checked` present + `MuiCheckbox-indeterminate` absent = fully checked (case step 6); confirmed live this run (via an exploratory partial-deselect) that MUI DOES add a distinguishing `MuiCheckbox-indeterminate` class in the partial-selection state, so this is a real 3-state signal, not a no-op class check. |
| Success toast (app-wide generic) | `toast-message` | on-main ✓ | existing, not independently re-verified this run | Already declared as `ArtifactsPage.success_toast_message`; not re-confirmed with a fresh DOM query this run (auto-dismisses too fast to reliably poll after `expect_download()` resolves — same admission ELITEA-1840's AFS makes); not required by this case's own step text (case step 11 doesn't name the toast) |

## Network Behavior
- Opening the bucket/subfolder: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id={id}&format=json` →
  `200 OK`. Fires once per navigation, before the file table renders. Confirmed live 3/3 runs the response
  body already contains full bucket data even during the transient left-panel "No buckets" render (§ Test
  Step 1 note) — the race is render-timing, not a missing/late API response.
- **Each of the 6 selected files' download** (fired **sequentially** — confirmed via live network-request
  ordering, same `downloadArtifactsAsZip` synchronous `for`-loop architecture ELITEA-1840 already confirmed
  via source read): `GET {ELITEA_URL}/api/v2/artifacts/artifact/default/{project_id}/{bucket}/{url-encoded-key}`
  → `200 OK` ×6, e.g.
  `.../artifact/default/399/{bucket}/a1%2Fsample.txt`,
  `.../a1%2Fsample_640x426.gif`, `.../a1%2Fsample.png`, `.../a1%2FQ%26A.docx.odt`,
  `.../a1%2FRegression%20test%20cases.odt`, `.../a1%2Fsharepoint.docx` (exact order varies slightly by run —
  the case doesn't require a fixed processing order, only that all 6 complete).
- **No other network request fires between the toolbar-button click and the ZIP download completing** —
  confirmed live 3/3 runs via network-request capture filtered on `artifact/default`: exactly 6 GETs, no
  POST/PUT, no dedicated ZIP-building endpoint (same "no server-side ZIP work" architectural fact ELITEA-1840
  established, now independently reconfirmed at N=6 instead of N=2).
- No console errors any run (only the pre-existing, flow-unrelated Vite `stream.Stream` module-
  externalization warning present, identical to prior siblings' finding — not caused by this flow).

## Known Defects Found During Exploration
None found. Live product behavior matched the case's expected behavior across all 3 runs: one header-
checkbox click selects all 6 rows, the header checkbox itself correctly reflects fully-checked/non-
indeterminate state, the toolbar button enables with an invariant tooltip, the ZIP dialog shows the correct
title/progress bar/counter/current-file/Cancel elements and progresses through the full 1-to-6 range, the
dialog auto-closes and a correctly-named ZIP downloads on completion, and the ZIP contains exactly the 6
seeded files (flattened, byte-identical, CRC-clean). The transient left-panel "No buckets created yet" render
(§ Test Step 1) is the SAME already-documented, self-correcting ELITEA-1808 finding — not re-filed. No
CLARIFICATION filed either — the case's `bucket-1`/`a1` placeholder naming was already established as
intentional TMS-authoring shorthand by prior sibling runs, re-confirmed (not re-derived) this run.

## Blocked Steps
None. The single `testid needed:` row in § Concrete Handles (the header "Select all" checkbox) is
implementer work (per `.agents/role-overrides.md` § Analyst slot: not softened into a MINOR defect or a
note; the AFS is the work order) — an additive, well-precedented shared-component prop addition (identical
shape to ELITEA-1840's already-merged `checkboxTestId` fix on the sibling `GridTableRow` component), not an
environment/access/data blocker.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **New test file** (not an extension of `test_artifacts_download_multiple_files_zip.py` — see § Coverage
  Map vs ELITEA-1840): `automation/tests/ui/artifacts/test_artifacts_download_all_files_select_all_zip.py`,
  class `TestArtifactDownloadAllFilesSelectAllZip`, e.g.
  `test_download_all_files_via_select_all_as_zip`.
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`) — already has every ZIP-dialog
  handle from ELITEA-1840 (reuse as-is). Add:
  - `select_all_checkbox = LocatorDescriptor(testid="artifacts-select-all-checkbox")` (once the implementer
    adds the testid per § Concrete Handles).
  - `click_select_all_checkbox()` — clicks the header checkbox.
  - `is_select_all_checkbox_checked()` / `is_select_all_checkbox_indeterminate()` — read `Mui-checked` /
    `MuiCheckbox-indeterminate` off the class attribute of the same testid-anchored locator, same technique
    as the existing `is_file_checkbox_checked()` (ELITEA-1840).
  - Reuse `get_checkbox_states()`, `download_files_button`, all `zip_download_progress_*` handles, and
    `capture_requests_matching()` as-is — no changes needed to those.
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`) and
  `ArtifactAPI.upload_file()` (`automation/api/client.py:1282`) to seed all 6 files — no browser-driven
  upload needed (confirmed live, § Test Data).
- Navigation: reuse `ArtifactsPage.navigate_to_bucket_folder()` as-is (built-in issue #638 retry mitigation).
- **Observing the full progress-counter sequence (case step 10) is the one genuinely non-obvious part of
  this case**, same underlying technique as ELITEA-1840 but with a stronger assertion shape: with 6 small
  files the real flow completes in well under 2 seconds — too fast for a naive script to catch more than
  maybe one intermediate frame. Use `page.route()` intercepting `**/artifact/default/**` and delaying
  `route.continue_()` by a short fixed amount (this run used 600ms, confirmed reliable) for **this test
  only**, then poll the counter/progress-bar/current-file trio at a short fixed interval (this run used
  150ms) while the dialog is visible, collecting a list of frames. Assert the collected counter sequence is
  non-decreasing and its final non-`"0 of 0"` value is `"6 of 6 files"`/`valuenow="100"` — **do not** assert
  against the dialog's literal last-observed frame before it closes, since this run confirmed a harmless
  `"0 of 0 files"`/`valuenow="NaN"` reset fires for one tick immediately before unmount.
- "Not corrupted" assertion (case step 13): reuse ELITEA-1840's byte-identical-content technique (compare
  each of the 6 entries' bytes to the exact seeded content constants), and additionally call
  `zipfile.ZipFile.testzip()` and assert it returns `None` — a purpose-built CRC-integrity check new to this
  case, directly responsive to the case's own "not corrupted" wording.
- Cancel-button flow is out of this case's scope (visibility only, same boundary as ELITEA-1840).
- Do **not** fold this case's select-all coverage back into `test_artifacts_download_multiple_files_zip.py`
  — see § Coverage Map vs ELITEA-1840 for why a fresh file is the correct call.
