# Test Case: Upload Flow – File Uploaded to Selected Subfolder When Using Bucket Actions Button

## Metadata
- **TMS ID**: ELITEA-1834
- **Source case**: `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/artifacts/ELITEA-1834_*.md`
  (snapshot read from `.agents/automation/artifacts-w02/cases/ELITEA-1834.md`)
- **Priority**: medium (case metadata) → AFS `l2`
- **Feature / surface**: artifacts — bucket 3-dot ("Bucket actions") menu → "Upload files" → "Upload files to ..." dialog
- **Surface key**: `artifacts-upload-path-dialog`
- **Environment explored**: local `http://localhost:5173` (EliteaUI `automation/testids` → DEV backend,
  project `Private` / `project_id=399`), 2026-08-21
- **User set**: `${TEST_USER}` (on localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot, batch `artifacts-w02`
- **Shipped as**: `automation/tests/ui/artifacts/test_artifacts_upload_to_selected_subfolder.py`
  ::`TestArtifactUploadToSelectedSubfolder::test_upload_via_bucket_actions_lands_in_selected_subfolder`
  — implemented exactly to this AFS, zero handle drift, GREEN 1/1 first run (51.3 s,
  zero console errors, no page-object changes needed).
- **Status**: **ready-for-automation** — all 18 case steps executed live end-to-end in one
  pytest scratch run (34 s, zero console errors, every expected result matched exactly).
- **Filed this run**: [#1629](https://github.com/EliteaAI/elitea-testing-public/issues/1629)
  — CLARIFICATION (label `question`, `case-text-drift`): **this case's expected result is the
  exact behaviour bug [#649](https://github.com/EliteaAI/elitea-testing-public/issues/649)
  calls a defect.** See § Findings — the implementer must read this before writing the test.

---

## Overlap check vs existing automation

Searched `test-specs/artifacts/` and `automation/tests/ui/artifacts/` **by behaviour**
(bucket menu, upload path pre-fill, subfolder, `currentPrefix`), not by case id.

**Nearest neighbour — the only spec that touches this exact entry point:**
`automation/tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py`
(ELITEA-1824, extended by ELITEA-1827 and ELITEA-1835; merged to `automation/base`).
Its "Steps 30-32" block (lines ~442-467) opens the bucket 3-dot menu while `currentPrefix`
is `a1/` and reads the very same Path field.

**It is NOT coverage of this case — the expected result is inverted:**

| | ELITEA-1834 (this case) | 1824's block at the same DOM node |
|---|---|---|
| Asserted value of the Path prefix | `{bucket}/a1/` is **CORRECT** | `{bucket}/` (root) is correct → `expect.soft(...)` **fails on purpose** (`# Known defect: #649`) |
| What happens next | **Upload is clicked from that dialog**; the PUT, toast, breadcrumb, and a1-vs-root listing are asserted | The dialog is **abandoned** (`close_upload_path_dialog()`), the bucket is re-selected at root, and the upload is redone from root |

So the observable this case exists to prove — *a file uploaded through the bucket-actions
menu while a subfolder is selected actually lands in that subfolder and not at the bucket
root* — is asserted **nowhere** in the merged suite. `already-covered` and `extend-existing`
are both wrong here: 1824's covering block asserts the opposite expected result and never
completes the upload. Also checked and rejected as coverage: `test_artifacts_upload_multiple_files.py`
(ELITEA-1826, toolbar entry point), `test_artifacts_create_bucket_upload_file.py` (ELITEA-1808,
empty-state entry point + typed path), `test_artifacts_upload_path_cancel.py` (ELITEA-1825, Cancel).

**Boundary call (why a fresh spec, not an extension of 1824):** 1824's test is already a
50+-step, twice-extended flow whose middle is a `#649` soft-assert + recovery workaround.
Appending 1834 there would require asserting `{bucket}/a1/` as CORRECT ~15 lines from where
the same value is soft-asserted as a DEFECT, inside one test — an unreadable and actively
misleading spec. Fresh spec, own bucket, ~35 s.

---

## Preconditions

1. User authenticated (localhost: `auth_state` fixture; no login step).
2. **A bucket exists** — use the existing `artifact_bucket` fixture
   (`automation/fixtures/data_fixtures.py:1679`; API-created, auto-deleted in teardown).
   The case text names `bucket-1`; the suite's convention is a per-test unique bucket and
   the case's observable does not depend on the literal name.
3. **The bucket contains subfolder `a1`** — created as *transit* by one upload through the
   empty-state entry point with `a1` typed into the Path field (the same seeding technique
   ELITEA-1824 uses; the folder is a key prefix in S3, there is no "create folder" UI).
   Seed it with a file whose name is **not** `sample.txt` (this AFS used `seed.txt`) —
   uploading `sample.txt` into a folder that already holds `sample.txt` triggers the
   "Resolve duplicates" dialog and derails step 11.
4. `sample.txt` generated per-test via `tmp_path` (no repo fixture file needed).

---

## Test Data

| Field | Value | Note |
|---|---|---|
| Bucket | `artifact_bucket["name"]` | fixture-created, unique per test |
| Subfolder | `a1` | tree key is **`a1/`** (trailing slash), breadcrumb crumb is `a1` |
| Seed file (transit) | `seed.txt` | any content; only exists so `a1/` exists |
| Upload file (case subject) | `sample.txt`, 27 B | `b"ELITEA-1834 sample content\n"` |
| Expected path prefix in modal | `{bucket}/a1/` | read via `get_upload_path_normalized_prefix()` |
| Viewport | 1600x900 | the "Last update" column is clipped below ~1600 px (digest gotcha) |

---

## Concrete Handles

All confirmed live this session. **Provenance** column per `.agents/role-overrides.md`
§ Analyst slot (checked after `git -C ../EliteaUI fetch origin`, see § Live-execution evidence).

| Element / observable | Handle | Page-object member | Provenance |
|---|---|---|---|
| Bucket row (left panel) | `artifacts-bucket-row-{name}` | `ArtifactsPage.click_bucket_row()` / `is_bucket_selected()` | on-main ✓ |
| Bucket row 3-dot menu button | `bucket-menu-{name}-menu-button` (`BUCKET_MENU_BUTTON` class template; composed at runtime by `DotMenu.jsx:354` from `id`) | `hover_bucket_row()` + `open_bucket_menu()` | on-main ✓ |
| Bucket menu — "Upload files" item | `bucket-menu-upload-files-menuitem` (composed by `DotMenu.jsx:57` from `BucketItem.jsx:153`'s `key: 'bucket-menu-upload-files'`) | `bucket_menu_upload_files_menuitem`, `click_bucket_menu_upload_files_item(paths)` | on-main ✓ |
| Left-tree node (folder/file) | `[data-testid="artifacts-tree-item-{key}"]` (`ARTIFACTS_TREE_ITEM` class constant; key `a1/`, `a1/sample.txt`) | `click_tree_item()`, `is_tree_item_selected()`, `is_tree_item_visible()` | on-main ✓ |
| Tree-node selected state | `data-selected="true"` attribute on the node above | `is_tree_item_selected("a1/")` | on-main ✓ |
| "Upload files to ..." dialog root | `artifacts-upload-path-dialog` | `wait_for_upload_path_dialog()` | on-main ✓ |
| Path field (read-only prefix adornment) | `artifacts-upload-path-input` | `get_upload_path_normalized_prefix()` | on-main ✓ |
| Path field (editable segment) | `artifacts-upload-path-input-field` | `get_upload_path_typed_value()`, `fill_upload_path()` | on-main ✓ |
| Dialog description line | `artifacts-upload-path-description-text` | `get_upload_path_description_text()` | on-main ✓ (`UploadPathDialog.jsx`) |
| Dialog Upload button | `artifacts-upload-path-upload-button` | `click_upload_path_upload_button_and_capture_response()` | on-main ✓ |
| Success toast | `toast-message` | `success_toast_message` | on-main ✓ |
| Breadcrumb bucket / folder crumbs | `artifacts-breadcrumb-bucket` / `artifacts-breadcrumb-folder-{n}` | `get_breadcrumb_bucket_text()`, `get_breadcrumb_folder_names()` | on-main ✓ |
| File rows (right panel) | `artifacts-file-row` / `artifacts-folder-row` inside `artifacts-file-list` (`ArtifactTable.jsx:525`) | `get_file_names()`, `get_file_row_text()`, `wait_for_file_count()` | on-main ✓ |
| Upload request | `PUT /artifacts/s3/{bucket}/a1/sample.txt?project_id=<id>` → 200 | `click_upload_path_upload_button_and_capture_response()` | n/a (network) |

**No new testid is needed for this case** — every element it touches already carries one.

---

## Test Steps

Marker set as SHIPPED: `ui`, `regression`, `p2` (case priority medium), `new`.
*(Amended by the implementer: this AFS originally listed an `artifacts` marker —
no such marker is registered in `automation/pytest.ini` (no artifacts spec uses one),
so it would only raise an unknown-marker warning. `new` is the suite's own
"added on `automation/base`, not yet validated on a deployed env" marker, matching
the sibling upload specs `test_artifacts_upload_path_cancel.py` /
`test_artifacts_upload_three_options_verify_selection.py`.)*
Each step wrapped in `with allure.step("Step N — ...")`.

| # | Action | Assert (observed live) |
|---|---|---|
| — | *(transit)* seed `a1/` : select bucket → `upload_files_via_empty_state([seed.txt])` → `fill_upload_path("a1")` → Upload | PUT 200 to `.../a1/seed.txt`; breadcrumb becomes `{bucket} > a1` |
| 1 | `navigate_to_artifacts()` + `wait_for_page_load()` | Artifacts page loaded, bucket list rendered |
| 2 | `click_bucket_row(bucket)` (returns to root and leaves the tree expanded) | `is_bucket_selected(bucket)` is `True`; `is_tree_item_visible("a1/")` is `True`; breadcrumb folder crumbs `== []`. **If `a1/` is not visible, click the row once more** — a click on an already-selected bucket TOGGLES the tree (CLARIFICATION #651) |
| 3 | `click_tree_item("a1/")` | node exists and click resolves |
| 4 | read tree node state | `is_tree_item_selected("a1/")` is `True`; `is_bucket_selected(bucket)` flips to `False` (selection is exclusive — Axis-2 observable) |
| 5 | read breadcrumb + URL | `get_breadcrumb_bucket_text() == bucket`, `get_breadcrumb_folder_names() == ["a1"]`; URL gains `&folder=a1` |
| 6 | `hover_bucket_row(bucket)` → `open_bucket_menu(bucket)` | menu open |
| 7 | read menu items | `bucket_menu_upload_files_menuitem.is_visible()` is `True`; full text is `"Upload filesRenamePin to topDelete"` (case says "options including Upload files" — do not assert the whole string; "Rename" vs "Edit" is CLARIFICATION #650) |
| 8-10 | `click_bucket_menu_upload_files_item([str(sample_txt)])` | Playwright's `expect_file_chooser` fires **on the click** (no delay) — this IS the automatable form of case steps 8-9 ("system file explorer opens immediately"); the native OS dialog itself is not inspectable |
| 11 | `wait_for_upload_path_dialog()` | `upload_path_dialog.is_visible()` is `True` |
| 12 | `get_upload_path_normalized_prefix()` | `== f"{bucket}/a1/"` **exactly**. (raw `text_content()` is `'Path​{bucket}/a1/​'` — never assert on the raw form.) Also `get_upload_path_typed_value() == ""` (nothing pre-typed) |
| 13 | `get_upload_path_description_text()` | `== f'Files will be uploaded to "{bucket}/a1/". Optionally, enter a subfolder path (relative to current location). Leave empty to upload to the current folder.'` |
| 14 | `click_upload_path_upload_button_and_capture_response()` | response `.status == 200` and `f"{bucket}/a1/sample.txt" in response.url` (PUT) |
| 15 | success toast | `expect(success_toast_message).to_have_text("Your file(s) have been successfully uploaded!")` |
| 16 | breadcrumb + tree after upload | breadcrumb still `{bucket}` / `["a1"]`, URL still `&folder=a1`, `is_tree_item_selected("a1/")` still `True` |
| 17 | `wait_for_file_count(2)` then `get_file_names()` | `set(...) == {"sample.txt", "seed.txt"}`; row text matches `sample.txt\tText\t27 B\t<DD-MM-YYYY, HH:MM AM/PM>`; `is_tree_item_visible("a1/sample.txt")` is `True` |
| 18 | `click_bucket_row(bucket)` (back to root) then `get_file_names()` | `== ["a1"]` — the root listing contains only the `a1` **folder row**, `"sample.txt" not in ...` |
| — | console | no `console.error` messages across the whole flow |

---

## Expected Results

1. Selecting `a1` in the tree makes it the exclusive selection and drives breadcrumb + URL.
2. The bucket-actions menu's "Upload files" opens the file chooser immediately and, after
   selection, the "Upload files to ..." dialog whose Path prefix is **`{bucket}/a1/`** —
   i.e. the upload target follows the current selection, not the bucket root.
3. The upload PUTs to `.../{bucket}/a1/sample.txt`, returns 200, toasts success.
4. The view stays on `{bucket} > a1`; `sample.txt` is listed there and is **not** at root.

---

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | — | `auth_state` fixture | setup | covered (transit) |
| Precondition: bucket + subfolder `a1` | — | `artifact_bucket` + seeded upload | setup | covered (transit) |
| Precondition: `sample.txt` available | — | `tmp_path` generated | setup | covered |
| Step 1 Navigate to Artifacts | page loads | Step 1 | `wait_for_page_load()` | covered |
| Step 2 Click bucket to expand | subfolder `a1` shown | Step 2 | `is_tree_item_visible("a1/")` | covered (toggle caveat #651) |
| Step 3 Click subfolder `a1` | `a1` selected | Step 3-4 | `is_tree_item_selected("a1/")` | covered |
| Step 4 `a1` highlighted | highlighted state | Step 4 | `data-selected="true"` | covered |
| Step 5 Header shows `bucket > a1` | breadcrumb correct | Step 5 | breadcrumb getters | covered |
| Step 6 Bucket 3-dot menu | dropdown appears | Step 6 | `open_bucket_menu()` | covered |
| Step 7 Menu has "Upload files" | menu visible | Step 7 | `bucket_menu_upload_files_menuitem.is_visible()` | covered |
| Step 8 Click "Upload files" | file explorer opens | Step 8-10 | `expect_file_chooser` fires on click | covered (OS dialog not inspectable — chooser event is the observable) |
| Step 9 Explorer opens immediately | file explorer open | Step 8-10 | same event, no wait needed | covered |
| Step 10 Select `sample.txt`, Open | upload modal opens | Step 8-10 → 11 | `wait_for_upload_path_dialog()` | covered |
| Step 11 Modal visible | modal visible | Step 11 | `upload_path_dialog.is_visible()` | covered |
| Step 12 Path shows `bucket-1/a1/` | path pre-filled with selection | Step 12 | exact equality on normalized prefix | covered — **but see § Findings / #1629** |
| Step 13 Description names the target | description correct | Step 13 | exact equality on description text | covered |
| Step 14 Click Upload | upload completes | Step 14 | PUT 200 + URL contains `a1/sample.txt` | covered |
| Step 15 Success notification | exact toast text | Step 15 | `to_have_text(...)` | covered |
| Step 16 Panel remains on `bucket > a1` | subfolder view retained | Step 16 | breadcrumb + URL + tree selection | covered |
| Step 17 `sample.txt` in `a1` table | file listed | Step 17 | file-name set + row text | covered |
| Step 18 `sample.txt` NOT at root | absent at root | Step 18 | root listing `== ["a1"]` | covered |
| Pass/Fail: "no errors" | clean run | console listener | end of test | covered |

### Axis 2 — Analyst additions (beyond the case text)

| Added observable | Why |
|---|---|
| PUT status 200 + the request URL contains `{bucket}/a1/sample.txt` | The case's step 17/18 UI check can pass off a client-side optimistic listing; the request URL is the system's own statement of where the object was written — the strongest available oracle for "correct subfolder". |
| `is_bucket_selected(bucket)` becomes `False` when `a1` is selected | Case step 4 asserts `a1` is highlighted; selection being *exclusive* is the property that makes the highlight meaningful, and it is one attribute read away. |
| `get_upload_path_typed_value() == ""` | Distinguishes "prefix adornment carries `a1/`" (the case's claim) from "someone pre-typed a suffix" — without it, step 12 could pass for the wrong reason. |
| `is_tree_item_visible("a1/sample.txt")` | The left tree is a second, independent rendering of the same placement; cheap cross-check that the table row is not a stale/optimistic entry. |
| Zero `console.error` across the flow | Standard side-channel check (skill § Execute step 3). |
| Root listing asserted as exactly `["a1"]` rather than only `"sample.txt" not in ...` | Exact equality also catches a file wrongly written to root under a *different* name (e.g. a mangled key). |

---

## Fidelity Declaration

| Substitution | Transit or terminal | Authority |
|---|---|---|
| Bucket created via the artifacts **API** (`artifact_bucket` fixture) instead of the create-bucket UI | **Transit** — the case's preconditions state the bucket merely "exists"; every observable this case asserts (path pre-fill, PUT target, listing) is produced by the product after real UI interaction. | Established suite convention (ELITEA-1824/1825/1826/1830 all seed this way). |
| Subfolder `a1` seeded by a real UI upload through the empty-state entry point | **Transit** — a real product action, not injected state; the case's own subject (bucket-menu upload) is untouched. | Case precondition "Bucket bucket-1 exists with subfolder a1". |

No `page.route`, no `route.fulfill`, no `page.evaluate`, no monkeypatching. Every asserted
value (path prefix, description string, PUT URL/status, toast, breadcrumb, listings) is
produced by the running system.

---

## Blocked Steps

None. All 18 steps executed live.

---

## Findings

### 1. CRITICAL FOR THE IMPLEMENTER — this case's expected result contradicts open bug #649

`.agents/testing.md` § Merge gate's sanctioned-RED machinery is **not** what this case needs,
but the implementer must not be surprised by the collision:

- **ELITEA-1834 (this case)** expects the bucket-menu upload dialog to pre-fill `{bucket}/a1/`
  when `a1` is selected. **The product does exactly that** — verified live, step 12.
- **[#649](https://github.com/EliteaAI/elitea-testing-public/issues/649)** (filed from
  ELITEA-1824) calls that same behaviour a MAJOR defect and the merged spec
  `test_artifacts_upload_three_options_verify_selection.py` carries a deliberately-failing
  `expect.soft(...)` against it.

The product cannot satisfy both: `Artifacts.jsx` holds a single `currentPrefix` state
(line 95) that `BucketItem.jsx`'s `handleUploadClick` (line 96) does not reset, and
`UploadPathDialog.jsx:94` renders `{bucket}/{currentPrefix}`. The two cases describe the
identical machine state with opposite expectations.

Filed as **[#1629](https://github.com/EliteaAI/elitea-testing-public/issues/1629)**
(`question` + `case-text-drift`) for a human ruling. **Not** classified `defect-found`:
per the reverse-masking guard the live product matches *this* case's text exactly.

**Implementer instruction:** write the test to this AFS (assert the live contract as
CORRECT, hard asserts, no soft/known-defect comment). Add a docstring paragraph pointing at
#1629 and #649 so the contradiction is visible at the point of reading. If a human resolves
#1629 in favour of #649, this spec's steps 12-18 change — that is a re-analysis, not a
silent weakening.

### 2. Case text vs product — minor, already tracked
- Bucket menu item labelled **"Rename"**, not "Edit" — CLARIFICATION #650 (already filed;
  this case only requires "Upload files" to be present, so nothing new).
- Clicking an already-selected bucket row **toggles** the tree — CLARIFICATION #651. The
  spec must guard step 2 with a visibility check + conditional second click, not assume expand.

### 3. No new testid needed — and every handle is already on `EliteaAI/EliteaUI` `main`
Verified after `git -C ../EliteaUI fetch origin` (2026-08-21): all 13 handles in § Concrete
Handles resolve on `origin/main`, `artifacts-upload-path-description-text` included (it is on
`main`, despite ELITEA-1835's AFS having requested it as new). **This case has no testid
dependency that blocks promotion.**

**Grep gotcha worth carrying forward:** the closure-record two-stage grep
(`git grep -- "$t" … | grep -iE '(data-testid|testid[[:space:]]*[:=])'`) reports a FALSE
"not on main" for three of these handles, because the wiring line carries neither token:
`ArtifactTable.jsx:525` (`row.type === … ? 'artifacts-folder-row' : 'artifacts-file-row'`)
and `BucketItem.jsx:153` (`key: 'bucket-menu-upload-files'`, later composed into
`…-menuitem` by `DotMenu.jsx:57`). Verify these by reading the hit, not by counting it.

---

## Live-execution evidence (2026-08-21, localhost:5173, project `Private` / 399)

Executed as a throwaway pytest spec (`tests/ui/artifacts/test_scratch_1834.py`, deleted
after the run) — the digest's established probe pattern; Playwright MCP was not attempted
(8th consecutive session, see `_surface.md` § gotchas). Bucket
`autotest-test-scratch-1834-177255`. Total runtime **34.19 s**, 1 passed, console errors `[]`.

```
[PRECOND] seed PUT 200 http://localhost:5173/artifacts/s3/autotest-test-scratch-1834-177255/a1/seed.txt?project_id=399
[S2] bucket selected=True tree a1 visible=True breadcrumb=autotest-... / [] url=...?bucket=autotest-...
[S3-4] a1 selected=True bucket selected=False
[S5] breadcrumb='autotest-test-scratch-1834-177255' / ['a1'] url=...?bucket=...&folder=a1
[S5] files in a1 view: ['seed.txt']
[S6-7] menu items text='Upload filesRenamePin to topDelete'
[S7] Upload files item visible=True
[S11] dialog visible=True
[S12] normalized prefix='autotest-test-scratch-1834-177255/a1/' raw='Path​autotest-test-scratch-1834-177255/a1/​' typed=''
[S13] description='Files will be uploaded to "autotest-test-scratch-1834-177255/a1/". Optionally, enter a subfolder path (relative to current location). Leave empty to upload to the current folder.'
[S14] PUT 200 http://localhost:5173/artifacts/s3/autotest-test-scratch-1834-177255/a1/sample.txt?project_id=399
[S15] toast='Your file(s) have been successfully uploaded!'
[S16] breadcrumb='autotest-test-scratch-1834-177255' / ['a1'] url=...&folder=a1 ; a1 tree selected=True
[S17] files in a1 view=['sample.txt', 'seed.txt'] row='sample.txtText27 B21-08-2026, 09:16 PM'
[S17] tree has a1/sample.txt=True
[S18] root breadcrumb='autotest-test-scratch-1834-177255' / [] ; files at root=['a1']
[CONSOLE] errors=[]
```
