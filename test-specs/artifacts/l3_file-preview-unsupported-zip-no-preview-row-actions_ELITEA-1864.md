# Test Case: File Preview/Edit – Unsupported File Type (.zip) Has No Preview and Only Download/Delete in Actions

## Metadata
- **TMS ID**: ELITEA-1864
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1863/ELITEA-1864, 2026-08-23)
- **Status**: ready-for-automation
- **Cluster note**: analysed in ONE live session with ELITEA-1863 (shared bucket seeding,
  shared discovery) but written as a **separate AFS** — this case never opens the preview
  panel; it asserts the *row-level* contract (no preview icon, exactly two menu items, a
  working download). Different STEPS, not different data.

## Preconditions
- User is logged in to the Elitea platform (`auth_state`, localhost).
- A bucket contains `new-file-storage.zip`. The case names "bucket-1"; **no such shared
  fixture bucket exists in this suite** — the test seeds its own (§ Test Data), same
  discipline as every merged artifacts spec.

## Test Data
### generate-per-test (fresh bucket via the `artifact_bucket` fixture, API-seeded)
- `new-file-storage.zip` uploaded via `ArtifactAPI.upload_file(bucket, name, bytes,
  content_type="application/zip")`.
- **Seed exactly 235_520 bytes** (`b"PK\x03\x04" + padding`) so the row's size cell reads
  the case's literal `230.0 KB`: `formatFileSize` is base-1024 with one decimal
  (`src/utils/filePreview.js:719`), and 235520 / 1024 == 230.0 exactly. A real archive is
  not required — the preview gate is a filename-extension whitelist (`canPreviewFile`;
  `zip` is absent from `PREVIEWABLE_EXTENSIONS`), never a content sniff.

## Test Steps

> ⚠ Steps 3/5 phrase the row controls as appearing "on hover". Neither the preview icon
> nor the 3-dot trigger is hover-gated in the current product (already filed for this
> surface as **#994**). This AFS asserts the stronger, hover-independent contract and
> additionally re-checks after a hover, so it holds either way.

1. Navigate to Artifacts and open the fixture bucket
   (`ArtifactsPage.navigate_to_bucket(bucket)`)
   - **Verify**: the file table shows `new-file-storage.zip`
2. Verify the row's metadata cells (`get_file_row_text()`)
   - **Verify**: the row text contains `ZIP Archive` (type mapping, `fileTypes.js:127`)
     and `230.0 KB` (formatted size of the seeded payload)
3. Observe the row **without hovering**, then hover it (`hover_file_row`)
   - **Verify**: `artifacts-file-preview-button-new-file-storage.zip` resolves to
     **0 matches** in both states — no "View/Edit file" icon for an unsupported type
   - **Verify**: the 3-dot trigger `artifact-actions-{row.id}-menu-button` IS visible
     (before the hover too — not hover-gated, #994)
4. Click the 3-dot actions icon (`open_file_actions_menu("new-file-storage.zip")`)
   - **Verify**: the dropdown renders
5. Verify the dropdown's items
   - **Verify**: `get_file_actions_menu_item_labels("new-file-storage.zip")` ==
     `["Download", "Delete"]` — exactly two, in that order; **no** preview / view-edit /
     Copy Content item
6. Click **Download** in the dropdown
   - **Verify**: a download starts, `download.suggested_filename == "new-file-storage.zip"`,
     and the downloaded bytes equal the seeded 235_520-byte payload
   - **Verify**: **no** ZIP-packaging progress dialog appears —
     `artifacts-zip-download-progress-dialog` count == 0 (a single-file download streams
     the file itself; the "Preparing {bucket}.zip" dialog belongs to the multi-select flow,
     ELITEA-1839/1840)
7. Verify no console errors were emitted across the whole flow

## Expected Results
- The `.zip` row shows only the 3-dot actions control — never a "View/Edit file" icon.
- Its dropdown offers exactly `Download` and `Delete`.
- Download delivers the original archive byte-for-byte, with no ZIP-packaging dialog.
- No console errors.

## Fidelity Declaration
No substitution of any kind: every observable (row cells, control presence, menu labels,
downloaded bytes) is produced by the live product, reached through ordinary UI gestures.
No `route.fulfill` / `page.evaluate` / `monkeypatch` / mocked client anywhere.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains `new-file-storage.zip` (ZIP Archive, 230.0 KB) | file present with that type/size | steps 1–2 | `file_exists()` + `get_file_row_text()` contains `ZIP Archive` / `230.0 KB` | asserted *(fixture bucket, not the literal "bucket-1" — payload sized so the case's literal `230.0 KB` holds exactly)* |
| 1 Navigate to Artifacts, click "bucket-1" | bucket selected | step 1 | `navigate_to_bucket` + file table visible | asserted *(fixture-generated bucket)* |
| 2 Verify the file is listed (ZIP Archive, 230.0 KB) | file visible | step 2 | row text assertion | asserted |
| 3 Hover the row → only the 3-dot icon appears, no View/Edit icon | only actions icon | step 3 | preview-button testid count 0 **before and after** hover; dot-menu trigger visible | asserted *(hover framing corrected per #994 — checked hover-independently, which is strictly stronger)* |
| 4 Verify the View/Edit icon is NOT present | icon absent | step 3 | same count-0 assertion | asserted |
| 5 Verify only the 3-dot actions icon is available on hover | only actions icon | step 3 | same pair of assertions | asserted *(decomposed with step 3 — same two observables)* |
| 6 Click the 3-dot actions icon | dropdown appears | step 4 | `open_file_actions_menu` waits on the rendered menu | asserted |
| 7 Dropdown contains only Download and Delete | exactly those two | step 5 | `get_file_actions_menu_item_labels() == ["Download", "Delete"]` (exact list equality — catches an added item, which a per-item `is_visible` sweep would not) | asserted |
| 8 Click Download → the ZIP downloads | download starts | step 6 | `expect_download()`, filename + byte equality | asserted |
| Expected Final State (composite) | no preview icon, 2-item menu, successful download | steps 3–6 | combination of the above | asserted |

### Axis 2 — Analyst additions

| Addition | Why |
|---|---|
| Downloaded **bytes** equal the seeded payload — step 6 | A download event proves the click wired up; byte equality proves the right file arrived. The payload is a known constant, so this is exact and deterministic. |
| "No ZIP-packaging progress dialog" — step 6 | Single-file download and multi-select ZIP download share the same visible verb ("Download"); this guards against the row action ever being re-routed through `startZipDownload`. Same defensive shape already merged for ELITEA-1839. |
| Dot-menu trigger asserted visible **before** any hover — step 3 | The case's "appears on hover" phrasing can only be satisfied by an assertion that distinguishes always-visible from hover-revealed; asserting pre-hover is what would actually catch a future hover-gating regression (#994's lesson, applied on ELITEA-1862 too). |
| Console-error check — step 7 | Suite standard. |

## Cleanup
- `artifact_bucket` fixture teardown deletes the bucket (known `#636` 404 on teardown —
  benign). Nothing in this case mutates the file.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance (verified 2026-08-23 after `git fetch origin`) | Notes |
|---|---|---|---|
| File row | `artifacts-file-row` (`ARTIFACT_FILE_ROW`) | on `main` ✓ (`ArtifactTable.jsx:525`) | existing, reuse (`file_exists`, `get_file_row_text`) |
| "View/Edit file" icon (dynamic) | `artifacts-file-preview-button-{filename}` (`ARTIFACT_FILE_PREVIEW_BUTTON`) | on `main` ✓ (`ArtifactRowActions.jsx:83`) | existing; count-0 absence assertion only |
| Row 3-dot trigger (dynamic) | `artifact-actions-{row.id}-menu-button` (`ARTIFACT_ACTIONS_MENU_BUTTON`) | on `main` ✓ (DotMenu's `${id}-menu-button` convention) | existing, reuse (`open_file_actions_menu`) |
| Row actions menu + items | `artifact-actions-{}-menu` + `ROW_ACTIONS_MENU_ITEM_SELECTOR` | on `main` ✓ | existing, reuse (`get_file_actions_menu_item_labels`) |
| Download menu item | `download_menu_item` descriptor | on `main` ✓ | existing, reuse (`download_file` captures the Download event end-to-end) |
| ZIP progress dialog (absence) | `artifacts-zip-download-progress-dialog` | on `automation/testids` ✓, `main` pending human cherry-pick (added ELITEA-1839) | existing; count-0 absence assertion |

**No new testids are required for this case** — every handle already exists and was
exercised live this session.

## Network Behavior
- The dropdown's Download issues the artifact download request directly (no ZIP
  packaging, no `startZipDownload`) — confirmed live: 320-byte probe file arrived intact,
  no progress dialog.
- No console errors observed (live, 2026-08-23).

## Known Defects Found During Exploration
- None. The case text matches the product except for the "on hover" phrasing already
  tracked by **#994**; no new clarification filed (sibling occurrence, same misconception,
  same surface). Live evidence for the deep-linked .zip panel (out of this case's scope,
  captured while analysing ELITEA-1863):
  `test-results/screenshots/ELITEA-1864-zip-deeplink.png` /
  https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1864-deeplink-preview-not-available-zip.png

## Blocked Steps
- None.

## Automation Hints
- Suggested spec:
  `automation/tests/ui/artifacts/test_artifacts_file_preview_unsupported_zip_row_actions.py`.
- Everything needed already exists on `ArtifactsPage`: `navigate_to_bucket`,
  `file_exists`, `get_file_row_text`, `hover_file_row`, `is_file_preview_button_visible`,
  `open_file_actions_menu`, `get_file_actions_menu_item_labels`, `download_file`.
  Prefer `expect(locator).to_have_count(0)` (web-first, auto-retrying) over
  `is_file_preview_button_visible() is False` for the absence assertions, so a slow
  render can never produce a false pass.
- Markers: `ui`, `regression`, `p2`, `artifacts`. Wrap every step in `allure.step("Step N — …")`.
