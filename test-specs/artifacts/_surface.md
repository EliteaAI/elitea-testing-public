# Artifacts surface — exploration digest

Handle cache for the Artifacts feature (`/artifacts`), built up across analyst
runs. **Not a source of truth** — verify a handle as you use it; treat a stale
entry as a prompt to look at the app, not as a fact. One writer at a time
(units run serially); the current writer updates this file directly.

## Confirmed handles (as of ELITEA-1811/1814 analysis, 2026-08-02)

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | `ArtifactsPage.wait_for_page_load()` | |
| Create-bucket icon | `artifacts-create-bucket-button` | `click_create_bucket_button()` | full page nav to `/artifacts/create-bucket`, not a modal |
| Bucket name field | `artifacts-bucket-name-input` | `fill_bucket_name()` | pre-filled `"new-bucket"` on fresh load; `aria-invalid` flips `"true"` only after blur or Save-click (NOT immediately on type — Formik `touched` gates it) |
| Save button (New Bucket form) | `artifacts-bucket-save-button` | `bucket_save_button` field | **never carries a `disabled` attribute for an invalid-but-nonempty, ≤56-char name** — its `disabled` prop only checks `isCreating/isUpdating/!name/name.length===0/name.length>56`, never the regex (`CreateBucket.jsx:292-298`). For the happy path, `click_bucket_save_button()` wraps the click in `page.expect_response` for the `POST .../artifacts/buckets` — **do not reuse that helper for an invalid name**, no request ever fires and it hangs for its timeout. |
| Bucket name validation rule | n/a (client-side yup) | `CreateBucket.jsx:22-30` | `^[a-zA-Z][a-zA-Z0-9-]*$`, max 56 chars; single shared error message `"Name should start with a letter and contain only letters, numbers, and hyphen"` for EVERY violation of the regex (leading digit, `$`, `_`, space — all produce byte-identical text) |
| Inline validation message | **testid needed: `artifacts-bucket-name-helper-text`** | not yet added | MUI `<TextField>` helperText renders NO `data-testid` today; fix shape: `FormHelperTextProps={{ 'data-testid': 'artifacts-bucket-name-helper-text' }}` (or `slotProps.formHelperText`, precedent: `GenerateSkillReviewForm.jsx`) |
| "Click 'Artifacts'" (return nav) | no testid — use `ArtifactsPage.navigate_to_artifacts()` (direct URL nav) | n/a | Sidebar nav entries (`SidebarBody.jsx`/`SidebarMenuItem.jsx`) are a SHARED component with NO `data-testid` on any item; threading one through is out of proportion to a single-click case need (confirmed independently by both ELITEA-1809 and ELITEA-1811/1814 analysis) |
| Bucket-not-in-list check | `ArtifactsPage.bucket_exists(name)` | pre-existing, raw `get_by_text` (tech debt #25/#42) | reused as-is, not a new handle |

## Confirmed handles (as of ELITEA-1828/1829/1831 cluster analysis, 2026-08-02)

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| "Resolve duplicates" modal — message text | `artifacts-resolve-duplicates-message-text` | **added this run**, `DuplicateDialogContent.jsx`'s `label` Typography | Singular vs plural wording depends on `duplicateFilenames.length` — confirmed live singular text for exactly 1 duplicate: "This file already exists in this bucket. Choose how to handle duplicates." |
| "Resolve duplicates" modal — Skip button | `artifacts-resolve-duplicates-skip-button` | **added this run**, `DuplicateResolutionDialog.jsx` | Uploads ONLY the non-duplicate file(s) in the batch; fires exactly one PUT per non-duplicate, zero for the duplicate |
| "Resolve duplicates" modal — Replace button | `artifacts-resolve-duplicates-replace-button` | **added this run**, `DuplicateResolutionDialog.jsx` | Not yet exercised by any case (visibility-only in ELITEA-1828) — next case to click it should confirm its actual overwrite semantics live |
| "Resolve duplicates" modal — Keep both button | `artifacts-resolve-duplicates-keep-both-button` | **added this run**, `DuplicateResolutionDialog.jsx` | Renames the NEW file to `{baseName} - Copy{extension}` (space-hyphen-space, capitalized "Copy") — NOT the hyphenated `sample-copy.txt` shape a case's example text may suggest; see `EliteaAI/elitea-testing-public#1102` |
| All 4 resolve-duplicates testids | commit `EliteaAI/EliteaUI@918b8b22` | `automation/testids` | pushed; not yet on `main` — human cherry-pick pending |

## Confirmed handles (as of ELITEA-1851/1852/1856 cluster analysis, 2026-08-02)

File preview/edit editor surface (`FilePreviewCanvas`, opened via a file row's
"View/Edit file" icon). No page-object support exists for this surface yet
(`artifacts_page.py` has zero editor/preview methods today — only row-level
download/delete via `ArtifactRowActions`'s DotMenu).

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| "View/Edit file" icon (per row) | **testid needed**: `artifacts-file-preview-button-{filename}` (dynamic) | `ArtifactRowActions.jsx` | currently only `aria-label="Preview {name}"`, no `data-testid` |
| Editor 3-dot actions menu trigger | `file-preview-overflow-menu-menu-button` | `PreviewHeader.jsx`'s `DotMenu id="file-preview-overflow-menu"` | **EXISTS, confirmed live** — DotMenu's own `${id}-menu-button` convention, no work needed. NOT the same DotMenu as the row-level one (`artifact-actions-{row.id}-menu-button`, ELITEA-1839) — editor's has Copy Content + Download + Delete; row's has only Download + Delete. |
| Editor menu items (Copy Content/Download/Delete) | **testid needed**: add `key: 'artifacts-preview-copy-content'` etc. to `PreviewHeader.jsx`'s `menuItems` array — `DotMenu`'s `testId: item.key` mechanism then yields `data-testid="artifacts-preview-{key}-menuitem"` | `PreviewHeader.jsx` | confirmed live: currently `data-testid` is `None` on all 3 items (no `key` set) |
| Editor delete confirmation | `delete-confirm-dialog` / `delete-confirm-title` / `delete-confirm-message` / `delete-confirm-button` / `delete-confirm-cancel-button` | `Modal.DeleteEntityModal` (shared, reused from `FilePreviewCanvas/index.jsx`) | **EXISTS** — same component/testids as bucket/row deletes. Editor's delete does NOT pass `inlineExtraContent`, so message = `"Are you sure to delete the {name}?"` (no "can't be restored" clause) — differs from the row-level delete's message, which DOES pass that clause. |
| CodeMirror editable content | pass `contentTestId="artifacts-preview-code-content"` to `Field.CodeMirrorEditor` in `PreviewContent.jsx`'s default/CODE branch | `PreviewContent.jsx` | **first-party mechanism already exists** in `CodeMirrorEditor.jsx` (`contentTestId` prop → sets `data-testid` on `.cm-content` via `EditorView.contentAttributes`) — just not wired at this call site. NOT a #579 raw-handle case once added. |
| CodeMirror line-number gutter | **testid needed** on wrapper: `artifacts-preview-code-editor` on the `codeEditorWrapper` Box, then scope raw `.cm-lineNumbers` under it | `PreviewContent.jsx` | genuine **#579 sanctioned exception** — unlike `.cm-content`, the gutter has no first-party testid hook |
| Editor header file-path | **testid needed**: `artifacts-preview-file-path` | `PreviewHeader.jsx` (`canvasTitle` Typography) | no testid today |
| Language Select | **testid needed**: `artifacts-preview-language-select` | `PreviewHeader.jsx` | `Select.SingleSelect` **already accepts** a `data-testid` prop (`SingleSelect.jsx:82,660`) — trivial to wire, not a component gap |
| Save button | **testid needed**: `artifacts-preview-save-button` | `PreviewHeader.jsx` (`Button.BaseBtn`) | `BaseBtn` spreads `...restProps` — `data-testid` passthrough works once passed |
| Discard button | **testid needed**: `artifacts-preview-discard-button` (via `dataTestId` prop) | `PreviewHeader.jsx` (`Button.DiscardButton`) | `DiscardButton.jsx` already wires `dataTestId` → `data-testid` |
| Close (X) button | **testid needed**: `artifacts-preview-close-button` | `PreviewHeader.jsx` | only `aria-label="Close preview"` today |
| Save/Discard disabled state | `disabled={isSaving \|\| !hasUnsavedChanges}` (both buttons, same gate) | `PreviewHeader.jsx` props from `FilePreviewCanvas/index.jsx` | **both start disabled on open**, become enabled only after an edit. Case ELITEA-1851's text wrongly implies Save is active on open — filed `EliteaAI/elitea-testing-public#1108`. |
| Save success toast | `"File saved successfully"` (exact, hardcoded, matches case text) | `FilePreviewCanvas/index.jsx:308` | no toast-container testid exists in this codebase; `[class*="Toastify"]` CSS does NOT match — use `get_by_text(exact=True)` on the literal string as an accepted interim |
| Delete success toast | `"File deleted successfully"` (exact) | `FilePreviewCanvas/index.jsx:434` | case ELITEA-1856 claims `"The artifacts have been deleted successfully"` — that string doesn't exist anywhere in EliteaUI source (grepped). Filed `EliteaAI/elitea-testing-public#1109` (bundled with the delete-modal-text finding). |
| URL query params on preview open | `?bucket=<name>&file=<key>` | `Artifacts.jsx`'s `setSearchParams({ bucket, file })` | confirmed live |
| Test-data seeding for this surface | `artifact_bucket` fixture + `ArtifactAPI.upload_file(bucket, key, bytes)` | `automation/fixtures/data_fixtures.py:453`, `automation/api/client.py:1292` | no "bucket-1"/"machine_learning.py" fixture exists anywhere in the suite — each preview/edit case seeds its own fresh bucket+file; cases that mutate (1852 edits) or delete (1856) the file MUST NOT share a bucket with read-only cases (1851) |

## Known gotchas
- **Formik `touched` gating**: typing alone never reveals a validation error
  in this form — only blur or submit-attempt sets `touched.name = true`,
  which the `error`/`helperText` render both depend on. Don't assert
  `aria-invalid` immediately after `fill_bucket_name()`; assert it after the
  Save click (or a deliberate blur).
- **Invalid-name Save click produces NO network request at all** (yup blocks
  `formik.onSubmit` client-side) — this is distinct from ELITEA-1809's
  duplicate-name case, which DOES reach the server and gets a 400. Don't
  wait on a response for the invalid-name path.
- MCP Playwright server (`.mcp.json` → `playwright`) was not reachable via
  `ToolSearch` in this session — fell back to a direct
  `playwright.sync_api` Python scratch script driving `ArtifactsPage`
  methods directly. If this recurs, flag it — may indicate the MCP server
  needs a restart/reinstall, not just a one-off hiccup. (Recurred again in
  the ELITEA-1828/1829/1831 cluster session, 2026-08-02 — now 2/2 sessions.)
- **`artifact_bucket` fixture teardown 404s on every run** (tracked, `#636`,
  `.agents/memory/qa-engineer/artifact_bucket_fixture_delete_silently_fails_404.md`)
  — reconfirmed live this session on 3/3 buckets created for the
  ELITEA-1828/1829/1831 cluster. Already wrapped in try/except by the
  fixture; doesn't fail tests, but expect `autotest-*` buckets to keep
  accumulating in the `Private` project.
