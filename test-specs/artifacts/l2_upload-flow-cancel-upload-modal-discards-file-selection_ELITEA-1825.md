# Test Case: Upload Flow – Cancel Upload Modal Discards File Selection

## Metadata
- **TMS ID**: ELITEA-1825
- **Priority**: l2 (source case says `priority: medium`; filed under `l2_` to match the
  sibling upload-flow AFS naming in this folder — ELITEA-1824/1826 are `l2_`, the
  duplicate-resolution siblings are `l3_`)
- **Feature / module**: artifacts (upload flow)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private`), 2026-08-21
- **User set**: `${TEST_USER}` (on localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — all 11 case steps executed live end-to-end in one
  scripted run; every expected result held exactly as authored. One testid gap found
  (the modal's **Cancel** button carries no testid — implementer work, see § Concrete
  Handles) and one harmless case-text typo recorded (§ Findings). No defects.

## Overlap check vs existing automation

Read before executing: `automation/pages/artifacts_page.py` (upload region, lines
151–400 / 2141–2300), and the four closest siblings —
`automation/tests/ui/artifacts/test_artifacts_upload_duplicate_cancel.py` (ELITEA-1832),
`test_artifacts_upload_three_options_verify_selection.py` (ELITEA-1824),
`test_artifacts_upload_multiple_files.py` (ELITEA-1826),
`test_artifacts_create_bucket_upload_file.py` (ELITEA-1808), plus their AFS files.

- **ELITEA-1832** (`test_artifacts_upload_duplicate_cancel.py:226-260`) is the nearest
  neighbour and the one that must NOT be mistaken for coverage: it clicks **Cancel on the
  "Resolve duplicates" dialog** — a *second*, different modal reached only after clicking
  **Upload** in the path dialog. ELITEA-1825's subject is Cancel on the **first** modal
  ("Upload files to ...", `artifacts-upload-path-dialog`), i.e. abandoning the upload
  *before* Upload is ever pressed. Different element, different component
  (`DuplicateResolutionDialog.jsx` vs `UploadPathDialog.jsx`), different product code path
  (`handleCancel` → `onClose` + `setFolderPath('')` never reaches the duplicate diff at
  all). Its terminal assertions (no toast, file absent, count unchanged) look similar
  precisely because both abort an upload — that is behavioural similarity of the
  *outcome*, not of the *trigger*.
- **ELITEA-1824** (`test_artifacts_upload_three_options_verify_selection.py:481`) does
  close the path dialog — but via **Escape**, and only as a workaround step to re-enter the
  same flow from bucket root (defect `#649`); it asserts nothing about the upload being
  discarded, no toast absence, no unchanged file table at that point.
- **ELITEA-1826 / ELITEA-1808** always complete their uploads; neither ever cancels.

Verdict: **no existing merged spec proves this observable** → `ready-for-automation`.

## Preconditions
- User logged in (localhost `auth_state` fixture).
- **A bucket exists.** `bucket-1` in the case text is a placeholder — no such bucket exists
  in the project (same finding as ELITEA-1808/1824/1826). Use the existing
  `artifact_bucket` fixture (`automation/fixtures/data_fixtures.py:1679`, API-created,
  function-scoped, torn down by the fixture).
- **The bucket holds at least one pre-existing file**, so "the file table is unchanged"
  (case step 10 / Expected Final State) is a real observable rather than
  empty-stays-empty. Seed it via `artifact_api.upload_file(bucket, "seed.txt", b"...")`
  (`automation/api/client.py:1434`) — transit-only setup, see § Fidelity Declaration.
- Test file `sample1.txt` generated in-test via `tmp_path` (project convention — there is
  no checked-in fixture-files directory).

## Test Data

### generate-per-test
| Item | Value | Note |
|---|---|---|
| Bucket | `artifact_bucket` fixture (`autotest-…`) | do NOT hardcode `bucket-1` |
| Pre-existing file | `seed.txt`, small text bytes, uploaded via `ArtifactAPI.upload_file` | gives baseline count = 1 |
| File to select | `sample1.txt` written by `tmp_path` (content irrelevant; this run 24 B) | the case's literal name — safe, bucket is unique per test |
| Probe folder path (Axis-2 only) | `probe-folder` typed into the Path field before Cancel | proves the dialog's own state is reset |
| Viewport | 1600×900 | the file table's `Last update` column clips below ~1600 px (documented in `_surface.md`) |

## Concrete Handles

All testid-only per `.agents/testing.md` § Locator policy. Provenance verified this run
with a fresh `git fetch origin` in `../EliteaUI`.

| Element | Handle | Page-object member | Provenance |
|---|---|---|---|
| Toolbar upload icon | `artifacts-upload-files-button` | `ArtifactsPage.upload_files_button` / `upload_files(paths)` (`artifacts_page.py:222`, `:2141`) | on-main ✓ |
| "Upload files to ..." modal root | `artifacts-upload-path-dialog` | `upload_path_dialog` / `wait_for_upload_path_dialog()` (`:290`, `:2184`) | on-main ✓ |
| Path field (read-only prefix) | `artifacts-upload-path-input` | `get_upload_path_normalized_prefix()` (`:2232`) — strips the two `​` MUI zero-width spaces the raw `text_content()` carries | on-main ✓ |
| Path field (editable input) | `artifacts-upload-path-input-field` | `get_upload_path_typed_value()` (`:2249`) | on-main ✓ |
| Modal description line | `artifacts-upload-path-description-text` | `get_upload_path_description_text()` (`:2287`) | on-main ✓ |
| Modal **Cancel** button | `artifacts-upload-path-cancel-button` | **testid needed** — new `LocatorDescriptor` + a `click_upload_path_cancel_button()` action | **needs-adding** |
| Modal Upload button (not clicked here; used only to prove the pair) | `artifacts-upload-path-upload-button` | `click_upload_path_upload_button()` | on-main ✓ |
| Success toast | `toast-message` | `success_toast_message` (`:391`) | on-main ✓ |
| File list container | `artifacts-file-list` | `file_exists()` / `get_file_names()` (`:1710`, `:1815`) | on-main ✓ |
| Pagination counter | `artifacts-pagination-page-info` | `get_pagination_info_text()` (`:3537`) — **prefer this over `get_total_file_count_from_pagination()` (`:1792`), which is a pre-existing raw-CSS handle (tech debt #25/#42)** | on `automation/testids` only (added by the ELITEA-1803 cluster, EliteaAI/EliteaUI@6449a5c4) — human cherry-pick to `main` pending |

### testid needed: `artifacts-upload-path-cancel-button`
`../EliteaUI/src/pages/Artifacts/component/UploadPathDialog.jsx` — the `actions` fragment
renders two `Button.BaseBtn`s; the second (Upload) already carries
`data-testid="artifacts-upload-path-upload-button"`, the first (Cancel, `onClick={handleCancel}`)
carries none. Confirmed live this run: enumerating the dialog's buttons returned
`[('', None), ('Cancel', None), ('Upload', 'artifacts-upload-path-upload-button')]`.
Add the attribute to the existing Cancel `Button.BaseBtn` — **attribute only, no new DOM
node, no hook, no structural change** (zero-functional-impact check, `add-data-testid`
§ 5.5). Naming follows the sibling exactly. Do **not** substitute Escape for the click:
ELITEA-1824 legitimately uses Escape for a *workaround*, but this case's step 8 is
literally "Click Cancel", and Escape exercises MUI's `onClose` rather than the button.

## Test Steps

Marker set: `@pytest.mark.p2 @pytest.mark.artifacts @pytest.mark.regression @pytest.mark.ui`.
Each step in its own `with allure.step("Step N — …")`.

1. **Setup (preconditions, not a case step)** — `artifact_bucket` fixture; seed `seed.txt`
   via `artifact_api.upload_file`; write `sample1.txt` into `tmp_path`; set viewport
   1600×900.
2. **Step 1** — `navigate_to_artifacts()` + `wait_for_page_load()`.
   *Verify*: artifacts page loaded (`artifacts-buckets-heading` visible).
3. **Step 2** — `navigate_to_bucket(bucket_name)`.
   *Verify*: URL carries `?bucket={bucket_name}`; record the baseline —
   `baseline_names = get_file_names()` (live: `['seed.txt']`) and
   `baseline_info = get_pagination_info_text()` (live: `1 - 1 of 1`).
4. **Steps 3–6 (mechanically inseparable — same folding ELITEA-1832 applies)** —
   `upload_files([str(sample1_path)])`. The `expect_file_chooser` context must wrap the
   click; the chooser fires the instant the button is clicked (no loading delay,
   re-confirmed live) and files are set the moment it resolves. A chooser that never
   opened raises a timeout here, which IS the assertion for case steps 3–5.
5. **Step 7** — `wait_for_upload_path_dialog()`.
   *Verify*: dialog visible; `get_upload_path_normalized_prefix()` contains
   `f"{bucket_name}/"` (live raw read: `'Path​{bucket}/​'`);
   `get_upload_path_typed_value() == ""`; description text equals the no-prefix wording
   (live: `Files will be uploaded to the selected bucket. Optionally, enter a folder path
   to organize your files. Use "/" to create nested folder(s).`).
6. **Axis-2 probe (before step 8)** — fill the editable Path field with `probe-folder`;
   assert `get_upload_path_typed_value() == "probe-folder"`. This makes step 8's discard
   observable (see Axis 2, row A2-3).
7. **Step 8** — start `capture_requests_matching("artifacts")`, then
   `click_upload_path_cancel_button()` (new page-object action on the new testid).
8. **Step 9** — `upload_path_dialog.wait_for(state="hidden")`.
   *Verify*: modal hidden **and** the captured request list is empty — zero `artifacts`
   requests fired by Cancel (live: `[]`). This is the strong form of "no upload happened",
   mirroring ELITEA-1832's step-11 assertion.
9. **Step 10** — `expect` the file table unchanged: `file_exists("sample1.txt")` is
   `False` (use a short absence timeout, ~3 s), `get_file_names() == baseline_names`, and
   `get_pagination_info_text() == baseline_info`. Then **reload** the page and re-navigate
   to the bucket and re-assert `get_file_names() == baseline_names` — the reload makes the
   *server* the oracle rather than the un-refreshed client list (live: `['seed.txt']` both
   before and after reload).
10. **Step 11** — `expect(success_toast_message).to_have_count(0, timeout=…)` (live: 0
    toasts, checked ~2.5 s after Cancel).
11. **Side channel** — assert no `console` errors were emitted during the flow (live: none).

## Expected Results
- The "Upload files to ..." modal opens on file selection with the Path field pre-filled
  with `{bucket}/` and an empty editable segment.
- Clicking Cancel closes the modal, fires **zero** network requests, uploads nothing, and
  shows **no** success toast.
- The bucket's file table is byte-identical to its baseline — before *and* after a reload.
- Re-opening the upload dialog shows a **cleared** Path field (the discard is real state
  reset, not just a hidden modal).

## Coverage Map

### Axis 1 — Case coverage
| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| P1 | User logged in | — | `auth_state` fixture | setup | precondition |
| P2 | Bucket "bucket-1" exists | — | `artifact_bucket` fixture (+ seeded `seed.txt`) | setup | precondition (name is a placeholder — § Preconditions) |
| P3 | Test file `sample1.txt` available | — | `tmp_path` | setup | precondition |
| 1 | Navigate to Artifacts | Artifacts page loads | Step 2 | `artifacts-buckets-heading` visible | asserted |
| 2 | Click bucket in list | Bucket is selected | Step 3 | URL `?bucket=` + baseline read from the bucket's own table | asserted |
| 3 | Click upload icon | File explorer opens | Step 4 | `expect_file_chooser` resolves (timeout = fail) | asserted (folded) |
| 4 | Verify explorer opens immediately | Explorer open | Step 4 | same — the chooser is awaited with no intervening wait | asserted (folded) |
| 5 | Select `sample1.txt` | File selected | Step 4 | `set_files()` inside the chooser | asserted (folded) |
| 6 | Click Open | Upload modal opens | Steps 4–5 | `wait_for_upload_path_dialog()` | asserted |
| 7 | Modal open, Path pre-filled | Modal open with path pre-filled | Step 5 | prefix contains `{bucket}/`, typed value empty, description text equals live wording | asserted |
| 8 | Click Cancel | Modal closes | Step 7 | click on `artifacts-upload-path-cancel-button` (**testid needed**) | asserted |
| 9 | Verify modal closed | Modal not visible | Step 8 | `wait_for(state="hidden")` + zero captured requests | asserted (strengthened) |
| 10 | Verify file NOT in the table | No new file appeared | Step 9 | `file_exists(...) is False`, names + pagination equal baseline, re-verified after reload | asserted (strengthened) |
| 11 | Verify no success notification | No success notification | Step 10 | `to_have_count(0)` on `toast-message` | asserted |
| F | Expected final state: table unchanged | — | Step 9 (incl. reload) | names + pagination counter | asserted |

*Case step 10 names `sample.txt` while Test Data and step 5 name `sample1.txt` — an
internal typo in the case text; the assertion uses the file actually selected,
`sample1.txt` (§ Findings).*

### Axis 2 — Analyst additions
| # | Observable | Why grounded |
|---|---|---|
| A2-1 | **Zero `artifacts` network requests** between the Cancel click and the modal closing | "Discards" must mean *never uploaded*, not *uploaded then hidden*. Absence of a row in the table can also be a stale-listing artifact; zero requests cannot. Same technique already sanctioned in ELITEA-1832 step 11. |
| A2-2 | File list re-read **after a page reload** | Makes the server the oracle for "not uploaded" instead of a client list the cancel path never refreshed. |
| A2-3 | Re-opened dialog's Path field is empty after typing `probe-folder` and cancelling | The case title says the selection is *discarded*. Source (`UploadPathDialog.jsx` `handleCancel` = `setFolderPath('') ; onClose()`) says the dialog's own state resets; confirmed live (`REOPEN typed=''`). Catches a regression where Cancel only hides the modal and leaves a stale pending path/selection. |
| A2-4 | No console errors across the flow | Project side-channel discipline; live run produced none. |

## Fidelity Declaration
| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket + its pre-existing `seed.txt` created via `ArtifactAPI` rather than through the UI | **Transit only** | The case's preconditions state the bucket and its contents already exist — creation is not a case step (identical precedent: ELITEA-1826/1832). Every observable the case asks for (modal behaviour, absence of the upload, absence of the toast, unchanged table) is produced by the live product through the real UI upload flow. |

No response fabrication, no injected state, no `page.route`/`evaluate` on any asserted
value. The file chooser is driven through Playwright's real `expect_file_chooser` (the
same mechanism every existing upload spec uses) — the browser's native OS dialog is not
rendered, which is a framework property of file inputs, not a substitution of the system
under test.

## Blocked Steps
None — all 11 steps executed live.

## Findings
1. **testid gap (implementer work)** — `artifacts-upload-path-cancel-button` must be added
   to `UploadPathDialog.jsx` before this case can be automated per the locator policy. See
   § Concrete Handles.
2. **Case-text typo (clarification, no product impact)** — case step 10 says
   `"sample.txt"` while the Test Data table and step 5 say `"sample1.txt"`. Intent is
   unambiguous (the file selected in step 5); the AFS asserts the selected file's absence.
   Not filed as a tracker issue — no behavioural ambiguity, and the AFS records the
   resolution. Reported to the lead in the run's findings.
3. **`get_total_file_count_from_pagination()` is raw-CSS tech debt** — it locates
   `main *:has-text("of "):not(:has(*))`. A testid-backed replacement now exists
   (`get_pagination_info_text()` on `artifacts-pagination-page-info`); this case should use
   the testid-backed one. Not a defect, a suite-hygiene note (tracked debt #25/#42).

## Live-execution evidence (2026-08-21, localhost:5173, project Private)

Scripted probe driving `ArtifactsPage` (Playwright sync API via pytest, HEADLESS=true);
one run, all output below is verbatim:

```
BUCKET=autotest-test-scratch-1825-693656 URL=.../artifacts?bucket=autotest-test-scratch-1825-693656
BASELINE names=['seed.txt'] count=1
STEP7 prefix='Path​autotest-test-scratch-1825-693656/​' typed='' desc='Files will be uploaded to the selected bucket. Optionally, enter a folder path to organize your files. Use "/" to create nested folder(s).'
DIALOG TITLE=['Upload files to ...']
DIALOG BUTTONS=[('', None), ('Cancel', None), ('Upload', 'artifacts-upload-path-upload-button')]
TYPED-BEFORE-CANCEL='probe-folder'
STEP9 dialog_hidden=True requests_during_cancel=[]
STEP10 after_names=['seed.txt'] count=1 sample1_exists=False
STEP11 toast_count=0 toast_text=None
AFTER-RELOAD names=['seed.txt']
REOPEN typed='' prefix='Path​autotest-test-scratch-1825-693656/​'
CONSOLE_ERRORS=[]
```

(The `('', None)` first button is the modal's unlabelled close/X control — not used by this
case; no testid needed for it here.)
