# Test Case: Credential Dashboard — View Toggle (Table/Card)

## Metadata
- **TMS ID**: ELITEA-1973
- **Linked Story**: none
- **Priority**: l1 — **⚠ contradictory case metadata**: frontmatter says
  `priority: high`, the body header says `Priority: medium`. Per
  `.agents/test-automation.yaml` § `intake.contradictory_metadata` this is
  *reported, never silently guessed*: it is raised as a `clarification` finding
  in this unit's Run Report. Resolved here in favour of the **frontmatter**
  (the structured field the TMS indexes and the intake selector reads) →
  `high`→l1, marker `p1`. Flip both the AFS name and the marker if the TMS is
  corrected the other way.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend `https://dev.elitea.ai/api/v2`), project
  `Private` / `${ELITEA_PROJECT_ID}`=399, identity "Test Bot"
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation
- **Case-gate note**: `status: draft`, `execution_type: manual` — intake-eligible
  per `.agents/test-automation.yaml`. Fully executed live 2026-08-22.

## Preconditions
- User is logged in (localhost `auth_state`).
- Project `Private` (399) selected.
- **More than 20 credentials must exist** — the case says so explicitly, and it
  is load-bearing: `GridTablePagination` renders `1 - N of TOTAL` and BOTH
  arrows are `disabled` when `total <= pageSize`, so steps 6–8 (a full first
  page + a working Next/Prev) are unobservable below 21. Live-verified: with
  22 credentials the footer read `1 - 20 of 22`, Next → `21 - 22 of 22`,
  Prev → `1 - 20 of 22`. The project carries ONE credential today, so the test
  MUST top the project up to ≥21 itself.
- The Credentials section is reachable at `/credentials/all`.

## Test Data

### generate-per-test (created in setup, deleted in teardown)
- **Top-up seeding**: read the current total via
  `credential_api.list_credentials(params={"section": ["credentials","storage"], "limit": 1})["total"]`,
  then create `max(0, 21 - total)` credentials of type `github`
  (`data={"base_url": "https://api.github.com"}`, labels
  `autotest_cred_view_<NN>_<ts>`) via `credential_api.create_credential`.
  This is **read-only-by-default applied as far as it goes** (Hard Rule 10):
  existing credentials are reused as page-1 content and never touched; only the
  shortfall to the case's own >20 precondition is seeded.
- **API seeding is transit, not terminal substitution** (`.agents/testing.md`
  § Fidelity policy): every observable this case asserts — the pressed view
  button, the rendered layout, the column headers, the page-info string, the
  rows on each page — is computed and rendered by the product from its own
  server response. Nothing is fabricated, injected or intercepted. The case has
  no "create a credential" step; existence of >20 credentials is a stated
  precondition, so the cheapest honest route to that state is the API.
- Cleanup: delete every seeded id in a `finally` block.

### reuse-existing
- `${TEST_USER}` — `.agents/profile.md` § Roles & sample users.
- Whatever credentials the project already holds.

## Test Steps

1. **Navigate to `/credentials/all`** (case step 1).
   - **Verify**: page loads, URL carries **no** `?view=` param on a fresh
     navigation, at least one `entity-card` is rendered.
2. **Verify the default view is Card** (case step 2).
   - **Verify**: `agent-card-view-button` has `aria-pressed="true"` and
     `agent-table-view-button` has `aria-pressed="false"`; cards are rendered
     (`entity-card` count > 0) and there is no table pagination footer.
   - Capture the card names as the baseline for step 10.
3. **Click the Table view button** (case step 3).
   - **Verify**: URL becomes `/credentials/all?view=table`;
     `agent-table-view-button` `aria-pressed="true"` and
     `agent-card-view-button` `aria-pressed="false"`.
4. **Verify credentials display in table format** (case step 4).
   - **Verify**: `entity-card` count is 0 (cards gone) and at least one
     `credentials-table-row-name` row is rendered.
5. **Verify the table columns** (case step 5).
   - **Verify**: exactly the five headers, in DOM order, with these testids and
     texts:
     | testid | text |
     |---|---|
     | `credentials-table-column-header-name` | `Name & Description` |
     | `credentials-table-column-header-type` | `Type` |
     | `credentials-table-column-header-author` | `Authors` |
     | `credentials-table-column-header-created_at` | `Created` |
     | `credentials-table-column-header-actions` | `Actions` |
6. **Verify pagination controls, defaulting to 20 per page** (case step 6).
   - **Verify**: `credentials-pagination-page-info` reads `1 - 20 of {total}`
     with `total > 20`; exactly 20 `credentials-table-row-name` rows are
     rendered; `credentials-pagination-prev-button` is **disabled** (first page)
     and `credentials-pagination-next-button` is **enabled**.
   - Capture page-1 row names.
7. **Click Next** (case step 7).
   - **Verify**: page-info reads `21 - {min(40,total)} of {total}`; the rendered
     row names are **disjoint** from page 1's; row count == `total - 20`
     (capped at 20); `credentials-pagination-prev-button` is now enabled.
8. **Click Previous** (case step 8).
   - **Verify**: page-info is back to `1 - 20 of {total}`; the rendered row
     names equal page 1's captured set; prev is disabled again.
9. **Click the Card view button** (case step 9).
   - **Verify**: URL becomes `/credentials/all?view=cards`;
     `agent-card-view-button` `aria-pressed="true"`,
     `agent-table-view-button` `aria-pressed="false"`.
10. **Verify card format is restored** (case step 10).
    - **Verify**: `entity-card` count > 0; no `credentials-table-row-name` rows
      remain; the step-2 baseline card names are all still present.

## Expected Results
- Card view is the default; the toggle is URL-driven (`?view=table` /
  `?view=cards`, read by `useIsTableView`) and reflected on the buttons'
  `aria-pressed`.
- Table view renders exactly five columns for credentials:
  Name & Description, Type, Authors, Created, Actions.
- Pagination defaults to 20 rows/page, shows `start - end of total`, disables
  Prev on the first page and Next on the last.
- Next/Prev move between disjoint row sets and return to the original set.
- Switching back to Card view restores the card layout and the same credentials.
- No console errors. Only the #554 prompt_lib-404 filter is applied (closed
  2026-08-11 as a local-UI/test-client artifact, pinned to that exact URL
  shape). The suite's `#518` `<CredentialsList>`-crash filter is deliberately
  NOT reused: #518 is CLOSED as NOT REPRODUCIBLE, so that signature is now a
  regression of the component under test and must fail the test.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: >20 credentials exist | — | AFS § Test Data top-up | setup asserts `total >= 21` after seeding | asserted |
| 1 Navigate to Credentials list | page loads | AFS step 1 | step 1: URL `/credentials/all`, no `?view=`, `entity-card` visible | asserted |
| 2 Default view is Card (button pressed) | Card default + active | AFS step 2 | step 2: `aria-pressed` true/false pair, cards rendered | asserted |
| 3 Click Table view button | switches to table | AFS step 3 | step 3: URL `?view=table`, `aria-pressed` flipped | asserted |
| 4 Credentials display in table format | table layout shown | AFS step 4 | step 4: `entity-card` count 0, table rows > 0 | asserted |
| 5 Columns: Name & Description, Type, Authors, Created, Actions | all five present | AFS step 5 | step 5: five header testids + exact texts, in order | asserted |
| 6 Pagination present, 20/page default | controls visible; 20 shown | AFS step 6 | step 6: page-info `1 - 20 of N`, 20 rows, prev disabled / next enabled | asserted |
| 7 Click next page | next set displayed | AFS step 7 | step 7: page-info `21 - …`, row names disjoint from page 1 | asserted |
| 8 Click previous page | previous set displayed | AFS step 8 | step 8: page-info back to `1 - 20 of N`, row names == page-1 set | asserted |
| 9 Click Card view button | switches back to cards | AFS step 9 | step 9: URL `?view=cards`, `aria-pressed` flipped back | asserted |
| 10 Credentials display in card format | card layout restored | AFS step 10 | step 10: cards > 0, table rows 0, baseline names present | asserted |
| Expected Final State / Pass criteria | — | steps 3–10 | as above + console side-channel | asserted |

### Axis 2 — Analyst additions
- **Disjointness** of page-2 row names vs page 1 (step 7) — *added: "next set is
  displayed" is only proven by showing the set actually changed; a broken pager
  that re-rendered page 1 would satisfy a naive "rows are visible" check.*
- **Prev/Next disabled state** at the boundaries (steps 6, 8) — *added: the
  product expresses "you are on the first page" only through the disabled
  arrow; asserting it makes the boundary behaviour a tested invariant rather
  than an assumption.*
- **Round-trip identity** of page-1 rows after Prev (step 8) — *added: "previous
  set is displayed" made concrete against the captured page-1 set.*
- **Absence assertions** — `entity-card` count 0 in table view (step 4),
  `credentials-table-row-name` count 0 back in card view (step 10) — *added:
  a toggle that renders BOTH layouts is a real regression shape and is invisible
  to presence-only checks. Also satisfies the testid-reference rule for the
  card/table handles on the non-active branch.*
- **No `?view=` on fresh navigation** (step 1) — *added: pins "Card is the
  DEFAULT" as an absence-of-state fact, not merely "cards happen to be shown".*
- No console errors — *added, standard side-channel check.*

## Cleanup
1. Delete every top-up-seeded credential id via
   `credential_api.delete_credential(id)` in a `finally`.
2. The `?view=` param is URL-local; nothing persists server-side. (Note:
   `DataTable` mirrors page size into a redux `settings.pageSize`, but this test
   never changes page size, so there is nothing to restore.)

## Concrete Handles (discovered during exploration)

Locator policy: **testid-only** (`.agents/testing.md` § Locator policy).

| Element | Testid | Provenance | Fallback |
|---|---|---|---|
| Table view button | `agent-table-view-button` (shared, cross-page generic despite the `agent-` prefix — see elitea-testing-public#521) | **on-main ✓** | none |
| Card view button | `agent-card-view-button` (same) | **on-main ✓** | none |
| Credential card container | `entity-card` | on-`automation/testids` only | none |
| Credential card name | `entity-card-name` | **on-main ✓** | none |
| Table column headers | `credentials-table-column-header-{name,type,author,created_at,actions}` | **needs-adding → ADDED** this unit: EliteaAI/EliteaUI@84446b15 on `automation/testids` (awaiting human cherry-pick to `main`) | none |
| Table row name cell | `credentials-table-row-name` | **needs-adding → ADDED** same commit | none |
| Pagination page-info (`start - end of total`) | `credentials-pagination-page-info` | **needs-adding → ADDED** same commit | none |
| Pagination Previous button | `credentials-pagination-prev-button` | **needs-adding → ADDED** same commit | none |
| Pagination Next button | `credentials-pagination-next-button` | **needs-adding → ADDED** same commit | none |

### Testid work performed (`add-data-testid` discipline)
Three attribute-only edits, no DOM nodes / hooks / render-prop changes:
1. `src/[fsd]/widgets/data-table/ui/DataTable.jsx` — extended the **existing**
   `columnTestIdPrefix={isMCPs ? 'mcp-table' : undefined}` branch with
   `: isCredentials ? 'credentials-table'`. The prefix is the shared
   `GridTableHeader` prop already used by MCPs, Users, Personal Tokens and the
   Artifacts file table.
2. Same file — passed the **already-supported** `prevButtonTestId` /
   `nextButtonTestId` / `pageInfoTestId` props of `GridTablePagination`
   (previously `undefined` for every `DataTable` caller), gated on
   `isCredentials` so no other list page gains an unreferenced testid
   (canon #511 scope rule). Naming follows the existing
   `artifacts-pagination-*` / `notifications-pagination-*` precedent.
   `pageSizeSelectTestId` was deliberately **left unwired** — this case never
   changes the page size, so wiring it would be an unreferenced testid.
3. `src/[fsd]/widgets/data-table/ui/DataTableNameCell.jsx` — mirrored the
   existing `mcp-table-row-name` conditional with `credentials-table-row-name`.

**Declared consequence (canon-gap declaration, `.agents/role-overrides.md`
§ Declared-improvisation protocol):** `columnTestIdPrefix` is a *single* prop
that the shared `GridTableHeader` uses for BOTH the header cell
(`{prefix}-column-header-{field}`) and its sort icon
(`{prefix}-sort-icon-{field}`). Reusing it therefore also emits three
`credentials-table-sort-icon-*` testids that this test does not reference.
This is not a new pattern — it is the shared component's designed API and the
exact same consequence the merged `mcp-table` branch already carries
(`mcp-table-sort-icon-*` is likewise unreferenced). The alternative — a new,
header-only prop on a shared entity component — would be a functional change to
a widget used by six callers to avoid two side-effect attributes, which the
zero-functional-impact rule weighs against. Declared here and in the Run Report
so the reviewer can weigh it rather than discover it.

### Page object impact
`automation/pages/credentials_list_page.py` gains class-level fields
(`table_view_button`, `card_view_button`, `table_row_name`, the five
`credentials-table-column-header-*` fields, `pagination_page_info`,
`pagination_prev_button`, `pagination_next_button`) and methods
`switch_to_table_view()`, `switch_to_card_view()`, `is_card_view_active()`,
`is_table_view_active()`, `get_table_row_names()`, `get_page_info()`,
`click_next_page()`, `click_prev_page()`.

## Network Behavior
- `GET /api/v2/configurations/configurations/{project}?...&limit=20&offset=…&section=credentials&section=storage`
  on each page change; the table's visible rows come straight from the response
  (credentials are NOT client-side sliced — `DataTable`'s `visibleRows` skips
  the slice for `isCredentials`).
- Switching views re-issues the list GET (card view loads with an
  infinite-scroll shape, table view with `limit=pageSize`).
- Wait on the response, then `wait_for_network()` before reading DOM state.

## Known Defects Found During Exploration
1. **None.** All ten case steps behaved exactly as specified, 1/1, on the live
   product.
2. **Case-metadata contradiction** (not a product defect): `priority: high`
   (frontmatter) vs `Priority: medium` (body header). Reported as a
   `clarification` finding; resolved in favour of the frontmatter — see
   § Metadata.

## Blocked Steps
None — all 10 case steps executed and observed live on 2026-08-22.

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Markers: `ui`, `credentials`, `p1`, `regression`.
- Precedent to mirror: `tests/ui/toolkits/test_mcp_view_toggle.py`
  (ELITEA-1944) — same toggle, same shared buttons, same `aria-pressed`
  reading. Differences: credentials additionally exercise pagination, and the
  MCP test's `has_any_mcp()` seed-if-empty shape becomes a *top-up to 21* here.
- The two view buttons are inside a MUI toggle group that can be overlaid
  during a re-render — the MCP page object clicks them with `force=True`;
  do the same and then wait on the list GET rather than on a fixed delay.
