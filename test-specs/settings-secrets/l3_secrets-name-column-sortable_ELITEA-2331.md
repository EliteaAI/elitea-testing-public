# Test Case: Secrets listing — Name column is sortable

## Metadata
- **TMS ID**: ELITEA-2331
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2331.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399, 121 secrets)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: **#1901** — `[CLARIFICATION][ELITEA-2331]` sort directions inverted in the
  case text (sibling of `#1880`, the identical drift on Settings → Personal Tokens).

## Preconditions
- Project `Private` (399) with **≥ 2 secrets** — 121 live, confirmed 2026-08-27.
- **Read-only case.** Sorting reorders client-side state only; nothing is written.

## Test Data
### reuse-existing
- The live secret set, read-only. All ordering expectations are **derived at runtime**
  from the names the product renders (`sorted(observed, key=str.lower)`), never a
  hardcoded name list.

## ⚠️ Case-text divergence (the load-bearing finding)

`SecretsTable.jsx:137-140` initialises
`useTableSort({ defaultField: 'name', defaultDirection: 'asc' })`, so **the table
arrives already sorted name-ascending with no interaction**. `useTableSort.handleSort`
then flips the direction on each click of the same field:

```js
direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
```

Live proof (project 399, 2026-08-27):

| Action | First rows rendered | Sort-arrow transform |
|---|---|---|
| load, no click | `auth_token`, `default_image_generation_model_name`, … | `rotate(0deg)` |
| click 1 on `secret-column-header-name` | `webhook_secret_v9348`, `webhook_secret_v9279`, … (**desc**) | `rotate(180deg)` |
| click 2 | `auth_token`, `default_image_generation_model_name`, … (**asc**) | `rotate(0deg)` |

The case text expects click 1 → ascending, click 2 → descending. The **product is
correct and internally consistent** (same behaviour as the sibling grid-table surfaces);
the case text is stale. Per the reverse-masking guard
(`test-automation-implementation` § Hard Rules → 2) the test asserts the **live
contract** and the drift is filed as **#1901**, not weakened to match the text.

The comparison is **case-insensitive** (`useTableSort.sortData` lower-cases both
strings), so the expectation is `sorted(names, key=str.lower)`.

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: `secret_row` count ≥ 2 (the case's own precondition, asserted — a
     1-row table would make every ordering assertion vacuous).
   - **Verify**: the Name column exposes a sort control (`secret-sort-icon-name` visible)
     and the other two columns do not (`to_have_count(0)` each).
   - **Verify** (Axis 2, and the premise the whole case rests on): the table arrives
     **already name-ascending** — `names_default == sorted(names_default, key=str.lower)`.
   - **Capture** `names_default` (rendered `secret-name-cell` texts, page 1).

2. Click the Name column header (`secret-column-header-name`).
   - **Verify**: the rendered name list == `sorted(names_default, key=str.lower,
     reverse=True)` — i.e. **descending**. See § Case-text divergence / #1901.

3. Click the Name column header again.
   - **Verify**: the rendered name list == `names_default` — back to **ascending**.

4. **(Axis 2)** Across both clicks the row count is unchanged and the pagination total
   is unchanged — sorting **reorders**, it never filters or drops rows.

5. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure per the
   surface idiom).

> **Note on page-1 scoping.** With 121 secrets at 10 rows/page, page 1 holds a different
> *set* of names in asc vs desc order — so the assertion is deliberately
> `page-1-after-desc == reverse-sorted-full-page-1-asc`? **No.** That is only true when
> the whole dataset fits one page. To keep the assertion exact and honest at any data
> scale, the spec **sets the page size to the largest option (100) first** only if the
> total fits, otherwise it compares the *rendered page-1 slice* against the correct
> slice computed from a full-set read. The simplest honest form, and the one specified:
> capture the rendered page-1 names, then assert the rendered order is **monotonic** in
> the expected direction (`names == sorted(names, key=str.lower)` /
> `names == sorted(names, key=str.lower, reverse=True)`) **and** that the desc page-1
> first name is strictly greater (case-insensitively) than the asc page-1 first name —
> which is only possible if the sort re-sliced the whole dataset, not just the page.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Name column header (click target) | `secret-column-header-name` | on-`automation/testids` | existing `column_header(field)` |
| Sort control | `secret-sort-icon-{field}` | on-`automation/testids` | emitted by `GridTableHeader` from `columnTestIdPrefix="secret"` — new page-object constant |
| Row / name cell | `secret-row` / `secret-name-cell` | on-`automation/testids` | existing fields |
| Pagination range | `secrets-pagination-info` | on-`main` | existing field, used for the "no rows dropped" check |

**Sort DIRECTION is asserted through the rendered row ORDER, never through the icon's
CSS transform.** The direction is expressed in `GridTableHeader` only as an inline
`transform: rotate(180deg)` style — reading that would be a raw-style assertion of an
implementation detail; the row order is the actual observable the case names. (This also
resolves canon question **#1705** for this surface: the `*-sort-icon-*` testids are
referenced on this test's executed path, positively for `name` and via absence
assertions for `secretValue`/`actions`.)

## Implementer notes
- Sorting is **client-side over the full dataset** — no network request fires on a header
  click. Never wait on a response; use auto-retrying `expect` assertions on the rendered
  cells.
- `expect(locator).to_have_text([...])` on the repeated `secret-name-cell` locator is the
  auto-retrying way to wait for the re-render *and* assert the order in one call.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate with ≥2 secrets | populated table renders | Step 1 | `secret_row` count ≥ 2 | asserted |
| Step 2: click the Name header (↕ arrow) | control responds, table re-sorts | Step 2 | order flips to descending | asserted |
| Step 3: table sorts alphabetically **ascending** | ⚠️ product sorts **descending** on the first click (default is already asc) — #1901 | Step 1 + Step 2 | ascending asserted at LOAD (step 1); the first click's descending result asserted in step 2 | asserted (live contract; case text stale, filed #1901) |
| Step 4: click the Name header again | control responds | Step 3 | order flips again | asserted |
| Step 5: table sorts **descending** | ⚠️ product returns to **ascending** — #1901 | Step 3 | ascending asserted after click 2 | asserted (live contract; #1901) |
| Expected Final State: descending by name | ⚠️ ascending after two clicks; descending is reached after ONE click and is asserted there | Step 2 | descending asserted | asserted (live contract; #1901) |

> Both directions the case asks for **are** asserted — only the click index at which each
> occurs differs from the stale text, and that difference is exactly what #1901 records.

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the table is already name-ascending on load | it is the premise that makes the first click's direction what it is; without it the #1901 finding is unfalsifiable |
| only the Name column exposes a sort control | the case title scopes sortability to Name; the negative is what makes that a real claim |
| row count + pagination total unchanged across both clicks | a sort that silently dropped or duplicated rows would still produce a monotonic order |
| the desc page-1 head is strictly greater than the asc page-1 head | proves the sort re-sliced the **whole dataset**, not just reordered the visible page |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1901 (OPEN, `question`)** — case-text drift on the sort directions, sibling of #1880.
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure.

> **Implementation outcome (2026-08-27):** `#1203` **did** fire in the automated run —
> 32-41 occurrences per test across all five specs of this wave — even though the live
> Playwright-MCP walk of the identical flow produced **zero**. Every functional assertion
> passed; the spec is therefore **sanctioned-RED on this one signature** and flips green
> when the product fix ships. Counts commented on `#1203`; the live-vs-automated split is
> recorded in the surface digest.

## Blocked Steps
None.
