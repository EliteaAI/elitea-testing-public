---
name: Artifacts multi-select ZIP download — checkbox and dialog-internals testid gaps
description: ELITEA-1840 findings — GridTableRow's per-row checkbox has zero testid mechanism (shared component, 7 consumers), ZipDownloadProgressDialog's internals are entirely testid-less, current-file label shows full relative key not base filename, downloadArtifactsAsZip is sequential not parallel, and a window.fetch/page.route delay technique for observing fast UI transitions
type: feedback
---

## Context

ELITEA-1840 ("Download Multiple Selected Files as ZIP via Download Icon") is the first case to actually
*exercise* the toolbar `artifacts-download-files-button` → checkbox multi-select → ZIP-progress-dialog flow.
`ArtifactsPage.download_files_button`/`zip_download_progress_dialog` `LocatorDescriptor`s already existed
(added defensively during ELITEA-1839 to assert the dialog's *absence*), but nothing had ever clicked the
button or asserted the dialog's populated contents until this run.

## Checkbox testid gap — shared component, not a one-off

`GridTableRow.jsx` (`src/[fsd]/entities/grid-table/ui/GridTableRow.jsx:64`) renders
`<Checkbox.BaseCheckbox checked={isSelected} onChange={handleCheckboxChange} .../>` with **no
`data-testid`/`testId` prop threaded through at all** — confirmed via live DOM query (`data-testid: null` on
both the `<input>` and its wrapping span), and via `git grep` for any `checkboxTestId`-shaped prop anywhere in
the grid-table entity or Artifacts page — zero hits, on both `origin/main` and `origin/automation/testids`.

This is a **shared component** — `GridTableRow` has 7 consumers (`SecretsTable`, `TokensTable`, `UsersTable`,
`BucketAccessTable`, `DataTable`, `NotificationTable`, `ArtifactTable`). Per this project's shared-component
testid ruling, the fix is a new caller-supplied prop (e.g. `checkboxTestId`), mirroring the pattern
`GridTableRow` already uses for its own row-level `'data-testid': dataTestId` prop, threaded to
`<Checkbox.BaseCheckbox data-testid={checkboxTestId} .../>` and wired **only** at the call site the test
actually touches (`ArtifactTable.jsx`, `checkboxTestId={\`artifacts-file-checkbox-${row.id}\`}`) — not at the
other 6 consumers, per the testid-scope rule (testids go only where a test actually touches).

The header select-all checkbox (`GridTableHeader.jsx:27`) has the identical gap but was correctly left
un-specced — ELITEA-1840's case never clicks select-all (that's sibling case ELITEA-1841's scope).

## ZipDownloadProgressDialog internals — ALL testid-less except the outer shell

Only the outer `<BaseModal data-testid="artifacts-zip-download-progress-dialog">` (added during ELITEA-1839)
has a testid. Confirmed via live DOM query (`document.querySelectorAll('[data-testid]')` inside the open
dialog → only 1 result, the outer root) that **every internal element is bare**:
- Title (`<h2 class="MuiDialogTitle-root">`, "Preparing {bucket}.zip")
- "Downloading files..." body label
- The `LinearProgress` progress bar (`role="progressbar"`)
- The `"{current} of {total} files"` counter
- The conditional `"Current: {filename}"` label (only rendered when `progress.filename` is truthy)
- The Cancel action button

The case (ELITEA-1840 step 9) explicitly requires verifying title/progress-bar/counter/current-file/Cancel
independently — and this project's strict locator policy forbids a scoped raw-tag selector
(`dialog.locator("h2")`) even inside a real testid-anchored parent (scoped sub-selectors must themselves be
`[data-testid="…"]`-based). So all 5 internal elements needed their own `testid needed:` row, not just the
outer dialog. Named consistently under the `artifacts-zip-download-progress-*` prefix:
`-title`, `-bar`, `-counter`, `-current-file`, `-cancel-button`.

**Bonus finding**: `BaseModal` also always renders a header Close (✕) icon button (`aria-label="Close"`)
alongside whatever `actions` are passed in — a general `BaseModal` chrome element, not the case's own Cancel
button, easy to confuse with it if you're not looking at the DOM directly. Not requested by this case, left
un-specced.

## "Current: {filename}" shows the FULL relative key, not the base filename

Confirmed live (captured mid-flight via a network-delay technique, see below): the label reads
`"Current: a1/sample.png"` — the full key including the subfolder prefix — NOT `"Current: sample.png"`. This
is a genuinely new fact; prior static-analysis notes for this case didn't specify which. Contrast with the
per-row checkbox/dot-menu identity (`row.id` = base filename only, per the ELITEA-1839 memory entry) — the
ZIP-progress current-file label and the row identity use different string shapes for the "same" file. Don't
assume they match without checking.

## downloadArtifactsAsZip is sequential, not parallel

`src/common/utils.jsx:444`, confirmed via source read: a plain `for (let i = 0; i < expandedFilenames.length;
i += 1) { ... await fetch(...) ... onProgress(...) }` — one file fully downloaded (including its `blob()`
read and `zip.file()` add) before the next file's `fetch` starts. Not `Promise.all`. This matters for anyone
reasoning about the progress-counter's "as each file is processed" semantics, or trying to predict total ZIP
time from file count.

## Technique: observing a UI transition that completes in <1 second

With only 2 small (< 60 byte) seeded files, the whole select→click→ZIP-download flow completes in well under
1 second — too fast for a naive Playwright script (or even back-to-back MCP tool calls) to reliably observe
an intermediate frame of the progress dialog. Wrapping `window.fetch` with an artificial delay (matching the
artifact-download URL pattern) via `browser_evaluate`, installed *before* the click, reliably surfaced the
`"1 of 2 files"` / `"Current: a1/sample.png"` frame for a screenshot + DOM query. The idiomatic Playwright
equivalent for an actual automated test is `page.route()` intercepting the same URL pattern and delaying
`route.continue_()` — this is a legitimate timing-control technique (delays a network response, doesn't
synthesize a fake input event), not a Synthetic-Input-Hygiene violation and not defect-masking. Worth reusing
whenever a case asks to verify a genuinely-transient intermediate UI state that the real flow blows past too
fast to observe naturally.

## Confirmed: Playwright DOES capture client-side blob-URL anchor-click downloads

`downloadArtifactsAsZip` builds the ZIP fully client-side (JSZip) and triggers the download via
`document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.click()` — no server-streamed
response. Confirmed live 2/2 runs: Playwright's `expect_download()`/download-event machinery captures this
exactly like a normal server-initiated download, no special handling needed. This resolves a question flagged
in this case's own dispatch context ("if `expect_download()` doesn't catch it, that's an implementer concern
to flag") — it does catch it, cleanly.
