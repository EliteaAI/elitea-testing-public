# Test Case: Delete Flow – Delete Multiple Selected Files (Partial Selection) via Delete Selected Files Icon

## Metadata
- **TMS ID**: ELITEA-1846
- **Linked Story**: [EliteaAI/elitea-testing-public#268](https://github.com/EliteaAI/elitea-testing-public/issues/268) (originating tracking issue — "Found while working #268" for the defect filed from this case)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV
  backend, project `Private` / `${ELITEA_PROJECT_ID}`=399). Every handle's provenance below was verified
  against a **fresh `git fetch origin`** in `../EliteaUI`, checked independently against both `origin/main`
  and `origin/automation/testids`.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **extend-existing** — case executed end-to-end live, **2/2 clean runs** against two
  independently-seeded, freshly-navigated buckets (no shared session state between runs), 0 console errors
  either run. All 17 case steps confirmed matching live product behavior. One genuine, reproducible product
  defect was found **outside** the case's own required steps (an Axis-2 discovery, not a blocker) — filed as
  [#677](https://github.com/EliteaAI/elitea-testing-public/issues/677) (MINOR — stale toolbar selection state
  after a successful multi-file delete; see § Known Defects). Two wording CLARIFICATIONs the live product
  shows for this exact flow were **already filed** against the shared `DeleteEntityModal`/toast components by
  ELITEA-1847's own analysis run ([#659](https://github.com/EliteaAI/elitea-testing-public/issues/659) confirm-dialog
  wording, [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660) toast wording) — re-confirmed
  live this run to apply identically to this case's own text, not re-filed (same shared component, same
  drift, same reverse-masking-guard reasoning).

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_delete_subfolder_checkbox.py` (ELITEA-1847, merged to
`automation/base`) and its AFS
(`test-specs/artifacts/l2_delete-flow-subfolder-checkbox-deletes-contents_ELITEA-1847.md`) were read in full
before this run, along with `automation/pages/artifacts_page.py` (2133 lines) in full and
`test_artifacts_download_multiple_files_zip.py` (ELITEA-1840) and
`test_artifacts_download_all_files_select_all_zip.py` (ELITEA-1841).

**What ELITEA-1847's covering test already proves, reusable as-is:**
- The toolbar "Delete selected/all files" icon → confirmation-modal → confirm-click → toast → table/tree
  refresh → independent-API-ground-truth mechanics, end to end, for a **single folder-row** selection.
- Every page-object method this case needs (`select_file_checkbox`, `is_file_checkbox_checked`,
  `click_delete_files_button`, `delete_confirm_dialog`, `get_delete_confirm_message_text`, `confirm_delete`,
  `success_toast_message`, `wait_for_file_count`, `get_file_names`, `is_tree_item_visible`,
  `get_total_file_count_from_pagination`) **already exists** — zero new selectors, zero new page-object work
  needed for this case. Confirmed live this run every one of these methods works identically when driven
  against **file** rows (not just folder rows).
- `get_delete_button_tooltip_text()` and the live confirm-message/toast wording (CLARIFICATIONs #659/#660)
  are also already proven and reusable verbatim.

**What ELITEA-1847 never touches, and this case's own reason to exist:**
- **Multi-row selection via 2 individual FILE checkboxes** (not a folder, not select-all). ELITEA-1847 selects
  exactly 1 row (a folder). ELITEA-1840's download-flow test does select 2 file checkboxes and calls
  `get_checkbox_states()` to verify the rest stay unchecked — but never touches the delete flow at all (only
  download). No existing test combines multi-file-checkbox selection **with** the delete toolbar/confirm/
  toast mechanics.
- **The header "select all" checkbox's INDETERMINATE=TRUE state, asserted positively.** `is_select_all_checkbox_indeterminate()`
  already exists on `ArtifactsPage` (built for ELITEA-1841) and is already called in
  `test_artifacts_download_all_files_select_all_zip.py` — but only to assert it is **`False`** (the select-all
  case selects ALL rows, i.e. fully checked, not indeterminate). **No existing shipped test asserts this
  method returns `True`.** Confirmed live this run (`MuiCheckbox-indeterminate` class present on the header
  checkbox with 2-of-4 rows checked) — this is the case's own headline novel observable (case step 7) and the
  single strongest reason this isn't `already-covered`.
- **Verifying the two UNSELECTED subfolder rows stay unchecked while 2 FILE rows are checked** (case step 6).
  `get_checkbox_states()` (built for exactly this shape of assertion, per its own docstring) is proven in
  ELITEA-1840's download-flow test for 2 files among other files, but never for files-checked-vs-folders-
  unchecked, and never combined with delete.
- **The exact DELETE `fname[]` params for a 2-literal-file selection** (not a folder-expanded list).
  ELITEA-1847's own DELETE assertion is `fname[]=a1%2Ffile1.txt&fname[]=a1%2Ffile2.txt` (a folder's expanded
  underlying keys, per `expandFoldersToAllItems()`). This case's own DELETE is
  `fname[]=sample%20-%20Copy.md&fname[]=sample.md` — two literal root-level file keys, no expansion logic
  engaged at all. Confirmed live this run via `browser_network_requests` (2/2 runs, byte-identical shape).

**Data-precondition conflict that rules out "insert into the same test" (this project's own default
extend-existing shape, per `.agents/memory/qa-engineer/extend_existing_means_insert_into_same_test_not_sibling_method.md`):**
ELITEA-1847's covering test **deletes `a1` itself** as its own core assertion (its Step 6 fires the DELETE for
`a1`'s expanded file keys, and its Step 8 asserts pagination drops to `"1 - 3 of 3"` with `a1` gone). This
case's own precondition requires `a1` and `folder-a` to **survive completely untouched** through a delete of
the two OTHER (file) items. These two case's own required end-states are mutually exclusive within one
continuous bucket/session: appending this case's steps before 1847's own Step 2 would leave the bucket with
only 2 items by the time 1847's own Step 2 tries to check `a1`'s checkbox and later assert `"1 - 3 of 3"` (a
number computed from a precondition this insertion would have already broken). This is exactly the
"genuinely separate scenario sharing only setup — a different data precondition" exception the project's own
memory note reserves for a **sibling test method**, not the default "insert into the covering test's body"
shape (which fits when the gap is pure *addition*, e.g. ELITEA-1827/1835's own extensions, that never
conflicts with the covering test's own later assertions).

**Dedup verdict (Rule 6):** partial overlap — the toolbar/confirm/toast/refresh mechanics and every needed
page-object method are already proven; the delta is the selection SHAPE (2 files vs 1 folder), the positive
indeterminate assertion, and the sibling-unchecked verification. Not `already-covered` (the indeterminate=True
observable and the multi-file DELETE shape are both structurally unprovable by the existing single-folder-
selection test — a bug that broke only the multi-select/indeterminate code path could pass 1847's suite while
failing this one). Not fresh `ready-for-automation` either — zero new selectors/page-object work is needed,
and the reused mechanics (confirm modal, toast, refresh, independent-API check) are a majority of this case's
own steps (11 of 17). `extend-existing`, shaped as a new sibling `test()` method in the SAME file (not
inserted into the covering test's own body, per the data-precondition conflict above) — see § Gap assertions.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing exactly: subfolder `a1` (with ≥1 file inside — S3 key-prefix storage has no
  "empty folder" primitive, same finding as every sibling artifacts AFS), subfolder `folder-a` (with ≥1 file
  inside, same reason), and files `sample.md` and `sample - Copy.md` at the bucket root (4 top-level items
  total). **`bucket-1` is a case-text placeholder, not a literal fixture name** — confirmed live again this
  run (288 buckets present in `Private` at run time, none named exactly `bucket-1`) — identical finding to
  every sibling artifacts case.

## Test Data

### reuse-existing (from the covering test's own fixtures/constants, same shapes — new instances)
- **Bucket**: the covering test's own `artifact_bucket` pytest fixture (`automation/fixtures/data_fixtures.py:455`,
  function-scoped) — the sibling test gets its OWN fresh instance via the same fixture (function-scoped, so
  no sharing/conflict with the covering test's own run).
- **Seeding technique**: `ArtifactAPI.upload_file(bucket_name, key, content)` (`automation/api/client.py:1282`)
  — same no-browser-upload-needed technique the covering test already established. Confirmed live again this
  run (2/2 seeds via direct API calls, no browser involvement).

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Contents — seed all 4 keys** (one fewer than 1847's 5, since this case's `a1`/`folder-a` only need to
  exist, not be the delete target):
  - `a1/file1.txt` — inside subfolder `a1`; must survive the test untouched (only its EXISTENCE matters —
    unlike 1847, this case never deletes anything inside `a1`)
  - `folder-a/placeholder.txt` — makes `folder-a` exist; must survive the test untouched
  - `sample.md` — bucket root; **this case's own delete target**
  - `sample - Copy.md` — bucket root (literal filename, including the space and "Copy"); **this case's own
    delete target**
- **Content**: arbitrary but fixed, distinguishable per file — no byte-equality assertion required by this
  case (only presence/absence, same as 1847's own reasoning), confirmed live this run.

No `reuse-existing` bucket instance applies (this case is inherently destructive — same `generate-per-test`
reasoning as every sibling artifacts case) and no bucket instance is shared with the covering test's own run
(function-scoped fixture — each test gets an independent bucket).

## Test Steps

1. Navigate to `${BASE_URL}/artifacts?bucket={bucket_name}` via `ArtifactsPage.navigate_to_bucket()` (folds
   case steps 1–2).
   - **Verify**: file table shows exactly 4 rows — `a1`, `folder-a`, `sample - Copy.md`, `sample.md` — and
     pagination reads `"1 - 4 of 4"` (case step 3). Confirmed live 2/2 runs. Same known transient
     bucket-list-mid-fetch race documented by ELITEA-1808/1847's AFS re-observed this run (self-corrects
     within ~1-2s; `navigate_to_bucket()`'s existing condition-wait already absorbs it — do not add a fixed
     sleep).
2. Click the checkbox for `sample - Copy.md` (`ARTIFACT_FILE_CHECKBOX.format("sample - Copy.md")`) — case
   step 4.
   - **Verify**: `is_file_checkbox_checked("sample - Copy.md")` returns `True`. Confirmed live.
3. Click the checkbox for `sample.md` — case step 5.
   - **Verify**: `is_file_checkbox_checked("sample.md")` returns `True`. Confirmed live.
4. Verify subfolders `a1` and `folder-a` remain unchecked — case step 6. **Query EVERY visible row's
   checkbox independently** via `get_checkbox_states()` (built for exactly this shape of assertion, per its
   own docstring), not just the two rows just clicked.
   - **Verify**: `get_checkbox_states() == {"a1": False, "folder-a": False, "sample - Copy.md": True,
     "sample.md": True}`. Confirmed live 2/2 runs, via direct DOM class-attribute read
     (`Mui-checked` absent on `a1`/`folder-a`'s wrapping spans).
5. Verify the header "select all" checkbox shows the INDETERMINATE state — case step 7. **This is the case's
   own headline novel observable** — confirmed live this run to be the first case that asserts
   `is_select_all_checkbox_indeterminate()` returns `True` (every existing shipped use of this method only
   asserts `False`, per the Overlap check above).
   - **Verify**: `is_select_all_checkbox_indeterminate()` returns `True` AND `is_select_all_checkbox_checked()`
     returns `False` (confirms genuine 3-state behavior — partial selection is neither fully-checked nor
     fully-unchecked). Confirmed live 2/2 runs via direct DOM query
     (`document.querySelector('[data-testid="artifacts-select-all-checkbox"]').className` contains
     `MuiCheckbox-indeterminate`, not `Mui-checked`).
6. Verify the toolbar delete icon's tooltip text — case step 8. **Confirmed live via the established
   MUI-Tooltip static-`aria-label` technique** (same as ELITEA-1847's own finding): the wrapping
   `<span data-testid="artifacts-delete-files-button">` carries the DYNAMIC tooltip text as a static
   `aria-label`, computed by `ArtifactTableToolbar.jsx`'s `DeleteEntityButton` as
   `` `Delete ${rowSelectionModel.length === totalRows ? 'all files' : 'selected files'}` `` — 2 of 4 rows
   selected here (not all), so the "selected files" branch fires.
   - **Verify**: `get_delete_button_tooltip_text()` returns exactly `"Delete selected files"`. Confirmed live
     2/2 runs.
7. Click the toolbar delete icon — case step 9.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes visible. Confirmed live.
8. Verify the "Delete confirmation" modal — case step 10.
   - **Verify**: heading text is `"Delete confirmation"`.
   - **Verify (CLARIFICATION, not a defect — already filed as [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659)
     by ELITEA-1847's own analysis run, re-confirmed live this run to apply identically here)**: message text
     is **`"Are you sure to delete the selected files?"`** — the case's own text says `"Are you sure to
     delete selected files?"` (no "the"). Assert the LIVE text (reverse-masking guard), not the case's stale
     wording. Confirmed live 2/2 runs via `[data-testid="delete-confirm-message"]`.
9. Click `[data-testid="delete-confirm-button"]` — case step 11. **This is the case's own generic "Delete"
   button; do not confuse with the toolbar delete-icon button from Test Step 7.**
   - **Verify**: `DELETE ${ELITEA_API_BASE}/artifacts/artifacts/default/${PROJECT_ID}/{bucket_name}?fname[]=sample%20-%20Copy.md&fname[]=sample.md`
     → `200 OK`. Confirmed live 2/2 runs, byte-identical shape both times, via `browser_network_requests`.
     **This is TWO LITERAL file keys, not a folder-expanded list** (unlike ELITEA-1847's own DELETE
     assertion, which expands a folder to its underlying files) — confirms the app's `fname[]` param
     construction handles a direct multi-file selection with no folder-expansion logic engaged, a code path
     ELITEA-1847's own single-folder-selection test cannot exercise.
10. Verify the modal closes — case step 12.
    - **Verify**: `[data-testid="delete-confirm-dialog"]` is no longer visible. Confirmed live.
11. Verify the success notification — case step 13. **Confirmed live via a `MutationObserver` installed on
    `document.body` before the delete-confirm click** (same technique as ELITEA-1824/1826/1847's own
    precedent — a single-shot read after the click can miss the short-lived toast; confirmed this run when a
    first, non-observed attempt DID miss the toast entirely by the time a follow-up DOM read ran).
    - **Verify (CLARIFICATION, not a defect — already filed as [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660)
      by ELITEA-1847's own analysis run, re-confirmed live this run to apply identically here)**:
      `[data-testid="toast-message"]` fires with the LIVE text **`"The selected files have been successfully
      deleted."`** — the case's own Test Data table says `"The artifacts have been deleted successfully"`.
      Assert the LIVE text (reverse-masking guard). Confirmed live 2/2 runs via `MutationObserver`.
12. Verify `sample - Copy.md` and `sample.md` are no longer listed — case step 14.
    - **Verify**: `wait_for_file_count(2)` (condition-based settle, no fixed sleep — same precedent as
      1847's own `wait_for_file_count()` method, which also guards against the URL-param-loss race per issue
      #638); `get_file_names()` returns exactly `{"a1", "folder-a"}`. Confirmed live 2/2 runs.
13. Verify `sample - Copy.md` and `sample.md` are no longer in the left-panel tree — case step 15.
    - **Verify**: `is_tree_item_visible("sample.md")` and `is_tree_item_visible("sample - Copy.md")` both
      return `False` — confirmed live this run the left-panel tree's item list for the bucket dropped from
      `[artifacts-tree-item-a1/, artifacts-tree-item-folder-a/, ...]` (files never get a `-tree-item-` node
      of their own at the TOP level the same way subfolders do — confirmed live: post-delete, the tree query
      `[data-testid^="artifacts-tree-item-"]` returns exactly `["artifacts-tree-item-a1/",
      "artifacts-tree-item-folder-a/"]`, i.e. the file-level items were never separately tree-nodes to begin
      with at bucket-root scope in this bucket's shape — same "folders get tree nodes, root FILES render only
      in the file table" shape already implicit in every sibling AFS's own left-panel description). Confirmed
      live no `sample.md`/`sample - Copy.md` tree-item testid exists post-delete (nor did any exist for them
      pre-delete at this nesting level, since the tree component itself only surfaces folder nodes at root —
      worth noting as a minor case-text nuance: case step 15's phrasing implies file-level tree entries exist
      to be verified-absent; live behavior shows there was nothing to remove at this level in the first place,
      confirmed via the SAME `artifacts-tree-item-{key}` testid pattern 1847/1824/1827 already established).
14. Verify subfolders `a1` and `folder-a` are still listed and unchanged — case step 16.
    - **Verify**: `get_file_names()` (already confirmed `== {"a1", "folder-a"}` in Test Step 12) plus an
      INDEPENDENT ground truth beyond the DOM — `ArtifactAPI.list_bucket_files(bucket_name)` (a raw
      S3-listing API call) returned exactly `["a1/file1.txt", "folder-a/placeholder.txt"]` after the delete,
      confirmed live 2/2 runs — confirms `sample.md`/`sample - Copy.md` are truly gone from storage AND that
      `a1`'s/`folder-a`'s own underlying files were never touched.
15. Verify the pagination updates to `"1 - 2 of 2"` — case step 17.
    - **Verify**: `get_total_file_count_from_pagination() == 2`. Confirmed live 2/2 runs.

## Expected Results
- Checking 2 individual FILE row checkboxes (leaving 2 sibling FOLDER rows unchecked) correctly drives the
  header "select all" checkbox into the INDETERMINATE state — the first live-confirmed positive assertion of
  this 3-state behavior in this project's automation (every prior use of `is_select_all_checkbox_indeterminate()`
  only asserted `False`).
- The toolbar delete icon's tooltip/title correctly reads "Delete selected files" (not "Delete all files")
  when fewer than all rows are selected — same mechanism ELITEA-1847 already proves for a single-folder
  selection, re-confirmed here for a 2-file selection.
- Confirming deletion fires exactly one `DELETE .../artifacts?fname[]=...` request whose `fname[]` params are
  the two literal selected FILE keys — no folder-expansion logic engaged, a code path distinct from
  ELITEA-1847's own folder-selection DELETE assertion.
- On success: a toast fires (live text `"The selected files have been successfully deleted."`, same
  CLARIFICATION #660 wording ELITEA-1847 already documents for this shared component), the two selected files
  disappear from the file table, pagination updates to `"1 - 2 of 2"`, and — confirmed via an independent API
  listing, not just the DOM — the two deleted files are truly gone from storage while `a1`'s/`folder-a`'s own
  contents are completely untouched.
- No console errors during the flow (confirmed: 0 errors across both runs; only the same pre-existing,
  flow-unrelated Vite `stream.Stream` module-externalization warning every sibling artifacts case also
  reports).
- **Axis-2 discovery, outside the case's own required scope**: after the delete completes, the toolbar's
  Delete (and, by the same disabled-state logic, Download) button incorrectly remains enabled with a stale,
  misleading "Delete all files" tooltip — see § Known Defects, filed as
  [#677](https://github.com/EliteaAI/elitea-testing-public/issues/677). Confirmed non-destructive (the app's
  own defensive empty-selection check no-ops with a "No items to delete" toast if clicked through), so this
  does NOT block the case's own `extend-existing` classification.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture | asserted |
| Precondition: bucket "bucket-1" with a1, folder-a, sample - Copy.md, sample.md (4 items) | Precondition state exists | Test Data + Test Step 1 | `artifact_bucket` fixture + 4× `ArtifactAPI.upload_file()`; proven by Test Step 1's 4-row/pagination assertion | asserted *(generated name, not literal "bucket-1")* |
| Step 1: Navigate to Artifacts section | Artifacts page loads | Test Step 1 | Folded into direct bucket navigation | asserted *(folded)* |
| Step 2: Click bucket-1 | Bucket selected | Test Step 1 | Same navigation call | asserted *(folded)* |
| Step 3: Verify file table shows 4 items | All 4 items listed | Test Step 1 | 4-row table + `"1 - 4 of 4"` pagination | asserted |
| Step 4: Click checkbox next to "sample - Copy.md", verify checked | Checked | Test Step 2 | `is_file_checkbox_checked` | asserted |
| Step 5: Click checkbox next to "sample.md", verify checked | Checked | Test Step 3 | `is_file_checkbox_checked` | asserted |
| Step 6: Verify a1/folder-a remain unchecked | Both unchecked | Test Step 4 | `get_checkbox_states()` — every visible row queried independently | asserted |
| Step 7: Verify header checkbox shows indeterminate | Indeterminate=True | Test Step 5 | `is_select_all_checkbox_indeterminate()` — first live positive assertion of this state in this project | asserted |
| Step 8: Verify delete icon tooltip = "Delete selected files" | Tooltip correct | Test Step 6 | `get_delete_button_tooltip_text()` | asserted |
| Step 9: Click "Delete selected files" icon | Modal opens | Test Step 7 | `delete-confirm-dialog` visible | asserted |
| Step 10: Verify "Delete confirmation" modal + message | Modal shows correctly | Test Step 8 | Heading text + `delete-confirm-message` | asserted *(message wording is CLARIFICATION #659, already filed by 1847 — live text asserted)* |
| Step 11: Click "Delete" button | Deletion completes | Test Step 9 | `delete-confirm-button` click → `DELETE .../fname[]=sample%20-%20Copy.md&fname[]=sample.md` → 200 | asserted |
| Step 12: Verify modal closes | Modal not visible | Test Step 10 | `delete-confirm-dialog` hidden | asserted |
| Step 13: Verify green success notification | Toast shown | Test Step 11 | `toast-message`, MutationObserver-confirmed | asserted *(text is CLARIFICATION #660, already filed by 1847 — live text asserted)* |
| Step 14: Verify sample - Copy.md/sample.md no longer listed | Both removed from table | Test Step 12 | `get_file_names()` + `wait_for_file_count(2)` | asserted |
| Step 15: Verify left panel tree no longer shows the 2 files | Files removed from left panel | Test Step 13 | `is_tree_item_visible()` both `False` | asserted *(clarifying note: root-level files were never separate tree nodes to begin with at this bucket's nesting level — see Test Step 13 note)* |
| Step 16: Verify a1/folder-a still listed and unchanged | Both subfolders remain | Test Step 14 | `get_file_names()` + independent `ArtifactAPI.list_bucket_files()` ground truth | asserted |
| Step 17: Verify pagination updates to "1 - 2 of 2" | Pagination correct | Test Step 15 | `get_total_file_count_from_pagination() == 2` | asserted |
| Expected Final State: only sample - Copy.md/sample.md deleted, a1/folder-a intact, pagination updated | Composite pass condition | Test Steps 9-15 | Combination of the above, cross-checked via independent API listing | asserted |
| Pass criterion: "All steps complete without errors" | No errors | All steps | 0 console errors confirmed both clean runs (1 pre-existing unrelated Vite warning, same as every sibling case) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Independent API-level ground truth for the deletion** (`ArtifactAPI.list_bucket_files()`), not just a
  second DOM read — *added: same rationale as ELITEA-1847's own precedent; a DOM-only check could pass even
  if the UI silently failed to refetch.*
- **Network-level proof that a direct 2-file selection produces exactly 2 literal `fname[]` keys with no
  folder-expansion logic engaged** — *added: this is the one DELETE-request shape ELITEA-1847's own
  folder-selection test structurally cannot exercise; catches a future regression where a "helpful"
  refactor accidentally routes file selections through the folder-expansion code path.*
- **`get_checkbox_states()` queries every visible row, not just the two clicked** — *added: same rationale as
  ELITEA-1840's own precedent — catches a bug where checking one row's checkbox accidentally also checks a
  sibling's.*
- **`is_select_all_checkbox_indeterminate() == True` as a POSITIVE assertion** — *added: this project's own
  existing test suite only ever asserts this method returns `False`; a bug that broke the indeterminate-render
  branch specifically (leaving the header checkbox always fully-checked or always-unchecked on partial
  selection) would pass every existing test while failing a real user-facing signal — this closes that blind
  spot.*
- **A genuine, reproducible product defect found outside the case's own required steps** (post-delete stale
  toolbar-selection state, filed [#677](https://github.com/EliteaAI/elitea-testing-public/issues/677)) —
  *added: discovered by continuing to probe toolbar state after the case's own Step 17 pagination check;
  reproduced 2/2 in independent pristine contexts before filing, per the pristine-repro gate.*
- **2/2 clean, independently-seeded, freshly-navigated reproduction** (no shared session/bucket state between
  runs) — *added: rules out the multi-select/indeterminate/DELETE-shape findings being an artifact of this
  session's specific prior interactions.*
- **Console-message check immediately after the delete completes** — *added: standard silent-error guard,
  consistent with every sibling artifacts case's precedent.*

## Cleanup
1. Delete the seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)` in the `artifact_bucket` fixture's
   own teardown. **Known pre-existing defect, already filed**
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636)): this call 404s in the current dev
   environment (not re-tested this run — out of scope, unchanged from every sibling case's own documented
   behavior).
2. No other entities are created by this case (no Agent, no Toolkit, no Credential).
3. **This exploration run's own artifacts** (not part of the automated test): buckets
   `autotest-elitea1846-1784537355` and `autotest-elitea1846verify2-1784537602` were created via direct
   `ArtifactAPI` calls (operator convenience for this analysis pass) in the `Private` project (id 399). Both
   end this run containing only `a1/file1.txt` and `folder-a/placeholder.txt` (the two root files were
   deleted live during this run as the case's own subject matter; the second bucket also had its stale-state
   delete-button click attempted, which gracefully no-op'd, per § Known Defects). Left in place per this
   repo's existing convention (~288 pre-existing un-deleted `autotest-*` buckets already present); safe to
   delete any time via `ArtifactAPI.delete_bucket(...)` (will itself 404 per #636).
4. Local exploration screenshots (repo root, untracked; embedded in the filed defect
   [#677](https://github.com/EliteaAI/elitea-testing-public/issues/677) via the standard screenshot-evidence
   convention): `ELITEA-1846-step1-3-bucket-4-items.png`,
   `ELITEA-1846-step4-7-two-checked-indeterminate-header.png`, `ELITEA-1846-step9-10-confirm-dialog.png`,
   `ELITEA-1846-BUG-stale-selection-delete-all-tooltip.png`,
   `ELITEA-1846-BUG-stale-selection-verify2-reproduced.png`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md` § Analyst slot) is **testid-only, no
fallback ladder**. Every row below carries a PROVENANCE column verified this run via
`cd ../EliteaUI && git fetch origin` followed by `git grep` against both `origin/main` and
`origin/automation/testids`.

**Zero testid gaps this run** — every element this case touches already has a policy-compliant testid, and
`ArtifactsPage` already has every method needed (see § Gap assertions / Automation Hints). No `add-data-testid`
work required. (Note: ELITEA-1847's own AFS flagged `artifacts-delete-files-button` as `testid needed:` at
analysis time — confirmed live this run that gap has SINCE BEEN CLOSED: the testid now exists on
`origin/automation/testids`, still awaiting promotion to `origin/main`.)

| Element | testid | Provenance | Notes |
|---|---|---|---|
| File/folder row checkbox (per row, dynamic) | `artifacts-file-checkbox-{name}` | on-automation/testids only (awaiting promotion) | `ArtifactsPage.ARTIFACT_FILE_CHECKBOX`/`select_file_checkbox()`/`is_file_checkbox_checked()` (ELITEA-1840). Confirmed live this run for BOTH the two file rows this case checks (`sample - Copy.md`, `sample.md`) and the two folder rows it verifies stay unchecked (`a1`, `folder-a`) — same `row.id`-keyed mechanism regardless of `item.type`. |
| Header "select all" checkbox | `artifacts-select-all-checkbox` | on-automation/testids only (awaiting promotion) | `ArtifactsPage.select_all_checkbox`/`is_select_all_checkbox_indeterminate()`/`is_select_all_checkbox_checked()` (ELITEA-1841). Confirmed live this run: `MuiCheckbox-indeterminate` class present with 2-of-4 rows selected — the case's own headline observable, and this method's first-ever live positive (`True`) assertion in this project. |
| Toolbar "Delete selected/all files" icon button (wrapper) | `artifacts-delete-files-button` | on-automation/testids only (awaiting promotion) | `ArtifactTableToolbar.jsx` line ~202. **Gap closed since ELITEA-1847's own analysis** (that AFS flagged this as `testid needed:`) — confirmed live this run the wrapping `<span>` now carries this testid AND the dynamic tooltip `aria-label` MUI clones onto it, exactly per ELITEA-1847's own recommendation. `ArtifactsPage.delete_files_button`/`get_delete_button_tooltip_text()`/`click_delete_files_button()` already wired (per ELITEA-1847's implementer amendments). |
| Delete-confirmation dialog (root) | `delete-confirm-dialog` | on-automation/testids only (awaiting promotion) | `DeleteEntityModal.jsx` — shared component, already wired via `ArtifactsPage.delete_confirm_dialog`. |
| Delete-confirmation dialog message | `delete-confirm-message` | on-automation/testids only (awaiting promotion) | `DeleteEntityModal.jsx` — added as an implementer amendment during ELITEA-1847's landing (superseding that AFS's own original suggestion of a bare `#alert-dialog-description` id read, per this project's strict-testid-even-for-scoped-sub-selectors policy). `ArtifactsPage.get_delete_confirm_message_text()` already wired. |
| Delete-confirmation "Delete" (confirm) button | `delete-confirm-button` | on-automation/testids only (awaiting promotion) | `DeleteEntityModal.jsx`. `ArtifactsPage.confirm_delete()` already wired (wraps `page.expect_response()` matching the artifacts DELETE). |
| Left-panel tree item (folder, dynamic) | `artifacts-tree-item-{key}` (folder keys carry a trailing slash) | on-automation/testids only (awaiting promotion) | Existing (ELITEA-1824). Confirmed live this run: post-delete, only `artifacts-tree-item-a1/` and `artifacts-tree-item-folder-a/` exist — root-level FILES never had their own top-level tree-item node in this bucket's shape to begin with (files render only in the file table at this nesting level), so `is_tree_item_visible("sample.md")`/`is_tree_item_visible("sample - Copy.md")` correctly read `False` both before and after the delete via the SAME testid pattern. |
| Success toast (generic, app-wide) | `toast-message` | on-main ✓ | Existing `ArtifactsPage.success_toast_message` — text confirmed live 2/2 runs via `MutationObserver`. |
| File table row list / pagination | `artifacts-file-list`, `artifacts-file-row`, `artifacts-folder-row` | on-main ✓ | Existing, reused via `get_file_names()`/`get_file_count()`/`get_total_file_count_from_pagination()` — no changes needed. |

## Network Behavior
- Opening the bucket: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id=${PROJECT_ID}&format=json` →
  `200 OK`. Fires once per navigation/refetch, including automatically after the delete mutation resolves
  (`invalidatesTags`-driven refetch, same mechanism ELITEA-1847's own AFS documents).
- **The delete call itself** (confirmed live 2/2 runs, byte-identical both times):
  `DELETE {ELITEA_API_BASE}/artifacts/artifacts/default/${PROJECT_ID}/{bucket}?fname[]=sample%20-%20Copy.md&fname[]=sample.md`
  → `200 OK`. **Exactly one request**, with the two literal selected file keys as `fname[]` params — no
  folder-expansion logic engaged (contrast with ELITEA-1847's own folder-selection DELETE, whose `fname[]`
  params are the folder's fully-expanded underlying file keys).
- **No other network request fires between the confirm-click and the toast appearing** — confirmed live 2/2
  runs via `browser_network_requests` filtered on `artifacts`/`artifact`: exactly the 1 `DELETE` + the
  automatic post-mutation `GET` refetches, no unexpected POST/PUT.
- **Post-delete stale-selection defect ([#677](https://github.com/EliteaAI/elitea-testing-public/issues/677)):**
  clicking the toolbar delete button again immediately after a successful delete (with 0 checkboxes actually
  checked) opens a confirmation modal but fires **zero** new `DELETE` requests on confirm — the app's own
  `onDeleteArtifacts` (`ArtifactTable.jsx` line ~379, `sortedRows.filter(row => rowSelectionModel.includes(row.id))`)
  computes an empty `selectedItems` list (the stale ids no longer match any current row) and no-ops with a
  "No items to delete" toast instead of firing a request — confirms no data-loss risk from this defect.
- No console errors either run (one pre-existing, flow-unrelated Vite `stream.Stream` module-externalization
  warning present both times, identical to every sibling artifacts case's finding).

## Known Defects Found During Exploration
- **[MINOR]** [#677](https://github.com/EliteaAI/elitea-testing-public/issues/677) — After a successful
  multi-file delete via the toolbar, the toolbar's Delete button tooltip incorrectly reads "Delete all files"
  and the button remains enabled, even though 0 checkboxes are actually checked post-delete (`rowSelectionModel`
  retains the just-deleted rows' stale ids, and the toolbar's disabled/tooltip logic in
  `ArtifactTableToolbar.jsx` uses the raw stale `rowSelectionModel.length` rather than filtering against
  currently-visible row ids the way the per-row/header checkboxes themselves correctly do). Confirmed
  non-destructive (clicking through gracefully no-ops with a "No items to delete" toast, zero new network
  requests) — reproduced 2/2 in independent, freshly-seeded, freshly-navigated buckets. This finding is
  **outside** the TMS case's own 17 required steps (which all pass exactly as expected) — an Axis-2 discovery
  made by continuing to probe toolbar state after the case's own final assertion. Does not block this case's
  `extend-existing` classification; recorded here per the project's "file every finding" / "never mask"
  policy. **Not asserted in the Gap assertions below** (would require an `expect.soft()` + open-defect-link
  shape per the project's no-masking policy, and the case's own required steps don't call for it) —
  implementer's call whether to add it as a soft-asserted bonus check referencing #677, kept separate from
  this case's own required assertions either way.
- No other defects found. Live product behavior matched the case's functional expectations exactly for all
  17 required steps: checking 2 file checkboxes correctly drives the header checkbox into the indeterminate
  state, leaves sibling folder checkboxes unchecked, the toolbar tooltip correctly reads "selected files", the
  confirmation modal opens and its Delete button fires exactly one correctly-scoped DELETE request (2 literal
  file keys), the two files are removed from both the file table and (to the extent they ever had their own
  tree nodes) the left-panel tree, an independent API-level check confirms the files are truly gone from
  storage, and `a1`/`folder-a` are completely unaffected. The two wording departures from the case's literal
  text (confirmation-dialog phrasing, success-toast text) are pure copy/wording differences on a SHARED
  component already covered by ELITEA-1847's own CLARIFICATIONs #659/#660 — re-confirmed live this run to
  apply identically to this case's own flow, not re-filed as duplicates.

## Blocked Steps
None.

## Gap assertions (what the implementer appends to the covering test FILE, as a new sibling test method)

**Covering spec**: `automation/tests/ui/artifacts/test_artifacts_delete_subfolder_checkbox.py` (351 lines,
class `TestArtifactDeleteSubfolderCheckbox`, existing method `test_delete_subfolder_via_checkbox`).

**Shape**: a NEW sibling `test()` method in the SAME class/file — **not** an insertion into the existing
test's own body (contrast with ELITEA-1827/1835's own extend-existing precedent, which inserted pure
additions with no data-precondition conflict). This case's own precondition (`a1`/`folder-a` must SURVIVE)
directly conflicts with the covering test's own core assertion (`a1` gets DELETED, with numeric pagination
assertions computed from that fact) — see § Overlap check for the full reasoning. Per this project's own
memory note on the extend-existing boundary
(`.agents/memory/qa-engineer/extend_existing_means_insert_into_same_test_not_sibling_method.md`), a sibling
method is the correct shape specifically for "a genuinely separate scenario sharing only setup... a different
data precondition" — which this is. The two tests share the SAME fixtures (`artifact_bucket`, `artifact_api`),
the SAME page object, and the SAME imports/constants pattern — only the per-test bucket instance and the
selection/assertion shape differ.

**New test method to append** (after the existing `test_delete_subfolder_via_checkbox`, same class, same
file — do not renumber or touch the existing method):

```python
    FOLDER_KEEP_1 = "a1"
    FOLDER_KEEP_2 = "folder-a"
    FILE_DELETE_1 = "sample - Copy.md"
    FILE_DELETE_2 = "sample.md"

    A1_FILE1_KEY = f"{FOLDER_KEEP_1}/file1.txt"
    FOLDER_A_PLACEHOLDER_KEY = f"{FOLDER_KEEP_2}/placeholder.txt"

    A1_FILE1_CONTENT = b"ELITEA-1846 a1 file1 content\n"
    FOLDER_A_PLACEHOLDER_CONTENT = b"ELITEA-1846 folder-a placeholder\n"
    SAMPLE_MD_CONTENT = b"# ELITEA-1846 sample.md\n"
    SAMPLE_MD_COPY_CONTENT = b"# ELITEA-1846 sample - Copy.md\n"

    # Live-confirmed text, same shared-component CLARIFICATIONs ELITEA-1847
    # already documents (#659 confirm message, #660 success toast) —
    # re-confirmed live this run to apply identically to this case's own
    # 2-file selection flow.
    EXPECTED_CONFIRM_MESSAGE = "Are you sure to delete the selected files?"
    EXPECTED_SUCCESS_TOAST = "The selected files have been successfully deleted."

    @pytest.mark.p2
    @allure.title(
        "Selecting 2 individual files via checkbox (partial selection) drives "
        "the header checkbox indeterminate and deletes only those files"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1846_delete-flow-multiple-files-partial-selection.md",
        "onetest-ai Test Case link",
    )
    def test_delete_multiple_files_partial_selection(self, page, artifact_api, artifact_bucket):
        """Checking 2 file checkboxes (partial selection) drives the header
        'select all' checkbox into the INDETERMINATE state, leaves sibling
        folder checkboxes unchecked, and deleting via the toolbar removes
        only the 2 selected files — subfolders completely unaffected.

        Own fresh `artifact_bucket` instance (function-scoped fixture) —
        deliberately NOT sharing state with `test_delete_subfolder_via_checkbox`
        above, since that test's own core assertion (a1 gets deleted) directly
        conflicts with this test's own precondition (a1 must survive).
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifact_api.upload_file(bucket_name, self.A1_FILE1_KEY, self.A1_FILE1_CONTENT)
        artifact_api.upload_file(bucket_name, self.FOLDER_A_PLACEHOLDER_KEY, self.FOLDER_A_PLACEHOLDER_CONTENT)
        artifact_api.upload_file(bucket_name, self.FILE_DELETE_2, self.SAMPLE_MD_CONTENT)
        artifact_api.upload_file(bucket_name, self.FILE_DELETE_1, self.SAMPLE_MD_COPY_CONTENT)

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the bucket; verify all 4 top-level items "
            "(a1, folder-a, sample - Copy.md, sample.md) are listed"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == {
                self.FOLDER_KEEP_1, self.FOLDER_KEEP_2, self.FILE_DELETE_1, self.FILE_DELETE_2,
            }, f"Expected all 4 seeded top-level items, got {file_names}"
            assert artifacts_page.get_total_file_count_from_pagination() == 4

        with allure.step(
            "Step 2 — Click the checkbox for 'sample - Copy.md'; verify it "
            "becomes checked"
        ):
            artifacts_page.select_file_checkbox(self.FILE_DELETE_1, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(self.FILE_DELETE_1)

        with allure.step(
            "Step 3 — Click the checkbox for 'sample.md'; verify it becomes checked"
        ):
            artifacts_page.select_file_checkbox(self.FILE_DELETE_2, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(self.FILE_DELETE_2)

        with allure.step(
            "Step 4 — Verify subfolders 'a1' and 'folder-a' remain unchecked "
            "(query every visible row independently)"
        ):
            states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states == {
                self.FOLDER_KEEP_1: False,
                self.FOLDER_KEEP_2: False,
                self.FILE_DELETE_1: True,
                self.FILE_DELETE_2: True,
            }, f"Unexpected checkbox states: {states}"

        with allure.step(
            "Step 5 — Verify the header 'select all' checkbox shows the "
            "INDETERMINATE state (2 of 4 rows selected — neither fully "
            "checked nor fully unchecked)"
        ):
            assert artifacts_page.is_select_all_checkbox_indeterminate(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should be indeterminate with a partial selection"
            assert not artifacts_page.is_select_all_checkbox_checked(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should NOT be fully checked with a partial selection"

        with allure.step(
            "Step 6 — Verify the toolbar delete icon's tooltip reads "
            "'Delete selected files' (2 of 4 rows selected, not all)"
        ):
            tooltip_text = artifacts_page.get_delete_button_tooltip_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert tooltip_text == "Delete selected files", (
                f"Expected tooltip 'Delete selected files', got {tooltip_text!r}"
            )

        with allure.step(
            "Step 7 — Click the toolbar delete icon; verify the delete-"
            "confirmation modal opens"
        ):
            artifacts_page.click_delete_files_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 8 — Verify the modal's heading is 'Delete confirmation' and "
            "its message is the LIVE text 'Are you sure to delete the "
            "selected files?' (CLARIFICATION #659, already filed by "
            "ELITEA-1847 for this shared component; reverse-masking guard: "
            "assert the product's live contract, not the stale case wording)"
        ):
            dialog_text = artifacts_page.delete_confirm_dialog.text_content() or ""
            assert "Delete confirmation" in dialog_text
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message_text == self.EXPECTED_CONFIRM_MESSAGE, (
                f"Expected live confirm message {self.EXPECTED_CONFIRM_MESSAGE!r}, "
                f"got {message_text!r}"
            )

        with allure.step(
            "Step 9 — Click 'Delete'; verify exactly one DELETE request "
            "fires whose fname[] params are the 2 literal selected file "
            "keys (not a folder-expanded list)"
        ):
            response = artifacts_page.confirm_delete(timeout=DELETE_RESPONSE_TIMEOUT)
            assert response.status == 200
            query = parse_qs(urlsplit(response.url).query)
            fname_values = set(query.get("fname[]", []))
            assert fname_values == {self.FILE_DELETE_1, self.FILE_DELETE_2}, (
                f"Expected DELETE fname[] params to be exactly "
                f"{{{self.FILE_DELETE_1!r}, {self.FILE_DELETE_2!r}}}, got {fname_values}"
            )

        with allure.step("Step 10 — Verify the modal closes"):
            expect(artifacts_page.delete_confirm_dialog).not_to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 11 — Verify the success toast shows the LIVE text 'The "
            "selected files have been successfully deleted.' "
            "(CLARIFICATION #660, already filed by ELITEA-1847 for this "
            "shared component)"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                self.EXPECTED_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 12 — Verify 'sample - Copy.md' and 'sample.md' are no "
            "longer listed; only a1/folder-a remain"
        ):
            artifacts_page.wait_for_file_count(2, timeout=UI_ELEMENT_TIMEOUT)
            file_names_after = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names_after == {self.FOLDER_KEEP_1, self.FOLDER_KEEP_2}, (
                f"Expected only a1/folder-a to remain, got {file_names_after}"
            )

        with allure.step(
            "Step 13 — Verify 'sample - Copy.md' and 'sample.md' are no "
            "longer shown in the left-panel tree"
        ):
            assert not artifacts_page.is_tree_item_visible(
                self.FILE_DELETE_1, timeout=UI_ELEMENT_TIMEOUT
            )
            assert not artifacts_page.is_tree_item_visible(
                self.FILE_DELETE_2, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 14 — Verify, via an INDEPENDENT ground truth beyond the "
            "DOM, that a1/folder-a and their own underlying files are "
            "completely unaffected"
        ):
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert remaining_keys == {
                self.A1_FILE1_KEY, self.FOLDER_A_PLACEHOLDER_KEY,
            }, f"Expected exactly the 2 surviving keys, got {remaining_keys}"

        with allure.step(
            "Step 15 — Verify pagination updates to '1 - 2 of 2'"
        ):
            assert artifacts_page.get_total_file_count_from_pagination() == 2

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "multi-file partial-selection delete flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the multi-file delete flow: "
                f"{[m.text for m in console_errors]}"
            )
```

No changes needed to the existing `test_delete_subfolder_via_checkbox` method, its imports, or its module-level
constants — the new method reuses the same module-level `UI_ELEMENT_TIMEOUT`/`NAVIGATION_TIMEOUT`/
`DELETE_RESPONSE_TIMEOUT` constants and the same `parse_qs`/`urlsplit`/`allure`/`pytest`/`expect`/`ArtifactsPage`
imports already present at the top of the file — only its own class-level constants (`FOLDER_KEEP_1`, etc.,
namespaced to avoid colliding with the existing method's own `FOLDER_TO_DELETE`/`FOLDER_TO_KEEP`/etc. module-
level names) are new.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **Zero new page-object methods needed.** Every method the new test calls (`navigate_to_bucket`,
  `wait_for_file_count`, `get_file_names`, `get_total_file_count_from_pagination`, `select_file_checkbox`,
  `is_file_checkbox_checked`, `get_checkbox_states`, `is_select_all_checkbox_indeterminate`,
  `is_select_all_checkbox_checked`, `get_delete_button_tooltip_text`, `click_delete_files_button`,
  `delete_confirm_dialog`, `get_delete_confirm_message_text`, `confirm_delete`, `success_toast_message`,
  `is_tree_item_visible`) already exists on `ArtifactsPage` and was exercised live this run exactly as called
  in § Gap assertions.
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`) and `ArtifactAPI.upload_file()`
  (`automation/api/client.py:1282`) — same as the covering test, but each test gets its OWN fresh bucket
  instance (function-scoped fixture, no sharing).
- Toast-text capture: use `expect(...).to_have_text(...)` with Playwright's own auto-retry (same idiom
  ELITEA-1847's own shipped test already uses) — do not rely on a single-shot read; confirmed live this run a
  naive single-shot DOM read after other assertions can miss the short-lived toast entirely.
- Wait strategy: `page.expect_response()` for the single DELETE (via `confirm_delete()`, same idiom already
  established in this file); `wait_for_file_count()` for the post-delete table settle — never a fixed sleep.
- **Optional, not required**: the implementer MAY add a soft-asserted bonus check for
  [#677](https://github.com/EliteaAI/elitea-testing-public/issues/677) (post-delete stale toolbar-selection
  state) using `expect.soft()` with a `# Known defect: #677` comment, per this project's no-masking policy —
  but this is NOT part of the case's own required 17 steps and is left to the implementer's discretion,
  cleanly separated from the required assertions above either way.
