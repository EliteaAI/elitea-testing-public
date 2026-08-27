# Test Case: Token name and expiration columns are sortable

## Metadata
- **TMS ID**: ELITEA-2279
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2279.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`). **pytest marker: `@pytest.mark.p2`**
  — project convention TMS `medium` → AFS `l3_` prefix → pytest `p2` (same mapping as
  `l3_personal-tokens-page-layout-and-components_ELITEA-2277.md`).
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: **#1880** (`question` + `case-text-drift`) — case steps 2–3 assert the FIRST Token-name click
  sorts **ascending**; the product's default sort is *already* name-ascending, so the
  first click flips to **descending**. Case text is stale; the product is correct
  (reverse-masking guard — assert the live contract).

## Preconditions
- Logged-in user with **at least two** personal tokens (case step 1). Confirmed live
  2026-08-27: 5 persistent tokens under the shared `${TEST_USER}` identity —
  `for_ui_tests` (Never), `Levon` (Never), `Marian` (**Expired**), `New` (**Expired**),
  `uautomate` (Never). Unchanged since 2026-08-05.
- Tokens are **user-scoped, not project-scoped** (`useTokenListQuery({ skip:
  !user.personal_project_id })`, `PersonalTokens.jsx:32`) — the project selection is
  irrelevant to this case.
- **Read-only case.** It never creates, renames, or deletes a token. Do not seed data:
  the two `Expired` rows cannot be recreated (the create form only offers future
  expirations) and ELITEA-2284's merged test reads its `expired` branch off them.

## Test Data
### reuse-existing
- The 5 live tokens above, read-only.
- **Do not hardcode the five names.** They are shared leftover data another team member
  can add to or rename. Assert *order relations computed from the observed set*, not a
  literal list (see § Assertion shape below).

## The product's actual sort contract (source-confirmed + live-confirmed)

`TokensTable.jsx` drives the shared `useTableSort` hook
(`src/[fsd]/entities/grid-table/lib/hooks/useTableSort.hooks.js`):

```js
const { sortConfig, handleSort, sortData } = useTableSort({
  defaultField: 'name', defaultDirection: 'asc',
});
```

- **Default state on mount is already `name` / `asc`** — no click needed.
- `handleSort(field)` toggles: `direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'`.
  So clicking the *currently-active, ascending* column flips it to **descending**.
- Only two of the four columns are sortable — `TOKENS_COLUMNS` (`TokensTable.jsx:27-32`):
  `name` (`sortable: true`), `token` (`false`), `expires` (`true`), `actions` (`false`).
- Comparison is case-insensitive for strings (`aValue.toLowerCase()`,
  `useTableSort.hooks.js:50-53`) and puts `null` **last in asc / first in desc**
  (lines 45-47). `expires` is `null` for "Never" tokens and a date string otherwise
  (`calculateExpiryInDays`, `src/common/utils.jsx:692`), so the expiration sort's stable
  invariant is **dated rows before Never rows (asc), reversed (desc)**.

### Live observations (2026-08-27, real clicks unless noted)

| Action | Rendered name order | Note |
|---|---|---|
| page load, no click | `for_ui_tests, Levon, Marian, New, uautomate` | already name-**asc** |
| 1st click `Token name` | `uautomate, New, Marian, Levon, for_ui_tests` | name-**desc** ← **case says asc** |
| 2nd click `Token name` | `for_ui_tests, Levon, Marian, New, uautomate` | name-**asc** |
| 1st click `Expiration` | `Marian, New, Levon, uautomate, for_ui_tests` | dated (both Expired) first, then the 3 Never |
| 2nd click `Expiration` | `Levon, uautomate, for_ui_tests, New, Marian` | the 3 Never first, then dated |

Reproduced identically through synthesized `element.click()` and real Playwright clicks.

## Test Steps

1. Navigate to `${BASE_URL}/settings/tokens` (bare path — `.agents/testing.md`; the page
   object's `PersonalTokensPage.navigate()` already waits for the token-list GET **and**
   the first `token-row`, which is the correct branch guard — the page shows a
   `CircularProgress` ~2–2.5 s before either branch renders).
   - **Verify**: `token_row` count **≥ 2** (the case's own precondition, asserted rather
     than assumed — a 0/1-row table makes every ordering assertion vacuous).
   - **Capture** the baseline order: `names_default = [name-cell text per row, in DOM order]`.
   - **Verify (Axis 1, case title)**: exactly the two sortable columns expose a sort
     control — `[data-testid^="personal-token-sort-icon-"]` count **== 2**, and
     individually `personal-token-sort-icon-name` and `personal-token-sort-icon-expires`
     are visible while `personal-token-sort-icon-token` and
     `personal-token-sort-icon-actions` have `to_have_count(0)`.
   - **Verify (Axis 2)**: `names_default == sorted(names_default, key=str.lower)` — the
     table arrives name-ascending with no interaction. This is the fact the case text
     gets wrong, so pinning it is what stops step 2's expectation drifting back.

2. Click the **Token name** column header (`personal-token-column-header-name` — the
   whole header cell carries the `onClick`, `GridTableHeader.jsx:51`; `cursor: pointer`
   confirmed live, vs `default` on the non-sortable ones).
   - **Verify**: the rendered name order equals `sorted(names, key=str.lower, reverse=True)`
     — i.e. **descending**. ⚠️ **This is the documented divergence from case step 3.**

3. Click the **Token name** column header again.
   - **Verify**: the rendered name order equals `sorted(names, key=str.lower)` — ascending,
     and equal to `names_default` from step 1.

4. Click the **Expiration** column header (`personal-token-column-header-expires`).
   - **Verify**: every row whose `token-expiration-status` has
     `data-expiration-state != "never"` appears **before** every row whose state
     **is** `never`. (Equivalently: the list of per-row `is_never` booleans is
     non-decreasing.)
   - **Verify**: the row count is unchanged from step 1 — sorting reorders, never filters.

5. Click the **Expiration** column header again.
   - **Verify**: the relation inverts — every `never` row precedes every non-`never` row.

6. **Verify** no unexpected console errors across the whole flow (project standard; use
   `automation/utils/console_errors.collect_console_errors()`, which captures the failing
   resource URL — `.agents/testing.md` § 400/500 flavor). Surface was clean live: 0 product
   console errors (see § Known Defects for the two self-inflicted ones).

## Assertion shape — why relational, not literal

The five token names are **shared, mutable, real leftover data**. A literal
`["for_ui_tests", "Levon", ...]` expectation breaks the day anyone adds a token, and
worse, it would still *pass* if the product stopped sorting but the API happened to
return that order. Asserting `observed == sorted(observed)` proves the ordering
**property** against whatever the system actually returned — the values come from the
product either way, so this is not a weakened assertion, it is the correct one.

Same reasoning for expiration: assert the *null-partition invariant* (dated before
Never / Never before dated), not a name list. It survives a new token with a future
expiry, which a literal list would not.

`str.lower` in the key mirrors the product's own case-insensitive comparison — with
`Levon`/`Marian`/`New` capitalised and `for_ui_tests`/`uautomate` not, a
case-**sensitive** `sorted()` would produce a different expectation and fail against a
correct product.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| "Token name" header cell (clickable) | `personal-token-column-header-name` | **on-`automation/testids`; verify vs main at closure** | wired via `GridTableHeader`'s existing `columnTestIdPrefix="personal-token"`; already a `LocatorDescriptor` field (`personal_tokens_page.py:70`) |
| "Expiration" header cell (clickable) | `personal-token-column-header-expires` | same | already a field (`personal_tokens_page.py:78`) |
| "Token value" header (non-sortable) | `personal-token-column-header-token` | same | already a field; used for the sort-icon **absence** assertion |
| "Actions" header (non-sortable) | `personal-token-column-header-actions` | same | already a field; absence assertion |
| Sort control, name column | `personal-token-sort-icon-name` | **already emitted** by `columnTestIdPrefix` (`GridTableHeader.jsx:57`) | **no new testid work** — see § Known Defects note on issue #1705 |
| Sort control, expiration column | `personal-token-sort-icon-expires` | same | |
| Sort control, non-sortable columns | `personal-token-sort-icon-token` / `-actions` | **never rendered** (`isSortable` gate, `GridTableHeader.jsx:53`) | assert `to_have_count(0)` |
| Token row | `token-row` | on-`automation/testids` | existing `LocatorDescriptor` |
| Row name cell | `token-name-cell` (via `TOKEN_NAME_CELL_SELECTOR`) | on-`automation/testids` | existing `get_row_name_cell()` |
| Row expiration state | `token-expiration-status` + `data-expiration-state` | on-`automation/testids` | existing `TOKEN_EXPIRATION_STATUS_SELECTOR`; **needs a state-agnostic reader** — see § Implementer notes |

**Zero new testids required for this case.** Every handle already exists.

### ⚠️ Do NOT assert the sort-arrow rotation
The direction cue is a pure CSS `transform` (`rotate(180deg)` when active+desc,
`GridTableHeader.jsx:132-137`) behind a `transition: transform 0.2s ease`. Captured
mid-animation live as `matrix(0.907747, 0.419517, …)` — a raw `getComputedStyle` read
right after a click is a race. The **row order** is the case's real observable; the
transform is decoration. Same for the active-column `opacity: 1 vs 0.7` cue, which a
stray hover also changes (`&:hover { opacity: 1 }`).

## Implementer notes

- `PersonalTokensPage` (`automation/pages/personal_tokens_page.py`) already has every
  locator except two small additions, both class-level per the locator policy:
  - a `SORT_ICON_PREFIX_SELECTOR = '[data-testid^="personal-token-sort-icon-"]'` constant
    plus a named-icon template (reuse the existing `TOKEN_ACTION_ICON_SELECTOR` shape),
  - a **state-agnostic** expiration reader. The existing
    `TOKEN_EXPIRATION_STATUS_SELECTOR` bakes the `data-expiration-state` value into the
    selector, so it cannot answer "what state is this row in?". Add a sibling constant
    `TOKEN_EXPIRATION_STATUS_ANY_SELECTOR = '[data-testid="token-expiration-status"]'`
    and read `get_attribute("data-expiration-state")` per row.
- Add a `click_column_header(field)` / `get_row_names()` pair on the page object; the
  spec should read orders, not build locators (spec files never hold locators).
- Sorting is **client-side only** — no request fires on a header click (the list is
  already in the RTK-Query cache). Wait on the reordered DOM (`expect(...).to_have_text`
  / poll `get_row_names()`), never on a response or a sleep.
- **Sort state survives a search clear** (observed live: after Escape-clearing the search
  the expiration-desc order was retained). Irrelevant here, relevant to ELITEA-2287 if
  the two ever share a spec — they should not.
- Pagination: `DEFAULT_PAGE_SIZE = 10`, 5 rows → one page, so the DOM holds the whole
  sorted set. If the token count ever exceeds 10, the visible order is the *first page*
  of the sorted set and the assertions still hold for that page.

## Implementation outcome (test-automation-engineer, 2026-08-27)

- Shipped as `automation/tests/ui/admin/test_personal_tokens_column_sorting.py`
  (`TestPersonalTokensColumnSorting`), steps 1-6 mapping 1:1 to § Test Steps above.
- **Waits, as specced (no sleeps, no response waits — sorting is client-side):** the two
  name-sort steps use `expect(row_name_cell).to_have_text(<expected order>)`, whose list
  form also pins the row count. The expiration steps cannot derive an exact expected order
  (group-internal order is the untouched API order), so they anchor on the FIRST row's
  state — `expect(<first row's [data-expiration-state="never"]>).to_have_count(0)` after the
  asc click, `to_have_count(1)` after the desc click — then read every row's state and
  assert the partition.
- **One assertion added beyond § Test Steps:** before the expiration steps, the spec asserts
  the live set holds **at least one dated AND at least one never** row. Without it, the
  partition invariant would pass vacuously on an all-`Never` token set — i.e. it would report
  green while proving nothing. Same class as the specced `count >= 2` precondition assertion.
- Page-object additions landed exactly as § Implementer notes prescribed
  (`SORT_ICON_PREFIX_SELECTOR`, `SORT_ICON_SELECTOR`, `TOKEN_EXPIRATION_STATUS_ANY_SELECTOR`,
  `click_column_header()`, `get_row_names()`, `get_row_expiration_states()`), plus a
  `row_name_cell` repeatable `LocatorDescriptor` so the rendered order is one auto-retrying
  assertion instead of a poll loop. **Zero new testids for this case**, as predicted.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate with ≥2 tokens | `/settings/tokens` renders the populated table | Step 1 | `token_row` count ≥ 2 | covered |
| Step 2: click Token name header | header responds, table re-sorts | Step 2 | order changes | covered |
| Step 3: table sorts **ascending** by name | ❌ product sorts **descending** on the first click (default is already asc) | Step 2 | `sorted(..., reverse=True)` | **clarification** — case text stale, filed; live contract asserted |
| Step 4: click Token name header again | header responds, table re-sorts | Step 3 | order changes | covered |
| Step 5: table sorts **descending** by name | ❌ product returns to **ascending** | Step 3 | `sorted(...)` | **clarification** — same filing; the pair is inverted, not broken |
| Step 6: click Expiration header | header responds, table re-sorts | Step 4 | order changes | covered |
| Step 7: table sorts by expiration value | dated rows first, `Never` (null) last | Step 4 | null-partition invariant | covered |
| Expected Final State: sorts by expiration | as step 7 | Steps 4–5 | both directions | covered |
| Title claim: name **and** expiration are the sortable columns | exactly 2 sort controls | Step 1 | sort-icon count == 2 + per-column presence/absence | covered |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the table is **already** name-ascending on load, before any click | it is the premise that makes step 2's first click descending; pinning it stops the stale expectation reappearing, and it is a real product contract (`defaultField/defaultDirection`) |
| the two non-sortable columns expose **no** sort control | the case title asserts *which* columns are sortable — a "sortable" claim with no negative side would pass even if all four became sortable. Also converts two previously-orphan `*-sort-icon-*` testids into referenced ones (issue #1705) |
| row **count** is unchanged across every sort | separates "sorted" from "filtered"; a regression that dropped rows while reordering would otherwise read as a pass |
| expiration sort asserted as a null-partition invariant, both directions | the reverse click is what proves the second direction exists; the invariant survives new data where a literal order would not |
| no console errors | project standard; surface clean live |

## Known Defects / Clarifications

1. **[CLARIFICATION] Case steps 2–5 have the sort directions inverted.** The product's
   default sort is name-ascending, so the *first* Token-name click yields **descending**
   and the second yields ascending — the case asserts the opposite pair. The product is
   correct and internally consistent (`useTableSort` toggle semantics, shared by every
   grid table in the app); the **case text** is stale. Per `.agents/testing.md`
   reverse-masking guard this is a case-text clarification, **not** a defect: the AFS
   asserts the live contract. Filed as **#1880** (`question` + `case-text-drift`).
2. **No product defect found.** The two console errors seen during this session were
   **self-inflicted** — an ad-hoc `fetch('/api/v2/auth/token/')` from a Playwright
   `evaluate` does not carry the app's RTK-Query auth headers on localhost, so it is
   redirected to `dev.elitea.ai/forward-auth/auth_oidc/login` and blocked by CORS,
   emitting a CORS error + an `ERR_FAILED`. Recorded in the surface digest so nobody
   mis-attributes it to the product.
3. **Issue #1705 (`columnTestIdPrefix` emits unreferenced `*-sort-icon-*` testids)** —
   this case is the first to *reference* them on an executed path (presence on the two
   sortable columns, absence on the other two). It does not settle the canon question
   for the other tables, but it removes the orphan for this one; commented on #1705.

## Blocked Steps
None.
