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
| Row locator for assertions | `ArtifactsPage.bucket_row(name) -> Locator` | added this run | specs may not build locators (`.agents/testing.md` § Locator policy); this accessor is how a spec gets the row for `to_have_css` |

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
