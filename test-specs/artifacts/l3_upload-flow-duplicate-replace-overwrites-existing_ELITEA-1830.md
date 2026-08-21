# Test Case: Upload Flow – Duplicate Handling: Replace Overwrites Existing File

## Metadata
- **TMS ID**: ELITEA-1830
- **Linked Story**: none
- **Priority**: l3 (medium — as authored in the source TMS case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot (cluster session with ELITEA-1833, 2026-08-21)
- **Status**: ready-for-automation — all 13 case steps executed end-to-end live
  (2 independent runs, identical results), no defects found. Not already-covered,
  not extend-existing — see § Overlap check.

## Overlap check vs existing automation

Read before executing (grep by behaviour, not case id):
`automation/tests/ui/artifacts/test_artifacts_upload_duplicate_{detected_modal,skip,keep_both,cancel}.py`
(ELITEA-1828 / 1829 / 1831 / 1832) and `automation/pages/artifacts_page.py`.

- **ELITEA-1828** (`test_artifacts_upload_duplicate_detected_modal.py`) asserts the
  modal *appears* and its four buttons are visible — Replace is **visibility-only,
  never clicked**. The digest row for `artifacts-resolve-duplicates-replace-button`
  says so explicitly: *"Not yet exercised by any case … next case to click it should
  confirm its actual overwrite semantics live"*. This is that case.
- **ELITEA-1831** (Keep both) ends with **two** files and the original's
  `lastModified` explicitly asserted **unchanged** — the exact inverse of this case's
  observable.
- **ELITEA-1829** (Skip) fires **zero** PUTs for the duplicate; **ELITEA-1832**
  (Cancel) fires zero requests at all.

No merged spec anywhere clicks Replace or asserts an overwrite. Verdict: **zero
behavioural overlap**, `ready-for-automation` (fresh spec). It does, however, share
the entire setup/navigation/upload-trigger prefix with the four specs above — the
implementer reuses those page-object methods verbatim and diverges only at the
button click and the assertion chain.

## Preconditions
- User is logged in (on localhost, `auth_state` skips login).
- A bucket exists containing `sample.txt`. **No stable `bucket-1` fixture exists** —
  the case's named `bucket-1` is illustrative. Use the `artifact_bucket` fixture
  (fresh per test) and seed `sample.txt` into it via `artifact_api.upload_file(...)`,
  exactly as ELITEA-1831/1832 already do. Seeding via API is **transit only**
  (reaching the precondition); every asserted observable in this case is produced by
  the product.
- A local file named `sample.txt` is available for upload — write it into pytest's
  `tmp_path` (project convention; no checked-in upload fixtures exist).

## Test Data

### generate-per-test (created in setup, removed by the `artifact_bucket` teardown)
| Field | Value | Notes |
|---|---|---|
| Bucket | `artifact_bucket` fixture (`autotest-*`) | fresh per test; case's `bucket-1` is illustrative only |
| Existing file | `sample.txt`, content `ORIGINAL …` (32–68 B) | seeded via `artifact_api.upload_file`, `content_type="text/plain"` |
| Uploaded file | `sample.txt` (SAME name), **different content and different byte length** | the differing length makes the overwrite observable in the UI's own **Size** cell as well as via the API |

**Deliberate data choice:** the case does not specify the replacement file's content.
Give it a *different byte length* from the seed. That turns "the file was overwritten"
into a system-produced, UI-visible observable (`32 B` → `58 B`, confirmed live) instead
of resting on the timestamp alone.

## Test Steps

Live-confirmed behaviour; step numbers map to the TMS case.

| # | Action | Expected (confirmed live) |
|---|---|---|
| 1 | Navigate to Artifacts (`ArtifactsPage.navigate_to_artifacts()`) | Artifacts page loads |
| 2 | Open the seeded bucket (`navigate_to_bucket(bucket_name)`) | Bucket selected; `sample.txt` row visible (`file_exists` → `True`) |
| 3 | Note the current **Last update** value of `sample.txt` | Column IS rendered and readable — live value e.g. `21-08-2026, 08:40 PM`. Also capture `artifact_api.get_file_metadata(...)["lastModified"]` (UTC, e.g. `2026-08-21T17:40:37.000Z`) as the deterministic baseline — see the granularity caveat below |
| 4–6 | Click the upload icon, choose `sample.txt`, confirm (`upload_files([path])`) | Native chooser opens and resolves in one Playwright action (`expect_file_chooser` wraps the click — no observable exists between "click" and "files chosen"); the "Upload files to …" modal opens |
| 7 | Verify the modal's Path prefix | `get_upload_path_prefix_text()` contains the bucket name. Raw text is `'Path​{bucket}/​'` (MUI zero-width spaces) — prefer `get_upload_path_normalized_prefix()` for an exact `f"{bucket}/"` equality |
| 8 | Click **Upload** (`click_upload_path_upload_button()`) | Duplicate detection triggers **client-side** — capture on `"artifacts"` across the click returned `[]` (0 requests), 2/2 runs |
| 9 | Verify the "Resolve duplicates" modal lists `sample.txt` | `get_resolve_duplicates_filenames()` → `['sample.txt']`; message text (singular, 1 duplicate) = `This file already exists in this bucket. Choose how to handle duplicates.` |
| 10 | Click **Replace** | Modal closes. Exactly **one** `PUT` fires, to the **same key**: `/artifacts/s3/{bucket}/sample.txt?project_id=399`, followed by a `GET …?format=json` bucket refetch |
| 11 | Verify the success notification | `success_toast_message` count 1, exact text `Your file(s) have been successfully uploaded!` |
| 12 | Verify only one `sample.txt` entry exists | `artifacts-file-row` count = 1; `artifact_api.list_bucket_files(bucket)` → `['sample.txt']` (len 1); pagination total = 1 |
| 13 | Verify the **Last update** timestamp has been updated | API `lastModified` strictly newer (`17:40:37Z` → `17:41:10Z`); UI cell moved `08:40 PM` → `08:41 PM`; Size cell moved `32 B` → `58 B`; file content byte-equal to the replacement bytes |

### ⚠ Step-13 granularity caveat — read before writing the assertion

The **Last update** column renders with `format(lastModified, 'dd-MM-yyyy, hh:mm a')`
(`EliteaUI/src/pages/Artifacts/component/ArtifactTable.jsx:50`) — **minute** granularity,
in **local** time (UTC `17:41:10Z` displayed as `08:41 PM` at UTC+3). The full flow takes
~30–40 s, so in both analyst runs the seed and the replace landed in different minutes and
the displayed string did change — **but that is luck, not a guarantee**. A run that starts
mid-minute can seed and replace inside the same minute and render an *identical* string.

Do **not** assert `ui_cell_after != ui_cell_before` — it is a latent flake. Assert instead:

1. **Primary (deterministic, the case's actual claim):**
   `api_after["lastModified"] > api_before["lastModified"]` — strictly newer, from the
   product's own metadata endpoint.
2. **UI carries it through faithfully:** the rendered cell equals the API's `lastModified`
   formatted as `dd-MM-yyyy, hh:mm a` in local time. The API response is the oracle; the
   test writes no expected timestamp of its own.
3. **Supporting overwrite proof (never ambiguous):** the Size cell and
   `api_after["size"] != api_before["size"]`, plus `artifact_api.get_file(...)` equal to the
   replacement bytes.

## Expected Results
- Replace overwrites in place: exactly one `sample.txt` remains, no `- Copy` variant, no
  second row.
- Exactly one PUT, to the original key — no delete-then-create, no second key.
- Success toast with the exact wording above.
- `lastModified` strictly newer; content and size are the replacement's.
- Zero console errors across the whole flow (confirmed live, 2/2 runs).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains `sample.txt` with a known timestamp | present | API seed + `file_exists` + baseline `get_file_metadata` | Setup / Step 2 | covered |
| Precondition: local `sample.txt` available | present | `tmp_path` write | Setup | covered |
| Step 1 navigate | Artifacts loads | `navigate_to_artifacts()` | Step 1 | covered |
| Step 2 select bucket | bucket selected | `navigate_to_bucket()` + `file_exists` | Step 2 | covered |
| Step 3 note timestamp | recorded | UI cell read + API `lastModified` baseline | Step 3 | covered |
| Step 4 click upload icon | chooser opens | `upload_files()` (`expect_file_chooser`) | Steps 4–6 | covered (folded — no observable between click and chooser) |
| Step 5 chooser opens immediately | open | same action; a failure raises a chooser timeout | Steps 4–6 | covered (folded) |
| Step 6 select + Open | upload modal opens | `wait_for_upload_path_dialog()` | Steps 4–6 | covered |
| Step 7 Path pre-filled with bucket | modal open, prefixed | `get_upload_path_normalized_prefix() == f"{bucket}/"` | Step 7 | covered |
| Step 8 click Upload | detection triggered | `click_upload_path_upload_button()` | Step 8 | covered |
| Step 9 modal lists `sample.txt` | duplicate shown | `get_resolve_duplicates_filenames() == ['sample.txt']` | Step 9 | covered |
| Step 10 click Replace | action completes | `click_resolve_duplicates_replace_button()` (**new PO method**) + `wait_for_resolve_duplicates_dialog_closed()` | Step 10 | covered |
| Step 11 success notification | exact text | `expect(success_toast_message).to_have_text(...)` | Step 11 | covered |
| Step 12 exactly one `sample.txt` row | 1 row | row count + API listing len 1 | Step 12 | covered |
| Step 13 timestamp updated | newer | API delta + UI-cell equality (see caveat) | Step 13 | covered |
| Final state: original replaced by the new upload | one entry, updated | content + size + timestamp assertions | Step 13 | covered |

### Axis 2 — Observables asserted beyond the case
| Observable | Why (grounded) |
|---|---|
| Duplicate detection fires **0** network requests | Confirmed live 2/2; the same client-side-diff invariant ELITEA-1829/1831/1832 already assert — keeps the family consistent and catches a regression to server-side detection |
| Exactly **one** PUT, to the **original key**, none to any `- Copy` key | Distinguishes a true overwrite from Keep-both-style renaming; the case's "only one entry" is otherwise satisfiable by a UI that hides a second object |
| Replaced **content** is byte-equal to the uploaded bytes | "Replace" means the *bytes* changed; a metadata-only touch would pass a timestamp-only check |
| **Size** cell / API `size` changed | Second, granularity-immune overwrite proof (immune to the minute-rounding caveat) |
| No console errors | Project standard side-channel check |

## Cleanup
- `artifact_bucket` fixture teardown deletes the bucket. **Known: the delete 404s
  silently** (issue `#636`, wrapped in try/except; `autotest-*` buckets accumulate in
  project `Private`). Not this case's problem; do not add a workaround.
- No other residue: files live only inside the per-test bucket.

## Concrete Handles (discovered during exploration)

**PROVENANCE column verified 2026-08-21 after `cd ../EliteaUI && git fetch origin`.**

| Element | Handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Artifacts nav / bucket list / file list | existing `ArtifactsPage` methods | on-main ✓ | `navigate_to_artifacts`, `navigate_to_bucket`, `file_exists` |
| Upload icon | `artifacts-upload-files-button` (via `upload_files()`) | on-main ✓ | wraps `expect_file_chooser` |
| Upload-path dialog | `artifacts-upload-path-dialog` | on-main ✓ | `wait_for_upload_path_dialog()` |
| Upload-path Path field | `artifacts-upload-path-input` | on-main ✓ | read via `get_upload_path_normalized_prefix()` — never raw `text_content()` equality (zero-width spaces) |
| Upload-path **Upload** button | `artifacts-upload-path-upload-button` | on-main ✓ | `click_upload_path_upload_button()` |
| Resolve-duplicates dialog | `artifacts-resolve-duplicates-dialog` | on-`automation/testids` only (EliteaAI/EliteaUI@918b8b22) | human cherry-pick to `main` pending |
| Duplicate filename row | `artifacts-resolve-duplicates-filename` | on-`automation/testids` only (@918b8b22) | `get_resolve_duplicates_filenames()` |
| Dialog message text | `artifacts-resolve-duplicates-message-text` | on-`automation/testids` only (@918b8b22) | singular wording for exactly 1 duplicate |
| **Replace** button | `artifacts-resolve-duplicates-replace-button` | on-`automation/testids` only (@918b8b22) | **SHIPPED**: `click_resolve_duplicates_replace_button()` was added to `ArtifactsPage`, mirroring `click_resolve_duplicates_keep_both_button()`, over the pre-existing `resolve_duplicates_replace_button` descriptor. No new testid was needed |
| File row | `artifacts-file-row` | on-main ✓ | `ArtifactTable.jsx:526`. Count it with an auto-waiting assertion — a bare `.count()` immediately after navigation read `0` while the list was still hydrating (observed live) |
| File row **Last update** value | `ArtifactsPage.get_file_row_text(filename)` + regex (**established merged pattern — do NOT add a new handle**) | on-main ✓ | The cell has **no per-cell testid** — `ArtifactTable.jsx` renders data cells through the shared generic `GridTableRowDataCell`. The project already settled this: `get_file_row_text` (`artifacts_page.py:1848`) reads the whole row's text off the existing testid-anchored row locator, and the merged `test_artifacts_file_preview_edit_save.py:71-97` parses the timestamp out of it with `LAST_UPDATE_TIMESTAMP_RE = r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} [AP]M"` + `"%d-%m-%Y, %I:%M %p"`. **Reuse that helper's shape verbatim** — it is testid-compliant (no new selector) and reviewed. |
| File-table column headers | `artifacts-file-table-column-header-{field}` (`modified` = "Last update") | on-`automation/testids` (per `_surface.md` L125) | field key is `modified`, NOT `lastUpdate`. Only needed if the spec asserts the header itself |
| Success toast | `artifacts-success-toast-message` (`success_toast_message`) | on-main ✓ | exact-text assertion |
| Bucket listing / metadata / content | `artifact_api.list_bucket_files` / `get_file_metadata` / `get_file` | n/a (API) | server-side oracle |

**Scope note — this case needs NO new testid.** Every element it touches already carries one, and the single un-tagged value (the Last-update cell) has a merged, reviewed, testid-compliant read path (above). Adding `dataCellTestIdPrefix` to `ArtifactTable` was considered and **rejected**: the prop is a single prefix that would tag all four data cells at once, three of which this test never touches — a blanket add, against `.agents/testing.md` § Locator policy ("testids go ONLY on elements tests actually touch"). The only page-object addition required is `click_resolve_duplicates_replace_button()` over the **already-existing** `resolve_duplicates_replace_button` descriptor.

**Viewport (load-bearing for steps 3/13).** The `modified` column is width-gated (`hideBelow: 900` on the table's own width, `ArtifactTable.jsx:63`). It rendered fine at the framework default 1366x768 in the analyst run, but the merged `test_artifacts_upload_path_cancel.py:86-88,153` documents clipping below ~1600 px and sets `page.set_viewport_size({"width": 1600, "height": 900})`. **Follow that merged pattern** — don't rely on the default being wide enough.

### Implementation note — how steps 3 / 13 read the "Last update" cell (SHIPPED)

The caveat's three assertions ship exactly as written. Two mechanics worth recording,
both decided at implementation time:

- The spec parses the cell with the merged `LAST_UPDATE_TIMESTAMP_RE` regex shape from
  `test_artifacts_file_preview_edit_save.py`, but keeps the matched **string** rather than
  a parsed `datetime`, and compares it for **equality** against the API's own
  `lastModified` rendered through `dd-MM-yyyy, hh:mm a` in local time. That is caveat
  point 2 ("the API response is the oracle") in its most direct form — the test writes no
  expected timestamp of its own, in either direction.
- Reading the row's text with a single-shot `get_file_row_text()` immediately after the
  Replace PUT **races the table refetch**. A new additive page-object helper,
  `ArtifactsPage.wait_for_file_row_to_contain_text()`, wraps Playwright's auto-retrying
  `expect(...).to_contain_text()` over the same testid-anchored `ARTIFACT_FILE_ROW` class
  constant (no new selector, no sleep) and is awaited before the row is read.

## Network Behavior
| Moment | Requests (confirmed live, 2/2 runs) |
|---|---|
| Upload click → duplicate modal | **none** (client-side diff against the already-fetched listing) |
| Replace click | `PUT /artifacts/s3/{bucket}/sample.txt?project_id=399` (exactly 1), then `GET /artifacts/s3/{bucket}?project_id=399&format=json`, then `GET /artifacts/s3/?project_id=399&format=json` |
| After close | no further traffic |

## Known Defects
None. All 13 steps behaved as the case describes.

## Blocked Steps
None.

## Automation Hints
- **Fidelity:** every asserted value is produced by the product (UI cells, toast text,
  network trace, API metadata/content). The only substitution is the **API seed of the
  precondition file** — transit only, declared; the case's own observable (what Replace
  does) is entirely system-produced. No `route.fulfill`, no `page.evaluate`, no injected state.
- Markers: `ui`, `regression`, `p2` (matching ELITEA-1831/1832 in this family).
- Suggested file: `automation/tests/ui/artifacts/test_artifacts_upload_duplicate_replace.py`;
  class `TestArtifactUploadDuplicateReplace`.
- Wrap each step in `with allure.step("Step N — …")` (project mandatory).
- Reuse `capture_requests_matching("artifacts", method="PUT")` (`base_page.py:366`) — start
  the capture **before** the Replace click, as ELITEA-1831 does.
- **Reuse, don't re-derive:** `_extract_last_update_timestamp()` +
  `LAST_UPDATE_TIMESTAMP_RE` in `test_artifacts_file_preview_edit_save.py:71-97` already parse
  this exact cell (that spec asserts the same "timestamp advances after a write" observable for
  the *preview-edit-save* flow — a different trigger, so no coverage overlap with this case, but
  directly reusable machinery).
- Timing baseline: the analyst's full live run of this flow (seed → nav → upload → replace →
  reload → verify) took **~55 s** headless.
