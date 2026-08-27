# Test Case: Search field filters tokens by name in real time

## Metadata
- **TMS ID**: ELITEA-2287
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2287.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: none — the product matches the case text on every step.

## Preconditions
- Logged-in user with **at least two tokens with different names** (case step 1).
  Confirmed live 2026-08-27: 5 persistent tokens — `for_ui_tests`, `Levon`, `Marian`,
  `New`, `uautomate`.
- Tokens are **user-scoped, not project-scoped** — project selection is irrelevant.
- **Read-only case.** Never create/rename/delete a token (two rows are irrecoverably
  `Expired` and ELITEA-2284's merged test depends on them).

## Test Data
### reuse-existing
- The 5 live tokens, read-only.
- **Search terms are derived at runtime, not hardcoded.** Take a name from the observed
  set and slice it — e.g. `probe = names[0][:3]`, plus its `.upper()` and `.lower()`
  forms for the case-insensitivity step. This survives someone adding or renaming a
  token; a literal `"Lev"` does not. (Terms actually exercised live: `Lev` → `Levon`;
  `AUTO` → `uautomate`; `AUTOzzz` → no match.)

## The product's actual filter contract (source-confirmed + live-confirmed)

- `PersonalTokens.jsx:31` holds `const [search, setSearch] = useState('')` and passes
  `slotProps.searchInput = { placeholder: 'Search tokens...', search,
  onChangeSearch: setSearch, testId: 'personal-tokens-search-input' }` to the shared
  `DrawerPageHeader`.
- `DrawerPageHeader.jsx:63-70` wires it onto `Input.SimpleSearchBar` as
  `onSearchChange={onChangeSearch}` — and `SimpleSearchBar.jsx:21-26,55` calls it from
  the native `onChange`. **Filtering is per-keystroke; there is no Enter, no submit
  button, no debounce.** (Interaction-discovery ladder resolved at its decisive step —
  source — per `.agents/role-overrides.md`; this is *not* the `SearchBar.jsx` /
  issue #44 Enter-activated component.)
- `TokensSection.jsx:19-22` does the filtering:
  ```js
  return tokens.filter(token => token.name.toLowerCase().includes(search.toLowerCase()));
  ```
  → **substring match, both sides lower-cased ⇒ case-insensitive**, name-only (never the
  token value or expiration).
- `DrawerPageHeader.jsx:37` also wires `onSearchClear={() => onChangeSearch('')}`, which
  `SimpleSearchBar.jsx:28-33` fires on **Escape**.
- The search input is `autoFocus` (`SimpleSearchBar.jsx:39-46`, a 100 ms `setTimeout`
  focus after mount).

### Live observations (2026-08-27, real keystrokes)

| Input | Search value | Rows rendered |
|---|---|---|
| (none) | `""` | 5 — `for_ui_tests, Levon, Marian, New, uautomate` |
| typed `Lev` | `Lev` | **1** — `Levon` |
| replaced with `AUTO` | `AUTO` | **1** — `uautomate` (case-insensitive ✓) |
| appended `zzz` | `AUTOzzz` | **0** rows, and the column headers unmount too |
| `Escape` | `""` | 5 again, column headers back |
| `Ctrl/Cmd+A` then `Backspace` | `""` | 5 again |

## Test Steps

1. Navigate to `${BASE_URL}/settings/tokens` (`PersonalTokensPage.navigate()` already
   waits for the token-list GET and the first `token-row`).
   - **Verify**: `token_row` count **≥ 2** (the case's own precondition, asserted).
   - **Verify**: `personal-tokens-search-input` is visible with placeholder exactly
     `Search tokens...`, and its value is empty.
   - **Capture** `names_all = [name-cell text per row]` and `count_all = len(names_all)`.
   - Derive `probe = names_all[0][:3]` and `expected = [n for n in names_all if
     probe.lower() in n.lower()]`.

2. Type `probe` into the search field **one character at a time**
   (`press_sequentially`), **without pressing Enter**.
   - **Verify**: the input's value equals `probe` (case step 2 — "field accepts the
     input and displays the entered value").

3. **Verify** the table filtered in real time:
   - rendered name list == `expected` (as sets/lists — the sort order is orthogonal),
   - `token_row` count == `len(expected)` and **< `count_all`** (proves something was
     actually removed; equal counts would pass a broken filter).
   - No Enter was pressed and no submit control was clicked — that is the "real time"
     claim, and it is what this step proves.

4. **Verify case-insensitivity** (case step 4): clear the field and type
   `probe.upper()`; then clear and type `probe.lower()`.
   - **Verify** both produce the identical rendered name list as step 3.
   - Live proof point: `AUTO` (uppercase) matched `uautomate` (lowercase).

5. **Clear the search field** and **verify all tokens are shown again** (case step 5).
   - **Verify**: the input value is `""`, `token_row` count == `count_all`, and the
     rendered names are the same **set** as `names_all`.
   - Clearing technique — both confirmed live on this input, pick one and keep it in the
     page object: `Control/Meta+A` then `Backspace`, or `Home` → `Shift+End` →
     `Backspace`. ⚠️ The digest's "`Control+a` is unreliable" warning is scoped to the
     **create-token Name field** (whose `useAutoBlur` refocus races the shortcut);
     `SimpleSearchBar` is a plain MUI `InputBase` with no auto-blur and `Control+a`
     worked reliably here.

6. **Verify** no unexpected console errors (project standard;
   `automation/utils/console_errors.collect_console_errors()`).

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Search input | `personal-tokens-search-input` | **on-`automation/testids`; verify vs main at closure** | already a `LocatorDescriptor` field (`personal_tokens_page.py:58`); resolves to the **native `<input>`** (wired through `SimpleSearchBar`'s `inputProps`), so `.input_value()` / typing work directly — unlike the delete-dialog field on this same page object |
| Token row | `token-row` | on-`automation/testids` | existing field |
| Row name cell | `token-name-cell` | on-`automation/testids` | existing `get_row_name_cell()` |
| Column headers (for the no-match absence assertion) | `personal-token-column-header-*` | on-`automation/testids` | existing fields |
| No-match empty message | **testid needed: `personal-tokens-table-empty-message`** | **needs-adding** | only required for the Axis-2 no-match step — see below |

### The one new testid (Axis-2 only)
`GridTableContainer` (`src/[fsd]/entities/grid-table/ui/GridTableContainer.jsx:37-45`)
renders `emptyMessage` (here `"No tokens"`, set at `TokensTable.jsx`) in a bare
`<Typography>` with **no testid and no testid prop**. It is a **shared** component, so
per `.agents/testing.md` § "shared components never hardcode feature-scoped testids" the
fix is a caller-supplied prop — add `emptyMessageTestId` to `GridTableContainer` and pass
`emptyMessageTestId="personal-tokens-table-empty-message"` at the `TokensTable.jsx` call
site. Same "thread an existing-shape prop" pattern as `columnTestIdPrefix` /
`nameCellTestId` already used by this very table; no DOM node added, no hook added
(zero-functional-impact rule satisfied).

If the implementer would rather not touch a shared component for a beyond-case
assertion, the fallback is to drop the *message text* assertion and keep the structural
half of the no-match step (row count 0 + column headers absent), which needs **no new
testid**. Escalate to the lead rather than substituting a role/text handle.

## Implementer notes

- Page-object additions (all class-level): a `type_search(text)` /
  `clear_search()` / `get_row_names()` trio on `PersonalTokensPage`. Spec files hold no
  locators.
- **Filtering is client-side** — `TokensSection` filters an already-cached RTK-Query
  array. **No network request fires on a keystroke.** Never wait on a response; poll the
  rendered rows (`expect(page.token_row).to_have_count(n)`), never a sleep.
- **The no-match state is NOT the empty-state page.** With zero matches,
  `GridTableContainer.isEmpty` renders the `"No tokens"` message *and unmounts the four
  column headers*, while the page header/search bar stay. The `EmptyStatePage`
  (`empty-state-title` = "No tokens yet") belongs to the **zero-tokens-exist** branch and
  is **not** reachable by searching (confirmed live: `empty-state-title` absent with 0
  matches). Do not use search to fake ELITEA-2278/2250's empty state — different
  component, different observable.
- **Sort state is orthogonal and survives a search clear** (observed live: after
  Escape-clearing, the previously-applied expiration-desc order was retained). So step 5
  must compare name **sets**, not ordered lists, unless the spec also pins the sort.
- `autoFocus` puts the caret in the search box ~100 ms after mount; clicking the field
  first is harmless but unnecessary.
- Do **not** merge this spec with ELITEA-2279's. Different control, different steps,
  different observable — a shared parameterized spec would make one case's assertions
  carry the other's (see `test-case-analysis` § family-vs-separate).

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate with ≥2 differently-named tokens | populated table renders | Step 1 | `token_row` count ≥ 2 | covered |
| Step 2: type a partial name in "Search tokens..." | field accepts + displays the value | Step 2 | input value == probe; placeholder pinned in Step 1 | covered |
| Step 3: table filters in real time to matching names | per-keystroke substring filter on `name` | Step 3 | rendered names == expected; count < count_all | covered |
| Step 4: search is case-insensitive ("AUTO" matches "autotest-token") | both sides lower-cased ⇒ yes; live `AUTO` → `uautomate` | Step 4 | upper- and lower-case probes give identical results | covered |
| Step 5: clear the field — all tokens shown again | full set restored | Step 5 | value == ""; count == count_all; same name set | covered |
| Expected Final State: cleared search shows all tokens | as step 5 | Step 5 | same | covered |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| filtered count is strictly **less** than the unfiltered count | "shows only matching names" passes vacuously if the filter is a no-op on a set where everything matches; the strict inequality is what makes step 3 a real check |
| a deliberately non-matching term yields **0 rows** + the `"No tokens"` message | proves the filter can actually exclude everything, and pins the no-match branch as distinct from the zero-tokens `EmptyStatePage` — a regression conflating them would otherwise be invisible |
| the placeholder text is exactly `Search tokens...` | the case names the field by that placeholder; if it changes, this case's step 2 is ambiguous |
| no Enter / submit is used anywhere | "real time" is the case's actual subject; a test that pressed Enter would pass even on an Enter-activated redesign |
| no console errors | project standard; surface clean live |

## Known Defects / Clarifications
None — the product matches the case on every step, including the case's own
case-insensitivity example. (The two console errors observed during this session were
self-inflicted by an ad-hoc in-page `fetch` to the API; see the surface digest.)

## Blocked Steps
None.
