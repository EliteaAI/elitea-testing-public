# Test Case: Agent Hub — close agent detail modal with X button

## Metadata
- **TMS ID**: ELITEA-2357
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: high → medium execution priority)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright; all 6 steps reproduced and verified (screenshots: `test-results/screenshots/ELITEA-2357-step-03-modal-open.png`, `test-results/screenshots/ELITEA-2357-step-06-modal-closed.png`). Zero console errors, zero 4xx/5xx. All required testids confirmed present on `automation/testids` (close button is the ONLY new element; its testid was added in ELITEA-2356 work). No fallback-worthy gaps per project locator policy.
- **Related surfaces reused**: `AgentHubPage` (`automation/pages/agent_hub_page.py`) and the prerequisite `open_agent_by_name()` method (ELITEA-2356). The close button testid is already defined as `modal_close_button` in the page object (added by ELITEA-2356 implementer, `catalog-agent-modal-close-button`). This case adds exactly ONE method to the page object: `close_modal()` — a wrapper around `modal_close_button.click()` with optional animation wait.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- At least one published Catalog agent exists and its preview modal is already open. Confirmed live: **"User Story Creator"** (application id 172, author "Levon Dadayan", description "Thuis agent is responsible for creating proper user stories accordingly using provided user_template.md which is included in sub-agent." [sic — author-authored typo in live product data]). Matches the case's own "e.g." example for opening the modal (ELITEA-2356 prerequisite).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Catalog agent: **"User Story Creator"** (application id 172) — reused from ELITEA-2356 prerequisite.

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible. Reuse `AgentHubPage.navigate()`.

2. Click on any agent card to open the detail modal (e.g., "User Story Creator").
   - **Verify**: click succeeds; the underlying `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` request fires and resolves. Reuse `AgentHubPage.open_agent_by_name()` (already waits on this exact response).

3. Verify the agent detail modal is displayed as an overlay.
   - **Verify**: a MUI `Dialog` (`role="dialog"`) becomes visible over the Catalog page content — confirmed live. Check `catalog-agent-modal` testid visibility (locator: `modal_dialog` in page object).

4. Click the X button in the top-right corner of the modal.
   - **Verify**: the X button (close `IconButton`, `aria-label="close"`) is visible and clickable — confirmed live, testid `catalog-agent-modal-close-button` (locator: `modal_close_button` in page object). Clicking it fires no errors to console.

5. Verify the modal closes.
   - **Verify**: the modal overlay transitions to hidden state (`state="hidden"`) within 1000ms after the close button click — confirmed live. No errors during transition.

6. Verify the user remains on the Agent Hub list view.
   - **Verify**: the page URL remains `/elitea-catalog`; the catalog page heading (`catalog-page-heading`) remains visible; the catalog content area (agent cards / category sections) is still rendered — confirmed live. Zero console errors throughout the interaction.

## Expected Results
- Clicking the X button in the agent detail modal closes the modal.
- The modal transitions to hidden state cleanly.
- The user remains on the Agent Hub / Catalog list view (`/elitea-catalog`).
- The Catalog page heading, search bar, and agent card grid remain visible and interactive.
- Zero console errors, zero 4xx/5xx responses.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click on any agent card | Control responds; expected next state is shown | step 2 | agent-details GET fires, resolves 200 | asserted |
| 3 Verify the agent detail modal opens as an overlay | Condition holds as described | step 3 | `catalog-agent-modal` visible | asserted |
| 4 Click the X button in the top-right corner of the modal | Control responds; expected next state is shown | step 4 | `catalog-agent-modal-close-button` visible and clickable | asserted |
| 5 Verify the modal closes | Condition holds as described | step 5 | `catalog-agent-modal` hidden (state transition observed live) | asserted |
| 6 Verify the user remains on the Agent Hub list view | Condition holds as described | step 6 | page URL remains `/elitea-catalog`, `catalog-page-heading` and agent cards remain visible | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- **step 5** adds an explicit wait for the modal's `state="hidden"` transition with a 1000ms timeout — *added: CSS animations in MUI Dialogs take ~300ms to fade out; waiting on the state transition (not just a timeout) ensures the modal is truly gone, not just invisible mid-animation, catching any regression in the close flow that left the modal in a limbo state.*
- **step 6** asserts zero console errors during the entire close interaction — *added: standard side-channel regression guard per this skill's discipline (confirmed live: 0 errors during open + click + close).*
- (nothing else added beyond the case's own 6 steps.)

## Cleanup

None — read-only modal close interaction. No state created. No agent liked, no conversation started, no navigation away from Catalog. The page remains on `/elitea-catalog` after the test, in its pre-modal state.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` / `get_agent_card()` (`[data-testid^="catalog-agent-card-"]`) | none | on-main ✓ (pre-existing, ELITEA-2075) |
| Modal overlay root (dialog panel) | `AgentHubPage.modal_dialog` (`catalog-agent-modal`) | none | added by ELITEA-2356 implementer — on `automation/testids` ✓ (pushed EliteaAI/EliteaUI@b0dc74c0/@46586f2d), **not yet on `main`** (awaiting human cherry-pick) |
| Modal close ("x") button | `AgentHubPage.modal_close_button` (`catalog-agent-modal-close-button`) | none | added by ELITEA-2356 implementer — on `automation/testids` ✓ (pushed EliteaAI/EliteaUI@b0dc74c0/@46586f2d), **not yet on `main`** (awaiting human cherry-pick) |

## Network Behavior
- No new network requests fire during the close button click (the close action is purely UI state — Redux dispatch via `handleClose()` → `setOpenModal(false)`). Confirmed live: the Network tab shows zero additional requests after the click.
- No 4xx/5xx observed during the entire open-and-close flow.

## Known Defects Found During Exploration
None — case executed end-to-end without defects. All six steps reproduced live. Zero console errors, zero 4xx/5xx, no product bugs preventing automation. Modal opens correctly (ELITEA-2356 prerequisite), close button is functional and accessible, modal closes cleanly and transitions to hidden state, user remains on Catalog page.

## Blocked Steps
None — all 6 case steps were reached and observed live. The close button testid was confirmed to exist (added in ELITEA-2356 work); its presence is not a blocker.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools verified this dispatch.
- **No new page object fields needed** — the `modal_close_button` locator already exists in `AgentHubPage` (added by ELITEA-2356 implementer). **Add ONE method to the page object:** `close_modal(timeout: int = 10000)` — a simple wrapper that calls `self.modal_close_button.click()` and waits for the modal to transition to hidden via `self.modal_dialog.wait_for(state="hidden", timeout=timeout)`. Document it with `@action()` decorator per existing pattern.
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy). The modal and close button are both pre-existing testids from ELITEA-2356; no new testids needed.
- Flow: This case is a strict prerequisite → action → verify closure sequence with no branches or conditionals. Automation is straightforward.
- **Reuse pathway (recommended):** Open the modal via `AgentHubPage.open_agent_by_name()` (already handles Catalog navigation and modal wait), then call the new `close_modal()` method, then assert Catalog page is still visible.
- Marker suggestion: `@pytest.mark.p2` (high priority → medium automation priority, per case priority field), `@pytest.mark.regression`, `@pytest.mark.agents` (matches the rest of this family's marker set).
- Animation timing: the modal's CSS fade-out transition is ~300ms (MUI Dialog default); the `wait_for(state="hidden")` call waits up to 1000ms and will return as soon as the browser's state matches "hidden", typically within 300-500ms of the close click.

## Promotion Status

**Testids on `automation/testids` (Dev server sees them):**
- `catalog-agent-modal` (modal dialog) ✓
- `catalog-agent-modal-close-button` (close X button) ✓

**Testids NOT YET on `main` (awaiting human cherry-pick from `automation/testids`):**
- Both testids listed above are pushed to the integration branch; a human will cherry-pick them to EliteaUI `main` out of band.

**Promotability:** This case can run green on localhost immediately (dev server runs `automation/testids`). Promotion to `main` and then to deployed envs (dev.elitea.ai, etc.) requires the human's cherry-pick of the two testids from ELITEA-2356's work. Once those land on `main`, this case becomes deployable-env-green.

---

## References

- **Prerequisite case:** [ELITEA-2356](https://github.com/EliteaAI/elitea-testing-public/issues/863) — Agent Hub — open agent detail modal (provides the modal-open flow, modal dialog testid, and close button testid).
- **Case text note:** Case title says "close agent detail modal with X button"; the live product uses a `MUI Dialog` with an `aria-label="close"` `IconButton` at the top-right, functionally equivalent to an "X" button. Automation asserts the live implementation.
- **Related surfaces:** `AgentHubPage` (`automation/pages/agent_hub_page.py`) — all handles and navigation methods.
- **Locator policy:** `.agents/testing.md` § Locator policy (testid-only, no fallback ladder).
