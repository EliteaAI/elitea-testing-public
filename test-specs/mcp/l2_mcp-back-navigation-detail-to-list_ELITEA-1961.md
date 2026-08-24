# Test Case: MCP — Back Navigation from Detail to List

## Metadata
- **TMS ID**: ELITEA-1961
- **Linked Story**: none
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `399`, 19 MCPs present)
- **User set**: `${TEST_USER}` (localhost: no login — `VITE_DEV_TOKEN` auto-auths the dev server)
- **Analyst**: qa-engineer (agent), session 2026-08-24, batch `mcp-w02` (solo dispatch)
- **Status**: ready-for-automation
- **Surface key**: `mcp-list-detail-navigation`
- **Filed during analysis**:
  - CLARIFICATION [#1731](https://github.com/EliteaAI/elitea-testing-public/issues/1731) — **there is no back button on the MCP detail page**; the arrow was replaced by a breadcrumb trail. The case's steps 3-4 are stale.
  - CLARIFICATION [#1732](https://github.com/EliteaAI/elitea-testing-public/issues/1732) — step 6's "same scroll position" half does not hold (the "filters still applied" half does).
- **Reverse-masking note**: both divergences are **case-text drift, not product defects** (`test-case-analysis` § Classify findings). This AFS asserts the LIVE contract.

## Preconditions
- User authenticated (localhost: automatic via `VITE_DEV_TOKEN`; deployed: Keycloak as `${TEST_USER}`).
- Project context set (`${ELITEA_PROJECT_ID}`, `399` during exploration).
- **At least 2 MCPs exist in the project** — the filter observable is "the filtered count is strictly smaller than the unfiltered count", which is vacuous with one MCP. Project 399 held 19 during exploration; the test additionally creates its own so the *filtered* side is deterministic regardless of project state.
- Card view is the MCP list's default; this case never touches the table view.

## Test Data

### generate-per-test (created in setup, deleted in teardown)
| Alias | Name | Url |
|---|---|---|
| MCP **A** | `autotest_mcp_backnav_{ts}` | `https://mcp.example.com/sse` |

- The whole point of a generated, unique name is that searching for it yields **exactly one** card — the filtered count is then a hard `1`, not "fewer than before".
- `https://mcp.example.com/sse` is correct here: the URL is only ever **stored**, never dialled (Load Tools is not part of this case) — `_surface.md` § Fixtures (addendum).
- Name length: `MAX_NAME_LENGTH = 32`, **silently truncated**. `autotest_mcp_backnav_` is 21 chars → a 10-digit unix `ts` gives 31. Read back the *stored* name after creation rather than assuming the literal survived, and search on that.
- Creation path: the merged UI create flow (`McpFormPage.navigate_to_create()` → `select_remote_mcp_type()` → `fill_name()` → `fill_url()` → `save_and_wait_for_created(project_id)`), proven in `test_mcp_delete_remote.py`.
- Teardown: `ToolkitAPI.delete_toolkit(A.id)`. Never `ToolkitAPI.list_toolkits()` — known-broken discovery path on this env.

### reuse-existing
- Whatever other MCPs the project holds — used only for the *unfiltered* baseline count, never asserted by name.

## Test Steps

> Steps are numbered to match the TMS case. Step 3/4 assert the live control (breadcrumb `MCPs` link) instead of the case's stale "back button", per #1731.

**Setup (not a case step)** — create MCP **A** through the UI create flow; capture its id (from the `POST` response) and its stored name.

> ⚠️ Register the console-error listener **AFTER** setup. The `/mcps/create` type-picker emits a React dev-mode console error on every mount (`Each child in a list should have a unique "key" prop`, tracked as [#656](https://github.com/EliteaAI/elitea-testing-public/issues/656)); a listener registered before setup fails on scaffolding rather than on the surface under test. Confirmed pattern from ELITEA-1946/1959.

| # | Action | Expected (VERIFIED live 2026-08-24) |
|---|---|---|
| 1 | `McpListPage.navigate()` → `/mcps/all`, wait for load | List renders. Capture `count_unfiltered = get_card_count()` (19 during exploration). `breadcrumbs` nav is **absent** on the list page (`to_have_count(0)`) — verified. |
| 1b | Apply a filter: `McpListPage.search(A.name)` | Exactly **1** card, and its name is `A.name`. `agent-search-input` holds `A.name`. **URL stays `/mcps/all` with no query string** — the filter is client-side redux state, not a URL param (verified). Also assert `count_unfiltered > 1` so the filter is provably a narrowing. |
| 2 | `McpListPage.open_card_by_name(A.name)` then `McpFormPage.wait_for_page_load()` | URL becomes `/mcps/all/{A.id}?viewMode=owner&name={A.name}`; `toolkit-detail-title` reads `A.name`. **The `wait_for_page_load()` is mandatory** — `open_card_by_name()` does not wait for the destination page (`_surface.md`). |
| 3 | Verify the detail page's top-left navigation control | `breadcrumbs` (`<nav>`) is visible; its text is `MCPs/{A.name}`. Exactly **one** `breadcrumb-item` (`<a>`, text `MCPs`). **`back-button` has count 0** — the case's arrow-icon back button does not exist on this route (#1731). This absence assertion is deliberate and first-class (`.agents/testing.md` § Locator policy, #511 extension) — it keeps the drift test-enforced instead of documentation-only. |
| 4 | Click the `MCPs` breadcrumb link | Client-side navigation fires; no full reload. |
| 5 | Verify the MCP list page is displayed | URL is back to `/mcps/all`; `agent-search-input` is present; `breadcrumbs` is **absent** again (`to_have_count(0)`). |
| 6 | Verify the list's **filter** state survived | `agent-search-input` still holds `A.name`; still exactly **1** card, still named `A.name`. Verified twice live with two different search terms (`autotest_inv` → 4/19 preserved; `autotest_conn` → 1/19 preserved). |
| 6b | Side channel | Zero console **errors** across steps 1-6 (0 observed live). |

**Teardown** — `ToolkitAPI.delete_toolkit(A.id)`.

## Expected Results
- The MCP detail page offers a working navigation-to-list control at top-left — today a breadcrumb `MCPs` link, not a back arrow.
- Using it returns to `/mcps/all`.
- The list's **search filter is preserved** across the round trip.
- No console errors.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result (per case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Objective: "back button … returns the user to the MCP list page" | returns to list | steps 3-5 (breadcrumb link is today's control) | URL == `/mcps/all` + search box present | **covered (via successor control)** — #1731 |
| Objective: "preserving the list state such as scroll position and applied filters" | both preserved | filters: step 6; scroll: NOT asserted | filter value + filtered card count | **partial** — filters covered, scroll ⇒ `clarification` #1732 |
| Precondition: user logged in | — | `auth_state` fixture | — | covered |
| Precondition: MCP list has ≥1 MCP | — | Setup creates MCP A; step 1 asserts `count_unfiltered > 1` | — | covered |
| Step 1 — Navigate to MCP list page | list loads | step 1 | `get_card_count()` > 1 | covered |
| Step 2 — Click any MCP card to open detail | detail loads | step 2 | URL + `toolkit-detail-title` == A.name | covered |
| Step 3 — Back button (arrow icon, top-left) is visible | back button visible | step 3 | `breadcrumbs` visible + `breadcrumb-item` == "MCPs" + **`back-button` count 0** | **clarification** #1731 — asserted against the live control; the case's own wording is stale |
| Step 4 — Click back button | navigation triggered | step 4 | click on `breadcrumb-item` | **clarification** #1731 |
| Step 5 — Returns to MCP list page | list displayed | step 5 | URL == `/mcps/all`, `breadcrumbs` count 0 | covered |
| Step 6 — List state preserved (scroll position) | same scroll position | — | — | **clarification** #1732 — NOT preserved live (`scrollTop` 99 → 0). Deliberately not asserted in either direction (see § Known Defects Found) |
| Step 6 — List state preserved (filters still applied) | filters still applied | step 6 | search-input value + card count + card name | covered — verified twice |
| Expected Final State | back on list, same scroll + filters | steps 5-6 | as above | partial, per the two rows above |

### Axis 2 — Beyond the case (each with its grounded reason)

| Extra observable | Grounded reason |
|---|---|
| `back-button` count == 0 on the detail page | Makes #1731's finding **test-enforced**. If the UI team restores the arrow, this test goes red and the case text gets revisited — a documentation-only note would silently rot. |
| `breadcrumbs` count == 0 on the LIST page (steps 1 and 5) | The nav is the cleanest detail-vs-list discriminator and it is what makes the `breadcrumb-item` locator unambiguous; asserting its absence on the list proves step 5's navigation actually left the detail route rather than just changing the URL. |
| URL carries **no** query string while the list is filtered | Records the mechanism (redux, not URL) that makes step 6 pass — if a future change moves the filter into the URL, the preservation would then be for a different reason and this assertion flags the shift. |
| The filtered card's **name** (not just the count) | A count of 1 is satisfiable by the wrong card; the name makes the filter assertion exact. |
| Zero console errors | Standard side-channel check; 0 observed live across the whole flow. |

## Concrete Handles

All handles below are **on `origin/main` ✓** (verified 2026-08-24 with a fresh `git fetch origin` in `../EliteaUI`) — this case needs **no new testid** and is deployed-env promotable on the testid axis.

| Element | Testid (primary, testid-only per `.agents/testing.md`) | Provenance | Notes |
|---|---|---|---|
| MCP list search input | `agent-search-input` | on-main ✓ | shared `SearchBar`; already `McpListPage.search_input` |
| Search clear (X) | `search-clear-button` | on-main ✓ | already `McpListPage.search_clear_button`; only needed if the test clears |
| MCP card name | `entity-card-name` | on-main ✓ | already `McpListPage.mcp_card_name`; N per list |
| Breadcrumb nav (detail only) | `breadcrumbs` | on-main ✓ | `<nav>`, text `MCPs/{name}`. **NEW to the suite** — no page object binds it yet |
| Parent crumb link | `breadcrumb-item` | on-main ✓ | `<a>` text `MCPs`; exactly 1 on the MCP detail page. **NEW to the suite** |
| Current crumb (entity name) | `toolkit-detail-title` | on-main ✓ | already `McpFormPage.detail_title`; note it now lives INSIDE the breadcrumb trail |
| Back arrow (absence assertion) | `back-button` | on-main ✓ (`src/components/BackButton.jsx:120`) | rendered for other surfaces (`AgentDetailPage`, `SkillDetailPage`) — **never on `/mcps/all/:id`** |

### Page-object work

- **`McpFormPage`** — add two class-level `LocatorDescriptor` fields (`breadcrumbs_nav`, `breadcrumb_parent_link`) plus `click_breadcrumb_parent()` and `get_breadcrumb_text()`.
- Also add `back_button = LocatorDescriptor(testid="back-button")` on `McpFormPage` for the absence assertion. Note `AgentDetailPage:625` and `SkillDetailPage:41` already declare the same testid on their own classes — that is the established shape for this shared app-shell control, so a third declaration is consistent, not a duplication violation.
- **Recommended, declared:** keep all four on `McpFormPage` rather than promoting to `BasePage`. The breadcrumb trail IS app-shell and a future cross-surface case may want it on `BasePage` — but promoting now would bind a testid no other current spec touches. If the implementer prefers `BasePage`, that is a reasonable alternative; declare whichever is chosen in the Run Report.
- `McpListPage` needs **nothing new** — `search()`, `clear_search()`, `get_card_count()`, `get_card_names()`, `open_card_by_name()` all exist and were exercised live.

## Automation Hints

- **`McpListPage.search()` requires ≥3 characters and commits on Enter** — typing alone does not filter (`SearchBar.jsx`: `onChange` updates local input state only). The existing method already presses Enter and waits.
- **The filter lives in redux (`src/slices/search.js`), in-memory.** It survives a client-side route change (which is exactly why step 6 passes) but would NOT survive `page.reload()`. Never reload between steps 2 and 6, and never assert the filter from the URL.
- **`open_card_by_name()` does not wait for the detail page** — always follow with `McpFormPage.wait_for_page_load()` (`_surface.md`). Prefer retrying `expect(...)` assertions over bare `text_content()` reads on the detail header, which lags.
- **Assert `breadcrumb-item` by count-then-text, not `.first`.** There is exactly one on this page today; a `to_have_count(1)` assertion makes that an enforced invariant instead of a silent assumption.
- **Do not use the browser's native back** (`page.go_back()`) — the case is about an in-page control, and `BackButton`/breadcrumb navigation uses `replace: true` semantics elsewhere in this app, so history-based navigation is a different flow with a different contract.
- Console-listener registration goes **after** setup (#656, see step-table note).
- Whole flow runs in a few seconds — no long waits; nothing here touches the network beyond the setup POST and the list/detail GETs.

## Fidelity Declaration

**No substitutions of any kind.** Every observable is produced by the system:
- The filter is applied through the product's own search control (real typing + Enter).
- Navigation to the detail page is a real card click; the return is a real click on the product's breadcrumb link.
- No `page.route`, no `route.fulfill`, no `page.evaluate`-injected state, no API-seeded precondition standing in for a UI step.

*Analyst-side note on exploration technique:* during live exploration the analyst set `scrollTop` via `page.evaluate` to reach a scrolled state quickly. That was **exploration only** and produced no assertion in this AFS — the scroll observable is not asserted at all (§ Known Defects Found). If a future case does assert scroll, it must scroll via a real gesture (`page.mouse.wheel`), not by assignment.

## Blocked Steps

None. Every case step was executed live.

## Known Defects Found

Neither finding is a product defect — both are case-text drift, filed as clarifications per the reverse-masking guard.

### CLARIFICATION [#1731](https://github.com/EliteaAI/elitea-testing-public/issues/1731) — no back button on the MCP detail page

`src/pages/Toolkits/EditToolkit.jsx:390-403` renders `hasBreadcrumbTrail ? <Breadcrumbs/> : (<><BackButton/><Typography data-testid="toolkit-detail-title"/></>)`. `useHasBreadcrumbTrail()` is **purely route-based** (`resolveBreadcrumbTrail(pathname).length > 0`, `useBreadcrumbTrail.hooks.js:35`) and `/mcps/all/:id` declares a trail (`breadcrumb.constants.js:48`) — so the `<BackButton/>` branch is **unreachable on this route no matter how the user arrived**. Verified live from both a card click and a deep link. Breadcrumbs landed with the settings/redesign work (`breadcrumb.constants.js` last touched on `main` by `1facc163`, 2026-08-21).

**Automation consequence:** steps 3-4 are automated against the breadcrumb link, plus a `back-button → to_have_count(0)` absence assertion. Not blocking, no soft-assert, no RED.

### CLARIFICATION [#1732](https://github.com/EliteaAI/elitea-testing-public/issues/1732) — list scroll position not restored (filters are)

Measured live: list scroller `#EliteACustomTabPanel` (`scrollHeight` 900 / `clientHeight` 801 at 1920×1080 with 19 MCPs), scrolled to `scrollTop: 99` → opened a card → returned → `scrollTop: 0`, still `0` after a 2 s settle. No list scroll-restoration code exists anywhere in `src/`, so this reads as never-implemented rather than regressed.

**Why this AFS does not assert it in either direction:**
1. Asserting *preservation* would reverse-mask — a permanent RED for behaviour the product never implemented, with no ticket a fix could ever close.
2. Asserting *reset-to-0* would cement a possibly-unintended behaviour as the contract, and would go red the day someone implements scroll restoration correctly.
3. Mechanically, the scroller carries an `id`, not a `data-testid`. Asserting it needs a new testid on an element **no case actually touches** — the blanket-add ban (`.agents/testing.md` § Locator policy scope rule) says don't.

A human rules on #1732; if scroll restoration is deemed in-scope, that is UI-team work and a follow-up case, not a change to this test.

## Evidence

Live exploration, 2026-08-24, `http://localhost:5173`, project 399, MCP ids 1745 / 3134. All observations came from scripted DOM probes (`browser_evaluate`) rather than screenshots — the observables here are DOM/URL/state values, not visual judgment.

| Observation | Value |
|---|---|
| Unfiltered list | 19 cards, `breadcrumbs` absent, search value `""` |
| After `autotest_inv` + Enter | 4 cards, search `autotest_inv`, URL still `/mcps/all` (no query) |
| Detail page (id 1745) | `back-button` **null**, `breadcrumbs` text `MCPs/autotest_inv_url_spot1`, 1 × `breadcrumb-item` = `MCPs`, `toolkit-detail-title` = `autotest_inv_url_spot1` |
| After breadcrumb click | URL `/mcps/all`, **4 cards**, search **`autotest_inv`** ✅ |
| Scroll probe (unfiltered) | `scrollTop` 99 → open card → back → `scrollTop` **0** (still 0 at +2 s) ❌ |
| Repeat with `autotest_conn` | 1 card → detail (id 3134) → back → **1 card**, search **`autotest_conn`** ✅ |
| Console errors | **0** across the whole flow |
