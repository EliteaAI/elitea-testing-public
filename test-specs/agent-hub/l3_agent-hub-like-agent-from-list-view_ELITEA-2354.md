# Test Case: Agent Hub — like an agent from the list view

## Metadata
- **TMS ID**: ELITEA-2354
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium — same mapping as sibling ELITEA-2352)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), ELITEA-2354, 2026-08-05
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP against a real agent card. All 6 steps reproduced (like, icon-fill, count-increment, refresh-persistence all confirmed). One MINOR product defect found and filed (console error on every like/unlike click — does not block the observable behaviour). Two testids needed (like button + its `data-liked` state attribute) on a **shared** component (`Like.jsx`) — implementer work via `add-data-testid`, prop-threaded per the shared-component discipline.
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075/2350/2352) already covers navigation, page heading, and agent-card lookup (`get_agent_card(name)`, `AGENT_CARD_PREFIX`). **Not a target for `extend-existing`/`already-covered`**: no merged spec on this page clicks the like button, asserts like state, or asserts count persistence — this case's entire observable (the like interaction itself) is untouched by any existing spec. Fresh coverage.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- Agent Hub (Catalog) page freshly navigated to.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- **No specific agent name is a reliable fixture for "0 likes"** (see § Known Defects / case-text note below) — the implementer's test must **dynamically discover** any currently-rendered agent card whose like-count reads `0` at runtime, rather than hardcoding the case text's example ("AI Platform Design Advisor" currently shows **1** like in this environment, not 0 — live like counts are mutable shared product data, not a stable fixture). Confirmed live in this session: "Elitea Feature Story Generator" and "User Story Creator" both read `0` at time of exploration (Business Analyst category, `${TEST_USER}` / Private project).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.wait_for_page_load()`).
2. Locate an agent card currently showing `0` likes.
   - **Verify**: found dynamically (see § Test Data) — do not hardcode a specific agent name/id, since the case text's own example agent does not reliably show 0 likes in this environment.
3. Click the heart icon (the like button) on that agent card.
   - **Verify**: click succeeds; `POST /api/v2/social/like/prompt_lib/{project_id}/application/{id}` fires and returns `201 Created` (confirmed live: `POST .../social/like/prompt_lib/1/application/172 => 201`).
   - **KNOWN DEFECT (filed, non-blocking — see § Known Defects)**: one console `[ERROR]` fires on every click (`agentHub/updateApplicationInCategories` non-serializable-payload warning). Does not affect the observable UI/API behaviour — assert via `expect.soft()` per the no-masking decision tree, `# Known defect: #1215`, NOT a hard console-error-count-zero assertion for this specific interaction (all other console-cleanliness assertions in this suite remain unaffected).
4. Verify the heart icon changes to a filled/active state.
   - **Verify**: **testid needed** — see § Concrete Handles. Confirmed live via screenshot diff: unliked = outline heart (`HeartIcon`), liked = filled heart (`HeartActiveIcon`) — visually distinct, but the DOM has no accessible/stable signal of which is rendered (see § Concrete Handles for the `data-liked` attribute this case needs implemented).
5. Verify the like count increments by 1.
   - **Verify**: like-button testid's text content reads `1` (was `0` before step 3). Confirmed live: count read `0` → `1` immediately after the `201` response (optimistic-update pattern via `handleLikeSuccess`, not waiting on a re-fetch).
6. Refresh the page and verify the updated like count persists.
   - **Verify**: full page reload (`page.reload()` / re-navigate), then locate the SAME agent (by name, via the Catalog search box — `catalog-search-input` — since the unfiltered default view only renders the top-6 "Trending" cards by like-count descending, and a freshly-liked low-count agent will not necessarily be among them; confirmed live: the agent used in this session, "User Story Creator", was NOT in the default post-refresh view and had to be located via search) and confirm its like-button testid still reads `1` and the heart icon is still filled (screenshot-confirmed live).

## Expected Results
- Clicking an unliked agent card's heart icon likes it: count `0`→`1`, icon switches to filled/active, `POST .../social/like/...` returns `201`.
- The updated like count and liked state persist across a full page refresh.
- (Known, filed, non-blocking) one console error fires per like/unlike click — see § Known Defects.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Locate an agent card showing 0 likes (e.g., "AI Platform Design Advisor") | Action completes without error and produces the expected UI state | step 2 | dynamic discovery of a live 0-like card (see § Test Data note — case's named example is not a reliable fixture) | asserted *(with a data-selection adaptation, not a drift/defect — case text says "e.g.")* |
| 3 Click the heart icon on the agent card | Control responds; expected next state is shown | step 3 | click succeeds, `POST .../social/like/...` returns `201` | asserted — plus a known, filed, non-blocking console-error finding (§ Known Defects) |
| 4 Verify the heart icon changes to a filled/active state | Condition holds as described | step 4 | `data-liked="true"` on the like-button testid (new state attribute, testid needed) | asserted (pending testid implementation) |
| 5 Verify the like count increments by 1 | Condition holds as described | step 5 | like-button testid text content `0`→`1` | asserted (pending testid implementation) |
| 6 Refresh the page and verify the updated like count persists | Action completes without error and produces the expected UI state | step 6 | like-button testid text content still `1` + `data-liked="true"` after full reload, agent re-located via search | asserted (pending testid implementation) |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 3` asserts the underlying `POST .../social/like/...` network call and its `201` status — *added: proves the like reached the backend, not merely that the UI count changed (a pure client-state bug would otherwise pass this case).*
- `step 6` asserts re-locating the agent via search rather than assuming it's still in the default unfiltered view — *added: confirmed live that the default post-refresh view only shows the top-6 "Trending" cards (sorted by likes desc), so a freshly-liked low-count agent is not guaranteed to render there; asserting via the default view alone would be a false-negative risk depending on which agent was chosen in step 2.*
- Console-error check on the like click — *added: standard side-channel regression guard per this skill's own discipline; surfaced the filed defect (§ Known Defects).*

## Cleanup

**Required — this case mutates shared, cross-session product data (the agent's public like count/state), which sibling cases in this family depend on as a baseline (e.g. ELITEA-2355 "unlike", ELITEA-2364 "My Liked filter", ELITEA-2365 "reload button").** After step 6's assertions, the test MUST click the same like button again (unlike) and verify the count returns to its original value (`0`) before the test ends — confirmed live in this session (`DELETE .../social/like/prompt_lib/1/application/172 => 204`, count `1`→`0`). Without this cleanup, repeated CI runs would permanently accumulate likes on whichever agent the dynamic-discovery step (2) happened to pick, and could pollute the fixed agent list other Agent Hub cases enumerate by name.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Catalog search input | `AgentHubPage.search_input` (`catalog-search-input`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Agent card (by name) | `AgentHubPage.get_agent_card(name)` (`AGENT_CARD_PREFIX`, `catalog-agent-card-{id}`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| **Like button (heart icon + count) on an agent card** | **testid needed**: `catalog-agent-like-button-{application.id}` — dynamic, same `{section}-{element}-{param}` convention as `catalog-agent-card-{id}` | none | needs-adding. Root component is `src/components/Like.jsx` (**shared** — also consumed by `src/[fsd]/widgets/data-table/ui/DataTableCell.jsx`, `DataTableRow.jsx`, `src/components/Card.jsx`), so per `.agents/testing.md`'s shared-component rule this must be a caller-supplied `testId` prop, NOT hardcoded inside `Like.jsx`. Threading: `AgentCard.jsx` (call site, `src/[fsd]/features/agent-hub/ui/AgentCard.jsx`) → `testId={`catalog-agent-like-button-${application.id}`}` → `AgentHubLike.jsx` → `<Like testId={testId} .../>` → `Like.jsx` applies `data-testid={testId}` on the `IconButton` root. Confirmed via source: zero `data-testid`/`testId` anywhere in `Like.jsx`, `AgentHubLike.jsx`, or `AgentCard.jsx`'s `<AgentHubLike>` usage (`git grep -c "data-testid\|testId"` = 0 on `Like.jsx` against both `origin/main` and `origin/automation/testids`). |
| **Like button "liked" state** | **testid needed** (paired with the above): `data-liked="true"/"false"` attribute on the SAME `IconButton` root, driven by the existing `is_liked` prop already used to choose `HeartActiveIcon` vs `HeartIcon` (`Like.jsx:67`) — combined locator `[data-testid="catalog-agent-like-button-{id}"][data-liked="true"]`. Per `.agents/testing.md` § Locator policy ("Testid = stable identity; state via `data-*` attributes") — same precedent as ELITEA-2352's `CategoryRail.jsx` chip `data-selected` attribute. **Do not** give the liked/unliked icon two different testids (would violate the same-element-conditional-pair discipline for no benefit — a `data-*` attribute is the correct shape here, not a #277-style named-pair, since this is a single stable button whose icon child swaps, not two independently-referenced JSX branches). | none | needs-adding (same component/commit as above) |
| Like count (numeric text) | Read via the same like-button testid's `text_content()` (the count `Typography` is the only text node inside the `IconButton`, alongside the icon `<svg>` which has no text) — no separate testid needed. | none | needs-adding (same component/commit as above) |

## Network Behavior
- `POST /api/v2/social/like/prompt_lib/{project_id}/application/{application_id}` → `201 Created` on like. Confirmed live: `POST .../social/like/prompt_lib/1/application/172 => 201`.
- `DELETE /api/v2/social/like/prompt_lib/{project_id}/application/{application_id}` → `204 No Content` on unlike (used by this case's required cleanup). Confirmed live: `DELETE .../social/like/prompt_lib/1/application/172 => 204`.
- Update is optimistic client-side (`handleLikeSuccess` in `AgentHubLike.jsx` updates Redux state directly from the mutation's success callback) — no re-fetch of the list is awaited before the UI reflects the new count.
- No 4xx/5xx observed during either the like or unlike interaction.

## Known Defects Found During Exploration
- **[MINOR, filed]** [EliteaAI/elitea-testing-public#1215](https://github.com/EliteaAI/elitea-testing-public/issues/1215) — clicking the like/unlike heart icon on an Agent Hub agent card dispatches a Redux action (`agentHub/updateApplicationInCategories`) whose payload contains a raw function (`updateFn`), which fires a `console.error` ("non-serializable value detected") from Redux Toolkit's dev-only serializability-check middleware, on every single like AND unlike click (confirmed both directions live, same session). Root cause confirmed via source: `src/[fsd]/features/agent-hub/lib/hooks/useAgentHubData.hooks.js:330` dispatches the closure directly; `src/slices/agentHub.js:42-49`'s reducer then invokes it. **Functionally harmless** — the like/unlike flow itself (count, icon, persistence, backend call) is entirely correct; this is dev-console-only noise (the middleware doesn't run in production builds) but pollutes local/dev test runs and is exactly the kind of side-channel signal the analysis console-check step exists to catch. Automation should assert this as a KNOWN defect (`expect.soft()` + `# Known defect: #1215`) on the like AND unlike clicks specifically, not treat it as a general console-cleanliness regression for the rest of the test.
- **Not a defect — case-text note**: the case's example agent ("AI Platform Design Advisor") does not reliably show 0 likes (it showed 1 in this session) — live like counts are mutable, shared, cross-session product data, and the case text itself uses "e.g." (an example), so this is a data-selection adaptation for automation (dynamic discovery — see § Test Data), not a filed clarification.

## Blocked Steps
None — all 6 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- Extend `AgentHubPage` (`automation/pages/agent_hub_page.py`) with:
  - `LIKE_BUTTON = '[data-testid="catalog-agent-like-button-{}"]'` (class-level template constant, same idiom as `CATEGORY_FILTER_CHIP`/`CATEGORY_HEADING`).
  - `get_like_count(application_id)` — reads the like-button's text content as an int.
  - `is_agent_liked(application_id)` — checks `[data-liked="true"]` on the like-button locator (same idiom as `is_category_filter_chip_selected()`).
  - `click_like_button(application_id, timeout)` — clicks the like-button locator; the caller resolves `application_id` from the agent card's dynamic testid suffix (`catalog-agent-card-{id}` — the id is already embedded there, extractable via the card's `data-testid` attribute or by cross-referencing the `GET public_applications/prompt_lib/` list response captured during step 1/2).
  - A method to find ANY card with 0 likes, e.g. `find_agent_with_zero_likes()` iterating `AGENT_CARD_PREFIX` cards and checking each one's like-button text — needed for step 2's dynamic-discovery requirement (§ Test Data).
- Selector policy: testid-only + `data-*` state attribute, no fallback (`.agents/testing.md` § Locator policy). The `data-liked` addition follows the exact same precedent as ELITEA-2352's `data-selected` chip attribute.
- Cleanup is MANDATORY (see § Cleanup) — the test must unlike the agent it liked before ending, verified via the same `is_agent_liked()`/`get_like_count()` helpers returning to the pre-test baseline.
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.agents` (matches ELITEA-2350/2352's marker set for this same page).

---

## Repair — #2166 (networkidle / #1847), 2026-09-10

**Analyst**: qa-engineer (analyst slot) · **Verdict**: `ready-for-repair`
**Triage class**: **D — test-synchronisation defect** (`adjust-automated-test` § Step 2).
**NOT** class A (no UI drift), **NOT** class B/C (no product bug), **NOT** class F
(every testid the spec uses is on `origin/main` — table below).

### What CI actually ran (verify before you read the traceback)

The failure is on **`origin/main`'s** `AgentHubPage.search()`, not on HEAD's:

```
origin/main:automation/pages/agent_hub_page.py
  777:    def search(self, query: str, timeout: int = 15000):        # no response_timeout
  789:        with self.page.expect_response(..., timeout=timeout)    # 10s, shared budget
  795:        self.wait_for_network(timeout=timeout)   <-- the failing line, matches the traceback
```
`_expect_applications_response` (FIX #2078) does not exist on `main` (`grep -c` → 0; HEAD → 5),
so **the "Timeout 15000ms exceeded while waiting for event `response`" side-note in the captured
log is already fixed on `automation/base`** and is not part of this repair. The trailing
`wait_for_network()` **survives on HEAD at line 1117** — the defect is live and will re-red in CI
on the next promotion.

Blast radius of run #116: 7 of 10 jobs failed, but the intake card lists **exactly one** failing
test in the `agent_hub` job — so this is spec-specific, not the run-#114 gateway-outage class.

### Root cause — confirmed live, and the hypothesis is only PARTLY confirmed

`search()` awaits the debounced `GET /public_applications/prompt_lib/?query=…` correctly, then
runs a **trailing, redundant `self.wait_for_network(timeout=timeout)`** =
`wait_for_load_state("networkidle")`. That wait is **both unreliable and useless**, and the live
DEV probe (2026-09-10, `https://dev.elitea.ai/app/elitea-catalog`, `${TEST_USER}`) shows why:

```
socketio_requests_in_6s_idle_window : 0          <-- upgrades to a real WebSocket on DEV
socketio_total_since_nav            : 8          (handshake only)
networkidle_on_idle_page            : ok, 0.00s
trailing_networkidle_after_search   : ok, 0.00s  <-- the settle does NOTHING
zero_result_trailing_networkidle    : ok, 0.00s

search_response_url    : .../public_applications/prompt_lib/?query=Business+Analyst&statuses=published&agents_type=classic&limit=100&offset=0
search_response_status : 200
public_app_gets_during_search : 1                <-- exactly ONE GET; the predicate is correct

# SEARCH #2 (cold, after reload) — THE RACE, reproduced:
s2_oneshot_union_right_after_response      : false   <-- grid is EMPTY when search() returns
s2_oneshot_named_card_right_after_response : false
s2_response_to_union_visible_s             : 0.802   <-- 800ms of uncovered render window
s2_named_card_visible_after_union_settle   : true
```

- **The #1847 *class* is confirmed** — `networkidle` is not a valid settle signal for this app and
  Playwright marks it DISCOURAGED. **The specific socket.io-polling *mechanism* is NOT confirmed
  on DEV**: same-origin on `dev.elitea.ai` the transport upgrades to a WebSocket, so `networkidle`
  resolves in 0.00 s from this machine and the CI signature does **not** reproduce locally-against-DEV
  (3/3 green, below). The documented `?EIO=4&transport=polling` capture in `.agents/testing.md` is a
  **localhost**-topology observation. Stated plainly rather than claimed: the most likely CI mechanism
  is that a GHA-side proxy declines the WebSocket upgrade (leaving socket.io on a continuous long-poll)
  and/or run #116's degraded DEV left requests in flight — but **the CI 3/3 evidence stands on its own
  and the repair does not depend on which**: a wait that resolves in 0.00 s here provides no value and
  only risk.
- **The second, latent defect this probe found is the one that actually matters.**
  `useAgentHubData.hooks.js:190-215` (`searchAndCategorize`) calls `resetSearchByTag()` →
  `clearCache()` **before** `await fetchApplications(...)`, then dispatches `setApplicationsData`
  in the response's `.then()` continuation. Playwright's `expect_response` resolves at the **HTTP
  response**, i.e. *before* that dispatch and before React commits — so when `search()` returns the
  grid is **empty** (measured: 802 ms). The caller's one-shot `.is_visible()` on the next line was
  never protected by anything: `wait_for_network()` returned in 0.00 s. So line 1117 is
  simultaneously **fragile** (can time out → the CI red) and **insufficient** (does not settle the
  render → a latent false red at every caller).

### The repair — exact spec for the implementer

**File**: `automation/pages/agent_hub_page.py` · **Method**: `search()` (line ~1117).
Only *how it reaches* changes; **no assertion in any spec is touched**
(`adjust-automated-test` § Step 3 rail). Expected-result changes: **none**.

**1. Add a class-level constant** (next to `AGENT_CARD_PREFIX`, line ~142):

```python
#: The two mutually-exclusive TERMINAL renders of the Catalog content grid.
#: `CatalogBody.jsx` renders exactly one of three things in its left column:
#: anonymous loading skeletons (NO testid), the category sections (agent
#: cards), or `NoResultsMessage` — so a union of the two testid'd branches is
#: satisfied only once the grid has COMMITTED for the current query, and can
#: never be satisfied by the loading state.
SEARCH_RESULTS_SETTLED = (
    '[data-testid^="catalog-agent-card-"], [data-testid="catalog-no-results-title"]'
)
```

**2. Replace the trailing settle** — delete `self.wait_for_network(timeout=timeout)` and use:

```python
self.page.locator(self.SEARCH_RESULTS_SETTLED).first.wait_for(state="visible", timeout=timeout)
```

**3. Docstring**: replace the `timeout` arg's "and the trailing settle" wording with
"…and the post-response render settle (`SEARCH_RESULTS_SETTLED`)", and record the
`networkidle`/#1847 removal + the `clearCache()`-then-commit mechanism above.

Locator policy: the added line references an UPPER_CASE class constant whose class-level
definition is a `[data-testid=` string — compliant one-hop form (`.agents/testing.md`
§ Locator policy). **No new testid is needed.** Fidelity: a *timing* wait on a
product-rendered element; nothing is substituted, no observable is weakened.
**No timeout is raised** anywhere (the ledger forbids it, and 10 s already covers the
measured 0.802 s by >12x).

### Per-caller sufficiency analysis (`grep -rn '\.search(' tests pages`)

`AgentHubPage.search()` has exactly **4** call sites (other `.search(` hits are `re.search`
or other page objects' own `search`):

| # | Caller | Next statement | Sufficient? |
|---|---|---|---|
| 1 | `tests/ui/agent_hub/test_agent_hub_like_agent_list_view.py:198` (ELITEA-2354, this card) | `assert get_agent_card(name).first.is_visible()` — **one-shot** | ✅ **Yes, and this is the caller the repair rescues.** Today the 802 ms window is unprotected; the union settle closes it. Search runs on a freshly `page.reload()`-ed page, so no stale card can satisfy the union. |
| 2 | `tests/ui/agent_hub/test_agent_hub_unlike_agent_list_view.py:236` (ELITEA-2355) | `assert get_agent_card(name).first.is_visible()` — **one-shot**, then two retrying `wait_for_*` | ✅ Yes — identical shape, also post-`reload()`. Same rescue. |
| 3 | `tests/ui/agent_hub/test_agent_hub_search_bar_filters_in_real_time.py:87` (ELITEA-2363) | `assert search_input.input_value() == SEARCH_TERM` (the input, not the grid); the grid assertion at :131 is 2 steps later | ✅ Yes — never depended on the settle; the union only makes its later grid reads deterministic. |
| 4-5 | `tests/ui/skills/test_agent_with_skills_publishing_flow.py:293, :326` | `:293` → `get_agent_card(...).first.is_visible(timeout=…)`; `:326` → `open_agent_by_name(...)` | ✅ Yes. ⚠️ Note for the implementer: `Locator.is_visible(timeout=)` is **deprecated and ignored** by Playwright — `:293` is a one-shot despite the argument, so it depends on the settle exactly like #1 and #2. Both call sites `navigate()` first, so no stale grid. |

**Residual window, declared:** if `clearCache()`'s render had not yet committed when the response
lands, a **stale** card could satisfy the union. Not reachable by any current caller — all four
search a freshly navigated/reloaded grid — and probe search #2 shows the empty-grid render *had*
committed (union false at the response). Recorded so a future caller that searches a
populated grid knows to add its own query-specific assertion rather than trusting the settle alone.

**Recommended (optional, same PR) hardening at the callers**: convert the one-shot
`assert …is_visible()` at #1 :199, #2 :237 and #4 :294 to the retrying
`expect(...).to_be_visible()`. This preserves exactly what is verified (the card is visible) and
only changes how it waits — the "free to change" side of the rail. The lead may take it or leave it;
the `search()` fix alone is sufficient for the measured race.

### Same-path `wait_for_network()` sweep (scoped to THIS test's executed path)

| Site | On this path? | Verdict |
|---|---|---|
| `AgentHubPage.search()` :1117 | ✅ yes (Step 6) | **THE defect — repaired above.** |
| `BasePage.navigate()` :360 (`networkidle`, 30 s) | ✅ yes (Step 1, via `navigate_and_capture_applications`) | **Leave it.** Already wrapped in `try/except` with an explicit "pages with persistent WebSocket connections never reach networkidle — continuing" comment (:361-365). It cannot fail the test; worst case it costs 30 s. Broader cleanup is #1847's own scope, not this card's. |
| `AgentHubPage.clear_search()` :1175 | ❌ no (ELITEA-2363's path only) | **Byte-identical unguarded shape.** Its own caller already settles properly (`wait_for_agent_card_count()`), so it is fragile-not-insufficient. **Recommended** to fix in the same PR (same one-line union settle, same file); flagged rather than mandated because it is off this card's path. |

No repo-wide sweep of the other ~140 `wait_for_network` call sites is proposed — that is #1847.

### Testid provenance (fresh `git fetch origin` in `../EliteaUI`, 2026-09-10)

```
catalog-agent-card               main:YES  testids:YES
catalog-no-results-title         main:YES  testids:YES
catalog-search-input             main:YES  testids:YES
catalog-agent-like-button        main:YES  testids:YES
```
All `on-main ✓`. **Nothing to add, nothing to promote** — class F ruled out.
*(This supersedes `test-specs/agent-hub/_surface.md`'s stale "No results empty state — NO testids"
entry: `catalog-no-results-title` / `-description` were added since and are on `main`.)*

### Case observable re-verified on DEV — unchanged

3 clean invocations of the unmodified spec against `https://dev.elitea.ai`
(`APP_PREFIX=/app`, symlink-safe env swap + restore trap):

```
DEV RUN 1: 1 passed in 27.82s   reruns.json {}   allure: passed
DEV RUN 2: 1 passed in 26.32s   reruns.json {}   allure: passed
DEV RUN 3: 1 passed in 25.54s   reruns.json {}   allure: passed
```
Like → `POST …/social/like/…` **201**, `data-liked="true"`, count 0→1, **both persist across
`page.reload()` + re-search**, cleanup unlike → 204 → count back to 0. The case's expected
results are exactly as originally specced. **The networkidle signature did not reproduce
from this machine against DEV** (consistent with the 0.00 s measurement above) — reported as
`not-reproducible locally`; the CI 3/3 evidence is the deterministic record.

### #1215 is ENVIRONMENT-SCOPED — the gate expectation differs per environment

Same spec, same session, same day:

| Environment | Result |
|---|---|
| `https://dev.elitea.ai` (production build) | **GREEN 3/3**, `reruns.json == {}` |
| `http://localhost:5173` (vite dev server) | **RED** — `Known defect …#1215: non-serializable Redux console error(s) on like click: 1 occurrence(s)`, all functional assertions passed |

**Root cause of the asymmetry, verified in source, not inferred:** the message
("A non-serializable value was detected in an action, in the path: `payload.updateFn`") comes
from `createSerializableStateInvariantMiddleware`, and `@reduxjs/toolkit@^2.6.1`'s
`buildGetDefaultMiddleware` adds it **only** inside
`if (process.env.NODE_ENV !== "production")` (`redux-toolkit.legacy-esm.js:467-480`).
EliteaUI ships `"build": "vite build"` → `mode=production` → **the middleware is not in the store
at all on any deployed env**, so #1215 physically cannot fire there.

This is the exact **ELITEA-1892 / #2082** precedent (`.agents/testing.md` § Merge gate,
"A sanctioned-RED signature can be ENVIRONMENT-SCOPED"). #1215 is **not fixed** and stays
**OPEN** on its own localhost evidence; nothing is weakened, because the spec's #1215 handling is
an absence-tolerant *recorder* (zero matching messages append nothing to `soft_failures`), while
every functional assertion runs identically on both environments. The unexpected-console-error
hard assert is untouched, so a genuinely new error still fails on either environment.

> ⚠️ **This corrects the spec's own module docstring and this AFS's original § Known Defects
> line**, both of which imply an unconditional sanctioned-RED. **The docstring should say
> "sanctioned-RED on localhost (vite dev build); GREEN on any deployed env".** One link is
> INFERRED, not verified, exactly as in #2082: that the DEV deployment serves the released
> production artifact rather than a dev-mode container — the 3/3 green is consistent with it.

### Expected gate outcome after the repair

| Gate environment | Expected |
|---|---|
| **`https://dev.elitea.ai`** (what #2166 is about — CI DEV Stable) | **GREEN 3/3.** No sanctioned-RED. Any red is a real finding. |
| `http://localhost:5173` | **Sanctioned-RED 3/3**, single signature, `# Known defect: #1215`, all functional assertions passing. Record it as such in the closure record. |

Gate this repair on **DEV** — that is where the card's failure lives and where the repaired wait
must be proven. Budget 2-4x nominal wall clock and read `reports/reruns.json` after every
invocation: the `#2124`/`#2156` DEV `Page.goto` hazard is *not* this case's signature
(allure `broken`, 0 steps, at a precondition) and must be re-run, never accepted 2-of-3.

### Defects filed / escalations

**None.** No new product defect surfaced. No blocker requiring a human decision. The
declared items above (the residual stale-grid window; the `clear_search()` sibling; the
docstring correction for #1215's environment scope) are recorded here rather than escalated,
because none of them changes *what* the test verifies.
