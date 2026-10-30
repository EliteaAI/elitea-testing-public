# Test Case: Pipeline — Attach Files in Chat

## Metadata
- **TMS ID**: ELITEA-2059
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: DEV as deployed (`https://dev.elitea.ai`, `APP_PREFIX=/app`, project `Private` id 575) — see § Adjustment
- **User set**: `${TEST_USER}` (DEV: Keycloak API login via `auth_state`/`dev_storage_state.py`)
- **Analyst**: qa-engineer, adjust-round for issue #2408 (overturned triage #2412)
- **Status**: **ready-for-automation** — re-executed end-to-end live on DEV (API-driven setup + Playwright-driven UI verification, both confirmed; see § Adjustment). The corrected flow (artifact toolkit attached + wired into the LLM node, Attachments module on) was built and run twice: once via a hand-authored pipeline YAML (API) to prove the mechanism, once by driving the actual UI attach flow end-to-end from an empty pipeline (add LLM node → "+ Toolkit" popper → select → Attachments module toggle → LLM node Toolkits multi-select) to confirm the AFS's new steps are literally what an implementer will automate. Zero console errors observed throughout both runs.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}`, Keycloak on DEV).
- A pipeline exists with a single LLM node wired `entry_point -> LLM 1 -> END`, with **an artifact toolkit attached and wired into the node** — this is the corrected precondition (see § Adjustment; the pre-adjustment precondition below described a bare LLM node, which cannot resolve attachment content). Three things must all be true for Step 7's execution assertion to be meaningful:
  1. **An Artifact toolkit pointing at the `attachments` bucket is attached to the pipeline's Tools section.** Create via `ToolkitAPI.create_artifact_toolkit(name, description, bucket_name="attachments")` (`automation/api/client.py:1890`) for API-driven setup, or live via the UI: click "+ Toolkit" (`agent-add-toolkit-button`) → select the toolkit in the popper (`select_toolkit_in_popper()`) → the attach is NOT auto-persisted (unlike MCP) so a subsequent pipeline Save is required (confirmed live, matches the existing `select_toolkit_in_popper()` docstring precedent from ELITEA-2021/2037).
  2. **The LLM node's Toolkits multi-select (`pipeline-llm-node-toolkits-select`) has the attached toolkit selected**, and its `tool_names` mapping includes at least `read_file` (plus `list_files`/`get_file_metadata` as convenience). This is what gives the node's underlying LLM a callable tool to read the attachment's actual bytes — confirmed live: a node with the toolkit attached in the Tools section but NOT selected in this field never issues a `read_file` call, and the response falls back to the honest "I can't access the contents" reply the pre-adjustment AFS recorded as expected.
  3. The LLM node's `task` input mapping must be `type: fstring, value: 'User question: {input}\nAttached file paths (if any): {input_attachments}'` (NOT `type: variable` — confirmed live and matches the documented LLM-node gotcha, `.claude/skills/elitea-pipeline/references/yaml-schema.md` § LLM node gotchas: `type: variable` on `task` silently passes empty content), AND the pipeline's YAML `state` must declare `input_attachments: {type: list, default: []}` (confirmed live per `.claude/skills/elitea-pipeline/references/workflows.md` § File attachments into a pipeline — **the state declaration, not the Attachments-module toggle, is what actually populates `input_attachments`**; the toggle only auto-adds this same state key via the UI-side `usePipelineAttachmentYamlSync` sync, so either path works as long as the state key ends up declared and the pipeline is saved).
  4. The "Attachments" MODULES toggle (`agent-canvas-tools-toggle-attachments`) must be switched on — this IS a live-formik-state, no-save-required gate for the chat's *attach button* (confirmed live, unchanged from the pre-adjustment finding: the button flips from disabled to enabled the instant the switch is toggled, before any Save). This governs the **UI affordance** only; it does not by itself make content resolution work — that is governed by items 1-3 above.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- `settings.default_model_name` (`automation/config.py:196`) = `"gpt-5.2"` — already the correct choice; do **not** rely on whatever model the chat's "Select LLM Model" defaults to at runtime. Historical finding (pre-adjustment session, local-env `test-pipeline` fixture): the chat-panel's default model ("Anthropic Claude 4.5 Sonnet") 400s on **every** message on that fixture — DEV-environment LLM-provider-routing gap, not an Attach-Files defect, same precedent as ELITEA-2012. **Re-confirmed on DEV this adjust round**: a fresh pipeline created via `PipelineAPI.create_pipeline_with_nodes`/`create_pipeline` (this case's own setup path) already defaults to `gpt-5.2` via `_default_llm_settings()` — no model switch needed when the implementer builds its own pipeline rather than reusing a shared fixture.
- `ToolkitAPI.create_artifact_toolkit(name, description, bucket_name="attachments")` (`automation/api/client.py:1890`) — points the toolkit at the project's **default attachments bucket** (same bucket the chat's attach-files mechanism writes into — confirmed live: creating this toolkit does NOT require a separately-created bucket; `attachments` already exists implicitly as a storage target even though it 404s on an explicit `ArtifactAPI.bucket_exists()`/`list_bucket_files()` probe prior to any file ever being written there — the bucket materializes on first write, not on toolkit creation).

### generate-per-test (created in test setup, cleaned up via file cleanup)
- One small `.txt` file with **literal, unambiguous content** — not merely a token to match by string equality, but content requiring the LLM to actually interpret it. This adjust round used literal content `"cat"` and the question "What animal is in the attachment?", so the correct response must say "cat" — a fact that cannot be derived from the filename alone (confirmed live: filenames used throughout this round, e.g. `elitea2059_adjust_testfile3.txt`, contain no animal-related substring). Generate via pytest's `tmp_path` fixture, matching the existing `test_attach_files_button_sends_file_with_message` pattern in `tests/ui/chat/test_chat_interface.py:288-290`.

## Test Steps

> **Steps 1-2 are NEW** (added this adjust round — see § Adjustment). Steps 3-9 are
> the original case's steps 2-7, renumbered, with step 9's assertion strengthened.

1. **[NEW]** Create a fresh pipeline with a single LLM node via `PipelineAPI.create_pipeline`/`create_pipeline_with_nodes`, then attach an Artifact toolkit (pointed at the `attachments` bucket) to the pipeline's Tools section via the "+ Toolkit" button (`agent-add-toolkit-button`) → popper → select (`select_toolkit_in_popper()`), and **Save** (`agent-save-button`) — confirmed live this round: unlike the MCP picker, the Toolkit picker's selection does NOT auto-persist (matches the existing `select_toolkit_in_popper()` docstring).
   - **Verify**: an attached-item card (`agent-toolkit-card`) renders with the toolkit's name; `is_toolkit_attached(toolkit_name)` returns true.
2. **[NEW]** In the LLM node's config, open the Toolkits multi-select (`pipeline-llm-node-toolkits-select`) and select the attached toolkit; fix the node's `task` mapping to `type: fstring, value: 'User question: {input}\nAttached file paths (if any): {input_attachments}'` and ensure the pipeline's YAML `state` declares `input_attachments: {type: list, default: []}` (either by hand-editing the YAML, or by relying on the Attachments-module toggle's auto-sync — see step 3), then **Save**.
   - **Verify**: the Toolkits select shows the toolkit's name as a selected chip (confirmed live: `[data-testid="select-option-{toolkit_name}"]` is the option row inside the multi-select's popper — same generic `SingleSelect` auto-derivation already documented for ELITEA-2037's node dropdowns); the LLM node's Toolkits section (`agent-toolkit-card`'s sibling block) lists the toolkit with "Show tools" affordance.
3. Navigate to the pipeline detail page (if not already there post-save). In the left "Tools" accordion, under "MODULES", locate the "Attachments" switch (`agent-canvas-tools-toggle-attachments`) and turn it on.
   - **Verify**: the embedded chat panel's attach button (`aria-label="attach files"`, tooltip "Attach Files (10 left)") flips from `disabled` to enabled **immediately**, with no Save required — confirmed live via a direct DOM check (`disabled` attribute present/absent) both before and after the toggle, no page reload.
4. In the chat panel, locate the "Attach Files (10 left)" button.
   - **Verify**: visible and enabled (post-step-3). Confirmed the *tooltip text* IS the accessible name (`AttachmentButton.jsx`'s `processStatus` memo, `!showLabel` branch) — there is no separate visible label at this call site (see § Concrete Handles — this is a DIFFERENT render than the Chat-page plus-menu's `showLabel` variant).
5. Click the attach button.
   - **Verify**: native file chooser opens (`page.expect_file_chooser()`).
6. Select one `.txt` file, with literal unambiguous content (e.g. the single word `"cat"`), in the file chooser.
   - **Verify**: file appears as an attachment chip in the message area BEFORE sending (`[data-testid="chat-attachment-chip-0"]`, exact filename as its text content), and the button's tooltip/accessible name decrements to "Attach Files (9 left)".
7. Send a message that requires the LLM to resolve the attachment's actual content (e.g. "What animal is in the attachment?" for a file containing the word "cat") — **NOT** a generic "summarize the file" request, which an honest acknowledgment-only reply could satisfy without ever reading the file.
   - **Verify**: the user's message bubble shows both the typed text and the attachment chip; `[data-testid="chat-attachment-chip-0"]` count resets to 0 (no residual chips in the composer) after send.
8. **[STRENGTHENED]** Verify the pipeline actually resolves the attachment's content, not merely acknowledges its presence.
   - **Verify (confirmed live on DEV, 2026-10-15, with the artifact-toolkit wiring from steps 1-2 applied)**: the pipeline executes and produces an AI response with **no execution error visible** in the message thread (no `Error: Error code:` text), and the response **contains the correct fact from the file's actual content** (e.g. the word "cat") — not merely the filename or a generic "I see you attached a file" acknowledgment. Confirmed live, verbatim response: *"The animal in the attachment is a cat."* Cross-checked against the conversation's raw message-items via the Messages API (`GET /elitea_core/messages/prompt_lib/{project}/{conversation_id}`): the user's `attachment_message` item carries only a path reference (`"Attached document: {uuid}/{filename} (attachments/{uuid}/{filename})"`) — the model never receives the literal file bytes in the prompt text, so a correct "cat" answer is only reachable by the LLM actually invoking `read_file` via the attached-and-wired toolkit (see § Network Behavior for the toolkit's role in the predict trace; `tool_calls_dict` is where this is externally visible per `elitea-pipeline` skill's workflows.md). This is the behavior-drift fix: see § Adjustment and § Known Defects (reframed).
   - Evidence: ![LLM node config + chat response showing correct content resolution](https://github.com/EliteaAI/elitea-testing-public/releases/download/evidence/ELITEA-2059-step7-artifact-toolkit-chat-result.png)

## Expected Results
- An Artifact toolkit (pointed at the `attachments` bucket) can be attached to the pipeline's Tools section and selected in the LLM node's Toolkits multi-select; both states persist through Save.
- Attach button disabled while "Attachments" module is off; enabled the instant it's turned on (no save needed for this gate).
- File attaches, shows as a chip in the message area, and is included when the message is sent.
- **The pipeline executes without error and its response correctly reflects the attached file's actual content** (e.g. correctly names the animal described in the file) — not merely an acknowledgment that a file was attached. This replaces the pre-adjustment expected result ("acknowledges the attachment... full byte-level content extraction... not asserted here") — see § Adjustment for why.
- No console errors during the sequence (confirmed live — none observed across both the API-setup run and the full UI-driven run).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open a pipeline that supports attachments (Attachments module enabled in Tools) | Pipeline open with attachments-enabled chat panel | AFS steps 1–3 | step 3: attach button `disabled` attribute flips to absent immediately after the switch click, before Save | asserted — precondition decomposed into "create pipeline + attach toolkit" (step 1), "wire toolkit into LLM node" (step 2), and "enable module" (step 3); steps 1-2 are the **[NEW]** behavior-drift fix (see § Adjustment) |
| 2 Locate "Attach Files (10 left)" button | Button visible and enabled | AFS step 4 | step 4: `[aria-label="attach files"]` visible, not disabled; accessible name via tooltip = "Attach Files (10 left)" | asserted |
| 3 Click the attach files button | File picker opens | AFS step 5 | step 5: `page.expect_file_chooser()` fires | asserted |
| 4 Upload a supported file | File uploaded, appears as attachment | AFS step 6 | step 6: `chat-attachment-chip-0` count==1, text==filename | asserted |
| 5 Verify file appears as attachment in message area | Attachment thumbnail/name shown | AFS step 6 (same evidence) | step 6 | asserted |
| 6 Send a message referencing the file | Message with attachment is sent | AFS step 7 | step 7: message bubble shows text+chip, composer's chip count resets to 0 | asserted |
| 7 Verify pipeline processes the attachment | Pipeline responds with content referencing/processing the file | AFS step 8 | step 8: no `Error: Error code:` text in the response; response **correctly reflects the attached file's actual content** (e.g. names the animal described in the file), not merely an acknowledgment | asserted — **[STRENGTHENED]**, the Expected-result change this adjustment makes: the pre-adjustment "weaker-than-literal form" (filename-or-generic-keyword match) is replaced because it could pass even when the pipeline never read the file at all. See § Adjustment. |
| Precondition: "Attachments module enabled" | — | AFS step 3 | — | asserted (see row 1) |
| Test Data: File type .txt or .png | — | AFS uses `.txt` (generate-per-test) | — | asserted — `.png` not additionally exercised (ELITEA-2197/2200 already cover file-type variety on the general Chat surface via the identical shared `AttachmentButton`/validation utils; re-proving type acceptance here would be redundant per Rule-6, not a gap) |

### Axis 2 — Analyst additions
- Steps 1-2 (artifact-toolkit attach + wire-into-node) are **added, not implied by the case text** — *added because the case's literal steps never mention a toolkit; this is the human-reviewed triage verdict (issue #2408, overturning the earlier Class-D parked question #2412): "to make attachments work in pipeline we must add artifact toolkit to pipeline." Omitting this step reproduces the exact gap the triage flagged — a test that passes on an honest "I can't read this" reply.*
- Step 3 asserts the module-toggle → attach-button-enablement causal link is **instant, formik-state-driven, no-Save-required** — *unchanged from the pre-adjustment AFS: this is the precondition's actual mechanism (`useAgentAttachments`'s `disableAttachments = !internal_tools.includes('attachments')`, read from live form state), and distinguishes it from the Task-field fix and the toolkit-attach fix, both of which DO require Save.*
- Step 8's assertion is now **content-resolution, not acknowledgment-detection** — *added per the triage's second action item ("verification is weak, we must add attachment file with straightforward content... and verify that [it] was resolved"). Prevents a downstream implementer/reviewer from writing an assertion that is satisfied by a model that never actually read the file.*
- No console errors during the full sequence — *unchanged: standard side-channel check per the skill's "check the side channels even when the UI looks fine" rule; confirmed 0 errors across both this round's live runs.*
- The DEV-backend default-model gotcha is recorded as test data, not a defect, with its historical finding preserved and a note that this case's own pipeline-creation path doesn't hit it — *added this round: the implementer building a fresh pipeline (this case's own precondition) gets `gpt-5.2` by default and should not need to additionally invoke `select_llm_model()`.*

## Cleanup
- Delete the pipeline created in step 1 via `PipelineAPI.delete_pipeline(pipeline_id)`.
- No server-side attachment cleanup needed beyond the pipeline's own deletion (attachment lifecycle is tied to the conversation, which is deleted with the pipeline's test data teardown).

## Concrete Handles (discovered during exploration)

**This is a different `AttachmentButton` call site than ELITEA-2197/2200.** Those cases exercise the *Popper MenuList* instance in `PlusChatButton.jsx` (`testId="chat-attach-menuitem-button"`, `showLabel` variant, reached via a separate "+" plus-menu button). The Pipeline's (and Agent's — same shared `NewChatInput.jsx`/`isAgentsPage=true` path) embedded chat panel renders NO plus-menu at all; it renders the **bare, icon-only** `ChatButton.AttachmentButton` directly (`src/pages/NewChat/NewChatInput.jsx:272-278`, the `!hideAttachments && !fromTheChat` branch) — confirmed live via `document.querySelector('[data-testid="plus-menu-button"]')` returning `null` on the pipeline chat panel, and exactly one `[aria-label="attach files"]` button present, with `data-testid` attribute `null`.

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Attach button (bare icon, pipeline/agent embedded chat) | `testid needed: chat-attach-button` | **needs-adding** | `NewChatInput.jsx:273`'s `<ChatButton.AttachmentButton ref={attachmentButtonRef} onAttachFiles={...} disableAttachments={...} attachments={...} limits={...} />` — thread `testId="chat-attach-button"` through (the component already accepts a `testId` prop, wired straight to `data-testid` on its `<IconButton>` — see `AttachmentButton.jsx`'s `data-testid={testId}`). Name is FREE and semantically exact: `chat-attach-button` was previously a **dead/stale** field value on `ChatPage.attach_files_button` (ELITEA-2197's AFS confirmed zero hits for it anywhere in `EliteaUI/src`, on either `main` or `automation/testids`) — that field has since been re-pointed to `chat-attach-menuitem-button`, freeing this name for the call site it always semantically described (the plain, non-menu attach button). Shared component (`NewChatInput.jsx` is common chat infrastructure, used by both Agent and Pipeline embedded chat via `isAgentsPage=true`) — naming carries NO `agent-`/`pipeline-` prefix per the "shared components never hardcode feature-scoped testids" rule; scope this case's add to exactly this call site (line 273), not the sibling `showLabel` Popper instance (out of scope — ELITEA-2197/2200's) or the hidden drag-drop instance in `PlusChatButton.jsx:336` (different file, different case). |
| "Attachments" MODULES toggle | `[data-testid="agent-canvas-tools-toggle-attachments"]` (the `<input>` inside the switch) | **on-`automation/testids`, NOT on `main`** — confirmed via `git grep` both refs after `git fetch origin` (2026-08-09): `AgentInternalToolSwitch.jsx:108`'s `slotProps.switch.slotProps.input['data-testid']` template. Pre-existing (added for the Agent surface; reused verbatim here — `ApplicationTools.jsx` renders it for pipelines too when `isPipeline=true`, filtering `pipelineVisibleTools` to only the `attachments` tool). Naming carries the tracked `agent-` prefix despite covering both surfaces — same class of pre-existing shared-component tech debt the `_surface.md` digest already flags for `ConversationStarters.jsx`; not this case's to fix. | State-dependent (checked/unchecked) — assert via the `checked` DOM property, not a testid variant, per the project's testid-is-stable-identity rule. | **Adjusted:** opening the Test Pipeline panel auto-collapses the left config column (MODULES switches unmount); re-expand via `pipeline-config-collapse-button` (testid on DEV ✓) before toggling.
| Attachment chip (per file) | `[data-testid="chat-attachment-chip-{index}"]` (`CHAT_ATTACHMENT_CHIP` class constant, `chat_page.py:270`) | **pre-existing, reused verbatim** | `FileList.jsx` is shared infrastructure — the SAME testid resolves correctly on the pipeline's embedded chat composer (confirmed live: `chat-attachment-chip-0` present with the uploaded filename as text, identical shape to ELITEA-2197's Chat-page finding). Zero new work. |
| Chat message input | `[data-testid="chat-message-input"]` (`PipelineDetailPage.chat_input`, `pipeline_detail_page.py:437`) | **pre-existing** | Already used by every embedded-chat pipeline test. |
| Chat send button | `[data-testid="chat-send-button"]` (`PipelineDetailPage.chat_send_button`, `pipeline_detail_page.py:443`) | **pre-existing** | Already used by every embedded-chat pipeline test. |
| Clear chat button | `[data-testid="chat-clear-button"]` | **pre-existing** | Used between attempts in this exploration session; not strictly required by the case's own steps but useful for isolating attempts within one test if reused across assertions. |
| Model selector (workaround for the DEV default-model 400) | `pipelines.open_model_selector()` / `pipelines.select_llm_model(name)` / `pipelines.get_selected_model_name()` (`pipeline_detail_page.py:6269-6299`) | **pre-existing methods** | Not part of the case's own steps, but needed as TEST SETUP if the implementer reuses a fixture pipeline whose model 400s — see § Test Data. Not needed if a fresh pipeline is created via `create_pipeline_with_llm_node` (already defaults to `gpt-5.2`). |
| Attachments-module state variable (pipeline-only side effect, informational) | n/a — no locator | n/a | `AttachmentSwitch.jsx`'s docstring/YAML-sync logic (`STATE_INPUT_ATTACHMENTS = 'input_attachments'`) auto-adds an `input_attachments` list-type state variable to the pipeline's YAML when the module is toggled on via the (unused-for-pipelines) `AttachmentSwitch` component; the ACTUAL toggle rendered for pipelines is `AgentInternalToolSwitch` (no YAML-sync side effect observed live — the switch alone does not add the state var; confirmed by inspecting the Task field's "Variable" dropdown, which lists `input`, `messages`, `input_attachments` as available Task-mapping targets regardless of the switch state). **CORRECTED this adjust round**: the real sync mechanism, confirmed via frontend-source read (`origin/main:src/[fsd]/features/pipelines/lib/hooks/usePipelineAttachmentYamlSync.hooks.js`), is `usePipelineAttachmentYamlSync` — mounted on `ConfigurationTab.jsx`, it watches `version_details.meta.internal_tools` for `'attachments'` and adds/removes the `input_attachments` state key accordingly. This DOES fire for pipelines (contrary to the superseded note's "no YAML-sync side effect observed" — that observation predates this adjust round's live re-check); either path (toggle-driven auto-sync, or declaring the state key by hand in the YAML as this case's own setup does) ends in the same state. **ELITEA-2066's own test** (same file, second test function) already asserts the toggle's ON/OFF persistence; this AFS does not re-assert the sync mechanism itself. |
| "+ Toolkit" button (Tools section) | `agent_add_toolkit_button` / `[data-testid="agent-add-toolkit-button"]` — pre-existing `LocatorDescriptor` field on `PipelineDetailPage` (`pipeline_detail_page.py:877`), confirmed working live this round | **on-main** (pre-existing, shared with Agent forms, ELITEA-2021 provenance) | Opens the same `UnifiedDropdown` popper mechanism as "+ MCP"/"+ Agent" — `open_toolkit_popper()` / `select_toolkit_in_popper()` (pre-existing methods, `pipeline_detail_page.py:6127` / `6147`) reused verbatim, zero new page-object work needed. |
| Attached toolkit card (Tools section) | `[data-testid="pipeline-tool-card"]` (PipelineToolCard.jsx; replaces `agent-toolkit-card` for pipelines); list container `pipeline-tools-list`; "Show tools" toggle `pipeline-tool-card-show-tools` (replaces `toolkit-card-tools-toggle`); hover-revealed delete `pipeline-tool-card-remove` (replaces `agent-toolkit-delete-button`) | **testid on DEV ✓** (rung 1; suggested_testid n/a) | `is_toolkit_attached(toolkit_name)` confirms presence by name. **Adjusted (#UI drift): pipeline TOOLS cards are no longer `agent-toolkit-card`.** |
| LLM node Toolkits multi-select | `llm_node_toolkits_select` / `[data-testid="pipeline-llm-node-toolkits-select"]` — pre-existing `LocatorDescriptor` field (`pipeline_detail_page.py:879`), confirmed working live this round (both via a hand-authored-YAML pipeline and via driving the full UI attach flow from an empty pipeline) | **on-automation/testids** (ELITEA-2004's addition — `ToolkitsSelect.jsx`'s caller-supplied `data-testid`, LLM-node-only call site per its own source comment) | Multi-select (`multiple` prop on the underlying `Select.SingleSelect`); shows the attached toolkit's name as a chip once selected. Only toolkits already attached in the Tools section populate this select's options (`toolkitOptions` reads `version_details.tools`) — attaching in Tools section is a PREREQUISITE for this select to offer the toolkit at all, confirmed live (an unattached toolkit never appears as an option here). | **Adjusted:** this select now renders ONLY inside the node config side panel, which exists only while the node is selected. Flow: select the node, read the chip, close the panel via `pipeline-node-panel-close` (testid on DEV ✓).
| LLM node Toolkits select — dropdown option (per toolkit) | `[data-testid="select-option-{toolkit_name}"]` (dynamic) — confirmed live via DOM probe this round (e.g. `select-option-autotest2059_attachments_toolkit`) | **on-automation/testids** (same generic `SingleSelect` auto-derivation already documented for ELITEA-2037's node Toolkit/Tool/Input/Output dropdowns — this is simply that same mechanism's first appearance on the LLM-node Toolkits field) | No new page-object method needed — the generic `[data-testid="select-option-{}"]` template constant pattern (if one exists) or a `ScopedLocator` resolved within the open popper covers this; not yet exercised by any existing test prior to this round. |

**Resolved/added during ELITEA-2059 implementation:**
- `chat-attach-button` added per plan — `NewChatInput.jsx:273`'s `testId` prop, `EliteaAI/EliteaUI@2a4aab23` on `automation/testids`.
- A SECOND testid was needed and added beyond the AFS's original plan: `chat-attach-button-tooltip` (`AttachmentButton.jsx`'s `Tooltip` `slotProps={{ tooltip: { 'data-testid': ... } }}`, `EliteaAI/EliteaUI@a926573d` on `automation/testids`). Reason: live verification showed the button's own `aria-label` stays the STATIC string `"attach files"` — it does NOT reflect the dynamic `"Attach Files (N left)"` counter text (that text only exists in the MUI `Tooltip`'s `[role="tooltip"]` popper, confirmed via `getAttribute('aria-label')` before/after hover). The AFS's "accessible name via tooltip" wording is imprecise: the counter text is tooltip-*content*, not an aria-label override. Per the testid-only locator policy, a raw `[role="tooltip"]` selector is not a compliant NEW handle (not a #579 exception — this is our own MUI usage, not a third-party widget), so a testid on the tooltip's popper content was the compliant path (same shape as `toolkit_creation_page.py`'s `bucket_info_tooltip_content` precedent). Only one render path reaches this `Tooltip` (the `!showLabel` branch, `NewChatInput.jsx` only — `PlusChatButton.jsx`'s `showLabel=true` instance returns before the `Tooltip` wrapper) so a hardcoded generic testid (no `testId` prop plumbing needed) is collision-safe.
- Step 7's assertion needs a WIDER acknowledgment check than "filename substring" alone. Live re-verification during implementation (fresh probe pipeline, same `type: variable, value: input` TASK mapping) produced a DIFFERENT GPT-5.2 response than the AFS's originally recorded one: *"I can summarize it, but I don't have access to the contents of that attached .txt file in this chat context. Please either: Paste the text here..."* — this phrasing does NOT contain the filename substring at all (unlike the AFS's originally recorded example, which did). Confirms the AFS's own non-determinism warning ("Do not assert on the literal wording") extends to the filename-substring fallback itself. The implemented assertion therefore accepts EITHER the filename substring OR a generic attachment-acknowledgment keyword (`"attach"` — present in both observed variants: "attachment"/"attached"), not filename-only.

## Network Behavior
- Enabling the "Attachments" MODULES switch: no network request (pure client-side formik state) — confirmed via `browser_network_requests` before/after the toggle.
- Attaching a file (before send): no network request (validated client-side only, matches ELITEA-2197's finding for the general Chat surface).
- Saving the pipeline (Task field fix, toolkit attach/wire): `PUT .../elitea_core/application/prompt_lib/{project}/{id}` → `201` (confirmed live this round; earlier draft of this row said `200` — re-verified, create/update both returned `201` in this round's runs).
- Sending the message: `POST .../elitea_core/conversations/prompt_lib/{project}` (creates the conversation, `201`), then `POST .../elitea_core/attachments/prompt_lib/{project}/{conversation_id}` (uploads the file to the `attachments` bucket) — confirmed live this round via direct request-log capture (both calls observed in sequence). The actual predict/execution traffic (including the LLM's internal `read_file` tool call) rides the WebSocket/execution-generation channel per `.agents/architecture.md`; it is NOT visible in the plain `GET .../elitea_core/messages/prompt_lib/{project}/{conversation_id}` response, which shows only the final text + the attachment's path reference (`attachment_message` item), not any intermediate tool_calls. **[NEW this round]** Per `.agents/role-overrides.md` § 4xx/5xx cross-check discipline and the `elitea-pipeline` skill's `tool_calls_dict` note (`workflows.md`), a deeper trace of the actual `read_file` invocation would require either `debug: true` on a code node (not applicable to a bare `llm` node) or the predict response's raw `tool_calls_dict` — not captured this round since the chat-UI flow (the case's own interface) doesn't surface it; the CORRECT, user-visible content in the final response is the evidence this case asserts on, which is sufficient for the case's stated scope.

## Known Defects Found During Exploration

**None filed as product defects — the gap this section used to describe was case-text/test drift, now corrected (see § Adjustment), not a product bug.**

1. The DEV backend's default pipeline-chat model (Anthropic Claude 4.5 Sonnet) has no configured LLM-provider fallback and 400s on **every** message on the shared `test-pipeline` UI fixture (with or without an attachment) — environment config, not attach-files-specific, matches the existing ELITEA-2012 precedent of documenting rather than filing. Unaffected by this adjustment; recorded as test data (§ Test Data).
2. **[REFRAMED — was previously recorded as expected/architectural, no longer the expected behavior]** A bare `llm`-type pipeline node, with no toolkit attached or wired, cannot extract an attached file's byte content — it only sees a path-like reference in the message text, and honestly reports "I can't access the contents of that attachment." **This observation is still factually true** (re-confirmed implicitly: the corrected pipeline differs from a bare node precisely by having the toolkit attached-and-wired, and that difference is what makes content resolution work) **but it is no longer this case's expected result.** The pre-adjustment AFS treated the bare-node limitation as "correct architecture, outside this case's scope" — the human triage on issue #2408 overturned that reading: the case's real intent (per its title, "Pipeline — Attach Files in Chat", and its step 7, "Verify pipeline processes the attachment") is that attaching a file and asking about it should work end-to-end, which requires the toolkit step this case was missing. **Read this note as describing a DIFFERENT (now out-of-scope-for-this-case) configuration** — a bare LLM node with no toolkit — not as describing what THIS case's pipeline does. A future case that specifically wants to test the bare-node fallback behavior (e.g. "pipeline without an artifact toolkit gives an honest 'cannot read' response") would need its own case id and AFS; this one no longer covers that configuration.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- **Fixture — new recommended shape this round**: build a pipeline fixture that (a) creates the pipeline + LLM node (`create_pipeline`/`create_pipeline_with_nodes`), (b) creates an Artifact toolkit via `ToolkitAPI.create_artifact_toolkit(name, description, bucket_name="attachments")`, (c) attaches the toolkit to the pipeline's `tools` list AND wires it into the LLM node's `tool_names` mapping, (d) sets `task: {type: fstring, value: 'User question: {input}\nAttached file paths (if any): {input_attachments}'}`, and (e) declares `state.input_attachments: {type: list, default: []}` in the YAML — all at creation time via the API, mirroring the shape `pipeline_with_variable_task_llm_id` already uses for the single-fix case, but extended for the toolkit. Recommend a NEW fixture (e.g. `pipeline_with_artifact_toolkit_llm_id`) rather than overloading the existing `pipeline_with_variable_task_llm_id`, since the existing fixture's `task` mapping (`type: variable, value: input`) is the WRONG shape for this case now (see § Preconditions item 3 — `type: variable` silently passes empty content; this case needs `type: fstring`). The sibling fixture `pipeline_with_fstring_llm_id` (`fixtures/data_fixtures.py`) is the closer analog to crib `task`'s shape from, extended with the toolkit-attach + tool_names wiring.
- Page object: `toggle_attachments_module()`, `open_embedded_chat_file_chooser()`/`attach_file_in_embedded_chat(file_path)`, `open_toolkit_popper()`/`select_toolkit_in_popper()`, `is_toolkit_attached()`, and `llm_node_toolkits_select` are all PRE-EXISTING — zero new page-object methods were needed for this adjustment's live run (confirmed both via the API-driven setup path and the full UI-driven attach flow from an empty pipeline). The one new page-object surface a strict from-scratch-UI implementation would exercise is clicking an option inside the LLM node's Toolkits multi-select popper (`[data-testid="select-option-{toolkit_name}"]`) — likely coverable by an existing generic `select_option_by_testid`-style helper if one exists, or a one-line addition if not; this round drove it via `.click()` on a Locator built from the testid template directly (not a durable page-object pattern — the implementer should add a proper method, e.g. `select_llm_node_toolkit(toolkit_name)`, rather than reusing this round's throwaway probe script's approach).
- Wait strategy: after the Toolkit-attach + Toolkits-select + Task/state wiring, use `save_and_wait_for_update()` (existing method) before navigating away — confirmed this round that the attach-in-Tools-section step does NOT auto-persist (unlike MCP's immediate-PATCH behavior per ELITEA-2037), so an explicit Save-and-wait is mandatory here, not merely cautious. After send, reuse the existing `wait_for_embedded_chat_response()` (`pipeline_detail_page.py:7393`) rather than a fixed sleep; assert the final response text does NOT contain `"Error: Error code:"` and DOES contain the correct resolved fact (e.g. `"cat"`, case-insensitive substring) — NOT the filename and NOT a generic acknowledgment keyword, which is the Expected-result change this round makes (§ Adjustment).
- Viewport: no width-sensitivity concerns found for this call site (single icon button, no `FileList.jsx` overflow-split risk at typical CI viewport widths — only relevant if attaching >1 file, which this case's Test Data doesn't call for).

## Adjustment

**Triggered by**: issue EliteaAI/elitea-testing-public#2408 ([FIX][ELITEA-2059]), a human
review of the earlier Class-D triage parked on question #2412. The human overturned
that triage with:

> "there is a test case drift - behavior changed, to make attachments work in
> pipeline we must add artifact toolkit to pipeline. Action items - add test
> step - create and add artifact toolkit (adjust onetest test case and test
> code); verification is weak, we must add as attachment file with
> straightforward content - like 'cat', and specify llm to process it in a way
> like 'what animal is in attachment' - and verify that cat was resolved
> (adjust onetest test case and test code)"

**Triage class: A — UI/behavior drift** (per `adjust-automated-test` skill § Step 2).
The real/intended flow needs an artifact toolkit attached-and-wired for file content
to reach the LLM; the pre-adjustment case+test asked for a bare LLM node and accepted
an honest "I can't read this" reply as passing, which is weaker than the case's own
stated intent ("Verify pipeline processes the attachment... Pipeline responds with
content referencing or processing the attached file").

**What changed:**
1. **Added two new steps** (now AFS steps 1-2) that attach an Artifact toolkit (bucket
   `attachments`) to the pipeline and wire it into the LLM node's Toolkits select +
   `task`/`state` mapping, per the preconditions above. Without this, the LLM has no
   mechanism to read the attachment's bytes at all — confirmed by both the
   pre-adjustment session (which recorded the honest "I can't access the contents"
   reply as correct/expected) and this round (same reply reproduces on a bare node;
   diverges to a correct content-resolution reply only once the toolkit is attached
   AND selected in the node's Toolkits field — attaching to the Tools section alone,
   without the node-level selection, is not sufficient).
2. **Expected-result change** (requires this flag per `adjust-automated-test` § Step 3
   — an assertion's *nature* changed, not merely its *mechanism*): the final step's
   assertion moves from "no error + filename-or-generic-acknowledgment substring" to
   "no error + the correct resolved fact from the file's actual content." This is
   NOT a weakening (the rail's forbidden direction) — it is a STRENGTHENING: the new
   assertion is strictly harder to satisfy honestly (an unwired bare node can no
   longer pass) and could not have been satisfied by the pre-adjustment pipeline
   configuration at all. The sign-off for this change is the human triage comment
   quoted above, which explicitly names the weak-verification problem and the fix.
3. **Known Defects reframed, not deleted** (see that section) — the bare-LLM-node
   content-extraction limitation is still a true, confirmed fact about that
   configuration; it is simply no longer what THIS case's pipeline looks like, so it
   is relabeled from "expected architecture, in scope" to "describes a different,
   now out-of-scope configuration."
4. **TMS case update required** — flagged to the orchestrator for a separate PR
   against `onetest-ai-tm-Elitea` (this analyst dispatch is AFS-only per its own
   scope; the test-code update is also a separate, subsequent implementer
   dispatch). The TMS case's steps 1 and 7 need the same two changes reflected: add
   an explicit "attach + wire an artifact toolkit" step, and reword step 7's expected
   result from "responds with content referencing or processing the attached file"
   to something unambiguous about actual content resolution (e.g. "responds with the
   correct fact extracted from the attached file's content, verified against a file
   with concrete, unambiguous content").

**Verification performed**: live on DEV (`https://dev.elitea.ai`, project id 575),
twice — (a) a hand-built pipeline (API-authored YAML with the toolkit wired in,
`task: fstring`, `state.input_attachments` declared) sent a `.txt` file containing
the literal word `"cat"` with the question "What animal is in the attachment?" and
received the verbatim response *"The animal in the attachment is a cat."*; (b) the
full UI-driven flow (empty pipeline → add LLM node → "+ Toolkit" popper → attach →
Attachments-module toggle → LLM node Toolkits multi-select → select) was independently
driven end-to-end and confirmed every new step's locators/behavior match what AFS
steps 1-2 now describe. Zero console errors in both runs. All API-created test
artifacts (4 pipelines, 2 toolkits) were deleted after verification; the implicit
`attachments`-bucket toolkit left no bucket residue requiring cleanup (confirmed:
`ArtifactAPI.delete_bucket("attachments")` was never called — only the throwaway
`autotest2059bucket` from an earlier abandoned approach needed cleanup, and its
delete 404'd harmlessly since the bucket was never actually written to).

## Adjustment — #2574 (triage class A: UI drift, EL-7155 "Pipelines 2.0 Test Pipeline panel")

**Old -> new.** The pipeline's embedded chat moved into a side `TestPanel` (`pipeline-test-panel`, mounted but `display:none` until opened). It is opened by the toolbar button `pipeline-test-button` ("Test Pipeline"). `chat-attach-button` is therefore not visible until the panel is open.

| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 testid | `pipeline-test-button` (`PipelineDetailPage.test_pipeline_button`) | n/a | testid on DEV ✓ (served, verified by passing run) |
| 1 testid | `pipeline-test-panel` (`PipelineDetailPage.test_pipeline_panel`) | n/a | testid on DEV ✓ |

Changes:
- `open_test_pipeline_panel()` (idempotent; waits for the button to be enabled) called in ELITEA-2059 Step 3 (before the attach-button assertions) and in every state check of ELITEA-2066 (after each navigate/reload).
- The button is **disabled while the pipeline has no node connected to End** (`getTestBlockReason`), so the ELITEA-2066 test now uses `pipeline_with_llm_id` instead of the empty `pipeline_id`.
- The Test panel blocks Send while the pipeline has unsaved edits (`sendBlockedReason`, `useIsPipelineYamlCodeDirty`); ELITEA-2059 now Saves (after the Attachments toggle) before sending in Step 7.

Expected-result changes: none. All assertions and step titles unchanged.

## Adjustment — pipeline TOOLS card / node panel / config column (triage class A: UI drift)

**What changed (verified on DEV and in EliteaUI origin/main source):**
1. Pipeline TOOLS section cards are now `PipelineToolCard.jsx`: `pipeline-tool-card` (card), `pipeline-tool-card-show-tools` (toggle, was `toolkit-card-tools-toggle`), `pipeline-tool-card-remove` (hover-revealed delete, was `agent-toolkit-delete-button`), `pipeline-tools-list`. Previously `agent-toolkit-card`.
2. The LLM node Toolkits select (`pipeline-llm-node-toolkits-select`) renders only in the node config side panel, present only while the node is selected: select node, read chip, close via `pipeline-node-panel-close`.
3. Opening the Test Pipeline panel auto-collapses the left config column (unmounting MODULES switches); re-expand via `pipeline-config-collapse-button` before toggling Attachments (`agent-canvas-tools-toggle-attachments`).

**Why:** product UI refactor (Pipelines 2.0), not a defect. Class A.

**Expected-result changes: none.** All assertions and steps are unchanged.
