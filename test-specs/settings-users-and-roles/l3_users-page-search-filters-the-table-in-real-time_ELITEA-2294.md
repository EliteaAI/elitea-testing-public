# Test Case: Users page search filters the table in real time

## Metadata
- **TMS ID**: ELITEA-2294
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2294.md`
- **Linked Story**: none
- **Priority**: l3 (case frontmatter `priority: medium`). **pytest marker:
  `@pytest.mark.p2`**.
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` -> DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: ready-for-automation

## Preconditions
- Logged in, `admin` in project 400 (see `_surface.md` § project-topology).
- At least **two** user rows whose emails/names differ enough that a probe can
  filter to a proper subset. Live at analysis time: 4 rows.

## Test Data
### reuse-existing
- `${USERS_TEAM_PROJECT_ID}` = `400`; whatever rows exist — read-only.
- **The probes are DERIVED FROM THE OBSERVED DATA at runtime**, never
  hardcoded: the test reads the rendered emails/names and picks the first
  prefix that yields a proper, non-empty subset. A literal `"epam"` would
  break the day the user set changes.

## Test Steps
1. Navigate to Settings -> Users.
   - **Verify**: >= 2 rows render; the search input (`users-search-input`) is
     visible, empty, and carries the exact placeholder `"Search "` (trailing
     space).
   - Capture the full email set and name set as the restore baseline.
2. Type a derived **partial email** into the search field, one character at a
   time, **without pressing Enter**.
   - **Verify**: the field displays the typed value.
3. **Verify** the table filtered in real time to exactly the matching rows,
   and that the filtered count is **strictly less** than the unfiltered count
   (an equal count would also pass for a no-op filter).
4. Clear the search field, then type a derived **partial name** the same way.
   - **Verify**: the field displays the typed value.
5. **Verify** the table shows exactly the rows whose name matches.
6. Clear the search field.
   - **Verify**: the field is empty and **every** user is shown again — the
     restored row count equals the baseline and the restored email **set**
     equals the baseline set.
7. **Verify** no unexpected console errors across the flow.

## Expected Results
- Filtering happens per keystroke with no Enter and no submit control.
- An email probe and a name probe each narrow the table to their matches.
- Clearing restores the complete original set.
- No console errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: user is logged in | — | `auth_state` fixture | implicit — permission-gated page renders | asserted |
| 1 Navigate to Settings -> Users as Admin | Target page/section loads successfully | step 1 | `step 1`: rows visible, search input visible + empty | asserted |
| 2 Type a partial email in the Search field | Field accepts the input and displays the entered value | step 2 | `step 2`: `get_search_value() == probe` | asserted |
| 3 Verify the table filters to show only matching users | Condition holds as described | step 3 | `step 3`: rendered email list == expected matches, count strictly < baseline | asserted |
| 4 Clear search and type a partial name | Action completes without error and produces the expected UI state | step 4 | `step 4`: field cleared then displays the name probe | asserted |
| 5 Verify the table filters to show only matching names | Condition holds as described | step 5 | `step 5`: rendered name list == expected matches | asserted |
| 6 Clear search — verify all users are shown again | Action completes without error and produces the expected UI state | step 6 | `step 6`: field empty, row count == baseline, email SET == baseline set | asserted |
| Expected Final State: Clear search — verify all users are shown again | (restates step 6) | step 6 | same as row above | asserted |

**Axis 2 — Analyst additions:**
- Step 3 asserts the filtered count is **strictly less** than the baseline —
  *added: "shows only matching users" is satisfied vacuously by a filter that
  matches everything; this is the assertion that makes the claim real.*
- Step 1 asserts the exact placeholder `"Search "` — *added: the case names
  the control "the Search field"; the placeholder is how it is identified in
  the UI, and it is a deterministic literal in `Users.jsx`.*
- Step 6 compares **sets**, not ordered lists — *added: the table's sort
  order is orthogonal to the search and survives a clear, so an ordered
  comparison would be asserting sort state this case never touched.*
- Step 7 no-console-errors side-channel check — *standard discipline;
  confirmed 0 errors live.*
- The typing is `press_sequentially`, never `fill` + Enter — *the case's
  subject is the words "in real time", and `SimpleSearchBar` filters from the
  native `onChange` with no debounce and no submit control. Pressing Enter
  would defeat the case.*

## Cleanup
None — read-only. Filtering is client-side over an already-cached list.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| Search input | `users-search-input` | pre-existing (ELITEA-2292) — on `automation/testids` |
| Rows | `user-row` | pre-existing |
| Row name / email cells | `user-row-name`, `user-column-value-email` | pre-existing |

No new testid is needed for this case.

## Network Behavior
Filtering is **client-side** (`Users.jsx`'s `filteredUsers` memo filters the
already-fetched array) — **no request fires on a keystroke**, confirmed live.
Assertions therefore wait on rendered rows, never on a response.

**Live-confirmed matching rule (`Users.jsx:82-92`):** a row matches when the
lower-cased search term is a substring of its **email OR name OR joined
roles**. The roles arm means a probe that happens to be a substring of
`admin`/`editor`/`viewer` will match on role too — the runtime probe
derivation must therefore compute its expected matches with the SAME
three-arm rule, not an email-only or name-only one.

## Known Defects Found During Exploration
None.

## Blocked Steps
None.

## Automation Hints
- Page object: extend `AdminUsersPage` with `type_search`, `clear_search`,
  `get_search_value`, `get_row_emails`, `get_row_names` — mirror
  `PersonalTokensPage`'s equivalents exactly (same shared `SimpleSearchBar`).
- `clear_search` via `ControlOrMeta+a` then `Backspace` — confirmed live on
  this field (plain MUI `InputBase`, no auto-blur wrapper).
- The `users-search-input` testid resolves to the native `<input>`, so
  `input_value()` works directly.
- The no-match branch (zero rows + "No users" empty message) is deliberately
  NOT in scope: the case never asks for it, and the grid-table empty message
  carries no testid on this surface (adding one would be out-of-scope testid
  work per canon ruling #511).

### Console-error assertion — known-defect exclusion (implementer, 2026-08-29)

The final "no unexpected console errors" step excludes ONE exact URL:
`/api/v2/elitea_core/toolkits/prompt_lib/` (project-id-less), via
`utils.console_errors.exclude_known_defect_urls` with a `# Known defect: #1971`
comment. **#1971 is a filed, OPEN product defect** (regression of the closed
#554): during the project switch `AdminUsersPage.navigate()` performs, EliteaUI's
`toolkitTypes` RTK-Query fires before `useSelectedProjectId()` resolves and
requests a project-id-less path, which 404s. Cosmetic in the product, unrelated
to anything this case drives — but it intermittently failed the console step on
2 of 4 full-suite runs of this wave.

The exclusion is keyed to the **exact URL, never the status code** (a "404"
filter would swallow the next genuine one — masking, explicitly ruled out in
`.agents/testing.md` § Unconfirmed). One argument to delete when #1971 ships.
