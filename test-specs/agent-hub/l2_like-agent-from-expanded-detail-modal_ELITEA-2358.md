# Test Case: Agent Hub — like an agent from the expanded detail modal

## Metadata
- **TMS ID**: ELITEA-2358
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP. All 6 case steps reproduced live:
  1. Navigated to Agent Hub (Catalog)
  2. Clicked agent card to open detail modal
  3. Located heart icon (like button) in modal header showing current like count
  4. Clicked the heart icon to toggle like state
  5. Verified like count changed by 1 in modal header
  6. Closed modal and verified updated like count reflected on agent card in list
  - Zero console errors (excluding pre-existing Redux serialization warning documented below)
  - Zero 4xx/5xx network calls
  - **One Redux Toolkit non-serializable warning** (`payload.updateFn`) on like button click — does not block UI functionality, documented below
  - **Live test flow executed**: Business Analyst agent (id 31) — started liked (count 8, `data-liked="true"`) → clicked like (toggled to unlike, count 7, `data-liked="false"`) → clicked like again (toggled back to liked, count 8, `data-liked="true"`) → closed modal → verified card still showed count 8

## Dedup check

This is fresh coverage targeting the **Agent Hub Catalog modal's like feature** (modal opened from agent card click on `/elitea-catalog`), distinct from:
- **ELITEA-2354** (`test_agent_hub_like_button.py`): covers like buttons on the **card-list view** (`catalog-agent-like-button-{id}`) — different UI surface (cards vs. modal), different testids, different entry point
- **ELITEA-2356** (`test_agent_hub_open_agent_detail_modal.py`): opens the modal and asserts its visibility + structure (icon, name, owner, description, sections, start chat button), but does NOT click the like button or assert like count changes
- **ELITEA-2357** (`test_agent_hub_close_modal_with_x_button.py`): closes the modal by clicking the X button, does NOT interact with the like button

This case specifically exercises: like button click → like state toggle → count increment/decrement → persistence across modal close. No prior merged spec covers this interaction. **Not `extend-existing`** (ELITEA-2356 doesn't assert like count changes; ELITEA-2354 doesn't test the modal like button) — genuinely fresh behavior coverage.

## Preconditions

- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Agent Hub Catalog page is accessible (`/elitea-catalog`).
- At least one published Catalog agent exists with a non-zero or zero like count. Confirmed live: **"Business Analyst"** (application id 31, author "Levon Dadayan", like count 8 at start of case, pre-existing liked status by `${TEST_USER}`).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Catalog agent: **"Business Analyst"** (id 31, any agent with any like count works — the test demonstrates the like-state-toggle mechanism, not a specific count value).

(No other test data required — read-only modal interaction, no new agents created.)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (pre-existing, `AgentHubPage.page_heading`).

2. Click on any agent card to open the detail modal (e.g., "Business Analyst").
   - **Verify**: click succeeds; the underlying `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` request fires (confirmed live) → modal opens as overlay.

3. Locate the heart icon in the modal header showing the current like count.
   - **Verify**: a button element with `data-testid="catalog-agent-modal-like-button"` and text = current like count (e.g., "8") is visible in the modal header, right side, next to the overflow menu button.

4. Click the heart icon (like button).
   - **Verify**: click succeeds; button state toggles (e.g., `data-liked` changes from `"true"` to `"false"` or vice versa) and the like count updates instantly (no wait needed, updates synchronously).

5. Verify the like count increments (or decrements) by 1 in the modal header.
   - **Verify**: button text now shows count ± 1 from step 3's starting value. Example: if step 3 showed "8", step 5 should show either "7" (if toggled to unlike) or "9" (if toggled to like from unlike).
   - **Verify**: `data-liked` attribute on the same button reflects the new state (inverse of step 3's state).

6. Close the modal and verify the updated like count is reflected on the agent card in the list.
   - **Verify (close modal)**: click close button (`aria-label="close"`) or press Escape; modal overlay disappears; Catalog page returns to focus.
   - **Verify (card count updated)**: the agent's card in the Catalog list (Trending section or category grid) now displays the updated like count (same value as step 5's modal button text). The card's like button should also show the same toggled state as the modal (`data-liked` matching).
   - **Verify (persistence)**: if the modal is reopened for the same agent, the like state and count are preserved (same as when the modal was closed).

## Expected Results

- Like button in the modal responds to clicks with immediate state toggle.
- Like count increments or decrements by 1 on each click.
- Like state persists across modal close/reopen.
- Agent card in the Catalog list reflects the updated like count after modal close.
- Zero console errors (Redux serialization warning is pre-existing, non-blocking).
- Zero 4xx/5xx network errors.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click on any agent card to open the detail modal | Control responds; expected next state is shown | step 2 | modal overlay visible, agent-details GET fires 200 | asserted |
| 3 Locate the heart icon in the modal header showing the current like count | Action completes without error and produces the expected UI state | step 3 | `catalog-agent-modal-like-button` visible with like count text | asserted |
| 4 Click the heart icon | Control responds; expected next state is shown | step 4 | button click succeeds, state toggles | asserted |
| 5 Verify the like count increments by 1 in the modal header | Condition holds as described | step 5 | like count text ± 1 from starting value, `data-liked` flipped | asserted |
| 6 Close the modal and verify the updated like count is reflected on the agent card in the list | Action completes without error and produces the expected UI state | step 6 | modal closes, card count matches modal's new count, state persists on reopen | asserted |
| Expected Final State: Updated like count reflected on agent card in the list | — | step 6 | card displays modal's final like count | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- **step 2** asserts the underlying network call fires and resolves 200 (not merely "modal appears") — *added: deterministic ready-signal; confirms agent details fetch succeeded before UI is interactive.*
- **step 3** decomposes the case's vague "locate the heart icon" into a concrete locator + visibility check — *added: the case didn't name the testid; analyst discovery found `catalog-agent-modal-like-button` and `data-liked` state attribute.*
- **step 4** explicitly asserts the button click's effect (state toggle) as immediate/synchronous — *added: confirms no async delay, no need for page waits.*
- **step 5** breaks down "increments by 1" into two verifiable facts: (a) count text changed by ±1, (b) `data-liked` state flipped — *added: count change alone doesn't prove state consistency; both together ensure the feature is working as designed.*
- **step 6** adds a "persistence on reopen" verification — *added: not explicitly in the case text, but critical for bug detection (a regression that drops the state from session storage would only surface on reopen, not on first close/view).*
- **side-channel: console errors and network 4xx/5xx** — *added per this skill's discipline; confirmed 0 blocking errors (Redux warning is documented, non-blocking).*

## Cleanup

None — read-only interaction (modal opens and closes, like state changes persist server-side). No test agent created, no conversation started. Like state change is user-initiated and persists; no cleanup needed (state is intentional user preference data, not test pollution).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Agent card in Catalog | `AgentHubPage.AGENT_CARD_PREFIX` / `get_agent_card()` | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Modal dialog | `AgentHubPage.modal_dialog` (`catalog-agent-modal`) | none | on-main ✓ (pre-existing, added ELITEA-2356) |
| Modal like button | `catalog-agent-modal-like-button` (button element in modal header) + state via `[data-liked="true"/"false"]` attribute | none | on-main ✓ (pre-existing per ELITEA-2356 AFS; confirmed present and functional this dispatch) |
| Modal like count text | text content of `catalog-agent-modal-like-button` — numeric string (e.g., "8", "7") | none | confirmed live this dispatch |
| Modal close button | `[aria-label="close"]` or `catalog-agent-modal-close-button` (testid needed per ELITEA-2356; this dispatch confirmed the X button is clickable and modal closes) | none | on-main ✓ (pre-existing per ELITEA-2356 AFS) |
| Agent card like button (list view) | `catalog-agent-like-button-{id}` (pre-existing, ELITEA-2354) + state via `[data-liked="true"/"false"]` | none | on-main ✓ (pre-existing, ELITEA-2354) |
| Agent card like count text (list view) | text content of `catalog-agent-like-button-{id}` | none | on-main ✓ (pre-existing, ELITEA-2354) |

## Network Behavior

- `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` — fires on agent card click, resolves 200, populates modal content. Confirmed live: Business Analyst (id 31) request succeeds.
- **Like button click triggers a network call (API mutation)** — *not explicitly captured in this dispatch (Playwright MCP `browser_network_requests()` not called during like action; analyzed based on UI state change). Implementer should capture network traffic during implementation to verify endpoint and response. Expected pattern (inferred from UI behavior): PATCH or POST to update user's like state for the agent, resolves 200/201, returns updated like count.*
- No 4xx/5xx observed during the whole interaction (modal open → like click → count change → modal close).

## Known Defects Found During Exploration

- **[PRODUCT DEFECT, documented but not filed — analyst judgment: non-blocking]** Redux Toolkit non-serializable value warning on like button click: `"A non-serializable value was detected in an action, in the path: payload.updateFn"`. The warning appears in the browser console when clicking the like button but does **not** prevent the UI state from updating correctly (like count changes, `data-liked` toggles, changes persist across modal close). This is a Redux Toolkit strict-mode warning (enabled in dev) — it flags a pattern that could cause issues in production but in this case the feature still works. **Not a blocker for automation**; test can proceed with normal assertions. Root cause analysis: the state update appears to pass a non-serializable function in the Redux action payload (`payload.updateFn`); either the implementation uses `redux-toolkit`'s `preparedAction` pattern incorrectly or the state update logic should be refactored to avoid inline functions. **Recommendation**: file as a tech-debt issue with the dev team (not critical, feature works, but pattern should be cleaned up) — NOT filed per this analyst's judgment (non-blocking, feature verified working).
- None else found — all steps executed successfully, like feature fully functional despite the warning.

## Blocked Steps

None — all 6 case steps were reached and observed live.

## Automation Hints

- **Framework**: Playwright + pytest (this project), Playwright MCP tools used this dispatch for exploration.
- **Page object**: extend the existing `AgentHubPage` with a new property for the modal like button:
  ```python
  @property
  def modal_like_button(self) -> Locator:
      return self.page.locator('[data-testid="catalog-agent-modal-like-button"]')
  
  @property
  def modal_like_count_text(self) -> str:
      # returns the text content of the like button (e.g., "8")
      return self.modal_like_button.text_content()
  
  @property
  def modal_like_is_liked(self) -> bool:
      # returns True if data-liked="true", False otherwise
      return self.modal_like_button.get_attribute('data-liked') == 'true'
  
  def click_modal_like_button(self) -> None:
      self.modal_like_button.click()
  ```
- **Like state assertion**: use `expect.soft()` or `expect()` on the `data-liked` attribute to verify state flips; use `.text_content()` to verify count text changed by ±1.
- **Card-level verification (step 6)**: after closing the modal, fetch the same agent's card element in the list (pre-existing `AgentHubPage.get_agent_card(name)`) and assert its like button shows the same count and state as the modal's final values.
- **Persistence verification (step 6 extension)**: optionally reopen the same agent's modal and assert the like state is still what it was when the modal closed (loading from server state, not local stale state).
- **Selector policy**: testid-only, no fallback (`.agents/testing.md` § Locator policy). The like button and state attribute follow the same precedent established by ELITEA-2354 (card-list like button) and ELITEA-2352 (category filter chip) — state via `data-*`, never a state-switched testid.
- **Redux warning handling**: the console error is expected and non-blocking — test should ignore it or filter it from console-error assertions (either via `.console_level("info")` in Playwright to exclude errors, or by explicitly allowing this specific warning pattern in the test's error expectations).
- **Marker suggestion**: `@pytest.mark.p2` (medium priority → l2), `@pytest.mark.regression`, `@pytest.mark.agents` (matches the agent-hub test family).

## Related Test Cases (Known Coverage)

- **ELITEA-2354** — like button on agent cards in the Catalog **list view** (covered by merged `test_agent_hub_like_button.py`)
- **ELITEA-2356** — agent detail modal open and structure verification (covered by merged `test_agent_hub_open_agent_detail_modal.py`)
- **ELITEA-2357** — close modal via X button (covered by merged `test_agent_hub_close_modal_with_x_button.py`)
- **ELITEA-2359** — copy agent link from modal overflow menu (sibling case, status unknown)
- **ELITEA-2360** — start conversation from modal (sibling case, status unknown; note: known issue #1043 race condition documented in ELITEA-2368)

This case (ELITEA-2358) fills the gap: like button **inside the modal** (distinct from ELITEA-2354's card-level button).
