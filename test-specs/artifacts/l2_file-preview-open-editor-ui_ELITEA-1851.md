# Test Case: File Preview/Edit – Open Supported Text File via View/Edit Icon and Verify Editor UI

## Metadata
- **TMS ID**: ELITEA-1851
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (cluster session ELITEA-1851/1852/1856, 2026-08-02)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (auth_state, localhost).
- A bucket exists containing a text file the editor can preview (Python source
  used in this analysis — `.py` is in the previewable-extensions list per
  `filePreview.js`). **Not** a pre-existing "bucket-1" — see § Test Data.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Fresh bucket via `artifact_bucket` fixture (`automation/fixtures/data_fixtures.py:453`)
  — unique name `autotest-<test-name>-<ts>`, deleted in fixture teardown.
- `machine_learning.py` uploaded into that bucket via `ArtifactAPI.upload_file()`
  (`automation/api/client.py:1292`) — a small Python source string is sufficient;
  the case's exact "18.5 KB" size is flavor text, not an assertable value (the
  file size shown in the UI simply reflects whatever bytes were uploaded — assert
  it matches the uploaded content's actual byte length, not a hardcoded "18.5 KB").
- Detected language: confirmed live as `Python (detected)` for a `.py` file
  (see `getLanguageFromFilename`, `EliteaUI/src/utils/filePreview.js`).

**Why not reuse a literal "bucket-1"**: no such fixture/bucket exists in the
suite or as seeded test data (grepped `automation/` — zero hits outside a
stale literal-string comment in `test_artifacts_upload_three_options_verify_selection.py`).
Per `.agents/testing.md` § Test data strategy ("seed minimally... when the
observable requires fresh state"), each test creates its own bucket/file via
`artifact_bucket` + `ArtifactAPI.upload_file()`.

## Test Steps
1. Navigate to `${BASE_URL}/artifacts`
   - **Verify**: Artifacts page loads (bucket list visible)
2. Click the fixture bucket in the bucket list
   - **Verify**: URL becomes `?bucket=<bucket-name>`; file table shows the bucket's contents
3. Verify the file table displays `machine_learning.py` (type `Python`, a size string)
   - **Verify**: row visible via `artifacts-file-row` filtered by filename
4. Hover the `machine_learning.py` row
   - **Verify**: the "View/Edit file" icon (tooltip "View/Edit file", `aria-label="Preview machine_learning.py"`) becomes visible
5. Click the "View/Edit file" icon
   - **Verify**: editor panel opens; URL becomes `?bucket=<bucket-name>&file=machine_learning.py`
6. Verify the panel header shows the full path `<bucket-name>/machine_learning.py`
7. Verify the language label shows `Python (detected)` with a dropdown control
8. Verify the file content renders with CodeMirror line numbers on the left
9. Verify Save and Discard buttons are present **and both DISABLED** (no edit made yet — see Coverage Map clarification)
10. Verify the 3-dot (ellipsis) actions menu icon is present and clickable
11. Verify an X (close) icon is present

## Expected Results
- Editor opens showing: full file-path header, language label with dropdown,
  line-numbered content, Save/Discard buttons (disabled pre-edit), a clickable
  3-dot actions menu, and a close (X) icon.
- URL reflects `?bucket=<bucket-name>&file=machine_learning.py`.
- No console errors during open.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Artifacts | page loads | step 1 | bucket list visible | asserted |
| 2 Click bucket-1 | bucket selected | step 2 | URL `?bucket=` | asserted *(bucket is fixture-generated, not literal "bucket-1" — see Test Data)* |
| 3 File table shows machine_learning.py (Python, 18.5 KB) | file visible | step 3 | `artifacts-file-row` text | asserted *(exact "18.5 KB" not asserted — see Test Data note)* |
| 4 Hover row → icon appears | icon visible on hover | step 4 | preview button visible after `hover()` | asserted |
| 5 View/Edit icon visible | icon visible | step 4 | same | asserted |
| 6 Click icon → editor opens | editor panel opens | step 5 | Save/Discard buttons render | asserted |
| 7 File opens in editor | editor visible | step 5 | same | asserted |
| 8 Header shows full path | "bucket-1/machine_learning.py" | step 6 | header text = `<bucket>/machine_learning.py` | asserted *(bucket name is the fixture's generated name, not literal "bucket-1")* |
| 9 Language label shown | "Python (detected)" + dropdown | step 7 | label text + Select control present | asserted |
| 10 Line numbers visible | line numbers on left | step 8 | `.cm-lineNumbers` present (scoped, #579 exception) | asserted |
| 11 Save (active/blue) + Discard present | both visible, Save active | step 9 | Save/Discard render | **clarification** — live product shows Save **disabled** on open (no edit yet); becomes active only after an edit (confirmed by code: `disabled={isSaving \|\| !hasUnsavedChanges}`, and live in the ELITEA-1852 flow). Filed: `EliteaAI/elitea-testing-public#1108`. AFS asserts the correct live contract: both buttons present, both disabled pre-edit. |
| 12 3-dot menu present + clickable | menu present | step 10 | DotMenu trigger clickable, opens 3 items | asserted |
| 13 X close icon present | close icon visible | step 11 | Close button (`aria-label="Close preview"`) visible | asserted |
| 14 URL updates with file param | URL has `&file=...` | step 5 | `page.url` contains `file=machine_learning.py` | asserted |

### Axis 2 — Analyst additions
- Assert **no console errors** across the open flow — added: silent errors are
  the worst bugs (skill discipline); zero found live.
- Assert the DotMenu, when opened, contains exactly the three items
  Copy Content / Download / Delete (visual/structural check, not full
  interaction — full interaction is ELITEA-1856's job) — added: cheap
  confirmation that the same DotMenu ELITEA-1856 will drive is present and
  correctly populated at open time, catching a regression here rather than
  only in the 1856 spec.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket automatically.
   **Known flake**: teardown 404s on every run (tracked `#636`,
   `.agents/memory/qa-engineer/artifact_bucket_fixture_delete_silently_fails_404.md`)
   — already wrapped in try/except by the fixture, doesn't fail the test.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| File row | `page.get_by_test_id("artifacts-file-row").filter(has_text=filename)` | existing, confirmed live |
| "View/Edit file" icon (per row) | **testid needed**: `artifacts-file-preview-button-{filename}` (dynamic, template constant per `.agents/testing.md` § dynamic testids) — currently only `aria-label="Preview {name}"` on the `IconButton` in `ArtifactRowActions.jsx` (no `data-testid`) | add via `add-data-testid` on `EliteaUI/src/pages/Artifacts/component/ArtifactRowActions.jsx` |
| Editor header file-path text | **testid needed**: `artifacts-preview-file-path` | `PreviewHeader.jsx` — the `canvasTitle` `Typography` currently has no testid |
| Language label / Select | **testid needed**: `artifacts-preview-language-select` — `Select.SingleSelect` **already supports** a `data-testid` passthrough prop (`SingleSelect.jsx:82,660`); the call site in `PreviewHeader.jsx` just doesn't pass one yet | trivial addition, no library gap |
| Line numbers (CodeMirror gutter) | **testid needed** on the wrapping container: `artifacts-preview-code-editor` on the `codeEditorWrapper` `Box` in `PreviewContent.jsx` (currently untagged); then scope raw `.cm-lineNumbers` under it — **sanctioned #579 exception** (third-party editor library internal render nodes; CodeMirror renders its own gutter DOM, no first-party testid hook for it) | doc the exception in the page-object method per `.agents/testing.md` § Locator policy stop+flag rule |
| CodeMirror content area | **testid needed**: pass `contentTestId="artifacts-preview-code-content"` to `Field.CodeMirrorEditor` in `PreviewContent.jsx`'s default/CODE branch — **first-party mechanism already exists** (`CodeMirrorEditor.jsx`'s `contentTestId` prop → `EditorView.contentAttributes.of({'data-testid': contentTestId})`, sets it directly on `.cm-content`); just not wired at this call site yet | NOT a #579 case — use the existing extension point, don't add a raw handle |
| Save button | **testid needed**: `artifacts-preview-save-button` — `Button.BaseBtn` spreads `...restProps` onto the underlying MUI `Button`, so `data-testid` passthrough works once passed at the call site | `PreviewHeader.jsx` |
| Discard button | **testid needed**: `artifacts-preview-discard-button` via `Button.DiscardButton`'s existing `dataTestId` prop (`DiscardButton.jsx:41` wires it to `data-testid`) | `PreviewHeader.jsx` |
| 3-dot actions menu trigger | `file-preview-overflow-menu-menu-button` — **EXISTS, confirmed live.** `DotMenu` (`id="file-preview-overflow-menu"`) renders its `IconButton` with `data-testid={\`${id}-menu-button\`}` per `DotMenu.jsx` | no testid work needed |
| 3-dot menu (opened) container | `file-preview-overflow-menu-menu` (same `${id}-menu` pattern on the MUI `Menu`) — exists per code, not independently clicked this run | reuse as-is |
| Close (X) icon | **testid needed**: `artifacts-preview-close-button` — plain MUI `IconButton` with only `aria-label="Close preview"` today | `PreviewHeader.jsx` |
| URL / query params | n/a (browser URL) | `page.url` contains `bucket=<name>&file=machine_learning.py` — confirmed live via `Artifacts.jsx`'s `setSearchParams({ bucket, file })` |

## Network Behavior
- No explicit network capture needed for this read-only view case beyond the
  page's own file-content fetch (`useArtifactContentFetch` hook) — the editor
  opening and rendering content IS the observable.

## Known Defects Found During Exploration
- **[CLARIFICATION]** Save button is disabled (not "active/blue") on initial
  open, per case step 11 — filed `EliteaAI/elitea-testing-public#1108`.
  Case-text drift, not a defect: AFS asserts the correct live behavior
  (disabled pre-edit).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- New page object needed/extended: `ArtifactsPage` (`automation/pages/artifacts_page.py`)
  gains editor-panel methods once the testids above are added — no editor
  support exists in the page object today (grepped: zero `editor`/`preview`
  hits besides download/delete row actions).
- Testids to add (this case's scope only — see also ELITEA-1852/1856 for the
  editor's Save/Discard-active and DotMenu-item testids, shared surface):
  `artifacts-file-preview-button-{filename}` (dynamic), `artifacts-preview-file-path`,
  `artifacts-preview-language-select`, `artifacts-preview-code-editor`,
  `contentTestId="artifacts-preview-code-content"`, `artifacts-preview-save-button`,
  `artifacts-preview-discard-button`, `artifacts-preview-close-button`.
- MCP Playwright server was unreachable via `ToolSearch` this session (recurring,
  ≥3/3 sessions per `test-specs/artifacts/_surface.md`) — explored via a direct
  `playwright.sync_api` scratch script driving the live app instead. Screenshots
  saved to `automation/test-results/screenshots/ELITEA-1851-1852-1856-*.png`.
