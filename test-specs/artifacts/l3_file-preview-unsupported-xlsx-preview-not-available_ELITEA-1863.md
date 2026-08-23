# Test Case: File Preview/Edit – Unsupported File Type (.xlsx) Shows Preview Not Available Message

## Metadata
- **TMS ID**: ELITEA-1863
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1863/ELITEA-1864, 2026-08-23)
- **Status**: ready-for-automation
- **Cluster note**: analysed in ONE live session with ELITEA-1864 (shared bucket seeding,
  shared discovery) but written as a **separate AFS** — the two cases differ in STEPS
  (unsupported-preview *panel* content vs. row-level absence + actions dropdown + download),
  not merely in data (`test-case-analysis` § Execute, family-vs-separate call).

## Preconditions
- User is logged in to the Elitea platform (`auth_state`, localhost).
- A bucket contains `top-5-soccer-players.xlsx`. **Not** a shared literal bucket — the
  suite seeds its own (§ Test Data), same discipline as every merged artifacts spec.

## Test Data
### generate-per-test (fresh bucket via the `artifact_bucket` fixture, API-seeded)
- `top-5-soccer-players.xlsx` uploaded via `ArtifactAPI.upload_file(bucket, name, bytes,
  content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")`.
- **Content is irrelevant to every assertion in this case** — the product's preview gate
  is a *filename-extension whitelist* (`canPreviewFile`, `src/utils/filePreview.js:226`,
  over `PREVIEWABLE_EXTENSIONS`; `xlsx` is absent, `docx` is present), never a content
  sniff. Any non-empty byte payload is sufficient; a real workbook is NOT required
  (confirmed live: a 221-byte stub rendered the full unsupported state and downloaded
  intact). Seed a *stable* payload so the downloaded-bytes assertion is exact.

## Test Steps

> ⚠ **Steps 2–4 of the TMS case do not match the product** — the .xlsx row has **no**
> "View/Edit file" icon, so the preview panel cannot be opened from the file table at
> all. Filed as case-text clarification **#1692**. This AFS specs the LIVE contract
> (asserting the stale text would be reverse-masking). Step 9's "greyed out" is a second
> drift — filed as **#1693**.

1. Navigate to Artifacts and open the fixture bucket
   (`ArtifactsPage.navigate_to_bucket(bucket)`)
   - **Verify**: the file table shows `top-5-soccer-players.xlsx`
   - **Verify**: the row's type/size cells read `Excel Spreadsheet` and the formatted
     size of the seeded payload (`get_file_row_text()`; `formatFileSize`, base-1024,
     `src/utils/filePreview.js:719`)
2. Observe the row **without hovering**, then hover it (`hover_file_row`)
   - **Verify**: `artifacts-file-preview-button-top-5-soccer-players.xlsx` resolves to
     **0 matches** in both states — the "View/Edit file" icon is absent for an
     unsupported type (`ArtifactRowActions.jsx` gates it on `row.canPreview`).
     *(Case steps 2–3 claim the opposite — #1692.)*
3. Open the file's preview via the product's own preview URL route —
   `/artifacts?bucket=<bucket>&file=top-5-soccer-players.xlsx` (the exact params
   `Artifacts.jsx` writes when a previewable file is opened, restored by its URL-restore
   effect, `Artifacts.jsx:545-570`). New page-object method
   `navigate_to_file_preview(bucket, file_key)` — sibling of the existing
   `navigate_to_bucket_folder`. See § Fidelity Declaration.
   - **Verify**: the preview panel opens (its Close (X) button,
     `artifacts-preview-close-button`, is visible)
4. Verify the panel header shows the full path
   - **Verify**: `artifacts-preview-file-path` text == `f"{bucket}/top-5-soccer-players.xlsx"`
     (live: `autotest-test-probe-890968/top-5-soccer-players.xlsx`)
5. Verify the unsupported-preview body
   - **Verify**: the empty-file icon is visible
     (**testid needed** `artifacts-preview-unavailable-icon`)
   - **Verify**: the heading reads exactly `Preview Not Available`
     (**testid needed** `artifacts-preview-unavailable-title`)
   - **Verify**: the supporting message reads exactly
     `Preview is not supported for this file type.`
     (**testid needed** `artifacts-preview-unavailable-message`)
   - **Verify**: the supported-formats paragraph is visible and starts with
     `Supported formats:` and contains `txt, md, json` (assert `starts_with` +
     `contains`, NOT full equality — the sentence is a long hardcoded literal in
     `PreviewUnavailable.jsx` that will churn as formats are added)
     (**testid needed** `artifacts-preview-unavailable-formats`)
6. Verify the centred **Download** button is present
   (**testid needed** `artifacts-preview-unavailable-download-button`)
7. Verify the header edit controls are **structurally absent** (not disabled)
   - **Verify**: `artifacts-preview-save-button` count == 0
   - **Verify**: `artifacts-preview-discard-button` count == 0
     *(Case step 9 says "inactive/greyed out" — #1693. `PreviewHeader.jsx` wraps both in
     `{canPreview && …}`; contrast image files (ELITEA-1862) where they DO render, disabled.)*
8. Verify no Preview/Raw tabs are shown
   - **Verify**: `artifacts-preview-mode-toggle-group` count == 0
9. Click the panel's **Download** button
   - **Verify**: a download starts, `download.suggested_filename ==
     "top-5-soccer-players.xlsx"`, and the downloaded bytes equal the seeded payload
     (`Path(download.path()).read_bytes()`)
10. Verify no console errors were emitted across the whole flow

## Expected Results
- The .xlsx row offers **no** preview entry point; only the 3-dot actions menu.
- Deep-linked, the panel renders the unsupported state: icon + `Preview Not Available` +
  `Preview is not supported for this file type.` + the supported-formats sentence + a
  working Download button.
- Save, Discard and the render-mode toggle group are **absent** (count 0). The Close (X)
  and the 3-dot overflow menu remain present.
- Download delivers the original file byte-for-byte.
- No console errors.

## Fidelity Declaration

| What | Transit or terminal | Authority |
|---|---|---|
| Reaching the preview panel via `/artifacts?bucket=…&file=…` instead of a row click | **Transit** | The URL is the product's OWN preview route — `Artifacts.jsx` sets exactly these params on every preview open and restores the panel from them on load; navigating to it is ordinary user navigation (bookmark / shared link), not injected state. **No in-app path exists for an unsupported type** (#1692). Every observable this case asserts — the panel's text, the absent buttons, the download bytes — is produced by the product. |

No `route.fulfill` / `page.evaluate` / `monkeypatch` / mocked client is used or needed
anywhere in this case.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket contains `top-5-soccer-players.xlsx` | file present | step 1 | `file_exists()` on the fixture-seeded bucket | asserted *(fixture bucket, not a literal shared one)* |
| 1 Navigate to Artifacts, locate bucket with the file | bucket found | step 1 | `navigate_to_bucket` + file table visible | asserted |
| 2 Hover the row → View/Edit icon appears | icon visible on hover | step 2 | `artifacts-file-preview-button-{name}` count == 0 before AND after hover | **clarification #1692** — asserted as ABSENCE (live contract) |
| 3 Verify the View/Edit icon IS present | icon visible | step 2 | same | **clarification #1692** — inverted to absence |
| 4 Click the View/Edit icon → preview panel opens | panel opens | step 3 | panel reached via the product's preview URL route; Close (X) visible | **clarification #1692** — gesture replaced, observable kept |
| 5 Header shows the file path | header shows path | step 4 | `artifacts-preview-file-path` == `{bucket}/{file}` | asserted |
| 6 Empty-file icon + `Preview Not Available` message | message shown | step 5 | new `artifacts-preview-unavailable-icon` / `-title` testids, exact text | asserted |
| 7 Supporting message listing supported formats | visible | step 5 | new `artifacts-preview-unavailable-message` + `-formats` testids | asserted *(decomposed — live shows TWO lines: the "not supported for this file type" message AND the formats sentence)* |
| 8 Download button in the centre of the preview area | present | step 6 | new `artifacts-preview-unavailable-download-button` testid | asserted |
| 9 Save/Discard top-right are INACTIVE/greyed out | both disabled | step 7 | both testids count == 0 | **clarification #1693** — asserted as structural absence |
| 10 No Preview/Raw tabs | no tabs | step 8 | `artifacts-preview-mode-toggle-group` count == 0 | asserted *(case text matches live)* |
| 11 Click Download → file downloads | download starts | step 9 | `expect_download()`, filename + byte equality | asserted |
| Expected Final State (composite) | unsupported state + working download | steps 4–9 | combination of the above | asserted |

### Axis 2 — Analyst additions

| Addition | Why |
|---|---|
| Row type/size cells (`Excel Spreadsheet` + formatted size) — step 1 | The row is the only place the product states the file's recognised type; asserting it pins the `fileTypes.js` mapping the preview gate is paired with, and it is free (one `get_file_row_text()`). Mirrors ELITEA-1864's own step 2. |
| Downloaded **bytes** equal the seeded payload — step 9 | `suggested_filename` alone proves a download event, not a correct file. The seeded payload is a known constant, so byte equality is exact and deterministic. |
| Console-error check — step 10 | Standard for this suite; a deep-link that renders an unsupported panel is exactly the path where a silent fetch error could hide (`useArtifactContentFetch` skips fetching when `canPreview` is false — confirmed no errors live). |
| Absence assertion on the mode-toggle group **and** on Save/Discard rather than a visual check | Testid-keyed `to_have_count(0)` is the project's sanctioned absence shape (canon #511 — absence assertions count as references). |

## Cleanup
- `artifact_bucket` fixture teardown deletes the bucket (known `#636` 404 on teardown —
  benign, does not fail tests).
- Nothing else mutates: this case never edits, saves or deletes a file.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance (verified 2026-08-23 after `git fetch origin`) | Notes |
|---|---|---|---|
| File row | `artifacts-file-row` (`ARTIFACT_FILE_ROW` class constant) | on `main` ✓ (`ArtifactTable.jsx:525`) | existing, reuse (`get_file_row_text`) |
| "View/Edit file" icon (dynamic) | `artifacts-file-preview-button-{filename}` (`ARTIFACT_FILE_PREVIEW_BUTTON`) | on `main` ✓ (`ArtifactRowActions.jsx:83`) | existing; used here **only** for a count-0 absence assertion |
| Preview panel file path | `artifacts-preview-file-path` | on `main` ✓ | existing, reuse (`get_file_preview_path_text`) |
| Save button | `artifacts-preview-save-button` | on `main` ✓ | existing; count-0 absence assertion |
| Discard button | `artifacts-preview-discard-button` | on `main` ✓ | existing; count-0 absence assertion |
| Render-mode toggle group | `artifacts-preview-mode-toggle-group` | on `main` ✓ (`PreviewHeader.jsx:267`) | existing; count-0 absence assertion |
| Close (X) | `artifacts-preview-close-button` | on `main` ✓ | existing; used as the panel-open wait anchor |
| Unavailable icon | **testid needed**: `artifacts-preview-unavailable-icon` | needs-adding | `PreviewUnavailable.jsx`'s `<Box component={UnavailableIcon} …>` — `Box` spreads props, so `data-testid` passes straight through. No DOM node added. |
| Unavailable title | **testid needed**: `artifacts-preview-unavailable-title` | needs-adding | the `Typography variant="headingSmall"` rendering the literal `Preview Not Available` |
| Unavailable message | **testid needed**: `artifacts-preview-unavailable-message` | needs-adding | the `Typography` rendering the `message` prop — `Preview is not supported for this file type.` for a type-gated file (the size-gated branch passes a different `sizeLimitMessage`, out of scope here) |
| Unavailable formats line | **testid needed**: `artifacts-preview-unavailable-formats` | needs-adding | the `Typography variant="bodySmall"` with the hardcoded formats sentence |
| Unavailable Download button | **testid needed**: `artifacts-preview-unavailable-download-button` | needs-adding | `Button.BaseBtn` spreads `...restProps` → `data-testid` passthrough works (same mechanism as `artifacts-preview-save-button`) |

All five new testids go on **existing** JSX nodes in
`src/[fsd]/features/artifacts/ui/FilePreviewCanvas/PreviewUnavailable.jsx` — attribute-only
additions, no wrapper elements, no hooks (zero-functional-impact check clean). Add via
`add-data-testid` on `EliteaAI/EliteaUI` `automation/testids`.

## Network Behavior
- Opening the panel for an unsupported type triggers **no content fetch** —
  `useArtifactContentFetch` returns early when `canPreview` is false. Do not wait on a
  content response; wait on the panel's own elements.
- The Download button calls the same `handleDownload` as the row menu (a presigned/blob
  fetch followed by an anchor click); capture it with `page.expect_download()`.
- No console errors observed across the whole flow (live, 2026-08-23).

## Known Defects Found During Exploration
- None — no product defect. Two **case-text clarifications** filed:
  **#1692** (steps 2–4: no View/Edit icon for .xlsx; panel unreachable from the row) and
  **#1693** (step 9: Save/Discard are absent, not greyed out).

## Blocked Steps
- None.

## Automation Hints
- Suggested spec: `automation/tests/ui/artifacts/test_artifacts_file_preview_unsupported_xlsx.py`
  — a NEW file (the `.py`/markdown/image preview specs all assume `canPreview == true`;
  this is the first unsupported-type spec).
- New page-object work in `automation/pages/artifacts_page.py`:
  - `navigate_to_file_preview(bucket_name, file_key, timeout=…)` — mirror
    `navigate_to_bucket_folder`'s URL-building + the `#638` bucket-param re-check guard,
    setting `?bucket=&file=`; wait on `file_preview_close_button` (present for BOTH the
    supported and unsupported branches) rather than the Save button (absent here — the
    existing `open_file_in_editor` waits on Save and therefore cannot be reused).
  - Five `LocatorDescriptor` fields for the new `artifacts-preview-unavailable-*` testids
    plus small readers (`get_preview_unavailable_title_text()` etc.).
- Markers: `ui`, `regression`, `p2`, `artifacts`. Wrap every step in `allure.step("Step N — …")`.
- Live-verified evidence: `test-results/screenshots/ELITEA-1863-xlsx-deeplink.png`
  (also embedded in #1692:
  https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-1863-step06-preview-not-available-xlsx.png).
