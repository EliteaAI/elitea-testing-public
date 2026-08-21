# Test Case: Artifacts Landing Page UI – Bucket with More Than 10 Files and Pagination

## Metadata
- **TMS ID**: ELITEA-1804
- **Linked Story**: none
- **Priority**: l3 (TMS `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/399)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, artifacts-w01 cluster ELITEA-1803/1804/1805/1806, 2026-08-21)
- **Status**: ready-for-automation

## Preconditions
- User is logged in (auth_state, localhost).
- A bucket containing **12** files exists (the case's own "more than 10, e.g. 12").

## Test Data
### generate-per-test (test setup, own teardown)
- Fresh bucket via the `artifact_bucket` fixture + 12 files
  (`file-01.txt` … `file-12.txt`) uploaded via `ArtifactAPI.upload_file()`.
  12 is chosen because the case's own expected strings (`1 - 10 of 12`,
  `11 - 12 of 12`) are written for exactly that count.
- **Precondition seeding is transit substitution** (§ Fidelity Declaration).

## Test Steps
1. Navigate to `/artifacts`, wait for page load
   - **Verify**: page loads (`artifacts-buckets-heading` visible)
2. Click the seeded 12-file bucket row
   - **Verify**: the main panel loads its files
3. Verify selection
   - **Verify**: the bucket row carries `data-selected="true"`; the file table
     is rendered
4. Verify the file-table column headers
   - **Verify**: `artifacts-file-table-column-header-{name,fileType,size,modified,actions}`
     read `Name`, `Type`, `Size`, `Last update`, `Actions`
5. Verify the rows-per-page default
   - **Verify**: `artifacts-pagination-page-size-select-combobox` reads `10`
6. Verify the first page's row count
   - **Verify**: exactly 10 `artifacts-file-row` elements
7. Verify the first page's counter
   - **Verify**: `artifacts-pagination-page-info` reads `1 - 10 of 12`
8. Verify prev is disabled on page 1
   - **Verify**: `artifacts-pagination-prev-button` `is_disabled()` True
9. Verify next is enabled on page 1
   - **Verify**: `artifacts-pagination-next-button` `is_disabled()` False
10. Click next
    - **Verify**: the click resolves; the table re-renders
11. Verify the counter updates
    - **Verify**: page info reads `11 - 12 of 12`
12. Verify prev becomes enabled
    - **Verify**: prev `is_disabled()` False
13. Verify the table shows the remaining files
    - **Verify**: page 2's name set is DISJOINT from page 1's, and their union
      is exactly the 12 seeded names
    - **Implementation amendment (Phase 2):** this originally asserted the
      literal slice `file-11.txt`, `file-12.txt`, assuming a name-ascending
      default sort. **Live, the table's default order is not by name** — the
      listing arrives in modification order and same-second API uploads tie, so
      page 2 was observed as `file-02.txt`, `file-03.txt`. The case says only
      "the next set of files"; the partition (disjoint pages, union == the full
      set) is what that means and is the stronger, sort-independent contract.
      Asserting a sort the case never states would have invented a contract.
14. Verify next's state on the last page
    - **Verify**: next `is_disabled()` True (12 files = exactly 2 pages, so the
      "more pages exist" branch of the case's step 14 does not apply here)
15. (same observable as 14 — case repeats it) next disabled on the last page
    - **Verify**: next `is_disabled()` True
16. Verify only the remaining files are shown
    - **Verify**: exactly 2 `artifacts-file-row` elements
17. Click prev
    - **Verify**: the click resolves; the table re-renders
18. Verify the counter returns
    - **Verify**: page info reads `1 - 10 of 12`
19. Verify prev is disabled again
    - **Verify**: prev `is_disabled()` True
20. Verify 10 rows again
    - **Verify**: exactly 10 `artifacts-file-row` elements, and the name set is
      identical to the one page 1 showed before navigating away (same Phase-2
      amendment as step 13 — the returned page must be the same page, which
      does not require knowing the sort)

## Expected Results
- Page 1: 10 rows, `1 - 10 of 12`, prev disabled, next enabled.
- Page 2: 2 rows (`file-11.txt`, `file-12.txt`), `11 - 12 of 12`, prev enabled,
  next disabled.
- Back on page 1: identical to the initial state (10 rows, same names, counter
  and arrow states restored).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: bucket with >10 files (upload if absent) | 12 files exist | § Test Data | fixture + 12 `upload_file` calls | covered *(the case's own "if not, upload them" branch — done via API as transit)* |
| 1 Navigate to Artifacts | page loads | step 1 | heading visible | asserted |
| 2 Click bucket with >10 files | selected, files shown | step 2 | table rendered | asserted |
| 3 Bucket highlighted, files listed | highlighted + list visible | step 3 | `data-selected="true"` + rows > 0 | asserted |
| 4 File table with 5 columns | all five present | step 4 | 5 column-header testids + labels | asserted |
| 5 Rows per page default 10 | `10` | step 5 | combobox text | asserted |
| 6 Only 10 rows on page 1 | exactly 10 | step 6 | row count | asserted |
| 7 Counter `1 - 10 of 12` | exact string | step 7 | page-info text | asserted |
| 8 Prev disabled on page 1 | disabled | step 8 | `is_disabled()` | asserted |
| 9 Next enabled | enabled | step 9 | `is_disabled()` False | asserted |
| 10 Click next | navigates | step 10 | subsequent assertions | asserted |
| 11 Counter `11 - 12 of 12` | exact string | step 11 | page-info text | asserted |
| 12 Prev becomes enabled | enabled | step 12 | `is_disabled()` False | asserted |
| 13 Table shows next set | remaining files | step 13 | disjoint-from-page-1 + union == seeded set | asserted |
| 14 Next remains active if more pages, else disabled | disabled (2 pages total) | step 14 | `is_disabled()` True | asserted *(the "more pages" branch is unreachable at 12 files; the case's own Test Data fixes the count at 12)* |
| 15 Next disabled on last page | disabled | step 15 | same | asserted |
| 16 Only remaining files shown | exactly 2 | step 16 | row count | asserted |
| 17 Click prev | navigates back | step 17 | subsequent assertions | asserted |
| 18 Counter back to `1 - 10 of 12` | exact string | step 18 | page-info text | asserted |
| 19 Prev disabled again | disabled | step 19 | `is_disabled()` | asserted |
| 20 10 rows on page 1 | exactly 10 | step 20 | row count + name set identical to the first visit | asserted |

### Axis 2 — Analyst additions
- Assert the **page partition** (steps 13/20) — disjoint pages whose union is
  the seeded set, and a page 1 that comes back identical — not just row counts:
  the case only counts rows, but a pagination bug that renders the right count
  of the wrong slice would pass a count-only check. (Sort-independent by
  design — see step 13's amendment.)
- **NOT asserted: console errors.** The AFS's original Axis-2 addition ("assert no console errors") was dropped during implementation (Phase-2 amendment): `.agents/testing.md` § Unconfirmed records a **confirmed recurring** environmental pattern on this project where `assert not console_messages` intermittently fails on an unrelated background resource returning 500 (3+ occurrences) or 404 (3 occurrences, one repeat on the same spec). Adding that assertion here would import a known flake class into three rendering tests that otherwise have no timing surface. Recorded rather than silently skipped.

## Fidelity Declaration

| Substituted | Transit or terminal | Authority |
|---|---|---|
| Bucket + 12 files created via `ArtifactAPI` instead of the UI | **transit** | Only reaches the precondition the case itself instructs to create ("if not, upload them"). Every asserted observable — row counts, name slices, counter strings, arrow disabled-states — is computed and rendered by the product from its own listing response. |

No `route.fulfill`, no `page.evaluate`, no injected state.

## Cleanup
1. `artifact_bucket` fixture teardown deletes the bucket (known `#636` 404 flake).

## Concrete Handles
Same inventory as ELITEA-1803's AFS § Concrete Handles (pagination + column
headers + bucket row). PROVENANCE identical: the pagination and column-header
testids were added this run and live on `automation/testids` only
(EliteaAI/EliteaUI@6449a5c4); everything else is pre-existing on `main`.

### Live-observed values (2026-08-21)
- Page 1: 10 rows, `1 - 10 of 12`, prev disabled=True, next disabled=False.
- After next: 2 rows, `11 - 12 of 12`, prev disabled=False, next disabled=True.
- After prev: 10 rows, `1 - 10 of 12`, prev disabled=True.

### Gotchas
- **The default order is NOT name-ascending** — confirmed live: after seeding
  `file-01 … file-12` via the API, page 2 came back as `file-02.txt`,
  `file-03.txt`. The listing arrives in modification order and same-second
  uploads tie, so the per-page slice is not predictable from the names. Assert
  the partition, not a slice. (Names are still zero-padded so the seeded set is
  readable in failure messages.)
- The "Last update" column is width-gated (`hideBelow: 900`) — set the viewport
  to 1600x900 before asserting column headers.
