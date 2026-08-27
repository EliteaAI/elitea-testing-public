# Test Case: Secrets listing — pagination navigates between pages correctly

## Metadata
- **TMS ID**: ELITEA-2332
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2332.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399, 121 secrets)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none — the product matches the case text on every step.

## Preconditions
- Project `Private` (399) with **more than 10 secrets** (case step 1) — **121 live**,
  confirmed 2026-08-27 (`1 - 10 of 121`). The precondition is **asserted**, not assumed:
  a total ≤ 10 makes the whole case vacuous and must fail loudly with a named reason.
- **Read-only case.** Pagination is pure client-side React state.

## Test Data
### reuse-existing
- The live secret set, read-only. Page contents are compared as **rendered sets**, never
  against hardcoded names.

## The product's actual pagination contract (source + live confirmed)

- `SecretsTable.jsx:152-155`: `usePagination({ totalRows: sortedRows.length,
  defaultPageSize: 10, pageSizeOptions: [5, 10, 50, 100] })`.
- `GridTablePagination.jsx` renders the range as the literal template
  `` `${startRow} - ${endRow} of ${totalRows}` `` — i.e. **`1 - 10 of 121`**, an
  ASCII hyphen with spaces (the case's `"1–10 of N"` is an illustrative en-dash form,
  not the rendered string).
- `handlePrevPage` / `handleNextPage` are guarded by `isFirstPage` / `isLastPage`, and
  both `IconButton`s carry the matching `disabled` prop.
- `handlePageSizeChange(newPageSize)` sets the size **and resets the page to 0**.
- Everything is client-side over the already-fetched list — **no network request fires**
  on a page change or a page-size change.

### Live observations (2026-08-27, project 399)

| Action | `secrets-pagination-info` | rows | prev | next |
|---|---|---|---|---|
| load | `1 - 10 of 121` | 10 | disabled | enabled |
| click next | `11 - 20 of 121` | 10 (a **different** name set) | enabled | enabled |
| rows-per-page → `5` | `1 - 5 of 121` | 5 | **disabled** (page reset to 1) | enabled |

Rows-per-page options render as `select-option-5` / `-10` / `-50` / `-100` (the shared
`SingleSelectMenuItem`'s pre-existing default `data-testid`), and only one select menu
is ever mounted at a time (0 such nodes in the DOM when closed — confirmed live).

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify** the case precondition: the total parsed out of `secrets-pagination-info`
     is **> 10** (fail with a named reason otherwise — the case cannot be run on a
     single-page dataset).
   - **Capture** `total`, and `page1_names` (rendered `secret-name-cell` texts).

2. **Verify the page range shows `1 - 10 of {total}`** — the first page, full default
   page size — and that `secret_row` count == 10, prev is **disabled**, next is
   **enabled**.

3. Click the next-page arrow (`secrets-pagination-next-button`).

4. **Verify the next set of secrets is shown and the range updates**:
   - range == `11 - {min(20, total)} of {total}`,
   - the rendered names are **disjoint** from `page1_names` (a set-difference check — a
     range label that advanced while the rows stayed put is exactly the regression this
     step exists to catch),
   - prev is now **enabled**.

5. Change "Rows per page" to a different value (`5`): click
   `secrets-pagination-page-size-select-combobox`, then `select-option-5`.

6. **Verify the table updates to show the selected number of rows per page**:
   - `secret_row` count == **5**,
   - the select renders `5`,
   - range == `1 - 5 of {total}` (Axis 2: the page **resets to the first page**, per
     `handlePageSizeChange`), and prev is **disabled** again.

7. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure).

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Range label | `secrets-pagination-info` | on-`main` | existing field |
| Prev arrow | `secrets-pagination-prev-button` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 on `automation/testids` | `GridTablePagination`'s existing `prevButtonTestId` prop |
| Next arrow | `secrets-pagination-next-button` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 | `nextButtonTestId` |
| Rows-per-page select (root, read its text) | `secrets-pagination-page-size-select` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 | `pageSizeSelectTestId` |
| Rows-per-page select (click target) | `secrets-pagination-page-size-select-combobox` | derived automatically by `SingleSelect` from the root testid (`SelectDisplayProps`) | the root node is not clickable — same split already documented on `notification_center_page.py` |
| Rows-per-page option | `select-option-{n}` | **pre-existing, generic** (`SingleSelectMenuItem.jsx:117` default) | a real `data-testid`; only one select menu is mounted at a time, so no scoping is needed — same shape as `notifications-page-size-option-{n}` but without needing a new prop |
| Row / name cell | `secret-row` / `secret-name-cell` | on-`automation/testids` | existing fields |

## Assertion shape
Every expectation is computed from the product's own `total` (parsed out of the range
label the product rendered), not from a constant — so the spec stays correct as the
project's secret count changes, and still fails loudly if pagination arithmetic breaks.

## Implementer notes
- Page-object additions: `prev_page_button` / `next_page_button` / `page_size_select` /
  `page_size_select_combobox` `LocatorDescriptor`s, a `PAGE_SIZE_OPTION` class template
  (`'[data-testid="select-option-{}"]'`), `select_page_size(n)`, `click_next_page()`,
  `get_pagination_total()`, `get_row_names()`.
- **No network wait anywhere in this flow** — the list GET happens once on navigate; page
  and page-size changes are pure React state. Use auto-retrying `expect` assertions
  (`to_have_count` / `to_have_text`), never a sleep.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate with more than 10 secrets | populated, multi-page table | Step 1 | total parsed from the range label asserted `> 10` | asserted |
| Step 2: page range shows "1–10 of N" | rendered as `1 - 10 of 121` | Step 2 | exact string built from the product's own total | asserted |
| Step 3: click the next page arrow | control responds | Step 3 | click on `secrets-pagination-next-button` | covered |
| Step 4: next set of secrets shown + range updates | `11 - 20 of 121`, different rows | Step 4 | range equality + name-set disjointness + prev enabled | asserted |
| Step 5: change "Rows per page" to a different value | select opens, `5` chosen | Step 5 | combobox click + `select-option-5` click | covered |
| Step 6: table shows the selected number of rows per page | 5 rows, `1 - 5 of 121` | Step 6 | row count == 5 + select text == `5` + range | asserted |
| Expected Final State: table shows the selected rows-per-page | as step 6 | Step 6 | same | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| page-2 names are **disjoint** from page-1 names | "the next set is shown" passes vacuously against a label-only change; the disjointness is what proves the data actually paged |
| prev disabled on page 1 / enabled on page 2 | the arrows' *state* is what proves they track the page position rather than being decorative |
| changing the page size **resets to page 1** | a real, source-backed behaviour (`handlePageSizeChange`) a user relies on; silently staying on a now-out-of-range page is a classic pagination bug |
| the total is unchanged by paging and by resizing | pagination must never alter the dataset |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure.
- Note (not a defect): the case writes the range as `"1–10 of N"` with an en dash; the
  product renders an ASCII `" - "`. Illustrative formatting in the case text, asserted
  against the real rendered string.

> **Implementation outcome (2026-08-27):** `#1203` **did** fire in the automated run —
> 32-41 occurrences per test across all five specs of this wave — even though the live
> Playwright-MCP walk of the identical flow produced **zero**. Every functional assertion
> passed; the spec is therefore **sanctioned-RED on this one signature** and flips green
> when the product fix ships. Counts commented on `#1203`; the live-vs-automated split is
> recorded in the surface digest.

## Blocked Steps
None.
