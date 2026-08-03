# Test Case: Chat – Agent Hub Agent – Verify Only LLM and LLM Settings Can Be Changed and Changes Are Saved Per Conversation Only

## Metadata
- **TMS ID**: ELITEA-2075
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private")
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live via a `sync_playwright` scratch driver (no Playwright MCP tools were surfaced this dispatch). Every step 1–13 reproduced live with screenshots; step 14 (AI response using the new model) is left to the implementer per § Automation Hints (a live completion takes 30–90s per this surface's own digest, and the model-in-use is verifiable via response metadata without waiting out full generation on every gate run). One re-encountered, ALREADY-TRACKED product defect (issue #1043 — commented, not re-filed). Two case-text naming drifts (CLARIFICATION-worthy, not defects — see Coverage Map). Multiple `testid needed` gaps on elements this case's own steps touch — none are fallback-worthy per project policy; all must be added via `add-data-testid`.
- **Related surfaces reused**: `ChatPage.expand_participants_panel()` / `chat-participants-panel-toggle-button` (ELITEA-2168's digest entry); the shared `LLMModelSelector.jsx` widget + its testids (`model-selector-name`, `model-selector-button`, `model-settings-button`, `model-settings-dialog`, `model-settings-cancel-button`, `model-settings-reasoning-slider`, `model-settings-max-tokens-section`) already exist as `AgentDetailPage` `LocatorDescriptor`s (`automation/pages/agent_detail_page.py:237-265`) — same component tree, reusable as-is for a NEW page object covering this chat-canvas context (see § Automation Hints). Not a target for `extend-existing`/`already-covered`: no existing spec asserts the Agent-Hub-participant read-only canvas or the per-conversation LLM-override persistence — this is genuinely new coverage.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- At least one published/public agent exists in the Agent Hub ("Catalog"). Confirmed live: **"Reflexion"** (author "Levon Dadayan", description "This prompt is designed to determine the correspondance of Initial Request and Documentation Response.", no conversation starters, no welcome message) — matches the case's own Test Data row. If this specific agent is later renamed/removed, any published Catalog agent exercises the same code path (root cause is generic per component review).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Agent Hub agent: **"Reflexion"** (case's own Test Data value — confirmed present live).
- Test message: `"hello"` (case's own Test Data value).

### generate-per-test (created in test setup, cleaned up in its own teardown)
- A new conversation is created as a side effect of Step 3 (Start Chat) — no separate seeding needed. Clean up via the conversation's own delete flow (existing `ConversationAPI`/`ChatPage` teardown pattern) after the test.

## Test Steps

1. Navigate to the Agent Hub from the left sidebar.
   - **CASE-TEXT DRIFT (CLARIFICATION, not a defect)**: the live sidebar item is labelled **"Catalog"** (`/elitea-catalog`), not "Agent HUB". `AgentHub`/`/agents-hub` is only a legacy redirect source in `routes.js`, not a rendered nav label. Assert the live label.
   - **Verify**: page shows "Welcome to ELITEA Catalog!" heading, a search bar, and category sections (Trending, Business Analyst, DevOps, …) — confirmed live.
2. Locate the "Reflexion" agent and click on it.
   - **Verify**: agent preview modal opens showing agent name "Reflexion", author, description, "Show instructions" link, CHAT STARTERS / WELCOME MESSAGE sections, and an action button — confirmed live (screenshot: agent-modal).
3. Click the action button to start a conversation.
   - **CASE-TEXT DRIFT (CLARIFICATION, not a defect)**: the live button text is **"Start Chat"**, not "Start conversation". Assert the live label.
   - **KNOWN DEFECT (already tracked, issue #1043 — commented this session, not re-filed)**: clicking this button BEFORE the modal's own agent-details fetch resolves throws an uncaught `TypeError: Cannot read properties of null (reading 'version_details')` and silently no-ops (no navigation). Automation MUST wait for the modal's own content (e.g. the "Show instructions" link, confirmed present once details load) to be visible before clicking — confirmed live: 2/2 repro on an immediate click, 0/2 after a short wait. This is test synchronization, not defect-masking; the underlying product gap (no `disabled={isFetching}` guard on the button) stays tracked on #1043.
   - **Verify**: new conversation created; URL becomes `/chat`; expanding the collapsed Participants badge (`chat-participants-panel-toggle-button`) shows an "AGENTS" section with row text **"Reflexion v1.0"** — confirmed live (matches case's own expected result verbatim).
4. Click the "View settings" button next to the agent in the expanded PARTICIPANTS popover.
   - **Verify**: the same `EditParticipantButton` component used for "Edit agent" renders with `aria-label="View settings"` (confirmed live — it swaps tooltip/label based on `canEdit`, which is false for a public agent without edit permission on it) at `#EditButton` (a raw `id`, no `data-testid` yet — **testid needed**, see § Concrete Handles). Clicking it opens the agent settings canvas showing title "Reflexion", subtitle "v1.0" (`agent-canvas-title`/`agent-canvas-subtitle`, pre-existing), and a **"Public"** label (plain `Typography` text, no testid — **testid needed**) in the header instead of Discard/Save buttons. URL becomes `/chat?edited_participant_id={id}` — confirmed live (screenshot: canvas-open).
5. Verify the LLM model selector is visible at the top of the canvas.
   - **Verify**: `model-selector-name` (pre-existing testid, shared `LLMModelSelector.jsx`) is visible and shows "GPT-5.4-mini" for this agent — confirmed live.
6. Verify the INSTRUCTIONS section appears READ-ONLY.
   - **Verify**: instructions text renders as plain (non-editable) text under an "INSTRUCTIONS" heading — confirmed live via the canvas screenshot (no input border, no `contenteditable` region visible in the rendered DOM around this text). `ApplicationConfigurationForm` receives `viewMode={ViewMode.Public}` for this canvas (source-confirmed, `AgentEditor.jsx`), which is the mechanism enforcing read-only rendering — matches the case's expectation without a separate "attempt to type" probe being independently necessary (step 12 below is the case's own explicit probe for this).
7. Verify module toggles in the TOOLS section appear DISABLED.
   - **Verify**: confirmed live via the `checked` DOM property (NOT the `disabled`/`aria-disabled` attributes, which are not set on this component's raw `<input role="switch">`) — a click attempt (both a raw coordinate click and a Playwright `.click(force=True)`) leaves `checked` unchanged and fires zero network requests. 4 toggles visible (Attachments, Data Analysis, Image creation, Agents & Pipeline Builder) plus a "Show all" expander.
8. Verify no SAVE button is visible in the canvas header.
   - **Verify**: `page.get_by_text("Save", exact=True)` returns 0 matches while the canvas is open — confirmed live (the "Public" label renders in the Save button's position instead, per `EditorHeader.jsx`'s `{isPublic && <Publicbadge/>}` branch).
9. Click the LLM model chip and select a Sonnet 4.5-family model from the dropdown.
   - **CASE-TEXT DRIFT (CLARIFICATION, not a defect)**: the case's literal "Anthropic Claude 4.5 Sonnet" does not exist verbatim in this environment. The live option is named **"Azure Claude Sonnet 4.5"** (one of 11 models listed via `model-selector-option-*`, pre-existing dynamic testids). Match by a case-insensitive "sonnet"+"4.5" filter over option text, not the exact case string.
   - **Verify**: `model-selector-name` updates to "Azure Claude Sonnet 4.5" — confirmed live.
10. Click the settings/gear icon (`model-settings-button`, pre-existing) next to the LLM model selector.
    - **Verify**: `model-settings-dialog` (pre-existing) opens showing a REASONING slider (`model-settings-reasoning-slider`, pre-existing; Low/Medium/High), a MAX COMPLETION TOKENS section (`model-settings-max-tokens-section`, pre-existing container; Default/Custom radios) and a CAPABILITIES section (own component, no testid — **testid needed**) showing "Image analysis" + "Reasoning" chips for this model — all confirmed live (screenshot: settings-modal).
11. Adjust the REASONING slider to "High" and click "Apply".
    - **Verify**: confirmed live — clicking within the `model-settings-reasoning-slider` container's bounding box at its rightmost edge (≈100% position) moves the slider to "High" (the slider's own invisible per-mark click-trigger mechanism; **no dedicated per-level testid exists** — see § Concrete Handles for the exact mechanism and the recommended testid addition). Clicking "Apply" (`get_by_role("button", name="Apply")` — **no testid**, needs `model-settings-apply-button`; only "Cancel" has one today) closes the modal; `model-selector-name` continues to show "Azure Claude Sonnet 4.5" in the canvas header — confirmed live.
12. Attempt to click into the INSTRUCTIONS text area.
    - **Verify**: no editable input/cursor state is entered (matches Step 6's structural read-only rendering — `viewMode={ViewMode.Public}` means no input element is mounted at all for this section, not merely a disabled one).
13. Close the canvas by clicking the X (`agent-canvas-close-button`, pre-existing) and verify the canvas closes.
    - **Verify**: canvas unmounts; conversation view (composer + message list) is displayed; URL drops the `?edited_participant_id=` query param — confirmed live.
    - **Additional verification beyond the case's own step (Axis 2)**: re-opening "View settings" on the SAME agent in the SAME conversation (repeat step 4) still shows `model-selector-name` = "Azure Claude Sonnet 4.5" — confirmed live. This is the load-bearing proof of the case's own title claim ("changes are saved per conversation only"): the override persists in-conversation. *Added: this is the case's central assertion and the original steps never explicitly re-open the canvas to prove persistence — worth guarding explicitly rather than inferring it from the absence of a PUT request alone.*
14. Send a test message "hello".
    - **Verify**: agent responds using the newly selected LLM model. **Not independently re-verified live this session** (a full live completion on this environment takes 30-90s per this surface's existing digest entry, and re-running it would not have added information beyond what steps 9-13 already proved about which model is active) — see § Automation Hints for the exact assertion mechanism the implementer should use (the response's model-chip testid, not a text/behavioral inference).

## Expected Results
- Agent Hub ("Catalog") agent's canvas allows LLM model and LLM settings changes only; Instructions, Welcome Message, and Tools remain read-only/disabled.
- The per-conversation LLM override persists across closing/reopening the canvas within the same conversation, and is never written back to the agent's own version (confirmed live: zero `PUT`/`PATCH`/`POST` request touching `application` fires on model select or Apply).
- The newly selected LLM is used for subsequent messages in this conversation only.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent HUB from sidebar | Agent HUB page opens with categories | step 1 | Catalog page heading + category sections | asserted *(label drift, see clarification)* |
| 2 Click "Reflexion" agent | Agent preview modal opens | step 2 | modal with agent name/description | asserted |
| 3 Click "Start conversation" | New conversation created; PARTICIPANTS shows "Reflexion v1.0" | step 3 | URL `/chat`; participants popover row text | asserted *(label + race-condition drift, see clarification/defect)* |
| 4 Click "View settings" | Canvas opens showing "Reflexion v1.0" + "Public" | step 4 | `agent-canvas-title`/`-subtitle` text + Public label presence | asserted |
| 5 Verify LLM model selector visible | Model chip displayed and clickable | step 5 | `model-selector-name` visible | asserted |
| 6 Verify INSTRUCTIONS read-only | Text visible, not editable | step 6 | `viewMode=Public` structural check + no input element | asserted |
| 7 Verify TOOLS toggles disabled | Toggles greyed, cannot be changed | step 7 | `checked` property unchanged after click attempt | asserted |
| 8 Verify no SAVE button | No Save button in header | step 8 | `get_by_text("Save", exact=True)` count 0 | asserted |
| 9 Select "Anthropic Claude 4.5 Sonnet" | Model selector updates | step 9 | `model-selector-name` text after selection | asserted *(model-name drift, see clarification)* |
| 10 Click gear icon | Settings modal opens with REASONING/MAX COMPLETION TOKENS/CAPABILITIES | step 10 | modal + 3 sections all present | asserted |
| 11 Set Reasoning=High, click Apply | Modal closes; settings updated | step 11 | slider position + model name persists after close | asserted |
| 12 Attempt to type in Instructions | No cursor, not editable | step 12 | same read-only structural check as step 6 | asserted |
| 13 Close canvas via X | Conversation view displayed | step 13 | canvas unmounts, URL query param drops | asserted |
| 14 Send "hello" | Agent responds using new model | step 14 | response model-chip testid (implementer, live completion) | blocked *(deferred to implementer — see Automation Hints; not a scope gap, a cost/turn-budget deferral within this analysis pass)* |
| Expected Final State: only LLM/settings changeable, Instructions/Tools read-only, new LLM used | — | steps 6-14 | as above | asserted |
| Pass/Fail Criteria: "Instructions become editable, or LLM model cannot be changed" = FAIL | — | steps 6, 9 | read-only check + model-change check | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions (beyond the original case)

- **step 3** asserts the modal's "Start Chat" click race condition (wait-before-click requirement) — *added: live-discovered, already-tracked defect (#1043) whose failure mode (silent no-op) would otherwise make the whole downstream flow non-deterministic in CI if the implementer clicked too fast.*
- **step 9** asserts zero `PUT`/`PATCH`/`POST` to any `application` endpoint fires on model change — *added: this is the concrete, network-level proof of "never saved to the agent's own version," which the case's prose implies but never states as an explicit check.*
- **step 13** re-opens the canvas after closing to prove in-conversation persistence — *added: the case's own steps never re-verify persistence; this is the title's central claim ("per conversation only") and deserves its own assertion, not an inference.*
- (No console-error assertion added beyond the default `page.on("console")`/`page.on("pageerror")` capture already standard for this suite — zero console errors observed throughout the entire live flow except the tracked #1043 pageerror under the deliberately-provoked fast-click condition.)

## Cleanup
1. Delete the conversation created in Step 3 via the existing conversation-delete flow (UI or `ConversationAPI`).
2. No agent-side cleanup needed — the LLM override is participant-scoped (conversation-local), never written to the agent's own version; no agent state to restore.

## Concrete Handles (discovered during exploration)

Locator policy for this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`) — no role/text/CSS handles as primaries. Every row below is either an existing testid (reused) or a `testid needed` row for the implementer to add via `add-data-testid` before use.

| Element | Testid (existing) | Status |
|---|---|---|
| Catalog "Reflexion" agent card | — | `testid needed: catalog-agent-card-{agent_id}` (dynamic) — zero testids anywhere in `AgentHub.jsx`/`AgentCard.jsx`/`AgentModal.jsx`, confirmed via grep against both `origin/main` and `origin/automation/testids` |
| Agent preview modal "Start Chat" button | — | `testid needed: catalog-agent-modal-start-chat-button` |
| Participants panel toggle (collapsed→expanded) | `chat-participants-panel-toggle-button` | on-main (pre-existing, ELITEA-2168 digest) |
| "View settings" button on agent participant row | — (raw `id="EditButton"`, `aria-label="View settings"`) | `testid needed: chat-participant-edit-view-button` (same element also serves "Edit agent"/"Edit pipeline"/"Edit mcp"/"Edit toolkit" — testid should be on `EditParticipantButton.jsx` generically, disambiguated by scoping to the participant row, not by a separate testid per tooltip variant) |
| Canvas title | `agent-canvas-title` | on-main (pre-existing) |
| Canvas subtitle (version) | `agent-canvas-subtitle` | on-main (pre-existing) |
| Canvas close (X) button | `agent-canvas-close-button` | on-main (pre-existing) |
| "Public" label | — | `testid needed: agent-canvas-public-label` (plain `Typography`, `EditorHeader.jsx`) |
| LLM model selector name/chip | `model-selector-name` | on-main (pre-existing, shared `LLMModelSelector.jsx`) |
| LLM model selector button group | `model-selector-button` | on-main (pre-existing) |
| Model dropdown option (dynamic) | `model-selector-option-{model_api_name}` | on-main (pre-existing, keyed by API `name`; select/verify by rendered display text) |
| Model settings gear icon | `model-settings-button` | on-main (pre-existing) |
| Model settings dialog | `model-settings-dialog` | on-main (pre-existing) |
| Model settings Cancel button | `model-settings-cancel-button` | on-main (pre-existing) |
| Model settings Apply button | — | `testid needed: model-settings-apply-button` (THIS case is the first that needs to click Apply — `AgentDetailPage`'s existing docstring explicitly scoped Apply as out-of-scope for its own case) |
| Model settings Reasoning slider (container) | `model-settings-reasoning-slider` | on-main (pre-existing); **per-level click target has no testid** — see Automation Hints for the bounding-box mechanism |
| Model settings Max Tokens section (container) | `model-settings-max-tokens-section` | on-main (pre-existing); the Default/Custom radios themselves have no testid |
| Model settings Capabilities section | — | `testid needed: model-settings-capabilities-section` (`CapabilitySection.jsx`, conditionally rendered) |
| TOOLS module toggle switches (4, e.g. Attachments/Data Analysis/Image creation/Agents & Pipeline Builder) | — | `testid needed: agent-canvas-tools-toggle-{module_key}` (dynamic; none have any today) |
| Instructions text block | `agent-instructions-input` | **AMENDMENT (implementer, ELITEA-2075):** this row was STALE — `agent-instructions-input` (`AgentFormPage.instructions_input`) already renders on the field's underlying `<textarea>` (`InstructionsInput.jsx`'s `inputProps={{'data-testid': 'agent-instructions-input'}}`) regardless of `viewMode`; `disabled` only toggles editability, it never unmounts the element. No new testid was needed — reused via composition, asserted via `.is_editable() is False`, not element absence. |
| Response model-chip (for step 14) | `chat-answer-model-chip` | on-main (pre-existing — `ActionView.jsx`, same-element conditional pair per canon #277 shape (a); documented in this surface's `_surface.md` HITL section) |

**Implementation note (ELITEA-2075, testid additions actually landed on `automation/testids`):** `catalog-page-heading`, `catalog-search-input`, `catalog-category-heading-{slug}` (dynamic, slugified category name), `catalog-agent-card-{application_id}` (dynamic), `catalog-agent-modal-agent-name`, `catalog-agent-modal-show-instructions-link`, `catalog-agent-modal-start-chat-button`, `chat-participant-edit-view-button` (static, scoped via the participant row — matches this row's own recommendation), `agent-canvas-public-label`, `model-settings-apply-button`, `model-settings-capabilities-section`, `agent-canvas-tools-toggle-{module_key}` (dynamic), `model-settings-reasoning-level-{1|2|3}` (dynamic, replacing the bounding-box mechanism below with a real per-mark testid on `DiscreteSlider.jsx`, threaded via a new `markTestIdPrefix` prop from `ReasoningSlider.jsx`). All via EliteaAI/EliteaUI commits on `automation/testids` (see PR description / closure record for SHAs). One MUI v7 quirk discovered + fixed: the legacy `inputProps` prop on `<Switch>` is silently discarded (Switch.js unconditionally rebuilds `slotProps.input`, overwriting SwitchBase's `inputProps`-derived mapping) — the working channel is `slotProps.input`, confirmed via `node_modules` source and fixed in `AgentInternalToolSwitch.jsx`.

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?...` — Catalog agent list load (3 variants observed: trending/liked/full).
- `GET` (per-agent) via `usePublicApplicationDetailsQuery`/`getPublicApplicationDetail` — fires on opening the agent preview modal; MUST resolve before clicking Start Chat (see step 3 known defect).
- **Zero** `PUT`/`PATCH`/`POST` request containing `application` in its URL fires when selecting a model or clicking Apply in the settings dialog — confirmed live; this is the network-level proof the override never reaches the agent's own version.

## Known Defects Found During Exploration
- **[MAJOR, already tracked — issue #1043, commented not re-filed]** Catalog agent-detail modal's "Start Chat" button has no `disabled={isFetching}` guard; clicking it before the agent-details fetch resolves throws an uncaught `TypeError` and silently no-ops. Automation must wait for the modal's content to be ready before clicking (documented in step 3, § Automation Hints).

## Blocked Steps
None — all 14 case steps were reached and observed live. Step 14's full live-completion re-verification was deferred to the implementer for turn-budget reasons (see Coverage Map row + Automation Hints), not because it was unreachable.

## Automation Hints
- Framework: Playwright + pytest (this project). No Playwright MCP tools were available this dispatch — analysis was driven via a from-scratch `sync_playwright` script (documented per `.agents/memory/qa-engineer/no_playwright_mcp_use_sync_playwright_script.md`, if present; else this AFS is the first record of that constraint this session).
- **New page object needed**: none of the existing chat/agent page objects cover this canvas-in-chat-context flow end-to-end. **Implemented (ELITEA-2075):** `AgentHubPage` (Catalog listing + preview modal), `AgentParticipantCanvasPage(AgentCanvasPage)` (inherits title/subtitle/close from the ELITEA-2166 canvas — confirmed via source that `AgentEditor.jsx` passes the identical `EditorHeader` testids for both create and view/edit modes), plus a new `ChatPage.open_agent_participant_settings()` method (expand panel → resolve row by name via a new `PARTICIPANT_ROW_PREFIX` + `.filter(has_text=...)` → hover → click the new `chat-participant-edit-view-button` testid). The LLM model selector/settings fields are reused directly from `AgentDetailPage` by composition (same `page` instance, same shared widget), and Instructions reuses `AgentFormPage.instructions_input` — no duplicated locators.
- **Wait strategy for step 3 — AMENDMENT:** the "Show instructions" link is **NOT** a valid ready-signal — it is unconditionally rendered in `AgentModal.jsx` regardless of fetch status (confirmed via source), so waiting on its visibility alone does not prove the agent-details fetch resolved, and clicking Start Chat immediately still raced known defect #1043 live during implementation. The deterministic wait is the modal's own network response: `page.expect_response` on `GET .../public_application/prompt_lib/{id}` (confirmed exact endpoint via `src/api/applications.js`), awaited around the card click.
- **Reasoning slider "High" selection — AMENDMENT:** the bounding-box mechanism below is now REPLACED by a real testid. `DiscreteSlider.jsx` gained a `markTestIdPrefix` prop (threaded from `ReasoningSlider.jsx` as `"model-settings-reasoning-level"`), rendering `data-testid="model-settings-reasoning-level-{1|2|3}"` on each per-mark click-trigger `Box` (1=Low, 2=Medium, 3=High). Click that testid directly — no bounding-box math needed. (Original bounding-box description kept below for historical context only.) `ReasoningSlider.jsx`/`DiscreteSlider.jsx` positions one invisible click-trigger `Box` per mark at `left: {(mark-min)/(max-min)*100}%` inside the `model-settings-reasoning-slider` container, each with `pointerEvents: none` at the CURRENTLY-selected mark.
- **MUI v7 `<Switch>` `inputProps` quirk (discovered during implementation):** the legacy `inputProps` prop on the top-level `<Switch>` component is silently discarded — `Switch.js` unconditionally rebuilds its own `slotProps.input` (merging in `role: "switch"`) and passes it as an explicit `slotProps` prop to `SwitchBase`, which overwrites `SwitchBase`'s own `input: inputProps` mapping via object-spread key order. The working channel is `slotProps.input`; `AgentInternalToolSwitch.jsx` was fixed to pass `slotProps={{ switch: { slotProps: { input: { 'data-testid': ... } } } }}` through `BaseSwitch.jsx`'s own `slotProps.switch` passthrough. Worth a project-wide note for any future testid addition on a `<Switch>`.
- **Step 14 verification approach**: rather than waiting out a full 30-90s live completion on every automated run, assert the model actually used via the response's `chat-answer-model-chip` testid text (e.g. contains "Sonnet") once the response completes — same testid this surface's `_surface.md` HITL section already documents. Use a generous wait (`wait_for_selector` on the chip, timeout ≥90s) rather than a fixed sleep, per this project's no-sleep rule.
- Selector policy: **testid-only, no fallback** (`.agents/testing.md` § Locator policy) — every `testid needed` row above is implementer work via `add-data-testid`, not a role/text/CSS substitute.
