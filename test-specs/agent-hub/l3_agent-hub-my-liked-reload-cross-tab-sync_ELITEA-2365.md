# Test Case: Agent Hub — "My Liked" reload reflects a like made in another tab

## Metadata
- **TMS ID**: ELITEA-2365
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login. Both tabs in this case share the SAME authenticated browser context (`page.context.new_page()`) — no second login/auth flow needed, same precedent as `test_guardrails_live_reload.py`/`test_ghost_skill_after_agent_removed.py`.
- **Analyst**: qa-engineer (analyst slot), ELITEA-2365, 2026-08-06
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP (two tabs in one browser context). All 11 steps reproduced except step 8's literal "reload/refresh (↻) icon" (case-text drift, see § Known Defects/Clarifications — cite EliteaAI/elitea-testing-public#1212, do not re-file). The case's real observable — a liked-in-another-tab agent appearing in "My Liked" with the matching count after a refresh — is fully confirmed live via a **full page reload** substituted for the non-existent icon (same substitution precedent as ELITEA-2354 step 6's page-refresh persistence check). Zero new testids needed — every handle this case touches was already added by ELITEA-2350/2352/2354's implementers and is live on `automation/testids` (confirmed via fresh `git grep`, § Concrete Handles).
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`, ELITEA-2075/2350/2352/2354) already provides everything this case needs by composition: `navigate()`/`wait_for_page_load()`, `click_category_filter_chip("My Liked")`/`is_category_filter_chip_selected("My Liked")` (ELITEA-2350/2352), `is_category_section_visible("my-liked")` (ELITEA-2352's `CATEGORY_HEADING` template), `get_agent_card(name)` (ELITEA-2075), `click_like_button(application_id)`/`get_like_count(application_id)`/`is_agent_liked(application_id)`/`wait_for_like_count(...)`/`find_zero_like_application(...)`/`navigate_and_capture_applications()` (ELITEA-2354), and `BasePage.reload_and_wait()`. **Not a target for `extend-existing`/`already-covered`**: no merged spec exercises TWO tabs/pages against this surface, and no merged spec asserts that the "My Liked" section reflects a like made through a *different* page instance — ELITEA-2354's own page-refresh check (step 6) is single-tab, re-locating the SAME agent it itself liked, not a cross-tab propagation check. This case's entire observable (cross-tab My-Liked-list sync via refresh) is untouched by any existing spec. Fresh coverage.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost) — same in both tabs (same browser context, same auth/session).
- Agent Hub (Catalog) page freshly navigated to in Tab A.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- **No specific agent name is a reliable fixture for "not yet liked"** (same class of gap as ELITEA-2354's "0 likes" fixture note — like state is mutable, shared, cross-session product data). The implementer's test must **dynamically discover** a currently-unliked agent card in Tab B at runtime (e.g. via `AgentHubPage.navigate_and_capture_applications()` + a helper checking `is_liked` on the returned rows, mirroring `find_zero_like_application`'s idiom but filtering on `is_liked is False` instead of `likes == 0`), rather than hardcoding a name. Confirmed live this session: "Elitea Feature Story Generator" (application id **277**) read `0` likes / not liked at time of exploration (Business Analyst category, `${TEST_USER}` / Private project) and was used for this run.
- Pre-existing liked agents in this environment at time of exploration (baseline, NOT to be touched by this test): "Business Analyst" (agent, 8 likes) and "Magic Assistant" (2 likes) — both already under "My Liked" before this case's own like action. The test must not assume a specific pre-existing baseline set/count — only that the NEWLY liked agent (picked dynamically in Tab B) is absent from "My Liked" in Tab A before the refresh and present after it.

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`) in Tab A and click the "My Liked" category filter-rail chip.
   - **Verify**: page loads (`catalog-page-heading` visible, reuse `AgentHubPage.wait_for_page_load()`); chip click narrows the content list to render ONLY the "My Liked" category section (confirmed live: clicking the chip via `AgentHubPage.click_category_filter_chip("My Liked")` left `catalog-category-heading-my-liked` as the sole rendered category heading, same multi-select-chip mechanic ELITEA-2352 documented — a fresh page starts with zero chips selected, so this single click is effectively exclusive). Chip's own selected state is verifiable via `is_category_filter_chip_selected("My Liked")` (`data-selected="true"`, ELITEA-2352 precedent).
2. Verify the current list of liked agents is displayed under the "My Liked" section.
   - **Verify**: `catalog-category-heading-my-liked` visible + the pre-existing liked agent cards render beneath it (confirmed live: "Business Analyst" (8) and "Magic Assistant" (2) both rendered). Automation should assert the SET of card names present at this point as the pre-refresh baseline (do not hardcode these two names — read them live, since like state is shared cross-session data), and specifically assert the target agent (step 4/2's dynamically-discovered one) is NOT yet a member.
3. Open Agent Hub in a second tab (Tab B), same browser context.
   - **Verify**: `page.context.new_page()` → navigate to `/elitea-catalog` → page loads (`catalog-page-heading` visible). Same authenticated session (no re-login) — confirmed live via the page title `"ELITEA Catalog - Private"` matching Tab A's project context.
4. In Tab B, locate an agent that is not yet liked and click its heart icon (like button) to like it.
   - **Verify**: found dynamically (see § Test Data — do not hardcode a specific agent name/id). Click succeeds; `POST /api/v2/social/like/prompt_lib/{project_id}/application/{id}` fires and returns `201 Created` (confirmed live: `POST .../social/like/prompt_lib/1/application/277 => 201`).
   - **KNOWN DEFECT (filed, non-blocking — see § Known Defects/Clarifications)**: same as ELITEA-2354 — one console `[ERROR]` fires on this click (`agentHub/updateApplicationInCategories` non-serializable-payload warning, EliteaAI/elitea-testing-public#1215). Assert via `expect.soft()`/the suite's `soft_failures` idiom + `# Known defect: #1215`, not a hard console-cleanliness assertion for this specific click.
5. Verify the like count increments on the agent card in Tab B.
   - **Verify**: like-button testid's text content reads `1` (was `0` before step 4). Confirmed live: `catalog-agent-like-button-277` read `"0"` → `"1"` immediately after the `201` response (optimistic update, same idiom as ELITEA-2354).
6. Switch back to Browser Tab A.
   - **Verify**: Tab A's page state is unchanged from step 2 (still showing the pre-like "My Liked" set — this tab did nothing to trigger a re-fetch).
7. Verify the newly liked agent from Tab B is not yet visible in the "My Liked" list in Tab A.
   - **Verify**: the target agent (by name/id, resolved in step 4) is absent from Tab A's currently-rendered "My Liked" card set. Confirmed live: "Elitea Feature Story Generator" was NOT among Tab A's rendered My-Liked cards at this point (only "Business Analyst"/"Magic Assistant" from the pre-existing baseline).
8. Click the reload/refresh (↻) icon next to the "My Liked" section header in Tab A.
   - **CASE-TEXT DRIFT (CLARIFICATION, do not re-file — cite EliteaAI/elitea-testing-public#1212)**: **no reload/refresh icon exists anywhere next to any category section header**, including "My Liked" — confirmed both visually (screenshot, `.playwright-mcp/elitea-2365-myliked-filtered.md`: the "My Liked" heading renders with zero sibling icon elements) and via source: `AgentCategorySection.jsx`'s `headerContainer` (the SAME shared component rendering every category section, "My Liked" included — it has no category-specific branching) renders only a `Typography` title (read in full this session; confirmed zero icon elements). This is the exact same drift #1212 already tracks for ELITEA-2352 ("reload category items icon" next to a filtered category's header) — the underlying component and root cause are identical, only the presenting category name differs ("Business Analyst" there, "My Liked" here). Per the `_surface.md` digest's own explicit instruction ("Future analysts in this family: expect the same claim to recur... cite #1212 rather than re-discovering it"), this is cited, NOT re-filed. **Automation substitutes the only actual refresh mechanism the live product offers for this surface: a full page reload** (`BasePage.reload_and_wait()` / re-navigate to `/elitea-catalog`), the same substitution ELITEA-2354's own step 6 already established for "refresh the page and verify...". Confirmed live: after a full reload, the "My Liked" filter-chip selection does NOT persist (it is client-only UI state, not a URL param) — the test must re-click the "My Liked" chip (`click_category_filter_chip("My Liked")`) after the reload before re-reading the section.
9. Verify the "My Liked" list refreshes.
   - **Verify**: after the substituted reload + re-selecting the "My Liked" chip, the section re-renders (new network fetch observed: `GET .../public_applications/prompt_lib/?...my_liked=true...`, same query-param signature the `_surface.md` digest documented for the initial-mount My-Liked request).
10. Verify the agent liked in Tab B now appears in the "My Liked" list in Tab A.
    - **Verify**: the target agent's card (by name/id) is now present among Tab A's "My Liked" cards. Confirmed live: "Elitea Feature Story Generator" appeared in Tab A's "My Liked" list immediately after the reload + re-filter, alongside the pre-existing "Business Analyst"/"Magic Assistant" baseline.
11. Verify the like count on the newly appeared agent card matches the count seen in Tab B.
    - **Verify**: Tab A's like-button testid for the target agent reads the SAME numeric value Tab B showed in step 5. Confirmed live: both read `"1"`.

## Expected Final State
The agent liked in Tab B is visible in Tab A's "My Liked" list after a refresh, with a like count matching what Tab B showed — confirmed live via a full page reload (the case's literal "reload icon" does not exist on this surface; see step 8's clarification).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open Agent Hub in Tab A, click "My Liked" filter tab | Target page/section loads successfully | step 1 | `catalog-page-heading` visible + `catalog-category-heading-my-liked` sole rendered heading + chip `data-selected="true"` | asserted |
| 2 Verify current liked-agents list displayed under "My Liked" | Condition holds as described | step 2 | pre-existing card set read live (not hardcoded), target agent confirmed absent | asserted |
| 3 Open Agent Hub in Tab B (new tab) | Target page/section loads successfully | step 3 | `page.context.new_page()` + `catalog-page-heading` visible in the new page | asserted |
| 4 In Tab B, like an unliked agent | Action completes without error and produces the expected UI state | step 4 | dynamic discovery (see § Test Data) + `POST .../social/like/...` `201` | asserted — plus a known, filed, non-blocking console-error finding (§ Known Defects) |
| 5 Verify like count increments in Tab B | Condition holds as described | step 5 | like-button testid text `0`→`1` in Tab B | asserted |
| 6 Switch back to Tab A | Action completes without error and produces the expected UI state | step 6 | tab-select, Tab A state unchanged | asserted |
| 7 Verify newly liked agent NOT yet visible in Tab A's "My Liked" | Condition holds as described | step 7 | target agent absent from Tab A's rendered My-Liked card set | asserted |
| 8 Click reload/refresh icon next to "My Liked" header in Tab A | Control responds; expected next state is shown | step 8 | **no such icon exists** — case-text drift, cited (EliteaAI/elitea-testing-public#1212), not re-filed; substituted with a full page reload + re-selecting the "My Liked" chip | clarification (icon-claim half); the refresh *behavior itself* is asserted via the substituted action |
| 9 Verify "My Liked" list refreshes | Condition holds as described | step 9 | `GET .../public_applications/prompt_lib/?...my_liked=true...` re-fires after the substituted reload + re-filter | asserted |
| 10 Verify agent liked in Tab B now appears in Tab A's "My Liked" | Condition holds as described | step 10 | target agent present in Tab A's post-reload "My Liked" card set | asserted |
| 11 Verify like count on newly appeared card matches Tab B's count | Condition holds as described | step 11 | both tabs' like-button testid text content equal (`"1"` == `"1"`, confirmed live) | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 1`/`step 8` assert the category filter-rail chip's `data-selected` state explicitly (not just the visual filtering effect) — *added: reuses the exact, already-proven `is_category_filter_chip_selected()` signal from ELITEA-2352 rather than inferring selection from which cards render, which is a weaker/indirect proof.*
- `step 4` asserts the underlying `POST .../social/like/...` `201` response, not merely the Tab B UI count — *added: proves the like reached the backend (same rationale as ELITEA-2354's step 3), so a pure client-state bug in Tab B alone wouldn't silently pass this case's cross-tab claim.*
- `step 8` documents that filter-chip selection does NOT survive a full page reload (client-only state, no URL param) — *added: a real implementation gotcha discovered live; the test must re-click "My Liked" post-reload or it will read the wrong (unfiltered) section and false-fail/false-pass depending on which cards happen to render by default.*
- `step 9` asserts the specific `my_liked=true` network request re-fires after the reload — *added: proves the refresh actually re-fetched from the backend rather than merely re-rendering stale client cache, which is the actual product claim under test (cross-tab likes require a fresh read since Tab A has no live subscription to Tab B's mutation).*
- Console-error check on the Tab B like click — *added: standard side-channel regression guard per this skill's own discipline; surfaced the already-tracked #1215 defect (same as ELITEA-2354).*

## Cleanup

**Required — this case mutates shared, cross-session product data (the target agent's public like count/state), which sibling cases in this family depend on as a clean baseline (e.g. ELITEA-2354 "like from list view", ELITEA-2355 "unlike", ELITEA-2364 "My Liked filter").** After step 11's assertions, the test MUST click the same like button again (in either tab — same backend state) to unlike the target agent, and verify its count returns to its original pre-test value (`0`) before the test ends. Confirmed live in this session: `DELETE .../social/like/prompt_lib/1/application/277 => 204`, count `1`→`0`. The two pre-existing baseline likes ("Business Analyst"/"Magic Assistant") must NOT be touched — only the agent this test itself liked in step 4.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | **needs re-verification against `origin/main` — NOT confirmed on-main this session** (see `_surface.md`'s PROVENANCE CORRECTION, 2026-08-06); confirmed present on `automation/testids`. |
| "My Liked" category filter-rail chip | `AgentHubPage.click_category_filter_chip("My Liked")` / `is_category_filter_chip_selected("My Liked")` (`CATEGORY_FILTER_CHIP.format("my-liked")` → `catalog-agent-category-filter-chip-my-liked`) | none | on-`automation/testids` ✓ (pre-existing, ELITEA-2350/2352 — `EliteaAI/EliteaUI` `AgentsTab.jsx:230`, `chipTestIdPrefix="catalog-agent-category-filter-chip"`). **Fresh `git grep` this session (2026-08-06) against `origin/main` — ZERO hits.** NOT yet on `main`. |
| "My Liked" content-list section heading | `AgentHubPage.is_category_section_visible("my-liked")` (`CATEGORY_HEADING.format("my-liked")` → `catalog-category-heading-my-liked`) | none | on-`automation/testids` ✓ (pre-existing, ELITEA-2352 — `AgentCategorySection.jsx:59`). **Fresh `git grep` this session — ZERO hits on `origin/main`.** NOT yet on `main`. |
| Agent card (by name) | `AgentHubPage.get_agent_card(name)` (`AGENT_CARD_PREFIX`, `catalog-agent-card-{id}`) | none | needs re-verification against `origin/main` per the digest's PROVENANCE CORRECTION (not independently re-checked this session — this case does not add new risk here since it only reuses the existing helper). |
| Like button (heart icon + count) on an agent card | `AgentHubPage.get_like_button(application_id)` / `click_like_button(...)` / `get_like_count(...)` / `wait_for_like_count(...)` (`LIKE_BUTTON.format(id)` → `catalog-agent-like-button-{id}`) | none | on-`automation/testids` ✓ (pre-existing, ELITEA-2354 — `AgentCard.jsx:79`). **Fresh `git grep` this session — ZERO hits on `origin/main`.** NOT yet on `main`. |
| Like button "liked" state | `AgentHubPage.is_agent_liked(application_id)` (`LIKE_BUTTON` + `[data-liked="true"]`) | none | same commit/provenance as the like button above (ELITEA-2354). NOT yet on `main`. |
| Second tab / page | `page.context.new_page()` (plain Playwright API, not a testid) | none | n/a — framework primitive, same precedent as `test_guardrails_live_reload.py` (`ctx.new_page()`) / `test_ghost_skill_after_agent_removed.py` (`page.context.new_page()`). |
| "My Liked" section reload/refresh icon | **DOES NOT EXIST** — see step 8's clarification | n/a | n/a — case-text drift, cited EliteaAI/elitea-testing-public#1212, not re-filed. Substituted with `BasePage.reload_and_wait()`. |

**No new testids needed for this case.** Every handle above was already added by an earlier case in this family (ELITEA-2350/2352/2354) and is live on the dev server (`automation/testids`) today — this case is pure composition + a two-page cross-tab flow. The implementer's own closure record must still re-verify main-provenance with a fresh fetch at merge time per `.agents/workflow.md` § Closure record (do not copy the "NOT yet on main" claims above without re-checking, per the same PROVENANCE CORRECTION discipline the `_surface.md` digest itself flags).

## Network Behavior
- `POST /api/v2/social/like/prompt_lib/{project_id}/application/{application_id}` → `201 Created` on like (Tab B). Confirmed live: `POST .../social/like/prompt_lib/1/application/277 => 201`.
- `DELETE /api/v2/social/like/prompt_lib/{project_id}/application/{application_id}` → `204 No Content` on unlike (cleanup). Confirmed live: `DELETE .../social/like/prompt_lib/1/application/277 => 204`.
- The like mutation itself is optimistic client-side in the tab that performs it (Tab B) — no re-fetch awaited there. Tab A has NO live subscription/websocket push for another tab's like — it only reflects the change after its OWN next data fetch, which on this surface only happens via a full page reload (or the app's separate, fully-automatic `useCatalogAutoRefresh` background poll, not pursued further by this case — see `_surface.md`) since there is no manual reload control (step 8's drift).
- After the substituted reload + re-filter, Tab A re-fires the `GET .../public_applications/prompt_lib/?...my_liked=true...` request (confirmed live) — the same My-Liked-specific query-param signature `_surface.md` documents for initial page mount.
- No 4xx/5xx observed during any interaction in this session.

## Known Defects/Clarifications Found During Exploration
- **[CLARIFICATION, cited not re-filed]** [EliteaAI/elitea-testing-public#1212](https://github.com/EliteaAI/elitea-testing-public/issues/1212) — case text (step 8) claims a reload/refresh icon exists next to the "My Liked" section header; no such icon exists anywhere in the live product for ANY category section (confirmed via source: `AgentCategorySection.jsx`'s `headerContainer` renders only a `Typography`, zero icon elements, for every category including "My Liked" — same shared component, same root cause #1212 already tracks for ELITEA-2352's "Business Analyst" instance). Per the `_surface.md` digest's explicit standing instruction for this family, cited rather than re-filed.
- **[MINOR, filed, already tracked]** [EliteaAI/elitea-testing-public#1215](https://github.com/EliteaAI/elitea-testing-public/issues/1215) — same Redux non-serializable-value console error on every like/unlike click, reproduced again this session on the Tab B like click (`POST .../social/like/prompt_lib/1/application/277`). Cited, not re-filed, per the `_surface.md` digest's own standing instruction ("Future analysts on like/unlike-adjacent cases (ELITEA-2355, 2364, 2365): expect the same console error and cite #1215").
- **Not a defect — implementation note**: the "My Liked" filter-chip selection is client-only UI state and does NOT survive a full page reload/re-navigation (confirmed live — the chip reset to unselected after `page.goto()`, requiring an explicit re-click before re-reading the section). Not case-text drift (the case never claims otherwise) — flagged here purely as an implementation gotcha for whoever automates step 8/9.

## Blocked Steps
None — all 11 case steps were reached and observed live (step 8's literal icon-click sub-clause is drift, not a blocker — the underlying refresh behavior it's checking for was still fully exercised via the substituted reload).

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- No `AgentHubPage` changes needed — every method this case requires already exists (see § Concrete Handles). New TEST-level logic only:
  - A small helper (test-local, not necessarily page-object-level since it's a one-off cross-tab orchestration) to open Tab B via `page.context.new_page()`, navigate it, and return the `Page` — same idiom as `test_guardrails_live_reload.py`'s `ctx.new_page()` / `test_ghost_skill_after_agent_removed.py`'s `page.context.new_page()`.
  - Dynamic "find an unliked agent" discovery in Tab B — extend the existing `find_zero_like_application`-style idiom (ELITEA-2354) with an `is_liked`-based variant (the bulk applications response — confirmed live via `navigate_and_capture_applications()` — includes both `likes` and presumably an `is_liked`/similar field per row; verify the exact field name against a live response capture during implementation, since ELITEA-2354's helper only reads `likes`).
  - After the substituted reload in Tab A (step 8), re-call `click_category_filter_chip("My Liked")` before re-reading the section (see § Known Defects/Clarifications implementation note) — `BasePage.reload_and_wait()` handles the reload wait itself.
  - Assert cross-tab count equality by comparing `AgentHubPage(tab_b).get_like_count(app_id)` (captured in step 5, before Tab A's reload) against `AgentHubPage(tab_a).get_like_count(app_id)` (read after step 10's re-render) — use `wait_for_like_count(app_id, expected_count)` on the Tab A side for the auto-retry semantics `get_like_count`'s own docstring recommends for post-action reads.
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy) — this case needs zero NEW testids, only composition of existing `AgentHubPage` methods across two `Page` instances sharing one `BrowserContext`.
- Known-defect console assertion: same idiom as `test_agent_hub_like_agent_list_view.py`'s `_is_known_defect_1215_prefix()` helper — reuse it (or extract to a shared location if not already) rather than re-deriving the prefix string.
- Cleanup is MANDATORY (see § Cleanup) — the test must unlike the agent it liked in step 4 before ending, verified via `is_agent_liked()`/`get_like_count()` returning to the pre-test baseline (`0`). Do NOT touch the two pre-existing baseline-liked agents ("Business Analyst"/"Magic Assistant" in this environment, but read live — do not hardcode).
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.agents` (matches ELITEA-2350/2352/2354's marker set for this same page).
