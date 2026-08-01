# Test Case: MCP Dashboard — View Toggle (Card/Table)

## Metadata
- **TMS ID**: ELITEA-1944
- **Linked Story**: none
- **Priority**: l1
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-07-15
- **Status**: ready-for-automation

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`; on
  deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: Private`; project id read from
  `${ELITEA_PROJECT_ID}`).
- At least one MCP exists in the project. Confirmed live: 6 pre-existing MCPs
  already present in the `Private` test project (`autotest_deepwiki_mcp_1954`,
  `verify_ttl_1784105621`, `verify_secret_1784105552`, `autotest_remote_mcp_full`,
  `f`, `Remote Github`) — **reuse-existing**, no new MCP needed to be created for
  this case. If the implementer's test environment starts from a clean project
  with zero MCPs, seed at least one via the existing `McpFormPage` create flow
  (see `test-specs/mcp/l1_create-remote-mcp-all-fields-populated_ELITEA-1922.md`)
  or the `ToolkitAPI` client before asserting the toggle — the toggle group
  itself is visible even with zero MCPs (not exercised live in this session,
  flagged as an untested edge case, see Coverage Map Axis 2).

## Test Data

### reuse-existing
- The 6 MCPs already present in the `Private` project (see Preconditions).
  No test data needs to be generated for this case — it only exercises the
  list page's view-toggle UI, not MCP CRUD.
- `${TEST_USER}` — only needed on deployed envs; localhost skips login entirely.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/all` (localhost: `APP_PREFIX` is empty, so no
   `/app` prefix).
   - **Verify**: MCP list page loads; page header shows "MCPs"; URL is exactly
     `${BASE_URL}/mcps/all` (no `?view=` query param on a fresh, unvisited
     load).
2. Verify the "Small View Toggler" group (`aria-label="Small View Toggler"`,
   grandparent of both toggle buttons) is visible, containing the Table view
   button (`data-testid="agent-table-view-button"`, `aria-label="Table view"`)
   and the Card list view button (`data-testid="agent-card-view-button"`,
   `aria-label="Card list view"`).
   - **Verify**: both buttons are visible and enabled.
   - **KNOWN DEFECT (informational, non-blocking, see Known Defects):** these
     testids are the exact same ones used on the Agents list page
     (`automation/pages/agents_list_page.py`) — the MCP page does not have its
     own `mcp-*`-scoped testids. Filed as
     `EliteaAI/elitea-testing-public#521`. Automate against the existing
     `agent-*` testids as-is (they are stable and functionally correct);
     re-point the locators to `mcp-*` testids if/when #521 is fixed.
3. Verify the Card list view button is pressed (active) by default on a fresh
   page load.
   - **Verify**: `agent-card-view-button.getAttribute('aria-pressed') === 'true'`;
     `agent-table-view-button.getAttribute('aria-pressed') === 'false'`.
     Confirmed live on a clean navigation (no `?view=` param): card button
     `aria-pressed="true"`, table button `aria-pressed="false"`.
4. Verify MCPs are displayed in card format by default.
   - **Verify**: `[data-testid="entity-card"]` count === number of MCPs in
     the project (6, confirmed live); each card exposes
     `[data-testid="entity-card-name"]` with the MCP's name.
5. Click the Table view button (`agent-table-view-button`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/all?view=table` (the view
     selection is reflected in the URL query param — confirmed live, useful
     for a direct-URL / reload persistence assertion, see Axis 2);
     `agent-table-view-button` becomes `aria-pressed="true"`,
     `agent-card-view-button` becomes `aria-pressed="false"`.
6. Verify MCPs display in table/list format.
   - **Verify**: `[data-testid="entity-card"]` count === 0 (cards gone);
     a table with column headers "Name & Description", "Authors", "Created",
     "Status", "Actions" is visible; row count === number of MCPs (6,
     confirmed live via `document.body.innerText` containing each MCP name
     under the table headers); pagination footer shows "Rows per page: 20"
     and "1 - 6 of 6".
7. Click the Card list view button (`agent-card-view-button`).
   - **Verify**: URL becomes `${BASE_URL}/mcps/all?view=cards`;
     `agent-card-view-button` becomes `aria-pressed="true"`,
     `agent-table-view-button` becomes `aria-pressed="false"`.
8. Verify MCPs display back in card format.
   - **Verify**: `[data-testid="entity-card"]` count === 6 again, matching
     the names observed in step 4 (`autotest_deepwiki_mcp_1954`,
     `verify_ttl_1784105621`, `verify_secret_1784105552`,
     `autotest_remote_mcp_full`, `f`, `Remote Github`); table/rows no longer
     present.

## Expected Results
- The "Small View Toggler" group is visible on the MCP list page with both
  Table view and Card list view buttons reachable and enabled.
- Card view is the default active layout on a fresh, unvisited page load
  (no `?view=` query param).
- Clicking Table view switches the layout to a table (columns: Name &
  Description / Authors / Created / Status / Actions) and updates
  `aria-pressed` state on both buttons; the URL reflects `?view=table`.
- Clicking Card list view re-activates the card layout, restores all MCP
  cards with correct names, and updates `aria-pressed` state back; the URL
  reflects `?view=cards`.
- No console errors and no failed network requests during either toggle
  transition (confirmed live — clean).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user logged in, ≥1 MCP exists | list page accessible with data | Preconditions section | step 1 | asserted — reused 6 pre-existing MCPs, no seed needed live |
| 1 Navigate to MCP list page | MCP list page loads | step 1 | step 1: header + URL | asserted |
| 2 Verify "Small View Toggler" group visible with Table/Card buttons | toggle group displayed | step 2 | step 2: group aria-label + both buttons visible | asserted |
| 3 Verify Card list view button pressed (active) by default | card view is default | step 3 | step 3: `aria-pressed` on both buttons | asserted |
| 4 Click Table view button | table view activated | step 5 | step 5: URL + `aria-pressed` | asserted |
| 5 Verify MCPs display in table/list format | MCPs shown as table rows | step 6 | step 6: column headers + row count + card count 0 | asserted |
| 6 Click Card list view button | card view re-activated | step 7 | step 7: URL + `aria-pressed` | asserted |
| 7 Verify MCPs display back in card format | MCPs shown as cards | step 8 | step 8: card count + names match step 4 | asserted |
| Expected Final State: MCPs displayed in Card view after toggling back | — | step 8 | step 8 | asserted |
| Pass/Fail criteria: all steps complete without error, layout changes correctly | — | all steps | all steps | asserted |

### Axis 2 — Analyst additions

- **step 5/7** assert the URL query param (`?view=table` / `?view=cards`)
  updates on toggle — *added: observed live during exploration, not called
  out in the case text. This is a useful, cheap assertion (confirms the view
  state is URL-addressable/shareable) and also gives the implementer a hook
  for a reload-persistence test later if desired; not required to pass this
  case, but free to assert alongside the `aria-pressed` check since it's the
  same interaction.*
- **step 4/8** assert the exact MCP names shown in card view (not just card
  count) — *added: strengthens the round-trip assertion in step 8 (card view
  after toggling back shows the SAME MCPs, not just "some cards"), directly
  supporting the case's "Expected Final State" line.*
- **Known Defects** section flags the `agent-*`-prefixed testids on the MCP
  page (see step 2) — *added: this is a testid-naming/coverage-metric issue
  discovered during exploration, not a case requirement, but material to how
  the implementer should build `McpListPage` locators (see Concrete Handles).*
- **No console-error assertion added beyond the general clean-check** — the
  page produced no console errors or failed network requests during either
  toggle direction; nothing pre-existing was observed on this page (unlike
  the two known React-warning findings noted in the ELITEA-1922 AFS, which
  are on the MCP *creation* form, not the list page — not re-verified here as
  out of scope for this case).
- **Zero-MCP empty state was NOT explored** — the live test project always had
  ≥1 MCP; the case's own precondition only requires "at least one MCP exists,"
  so this case doesn't require testing the toggle with zero MCPs. Flagged as
  an untested edge case in case the implementer wants a separate, smaller
  case for it later — out of scope here.

## Cleanup

No new test data was created by this analysis session — the case only reads
and toggles a view state on pre-existing MCPs. No cleanup required. If the
implementer's test needs a guaranteed non-zero MCP count and seeds one via
the create flow, that test's own teardown should delete it (see
`ToolkitAPI.delete_toolkit()`, already documented in the ELITEA-1922 AFS).

**Implementer Phase 2 amendment (2026-07-15):** by the time this case was
implemented, the shared dev project's 6 pre-existing MCPs listed above no
longer existed (the environment is shared and other tests' cleanup removed
them) — the "at least one MCP exists" precondition was NOT met live and had
to be seeded. Two things were confirmed live during that seeding:

1. **`/mcps/all` auto-redirects to `/mcps/create` (the type picker) when the
   project has zero MCPs** — the toggle group is NOT visible in that state.
   This resolves the "Zero-MCP empty state was NOT explored" open question
   from the original session: the toggle group requires >=1 MCP to render at
   all, it does not show with an empty list.
2. **Seeding via the raw REST API does not work for this case.** A toolkit
   created directly via `ToolkitAPI.create_toolkit()` (`POST
   tools/prompt_lib/{project}`) returns 201 and is individually fetchable by
   id, but never appears in the list endpoint (`GET
   tools/prompt_lib/{project}` returns `{"rows": [], "total": 0}` regardless
   of params) — and since `/mcps/all` renders from that same list endpoint,
   an API-seeded MCP never becomes visible in the UI either. This is the same
   environment quirk already documented in
   `.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md`
   (`ToolkitAPI.list_all_toolkits()` returns empty on this environment), now
   confirmed to also affect the UI list page itself, not just the API
   client. **Seeding must go through the UI create flow (`McpFormPage`)** —
   confirmed live to populate the list correctly — not the `ToolkitAPI`
   client as this AFS originally suggested as an equally-valid alternative.
   The implemented test (`tests/ui/toolkits/test_mcp_view_toggle.py`) probes
   via `McpListPage.has_any_mcp()` and seeds through `McpFormPage` only when
   the project is genuinely empty, cleaning up via `ToolkitAPI.delete_toolkit()`
   afterward (delete-by-id is unaffected by the quirk).

## Concrete Handles (discovered during exploration)

No new testids were added during this session — all elements needed for this
case already carry usable testids (though the toggle buttons' testids are
misnamed relative to the page they're on, see Known Defects). There is
currently **no page object for the MCP list page** — only
`automation/pages/mcp_form_page.py` (create/detail form) exists. The
implementer should create `automation/pages/mcp_list_page.py` (`McpListPage`,
URL `/mcps/all`), mirroring the shape of `AgentsListPage`
(`automation/pages/agents_list_page.py`) and `PipelinesListPage`
(`automation/pages/pipelines_list_page.py`) — both already implement the
identical card/table toggle pattern with `is_table_view_active()` /
`is_card_view_active()` reading `aria-pressed`, and
`switch_to_table_view()` / `switch_to_card_view()` using `.click(force=True)`
(MUI overlay may intercept, same pattern applies here — not yet verified
whether MCP's toggle needs `force=True` live, but both sibling
implementations do it defensively and this page shares the same
`ToggleButtonGroup` component, so the implementer should keep the same
defensive `force=True`).

| Element | Recommended Locator | Fallback |
|---|---|---|
| Table view button | `[data-testid="agent-table-view-button"]` — **misnamed** (shared with Agents list page; see Known Defects, `EliteaAI/elitea-testing-public#521`) | none — testid-only policy |
| Card list view button | `[data-testid="agent-card-view-button"]` — **misnamed**, same caveat | none |
| MCP card (card view) | `[data-testid="entity-card"]` | none |
| MCP card name (card view) | `[data-testid="entity-card-name"]` | none |
| MCP card tag chip (card view) | `[data-testid="entity-card-tag-chip"]` | none |
| Page header | no dedicated `mcps-page-header` testid found live (unlike Agents' `agents-page-header` / Pipelines' `pipelines-page-header`) — the "MCPs" heading text has no `data-testid`. **Add via `add-data-testid`** if the implementer wants a `wait_for_page_load()` pattern matching the sibling list pages (both `AgentsListPage.wait_for_page_load()` and `PipelinesListPage.wait_for_page_load()` wait on their page-header testid); until then, wait on `agent-card-view-button` visibility as a load-complete proxy (confirmed present as soon as the list renders) | none |
| Table view column header (per column) | `[data-testid="mcp-table-column-header-{field}"]` — `{field}` is the column's `SortFields` id (`name`, `author`, `created_at`, `online`, `actions`). Added via `add-data-testid` in the reviewer fix-pass (EliteaUI draft PR `EliteaAI/EliteaUI#564`): `GridTableHeader.jsx` gained an optional `columnTestIdPrefix` prop, wired only from `DataTable.jsx` when `isMCPs` is true — zero impact on Agents/Pipelines/Skills/Credentials/Toolkits table views, which don't set the prop | none — testid-only policy |
| Table view row name (per row) | `[data-testid="mcp-table-row-name"]` — shared testid across all visible rows (collection locator, matched by text), mirroring the `entity-card-name` convention in card view. Added in the same fix-pass: `DataTableNameCell.jsx`'s row-name `Typography` gets the testid only when `cardType` contains `"mcp"` | none |

**Testids added in the reviewer fix-pass (EliteaUI draft PR `EliteaAI/EliteaUI#564`,
cherry-picked from `automation/testids` commit `3eba20e`):** the original session below flagged
these as missing/interim; the implementer fix-pass (2026-07-15, responding to a
`CHANGES_REQUESTED` review on PR #523 for a non-testid `get_by_text()` locator
violation) added them via `add-data-testid` rather than leaving the interim
text-matching approach — see the two rows above. The original "Missing testids
to flag" list below is kept for history; item 2 (the page-header testid) is
still open.

**Still-missing testids to flag for `add-data-testid` (not blocking this case,
but recommended for a follow-up):**
1. `mcps-page-header` (or similar) on the "MCPs" heading — parity with
   Agents/Pipelines list pages, needed for a clean `wait_for_page_load()`.
2. MCP-scoped view-toggle testids (`mcp-table-view-button` /
   `mcp-card-view-button`) — tracked in
   `EliteaAI/elitea-testing-public#521`, not required to implement this case
   (the existing `agent-*` testids work fine functionally) but the right fix
   long-term for the coverage metric.

## Network Behavior
- No new network requests fire on view toggle — confirmed via
  `get-network --status error` returning `[]` after both toggle clicks; the
  view switch is a pure client-side render/URL-state change (no
  refetch of MCP list data between card ↔ table).
- The MCP list itself is presumably fetched once on initial page load (not
  specifically captured/named in this session — out of scope, the case only
  concerns the toggle, not the initial list-load request).

## Known Defects Found During Exploration

**No functional defects.** All 8 case steps (as decomposed above) produced
the expected result live: Card view defaults active, Table view toggles
correctly with proper columns/rows, Card view restores correctly with the
same MCPs, no console errors, no failed network requests.

**One low-severity, non-blocking naming/coverage-metric issue filed:**
- `EliteaAI/elitea-testing-public#521` — the MCP list page's view-toggle
  buttons carry `agent-table-view-button` / `agent-card-view-button` testids
  (identical to the Agents list page) instead of MCP-scoped testids, unlike
  the Pipelines list page which correctly threads its own `pipeline-*`
  testids into the same shared toggle component. Does not block automating
  this case — the existing testids are stable and functionally correct — but
  corrupts this project's testid-presence-based coverage metric (an MCP test
  asserting on an `agent-*` handle misattributes coverage to the wrong
  feature area). `expect.soft()` not needed here since this isn't an
  assertion-blocking defect; automate against the existing handles as
  documented above.
