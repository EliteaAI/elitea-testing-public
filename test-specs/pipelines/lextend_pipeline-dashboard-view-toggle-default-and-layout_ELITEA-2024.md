# Test Case: Pipeline Dashboard — View Toggle (Card vs Table) — default state + actual layout-format gap

## Metadata
- **TMS ID**: ELITEA-2024
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend, project `Private`/`project_user_659` id 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `pipelines-remaining-w2`
- **Status**: extend-existing

## Extension target

**Covering spec**: `automation/tests/ui/pipelines/test_pipeline_management.py`,
class `TestPipelineDashboard`, method `test_view_toggle_table_and_card`
(lines 87–107), merged to `origin/automation/base` (originating commit
`9327052c`, "Initial commit — public release"; file's latest touch is
`97fac3fc`, ELITEA-2022, unrelated to this method). Linked to a different TMS
case (`ELITEA-0855` per its `allure.issue` decorator) but exercises the exact
same dashboard control ELITEA-2024 targets.

**Behavioural overlap (what's already proven).** `test_view_toggle_table_and_card`
already covers, live-reconfirmed this session:
- Navigate to the Pipelines dashboard.
- Both `table_view_button` and `card_view_button` (testids `pipeline-table-view`
  / `pipeline-card-view`) are visible — case Step 2.
- Click Table view → `is_table_view_active()` (button's own `aria-pressed`)
  returns `true` — case Step 4.
- Click Card view → `is_card_view_active()` returns `true` — case Step 6.

**The gap (why this isn't `already-covered`).** Two things the case explicitly
asks for are NOT asserted by the existing test:

1. **Default-state verification (case Step 3).** The existing test never checks
   the toggle's state immediately after `navigate()`, before any click. It goes
   straight from "buttons visible" (Step 2) to "click Table view" (Step 3 in
   the test == case Step 4) — the case's own Step 3 ("verify default view is
   Card list view") has no corresponding assertion at all.
2. **Actual layout-format verification (case Steps 5 & 7).** The existing
   test's `is_table_view_active()` / `is_card_view_active()` only read the
   clicked **button's own** `aria-pressed` attribute — they prove the toggle
   registered the click, not that the dashboard's **rendered content**
   actually switched from a card grid to a row/column table (or back). A
   product regression that left the toggle visually "pressed" while the
   underlying `DataTable`/`DataCards` swap silently broke would go undetected
   by the current assertions. Case Steps 5 and 7 explicitly ask for the
   layout-format check, not just the button state.

Both gaps are closable with **existing testid-only handles already declared
in `PipelinesListPage`** — no new testid work needed (see § Concrete Handles).

## Preconditions
- User is logged in (`auth_state` on localhost).
- The Pipelines dashboard contains at least one pipeline (already true on the
  shared dev project — 12 pipelines visible during this session's live run;
  the extended test doesn't need to create one, it only reads the existing
  grid/table rendering).

## Test Data
| Field | Value |
|-------|-------|
| (none required) | — reuses whatever pipelines already exist in the project |

## Test Steps

(Steps below map onto the *existing* test's flow — the implementer inserts the
two new assertion blocks at the marked points; the existing Steps 2–4 [test's
own numbering] pass unmodified.)

1. Navigate to the Pipelines dashboard (existing covering-spec behavior).
   **Verify**: dashboard loads with pipelines visible (case Step 1, already
   satisfied by the existing `list_page.navigate()` + the grid rendering).
2. Verify both view-toggle buttons are visible, inside the "Small View
   Toggler" `group` (existing covering-spec behavior — confirmed live:
   `aria-label="Small View Toggler"` on the containing `TabGroupButton`,
   matches the case's own step-2 wording exactly) (case Step 2).
3. **[GAP — new assertion]** Immediately after navigate, **before any click**,
   verify the default view is Card list view:
   `list_page.is_card_view_active()` is `True` and
   `list_page.is_table_view_active()` is `False`. Confirmed live this session:
   fresh navigate to `/pipelines/all` renders the Card list view button with
   `[pressed]` (`aria-pressed="true"`) and the Table view button with no
   `pressed` state (case Step 3).
4. Click "Table view" button (existing covering-spec behavior, testid
   `pipeline-table-view`). **Verify**: `is_table_view_active()` is `True`
   (existing assertion, case Step 4).
5. **[GAP — new assertion]** Verify the rendered layout actually changed to
   table/row format, not just the button's own pressed state: the URL's
   `view` query param becomes `table` (confirmed live:
   `http://localhost:5173/pipelines/all?view=table`) **and** the
   `entity-card-name` testid (only rendered by the Card-view `Card.jsx`
   component, never by the Table view's `DataTable`) has a count of `0`.
   Confirmed live this session:
   `document.querySelectorAll('[data-testid="entity-card-name"]').length`
   dropped from `12` (card view, 12 pipelines) to `0` immediately after
   switching to Table view. Table view instead renders column headers "Name &
   Description" / "Authors" / "Created" / "Actions" (no stable testid on
   these header cells currently — see § Concrete Handles note; not needed for
   this assertion since the `entity-card-name` absence + URL param already
   prove the layout swapped, without requiring a new testid) (case Step 5).
6. Click "Card list view" button (existing covering-spec behavior, testid
   `pipeline-card-view`). **Verify**: `is_card_view_active()` is `True`
   (existing assertion, case Step 6).
7. **[GAP — new assertion]** Verify the layout returned to the card grid: URL
   `view` param becomes `cards`
   (`http://localhost:5173/pipelines/all?view=cards`) **and**
   `entity-card-name` count is `> 0` again (confirmed live: back to `12`,
   matching the same 12 pipelines) — equivalently, reuse the existing
   `list_page.get_card_names()` helper and assert it returns a non-empty list
   (case Step 7).

## Expected Results
- Existing test's own assertions (buttons visible, `is_table_view_active()` /
  `is_card_view_active()` after each click) — unchanged, still pass.
- New Step 3: default view is Card list view on a fresh dashboard load — no
  click needed to reach that state.
- New Steps 5 & 7 (the gaps): the dashboard's actual rendered content — not
  just the toggle button — switches between a table/row layout (zero
  `entity-card-name` elements, `?view=table`) and a card grid (twelve
  `entity-card-name` elements matching the visible pipeline count,
  `?view=cards`).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Pipelines dashboard | Dashboard loads with pipelines visible | step 1 | covering spec's existing `list_page.navigate()` | asserted (existing) |
| 2 Locate "Small View Toggler" group with Table view / Card list view buttons | Both buttons visible | step 2 | covering spec's existing visibility assertions | asserted (existing) |
| 3 Verify default view is Card list view (button pressed/active) | Card list view button shown as active by default | step 3 | **NEW** — `is_card_view_active()`/`is_table_view_active()` checked immediately post-navigate, before any click | **gap — needs new assertion** |
| 4 Click "Table view" button | Table view is activated | step 4 | covering spec's existing `switch_to_table_view()` + `is_table_view_active()` | asserted (existing) |
| 5 Verify layout changes to table format (rows/columns instead of cards) | Pipelines displayed in table/row format | step 5 | **NEW** — `entity-card-name` count == 0 + `?view=table` URL param, post table-view click | **gap — needs new assertion** |
| 6 Click "Card list view" button | Card list view is activated | step 6 | covering spec's existing `switch_to_card_view()` + `is_card_view_active()` | asserted (existing) |
| 7 Verify layout returns to card grid format | Pipelines displayed as cards in a grid | step 7 | **NEW** — `entity-card-name` count > 0 (or `get_card_names()` non-empty) + `?view=cards` URL param | **gap — needs new assertion** |

**Axis 2 — Analyst additions**

- URL query-param (`?view=table`/`?view=cards`) assertion alongside the
  DOM-content check — *added: zero-cost, stable, testid-free signal
  (`SearchParams.View`/`ViewOptions`, confirmed via source read of
  `ViewToggle.jsx`/`useIsTableView.js`) that directly proves which branch of
  `CardList.jsx`'s `shouldRenderTable` ternary is mounted; strengthens the
  layout-format gap assertion beyond a single testid count.*
- (nothing else added beyond the case; the console-error check the
  team's live-session discipline calls for showed 0 errors throughout,
  not called out separately since nothing was observed.)

## Cleanup
None needed — this extension is read-only (view toggling + count assertions
on the dashboard's existing pipeline grid); no data created or modified.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** — see
`.agents/role-overrides.md` / `.agents/testing.md` § Locator policy. All
handles below already exist as `LocatorDescriptor` class fields in
`PipelinesListPage` (`automation/pages/pipelines_list_page.py`) — **no new
testid work needed** for this extension.

| Element | Testid | LocatorDescriptor / access path | Provenance |
|---|---|---|---|
| Table view toggle button | `pipeline-table-view` | `PipelinesListPage.table_view_button` (existing field; note the field's `fallback=` param is pre-existing tech debt — unchanged by this extension, not to be copied into new code) | on-`automation/testids` ✓ / on-`main` — **not yet** (awaiting human promotion; confirmed via fresh `git fetch origin` this session: `git grep pipeline-table-view origin/main -- src/` → no hit, `origin/automation/testids` → hit at `src/pages/Pipelines/Pipelines.jsx:274`) |
| Card view toggle button | `pipeline-card-view` | `PipelinesListPage.card_view_button` (existing field, same fallback caveat) | on-`automation/testids` ✓ / on-`main` — **not yet** (same fetch, hit at `src/pages/Pipelines/Pipelines.jsx:275`) |
| Table/Card active state | (n/a — `aria-pressed` attribute read off the two buttons above) | `PipelinesListPage.is_table_view_active()` / `is_card_view_active()` (existing methods) | n/a (attribute read, not a new locator) |
| Pipeline card name (Card view only; absent in Table view) | `entity-card-name` | `PipelinesListPage.entity_card_name` (existing field) — reuse directly, or via existing `get_card_names()` helper for the Step 7 non-empty check | on-`main` ✓ (pre-existing, confirmed via fresh fetch) |
| "Small View Toggler" group (case-text anchor only, not a click target) | none — `aria-label="Small View Toggler"` on the `TabGroupButton` wrapper | Not a `LocatorDescriptor` field; no assertion in this AFS targets it directly (the two buttons inside it are the actual handles) — informational only, matches the case's own wording | n/a |
| Table view column headers ("Name & Description" etc.) | none — `GridTableHeader` only emits `data-testid` when the caller passes `columnTestIdPrefix`; `DataTable.jsx` passes this only for MCPs (`isMCPs ? 'mcp-table' : undefined`), `undefined` for Pipelines | Not used by this AFS's assertions — the `entity-card-name` absence + `?view=table` URL param already prove the layout swapped without needing this testid | **testid gap, NOT required for this AFS** — flagging only in case a future pipelines-table case wants a header-cell-level assertion; adding `columnTestIdPrefix="pipeline-table"` at the `DataTable.jsx` call site (`isPipelines ? 'pipeline-table' : ...`) would close it then, out of scope here per the "touches" scoping rule (this test never needs it) |

## Network Behavior
No new network traffic — view toggling is a pure client-side URL
(`useSearchParams`) + React re-render swap (`CardList.jsx`'s
`shouldRenderTable` ternary between `DataTable` and `DataCards`), confirmed
via source read of `useIsTableView.js`/`ViewToggle.jsx`. No XHR observed
firing on toggle click during this session's live run.

## Known Defects Found During Exploration
None found. Both view-toggle branches (default Card view, Table view
switch, Card view switch-back) work correctly and match the case's expected
results.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, matches covering spec).
- Extend `test_view_toggle_table_and_card` in-place with two new assertion
  blocks — one right after `list_page.navigate()` (Step 3 gap), one right
  after each `switch_to_*_view()` call (Steps 5 & 7 gaps):
  ```python
  with allure.step("Step 3 — Verify default view is Card list view"):
      assert list_page.is_card_view_active(), (
          "Card list view should be the active/default view on fresh load"
      )
      assert not list_page.is_table_view_active(), (
          "Table view should NOT be active on fresh load"
      )

  with allure.step("Step 4 — Switch to table view"):
      list_page.switch_to_table_view()
      assert list_page.is_table_view_active(), (
          "Table view toggle should be active after switching to table view"
      )

  with allure.step("Step 5 — Verify layout actually changed to table format"):
      assert "view=table" in page.url, f"Expected ?view=table in URL, got {page.url!r}"
      assert list_page.entity_card_name.count() == 0, (
          "No card elements (entity-card-name) should render while in table view"
      )

  with allure.step("Step 6 — Switch back to card view"):
      list_page.switch_to_card_view()
      assert list_page.is_card_view_active(), (
          "Card view toggle should be active after switching to card view"
      )

  with allure.step("Step 7 — Verify layout returned to card grid format"):
      assert "view=cards" in page.url, f"Expected ?view=cards in URL, got {page.url!r}"
      assert list_page.get_card_names(), (
          "Card elements (entity-card-name) should render again after switching to card view"
      )
  ```
- `entity_card_name` is already a page-level `LocatorDescriptor` field — the
  `.count()` call above is a plain Playwright locator method, not a new raw
  handle (no new selector construction).
- No fixture/data setup needed beyond what the covering spec already has —
  this is purely additional assertions on the same navigate-and-click flow.
