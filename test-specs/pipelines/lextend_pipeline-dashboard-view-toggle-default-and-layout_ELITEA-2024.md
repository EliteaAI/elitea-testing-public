# Test Case: Pipeline Dashboard — View Toggle (Card vs Table) — default state + actual layout-format gap

## Metadata
- **TMS ID**: ELITEA-2024
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/`project_user_659` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage) — batch `pipelines-remaining-w2` (original, 2026-08-xx);
  **repair triage + re-execution 2026-09-09** (board card #2118, `[FIX][ELITEA-2024]`)
- **Status**: extend-existing (repair of the already-merged extension — see § Adjustment)

## Adjustment — 2026-09-09 (board #2118, CI run 34331579791 / DEV Stable #114)

**Triage class: D — missing data precondition (test defect). NOT UI drift, NOT a product
bug, NOT a promotion gap.** No product behaviour changed; nothing here weakens what the
test verifies (see § Rail check).

### What failed

`tests.ui.pipelines_2.test_pipeline_management.TestPipelineDashboard.test_view_toggle_table_and_card`
failed in CI at Step 7:

```
AssertionError: Card elements (entity-card-name) should render again after switching to card view
assert [] +  where [] = get_card_names()
```

Allure per-step durations: Steps 1–6 **all passed** (Step 4 switch-to-table 0.53 s, Step 6
switch-to-card 0.52 s); Step 7 failed after exactly **5.00 s** — `get_card_names()`'s own
5 s `first.wait_for(visible)` expiring. Its `?view=cards` URL assertion, which runs first
in the same step, passed. So the toggle worked perfectly; there was simply nothing to render.

### The evidence that forces the classification

1. **The failure screenshot** (`/tmp/ci2118/evidence/ELITEA-2024-step07-no-pipelines-yet.png`)
   shows the Pipelines dashboard rendering the app's own **"No pipelines yet — Create your
   first pipeline…"** empty state, the "Card list view" toggle correctly selected, project
   selector `Private`. Not a gateway error page, not a broken toggle.
2. **Source proof that this is an empty list, not a failed fetch.**
   `src/components/CardList.jsx:40-42`:
   ```js
   const showEmptyOrError = !rest.isLoading && (isError || isEmptyList);
   const showCustomEmptyState = showEmptyOrError && customEmptyState && !isError;
   ```
   The custom `EmptyStatePage` ("No pipelines yet", `data-testid="empty-state-title"`) is
   reachable **only when `isError` is false**; a failed applications fetch renders
   `EmptyListBox` with `showErrorMessage` instead. The screenshot is the `!isError` branch
   ⇒ the fetch **succeeded and returned zero pipelines**.
3. **Run ordering makes the empty project inevitable.** In the same job, the sibling
   `TestPipelineDashboard::test_pipeline_created_via_api_visible_in_dashboard` **passed**
   at `1788944227833–1788944241071`; it uses the `pipeline_id` fixture, which creates one
   pipeline and **deletes it in teardown**. `test_view_toggle_table_and_card` started
   2.7 s later at `1788944243828` — on a project with zero pipelines.
4. **Independent corroboration in the same file, same job.**
   `TestSearchPipeline::test_search_placeholder_and_dashboard_grid_filters_and_clears`
   broke with `StopIteration` at its Step 2 ("verify full list loads including the 'YAML'
   pipeline **and a non-matching pipeline**") — a `next()` over an empty
   "other pipelines" list. Two independent tests, one root cause: the CI matrix project
   (`prompt_lib/573`, "Private") holds **no pipelines of its own**.
5. **Not the run-wide gateway-500 outage** (`.agents/testing.md`, sibling cards
   #2076–#2084). The `pipelines_2` job spread was **46 passed / 3 failed / 11 broken** —
   mixed, not an outage — and Steps 1–6 of this very test drove a healthy, rendering app.
6. **Green locally, red in CI.** Both this test and its sibling pass on
   `http://localhost:5173` (project 399, 14 pipelines): `2 passed in 16.04s`,
   `reruns.json == {}`. Per `adjust-automated-test` Step 1.3 that is class **D**, not drift.
7. **Promotion gap ruled out** — fresh `git fetch origin` in `../EliteaUI`, 2026-09-09:
   ```
   pipeline-table-view    main:YES  testids:YES
   pipeline-card-view     main:YES  testids:YES
   entity-card-name       main:YES  testids:YES
   empty-state-title      main:YES  testids:YES
   ```
   (This supersedes the original AFS's `pipeline-table-view` / `pipeline-card-view`
   `main: not yet` rows — they have since been promoted; `Pipelines.jsx:274` on
   `origin/main`.)

### The second, worse finding: Step 5 was VACUOUS on the CI run

`showEmptyOrError` short-circuits **both** `showTable` and `showCards` (`CardList.jsx:43-44`).
So on an empty list the dashboard renders the empty state in *table* view too — zero
`entity-card-name` nodes and **no table at all**. The merged Step 5 assertion
(`entity_card_name.count() == 0`) therefore passes without any table ever mounting.
It passed in 0.00 s on the CI run and proved nothing.

**Live-verified this session** (search-filtered to an empty list, no data mutated):

| State | URL | `entity-card-name` | `empty-state-title` | table headers |
|---|---|---|---|---|
| populated, default load | `/pipelines/all` | **14** | 0 | — |
| populated, table view | `?view=table` | **0** | **0** | "Name & Description / Authors / Created / Actions" ✓ |
| populated, card view | `?view=cards` | **14** | 0 | — |
| **empty list**, card view | `?view=cards` | **0** | **1 — "No pipelines yet"** | — |
| **empty list**, table view | `?view=table` | **0** | **1 — "No pipelines yet"** | **none — `hasColumnHeaders: false`** |

The last row is the false-pass path. `empty-state-title` is the observable that
distinguishes "a table rendered" from "nothing rendered", and it reads **0** on a
populated dashboard in every view — so an absence assertion on it is unambiguous.

### The repair (what the implementer must build)

The test must **establish** the precondition the case declares, and both layout
assertions must be made non-vacuous by it.

1. **Precondition** — request the existing `pipeline_id` (+ `pipeline_api`) fixtures so a
   fresh, uniquely-named pipeline exists for the whole test and is deleted in teardown.
   Same fixture the sibling `test_pipeline_created_via_api_visible_in_dashboard` already
   uses in this class, live-confirmed to land in the project the dashboard shows.
2. **Step 1 gains a precondition assertion** — after `navigate()`, the fixture pipeline's
   name is among `get_card_names(timeout=UI_ELEMENT_TIMEOUT)`. This waits out the loading
   state (during load *both* counts are 0 — see § Automation Hints), proves the
   precondition, and makes a future empty-project failure report itself at **Step 1** with
   the right subsystem named, instead of misattributing at Step 7.
3. **Step 5 strengthened** — add `empty_state_title.count() == 0` alongside the existing
   `?view=table` + `entity_card_name.count() == 0`. Closes the vacuity above.
4. **Step 7 strengthened** — assert the **fixture's own pipeline name** is in
   `get_card_names()`, not merely that the list is non-empty.
5. **One new page-object field** — `empty_state_title = LocatorDescriptor(testid="empty-state-title")`
   on `PipelinesListPage`. Testid already exists on `main` **and** `automation/testids` —
   **no `add-data-testid` work.**

### Rail check (`adjust-automated-test` § Step 3)

**Expected-result changes: NONE.** Nothing deleted, no comparison loosened, no count
lowered, no check made conditional. Every change is strictly additive or strictly
stronger (Step 7 moves from "any card" to "this specific known card"). Markers,
`allure.issue` decorators and `allure.step("Step N — …")` structure are preserved verbatim.

### TMS case text — no change needed

The case already states the precondition: *"The Pipelines dashboard contains at least one
pipeline."* It is the **automation** that assumed it instead of establishing it (the
original AFS explicitly waived it — *"already true on the shared dev project — 12 pipelines
visible… the extended test doesn't need to create one"* — an assumption true of project
399 and false of the CI matrix project 573). **No case-text clarification issue is
warranted, and no TMS PR is required** — `automation_test_id` is unchanged.

### Defects filed

**None.** The product behaves correctly in every observed state, including the empty one.
Zero console errors across the whole live walk.

---

## Extension target

**Covering spec**: `automation/tests/ui/pipelines_2/test_pipeline_management.py`,
class `TestPipelineDashboard`, method `test_view_toggle_table_and_card` — merged to
`origin/automation/base` (extension landed via PR #1343). Carries `allure.issue` links to
both `ELITEA-0855` (its original case) and `ELITEA-2024`.

**Behavioural overlap (what's already proven, live-reconfirmed 2026-09-09).**
- Navigate to the Pipelines dashboard.
- Both `table_view_button` and `card_view_button` (testids `pipeline-table-view` /
  `pipeline-card-view`) are visible, inside the `group "Small View Toggler"` — case Step 2.
- Default state: Card list view button `aria-pressed="true"`, Table view `"false"` — case Step 3.
- Click Table view → `is_table_view_active()` true, URL `?view=table` — case Step 4.
- Click Card list view → `is_card_view_active()` true, URL `?view=cards` — case Step 6.

**The gap that remains (why this is still `extend-existing`, now a repair).** The merged
test asserts the *toggle button's* state and the URL honestly, but its two layout-format
assertions (case Steps 5 & 7) are only meaningful when the dashboard actually holds a
pipeline — which the test never guarantees. See § Adjustment.

## Preconditions

- User is logged in (`auth_state` on localhost; Keycloak on deployed envs).
- **The Pipelines dashboard contains at least one pipeline — the test MUST establish this
  itself, via the `pipeline_id` fixture. It may NOT assume the ambient project holds one.**
  This is the repair. The CI matrix project (`prompt_lib/573`, "Private") holds zero
  pipelines of its own; the local dev project (399) holds 14. A test that reads "whatever
  cards happen to exist" is green on one and red on the other while the product is
  identical on both.

## Test Data

| Field | Value |
|-------|-------|
| Pipeline name | `pipeline_id` fixture's own name — `f"autotest_{request.node.name}"[:32]` ⇒ `autotest_test_view_toggle_table_` |
| Pipeline description | fixture default (`Auto-created for test …`) |

Read the name back from the API (`pipeline_api.get_pipeline(pipeline_id)["name"]`) rather
than re-deriving the truncation rule in the test — the sibling
`test_pipeline_created_via_api_visible_in_dashboard` already does exactly this.

## Test Steps

1. **[REPAIR — new precondition]** Create a pipeline via the `pipeline_id` fixture, read
   its name from the API, then navigate to the Pipelines dashboard.
   **Verify**: the created pipeline's name is among `get_card_names(timeout=10000)`.
   Live-confirmed: a populated dashboard renders one `entity-card-name` per pipeline
   (14 on project 399); the list takes ~4 s locally and ~10 s in CI to appear after
   navigate, and during that window **both** `entity-card-name` and `empty-state-title`
   read 0 — hence the waiting, positive assertion here rather than a bare count
   (case Step 1 + the case's declared precondition).
2. Verify both view-toggle buttons are visible, inside the `group "Small View Toggler"`
   (unchanged; `aria-label="Small View Toggler"` confirmed live again) (case Step 2).
3. Immediately after navigate, **before any toggle click**, verify the default view is
   Card list view: `is_card_view_active()` is `True`, `is_table_view_active()` is `False`.
   Live-confirmed: fresh load of `/pipelines/all` (no `view` query param at all) gives
   `pipeline-card-view` `aria-pressed="true"`, `pipeline-table-view` `"false"`
   (unchanged) (case Step 3).
4. Click "Table view" (`pipeline-table-view`). **Verify**: `is_table_view_active()` is
   `True` (unchanged) (case Step 4).
5. **[REPAIR — strengthened]** Verify the rendered layout actually changed to table format:
   - `"view=table" in page.url` — live-confirmed `http://localhost:5173/pipelines/all?view=table`.
   - `entity_card_name.count() == 0` — live-confirmed `14 → 0` on a populated dashboard.
   - **NEW**: `empty_state_title.count() == 0` — proves the zero-cards reading comes from a
     *table* being mounted, not from the empty state short-circuiting both branches.
     Live-confirmed: `0` on the populated dashboard in table view, `1` ("No pipelines yet")
     on an empty list in table view (case Step 5).
6. Click "Card list view" (`pipeline-card-view`). **Verify**: `is_card_view_active()` is
   `True` (unchanged) (case Step 6).
7. **[REPAIR — strengthened]** Verify the layout returned to the card grid:
   - `"view=cards" in page.url` — live-confirmed.
   - **NEW (replaces "any card")**: the fixture pipeline's name is in `get_card_names()`.
     Live-confirmed: card names return to the full set (14) after switching back
     (case Step 7).

## Expected Results

- Default view on a fresh dashboard load is Card list view — no click needed.
- Table view: `?view=table`, **zero** `entity-card-name` elements, **zero**
  `empty-state-title` elements, column headers "Name & Description / Authors / Created /
  Actions" rendered.
- Card list view: `?view=cards`, the known fixture pipeline rendered as a card.
- The test's own precondition (≥1 pipeline present) holds at Step 1 and is asserted there,
  so no later step can pass or fail for the wrong reason.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| The precondition pipeline is created through the **API** (`pipeline_id` fixture) rather than through the UI create form | **Transit only** | The case's own observables — the toggle's `aria-pressed` state, the `view` URL parameter, and which layout component the dashboard mounts — are all produced by the live application in response to real clicks. The API call only *populates the list* so the case's declared precondition ("contains at least one pipeline") holds; it never supplies a value the test asserts on. The case does not specify how the pipeline gets there. Precedent in the same class: `test_pipeline_created_via_api_visible_in_dashboard`. |

No fabricated responses, no injected state, no replaced clients. Nothing in this AFS
authorises `page.route`, `route.fulfill`, `page.evaluate` or `monkeypatch`.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: dashboard contains at least one pipeline | ≥1 pipeline present before the toggle is exercised | step 1 | **REPAIR** — `pipeline_id` fixture + fixture-name-in-`get_card_names()` assertion | **gap — was assumed, now established** |
| 1 Navigate to Pipelines dashboard | Dashboard loads with pipelines visible | step 1 | existing `list_page.navigate()` + the new precondition assertion | asserted |
| 2 Locate "Small View Toggler" group with both buttons | Both view toggle buttons are visible | step 2 | existing visibility assertions | asserted (unchanged) |
| 3 Verify default view is Card list view | Card list view button shown as active/pressed | step 3 | `is_card_view_active()` / `not is_table_view_active()` pre-click | asserted (unchanged) |
| 4 Click "Table view" button | Table view is activated | step 4 | `switch_to_table_view()` + `is_table_view_active()` | asserted (unchanged) |
| 5 Verify layout changes to table format | Pipelines displayed in table/row format | step 5 | `?view=table` + `entity_card_name.count()==0` + **NEW** `empty_state_title.count()==0` | **repaired — was vacuous on an empty project** |
| 6 Click "Card list view" button | Card list view is activated | step 6 | `switch_to_card_view()` + `is_card_view_active()` | asserted (unchanged) |
| 7 Verify layout returns to card grid format | Pipelines displayed as cards in a grid | step 7 | `?view=cards` + **NEW** fixture pipeline name in `get_card_names()` | **repaired — was "any card", now a known card** |

**Axis 2 — Analyst additions**

- URL query-param (`?view=table` / `?view=cards`) assertion alongside the DOM check —
  *retained from the original AFS: a stable, testid-free signal
  (`SearchParams.View`/`ViewOptions`, `useIsTableView.js`) proving which branch of
  `CardList.jsx`'s `shouldRenderTable` ternary is mounted.*
- `empty-state-title` absence in table view — *added by this repair: it is the ONLY
  observable that separates "table mounted" from "empty state short-circuited both
  branches" (`CardList.jsx:40-44`). Without it the Step-5 assertion is satisfiable by a
  dashboard that rendered nothing at all — which is exactly what happened in CI run
  34331579791.*
- Console errors: 0 across the entire live walk (default load, both toggles, the
  empty-list probe) — nothing to report.

## Cleanup

The `pipeline_id` fixture deletes the pipeline it created in teardown (even on failure).
No other data is created or modified — the toggling and counting remain read-only.

## Concrete Handles (discovered during exploration)

Locator policy is **testid-only** (`.agents/role-overrides.md` / `.agents/testing.md`
§ Locator policy). **PROVENANCE verified 2026-09-09 with a fresh `cd ../EliteaUI &&
git fetch origin` immediately before the grep** (command + output in § Adjustment, point 7).

| Element | Testid | LocatorDescriptor / access path | PROVENANCE |
|---|---|---|---|
| Table view toggle button | `pipeline-table-view` | `PipelinesListPage.table_view_button` (existing field; its `fallback=` param is pre-existing tech debt — leave it, never copy it into new code) | **on-main ✓** (`src/pages/Pipelines/Pipelines.jsx:274`, `tableViewTestId="pipeline-table-view"`) — promoted since the original AFS, which recorded "not yet" |
| Card view toggle button | `pipeline-card-view` | `PipelinesListPage.card_view_button` (existing field, same fallback caveat) | **on-main ✓** (`Pipelines.jsx:275`) — promoted since the original AFS |
| Table/Card active state | (n/a — `aria-pressed` read off the two buttons above) | `is_table_view_active()` / `is_card_view_active()` (existing methods) | n/a — attribute read, not a locator |
| Pipeline card name (Card view only) | `entity-card-name` | `PipelinesListPage.entity_card_name` (existing field) / `get_card_names()` helper | **on-main ✓** |
| Empty-state title ("No pipelines yet") | `empty-state-title` | **NEW class field** — `empty_state_title = LocatorDescriptor(testid="empty-state-title", description="Generic EmptyStatePage title — absent whenever the list has content")` on `PipelinesListPage` | **on-main ✓** (`src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx:49`) — **no `add-data-testid` work needed** |
| Pipeline table row name cell | none for pipelines — `DataTableNameCell.jsx:71` emits a testid only for `mcp` / `credential` card types, `undefined` otherwise | not used by this AFS | **needs-adding — but explicitly OUT OF SCOPE.** A positive row-level assertion is not required: `empty_state_title.count()==0` + `entity_card_name.count()==0` already discriminate the three possible branches (`table` / `cards` / `empty`). Adding a feature-scoped testid to the shared `[fsd]/widgets/data-table` component is a `.agents/testing.md` § Locator policy shared-component question that must not be settled inside a repair card — raise it as a `question` card if a future pipelines-table case needs row-level assertions. |

**Note on `empty-state-title` being a generic shared testid.** It is rendered by the
shared `EmptyStatePage` entity, so it could in principle appear on another surface of the
same page. Live-verified this session: on a populated Pipelines dashboard the page-wide
count is **0** in card view and **0** in table view (the right-hand panel's "No folders
created yet" / "No tags to display." are plain `Typography`, not `EmptyStatePage`). A
page-level absence assertion is therefore unambiguous here.

## Network Behavior

No new network traffic — view toggling is a pure client-side `useSearchParams` + React
re-render swap (`CardList.jsx`'s `shouldRenderTable` ternary between `DataTable` and
`DataCards`). Re-confirmed live 2026-09-09. The `pipeline_id` fixture's create/delete are
ordinary REST calls made outside the browser.

## Known Defects Found During Exploration

None. Both view-toggle branches and the empty-list state behave exactly as designed.
Zero console errors throughout.

## Blocked Steps

None.

## Automation Hints

- Framework: Playwright + pytest. **Update the existing method in place** — no new test
  file, no new test class (`adjust-automated-test` § Never).
- Add `pipeline_id` and `pipeline_api` to the signature, mirroring the sibling
  `test_pipeline_created_via_api_visible_in_dashboard` in the same class.
- **Ordering matters at Step 1.** During the dashboard's loading window *both*
  `entity-card-name` and `empty-state-title` read 0, so a bare count assertion would pass
  vacuously there too. Lead with the **waiting, positive** assertion
  (`get_card_names(timeout=UI_ELEMENT_TIMEOUT)` — 10 s, not the helper's 5 s default,
  which is what expired in CI) and let it absorb the load.
- Suggested shape (the implementer owns the final code):
  ```python
  def test_view_toggle_table_and_card(self, page, pipeline_id, pipeline_api):
      with allure.step("Step 1 — Navigate to pipelines dashboard with a known pipeline present"):
          pipeline_name = pipeline_api.get_pipeline(pipeline_id).get("name", "")
          list_page = PipelinesListPage(page)
          list_page.navigate()
          assert pipeline_name in list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT), (
              f"Precondition: pipeline {pipeline_name!r} should be on the dashboard "
              "before the view toggle is exercised"
          )
      ...
      with allure.step("Step 5 — Verify layout actually changed to table format"):
          assert "view=table" in page.url, f"Expected ?view=table in URL, got {page.url!r}"
          assert list_page.empty_state_title.count() == 0, (
              "Dashboard must not be showing the empty state — a zero card count would "
              "then prove nothing about the table layout"
          )
          assert list_page.entity_card_name.count() == 0, (
              "No card elements (entity-card-name) should render while in table view"
          )
      ...
      with allure.step("Step 7 — Verify layout returned to card grid format"):
          assert "view=cards" in page.url, f"Expected ?view=cards in URL, got {page.url!r}"
          assert pipeline_name in list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT), (
              f"Pipeline {pipeline_name!r} should render as a card again after "
              "switching back to card view"
          )
  ```
- `empty_state_title` must be a **class-level** `LocatorDescriptor` field on
  `PipelinesListPage` — `.count()` on it is a plain Playwright locator method, not a new
  raw handle.
- Add one docstring line naming the transit substitution (§ Fidelity Declaration) — the
  next reader reads the test, not this AFS.
- **Gate on the environment the repair is for.** The bug only manifests on a project with
  no pipelines of its own, which localhost (project 399, 14 pipelines) is not. A local
  3×-green proves the repair did not break the happy path; it does **not** prove the
  precondition fix works. The lead should decide whether to gate the merge candidate
  against `https://dev.elitea.ai` (`APP_PREFIX=/app`) as well — noting `.env.test` beats
  shell env, so the env file itself must be swapped and restored
  (`.agents/testing.md` § Merge gate).
