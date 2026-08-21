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

## Confirmed handles (as of ELITEA-1857/1858/1862 cluster analysis, 2026-08-03)

Markdown-file (Preview/Raw toggle) and image-file editor surfaces — extends
the ELITEA-1851/1852/1856 editor-surface digest above. The `.py`-file cluster
never exercised the render-mode toggle (CODE files skip straight to
CodeMirror, no toggle) or the IMAGE branch — both are genuinely new surface.

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Render-mode toggle group | **testid needed**: `artifacts-preview-mode-toggle-group` | `PreviewHeader.jsx`, `ToggleButtonGroup` (currently only `aria-label="Render Mode Toggle"`, no `data-testid`) | present for markdown/html/mdx/data/mermaid files, absent for image/code/docx (`modeTogglerAvailable` gate) |
| "Rendered mode" toggle button | **testid needed**: `artifacts-preview-mode-toggle-rendered` | same file, `ToggleButton value="rendered"` | name by the stable `value` prop, NOT the visible label — label text is "Preview" for markdown/html/mdx, "Table" for CSV/TSV, "Diagram" for Mermaid (state-conditional label, stable value) |
| "Code mode" toggle button | **testid needed**: `artifacts-preview-mode-toggle-code` | same file, `ToggleButton value="code"` | always labeled "Raw" for every file type that has a toggler |
| Rendered Markdown content wrapper | **testid needed**: `artifacts-preview-markdown-content` | `PreviewContent.jsx`, `<Box sx={styles.markdownWrapper}><Markdown>{fileContent}</Markdown></Box>` | currently untagged; verify headings/bold/bullets via `.text_content()`/`.inner_html()` scoped under this testid |
| Rendered image | **testid needed**: `artifacts-preview-image` | `PreviewContent.jsx`, `<Box component="img" src={imageBlobUrl} alt={file.name} .../>` | currently only `alt={file.name}`, no `data-testid`; interim raw handle `img[alt='{filename}']` is NOT testid-compliant, must be replaced before merging |
| Default render mode on open | markdown/data/mermaid/image/html/mdx → `RENDERED`; everything else → `CODE` | `FilePreviewCanvas/index.jsx`'s open-effect | confirmed live: a `.md` file opens with "Preview" pressed by default |
| Save behavior branch on file type | `isHtmlFile \|\| isMdxFile \|\| isMarkdownFile` → editor stays open, auto-switches `renderMode` to `RENDERED` after save; everything else → `onClose()` closes the editor | `FilePreviewCanvas/index.jsx`'s `handleSaveChanges` | **live-confirmed, contradicts case ELITEA-1858's "reopen the file" step** — no reopen occurs or is needed; filed `EliteaAI/elitea-testing-public#1111` |
| Editing gate (`canEdit`) | `renderMode === CODE && !isImageFileType && fileContent` | `FilePreviewCanvas/index.jsx` | false in Preview/rendered mode (no editing possible) AND unconditionally false for images (no Raw-tab escape hatch exists for images — there's no toggle at all) |
| Copy Content menu-item visibility | `show: canPreview && fileContent && !isImageFileType` | `PreviewHeader.jsx`'s `menuItems` | confirmed live: image files' actions dropdown has exactly `["Download", "Delete"]`, Copy Content structurally absent (filtered pre-render, not merely disabled) |
| Reliable single-line edit targeting in CodeMirror | `page.locator(".cm-line").filter(has_text="<target text>").first.click()` then `End` then `type()` | n/a — technique, not a testid | **`Control+Home` did NOT reliably move the cursor to true document start** in this CodeMirror instance during live testing — a plain `.click()` on the content wrapper lands wherever the pointer's bounding-box center falls, and `Control+Home` failed to correct it (live repro: an edit intended for line 1 landed on paragraph 2 instead). The existing `edit_file_preview_content(text, line_index=0)` helper (ELITEA-1852) works for THAT case only because it doesn't care which line gets hit ("any known content line" per its own AFS) — don't reuse it blind when a case needs a SPECIFIC line (e.g. the heading). |
| Image load timing | image blob fetch can exceed 1s beyond `networkidle` on a busy shared DEV backend | live-observed | use a condition-based wait on the `<img>` element's visibility (generous timeout), not a fixed short sleep — a `networkidle` + 1s wait intermittently caught the panel still on "Loading file content..." |

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
  accumulating in the `Private` project. **Reconfirmed again in the
  ELITEA-1857/1858/1862 cluster (2026-08-03)** — the `Private` project now
  shows **555 accumulated buckets**. Flagging for a dedicated cleanup sweep;
  out of scope for any single case's teardown to fix.
- MCP Playwright server unreachable via `ToolSearch` again in the
  ELITEA-1857/1858/1862 cluster session (2026-08-03) — now 4 consecutive
  sessions (ELITEA-1880/1993, ELITEA-2004/2010, ELITEA-1828/1829/1831, and
  this one). See `.agents/memory/qa-engineer/no_playwright_mcp_use_sync_playwright_script.md`
  — go straight to a `playwright.sync_api` scratch script, don't retry `ToolSearch`.

## Confirmed handles (as of ELITEA-1803/1804/1805/1806 cluster, 2026-08-21)

Artifacts **landing page chrome** — left-panel header/footer/storage selector,
the file-table column headers, and the pagination controls. All of these were
untagged before this run; the testids below were added on
EliteaAI/EliteaUI@6449a5c4 (`automation/testids`, human cherry-pick to `main`
pending).

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Storage-provider row | `artifacts-storage-selector` (+ `-arrow`) | `Components/BucketStorageSelector.jsx` | text reads `Elitea S3 storage` |
| Left-panel footer — bucket count | `artifacts-buckets-footer-count` | `Components/BucketFooter.jsx` | `text_content()` is `Buckets:757` — label + value are two sibling `<Typography>`s inside the testid'd Box, **no whitespace between them**; match with `Buckets:\s*(\d+)`. The number is NOT stable (the `#636` leak keeps adding buckets) — cross-check against the API's own bucket list instead of a literal |
| Left-panel footer — total size | `artifacts-buckets-footer-size` | same | `Size:254.8 MB` |
| Bucket's empty-tree label | `artifacts-bucket-tree-empty-label-{bucketName}` (**dynamic**) | `Components/BucketContent.jsx` | had to be bucket-parameterized: `BucketContent` is a SIBLING of `BucketItem` inside an untagged wrapper `<Box>`, so it cannot be CSS-scoped under `artifacts-bucket-row-{name}`, and several buckets can be expanded at once |
| Bucket-info (i) icon — main panel toolbar | `artifacts-bucket-info-button` | `component/BucketInfoTooltip.jsx` (mounted from `ArtifactTableToolbar.jsx`) | **This — not the left-panel bucket name — is where the Retention Policy / Number of files tooltip lives.** ELITEA-1805's case text says "hover the bucket name in the left panel"; that element only has a conditional overflow tooltip repeating the name. Filed `EliteaAI/elitea-testing-public#1617` |
| Bucket-info tooltip content | `artifacts-bucket-info-tooltip-content` | same | opens on **hover** (same activation as #669's field tooltip). Text: `Retention Policy:1 YearNumber of files:1` — labels/values are sibling Typographies, no whitespace |
| File-table column headers | `artifacts-file-table-column-header-{field}` | `component/ArtifactTable.jsx` wires the shared `GridTableHeader`'s existing `columnTestIdPrefix` prop | fields are `name`, `fileType`, `size`, **`modified`** (label "Last update" — the field key is NOT `lastUpdate`), `actions`. Width-gated: `modified` hides below a 900px table width — set viewport 1600x900 |
| Pagination — page info | `artifacts-pagination-page-info` | `component/ArtifactTable.jsx` → shared `GridTablePagination` `pageInfoTestId` | `1 - 1 of 1` / `1 - 10 of 12` / `11 - 12 of 12` |
| Pagination — prev / next | `artifacts-pagination-prev-button` / `-next-button` | same | `prevButtonTestId` prop was **added** to the shared component this run (`nextButtonTestId` already existed). Both are real `disabled` attributes — assert with `is_disabled()` |
| Pagination — rows per page | `artifacts-pagination-page-size-select-combobox` | same, via a new `pageSizeSelectTestId` prop → `SingleSelect` derives the `-combobox` suffix | default text `10` |
| Whole pagination footer | — | `GridTablePagination` returns `null` when `totalRows === 0` | an empty bucket has NO pagination block at all (count 0), not a `0 - 0 of 0` |

### Landing-page behaviours confirmed live (2026-08-21)
- **`/artifacts` auto-selects (and expands) a bucket** when the URL carries no
  `?bucket=` param. Consequence: any page-wide count of "empty tree label" or
  "tree item" elements is polluted by that auto-selected bucket — always scope
  per bucket.
- Empty bucket: 0 file rows, 0 column headers, 0 pagination block, but the
  toolbar (search/upload/download/delete) and the footer stats still render.
- Single-file bucket: `1 - 1 of 1`, **both** arrows present and disabled.
- 12-file bucket: page 1 = 10 rows / `1 - 10 of 12` / prev disabled / next
  enabled; page 2 = 2 rows / `11 - 12 of 12` / prev enabled / next disabled.
  **The default order is NOT name-ascending** — after seeding `file-01 …
  file-12` via `ArtifactAPI.upload_file`, page 2 came back as `file-02.txt`,
  `file-03.txt` (modification-order listing, same-second uploads tie). Assert
  the page PARTITION (disjoint pages, union == seeded set), never a named slice.
- Row text for a `.txt` file: `sample.txtText120 B21-08-2026, 05:43 PM`
  (Type column renders `Text`; timestamp format `DD-MM-YYYY, HH:MM AM/PM`).

### ELITEA-1806 (no-buckets empty state) is BLOCKED — do not retry blind
Bucket counts measured via `GET /artifacts/buckets/default/{pid}` for every
project the selector offers: 399 Private **759**, 406 Bugs & Features **4**,
25 Elitea Development **19**, 471 Elitea Testing Team **13**, 400 UI Testing
**2**. No empty project exists, the suite has no project create/delete client,
and emptying a shared project is destructive. Faking the buckets response would
be a terminal substitution of the very thing the case observes. Needs a human
decision (dedicated empty project / project-lifecycle API / manual-only) — see
`test-specs/artifacts/l3_artifacts-landing-page-no-buckets_ELITEA-1806.md`.

### Gotchas added this run
- **Vite HMR did NOT pick up an edit under `src/[fsd]/`** (bracketed FSD
  directories). The dev server kept serving the pre-edit module — verified by
  `curl -s 'http://localhost:5173/src/%5Bfsd%5D/entities/grid-table/ui/GridTablePagination.jsx' | grep <new-prop>`
  returning 0 hits while the file on disk had it. Edits under
  `src/pages/…` in the SAME commit HMR'd fine. **Restart `npm run dev` after
  touching anything under `src/[fsd]/`**, and verify with that curl before
  concluding "the testid does not render".
- The project's `Private`/399 bucket leak (`#636`) is now at **759** buckets.

### Footer "Buckets: N" — use the rendered list as the oracle, not the API
`BucketsPanel.jsx` feeds `BucketFooter` `bucketCount={buckets?.length}` — the
same array the list renders. An API cross-check
(`GET /artifacts/buckets/default/{project}`) is **racy**: the listing is
eventually consistent, measured live at 760 rendered vs 762 from the API
seconds after creating buckets. Compare the footer against the panel's own
DISTINCT rendered rows instead (`ArtifactsPage.get_rendered_bucket_names()`) —
distinct, because a PINNED bucket is rendered twice (`BucketsListContent.jsx`
renders the pinned list AND the full list).
