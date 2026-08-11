# Test Case: LLM model settings are configurable (Skill test panel)

## Metadata
- **TMS ID**: ELITEA-2436
- **Linked Story**: none
- **Priority**: l3 (case frontmatter/body: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend, project `Private` /
  `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (localhost `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Case-gate note**: case frontmatter carries `status: draft`,
  `execution_type: manual` — per `.agents/test-automation.yaml` § `intake`,
  `status: draft` is the intake-eligible value, not an exclusion. Proceeded
  to full execution.
- **Dedup / reuse check**: grepped `test-specs/skills/` and
  `automation/tests/ui/skills/*.py` for `model_selector` / `model-settings` /
  `reasoning` — no existing skills-surface spec touches the model selector or
  its Settings dialog. The closest neighbour by SHARED WIDGET (not by
  screen) is `test-specs/agents/l2_llm-selector-change-model-settings-dialog-persist_ELITEA-1880.md`
  (merged, `automation/tests/ui/agents/test_agent_llm_selector_model_settings_persist.py`)
  — it drives the **identical** `LLMSettings`/`LLMSettingsDialog` React
  component (`src/[fsd]/widgets/llm-model-selector/`) and the **same**
  generic testids, but from the **Agent detail page** (`/agents/all/{id}`),
  not the **Skill test panel** (`/skills/all/{id}`, `SkillTestPanel.jsx`).
  Per `.agents/test-automation.yaml`/`test-case-analysis` § Classify
  findings' merged-target rule, `already-covered`/`extend-existing` require
  the SAME screen/page-object asserting the SAME observable — a shared
  widget reused from a different page is NOT that. `SkillDetailPage`
  currently has **zero** model-selector/model-settings methods (confirmed:
  `grep -n "model\|Model\|reasoning\|Reasoning\|Settings" automation/pages/skill_detail_page.py`
  returns nothing), so this is genuinely new page-object surface, not an
  extension of an existing one. Classified `ready-for-automation`, fresh
  spec — see § Relationship to ELITEA-1880 below for exactly what IS reused
  (the testids and the pattern, not the code/page-object).

## Preconditions
- User is logged in to the Elitea platform (satisfied automatically on
  localhost via `auth_state`/`VITE_DEV_TOKEN`).
- At least one existing Skill is available with a functioning test panel
  (any skill works — this run used a pre-existing shared fixture skill,
  `elitea-1735-skill-underscore`, id `1417`, owned by the ELITEA-1735 suite;
  no mutation was made to it — see § Cleanup).

## Test Data
### reuse existing (read-only; no fixture mutation)
- Any existing Skill reachable at `/skills/all/{id}` with its test panel
  visible. This run used skill id `1417` (`elitea-1735-skill-underscore`) —
  confirmed live the model selector / Settings dialog interactions in this
  case are **pure client-side local state** (see § Network Behavior): no
  `PUT`/`PATCH` to the skill entity fires from selecting a model or editing
  Settings-dialog fields, so **any** existing skill is safe to reuse without
  risk of mutating shared fixture data. The implementer may instead create a
  disposable per-test skill via `SkillAPI.create_skill()` if preferred for
  isolation — either is defensible; this AFS recommends reusing an existing
  skill (cheaper, and confirmed safe) unless xdist parallelism makes a
  disposable skill simpler to reason about.

## Test Steps

1. Open a Skill and locate the model settings control in the test panel
   (gear/⚙️ icon next to the model selector).
   - **Verify**: the gear-icon button is present and clicking it opens the
     "Model settings" dialog.
   - **OBSERVED live**: navigated to `/skills/all/1417`; the test panel's
     `NewChatInput` renders a "Select LLM Model" group with the model-name
     button (`model-selector-button`/`model-selector-name`, showed
     `"Anthropic Claude 4.5 Sonnet"` — the skill's/project's currently
     effective default model) and, next to it, a `"model settings menu"`
     gear button (`model-settings-button`). Clicking it opened a MUI dialog
     titled **"Model settings"** (`model-settings-dialog`).

2. Select a standard model (e.g., `gpt5-mini`) and adjust the reasoning
   slider.
   - **Verify**: control responds; expected next state is shown.
   - **OBSERVED live — case-text drift, not a defect (reverse-masking
     guard)**: selected `gpt-5-mini`
     (`model-selector-option-gpt-5-mini`) via the model dropdown, then
     reopened the Settings dialog. Per the LIVE product (and confirmed in
     code, `LLMSettings.jsx:119`: `model?.supports_reasoning ? <ReasoningSlider/>
     : <CreativitySlider/>`), `gpt-5-mini` is **not** a reasoning-capable
     model on this platform, so the dialog does **not** render a Reasoning
     slider for it at all — it renders a **Creativity** slider instead (1–5
     discrete positions, labelled `Low (0.2)` / `Mid-Low (0.4)` /
     `Medium (0.6)` / `Mid-High (0.8)` / `High (1)`). There is no "reasoning
     slider" to adjust for this specific model — the case's step-2 phrasing
     assumes a reasoning slider is present for a "standard" model, which the
     live product correctly contradicts (identical drift to ELITEA-1880's
     already-filed Clarification 1, now confirmed to reproduce identically
     on this second screen/widget instance). Automation should satisfy the
     step's actual intent — "a settings control for the selected model
     responds and shows the expected next state" — by exercising **whichever
     slider the model-type branch actually renders** (Creativity, for a
     non-reasoning model): confirmed live, focusing the slider `<input
     type="range" aria-label="Creativity level">` and pressing `ArrowRight`
     moved its value from `3` → `4`, and the dialog's **Apply** button
     (`model-settings-apply-button`, disabled by default) became enabled
     immediately after the change — confirming the control responds and
     surfaces the expected next state (an enabled Apply). Clicking Apply
     closed the dialog with no console errors and no network request (see
     § Network Behavior).

3. Run a test — verify no error occurs.
   - **Verify**: action completes without error and produces the expected
     UI state.
   - **OBSERVED live**: with `gpt-5-mini` selected (Apply already clicked
     from step 2), sent the test message `"Say OK"` via
     `chat-message-input` / `chat-send-button`. Response streamed and
     stabilized; `skill-test-last-response` read exactly `"OK"`. Network:
     `POST /api/v2/elitea_core/predict_llm/prompt_lib/399` → `200 OK`. Zero
     console errors; one **pre-existing, unrelated** console warning (MUI:
     "You are providing a disabled `button` child to the Tooltip
     component" — traced to the test panel's disabled "Clear the chat"
     button, not to anything this case's steps touch; not filed, noted for
     completeness only per this skill's side-channel discipline).

4. Switch to a reasoning model (if available) and verify reasoning effort
   options appear (Low / Medium / High).
   - **Verify**: action completes without error and produces the expected
     UI state.
   - **OBSERVED live — this is the case's stated Pass/Objective criterion,
     and it holds.** Reopened the model selector, selected `GPT-5.2`
     (`model-selector-option-gpt-5.2`, confirmed reasoning-capable — its
     Capabilities section shows both `Image analysis` and `Reasoning`
     chips), then reopened the Settings dialog
     (`model-settings-button` → `model-settings-dialog`). The dialog now
     rendered the **Reasoning** slider
     (`model-settings-reasoning-slider`) with exactly 3 discrete positions
     labelled **`low` / `medium` / `high`**
     (`model-settings-reasoning-level-1` / `-2` / `-3`) — matching the
     case's expected result verbatim. Dialog full-text dump (script
     capture): `"Model settingsReasoninglowmediumhighMax Completion
     TokensDefaultCustom...CapabilitiesImage analysisReasoningCancelApply"`.
     No console errors; no network request (client-side only, same as step
     2).

## Expected Results
Matches the case's Pass criteria, live-verified end-to-end: the Skill test
panel's model settings are configurable — a gear-icon control opens a
"Model settings" dialog whose contents adapt to the selected model's
capabilities (Creativity slider for a non-reasoning model like `gpt-5-mini`;
Reasoning slider with Low/Medium/High for a reasoning-capable model like
`GPT-5.2`), controls respond to interaction (slider value change enables
Apply), and a test prompt runs without error regardless of which model is
selected. One case-text drift found (step 2's "reasoning slider" wording for
a non-reasoning "standard" model) — CLARIFICATION, not a defect; no
functional product defect found; no testid gaps found (see Concrete
Handles — every element this case touches already carries a testid, all
added generically to the shared `llm-model-selector` widget during the
ELITEA-1880 implementation and inherited for free by this Skill-surface
case).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | AFS Preconditions | `auth_state` fixture | asserted |
| 1 Open a Skill, locate model settings in test panel | target page/section loads | step 1 | step 1: gear button present, dialog opens titled "Model settings" | asserted |
| 2 Select a standard model (e.g. gpt5-mini) and adjust the reasoning slider | control responds; expected next state shown | step 2 | step 2: Creativity slider (the model-type-correct control for a non-reasoning model) responds — value change enables Apply | asserted, **clarification** on "reasoning slider" wording (see step 2 note) |
| 3 Run a test — verify no error | action completes without error, expected UI state | step 3 | step 3: `POST predict_llm` → `200 OK`, response text `"OK"`, zero console errors | asserted |
| 4 Switch to a reasoning model (if available), verify reasoning effort options appear (Low/Medium/High) | action completes without error, expected UI state | step 4 | step 4: `model-settings-reasoning-slider` + 3 levels labelled low/medium/high, confirmed for `GPT-5.2` | asserted — this is the case's own stated Objective/Pass criterion |
| Expected Final State: reasoning effort options appear after switching to a reasoning model | — | step 4 | step 4, same assertion | asserted |

**Note on step 2 (case-text drift, reverse-masking guard):** the case's
step-2 expected result implies every "standard" model has an adjustable
reasoning slider. Live code + UI show the Reasoning slider is conditional on
`model.supports_reasoning`; `gpt-5-mini` (the case's own suggested example)
is NOT reasoning-capable on this platform, so it renders the Creativity
slider instead — there is no reasoning slider to adjust for that specific
model. This exactly reproduces ELITEA-1880's already-documented Clarification
1, now confirmed live on a second, independent screen (Skill test panel vs
Agent detail page) that consumes the same shared widget — strengthening
the case that this is a genuine, stable product characteristic and not
adjacent-screen coincidence. Not a product defect: classified
`ready-for-automation` with the assertion written against the live
contract, not the stale case text, per `test-case-analysis` § Classify
findings' reverse-masking guard. File as a CLARIFICATION per
`.agents/profile.md` § Bug filing if the team wants the TMS case text
corrected (see § Defect/Clarification Filing below).

### Axis 2 — Analyst additions

- Captured the exact `predict_llm` network call + `200 OK` status for step
  3's "no error occurs" — *added: the UI's only visible signal is the
  streamed response text; the network assertion is the stronger,
  non-flaky proof, consistent with the ELITEA-2440/ELITEA-1880 AFS
  pattern for this app.*
- Captured that model-selection and Settings-dialog field edits are
  **pure client-side state** with **zero** network calls (confirmed via
  `browser_network_requests` — no `PUT`/`PATCH` fired for the skill
  entity across the whole run) — *added: this is why any existing skill is
  safe to reuse for this case without a dedicated disposable-skill/cleanup
  pattern (unlike ELITEA-1880's agent case, where a real `Save` persists
  the model to the entity). Confirms the implementer does NOT need
  `SkillAPI` cleanup for this specific case.*
- Zero console errors across all 4 case steps; the one console warning
  observed (`MUI: You are providing a disabled 'button' child to the
  Tooltip component`) is unrelated to model settings — pre-existing on the
  test panel's disabled "Clear the chat" button — *added: side-channel
  discipline per this skill's standard practice; not itself a case
  requirement, noted for completeness, not filed.*
- Confirmed the `GPT-5.2` Capabilities section shows BOTH `Image analysis`
  and `Reasoning` chips (multi-capability model) — *added: useful
  implementer context; the case only requires the Reasoning branch to
  render, which it does regardless of the model's other capabilities.*

## Relationship to ELITEA-1880 (`test-specs/agents/l2_llm-selector-change-model-settings-dialog-persist_ELITEA-1880.md`, merged to `origin/automation/base` — `automation/tests/ui/agents/test_agent_llm_selector_model_settings_persist.py`)

**Checked before classifying** (per `test-case-analysis` § 2b). ELITEA-1880's
merged test drives the exact same `LLMSettings`/`LLMSettingsDialog` shared
React component and the exact same generic testids (`model-selector-button`,
`model-settings-button`, `model-settings-dialog`,
`model-settings-reasoning-slider`, `model-settings-max-tokens-section`,
`model-settings-cancel-button`) — confirmed live in this run: every one of
those testids resolved correctly on the **Skill test panel** screen with zero
new `add-data-testid` work needed.

**Classification call: `ready-for-automation` (fresh spec), NOT
`extend-existing` or `already-covered`.** Reasoning:
- The two cases exercise the SAME shared widget from TWO DIFFERENT SCREENS —
  ELITEA-1880 is `/agents/all/{id}` via `AgentDetailPage`; this case is
  `/skills/all/{id}` via `SkillDetailPage`/`SkillTestPanel`. Per the
  merged-target rule, extend/already-covered require the SAME
  screen/page-object asserting the SAME observable; a different page
  reusing a shared widget is out of scope for either verdict.
- `SkillDetailPage` (`automation/pages/skill_detail_page.py`) currently has
  **no** model-selector or model-settings methods at all (confirmed via
  grep) — this is genuinely new page-object surface to build, not an
  extension of existing Skill-page methods.
- **What IS reused** (implementer time-saver, not a code dependency): the
  testid names (identical, zero new `add-data-testid` work — see Concrete
  Handles), and the interaction pattern for the MUI discrete slider
  (`AgentDetailPage`'s handling, plus `user_profile_settings_page.py`'s
  `set_speed()` precedent: focus the underlying `<input type="range">`
  directly via `.focus()` then `keyboard.press("ArrowRight"/"ArrowLeft")` —
  clicking the visual thumb directly is unreliable, MUI's thumb `<span>`
  intercepts pointer events over the underlying range input; confirmed
  live in this run).
- This case additionally proves the **non-reasoning-model branch**
  (Creativity slider) live, which ELITEA-1880's AFS explicitly flagged as
  "a natural follow-on case... out of this case's literal scope" — this
  case closes exactly that gap, on top of proving the Skill-surface
  Reasoning-slider branch.

## Cleanup
None required. Confirmed live: this case never mutates the reused skill's
persisted data — model selection and Settings-dialog field edits inside the
test panel are pure client-side state (see § Network Behavior); the only
network call any of the 4 steps make is the read-only `predict_llm` test-run
in step 3. If the implementer instead opts to create a disposable per-test
skill (see § Test Data), standard `SkillAPI.delete_skill()` /
`delete_skill_via_menu()` teardown applies.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Status |
|---|---|---|
| Model selector button (group) | `page.get_by_test_id("model-selector-button")` | **confirmed live on Skill test panel**, on-automation/testids ✓ (pre-existing from ELITEA-1880) |
| Model selector current-name display | `page.get_by_test_id("model-selector-name")` | **confirmed live**, on-automation/testids ✓ |
| Model dropdown option, per model | `page.locator('[data-testid="model-selector-option-{}"]'.format(model_name))` (dynamic) | **confirmed live** for `gpt-5-mini`, `gpt-5.2`, and 10 others enumerated live; on-automation/testids ✓ |
| Settings (gear) button | `page.get_by_test_id("model-settings-button")` | **confirmed live**, on-automation/testids ✓ |
| Model Settings dialog root | `page.get_by_test_id("model-settings-dialog")` | **confirmed live**, on-automation/testids ✓ |
| Reasoning slider (reasoning-capable models only) | `page.get_by_test_id("model-settings-reasoning-slider")` | **confirmed live** for `GPT-5.2`/default `Anthropic Claude 4.5 Sonnet`, on-automation/testids ✓ |
| Reasoning slider level marks (Low/Medium/High) | `page.locator('[data-testid="model-settings-reasoning-level-{}"]'.format(n))` for `n` in `1,2,3` | **confirmed live**, on-automation/testids ✓ — dialog full-text confirms rendered labels are lowercase `low`/`medium`/`high` |
| Creativity slider (non-reasoning models, e.g. gpt-5-mini) | underlying range input: `page.locator('[aria-label="Creativity level"]')` — **no dedicated `data-testid`** on this control per this run's DOM inspection (the reasoning branch got one via ELITEA-1880's `add-data-testid` work; the Creativity/temperature branch did not) | **testid needed: `model-settings-creativity-slider`** on `CreativitySlider.jsx`'s slider wrapper, mirroring `ReasoningSlider.jsx`'s existing `testId="model-settings-reasoning-slider"` prop-threading pattern through the shared `DiscreteSlider.jsx` (see `agent_detail_page.py`'s comment block at the `model_settings_reasoning_slider` field for the exact prior precedent to copy) — this case's step 2 exercises the Creativity slider for `gpt-5-mini`, so the testid is in-scope per the "elements this test touches" rule |
| Max Completion Tokens section | `page.get_by_test_id("model-settings-max-tokens-section")` | **confirmed live**, on-automation/testids ✓ |
| Settings dialog Cancel button | `page.get_by_test_id("model-settings-cancel-button")` | **confirmed live**, on-automation/testids ✓ |
| Settings dialog Apply button | `page.get_by_test_id("model-settings-apply-button")` | **confirmed live, NEW FINDING**: this testid now exists (it did NOT at ELITEA-1880 analysis time — that AFS explicitly noted "Apply button intentionally has NO testid here... do not add unless a future case needs it"). Someone added it since; `AgentDetailPage`'s `LocatorDescriptor` set does not yet have a field for it — implementer should add `model_settings_apply_button = LocatorDescriptor(testid="model-settings-apply-button")` to whichever page object(s) need it (this case's `SkillDetailPage`, and optionally back-filling `AgentDetailPage` as a drive-by since the testid is already there for free) |
| Test panel chat input | `page.get_by_test_id("chat-message-input")` | **confirmed live**, on-automation/testids ✓ (already used inline in `SkillDetailPage.send_test_message()`) |
| Test panel send button | `page.get_by_test_id("chat-send-button")` | **confirmed live**, on-automation/testids ✓ |
| Test panel last AI response text | `page.get_by_test_id("skill-test-last-response")` | **confirmed live**, on-automation/testids ✓ (already `SkillDetailPage.get_last_test_response()`) |

**Summary for the implementer / `add-data-testid`:** ONE testid gap found —
`model-settings-creativity-slider` on `CreativitySlider.jsx` (step 2's
non-reasoning-model branch). Every other element this case touches already
carries a testid, inherited for free from the ELITEA-1880 implementation on
the shared `llm-model-selector` widget. Also flag (not blocking): the
now-live `model-settings-apply-button` testid has no `LocatorDescriptor`
field yet on `AgentDetailPage` or `SkillDetailPage` — add it to
`SkillDetailPage` as part of this case's page-object work.

## Network Behavior
- `POST /api/v2/elitea_core/predict_llm/prompt_lib/399` → `200 OK` (step 3,
  test-message send — the only network call this case's 4 steps make).
- Model selection (step 2/4's dropdown picks) and Settings-dialog field
  edits (slider value changes, Apply/Cancel) fire **no network request** —
  confirmed via `browser_network_requests` across the full run: pure
  client-side React state (`LLMSettings`/`LLMSettingsDialog` hold
  `localSettings`, same as the ELITEA-1880 AFS documented for the Agent
  detail page instance of this same dialog).
- AI test-panel responses arrive over WebSocket per `.agents/testing.md`
  — `wait_for_test_response()`'s content-stabilization polling is the
  correct wait strategy for step 3, not a network-response wait (the
  `predict_llm` POST's `200 OK` confirms the request was accepted; the
  actual streamed content arrives separately).

## Known Defects / Observations Found During Exploration
No functional product defect found. One case-text drift (step 2, see
Coverage Map note) — CLARIFICATION, not a defect, reproduces ELITEA-1880's
already-documented Clarification 1 on a second, independent screen. One
pre-existing, unrelated console warning (MUI Tooltip-on-disabled-button,
traced to the test panel's disabled "Clear the chat" button) — not filed,
noted for completeness only.

## Blocked Steps
None. All 4 case steps were executed end-to-end live against the real DEV
backend on localhost: opening the Skill test panel's model settings,
selecting a non-reasoning model and exercising its Creativity slider,
running a test prompt without error, and switching to a reasoning-capable
model to confirm the Reasoning slider (Low/Medium/High) renders correctly.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_test_panel_llm_model_settings.py`
  (new file — grep of `automation/tests/ui/skills/` found no existing test
  touching the model selector or Settings dialog).
- New `SkillDetailPage` methods needed (mirror `AgentDetailPage`'s existing
  model-selector/model-settings method shapes — `open_model_selector()`,
  `select_llm_model()`, `get_selected_model_name()`,
  `open_model_settings_dialog()`, `is_reasoning_slider_visible()`,
  `get_reasoning_slider_text()`, `close_model_settings_dialog_via_cancel()`
  at `automation/pages/agent_detail_page.py:2720-2870` — same testids,
  same interaction patterns, different page-object class).
- **Discrete-slider interaction (MUI quirk, confirmed live):** do NOT
  `.click()` the visual `<span class="MuiSlider-thumb">` directly — it
  intercepts pointer events and the click times out. Instead:
  `page.locator('[aria-label="Creativity level"]').focus()` (or the
  equivalent `aria-label` for the Reasoning slider, if the implementer
  needs to move it, though this case only needs to confirm the Reasoning
  slider's *presence*, not move it) then
  `page.keyboard.press("ArrowRight")` / `"ArrowLeft"` — mirrors
  `user_profile_settings_page.py`'s `set_speed()` precedent
  (`automation/pages/user_profile_settings_page.py:690-714`).
- `add-data-testid` work needed for ONE element: `model-settings-creativity-slider`
  on `CreativitySlider.jsx` (see Concrete Handles) — thread a `testId` prop
  through the shared `DiscreteSlider.jsx`, mirroring the existing
  `ReasoningSlider.jsx` → `testId="model-settings-reasoning-slider"`
  precedent exactly (`EliteaUI/src/[fsd]/widgets/llm-model-selector/ui/settings/ReasoningSlider.jsx:65-67`).
- No disposable-skill/cleanup infrastructure needed for this case — see §
  Cleanup (model settings are pure client-side state here, unlike
  ELITEA-1880's agent-page instance which persists via a real Save).
- Suggested markers: `p3`, `regression`, `skills` (fast test, no live-LLM
  cost beyond the one required "run a test" step's single message).

## Defect/Clarification Filing
Filed: [EliteaAI/elitea-testing-public#1447](https://github.com/EliteaAI/elitea-testing-public/issues/1447)
— `[Clarification][ELITEA-2436] Step 2's "standard model (gpt5-mini) ...
adjust the reasoning slider" — gpt-5-mini has no reasoning slider`, labels
`question` + `case-text-drift`, per `.agents/profile.md` § Bug filing. Light
dedup search (`gh issue list --label question --state all`) found no
existing tracker issue for ELITEA-1880's sibling Clarification 1 (same root
cause, different screen/case), so this was filed as its own item rather than
assumed-duplicate — the new issue cross-references ELITEA-1880's AFS and
flags the possible sibling relationship for a human to merge/cross-link if
that occurrence turns out to be tracked elsewhere.
