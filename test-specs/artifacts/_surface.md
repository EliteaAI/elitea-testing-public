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
| "Click 'Artifacts'" (return nav) | `sidebar-menu-item-artifacts` — or `ArtifactsPage.navigate_to_artifacts()` (direct URL nav) | n/a | **CORRECTED 2026-08-21 (ELITEA-1807):** the 2026-08-02 claim that sidebar nav entries carry NO `data-testid` is no longer true — `SidebarBody.jsx` passes `testId={\`sidebar-menu-item-${i.value}\`}` to every item. See the ELITEA-1807 section below for the full list. Direct URL nav remains the cheaper transit for a "return to Artifacts" step. |
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
| Left-panel footer — bucket count | `artifacts-buckets-footer-count` | `Components/BucketFooter.jsx` | `text_content()` is `Buckets:757` — label + value are two sibling `<Typography>`s inside the testid'd Box, **no whitespace between them**; match with `Buckets:\s*(\d+)`. The number is NOT stable (the `#636` leak keeps adding buckets) — cross-check against the panel's own DISTINCT rendered rows (`ArtifactsPage.get_rendered_bucket_names()`) instead of a literal; an API cross-check is racy, see § Footer "Buckets: N" below |
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

## Confirmed handles (as of ELITEA-1807, 2026-08-21)

Panel **collapse/expand** chrome — the BUCKETS left panel's `<<`/`>>` control
and the global navigation sidebar's `<`/`>` control. Testids added on
EliteaAI/EliteaUI@9062dff0 (`automation/testids`, human cherry-pick to `main`
pending).

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| BUCKETS panel collapse/expand toggle | `artifacts-buckets-panel-toggle-button` + `data-collapsed="true|false"` | `Components/BucketHeader.jsx` | ONE element whose icon flips (`DoubleLeftIcon`↔`DoubleRightIcon`); the icons are untagged SVGs, so state rides the `data-collapsed` attribute per the PR #581 ruling — asserting it IS asserting the icon swap |
| Sidebar collapse/expand toggle | `sidebar-collapse-toggle-button` + `data-collapsed="true|false"` | `src/[fsd]/widgets/sidebar-root/ui/Sidebar.jsx` | same shape; the control is a fixed-position circular `Box`, NOT inside the drawer |
| Sidebar nav items | `sidebar-menu-item-{value}` — `chat`, `agents`, `pipelines`, `skills`, `toolkits`, `mcps`, `credentials`, `applications`, `artifacts` | `SidebarBody.jsx` | **pre-existing** — `SidebarMenuItem` already takes a `testId` prop and `SidebarBody` already supplies it. Supersedes the older ELITEA-1809/1811 digest row claiming sidebar nav items carry NO testid: that is no longer true. |
| Sidebar Settings button | `sidebar-settings-button` | `ui/button/SettingsButton.jsx` → shared `SidebarButton` | added via a new caller-supplied `testId` prop on the SHARED `SidebarButton` (the compliant shared-component shape) — other SidebarButton consumers stay untagged |
| Sidebar Agent HUB button | `sidebar-agent-hub-button` | `ui/button/AgentHubButton.jsx` | its label is **`Catalog`**, not "Agent HUB" |

### Collapse/expand behaviours confirmed live (2026-08-21)
- **BUCKETS collapsed** → `artifacts-buckets-heading`, `artifacts-storage-selector`
  and `artifacts-buckets-footer-count` are **unmounted** (count 0 — all three are
  gated on `!collapsed` in `BucketsPanel.jsx`/`BucketHeader.jsx`), while the bucket
  ROWS stay in the DOM and merely go invisible (`bucketListOuterContainer` has
  `display: collapsed ? 'none' : 'flex'`). Assert count 0 for the former and
  **not-visible** for the latter — mixing them up gives a test that passes for the
  wrong reason.
- **Sidebar collapsed** → every `sidebar-menu-item-*` (and Settings / Agent HUB)
  stays visible as an icon, but its label `<Typography>` is unmounted
  (`showLabel={!sideBarCollapsed}`), so `text_content()` becomes `''`. Icon-only
  mode is therefore "same elements, empty text", never "elements gone".
- **The two panels are genuinely independent**, verified in both directions and
  from both starting states (sidebar collapsed while BUCKETS toggles twice, and
  BUCKETS collapsed while the sidebar toggles twice) — no state leaked either way.
- **Sidebar state is redux + `localStorage['sideBarCollapsed']` (write-only)**:
  `settings.js` writes the key but initialises `sideBarCollapsed: ''` (expanded)
  on load, so a collapsed sidebar does **not** survive a page load and cannot leak
  into a later test. Within one page session it does persist across SPA navigation.
- Live sidebar labels for the automation user: `Chats, Agents, Pipelines, Skills,
  Toolkits & Indexes, MCPs, Credentials, Applications, Artifacts` + `Settings` +
  `Catalog`. Case ELITEA-1807 says "Toolkits" and "Agent HUB" — stale copy, filed
  `EliteaAI/elitea-testing-public#1619` (sibling of #1208).
- **`src/[fsd]/` HMR gap reconfirmed** (the gotcha above): after editing
  `Sidebar.jsx`/`SidebarButton.jsx` the dev server had to be restarted
  (`npm run dev`) before the testids appeared; the `src/pages/Artifacts/…` edit in
  the same commit was live immediately. Verify with
  `curl -s 'http://localhost:5173/src/%5Bfsd%5D/…' | grep <testid>`.
- **Playwright MCP was NOT used** (5th consecutive session per the gotcha above):
  live execution ran as a throwaway pytest spec under `automation/tests/ui/artifacts/`
  driving the framework's own `page`/`auth_state` fixtures with `-s` prints — cheaper
  than a standalone `sync_playwright` script because auth and config come for free.
- This case needs **no seeding at all** — the precondition ("at least one bucket")
  is satisfied by the project's existing 766 buckets, so it is fully read-only and
  adds nothing to the `#636` bucket leak.

## Confirmed handles (as of ELITEA-1820/1821 pin/unpin cluster, 2026-08-21)

Bucket **pin/unpin** surface — the left panel's per-bucket dot-menu pin item and
the pin indicator next to a pinned bucket's name. Testids added on
`automation/testids` (human cherry-pick to `main` pending).

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Dot-menu pin item | `bucket-menu-pin-menuitem` | **added this run** — `key: 'bucket-menu-pin'` on `BucketItem.jsx`'s menu item; `DotMenu` turns a top-level item's `key` into `data-testid="{key}-menuitem"` | ONE testid for BOTH states — the label is `isPinned ? 'Unpin from top' : 'Pin to top'` (PR #581: testid = identity, label/`data-*` = state). Do NOT split it into pin/unpin testids. |
| Pin icon beside a pinned bucket | `artifacts-bucket-pin-indicator-{name}` (**dynamic**) | **added this run** — `BucketItem.jsx`'s `isPinned &&` wrapper `<Box>` | The row renders a SECOND, hover-only pin button under `!isPinned && isHovering`; it is deliberately left **untagged** (#511 — not on any test's executed path), which is what keeps `to_have_count(0)` absence assertions honest while hovering. |
| Any pin indicator | `[data-testid^="artifacts-bucket-pin-indicator-"]` | same | project-wide "nothing is pinned" check |
| Pin/unpin request | `PATCH /artifacts/buckets/default/{projectId}?name={bucket}` body `{"is_pinned": bool}` | `src/api/artifacts.js` `updateBucketPin` | returns 200 immediately; the LIST lags it (below) |
| Bucket dot-menu text, unpinned | `Upload filesRenamePin to topDelete` | `get_bucket_menu_items_text()` | personal project (399) hides Share / Manage permissions (`isPersonalProject`) — a TEAM project's menu has 6 items |
| Bucket dot-menu text, pinned | `Upload filesRenameUnpin from topDelete` | same | |

### Bucket-list ordering — settled live (2026-08-21)
- **The rendered list is ALPHANUMERIC.** All 766 rendered names were exactly
  `== sorted(names)` once nothing was pinned. `SimpleBucketList.jsx` calls
  `sortBucketsByRecent`, but the listing payload has no usable
  `updated_at`/`created_at`, so every comparison is `NaN`, the sort is a no-op,
  and the backend's alphanumeric order survives. Assert the observable
  (alphanumeric), not the mechanism — a payload change could make the code's
  recency intent real.
- **Pinned buckets render in their own list ABOVE the unpinned list**
  (`BucketsListContent.jsx`); `BucketsPanel.jsx` splits `pinnedBuckets` /
  `unpinnedBuckets`, so a pinned bucket is rendered **ONCE**, not twice.
  **Corrects** the ELITEA-1803-era claim in the § Footer section above and in
  `ArtifactsPage.get_rendered_bucket_names()`'s docstring ("rendered twice") —
  the de-duplication there is harmless but the stated reason was wrong.
- Consequence: a **leaked pinned bucket permanently sits at the top of the list
  for every project member** and breaks any "first item" assertion. Both pin
  cases clear the flag in teardown (`ArtifactAPI.set_bucket_pinned`, added this
  run) BEFORE deleting.

### Pin/unpin behaviours confirmed live (2026-08-21)
- **The bucket list lags the pin PATCH by ~8-10 s** (10 s pin, 8 s unpin,
  measured by 2-second polling; no intervening
  `GET .../artifacts/buckets/default/{pid}` was observed on the wire). Not filed
  as a defect — the state does arrive and no case sets a timing expectation —
  but every post-click assertion needs a generous condition wait (30 s), never a
  short one.
- **While the list is stale, the dot-menu is stale too**: it still reads "Pin to
  top" for an already-pinned bucket, and clicking it sends `is_pinned: true`
  again instead of unpinning. Always wait for the pinned state to RENDER before
  re-opening the menu.
- Pinning is persisted server-side and survives a reload.

### `#636` bucket leak — probable root cause found (2026-08-21)
`ArtifactAPI.delete_bucket` deletes via the **path** form
`/artifacts/buckets/default/{pid}/{bucket}` (and a `p--{pid}.{bucket}`
fallback), both of which **404**. The UI deletes via the **query** form
`/artifacts/buckets/default/{pid}?name={bucket}` — 10 leaked buckets were
deleted live with it, all **200**. Fixing `delete_bucket` is a shared-client
change with many callers (out of scope for a case); reported to the lead as a
suite-health item.

## Confirmed handles (as of ELITEA-1822 bucket-list scrolling, 2026-08-21)

Left-panel **scrolling** surface — the BUCKETS list's scroll container, plus how
it responds to the mouse wheel and to arrow keys.

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Buckets list scroll container | `artifacts-buckets-scroll-container` | **added this run** — `BucketsPanel.jsx`'s `bucketListOuterContainer` Box, EliteaAI/EliteaUI@3c96bc4b (`automation/testids`, human cherry-pick pending) | attribute-only edit; this is the element with `overflowY: auto` and the one the case means by "the bucket list panel" |
| "Is this row scrolled into view?" | `ArtifactsPage.is_bucket_row_within_panel(name)` — compares the row's `bounding_box()` with the container's | added this run | **`is_visible()` is the wrong oracle here**: a row clipped by the `overflow: auto` container still has a box and no `visibility: hidden`, so Playwright reports it visible even when it is 30 000 px below the fold |

### Bucket-list scrolling behaviours confirmed live (2026-08-21)
- **No virtualisation.** All 768 buckets are real DOM rows: container
  `scrollHeight` 30792 vs `clientHeight` 755 at viewport 1600x900, row height
  40 px. Any "scroll to the last bucket" step is therefore reachable, just long
  (six `mouse.wheel(0, 5000)` from the top).
- **Mouse wheel works in both directions** and needs a preceding
  `page.mouse.move()` onto the container (the wheel goes to whatever is under
  the cursor). One `wheel(0, 500)` ≈ 500 px.
- **Arrow keys DO scroll the panel** — ~38.7 px per `ArrowDown`/`ArrowUp` —
  after a plain click inside the container, even though the container carries no
  `tabIndex` and `document.activeElement` stays `BODY`. Chromium keeps the
  clicked scroll container as the keyboard scroll target. Do **not** conclude
  "keyboard scrolling is unsupported" from the missing `onKeyDown`/`tabIndex` in
  the source.
- **Click into the panel at the LEFT PADDING GUTTER** (`x + 6`, the container
  has `padding: 1rem` while rows start 16 px in) — a click on a bucket row would
  select and expand that bucket instead. Verified live: the gutter click leaves
  the URL unchanged and selects nothing.
- The initial `scrollTop` is **not always 0**: `SimpleBucketList.jsx` does a
  one-shot `scrollIntoView` for the URL-selected bucket, and a fresh
  `/artifacts` load auto-selects one (measured `scrollTop` 16 on arrival). Never
  assume the list starts pinned to the top — assert the top-alignment you want
  after scrolling there.

## Confirmed handles (as of ELITEA-1823 bucket hover highlight, 2026-08-21)

Left-panel bucket-row **hover highlight**. No testid was added this run — the
row's pre-existing `artifacts-bucket-row-{name}` is both the hover target and
the element whose background the case observes.

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Bucket row background (hover observable) | `artifacts-bucket-row-{name}` + `expect(...).to_have_css("background-color", …)` | `BucketItem.jsx`'s root Box | a computed-style assertion on a testid-anchored locator — **no `evaluate()`**, Playwright's web-first `to_have_css`/`not_to_have_css` retries until the style settles |
| Row selection state | `data-selected="true|false"` on the same row | same | pre-existing (`is_bucket_selected()`); the filter that keeps hover targets honest |
| "Park the cursor off every row" | `ArtifactsPage.move_mouse_off_bucket_list()` — `mouse.move()` to the right of `artifacts-buckets-scroll-container`'s box | added this run | `hover_buckets_panel()` moves onto the panel CENTRE, which lands ON a row — wrong primitive for "cursor away from the bucket list" |
| Row locator for assertions | `ArtifactsPage.bucket_row(name) -> Locator` | **pre-existing** (ELITEA-1820/1821) | specs may not build locators (`.agents/testing.md` § Locator policy); this accessor is how a spec gets the row for `to_have_css` — reused as-is, nothing added |

### Hover behaviours confirmed live (2026-08-21)
- **Hover is React state, not a CSS `:hover` rule.** `BucketItem.jsx` keeps
  `isHovering` in `useState`, set by `onMouseEnter`/`onMouseLeave` on the row's
  root Box, and `bucketItemStyles.getBackgroundColor()` reads it. Consequences:
  a real pointer move is required (`Locator.hover()` works; dispatching a
  synthetic event on a parent does not), and the **single-highlight invariant is
  structural** — one flag per row, cleared on leave.
- **Background colours, measured live (dark theme):** default
  `rgba(0, 0, 0, 0)` (`conversation.normal: 'transparent'`), hovered
  `rgba(255, 255, 255, 0.06)` (`white6`), selected `rgba(41, 184, 245, 0.15)`
  (`blue15`). `normal` is `'transparent'` in **both** palettes
  (`darkPalette.js:352` / `lightPalette.js:350`), so "row is in its default
  appearance" is theme-independent; the hover literal is **not** (light theme
  uses `dark6`) — assert default-vs-not-default, never the hover literal.
- **`isActive` beats `isHovering`**: `getBackgroundColor()` returns the selected
  colour first, so hovering the **selected** bucket produces NO background
  change. Since `/artifacts` auto-selects the first bucket on a param-less load,
  "hover the first bucket in the list" is a trap — always pick rows with
  `data-selected="false"`. (Case ELITEA-1823's Step 4 says "the first bucket";
  filed as a clarification, `EliteaAI/elitea-testing-public#1623`.)
- A hovered row also gains a hover-only pin button and its dot-menu container
  flips to `display:flex` (both deliberately out of ELITEA-1823's scope — the
  dot-menu reveal is ELITEA-1820's assertion).
- Playwright MCP again not used (6th consecutive session per the gotcha above) —
  live execution ran as a throwaway pytest spec under
  `automation/tests/ui/artifacts/` driving the framework's own `page`/`auth_state`
  fixtures with `-s` prints.

## Confirmed handles (as of ELITEA-1825 upload-path Cancel, 2026-08-21)

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| "Upload files to ..." modal — **Cancel** button | `artifacts-upload-path-cancel-button` (**Resolved/added during ELITEA-1825 implementation, 2026-08-21** — EliteaAI/EliteaUI@6d360e82 on `automation/testids`, attribute-only; page object: `ArtifactsPage.upload_path_cancel_button` / `click_upload_path_cancel_button()`) | `src/pages/Artifacts/component/UploadPathDialog.jsx`, `actions` fragment | The sibling Upload button already has `artifacts-upload-path-upload-button`; Cancel has nothing. Live enumeration of the dialog's buttons: `[('', None), ('Cancel', None), ('Upload', 'artifacts-upload-path-upload-button')]` — the first, unlabelled one is the modal's X control (also untagged). Attribute-only add, zero functional impact |
| Path field prefix raw text | `artifacts-upload-path-input` | same | raw `text_content()` is `'Path​{bucket}/​'` — MUI wraps the label + adornment with zero-width spaces; use `ArtifactsPage.get_upload_path_normalized_prefix()`, never a raw equality on `text_content()` |
| Upload-dialog description (no prefix / bucket root) | `artifacts-upload-path-description-text` | same | exact live wording at bucket root: `Files will be uploaded to the selected bucket. Optionally, enter a folder path to organize your files. Use "/" to create nested folder(s).` |

### Upload-path-dialog Cancel behaviours confirmed live (2026-08-21)
- **Cancel fires ZERO network requests** — capture on `"artifacts"` across the click and
  the modal close returned `[]`. Cancel aborts before any PUT, so "nothing uploaded" can be
  asserted positively, not only by absence in the table.
- **Cancel resets the dialog's own state**: `handleCancel` = `setFolderPath('') ; onClose()`.
  Typing `probe-folder` into the Path field, cancelling, and re-opening the dialog returns
  `typed=''`. Useful Axis-2 observable for any "discard" case on this modal.
- **No toast at all on Cancel** (`toast-message` count 0), and the file table is identical
  before and after a page reload — the reload is the cheap way to make the server the
  oracle rather than an un-refreshed client listing.
- **Escape ≠ Cancel for case fidelity.** `ArtifactsPage.close_upload_path_dialog()`
  (ELITEA-1824) presses Escape, which reaches the same `handleCancel` through MUI's
  `onClose`. Fine as a workaround/transit; NOT acceptable when a case's step literally says
  "Click Cancel" — that needs the button testid.
- `get_total_file_count_from_pagination()` (`artifacts_page.py:1792`) is a **raw-CSS**
  handle (`main *:has-text("of "):not(:has(*))`) — pre-existing tech debt. Prefer
  `get_pagination_info_text()` on `artifacts-pagination-page-info` (on `automation/testids`,
  not yet on `main`).
- Playwright MCP was NOT attempted this session — the digest's own gotcha (4 consecutive
  unreachable sessions) plus the `playwright.sync_api` scratch-script pattern worked first
  try: drop the script into `automation/tests/ui/artifacts/`, run it with the project
  pytest (the repo-root `/tmp` path fails — `pages` is not importable from there), delete
  it afterwards. One full case run cost ~69 s.

## Resolved/added during ELITEA-1825 implementation (2026-08-21, implementer slot)

- **`artifacts-upload-path-cancel-button` now exists** (EliteaAI/EliteaUI@6d360e82, on
  `automation/testids`; NOT yet on `main` — human cherry-pick pending). The digest row above
  is updated. Attribute-only on the pre-existing `Button.BaseBtn`; all three
  `add-data-testid` § 5.5 zero-functional-impact greps returned 0 hits.
- **New page-object members** on `ArtifactsPage` (all additive):
  `upload_path_cancel_button`, `click_upload_path_cancel_button()`,
  `wait_for_upload_path_dialog_closed()`, and `fill_upload_path(folder_path)` (types into
  `artifacts-upload-path-input-field`; the read-only prefix adornment is untouched).
- **Cancel's runtime behaviour, confirmed green:** clicking Cancel fires **zero** requests
  matching `artifacts`, closes the dialog, and resets the dialog's own folder-path state —
  re-opening the upload dialog shows an EMPTY editable Path segment even after
  `probe-folder` was typed before cancelling. The read-only prefix returns to
  `{bucket}/`.
- **`get_upload_path_normalized_prefix()` equals `f"{bucket}/"` exactly** at bucket root —
  a `contains` check is unnecessarily weak; the normalization already strips the MUI label
  and both zero-width spaces.
- **EliteaUI commits are hook-gated:** `commitlint` rejects any subject without an
  `[EL-XXXX]` ticket token — `[ELITEA-1825]` FAILS, `[EL-1825]` passes. `lint-staged`
  (eslint --fix + prettier) also runs on staged JSX.
- **Timing baseline:** the full ELITEA-1825 spec (bucket seed + upload dialog + cancel +
  reload + dialog reopen) runs in **~70 s** headless.

## Confirmed handles (as of ELITEA-1830/1833 duplicate Replace + X-close cluster, 2026-08-21)

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| "Resolve duplicates" modal — **Replace** button | `artifacts-resolve-duplicates-replace-button` | `DuplicateResolutionDialog.jsx` (EliteaAI/EliteaUI@918b8b22, `automation/testids`) | **Now exercised live (ELITEA-1830)** — retires the digest's earlier "not yet exercised by any case" caveat. Semantics confirmed: overwrites **in place** — exactly ONE `PUT /artifacts/s3/{bucket}/{name}?project_id=N` to the SAME key (no delete-then-create, no second key), then a `GET …&format=json` refetch. `LocatorDescriptor` field exists (`artifacts_page.py:384`); **no `click_…()` method yet** — add one mirroring `click_resolve_duplicates_keep_both_button()` |
| "Resolve duplicates" modal — **X (close)** icon | **testid needed**: `artifacts-resolve-duplicates-close-button` | `DuplicateResolutionDialog.jsx`'s `Modal.BaseModal` call | The X exists and is visible but carries **no** testid. Live button enumeration inside the dialog root: `[('', None, 'Close'), ('Cancel', 'artifacts-resolve-duplicates-cancel-button', None), ('Skip', …), ('Replace', …), ('Keep both', …)]` — the X is the first, label-less one (`aria-label="Close"`). `Modal.BaseModal` **already accepts** `closeButtonTestId` (`src/[fsd]/shared/ui/modal/BaseModal.jsx:35`, applied line 154); the dialog just never passes it. Prop-only add, zero functional impact |

### Duplicate-resolution behaviours confirmed live (2026-08-21)
- **Replace (ELITEA-1830):** one PUT to the original key → success toast
  `Your file(s) have been successfully uploaded!` → exactly one row remains
  (`list_bucket_files` len 1, no `- Copy` variant) → `lastModified` strictly newer
  (`17:40:37Z` → `17:41:10Z`), `size` `32 B` → `58 B`, content byte-equal to the uploaded
  bytes. Zero console errors.
- **X close (ELITEA-1833):** the X is wired to the SAME `onCancel` handler as the Cancel
  button (`DuplicateResolutionDialog.jsx` passes `onCancel` to both `Modal.BaseModal`'s
  `onClose` and the Cancel button's `onClick`). Live: **zero** `artifacts` requests from the
  click onward, dialog closes, **the parent "Upload files to …" dialog does NOT re-open**
  (count 0 — X dismisses the whole interaction, it does not step back), no toast, file count
  1 before and after a reload, `lastModified`/`size`/content all byte-identical.
- **Duplicate detection remains purely client-side** — 0 network requests between the
  Upload click and the modal, reconfirmed 3/3 runs this session.

### ⚠ Correction to an earlier digest-era claim: the "Last update" column DOES exist
Some older artifacts specs' prose (ELITEA-1831/1832 step text) says there is "no UI-visible
timestamp column" and reads timestamps only from the S3 JSON listing. **That is wrong and
already superseded** — `ArtifactTable.jsx:58-66` renders a `modified` column labelled
**"Last update"**, and it was read live this session straight off the row:
`'sample.txt\nText\n32 B\n21-08-2026, 08:40 PM'`. The correct current pattern is
`ArtifactsPage.get_file_row_text()` (`artifacts_page.py:1848`) + the regex/parse helper in the
merged `test_artifacts_file_preview_edit_save.py:71-97`. Two gotchas that come with it:
- **Minute granularity, local time.** Format is `dd-MM-yyyy, hh:mm a`
  (`ArtifactTable.jsx:50`); UTC `17:41:10Z` renders as `08:41 PM` at UTC+3. A write that
  lands in the same minute as its baseline renders an **identical string** — never assert
  `ui_after != ui_before` on a fast flow; assert the API `lastModified` delta and use the UI
  cell for a carries-it-through equality.
- **Width-gated** (`hideBelow: 900` on table width). It rendered at the framework default
  1366x768 this session, but the merged `test_artifacts_upload_path_cancel.py:86-88,153`
  documents clipping below ~1600 px and sets `set_viewport_size(1600x900)` — follow that.
- **No per-cell testid, and that is settled**: adding `dataCellTestIdPrefix` to
  `ArtifactTable` would tag all four data cells at once (single prefix prop) — a blanket add
  against the scope rule. Row-text + regex is the sanctioned read.

### Gotchas added this run
- `page.locator('[data-testid="artifacts-file-row"]').count()` read **0** immediately after
  `navigate_to_bucket()` while the row's `inner_text()` (auto-waiting) returned the full row
  — the list is still hydrating. **Use auto-waiting assertions / `expect(...)`, never a bare
  `.count()` right after navigation.**
- The file table is a **CSS-grid of divs**, not an HTML `<table>`: `table thead th` /
  `table tbody tr` match **nothing**. Probing scripts must target `artifacts-file-row` /
  `artifacts-file-list`.
- Playwright MCP again NOT attempted (7th consecutive session per the gotcha above) — the
  `playwright.sync_api`-style throwaway **pytest** spec dropped into
  `automation/tests/ui/artifacts/`, run with the project pytest and `-s` prints, worked first
  try. Both cases in one invocation cost **111 s**.

## Resolved/added during ELITEA-1830 + ELITEA-1833 implementation (implementer, 2026-08-21)

- **New testid — `artifacts-resolve-duplicates-close-button`** (the X in the "Resolve
  duplicates" dialog header). Added by passing the shared `Modal.BaseModal`'s
  already-existing `closeButtonTestId` prop from `DuplicateResolutionDialog.jsx`
  (EliteaAI/EliteaUI@bbb329c4, `automation/testids`; human cherry-pick to `main` pending).
  Prop-only — no new DOM node, no new hook, no removed line. That prop already has ~10
  merged consumers, so it is the sanctioned shape for ANY `BaseModal` X icon: pass
  `closeButtonTestId`, never wrap the header or add a node.
- **The Replace button is no longer un-exercised.** ELITEA-1830 clicks it and confirms the
  overwrite semantics the earlier digest row asked for: exactly **one** PUT, to the
  **original** key (`/artifacts/s3/{bucket}/sample.txt`), no delete-then-create and no
  `- Copy` key; the bucket keeps exactly one entry; `lastModified` is strictly newer and
  `size`/bytes are the replacement's. Page objects: `click_resolve_duplicates_replace_button()`
  and `click_resolve_duplicates_close_button()` now exist alongside Cancel/Skip/Keep-both.
- **`.click_resolve_duplicates_close_button()` and Cancel hit the same handler today.**
  `DuplicateResolutionDialog.jsx` passes one `onCancel` to both `BaseModal`'s `onClose`
  (X / backdrop / Escape) and the Cancel button's `onClick`. Live-confirmed identical
  outcome: dialog closes, **zero** network requests, no toast, original untouched — and the
  parent "Upload files to ..." dialog does **not** re-appear (the X does not fall back a step).
- **Reading the "Last update" cell right after a write races the table refetch.** New
  additive helper `ArtifactsPage.wait_for_file_row_to_contain_text(filename, text)` wraps
  an auto-retrying `expect(...).to_contain_text()` over the existing `ARTIFACT_FILE_ROW`
  class constant. Use it before `get_file_row_text()` whenever the value under assertion
  only lands after a backend round-trip. The Size cell's rendered form for sub-KB files is
  exactly `f"{bytes} B"` (`src/utils/filePreview.js` `formatFileSize`).
- **Dev-server staleness gotcha — cost one full red run.** After committing a NEW testid to
  `../EliteaUI` on `automation/testids`, the very next pytest run still saw a DOM without it
  (`Locator.click` timed out with only `- waiting for get_by_test_id(...)` in the call log —
  i.e. never attached), twice, including pytest-rerunfailures' own reruns. A `curl -s
  http://localhost:5173/src/<path-to-edited>.jsx | grep -c <testid>` afterwards showed the
  Vite dev server serving the edit correctly, and the identical spec then passed first try.
  **Before running a spec that depends on a testid you just added, curl the module off the
  dev server and confirm the string is there** — it is one cheap command against a ~60 s
  red run plus its reruns.

## Confirmed handles (as of ELITEA-1834 bucket-actions upload-to-subfolder, 2026-08-21)

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Bucket row 3-dot menu button | `bucket-menu-{bucket}-menu-button` (`ArtifactsPage.BUCKET_MENU_BUTTON`) | composed at runtime by `DotMenu.jsx:354` (`data-testid={id ? \`${id}-menu-button\` : undefined}`) | **invisible to a `data-testid`-literal grep** — the string never appears whole in source |
| Bucket menu "Upload files" item | `bucket-menu-upload-files-menuitem` | `BucketItem.jsx:153` supplies `key: 'bucket-menu-upload-files'`; `DotMenu.jsx:57` appends `-menuitem` | same grep blind spot |
| File / folder rows | `artifacts-file-row` / `artifacts-folder-row` inside `artifacts-file-list` | `ArtifactTable.jsx:521-526` (ternary, no `data-testid=` token on the value line) | same grep blind spot |
| Upload-dialog description at a SUBFOLDER | `artifacts-upload-path-description-text` | `UploadPathDialog.jsx:33-41` | wording differs from bucket root: `Files will be uploaded to "{bucket}/{prefix}". Optionally, enter a subfolder path (relative to current location). Leave empty to upload to the current folder.` — the root wording (generic, bucket-name-free, per #674) is the `!currentPrefix` branch |

### Bucket-actions upload behaviours confirmed live (2026-08-21, ELITEA-1834)
- **The bucket 3-dot menu's "Upload files" targets the CURRENT SELECTION, not the bucket
  root.** With subfolder `a1` selected in the tree, the dialog pre-fills `{bucket}/a1/`, the
  PUT goes to `/artifacts/s3/{bucket}/a1/sample.txt` (200), the view stays on `{bucket} > a1`
  and the root listing keeps showing only the `a1` folder row. Mechanism: `Artifacts.jsx:95`'s
  single `currentPrefix` state; `BucketItem.jsx:96` `handleUploadClick` never resets it;
  `UploadPathDialog.jsx:94` renders `{bucket}/{currentPrefix}`.
- ⚠ **Two TMS cases contradict here.** ELITEA-1834 calls that behaviour CORRECT; ELITEA-1824
  (→ open bug **#649**, soft-asserted in
  `test_artifacts_upload_three_options_verify_selection.py`) calls the identical state a
  defect. Filed **#1629** (`question` + `case-text-drift`) for a human ruling. Anyone touching
  either spec should read #1629 first rather than "fixing" one to match the other.
- **Tree selection is exclusive:** selecting `a1/` flips the bucket row's own
  `data-selected` to `false`; `is_tree_item_selected("a1/")` is the highlight oracle.
- **Coming back to root from inside a subfolder is one `click_bucket_row()`** — it both
  navigates to root and leaves the tree expanded (no toggle-collapse observed on this path;
  the #651 toggle caveat still applies when the bucket is ALREADY the active root selection,
  so guard with `is_tree_item_visible("a1/")` + conditional second click).
- **Seeding a subfolder for a test:** empty-state upload + `fill_upload_path("a1")`. Use a
  seed filename ≠ the case's own upload file, or the "Resolve duplicates" dialog fires and
  derails the upload-path dialog assertions.
- ⚠ **The closure-record two-stage testid grep produces FALSE "not on main" rows** for
  runtime-composed and ternary/`key:`-wired testids (three of them in this case's set —
  table above). Read the `git grep` hits rather than filtering them when a handle you have
  *used live* reports absent.
- Playwright MCP again NOT attempted (8th consecutive session per the digest gotcha); one
  throwaway pytest spec in `automation/tests/ui/artifacts/` ran the whole 18-step case in
  **34 s**, zero console errors.

## Resolved/confirmed during ELITEA-1834 implementation (test-automation-engineer, 2026-08-21)

- **Every handle in ELITEA-1834's AFS held exactly as documented** — the whole
  bucket-menu → upload-path-dialog → subfolder-listing flow ran green on the
  first attempt with **zero page-object changes**. `click_bucket_row`,
  `is_bucket_selected`, `click_tree_item`, `is_tree_item_selected`,
  `is_tree_item_visible`, `hover_bucket_row`, `open_bucket_menu`,
  `click_bucket_menu_upload_files_item`, `wait_for_upload_path_dialog`,
  `get_upload_path_normalized_prefix`, `get_upload_path_typed_value`,
  `get_upload_path_description_text`,
  `click_upload_path_upload_button_and_capture_response`, the breadcrumb
  getters, `wait_for_file_count`, `get_file_names`, `get_file_row_text` all
  cover this surface end-to-end today.
- **The bucket-actions "Upload files" entry point is now asserted BOTH ways in
  the merged suite — this is deliberate, not a duplication to collapse.**
  `test_artifacts_upload_to_selected_subfolder.py` (ELITEA-1834) hard-asserts
  the dialog prefix `{bucket}/a1/` as CORRECT while `a1` is selected;
  `test_artifacts_upload_three_options_verify_selection.py` (ELITEA-1824)
  soft-asserts the opposite (`{bucket}/`) as KNOWN DEFECT #649 at the same DOM
  node. One `currentPrefix` machine state, two case texts with opposite
  expectations — filed for a human ruling as CLARIFICATION #1629. Whoever
  resolves #1629 must touch BOTH specs; do not "align" one to the other before
  that ruling lands.
- **`artifacts` is NOT a registered pytest marker** (`automation/pytest.ini`) —
  no artifacts spec uses one. Feature scoping is by directory
  (`tests/ui/artifacts/`); the marker set for a new artifacts spec is
  `ui, regression, p<pri>, new`.
- **`a1/`-seeding gotcha reconfirmed:** the seed file must NOT be named
  `sample.txt` when `sample.txt` is the case's own upload subject — the second
  upload would raise the "Resolve duplicates" dialog instead of the
  "Upload files to ..." dialog. `seed.txt` used here.

## Confirmed handles (as of ELITEA-1836/1837/1838 file-tree cluster, 2026-08-21)

Left-panel **file-tree behaviour** — subfolder expand/collapse, breadcrumb + URL
navigation, and bucket switching. **No testid was added this run** — every
element these three cases touch already carries one.

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Tree node (folder or file) | `artifacts-tree-item-{key}` (`ArtifactsPage.ARTIFACTS_TREE_ITEM`) | `Components/FileTreeItem.jsx:107` | key = the item's FULL relative key: a folder is `a1/` (trailing slash), a nested file is `a1/f1.txt`. Keys are bucket-relative, so two buckets with same-named files produce colliding keys — give seeded buckets distinct filenames |
| Tree node selection | `data-selected="true\|false"` on the same node | same | `is_tree_item_selected()`; selection is EXCLUSIVE — selecting `a1/` flips the bucket row's own `data-selected` to `false` |
| "Bucket is expanded" observable | the bucket's own tree nodes exist at all | `SimpleBucketList.jsx:89` renders `{isExpanded && <BucketContent …>}` | there is NO `data-expanded` on the bucket row and none is needed — a collapsed bucket has ZERO tree nodes in the DOM |
| "Subfolder is expanded" observable | the folder's CHILD tree nodes exist | `FileTreeItem.jsx`'s `<Collapse in={isExpanded} unmountOnExit>` | children unmount ~300 ms after the collapse click (MUI transition) — assert with `to_have_count(0)`, never a fixed sleep |
| Breadcrumb bucket crumb (clickable root link) | `artifacts-breadcrumb-bucket-label` + `ArtifactsPage.click_breadcrumb_bucket_label()` (**added during this run's implementation**) | `component/ArtifactTableToolbar.jsx:65` | `onClick` is wired **only while `currentPrefix` is truthy** — at bucket root the crumb is inert (not a bug) |

### File-tree behaviours confirmed live (2026-08-21)
- **Subfolder click toggles expansion AND (re)selects the folder.**
  `FileTreeItem.handleSelect` does `setIsExpanded(prev => !prev)` **and** calls
  `onSelectFolder(item.key)` on BOTH clicks. Consequence: collapsing a subfolder
  does **not** reset the breadcrumb or the URL — after the collapse click the
  header still reads `bucket > a1`, the URL still carries `&folder=a1`, and the
  main panel still lists the subfolder's files. Only the tree branch closes.
- **⚠ A collapse click fired during the expand ANIMATION is lost — permanently
  (product defect `#1631`).** Mechanism, pinned down during the ELITEA-1836
  implementation: the click interrupts MUI `Collapse`'s ~300 ms **enter**
  transition, `onExited` never fires, and `unmountOnExit` therefore never
  unmounts the children — the folder stays open for good, not just for a moment.
  **No network request is involved** (request capture across the window: empty),
  so the earlier "`isFetching` remount" hypothesis recorded on first analysis was
  **wrong**; corrected here and on the issue.
  Measured: **3/3 failures** with the collapse click inside the transition
  window, **18/18 successes** once it had finished (plus 12/12 in two earlier
  probes; a 200 ms gap is borderline, 500 ms+ reliable).
  **Rule for any tree test: never fire two tree clicks back-to-back — wait for
  the subtree to stop moving** with
  `ArtifactsPage.wait_for_tree_item_stable("<last child key>")` (added with
  ELITEA-1836; polled geometry, same shape as
  `wait_until_bucket_row_within_panel`, no sleep).
- **URL shapes:** bucket root `?bucket=<name>`; inside a subfolder
  `?bucket=<name>&folder=a1` — the `folder` param carries **no** trailing slash
  even though the prefix and the tree key do (`Artifacts.jsx`:
  `normalizedPrefix.replace(/\/$/, '')`). Assert anchored, not by substring: a
  stale `&folder=…` survives a `"bucket=<name>" in url` check.
- **Breadcrumb-root click returns to root without collapsing the tree** — the
  `a1/` subtree stays rendered; only `data-selected` clears and `currentPrefix`
  resets.
- **Switching buckets never collapses the previous one.** Expansion lives in
  `BucketsListContent.jsx`'s `expandedBuckets` map, only ever set `true` for the
  newly selected bucket and toggled solely by clicking an ALREADY-active row
  (the `#651` behaviour). Live: bucket A's tree nodes stayed visible with
  `data-selected="false"` while B was selected.
- **Returning to a bucket restores the BUCKET's expansion but not a subfolder's**
  — `BucketContent` remounts and `FileTreeItem` re-initialises from
  `expandedPaths`, empty once the bucket click reset `currentPrefix`. Not a
  regression; not asserted by any of these three cases.
- **`/artifacts` auto-selects the alphabetically-first bucket** on a param-less
  load — measured live as never an `autotest-…` one, but every spec here asserts
  `is_bucket_selected(bucket) is False` before its first bucket click so the
  `#651` toggle trap can never be entered silently.
- **Two-bucket seeding pattern (ELITEA-1838):** take bucket A from the
  `artifact_bucket` fixture and create B as `f"{A}-b"` via
  `ArtifactAPI.create_bucket` with its own try/except teardown — `{A}-b` sorts
  immediately after A in the alphanumeric list, so both rows land in the same
  scroll band of a 760-bucket panel.
- **Page-object additions this run:** `click_breadcrumb_bucket_label()` (clicks
  the `artifacts-breadcrumb-bucket-label` crumb → back to bucket root) and
  `wait_for_tree_item_stable(item_key)` (the expand-animation settle wait above).
- Playwright MCP again NOT attempted (9th consecutive session per the digest
  gotcha) — all three cases were executed live via throwaway pytest specs under
  `automation/tests/ui/artifacts/` driving the framework's `page`/`auth_state`
  fixtures with `-s` prints (4 probe runs, 38-64 s each), then deleted.

## ZIP-download progress dialog — CANCEL flow (ELITEA-1842 / ELITEA-1843, 2026-08-21)

First session to actually CLICK the progress dialog's controls (ELITEA-1840/1841 asserted the
Cancel button's visibility only and declared the flow out of scope).

| Element | Handle | Notes |
|---|---|---|
| Dialog **X (close)** button | `artifacts-zip-download-progress-close-button` (**added during ELITEA-1843 implementation, 2026-08-21** — EliteaAI/EliteaUI@b93c631b on `automation/testids`) | Prop-only add: `ZipDownloadProgressDialog.jsx` now passes `closeButtonTestId` to `BaseModal`, which already accepted and applied it (`BaseModal.jsx:35,154`). No new DOM node, no hook, no removal. Page object: `ArtifactsPage.zip_download_progress_close_button` / `click_zip_download_close_button()` |
| Dialog **Cancel** button | `artifacts-zip-download-progress-cancel-button` | pre-existing (ELITEA-1840); page object: `click_zip_download_cancel_button()` |

**Cancel behaviours confirmed live (both controls, 2026-08-21):**
- **X and Cancel are the SAME handler.** `ZipDownloadProgressDialog.jsx` passes one `onCancel`
  to both `BaseModal`'s `onClose` (X / backdrop / Escape) and the Cancel button's `onClick` —
  the same shape `DuplicateResolutionDialog` uses (ELITEA-1832/1833).
- **Order of effects:** the dialog unmounts **synchronously** on click (`cancelZipDownload`
  sets `isOpen:false`), while the `Download cancelled` toast (`toast-message`, `toastInfo`)
  arrives only once the aborted in-flight `fetch` rejects with `AbortError` and
  `downloadArtifactsAsZip` maps it to `onCancel()`. Live: toast first seen ~2.0-2.1 s after the
  click **in the instrumented run** (inflated by a 1500 ms pre-fetch delay wrapper). Never assert
  dialog-hidden and toast-visible as one expectation; give the toast a generous timeout.
- **No ZIP is ever saved after a cancel** — `downloadArtifactsAsZip` only creates the blob +
  `anchor.download` AFTER the whole per-file loop completes, so an abort mid-loop cannot produce
  one. Live-instrumented `HTMLAnchorElement.prototype.click` capture: `[]` in both runs.
- **Selection + table are untouched** by cancel (selection lives in `ArtifactTable` state):
  4-of-4 and 3-of-3 checkboxes still `Mui-checked`, all 4 rows still listed, 0 console errors.
- **Making "in progress" observable:** with small files the whole flow finishes in <2 s. Use
  `page.route("**/artifact/default/**")` + a delayed `route.continue_()` (1000-1500 ms), poll the
  counter until `1 of N files`, then click. This is timing control, not substitution
  (`.agents/testing.md` § Fidelity policy) — same technique ELITEA-1841 ships.
- **`aria-valuenow` at `1 of N`:** `25` for N=4, `33` for N=3 (integer `current/total*100`).
  A `0 of N files` / `valuenow="0"` precursor frame precedes the first completion, and the
  current-file label is absent until the first file is in flight.

**Gotcha — Vite does NOT pick up EliteaUI edits on this OneDrive checkout (2026-08-21).** After
committing a testid, the dev server kept serving the STALE transform: a plain
`curl http://localhost:5173/src/.../X.jsx` showed no change (a `?t=<ts>` cache-buster showed the
new code), and a full browser reload still rendered the old component. `touch` did not help — the
file watcher never fires on OneDrive-backed paths. **Restart the dev server** (`kill` the vite pid,
`npm run dev`) after any EliteaUI edit, and verify with
`curl -s http://localhost:5173/src/<path> | grep -c <testid>` before blaming the JSX.

## Confirmed handles (as of ELITEA-1844/1845 cluster, 2026-08-22)

Row-level **single-file delete via the actions dropdown** — a third, distinct
delete path alongside ELITEA-1847's bulk checkbox+toolbar delete and
ELITEA-1856's file-preview-editor delete.

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Dropdown `Delete` item (row) | `artifacts-file-delete-menuitem` | `ArtifactRowActions.jsx` | **Now clicked live (ELITEA-1844)** — retires ELITEA-1839's "visibility-only, never clicked" caveat. Opens the shared `DeleteEntityModal` via `DotMenu`'s `ActionWithDialog`. |
| Confirmation message (row delete) | `delete-confirm-message` → `"Are you sure to delete the {name}? It can't be restored."` | `DeleteEntityModal.jsx` (`textContent` default `'Are you sure to delete the '` + `ArtifactRowActions.jsx`'s `inlineExtraContent: "? It can't be restored."`) | note the **"the"** — the cases' own text drops it (CLARIFICATION #1638, sibling of #659/#664). Distinct from the bulk path's `"Are you sure to delete the selected files?"`. |
| Emphasised entity name in the message | `delete-confirm-entity-name` | **added 2026-08-22**, EliteaAI/EliteaUI@e59d0c97 (`automation/testids`) | the "highlighted in blue" span (`palette.text.deleteAlertEntityName`); attribute-only add on an existing `<Typography component="span">`. Colour itself is not testid-assertable — assert this element's text. |
| Modal X (close) icon | `delete-confirm-close-button` | **added 2026-08-22**, EliteaAI/EliteaUI@08d9bb4f (`automation/testids`) | prop-only: `DeleteEntityModal` now forwards `closeButtonTestId` to `Modal.BaseModal` (which already accepted it, `BaseModal.jsx:35,154`). `showCloseButton` defaults `true`, so the X was always rendered — it just had `data-testid={undefined}`. |
| Modal `Cancel` button | `delete-confirm-cancel-button` | `DeleteEntityModal.jsx:103` | **on `origin/main`** (EliteaAI/EliteaUI@bf4a13ad). This CORRECTS the standing note at `artifacts_page.py` (ELITEA-1847 block) claiming Cancel "carries no testid, confirmed absent" — stale since the 2026-08-12 promotion. First driven live by ELITEA-1845. |
| Single-file DELETE endpoint | `DELETE /api/v2/artifacts/artifact/default/{projectId}/{bucket}?filename={name}` | `src/api/artifacts.js:125` (`deleteArtifact`) | **SINGULAR** — `ArtifactsPage.confirm_delete()`'s `expect_response` matcher (`"artifacts/artifacts" in r.url`) does NOT match it. ELITEA-1844 adds the additive sibling `confirm_delete_single_artifact()`. A *folder* row's dropdown delete would still take the plural path (`ArtifactTable.jsx:347-370`). |
| Single-file delete success toast | `"The {name} file has been successfully deleted."` | `ArtifactTable.jsx:433` | third distinct wording on this surface: bulk = `"The selected files have been successfully deleted."`, editor = `"File deleted successfully"`. Cases' `"The artifacts have been deleted successfully"` exists nowhere in source (#1638). |
| Post-delete settle | `wait_for_file_count(n)` then read | — | `deleteArtifact` invalidates `TAG_ARTIFACTS` + `TAG_BUCKETS`; the table and the left tree refetch asynchronously. Live-confirmed: tree item for the deleted file disappears, sibling `sample - Copy.md` stays. |

**Vite HMR missed a `src/` edit this session (2026-08-22).** Two testids committed on
`automation/testids` were served WITHOUT the change (`curl` of the transformed module showed the
old text, and both locators resolved to count=0) until `npm run dev` was killed and restarted.
Under OneDrive the file watcher is not reliable — if a freshly added testid resolves to 0 elements,
`curl -s "http://localhost:5173/src/<path>" | grep <testid>` first, and restart the dev server
before doubting the JSX edit.

## Bulk delete — SELECT-ALL branch + modal dismissal (ELITEA-1848 / 1849 / 1850, 2026-08-22)

First session to click the header **select-all** checkbox and the delete modal's **X**. Everything
below was observed live in one clean run (3 flows, 0 console errors, first attempt).

| Element / fact | Value | Notes |
|---|---|---|
| Header select-all checkbox | `artifacts-select-all-checkbox` → `click_select_all_checkbox()` | on-main ✓. First test to actually CLICK it (ELITEA-1841/1846 only read its state). All 4 rows — folders included — become checked; header goes `Mui-checked`, `indeterminate` False. |
| Toolbar tooltip, all rows selected | **`Delete all files`** | `ArtifactTableToolbar.jsx:157` — `Delete ${rowSelectionModel.length === totalRows ? 'all files' : 'selected files'}`. Read off the wrapper's `aria-label`, no hover. |
| Modal message, all rows selected | **`Are you sure to delete the all files?`** | `name='all files'` + `DeleteEntityModal`'s fixed prefix `'Are you sure to delete the '` ⇒ ungrammatical. Cases say `Are you sure to delete all files?`. CLARIFICATION #1640 (sibling of #659). `delete-confirm-entity-name` = `all files`. |
| Bulk-delete success toast | `The selected files have been successfully deleted.` | `ArtifactTable.jsx:431` — **same string whether the selection is partial or complete**; there is no "all files" toast variant. Cases' `The artifacts have been deleted successfully` exists nowhere in source (exact dup of #660, commented not re-filed). |
| DELETE on a full selection | `DELETE …/artifacts/artifacts/default/{project}/{bucket}?fname[]=…` → 200, `fname[]` = the 4 **expanded** storage keys | folders expand to their underlying files (`a1/file1.txt`, `folder-a/placeholder.txt`), never a bare `a1/` prefix — same expansion ELITEA-1847 proved for a single folder. |
| Emptied-bucket state | right panel `artifacts-empty-state` = `No files in this bucket`; left tree `artifacts-bucket-tree-empty-label-{bucket}` = same text; bucket row still listed; `list_bucket_files()` = `[]` | both panels carry the identical string (`ArtifactTable.jsx:504`, `BucketContent.jsx:89`). Deleting every file does NOT delete the bucket. |
| Modal X (close) | `delete-confirm-close-button` → **`click_delete_close_button()` added by ELITEA-1850** | first time DRIVEN (ELITEA-1844 only asserted presence). Same single `onClose` handler as Cancel (`DeleteEntityModal` passes one to both `BaseModal.onClose` and the Cancel button). |
| Dismissal (Cancel **or** X) side-effects | **none** | zero DELETE requests captured, zero `toast-message` elements over a 3 s window, all rows + pagination + tree unchanged, storage listing intact — and **the selection is RETAINED**: all 4 checkboxes still checked after Cancel; the 2-of-4 partial selection still checked (header still indeterminate) after X. Selection lives in `ArtifactTable`'s `rowSelectionModel`, which the modal never touches. |

**Absence-assertion idiom for this surface (reviewer finding on ELITEA-1845):** assert "no toast" by
waiting for it to APPEAR and requiring the wait to time out —
`pytest.raises(PlaywrightTimeoutError)` around `success_toast_message.wait_for(state="visible",
timeout=3000)`. `to_have_count(0)` is true at the first poll and cannot see a toast that renders
300 ms later. The detector is proven inside the same spec file by ELITEA-1848, which asserts the
same locator carries text after a real delete.

**Testid promotability for this cluster:** no new testid was needed, but FOUR of the ones these
specs reference are on `automation/testids` only — `delete-confirm-title-icon` (EliteaAI/EliteaUI@7b359d32),
`delete-confirm-entity-name` (EliteaAI/EliteaUI@e59d0c97), `delete-confirm-close-button`
(EliteaAI/EliteaUI@08d9bb4f) and the runtime-composed `artifacts-bucket-tree-empty-label-*`
(`BucketContent.jsx:87`, invisible to a bare-substring grep of `main`). Verified 2026-08-22 with a
fresh `git fetch origin` + the two-stage `-i`/`[:=]` grep on both refs.

**`get_file_row_text()` is FILE-row-only (ELITEA-1849/1850, 2026-08-22).** It is anchored on
`artifacts-file-row`; a folder row renders as `artifacts-folder-row`, so calling it with `a1` /
`folder-a` times out at 10 s (cost one rerun on this cluster). Folders also carry no Type/Size
metadata to snapshot — assert their presence via `get_file_names()` and the left-panel tree instead.

---

## Confirmed handles (as of ELITEA-1810 retention edit/persistence, 2026-08-23)

| Element | Handle | Method / constant | Notes |
|---|---|---|---|
| New-Bucket / Edit-bucket Cancel button | `artifacts-bucket-cancel-button` | *(no page-object field yet)* | `CreateBucket.jsx:307`; `onCancel = navigate(-1)` — no request fires |
| Retention measure options | `select-option-days` / `-weeks` / `-months` / `-years` | `BasePage.SELECT_OPTION.format(m)` | shared `SingleSelect` popover; only one select open at a time |
| Bucket dot-menu **Rename** item | `bucket-menu-rename-menuitem` | *(no page-object method yet)* | derived from `BucketItem.jsx:165` key via `DotMenu.jsx:58`; opens the SAME `/artifacts/create-bucket` route in edit mode (form heading text `Edit bucket`) |
| Bucket-edit save | `artifacts-bucket-save-button` | ⚠ existing `click_bucket_save_button()` waits for a **POST** | an edit save is a **PUT** `/artifacts/buckets/default/{project_id}` (`src/api/artifacts.js:55`) — the existing method hangs on edits |
| Delete-confirm dialog | `delete-confirm-title` / `-message` / `-entity-name` / `-cancel-button` / `delete-confirm-button` / `delete-confirm-close-button` | | full inventory read live |

### Retention-policy behaviours confirmed live (2026-08-23)

- Create form defaults: name `new-bucket`, measure `Years`, value `1`.
- Both retention fields are pre-populated — **select-all before typing** or values
  concatenate (`1` + `10` → `110`).
- Measure is a MUI Select: read `textContent`. Value is a real `<input type="number">`:
  read `input_value()`.
- Save (create) → `POST …/artifacts/buckets/default/{pid}` 200, then auto-navigates to
  `/artifacts?bucket=<name>` and auto-selects the new bucket (`PENDING_BUCKET_SESSION_KEY`).
- Save (edit) → `PUT` same URL, 200, then `/artifacts?bucket=<name>`.
- **Cancel fires NO request** (verified with a request listener) and does not change
  `retentionDays`.
- Bucket list is alphabetically sorted; a created bucket keeps its index across an edit.
- **No toast fires on bucket save** — the response status is the only honest oracle.
- Backend stores retention as `retentionDays` (readable via
  `GET /artifacts/s3/?project_id={id}&format=json`): `20 Weeks`→140, `10 Months`→304,
  `3 Months`→92. Useful independent tie-breaker for a stale-looking UI read.

### `#1677` — Months retention never round-trips (filed 2026-08-23)

A bucket saved with **Months** reopens as **Days** (`10 Months`→`304 Days`,
`3 Months`→`92 Days`). Backend stores calendar-accurate days;
`convertDaysToMeasure()` (`src/utils/retentionPolicy.js`) needs `days % 30 === 0` to
reconstruct months, which a real month count never satisfies. Weeks (×7) and Years (×365)
round-trip fine. Deterministic — any case asserting a Months policy after a reopen is
sanctioned-RED against #1677.

### Gotchas added this run

- **NEVER poll with a busy `while` loop inside `browser_evaluate` / `page.evaluate`.**
  A JS spin-loop blocks the main thread, so React cannot render the ~967-row bucket list
  and the poll reads `0 rows` until it times out — this produced a false "the bucket list
  never loads / shows *No buckets created yet*" reading twice (~65 s wasted). Use
  Playwright waits (`expect(...).to_have_count`, `locator.wait_for`), which yield.
- The bucket-list **empty state** (`No buckets created yet`) renders transiently while the
  list is still loading — never assert emptiness without a settled-list wait.
- `bucket-menu-{name}-menu-button` is in the DOM but **invisible until the row is
  hovered**; a direct click fails with *"element is not visible"*.
- There is exactly **ONE** bucket-creation entry point in the product
  (`artifacts-create-bucket-button`, a `NewFolder` icon in `BucketHeader.jsx:59`) —
  TMS cases describing a "Path 1 button" vs a "Path 2 folder icon" (ELITEA-1808 vs
  ELITEA-1810) both land on it.
- `#636` ("bucket delete 404s silently, buckets never removed") did **not** reproduce via
  the **UI** delete path today: row hover → dot-menu `Delete` → `delete-confirm-button`
  removed the bucket from the S3 listing immediately. Usable teardown fallback.
- Project 399 held **967 buckets** at run time, including leaked `autotest-*` names from
  earlier runs (e.g. `autotest-1810-b2-2251`) — always generate unique bucket names.

### Resolved/added during ELITEA-1810 implementation (2026-08-23, implementer)

- **Testids added and PUSHED** — EliteaAI/EliteaUI@c91c2aac on `automation/testids`
  (3 attribute-only lines, 0 removals, no hooks, no new DOM nodes):
  `key: 'bucket-menu-rename'` on `BucketItem.jsx`'s Rename item (DotMenu derives
  `bucket-menu-rename-menuitem`), `data-testid="artifacts-bucket-cancel-button"`, and
  the new `data-testid="artifacts-bucket-form-heading"` on `CreateBucket.jsx`'s heading
  Typography. **Caution for future analysis on this surface:** the first two were
  present only as *uncommitted* edits in the `../EliteaUI` working tree at analysis
  time, so a plain grep reported them as "exists" while they lived on no branch. Verify
  a testid's provenance with `git grep <t> origin/automation/testids -- src/`, not with
  a working-tree grep.
- **`artifacts-bucket-form-heading` is the only observable separating the create form
  from the edit form.** `/artifacts/create-bucket` is ONE route serving both;
  `CreateBucket.jsx` renders `currentBucket ? 'Edit bucket' : 'New Bucket'`. One stable
  testid, state read from the TEXT.
  **Consequence for every artifacts case whose step reads "the New Bucket form opens"
  (added during ELITEA-1812/1816 review round 1, 2026-08-23):** a `"/artifacts/create-bucket"
  in page.url` assertion does NOT verify that expected result — a regression that opened the
  EDIT form on the same route would pass it. Assert
  `get_bucket_form_heading_text() == "New Bucket"` alongside the URL. Both ELITEA-1812's and
  ELITEA-1816's specs now do this at their Step 2.
- **The retention-measure Select's own MUI backdrop blocks a second combobox click.**
  Opening the dropdown mounts an invisible `MuiBackdrop` for `menu-expiration_measure`
  that sits over the combobox — so "open the dropdown, then select an option" as two
  separate page-object calls times out on `Locator.click`. `select_retention_measure()`
  now only issues the open-click when `aria-expanded != "true"`, and waits for the
  option to reach `hidden` before returning so the closing backdrop cannot race the
  caller's next click.
- **The bucket-list refetch needs well over 15 s in project 399 (~970 buckets).** The
  15 s `NAVIGATION_TIMEOUT` the sibling artifacts specs use produced a false "bucket
  never appeared" right after the create-save; a fresh `navigate_to_artifacts()`
  showed it instantly. ELITEA-1810 uses a dedicated `BUCKET_LIST_TIMEOUT = 45_000`
  for every bucket-list condition wait. Expect the sibling specs to start flaking on
  this as the project's bucket count grows.
- **An EDIT save is a `PUT`, not a `POST`.** `ArtifactsPage.click_bucket_save_button()`
  hardcodes `method == "POST"` in its `expect_response` predicate and HANGS on an edit
  save — use the new additive sibling `click_bucket_save_button_expect_put()`.
- **Cancel fires no bucket request at all** (`onCancel` is a plain `navigate(-1)`) —
  confirmed by a `capture_requests_matching("artifacts/buckets", method="PUT")`
  listener armed before the form is touched: zero captured across the whole
  select-Days / set-1 / Cancel sequence.
- **#636 re-confirmed both ways:** `ArtifactAPI.delete_bucket()` 404s every time
  (`.../buckets/default/399/p--399.<name>`), while the UI delete path removes the
  bucket cleanly — provided the removal wait gets `BUCKET_LIST_TIMEOUT`, not 15 s.

## Confirmed handles + behaviours (ELITEA-1812/1816 cluster, 2026-08-23)

Bucket **name case-handling** and the **Edit-bucket form's read-only Name field**.
**Zero new testids were needed** for either case — every handle already existed.

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Bucket name input | `artifacts-bucket-name-input` | `fill_bucket_name()` | **Enabled in Create mode, `disabled` in Edit mode** — `CreateBucket.jsx:238` renders `disabled={!!currentBucket}`. It is a real `disabled` attribute (`get_attribute("disabled") == ""`), **not** `readOnly` (`readonly` is `None`). A `click()` on it in Edit mode raises Playwright `TimeoutError` ("not enabled"); the deprecated `Locator.type()` does **not** raise, it silently no-ops — so *value-unchanged* is the assertion that proves "no input accepted", never `type()`'s outcome. |
| Inline name-validation helper text | `artifacts-bucket-name-helper-text` | `CreateBucket.jsx:244` (`FormHelperTextProps`) | **CORRECTS the 2026-08-02 digest row above**, which says "testid needed / not yet added" — it exists now and is on `origin/main`. |
| Form heading (New Bucket / Edit bucket) | `artifacts-bucket-form-heading` | `get_bucket_form_heading_text()` | text is `New Bucket` on create, **`Edit bucket`** on edit — same route `/artifacts/create-bucket` for both, so the URL alone never tells you which mode you are in |
| Bucket dot-menu item order | `Upload files` · **`Rename`** · `Pin to top` · `Delete` | `BucketItem.jsx:153-205` | `get_bucket_menu_items_text()` returns them concatenated with no separator: `"Upload filesRenamePin to topDelete"`. Case texts saying "Edit" (and a different order) are tracked drift — `EliteaAI/elitea-testing-public#666` |

### Bucket-name case conversion is a BACKEND behaviour (confirmed live)
Typing `AUTOTEST-1812-182449` (or mixed `AuToTest-1816-182606`) into the New Bucket form:
- the input **preserves the typed case verbatim** — there is **no `toLowerCase()` anywhere
  in `src/pages/Artifacts/CreateBucket.jsx`**, and the yup schema `^[a-zA-Z][a-zA-Z0-9-]*$`
  explicitly *permits* uppercase (so this is not a validation rejection);
- the form posts `values.name.trim()` unchanged to
  `POST /api/v2/artifacts/buckets/default/{project_id}` (note: **v2**, not v1);
- the **response body** comes back lowercased —
  `{"message":"Created","id":"p--399.autotest-1812-182449","name":"autotest-1812-182449"}`.
  That body is the honest oracle for the "**stored** lowercase" half of the claim; the DOM
  alone can only prove "**displayed** lowercase".
- The bucket row testid is derived from the stored name
  (`data-testid={\`artifacts-bucket-row-${name}\`}`, `BucketItem.jsx:243`), so
  `artifacts-bucket-row-{lower}` present + `artifacts-bucket-row-{TYPED}` count 0 is a
  two-sided name assertion.

### Retention `Days / 1` round-trips cleanly
Create with `Days`/`1` → reopen the Edit form → `Days`/`1` (hard-asserted, passed). Defect
`#1677` (a `Months` policy reopening as `Days`) only bites units whose day-count is not
divisible by 30 — **use `Days` or `Weeks` for any retention step that is incidental to the
case**, so an unrelated red never leaks in.

### Gotchas added this run
- **Cold-session `networkidle`**: the *first* `/artifacts` navigation of a fresh browser
  session exceeded `wait_for_page_load()`'s default 15 s once (45 s was comfortable).
  Subsequent navigations in the same session were fine. Raise that one call's timeout;
  it is not a product issue.
- Project 399's bucket leak (`#636`) keeps growing — this run added 2 more
  (`autotest-1812-182449`, `autotest-1816-182606`).
- Playwright MCP was **not** attempted this session — went straight to a
  `playwright.sync_api` scratch script driving `ArtifactsPage` (per the 5-consecutive-session
  history in the gotchas above). It worked first try; that remains the cheap default here.

### Resolved/added during ELITEA-1812 + ELITEA-1816 implementation (2026-08-23, implementer)
- **A bucket save lands on the BARE `/artifacts` root — there is no `?bucket=<name>`
  param.** ELITEA-1812's AFS expected the create form's `PENDING_BUCKET_SESSION_KEY`
  auto-select to show up as a `?bucket=` query param; an auto-retrying `to_have_url`
  polled 87 times over 45 s and every sample was plain `http://localhost:5173/artifacts`
  (project 399, ~970 buckets). Assert the ROUTE after a bucket save, never the param.
  (Contrast: the file-preview flow *does* set `?bucket=&file=` — see the URL-query row
  above. The two are different navigations.)
- **`sidebar_menu_item("artifacts").click()` verified live** as the case-faithful way to
  return to the Artifacts root (ELITEA-1812 step 5) — testid
  `sidebar-menu-item-artifacts`, still `automation/testids`-only.
- **The bucket-form Name field is `disabled`, never `readonly`** (`CreateBucket.jsx`:
  `disabled={!!currentBucket}`). A `click()` on it in Edit mode is REFUSED by Playwright's
  actionability check (assert with a SHORT ~3 s budget inside `pytest.raises`), while
  `Locator.type()`/`press()` do **not** raise — they silently do nothing. So the only
  assertion that proves "no input accepted" is the unchanged `input_value()`.
  New page-object accessors: `is_bucket_name_input_disabled()` /
  `is_bucket_name_input_editable()`.
- **`ArtifactsPage.delete_bucket_via_menu(name)` now exists** — the UI bucket-teardown
  composition (navigate → wait for row → dot-menu → Delete → confirm → wait for removal),
  lifted to the page object at its third repetition. Use it for teardown instead of
  copying the local helper again. ELITEA-1810's suite-local copy is deliberately left in
  place (that spec is sanctioned-RED on `#1677`).
- Both new specs delete their own bucket at teardown (UI path, API fallback), so this run
  added **no** new leak to `#636`.
