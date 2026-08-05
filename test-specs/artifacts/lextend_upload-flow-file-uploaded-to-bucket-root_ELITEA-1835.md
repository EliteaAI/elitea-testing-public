# Test Case: Upload Flow – File Uploaded to Bucket Root When Bucket (Not Subfolder) Is Selected

## Metadata
- **TMS ID**: ELITEA-1835
- **Linked Story**: [EliteaAI/elitea-testing-public#260](https://github.com/EliteaAI/elitea-testing-public/issues/260) (tracking issue)
- **Priority**: medium (as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399, dev server confirmed
  up and already synced to `origin/main` at session start — no restart needed).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **extend-existing** — case executed end-to-end live (all 17 case steps + all 3
  preconditions verified against a real, freshly-created bucket:
  `autotest-elitea1835-93017`, `Private` project). Zero product defects, zero console errors.
  One CLARIFICATION filed
  ([#674](https://github.com/EliteaAI/elitea-testing-public/issues/674)) for case-text drift
  on step 11 (the modal's separate "description" line does NOT name the bucket at root — see
  § Known Defects). This case's own observable — bucket-menu upload path pre-fills the bucket
  ROOT correctly (not a stale subfolder) when the bucket, not a subfolder, is the currently
  active selection — is a **partial** overlap with an already-merged spec covering the exact
  same code path via a different (but behaviorally-equivalent) route to reach it. See
  § Overlap check for the full dedup/extend boundary reasoning, including a **live,
  pristine re-verification** (not just a read of the covering spec) that closes the
  dispatch's own flagged risk: whether 1824's "isolation check" — reached via an
  Escape-and-recovery workaround after first triggering defect #649 — actually generalizes to
  the case's own literal scenario (a bucket clicked at root as a genuinely FIRST action,
  never having opened any upload dialog in-session before). It does; confirmed live in a
  brand-new bucket this run.

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py`
(ELITEA-1824, merged to `automation/base`, already extended once for ELITEA-1827's nested-path
case — Steps 47-54, lines 649-698) was read in full (724 lines) before this run, alongside its
AFS (`test-specs/artifacts/l2_upload-three-options-verify-selection_ELITEA-1824.md`) and
ELITEA-1808's AFS/test
(`test-specs/artifacts/l2_create-bucket-path1-and-upload-file_ELITEA-1808.md` /
`test_artifacts_create_bucket_upload_file.py`), per the dispatch's own heads-up.

**ELITEA-1808 — confirmed NOT a match.** 1808 drives the bucket-menu "Upload files" entry
point, but ONLY from a **freshly-created, empty bucket** — `currentPrefix` is empty because no
subfolder exists yet at all, not because the user deliberately re-selected the bucket root
after having browsed a subfolder. 1808 never has a real subfolder to "accidentally" land a
file in, so it structurally cannot exercise (or accidentally mask) defect #649, and never
touches the case's own steps 16-17 (negative-presence check in a subfolder) at all — there is
no subfolder in 1808's bucket to check.

**ELITEA-1824 — the real candidate, examined in depth.** 1824's own "isolation check" for
defect #649 (AFS § Known Defects, "2 controlled passes") is implemented as a literal recovery
sequence in the shipped test (lines 426-454):
1. `close_upload_path_dialog()` (Escape) — abandons a dialog that was already showing the BUG
   (path incorrectly inherited `"{bucket}/a1/"` because the user had just been browsing `a1`).
2. `click_bucket_row(bucket_name)` (line 441) — re-selects the bucket at its own root,
   resetting `currentPrefix` to `""`.
3. `open_bucket_menu(bucket_name)` + `click_bucket_menu_upload_files_item([md_path])`
   (lines 442-445) — re-opens the SAME bucket-menu "Upload files" entry point.
4. `get_upload_path_normalized_prefix() == f"{bucket_name}/"` (lines 447-454) — asserts the
   Path field now correctly reads bucket-root-only. **This is a real, already-shipped
   assertion of the exact Path-field observable ELITEA-1835's own step 10 wants.**
5. Step 33 (lines 456-476) clicks Upload and asserts the PUT lands at
   `{bucket_name}/{MD_FILE_NAME}` (root key) with an explicit negative check that it is NOT
   nested under `a1/` — matching case step 12 and the placement half of steps 14-15.
6. Lines 483-492 assert the breadcrumb shows the bucket root only (no folder crumb) —
   matching case step 3 / the placement half of step 14, though asserted **after** the
   upload completes, not immediately after re-selecting the bucket (see § Gap assertions).
7. Lines 494-501 assert `sample.md` is listed at bucket root — matching case steps 14-15
   (substituting the covering test's own `sample.md` for the case's literal `sample.png` —
   see § Test Data for why this substitution is required, not incidental).
8. Lines 550-565 (Steps 41-42) later click into the `a1` subfolder and assert exactly 2 files
   (`sample.txt`, `sample.png`) are present **and that `sample.md` is explicitly NOT
   listed** — this is the byte-for-byte same mechanism (and even the same negative-presence
   assertion shape) as case 1835's own steps 16-17.

**What genuinely remains uncovered — the actual gap this AFS extends:**
1. **Case step 11 (modal description text)** — 1824 never asserts this element at all; it has
   no testid, and (confirmed live this run, see § Known Defects) its live text does not match
   what the case's own step 11 implies. This alone is enough to rule out `already-covered`.
2. **Sequencing** — 1824's existing assertions of "bucket selected at root" / "breadcrumb
   root-only" (item 6 above) happen **after** the recovery upload completes, not
   **immediately after** re-selecting the bucket and **before** opening the bucket-menu, which
   is the literal order of case 1835's own steps 2-3-4. A cheap, non-redundant addition closes
   this precisely (see § Gap assertions).

**The dispatch's own flagged risk, resolved via live re-verification (not just reading the
covering spec):** is 1824's "isolation check" — reached via an Escape-and-recovery workaround
**after** defect #649 was first triggered — representative of the case's own literal scenario,
where the user clicks the bucket at root as a **first** action, having never opened any
upload dialog in the session? Read alone, `useFileUpload.hooks.js`'s `computeFullPath()`
reads `currentPrefix`'s CURRENT value only, with no memory of how it got there — so the two
routes should be behaviorally identical. Rather than trust that source-reading argument alone,
this run reproduced the exact case-1835 scenario from scratch in a **brand-new, pristine
bucket** (`autotest-elitea1835-93017`) that had never seen defect #649 triggered in-session:
uploaded `sample.png` into a fresh `a1` subfolder via the TOOLBAR entry point (establishing the
precondition), clicked the bucket's own breadcrumb label to return to root as a genuinely
**first** action, then invoked the bucket-menu "Upload files" item for the first time ever in
that session. Result: Path field correctly read `autotest-elitea1835-93017/` (root-only, zero
subfolder leakage), the PUT landed at
`/artifacts/s3/autotest-elitea1835-93017/sample-root.png` (root key, confirmed via
`browser_network_requests`), and the uploaded file was confirmed present at root and **absent**
from `a1` (screenshot:
`ELITEA-1835-step16-17-sample-root-absent-in-a1.png`). This confirms live, not just by
argument, that 1824's recovery-path proof generalizes to the case's own literal fresh-click
scenario — closing exactly the risk the dispatch called out.

**Dedup verdict (Rule 6):** partial overlap — most of the case's 17 steps are already proven,
live-reproduced-fresh, and shipped in the covering test; a small, well-defined residual (the
step-11 description-text assertion + a minor sequencing addition) remains. This is the
"small number of missing assertions on an existing state-machine test" shape `extend-existing`
exists for (per `.agents/memory/qa-engineer/
extend_existing_means_insert_into_same_test_not_sibling_method.md`), not a distinct fresh
scenario and not a full duplicate — see § Gap assertions for the precise insertion points.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Bucket "bucket-1" exists with subfolder "a1" — confirmed live (again) as a case-text
  placeholder, not a literal fixture name (same finding as every sibling AFS in this folder).
  The covering test's own `artifact_bucket` fixture + its own Steps 2-11 (which upload
  `sample.txt` into a freshly-typed `a1` subfolder via the center empty-state button) already
  supply this precondition in full by the time the recovery sequence (the insertion point for
  this extension) runs — no new bucket or subfolder creation needed.
- Test file "sample.png" is available for upload (case's own literal test data) — **but see
  § Test Data for why the extension re-uses the covering test's own `sample.md` /
  `MD_FILE_NAME` instead of literally uploading a second `sample.png`**, a required
  substitution, not a shortcut.

## Test Data

### reuse-existing (from the covering test's own fixtures/constants)
- **Bucket**: the covering test's `artifact_bucket` fixture (`bucket_name` local var) — do
  **not** create a second bucket for this extension.
- **File**: the covering test's own `MD_FILE_NAME` (`"sample.md"`) / `md_path`, already
  written to `tmp_path` and already the exact file the recovery sequence (lines 440-454)
  uploads. **Why not the case's own literal `sample.png`**: `PNG_FILE_NAME` (`"sample.png"`)
  is already uploaded into `a1/` by the covering test's own EARLIER, unrelated step (its
  original toolbar-upload step, lines ~313-360) — confirmed live this run via source read of
  `useFileUpload.hooks.js` that the client-side duplicate check is scoped to the TARGET
  folder/prefix, not the whole bucket, so re-uploading `sample.png` to the bucket ROOT would
  NOT trigger a "Resolve duplicates" dialog — but it WOULD make case 1835's own steps 16-17
  ("verify sample.png is NOT in subfolder a1") assert something **false**, since a
  same-named `sample.png` already legitimately lives in `a1/` for a completely unrelated
  reason. Reusing the covering test's own `sample.md` (already the exact file its Step 33
  recovery-upload targets, already proven absent from `a1/` at Steps 41-42) is the only way
  to keep the negative-presence assertion meaningful inside the shared-bucket state this
  extension necessarily inherits. The file's own type (Markdown vs PNG) is incidental —
  case 1835's steps never assert the Type column, only presence/absence and Path-field text,
  both of which are file-content-independent.

### generate-per-test
None — this extension introduces no new literals; it inserts assertions at existing
insertion points using data the covering test already generates.

No `reuse-existing` fixture is needed beyond what's already documented above — same reasoning
as every sibling AFS: this extension rides entirely on the covering test's own already-scoped,
function-level bucket fixture and file constants.

## Test Steps

*(Steps below are the case's own 17 steps, executed live this run against a **fresh, isolated**
bucket built via the UI "New Bucket" form for exploration purposes —
`autotest-elitea1835-93017`, `Private` project, project id 399 — deliberately NOT reusing any
prior session's leftover state, per the reproducing-issues discipline of re-verifying in a
pristine context. § Gap assertions maps the two genuinely-missing pieces onto precise
insertion points in the covering test; everything else maps onto lines already shipped and
merged.)*

1. Navigate to the Artifacts section in the left sidebar (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible. **Already asserted** by the covering
     test's own Step 1 (unchanged).
2. Click on "bucket-1" in the bucket list — verify "bucket-1" is highlighted at the root
   level (case step 2).
   - **Verify (live this run)**: clicked the bucket's own breadcrumb label
     (`artifacts-breadcrumb-bucket-label`) to return to root from inside `a1` — URL became
     `?bucket=autotest-elitea1835-93017` (no `folder` param), confirmed via
     `browser_network_requests`/URL read.
   - **Covered by**: the covering test's own recovery sequence, line 441
     (`click_bucket_row(bucket_name)`) — same underlying action (re-selects the bucket at
     root, resets `currentPrefix`). **Gap**: the covering test does not immediately assert
     `is_bucket_selected(bucket_name) == True` at this exact point (only later, at line
     518 in a DIFFERENT, subsequent click) — see § Gap assertions for the precise insertion.
3. Verify the main panel header displays "bucket-1" (no subfolder path) (case step 3).
   - **Verify (live this run)**: breadcrumb showed `autotest-elitea1835-93017` with no folder
     crumb, confirmed via snapshot immediately after the root-click.
   - **Covered by**: the covering test asserts this exact observable at lines 483-492, but
     only **after** the recovery upload completes (Step 35), not immediately after the
     root-click and before opening the bucket-menu — see § Gap assertions for the precise,
     earlier insertion this case's own step ordering wants.
4. Hover over "bucket-1" in the left panel and click the 3-dot (ellipsis) / actions icon
   (case step 4).
   - **Verify (live this run)**: dot-menu button (`bucket-menu-{name}-menu-button`) became
     visible only after hovering the row (hover-gated, confirmed via bounding-rect read),
     then opened on click.
   - **Covered by**: the covering test's own `open_bucket_menu(bucket_name)` call, line 442
     (existing method, ELITEA-1808/1824). **Already asserted.**
5. Verify a dropdown menu appears with options including "Upload files" (case step 5).
   - **Verify (live this run)**: menu showed "Upload files", "Rename", "Pin to top",
     "Delete" — confirmed via snapshot.
   - **Covered by**: the covering test's own `bucket_menu_upload_files_menuitem.is_visible()`
     assertion (Steps 25-26 block, line ~387-391). **Already asserted.**
6. Click "Upload files" (case step 6).
   - **Verify (live this run)**: native file-chooser fired immediately (Playwright modal
     state, no loading delay).
   - **Covered by**: the covering test's own `click_bucket_menu_upload_files_item([md_path])`
     call, lines 443-445. **Already asserted** (`expect_file_chooser` fires — same mechanism
     the covering test's own Steps 27-29 already prove, and the recovery sequence re-uses
     verbatim).
7. Verify the system file explorer/Open dialog window opens immediately (case step 7).
   - **Covered by**: same observable as step 6 (folded). **Already asserted.**
8. Navigate to the test data folder and select "sample.png" and click "Open" (case step 8).
   - **Verify (live this run)**: selected a distinct file (`sample-root.png` this run,
     `sample.md`/`MD_FILE_NAME` in the shipped extension — see § Test Data for why).
   - **Covered by**: `set_files([...])` on the recovery sequence's file-chooser, line 444.
     **Already asserted** (mechanism only — the exact filename substitution is this
     extension's own documented adjustment).
9. Verify the "Upload files to ..." modal opens (case step 9).
   - **Covered by**: `wait_for_upload_path_dialog()`, line 446. **Already asserted.**
10. Verify the Path field displays "bucket-1/" (reflecting the bucket root, not any
    subfolder) (case step 10).
    - **Verify (live this run)**: Path field read `autotest-elitea1835-93017/` exactly —
      screenshot `ELITEA-1835-step10-11-path-and-description-at-root.png`.
    - **Covered by**: `get_upload_path_normalized_prefix() == f"{bucket_name}/"`, lines
      447-454 — **this is the case's own single most load-bearing assertion, and it is
      already shipped, merged, and live-reconfirmed this run in a genuinely fresh (not
      recovery-only) context.** Fully asserted.
11. Verify the modal description indicates files will be uploaded to "bucket-1/" (case step
    11).
    - **Verify (live this run) — CASE-TEXT DRIFT FOUND**: the modal's separate description
      `<Typography>` (distinct DOM node from the Path field, confirmed via source,
      `UploadPathDialog.jsx` lines 32-42/65-73) reads a GENERIC string with **no bucket name
      at all** when `currentPrefix` is empty (root): *"Files will be uploaded to the selected
      bucket. Optionally, enter a folder path to organize your files. Use "/" to create
      nested folder(s)."* The bucket name is only interpolated into this description when
      `currentPrefix` is non-empty (inside a subfolder). Filed as CLARIFICATION
      [#674](https://github.com/EliteaAI/elitea-testing-public/issues/674) — this is the
      live product's correct, intentional behavior (a deliberate `!currentPrefix` branch in
      source), not a regression; the case's own expected-result text should be corrected to
      describe the Path FIELD (which does correctly show `bucket-1/`), not this separate
      description line.
    - **Covered by**: **nothing — genuine gap.** This element has zero testid
      (`testid needed: artifacts-upload-path-description-text`, `UploadPathDialog.jsx`
      lines 65-73) and 1824 never asserts it. See § Gap assertions.
12. Click "Upload" (case step 12).
    - **Covered by**: Step 33 (lines 456-476) — clicks
      `click_upload_path_upload_button_and_capture_response()`, asserts `200 OK`.
      **Already asserted.**
13. Verify a success notification is displayed (case step 13).
    - **Covered by**: line 478-481 (`success_toast_message` exact-text assertion).
      **Already asserted.**
14. Verify the main panel displays "bucket-1" root level contents (case step 14).
    - **Covered by**: lines 483-492 (breadcrumb root-only, post-upload). **Already asserted**
      (for the file this extension actually uploads — `sample.md`, not a literal
      `sample.png` — see § Test Data).
15. Verify "sample.png" is listed in the file table at the root level of "bucket-1" (case
    step 15).
    - **Verify (live this run)**: the uploaded file (`sample-root.png`) appeared in the root
      file table (Type "PNG Image", 38 B) alongside the pre-existing `a1` folder row.
    - **Covered by**: lines 456-472 (PUT URL confirms root placement, explicit negative
      check it is NOT nested under `a1/`) + lines 494-501 (`file_exists(MD_FILE_NAME)` at
      root). **Already asserted** (file-literal substitution as above).
16. Verify "sample.png" is NOT listed inside subfolder "a1" (case step 16).
    - **Verify (live this run)**: navigated into `a1` via
      `[data-testid="artifacts-tree-item-a1/"]`; file table showed only the ORIGINAL
      precondition file, not the newly-uploaded one — screenshot
      `ELITEA-1835-step16-17-sample-root-absent-in-a1.png`.
    - **Covered by**: lines 550-565 (Steps 41-42 — exactly 2 files in `a1`
      [`sample.txt`, `sample.png`] + explicit `file_exists(MD_FILE_NAME) == False` while
      viewing `a1`). **Already asserted** — this is the byte-for-byte same
      negative-presence mechanism case 1835's own step 16 wants.
17. In the left panel click on subfolder "a1" and verify "sample.png" is not present there
    (case step 17).
    - **Covered by**: same as step 16 (lines 528, 562-565 — `click_tree_item("a1/")` then
      the negative `file_exists` check). **Already asserted** (decomposed — click + check
      are one combined observable, matching the case's own single step 17).

## Expected Results
- Clicking the bucket at its own root (not a subfolder) and invoking the bucket-menu's
  "Upload files" item correctly pre-fills the dialog's Path field with the bucket root only
  (`"{bucket}/"`), with zero leakage from any previously-browsed subfolder — **already proven
  live and shipped** (covering test lines 447-454), and **independently re-confirmed this run
  in a genuinely fresh, non-recovery context** (no prior in-session trigger of #649).
- The uploaded file lands at the bucket root (confirmed via the upload PUT's own URL, not
  just DOM inference) and is correctly absent from the subfolder — already proven and shipped
  (lines 456-476, 550-565).
- The modal's separate description text, however, does NOT literally interpolate the bucket
  name at root (case-text drift, CLARIFICATION #674) — this is the one genuinely new
  observable this extension surfaces, currently un-asserted and un-testid'd anywhere in the
  covering suite.
- No console errors during the flow (confirmed live: 0 errors across this run's own
  exploration pass, consistent with the covering test's own existing final side-channel
  check).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture, reused as-is | asserted *(via extend)* |
| Precondition: bucket-1 exists w/ subfolder a1 | Bucket + subfolder ready | Preconditions + Test Data | covering test's own `artifact_bucket` fixture + its own Steps 2-11, reused as-is | asserted *(via extend — no new bucket/subfolder)* |
| Precondition: sample.png available | File exists locally | Preconditions + Test Data | covering test's own `MD_FILE_NAME`/`md_path` substituted in — see § Test Data for why the literal png cannot be reused here | asserted *(via extend, documented substitution)* |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | covering test's own Step 1, unchanged | asserted *(already proven)* |
| Step 2: Click bucket-1 at root; verify highlighted | Bucket selected at root | Test Step 2 | covering test line 441 (`click_bucket_row`) for the action; `is_bucket_selected()` NOT yet asserted at this exact point | asserted *(action)* / gap *(selected-state assertion — see Gap Insertion A)* |
| Step 3: Verify breadcrumb shows "bucket-1" only | Root breadcrumb | Test Step 3 | covering test lines 483-492, but only AFTER the upload completes, not before opening the menu | asserted *(post-hoc, later in the flow)* / gap *(earlier assertion — see Gap Insertion A)* |
| Step 4: Hover bucket-1, click 3-dot menu | Dropdown appears | Test Step 4 | covering test line 442 (`open_bucket_menu`) | asserted *(already proven)* |
| Step 5: Verify dropdown has "Upload files" | Menu item visible | Test Step 5 | covering test lines 387-391 | asserted *(already proven)* |
| Step 6: Click "Upload files" | File explorer opens | Test Step 6 | covering test lines 443-445 | asserted *(already proven)* |
| Step 7: Verify file explorer opens | Explorer open | Test Step 7 | same observable as step 6 | asserted *(decomposed, already proven)* |
| Step 8: Select sample.png, click Open | File selected | Test Step 8 | covering test line 444 (`set_files`), using `md_path` not a literal png — see § Test Data | asserted *(mechanism proven; literal substitution documented)* |
| Step 9: Verify "Upload files to ..." modal opens | Modal visible | Test Step 9 | covering test line 446 | asserted *(already proven)* |
| Step 10: Verify Path field shows "bucket-1/" | Path pre-fills root | Test Step 10 | covering test lines 447-454 — **the case's own load-bearing assertion, already shipped** | asserted *(already proven + live-reconfirmed fresh this run)* |
| Step 11: Verify modal description indicates "bucket-1/" | Description text | Test Step 11 | **nothing** — genuine gap, no testid exists | gap *(filed [#674](https://github.com/EliteaAI/elitea-testing-public/issues/674); `testid needed: artifacts-upload-path-description-text` — see Gap Insertion B)* |
| Step 12: Click Upload | Upload completes | Test Step 12 | covering test lines 456-476 | asserted *(already proven)* |
| Step 13: Verify success notification | Toast shown | Test Step 13 | covering test lines 478-481 | asserted *(already proven)* |
| Step 14: Verify root level contents shown | Root view | Test Step 14 | covering test lines 483-492 | asserted *(already proven)* |
| Step 15: Verify sample.png listed at root | File at root | Test Step 15 | covering test lines 456-472 (PUT URL) + 494-501 (`file_exists` at root) | asserted *(already proven, file-literal substitution documented)* |
| Step 16: Verify sample.png NOT in subfolder a1 | Absent from a1 | Test Step 16 | covering test lines 550-565 (Steps 41-42) — same negative-presence mechanism | asserted *(already proven)* |
| Step 17: Click a1, verify sample.png absent | Same as step 16 | Test Step 17 | covering test lines 528, 562-565 | asserted *(decomposed, already proven)* |
| Expected Final State: file at root, absent from subfolder, path pre-fills root | Composite pass condition | Test Steps 10, 15-17 | combination of the above, all already shipped and merged | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | covering test's own final console-error check (unchanged, extend the docstring to mention this case) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Live, pristine re-verification of the covering test's own dedup claim** — *added: rather
  than trust that 1824's Escape-and-recovery isolation-check generalizes to a genuinely-first
  (non-recovery) bucket-menu invocation purely by reading `useFileUpload.hooks.js`'s
  `currentPrefix`-only-cares-about-current-value logic, this run reproduced case 1835's exact
  scenario from scratch in a brand-new bucket that never triggered #649 in-session — closing
  the dispatch's own flagged risk with evidence, not argument.*
- **Network-level proof the upload PUT targets the bucket-root key with no subfolder
  prefix** (`browser_network_requests` on the live exploration pass) — *added: stronger
  signal than DOM-only inference, consistent with the covering test's own established
  pattern of asserting the PUT URL directly.*
- **Console-error check across this run's own live exploration** (0 errors) — *added:
  standard silent-error guard, consistent with every sibling AFS's precedent.*
- **Documented, load-bearing test-data substitution** (`sample.md` for the case's literal
  `sample.png`) rather than silently reusing the case's literal filename — *added: a silent
  substitution would look like a shortcut; explaining WHY it's structurally required (to keep
  the negative-presence check in steps 16-17 meaningful against the shared bucket's own
  pre-existing `sample.png` in `a1/`) prevents a future reviewer from "fixing" it back to a
  literal png and silently breaking the case's own intent.*

## Gap assertions (what the implementer inserts into the covering test)

**Covering spec**: `automation/tests/ui/artifacts/
test_artifacts_upload_three_options_verify_selection.py::
TestArtifactsUploadThreeOptionsVerifySelection::
test_upload_via_three_options_and_verify_selection` (method body: lines 190-724, already
extended once for ELITEA-1827 at lines 649-698).

This extension is two small, precisely-located **insertions** into the EXISTING recovery
block (not a new appended flow at the end, unlike ELITEA-1827's extension) — the covering
test already reaches, uses, and re-uses the exact state case 1835 needs; only two assertions
are missing at that exact point.

### Gap Insertion A — bucket-selected + breadcrumb-root, asserted BEFORE opening the menu

**Insertion point**: immediately after line 441
(`artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)`) and **before**
line 442 (`artifacts_page.open_bucket_menu(...)`), inside the existing `allure.step` block
that starts at line 426 (labelled "Step 23 (AFS workaround — CORRECTED ...)"). Append the
ELITEA-1835 case-ID to that step's label so both cases' traceability is visible in the report.

```python
            artifacts_page.close_upload_path_dialog(timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)

            # ELITEA-1835 Steps 2-3 — verify the bucket is selected and the
            # breadcrumb shows root ONLY, immediately after re-selecting it
            # and BEFORE opening the bucket-menu (the case's own literal
            # ordering) — not just after the whole recovery upload completes
            # (which the existing lines 483-492 already do, later).
            assert artifacts_page.is_bucket_selected(bucket_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Bucket '{bucket_name}' should carry data-selected=\"true\" "
                "immediately after re-selecting its own root row"
            )
            assert artifacts_page.get_breadcrumb_bucket_text(timeout=UI_ELEMENT_TIMEOUT) == bucket_name, (
                f"Breadcrumb bucket label should read '{bucket_name}' at root"
            )
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "Breadcrumb should show no folder crumbs immediately after "
                "re-selecting the bucket root, before opening the bucket-menu"
            )

            artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
```

### Gap Insertion B — modal description text (case step 11)

**Prerequisite (implementer work, per `.agents/role-overrides.md` § Analyst slot — NOT
self-fixed here)**: run `add-data-testid` to add `data-testid="artifacts-upload-path-description-text"`
to the description `<Typography>` in `EliteaUI/src/pages/Artifacts/component/
UploadPathDialog.jsx` (lines 65-73, the element currently rendering `descriptionMessage`),
then wire a `LocatorDescriptor` + a `get_upload_path_description_text()` getter onto
`ArtifactsPage`, following the exact pattern already used for the sibling
`get_upload_path_normalized_prefix()` (no special handling needed — this Typography's own
`textContent()` is not polluted by any adjacent read-only adornment the way the Path field's
wrapper is).

**Insertion point**: immediately after the existing Path-field assertion (line 454, end of
the `expect.soft`... no — this is the CORRECTED-workaround block's own assertion at lines
447-454, a plain `assert`, not `expect.soft`) and before the blank line at 455.

```python
            path_text = artifacts_page.get_upload_path_normalized_prefix()
            assert path_text == f"{bucket_name}/", (
                f"Path field should read the bucket-root prefix "
                f"'{bucket_name}/' once re-opened from bucket root (isolates "
                f"the #649 defect to stale currentPrefix reuse, same proof "
                f"technique as the AFS's own Known Defects isolation pass), "
                f"got: {path_text!r}"
            )

            # ELITEA-1835 Step 11 — the modal's separate description line
            # does NOT name the bucket at root (CLARIFICATION #674): it
            # reads a GENERIC string when currentPrefix is empty, only
            # naming the bucket when a subfolder IS selected. Assert the
            # LIVE-CORRECT text, not the case's own literal ("bucket-1/")
            # expectation — per the reverse-masking guard.
            description_text = artifacts_page.get_upload_path_description_text()
            assert description_text == (
                "Files will be uploaded to the selected bucket. Optionally, "
                'enter a folder path to organize your files. Use "/" to '
                "create nested folder(s)."
            ), (
                "Upload-dialog description should show the GENERIC "
                "bucket-name-free text at bucket root (CLARIFICATION #674 — "
                f"case text implies the bucket name appears here), got: "
                f"{description_text!r}"
            )
```

**Everything else** (case steps 1, 4-10, 12-17) needs **no new code** — the existing
Steps 1-46 (as extended by ELITEA-1827's own Steps 47-54) already assert them, per the exact
line references in § Overlap check and the Coverage Map above. Do **not** duplicate them as
new steps; that would re-prove already-shipped behavior and bloat the test for no new
signal — the "small number of missing assertions" character required for `extend-existing`
is exactly these two small insertions, not a parallel walk of the whole flow.

## Cleanup
1. No new bucket/fixture cleanup needed for the extension — it reuses the covering test's
   own `artifact_bucket` fixture teardown as-is (**known pre-existing defect, already
   filed**: [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636) — the
   delete call 404s and the bucket will likely leak; out of scope here, unchanged from the
   covering test's own existing behavior).
2. No other entities are created by this extension (no Agent, no Toolkit, no Credential).
3. **This exploration run's artifacts** (not part of the automated test — a standalone
   bucket built via the UI form to verify the case live before writing this AFS, since the
   automated extension runs inside the COVERING test's own fixture-managed bucket, not a new
   one): bucket `autotest-elitea1835-93017` was created in the `Private` project (id 399),
   ending this run containing subfolder `a1/` with `sample.png` (50 B), and at bucket root:
   `sample-root.png` (38 B, uploaded via the bucket-menu entry point from a genuinely fresh
   root-click, confirming the case's own expected behavior). Left in place — matches this
   project's existing convention of ~269 un-deleted `autotest-*` buckets already present in
   `Private` from prior runs; safe to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-elitea1835-93017")`.
4. Local exploration screenshots (repo root, untracked, uploaded to the `evidence`
   prerelease store and embedded below):
   `ELITEA-1835-step10-11-path-and-description-at-root.png` — shows the Path field correctly
   reading the bucket-root prefix alongside the GENERIC (bucket-name-free) description text;
   `ELITEA-1835-step16-17-sample-root-absent-in-a1.png` — shows subfolder `a1` containing
   only the original precondition file, with the newly-uploaded root file absent.

   ![Path root-only, description generic at root](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1835-step10-11-path-and-description-at-root.png)
   ![sample-root.png absent from a1](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1835-step16-17-sample-root-absent-in-a1.png)
5. Local temp upload source files (untracked, harmless to leave or delete):
   `.playwright-mcp/sample.png`, `.playwright-mcp/sample-root.png`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator
policy (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) is
**testid-only, no fallback ladder** — `LocatorDescriptor(testid=...)` with no
`fallback=`/`locator=`.

**One testid gap this run** (see Gap Insertion B) — every other element this case touches
already has a policy-compliant testid, verified live against `automation/testids`.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ | existing |
| Bucket row (hover/click target) | `artifacts-bucket-row-{name}` (dynamic) | on-automation/testids only | `BucketItem.jsx`; confirmed live this run, hover reveals the dot-menu button |
| Bucket-menu trigger | `bucket-menu-{name}-menu-button` (dynamic) | on-automation/testids only | hover-gated, confirmed live |
| Bucket-menu "Upload files" item | `bucket-menu-upload-files-menuitem` | on-automation/testids only | static testid regardless of which bucket's menu is open |
| "Upload files to ..." dialog | `artifacts-upload-path-dialog` | on-automation/testids only | existing (ELITEA-1832) |
| Upload path input — read-only prefix wrapper | `artifacts-upload-path-input` | on-automation/testids only | use `get_upload_path_normalized_prefix()`, not the raw `text_content()` |
| Upload path input — editable `<input>` | `artifacts-upload-path-input-field` | on-automation/testids only | not touched by this case (no subfolder typed) |
| **Upload dialog description text (case step 11)** | `artifacts-upload-path-description-text` | **testid needed** | `UploadPathDialog.jsx` lines 65-73, the `<Typography>` rendering `descriptionMessage` — zero testid on either branch, confirmed via source this run. Once added: read via a new `get_upload_path_description_text()` getter on `ArtifactsPage`, same simple `text_content()` read as the description has no adjacent read-only adornment polluting it (unlike the Path field). |
| Upload path "Upload" button | `artifacts-upload-path-upload-button` | on-automation/testids only | existing (ELITEA-1832) |
| Left-panel tree item (file/folder) | `artifacts-tree-item-{key}` (dynamic) | on-automation/testids only | folder keys carry a trailing slash (`artifacts-tree-item-a1/`), confirmed live again this run |
| Bucket-row / tree-item "selected" state | `data-selected="true"/"false"` | on-automation/testids only | attribute on `artifacts-bucket-row-{name}` (ELITEA-1824); read via `is_bucket_selected()` |
| Main-panel breadcrumb — bucket label | `artifacts-breadcrumb-bucket-label` | on-automation/testids only | `ArtifactTableToolbar.jsx` (ELITEA-1824); confirmed live this run clicking it navigates to bucket root |
| Main-panel breadcrumb — folder crumb(s) | `artifacts-breadcrumb-folder-label` | on-automation/testids only | `BreadcrumbNavigation.jsx` (ELITEA-1824); absent at root, confirmed live |
| File list container / file row | `artifacts-file-list` / `artifacts-file-row` | on-main ✓ | existing |
| Success toast (generic, app-wide) | `toast-message` | on-main ✓ | confirmed live this run, exact text `"Your file(s) have been successfully uploaded!"` |

## Network Behavior
- **Bucket-menu upload from a genuinely fresh root-click — confirmed live this run**:
  `PUT http://localhost:5173/artifacts/s3/autotest-elitea1835-93017/sample-root.png
  ?project_id=399` → `200 OK` — root-level key, no subfolder prefix, confirmed via
  `browser_network_requests`. This is the SAME endpoint pattern the covering test's own
  Step 33 already asserts for the recovery-path scenario (`{bucket}/{MD_FILE_NAME}`, no
  `a1/` prefix) — byte-identical mechanism, independently re-confirmed from a pristine
  (non-recovery) invocation.
- **Bucket-listing refetch after upload**: `GET {ELITEA_URL}/artifacts/s3/{bucket}
  ?project_id={project_id}&format=json` → `200 OK`, powers the file-table/tree re-render —
  unchanged from every sibling AFS's own documented finding.
- No unexpected requests observed between any click and its corresponding network call;
  zero console errors across this run's own live exploration pass.

## Known Defects Found During Exploration

**No product defect found for this case's own core observable** (bucket-menu upload path
pre-fill correctness at a freshly-selected root) — confirmed live, working exactly as the
case expects, in a genuinely pristine (non-recovery) context.

**One CLARIFICATION filed** (case-text drift, reverse-masking guard applied — NOT a defect):
[#674](https://github.com/EliteaAI/elitea-testing-public/issues/674) — case step 11 implies
the modal's separate description line names the bucket ("files will be uploaded to
bucket-1/") when the bucket root is selected. Live product (confirmed via source,
`UploadPathDialog.jsx`'s `descriptionMessage` `useMemo`, lines 32-42) shows a GENERIC string
with no bucket name at all when `currentPrefix` is empty — the bucket name is only
interpolated when a subfolder is active. This is the live product's deliberate, correct
behavior, not a regression; the case's own step-11 expected-result text should be corrected.

## Blocked Steps
None. All 17 case steps were verified end-to-end live this run; only the description-text
assertion (step 11) needs a new testid before it can be automated — tracked as `testid
needed:`, not a blocker to the rest of the case.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **Do not create a new test file, and do not append a new flow at the end of the covering
  test either** (unlike ELITEA-1827's own extension, which needed a genuinely separate
  nested-path scenario). This case's gap is two small, precisely-located INSERTIONS into the
  covering test's EXISTING recovery block — see § Gap assertions for the exact line numbers
  and code. Per `.agents/memory/qa-engineer/
  extend_existing_means_insert_into_same_test_not_sibling_method.md`: the covering test is
  already walking the exact state machine cell this case needs (bucket-menu invocation from
  a freshly-reselected root); the gap is more assertions on that SAME cell, not a new one.
- **One new page-object method needed**: `get_upload_path_description_text()` on
  `ArtifactsPage`, mirroring the existing `get_upload_path_normalized_prefix()` shape but
  simpler (no adjacent read-only adornment to strip — the description `<Typography>`'s own
  `text_content()` is the full, unpolluted string). Requires the new testid
  (`artifacts-upload-path-description-text`) added via `add-data-testid` first.
- **Update the module docstring and the two existing `allure.step` labels touched by Gap
  Insertion A/B** to mention ELITEA-1835, and add a fourth `@allure.issue` decorator
  referencing this case's own TMS link
  (`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/artifacts/
  ELITEA-1835_upload-flow-file-uploaded-to-bucket-root.md`) plus a fifth referencing
  CLARIFICATION #674 — alongside the existing ELITEA-1824/#649/ELITEA-1827 decorators
  (lines 174-189) — per this project's own precedent
  (`.agents/memory/qa-engineer/coverage_classification_needs_board_task_not_just_behavioral_match.md`)
  that a behavioral match alone is not the same as delivered traceability.
- Wait strategy: no new wait pattern needed — both insertions read already-visible DOM state
  synchronously (via existing, already-waited-for locators); no additional
  `wait_for`/`expect` polling required beyond what's already in place at those exact lines.
