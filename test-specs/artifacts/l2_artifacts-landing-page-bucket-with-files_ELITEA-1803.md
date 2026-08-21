# Test Case: Artifacts Landing Page UI – Bucket with Files (at least 1 file)

## Metadata
- **TMS ID**: ELITEA-1803
- **Linked Story**: none
- **Priority**: l2 (TMS `priority: high` — same mapping as ELITEA-1824)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01 cluster ELITEA-1803/1804/1805/1806, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- A bucket containing at least one file exists. **Not** the case text's literal
  `add-as-attachment`/`12.png` — that is one operator's ad-hoc data in a shared
  project; see § Test Data.

## Test Data
### generate-per-test (test setup, own teardown)
- Fresh bucket via the `artifact_bucket` fixture.
- One file uploaded through `ArtifactAPI.upload_file(bucket, "sample.txt", ...)`
  — an ordinary text file. The case's own `12.png` / `295.9 KB` /
  `29-01-2026, 06:11 PM` values are illustrative of ONE row, not a contract;
  the assertions below bind to the file the test itself uploads and to the
  live-observed **formats** (`Text`, `\d+ B`, `DD-MM-YYYY, HH:MM AM/PM`).
- **Precondition seeding is transit substitution** (§ Fidelity Declaration).

### stable / read-only
- The left-panel footer's bucket count + total size are read-only observables of
  the whole project; the test cross-checks the footer count against the **left
  panel's own DISTINCT rendered bucket rows** (system-produced oracle, not a
  hard-coded number — the project accumulates buckets, see #636). *Phase-2
  amendment: an `ArtifactAPI.list_buckets()` oracle was tried first and proved
  racy — the buckets listing is eventually consistent (760 rendered vs 762
  returned). See step 10.*

## Test Steps
1. Navigate to `/artifacts`, wait for page load
   - **Verify**: left panel renders; `artifacts-buckets-heading` reads `Buckets`
     (case text writes "BUCKETS" — the DOM text is `Buckets`, upper-casing is CSS)
2. Verify the left-panel header controls
   - **Verify**: `artifacts-create-bucket-button` (folder / create-bucket icon)
     and `artifacts-search-buckets-button` (magnifier) are both visible
3. Verify the storage-provider row
   - **Verify**: `artifacts-storage-selector` is visible and reads
     `Elitea S3 storage`; `artifacts-storage-selector-arrow` (dropdown arrow) is visible
4. Click the seeded bucket row (`artifacts-bucket-row-{bucket}`)
   - **Verify**: the click resolves and the main panel loads the bucket
5. Verify selection + tree expansion
   - **Verify**: the bucket row carries `data-selected="true"`, and the
     left-panel tree shows `artifacts-tree-item-sample.txt`; the bucket's own
     empty-tree label (`artifacts-bucket-tree-empty-label-{bucket}`) is absent
6. Verify the main-panel header
   - **Verify**: `artifacts-breadcrumb-bucket-label` text == the bucket name
7. Verify the file-table column headers
   - **Verify**: `artifacts-file-table-column-header-{name,fileType,size,modified,actions}`
     read exactly `Name`, `Type`, `Size`, `Last update`, `Actions`
8. Verify the file row's cells
   - **Verify**: exactly one `artifacts-file-row`; it contains the checkbox
     (`artifacts-file-checkbox-*`), the name `sample.txt`, the type `Text`, a
     size matching `\d+(\.\d+)? [KMG]?B` and a timestamp matching
     `DD-MM-YYYY, HH:MM AM/PM`; the row's actions dot-menu
     (`artifact-actions-{row-id}-menu-button`) is present
9. Verify the main-panel toolbar (top-right)
   - **Verify**: `artifacts-file-search-input`, `artifacts-upload-files-button`,
     `artifacts-download-files-button`, `artifacts-delete-files-button` all visible
10. Verify the left-panel footer
    - **Verify**: `artifacts-buckets-footer-count` text matches `Buckets:\s*(\d+)`
      and the captured number equals the number of DISTINCT bucket rows the
      left panel actually renders; `artifacts-buckets-footer-size` matches
      `Size:\s*[\d.]+\s*[KMG]?B`
    - **Implementation amendment (Phase 2):** the oracle was originally the
      API's own bucket list. That proved **racy** — the buckets listing is
      eventually consistent, measured live as 760 rendered vs 762 returned by
      `GET /artifacts/buckets/default/399` seconds after creating buckets. The
      footer is fed `bucketCount={buckets?.length}` from the SAME array the
      list renders (`BucketsPanel.jsx`), so footer-vs-list is the race-free
      form of the same check, still entirely product-produced. Distinct names
      are counted because a PINNED bucket renders twice
      (`BucketsListContent.jsx` renders the pinned list AND the full list).
11. Verify the rows-per-page control
    - **Verify**: `artifacts-pagination-page-size-select-combobox` reads `10`
12. Verify the pagination counter
    - **Verify**: `artifacts-pagination-page-info` reads `1 - 1 of 1`
13. Verify both navigation arrows exist
    - **Verify**: `artifacts-pagination-prev-button` and
      `artifacts-pagination-next-button` are both visible
14. Verify prev is disabled on the first page
    - **Verify**: prev `is_disabled()` is True
15. Verify next is disabled when everything fits on one page
    - **Verify**: next `is_disabled()` is True

## Expected Results
- Every landing-page chrome element renders for a bucket that has files:
  heading + 2 header icons, storage selector with arrow, bucket list, footer
  stats, main-panel header, the 5-column file table with a correctly-populated
  row, the toolbar icon set, and pagination reading `1 - 1 of 1` with **both**
  arrows present and disabled.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket with ≥1 file | exists | § Test Data | fixture + `upload_file` | covered *(fixture bucket, not the case's literal `add-as-attachment`)* |
| 1 Navigate to Artifacts | page + left panel load | step 1 | `artifacts-buckets-heading` visible | asserted |
| 2 "BUCKETS" label + folder + search icons | all present | steps 1-2 | heading text + 2 testids visible | asserted *(DOM text is `Buckets`; the all-caps is CSS text-transform)* |
| 3 Bucket list under storage provider + dropdown arrow | visible | step 3 | storage-selector text + arrow visible + ≥1 bucket row | asserted |
| 4 Click bucket with ≥1 file | selected + expanded | steps 4-5 | `data-selected="true"` + tree item visible | asserted |
| 5 Selected bucket highlighted, files listed beneath | highlighted + file listed | step 5 | same | asserted |
| 6 Bucket name as main-panel header | header shows bucket name | step 6 | `artifacts-breadcrumb-bucket-label` text | asserted |
| 7 File table with 5 columns | all five present | step 7 | 5 column-header testids + exact labels | asserted |
| 8 Row: checkbox, name, type, size, timestamp, actions icon | all present with correct shapes | step 8 | row text + checkbox + actions testids | asserted *(formats, not the case's literal PNG values — different file)* |
| 9 Search bar + upload/download/delete icons top-right | all present | step 9 | 4 testids visible | asserted |
| 10 Footer "Buckets: N Size: X MB" reflects actual values | correct count + size | step 10 | count: footer N == the panel's DISTINCT rendered bucket rows (`get_rendered_bucket_names()`); size: shape only (`Size:\s*\d+(\.\d+)?\s*[KMG]?B`) | asserted *(count against an oracle; size shape-only — no race-free total-size oracle exists)* |
| 11 "Rows per page" defaults to 10 | default 10 | step 11 | combobox text == `10` | asserted |
| 12 Pagination shows correct range/total | `1 - 1 of 1` | step 12 | page-info text | asserted |
| 13 Prev/next arrows present | both present | step 13 | both testids visible | asserted |
| 14 Prev disabled on first page | disabled | step 14 | `is_disabled()` True | asserted |
| 15 Next disabled when all files fit one page | disabled | step 15 | `is_disabled()` True | asserted |

### Axis 2 — Analyst additions
- Cross-check the footer bucket count against the **left panel's own rendered
  bucket rows** rather than a hard-coded number — the case says "reflecting the
  actual number of buckets"; a literal would be false within minutes (the
  project accumulates leaked `autotest-*` buckets, #636). See step 10's
  implementation amendment for why the API is NOT the oracle here.
- Assert the bucket's own empty-tree label is ABSENT (step 5) — the positive
  case's mirror of ELITEA-1805's assertion; cheap, and it catches the
  render-both-states regression.
- **NOT asserted: console errors.** The AFS's original Axis-2 addition ("assert no console errors") was dropped during implementation (Phase-2 amendment): `.agents/testing.md` § Unconfirmed records a **confirmed recurring** environmental pattern on this project where `assert not console_messages` intermittently fails on an unrelated background resource returning 500 (3+ occurrences) or 404 (3 occurrences, one repeat on the same spec). Adding that assertion here would import a known flake class into three rendering tests that otherwise have no timing surface. Recorded rather than silently skipped.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket + file created via `ArtifactAPI` instead of the UI | **transit** | Only reaches the state under test. Every observable this case asserts (footer, table, row cells, pagination, arrow states) is rendered by the product from its own `GET /artifacts` data — nothing asserted is read off the seeding call. Established precedent for this surface (ELITEA-1851/1857/1862). |

No `route.fulfill`, no `page.evaluate`, no injected state.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (subject to the known
   `#636` 404-on-teardown flake, handled gracefully by the fixture).

## Concrete Handles (discovered/verified live this session)

| Element | Handle | PROVENANCE |
|---|---|---|
| Buckets heading | `artifacts-buckets-heading` | on-main ✓ (pre-existing) |
| Create-bucket icon | `artifacts-create-bucket-button` | on-main ✓ (pre-existing) |
| Search-buckets icon | `artifacts-search-buckets-button` | on-main ✓ (pre-existing) |
| Storage selector | `artifacts-storage-selector` | added this run — `automation/testids` only (EliteaAI/EliteaUI@6449a5c4) |
| Storage dropdown arrow | `artifacts-storage-selector-arrow` | added this run — `automation/testids` only |
| Bucket row / selection | `artifacts-bucket-row-{name}` + `data-selected` | on-main ✓ (pre-existing) |
| Left-tree file node | `artifacts-tree-item-{path}` | on-main ✓ (pre-existing) |
| Bucket's empty-tree label | `artifacts-bucket-tree-empty-label-{bucket}` (dynamic) | added this run — `automation/testids` only |
| Main-panel bucket header | `artifacts-breadcrumb-bucket-label` | on-main ✓ (pre-existing) |
| Column headers | `artifacts-file-table-column-header-{name,fileType,size,modified,actions}` | added this run (wired `columnTestIdPrefix` on the existing shared `GridTableHeader` prop) — `automation/testids` only |
| File row | `artifacts-file-row` | on-main ✓ |
| Row checkbox | `artifacts-file-checkbox-{row-id}` | on-main ✓ |
| Row actions menu | `artifact-actions-{row-id}-menu-button` | on-main ✓ |
| Toolbar search/upload/download/delete | `artifacts-file-search-input`, `artifacts-upload-files-button`, `artifacts-download-files-button`, `artifacts-delete-files-button` | on-main ✓ |
| Footer count / size | `artifacts-buckets-footer-count` / `-size` | added this run — `automation/testids` only |
| Pagination page info | `artifacts-pagination-page-info` | added this run (passed to the shared `pageInfoTestId` prop) |
| Pagination prev / next | `artifacts-pagination-prev-button` / `-next-button` | prev prop added + both wired this run |
| Rows-per-page select | `artifacts-pagination-page-size-select-combobox` (SingleSelect derives the `-combobox` suffix) | added this run |

### Live-observed values (2026-08-21)
- `artifacts-buckets-footer-count`.text_content() → `Buckets:757` (label and
  value are two sibling `<Typography>`s inside the testid'd Box → **no space**
  in `text_content()`; assert with `\s*`).
- `artifacts-buckets-footer-size` → `Size:254.8 MB`.
- Column-header labels: `Name`, `Type`, `Size`, `Last update`, `Actions` —
  note the field key for "Last update" is **`modified`**, not `lastUpdate`.
- Row text for a text file: `sample.txtText120 B21-08-2026, 05:43 PM`.
- Page-size combobox text: `10`. Page info: `1 - 1 of 1`.
- Prev `is_disabled()` True, next `is_disabled()` True on a single-page bucket.

### Gotchas
- **Landing auto-selects a bucket.** `/artifacts` with no `?bucket=` param
  auto-selects one, which also EXPANDS it — so a page-wide count of the
  left-tree empty label is never 0. This is why the empty-tree label testid is
  bucket-parameterized.
- The "Last update" column is width-gated (`hideBelow: 900` on the table's own
  width) — set the viewport explicitly (1600x900, same as ELITEA-1824).
