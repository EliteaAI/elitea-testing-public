# Test Case: Search field filters secrets by name

## Metadata
- **TMS ID**: ELITEA-2334
- **Source case**: `.agents/automation/settings-w05/cases/ELITEA-2334.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`) → **pytest marker `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, project `Private` / 399, 121 secrets)
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (Axel), combined slot, batch `settings-w05`, 2026-08-27
- **Status**: **ready-for-automation**
- **Surface digest**: `test-specs/settings-secrets/_surface.md`
- **Filed**: none — the product matches the case text on every step.

## Preconditions
- Project `Private` (399) with **≥ 2 secrets with different names** — 121 live.
- **Read-only case.** Filtering is pure client-side state.

## Test Data
### reuse-existing
- The live secret set, read-only.
- **The search term is derived at runtime, not hardcoded.** Walk the observed names and
  take the first prefix that filters to a **proper, non-empty subset** (so the
  strict-inequality assertion is achievable against whatever data exists), then use its
  `.upper()` and `.lower()` forms for the case-insensitivity step. Terms actually
  exercised live: `pgvector` → `pgvector_project_connstr`, `pgvector_project_password`;
  `PGVECTOR` → the identical two rows.

## The product's actual filter contract (source + live confirmed)

- `SecretsContent.jsx:25` holds `const [search, setSearch] = useState('')` and passes
  `slotProps.searchInput = { placeholder: 'Search', search, onChangeSearch: setSearch,
  testId: 'secrets-search-input' }` to the shared `DrawerPageHeader`.
- `DrawerPageHeader.jsx` wires it to `Input.SimpleSearchBar` as `onSearchChange`, which
  `SimpleSearchBar.jsx` fires from the native `onChange` — **per-keystroke; no Enter, no
  submit button, no debounce** (interaction-discovery ladder resolved at its decisive
  step, source, per `.agents/role-overrides.md`; this is *not* the Enter-activated
  `SearchBar.jsx` of issue #44).
- `SecretsContent.jsx:58-64` does the filtering:
  ```js
  secretsList.filter(secret => secret.name.toLowerCase().includes(search.toLowerCase()))
  ```
  → **substring match, both sides lower-cased ⇒ case-insensitive**, **name-only** (never
  the `{{secret.…}}` value).
- `DrawerPageHeader` also wires `onSearchClear` → `onChangeSearch('')`, fired on Escape.
- The filtered set feeds pagination, so the range label re-totals to the match count.

### Live observations (2026-08-27, project 399)

| Input | Rows rendered | `secrets-pagination-info` |
|---|---|---|
| `""` | 10 of 121 | `1 - 10 of 121` |
| `pgvector` | 2 — `pgvector_project_connstr`, `pgvector_project_password` | `1 - 2 of 2` |
| `PGVECTOR` | the identical 2 | `1 - 2 of 2` |
| cleared | full set restored | `1 - 10 of 121` |

## Test Steps

1. Navigate to `${BASE_URL}/settings/secrets`.
   - **Verify**: `secret_row` count ≥ 2 and the total (parsed from the range label) ≥ 2 —
     the case's own precondition, asserted.
   - **Verify**: `secrets-search-input` is visible, placeholder exactly `Search`, value
     empty.
   - **Capture** `total_all` (from the range label) and the full name set. Because the
     project holds 121 secrets across pages, the **full name set is read by raising the
     page size to `100`** — the filter must be compared against the *whole* dataset, not
     just page 1, or "shows only matching names" becomes a page-1 statement. Derive the
     probe from that full set.

2. Type the probe into the search field **one character at a time**
   (`press_sequentially`), **without pressing Enter**.
   - **Verify**: the input's value equals the probe (case step 2 — "field accepts the
     input and displays the entered value").

3. **Verify the table filters to only matching secret names**:
   - the rendered name set == `{n for n in all_names if probe.lower() in n.lower()}`,
   - every rendered name contains the probe case-insensitively,
   - the filtered total is **strictly less** than `total_all` (proves something was
     actually removed — equal totals would pass a no-op filter),
   - no Enter was pressed and no submit control was clicked — that IS the filter contract
     this step proves.

4. **Verify the search is case-insensitive** (case step 4): clear the field and type
   `probe.upper()`, then clear and type `probe.lower()`.
   - **Verify** both produce the **identical** rendered name set as step 3.

5. **Clear the search field — verify all secrets are shown again**:
   - the input value is `""`, the range-label total is back to `total_all`, and the
     rendered name set equals the page-1 slice of the unfiltered set.

6. **(Axis 2)** Type a deliberately non-matching term (probe + a nonsense suffix).
   - **Verify**: `secret_row` count == 0 — the filter can actually exclude everything.
     (The `"No secrets"` empty text is a bare `<span>` from the shared
     `GridTableContainer` with **no testid** and none placeable without threading a new
     prop; per `.agents/testing.md` § Locator policy the assertion stays on the
     testid-based row count, exactly as the surface digest's delete-flow note prescribes.
     `secrets-pagination-info` is **absent** in this state — asserted as `count(0)`.)

7. **(Axis 2)** No unexpected console errors (`#1203` isolated as a soft failure).

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Search input | `secrets-search-input` | **ADDED this session** — EliteaAI/EliteaUI@249c0186 on `automation/testids` | `DrawerPageHeader`'s existing `slotProps.searchInput.testId` prop; resolves to the **native `<input>`** (via `SimpleSearchBar`'s `inputProps`), so typing and `.input_value()` work directly |
| Row / name cell | `secret-row` / `secret-name-cell` | on-`automation/testids` | existing fields |
| Range label (totals + absence in the no-match branch) | `secrets-pagination-info` | on-`main` | existing field |
| Rows-per-page select / option (to read the full set) | `secrets-pagination-page-size-select-combobox` / `select-option-100` | **ADDED this session** (root) + pre-existing generic option testid | see ELITEA-2332's AFS |

## Implementer notes
- Page-object additions: `search_input` `LocatorDescriptor`, `type_search(text)`,
  `clear_search()`, `get_row_names()`. Spec files hold no locators.
- **Filtering is client-side** over the already-fetched array — **no network request fires
  on a keystroke.** Never wait on a response; poll the rendered rows with auto-retrying
  `expect` assertions.
- Clearing: `fill("")` is what the live session used and it fires React's `onChange`
  correctly on this plain MUI `InputBase` (no `useAutoBlur`, unlike the create-row Name
  field whose `Control+a` unreliability the digest documents — that warning does **not**
  apply here).
- Do **not** merge this spec with ELITEA-2331's or ELITEA-2332's — different control,
  different steps, different observable.

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate with ≥2 differently-named secrets | populated table renders | Step 1 | row count ≥ 2 + total ≥ 2 | asserted |
| Step 2: type a partial name in the Search field | field accepts + displays the value | Step 2 | input value == probe | asserted |
| Step 3: table filters to only matching secret names | per-keystroke substring filter on `name` | Step 3 | rendered set == expected set; every name contains the probe; filtered total < total_all | asserted |
| Step 4: search is case-insensitive | both sides lower-cased ⇒ yes (live `PGVECTOR` → `pgvector_*`) | Step 4 | upper- and lower-case probes give identical sets | asserted |
| Step 5: clear the field — all secrets shown again | full set restored | Step 5 | value == ""; total == total_all; page-1 set restored | asserted |
| Expected Final State: cleared search shows all secrets | as step 5 | Step 5 | same | asserted |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the filter is evaluated against the **whole dataset** (page size raised to 100 first) | with 121 secrets on 10-row pages, a page-1-only comparison would call a broken filter correct |
| filtered total is strictly **less** than the unfiltered total | "only matching names" passes vacuously if nothing was excluded |
| a non-matching term yields **0 rows** and no range label | proves the filter can exclude everything, and pins the no-match branch |
| the search never fires a network request / never needs Enter | "filters by name" as a live, client-side contract — a test that pressed Enter would pass even on an Enter-activated redesign |
| the placeholder is exactly `Search` | the case names the control by its placeholder |
| no console errors (`#1203` isolated) | project standard |

## Known Defects / Clarifications
- **#1203 (OPEN)** — React "Maximum update depth exceeded" on mount; isolated soft failure.

## Blocked Steps
None.
