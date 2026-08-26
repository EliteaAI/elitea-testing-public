# Test Case: MCP Dashboard — Filter by Type (Remote only)

## Metadata
- **TMS ID**: ELITEA-1942
- **Linked Story**: none
- **Priority**: l1 (case frontmatter `priority: high`; case body says "Priority: medium" — inconsistent in the TMS, treated as high per frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project 399)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, cluster dispatch with ELITEA-1943 (batch `mcp-w03`)
- **Status**: ready-for-automation
- **Sibling case**: ELITEA-1943 (Local-only filter) — **blocked**, see
  `test-specs/mcp/l1_mcp-dashboard-filter-by-type-local_ELITEA-1943.md`

## Preconditions

- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- Project contains **at least one Remote MCP**. Live at analysis time: 19 MCPs,
  **all Remote** (`autotest_conn_tools_a1`, `Remote Github`, `f`, …).
- **The case's precondition "Both Local MCPs (e.g. ADO, FileSystem,
  PlaywrightMCP) and Remote MCPs exist" does NOT hold and cannot be made to
  hold in this environment** — `GET /api/v2/elitea_core/toolkit_types/prompt_lib/399?mcp=true`
  returns `{"rows": ["mcp"], "total": 1}` (Remote only) and `/mcps/create`
  offers exactly one type card (`toolkit-type-card-mcp` = "Remote MCP"), so a
  Local MCP can neither be found nor created. Parked for a human as
  **question #1738**. Consequence for this case: step 5 ("Local MCPs are
  hidden") is *vacuously* true and is automated as the honest, test-enforced
  form — **no rendered card carries a `Local` type badge while the Remote
  filter is active** (absence assertion), not as "ADO/FileSystem/PlaywrightMCP
  disappeared".
- With **zero** MCPs in the project `/mcps/all` auto-redirects to `/mcps/create`
  and the Types panel never renders — the existing `McpListPage.has_any_mcp()`
  seed-if-empty guard (see `tests/ui/toolkits/test_mcp_view_toggle.py`) is the
  established pattern and applies here too.

## Test Data

### reuse-existing
- Whatever MCPs the project already holds — the test must NOT hardcode the
  count 19 or any MCP name; it captures the unfiltered baseline in step 1 and
  compares against it (the DEV project is shared and churns constantly).

No test data is created.

## Test Steps

1. Navigate to `${BASE_URL}/mcps/all` (localhost: `APP_PREFIX` empty).
   - **Verify**: the MCP list renders; capture the unfiltered baseline —
     `baseline_names = [entity-card-name…]`, `baseline_count = len(...)`.
   - **Verify**: `[data-testid="tags-panel-clear-all"]` has count 0 (no filter
     active on a clean load).
2. Verify the "Types" filter area shows both type chips.
   - **Verify**: `[data-testid="tags-panel-chip-Local"]` visible.
   - **Verify**: `[data-testid="tags-panel-chip-Remote"]` visible.
   - Confirmed live: the MCP Types panel is **hardcoded** to exactly these two
     chips (`useLoadToolkits.hooks.js` `tagList`, `isMCP` branch) — it is NOT
     data-derived, so both chips render regardless of what the project holds.
     (This differs from Credentials' Types panel, which IS data-derived.)
   - The panel title text "Types" carries no testid; asserting the two chips
     (which do) is the testid-only equivalent and is what the case's intent
     ("Types label and filter buttons Local and Remote are visible") reduces
     to. Do **not** add a testid for the title — nothing else needs it (#511).
3. Click the **Remote** chip.
   - **Verify**: the filter is applied — `page.url` contains `tags%5B%5D=Remote`
     (i.e. `?tags[]=Remote`), **and** `[data-testid="tags-panel-clear-all"]`
     becomes visible (the product's own "a filter is active" signal, same
     reading `CredentialsListPage` already uses).
   - Confirmed live: this fires a real server-side filtered request —
     `GET …/tools/prompt_lib/{project}?query=&sort_by=created_at&sort_order=desc&mcp=true&limit=20&offset=0&toolkit_type=mcp`.
4. Verify only MCPs with a "Remote" type badge are displayed.
   - **Verify**: every visible card's type badge reads `Remote` —
     `set(badge_texts) == {"Remote"}` over the page-wide
     `entity-card-tag-chip` collection, and the badge count equals the card
     count (every card is badged, none unlabelled).
   - **Verify**: card count == `baseline_count` and names == `baseline_names`
     — in this environment every MCP is Remote, so the Remote filter is a
     no-op on the result set. Assert equality against the **captured**
     baseline, never a literal.
5. Verify Local MCPs are hidden.
   - **Verify (absence)**: `badge_texts.count("Local") == 0` — no rendered card
     carries a Local badge while the Remote filter is active.
   - **CLARIFICATION**: vacuous in this environment (see Preconditions /
     question #1738) — the assertion is kept so it turns red the day a Local
     MCP exists and leaks through the Remote filter.
6. Click the **Remote** chip again to deselect it.
   - **Verify**: `page.url` no longer contains `tags%5B%5D=` (back to
     `/mcps/all`), and `[data-testid="tags-panel-clear-all"]` has count 0.
   - Confirmed live 1/1 by re-click; the panel's **Clear all** button
     (`tags-panel-clear-all`) is a verified equivalent path (1/1) — the case
     itself allows either ("or click elsewhere to clear").
7. Verify all MCPs reappear.
   - **Verify**: card names == `baseline_names` (order preserved live) and
     count == `baseline_count`.

## Expected Results

- Both "Local" and "Remote" type chips are present in the Types panel.
- Selecting "Remote" applies a filter (URL param + Clear-all control) and the
  list shows only Remote-badged MCPs; no Local-badged card is rendered.
- Deselecting restores the unfiltered list exactly as captured in step 1.
- No console errors during the flow (verified live: 0 errors on `/mcps/all`
  across the whole filter flow).

## Coverage Map

**Axis 1 — Case coverage.**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: both Local and Remote MCPs exist | — | Preconditions | n/a | **clarification** — unsatisfiable in DEV, parked as question #1738; Remote half satisfied |
| 1 Navigate to MCP list page | page loads | step 1 | baseline captured, list rendered | asserted |
| 2 "Types" label + "Local"/"Remote" filter buttons visible | both displayed | step 2 | both `tags-panel-chip-*` visible | asserted *(title text has no testid — chips are the testid-only equivalent)* |
| 3 Click "Remote" filter button | filter applied | step 3 | URL `tags[]=Remote` + `tags-panel-clear-all` visible | asserted |
| 4 Only MCPs with "Remote" badge displayed | only Remote shown | step 4 | badge set == {"Remote"}, badge count == card count | asserted |
| 5 Local MCPs (ADO/FileSystem/PlaywrightMCP) hidden | Local not visible | step 5 | zero `Local` badges | asserted as an absence *(vacuous in this env — clarification, see Preconditions)* |
| 6 Click "Remote" again to deselect | filter deactivated | step 6 | URL param gone + clear-all count 0 | asserted |
| 7 All MCPs reappear | all visible | step 7 | names/count == captured baseline | asserted |
| Expected Final State: all MCPs displayed after removing the filter | — | step 7 | same | asserted |

**Axis 2 — Analyst additions.**

- Step 1 captures the unfiltered baseline instead of asserting a literal count
  — *added: the DEV project is shared and its MCP set changes between runs
  (19 today, 6 in the ELITEA-1941/1944 sessions); a literal would be flaky
  and would prove nothing about the filter.*
- Step 3 asserts BOTH the URL query param and the `tags-panel-clear-all`
  control — *added: the chip's selected state is expressed ONLY through an
  emotion CSS class hash (`css-1oy09ev` selected vs `css-16qy5qb` idle), which
  is not a legal handle here and is not stable across builds; the URL param
  plus the product's own clear-all affordance are the two honest, stable
  signals that a filter is active.*
- Step 4 asserts badge count == card count — *added: `set(badges) == {"Remote"}`
  alone passes if a card renders no badge at all; pairing the counts closes
  that hole.*
- Step 1 asserts clear-all is absent on a clean load — *added: without it,
  step 3's clear-all assertion could be satisfied by a leftover filter from a
  previous test in the same session.*
- Console-error check across the flow — *added: standard side-channel check;
  verified clean live (0 errors) so an assertion here is honest, unlike on
  `/mcps/create` which carries a pre-existing React warning (#291/#656).*

## Concrete Handles (discovered/confirmed during exploration)

| Element | Handle | Provenance (verified 2026-08-24, `git fetch origin` first) | Notes |
|---|---|---|---|
| Types-panel type chip (dynamic) | `[data-testid="tags-panel-chip-{TypeName}"]` → `tags-panel-chip-Local`, `tags-panel-chip-Remote` | **on-main ✓** | `Categories.jsx:336`. Runtime-parameterized ⇒ UPPER_CASE class-level template constant (`.agents/testing.md` § Locator policy). **`CredentialsListPage.TYPE_FILTER_CHIP` is the identical constant** — mirror it in `McpListPage`. |
| Types-panel "Clear all" | `tags-panel-clear-all` | **on-main ✓** | `Categories.jsx:299`. Rendered **only** while ≥1 chip is selected ⇒ its presence IS the "a filter is active" signal; assert absence with `to_have_count(0)` (it is unmounted, not hidden). |
| MCP card | `entity-card` | on-main ✓ | already `McpListPage.mcp_card` |
| MCP card name | `entity-card-name` | on-main ✓ | already `McpListPage.mcp_card_name` / `get_card_names()` |
| Card type badge (Local/Remote) | `entity-card-tag-chip` | on-main ✓ | `McpListPage` currently only has the **scoped** `CARD_TAG_CHIP_SELECTOR` (per-card). This case needs the **page-wide collection** form as well — copy `CredentialsListPage.entity_card_tag_chip` (`LocatorDescriptor(testid="entity-card-tag-chip")`) + a `get_visible_type_badges()` method (credentials has exactly this, `credentials_list_page.py:487`). |
| Zero-results empty state | `empty-state-title` | on-main ✓ | already `McpListPage.empty_state_title`; not reached by this case (Remote always matches here) |

**No new testids are required for this case** — every handle already exists on
`EliteaAI/EliteaUI` `main`.

**Known handle GAP (not required, do not add for this case):** the chip's
*selected* state has no `data-*` attribute — only the emotion class changes.
Per `.agents/testing.md` § Locator policy state belongs in a `data-*`
attribute (e.g. `data-selected` on `StyledChip` in `Categories.jsx`), but this
case does not need it: URL + `tags-panel-clear-all` cover "filter is applied"
without touching shared-component JSX. Recorded in `_surface.md`; raise it as
its own piece of work if a future case must assert *which* chip is lit while
several are selectable.

## Network Behavior

- List query: `GET /api/v2/elitea_core/tools/prompt_lib/{project}?query=&sort_by=created_at&sort_order=desc&mcp=true&limit=20&offset=0`
  — with the Remote filter active it gains **`&toolkit_type=mcp`** (server-side
  filtering, unlike the client-side search in ELITEA-1941).
- Types panel data: `GET /api/v2/elitea_core/toolkit_types/prompt_lib/{project}?mcp=true`
  → `{"rows": ["mcp"], "total": 1}` here. **The chip list does NOT come from
  it** (it is hardcoded Local+Remote), but the *Local* selection's type list
  does — see ELITEA-1943's AFS and bug #1737.
- Deselect / Clear all re-issues the plain unfiltered query.

## Automation Hints

- **The Types chips mount LATER than the page's own load signal.** Immediately
  after `McpListPage.navigate()` (which waits on the card-view toggle button)
  `tags-panel-chip-Remote` is still absent — observed live, a click at that
  moment fails with "does not match any elements". Wait for the chip itself
  (framework auto-wait / `wait_for(state="visible")`) before clicking; never a
  fixed sleep.
- Filtering is a **server round-trip**; wait for the network to settle after a
  chip click (the page object's existing `wait_for_network()` + short settle,
  same shape as `McpListPage.search()`), or await the `toolkit_type=mcp`
  response.
- Suggested `McpListPage` additions (all testid-only):
  `TYPE_FILTER_CHIP = '[data-testid="tags-panel-chip-{}"]'`,
  `tags_clear_all_button = LocatorDescriptor(testid="tags-panel-clear-all")`,
  `entity_card_tag_chip = LocatorDescriptor(testid="entity-card-tag-chip")`,
  plus `click_type_filter(type_label)`, `is_type_filter_active()`,
  `get_visible_type_badges()`, `clear_all_type_filters()`. Every one of these
  already exists in `automation/pages/credentials_list_page.py` (lines
  ~364-500) against the *same shared components* — port the shape rather than
  inventing a new one.
- The list is paginated (`limit=20`); with >20 MCPs a "load more" would be
  needed. Live count is 19 — if the project grows past 20 the baseline capture
  must page through, so keep the assertion on *what is rendered* symmetric
  between baseline and post-clear (both read the same way), which is what the
  steps above do.
- Test file: new `automation/tests/ui/toolkits/test_mcp_type_filter.py`
  (sibling of `test_mcp_search_by_name.py` / `test_mcp_view_toggle.py`),
  markers `p1`, `mcp`-area (`toolkits`), `regression`, `ui`.

## Known Defects Found

- **#1737 (filed this session, OPEN, `bug`)** — the **Local** chip applies
  visibly but does not filter: all Remote MCPs stay listed. It does **not**
  affect this case (Remote path is correct) but the implementer must not
  "fix" the Local absence assertion by clicking Local.
- Pre-existing, unrelated, not re-verified here: #1734 (search-clear
  redirect), #521 (view-toggle testids carry an `agent-` prefix on a shared
  component).

## Cleanup

None — read-only case, no data created.
