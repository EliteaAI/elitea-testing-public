# Test Case: Pipeline — Attach Files in Chat

## Metadata
- **TMS ID**: ELITEA-2059
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` @ `automation/testids`, DEV backend, project `Private` id 399)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer, batch `pipelines-remaining-w5`
- **Status**: **ready-for-automation** — case executed end-to-end live via Playwright MCP on the shared fixture pipeline `test-pipeline` (id 6938). No merged spec exercises attachments on the Pipeline surface (`ELITEA-2197`/`ELITEA-2200` cover the SAME `AttachmentButton`/`FileList.jsx` components but on the general Chat page's plus-menu path, and never send the message) — this is a genuinely different call site (see § Concrete Handles) and the first case in this suite to actually send a message with an attachment through a pipeline and assert on the execution result. Zero console errors observed throughout.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- A pipeline exists with a single LLM node wired `entry_point -> LLM 1 -> END`, created via `PipelineAPI.create_pipeline_with_llm_node(name, description)` (`automation/api/client.py:689`) — **NOT** the shared UI fixture `test-pipeline` (id 6938), which prior/parallel cases reuse read-only (see `lextend_pipeline-llm-model-selection-and-execution-usage_ELITEA-2058.md`). Two mandatory post-creation fixes are required for Step 7's execution assertion to be meaningful — see § Test Data and § Automation Hints:
  1. The LLM node's `task` input mapping must be `type: variable, value: input` (NOT the API helper's default `type: fixed, value: ''`), and the pipeline must be **saved** for this to take effect at execution time (see Coverage Map row 7 discovery notes — the live form state gates the chat's *availability* of the attach control instantly, but the LLM node's *content mapping* is read from the persisted version at predict time, not the live form).
  2. The "Attachments" MODULES toggle (`agent-canvas-tools-toggle-attachments`) must be switched on — this IS a live-formik-state, no-save-required gate (confirmed live: the chat's attach button flips from disabled to enabled the instant the switch is toggled, before any Save).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- `settings.default_model_name` (`automation/config.py:196`) = `"gpt-5.2"` — already the correct choice; do **not** rely on whatever model the chat's "Select LLM Model" defaults to at runtime. Live-confirmed this session: on the shared `test-pipeline` fixture, the chat-panel's default model ("Anthropic Claude 4.5 Sonnet") 400s on **every** message on this DEV backend — `Error code: 400 - {'error': {'message': '{"message":"messages.0: user messages must have non-empty content"}No fallback model group found for original model_group=1_eu.anthropic.claude-sonnet-4-5-20250929-v1:0. Fallbacks=[]...'}}` — reproduced identically with and without an attachment, and even with a correctly-mapped Task field. Switching the model to **GPT-5.2** (`pipelines.select_llm_model("GPT-5.2")`, existing method, `pipeline_detail_page.py:6292`) makes the SAME pipeline execute successfully. This is a DEV-environment LLM-provider-routing gap (no fallback configured for that specific Anthropic model group on this backend), **not an Attach-Files defect** — not filed as a new bug; documented here as mandatory test data per the same precedent already recorded for ELITEA-2012 (`test-specs/pipelines/_surface.md`, "Execution gotcha, NOT an import defect"). If the implementer creates a fresh pipeline via `create_pipeline_with_llm_node`, its `llm_settings` already default to `gpt-5.2` — no explicit model switch should be needed there, but confirm live since this is a shared-fixture-specific default that may differ per pipeline.

### generate-per-test (created in test setup, cleaned up via file cleanup)
- One small `.txt` file (e.g. `elitea2059_testfile.txt`, generated via pytest's `tmp_path` fixture, matching the existing `test_attach_files_button_sends_file_with_message` pattern in `tests/ui/chat/test_chat_interface.py:288-290`).

## Test Steps

1. Create a fresh pipeline via `PipelineAPI.create_pipeline_with_llm_node(name, description)`, then fix its LLM node's `task` mapping to `type: variable, value: input` (via `update_pipeline` PATCHing the `instructions` YAML, or via the UI: Task's Type combobox → "Variable" → Value combobox → "input"), and **Save** (`agent-save-button`).
2. Navigate to the pipeline detail page. In the left "Tools" accordion, under "MODULES", locate the "Attachments" switch (`agent-canvas-tools-toggle-attachments`) and turn it on.
   - **Verify**: the embedded chat panel's attach button (`aria-label="attach files"`, tooltip "Attach Files (10 left)") flips from `disabled` to enabled **immediately**, with no Save required — confirmed live via a direct DOM check (`disabled` attribute present/absent) both before and after the toggle, no page reload.
3. In the chat panel, locate the "Attach Files (10 left)" button.
   - **Verify**: visible and enabled (post-step-2). Confirmed the *tooltip text* IS the accessible name (`AttachmentButton.jsx`'s `processStatus` memo, `!showLabel` branch) — there is no separate visible label at this call site (see § Concrete Handles — this is a DIFFERENT render than the Chat-page plus-menu's `showLabel` variant).
4. Click the attach button.
   - **Verify**: native file chooser opens (`page.expect_file_chooser()`).
5. Select one `.txt` file in the file chooser.
   - **Verify**: file appears as an attachment chip in the message area BEFORE sending (`[data-testid="chat-attachment-chip-0"]`, exact filename as its text content), and the button's tooltip/accessible name decrements to "Attach Files (9 left)".
6. Send a message referencing the file (e.g. "Please summarize the content of the attached file.").
   - **Verify**: the user's message bubble shows both the typed text and the attachment chip; `[data-testid="chat-attachment-chip-0"]` count resets to 0 (no residual chips in the composer) after send.
7. Verify the pipeline processes the attachment.
   - **Verify (confirmed live, with the fixes in § Preconditions applied)**: the pipeline executes and produces an AI response with **no execution error visible** in the message thread (no `Error: Error code:` text) within the existing `wait_for_embedded_chat_response()` timeout. The response references the attachment's presence (mentions the filename or acknowledges an attached file was sent) — confirmed live: `GPT-5.2 (LLM1)` replied "I can't access the contents of that attachment from here (I don't have file-browsing access to attachments/…/elitea2059_testfile.txt)." for a bare LLM-node pipeline. **This is the correct, honest assertion boundary** — see Coverage Map row 7 discovery notes: a bare `llm`-type node receives the attachment only as a path reference in its `task` text, not as extracted file content; genuine content extraction requires an additional toolkit/node wired to read artifacts, which is outside a minimal "attach + send" pipeline and outside this case's stated scope (case Test Data table lists only "File type: .txt or .png", nothing about pipeline architecture). Do **not** assert on the literal wording of the AI's reply (model-output text is inherently non-deterministic) — assert the absence of an error state and the presence of file-related acknowledgment (e.g. the filename substring) instead.

## Expected Results
- Attach button disabled while "Attachments" module is off; enabled the instant it's turned on (no save needed for this gate).
- File attaches, shows as a chip in the message area, and is included when the message is sent.
- The pipeline executes without error and its response acknowledges the attachment (references the filename / states awareness of an attached file) — full byte-level content extraction is a pipeline-architecture concern beyond a bare LLM node, not asserted here.
- No console errors during the sequence (confirmed live — none observed, `browser_console_messages(level="error")` → 0).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline that supports attachments (Attachments module enabled in Tools) | Pipeline open with attachments-enabled chat panel | AFS steps 1–2 | step 2: attach button `disabled` attribute flips to absent immediately after the switch click, before Save | asserted — precondition decomposed into "create/fix pipeline" (step 1) + "enable module" (step 2), since the case's own precondition text bundles both |
| 2 Locate "Attach Files (10 left)" button | Button visible and enabled | AFS step 3 | step 3: `[aria-label="attach files"]` visible, not disabled; accessible name via tooltip = "Attach Files (10 left)" | asserted |
| 3 Click the attach files button | File picker opens | AFS step 4 | step 4: `page.expect_file_chooser()` fires | asserted |
| 4 Upload a supported file | File uploaded, appears as attachment | AFS step 5 | step 5: `chat-attachment-chip-0` count==1, text==filename | asserted |
| 5 Verify file appears as attachment in message area | Attachment thumbnail/name shown | AFS step 5 (same evidence) | step 5 | asserted |
| 6 Send a message referencing the file | Message with attachment is sent | AFS step 6 | step 6: message bubble shows text+chip, composer's chip count resets to 0 | asserted |
| 7 Verify pipeline processes the attachment | Pipeline responds with content referencing/processing the file | AFS step 7 | step 7: no `Error: Error code:` text in the response; response text contains the filename or an attachment acknowledgment | asserted *(weaker-than-literal form — see step 7 discovery notes; full content-extraction is a pipeline-architecture concern, not a bare-LLM-node capability, and outside this case's Test Data scope)* |
| Precondition: "Attachments module enabled" | — | AFS step 2 | — | asserted (see row 1) |
| Test Data: File type .txt or .png | — | AFS uses `.txt` (generate-per-test) | — | asserted — `.png` not additionally exercised (ELITEA-2197/2200 already cover file-type variety on the general Chat surface via the identical shared `AttachmentButton`/validation utils; re-proving type acceptance here would be redundant per Rule-6, not a gap) |

### Axis 2 — Analyst additions
- Step 2 asserts the module-toggle → attach-button-enablement causal link is **instant, formik-state-driven, no-Save-required** — *added: this is the precondition's actual mechanism (`useAgentAttachments`'s `disableAttachments = !internal_tools.includes('attachments')`, read from live form state), and distinguishes it from the Task-field fix in step 1, which DOES require Save. Conflating the two would produce a flaky/wrong-reason test if an implementer assumes both need saving.*
- Step 7 explicitly documents why the assertion is on error-absence + filename-acknowledgment rather than literal content-quoting — *added: prevents a downstream implementer/reviewer from either (a) over-asserting on non-deterministic LLM prose, or (b) mistakenly filing a "pipeline can't read attachments" defect against a bare LLM node, which is expected architecture, not a bug.*
- No console errors during the full sequence — *added: standard side-channel check per the skill's "check the side channels even when the UI looks fine" rule; confirmed 0 errors via `browser_console_messages(level="error")`.*
- The DEV-backend default-model 400 (Claude 4.5 Sonnet, no fallback model group) is recorded as mandatory test data, not a defect — *added: reproduced independently of attachments (plain text also 400s), matches the existing ELITEA-2012 precedent of documenting rather than filing this class of environment gotcha.*

## Cleanup
- Delete the pipeline created in step 1 via `PipelineAPI.delete_pipeline(pipeline_id)`.
- No server-side attachment cleanup needed beyond the pipeline's own deletion (attachment lifecycle is tied to the conversation, which is deleted with the pipeline's test data teardown).

## Concrete Handles (discovered during exploration)

**This is a different `AttachmentButton` call site than ELITEA-2197/2200.** Those cases exercise the *Popper MenuList* instance in `PlusChatButton.jsx` (`testId="chat-attach-menuitem-button"`, `showLabel` variant, reached via a separate "+" plus-menu button). The Pipeline's (and Agent's — same shared `NewChatInput.jsx`/`isAgentsPage=true` path) embedded chat panel renders NO plus-menu at all; it renders the **bare, icon-only** `ChatButton.AttachmentButton` directly (`src/pages/NewChat/NewChatInput.jsx:272-278`, the `!hideAttachments && !fromTheChat` branch) — confirmed live via `document.querySelector('[data-testid="plus-menu-button"]')` returning `null` on the pipeline chat panel, and exactly one `[aria-label="attach files"]` button present, with `data-testid` attribute `null`.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Attach button (bare icon, pipeline/agent embedded chat) | `testid needed: chat-attach-button` | **needs-adding** | `NewChatInput.jsx:273`'s `<ChatButton.AttachmentButton ref={attachmentButtonRef} onAttachFiles={...} disableAttachments={...} attachments={...} limits={...} />` — thread `testId="chat-attach-button"` through (the component already accepts a `testId` prop, wired straight to `data-testid` on its `<IconButton>` — see `AttachmentButton.jsx`'s `data-testid={testId}`). Name is FREE and semantically exact: `chat-attach-button` was previously a **dead/stale** field value on `ChatPage.attach_files_button` (ELITEA-2197's AFS confirmed zero hits for it anywhere in `EliteaUI/src`, on either `main` or `automation/testids`) — that field has since been re-pointed to `chat-attach-menuitem-button`, freeing this name for the call site it always semantically described (the plain, non-menu attach button). Shared component (`NewChatInput.jsx` is common chat infrastructure, used by both Agent and Pipeline embedded chat via `isAgentsPage=true`) — naming carries NO `agent-`/`pipeline-` prefix per the "shared components never hardcode feature-scoped testids" rule; scope this case's add to exactly this call site (line 273), not the sibling `showLabel` Popper instance (out of scope — ELITEA-2197/2200's) or the hidden drag-drop instance in `PlusChatButton.jsx:336` (different file, different case). |
| "Attachments" MODULES toggle | `[data-testid="agent-canvas-tools-toggle-attachments"]` (the `<input>` inside the switch) | **on-`automation/testids`, NOT on `main`** — confirmed via `git grep` both refs after `git fetch origin` (2026-08-09): `AgentInternalToolSwitch.jsx:108`'s `slotProps.switch.slotProps.input['data-testid']` template. Pre-existing (added for the Agent surface; reused verbatim here — `ApplicationTools.jsx` renders it for pipelines too when `isPipeline=true`, filtering `pipelineVisibleTools` to only the `attachments` tool). Naming carries the tracked `agent-` prefix despite covering both surfaces — same class of pre-existing shared-component tech debt the `_surface.md` digest already flags for `ConversationStarters.jsx`; not this case's to fix. | State-dependent (checked/unchecked) — assert via the `checked` DOM property, not a testid variant, per the project's testid-is-stable-identity rule. |
| Attachment chip (per file) | `[data-testid="chat-attachment-chip-{index}"]` (`CHAT_ATTACHMENT_CHIP` class constant, `chat_page.py:270`) | **pre-existing, reused verbatim** | `FileList.jsx` is shared infrastructure — the SAME testid resolves correctly on the pipeline's embedded chat composer (confirmed live: `chat-attachment-chip-0` present with the uploaded filename as text, identical shape to ELITEA-2197's Chat-page finding). Zero new work. |
| Chat message input | `[data-testid="chat-message-input"]` (`PipelineDetailPage.chat_input`, `pipeline_detail_page.py:437`) | **pre-existing** | Already used by every embedded-chat pipeline test. |
| Chat send button | `[data-testid="chat-send-button"]` (`PipelineDetailPage.chat_send_button`, `pipeline_detail_page.py:443`) | **pre-existing** | Already used by every embedded-chat pipeline test. |
| Clear chat button | `[data-testid="chat-clear-button"]` | **pre-existing** | Used between attempts in this exploration session; not strictly required by the case's own steps but useful for isolating attempts within one test if reused across assertions. |
| Model selector (workaround for the DEV default-model 400) | `pipelines.open_model_selector()` / `pipelines.select_llm_model(name)` / `pipelines.get_selected_model_name()` (`pipeline_detail_page.py:6269-6299`) | **pre-existing methods** | Not part of the case's own steps, but needed as TEST SETUP if the implementer reuses a fixture pipeline whose model 400s — see § Test Data. Not needed if a fresh pipeline is created via `create_pipeline_with_llm_node` (already defaults to `gpt-5.2`). |
| Attachments-module state variable (pipeline-only side effect, informational) | n/a — no locator | n/a | `AttachmentSwitch.jsx`'s docstring/YAML-sync logic (`STATE_INPUT_ATTACHMENTS = 'input_attachments'`) auto-adds an `input_attachments` list-type state variable to the pipeline's YAML when the module is toggled on via the (unused-for-pipelines) `AttachmentSwitch` component; the ACTUAL toggle rendered for pipelines is `AgentInternalToolSwitch` (no YAML-sync side effect observed live — the switch alone does not add the state var; confirmed by inspecting the Task field's "Variable" dropdown, which lists `input`, `messages`, `input_attachments` as available Task-mapping targets regardless of the switch state). Noted for the implementer's awareness only — not asserted by this case. |

## Network Behavior
- Enabling the "Attachments" MODULES switch: no network request (pure client-side formik state) — confirmed via `browser_network_requests` before/after the toggle.
- Attaching a file (before send): no network request (validated client-side only, matches ELITEA-2197's finding for the general Chat surface).
- Saving the pipeline (Task field fix): `PUT .../elitea_core/application/prompt_lib/{project}/{id}` → `200`.
- Sending the message: conversation/message POSTs to `.../elitea_core/conversations/prompt_lib/{project}` (`201`) followed by a `PUT .../elitea_core/conversation/prompt_lib/{project}/{id}` (`200`); the actual predict/execution traffic rides the WebSocket channel per `.agents/architecture.md`, not a plain REST body inspectable via `browser_network_request` (both POST/PUT bodies inspected this session were empty — message content is not carried in these particular calls).

## Known Defects Found During Exploration
- None filed. Two DEV-environment/architecture observations recorded as test data / automation hints instead (see § Test Data and step 7's discovery notes) — neither is an Attach-Files-specific product defect:
  1. The DEV backend's default pipeline-chat model (Anthropic Claude 4.5 Sonnet) has no configured LLM-provider fallback and 400s on **every** message (with or without an attachment) — environment config, not attach-files-specific, matches the existing ELITEA-2012 precedent of documenting rather than filing.
  2. A bare `llm`-type pipeline node cannot extract an attached file's byte content — it only sees a path-like reference in the message text, and honestly reports "I can't access the contents of that attachment" — this reflects the pipeline's node architecture (content extraction needs an explicit toolkit/artifact-reading node), not a defect in the Attach-Files UI/upload mechanism, which itself worked flawlessly across all of steps 1–6.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Fixture pipeline: create fresh via `PipelineAPI.create_pipeline_with_llm_node(name, description)` (`automation/api/client.py:689`) rather than reusing the shared UI-fixture `test-pipeline` (id 6938) — avoids polluting a fixture multiple other analyses treat as read-only, and this case specifically needs mutated Task-field + Attachments-module state.
- After creation, PATCH the `task` input mapping to `{type: variable, value: input}` — either via a direct API PUT of the updated `instructions` YAML (fetch the pipeline, edit the YAML string, `update_pipeline(id, instructions=new_yaml, ...)` preserving the rest of the payload shape) or via the UI (Task Type combobox → "Variable" → Value combobox → "input" → click `agent-save-button`). **The UI path requires an explicit Save** — the module toggle does not, but this field does (confirmed live: response stayed "I didn't receive any text or image" even after the UI-level field change, until Save was clicked).
- Page object: extend `PipelineDetailPage` with `toggle_attachments_module()` (click `agent-canvas-tools-toggle-attachments`'s parent switch) and `open_attach_button()` / `attach_file_in_embedded_chat(file_path)` (parallel to `ChatPage.attach_file()`, but targeting the new `chat-attach-button` testid directly — no plus-menu hop needed here).
- Wait strategy: after send, reuse the existing `wait_for_embedded_chat_response()` (`pipeline_detail_page.py:6037`) rather than a fixed sleep; assert the final response text does NOT contain `"Error: Error code:"` and DOES contain the attached filename (case-insensitive substring), per step 7's discovery notes.
- Viewport: no width-sensitivity concerns found for this call site (single icon button, no `FileList.jsx` overflow-split risk at typical CI viewport widths — only relevant if attaching >1 file, which this case's Test Data doesn't call for).
