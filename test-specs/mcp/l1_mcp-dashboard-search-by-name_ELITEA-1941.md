# Test Case: MCP Dashboard — Search by Name

## Metadata
- **TMS ID**: ELITEA-1941
- **Linked Story**: none
- **Priority**: l1
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-07-16
- **Status**: defect-found

## Preconditions
- User is authenticated (on localhost this is automatic via `VITE_DEV_TOKEN`;
  on deployed envs, standard Keycloak login via `${TEST_USER}`).
- Project context is set (sidebar shows `Project: Private`; project id read
  from `${ELITEA_PROJECT_ID}`).
- At least one MCP exists in the project — **case's stated precondition
  ("at least one MCP named 'Web Search'") does NOT hold live**: the `Private`
  test project has 6 pre-existing MCPs and none is named "Web Search" or
  contains "Web" (`autotest_deepwiki_mcp_1954`, `verify_ttl_1784105621`,
  `verify_secret_1784105552`, `autotest_remote_mcp_full`, `f`,
  `Remote Github`) — same 6 reused by `l1_mcp-dashboard-view-toggle-card-table_ELITEA-1944.md`.
  Case-text drift (CLARIFICATION, reverse-masking guard) — the match search
  term was substituted with `github` (matches exactly one existing MCP,
  "Remote Github") for this AFS; see Test Data.

## Test Data

### reuse-existing
- The 6 MCPs already present in the `Private` project (see Preconditions).
- `${TEST_USER}` — only needed on deployed envs; localhost skips login.

### Adapted from case (case-text drift — see Preconditions)
- Search term (match), **adapted**: `github` (matches exactly 1 of 6 MCPs:
  "Remote Github"). Case's literal `Web` / "Web Search" does not exist live.
- Search term (no match), **as specified**: `nonexistent_xyz_mcp`.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/all` (localhost: `APP_PREFIX` is empty, no
   `/app` prefix).
   - **Verify**: MCP list page loads; all 6 MCPs visible as cards.
2. Verify the search textbox (`data-testid="agent-search-input"`) is visible
   with placeholder `"Let's find something amazing!"`.
   - **Verify**: `input.getAttribute('placeholder') === "Let's find something amazing!"`.
     Confirmed live, exact match to case wording.
3. Click the search box, type `github`, press **Enter** (see Automation Hints
   — filtering is explicit-activation, not live-as-you-type).
   - **Verify**: filter is applied after Enter (not before — confirmed live,
     see Concrete Handles § filtering mechanics).
4. Verify only MCPs with "github" in the name are shown.
   - **Verify**: `[data-testid="entity-card-name"]` count === 1, text ===
     "Remote Github". Confirmed live — the other 5 MCPs are hidden.
5. Clear search (`data-testid="search-clear-button"`) and type
   `nonexistent_xyz_mcp`, press Enter.
   - **Verify**: filter is updated.
6. Verify no results are shown (empty state).
   - **Verify**: `[data-testid="empty-state-title"]` is visible.
   - **CLARIFICATION (content accuracy, non-blocking for this step):** the
     empty state shown is the generic zero-MCPs-in-project state — text
     reads **"No MCPs yet"** / "Create your first MCP…", identical to what
     renders when the project genuinely has 0 MCPs. It does not distinguish
     "no MCPs exist" from "no MCPs match this search," which is misleading,
     but an empty state per the case's loose wording ("empty state or
     'no results' message") IS technically displayed. Flagged, not filed
     as its own ticket (noted inside the Known Defects issue below) — the
     step 7 defect below is the blocking one.
7. Clear search (`data-testid="search-clear-button"`) — verify all MCPs
   reappear.
   - **DEFECT — see Known Defects Found.** Actual: clicking Clear while the
     zero-match empty state (step 6) is showing navigates the browser away
     to `${BASE_URL}/mcps/create` instead of restoring the MCP list. Step 7
     as written cannot pass. Confirmed 2/2 reproductions, fresh
     `page.goto()` each time, real Playwright `locator().click()` (not
     JS-evaluated).

## Expected Results
- Search box has the placeholder text from the case.
- A matching search term filters the visible card list to only matching
  MCPs (case term "Web"/"Web Search" replaced with "github"/"Remote Github"
  — see Preconditions).
- A non-matching search term shows an empty state.
- Clearing the search restores the full unfiltered MCP list — **does NOT
  hold live; see Known Defects Found**.

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: MCP named "Web Search" exists | — | Preconditions | n/a | clarification *(case-text drift — no such MCP in live project; term substituted, see Preconditions)* |
| 1 Navigate to `/app/mcps/all` (case says `/app/mcps/all`; localhost has no `/app` prefix) | MCP list page loads | step 1 | step 1: all 6 cards visible | asserted *(clarification: path adapted per `APP_PREFIX`, per project convention — not a defect)* |
| 2 Verify search textbox visible with placeholder | search box displayed w/ correct placeholder | step 2 | step 2: placeholder attr | asserted |
| 3 Type "Web" in search box | filter is applied | step 3 | step 3: Enter submits filter | asserted *(term adapted to "github", see Preconditions)* |
| 4 Verify only MCPs with "Web" in name shown (e.g. "Web Search") | only matching MCPs visible | step 4 | step 4: card-name count === 1 | asserted *(term/expected-match adapted to "github"/"Remote Github")* |
| 5 Clear search and type "nonexistent_xyz_mcp" | filter is updated | step 5 | step 5 | asserted |
| 6 Verify no results shown (empty state or no-results message) | empty state or no-results message displayed | step 6 | step 6: `empty-state-title` visible | asserted, with a content-accuracy CLARIFICATION noted inline (see step 6) |
| 7 Clear search — verify all MCPs reappear | all MCPs visible again | step 7 | step 7 | **defect** — does not pass live, see Known Defects Found |
| Expected Final State: list returns to showing all MCPs after clear | — | step 7 | step 7 | **defect** — same as above |

**Axis 2 — Analyst additions.**

- step 4 asserts the exact surviving card name (`"Remote Github"`), not just
  a count — *added: a bare count of 1 doesn't prove the **right** MCP
  survived the filter; asserting identity closes that gap.*
- step 7 (control check, not in the case) — clearing a search that still has
  ≥1 matching result (e.g. clearing after searching "github", which has a
  match) restores the list correctly, no redirect — *added: needed to
  isolate the defect to "clearing from a zero-match state" specifically,
  rather than "clearing" in general; this scopes the regression test's
  precondition precisely.*
- Console messages checked after every step (steps 1, 3, 5, 7) — *added: the
  one error present throughout the session (`ToolkitTypeSelector.jsx` React
  "key" prop warning) was confirmed pre-existing/unrelated, not caused by
  this case's actions — ruled out before filing the navigation defect.*

## Cleanup
- No test data created (search-only case against `reuse-existing` MCPs) — no
  cleanup required.
- If run against a project seeded specifically for this case, no MCP
  creation/deletion is needed either; only search-state (query cleared) which
  self-resets on next navigation.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Search textbox | `getByTestId('agent-search-input')` | none needed — testid unique, confirmed live (shared `SearchBar.jsx` component, default `testId` prop — same handle as Credentials/Skills/Toolkits/Applications search, per `useSearchBar.jsx` / `RightPanel.jsx`) |
| Search Clear (X) icon | `getByTestId('search-clear-button')` | none needed — confirmed unique in DOM (`document.querySelectorAll` count === 1) |
| Search Send icon | `getByTestId('search-send-button')` | not exercised this session (Enter key used instead — see Automation Hints); present in `SearchBar.jsx`, same shared component |
| MCP card name (collection) | `getByTestId('entity-card-name')` | already in `automation/pages/mcp_list_page.py` as `mcp_card_name` — reuse, don't redeclare |
| Zero-match empty state title | `getByTestId('empty-state-title')` | **newly added this session** — `EliteaUI/src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx`, on the `Typography` rendering `title` (shared `EmptyStatePage` component, used by MCP/Toolkits/Applications/Skills/Pipelines/PersonalTokens list pages — generic testid per the "shared component" locator ruling, no caller-scoped variant exists) |

### Filtering mechanics (non-obvious, confirmed live)

The search box does **not** live-filter on keystroke. `SearchBar.jsx`'s
`handleInputChange` only updates local input state; the actual filter
dispatch (`actions.setQuery`) fires only from `onSearch`, triggered by
**Enter** or the Send icon click, and only when the trimmed term is
`>= MIN_SEARCH_KEYWORD_LENGTH` (3) characters. Automation must press Enter
(or click `search-send-button`) after typing — typing alone does not filter.
Same mechanics as the Credentials search precedent
(`automation/pages/credentials_list_page.py::search`).

## Network Behavior
- Not captured — filtering is client-side against an already-fetched MCP
  list (no new XHR observed firing on Enter/filter-apply in this session).
  Not asserted; flag if the implementer sees otherwise on a re-check.

## Known Defects Found During Exploration

- **[MAJOR] Clearing a zero-match MCP search redirects to `/mcps/create`
  instead of restoring the list.** Filed:
  `EliteaAI/elitea-testing-public#585`. Reproduced 2/2, fresh navigation
  each time, real Playwright click (not synthetic). Control check confirms
  the bug is specific to clearing **from the empty (zero-match) state** —
  clearing a search that still has ≥1 result works correctly and does not
  redirect. Automation for step 7 should assert the **current (broken)**
  behavior with `# Known defect: EliteaAI/elitea-testing-public#585` per
  `.agents/testing.md` § Merge gate sanctioned-RED exception, OR the
  implementer/lead may choose to leave step 7 `blocked`/skipped until the
  product fix ships — lead's call per merge-gate policy.
- **[INFO/content, not separately filed]** The zero-match empty state reuses
  the generic "No MCPs yet / Create your first MCP…" copy — identical to
  the genuine zero-MCPs-in-project state, not distinguishing "no MCPs
  exist" from "no MCPs match this search." Noted inline in issue #585 (its
  "Related" section) as likely the same stale empty-check surfacing both
  defects; not filed as a second ticket per this project's strict-per-bug
  default (the umbrella-bundling prerequisites don't hold here) — mentioning
  it here so the fix owner sees both symptoms together.

## Blocked Steps
- None — the case's steps could all be *executed*; step 7 is a defect, not
  a block (the action is performable, the app just does the wrong thing).

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`), page object
  `automation/pages/mcp_list_page.py` — extend it with `search_input`,
  `search_clear_button`, `search_send_button`, `empty_state_title` fields
  (do not redeclare `mcp_card_name`, already present).
- Reuse the `search()` / `clear_search()` method shape already implemented
  in `automation/pages/credentials_list_page.py` (explicit-activation via
  Enter, `assert_unfiltered_while_typing` flag, clear-then-wait-for-network
  pattern) — same shared `SearchBar.jsx` component, same mechanics.
- Wait strategy: after Enter, wait for the card/table content to settle
  (`wait_for_network` + a short settle, per `mui-patterns.md` § MUI Debounce
  Patterns) before asserting filtered results — confirmed ~1–1.5s render lag
  live.
- Step 7's regression test (once written) should navigate fresh, search a
  no-match term, then click clear, and assert
  `page.url` **stays** `${BASE_URL}/mcps/all` (soft-assert, tied to
  `EliteaAI/elitea-testing-public#585`) rather than asserting the ultimately
  correct behavior outright — see `.agents/testing.md` § Merge gate
  sanctioned-RED exception.
