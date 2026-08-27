# Test Case: Secrets page loads with correct layout and components

## Metadata
- **TMS ID**: ELITEA-2330
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2330.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none for this case (see § Known Defects for the pre-existing `#1203`).

## Preconditions
- Logged-in user, project `Private` (399) selected — **121 secrets live** (confirmed
  2026-08-27 via the pagination label `1 - 10 of 121`). Secrets are PROJECT-scoped
  (`GET /api/v2/secrets/secrets/default/{project_id}`); a `403` project renders an
  identical-looking empty table (bug `#1773`) — never read "empty" as "no secrets".
- **Read-only case.** Creates nothing, deletes nothing.

## Test Data
### reuse-existing
- The live secret set, read-only. Names/values are never hardcoded — every asserted
  value is read off the rendered table (§ Assertion shape).

## The product's actual layout contract (source + live confirmed)

`SecretsContent.jsx` renders the shared `DrawerPageHeader` (`title="Secrets"`,
`showSearchInput`, `showAddButton`) over `SecretsTable.jsx`, which composes the shared
`grid-table` entity: `GridTableHeader` (`columnTestIdPrefix="secret"`), `GridTableBody`
rows and `GridTablePagination`.

`SECRETS_COLUMNS` (`SecretsTable.jsx:53-57`) is exactly:

| `field` | `label` | `sortable` |
|---|---|---|
| `name` | Name | **true** |
| `secretValue` | Value | false |
| `actions` | Actions | false |

`GridTableHeader` renders a sort control **only** for a sortable column, as
`secret-sort-icon-{field}` — so `secret-sort-icon-name` exists and the other two do not.
Pagination defaults: `DEFAULT_PAGE_SIZE: 10`, `PAGE_SIZE_OPTIONS: [5, 10, 50, 100]`.

### Live observations (2026-08-27, project 399)

| Observable | Value |
|---|---|
| `secrets-page-title` | `Secrets` |
| `secrets-search-input` | native `<input>`, placeholder `Search`, value `""` |
| `secrets-add-button` | present, enabled |
| `secret-column-header-*` | `name`→`Name`, `secretValue`→`Value`, `actions`→`Actions` (exactly 3) |
| sort icons | `secret-sort-icon-name` only (count 1) |
| `secret-row` | 10 |
| `secret-name-cell` / `secret-value-cell` | 10 / 10, values `{{secret.<name>}}` |
| `secret-row-visibility-toggle-button` / `secret-row-actions-button` | 10 / 10 |
| `secrets-pagination-info` | `1 - 10 of 121` |
| prev / next arrows | prev `disabled=true` (page 1), next `disabled=false` |
| rows-per-page select | renders `10`; label text "Rows per page:" present |

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets` (`SecretsPage.navigate()` already waits
   for the secrets-list GET and the first `secret-row`).
   - **Verify**: `secret_row` count ≥ 1 (populated path reached, so every later
     per-row assertion is non-vacuous).

2. **Verify the page header** shows exactly `Secrets` (`secrets-page-title`).

3. **Verify a Search input is present** (`secrets-search-input`): visible, placeholder
   exactly `Search`, value empty.

4. **Verify the "+" button is present** (`secrets-add-button`): visible and enabled.

5. **Verify the table has exactly three columns** — `secret-column-header-name` /
   `-secretValue` / `-actions` with texts `Name` / `Value` / `Actions`, AND
   `[data-testid^="secret-column-header-"]` count == 3 (the bi-directional half: no
   fourth column). **Verify Name is the sortable one**: `secret-sort-icon-name` visible,
   `secret-sort-icon-secretValue` and `secret-sort-icon-actions` `to_have_count(0)`.

6. **Verify each rendered row's anatomy** — for every one of the `n` rendered rows:
   a name cell (`secret-name-cell`, non-empty), a value cell (`secret-value-cell`)
   reading exactly `{{secret.<that row's name>}}`, an eye toggle
   (`secret-row-visibility-toggle-button`) and a three-dot menu button
   (`secret-row-actions-button`). Assert by **count equality against the row count**
   (`n` name cells, `n` value cells, `n` eye buttons, `n` dots buttons) plus the
   per-row name↔value correspondence — not "at least one exists".

7. **Verify the pagination controls**: `secrets-pagination-info` matches
   `^\d+ - \d+ of \d+$` and, on the first page, starts at `1 - `; the rows-per-page
   select renders `10` (the product default); the prev arrow is **disabled** and the
   next arrow is **enabled** (121 > 10 rows). Row count == `min(10, total)` parsed out
   of the range label.

8. **(Axis 2)** No unexpected console errors across the flow
   (`automation/utils/console_errors.collect_console_errors`), with the pre-existing,
   filed `#1203` React "Maximum update depth exceeded" recorded as an isolated
   soft failure per the surface's established idiom.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Page title | `secrets-page-title` | on-`automation/testids` (also on `main`) | existing `LocatorDescriptor` |
| Search input | `secrets-search-input` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 on `automation/testids` | `DrawerPageHeader`'s existing `slotProps.searchInput.testId` prop; lands on the native `<input>` via `SimpleSearchBar`'s `inputProps` |
| "+" button | `secrets-add-button` | on-`automation/testids` | existing field |
| Column headers | `secret-column-header-{field}` | on-`automation/testids` | existing `SECRET_COLUMN_HEADER_SELECTOR` template |
| Sort control | `secret-sort-icon-{field}` | on-`automation/testids` | emitted by `GridTableHeader` from the same `columnTestIdPrefix="secret"` — **new page-object constant needed** |
| Row / name cell / value cell | `secret-row` / `secret-name-cell` / `secret-value-cell` | on-`automation/testids` | existing fields |
| Eye toggle / dots menu | `secret-row-visibility-toggle-button` / `secret-row-actions-button` | on-`automation/testids` | existing fields |
| Pagination range | `secrets-pagination-info` | on-`main` | existing field |
| Prev / next arrows | `secrets-pagination-prev-button` / `secrets-pagination-next-button` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 | `GridTablePagination`'s existing `prevButtonTestId`/`nextButtonTestId` props, same wiring as `artifacts-`/`notifications-pagination-*` |
| Rows-per-page select | `secrets-pagination-page-size-select` (+ auto `-combobox`) | **ADDED this session** — EliteaAI/EliteaUI@249c0186 | `pageSizeSelectTestId`; `SingleSelect` derives the `-combobox` display-node testid itself |

**All four new testids are pure additive props on pre-existing components** — no DOM
node, no hook, no state, nothing removed (zero-functional-impact rule satisfied).

## Assertion shape
Relational and read-off-the-product, never literal: the row anatomy is asserted as
counts equal to the observed row count and as `value == "{{secret." + name + "}}"`
computed from the name the product itself rendered. A hardcoded name list would break
the day anyone adds a secret and would still pass if the product stopped rendering the
reference format correctly for new rows.

## Implementer notes
- Page-object additions: a `SECRET_SORT_ICON_SELECTOR` class template + `sort_icon(field)`,
  `page_size_select` / `page_size_select_combobox` / `prev_page_button` /
  `next_page_button` / `search_input` `LocatorDescriptor`s, and small readers
  (`get_row_names()`, `get_row_values()`, `get_pagination_total()`). Spec files hold no locators.
- Everything on this page is **client-side** after the initial list GET — never wait on a
  network response for a layout assertion; use auto-retrying `expect` assertions.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Secrets | populated page loads | Step 1 | `secret_row` count ≥ 1 after the list GET | asserted |
| Step 2: header shows "Secrets" | exact text `Secrets` | Step 2 | `expect(page_title).to_have_text("Secrets")` | asserted |
| Step 3: Search input present top-right | `Search`-placeholder input | Step 3 | visible + placeholder + empty value | asserted |
| Step 4: "+" button present top-right | enabled add button | Step 4 | visible + enabled | asserted |
| Step 5: three columns Name (sortable ↕) / Value / Actions | exactly those 3; only Name sortable | Step 5 | header texts + count==3 + sort-icon present/absent | asserted |
| Step 6: each row shows name, masked `{{secret.name}}`, eye icon, three-dot menu | all four per row | Step 6 | count equality vs row count + per-row name↔value equality | asserted |
| Step 7: pagination — rows-per-page selector, range label, prev/next arrows | `10`, `1 - 10 of 121`, prev disabled / next enabled | Step 7 | format regex + select text + both arrows' enabled state | asserted |
| Expected Final State: pagination controls shown | as step 7 | Step 7 | same | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| exactly **three** column headers (no fourth) | "the table has three columns" is only half-checked by finding three; a regression adding a column would otherwise pass |
| the two non-sortable columns expose **no** sort control | the case marks Name specifically as the sortable one; without the negative the claim passes even if all three became sortable |
| prev arrow disabled / next arrow enabled on page 1 | the case asks for "prev/next arrows"; presence alone would pass on two dead buttons — their enabled state is what proves they are wired to the page position |
| per-row `value == "{{secret." + name + "}}"` correspondence | "masked value in `{{secret.name}}` format" is only meaningful against *that row's* name; a shared/stale value would satisfy a format-only regex |
| no console errors (with `#1203` isolated) | project standard |

## Known Defects / Clarifications
- **`#1203` (OPEN)** — React "Maximum update depth exceeded" on `/settings/secrets`
  mount. Not observed during this session's live exploration (0 occurrences across the
  full flow) but deterministic 3/3 in ELITEA-2336's automated run. Handled as an
  **isolated soft failure** (sanctioned-RED per `.agents/testing.md` § Merge gate) with
  the same `soft_failures`/`pytest.fail()` idiom the sibling secrets specs already use —
  never filtered away.

## Blocked Steps
None.
