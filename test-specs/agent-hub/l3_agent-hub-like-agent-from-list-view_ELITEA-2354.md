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
