# Test Case: Chat – Create Pipeline from Conversation – Discard Changes and Verify Data is Cleared

## Metadata
- **TMS ID**: ELITEA-2076
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`, matches `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer slot, `.agents/test-automation.yaml` batch tiering)
- **Status**: **ready-for-automation** — case executed end-to-end live (all 10 steps observed against the real app) at analysis time. Reuses the exact same in-chat "Create New Pipeline" canvas entry point already automated by ELITEA-2079 (`ChatPage.open_create_new_pipeline_canvas()`, `PipelineDetailPage.fill_form()` — same `CreateAgentForm`/`BaseEditor`/`EditorHeader` shared chrome). New page-object surface needed only for the canvas's Discard button + its confirmation modal (`PipelineCanvasPage`), which the ELITEA-2079/ELITEA-2089 sibling cases never exercised (ELITEA-2089's own AFS/test only verified the Agent canvas's Discard button became *enabled*, never clicked it).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation in the Chats section — satisfied via the `conversation_id` fixture (API-created, real `/chat/{id}` URL from the first navigation, sidesteps the known #1085-class loading-overlay/composer-timing gap already documented for this canvas family in `test-specs/chat-interface/_surface.md` § "In-chat 'Create New X' canvas family").

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Private project (`${ELITEA_PROJECT_ID}`, `399`) — ambient default for a fresh dev-token session in this environment (confirmed live).

### generate-per-test
- **New conversation** — created via the `conversation_id` fixture (API, `ConversationAPI`), auto-deleted after the test.
- Case's own literal Test Data: Pipeline name `test-pipeline`, Pipeline description `This is a test pipeline for validation`. No pipeline is ever persisted by this flow (Discard, never Save) — nothing to clean up on the pipeline side.

## Test Steps

1. Navigate to the Chats section and open or create a conversation.
   - **Verify**: `ChatPage.navigate_to_chat(conversation_id=...)` (existing method, `conversation_id` fixture); `message_input` (`chat-message-input`) visible.
2. Click the `+` icon at the bottom left of the message input area.
   - **Verify**: `ChatPage.plus_menu_button` (`plus-menu-button`, existing, confirmed **on-main ✓**) click opens the popup menu; `pipelines-menuitem` (existing, confirmed **on-main ✓**) becomes visible. **MUI-overlay gotcha confirmed live** (`.claude/rules/mui-patterns.md`): a direct Playwright `.click()` on `plus-menu-button` times out — "subtree intercepts pointer events" — an invisible MUI overlay div sits over the button even though Playwright's actionability check reports it visible/enabled/stable. Requires `force=True` or `evaluate("el => el.click()")`; confirmed both work live (`page.evaluate` used during this analysis). Not a new finding — `ChatPage.open_create_new_pipeline_canvas()` (the existing, already-merged method reused by ELITEA-2079) already handles this internally; the implementer only needs to call the existing method, not re-derive the click strategy.
3. Click on "Pipelines" and then click "+ Create New Pipeline".
   - **Verify**: `ChatPage.open_create_new_pipeline_canvas()` (existing method — hover `pipelines-menuitem` → click `pipelines-create-new-button`, both confirmed **on-main ✓**). Confirmed live: canvas slides in on the right, heading "Create New Pipeline".
4. Verify the canvas header shows "Create New Pipeline" with X, "Discard", and "Save" buttons.
   - **Verify**: confirmed live — heading text exactly "Create New Pipeline"; three header controls present: X (no text), "Discard" (disabled), "Save" (disabled) — both Discard/Save start disabled (form not yet dirty), matching this case's own step-2 implication ("canvas header is correct") without asserting enabled state yet (that's covered by the Name/Description-typing steps below via the Discard-button-enabled check). Close button: `pipeline-canvas-close-button` (confirmed **on-main ✓**, added by ELITEA-2079). Discard button: confirmed live via DOM probe — **NO TESTID PATH THREADED** for either the button itself or its confirmation modal at this call site (`PipelineEditor.jsx`'s `<BaseEditor>` call did not supply `discardButtonTestId`/pass any modal testid — `EditorHeader.jsx` already rendered `Button.DiscardButton` unconditionally when `!isPublic`, and `Button.DiscardButton` itself already supports `modalDataTestId`/`confirmButtonDataTestId` internally per `CredentialsTabBar.jsx`'s existing usage, but `EditorHeader.jsx` never forwarded them). See § Concrete Handles for the full add-data-testid plan.
5. Type "test-pipeline" in the "Name *" field.
   - **Verify**: `PipelineDetailPage.name_input` (`agent-name-input`, existing, confirmed **on-main ✓**, same shared `CreateAgentForm` component ELITEA-2079's setup already uses). Confirmed live: field shows `"test-pipeline"`.
6. Type "This is a test pipeline for validation" in the "Description *" field.
   - **Verify**: `PipelineDetailPage.description_input` (`agent-description-input`, existing, confirmed **on-main ✓**). Confirmed live: field shows the full description text. **Side observation, confirmed live**: once both fields are dirty, the (until-now-disabled) Discard button becomes enabled — a useful intermediate assertion point, added as Axis 2 below.
7. Click the "Discard" button.
   - **Verify**: confirmed live — clicking the (now-enabled) Discard button opens a confirmation `Warning` dialog with body text `"Are you sure you want to discard changes?"` and its own "Discard" button. `Button.DiscardButton`'s pre-existing, unconditional confirm-modal-before-calling-`onDiscard` behavior (same mechanism `ToolkitCreationPage`'s Cancel-confirm flow already documents) — not new UI logic, only a new testid path to reach it (see step 4 / § Concrete Handles).
8. Click "Discard" to confirm.
   - **Verify**: confirmed live — the confirmation modal closes (removed from DOM); `PipelineDetailPage.name_input`/`description_input` both read back `""` (Formik's `resetForm()` inside `useDiscardApplicationChanges`, wired through `EditorHeader.jsx` → `PipelineEditor.jsx`'s `handleDiscard` → `dispatch(actions.resetPipeline())`); the Discard button itself returns to `disabled` (form no longer dirty). **Network-level confirmation**: zero `POST`/`PUT` requests to `/applications/prompt_lib/{project}` fired at any point in this flow (captured via the page's response listener across the whole scenario) — the Discard path never calls the create endpoint, unlike ELITEA-2079's Save path.
9. Close the canvas by clicking "X".
   - **Verify**: `PipelineCanvasPage.close_button` (`pipeline-canvas-close-button`, existing). Confirmed live: canvas chrome (`pipeline-canvas-close-button` et al.) removed from the DOM; conversation view fully displayed again.
10. Verify no pipeline was created in the PARTICIPANTS panel.
    - **Verify**: `ChatPage.is_participants_badge_visible(section="pipelines")` returns `False` — confirmed live (the `chat-participants-badge-pipelines` container disappears entirely from the DOM at participant count 0, per the pre-existing, already-documented behavior `ChatPage`'s own docstring records — the established idiom this suite already uses for "no X participant" assertions, e.g. `test_slash_mention_empty_state.py`, `test_direct_toolkit_call_complete_flow.py`).

## Expected Results
All 10 steps pass cleanly as specced above once the four `needs-adding` testids (§ Concrete Handles) land: canvas header shows the correct X/Discard/Save chrome; typing Name+Description enables Discard; clicking Discard opens the Warning confirmation dialog; confirming Discard clears both fields, re-disables Discard, and fires zero create requests; closing the canvas returns to the conversation view; the PARTICIPANTS panel shows no PIPELINES section. No product defect found — this flow behaves exactly as the case describes.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: open conversation in Chats section | — | Setup | `conversation_id` fixture + `navigate_to_chat()` | asserted |
| 1 Navigate to Chats, open/create conversation → Conversation view displayed | conversation view shown | step 1 | `message_input` visible | asserted |
| 2 Click + icon → Popup menu opens | popup menu visible | step 2 | `pipelines-menuitem` visible after plus-menu click | asserted |
| 3 Click Pipelines → + Create New Pipeline → canvas opens on the right | canvas opens | step 3 | canvas heading "Create New Pipeline" visible | asserted |
| 4 Verify canvas header shows title + X/Discard/Save | header correct | step 4 | heading text + 3 header controls present, Discard/Save start disabled | asserted |
| 5 Type "test-pipeline" in Name → Name appears in field | name entered | step 5 | `name_input` value == "test-pipeline" | asserted |
| 6 Type description → Description appears in field | description entered | step 6 | `description_input` value == full description text | asserted |
| 7 Click Discard → Confirmation dialog appears | confirm dialog shown | step 7 | discard-confirm-modal visible, body text confirmed | asserted |
| 8 Click Discard to confirm → Canvas content is cleared | fields cleared | step 8 | name/description values == "", Discard re-disabled, zero create requests fired | asserted |
| 9 Close canvas via X → Canvas closes | canvas closed | step 9 | canvas chrome testids absent from DOM | asserted |
| 10 Verify no pipeline created in PARTICIPANTS | no pipeline participant | step 10 | `is_participants_badge_visible(section="pipelines")` == False | asserted |
| Expected Final State: "All entered data is cleared after clicking Discard; no pipeline is created in the conversation" | — | steps 8, 10 | field-value + network + participants-badge assertions | asserted |
| Pass/Fail: "Discard clears all entered data and no pipeline is created" / "Pipeline is created despite discarding, or data is not cleared" | — | steps 8, 10 | same as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 6 adds an intermediate assertion that the Discard button transitions from disabled → enabled once the form becomes dirty — *added: gives the reviewer/implementer a clean, independently-verifiable checkpoint before step 7's click, and mirrors the same disabled→enabled pattern ELITEA-2089's AFS already asserts for the sibling Agent canvas.*
- Step 8 adds a network-level assertion (zero `POST`/`PUT` to `/applications/prompt_lib/{project}` across the whole flow) alongside the DOM-level field-clearing check — *added: the case's own Pass/Fail criteria explicitly calls out "Pipeline is created despite discarding" as a fail condition; a network-level check is a stronger, system-produced signal of "not created" than the DOM/participants-badge check alone (which could theoretically pass even if a create request fired but the response hadn't been consumed into a participant row yet). Confirmed live during this analysis: only pre-existing `GET .../applications/prompt_lib/399?...` list-refresh calls fired (from opening the `+` menu's Pipelines submenu), zero `POST`/`PUT`.*
- Console/network side-channel checked after every step — confirmed clean throughout (zero console errors, zero failed (4xx/5xx) requests) across all 10 steps in this session.

## Cleanup
1. Delete the created conversation via `conversation_api.delete_conversation(id)` (handled automatically by the `conversation_id` fixture's teardown).
2. No pipeline cleanup needed — this flow never persists a pipeline (confirmed live via the network-level check in step 8).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `cd EliteaUI && git fetch origin` (this session) then `git grep` on `origin/main`; `automation/testids` provenance is this session's own commit.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| `+` menu → Pipelines menuitem | `pipelines-menuitem` | on-main ✓ | Existing, reused from ELITEA-2079. |
| `+` menu → Pipelines submenu → "+ Create New Pipeline" | `pipelines-create-new-button` | on-main ✓ | Existing, reused from ELITEA-2079. |
| Pipeline Name field (create form) | `agent-name-input` | on-main ✓ | Existing, reused from ELITEA-2079 (`PipelineDetailPage.name_input`). |
| Pipeline Description field (create form) | `agent-description-input` | on-main ✓ | Existing, reused from ELITEA-2079. |
| Canvas X (close) button | `pipeline-canvas-close-button` | on-main ✓ | Existing, added by ELITEA-2079. |
| Canvas header title (`"Create New Pipeline"`) | `pipeline-canvas-title` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED fix-round-1 (`EliteaAI/EliteaUI@93dc5667`). `EditorHeader.jsx`'s title `Typography` already accepted an optional `titleTestId` prop (forwarded by `BaseEditor.jsx`), and sibling canvases already supply it (`AgentEditor.jsx` → `agent-canvas-title`, `ToolkitEditor.jsx` → `toolkit-canvas-title`/`mcp-canvas-title`) — `PipelineEditor.jsx`'s `<BaseEditor>` call simply never supplied a value. Supplied as `pipeline-canvas-title` at the Pipeline call site only, matching the Coverage Map row-4 claim that the heading text is asserted (previously unimplemented gap, filled in review fix round 1). |
| Canvas Discard button | `pipeline-canvas-discard-button` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED this session (`EliteaAI/EliteaUI@d4edc6e5`). `BaseEditor.jsx`/`EditorHeader.jsx` already rendered `Button.DiscardButton` unconditionally (`!isPublic` guard) with a pre-existing `discardButtonTestId` prop path (added for ELITEA-2089's Agent-canvas Discard, but never verified against a real click — that AFS only asserted `enabled`/`disabled` state) — `PipelineEditor.jsx`'s `<BaseEditor>` call simply never supplied a value for it. Supplied as `pipeline-canvas-discard-button` at the Pipeline call site only (component-sharing guard, same precedent as `agent-save-button`/`pipeline-canvas-close-button`). |
| Discard confirmation modal | `pipeline-canvas-discard-confirm-modal` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED this session (`EliteaAI/EliteaUI@d4edc6e5`). `Button.DiscardButton` (`DiscardButton.jsx`) already supports a `modalDataTestId` prop internally — `CredentialsTabBar.jsx` already calls it directly with one — but `EditorHeader.jsx`'s own `<Button.DiscardButton>` call only ever forwarded `dataTestId`, never `modalDataTestId`/`confirmButtonDataTestId`. Added two new optional props, `discardModalTestId`/`discardConfirmButtonTestId`, threaded `BaseEditor.jsx` → `EditorHeader.jsx` → the existing `Button.DiscardButton` props (same shape as the pre-existing `discardButtonTestId`), supplied ONLY at `PipelineEditor.jsx`'s call site — the sibling Agent/MCP chat canvases (`AgentEditor.jsx`/`ToolkitEditor.jsx`) are unaffected since the new props are optional and caller-supplied (`.agents/testing.md` § "Shared components never hardcode feature-scoped testids"). |
| Discard-confirm button (inside the modal) | `pipeline-canvas-discard-confirm-button` | **on-`automation/testids` only — awaiting human promotion to `main`** | ADDED this session (`EliteaAI/EliteaUI@d4edc6e5`), same commit/mechanism as the modal testid above. |
| PARTICIPANTS pipelines badge | `chat-participants-badge-pipelines` | on-main ✓ | Existing `ChatPage.is_participants_badge_visible(section="pipelines")` — same dynamic template ELITEA-2079 uses for the positive-presence case; this case is its negative-absence counterpart. |
| Message input | `chat-message-input` | on-main ✓ | Existing `ChatPage.message_input`. |

## Network Behavior
- `GET /api/v2/elitea_core/applications/prompt_lib/399?...&agents_type=classic...` / `...&agents_type=pipeline...` / `GET /api/v2/elitea_core/public_applications/prompt_lib/?...` → `200 OK` — list-refresh calls fired when the `+` menu's Pipelines submenu opens (unrelated to this case's own Discard flow, same background calls ELITEA-2079 also observes).
- **Zero** `POST`/`PUT` to `/applications/prompt_lib/{project}` at any point — confirmed live across the full Name/Description-typed → Discard → confirm-Discard sequence. This is the case's own central concern (Pass/Fail: "Pipeline is created despite discarding" is a fail) and is asserted directly in the test (see Axis 2).
- No 4xx/5xx observed at any point in this session's execution of this case's own 10 steps.

## Known Defects Found During Exploration
None. This flow behaves exactly as the case describes — Discard correctly clears all entered data and never creates a pipeline.

## Blocked Steps
None. All 10 case steps were executed and observed end-to-end live.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Reuse, don't rewrite**: compose `ChatPage` (canvas entry point, plus-menu, participants badge) + `PipelineDetailPage` (Name/Description fields, inherited from `PipelineFormPage`) + the new `PipelineCanvasPage` (close/discard/discard-confirm chrome) on the SAME `page` — exactly the same composition pattern ELITEA-2079's test already uses, plus the new Discard-specific fields.
- **`PipelineCanvasPage` needs three new fields + two new methods** (mirrors `CredentialDetailPage`'s existing `discard_button`/`discard_confirm_modal`/`discard_confirm_button` + `click_discard()`/`confirm_discard()` shape 1:1 — same underlying `Button.DiscardButton`/`BaseModal` components, different call site).
- Three `needs-adding` testids required before compliant automation (all added this session, pushed to `automation/testids` — see § Concrete Handles): `pipeline-canvas-discard-button`, `pipeline-canvas-discard-confirm-modal`, `pipeline-canvas-discard-confirm-button`.
- **MUI overlay gotcha on `plus-menu-button`** (step 2): a direct Playwright `.click()` times out ("subtree intercepts pointer events") even though the button reports visible/enabled/stable — `.claude/rules/mui-patterns.md`'s documented MUI-overlay-interception pattern. Already handled inside the existing, reused `ChatPage.open_create_new_pipeline_canvas()` method — no new workaround needed by the implementer, just call the existing method.
- Wait strategy: no fixed sleeps — `wait_for(state="visible"/"detached")` polling throughout, matching `PipelineCanvasPage`'s existing `close()`/`click_flow_editor_tab()` idiom and `CredentialDetailPage`'s `click_discard()`/`confirm_discard()` idiom.
- Network-absence assertion (step 8): register a `page.on("response", ...)` listener before opening the canvas, collect any `POST`/`PUT` whose URL contains `/applications/prompt_lib/`, assert the collected list is empty after confirming Discard — mirrors the existing `console_messages` collector pattern already used throughout this suite (e.g. `test_pipeline_flow_editor_add_llm_node_from_chat_canvas.py`), applied to network responses instead of console messages.
