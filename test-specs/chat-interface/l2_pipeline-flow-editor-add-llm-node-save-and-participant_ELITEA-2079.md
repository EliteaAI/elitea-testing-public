# Test Case: Chat – Pipeline Flow Editor – Add LLM Node, Verify YAML, Save Pipeline, and Add to Conversation

## Metadata
- **TMS ID**: ELITEA-2079
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", observed live as `projectId=399`, matches `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live (all 11 steps observed against the real app). No product defect found; one pre-existing, already-tracked test-robustness gotcha applies to the send-message step (see § Automation Hints / § Known Defects). New page-object surface needed only for the in-chat canvas *entry point* and *close button* — the Flow Editor / YAML editor / add-node surface itself is the exact same `EditorPanel` React component already driven by `PipelineDetailPage` (standalone `/pipelines/all/{id}` page), confirmed by reading `PipelineEditor.jsx`'s import of `@/pages/Pipelines/Components/EditorPanel` — so `PipelineDetailPage`'s existing methods (`add_node`, `switch_to_yaml_view`, `get_yaml_content`, `switch_to_flow_view`) are directly reusable on the same `page`, mirroring the `AgentFormPage`-reuse pattern from `test_create_agent_via_chat_canvas.py` (ELITEA-2166).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- **The case's own precondition ("the 'test-pipeline' Flow Editor is open with only the 'End' node visible, following ELITEA-2078") is NOT yet automatable as a merged upstream fixture** — ELITEA-2077 ("Create Pipeline from Conversation – Save Basic Configuration") and ELITEA-2078 ("… Discard Changes …") are siblings in the same TMS folder but have not been analysed/automated in this batch. Per the project's "Seeding gotcha" precedent (`test_pipeline_yaml_flow_sync.py`'s docstring, ELITEA-2028), this AFS specs the precondition as **live UI setup, not one of this case's own 11 numbered steps**:
  1. `ChatPage.click_create_conversation()` (existing method) → new blank conversation.
  2. Open the `+` menu → **Pipelines** → **+ Create New Pipeline** (`pipelines-menuitem` → `pipelines-create-new-button`, both confirmed **on-main ✓**, existing testids).
  3. Fill Name = `test-pipeline`, Description = `A test pipeline for conversation` (`agent-name-input` / `agent-description-input` — confirmed **on-main ✓**, same shared `CreateAgentForm` component the standalone Agent-create canvas uses, entityType="pipeline").
  4. Click Save (create-mode) — confirmed **NO TESTID** live (role-based `get_by_role("button", name="Save")` only); see § Concrete Handles, `testid needed: agent-save-button` on `CreateApplicationSaveButton.jsx` (same gap already flagged by the ELITEA-2166 AFS for the Agent-create path — `CreateApplicationSaveButton.jsx` is the SAME shared component for Agent/Pipeline create-mode canvases, so wiring the testid there once satisfies both). Confirmed live: `PUT`/`POST … /applications/prompt_lib/399` → `201 Created`.
  5. Click the **Flow editor** tab (`get_by_role("tab", name="Flow editor")` — confirmed **NO TESTID** on the tab itself live; low-risk gap, only 2 tabs ever render here, "Configuration"/"Flow editor", role-based lookup is stable, but per policy still flagged, see § Concrete Handles).
  6. Confirmed live: canvas renders with exactly one node, `rf__node-END` (`.react-flow__node-END`), matching this case's own precondition text ("only the 'End' node visible").

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment (confirmed live, unlike ELITEA-2166's finding for a different account state — re-verify at implementation time with `get_selected_project_text()` rather than assuming).

### generate-per-test
- **New conversation** — created via `ChatPage.click_create_conversation()`, cleaned up via `conversation_api.delete_conversation(id)`.
- **New pipeline "test-pipeline"** — created as setup (see § Preconditions). Case's own Test Data table literal values: Name `test-pipeline`, Description not specified as a literal test-data row in the case (case gives it in the Preconditions narrative, `A test pipeline for conversation`, per the sibling ELITEA-2077 case's Test Data table). Cleaned up via the pipeline's own delete (API or UI) — do NOT rely on conversation deletion to cascade.
- **Test message**: `hello` (case's literal Test Data value, step 11).

## Test Steps

1. Verify the Flow Editor is open with only the "End" node visible and "Flow" sub-tab active.
   - **Verify**: `PipelineDetailPage.get_node_count() == 1`; the one node's class is `react-flow__node-END`; the "Flow" sub-tab (`pipeline-flow-view`, confirmed **on-main ✓**) is the active one (`is_flow_view_active()`, existing method).
2. Click "+ Add node" and select "LLM".
   - **Verify**: `PipelineDetailPage.add_node("LLM")` (existing method, reused as-is — see § Automation Hints on why this pre-existing raw-selector method is NOT a new violation). Confirmed live: node count becomes 2 (`react-flow__node-END` + `react-flow__node-llm`), the LLM node is auto-selected (its detail panel opens showing Trigger/System/Type fields — not asserted by this case, informational).
3. Click the "Yaml" tab.
   - **Verify**: `PipelineDetailPage.switch_to_yaml_view()` (existing method); `yaml_editor` (`pipeline-yaml-editor`, confirmed **on-main ✓**) becomes visible.
4. Verify line 1 shows "entry_point: LLM 1", line 2 shows "nodes:", line 3 shows "- id: LLM 1", line 4 shows "type: llm".
   - **Verify**: `PipelineDetailPage.get_yaml_content()` (existing method — extracts clean text via `.cm-line`, NOT the raw `inner_text()` of the whole editor, which interleaves CodeMirror's gutter line-numbers before the content in DOM order and would corrupt a naive read). Confirmed live, exact content:
     ```
     entry_point: LLM 1
     nodes:
       - id: LLM 1
         type: llm
         input: []
         input_mapping:
           chat_history:
             type: fixed
             value: []
           system:
             type: fixed
             value: ''
           task:
             type: fixed
             value: ''
         output: []
         structured_output: false
         transition: END
     ```
     Case's line 3 wording "- id: LLM 1" matches live modulo leading indentation (2 spaces, YAML-standard) — not a clarification, just normal YAML nesting.
5. Verify YAML includes `input_mapping`, `task`, `structured_output: false`, and `transition: END`.
   - **Verify**: all four confirmed present verbatim in the live content above (`input_mapping` block has `chat_history`/`system`/`task` sub-keys; `task` present with `type: fixed, value: ''`; `structured_output: false` present; `transition: END` present).
6. Click back on the "Flow" tab.
   - **Verify**: `PipelineDetailPage.switch_to_flow_view()` (existing method); `is_flow_view_active()` True; LLM node still present (`get_node_count() == 2`, unchanged from step 2).
7. Click the "Save" button.
   - **Verify**: `agent-save-button` (confirmed **on-main ✓** — this is the SAME testid `PipelineFormPage.save_button` already uses; `SaveApplicationButton.jsx` hardcodes `data-testid="agent-save-button"` unconditionally, shared across Agent/Pipeline/Toolkit edit-mode canvases — pre-existing naming quirk, already tracked as issue #1040, not a new finding). Confirmed live: `PUT /api/v2/elitea_core/application/prompt_lib/399/{pipeline_id}` → `201`; success toast "The pipeline has been updated" (`toast-message`, confirmed **on-main ✓**).
8. Click the X button to close the canvas panel.
   - **Verify**: canvas close button — confirmed **NO TESTID** live (`EditorHeader.jsx`'s close `IconButton`; `PipelineEditor.jsx`'s `<BaseEditor>` call does not pass `closeButtonTestId` — the prop exists and is wired end-to-end in `EditorHeader.jsx`, just never supplied for the Pipeline path; ELITEA-2166 already added it for the Agent path as `agent-canvas-close-button`). `testid needed: pipeline-canvas-close-button` at `PipelineEditor.jsx`'s own `<BaseEditor>` call site (component-sharing guard — same precedent as `agent-save-button`/`agent-canvas-close-button`: only this call site gets the new prop value). Confirmed live via bounding-box probe: the button is the first `<button>` in the canvas header (x<900, y<90, no visible text), distinct from `Discard`/`Save`.
9. Verify the "test-pipeline" chip shows "test-pipeline base" (without "Editing..." status) in the message input area.
   - **Verify**: confirmed live — body text contains `test-pipeline` and `base`; contains **no** `Editing` text once the canvas is closed (it DOES still show "Editing…" immediately after Save while the canvas remains open — closing is what flips it, matching this case's own step ordering, unlike the sequencing drift found in ELITEA-2166/#709). Composer element: `chat-switch-participant-button` (confirmed **on-main ✓**, existing `ChatPage.switch_participant_button`).
10. Verify a "PIPELINES" section now appears in the PARTICIPANTS panel with "test-pipeline base" listed.
    - **Verify**: expand via `chat-participants-panel-toggle-button` (confirmed **on-main ✓**). Confirmed live, exact text: `PARTICIPANTS` / `PIPELINES` / `test-pipeline` / `base`. Row testid: `chat-participant-row-pipeline_{participant_id}_{project_id}` (confirmed live as `chat-participant-row-pipeline_6937_399` — matches the EXISTING dynamic `PARTICIPANT_ROW` template already in `chat_page.py`, `'[data-testid="chat-participant-row-{}"]'`; no new handle needed, same infra ELITEA-2168/2075 already exercise for other participant types). Badge testids `chat-participants-badge-pipelines` / `chat-participants-badge-icon-pipelines` also confirmed **on-main ✓** (same `PARTICIPANTS_BADGE` template, `.format("pipelines")`).
11. Send a test message "hello".
    - **Verify**: `chat-message-input` (fill) → `chat-send-button` (click) → user message "hello" appears in the message list; pipeline (through its LLM node) generates a response within a bounded wait (`wait_for_ai_response()`, existing method). **Automation Hint**: use the framework's established `conversation_id` fixture + `ChatPage.navigate_to_chat(conversation_id=...)` pattern for the conversation this case's own setup creates — do NOT drive message-send timing off a bare `sidebar-create-button` click + fixed short wait; see § Known Defects / Automation Hints for why (issue #1085, a known, already-tracked test-robustness gap: the composer can be covered by a loading overlay for longer than expected when the account's conversation list has accumulated many entries — reproduced live during this analysis, root-caused to the identical class of issue #1085, not a new defect).

## Expected Results
- All 11 steps pass cleanly as specced above. No product defect found — this case is a genuinely clean happy path once the two `needs-adding` testids (§ Concrete Handles) land.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: "test-pipeline" Flow Editor open, only End node visible, following ELITEA-2078 | — | Setup (live UI replication, not a case step — ELITEA-2077/2078 not yet automated) | pipeline created via chat canvas, Flow Editor tab opened, node count == 1 | asserted *(setup, not one of the 11 numbered steps — see § Preconditions)* |
| 1 Verify Flow Editor open, only End node, Flow tab active | Flow editor initialized | step 1 | node count == 1, class `react-flow__node-END`, `is_flow_view_active()` | asserted |
| 2 Click + Add node, select LLM → LLM node added above End node | LLM node added | step 2 | `add_node("LLM")`, node count == 2 | asserted |
| 3 Click Yaml tab → YAML editor opens | YAML editor visible | step 3 | `switch_to_yaml_view()`, `yaml_editor` visible | asserted |
| 4 Verify YAML lines 1-4 | YAML correctly formatted | step 4 | `get_yaml_content()` exact-text match | asserted |
| 5 Verify YAML includes input_mapping/task/structured_output/transition | all properties present | step 5 | same `get_yaml_content()` capture, substring checks | asserted |
| 6 Click back on Flow tab → Visual editor shown, LLM node still present | flow view + node present | step 6 | `switch_to_flow_view()`, node count unchanged | asserted |
| 7 Click Save → Pipeline saved, success notification | saved + toast | step 7 | `201` PUT response + `toast-message` text | asserted |
| 8 Click X to close canvas → Canvas closes, conversation fully displayed | canvas closed | step 8 | canvas testids gone from DOM (`rf__wrapper`, `pipeline-yaml-view`, etc. absent) | asserted |
| 9 Verify chip shows "test-pipeline base" without "Editing..." | chip updated | step 9 | composer text contains `test-pipeline`/`base`, not `Editing` | asserted |
| 10 Verify PIPELINES section in PARTICIPANTS with "test-pipeline base" | pipeline listed as participant | step 10 | `PARTICIPANTS`/`PIPELINES`/`test-pipeline`/`base` text + dynamic row testid | asserted |
| 11 Send "hello" → Pipeline processes message, generates response | message processed, response generated | step 11 | message-list assertions + `wait_for_ai_response()` | asserted *(recommend `conversation_id` fixture per known test-robustness gotcha #1085 — see Automation Hints)* |
| Expected Final State: "LLM node added, YAML valid, pipeline saved and added as participant, responds to messages" | — | steps 2-11 | — | asserted |
| Pass/Fail: "Any step produces an error... YAML invalid, pipeline fails to save, or pipeline does not appear in PARTICIPANTS" | — | all steps | side-channel console/network checks throughout | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Steps 4/5 assert the YAML content via `get_yaml_content()`'s existing `.cm-line`-based extraction rather than a raw `inner_text()` of the editor — *added: a naive read interleaves CodeMirror's gutter line-numbers before the actual content lines in DOM order (confirmed live during this analysis), which would silently corrupt an exact-line assertion. `PipelineDetailPage.get_yaml_content()` already handles this correctly (used successfully by `test_pipeline_yaml_flow_sync.py`).*
- Step 7's underlying network call is asserted (`PUT … 201`) rather than only the toast — *added: matches this suite's established pattern of confirming persistence via the API, not just a DOM/toast signal.*
- Step 11 recommends the `conversation_id` fixture over a bare UI-driven new-conversation + immediate send — *added: this analysis reproduced the exact composer-covered-by-loading-overlay symptom already tracked as issue #1085 (root cause: conversation list load time under accumulated test data, not this case's own flow) when driving a raw new conversation without the fixture's readiness handling. Flagging pre-emptively rather than letting the implementer rediscover it.*
- Console/network side-channel checked after every step — confirmed clean throughout (zero console errors, zero failed (4xx/5xx) requests) across all 11 steps in this session.

## Cleanup
1. Delete the created pipeline (`application` entity — `PipelineAPI` or the UI's Pipelines-list delete action).
2. Delete the created conversation via `conversation_api.delete_conversation(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main`.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu → Pipelines menuitem | `pipelines-menuitem` | on-main ✓ | `PlusChatButton.jsx`'s `EXPANDABLE_ITEMS` static config — confirmed via source read, no live-vs-main ambiguity for this one (static string literal in JSX, not testid-gated by any build flag). |
| `+` menu → Pipelines submenu → "+ Create New Pipeline" | `pipelines-create-new-button` | on-main ✓ | `PlusChatSubmenu.jsx`'s `${sectionKey}-create-new-button` pattern, `sectionKey="pipelines"`. Confirmed live via DOM dump. |
| Pipeline Name field (create form) | `agent-name-input` | on-main ✓ | Same `CreateAgentForm` component (entityType="pipeline") — confirmed identical testid live. |
| Pipeline Description field (create form) | `agent-description-input` | on-main ✓ | Same as above. |
| Canvas Save button (create-mode) | **NO TESTID** | needs-adding | `testid needed: agent-save-button` on `CreateApplicationSaveButton.jsx` — same gap and same recommended fix already flagged by the ELITEA-2166 AFS for the Agent-create path (shared component, single fix serves both). Currently only resolvable via `get_by_role("button", name="Save")`. |
| "Flow editor" / "Configuration" tabs (post-save canvas) | **NO TESTID** | needs-adding (low priority) | `testid needed: pipeline-canvas-tab-{flow,configuration}` or similar. Only 2 static tabs, role-based lookup (`get_by_role("tab", name=...)`) is stable and low-risk, but flagged per policy. Not a blocker — implementer may add or escalate. |
| Flow/Yaml sub-view toggle | `pipeline-flow-view` / `pipeline-yaml-view` | on-main ✓ | Existing `PipelineDetailPage.flow_view_button` / `yaml_view_button` — SAME shared `EditorPanel` component, confirmed identical testid live inside the chat canvas. |
| YAML editor content | `pipeline-yaml-editor` | on-main ✓ | Existing `PipelineDetailPage.yaml_editor`. |
| ReactFlow canvas / nodes / edges | `rf__wrapper`, `rf__node-{id}`, `rf__edge-xy-edge__{source}---{target}` | on-main ✓ | Existing `PipelineDetailPage` infra (`canvas_wrapper`, `get_node_count()`, `edge_exists()`) — confirmed identical live inside the chat canvas (same `EditorPanel`/ReactFlow instance type). |
| "+ Add node" button + node-type menu items | **NO TESTID** (pre-existing, tracked tech debt) | n/a — reuse, not new | `PipelineDetailPage.add_node()` (existing method) uses `button.MuiIconButton-colorPrimary` + `get_by_role("menuitem", name=...)`. This is EXISTING, already-merged code being **reused as-is** on the same shared component — not a new raw-locator author. See § Automation Hints. |
| Canvas Save button (edit-mode, post-creation) | `agent-save-button` | on-main ✓ | Same testid as `PipelineFormPage.save_button` — confirmed live, works identically inside the chat canvas. Pre-existing naming quirk (misleadingly "agent"-prefixed for a Pipeline/Toolkit-shared button) already tracked as issue #1040 — not a new finding. |
| Canvas X (close) button | **NO TESTID** | needs-adding | `testid needed: pipeline-canvas-close-button` at `PipelineEditor.jsx`'s `<BaseEditor closeButtonTestId=...>` call (the prop is already wired end-to-end in `EditorHeader.jsx`/`BaseEditor.jsx`, just never supplied here — same shape as `agent-canvas-close-button`, added by ELITEA-2166 for the Agent path). Currently only resolvable via a position-based probe (first header button, no text) — not testid-only compliant; blocks step 8 without this addition. |
| Composer active-participant button | `chat-switch-participant-button` | on-main ✓ | Existing `ChatPage.switch_participant_button`. |
| Participants badge / popper / dynamic row | `chat-participants-badge-pipelines`, `chat-participants-badge-icon-pipelines`, `chat-participant-row-pipeline_{id}_{project_id}` | on-main ✓ | All confirmed live via the existing `PARTICIPANTS_BADGE`/`PARTICIPANT_ROW` dynamic templates already in `chat_page.py` — no new handle needed. |
| Message input / send button | `chat-message-input` / `chat-send-button` | on-main ✓ | Existing `ChatPage.message_input` / `send_button`. |

## Network Behavior
- `PUT /api/v2/elitea_core/application/prompt_lib/399/{id}` → `201 Created` on the create-mode Save (setup) and again on the edit-mode Save (step 7, "The pipeline has been updated").
- `GET /api/v2/elitea_core/applications/prompt_lib/399?...&agents_type=pipeline...` / `...&agents_type=classic...` → `200 OK`, refire after Save (list re-fetch for the Pipelines/Agents submenus).
- No 4xx/5xx observed at any point in this session's execution of this case's own 11 steps.

## Known Defects Found During Exploration
None new. One PRE-EXISTING, already-tracked test-robustness gap applies to step 11's send-message timing:
- **Issue #1085** ("[TEST-ROBUSTNESS] chat canvas test: + menu click lands on the conversation loading overlay") — reproduced during this analysis in a different shape (composer/message-input covered by a loading-spinner overlay, blocking `click()`, on a conversation whose surrounding sidebar list has accumulated many entries in this long-lived local environment). Confirmed NOT a defect in this case's own flow — the SAME real pytest suite (`test_chat_interface.py::TestSendingMessages::test_send_text_message`, which uses the `conversation_id` fixture + `navigate_to_chat(conversation_id=...)`) sends messages successfully in this exact environment (5/5 passed, re-verified live during this session). The gap is specific to driving a BRAND NEW conversation via the raw `+Chat` sidebar button without the fixture's readiness handling — not specific to this case's pipeline/participant flow. See § Automation Hints.

## Blocked Steps
None. All 11 case steps were executed and observed end-to-end live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: the Flow Editor / YAML / add-node surface is the SAME `EditorPanel` component the standalone `PipelineDetailPage` already drives (confirmed via source: `PipelineEditor.jsx` imports `@/pages/Pipelines/Components/EditorPanel`, the identical module `pipeline_detail_page.py`'s methods already target). Compose `ChatPage` (canvas entry point, close, chip, participants) + `PipelineDetailPage` (Flow Editor internals) on the SAME `page`, exactly like `test_create_agent_via_chat_canvas.py` composes `ChatPage` + `AgentFormPage`. Do not write a new Flow-Editor page object from scratch.
- `PipelineDetailPage.add_node()`'s existing raw-selector body (`button.MuiIconButton-colorPrimary`, `get_by_role("menuitem", ...)`) is being **reused unchanged**, not newly authored — this is NOT a new testid-only violation (the reviewer's mechanical diff-grep only flags ADDED lines; this method's body is untouched by this case's implementation). If the reviewer or lead wants it hardened, that is a separate, opt-in improvement to `pipeline_detail_page.py`, out of scope for this AFS.
- Two `needs-adding` testids are required before compliant automation: `agent-save-button` on `CreateApplicationSaveButton.jsx` (setup only — shared with the already-flagged ELITEA-2166 gap) and `pipeline-canvas-close-button` on `PipelineEditor.jsx`'s `<BaseEditor>` call (step 8). Both are mechanical, low-risk pluming (the props already exist end-to-end; only the call-site value is missing).
- Step 11: prefer the `conversation_id` fixture (`ConversationAPI`-backed, existing pattern in every `test_chat_interface.py` test) over a bare `sidebar-create-button` click for the conversation this case's setup uses — sidesteps the known #1085-class loading-overlay timing gap entirely, since API-created conversations navigate straight to a real `/chat/{id}` URL rather than sitting in an unsent, ID-less draft state.
- Wait strategy: no fixed sleeps — `wait_for_ai_response()` (existing method) for step 11; standard `is_editable()`/`wait_for(state="visible")` polling elsewhere, matching `ChatPage.wait_for_page_load()`'s own idiom.
