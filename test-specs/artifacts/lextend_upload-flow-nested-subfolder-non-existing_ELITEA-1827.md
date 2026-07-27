# Test Case: Upload Flow – Upload File to Nested Subfolder Path (Non-Existing Folder)

## Metadata
- **TMS ID**: ELITEA-1827
- **Linked Story**: [EliteaAI/elitea-testing-public#240](https://github.com/EliteaAI/elitea-testing-public/issues/240) (tracking issue)
- **Priority**: l2 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399, freshly synced
  against `origin/main` this session via `git fetch origin` — see § Concrete Handles for
  per-testid provenance).
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **extend-existing** — case executed end-to-end live (all 14 case steps +
  all 4 preconditions verified against a real, freshly-created bucket), zero defects, zero
  testid gaps, zero console errors. This case's own observable (typing a NON-existent,
  multi-segment nested path in the Upload dialog auto-creates ALL intermediate folders in
  one action, and the left-panel tree/breadcrumb correctly render the resulting 2-level
  nesting) is a **partial** overlap with an already-merged spec — see § Overlap check for
  the dedup/extend boundary call. Not `already-covered` (the merged spec never exercises a
  multi-segment path — see below) and not fresh `ready-for-automation` (the gap is small
  enough to graft onto the existing test's own state-machine, per this project's own
  `extend-existing` precedent — see `.agents/memory/qa-engineer/
  extend_existing_means_insert_into_same_test_not_sibling_method.md`).

## Overlap check vs existing automation

`automation/tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py`
(ELITEA-1824, merged to `automation/base` — commit `79fe4e84`, PR #653) was read in full
(594 lines) before this run, alongside its AFS
(`test-specs/artifacts/l2_upload-three-options-verify-selection_ELITEA-1824.md`). Three
other sibling AFS files in this folder
(`l2_create-bucket-path1-and-upload-file_ELITEA-1808.md`,
`l2_upload-flow-upload-multiple-files-at-once_ELITEA-1826.md`,
`l3_upload-flow-duplicate-cancel-stops-entire-upload_ELITEA-1832.md`) were also read in
full — none of them touch nested-folder path typing at all (1808/1826/1832 all upload to
the bucket's own pre-filled root path, never editing the Path field's suffix).

**ELITEA-1824's covering test, `test_upload_via_three_options_and_verify_selection`
(lines 176–594), DOES exercise typed-path folder auto-creation** — its Steps 5-14
(lines 223–299) type a **single-segment** subfolder name (`"a1"`, case-text literal, not
yet existing) into the same `artifacts-upload-path-input-field`, click Upload, and verify:
the PUT lands at `{bucket}/a1/sample.txt` (line 269-282), the tree shows `a1` under the
bucket (line 289-291), and the breadcrumb reads `"{bucket} > a1"` (line 292-299). This
**proves single-level auto-creation** — the exact mechanism this case (1827) also uses.

**What ELITEA-1824 never exercises, and this case's own reason to exist:** a path typed
with **more than one `/`-separated segment that does not yet exist at ANY level**
(`"folder-a/folder-b"` — both `folder-a` and `folder-b` are new). This case's whole point
is proving that (a) a SINGLE upload action can auto-create an arbitrarily-deep chain of new
folders in one shot (not just one new leaf folder under an already-selected root), (b) the
left-panel tree correctly **lazy-renders and expands through two levels** (confirmed live
this run: `folder-b`'s tree-item DOM node does not exist at all until `folder-a` is
expanded — a qualitatively different rendering path than 1824's single-level case, where
the one new folder is a direct, immediately-visible child of the bucket), and (c) the
breadcrumb renders **three segments** (`bucket > folder-a > folder-b`) via
`get_breadcrumb_folder_names()` returning a 2-element list — 1824's own assertions only
ever check a 1-element list (`== ["a1"]` / `== []`), so the list's general multi-element
shape is unexercised prior to this case.

**Dedup verdict (Rule 6):** partial, not full, overlap. The underlying app mechanism
(nested "folders" are virtual — see § Known Defects/Network Behavior for why) is the same
one 1824 already proves at depth 1; this case proves it holds at depth 2 and exercises the
tree/breadcrumb's *multi-level* rendering, which 1824's assertions structurally cannot
catch (a depth-1 case can pass even if depth-2 rendering were broken — e.g. if the tree
component only supported one level of lazy-expansion, or if `get_breadcrumb_folder_names()`
had an off-by-one truncating to 1 crumb, 1824's suite would stay green while this
case's observable would fail). This is exactly the "small number of missing assertions on
an existing state-machine test" shape `extend-existing` exists for, not a distinct fresh
scenario — see § Gap assertions below for the precise insertion point.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- A bucket exists (the case's `bucket-1` is a **case-text placeholder**, not a literal
  fixture name — confirmed live again this run: the left-panel bucket list showed 209
  buckets at the time of this run, including every `autotest-*` bucket from prior cases'
  runs, and none named exactly `bucket-1`; same finding as every sibling AFS in this
  folder). The covering test's own `artifact_bucket` fixture already supplies this — no
  new bucket-creation step is needed for the extension (see § Gap assertions).
- Test file `sample.txt` is available for upload — confirmed live this is a real, intentional
  literal filename in the case text (not a placeholder, same finding as 1824/1826's own
  `sample.txt`/`sample.png`/`sample.md`) — reuse the covering test's existing
  `TXT_FILE_NAME`/`TXT_FILE_CONTENT` constants (line 99-100) rather than reintroducing a
  new file, since the target key (`{bucket}/folder-a/folder-b/sample.txt`) cannot collide
  with the covering test's own uses of the same literal name at other paths in the same
  bucket (`{bucket}/a1/sample.txt` from its own Steps 5-8) — S3-style storage keys are
  unique per FULL path, confirmed live this run (see § Network Behavior).
- Subfolders `folder-a` and `folder-b` do not yet exist in the bucket — inherent to the
  observable (this case's whole point is auto-creation of NEW nested folders); satisfied
  automatically by using literal names (`folder-a`, `folder-b`) that never appear anywhere
  else in the covering test's own bucket-content plan (`a1`, bucket root) — confirmed live
  this run there is no accidental collision.

## Test Data

### reuse-existing (from the covering test's own fixtures/constants)
- **Bucket**: the covering test's `artifact_bucket` fixture (`bucket_name` local var,
  line 186) — do **not** create a second bucket for this extension; append the new steps
  to run against the SAME bucket instance, after the covering test's own Step 46 (the
  bucket is left selected at its own root at that point — see § Gap assertions).
- **File**: the covering test's own `TXT_FILE_NAME`/`TXT_FILE_CONTENT`/`txt_path`
  (lines 99-100, 198-199) — same literal `sample.txt`, same fixed content, already written
  to `tmp_path` in the covering test's setup; no new file needs generating.

### generate-per-test
- **Nested path literal**: `"folder-a/folder-b"` — confirmed live via source
  (`UploadPathDialog.jsx`'s helper text: *"Files will be uploaded to the selected bucket.
  Optionally, enter a folder path to organize your files. Use "/" to create nested
  folder(s)."*) this is documented, intentional product behavior, not an incidental
  side-effect — the dialog's own copy explicitly advertises multi-segment `/`-separated
  nesting.

No `generate-shared-with-cleanup` applies — the extension runs entirely within the
covering test's own already-scoped, function-level bucket fixture.

## Test Steps

*(Steps below are the case's own 14 steps, executed live this run against a **fresh**
bucket built via the UI "New Bucket" form for exploration purposes —
`autotest-elitea1827-nested`, `Private` project. § Gap assertions maps each one onto
concrete NEW steps to append after the covering test's existing Step 46.)*

1. Navigate to the Artifacts section in the left sidebar (case step 1).
   - **Verify**: `artifacts-buckets-heading` visible.
2. Click on the bucket in the bucket list (case step 2).
   - **Verify**: bucket selected, right-panel header shows its name.
3. Click the upload icon in the top-right corner of the main panel (case step 3) —
   **confirmed live this is the TOOLBAR entry point** (`artifacts-upload-files-button`),
   distinct from the bucket-menu entry point ELITEA-1824's own known defect #649 affects
   (that defect is isolated to the bucket 3-dot-menu's own "Upload files" item inheriting a
   stale `currentPrefix` — the toolbar entry point this case uses recomputes its default
   path correctly from whatever folder is currently selected, confirmed live this run: at
   bucket ROOT the toolbar dialog's helper text and Path prefix both correctly read the
   bucket-root-only prefix, no stale-subfolder carryover).
   - **Verify**: native file-chooser fires immediately (case step 4, folded — same
     observable, no separate action).
4. (Folded into step 3's verify.)
5. Select `sample.txt` and click "Open" (case step 5).
   - **Verify**: "Upload files to ..." modal opens (case step 6).
6. (Folded into step 5's verify.)
7. Clear the Path field and enter `"{bucket_name}/folder-a/folder-b"` (case step 7) —
   confirmed live: type ONLY the suffix `"folder-a/folder-b"` into
   `artifacts-upload-path-input-field` (the editable native `<input>`); the bucket-name
   prefix is a separate, read-only `startAdornment` segment supplied automatically — do
   not type a leading `/`, the prefix already ends in one.
   - **Verify**: `get_upload_path_normalized_prefix() + get_upload_path_typed_value()`
     (`ArtifactsPage.get_upload_path_combined_text()`) reads
     `"{bucket_name}/folder-a/folder-b"`.
8. Click "Upload" (case step 8).
   - **Verify**: fires **exactly ONE** `PUT
     ${ELITEA_URL}/artifacts/s3/{bucket_name}/folder-a/folder-b/sample.txt?project_id=
     ${PROJECT_ID}` → `200 OK` — confirmed live via `browser_network_requests`; **no
     separate "create folder" request fires for either intermediate segment** (see
     § Network Behavior for why — this storage is key-prefix-based, "folders" are a UI
     construct derived from `/`-splitting object keys, not a distinct server-side entity).
9. Verify a success notification "Your file(s) have been successfully uploaded!" is
   displayed (case step 9).
   - **Verify**: confirmed live via a `MutationObserver` installed before the (throwaway,
     separate) confirmation upload used to independently verify the exact toast text —
     `toast-message` becomes visible with the byte-identical string
     `"Your file(s) have been successfully uploaded!"`.
10. Verify in the left panel the bucket expands and shows `folder-a` as a subfolder (case
    step 10).
    - **Verify**: `[data-testid="artifacts-tree-item-folder-a/"]` visible — confirmed live
      the app auto-navigates into the newly-created deepest folder immediately after
      upload (URL becomes `?bucket={bucket}&folder=folder-a%2Ffolder-b`), so `folder-a` is
      visible in the already-expanded tree without any manual click needed at this point.
11. Verify `folder-a` expands and shows `folder-b` as a nested subfolder (case step 11).
    - **Verify (two independent passes this run)**:
      1. Immediately after upload (auto-navigated state): `[data-testid=
         "artifacts-tree-item-folder-a/folder-b/"]` already visible (both levels rendered
         at once, matching the auto-navigation target).
      2. **Re-verified from a FRESH page load at bucket root** (navigated directly to
         `?bucket={bucket_name}`, no `folder` param): confirmed live at that point ONLY
         `artifacts-tree-item-folder-a/` exists in the DOM —
         `artifacts-tree-item-folder-a/folder-b/` is **not yet rendered** until `folder-a`
         is clicked/expanded. Clicking `folder-a`'s tree item (URL becomes
         `?bucket={bucket}&folder=folder-a`) causes `folder-b`'s tree-item node to appear
         for the first time. This confirms the tree **lazy-renders** each nesting level on
         expand, not eagerly on bucket load — the qualitatively new behavior this case
         exists to prove (1824's single-level case can't distinguish eager-vs-lazy
         rendering because there's only one level to render).
12. Click on `folder-b` in the left panel (case step 12).
    - **Verify**: `[data-testid="artifacts-tree-item-folder-a/folder-b/"]` clicked; URL
      becomes `?bucket={bucket_name}&folder=folder-a%2Ffolder-b`; `data-selected="true"`
      on that same tree-item testid (confirmed live via `get_attribute`).
13. Verify the main panel header displays `"{bucket_name} > folder-a > folder-b"` (case
    step 13).
    - **Verify**: `get_breadcrumb_bucket_text() == bucket_name` AND
      `get_breadcrumb_folder_names() == ["folder-a", "folder-b"]` — confirmed live via DOM
      query, a genuine 2-element list (1824's own assertions only ever produced a
      0- or 1-element list).
14. Verify `sample.txt` is listed in the file table inside `folder-b` (case step 14).
    - **Verify**: `get_file_row_text("sample.txt")` contains `"sample.txt"`, `"Text"`, and
      a byte-size string (`"50 B"` this run) — confirmed live via `_file_rows()` /
      `file_exists()`; pagination read `"1 - 1 of 1"` immediately after upload (before the
      throwaway toast-check file was added and then deleted again during cleanup).

## Expected Results
- Typing a NEW, multi-segment path (`"folder-a/folder-b"`, neither segment existing yet)
  into the Upload dialog's Path field and clicking Upload creates BOTH intermediate
  "folders" in a single PUT request — no separate folder-creation call, confirmed by
  network capture.
- The left-panel tree lazy-renders each new nesting level on expand (confirmed via a
  fresh-page-load re-verification, not just the auto-navigated post-upload state) and
  correctly shows both `folder-a` and, once expanded, `folder-b` beneath it.
- The main-panel breadcrumb renders all intermediate segments
  (`"{bucket} > folder-a > folder-b"`), proving `get_breadcrumb_folder_names()`'s
  multi-element case (not just its single-element case, which is all 1824 exercises).
- `sample.txt` lands at the correct, fully-nested key and is visible in the file table
  scoped to `folder-b` only.
- No console errors during the flow (confirmed: 0 errors across the entire run, only the
  one pre-existing unrelated Vite `docx-js-editor` externalization warning already
  documented in every sibling AFS in this folder).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session valid | Preconditions | `auth_state` fixture (skips login on localhost) | asserted |
| Precondition: bucket "bucket-1" exists | Bucket available | Preconditions + Test Data | covering test's `artifact_bucket` fixture, reused as-is — "bucket-1" confirmed live (again) as a case-text placeholder, none of 209 current buckets literally named that | asserted *(via extend — no new bucket)* |
| Precondition: sample.txt available for upload | File exists locally | Preconditions + Test Data | covering test's own `TXT_FILE_NAME`/`txt_path`, reused as-is | asserted *(via extend — no new file)* |
| Precondition: folder-a/folder-b do not yet exist | Fresh nested state | Preconditions + Test Data | inherent — literals never used elsewhere in the covering test's bucket-content plan | asserted |
| Step 1: Navigate to Artifacts | Artifacts page loads | Test Step 1 | `artifacts-buckets-heading` visible (covering test's own Step 1, unchanged) | asserted *(already proven by covering test)* |
| Step 2: Click bucket-1 | Bucket selected | Test Step 2 | covering test's own bucket-selection (Steps 2-4), unchanged | asserted *(already proven by covering test)* |
| Step 3: Click upload icon top-right | System file explorer opens | Gap Step 1 (new) | `expect_file_chooser()` on `artifacts-upload-files-button`, reusing `ArtifactsPage.upload_files()` — same method the covering test's own Steps 13-16 already call | asserted |
| Step 4: Verify file explorer opens immediately | File explorer open | Gap Step 1 (folded) | same observable | asserted *(decomposed)* |
| Step 5: Select sample.txt, click Open | File selected, modal opens | Gap Step 1 | `set_files([txt_path])` — `wait_for_upload_path_dialog()` | asserted |
| Step 6: Verify "Upload files to ..." modal opens | Modal visible | Gap Step 1 (folded) | same observable | asserted *(decomposed)* |
| Step 7: Clear Path field, enter "bucket-1/folder-a/folder-b" | Path shows nested value | Gap Step 2 (new) | `get_upload_path_combined_text()` — proves the general multi-segment-typing case the covering test's own single-segment ("a1") typing never exercises | asserted |
| Step 8: Click Upload | Upload completes | Gap Step 3 (new) | `PUT .../folder-a/folder-b/sample.txt` → 200, single request, confirmed live via network capture | asserted |
| Step 9: Verify success notification | Toast shown | Gap Step 4 (new) | `toast-message` exact text, MutationObserver-confirmed (same technique as 1824/1826's own precedent) | asserted |
| Step 10: Verify bucket expands, shows folder-a | folder-a visible | Gap Step 5 (new) | `artifacts-tree-item-folder-a/` visible | asserted |
| Step 11: Verify folder-a expands, shows folder-b | folder-b visible, LAZY-rendered | Gap Step 5 + Gap Step 6 (new) | `artifacts-tree-item-folder-a/folder-b/` — proven absent-until-expanded via a fresh-page-load re-check, the multi-level rendering the covering test structurally cannot exercise at depth 1 | asserted |
| Step 12: Click folder-b | folder-b selected | Gap Step 7 (new) | `click_tree_item("folder-a/folder-b/")`, `is_tree_item_selected()` reads `data-selected="true"` | asserted |
| Step 13: Verify breadcrumb "bucket-1 > folder-a > folder-b" | 3-segment breadcrumb | Gap Step 8 (new) | `get_breadcrumb_folder_names() == ["folder-a", "folder-b"]` — the 2-element-list case, unexercised by the covering test's own 0-/1-element assertions | asserted |
| Step 14: Verify sample.txt listed in folder-b | File in correct nested location | Gap Step 9 (new) | `get_file_row_text("sample.txt")` / `file_exists()` scoped to the folder-b view | asserted |
| Expected Final State: nested structure auto-created, file at correct path | Composite pass condition | Gap Steps 3, 5-9 | combination of the above | asserted |
| Pass criterion: "All steps complete without errors" | No errors during flow | All steps | console-error check (0 errors, confirmed this run) — extend the covering test's own EXISTING final console-error step (line 587-594) to also cover the appended Gap steps, rather than adding a second check | asserted |

### Axis 2 — Observables asserted beyond the case
- **Network-level proof of exactly ONE PUT request for the whole nested key, no
  intermediate "create folder" calls** — *added: stronger, more specific signal than a
  DOM-only "it looks nested" check; also the direct evidence for why this is safe,
  low-risk product behavior (nesting is a pure client-side path-string concern, not a
  distinct multi-step server operation that could partially fail).*
- **Lazy-vs-eager tree rendering, proven via a fresh-page-load re-check** (not just reading
  the auto-navigated post-upload DOM state) — *added: the auto-navigate-after-upload
  behavior alone would make BOTH lazy and eager rendering look identical (everything is
  already expanded); a second, independent pass from a cold bucket-root load is required
  to actually distinguish them, and is the single most load-bearing piece of new evidence
  this extension contributes.*
- **`get_breadcrumb_folder_names()`'s genuine multi-element return value**, confirmed via
  live DOM query rather than merely inferred from the covering test's single-element
  assertions — *added: an off-by-one truncation bug in that helper (real product code, not
  page-object code) would pass every existing 1824 assertion while failing this case's;
  this closes exactly that blind spot.*
- **Console-error check across the appended flow** — *added: standard silent-error guard,
  consistent with every sibling AFS's precedent; 0 errors confirmed this run (only the
  pre-existing unrelated Vite warning).*
- **Toast-text exact-match confirmation via a second, throwaway single-file upload +
  MutationObserver** (not required by the case's own step 9 beyond "a notification
  appears") — *added: same rationale as 1824/1826's own precedent — proves the EXACT
  case-specified string, not just "some toast fired."*

## Gap assertions (what the implementer appends to the covering test)

**Covering spec**: `automation/tests/ui/artifacts/
test_artifacts_upload_three_options_verify_selection.py::
TestArtifactsUploadThreeOptionsVerifySelection::
test_upload_via_three_options_and_verify_selection` (method body: lines 176–594).

**Insertion point**: immediately after the existing **Step 46** block (ends line 585),
and **before** the existing final side-channel console-error check (currently lines
587–594) — so that check's own docstring ("across the full ... flow") continues to be
literally true once the new steps are appended, with no need for a second console check.
At that point in the test the bucket is already selected at its own ROOT (Step 43/44
re-confirmed this), containing `sample.md` at root and `sample.txt`+`sample.png` under
`a1/` — a clean, known state to upload a fourth file into a brand-new nested path from.

**New steps to append** (renumber as `Step 47` onward — do not renumber the existing
1–46, this is pure append per the project's own `extend-existing` convention):

```python
        with allure.step(
            "Step 47 (ELITEA-1827 extension) — Click the TOOLBAR 'Upload files' icon "
            "again; select sample.txt; native file explorer opens immediately"
        ):
            artifacts_page.upload_files([str(txt_path)])
            artifacts_page.wait_for_upload_path_dialog()

        with allure.step(
            "Step 48 (ELITEA-1827) — Type a NEW, NON-existing two-segment nested path "
            "'folder-a/folder-b' into the Path field; verify the combined text"
        ):
            artifacts_page.upload_path_input_field.click()
            artifacts_page.upload_path_input_field.type("folder-a/folder-b")
            assert artifacts_page.get_upload_path_combined_text() == (
                f"{bucket_name}/folder-a/folder-b"
            ), "Path field should show the bucket prefix plus the typed nested suffix"

        with allure.step(
            "Step 49 (ELITEA-1827) — Click Upload; verify a SINGLE PUT lands at the "
            "fully-nested key (no separate folder-creation request)"
        ):
            with page.expect_response(
                lambda r: "artifacts/s3" in r.url and r.request.method == "PUT"
            ) as resp_info:
                artifacts_page.click_upload_path_upload_button()
            assert resp_info.value.status == 200
            assert (
                f"/artifacts/s3/{bucket_name}/folder-a/folder-b/{TXT_FILE_NAME}"
                in resp_info.value.url
            )

        with allure.step("Step 50 (ELITEA-1827) — Verify the success toast"):
            expect(artifacts_page.success_toast_message).to_be_visible()
            expect(artifacts_page.success_toast_message).to_contain_text(
                SUCCESS_TOAST_TEXT
            )

        with allure.step(
            "Step 51 (ELITEA-1827) — Verify the left panel shows folder-a under the "
            "bucket (auto-navigated state right after upload)"
        ):
            artifacts_page.wait_for_file_in_tree("folder-a/")

        with allure.step(
            "Step 52 (ELITEA-1827) — Re-load the bucket at its own ROOT (fresh page "
            "state, not the auto-navigated one); verify folder-b's tree node is "
            "LAZILY absent until folder-a is expanded, then click folder-a to expand it"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert not artifacts_page.is_tree_item_visible(
                "folder-a/folder-b/", timeout=ABSENCE_CHECK_TIMEOUT
            ), "folder-b's tree node should not exist before folder-a is expanded"
            artifacts_page.click_tree_item("folder-a/")
            artifacts_page.wait_for_file_in_tree("folder-a/folder-b/")

        with allure.step(
            "Step 53 (ELITEA-1827) — Click folder-b; verify it is selected and the "
            "breadcrumb shows the full 3-segment nested path"
        ):
            artifacts_page.click_tree_item("folder-a/folder-b/")
            assert artifacts_page.is_tree_item_selected("folder-a/folder-b/")
            assert artifacts_page.get_breadcrumb_bucket_text() == bucket_name
            assert artifacts_page.get_breadcrumb_folder_names() == [
                "folder-a", "folder-b",
            ]

        with allure.step(
            "Step 54 (ELITEA-1827) — Verify sample.txt is listed in the folder-b file "
            "table"
        ):
            assert artifacts_page.file_exists(TXT_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            row_text = artifacts_page.get_file_row_text(TXT_FILE_NAME)
            assert TXT_FILE_NAME in row_text and "Text" in row_text
```

Then widen the EXISTING final console-error step's docstring text (line 587-589) to
mention the appended nested-path flow, and let it run unchanged (it already reads
`console_errors` collected from page load, so it needs no code change beyond the comment —
confirmed live 0 errors across the appended flow this run).

## Cleanup
1. No new bucket/fixture cleanup needed for the extension — it reuses the covering test's
   own `artifact_bucket` fixture teardown as-is (**known pre-existing defect, already
   filed**: [#636](https://github.com/EliteaAI/elitea-testing-public/issues/636) — the
   delete call 404s and the bucket will likely leak; out of scope here, unchanged from the
   covering test's own existing behavior).
2. No other entities are created by this extension (no Agent, no Toolkit, no Credential).
3. **This exploration run's artifacts** (not part of the automated test — a standalone
   bucket built via the UI form to verify the case live before writing this AFS, since the
   automated extension runs inside the COVERING test's own fixture-managed bucket, not a
   new one): bucket `autotest-elitea1827-nested` was created in the `Private` project
   (id 399), ending this run containing `sample.txt` (50 B) at
   `folder-a/folder-b/sample.txt`. A throwaway `toastcheck-1827.txt` (used only to
   independently verify the exact toast text via `MutationObserver`) was uploaded to the
   same nested path and deleted again via the file-row dot-menu before hand-off. Left in
   place — matches this project's existing convention of ~209 un-deleted `autotest-*`
   buckets already present in `Private` from prior runs; safe to delete at any time via
   `ArtifactAPI.delete_bucket("autotest-elitea1827-nested")`.
4. Local exploration screenshot (repo root, untracked, uploaded to the `evidence`
   prerelease store and embedded below):
   `ELITEA-1827-step10-14-nested-tree-breadcrumb-file.png` — shows the 2-level tree
   (`folder-a` → `folder-b` → `sample.txt`), the 3-segment breadcrumb, and the file table
   scoped to `folder-b`, all live at once.

   ![Nested tree, breadcrumb, and file table](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1827-step10-14-nested-tree-breadcrumb-file.png)
5. Local temp upload source files (untracked, harmless to leave or delete):
   `.playwright-mcp/sample.txt`, `.playwright-mcp/toastcheck-1827.txt`.

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator
policy (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) is
**testid-only, no fallback ladder** — `LocatorDescriptor(testid=...)` with no
`fallback=`/`locator=`. Every row below carries a **PROVENANCE** column verified this run
via `cd ../EliteaUI && git fetch origin` followed by `git grep` against both
`origin/main` and `origin/automation/testids` (substring grep, since several of these are
set via single-quoted `inputProps`/ternary expressions rather than a literal
double-quoted JSX attribute — confirmed by reading the exact source lines, not just the
grep hit).

**Zero testid gaps this run** — every element this case touches already has a
policy-compliant testid on `automation/testids`, and `ArtifactsPage` already has every
method needed (see § Gap assertions / Automation Hints). No `add-data-testid` work
required.

| Element | testid | Provenance | Notes |
|---|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ | existing |
| Upload files button (toolbar) | `artifacts-upload-files-button` | on-main ✓ | this case's own entry point (case step 3) |
| "Upload files to ..." dialog | `artifacts-upload-path-dialog` | on-automation/testids only (awaiting promotion) | existing (ELITEA-1832) |
| Upload path input — read-only prefix wrapper | `artifacts-upload-path-input` | on-automation/testids only | `text_content()` includes the "Path" label + prefix; use `get_upload_path_normalized_prefix()`, not the raw read |
| Upload path input — editable `<input>` | `artifacts-upload-path-input-field` | on-automation/testids only | `UploadPathDialog.jsx`, via `slotProps.htmlInput` (ELITEA-1824's fix) — confirmed live this run accepts a full multi-segment string (`"folder-a/folder-b"`) in one `type()` call, no special handling needed for the embedded `/` |
| Upload path "Upload" button | `artifacts-upload-path-upload-button` | on-automation/testids only | existing (ELITEA-1832) |
| Left-panel tree item (file/folder) | `artifacts-tree-item-{key}` (dynamic) | on-automation/testids only | `FileTreeItem.jsx`; **key is the FULL relative path** — confirmed live this run `folder-b`'s own key is `folder-a/folder-b/` (not just `folder-b/`), a detail 1824's single-level case never had reason to surface since its only folder's key and leaf name coincide (`a1/` either way) |
| Bucket/tree-item "selected" state | `data-selected="true"/"false"` | on-automation/testids only | attribute on the same `artifacts-tree-item-{key}` node (ELITEA-1824); confirmed live on the depth-2 `folder-a/folder-b/` node exactly as on 1824's depth-1 `a1/` node — no new plumbing needed at deeper nesting |
| Main-panel breadcrumb — bucket label | `artifacts-breadcrumb-bucket-label` | on-automation/testids only | `ArtifactTableToolbar.jsx` (ELITEA-1824) |
| Main-panel breadcrumb — folder crumb(s) | `artifacts-breadcrumb-folder-label` (repeated, one per level) | on-automation/testids only | `BreadcrumbNavigation.jsx` (ELITEA-1824); confirmed live this run renders TWO elements when 2 levels deep — `get_breadcrumb_folder_names()`'s list-returning shape was written generically enough to already handle this correctly |
| File list container / file row | `artifacts-file-list` / `artifacts-file-row` | on-main ✓ | existing |
| Success toast (generic, app-wide) | `toast-message` | on-main ✓ | confirmed live this run, exact text `"Your file(s) have been successfully uploaded!"` |
| File-row actions dot-menu (cleanup only) | `artifact-actions-{filename}-menu-button` (dynamic) | on-main ✓ | used only to delete the throwaway toast-check file during this exploration, not part of the case's own steps |
| File-row "Delete" menu item (cleanup only) | `artifacts-file-delete-menuitem` | on-automation/testids only | computed via the shared `DotMenu`/`BasicMenuItem` `key`→`${key}-menuitem` mechanism, not a literal grep-able string (same caveat 1824's AFS already documents) |
| Delete-confirmation dialog "Delete" button (cleanup only) | `delete-confirm-button` | on-automation/testids only | existing |

## Network Behavior
- **Nested-path upload — exactly ONE request, confirmed live**:
  `PUT {ELITEA_URL}/artifacts/s3/{bucket}/folder-a/folder-b/sample.txt?project_id=
  ${PROJECT_ID}` → `200 OK`. Confirmed live:
  `PUT http://localhost:5173/artifacts/s3/autotest-elitea1827-nested/folder-a/folder-b/sample.txt?project_id=399`.
  **No separate request creates `folder-a` or `folder-b` as distinct entities** — this
  storage is S3-style/key-prefix-based, so "folders" are a client-side rendering construct
  derived by `/`-splitting the object's own key, not a server-side resource with its own
  lifecycle. This is *why* multi-level nesting is safe/low-risk to prove in a single
  upload action: there is no multi-step server operation that could partially fail midway
  (e.g. create `folder-a` successfully, then fail to create `folder-b`) — the whole nested
  path is encoded in one atomic PUT.
- **Bucket listing refetch after upload**: `GET {ELITEA_URL}/artifacts/s3/{bucket}
  ?project_id=${PROJECT_ID}&format=json` → `200 OK`, powers both the file-table and the
  left-panel tree's re-render — confirmed live the response's `contents[].key` field
  carries the full nested key (`"folder-a/folder-b/sample.txt"`), which the tree component
  derives its lazy per-level nodes from client-side.
- No unexpected requests observed between any click and its corresponding network call;
  zero console errors across the entire run (11 total console messages, 1 pre-existing
  unrelated Vite `docx-js-editor` warning, same as every sibling AFS in this folder).

## Known Defects Found During Exploration
**None found.** Live product behavior matches the case's expected behavior exactly: a
single upload action with a NEW, non-existing two-segment path auto-creates both
intermediate folders, the left-panel tree correctly lazy-renders and expands through both
levels, the breadcrumb renders the full 3-segment chain, and `sample.txt` lands at the
correct, fully-nested location. Zero console errors. This case's entry point (toolbar
upload icon, from bucket root) is unaffected by ELITEA-1824's own known defect #649 (which
is isolated to the BUCKET-MENU 3-dot entry point inheriting a stale `currentPrefix` — not
exercised here, confirmed live via the dialog's own helper text correctly reflecting
bucket-root-only state at the point this case's steps begin).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **Do not create a new test file.** Append the steps in § Gap assertions directly to
  `test_upload_via_three_options_and_verify_selection` in
  `automation/tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py`,
  per this project's own `extend-existing` precedent (`.agents/memory/qa-engineer/
  extend_existing_means_insert_into_same_test_not_sibling_method.md`): the covering test is
  already a single continuous state-machine walk through bucket/folder selection states,
  and this case's gap is more cells of that same machine (one more upload-and-verify
  sub-scenario), not a materially different flow that would justify its own setup.
- **Zero new page-object methods needed.** Every method the Gap steps call
  (`upload_files`, `wait_for_upload_path_dialog`, `upload_path_input_field`,
  `get_upload_path_combined_text`, `click_upload_path_upload_button`,
  `wait_for_file_in_tree`, `is_tree_item_visible`, `click_tree_item`,
  `is_tree_item_selected`, `get_breadcrumb_bucket_text`, `get_breadcrumb_folder_names`,
  `navigate_to_bucket`, `file_exists`, `get_file_row_text`) already exists on
  `ArtifactsPage` and was exercised live this run exactly as called in § Gap assertions —
  confirmed each one handles a depth-2 key (`folder-a/folder-b/`) with no special-casing
  needed beyond passing the full relative path string, same as it already does for
  depth-1 (`a1/`).
- **The `@allure.issue` decorator referencing this case's own TMS link is a follow-up for
  whoever lands the extension** — add a second
  `@allure.issue(".../ELITEA-1827_upload-flow-nested-subfolder-non-existing.md",
  "onetest-ai Test Case link")` alongside the existing ELITEA-1824/​#649 issue decorators
  (lines 166-175), so the shipped test's own traceability reaches BOTH TMS cases it now
  proves — per `.agents/memory/qa-engineer/
  coverage_classification_needs_board_task_not_just_behavioral_match.md`'s
  broader point that a behavioral match alone is not the same as delivered traceability;
  this extension's whole value would otherwise be invisible to a future audit grepping for
  ELITEA-1827's own issue link.
- Viewport: the covering test already sets `page.set_viewport_size({"width": 1600,
  "height": 900})` at its own setup (line 196) — inherited for free by the appended steps,
  no separate viewport call needed even though these Gap steps don't themselves assert the
  "Last update" timestamp column.
- Wait strategy: `page.expect_response()` for the single upload PUT (same idiom already
  established in this file's own Step 8/16/33 blocks); `wait_for_file_in_tree()` /
  `is_tree_item_visible()` for tree-node condition waits, never a fixed sleep — same
  precedent as the covering test's own existing steps.
