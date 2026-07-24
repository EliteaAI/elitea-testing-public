# Artifacts surface — exploration digest

Handle cache for analysts/implementers working the Artifacts area
(`test-specs/artifacts/`). Confirmed via live exploration, most recently during
GAP-035 (2026-07-24, file-table column-header sort) and ELITEA-1851 (2026-07-24,
file preview/edit canvas), ELITEA-1828 (2026-07-23). Not a substitute for
execution — verify each handle live as you use it; update this file after your
own run rather than trusting it blindly.

## Navigation & bucket list (left panel)

| Handle | testid | Notes |
|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | left panel |
| Create bucket button | `artifacts-create-bucket-button` | opens `/artifacts/create-bucket` |
| Bucket name input (create form) | `artifacts-bucket-name-input` | plain textbox, `fill()` works fine (not an MUI-onChange-blocking field) |
| Bucket save button (create form) | `artifacts-bucket-save-button` | |
| Search buckets button | `artifacts-search-buckets-button` | "No buckets found" empty state confirmed |
| Bucket list item | plain text node per bucket name, no dedicated testid confirmed yet | click via text match; direct `?bucket={name}` URL nav is flaky right after creating a NEW bucket (see Quirks below) — prefer clicking the list item for a just-created bucket |

## Upload flow

| Handle | testid | Notes |
|---|---|---|
| Upload files button (toolbar, bucket has ≥1 file) | `artifacts-upload-files-button` | opens native file chooser immediately, no loading delay |
| Upload files button (empty-bucket state) | `artifacts-upload-files-empty-state-button` | **distinct testid** from the toolbar button above — confirmed live, only appears when the bucket has zero files |
| "Upload files to ..." dialog | `artifacts-upload-path-dialog` | on `automation/testids` only as of ELITEA-1832 |
| Upload path input (read-only prefix wrapper) | `artifacts-upload-path-input` | `text_content()` includes bucket-prefix `startAdornment` text |
| Upload path input (editable `<input>`) | `artifacts-upload-path-input-field` | added for ELITEA-1824; accepts a full multi-segment string (`"folder-a/folder-b"`) in one `type()` call |
| Upload path "Upload" button | `artifacts-upload-path-upload-button` | |
| Success toast (generic, app-wide) | `toast-message` | exact text `"Your file(s) have been successfully uploaded!"` (ELITEA-1826/1824); auto-dismisses fast — assert via a short polled wait, not a single instantaneous check |

## "Resolve duplicates" modal (client-side duplicate detection)

| Handle | testid | Notes |
|---|---|---|
| Dialog root | `artifacts-resolve-duplicates-dialog` | via `BaseModal`'s `data-testid` prop |
| Duplicate filename row | `artifacts-resolve-duplicates-filename` | repeated per colliding file; text split across `sample`/`.ext` spans |
| Cancel button | `artifacts-resolve-duplicates-cancel-button` | aborts the ENTIRE upload batch (incl. non-duplicate files), zero network request |
| Message text (dynamic singular/plural) | `artifacts-resolve-duplicates-message` — **needs-adding** (ELITEA-1828) | `DuplicateDialogContent.jsx`; singular "This file already exists..." for 1 duplicate, "N files already exist..." for >1 |
| Skip / Replace / Keep both buttons | none yet — **needs-adding** (ELITEA-1828) | `DuplicateResolutionDialog.jsx`; present in DOM, un-testid'd until ELITEA-1828 lands — no case has clicked any of them yet |
| Detection trigger | — | confirmed purely client-side: clicking "Upload" with a duplicate present fires **zero** network requests; the app diffs selected filenames against the bucket listing already fetched when the bucket was opened |

## File list / tree (main panel)

| Handle | testid | Notes |
|---|---|---|
| File list container | `artifacts-file-list` | |
| File row | `artifacts-file-row` | one per file |
| Per-file actions (dot) menu | `artifact-actions-{filename}-menu-button` | dynamic, filename-templated — use an UPPER_CASE class-constant template, not an inline f-string |
| Delete-confirmation "Delete" button | `delete-confirm-button` | reusable app-wide |
| Left-panel tree item (folder/file) | `artifacts-tree-item-{key}` | dynamic; **key is the FULL relative path** (`folder-a/folder-b/`, not just `folder-b/`) |
| Tree-item "selected" state | `data-selected="true"/"false"` | attribute on the same tree-item testid node — filter on it, don't add a new state-keyed testid |
| Breadcrumb — bucket label | `artifacts-breadcrumb-bucket-label` | |
| Breadcrumb — folder crumb(s) | `artifacts-breadcrumb-folder-label` | repeated, one per nesting level; `get_breadcrumb_folder_names()` returns a list |

## File preview/edit canvas (main panel, opens over the file list)

Brand-new surface as of ELITEA-1851 (2026-07-24) — zero pre-existing
page-object coverage (`automation/pages/artifacts_page.py` has no
Preview/Editor methods) and **zero testids anywhere in the whole canvas**
except the 3-dot menu trigger. Opens by clicking a file row's Preview icon;
URL gains `&file={filename}`.

| Handle | testid | Notes |
|---|---|---|
| File row's Preview/View-Edit icon | none — **needs-adding**: `artifacts-file-preview-{filename}-button` (dynamic) | Only `aria-label="Preview {filename}"` today. **Confirmed ALWAYS visible** (`opacity:1`, `display:flex`) — NOT hover-gated, despite ELITEA-1851's case text implying hover-reveal. |
| Editor header (full path text) | none — needs-adding: `artifacts-file-editor-header` | `PreviewHeader.jsx`'s `canvasTitle`; truncates to `bucket/…/folder/file` beyond 3 path segments |
| Language selector ("Python (detected)" etc.) | none — needs-adding: `artifacts-file-editor-language-select` | Custom `Select.SingleSelect`, appends `" (detected)"` when value matches auto-detected language |
| Save button | none — needs-adding: `artifacts-file-editor-save-button` | `disabled={isSaving \|\| !hasUnsavedChanges}` — **starts disabled** on a fresh unedited open (confirmed live + via source), enables + turns solid/blue after any edit. Case text sometimes assumes "active on open" — it isn't; verify live before trusting a case's claim here. |
| Discard button | none — needs-adding: `artifacts-file-editor-discard-button` | Same disabled-condition as Save. Clicking it (once enabled) opens a separate, also-un-testid'd "Are you sure you want to discard changes?" confirmation dialog. |
| Close (X) button | none — needs-adding: `artifacts-file-editor-close-button` | `aria-label="Close preview"` only. **MUI Tooltip overlay quirk**: a click immediately after only a `hover()` can land on the Tooltip's own label instead of the button — a direct click with no preceding hover works reliably; use `force=True` if the caller does hover first. |
| 3-dot overflow menu button | `file-preview-overflow-menu-menu-button` | **pre-existing, on-main** ✓ (EliteaAI/EliteaUI@7515f444) — generated by the shared `DotMenu` component's `id="file-preview-overflow-menu"` prop, same `{id}-menu-button` convention as `bucket-menu-{name}-menu-button`. Opens Copy Content / Download / Delete, none of which carry their own per-item testid yet (DotMenu only emits one when the item object has a `key` field; this menu's items have none). |
| Editor content (CodeMirror) | none on the wrapping container; `.cm-content`/`.cm-lineNumbers` are third-party internals | **No app testid wraps the CodeMirror instance at all** — add one on the container first (`artifacts-file-editor-content` or similar), then scope `.cm-content`/`.cm-lineNumbers` off it (#579 sanctioned-exception shape, same as `mcp_form_page.py`'s `raw_json_editor_content`). |
| File-content fetch endpoint | n/a (network, not a DOM handle) | `GET /artifacts/artifact/default/{project_id}/{bucket}/{filePath}` (`useArtifactContentFetch.hooks.js:72`) — same endpoint the Download menu item/button already use. |

**Quirk — Save/Discard's disabled gate is a hard prerequisite for any
edit/save automation**: any case that clicks Save/Discard must first make a
real edit (e.g. type one character into `.cm-content`) or the click is a
no-op on a disabled button. Confirmed live: typing flips both to enabled
immediately, no debounce observed.

**Quirk — precondition data doesn't exist as a literal fixture**: same
"`bucket-1` is case-text shorthand, not a real bucket" pattern already
documented below for the upload-flow cases — confirmed again for ELITEA-1851
(zero matches for `bucket-1` across 363+ existing buckets). Seed via
`artifact_bucket` fixture + `ArtifactAPI.upload_file()`, don't hardcode the
case's literal name/size.

## File table sort (column headers) — GAP-035, 2026-07-24

`ArtifactTable.jsx` renders its file-table header via the shared
`GridTableHeader.jsx` (`@/[fsd]/entities/grid-table/ui`) + `useTableSort`/
`SortComparators` (`@/[fsd]/entities/grid-table/lib`). Confirmed live, all four
sortable columns (Name, Type, Size, Last update) toggle asc→desc→asc correctly
per `useTableSort.hooks.js`'s `handleSort` (new field ⇒ always starts
ascending; same field ⇒ toggles; a third click on the same field wraps back to
ascending, not a 3-state cycle).

| Handle | testid | Notes |
|---|---|---|
| Name/Type/Size/Last-update header cells | none yet — **needs-adding**: `artifacts-column-header-{name,fileType,size,modified}` | `GridTableHeader.jsx` already destructures + wires a generic `columnTestIdPrefix` prop (confirmed on `automation/testids`, absent on `main` entirely) — **already in production use** by the MCP table (`DataTable.jsx:446`, `columnTestIdPrefix={isMCPs ? 'mcp-table' : undefined}`). The ONLY missing piece is one line at `ArtifactTable.jsx`'s own `<GridTableHeader>` call site: `columnTestIdPrefix="artifacts"`. Field names are `fileType` (not `type`) and `modified` (not `lastUpdate`) — the testid literally interpolates `column.field`. Wiring it also testids the non-sortable `Actions` column (`artifacts-column-header-actions`) as an inherent, all-or-nothing side effect — not a new scope violation, same as the MCP table's own usage. |
| Active-header state | no new selector — read `opacity` (computed style) on the header-cell testid element itself | `styles.headerCell(isActive, ...)` sets `opacity: isActive ? 1 : 0.7` on the SAME Box that gets the testid once wired. Do NOT chain a raw selector off it to reach the `SortArrows` icon for direction/rotation — the icon is an app asset (not third-party), so no `#579` exception applies; row-order already proves asc/desc, the icon rotation doesn't need its own assertion. |
| Sort click → network | none — pure client-side re-sort | Confirmed live: clicking any sortable header fires **zero** new network requests; `sortData`/`useTableSort` operate on the already-fetched in-memory `rows`. Wait on DOM row-order change, not any network condition. |
| S3 `lastModified` precision | n/a (backend fact, not a DOM handle) | Confirmed via direct API probe (`GET {elitea_root}/artifacts/s3/{bucket}?project_id=399&format=json` against an unrelated 270-file bucket): ISO-8601 timestamps always have `.000` milliseconds — real **whole-second** resolution. Any test seeding 2+ files whose relative "Last update" order matters MUST space uploads across a second boundary (poll `ArtifactAPI.get_file_metadata()` or a justified `sleep(1.1)`) — back-to-back API uploads in the same second produce a backend-ambiguous tie that falls back to S3 listing order, not real chronological order. |
| Size comparator is numeric, not lexical | n/a | `SortComparators.fileSize` (`sortComparators.js:2-28`) parses the formatted size string back into raw bytes before comparing. Proven live (not just by reading source): ascending order for `49 B`/`26.1 KB`/`155.7 KB` matched byte count, which DISAGREES with the lexical string order of those same labels (`"155.7 KB" < "26.1 KB" < "49 B"` alphabetically) — a good concrete counter-example to cite instead of asserting "not lexical" from source alone. |

## Quirks / gotchas

- **Direct `?bucket={name}` URL navigation races the storage-selection load** for a
  bucket **just created in the same session** — confirmed live (ELITEA-1828, this run):
  navigating straight to `?bucket=<new-bucket>` right after creating it produced
  "Select Storage" / "Buckets: 0" (storage selector hadn't attached yet). Reloading
  `/artifacts` plain and then clicking the bucket's list item works reliably. Existing,
  already-indexed buckets don't show this race (confirmed by ELITEA-1827's own
  `navigate_to_bucket()` usage, which navigates by URL param successfully for
  already-established buckets).
- **Pre-existing, unrelated console noise**: `GET /api/v2/secrets/secrets/default/{project_id}`
  → `403 Forbidden` fires on every page load in this local environment (documented
  across many AFS files in `chat-interface/` and now confirmed again here in
  `artifacts/`) — exclude it explicitly from any "no new console errors" check, it is
  not caused by any Artifacts action.
- **"Folders" are a client-side rendering construct**, not a server-side entity — the
  storage is S3-style/key-prefix-based; nested paths are encoded in the object key
  (`bucket/folder-a/folder-b/file.ext`) and the tree lazily derives per-level nodes from
  `/`-splitting `contents[].key` in the bucket's JSON listing response. A single upload
  PUT can create an arbitrarily deep new "folder" chain in one atomic request — no
  separate folder-creation call ever fires.
- **Tree lazy-rendering**: a not-yet-expanded folder's descendant tree nodes do not
  exist in the DOM at all until the parent is clicked/expanded — confirmed via a
  fresh-page-load re-check (the auto-navigated post-upload state has everything already
  expanded, which alone can't distinguish lazy vs. eager rendering).
- **MUI form fields in this area are plain-`fill()`-safe** (bucket-name create field
  confirmed) — unlike some other areas of the app, no keyboard-event workaround needed
  here.
