# Test Case: LLM selector — Anthropic models are available and functional (Claude 4.5 Sonnet, Claude 4.6 Sonnet, Claude Haiku 4.5)

## Metadata
- **TMS ID**: ELITEA-1881
- **Linked Story**: none
- **Priority**: l2 (source case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids` → DEV backend, project `Private` id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skip-login via `VITE_DEV_TOKEN`, user `project_user_659`)
- **Analyst**: qa-engineer (agent), 2026-07-16
- **Status**: **ready-for-automation** — executed end-to-end live. All 8 case steps completed, no blockers, no defects. One testid gap was found and remediated during execution (see below).

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via `auth_state`/`VITE_DEV_TOKEN` — no Keycloak login step needed in this environment).
- An existing agent is available (used the pre-existing "Test Agent", `agent id 3`, `version id 3`, in project `Private`/399 — any agent with an embedded chat panel works; no need to create one per run, though automation may prefer a dedicated `generate-per-test` agent to avoid mutating shared fixture state — see § Automation Hints).
- Anthropic models are configured in the platform — **confirmed live**: `GET /api/v2/configurations/models/399?include_shared=true` returns all 3 target models (see § Network Behavior for exact `name`/`display_name` values).

## Test Data
### reuse-existing
- Agent: existing "Test Agent" (id `3`), project `Private` (`399`) — reused for this exploration pass; see Automation Hints re: whether the implementer should isolate this into a dedicated fixture agent instead.

### generate-per-test (in test setup, cleaned up in its own teardown)
- None required beyond the reused agent, but automation SHOULD restore/reset the agent's selected model to its original value (`GPT-5.4-mini` at time of exploration) in teardown, since Step 4/7/8 (Save) mutates persisted agent state via `PUT /api/v2/elitea_core/application/prompt_lib/399/3`. Alternatively, create a disposable agent per test run and delete it in teardown — cleaner, avoids any cross-test/cross-analyst races on a shared fixture agent.

### Test message / expected response (verbatim per case Test Data table)
- Test message: `"Reply only with: CONFIRMED"`
- Expected response: contains `"CONFIRMED"`

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}` (agent detail page)
   - **Verify**: agent detail page loads — form sections (General, Instructions, Tools, Skills, Advanced, …) and the embedded chat panel are both visible.
   - **OBSERVED**: page loaded at `/agents/all/3?viewMode=owner&name=Test%20Agent`; chat panel visible on the right with a model selector reading `GPT-5.4-mini`.
2. Click the model selector dropdown (`model-selector-name`, inside `model-selector-button` group)
   - **Verify**: dropdown menu opens.
   - **OBSERVED**: `menu` with 11 `menuitem` entries opened (accessible names include the model display name plus capability chip text, e.g. `"Anthropic Claude 4.5 Sonnet Supports reasoning"`).
3. Verify all three Anthropic models are present in the dropdown
   - **Verify**: `Claude 4.5 Sonnet`, `Claude 4.6 Sonnet`, `Claude Haiku 4.5` all listed.
   - **OBSERVED**: all three present, with the platform's vendor-prefixed display names — `"Anthropic Claude 4.5 Sonnet"`, `"Anthropic Claude 4.6 Sonnet"`, `"Anthropic Claude Haiku 4.5"`. (The "Anthropic " prefix is not in the case's Test Data table but is the live, correct display text — case text is shorthand, not a defect; see Coverage Map row.) A 4th Anthropic-family model, `"Anthropic Sonnet 5"`, is also present but out of scope for this case (case only names the 3).
4. Select "Claude 4.5 Sonnet" and click Save
   - **Verify**: Save completes successfully.
   - **OBSERVED**: clicking the menu item sets the chat-panel model selector to "Anthropic Claude 4.5 Sonnet" and enables the previously-disabled top-toolbar `agent-save-button`. Clicking Save fires `PUT /api/v2/elitea_core/application/prompt_lib/399/3` → **201 Created**; Save/Discard buttons return to `disabled` (clean state), confirming persistence.
5. Open the embedded chat panel and send the test message
   - **Verify**: message is sent.
   - **OBSERVED**: chat panel is already embedded/visible on the agent detail page (not a separate navigation) — typed into `chat-message-input` and submitted via Enter. Message appears in the transcript immediately.
6. Verify the response contains "CONFIRMED"
   - **Verify**: agent response contains "CONFIRMED".
   - **OBSERVED**: response bubble appeared ~2–15s after send (see § Automation Hints re: wait budget), labeled with the responding model name (`"Anthropic Claude 4.5 Sonnet"` shown above the response text) and body text `"CONFIRMED"`. Evidence: `test-results/screenshots/ELITEA-1881-step-model1-confirmed.png`.
7. Repeat steps 4–6 for "Claude 4.6 Sonnet"
   - **Verify**: selected, saved, responds with "CONFIRMED".
   - **OBSERVED**: model selector → "Anthropic Claude 4.6 Sonnet" → Save → `PUT .../application/1` → 201 Created → message sent → response labeled "Anthropic Claude 4.6 Sonnet" → body "CONFIRMED". Evidence: `test-results/screenshots/ELITEA-1881-step-model2-confirmed.png`.
8. Repeat steps 4–6 for "Claude Haiku 4.5"
   - **Verify**: selected, saved, responds with "CONFIRMED".
   - **OBSERVED**: model selector → "Anthropic Claude Haiku 4.5" → Save → `PUT .../application/399/3` → 201 Created → message sent → response labeled "Anthropic Claude Haiku 4.5" → body "CONFIRMED". Evidence: `test-results/screenshots/ELITEA-1881-step-model3-confirmed.png`.

## Expected Results
- All three Anthropic models (`Claude 4.5 Sonnet`, `Claude 4.6 Sonnet`, `Claude Haiku 4.5`) are present in the LLM model selector dropdown on the agent detail page.
- Each model can be selected and persisted via the top-toolbar Save action (`PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` → 201).
- Each model, once selected+saved, produces a response containing "CONFIRMED" in the embedded chat panel when sent the literal test message.
- No console errors or warnings at any point in the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | N/A (env-level) | `auth_state` fixture / `VITE_DEV_TOKEN` | asserted (env precondition, not a runtime step) |
| Precondition: existing agent available | — | N/A | reused "Test Agent" id 3 | asserted |
| Precondition: Anthropic models configured | — | step 3 | `GET /api/v2/configurations/models/399` response body contains all 3 target `name`s | asserted |
| 1 Navigate to agent detail page | page loads | step 1 | `step 1`: form sections + chat panel visible | asserted |
| 2 Click model selector dropdown | dropdown opens | step 2 | `step 2`: `menu` with menuitems visible | asserted |
| 3 Verify all 3 Anthropic models present | all 3 listed | step 3 | `step 3`: 3 `model-selector-option-{name}` testids present, display names match (with "Anthropic " prefix — see clarification below) | asserted, **clarification** on exact display-name text |
| 4 Select Claude 4.5 Sonnet + Save | save completes | step 4 | `step 4`: `PUT .../application/.../.` → 201; Save button returns to disabled | asserted |
| 5 Open chat panel, send test message | message sent | step 5 | `step 5`: message bubble appears in transcript | asserted |
| 6 Verify response contains CONFIRMED | response contains CONFIRMED | step 6 | `step 6`: response paragraph text === "CONFIRMED" | asserted |
| 7 Repeat 4–6 for Claude 4.6 Sonnet | selected, saved, CONFIRMED | step 7 | `step 7`: same triad of assertions | asserted |
| 8 Repeat 4–6 for Claude Haiku 4.5 | selected, saved, CONFIRMED | step 8 | `step 8`: same triad of assertions | asserted |

**Clarification (case-text drift, not a defect):** the case's Test Data table names the models as `Claude 4.5 Sonnet` / `Claude 4.6 Sonnet` / `Claude Haiku 4.5` (no vendor prefix). The live dropdown displays them as `Anthropic Claude 4.5 Sonnet` / `Anthropic Claude 4.6 Sonnet` / `Anthropic Claude Haiku 4.5` — the platform prefixes every model's display name with its vendor (confirmed: `Azure Claude Sonnet 4.5`, `GPT-5.4-mini` etc. follow the same pattern). This is correct, current product behavior — the case text is shorthand. Automation should assert against the live, vendor-prefixed display name. Filed as a CLARIFICATION note here per the reverse-masking guard (`test-case-analysis` SKILL.md § Classify findings); no tracker ticket needed — this AFS is the record, and the discrepancy is cosmetic/self-evident, not a behavioral gap.

### Axis 2 — Analyst additions (beyond the case)

- `step 4/7/8` asserts the underlying `PUT` request returns `201 Created` (not just that the UI *looks* saved) — *added: the UI's only visible save signal is the Save/Discard buttons returning to disabled state, which could mask a silent failed request; the network assertion is the stronger, non-flaky proof of persistence.*
- `step 6/7/8` asserts the response is attributed to the *correct* model name in the transcript (e.g. "Anthropic Claude 4.6 Sonnet" shown above the CONFIRMED text for step 7) — *added: the case's Pass criterion only checks the response text, but attributing each response to the wrong model would be a silent regression the case as written wouldn't catch.*
- Console-message check (0 errors/warnings) across the full 8-step flow — *added: standard side-channel discipline per `test-case-analysis` SKILL.md; the widget renders fine even when console-level errors are present, so this is the only way to catch a silent JS error.*
- (No assertions beyond these were added.)

## Cleanup
1. If automation creates a dedicated agent for this case (recommended — see Automation Hints), delete it via `DELETE /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` in teardown.
2. If automation reuses a shared fixture agent instead, restore its LLM selection to the pre-test value (`GPT-5.4-mini` at time of exploration) and Save, to avoid leaking state into other tests/analysts sharing the same agent.
3. No conversation/chat cleanup needed — conversations are scoped to the agent and don't require separate teardown per existing project convention (see other agent chat specs in `test-specs/agents/`).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Model selector button (whole group) | `getByTestId('model-selector-button')` | none — testid-only project policy |
| Model selector button (opens menu, shows current selection) | `getByTestId('model-selector-name')` | none |
| Model dropdown menu item, per model | `getByTestId('model-selector-option-{model_name}')` — dynamic, `model_name` = the model's stable API `name` field (e.g. `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`, `eu.anthropic.claude-sonnet-4-6`, `eu.anthropic.claude-haiku-4-5-20251001-v1:0`) — **newly added during this analysis pass, see below** | none |
| Agent Save button (top toolbar) | `getByTestId('agent-save-button')` | none |
| Chat message input | `getByTestId('chat-message-input')` | none |
| Chat response text (per message) | scope to the last `listitem` in the transcript list, then read its paragraph text — **no testid found on individual response bubbles/paragraphs; flagged, not remediated (see Automation Hints)** | `page.locator('[role="listitem"]').last()` scoped to the chat transcript region, then `.getByRole('paragraph')` — acceptable per-scoped fallback since no stable testid exists yet on the response bubble itself |
| Chat response's attributed model name | same transcript `listitem`, the small text row above the response body (e.g. "Anthropic Claude 4.5 Sonnet") — **no testid**, same flag as above | text content of the region directly above the response paragraph, scoped to the same `listitem` |

**Testid gap found + remediated during this analysis pass:** `LLMModelsMenu.jsx`'s `<MenuItem>` (the dropdown's model options) had **no testid** — selecting a specific model required a fragile accessible-name locator (`getByRole('menuitem', { name: 'Anthropic Claude 4.5 Sonnet' })`), which also matches unrelated chip text ("Supports reasoning" / "Supports image analysis") baked into the same accessible name. Added `data-testid={`model-selector-option-${item.name}`}` to the `MenuItem` in `EliteaUI/src/[fsd]/widgets/llm-model-selector/ui/LLMModelsMenu.jsx`, using the model's stable API `name` field as the dynamic suffix (verified unique per the `GET /api/v2/configurations/models/399` response). Verified live via Vite HMR (`document.querySelector('[data-testid^="model-selector-option-"]')` returned the expected testid). Committed + pushed straight to `automation/testids` (commit `0b058c94`, message `test: [EL-0000] add data-testid for LLM model selector menu options (ELITEA-1881)`) per current EliteaUI testid-workflow policy — no separate PR opened; a human cherry-picks to `main` when ready.

**Not remediated (flagged only):** the individual chat message/response bubbles (both the user's sent message and the agent's response) have no testid on their container or on the response's model-attribution label. This wasn't in scope to fix for this case (the case only needs to read text content, not click into a specific message), but future chat-history-assertion cases will hit the same locator fragility. Flagging for the lead / next `add-data-testid` pass rather than scope-creeping this case's remediation.

## Network Behavior
- `GET /api/v2/configurations/models/{project_id}?include_shared=true` — fires on chat-panel mount / model-selector interaction; response `items[]` contains `name` (stable API model id, e.g. `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`) and `display_name` (UI text, e.g. `Anthropic Claude 4.5 Sonnet`) for all configured models, Anthropic and otherwise. Confirmed 11 models total at analysis time, including all 3 case targets plus a 4th Anthropic model (`Anthropic Sonnet 5`) not named in the case.
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` — fires on Save click after a model change; **201 Created** on success. This is the assertion point for "Save completes successfully" (steps 4/7/8) — don't rely solely on the Save button's disabled state, confirm the response status.
- The chat send/response cycle rides the project's existing WebSocket transport (per `.agents/testing.md` — "AI responses arrive over WebSocket with ~2s delay"). No new REST endpoint to note beyond the initial message-send; the response arrives async over the existing socket. See § Automation Hints for wait-budget guidance — this case's per-model round trip took 2–15s observed, well within a generous wait but notably variable across the 3 models (Haiku responded in <1s "thought" time on the 3rd call, Sonnet models took ~2s).

## Known Defects Found During Exploration
None found. All 3 models present, selectable, saveable (201 on each PUT), and each returned a "CONFIRMED" response correctly attributed to the selected model. Zero console errors/warnings across the full 8-step flow (3 full model-select/save/chat cycles).

## Blocked Steps
None. All 8 case steps executed to completion with no blockers.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Page object candidates: extend/add to whatever existing agent-detail page object covers the chat panel (grep `automation/pages/` for the agent-detail page object — `chat_page.py` already references model-select concerns per a prior grep during this analysis, worth checking for overlap/reuse before adding new methods).
- **Wait strategy — this case needs a more generous budget than the project default.** Sending a real chat message and awaiting a live LLM response is inherently slower and noisier than typical UI assertions. `.agents/testing.md` calls out "~2s delay" for the WebSocket transport generally, but that's for message *delivery*, not full LLM inference — observed round trips here ranged ~2–15s per model, and this is 3 independent live LLM calls (one per model) in a single test. Recommendations:
  - Use a condition-based wait (`wait_for` on the response text/selector appearing), never a fixed `sleep()` — consistent with project convention.
  - Set an explicit timeout override of at least 60s per response wait (vs. whatever the project's default UI-assertion timeout is) to absorb LLM latency variance without flaking. Confirm the exact default in `automation/config.py` / `conftest.py` and override per-call rather than globally.
  - Because this test drives 3 full model-cycles serially (select → save → send → await-response, ×3), total runtime will be materially longer than a typical UI test (observed ~2 minutes wall-clock for the exploration pass, including manual snapshot overhead — a clean automated run should be faster but still likely 30–90s). Consider marking it `slow` and/or `regression` (not `smoke`) per the project's marker conventions in `.agents/testing.md` § Markers.
- **Live API/cost/quota note:** this case makes 3 real calls to live Anthropic-backed models (via the platform's LLM proxy) every run. No quota/availability issues were hit during this analysis pass (Anthropic 5, Azure Claude variants, and GPT models were also available/selectable in the same dropdown, suggesting the backend has broad multi-provider config), but the implementer/CI owner should be aware this test has a real inference cost per run and depends on 3 live upstream models being available — consider whether `regression`-suite cadence (not run on every commit) is appropriate, per however this project gates LLM-cost-bearing tests elsewhere (check for a similar existing pattern in `automation/tests/ui/chat/` or `automation/tests/ui/skills/test_skill_conversation_interaction.py`, which also drive live chat).
- Consider whether to isolate this case onto a dedicated per-test agent (create+delete in fixture) rather than reusing a shared fixture agent — the shared "Test Agent" used during this exploration is likely also touched by other agents/specs; mutating its selected LLM model across 3 test runs could race with parallel test execution (`pytest-xdist` is in the stack per `.agents/testing.md`).
- New testid `model-selector-option-{model_name}` is live on `automation/testids` (commit `0b058c94`) — confirmed via Vite HMR during this session, no restart needed to consume it in a new test.
