# Test Case: Agent Hub — search bar filters agents in real time

## Metadata
- **TMS ID**: ELITEA-2363
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium — same mapping as siblings ELITEA-2352/2354)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot), ELITEA-2363, 2026-08-06
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP. All 6 steps reproduced: typing filters in real time with no Enter/submit control (300ms debounce, confirmed via source + a single debounced network request), only matching agents remain visible (including the case's own named example, "User Story Creator"), and clearing the field (no clear/X button exists — confirmed absent via source; clearing means manually deleting the typed text) restores the exact original unfiltered set. Zero console errors throughout. No new testid needed — both handles this case touches already exist, but neither is on `main` yet (see § Concrete Handles PROVENANCE — this corrects a stale claim in a prior sibling AFS, see note below).
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075/2350/2352/2354) already provides `search_input`, `search(query)` (with the exact debounce-aware wait this case needs), `get_agent_card(name)`, `AGENT_CARD_PREFIX`, `get_agent_card_count()`. **Not a target for `extend-existing`/`already-covered`**: the only existing caller of `search()` is `test_agent_hub_like_agent_list_view.py` (ELITEA-2354), which uses it purely as *transit* — to re-locate one already-known agent after a page refresh — and asserts nothing about real-time filtering, multi-agent narrowing, or clear-restores-all. This case's entire observable (the filtering behaviour itself) is untouched by any merged spec. Fresh coverage.
- **Provenance correction (fresh-ground-truth finding, worth a future compaction note):** the ELITEA-2354 AFS (`l3_agent-hub-like-agent-from-list-view_ELITEA-2354.md` § Concrete Handles) claims `catalog-page-heading`, `catalog-search-input`, and `catalog-agent-card-{id}` are "on-main ✓ (pre-existing, ELITEA-2075)". A fresh `git fetch origin` + `git grep` against `origin/main` in this session (2026-08-06) shows **none of the three exist on `origin/main`** — `EliteaCatalog.jsx` on `main` has no `data-testid` on the heading or the search `TextField` at all, and `AgentCard.jsx` was not checked further given the heading/search result alone falsifies the claim. All three ARE present on `origin/automation/testids`. Either the prior claim was wrong at the time, or `main` was reset/force-pushed since (out of scope for this case to root-cause) — recorded here so a future analyst/lead doesn't propagate the stale claim forward, and the closure record for THIS case must use the verified-today numbers, not the ELITEA-2354 file's.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- Agent Hub (Catalog) page freshly navigated to, Agents tab active (default).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- **Search term**: the case's own example, `"story"` — confirmed live (this session, `${TEST_USER}` / Private project) to match 6 agents across 2 categories: "Elitea Feature Story Generator", "User Story Creator" (Business Analyst); "Tell story agent", "Turtle Story Generator" (×2, same name/owner "Marian Matskevych", one with an "elitea" icon and one without — confirmed real distinct cards, not a UI bug), "StoryFromGithub" (Other). The match is confirmed **case-insensitive substring** (query `"story"` lowercase matched titles containing `"Story"` capitalized) — server-side, since the debounced request itself carries `query=story` and the backend returns the pre-filtered set (see § Network Behavior).
- **Do not hardcode the exact total card count** before/after the filter — the Catalog's agent list is live, mutable, shared product data (same caution as ELITEA-2354's like-count note); assert the STRUCTURAL invariants instead (see § Test Steps step 4/5): fewer cards after filtering than before, every visible card's name contains the query substring, and the case's own named example is among them. Counts observed in THIS session (for reference only, not to be asserted verbatim): 23 cards / 7 categories unfiltered → 6 cards / 2 categories filtered on "story".

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.wait_for_page_load()`); capture the full set of currently-rendered agent card names as the pre-search baseline (via `AGENT_CARD_PREFIX` or the underlying `public_applications` list response).
2. Click into the search bar at the top.
   - **Verify**: `catalog-search-input` is focused/editable (reuse `AgentHubPage.search_input`).
3. Type a partial search term (`"story"`) into the field.
   - **Verify**: field displays the typed value (`catalog-search-input` value = `"story"`).
4. Verify the agent list filters in real time as the user types — no Enter, no submit button, no other control needed.
   - **Verify**: confirmed live and via source (`AgentsTab.jsx` — `useDebounceValue(query, 300)` feeding `useAgentHubData`; `EliteaCatalog.jsx`'s `TextField.onChange` is the only wiring, no `onKeyDown`/`Enter` handler and no adjacent submit/search-icon button exists in the JSX). Typing alone (via `press_sequentially`, matching the existing `AgentHubPage.search()` idiom — `fill()` would not trigger the debounced React state per `.claude/rules/mui-patterns.md`) triggered exactly ONE debounced `GET /api/v2/elitea_core/public_applications/prompt_lib/?query=story&...` request (confirmed via network capture — `=> [200] OK`), ~300ms after the last keystroke, no click/Enter involved. This is the interaction-discovery ladder's step 6 (read the source) applied and confirmed — the intended mode (debounced live filtering) works exactly as coded; no case-text drift here.
5. Verify only matching agents are displayed (e.g., "User Story Creator").
   - **Verify**: confirmed live — after the debounced request resolves, only the 6 cards whose names contain "story" (case-insensitive) remain rendered, across only the 2 categories that contain a match (Business Analyst, Other); the 5 categories with zero matches (Trending, DevOps, Development, Elitea, Quality Assurance) are no longer rendered at all. The case's own named example, "User Story Creator", is confirmed present among the filtered results (Business Analyst section).
6. Clear the search field and verify all agents return to the list.
   - **Verify**: **case-text note, not drift** — there is no clear/X button on the search field (confirmed absent via source: `EliteaCatalog.jsx`'s `TextField` has no `InputProps` endAdornment/clear affordance at all — a plain MUI `TextField`). "Clear the search field" means manually deleting the typed text (confirmed live: click the field, select-all (`ControlOrMeta+a`), `Backspace`). After clearing, the SAME debounced-request pattern fires with an empty query (confirmed live: the exact 3-request pattern from initial page load re-fires — bulk `query=&...limit=1000`, Trending, My Liked — see § Network Behavior), and all 7 original categories / all originally-visible cards re-render (confirmed live: identical category set and card names to the step-1 baseline).

## Expected Results
- Typing a partial term into the Catalog search bar filters the agent list in real time (debounced ~300ms, no Enter/submit control involved) to only agents whose name contains the term (case-insensitive substring match), collapsing/removing categories with zero matches entirely.
- Clearing the typed text (no dedicated clear button exists) restores the full original unfiltered list exactly.
- Zero console errors throughout typing, filtering, or clearing.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click in the search bar at the top | Control responds; expected next state is shown | step 2 | `catalog-search-input` focused/clickable | asserted |
| 3 Type a partial search term (e.g., "story") | Field accepts the input and displays the entered value | step 3 | `catalog-search-input` value reads "story" | asserted |
| 4 Verify the agent list filters in real time as the user types | Condition holds as described | step 4 | single debounced `GET .../public_applications/prompt_lib/?query=story...` request fires ~300ms after typing stops, with no Enter/click needed (confirmed via source + live network capture) | asserted |
| 5 Verify only matching agents are displayed (e.g., "User Story Creator") | Condition holds as described | step 5 | every visible card name contains "story" (case-insensitive); "User Story Creator" specifically present; non-matching categories entirely absent | asserted |
| 6 Clear the search field and verify all agents return to the list | Action completes without error and produces the expected UI state | step 6 | post-clear category set/card set identical to the step-1 baseline; case-text says "clear" — no clear button exists, so automation clears via select-all+backspace (case-text note, not drift — see step 6) | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 4` asserts the underlying debounced network request (endpoint + query param + timing relative to the last keystroke) — *added: proves the real-time filtering is driven by the actual search mechanism (debounced onChange → API call), not a pre-loaded client-side-only illusion; also directly answers the interaction-discovery ladder question the dispatch asked to verify (Enter/submit vs plain typing).*
- `step 5` asserts the STRUCTURAL invariant (every visible name contains the query substring, non-matching categories absent) rather than a hardcoded total count — *added: the Catalog's agent list is live, mutable, shared product data (same caution already recorded for like counts in ELITEA-2354's AFS); a hardcoded count would be flaky as agents are added/removed by the team over time.*
- `step 6` asserts the exact same request pattern re-fires as on initial page load — *added: proves "clear" genuinely resets to the unfiltered state via the same code path as a fresh mount, not some other reset mechanism that might drift from it later.*
- Console-error check across steps 3–6 — *added: standard side-channel regression guard per this skill's own discipline. Zero errors observed at any point in this case (unlike the like/unlike flow's known #1215 defect) — no new finding.*

## Cleanup

None required — this case only reads/filters the existing agent list; it does not create, like, or otherwise mutate any shared product data. Clearing the search field at the end of step 6 already returns the page to its original (unfiltered) state.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance (verified 2026-08-06, fresh `git fetch origin`) |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | **on-main ✓** (re-verified 2026-09-10, fresh `git fetch origin`) |
| Catalog search input | `AgentHubPage.search_input` (`catalog-search-input`) | none | **on-main ✓** (re-verified 2026-09-10, fresh `git fetch origin`) |
| Agent card (by id) | `AgentHubPage.AGENT_CARD_PREFIX` (`catalog-agent-card-{id}`) | none | **on-main ✓** (re-verified 2026-09-10, fresh `git fetch origin`) |
| No-results title | `catalog-no-results-title` (in `SEARCH_RESULTS_SETTLED`) | none | **on-main ✓** (re-verified 2026-09-10, fresh `git fetch origin`) |

> ⚠️ **The three "on-automation/testids only" rows above were CORRECTED on 2026-09-10.** The
> 2026-08-06 analysis recorded all three as absent from `origin/main`; a fresh fetch today shows
> **all four present on `origin/main`** — the UI team promoted them in the interim. The stale rows
> are the reason this file previously carried a provenance-correction note about ELITEA-2354; that
> note is now itself stale and is superseded by this block. **This case is NOT a promotion gap
> (triage class F ruled out).** Verification command + output are pasted in § Adjustment below.

No testid needed for this case — every element it touches already carries one on `automation/testids` (which is what the local dev server under test runs), so the implementer needs no `add-data-testid` work. The three rows above are all pre-existing handles from ELITEA-2075/2350, re-used here, not new asks; the PROVENANCE column corrects the "on-main" claim inherited (incorrectly) from the ELITEA-2354 sibling AFS.

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?query=story&statuses=published&agents_type=classic&limit=100&offset=0` → `200 OK`. Fires exactly once, ~300ms after the last keystroke (the `AgentsTab.jsx` `useDebounceValue(query, 300)` debounce), regardless of how many characters were typed — confirmed live via network capture (typed "story" character-by-character via `press_sequentially`, only one `query=story` request observed).
- Clearing the field re-fires the SAME 3-request pattern observed on initial page mount: bulk `GET .../public_applications/prompt_lib/?query=&...limit=1000&offset=0`, Trending (`trend_start_period=...&sort_by=likes&sort_order=desc&limit=20`), and My Liked (`my_liked=true&limit=20`) — confirmed live, identical query shapes to the step-1 baseline capture.
- No 4xx/5xx observed at any point (typing, filtered state, or clearing).

## Known Defects Found During Exploration
None. All 6 case steps reproduced exactly as expected; zero console errors; no case-text drift beyond the already-tracked family-wide "Agent HUB" naming drift (issue #1208, not re-cited here since this case's own text doesn't use that phrase) and the search field's missing clear button, which is a **case-text note, not a defect** (see step 6 — the case's own wording "clear the search field" is satisfied by manually deleting the text; the live product never claimed to have a dedicated clear button, so there is no divergence between intended and actual behaviour to file).

## Blocked Steps
None — all 6 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- Reuse `AgentHubPage.search(query)` as-is for steps 2–4 (it already waits on the exact debounced `public_applications` response this case needs — see its docstring).
- Assert step 5 structurally, not by hardcoded count: read all currently-visible card names (`AGENT_CARD_PREFIX` locator's `text_content()` over each match, or the debounced response body's `rows[].name`) and assert (a) `len(filtered) < len(baseline)`, (b) every filtered name contains the query substring case-insensitively, (c) the case's named example ("User Story Creator") is among them.
- Assert step 6 by comparing the restored card-name set (or count) back to the step-1 baseline set/count captured before typing — exact equality, not just "not empty".
- Console-error capture across steps 3–6 (reuse the existing `capture_console_errors()`/`console_errors` idiom from `test_agent_hub_like_agent_list_view.py`) — expect zero; this case has no known defect to soft-assert around, unlike the like/unlike flow's #1215.
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.agents` (matches ELITEA-2350/2352/2354's marker set for this same page).

**Amended during implementation (ELITEA-2363, PR #1230, fix round after reviewer findings) — the snippet originally drafted here for `clear_search()` had a real race and was NOT what shipped. Replaced below with what actually merged, plus two more waits the review surfaced as missing.** All three are documented in `never_assume_a_transition_settled.md` (test-automation-engineer memory).

- **`AgentHubPage.clear_search()` — actual shipped version.** The original draft's generic `expect_response` predicate (`"/public_applications/prompt_lib/" in r.url`) matches THREE parallel requests that all re-fire on clear (bulk all-applications, Trending, My-Liked — see § Network Behavior) and can resolve on the fast Trending/My-Liked call while the bulk request — the one that actually repopulates the content grid — is still in flight, leaving the grid showing the stale filtered set for a beat after the method returns. Fixed by scoping the predicate to the bulk call specifically (excluding `trend_start_period`/`my_liked`, the same filter `navigate_and_capture_applications` already uses):
  ```python
  @action("Clear Catalog search field")
  def clear_search(self, timeout: int = 15000):
      """Clear the Catalog search field and wait for the debounced
      empty-query BULK request (the one that actually drives the main
      content grid) to resolve (ELITEA-2363).

      Uses select-all + Backspace, NOT `fill("")` — per
      `.claude/rules/mui-patterns.md`, `fill()` sets the DOM value
      directly and would not fire the debounced React `onChange`,
      leaving the `query` state (and therefore the rendered list)
      unchanged. There is no dedicated clear/X button on this field
      (confirmed via source — EliteaCatalog.jsx's TextField has no
      InputProps endAdornment) — this IS the intended interaction.

      Clearing re-fires the SAME 3-request pattern as initial page mount
      (bulk all-applications, Trending, My Liked — AFS § Network
      Behavior) — all three share the ``/public_applications/prompt_lib/``
      substring, so the predicate below excludes the Trending/My-Liked
      query params to deterministically await the BULK response
      specifically (confirmed live during implementation: awaiting "any"
      matching response could resolve on the faster My-Liked/Trending
      call while the bulk request — and therefore the re-rendered
      content grid — was still in flight).
      """

      def _is_bulk_applications_response(response):
          return (
              "/public_applications/prompt_lib/" in response.url
              and response.request.method == "GET"
              and "trend_start_period" not in response.url
              and "my_liked" not in response.url
          )

      self.search_input.wait_for(state="visible", timeout=timeout)
      with self.page.expect_response(_is_bulk_applications_response, timeout=timeout):
          self.search_input.click()
          self.search_input.press("ControlOrMeta+a")
          self.search_input.press("Backspace")
      self.wait_for_network(timeout=timeout)
  ```
  **Superseded twice since — read `automation/pages/agent_hub_page.py` for the current shape,
  not this snippet:**
  - **FIX #2078** replaced the bare `self.page.expect_response(…, timeout=timeout)` with
    `self._expect_applications_response(…, response_timeout, …)`, decoupling the bulk-response
    budget (`CATALOG_RESPONSE_TIMEOUT = 45_000`) from the caller's UI-element timeout.
  - **FIX #2168 (2026-09-10) removed the trailing `self.wait_for_network(timeout=timeout)`
    entirely** — the #1847 `networkidle` class, whose byte-identical twin in `search()` took a
    sibling spec RED 3/3 in CI run #116. It is replaced by **nothing**: the method's contract is
    now "returns on the bulk response; the grid re-renders ~376 ms later (measured on DEV), so
    callers MUST read it through an auto-retrying assertion" — which step 6 already does via
    `wait_for_agent_card_count(len(baseline_cards))`. Deliberately NOT replaced by `search()`'s
    `SEARCH_RESULTS_SETTLED` union, which is **vacuous after a clear** (satisfied 4.72 ms after
    the response, grid mid-restore at 12 of 27 cards — its `catalog-agent-card-*` branch already
    matches the pre-clear filtered cards). No terminal settle is expressible inside the page
    object, since only the caller knows the baseline count. Full analysis:
    `test-specs/agent-hub/_surface.md` § the `clear_search()` bullet.
- **Two more waits the fixed `clear_search()` alone didn't cover, both added to `AgentHubPage`:**
  - `wait_for_agent_card_count(expected_count, timeout)` / `wait_for_agent_card_count_not(unexpected_count, timeout)` — retrying `expect(locator).to_have_count(...)`/`.not_to_have_count(...)` assertions, used after `search()` (step 5, wait for the count to move away from the baseline before reading filtered names) and after `clear_search()` (step 6, wait for the count to return to exactly the baseline before reading restored names) — network-settling alone doesn't guarantee the React commit has landed by the time the DOM is read.
  - `wait_for_any_agent_card(timeout)` — used in **step 1** after `navigate_and_capture_applications()` (reused from ELITEA-2354, waits on the bulk response) and before reading the baseline names. The page heading is static and renders before the data-dependent card grid does, so a bare navigate-then-read races the same way. **Important, and NOT a wait for the DOM count to equal the bulk response's raw row count** — each category section (`AgentCategorySection.jsx`) only renders its first `INITIAL_CARD_DISPLAY_COUNT` items initially, with the rest behind "Show more"; the bulk response routinely lists far more rows (confirmed live: 46 rows) than are ever rendered in the grid at once (confirmed live: 23 cards). Waiting for "at least one card visible" is the correct render-completion signal here, not an exact count.
- **Step 4's network-count assertion — filter-then-count-1 is NOT enough.** The correct assertion counts ALL requests captured to the search endpoint during the typing window FIRST (assert the total is exactly 1), THEN checks that one request's `query` param — not filtering to `query=="story"` and counting the survivors. Filter-then-count would still show exactly 1 survivor even if the debounce were broken and fired once per keystroke (5 requests for "story", 4 with partial queries filtered out, 1 with the final value) — a real regression that the filter-first shape cannot catch.

---

## Adjustment — 2026-09-10 (repair triage for CI run 34436416962 / card #2179)

**Triage class: D — shared-mutable-data pollution.** NOT UI drift (A), NOT a product bug (B/C),
NOT a promotion gap (F — all four testids re-verified on `origin/main` today), NOT missing-testid
(E — no new testid is needed for this repair). Analyst: qa-engineer, ELITEA-2363, 2026-09-10.

### The failure

CI attempts 1 and 3 of run 34436416962 failed byte-identically at Step 6
(`test_...py:141`, `assert restored_cards == baseline_cards`) with exactly two deltas in a
27-element list:

1. **Content** — `multi-skill-agent-2600-1f1c00TB0` → `...TB1`
2. **Order** — `Quality Engineering Sidekick4` moved index 3 → 5, `Pytest: Quality Agent4` took index 3

### Root cause — ONE event, not two

Both deltas trace to a single cause: **a like landed on a catalog agent during the test window.**

**Why the like count is in the string at all.** `get_visible_agent_card_names()` returns each card's
whole `text_content()`. `AgentCard.jsx` renders, inside one `<Card>`: the name `Typography`, the
`AuthorContainer` avatar (initials fallback), and `AgentHubLike` → `Like.jsx:70`
`<Typography variant="bodySmall">{likes || 0}</Typography>`. So `text_content()` concatenates
`name + authorInitials + likeCount` with no separator. Confirmed live this session (localhost,
DEV backend):

```
whole: "Business Analyst9"   heading: "Business Analyst"   like: "9"
whole: "Reflexion5"          heading: "Reflexion"          like: "5"
```

`...1f1c00TB0` is therefore `multi-skill-agent-2600-1f1c00` + author initials `TB` + like count `0`.
The delta is the **like count going 0 → 1**. The helper's own docstring asserts this is
*"harmless … since no like state changes during this case"* — **that premise is exactly what CI
falsified**, and it is a premise this spec has no way to guarantee.

**Why the order moved too.** The order is NOT unstable. Measured against the live DEV backend,
6 identical requests each:

| Query | Runs | Same ORDER? |
|---|---|---|
| bulk `…/public_applications/prompt_lib/?query=&statuses=published&agents_type=classic&limit=1000` (**no `sort_by`**) | 5 | **5/5 identical** |
| Trending `…&trend_start_period=2000-01-01T00:00:00&sort_by=likes&sort_order=desc&limit=20` | 6 | **6/6 identical**, including inside every like-count tie group (ties observed at 4×2, 3×3, 2×4, 1×8) |

`useAgentHubData.hooks.js` passes **no** `sort_by`/`sort_order` on the bulk fetch and the frontend
never sorts (`bucketAppsByCategory` preserves `result.rows` order); **only `fetchTrendingApplications`
sends `sort_by: 'likes', sort_order: 'desc'`**, and `CatalogBody.jsx` renders Trending first
(`allCategories.slice(0, FEATURED_COUNT)`, Trending at index 0). So: **for a fixed dataset the order
is fully deterministic; when a like count changes, the Trending section legitimately re-ranks.** In
CI, `Pytest: Quality Agent` was at 4 likes and sorted ahead of `Quality Engineering Sidekick` (also
4); today it sits at 3 and sorts below. Product behaving correctly.

**Who does the liking — in this very suite.** `test_agent_hub_like_agent_list_view.py` Step 2 calls
`find_zero_like_application()` and asserts the target *"should start with 0 likes"*, then likes it
(**0 → 1** — precisely the observed `TB0` → `TB1`). Its cleanup-unlike is **soft-asserted**
(`like_count_restored` → `soft_failures`), so restoration is explicitly not guaranteed.
`test_agent_hub_like_agent_from_modal.py` and `test_agent_hub_unlike_agent_list_view.py` mutate the
same shared counter. This is the `#1082` shared-mutable-state family — but note the important
difference: **ELITEA-2363 is a read-only case and should be immune.** It is vulnerable only because
it baked a volatile counter into its identity string. The fix therefore belongs in **this spec**, not
in suite health.

### Reproduction

**Not reproducible on demand — intermittent by construction** (it needs a like to land inside the
~15 s window). Local, `http://localhost:5173`, DEV backend, clean process each time:

```
run 1: 1 passed in 16.11s   reruns.json {}
run 2: 1 passed in 14.57s   reruns.json {}
run 3: 1 passed in 15.01s   reruns.json {}
run 4: 1 passed in 13.47s   reruns.json {}
```

4/4 green with no reruns. A green local run does **not** refute the CI red here — it only confirms
no sibling spec liked anything during those four windows. The CI failure is fully explained above
and reproduced *by mechanism* (the like-count-in-text artifact is demonstrated live), which is the
correct standard for this class.

### The honest observable — measured against the TMS case, not convenience

TMS ELITEA-2363 Step 6 reads: *"Clear the search field and verify all agents return to the list"* →
*"Action completes without error and produces the expected UI state."* The Expected Final State is
*"Clear the search field and verify all agents return to the list."*

**"All agents return to the list" is a statement about membership.** The case never mentions like
counts, author initials, or ordering. This AFS's own § Automation Hints already specified
*"comparing the restored card-name **set** (or count) back to the step-1 baseline **set**/count"* —
the shipped implementation used ordered list equality on contaminated strings, which is **stricter
than both the case and this AFS**, and strict in precisely the two dimensions the product is free to
vary.

| Delta the current assertion catches | Part of what ELITEA-2363 verifies? | Disposition |
|---|---|---|
| An agent missing from the restored list | **YES** — this IS the case | **KEEP — must still fail** |
| An extra agent in the restored list | **YES** | **KEEP — must still fail** |
| A card's like count changed | **NO** — never mentioned; volatile shared data | **REMOVE** — never was the observable |
| A card's author initials changed | **NO** | **REMOVE** — never was the observable |
| Trending re-ranked after a like | **NO** — no ordering requirement in the case | **DROP — see sign-off below** |

### Required changes (implementer work order)

**1. Identity must be the card ID, not the card's rendered text.** Add to `AgentHubPage`:

```python
def get_visible_agent_card_ids(self) -> list[str]:
    """Return the application id of every currently-rendered agent card,
    read from the card's own `catalog-agent-card-{id}` testid (ELITEA-2363
    repair, #2179).

    Identity for the search/clear round-trip MUST come from this method, never
    from card text: `AgentCard.jsx` renders the name, the author-initials
    avatar and `AgentHubLike`'s live like count inside one `<Card>`, so
    `text_content()` yields `name + initials + likeCount`. Sibling specs in
    this same suite (test_agent_hub_like_agent_list_view.py et al.) mutate
    that like count by design, which took this case RED in CI run
    34436416962.
    """
```

Read `data-testid` off `self.page.locator(self.AGENT_CARD_PREFIX)` and strip the
`catalog-agent-card-` prefix. **No new testid is required** — `catalog-agent-card-{id}` already
exists and is on `main`.

**2. Compare as a SORTED LIST (multiset), never a `set`.** Measured live today: the grid renders
**27 cards but only 24 unique ids** — three agents appear twice, once in Trending and once in their
own category section (`dupes: ["31", "16", "127"]`). A `set()` would silently collapse 27 → 24 and
stop detecting a genuinely dropped duplicate. Step 6 becomes:

```python
restored_ids = agent_hub.get_visible_agent_card_ids()
assert sorted(restored_ids) == sorted(baseline_ids), (
    "Every agent present before searching should be present again after clearing "
    f"(baseline {len(baseline_ids)} cards, restored {len(restored_ids)})"
)
```

Membership **and** multiplicity preserved; only position dropped.

**3. Step 6's terminal wait must key on identity, not on a count.** `wait_for_agent_card_count(
len(baseline_cards))` is *currently* terminal — the restore is monotonic, measured live at
**6 → 12 → 27** over ~3.2 s (three discrete commits, matching the three parallel fetches) — so it is
**not** vacuous today, unlike the `clear_search()` settle retired by #2168. But it is not terminal
*by construction*: it keys on a number that shared mutable data can invalidate. If an agent is
published or unpublished mid-run the true target is 28, and `to_have_count(27)` either never resolves
(10 s timeout) or resolves **transiently while passing through 27**, handing the next line a
half-restored grid. Replace with an auto-retrying assertion on the identity multiset itself
(poll `get_visible_agent_card_ids()` until `sorted(...) == sorted(baseline_ids)` or timeout, then
assert once), so the wait and the assertion are the same condition and the read is terminal by
definition. **Do not change `wait_for_agent_card_count`'s own semantics** — two other specs use it
(`test_catalog_default_agents_tab.py:81`,
`test_agent_hub_my_liked_filter_shows_only_liked_agents.py:178`).

**4. Rename `get_visible_agent_card_names()` → `get_visible_agent_card_texts()` and fix its
docstring.** The current name is a lie (it returns name+initials+likes) and the docstring states the
false premise that took this case red. It is used **only by this spec** (grep confirmed), so the
rename is safe. Keep it for Step 5's substring check only, and have the docstring say explicitly:
*never use this for identity comparison — use `get_visible_agent_card_ids()`.*

**5. Step 1 captures `baseline_ids` alongside (or instead of) the text baseline.**

### What must NOT change

- **Step 4's network assertion** — count ALL requests to the endpoint first, *then* check the single
  survivor's `query` param. The filter-then-count-1 shape cannot catch a broken debounce (§ line 166).
- **Step 5** — `len(filtered) < len(baseline)`, every visible card contains `"story"`
  case-insensitively, and `"User Story Creator"` is present. All three stay exactly as they are.
- **Step 7** — the zero-console-errors assertion. Confirmed clean again live today (0 errors).
- **Step 6 still compares the FULL restored set to the FULL baseline.** Membership and multiplicity
  are preserved. Do **not** substitute a bare count check, a `len()` comparison, a subset check, or
  "not empty".
- No `pytest.skip`, no `expect.soft`, no `test.fail()`, no weakened assert. There is no product
  defect here to mask.

### ⚠️ Requires explicit human sign-off (preserve-the-nature rail)

**Dropping the positional/ordering claim from Step 6** is a comparison change
(`restored == baseline` → `sorted(restored) == sorted(baseline)`), which
`.agents/role-overrides.md` § Step 3 puts in the "requires explicit human sign-off" column.

The argument for it: the TMS case specifies membership only; the AFS's own Automation Hints already
said "set"; order is a deterministic function of live like counts (proved 5/5 and 6/6 above), so an
ordering assertion here cannot distinguish "the product scrambled the order" from "somebody liked an
agent" — it produces false reds with **zero** diagnostic value. No other assertion in this case
covers ordering, and no coverage of a specified behaviour is lost.

The counter-argument, stated fairly: this is still strictly less than the test asserted yesterday.
**The implementer must carry this verbatim under "Expected-result changes" in the PR body and must
not merge without a human accepting it.** Removing the like-count and author-initials contamination
(changes 1/2/4) is *not* in this category — those were never part of the case's observable and need
no sign-off.

### Residual risk — bounded, stated, not engineered around

The Trending section renders its first `INITIAL_CARD_DISPLAY_COUNT` cards (6 observed) out of a
`limit=20` likes-desc window. A like landing on an agent **near that boundary** could push it into or
out of the rendered set, genuinely changing membership and failing even the id-multiset comparison.

Today that is not reachable by the known polluter: `find_zero_like_application()` targets a **0-like**
agent and takes it to 1, while the Trending cut-off currently sits at 3–4 likes. If this ever does
fire, the correct response is to route it as a `question` (scope Step 6 to the non-Trending sections,
or freeze the identity source) — **never** to weaken the comparison further.

### Findings

- **No `bug` card.** Ordering is deterministic for fixed data and re-ranks correctly when likes
  change; the product is behaving as coded. No product defect was observed. Zero console errors.
- **One `question` card is owed** (suite health, not a blocker for this repair): sibling agent_hub
  specs mutate a shared, cross-session like counter with **soft-asserted** cleanup, so any spec that
  reads like-sensitive state is exposed. Related to the `#1082` / rotating-test-identity pointer in
  `.agents/testing.md` § Suite-health pointer. ⚠️ **Dedup not completed** — `gh issue list` returned
  `API rate limit already exceeded` this session, so the lead/implementer must run the § Bug filing
  dedup pass before filing.
