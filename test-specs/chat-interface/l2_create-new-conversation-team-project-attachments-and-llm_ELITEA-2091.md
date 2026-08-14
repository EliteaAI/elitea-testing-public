# Test Case: Chat – Team Project – Create New Conversation with File Attachments (picker + drag-drop) and Changing LLM

## Metadata
- **TMS ID**: ELITEA-2091
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; Team project "Elitea Testing Team", observed live as `projectId=471`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (analyst slot), 2026-08-14
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture on localhost).
- Acting project switched to the Team project `${ELITEA_TEAM_PROJECT_ID}` (471, "Elitea Testing Team") — a Private project's plus-menu never renders "Invite Users" (confirmed live, `PlusChatButton.jsx`'s `!isPrivateProject` guard), which is part of this case's own step-2 expected result.

## Test Data
### reuse-existing
- `${ELITEA_TEAM_PROJECT_ID}` = `471` ("Elitea Testing Team") — same project + env var already used by `test_open_conversation_today_section.py` / `test_team_users_mention_and_remove_participants.py` / `test_invite_users_add_cancel_close.py`. Do not reintroduce a second hardcoded `TEAM_PROJECT_ID = "471"` local constant in a NEW file needlessly — check whether a shared constant now exists before adding a fourth copy.
- First message: `"Please review the attached documents"` (verbatim, per case Test Data table).
- A non-default LLM to switch to — any model whose `model-selector-option-{name}` testid differs from the project's current default. Do not hardcode a display name (case-text drift risk, confirmed live — see § Concrete Handles); resolve the model actually pre-selected in the composer at runtime and pick any OTHER menu item.

### generate-per-test (in test setup, cleaned up in its own teardown)
- 3 small `.txt` files via `tmp_path`, each with a unique-token body (mirrors the existing `test_attach_files_10_file_limit_warning.py` / `test_attach_files_button_sends_file_with_message` pattern) — attached via the file-chooser (step 4).
- 1 additional small `.txt` file (distinct name/content) — attached via drag-and-drop (step 5). Total attachments after both steps = 4, well under the 10-file ceiling, so neither the "10 left" boundary nor the limit-warning toast (already covered by ELITEA-2197) is exercised here.
- The conversation itself is created fresh via the UI's own "+Chat" flow (`sidebar-create-button`) — NOT seeded via `ConversationAPI.create_conversation()` (see the `EliteaAI/elitea-testing-public#691` note the ELITEA-2095 AFS/test already carries: sending the first UI message to a conversation that exists server-side with ZERO messages silently creates a brand-new conversation). Clean up via `ConversationAPI(browser_cookies=..., project_id=ELITEA_TEAM_PROJECT_ID).delete_conversation(conv_id)` in a `finally` block, same pattern as `test_open_conversation_today_section.py`.

## Test Steps
1. Switch to the Team project (471); click "+Chat" (`sidebar-create-button`).
   - **Verify**: a new blank conversation opens — message input visible and empty.
2. Click the plus-menu button (`plus-menu-button`) below the message input.
   - **Verify**: the popper shows exactly: "Attach Files" (with an "N left" counter, N = 10 for a fresh conversation), Modules, Agents, Pipelines, Toolkits, MCPs, **and Invite Users** (Invite Users renders ONLY because this is a Team project — confirmed live by diffing the SAME popper on the default Private project, where it is absent).
3. Click "Attach Files" (`chat-attach-menuitem-button`).
   - **Verify**: the native OS file chooser opens (`page.expect_file_chooser()`).
4. Select 3 files in ONE chooser action (`file_chooser.set_files([...])`); verify each is listed as a chip and the counter decrements by the number attached.
   - **Verify**: 3 chips render (`chat-attachment-chip-{index}`, filenames match); "Attach Files (N left)" text on `chat-attach-menuitem-button` reads `"{10 - 3} left"` = `"7 left"` (live-confirmed exact transition 10→7 for 3 files).
5. Drag and drop 1 additional file onto the composer (see § Automation Hints — Drag-and-drop technique) and verify it appears identically to a picker-attached file.
   - **Verify**: a 4th chip renders with the dropped file's name; counter now reads `"6 left"`; the dropped file's chip is structurally identical to the picker-attached ones (same `chat-attachment-chip-{index}` template, same delete affordance).
6. Click the model selector (`model-selector-name`/`model-selector-button`).
   - **Verify**: the model dropdown menu opens, listing every available model as a `model-selector-option-{model.name}` menuitem (`model.name` = the model's raw/internal id, NOT its display text — confirmed live, e.g. `model-selector-option-eu.anthropic.claude-sonnet-4-5-20250929-v1:0` for the item displaying "Anthropic Claude 4.5 Sonnet").
7. Select a different LLM from the dropdown (any option other than the one currently selected).
   - **Verify**: the selected option's `MenuItem` carries `Mui-selected` (source-confirmed: `LLMModelsMenu.jsx`'s `selected={item.id === selectedModel?.id}`) and renders its checkmark icon (`CheckedIcon`, conditionally shown only for the selected item — same element, no separate testid); the composer's model-selector trigger (`model-selector-name`) now shows the newly-selected model's display name, replacing the previous one.
8. Type `"Please review the attached documents"` into the message input (`chat-message-input`).
   - **Verify**: text appears in the input.
9. Click Send (Enter, per the existing `ChatPage.send_message(use_enter=True)` convention).
   - **Verify**: the message renders in the thread with all 4 attached filenames listed under it; URL becomes `/chat/{conversation_id}?name=...`; the composer disables while the AI response streams.
10. Verify a new conversation entry appears under "Today" with a "Naming…" placeholder that resolves to an auto-generated title.
    - **Verify**: `chat-conversation-group-header-today` is visible and contains the new conversation; immediately post-send it renders as a "Naming" button with a progress spinner (live text: `"Naming"`, `role="progressbar"` inside); within ~15s it resolves to a real, non-"Naming" title (live-confirmed this session: resolved to `"Review attached documents"` for the exact first message above — do not assert this EXACT string, LLM titling is non-deterministic; assert only that the placeholder text is gone and the conversation renders with a genuine title as its accessible name).

## Expected Results
- All steps complete without errors.
- Files attach via BOTH the picker (step 4) and drag-and-drop (step 5); the LLM changes and is reflected with a checkmark in the dropdown and in the composer trigger; the message + all 4 attachments are submitted and appear in the thread; the conversation is auto-named after the first exchange.
- No console errors beyond the pre-existing, already-documented project-471 `secrets` 403 (`GET .../secrets/secrets/default/471` — fires on every page load in this project regardless of any action taken; filter it the same way `test_open_conversation_today_section.py`'s `_is_known_project_471_secrets_403()` does, don't let it mask a genuinely new error).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Team project, Chats, +Chat | new blank conversation opens | step 1 | `step 1`: message input visible+empty | asserted |
| 2 Click + button | dropdown with Attach Files (10 left), Modules, Agents, Pipelines, Toolkits, MCPs, Invite Users | step 2 | `step 2`: popper item set + counter text | asserted |
| 3 Click "Attach Files" | file picker opens | step 3 | `step 3`: `expect_file_chooser()` resolves | asserted |
| 4 Select up to 10 files, verify listed + counter decrements | files attached, counter correct | step 4 | `step 4`: chip count + names + counter text | asserted |
| 5 Drag and drop file(s), verify identical to picker | dropped files appear identically | step 5 | `step 5`: chip renders, same template, counter decrements further | asserted |
| 6 Click LLM model selector | list of LLMs opens | step 6 | `step 6`: menu visible, one `model-selector-option-*` per model | asserted |
| 7 Select a different LLM | selected LLM shown with checkmark | step 7 | `step 7`: `Mui-selected` class + checkmark icon + composer trigger text | asserted |
| 8 Type message | message entered | step 8 | `step 8`: input value | asserted |
| 9 Click Send | message + files submitted, appear in thread | step 9 | `step 9`: thread content + URL | asserted |
| 10 New conversation under "Today" with "Naming…" resolving to a title | conversation auto-named | step 10 | `step 10`: group membership + placeholder-then-title | asserted |
| Test Data: Max file attachments = 10 | ceiling respected | steps 4–5 | total attached (4) stays under 10; the 10-file boundary itself is already covered by ELITEA-2197 (`test_attach_files_10_file_limit_warning.py`) | already-covered *(cross-reference, not re-asserted here — see § Automation Hints)* |

**Axis 2 — Analyst additions:**
- `step 2` asserts "Invite Users" specifically PRESENT (not just the other 6 items) — *added: this is the live, structural signal that proves the case actually ran against a Team project and not the default Private one (the item is entirely absent, not merely disabled, on Private) — silently running this case against the wrong project would otherwise pass steps 3–10 unnoticed.*
- `step 9`/`step 10` assert the known, pre-existing project-471 `secrets` 403 does NOT mask a genuinely new console error — *added: standard side-channel discipline for this project (`ChatPage`/sibling specs already filter this exact noise); omitting the filter would either false-fail on unrelated ambient noise or (worse) hide a real new error behind a blanket ignore.*
- (Nothing else added beyond the case's own 10 steps + its Test Data ceiling.)

## Cleanup
1. `ConversationAPI(browser_cookies=..., project_id=ELITEA_TEAM_PROJECT_ID).delete_conversation(conv_id)` in a `finally` block.
2. `tmp_path`-based attachment files clean up automatically (pytest fixture).

## Concrete Handles (discovered during exploration)

Locator policy: testid-only (`.agents/testing.md` § Locator policy) — no role/label/text ladder. Every handle below is a `LocatorDescriptor(testid=...)` field or an UPPER_CASE `[data-testid="…"]` template constant. **Provenance freshly verified this session** (`cd EliteaUI && git fetch origin` first, then `git grep` both refs):

| Element | Testid | Provenance (main / automation/testids) |
|---|---|---|
| Team project selector trigger | `project-selector-trigger-combobox` (base `project-selector-trigger`, MUI `SelectDisplayProps` auto-suffixes `-combobox`) | on-main ✓ |
| Project dropdown option (dynamic) | `select-option-{project_id}` (e.g. `select-option-471`) — `ChatPage.SELECT_OPTION` template, pre-existing | on-main ✓ |
| "+Chat" button | `sidebar-create-button` (`ChatPage.create_conversation_button`) | on-main ✓ |
| Plus-menu trigger | `plus-menu-button` (`ChatPage.plus_menu_button`) | on-main ✓ |
| "Attach Files" popper item (+ "N left" text, no separate testid — read via `.text_content()`) | `chat-attach-menuitem-button` (`ChatPage.attach_files_button`) | on-main ✓ |
| Modules popper item | `internal-tools-menuitem` (`ChatPage.internal_tools_menuitem`) | on-main ✓ (per digest) |
| Agents popper item | `agents-menuitem` | on-main ✓ (per digest) |
| Pipelines popper item | `pipelines-menuitem` | on-main ✓ (per digest) |
| Toolkits popper item | `toolkits-menuitem` | on-main ✓ (per digest) |
| MCPs popper item | `mcps-menuitem` | on-main ✓ (per digest) |
| Invite Users popper item (Team-project only) | `invite-users-menuitem` | on-main ✓ |
| Attachment chip (dynamic, 0-based render index) | `chat-attachment-chip-{index}` (`ChatPage.CHAT_ATTACHMENT_CHIP`) | on-main ✓ |
| Message input | `chat-message-input` (`ChatPage.message_input`) | on-main (pre-existing) |
| Model selector trigger | `model-selector-name` / `model-selector-button` (`ChatPage.model_selector`) — live click resolved to `model-selector-name` specifically | on-main ✓ |
| Model dropdown option (dynamic, keyed by internal model id, NOT display name) | `model-selector-option-{model.name}` | on-main ✓ |
| "Today" date-group header (dynamic) | `chat-conversation-group-header-{group}` (`ChatPage.CONVERSATION_GROUP_HEADER`, `group="today"`) | on-main ✓ |
| Conversation item within a group (dynamic) | `chat-conversation-item-{conversation_id}` (`ChatPage.CONVERSATION_ITEM`) scoped inside the group header | on-main ✓ |
| "Naming…" placeholder | no testid — live text `"Naming"` inside the group-header conversation button, with a nested `role="progressbar"`; `ChatPage.wait_for_naming_label_to_resolve()` already implements the wait (existing method, reuse verbatim) | n/a (text-based, pre-existing helper) |
| **Drag-and-drop composer drop-zone** | **`testid needed: chat-composer-dropzone`** — the outer `Box` in `EliteaUI/src/ComponentsLib/Chat/UserInput.jsx` (`sx={styles.container}`, wraps `onDragOver`/`onDragLeave`/`onDrop`) currently carries NO testid at all (confirmed via source read). Add via `add-data-testid` on that exact `Box` before this step can be automated with a stable handle. | needs-adding |

## Network Behavior
- No new network endpoints beyond the existing chat-send/attachment-upload traffic already documented by `test_attach_files_10_file_limit_warning.py` / `test_open_conversation_today_section.py`. `POST .../secrets/secrets/default/471` fires a benign, already-documented 403 on every page load in this project — filter, don't assert against it.

## Known Defects Found During Exploration
None found. Full live walkthrough this session (Team-project switch → +Chat → plus-menu item set incl. Invite Users → attach 3 files via picker (counter 10→7, confirmed) → LLM switch to a non-default model (composer trigger text updated, confirmed) → send with all 3 attachments → conversation appeared under "Today" as a "Naming" placeholder with a progressbar → resolved within ~15s to a real title) reproduced every case step's expected result with no functional defect. (Drag-and-drop itself, step 5, was not click-verified live this session — see § Blocked Steps — but is a real, working product feature per source: `useFileDragAndDrop` hook is genuinely wired to `onDrop`, not a stub.)

## Blocked Steps
None blocking automation.
- **RESOLVED during implementation (ELITEA-2091 implementer pass):** Step 5's drop-zone testid (`chat-composer-dropzone`) was added to `UserInput.jsx` via `add-data-testid` (`automation/testids` commit `dd417746`) and live-verified end-to-end: the synthetic-`DataTransfer` drag-and-drop technique (declared, transit-only per § Automation Hints below) dispatches real `dragenter`→`dragover`→`drop` `DragEvent`s carrying a real in-page-constructed `File`, exercising the genuine `useFileDragAndDrop`/`AttachmentButton.handleFileChange` pipeline — chip renders, "N left" counter decrements, and the dropped filename appears in the sent message thread, all confirmed live. See `test-specs/chat-interface/_surface.md`'s "Resolved/added during ELITEA-2091 implementation" section for the full set of implementation-time findings (overflow-bucket counting, an `Escape`-closes-parent-popper side effect, a model-switch render race, and a model-selector reopen reliability fix).

## Automation Hints
- Page object: extend `ChatPage` (`automation/pages/chat_page.py`) — every non-drag-drop handle above already has a page-object field or an existing method (`switch_project()`, `click_create_conversation()`, `open_attach_menuitem()`/`attach_files_via_menu()`, `get_total_attached_file_count()`/`get_all_attached_file_names()`, `click_model_selector()`, `is_conversation_group_visible()`/`click_conversation_in_group()`, `wait_for_naming_label_to_resolve()`). Don't duplicate — reuse verbatim.
- Fixture: NOT the shared `conversation_id` fixture (that seeds via `ConversationAPI`, which hits the documented `#691` "first message on a zero-message server-side conversation silently creates a new one" defect) — create the conversation live via `+Chat`, same as `test_open_conversation_today_section.py`.
- **Drag-and-drop technique (step 5) — not a fidelity substitution.** A real OS-level drag from Finder/Explorer can't be driven by Playwright; the standard, non-substituting technique is to construct a synthetic `DataTransfer` holding a REAL `File` object (built in-page via `page.evaluate()` from the real file's bytes, e.g. base64-encoded and reconstructed via `new File([...], name, {type})`) and dispatch `dragenter`→`dragover`→`drop` `DragEvent`s at the composer drop-zone. This substitutes only the INPUT MECHANISM (mouse+OS drag, which Playwright cannot produce), not the observable: the real `onDrop` handler, the real upload/attach pipeline, and the real chip render are all exercised exactly as they are for the picker path in step 4 — no response is mocked, no app state is injected via `page.evaluate()` beyond constructing the synthetic input event itself. Declare this technique in the test docstring per `.agents/testing.md` § Fidelity policy (transit-only note), even though it is not a terminal substitution of the case's own observable.
- Model selection: resolve the CURRENTLY selected model's testid at runtime (read the composer trigger's text, or query which `model-selector-option-*` carries `Mui-selected`) before picking a different one — do not hardcode a display name (case-text/environment drift risk: this session's default model was `GPT-5.4` on the Team project vs `Anthropic Claude 4.5 Sonnet` on the Private project, and the model roster itself is environment-configured).
- Counter text: `chat-attach-menuitem-button` has no separate testid for its "N left" sub-text (`AttachmentButton.jsx` renders it as a plain child `Typography`, same parent testid) — read via `.text_content()` on the already-testid'd parent and assert the substring `f"{n} left"`, not a new locator.
- Reuse for auto-naming: this exact mechanism (Today group + "Naming" placeholder + resolution) is already live-proven end-to-end by the merged `test_open_conversation_today_section.py` (ELITEA-2095) in the SAME environment/project — this case adds the attachments+LLM-change precondition on top of it, it does not re-derive the naming mechanism from scratch.
