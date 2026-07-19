# Test Case: Delete Flow – Delete Subfolder via Checkbox Deletes Folder and Its Contents

## Metadata
- **TMS ID**: ELITEA-1847
- **Linked Story**: [EliteaAI/elitea-testing-public#242](https://github.com/EliteaAI/elitea-testing-public/issues/242) (tracking issue — "Found while working #242" for the two CLARIFICATIONs filed from this case)
- **Priority**: l2 (high — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend,
  project `Private` / `${ELITEA_PROJECT_ID}`=399). Every handle's provenance below was verified against a
  **fresh `git fetch origin`** in `../EliteaUI`, checked independently against both `origin/main` and
  `origin/automation/testids`.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live, **2/2 clean runs** (once deleting the
  full `a1` subfolder + its 2 files, once deleting a single throwaway file via the identical mechanism to
  capture the success-toast text with a `MutationObserver`), 0 console errors either run. No blocking defect.
  One genuine `testid needed:` gap (the toolbar delete-icon button itself carries **zero** `data-testid`,
  confirmed absent on both `origin/main` and `origin/automation/testids`) — additive, well-precedented (a
  single `data-testid` prop on an existing `IconButton`/wrapping `Box`), not an environment/access/data blocker,
  so this does **not** downgrade the status to `blocked` (same reasoning as ELITEA-1840's precedent). Two
  CLARIFICATIONs (case-text drift, reverse-masking guard applied — **not** defects) were filed for two wording
  differences between the live product and the case's own text:
  [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659) (confirmation-dialog message wording)
  and [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660) (success-toast wording).

## Overlap check vs existing automation

`automation/pages/artifacts_page.py` (1619 lines) was read in full before this run, plus all 8 existing artifacts
test files (`test_artifacts_create_bucket_upload_file.py`, `test_artifacts_download_multiple_files_zip.py`,
`test_artifacts_download_single_file_dropdown.py`, `test_artifacts_duplicate_bucket_name.py`,
`test_artifacts_multi_file.py`, `test_artifacts_upload_duplicate_cancel.py`,
`test_artifacts_upload_multiple_files.py`, `test_artifacts_upload_three_options_verify_selection.py`) and their
matching AFS files under `test-specs/artifacts/`.

- The page object already declares `delete_menu_item` (`artifacts-file-delete-menuitem`, the per-file dot-menu
  "Delete" item) — but its own docstring says **"visibility-only in ELITEA-1839, never clicked"**, and a repo-wide
  grep confirms this: every reference to `delete_menu_item` across the 8 existing test files is an
  `expect(...).to_be_visible()` assertion, never a `.click()`. No existing test drives an actual deletion —
  neither the single-file dot-menu path nor the bulk-checkbox-toolbar path this case exercises.
- No existing test touches the toolbar's bulk delete icon (`DeleteEntityButton`/`onDeleteArtifacts` in
  `ArtifactTableToolbar.jsx`/`ArtifactTable.jsx`) at all — confirmed via `grep -rn "delete" automation/tests/ui/artifacts/*.py`,
  every hit is either the visibility-only dot-menu check above or **bucket** deletion in test teardowns
  (`ArtifactAPI.delete_bucket()`, a completely different entity/endpoint).
- `ArtifactsPage` has no `delete_files_button`, `delete_confirm_dialog`, or per-row-checkbox-driven delete method
  of any kind prior to this case.

Verdict: **zero behavioral overlap** — this is a genuinely fresh scenario. Fresh implementation,
`ready-for-automation`.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists containing: subfolder `a1` with ≥1 file inside, subfolder `folder-a`, and files
  `sample - Copy.md` and `sample.md` at the bucket root. **`bucket-1` is a case-text placeholder, not a literal
  fixture name** — confirmed live again this run (217 buckets present in `Private` at run time, including every
  `autotest-*` bucket from prior sibling cases' runs; none named exactly `bucket-1`) — identical finding to
  every sibling artifacts case (ELITEA-1808/1824/1826/1832/1839/1840).
  - **`folder-a` needs ≥1 file inside it too, even though the case doesn't say so explicitly.** This storage is
    S3 key-prefix-based (confirmed via source and via ELITEA-1827's prior finding, reused here) — there is no
    "create empty folder" action anywhere in the UI or API (confirmed via `grep -rn "createFolder\|New Folder"`
    against `../EliteaUI/src`, zero hits for artifacts). A folder only exists implicitly, as the common prefix
    of at least one real file key. Seeded `folder-a/placeholder.txt` for this reason — confirmed live this
    renders as a folder row named `folder-a` identical in shape to `a1`.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- **Bucket**: reuse the existing `artifact_bucket` pytest fixture (`automation/fixtures/data_fixtures.py:455`,
  function-scoped, `ArtifactAPI.create_bucket()`/`delete_bucket()`). Do **not** hardcode `bucket-1`.
- **Contents — seed all 5 keys directly via `ArtifactAPI.upload_file(bucket_name, key, content)`**
  (`automation/api/client.py:1282`), same no-browser-upload-needed technique already established by ELITEA-1840's
  precedent (confirmed live again this run: uploading to a nested key auto-creates the parent folder node in
  both panels; no separate "create folder" call exists or is needed):
  - `a1/file1.txt` — inside subfolder `a1`, must be deleted along with the folder
  - `a1/file2.txt` — inside subfolder `a1`, must be deleted along with the folder
  - `folder-a/placeholder.txt` — makes `folder-a` exist; must survive the test untouched
  - `sample.md` — bucket root; must survive the test untouched
  - `sample - Copy.md` — bucket root (literal filename, including the space and "Copy"); must survive the test
    untouched
- **Content**: arbitrary but fixed, distinguishable per file (this run used short fixed text strings per key,
  e.g. `b"ELITEA-1847 a1 file1 content\n"`) — no byte-equality assertion is required by this case (unlike the
  download-flow siblings), only presence/absence.

No `reuse-existing` fixture applies — a bucket in this specific multi-folder, pre-populated state isn't safe to
share across parallel/serial runs, and this case is **inherently destructive** (its own purpose is to delete
part of the bucket's contents) — same `generate-per-test` reasoning as every sibling artifacts case, with the
added note that cleanup discipline matters more here than most: the test must not assume the deleted subfolder
can be "restored" for a retry: reseed a full fresh bucket per attempt instead of a partial delete-and-recreate
dance.

## Test Steps

1. Navigate to `${BASE_URL}/artifacts?bucket={bucket_name}` via `ArtifactsPage.navigate_to_bucket()` (folds case
   steps 1–2 into one navigation).
   - **Known transient race, already documented by ELITEA-1808's AFS, re-observed this run**: an accessibility
     snapshot taken *immediately* after navigating directly to a bucket URL can catch the bucket list mid-fetch
     (a stale `"No buckets created yet"` / `"Buckets: 0"` state that self-corrects within ~1–2s once the list
     refetch completes) — confirmed live this run (`http://localhost:5173/artifacts?bucket=...` initially showed
     `"No buckets created yet"`, then correctly resolved to the full 217-bucket list + the target bucket's own
     4-item contents after a condition-based wait on the bucket's own row). `navigate_to_bucket()`'s existing
     `_wait_for_bucket_panel()` condition-wait already absorbs this; do not add a fixed sleep.
   - **Verify**: file table shows exactly 4 rows — `a1`, `folder-a`, `sample - Copy.md`, `sample.md` — and
     pagination reads `"1 - 4 of 4"` (case step 3). Confirmed live 2/2 runs.
2. Locate the checkbox for the `a1` row (`ARTIFACT_FILE_CHECKBOX.format("a1")`, i.e.
   `[data-testid="artifacts-file-checkbox-a1"]` — confirmed live this dynamic testid, added for ELITEA-1840, works
   identically for **folder** rows, not just file rows: `row.id` = `item.name` regardless of `item.type`) and
   click it (case step 4).
   - **Verify**: checkbox becomes checked — confirmed live via the resolved element's accessibility `checked`
     state (Playwright snapshot showed `checkbox [checked] [active]`).
3. Verify the toolbar delete icon's tooltip text (case step 5). **Confirmed live via the established MUI-Tooltip
   static-`aria-label` technique** (documented in this project's own memory from ELITEA-1809): MUI clones the
   `Tooltip`'s `title` prop onto the wrapping `<Box component="span">` as a **static** `aria-label` attribute
   (`data-mui-internal-clone-element="true"`), readable without hovering or waiting for the ephemeral
   `role="tooltip"` popper. Confirmed live this run via direct DOM query:
   `wrapper.getAttribute('aria-label') === "Delete selected files"` — exactly matches the case's expected text,
   because `ArtifactTableToolbar.jsx`'s `DeleteEntityButton` computes
   `title={`Delete ${rowSelectionModel.length === totalRows ? 'all files' : 'selected files'}`}`, and only 1 of 4
   rows is selected here (not all), so the "selected files" (not "all files") branch fires.
   - **Verify**: wrapping element's `aria-label` == `"Delete selected files"`.
4. Click the toolbar delete icon (case step 6). **Confirmed live**: the inner `IconButton` itself carries a
   FIXED, non-dynamic `aria-label="delete entity"` (distinct from the dynamic tooltip text on its wrapper) and
   **zero `data-testid`** — see § Concrete Handles for the gap.
   - **Verify**: `[data-testid="delete-confirm-dialog"]` becomes visible (case step 6's "Delete confirmation
     modal opens").
5. Verify the confirmation modal's heading and message (case step 7).
   - **Verify**: heading text is `"Delete confirmation"`.
   - **Verify (CLARIFICATION, not a defect — filed [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659))**:
     message text is **`"Are you sure to delete the selected files?"`** — confirmed live via
     `document.querySelector('#alert-dialog-description').textContent` both runs. The case's own text says
     `"Are you sure to delete selected files?"` (no "the") — assert the LIVE text, not the case's stale wording
     (reverse-masking guard).
6. Click `[data-testid="delete-confirm-button"]` (case step 8, the "Delete" button inside the confirmation modal
   — **do not confuse with the toolbar delete-icon button from Test Step 4**, which has no testid at all).
   - **Verify**: `DELETE ${ELITEA_API_BASE}/artifacts/artifacts/default/${PROJECT_ID}/{bucket_name}?fname[]=a1%2Ffile1.txt&fname[]=a1%2Ffile2.txt`
     → `200 OK` (confirmed live, § Network Behavior). **Confirmed live via source read**
     (`ArtifactTable.jsx`'s `onDeleteArtifacts` → `expandFoldersToAllItems()` → `getItemsUnderFolder()`,
     `getItemsAtCurrentLevel.js:81-102`): a selected **folder** row is expanded to the full list of its
     underlying file keys (matched by `key.startsWith(folderKey)`) before the DELETE call — there is no
     "folder" object to delete server-side (S3 key-prefix storage has none), only its constituent files. This is
     why deleting `a1` correctly removes it: once no key starts with `a1/` any more, the folder simply no longer
     appears in any listing.
7. Verify the success notification (case step 9). **Confirmed live via a `MutationObserver` installed on
   `document.body` before the delete-confirm click** — a single-shot DOM read after the click can miss the
   short-lived toast (same technique as ELITEA-1824/1826's precedent).
   - **Verify (CLARIFICATION, not a defect — filed [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660))**:
     `[data-testid="toast-message"]` fires with the LIVE text **`"The selected files have been successfully deleted."`**
     — confirmed live both runs (once for the `a1`-folder deletion, once for a throwaway single-file deletion
     used specifically to isolate the toast-capture race from the folder-expansion logic). The case's own Test
     Data table says the expected text is `"The artifacts have been deleted successfully"` — assert the LIVE
     text, not the case's stale wording (reverse-masking guard).
8. Verify `a1` is no longer listed in the file table (case step 10).
   - **Verify**: `get_file_names()` no longer contains `"a1"`; pagination reads `"1 - 3 of 3"`. Confirmed live.
9. Verify `a1` is no longer shown in the left-panel tree under the bucket (case step 11).
   - **Verify**: `is_tree_item_visible("a1/")` (the folder-key trailing-slash convention, per ELITEA-1824's
     established finding) returns `False`. Confirmed live: the left-panel tree's item list for the bucket
     dropped from `[a1, folder-a, sample - Copy.md, sample.md]` to `[folder-a, sample - Copy.md, sample.md]`
     immediately after the DELETE response landed (no page reload needed — the mutation's `invalidatesTags`
     drives an automatic refetch of both the file-table and tree-panel queries).
10. Verify all files that were inside `a1` are also removed (case step 12). **Verified via an INDEPENDENT ground
    truth beyond the DOM** — `ArtifactAPI.list_bucket_files(bucket_name)` (a raw S3-listing API call, not a
    second DOM read of the same UI state) returned exactly `['folder-a/placeholder.txt', 'sample - Copy.md',
    'sample.md']` after the delete — confirms `a1/file1.txt` and `a1/file2.txt` are truly gone server-side, not
    merely hidden client-side.
11. Verify the remaining items (`folder-a`, `sample - Copy.md`, `sample.md`) are still listed unchanged (case
    step 13).
    - **Verify**: `set(get_file_names()) == {"folder-a", "sample - Copy.md", "sample.md"}`; each row's Type/Size
      cell unchanged from Test Step 1's baseline read (`folder-a`: `"-"`/`"-"`; `sample - Copy.md`: `Markdown`/
      `39 B`; `sample.md`: `Markdown`/`32 B`). Confirmed live via the same independent API listing in Test
      Step 10 plus a fresh UI snapshot.

## Expected Results
- Checking a folder row's checkbox and clicking the toolbar delete icon opens a confirmation modal
  (`delete-confirm-dialog`) whose tooltip/message reflect the "selected files" (not "all files") wording when
  fewer than all rows are selected.
- Confirming deletion (`delete-confirm-button`) fires exactly one `DELETE .../artifacts?fname[]=...` request
  whose `fname[]` params are the folder's fully-expanded list of underlying file keys (never a bare "folder"
  key) — confirmed via source: `expandFoldersToAllItems()`/`getItemsUnderFolder()`.
- On success: a toast fires (live text `"The selected files have been successfully deleted."`), the deleted
  folder disappears from both the file table and the left-panel tree, and — confirmed via an independent API
  listing, not just the DOM — the folder's underlying files are truly gone from storage.
- Every other item in the bucket (a sibling folder and two root-level files) is completely unaffected.
- No console errors during the flow (confirmed: 0 errors across both runs; only the same pre-existing,
  flow-unrelated Vite `stream.Stream` module-externalization warning every sibling artifacts case also reports).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture | asserted |
| Precondition: bucket "bucket-1" with a1 (files), folder-a, sample - Copy.md, sample.md | Precondition state exists | Test Data + Test Step 1 | `artifact_bucket` fixture + 5× `ArtifactAPI.upload_file()`; proven by Test Step 1's 4-row/pagination assertion | asserted *(generated name, not literal "bucket-1"; `folder-a` needs a seeded file to exist at all — noted in Preconditions)* |
| Step 1: Navigate to Artifacts section | Artifacts page loads | Test Step 1 | Folded into the direct bucket navigation | asserted *(folded)* |
| Step 2: Click bucket-1 | Bucket selected | Test Step 1 | Same navigation call | asserted *(folded)* |
| Step 3: Verify file table shows a1, folder-a, sample - Copy.md, sample.md | All items listed | Test Step 1 | 4-row table + `"1 - 4 of 4"` pagination confirmed live | asserted |
| Step 4: Click checkbox next to a1, verify checked | a1 checked | Test Step 2 | Checkbox `checked` state confirmed live | asserted |
| Step 5: Verify delete icon tooltip = "Delete selected files" | Tooltip text correct | Test Step 3 | Wrapper `aria-label` read (MUI-Tooltip static-attribute technique) | asserted |
| Step 6: Click "Delete selected files" icon | Delete confirmation modal opens | Test Step 4 | `delete-confirm-dialog` becomes visible | asserted |
| Step 7: Verify "Delete confirmation" modal + message | Modal visible with correct message | Test Step 5 | Heading text + `#alert-dialog-description` text | asserted *(message wording is CLARIFICATION [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659) — live text asserted, not case's stale wording)* |
| Step 8: Click "Delete" button | Deletion completes | Test Step 6 | `delete-confirm-button` click → `DELETE .../fname[]=a1%2Ffile1.txt&fname[]=a1%2Ffile2.txt` → 200 | asserted |
| Step 9: Verify green success notification | Success notification appears | Test Step 7 | `toast-message`, MutationObserver-confirmed | asserted *(text is CLARIFICATION [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660) — live text asserted, not case's stale Test-Data wording)* |
| Step 10: Verify a1 no longer listed in file table | a1 absent from table | Test Step 8 | `get_file_names()` + pagination `"1 - 3 of 3"` | asserted |
| Step 11: Verify a1 no longer shown in left panel tree | a1 removed from left panel | Test Step 9 | `is_tree_item_visible("a1/") == False` | asserted |
| Step 12: Verify all files inside a1 are also removed | No files from a1 remain | Test Step 10 | Independent `ArtifactAPI.list_bucket_files()` ground truth (not just DOM) | asserted |
| Step 13: Verify remaining items (folder-a, sample - Copy.md, sample.md) unchanged | All 3 remaining items present | Test Step 11 | `set(get_file_names())` + per-row Type/Size unchanged | asserted |
| Expected Final State: a1 + contents permanently deleted, remaining items unchanged | Composite pass condition | Test Steps 8–11 | Combination of the above, cross-checked via independent API listing | asserted |
| Pass criterion: "All steps complete without errors" | No errors | All steps | 0 console errors confirmed both clean runs (1 pre-existing unrelated Vite warning, same as every sibling case) | asserted |

### Axis 2 — Observables asserted beyond the case
- **Independent API-level ground truth for the deletion** (`ArtifactAPI.list_bucket_files()`), not just a second
  DOM read — *added: the case's own step 12 ("verify all files… are removed") is exactly the kind of negative
  assertion that's strongest when backed by a source independent of the UI being tested; a DOM-only check could
  pass even if the UI silently failed to refetch.*
- **Network-level proof that a folder selection is expanded to its full underlying file-key list before the
  DELETE call fires** (`fname[]=a1%2Ffile1.txt&fname[]=a1%2Ffile2.txt`, not a bare `a1/` folder key) — *added:
  confirms the folder-delete semantics work via key-prefix expansion (`expandFoldersToAllItems`/
  `getItemsUnderFolder`), which is the actual mechanism that makes case steps 10–12 true; asserting the exact
  `fname[]` params catches a future regression where the expansion silently drops a nested file.*
- **Cancel-path regression guard**: selecting `folder-a`'s checkbox, opening the delete confirmation dialog, and
  clicking **Cancel** correctly aborts with zero network request and `folder-a/placeholder.txt` still present
  (re-confirmed via the same independent API listing) — *added: not required by the case's own steps, but a
  natural companion assertion for a destructive flow, and confirms the modal's Cancel path (untestid'd, out of
  this case's required-elements list) doesn't silently delete anyway.*
- **2/2 clean, non-instrumented-except-for-toast-capture reproduction**, each targeting a different item (the
  full `a1` folder once, a throwaway single file once) — *added: rules out the folder-expansion logic being a
  fluke of this specific fixture shape, and isolates the toast-text capture (which needed a `MutationObserver`)
  from the folder-deletion network assertion (which didn't).*
- **Console-message check immediately after each delete completes** — *added: standard silent-error guard,
  consistent with every sibling artifacts case's precedent.*

## Cleanup
1. Delete the seeded bucket via `ArtifactAPI.delete_bucket(bucket_name)` in the `artifact_bucket` fixture's own
   teardown. **Known pre-existing defect, already filed
   ([#636](https://github.com/EliteaAI/elitea-testing-public/issues/636))**: this call 404s in the current dev
   environment (re-confirmed live this run — the compound `p--{project_id}.{bucket_name}` URL-format retry also
   404'd), so the bucket will likely leak — not new to this case, out of scope to fix here.
2. No other entities are created by this case (no Agent, no Toolkit, no Credential).
3. **This exploration run's own artifacts** (not part of the automated test): bucket
   `autotest-elitea1847-delete-84498920` was created via direct `ArtifactAPI` calls (operator convenience for
   this analysis pass) in the `Private` project (id 399). At hand-off it contains `folder-a/placeholder.txt`,
   `sample - Copy.md`, `sample.md` (the `a1` subfolder and its 2 files, plus a throwaway `toastcheck-1847.txt`,
   were both deleted live during this run as the case's own subject matter). Left in place per this repo's
   existing convention (~217 pre-existing un-deleted `autotest-*` buckets already present); safe to delete any
   time via `ArtifactAPI.delete_bucket("autotest-elitea1847-delete-84498920")` (will itself 404 per #636).
4. Local exploration screenshots (repo root, untracked; also uploaded + embedded in the two filed
   CLARIFICATIONs per `.agents/role-overrides.md` § screenshot evidence):
   `ELITEA-1847-CLARIFICATION-confirm-dialog-wording.png` (confirmation-modal wording, embedded in
   [#659](https://github.com/EliteaAI/elitea-testing-public/issues/659)),
   `ELITEA-1847-step10-13-a1-removed-remaining-items-intact.png` (post-delete final state, embedded in
   [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660)).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md` § Analyst slot) is **testid-only, no
fallback ladder**. Every row below carries a PROVENANCE column verified this run via
`cd ../EliteaUI && git fetch origin` followed by `git grep` against both `origin/main` and
`origin/automation/testids`.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| File/folder row checkbox (per row, dynamic) | `artifacts-file-checkbox-{name}` | on-automation/testids only (awaiting promotion to main) | Already declared as `ArtifactsPage.ARTIFACT_FILE_CHECKBOX`/`select_file_checkbox()` (ELITEA-1840). **Confirmed live this run it works identically for FOLDER rows, not just file rows** — `row.id` = `item.name` regardless of `item.type` (`ArtifactTable.jsx`'s `checkboxTestId={\`artifacts-file-checkbox-${row.id}\`}` call site has no type-based branching). No new handle needed, but this is the first case to exercise it on a folder row. |
| **Toolbar "Delete selected/all files" icon button** | `testid needed: artifacts-delete-files-button` | **confirmed absent on BOTH `origin/main` and `origin/automation/testids`** | Root cause (confirmed live via DOM query — `document.querySelector('button[aria-label="delete entity"]').getAttribute('data-testid')` returns `null`): `DeleteEntityButton.jsx`'s `<IconButton aria-label="delete entity" ...>` (line ~94) has **no `data-testid`/testid-forwarding prop at all** — unlike its sibling `download_files_button`/`upload_files_button` in the same toolbar, which both already carry static testids at their own call sites. `DeleteEntityButton` is a **shared component** used elsewhere in the app (any entity needing an inline delete-with-confirmation icon), so per this project's shared-component testid ruling the fix is a new caller-supplied prop (e.g. `testId`), threaded through to the `IconButton`'s `data-testid`, wired **only** at `ArtifactTableToolbar.jsx`'s call site (~line 198, the `<DeleteEntityButton ... />` for artifacts) as `testId="artifacts-delete-files-button"` — not at any of this component's other call sites (out of this case's scope). **Recommend placing the testid on the OUTER wrapping `<Box component="span">` inside `DeleteEntityButton.jsx` (the same element MUI's `Tooltip` clones its dynamic `aria-label` onto), not on the `IconButton` itself** — this lets the implementer read the dynamic tooltip text directly via `.get_attribute("aria-label")` on the SAME testid-anchored locator (confirmed live this run: `<span class="MuiBox-root css-0" aria-label="Delete selected files" data-mui-internal-clone-element="true"><button aria-label="delete entity" ...>`), then reach the actual clickable button via a single `.locator("button")` scoped inside it for the click/disabled-state checks — the same "testid-on-wrapper + scoped click-target" shape this page object's own pre-existing (legacy, pre-testid-only-policy) `create_bucket_button`/`download_files_button` `LocatorDescriptor`s already establish, just satisfied via a real testid instead of a `fallback=`. |
| Delete-confirmation dialog (root) | `delete-confirm-dialog` | on-automation/testids only (awaiting promotion) | `DeleteEntityModal.jsx` — shared component, already used defensively for exploration cleanup by ELITEA-1824's AFS but never asserted in a shipped test until now. |
| Delete-confirmation dialog message | *(no dedicated testid — read via `#alert-dialog-description` id inside the already-testid'd dialog)* | — | `DeleteEntityModal.jsx`'s `contentNode`'s `<Typography id="alert-dialog-description">`. This is a stable, hand-authored HTML `id` (not a CSS class, not testid-policy-violating since it's scoped inside an already-testid'd container) — reading `dialog.querySelector('#alert-dialog-description').textContent` is the same "read via an already-resolved testid element" shape as e.g. `is_file_checkbox_checked()`'s CSS-class read, not a new bare selector. No `testid needed:` flagged — a semantic `id` scoped inside a testid'd root is an acceptable read target, not a locator gap. |
| Delete-confirmation "Delete" (confirm) button | `delete-confirm-button` | on-automation/testids only (awaiting promotion) | `DeleteEntityModal.jsx`'s `<Button.OneClickButton data-testid="delete-confirm-button">`. Already referenced (declared, not yet driven) in ELITEA-1824's AFS for manual exploration cleanup — this case is the first to genuinely assert/drive it in a shipped test. |
| Delete-confirmation "Cancel" button | *(no testid)* | confirmed absent both branches | `DeleteEntityModal.jsx`'s plain `<Button.BaseBtn>` (no `data-testid` prop at all). **Not flagged as `testid needed:`** — this case's own required steps never click Cancel (the Axis-2 Cancel-path guard used a text-role lookup, `getByRole('button', {name: 'Cancel'})`, purely as an exploratory aside outside the case's asserted scope, same "testid-scope rule: only wire testids for elements a test actually touches" precedent as every sibling AFS). If a future case needs to assert/drive Cancel specifically, add a testid then. |
| Left-panel tree item (folder, dynamic) | `artifacts-tree-item-{key}` (folder keys carry a trailing slash, e.g. `artifacts-tree-item-a1/`) | on-automation/testids only | Existing (ELITEA-1824) — reused via `is_tree_item_visible("a1/")` to confirm the folder's removal from the left panel. |
| Success toast (generic, app-wide) | `toast-message` | on-main ✓ (per ELITEA-1832) | Existing `ArtifactsPage.success_toast_message` — text confirmed live this run via `MutationObserver` (see Test Step 7); the SAME generic component every sibling artifacts case already reuses for its own success text. |
| File table row list / pagination | `artifacts-file-list`, `artifacts-file-row`, `artifacts-folder-row` | on-main ✓ | Existing, reused via `get_file_names()`/`get_file_count()`/`get_total_file_count_from_pagination()` — no changes needed. |

## Network Behavior
- Opening the bucket: `GET {ELITEA_URL}/artifacts/s3/{bucket}?project_id=${PROJECT_ID}&format=json` → `200 OK`.
  Fires once per navigation/refetch, before the file table (re)renders — including automatically after the
  delete mutation resolves (`invalidatesTags: [TAG_ARTIFACTS, TAG_BUCKETS]` on `deleteArtifacts`, confirmed via
  source and via the 2 automatic re-fetch `GET`s observed immediately after the `DELETE` in this run's network
  log).
- **The delete call itself** (confirmed live both runs):
  `DELETE {ELITEA_API_BASE}/artifacts/artifacts/default/${PROJECT_ID}/{bucket}?fname[]=a1%2Ffile1.txt&fname[]=a1%2Ffile2.txt`
  → `200 OK`. **Exactly one request** for this case's 2-file folder (confirmed via source,
  `api/artifacts.js:135-167`'s `deleteArtifacts` mutation: it chunks `fname[]` params only when the combined URL
  would exceed `DELETE_ARTIFACTS_MAX_PATH_LENGTH`, executing chunks **sequentially** so a failure stops further
  deletion immediately — not relevant at this case's small scale, but worth knowing for a future case with many
  more files/a very long bucket name).
- **No other network request fires between the confirm-click and the toast appearing** — confirmed live both
  runs via `browser_network_requests` filtered on `artifacts`/`artifact`: exactly the 1 `DELETE` + the automatic
  post-mutation `GET` refetches, no unexpected POST/PUT.
- No console errors either run (one pre-existing, flow-unrelated Vite `stream.Stream` module-externalization
  warning present both times, identical to every sibling artifacts case's finding — not caused by this flow).

## Known Defects Found During Exploration
None. Live product behavior matched the case's functional expectations exactly: checking a folder's checkbox
correctly enables the toolbar delete icon with the "selected files" (not "all files") tooltip wording, the
confirmation modal opens and its Delete button fires exactly one correctly-scoped `DELETE` request (the folder
expanded to its full underlying file-key list), the folder and its contents are removed from both the file table
and the left-panel tree, an independent API-level check confirms the files are truly gone from storage, and
every other bucket item is completely unaffected. The only two departures from the case's literal text are pure
copy/wording differences (confirmation-dialog phrasing, success-toast text) — both filed as CLARIFICATIONs
([#659](https://github.com/EliteaAI/elitea-testing-public/issues/659),
[#660](https://github.com/EliteaAI/elitea-testing-public/issues/660)) per the reverse-masking guard, not Bugs.

## Blocked Steps
None. The one `testid needed:` row in § Concrete Handles (the toolbar delete-icon button) is implementer work
(per `.agents/role-overrides.md` § Analyst slot: not softened into a MINOR defect or a note; the AFS is the work
order), not an analyst-side blocker — it's a single additive, well-precedented `data-testid` prop addition.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- Page object: extend `automation/pages/artifacts_page.py` (`ArtifactsPage`). Already has
  `ARTIFACT_FILE_CHECKBOX`/`select_file_checkbox()`/`is_file_checkbox_checked()` (ELITEA-1840, reusable as-is —
  confirmed live this run it works for folder rows too), `is_tree_item_visible()` (ELITEA-1824),
  `success_toast_message` (ELITEA-1826/1832), `get_file_names()`/`get_total_file_count_from_pagination()`. New
  additions needed once the implementer wires the `artifacts-delete-files-button` testid:
  - `delete_files_button = LocatorDescriptor(testid="artifacts-delete-files-button")` — resolves to the
    wrapping `Box component="span"` per the recommendation in § Concrete Handles.
  - `delete_confirm_dialog = LocatorDescriptor(testid="delete-confirm-dialog")`,
    `delete_confirm_button = LocatorDescriptor(testid="delete-confirm-button")` — both testids already exist on
    `automation/testids`, just never wired into this page object before.
  - New methods, e.g. `get_delete_button_tooltip_text()` (reads `delete_files_button.get_attribute("aria-label")`),
    `click_delete_files_button()` (`.locator("button").click()` scoped inside `delete_files_button`, matching the
    "testid-on-wrapper, scoped click target" shape already used by the pre-existing `create_bucket_button`),
    `get_delete_confirm_message_text()` (reads `#alert-dialog-description` scoped inside `delete_confirm_dialog`),
    `confirm_delete()` (clicks `delete_confirm_button`, wrapped in `page.expect_response()` matching
    `"artifacts/artifacts" in r.url and r.request.method == "DELETE"` — the same `expect_response` idiom this
    page object already uses for bucket creation).
- Fixtures: reuse `artifact_bucket` (`automation/fixtures/data_fixtures.py:455`) and `ArtifactAPI.upload_file()`
  (`automation/api/client.py:1282`) to seed all 5 keys — no browser-driven upload needed (confirmed live, § Test
  Data). Use `ArtifactAPI.list_bucket_files()` (`automation/api/client.py:1226`) for the independent post-delete
  ground-truth check (Test Step 10/Axis 2).
- Toast-text capture: with a small (single-digit-KB) fixture, the toast can be short-lived enough that a
  single-shot read after the click misses it — use the same `MutationObserver`-before-click technique already
  established by ELITEA-1824/1826 (or Playwright's own auto-retrying `expect(toast).to_contain_text(...)`
  immediately after the confirm click, never a fixed sleep).
- Both CLARIFICATION wording differences ([#659](https://github.com/EliteaAI/elitea-testing-public/issues/659),
  [#660](https://github.com/EliteaAI/elitea-testing-public/issues/660)) should be asserted against the LIVE text
  documented in Test Steps 5/7 above, not the case's own (stale) Test Data/step text — per the reverse-masking
  guard, asserting the stale case-text would itself be the masking failure mode.
- Select-all-checkbox variant (deleting via the header "select all" checkbox, which would flip the tooltip/title
  to "Delete all files") is **not** covered by this case and is out of this case's scope — if a sibling TMS case
  exists for that variant, do not fold it into this implementation.

## Implementer Amendments (Phase 2 Explore, ELITEA-1847)

Two deviations from this AFS's own § Automation Hints / § Concrete Handles, both verified live before
implementation and landed alongside the test:

1. **`get_delete_confirm_message_text()` reads a NEW `delete-confirm-message` testid, not the bare
   `#alert-dialog-description` id this AFS suggested.** The AFS's own suggestion (chaining `.locator()` off
   `delete_confirm_dialog` to reach the id-selected `<Typography>`) conflicts with an established project
   precedent (ELITEA-1840's own memory finding: "this project's strict locator policy forbids a scoped raw-tag
   selector... even inside a real testid-anchored parent — scoped sub-selectors must themselves be
   `[data-testid="…"]`-based" — the same reasoning that produced the ZIP dialog's own `-title`/`-counter`/
   `-current-file` testids rather than raw tag/id selectors). Verified live via `add-data-testid`:
   `data-testid="delete-confirm-message"` added directly to `DeleteEntityModal.jsx`'s existing
   `id="alert-dialog-description"` Typography (the hand-authored a11y `id` is kept, unchanged) — a third generic,
   non-feature-scoped testid on this already-shared modal (alongside its existing `delete-confirm-dialog`/
   `delete-confirm-button`), landed on `automation/testids` (commit `a661d92d`). `get_delete_confirm_message_text()`
   reads this testid directly with zero `.locator()` chaining. Confirmed live the resulting text is byte-identical
   to the AFS's own asserted live message (`"Are you sure to delete the selected files?"`).
2. **`click_delete_files_button()` clicks `delete_files_button` directly — no `.locator("button")` scoping
   needed.** Confirmed live (CDP `getBoundingClientRect()` on both the wrapping `<Box data-testid="artifacts-delete-files-button">`
   and the inner `<IconButton>`): the two elements' bounding boxes are pixel-identical, so a Playwright `.click()`
   on the wrapper's own testid locator lands on — and fires the `onClick` of — the inner button with no
   scoped-selector chaining at all (simpler than the AFS's own "testid-on-wrapper + scoped click-target via
   `.locator("button")`" suggestion, and avoids a raw-tag-selector chain entirely).
3. **New `wait_for_file_count()` method — real, but NOT the actual root cause of the observed flake (correction
   below).** Local runs surfaced a genuine flake (3 failures in 8 runs) in Test Step 1: `get_file_names()` called
   immediately after `navigate_to_bucket()` occasionally read `[]` for a demonstrably non-empty bucket. The
   ORIGINAL diagnosis in this AFS (this paragraph, as first written) attributed this to the breadcrumb bucket-name
   label `_wait_for_bucket_panel()` waits on rendering synchronously from the URL's `bucket` query param,
   independent of the S3-listing fetch that actually populates the file table — and claimed this was "a DIFFERENT
   race from the one already documented on `navigate_to_bucket_folder()` (issue #638...)". **That diagnosis was
   wrong** (see item 4 below) — added `ArtifactsPage.wait_for_file_count(expected_count, timeout)` (Playwright
   auto-retrying `expect(...).to_have_count(...)` on the existing file-row locator — no fixed sleep; kept as a
   legitimate settle-wait, harmless even though it wasn't the fix for the actual race) and reported "5/5 clean
   re-runs after the fix" — a claim that did NOT hold under the reviewer's independent re-run (2/5 failures, see
   item 4).
4. **CORRECTION (R2 fix-only round, reviewer-driven): item 3's flake was issue #638, not a separate race.** An
   independent reviewer re-ran the merged test 5× in an isolated worktree and got 3 pass / 2 fail — both failures
   hit identically at `wait_for_file_count()` with the row-count locator STABLY stuck at 0 (not transiently empty,
   confirmed by both failures timing out at the full 15s). The failure screenshot showed the app had silently
   opened the WRONG bucket ("aa", an unrelated pre-existing bucket) instead of the freshly-seeded target — the
   exact symptom of issue #638 (project-id-resolution race stripping the `bucket` URL param before the
   auto-select-bucket effect reads it), already root-caused and guarded for the sibling method
   `navigate_to_bucket_folder()`. The plain `navigate_to_bucket()` this case uses had no such guard.
   `wait_for_file_count()` was solving the wrong layer: with the WRONG bucket loaded, the row-count locator is
   stably empty and can never converge no matter the timeout — item 3's "S3-listing-fetch lag" framing doesn't fit
   a stably-empty-forever locator, and in hindsight should have been recognized as the same #638 symptom at a
   second call site. **Fix:** `navigate_to_bucket()` (`automation/pages/artifacts_page.py`) now carries the same
   retry-on-URL-param-loss guard as `navigate_to_bucket_folder()` — re-checks the live URL's `bucket` query param
   after `_wait_for_bucket_panel()` settles and retries the navigation once (non-recursive beyond one retry) if
   the param was silently stripped. This touches a shared method with 4 other merged callers
   (`test_artifacts_upload_duplicate_cancel.py`, `test_artifacts_upload_three_options_verify_selection.py`,
   `test_artifacts_multi_file.py`, `test_artifacts_upload_multiple_files.py`); the change is purely defensive (only
   fires when the URL param check fails — never on the happy path any existing caller exercises) and all 4
   callers were re-run post-fix (see PR #661 description for the full re-run table). `wait_for_file_count()` is
   left in place — it's a real, harmless condition-based wait — but its docstring is corrected to no longer claim
   an independent root cause.
