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
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | **on-automation/testids only** — NOT on `origin/main` (see § Metadata provenance-correction note; `EliteaCatalog.jsx` on `main` has no `data-testid` on this `Typography` at all) |
| Catalog search input | `AgentHubPage.search_input` (`catalog-search-input`) | none | **on-automation/testids only** — NOT on `origin/main` (`git show origin/main:'src/[fsd]/pages/elitea-catalog/EliteaCatalog.jsx'` confirms the `TextField` there has no `inputProps`/`data-testid` at all) |
| Agent card (by name) | `AgentHubPage.get_agent_card(name)` (`AGENT_CARD_PREFIX`, `catalog-agent-card-{id}`) | none | **on-automation/testids only** — NOT on `origin/main` (`git grep -- "catalog-agent-card-" origin/main -- src/` returns zero hits; present on `origin/automation/testids` in `AgentCard.jsx:41`) |

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
- **Two more waits the fixed `clear_search()` alone didn't cover, both added to `AgentHubPage`:**
  - `wait_for_agent_card_count(expected_count, timeout)` / `wait_for_agent_card_count_not(unexpected_count, timeout)` — retrying `expect(locator).to_have_count(...)`/`.not_to_have_count(...)` assertions, used after `search()` (step 5, wait for the count to move away from the baseline before reading filtered names) and after `clear_search()` (step 6, wait for the count to return to exactly the baseline before reading restored names) — network-settling alone doesn't guarantee the React commit has landed by the time the DOM is read.
  - `wait_for_any_agent_card(timeout)` — used in **step 1** after `navigate_and_capture_applications()` (reused from ELITEA-2354, waits on the bulk response) and before reading the baseline names. The page heading is static and renders before the data-dependent card grid does, so a bare navigate-then-read races the same way. **Important, and NOT a wait for the DOM count to equal the bulk response's raw row count** — each category section (`AgentCategorySection.jsx`) only renders its first `INITIAL_CARD_DISPLAY_COUNT` items initially, with the rest behind "Show more"; the bulk response routinely lists far more rows (confirmed live: 46 rows) than are ever rendered in the grid at once (confirmed live: 23 cards). Waiting for "at least one card visible" is the correct render-completion signal here, not an exact count.
- **Step 4's network-count assertion — filter-then-count-1 is NOT enough.** The correct assertion counts ALL requests captured to the search endpoint during the typing window FIRST (assert the total is exactly 1), THEN checks that one request's `query` param — not filtering to `query=="story"` and counting the survivors. Filter-then-count would still show exactly 1 survivor even if the debounce were broken and fired once per keystroke (5 requests for "story", 4 with partial queries filtered out, 1 with the final value) — a real regression that the filter-first shape cannot catch.
