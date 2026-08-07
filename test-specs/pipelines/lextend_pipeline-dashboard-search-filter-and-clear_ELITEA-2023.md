# Test Case: Pipeline Dashboard — Search filters the grid and Clear restores it

## Metadata
- **TMS ID**: ELITEA-2023
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `elitea-2023-pipeline-dashboard-search`
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_management.py`,
class `TestSearchPipeline` (lines 333–370), merged to `origin/automation/base`
(commit `7c2d2e5b`, "feat: add allure.step() to all UI tests for better Allure
reporting").

**Behavioural overlap (what's already proven).** `TestSearchPipeline` already
covers:
- `test_search_pipeline_by_name` (lines 338–354) — a fresh pipeline created via
  `pipeline_api` is discoverable via `PipelinesListPage.search_and_wait_for_results(name)`.
- `test_search_pipeline_no_results` (lines 356–370) — a nonsense term produces
  no visible match.

**Important caveat the implementer must know** (this is the crux of the gap,
not a nitpick): `PipelinesListPage.search()` (`automation/pages/
pipelines_list_page.py:122-131`) only does `search_input.fill(query)` — it
never presses Enter or clicks the send icon. Per live source read of
`EliteaUI/src/components/SearchBar.jsx` (shared by Pipelines/Agents/MCP/
Credentials/Toolkits/Skills dashboards), `onChange` (typing) only updates
local input state and opens a **suggestions popover** (a real, API-backed
autocomplete — `SuggestionList.jsx` → `useSearch().getSuggestion()`, debounced
500ms); the actual filter dispatch that narrows the **dashboard grid**
(`onSearch()` → redux `actions.setQuery` + `navigateWithTags`) fires **only**
from `onKeyDown === 'Enter'` or a click on `data-testid="search-send-button"`.

So the two existing tests are real and pass, but they exercise the
**suggestions popover**, not the dashboard-grid filter ELITEA-2023 actually
asks about (case Step 4: "filtered results show only pipelines containing
'YAML'" — read in context of the dashboard's card/table grid, confirmed via
live execution below). This is not a defect (see filed clarification,
`EliteaAI/elitea-testing-public#1302`) — it is a page-object gap: sibling
list pages already fixed this correctly (`automation/pages/mcp_list_page.py`
lines 203–224, `automation/pages/credentials_list_page.py`) — their
`search()` types, then `press("Enter")`, then waits for network + a settle.
`PipelinesListPage.search()` predates that fix and needs the same change.

## Preconditions
- User is logged in (`auth_state` on localhost).
- Project `Private` (id `${ELITEA_PROJECT_ID}`) has ≥1 pre-existing pipeline
  NOT matching "YAML" (satisfied — 10 pre-existing pipelines observed live,
  none named "YAML*").
- A pipeline whose name contains "YAML" must exist — **not present in current
  live data**, so this AFS's own test creates one via `pipeline_api` directly
  (NOT the generic `pipeline_id` fixture — see Test Data below, name-length
  reasoning).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- A pipeline named `autotest_YAML_search_<short-suffix>` created via
  `pipeline_api.create_pipeline(name=..., description=...)` directly (NOT the
  `pipeline_id` fixture — that fixture derives the name from
  `f"autotest_{request.node.name}"[:32]`, and a sufficiently descriptive test
  function name truncates to 32 chars *before* reaching "yaml", losing the
  match term entirely. Confirmed live: probe pipeline
  `autotest_YAML_search_probe` (26 chars) created directly, id `8043`,
  cleaned up via `pipeline_api.delete_pipeline(8043)` after the probe —
  confirmed 400/"No application found" on re-fetch).
- Cleanup: `pipeline_api.delete_pipeline(pipeline_id)` in `finally`, same
  pattern as `TestPipelineIsolation::test_fixture_cleanup_cycle` (lines
  392–398 of the covering file).

## Test Steps

1. Navigate to `/pipelines/all` (`PipelinesListPage.navigate()`).
   - **Verify**: dashboard grid shows the pre-created pipeline(s), including
     the one whose name contains "YAML".
2. Verify the search input's placeholder reads exactly `Let's find something
   amazing!` (case Step 2 — not currently asserted anywhere; only visibility
   is asserted in `test_pipeline_dashboard_loads`, `test_pipeline_management.py:61-62`).
3. Type "YAML" into the search input, then press **Enter** (real activation —
   see Extension target above; NOT the current `search()` method as-is).
   - **Verify**: search input value is "YAML" (case Step 3).
4. Verify the dashboard grid, once settled, shows **only** pipeline(s) whose
   name contains "YAML" — both directions:
   - the "YAML" pipeline IS visible in the grid
   - a pipeline that does NOT match (e.g. one of the pre-existing
     `test-pipeline` / `probe-pipeline` names) is NOT visible in the grid
   (case Step 4 — the existing covering spec only asserts the first
   direction, via the suggestions popover, never the second).
5. Click the search input's Clear (X) icon (`data-testid="search-clear-button"`).
   - **Verify**: search input is empty (case Step 5).
6. Verify the dashboard grid is restored to the full, unfiltered list —
   both the "YAML" pipeline and the previously-hidden non-matching
   pipeline(s) are visible again, and the URL stays on `/pipelines/all`
   (case Step 6 — entirely uncovered by the existing spec; no existing test
   calls `clear_search()` on `PipelinesListPage` at all).

## Expected Results
- Search input placeholder is exactly `Let's find something amazing!`.
- Typing alone (no Enter/click) does NOT narrow the dashboard grid — only
  opens the suggestions popover (informational; not itself asserted by this
  AFS, already implicitly exercised by the covering spec).
- After Enter, the grid narrows to exactly the pipeline(s) matching "YAML" —
  confirmed live: with 1 pipeline named `autotest_YAML_search_probe` among 11
  total, searching "YAML" + Enter left exactly 1 card in the grid.
- After Clear, the grid is restored to all pipelines (confirmed live: all 11
  reappeared, including the ones hidden during the filtered state), and the
  page stays on `/pipelines/all` — **no redirect to `/pipelines/create`**
  (see Known Defects — this is a clean negative finding, not a gap).
- No console errors during type/search/clear (confirmed:
  `browser_console_messages(level="error")` → 0 errors across the whole
  live session).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Pipelines dashboard | Full list loads | step 1 | step 1: grid populated | asserted |
| 2 Locate search textbox, placeholder "Let's find something amazing!" | Textbox visible | step 2 | step 2: placeholder text equality | asserted |
| 3 Type "YAML" in the search box | Input populated with "YAML" | step 3 | step 3: input value | asserted |
| 4 Verify filtered results show only pipelines containing "YAML" | Only matching pipelines shown | step 4 | step 4: match visible AND non-match hidden | asserted |
| 5 Clear search text | Search field empty | step 5 | step 5: input value empty | asserted |
| 6 Verify full pipeline list is restored | All pipelines visible again | step 6 | step 6: matching + previously-hidden pipeline both visible, URL unchanged | asserted |

**Axis 2 — Analyst additions**

- Console-error check across the whole search/filter/clear flow — *added:
  silent failures are the worst bugs per skill discipline; zero-cost given
  the live session was already open.*
- URL-stays-on-`/pipelines/all`-after-clear assertion — *added: the sibling
  MCP (`#585`) and Credentials (`#551`) list pages have a confirmed defect
  where clearing a zero-match search redirects to their `/…/create` page;
  Pipelines does NOT reproduce this (confirmed live, see Known Defects), but
  the implementer should assert the URL explicitly so a future regression to
  the same pattern is caught, not just "some pipelines are visible".*

## Cleanup
1. `pipeline_api.delete_pipeline(pipeline_id)` for the "YAML"-named pipeline
   created in Test Data, in a `finally` block (matches
   `TestPipelineIsolation::test_fixture_cleanup_cycle` pattern already in the
   covering file).

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy. No
role/label/text ladder; every handle below is a `data-testid`, all
**already exist and are already wired** in `PipelinesListPage`
(`automation/pages/pipelines_list_page.py`) — no new testid work needed.

| Element | Testid | LocatorDescriptor (existing) | Provenance |
|---|---|---|---|
| Search input | `pipeline-search-input` | `PipelinesListPage.search_input` (line 29) | on-main ✓ (confirmed live: `page.getByTestId('pipeline-search-input')` resolved) |
| Search clear (X) icon | `search-clear-button` | **not yet a class field** — implementer needs to add `search_clear_button = LocatorDescriptor(testid="search-clear-button")` to `PipelinesListPage` (mirrors `mcp_list_page.py`'s existing `search_clear_button` field) | on-main ✓ (confirmed live via `SearchBar.jsx`: `data-testid="search-clear-button"`, and via click resolving to `page.getByTestId('search-clear-button')`) |
| Search send icon (alternate activation) | `search-send-button` | not currently used by any Pipelines page-object method; not required for this AFS (Enter is sufficient and is what step 3 uses) | on-main ✓ (`SearchBar.jsx`: `data-testid="search-send-button"`) |
| Pipelines page header (load proxy) | `pipelines-page-header` | `PipelinesListPage.page_header` (line 36) | on-main ✓ (already used by `wait_for_page_load`) |
| Pipeline card/row name (grid item) | no testid — the existing `pipeline_exists_in_list(name)` method (`pipelines_list_page.py:104-120`) locates by `page.locator(f'text="{name}"')`, a **legacy raw-text handle inside a page-object method**, tracked tech debt per `.agents/testing.md` § "Existing raw handles in `automation/pages/` are tracked tech debt" — not to be treated as precedent for new code, but also not a step-4/6 blocker (case only needs presence/absence-by-name, and this method already exists and works, confirmed live). Implementer may keep using it as-is; adding a `pipeline-card-name`/`pipeline-row-name` testid is a nice-to-have, not required by this AFS's Coverage Map — flag as a `question`/optional-scope item only if it becomes ambiguous with duplicate pipeline names (this env has 5 identically-named `test-pipeline` items, so absence-checking on a UNIQUE name like the generated "YAML" pipeline avoids the ambiguity entirely). | pre-existing method, unchanged |

**`PipelinesListPage.search()` needs updating** (not a new locator, a
behavior fix) to mirror `mcp_list_page.py::search()` (lines 203-224):
```python
def search(self, query: str):
    self.search_input.click()
    self.search_input.press_sequentially(query, delay=20)
    self.search_input.press("Enter")
    self.wait_for_network()
    self.page.wait_for_timeout(1000)  # confirmed live: ~1-2s settle after Enter
```
This is additive/corrective to an **already-merged** page object — the two
existing tests (`test_search_pipeline_by_name`, `test_search_pipeline_no_results`)
keep passing with this change (their assertions don't depend on the grid
staying unfiltered), and become MORE correct (they now exercise the real
filter, not just the suggestions popover).

## Network Behavior
- No new XHR observed firing on Enter — filtering appears client-side
  against an already-fetched pipeline list (same as documented for MCP,
  `mcp_list_page.py:212-213`). Wait strategy is network-idle + a short
  settle, not a response predicate.
- The suggestions popover DOES fire its own XHR while typing (before Enter)
  — irrelevant to this AFS's assertions, noted for completeness only.

## Known Defects Found During Exploration
- **None found for Pipelines.** Checked explicitly against the confirmed
  sibling pattern (`EliteaAI/elitea-testing-public#585` — MCP list, and
  `#551` — Credentials list: clearing a **zero-match** search redirects to
  the entity's `/create` page instead of restoring the list). Reproduced the
  same trigger conditions here (searched "YAML" with zero pre-existing
  matches → "No pipelines yet" empty state → clicked Clear) and the
  Pipelines dashboard correctly restored the full list and stayed on
  `/pipelines/all` — **not reproduced**. No sibling ticket filed; this AFS's
  step 6 asserts the URL explicitly as a regression guard (Axis 2).
- **Case-text drift (not a defect)**: filed as clarification
  `EliteaAI/elitea-testing-public#1302` — the case's Steps 3–4 imply typing
  alone filters the grid; live product requires Enter or the send-icon click
  (see Extension target above for the full mechanism).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches covering spec).
- Extend `TestSearchPipeline` in
  `automation/tests/ui/pipelines/test_pipeline_management.py` with new test
  method(s) covering steps 2–6 above (e.g.
  `test_search_placeholder_and_dashboard_grid_filters_and_clears`); don't
  duplicate the existing two tests' popover-based assertions.
- Update `PipelinesListPage.search()` per § Concrete Handles above; add
  `search_clear_button` LocatorDescriptor.
- Use `pipeline_api.create_pipeline()` directly (not the `pipeline_id`
  fixture) for the "YAML"-named pipeline, per Test Data reasoning.
- For absence assertions (non-matching pipeline hidden after filter, and
  reappearing after clear), pick a pre-existing pipeline name that is
  reasonably unique in this env's data if possible; if only duplicate
  names (`test-pipeline` ×5) are available, asserting the VISIBLE COUNT of
  matches (1, for the unique "YAML" pipeline) plus the total grid count
  returning to its pre-search value after Clear is an equally valid
  (and duplicate-name-proof) way to satisfy the same Coverage Map row.
