# Test Case: Artifacts Landing Page UI – Empty Bucket (No Files)

## Metadata
- **TMS ID**: ELITEA-1805
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01 cluster ELITEA-1803/1804/1805/1806, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- An **empty** bucket exists (case text's `as` is one operator's ad-hoc data —
  a fixture bucket is used instead; a fresh `artifact_bucket` is empty by
  construction).

## Test Data
### generate-per-test (test setup, own teardown)
- Fresh, empty bucket via the `artifact_bucket` fixture — no upload.
- **Precondition seeding is transit substitution** (§ Fidelity Declaration).

## Test Steps
1. Navigate to `/artifacts`, wait for page load
   - **Verify**: page loads
2. Verify the left-panel header
   - **Verify**: `artifacts-buckets-heading` reads `Buckets`;
     `artifacts-create-bucket-button` and `artifacts-search-buckets-button` visible
3. Verify the storage-provider row
   - **Verify**: `artifacts-storage-selector` reads `Elitea S3 storage`;
     `artifacts-storage-selector-arrow` visible; at least one bucket row rendered
4. Click the empty fixture bucket
   - **Verify**: the click resolves
5. Verify selection + the left-panel empty label
   - **Verify**: the bucket row carries `data-selected="true"`, and
     `artifacts-bucket-tree-empty-label-{bucket}` is visible reading
     `No files in this bucket`
6. Verify the main-panel header
   - **Verify**: `artifacts-breadcrumb-bucket-label` text == the bucket name
7. Verify no file table is rendered
   - **Verify**: `artifacts-file-row` count == 0 **and**
     `artifacts-file-table-column-header-*` count == 0 (no table at all, not
     just no rows)
8. Verify the centre empty state
   - **Verify**: `artifacts-empty-state` visible reading `No files in this bucket`,
     and `artifacts-upload-files-empty-state-button` visible (the icon above them
     is part of the same `ArtifactTableNoFiles` block)
9. Verify the toolbar (top-right)
   - **Verify**: `artifacts-file-search-input`, `artifacts-upload-files-button`,
     `artifacts-download-files-button`, `artifacts-delete-files-button` all visible
10. Verify the left-panel footer
    - **Verify**: `artifacts-buckets-footer-count` matches `Buckets:\s*(\d+)`
      with the number equal to the API's bucket count for the project;
      `artifacts-buckets-footer-size` matches `Size:\s*[\d.]+\s*[KMG]?B`
11. Hover the main-panel **info (i) icon** (`artifacts-bucket-info-button`)
    - **Verify**: `artifacts-bucket-info-tooltip-content` appears containing
      `Retention Policy:` (with a non-empty value) and `Number of files:` `0`
    - **CLARIFICATION #1617** — the case text says "hover over the bucket name
      in the left panel". Live, that element carries only a conditional
      overflow tooltip repeating the bucket name
      (`BucketItem.jsx` → `Tooltip.TypographyWithConditionalTooltip title={name}`).
      The retention/file-count tooltip is a **separate info icon in the main
      panel toolbar** (`BucketInfoTooltip.jsx` from `ArtifactTableToolbar.jsx`).
      The tooltip and its content exist and are correct — only the case's
      location is wrong, so the live contract is asserted (reverse-masking guard).

## Expected Results
- The empty bucket renders the empty state in BOTH panels: the left tree shows
  `No files in this bucket` under the bucket, the main panel shows the centred
  icon + message + `Upload files` button, and NO file table (no rows, no column
  headers) and NO pagination footer.
- The toolbar icon set and the left-panel footer stats render exactly as for a
  non-empty bucket.
- The bucket-info tooltip reports `Number of files: 0`.
- No console errors.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: empty bucket exists | exists | § Test Data | `artifact_bucket` fixture (empty by construction) | covered *(not the case's literal `as`)* |
| 1 Navigate to Artifacts | page loads | step 1 | heading visible | asserted |
| 2 "BUCKETS" + folder + search icons | present | step 2 | heading text + 2 testids | asserted *(DOM text `Buckets`; caps is CSS)* |
| 3 Bucket list under storage provider + arrow | visible | step 3 | selector text + arrow + ≥1 row | asserted |
| 4 Click empty bucket | selected | steps 4-5 | `data-selected="true"` | asserted |
| 5 Highlighted + "No files in this bucket" in left tree | both | step 5 | `data-selected` + bucket-scoped empty label text | asserted |
| 6 Bucket name as main-panel header | shows name | step 6 | breadcrumb text | asserted |
| 7 No file table / rows in main panel | none | step 7 | row count 0 AND column-header count 0 | asserted |
| 8 Centre empty state: icon + message + Upload files button | all present | step 8 | `artifacts-empty-state` text + empty-state upload button | asserted *(the icon is a non-testid SVG inside the same block — its presence is implied by the block; not separately asserted, see Axis 2)* |
| 9 Search bar + upload/download/delete icons | present | step 9 | 4 testids | asserted |
| 10 Footer "Buckets: N Size: X MB" | correct | step 10 | regex + API cross-check | asserted |
| 11 Hover bucket name → tooltip Retention Policy / Number of files: 0 | tooltip with correct content | step 11 | hover the main-panel info icon; tooltip content text | asserted *(CLARIFICATION #1617 — content asserted as specified, location corrected to the live one)* |

### Axis 2 — Analyst additions
- Assert the **column headers** are absent too (step 7), not just the rows —
  "does not display a file table" is stronger than "shows no rows", and only the
  header check distinguishes them.
- Assert the **pagination footer is absent** (`artifacts-pagination-page-info`
  count 0) — live-confirmed `GridTablePagination` returns `null` at
  `totalRows === 0`; a regression that renders `0 - 0 of 0` would be a real bug.
- Cross-check the footer bucket count against the API (same reasoning as
  ELITEA-1803).
- Assert **no console errors**.
- NOT asserted: the empty-state SVG icon itself has no testid and no accessible
  name (`ArtifactTableNoFiles.jsx` renders it as an `sx`-styled `Box`
  component). Adding a testid for a purely decorative icon inside a block whose
  message + button are already asserted would add a handle no behaviour depends
  on; the block's presence is proven by its message and button.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Empty bucket created via `ArtifactAPI` instead of the UI | **transit** | Only reaches the precondition. Every asserted observable (empty-state block, tree label, absent table, footer stats, tooltip counts) is rendered by the product from its own data. |

No `route.fulfill`, no `page.evaluate`, no injected state.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (known `#636` 404 flake).

## Concrete Handles (discovered/verified live this session)

| Element | Handle | PROVENANCE |
|---|---|---|
| Left-tree empty label | `artifacts-bucket-tree-empty-label-{bucket}` (dynamic) | added this run — `automation/testids` only (EliteaAI/EliteaUI@6449a5c4) |
| Bucket-info icon | `artifacts-bucket-info-button` | added this run — `automation/testids` only |
| Bucket-info tooltip content | `artifacts-bucket-info-tooltip-content` | added this run — `automation/testids` only |
| Centre empty state message | `artifacts-empty-state` | on-main ✓ (pre-existing) |
| Centre empty-state upload button | `artifacts-upload-files-empty-state-button` | on-main ✓ (pre-existing) |
| Footer / storage selector / column headers / pagination | see ELITEA-1803's AFS | as recorded there |

### Live-observed values (2026-08-21)
- Empty bucket: `artifacts-file-row` count 0, column-header count 0,
  `artifacts-pagination-page-info` count 0.
- `artifacts-empty-state` text: `No files in this bucket`.
- `artifacts-bucket-tree-empty-label-*` text: `No files in this bucket`.
- Tooltip text on the info icon: `Retention Policy:1 YearNumber of files:0`
  (label/value are sibling `<Typography>`s → no whitespace between them in
  `text_content()`; assert with `\s*` or substring checks).

### Gotchas
- **The left-tree empty label is NOT unique per page.** Any expanded empty
  bucket renders one, and `/artifacts` auto-selects (and expands) a bucket on
  landing — a page-wide count is never 0. Hence the bucket-parameterized testid.
- `BucketContent` (left tree) is a SIBLING of `BucketItem` (the row carrying
  `artifacts-bucket-row-{name}`) inside an untagged wrapper `<Box>` — the label
  cannot be CSS-scoped under the row testid, which is why it had to carry the
  bucket name itself.
