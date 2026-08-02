# Test Case: LLM selector — change model, verify settings dialog, save and persist

## Metadata
- **TMS ID**: ELITEA-1880
- **Linked Story**: none
- **Priority**: l2 (source case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaAI/EliteaUI `automation/testids` → DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` skip-login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (agent), 2026-08-02
- **Status**: **ready-for-automation** — executed end-to-end live via a scratch Playwright script (see § Automation Hints re: tooling — no Playwright MCP server was wired in this environment, so exploration used a standalone `sync_playwright` script reusing `AgentDetailPage`/`AgentAPI` directly). All 9 case steps completed, no blockers, no defects. Several testid gaps found (not remediated — see § Concrete Handles; per `.agents/role-overrides.md` § Analyst slot, testid remediation is implementer work via `add-data-testid`, not analyst work).

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on localhost via `auth_state`/`VITE_DEV_TOKEN`).
- An existing agent with an LLM selector is available. Automation should create a **dedicated, disposable agent** per test run (mirrors the ELITEA-1881/1883/1888 pattern) rather than mutating a shared fixture agent — this case mutates persisted `llm_settings` (model) via Save, so a shared agent would create cross-test races under `pytest-xdist`.

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated agent via `AgentAPI.create_agent_full()`, `reasoning_effort: "none"` and no `temperature` in the initial payload (avoids the open #524-class defect — see `test-specs/agents/_surface.md`). Initial model is irrelevant — the case re-selects a different model via the UI (confirmed live: initial model was `GPT-5.2`, target selected was `Anthropic Claude 4.5 Sonnet` — any two distinct models from the dropdown satisfy the case).

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` (agent detail page)
   - **Verify**: agent detail page loads — Information section visible, embedded chat panel visible.
   - **OBSERVED**: page loaded; model selector (`model-selector-name`) showed `GPT-5.2` (the disposable agent's initial model).
2. Note the currently selected model
   - **Verify**: current model name is recorded.
   - **OBSERVED**: `detail_page.get_selected_model_name()` returned `"GPT-5.2"`.
3. Click the model selector and choose a different model
   - **Verify**: the new model name is shown in the selector.
   - **OBSERVED**: opened via `model-selector-button`; dropdown listed 11 models (`Anthropic Claude 4.5 Sonnet`, `Anthropic Claude 4.6 Sonnet`, `Anthropic Claude Haiku 4.5`, `Anthropic Sonnet 5`, `Azure Claude Sonnet 4.5`, `Azure Claude Sonnet 4.6`, `Azure Claude Sonnet 5`, `GPT-5 mini`, `GPT-5.2`, `GPT-5.4`, `GPT-5.4-mini`); selected `Anthropic Claude 4.5 Sonnet` via `select_llm_model()`.
4. Verify the new model name is shown in the selector
   - **Verify**: selector displays the newly chosen model.
   - **OBSERVED**: `get_selected_model_name()` returned `"Anthropic Claude 4.5 Sonnet"` immediately after selection (client-side, no network round trip yet — Save hasn't been clicked).
5. Click the Settings (⚙️) icon
   - **Verify**: the settings dialog opens.
   - **OBSERVED**: a gear-icon button next to the model selector (`aria-label="model settings menu"`, no testid — see § Concrete Handles) opens a MUI dialog titled **"Model settings"**.
6. Verify the settings dialog opens with fields appropriate to the model type
   - **Verify**: Reasoning slider (Low, Medium, High) + Max Completion Tokens (Auto/Custom) for standard models.
   - **OBSERVED**: for `Anthropic Claude 4.5 Sonnet` (a reasoning-capable model), the dialog rendered, top to bottom: a **"Reasoning"** slider with 3 discrete positions labeled `Low` / `Medium` / `High`; a **"Max Completion Tokens"** section with a 2-way toggle labeled `Default` / `Custom` (not `Auto` — see Coverage Map clarification below); a **"Capabilities"** section showing a `Reasoning` chip; `Cancel` / `Apply` action buttons (no `Reset to defaults` button — `onResetToDefaults` prop isn't wired for the agent-page instance of this dialog). Full dialog text dump (script capture):
     ```
     Model settings
     REASONING
     Low / Medium / High
     MAX COMPLETION TOKENS
     Default / Custom
     CAPABILITIES
     Reasoning
     Cancel   Apply
     ```
   - **Code-confirmed** (`EliteaUI/src/[fsd]/widgets/llm-model-selector/ui/LLMSettings.jsx`): the slider shown is conditional on `model.supports_reasoning` — a reasoning-capable model gets the `ReasoningSlider` (Low/Medium/High); a non-reasoning model gets a `CreativitySlider` (temperature) instead. **Max Completion Tokens is unconditional — always shown for every model type.** The case's phrasing ("Reasoning slider … for standard models") is imprecise per the live code/UI: the Reasoning slider appears specifically for *reasoning-capable* models, not generically for "standard" ones; a non-reasoning model would show the Creativity/Temperature slider in its place. See Coverage Map clarification.
7. Close the settings dialog and click Save
   - **Verify**: Save completes successfully.
   - **OBSERVED**: closed the dialog via its `Cancel` button (no local llm-settings edits were made, so Cancel vs Apply is behaviorally equivalent here — Cancel was chosen as the neutral "close" action matching the case's "Close the settings dialog" wording, which doesn't ask to change reasoning/token settings). The model-selector chip still showed `Anthropic Claude 4.5 Sonnet`, and the top-toolbar `agent-save-button` was enabled (dirtied by the step-3 model change). Clicking it fired `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` → **201 Created**.
8. Reload the page
   - **Verify**: the page reloads.
   - **OBSERVED**: `page.reload()` + `wait_for_page_load()` completed; Information section + chat panel re-rendered.
9. Verify the model selector still shows the model chosen in step 3
   - **Verify**: model selector displays the saved model.
   - **OBSERVED**: `get_selected_model_name()` after reload returned `"Anthropic Claude 4.5 Sonnet"` — matches the step-3 selection. Persistence confirmed at the **UI level via a real reload**, not just via the Save PUT's 201 status (a stronger check than ELITEA-1881's network-only persistence assertion — see § Relationship to ELITEA-1881 below).

## Expected Results
- The model selector accepts a new model selection and reflects it immediately (client-side, pre-Save).
- The Settings (gear) dialog opens and shows a model-type-appropriate slider (Reasoning for reasoning-capable models, Creativity/Temperature otherwise) plus an always-present Max Completion Tokens section (Default/Custom toggle).
- Closing the dialog and clicking the main Save button persists the model change (`PUT .../application/... → 201`).
- After a full page reload, the model selector still shows the model chosen during editing.
- No console errors or warnings at any point in the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | N/A (env-level) | `auth_state` fixture / `VITE_DEV_TOKEN` | asserted (env precondition) |
| Precondition: existing agent with LLM selector | — | N/A | dedicated disposable agent created per test | asserted |
| 1 Navigate to agent detail page | page loads | step 1 | Information section + chat panel visible | asserted |
| 2 Note currently selected model | recorded | step 2 | `get_selected_model_name()` captured pre-change | asserted |
| 3 Click selector, choose different model | new model shown | step 3 | dropdown opens, `select_llm_model()` | asserted |
| 4 Verify new model name shown | selector shows new model | step 4 | `get_selected_model_name() == target` immediately post-select | asserted |
| 5 Click Settings (⚙️) icon | dialog opens | step 5 | gear button click → `[role="dialog"]` visible, titled "Model settings" | asserted |
| 6 Verify dialog fields appropriate to model type | Reasoning slider (Low/Med/High) + Max Completion Tokens (Auto/Custom) for standard models | step 6 | dialog text contains "REASONING"/"Low"/"Medium"/"High" and "MAX COMPLETION TOKENS"/"Default"/"Custom" | asserted, **clarification** on exact wording (see below) |
| 7 Close dialog, click Save | save completes | step 7 | Cancel closes dialog; `PUT .../application/...` → 201 via `page.expect_response` | asserted |
| 8 Reload the page | page reloads | step 8 | `page.reload()` + `wait_for_page_load()` | asserted |
| 9 Verify selector still shows step-3 model | model persisted | step 9 | `get_selected_model_name() == target` post-reload | asserted |

**Clarification 1 (case-text drift, not a defect):** the case's step 6 expected result says "Reasoning slider (Low, Medium, High) + Max Completion Tokens (Auto/Custom) **for standard models**". Live code (`LLMSettings.jsx`) shows the Reasoning slider is conditional on `model.supports_reasoning` being true — it's the *reasoning-capable*-model branch, not the "standard model" branch (a non-reasoning model gets a Creativity/Temperature slider instead, per the `model?.supports_reasoning ? <ReasoningSlider/> : <CreativitySlider/>` branch). "Standard" in the case text most likely means "non-multimodal, non-specialised" rather than "non-reasoning" — on this platform most selectable models (all 3 Anthropic + the default GPT tier) are reasoning-capable, so the Reasoning-slider branch is in practice the common path a tester hits, which likely motivated the case author's phrasing. Automation should assert the Reasoning-slider branch for the specific model selected in step 3 (a reasoning-capable model, matching what was live-confirmed), and may optionally extend coverage to the Creativity/Temperature branch for a non-reasoning model as a documented Axis-2 addition — but that is out of this case's literal scope (the case only asks to verify fields for the ONE newly selected model).

**Clarification 2 (case-text drift, not a defect):** the case says the Max Completion Tokens toggle reads "Auto/Custom"; the live UI labels it **"Default/Custom"** (`MaxTokensSection.jsx`: `{ label: 'Default', value: 'auto' }` / `{ label: 'Custom', value: 'custom' }` — the internal *value* is `'auto'`, but the *rendered label* is `"Default"`). Automation should assert the rendered label `"Default"`, not `"Auto"`.

### Axis 2 — Analyst additions (beyond the case)

- Asserted the Save PUT's network status (`201 Created`), not just the button's disabled/enabled visual state — *added: the UI's only visible save signal is the Save button's disabled state, which could mask a silently-failed request; the network assertion is the stronger, non-flaky proof, same rationale as ELITEA-1881's AFS.*
- Console-message check (0 errors/warnings) across the full 9-step flow — *added: standard side-channel discipline per `test-case-analysis` § Execute; a JS error opening the settings dialog wouldn't necessarily be visible in the UI.*
- Captured the dialog's **Capabilities** section (`Reasoning` chip) and the absence of a `Reset to defaults` button for this dialog instance — *added: not requested by the case, but useful context for the implementer deciding what to assert inside the dialog (documented in step 6's observation, not asserted as a separate pass/fail unless the implementer wants extra coverage).*

## Relationship to ELITEA-1881 (`test-specs/agents/l2_llm-selector-anthropic-models_ELITEA-1881.md`, merged to `origin/automation/base` — `automation/tests/ui/agents/test_agent_llm_selector_anthropic_models.py`)

**Checked before classifying** (per `test-case-analysis` § 2b — reuse to travel and to know, not to close the case). ELITEA-1881's merged test drives a materially overlapping *sub-flow* — navigate → open model selector → verify Anthropic models listed → select a model → Save (network-201-asserted) — across all 3 Anthropic models, each followed by a live chat round-trip.

**Classification call: `ready-for-automation` (fresh spec), NOT `extend-existing`.** Reasoning:
- Steps 5–6 (Settings-gear click, dialog field verification) and steps 8–9 (real page **reload** + UI-level persistence re-check) are **entirely new observables** — ELITEA-1881's test never opens the settings dialog and never reloads the page (its persistence check is network-status-only). That's 4 of this case's 9 steps with zero existing coverage, plus step 7's "close the dialog" sub-action.
- ELITEA-1881's test is shaped as a **3-model loop** (select → save → send chat message → await response, ×3, live-LLM-cost-bearing) built specifically to prove "these 3 Anthropic models are functional end-to-end via chat". Grafting a settings-dialog-open + reload-recheck into that loop would either 3x an already `slow`/live-inference-cost test for no case-mandated reason, or break the loop's per-model symmetry by only instrumenting one iteration — both distort a merged, working spec's intent to serve a differently-shaped case.
- Per `test-case-analysis` § Classify findings' extend-existing boundary call: "if the gap is large enough that the extension would be a near-rewrite of the covering spec, treat as `ready-for-automation` instead" — that threshold applies here.
- **What IS reused:** the implementer should reuse `AgentDetailPage`'s existing model-selector methods (`open_model_selector`, `select_llm_model`, `get_selected_model_name`, `close_model_selector`, `is_save_enabled`, `click_save` inherited from `AgentFormPage`) and the dedicated-disposable-agent creation pattern (`_build_dedicated_agent_payload` shape) from `test_agent_llm_selector_anthropic_models.py` — this case needs NO new agent-creation logic, only new page-object methods for the settings-gear button and dialog.

## Cleanup
1. Delete the dedicated disposable agent via `DELETE /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` in teardown (or `delete_agent_via_menu()` UI fallback, mirroring ELITEA-1881's `finally` block pattern).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Status |
|---|---|---|
| Model selector button (group) | `getByTestId('model-selector-button')` | on-automation/testids ✓ (pre-existing, used by ELITEA-1881) |
| Model selector current-name display | `getByTestId('model-selector-name')` | on-automation/testids ✓ (pre-existing) |
| Model dropdown menu item, per model | `getByTestId('model-selector-option-{model_name}')` (dynamic, API `name` suffix) | on-automation/testids ✓ (added during ELITEA-1881 analysis, commit `0b058c94`) |
| Agent Save button (top toolbar) | `getByTestId('agent-save-button')` | on-automation/testids ✓ (pre-existing) — **note:** `AgentFormPage.save_button`'s `LocatorDescriptor` currently also populates a `fallback=` lambda (`agent_form_page.py:145-148`), which is forbidden in new code per `.agents/testing.md` § Locator policy; this is pre-existing tech debt (like the ~350 raw-handle call sites tracked in #25/#42), not something to fix as part of this case — flagging only, not blocking. |
| **Settings (gear) button** — opens the Model Settings dialog | **testid needed: `model-settings-button`** — currently only `aria-label="model settings menu"` (`LLMModelSelector.jsx`'s default-variant `ButtonGroup` branch), no testid. This is a SHARED widget (`src/[fsd]/widgets/llm-model-selector/`) used across ChatBox/TestSettings/etc — name generically (matches the existing `model-selector-button`/`model-selector-name` generic-naming precedent on the same widget), not feature-scoped. |
| **Model Settings dialog root** | **testid needed: `model-settings-dialog`** — `LLMSettingsDialog.jsx` renders `Modal.BaseModal` but does not pass BaseModal's own `data-testid` / `titleTestId` / `closeButtonTestId` props (BaseModal already supports them — see `EliteaUI/src/[fsd]/shared/ui/modal/BaseModal.jsx:32-36` — they're simply unwired at this call site). Threading `dataTestId="model-settings-dialog"` through is the minimal fix. |
| **Reasoning slider** (shown for reasoning-capable models) | **testid needed: `model-settings-reasoning-slider`** on `ReasoningSlider.jsx`'s `DiscreteSlider` wrapper (or the underlying `DiscreteSlider` component, if shared — check for testid-prop threading same as `MaxTokensSection`) | no testid found |
| **Max Completion Tokens section** | **testid needed: `model-settings-max-tokens-section`** on `MaxTokensSection.jsx`'s container `Box` | no testid found |
| **Settings dialog Cancel button** (used to close without applying) | **testid needed: `model-settings-cancel-button`** — `LLMSettingsDialog.jsx`'s own `actions` JSX defines this button locally (does NOT use BaseModal's built-in Cancel), currently plain-text `"Cancel"` with no testid | no testid found |
| **Settings dialog Apply button** (not used by this case's steps, but present) | out of scope for THIS case (case step 7 says "close", not "apply changes") — do not add unless a future case needs it, per the strict "elements this test touches" scoping rule | n/a |

**None of the settings-dialog testid gaps were remediated during this analysis pass** — per `.agents/role-overrides.md` § Analyst slot, a testid demand is implementer work (`add-data-testid`), not something to soften into a note; the rows above are that work order, scoped to exactly the elements this case's steps touch (gear button, dialog container, Reasoning slider, Max Completion Tokens section, Cancel button — NOT the Apply/Reset buttons, which this case never exercises).

## Network Behavior
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` — fires on Save click after a model change; **201 Created** on success (confirmed live). This is the assertion point for "Save completes successfully" (step 7).
- Opening/closing the Settings dialog and toggling its fields (Reasoning slider, Max Completion Tokens mode) does **not** fire any network request by itself — `LLMSettingsDialog` holds `localSettings` in React state and only pushes it into the parent's `llmSettings` state via `onApply` (Apply button, not exercised by this case since we Cancel). No network assertion is needed/possible for step 6 — it's a pure client-side rendering check.
- Page reload (step 8) re-fetches the agent via the standard agent-detail-page load sequence (same `GET` the page normally issues on navigation) — no case-specific new endpoint.

## Known Defects Found During Exploration
None. All 9 case steps completed successfully; model change → settings dialog → save → reload → persistence-verify all behaved correctly. Zero console errors/warnings across the full flow.

## Blocked Steps
None. All 9 case steps executed to completion with no blockers.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Extend `AgentDetailPage` (`automation/pages/agent_detail_page.py`) with new locators/methods for the settings-gear button and dialog once the corresponding testids exist (see § Concrete Handles) — do not add methods using role/aria-label locators as a permanent solution; those are exploration-only in this AFS.
- **Tooling note:** no Playwright MCP server was available in this analysis session (deferred-tool search returned no `mcp__playwright__*` tools). Exploration was done via a standalone `sync_playwright` Python script (not committed — scratch-only) that imported `AgentDetailPage`/`AgentAPI` directly and drove the real browser against `localhost:5173`. This produced the same live observations a Playwright-MCP-driven session would; noting the substitution per the dispatch's tool-selection guidance (a different allowed route to the same goal).
- Model-type coverage: this case's live run selected a **reasoning-capable** model (`Anthropic Claude 4.5 Sonnet`) and confirmed the Reasoning-slider branch. If the implementer wants belt-and-suspenders coverage of the Creativity/Temperature branch (non-reasoning model), that would be a natural **follow-on case**, not part of this one's literal scope — flagging as an Axis-2-adjacent idea, not adding it here.
- Reuse `test_agent_llm_selector_anthropic_models.py`'s dedicated-agent creation helper shape (`_build_dedicated_agent_payload`) — same `reasoning_effort: "none"` / no-`temperature` payload to avoid #524.
- Standard timeout constants apply (`UI_ELEMENT_TIMEOUT`, `SAVE_RESPONSE_TIMEOUT`, `NAVIGATION_TIMEOUT` per `.agents/testing.md`/project convention) — this case does **not** need the generous `AI_RESPONSE_TIMEOUT` ELITEA-1881 needed, since it never sends a chat message.
- Suggested markers: `p2`, `regression`, `agents` (not `slow` — no live LLM chat round-trip, so this test should run fast, unlike ELITEA-1881).
