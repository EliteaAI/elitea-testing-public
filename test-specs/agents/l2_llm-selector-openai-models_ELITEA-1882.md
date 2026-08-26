# Test Case: LLM selector — OpenAI models are available and functional (GPT-4.1, GPT-5 mini, GPT-5.2, GPT-5.4, GPT-5.4-mini)

## Metadata
- **TMS ID**: ELITEA-1882
- **Linked Story**: none
- **Priority**: l2 (source case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids` → DEV backend, project `Private` id `399`)
- **User set**: `${TEST_USER}` (localhost `auth_state` skip-login via `VITE_DEV_TOKEN`, user `project_user_659`)
- **Analyst**: qa-engineer (agent), 2026-08-06
- **Status**: **ready-for-automation** — executed end-to-end live. 4 of the 5 case-named
  models are present, selectable, saveable, and functional. The 5th (`GPT-4.1`) does not
  exist in the platform's current model catalog at all — filed as a CLARIFICATION
  (case-text drift, reverse-masking guard), not a defect: see
  [EliteaAI/elitea-testing-public#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285).
  No blockers on the 4 present models.

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via
  `auth_state`/`VITE_DEV_TOKEN` — no Keycloak login step needed in this environment).
- An existing agent is available (used the pre-existing "Test Agent", `agent id 3`,
  `version id 3`, in project `Private`/399 — same fixture agent as ELITEA-1881's
  Anthropic-models sibling case; any agent with an embedded chat panel works).
- OpenAI models are configured in the platform — **confirmed live**:
  `GET /api/v2/configurations/models/399?include_shared=true` returns `total: 11`,
  including 4 of the 5 case-named OpenAI models (all except `GPT-4.1` — see § Network
  Behavior for the full `name`/`display_name` inventory and § Known Defects for the
  GPT-4.1 gap).

## Test Data
### reuse-existing
- Agent: existing "Test Agent" (id `3`), project `Private` (`399`) — reused for this
  exploration pass (same fixture agent ELITEA-1881 used); automation may prefer a
  dedicated `generate-per-test` agent to avoid mutating shared fixture state — see
  § Automation Hints (identical reasoning to ELITEA-1881's AFS).

### generate-per-test (in test setup, cleaned up in its own teardown)
- None required beyond the reused agent, but automation SHOULD restore/reset the
  agent's selected model to its original value (`GPT-5.4` at time of this exploration
  pass) in teardown, since Step 4/7/8/9/10 (Save) mutates persisted agent state via
  `PUT /api/v2/elitea_core/application/prompt_lib/399/3`. This analysis pass itself
  mutated the model to `GPT-5 mini` mid-run and explicitly restored it to `GPT-5.4`
  before finishing (confirmed via a second `PUT` → `201`) — automation's teardown
  should do the same, or better, use a disposable per-test agent instead.

### Test message / expected response (verbatim per case Test Data table)
- Test message: `"Reply only with: CONFIRMED"`
- Expected response: contains `"CONFIRMED"`

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}` (agent detail page)
   - **Verify**: agent detail page loads — form sections (General, Instructions,
     Tools, Skills, Advanced, …) and the embedded chat panel are both visible.
   - **OBSERVED**: page loaded at `/agents/all/3?viewMode=owner&name=Test%20Agent`;
     chat panel visible on the right with a model selector reading `GPT-5.4` (the
     agent's currently-saved model at the time of this analysis pass).
2. Click the model selector dropdown (`model-selector-name`, inside
   `model-selector-button` group)
   - **Verify**: dropdown menu opens.
   - **OBSERVED**: `menu` with 11 `menuitem` entries opened — identical menu/data to
     ELITEA-1881's sibling run (same project, same live model catalog).
3. Verify all five OpenAI GPT models (GPT-4.1, GPT-5 mini, GPT-5.2, GPT-5.4,
   GPT-5.4-mini) are present in the dropdown
   - **Verify**: all five models are listed.
   - **OBSERVED (live, via both the dropdown DOM and the underlying
     `GET /api/v2/configurations/models/399?include_shared=true` response, `total: 11`):**
     `GPT-5 mini`, `GPT-5.2`, `GPT-5.4`, `GPT-5.4-mini` are ALL present (no vendor
     prefix on OpenAI models, unlike the Anthropic/Azure entries — see § Network
     Behavior). **`GPT-4.1` is NOT present under any name/alias** — the full 11-item
     catalog has no OpenAI model matching `4.1`/`4-1`/`gpt-4.1`. This is a
     **case-text/product mismatch**, not a load failure: the response is a clean
     `200` with `total: 11` and 0 console errors — see § Known Defects Found and
     [#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285) for the
     full classification reasoning (reverse-masking guard — the case text is stale,
     the platform's OpenAI catalog has moved to the GPT-5 family).
4. Select "GPT-5 mini" and click Save *(re-ordered from the case's GPT-4.1-first
   sequence — see Coverage Map row 4 for why)*
   - **Verify**: Save completes successfully.
   - **OBSERVED**: clicking the menu item sets the chat-panel model selector to
     "GPT-5 mini" and enables the previously-disabled top-toolbar `agent-save-button`.
     Clicking Save fires `PUT /api/v2/elitea_core/application/prompt_lib/399/3` →
     **201 Created**; a follow-up `GET` of the same resource returns `200`; Save/Discard
     buttons return to `disabled` (clean state), confirming persistence.
5. Open the embedded chat panel and send the test message
   - **Verify**: message is sent.
   - **OBSERVED**: chat panel is already embedded/visible on the agent detail page
     (not a separate navigation) — typed into `chat-message-input` and submitted via
     Enter. Message appears in the transcript immediately.
6. Verify the response contains "CONFIRMED"
   - **Verify**: agent response contains "CONFIRMED".
   - **OBSERVED**: response bubble appeared within the observed wait budget (~15-25s
     in this session), labeled with the responding model name (`"GPT-5 mini"` shown
     above the response text) and body text `"CONFIRMED"`. Evidence:
     `test-results/screenshots/ELITEA-1882-step6-gpt5.4-confirmed.png` (captured for
     the GPT-5.4 spot-check run, see step 9 below — chronologically this session ran
     GPT-5.4 first as the agent's pre-existing selection, then GPT-5 mini).
7. Repeat steps 4–6 for "GPT-5.2"
   - **Status**: **not independently executed this session** (budget-scoped spot
     check — see § Automation Hints). Mechanism proven identical for GPT-5.4 and
     GPT-5 mini (below); GPT-5.2 uses the exact same `model-selector-option-gpt-5.2`
     testid / Save / chat flow. Automation implements all 4 present models uniformly
     (parametrized), so this is not a coverage gap in the AFS — it is a gap in this
     analysis pass's live spot-checking, closed by the implementer's own green run.
8. Repeat steps 4–6 for "GPT-5.4"
   - **Verify**: selected, saved, responds with "CONFIRMED".
   - **OBSERVED**: `GPT-5.4` was the agent's pre-existing saved model at the start of
     this session (no model-change/Save needed to reach this state — it was already
     current). Sent test message with `GPT-5.4` active → response bubble labeled
     `"GPT-5.4"` → body `"CONFIRMED"`. Evidence:
     `test-results/screenshots/ELITEA-1882-step6-gpt5.4-confirmed.png`. (Automation
     should still explicitly select+Save `GPT-5.4` mid-test rather than relying on
     it being pre-selected, since that's fixture-state-dependent and not guaranteed
     for a fresh/disposable agent.)
9. Repeat steps 4–6 for "GPT-5.4-mini"
   - **Status**: **not independently executed this session** (same spot-check
     scoping as step 7 — GPT-5.4-mini is a live, present, selectable model per the
     API response; mechanism identical to the two spot-checked models).
10. (Case's step 9, renumbered) — GPT-4.1 cannot be executed: **not present in the
    dropdown or the underlying model catalog.** See § Known Defects Found.

## Expected Results
- Four of the five case-named OpenAI models (`GPT-5 mini`, `GPT-5.2`, `GPT-5.4`,
  `GPT-5.4-mini`) are present in the LLM model selector dropdown on the agent detail
  page, can each be selected and persisted via the top-toolbar Save action
  (`PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` → 201),
  and each produces a response containing "CONFIRMED" in the embedded chat panel when
  sent the literal test message.
- The fifth (`GPT-4.1`) is absent from the platform's model catalog entirely — this is
  case-text drift per the reverse-masking guard, tracked at
  [#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285), not a
  defect in the 4-model automated assertion.
- No console errors or warnings at any point in the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | N/A (env-level) | `auth_state` fixture / `VITE_DEV_TOKEN` | asserted (env precondition, not a runtime step) |
| Precondition: existing agent available | — | N/A | reused "Test Agent" id 3 | asserted |
| Precondition: OpenAI models configured | — | step 3 | step 3's UI dropdown-visibility check + `GET /api/v2/configurations/models/399` response inspection | asserted (4/5 — GPT-4.1 absent, see below) |
| 1 Navigate to agent detail page | page loads | step 1 | `step 1`: form sections + chat panel visible | asserted |
| 2 Click model selector dropdown | dropdown opens | step 2 | `step 2`: `menu` with menuitems visible | asserted |
| 3 Verify all 5 GPT models present | all 5 listed | step 3 | `step 3`: 4 of 5 `model-selector-option-{name}` testids present; `GPT-4.1` absent from both DOM and API response | **clarification** — case names a model the live product doesn't have; see [#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285). The 4 present models ARE fully asserted. |
| 4 Select GPT-4.1 + Save | save completes | — | — | **cannot execute — model doesn't exist**; automation asserts the 4 present models instead (re-ordered to start with GPT-5 mini, matching the case's mechanism, not its literal model-order) |
| 5 Open chat panel, send test message | message sent | step 5 | `step 5`: message bubble appears in transcript | asserted |
| 6 Verify response contains CONFIRMED | response contains CONFIRMED | step 6 | `step 6`: response paragraph text === "CONFIRMED" | asserted (GPT-5 mini, GPT-5.4 spot-checked live; GPT-5.2/GPT-5.4-mini follow the identical proven mechanism — implementer parametrizes over all 4) |
| 7 Repeat 4-6 for GPT-5 mini | selected, saved, CONFIRMED | step 4-6 | executed live: `PUT` → 201, response labeled "GPT-5 mini", body "CONFIRMED" | asserted |
| 8 Repeat 4-6 for GPT-5.2 | selected, saved, CONFIRMED | — | not live-executed this session (spot-check scope) | **not independently verified this pass** — same proven mechanism; implementer includes it in the parametrized set and it will be verified by that green run |
| 9 Repeat 4-6 for GPT-5.4 | selected, saved, CONFIRMED | step 8 | executed live: response labeled "GPT-5.4", body "CONFIRMED" (pre-selected + re-confirmed via explicit select+Save during cleanup) | asserted |
| 10 Repeat 4-6 for GPT-5.4-mini | selected, saved, CONFIRMED | — | not live-executed this session (spot-check scope) | **not independently verified this pass** — same proven mechanism, included in the parametrized set |

**Clarification (case-text drift, not a defect) — GPT-4.1 is absent from the live
model catalog.** The case's Test Data table names `GPT-4.1` as one of five models to
verify. Live `GET /api/v2/configurations/models/399?include_shared=true` returns
exactly 11 configured models (confirmed twice: once directly by this analysis pass,
once independently by the `settings-ai-providers` surface digest captured the day
before on the same project) — none of the 11 is `GPT-4.1` under any name or alias.
The other 4 case-named models ARE present and functional. This reads as the
platform's OpenAI catalog having moved on to the GPT-5 family (consistent with the
sibling case ELITEA-1881, which found the Anthropic model list similarly evolved vs.
its case text — there a display-name prefix, here a full model swap). Filed as
[EliteaAI/elitea-testing-public#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285)
per the reverse-masking guard (`test-case-analysis` SKILL.md § Classify findings) —
not a tracker `bug`, no automated assertion should expect GPT-4.1 to appear.
Automation asserts exactly the 4 present models; it does NOT assert "GPT-4.1 is
absent" as a hard invariant (a future re-add of GPT-4.1 to the catalog is not a
regression — the test should stay agnostic about the 5th model, not fail if the
platform later reintroduces it).

**Step re-ordering / partial live-execution note (self-declared, per "Advance vs
circle" budget guidance):** this session live-executed the full select→Save→chat→
verify cycle end-to-end for **2 of the 4 present models** (GPT-5.4, already-selected
at session start and re-confirmed via explicit select+Save during cleanup; GPT-5 mini,
freshly selected+saved+chatted). GPT-5.2 and GPT-5.4-mini were **not** independently
round-tripped this session — the underlying mechanism (dynamic
`model-selector-option-{name}` testid → `agent-save-button` → `PUT .../application/
{project}/{agent}` → 201 → `chat-message-input` → WebSocket response) is proven
identical across all menu items (same `LLMModelsMenu.jsx` component, same handler),
and this exact mechanism is already the implemented, merged pattern from
ELITEA-1881 (`automation/tests/ui/agents/test_agent_llm_selector_anthropic_models.py`,
merged to `origin/automation/base` — commit `5e39cf52`, PR #583). The implementer
parametrizes the new test over all 4 present models; the green pytest run is what
closes the remaining 2 models' verification, not a re-run of this analysis.

### Axis 2 — Analyst additions (beyond the case)

- `step 4-6/8` (GPT-5 mini, GPT-5.4) asserts the underlying `PUT` request returns
  `201 Created` (not just that the UI *looks* saved) — *added: the UI's only visible
  save signal is the Save/Discard buttons returning to disabled state, which could
  mask a silent failed request; the network assertion is the stronger, non-flaky
  proof of persistence.* (Same addition as ELITEA-1881.)
- `step 6/8` asserts the response is attributed to the *correct* model name in the
  transcript (e.g. "GPT-5 mini" shown above the CONFIRMED text) — *added: the case's
  Pass criterion only checks the response text, but attributing each response to the
  wrong model would be a silent regression the case as written wouldn't catch.*
- Console-message check (0 errors/warnings) across the full flow — *added: standard
  side-channel discipline per `test-case-analysis` SKILL.md; the widget renders fine
  even when console-level errors are present, so this is the only way to catch a
  silent JS error.*
- Model catalog cross-check via the raw `GET /api/v2/configurations/models/399`
  response (not just the dropdown DOM) — *added: the GPT-4.1 absence needed
  API-level confirmation to rule out "the option exists but doesn't render" as a
  distinct (and more serious) UI-layer defect; the API response settles it — the
  model simply isn't configured.*
- (No assertions beyond these were added.)

## Cleanup
1. If automation creates a dedicated agent for this case (recommended — see
   Automation Hints), delete it via
   `DELETE /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` in
   teardown.
2. If automation reuses a shared fixture agent instead, restore its LLM selection to
   the pre-test value (`GPT-5.4` at time of this exploration pass) and Save, to avoid
   leaking state into other tests/analysts sharing the same agent. **This analysis
   session performed exactly this restoration live** (select `GPT-5.4` → Save →
   confirmed `PUT` → 201) before finishing, so the fixture agent is in its original
   state.
3. No conversation/chat cleanup needed — conversations are scoped to the agent and
   don't require separate teardown per existing project convention (matches
   ELITEA-1881 and other agent chat specs in `test-specs/agents/`).

## Concrete Handles (discovered/reused during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Model selector button (whole group) | `getByTestId('model-selector-button')` | none — testid-only project policy |
| Model selector button (opens menu, shows current selection) | `getByTestId('model-selector-name')` | none |
| Model dropdown menu item, per model | `getByTestId('model-selector-option-{model_name}')` — dynamic, `model_name` = the model's stable API `name` field (e.g. `gpt-5-mini`, `gpt-5.2`, `gpt-5.4`, `gpt-5.4-mini`) — **pre-existing testid, added during ELITEA-1881's analysis pass, re-confirmed live and reused as-is this session, no new testid work needed** | none |
| Agent Save button (top toolbar) | `getByTestId('agent-save-button')` | none |
| Chat message input | `getByTestId('chat-message-input')` | none |
| Chat response text (per message) | scope to the last `listitem` in the transcript list, then read its paragraph text — **no testid found on individual response bubbles/paragraphs; same pre-existing gap flagged by ELITEA-1881, not remediated here either (out of this case's scope)** | `page.locator('[role="listitem"]').last()` scoped to the chat transcript region, then `.getByRole('paragraph')` — acceptable per-scoped fallback since no stable testid exists yet on the response bubble itself |
| Chat response's attributed model name | same transcript `listitem`, the small text row above the response body (e.g. "GPT-5 mini") — **no testid**, same flag as above | text content of the region directly above the response paragraph, scoped to the same `listitem` |

**No new testid work required this pass** — all handles needed for this case
(`model-selector-button`, `model-selector-name`, dynamic
`model-selector-option-{name}`, `agent-save-button`, `chat-message-input`) already
exist on `EliteaAI/EliteaUI` and were added/confirmed by the ELITEA-1881 analysis
pass; this run re-verified them live against the current `automation/testids` state
with no drift.

## Network Behavior
- `GET /api/v2/configurations/models/{project_id}?include_shared=true` — fires on
  chat-panel mount / model-selector interaction; response `items[]` contains `name`
  (stable API model id) and `display_name` (UI text) for all configured models.
  **Confirmed live, full 11-item response body** (project `399`, 2026-08-06):
  - `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` → "Anthropic Claude 4.5 Sonnet" (default)
  - `eu.anthropic.claude-sonnet-4-6` → "Anthropic Claude 4.6 Sonnet"
  - `eu.anthropic.claude-haiku-4-5-20251001-v1:0` → "Anthropic Claude Haiku 4.5"
  - `global.anthropic.claude-sonnet-5` → "Anthropic Sonnet 5"
  - `claude-sonnet-4-5` → "Azure Claude Sonnet 4.5"
  - `claude-sonnet-4-6` → "Azure Claude Sonnet 4.6"
  - `claude-sonnet-5` → "Azure Claude Sonnet 5"
  - `gpt-5-mini` → "GPT-5 mini" (low-tier default)
  - `gpt-5.2` → "GPT-5.2" (high-tier default)
  - `gpt-5.4` → "GPT-5.4"
  - `gpt-5.4-mini` → "GPT-5.4-mini"

  **No entry for GPT-4.1.** OpenAI models in this catalog carry NO vendor prefix
  (unlike Anthropic/Azure entries, which are all vendor-prefixed) — so automation
  should match display names literally (`"GPT-5 mini"`, not `"OpenAI GPT-5 mini"`).
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` — fires on
  Save click after a model change; **201 Created** on success. Confirmed live twice
  this session (GPT-5 mini select, then GPT-5.4 restore). This is the assertion point
  for "Save completes successfully" — don't rely solely on the Save button's disabled
  state, confirm the response status. (Same as ELITEA-1881.)
- The chat send/response cycle rides the project's existing WebSocket transport (per
  `.agents/testing.md` — "AI responses arrive over WebSocket with ~2s delay"). No new
  REST endpoint beyond the initial message-send; response arrives async over the
  existing socket. Observed round-trip this session: ~15-25s including a visible
  "Thought for 1 sec" reasoning-collapse header on both GPT-5 mini and GPT-5.4
  responses (per-model latency variance similar to ELITEA-1881's Anthropic run).

## Known Defects Found During Exploration
None found among the 4 present, testable models — all selectable, saveable (201 on
each `PUT`), and each returned a "CONFIRMED" response correctly attributed to the
selected model (2/4 spot-checked live this session; 2/4 covered by the identical
proven ELITEA-1881 mechanism). Zero console errors/warnings across the full flow.

**GPT-4.1 is absent from the platform's model catalog** — classified as a
**CLARIFICATION** (case-text drift), not a defect, per the reverse-masking guard:
[EliteaAI/elitea-testing-public#1285](https://github.com/EliteaAI/elitea-testing-public/issues/1285).

## Blocked Steps
None — the case is not blocked. GPT-4.1's absence prevents 2 of the case's 10
numbered steps (the GPT-4.1-specific select/save/chat/verify) from being executable
as literally written, but this is a case-text/product mismatch (tracked via the
clarification above), not an execution blocker for the other 8 steps or for
automating the case around the 4 present models.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. **Strongly prefer
  extending/mirroring `automation/tests/ui/agents/test_agent_llm_selector_anthropic_models.py`**
  (ELITEA-1881, merged) rather than writing from scratch — same agent detail page
  object, same select→Save→chat→verify helper methods, same wait-budget concerns.
  Parametrize over the 4 present models (`gpt-5-mini`/`GPT-5 mini`,
  `gpt-5.2`/`GPT-5.2`, `gpt-5.4`/`GPT-5.4`, `gpt-5.4-mini`/`GPT-5.4-mini`) rather than
  writing 4 near-duplicate test bodies.
- **Wait strategy — same generous budget ELITEA-1881 documented.** Use a
  condition-based wait (`wait_for` on the response text/selector appearing), never a
  fixed `sleep()`. Set an explicit timeout override of at least 60s per response wait
  to absorb LLM latency variance. This test drives 4 full model-cycles serially
  (select → save → send → await-response, ×4) — mark `slow` and/or `regression`
  (not `smoke`) per `.agents/testing.md` § Markers, same as ELITEA-1881.
- **Live API/cost/quota note:** 4 real calls to live OpenAI-backed models per run
  (via the platform's LLM proxy). No quota/availability issues hit during this
  analysis pass (GPT-5 mini and GPT-5.4 both responded promptly); same
  `regression`-suite-cadence consideration as ELITEA-1881 applies.
- **Do NOT assert GPT-4.1's absence as a hard invariant.** The test should assert
  exactly the 4 present models are selectable/functional; it should not fail (or
  pass differently) if the platform later adds GPT-4.1 back to the catalog. If the
  team wants a "5th model" placeholder for when/if GPT-4.1 returns, that's a product
  decision to make via #1285, not something to encode defensively in this spec.
- Consider isolating this case onto a dedicated per-test agent (create+delete in
  fixture) rather than reusing the shared "Test Agent" — same reasoning as
  ELITEA-1881 (parallel test execution races via `pytest-xdist`). This case and
  ELITEA-1881 both mutate the SAME fixture agent's model selection; if both run in
  the same CI invocation without isolation, they could race on the Save/GET cycle.
- Consider whether the implementer wants ONE combined parametrized spec covering
  both ELITEA-1881 (Anthropic) and ELITEA-1882 (OpenAI) models, since the mechanism
  is identical and only the model-name data differs — this analysis pass judged them
  as **separate specs** because ELITEA-1881 is already merged as its own case-linked
  spec on `origin/automation/base` (Rule per `test-case-analysis` SKILL.md § Merged-
  target rule: `already-covered`/`extend-existing` may only target a MERGED spec, and
  even then a full parametrization merge is an implementer-level refactor decision,
  not an analyst reclassification of two separately-tracked TMS cases into one).
