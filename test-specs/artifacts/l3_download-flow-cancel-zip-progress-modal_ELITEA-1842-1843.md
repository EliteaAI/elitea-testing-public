# Test Case (FAMILY): Download Flow – Cancelling an in-progress ZIP preparation from the progress modal

## Metadata
- **TMS IDs (family members)**: **ELITEA-1842** (Cancel button) · **ELITEA-1843** (X close button)
- **Family AFS**: yes — the two cases are flow-variants of ONE flow (abort an in-flight ZIP
  preparation from the `artifacts-zip-download-progress-dialog`), differing only in **which control
  is clicked**. Confirmed in source: `ZipDownloadProgressDialog.jsx` passes the SAME `onCancel`
  handler to both `BaseModal`'s `onClose` (X / backdrop / Escape) and the Cancel button's `onClick`
  — the identical shape ELITEA-1832/1833 already established for the Resolve-duplicates dialog.
  Both members share this AFS path and become ONE parameterized spec (a row per case).
- **Priority**: l3 (medium — as authored in both source TMS cases)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` →
  DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399). `../EliteaUI` freshly
  `git fetch origin`'d this run; every handle's provenance recorded in § Concrete Handles.
- **User set**: `${TEST_USER}` (on localhost, `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer, combined analyst+implementer slot (batch `artifacts-w03`)
- **Status**: **ready-for-automation** (fresh parameterized spec — NOT an extension of
  `test_artifacts_download_multiple_files_zip.py` / `..._select_all_zip.py`, both of which
  explicitly scope the Cancel flow OUT: "Cancel button: present, labelled 'Cancel'
  (visibility-only — never clicked, out of this case's scope)", ELITEA-1840/1841 AFS).
  Both members executed live end-to-end this session against a freshly seeded bucket.

---

## Preconditions

- Logged in to Elitea (localhost: `auth_state`, no login step).
- A bucket containing a subfolder `a1` with **at least 4 files** (the source cases name
  `bucket-1` / `a1`; automation seeds its own bucket via `artifact_bucket` + `ArtifactAPI.upload_file`,
  the established precedent of every merged download spec — the case's own observable is
  produced entirely by the product).

## Test Data

| Field | ELITEA-1842 | ELITEA-1843 |
|---|---|---|
| Bucket | fresh `artifact_bucket` fixture bucket | same |
| Subfolder | `a1` | `a1` |
| Files seeded under `a1/` | `Q&A.docx.odt`, `Regression test cases.odt`, `sharepoint.docx`, `sample_640x426.gif` (4) | same 4 |
| Files selected | **4** (all — the case's own 4-file data set, "1 of 4 files" in step 6) | **3** (the case's own "3 or more") |
| Control clicked mid-flight | `Cancel` button | `X` (close) icon in the modal header |
| Expected counter at click | `1 of 4 files` (`aria-valuenow="25"`) | `1 of 3 files` (`aria-valuenow="33"`) |
| Cancellation notification | `Download cancelled` | `Download cancelled` |

---

## Live execution evidence (this session, 2026-08-21)

Both members were driven live via Playwright MCP against `localhost:5173`, with the ZIP flow's
per-file GETs slowed by an in-page `window.fetch` wrapper (**exploration instrumentation only** —
the shipped spec uses `page.route()` + a delayed `route.continue_()`, the same timing-control
technique ELITEA-1840/1841 already ship; see § Fidelity Declaration).

**ELITEA-1842 (Cancel button), 4 files selected:**

```
frames        : "0 of 4 files" (valuenow 0, no current-file label) x N
                → "1 of 4 files" (valuenow 25, "Current: a1/sample_640x426.gif")
title         : "Preparing autotest-analysis-1842-1843.zip"
cancel clicked at: "1 of 4 files"
after cancel  : dialogPresent=false, toast-message="Download cancelled" (first seen ~2.0 s
                after the click, inflated by the 1500 ms instrumentation delay),
                zipAnchorClicks=[]  (NO ZIP save attempted),
                checkedCount=4 / rowCount=4  (table + selection unchanged)
console errors: 0
```

**ELITEA-1843 (X close button), 3 files selected:**

```
X control     : <button aria-label="Close" data-testid="artifacts-zip-download-progress-close-button">
                visible=true during progress
clicked at    : "1 of 3 files" (valuenow 33, "Current: a1/sample_640x426.gif")
after click   : dialogPresent=false, toast-message="Download cancelled" (~2.1 s, same
                instrumentation inflation), zipAnchorClicks=[],
                checkedCount=3 / rowCount=4
console errors: 0
```

`zipAnchorClicks` is an in-page instrumentation of `HTMLAnchorElement.prototype.click` capturing
any `download`-attributed anchor — the exact mechanism `downloadArtifactsAsZip` uses to save the
ZIP (`anchor.download = "{bucket}.zip"; anchor.click()`). Empty ⇒ no ZIP was ever handed to the
browser. The shipped spec asserts the same fact through Playwright's own `page.on("download")`.

**Product mechanism (source-confirmed, `useZipDownload.hooks.js` + `common/utils.jsx`):**
`cancelZipDownload` aborts an `AbortController` and closes the dialog synchronously; the in-flight
`fetch(..., { signal })` rejects with `AbortError`, which `downloadArtifactsAsZip` maps to
`onCancel()` → `toastInfo('Download cancelled')`. The ZIP is only generated/saved **after** the
loop completes, so an abort mid-loop can never produce a saved ZIP. Selection state lives in
`ArtifactTable`'s own state and is untouched by the cancel path.

---

## Coverage Map

### ELITEA-1842 — Axis 1 (every case element dispositioned)

| Case element | Expected | Where asserted | Evidence | Disposition |
|---|---|---|---|---|
| Precondition: bucket + `a1` with ≥4 large files | — | Test Setup (API seed) | 4 files seeded + listed live | precondition |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | Folded into the direct bucket+folder navigation (same folding precedent as ELITEA-1840/1841) | asserted |
| Step 2: Click bucket, navigate to `a1` | Subfolder selected | Test Step 1 | 4 rows of `a1` listed after navigation | asserted |
| Step 3: Select 3+ files via checkboxes | Selected files checked | Test Step 2 | All 4 row checkboxes read `Mui-checked` | asserted |
| Step 4: Click "Download files" icon | Progress modal opens | Test Step 3 | Dialog appeared with title/bar/counter | asserted |
| Step 5: Verify "Preparing {bucket}.zip" modal + download begins | Modal visible, progress starts | Test Step 3 | Title `Preparing {bucket}.zip`, determinate bar, counter reaching `1 of 4 files` | asserted |
| Step 6: Click "Cancel" while in progress (e.g. "1 of 4 files") | Cancel clicked mid-download | Test Step 4 | Clicked exactly at `1 of 4 files`, `aria-valuenow=25` | asserted |
| Step 7: Progress modal closes immediately | Modal closes | Test Step 5 | `dialogPresent=false` | asserted |
| Step 8: "Download cancelled" notification | Notification appears | Test Step 5 | `toast-message` = `Download cancelled` | asserted |
| Step 9: No ZIP file saved | Download aborted | Test Step 6 | No `page.on("download")` event within the observation window | asserted |
| Step 10: File table intact, all files listed, checkbox states unchanged | Table + checkbox states unchanged | Test Step 7 | 4 rows, same 4 names, all still checked | asserted |
| Step 11: Selected files remain checked | Still checked | Test Step 7 | `checkedCount=4` | asserted |
| Expected Final State / Pass criteria | Composite | Test Steps 4-7 | Combination of the above | asserted |
| Fail criterion: "ZIP saved after Cancel / table state affected" | Negative-space guard | Test Steps 6-7 | No-download assertion + table/selection identity | asserted |

### ELITEA-1843 — Axis 1

| Case element | Expected | Where asserted | Evidence | Disposition |
|---|---|---|---|---|
| Precondition: bucket + `a1` with ≥3 files | — | Test Setup (API seed) | 4 seeded, 3 selected | precondition |
| Step 1: Navigate to Artifacts | Page loads | Test Step 1 | as above | asserted |
| Step 2: Click bucket, navigate to `a1` | Subfolder selected | Test Step 1 | as above | asserted |
| Step 3: Select 3+ files | Files selected | Test Step 2 | 3 checkboxes `Mui-checked` | asserted |
| Step 4: Click "Download files" icon | Progress modal opens | Test Step 3 | Dialog appeared | asserted |
| Step 5: Verify modal + download begins | Modal visible, progress starts | Test Step 3 | Title + counter reaching `1 of 3 files` | asserted |
| Step 6: Click the X (close) icon top-right of the modal | Modal closes | Test Step 4 | Clicked `artifacts-zip-download-progress-close-button` (`aria-label="Close"`) at `1 of 3 files` | asserted |
| Step 7: Modal closes immediately | Modal no longer visible | Test Step 5 | `dialogPresent=false` | asserted |
| Step 8: "Download cancelled" notification | Notification appears | Test Step 5 | `toast-message` = `Download cancelled` | asserted |
| Step 9: No ZIP file saved | No ZIP in downloads | Test Step 6 | No download event | asserted |
| Expected Final State / Pass criteria | Composite | Test Steps 4-6 | Combination of the above | asserted |
| Fail criterion: "ZIP saved after X / notification missing" | Negative-space guard | Test Steps 5-6 | Toast assertion + no-download assertion | asserted |

### Axis 2 — additions beyond the case text (each grounded)

| Addition | Why |
|---|---|
| Assert the counter reached `1 of N files` **with the matching `aria-valuenow`** before clicking | Case step 6 says "while the download is in progress (e.g. at '1 of 4 files')" — this makes "in progress" an observed fact rather than an assumed one, and is the only thing that keeps the test honest (clicking after completion would silently test nothing). |
| Assert the current-file label shows `Current: a1/<file>` at click time | Same reason: independent proof a real per-file transfer was under way. |
| Assert the file **names** (not just the row count) are unchanged after cancel | Case step 10 says "all files listed"; a count-only check would pass on a re-rendered wrong list. |
| Assert 0 console errors across the flow | Suite-wide convention on every artifacts spec; live-confirmed 0 in both runs. |
| ELITEA-1843 also asserts table/selection intact | Free ride on the shared helper; the product path is identical, and it strengthens the X-variant without changing the case's own scope. Reported as an addition, not as case coverage. |

**No `already-covered` / `extend-existing` route:** `test_artifacts_download_multiple_files_zip.py`
(ELITEA-1840) and `test_artifacts_download_all_files_select_all_zip.py` (ELITEA-1841) both assert
the Cancel button's **visibility only** and explicitly declare the cancel FLOW out of scope; neither
spec clicks it, and neither observes the abort, the toast, or the no-ZIP outcome. A fresh spec is
the correct call (and both merged specs stay byte-identical).

---

## Concrete Handles

| Element | Handle | Provenance (verified `git fetch origin` 2026-08-21) | Status |
|---|---|---|---|
| Toolbar "Download files" | `artifacts-download-files-button` | on-main ✓ / on-testids ✓ | existing, reuse |
| Per-row file checkbox | `[data-testid="artifacts-file-checkbox-{name}"]` (class template `ArtifactsPage.ARTIFACT_FILE_CHECKBOX`) | on-main ✓ (`checkboxTestId`) / on-testids ✓ | existing, reuse |
| ZIP progress dialog | `artifacts-zip-download-progress-dialog` | on-main ✓ / on-testids ✓ | existing, reuse |
| Dialog title | `artifacts-zip-download-progress-title` | on-main ✓ / on-testids ✓ | existing, reuse |
| Progress bar | `artifacts-zip-download-progress-bar` | on-main ✓ / on-testids ✓ | existing, reuse |
| File counter | `artifacts-zip-download-progress-counter` | on-main ✓ / on-testids ✓ | existing, reuse |
| Current-file label | `artifacts-zip-download-progress-current-file` | on-main ✓ / on-testids ✓ | existing, reuse (conditionally rendered — absent until the first file is in flight) |
| Dialog **Cancel** button | `artifacts-zip-download-progress-cancel-button` | on-main ✓ / on-testids ✓ | existing, now **clicked** for the first time (ELITEA-1842) |
| Dialog **X (close)** button | `artifacts-zip-download-progress-close-button` | on-main **no** / on-testids ✓ — **added this session**, EliteaAI/EliteaUI@b93c631b | **new** — prop-only add: `closeButtonTestId` passed to the existing `BaseModal` (which already accepts and applies it, `BaseModal.jsx:35,154`). Zero functional impact: no new DOM node, no new hook, no removed line. Same shape as ELITEA-1833's `artifacts-resolve-duplicates-close-button`. |
| Toast / notification | `toast-message` (app-wide `Toast.jsx:74`) | on-main ✓ / on-testids ✓ | existing, reuse |

No raw (non-testid) handles are introduced.

---

## Fidelity Declaration

| Substitution | Transit or terminal | Authority |
|---|---|---|
| `page.route("**/artifact/default/**")` + delayed `route.continue_()` | **Neither — timing control** | `.agents/testing.md` § Fidelity policy: *"Delaying a real response for timing control is NOT substitution."* Every byte still comes from the DEV backend; the delay only widens the window in which the modal is genuinely mid-flight, which is precisely the state both cases require ("while the download is in progress"). Precedent in-repo: `test_artifacts_download_all_files_select_all_zip.py` (ELITEA-1841, merged). |
| Bucket + files seeded via `ArtifactAPI` instead of the UI upload dialog | **Transit** | Both cases carry the files as a **precondition** ("Bucket bucket-1 with subfolder a1 contains at least 4 files"), not as a step. Every observable of both cases (modal, abort, toast, no-ZIP, table/selection state) is produced by the product. Established precedent: ELITEA-1839/1840/1841/1847. |

No fabricated responses, no injected state, no replaced clients. The one in-page `window.fetch`
wrapper used during **exploration** is instrumentation of the analyst session only and is NOT part
of the shipped spec.

---

## Test Steps (the shape the spec implements — parameterized, one row per case)

**Parameters:** `case_id`, `files_selected` (4 / 3), `trigger` (`cancel_button` / `close_x`).

1. **Setup + Step 1** — seed the bucket with the 4 case files under `a1/` (API), navigate directly
   to `?bucket={bucket}&folder=a1`, assert the 4 seeded names are listed and the toolbar download
   button starts disabled.
2. **Step 2** — check the row checkboxes for the row's `files_selected` files; assert exactly those
   read checked and the download button becomes enabled.
3. **Step 3** — click "Download files"; assert the dialog appears with title `Preparing {bucket}.zip`,
   a determinate progress bar (`aria-valuemin=0`/`aria-valuemax=100`), the counter, and BOTH controls
   present (Cancel button + X close button).
4. **Step 4** — poll until the counter reads `1 of {files_selected} files`; assert the matching
   `aria-valuenow` (`25` for 4 files, `33` for 3) and that the current-file label reads
   `Current: a1/<something>`; then click the row's `trigger` control.
5. **Step 5** — assert the dialog is hidden, and a toast reading exactly `Download cancelled` appears.
6. **Step 6** — assert NO download event fired for the whole test (registered before the click).
7. **Step 7** — assert the file table still lists exactly the 4 seeded names and the same
   `files_selected` checkboxes are still checked (ELITEA-1842 steps 10-11; also asserted for
   ELITEA-1843 as a declared Axis-2 addition).
8. **Pass criterion** — 0 console errors across the flow.

---

## Automation Hints

- Framework: Playwright + pytest. **New spec**:
  `automation/tests/ui/artifacts/test_artifacts_download_cancel_zip_progress.py`, class
  `TestArtifactDownloadCancelZipProgress`, one parameterized test
  (`@pytest.mark.parametrize` over the two rows, ids `ELITEA-1842` / `ELITEA-1843`).
- Page-object additions (`automation/pages/artifacts_page.py`, all additive):
  - `zip_download_progress_close_button = LocatorDescriptor(testid="artifacts-zip-download-progress-close-button")`
  - `click_zip_download_cancel_button()` / `click_zip_download_close_button()`
  - `wait_for_zip_progress_at_least(n, timeout)` — polls the counter until it reads `>= n of N files`,
    returning `(current, total, valuenow, current_file)`; the honest replacement for "click at some
    arbitrary moment".
  - Reuse as-is: `navigate_to_bucket_folder`, `get_file_names`, `get_checkbox_states`,
    `click_file_checkbox`, `download_files_button`, all `zip_download_progress_*` handles,
    `success_toast_message`.
- **No-ZIP assertion**: register `page.on("download", …)` **before** clicking Download, and after the
  cancel wait out a fixed observation window (the full remaining route-delay budget, ≥ 4 s) and assert
  the collected list is empty. Do NOT use `expect_download` (it can only prove a download, never its
  absence).
- **Route delay**: 1000-1500 ms per artifact GET is ample — the counter reaches `1 of N` after the
  first file completes, leaving seconds of genuine in-flight time. Keep the route scoped to the
  test's own `page`.
- **Toast timing**: the toast fires from the aborted fetch's rejection, i.e. AFTER the dialog has
  already closed — allow a generous timeout (10 s) and never assert dialog-hidden and toast-visible
  in the same expectation.
- Markers: `ui`, `regression`, `p2` (medium priority — matches l3), `artifacts`.
- Timing baseline (live, instrumented): ~35-45 s per parameterized row including bucket seed.
