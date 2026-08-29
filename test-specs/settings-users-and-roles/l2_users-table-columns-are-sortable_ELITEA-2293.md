# Test Case: Users table columns are sortable

## Metadata
- **TMS ID**: ELITEA-2293
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2293.md`
  (snapshot; TMS module `settings-users-and-roles`)
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: high`). **pytest marker:
  `@pytest.mark.p1`** — project convention TMS `high` -> AFS `l2_` -> pytest `p1`.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project "UI Testing" /
  `${USERS_TEAM_PROJECT_ID}` = 400)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via
  `VITE_DEV_TOKEN`; admin in project 400 only — see `_surface.md`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in, acting user holds `admin` in project 400 (the Users page is
  permission-gated and hidden entirely for a private project — see
  `AdminUsersPage.navigate()`'s two-hop project switch).
- At least **two** user rows exist so an ordering assertion is not vacuous.
  Self-guaranteed floor: the acting admin is always a member; project 400
  held **4 rows** at analysis time (2 real users + 2 orphaned
  `elitea-batch-edit-test2-*@example.com` rows left behind by an earlier
  ELITEA-2304 run — reported as a finding, not relied on).

## Test Data
### reuse-existing
- `${USERS_TEAM_PROJECT_ID}` = `400`.
- Whatever user rows the project holds — read-only. **No literal name /
  email / datetime is ever hardcoded**: every expectation is derived at
  runtime from the rendered table (§ Assertion shape).

## Assertion shape — relational, not literal
The user set is shared, mutable, real data. Assertions therefore compare the
**observed** rendered order against `sorted(observed)` / `sorted(observed,
reverse=True)` rather than a fixed list. The values still come from the
product on both sides of the comparison (the test never authors a row), so
this is the correct assertion, not a weakened one.

`useTableSort` (`entities/grid-table/lib`) is the sort engine, confirmed by
source read + live: case-insensitive string compare, and **null/blank values
sort LAST ascending, FIRST descending**. Project 400 exercises both null
branches live (2 rows have a blank Name and a `-` Last login), so the
null-placement rule is part of the expected ordering, not an edge case to
dodge.

## Test Steps
1. Navigate to Settings -> Users (`AdminUsersPage.navigate()`).
   - **Verify**: at least 2 rows render; exactly 3 sort controls exist
     (`user-sort-icon-name`, `-email`, `-last_login`) and **zero** on the
     non-sortable columns (`user-sort-icon-roles`, `-actions` -> count 0).
   - **Verify**: the table arrives **already name-ASCENDING** with no
     interaction (`useTableSort({defaultField:'name', defaultDirection:'asc'})`).
2. Click the **Name** column header.
   - **Verify**: the rendered name order is now name-**DESCENDING**
     (`sorted(names, reverse=True)`, blanks first). See § Case-text
     divergence — the case text claims ascending here; the product is right.
3. Click the **Name** column header again.
   - **Verify**: the order returns to name-ASCENDING — byte-identical to the
     load-time order captured in step 1.
4. Click the **Email** column header.
   - **Verify**: the rendered email order is email-ASCENDING (switching to a
     new field always starts at `asc` — `useTableSort`'s
     `prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'`).
   - **Verify**: the row count is unchanged (sorting reorders, never filters).
5. Click the **Last login** column header.
   - **Verify**: dated rows are in ascending datetime order and every blank
     (`-`) row sorts AFTER every dated row.
   - **Verify**: the row count is unchanged.
6. Click the **Last login** column header again.
   - **Verify**: the relation inverts — every blank row precedes every dated
     row, and the dated rows are in descending datetime order.
   - **Verify**: the row count is unchanged.
7. **Verify** no unexpected console errors across the flow.

## Expected Results
- Exactly the three columns the case marks sortable expose a sort control;
  Role and Actions expose none.
- Each sortable header toggles its column between the two directions, and the
  Name column returns to its load-time order after two clicks.
- Sorting only reorders: the row count is invariant across every click.
- No console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — the permission-gated page renders | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible after `navigate()` | asserted |
| 2 Click the Name column header (↕) | Control responds; expected next state is shown | step 2 | `step 2`: order flips to name-descending | asserted |
| 3 Verify rows sort alphabetically ascending by name | Condition holds as described | steps 1 + 3 | `step 1`: load-time order IS name-ascending; `step 3`: the SECOND click returns to it — **case-text divergence, see below**; the ascending state is fully asserted, just not at the click the case names | asserted (divergence filed) |
| 4 Click again — verify rows sort descending | Control responds; expected next state is shown | step 2 | `step 2`: the FIRST click produces descending (same divergence, mirrored) | asserted (divergence filed) |
| 5 Click the Email column header — verify rows sort by email | Control responds; expected next state is shown | step 4 | `step 4`: email order == `sorted(emails)`, row count unchanged | asserted |
| 6 Click the Last login column header — verify rows sort by last login datetime | Control responds; expected next state is shown | steps 5 + 6 | `step 5`/`step 6`: dated rows ordered, blanks placed per direction, row count unchanged | asserted |
| Expected Final State: Click the Last login column header — verify rows sort by last login datetime | (restates step 6) | steps 5 + 6 | same as row above | asserted |

**Case-text divergence (reverse-masking guard).** Case steps 2-4 assume the
first Name click yields ascending and the second descending. The product's
default sort is ALREADY name-ascending, so the first click flips to
**descending** and the second returns to ascending. The product is correct
and internally consistent (`useTableSort`); the case text is stale. The test
asserts the live contract and the divergence is filed as a case-text
clarification — **sibling of #1880**, which recorded the byte-identical
pattern on the Personal Tokens table (different surface, different case, so a
sibling and not a duplicate, per `.agents/profile.md` § Bug filing).

**Axis 2 — Analyst additions:**
- Step 1 asserts the sort-control **absence** on Role/Actions — *added: the
  case title claims WHICH columns are sortable; without the negative side the
  claim would still pass if every column became sortable.*
- Steps 4-6 assert the **row count is invariant** — *added: a filter
  masquerading as a sort would satisfy an ordering assertion alone; this is
  the cheapest guard that separates "reordered" from "reordered and dropped
  rows".*
- Steps 5-6 assert **null placement** explicitly — *added: it is the live
  contract on this data (2 of 4 rows have no last login) and asserting only
  the dated subset would silently tolerate blanks migrating anywhere.*
- Step 7 no-console-errors side-channel check — *standard discipline;
  confirmed 0 errors live.*

## Cleanup
None — read-only. Sorting is client-side over the RTK-Query cache; no request
fires on a header click and no state is persisted.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| Column headers (click targets) | `user-column-header-{name,email,last_login,roles,actions}` | pre-existing (ELITEA-2292) — on `automation/testids`; promotion to `main` is the human's |
| Sort-indicator icons | `user-sort-icon-{name,email,last_login}` | pre-existing (ELITEA-2292, EliteaAI/EliteaUI@52582fe3) |
| Rows | `user-row` | pre-existing |
| Row name cell | `user-row-name` | pre-existing |
| Row email / last-login cells | `user-column-value-email`, `user-column-value-last_login` | pre-existing |

No new testid is needed for this case.

## Network Behavior
Sorting is **client-side** — no request fires on a header click (confirmed
live). Only the page-mount `GET /admin/users/default/400` and
`GET /admin/roles/default/400` fire, both 200 OK.

## Known Defects Found During Exploration
None. One case-text divergence (above), not a product defect.

## Blocked Steps
None.

## Automation Hints
- Page object: extend `automation/pages/admin_users_page.py`. It already has
  the column-header and sort-icon handles; add `click_column_header(field)`,
  `get_row_names()`, `get_row_emails()`, `get_row_last_logins()`,
  `get_sort_icon(field)` mirroring `PersonalTokensPage`'s equivalents.
- Wait on the **reordered DOM**, never on a response and never on a sleep —
  use `expect(...).to_have_text([...])` on the repeatable cell locator so the
  assertion auto-retries through the re-render.
- The Name column's blank cells render as an empty string (`user-row-name` is
  present but empty for invited-not-yet-logged-in users), while the Last
  login column renders the literal `-` for a null — two different null
  renderings on the same table; do not assume one shape.
