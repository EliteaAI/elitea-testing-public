# Test Case: Chat – File Attachments – Send Message with Attached Files and Verify Files Are Included

## Metadata
- **TMS ID**: ELITEA-2201
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; default Private project)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (analyst slot, combined dispatch), 2026-08-19
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture on localhost).
- A new, blank conversation is opened via "+Chat" (default Private project — the case text names no specific project, unlike ELITEA-2091's Team-project scenario).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- 4 small `.txt` files via `tmp_path`, each with a distinct name and a unique-token body (mirrors the existing `test_attach_files_10_file_limit_warning.py` pattern) — attached via the file-chooser (case step 1: "3-4 supported files").
- Message text: `"Please analyze these files"` (verbatim, per case Test Data table).
- The conversation itself is created fresh via the UI's own "+Chat" flow (`sidebar-create-button`) — NOT seeded via the shared `conversation_id` fixture (`ConversationAPI.create_conversation()`), for the SAME documented reason as ELITEA-2091's AFS: sending the first UI message to a conversation that exists server-side with ZERO messages silently creates a brand-new conversation (`EliteaAI/elitea-testing-public#691`). Clean up via `ConversationAPI(browser_cookies=...).delete_conversation(conv_id)` in a `finally` block, using the conversation id read back from the URL after send (same pattern as `test_create_new_conversation_team_project_attachments_and_llm.py`).

## Test Steps
1. Click "+Chat" (`sidebar-create-button`); click the plus-menu button (`plus-menu-button`); click "Attach Files" (`chat-attach-menuitem-button`); select 4 files in ONE chooser action.
   - **Verify**: 4 chips render (`chat-attachment-chip-{index}`, filenames match) and the "Attach Files (N left)" counter decrements by 4 (`"6 left"` for a fresh conversation).
2. Type `"Please analyze these files"` into the message input (`chat-message-input`).
   - **Verify**: text appears in the input.
3. Click Send (Enter — `ChatPage.send_message(use_enter=True)` convention).
   - **Verify**: the message renders in the thread with all 4 attached filenames listed under it; the URL becomes `/chat/{conversation_id}?name=...`.
4. Wait for the AI/agent response to fully complete (`ChatPage.wait_for_ai_response()`).
   - **Verify**: the response is non-empty, non-transient, real generated content — AND, live-confirmed this session (see § Automation Hints), the response text explicitly references each of the 4 attached filenames by name. This is the case's own Pass criterion ("Response references attached files"); per `.agents/testing.md` § Fidelity policy the assertion reads the REAL captured response text (the oracle), never a hand-written/fabricated payload.
5. Verify the composer's attachment chips are cleared after send.
   - **Verify**: `chat.wait_for_attachment_chip_count(0)` — zero visible chips remain in the composer; `chat.get_attachment_overflow_count() == 0` — no residual overflow bucket either. (Live-confirmed: the composer's "Attach Files" counter also resets to the full `"10 left"` post-send, corroborating the chip-clear.)

## Expected Results
- All steps complete without errors.
- Files attach via the picker; the message + all 4 attachments are submitted and appear in the thread; the AI/agent produces a real response that references the attached files by name; the composer's attachment chips are cleared after send.
- No console errors / uncaught JS exceptions across the flow.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Attach 3-4 supported files via + icon > Attach Files | Files uploaded and chips shown | step 1 | `step 1`: chip count + names + counter text | asserted |
| 2 Type message | Message entered | step 2 | `step 2`: input value | asserted |
| 3 Click Send | Message sent; file references included in conversation | step 3 | `step 3`: thread content (message text + all 4 filenames) + URL | asserted |
| 4 Verify LLM/agent acknowledges and begins processing the files | Response references attached files | step 4 | `step 4`: real captured AI response text contains each attached filename | asserted |
| 5 Verify after sending, attachment chips are cleared from input field | Chips cleared | step 5 | `step 5`: visible chip count == 0 (web-first wait) + overflow count == 0 | asserted |

**Axis 2 — Analyst additions:**
- `step 3` asserts the URL transitions to `/chat/{id}?name=...` — *added: the same structural signal ELITEA-2091 uses to prove a real conversation was created and navigated to, not merely that some DOM text appeared.*
- Side-channel check (no unexpected console errors/page errors) across the full flow — *added: standard discipline for this project, same idiom as every sibling chat-attachment test in this file's neighbourhood.*
- (Nothing else added beyond the case's own 5 steps.)

## Cleanup
1. `ConversationAPI(browser_cookies=...).delete_conversation(conv_id)` in a `finally` block, using the conversation id read from the post-send URL (NOT a fixture-seeded id — see § Test Data / #691).
2. `tmp_path`-based attachment files clean up automatically (pytest fixture).

## Concrete Handles (discovered during exploration)

Locator policy: testid-only (`.agents/testing.md` § Locator policy). Every handle below is a pre-existing `LocatorDescriptor(testid=...)` field or UPPER_CASE `[data-testid="…"]` template constant on `ChatPage` — **zero new testids needed for this case**. **Provenance freshly re-verified this session** (`cd EliteaUI && git fetch origin` first, then `git grep` both refs):

| Element | Testid | Provenance (main / automation/testids) |
|---|---|---|
| "+Chat" button | `sidebar-create-button` (`ChatPage.click_create_conversation()`) | on-main ✓ |
| Plus-menu trigger | `plus-menu-button` (`ChatPage.plus_menu_button`) | on-main ✓ |
| "Attach Files" popper item (+ "N left" text via `.text_content()`) | `chat-attach-menuitem-button` (`ChatPage.attach_files_button`) | on-main ✓ |
| Attachment chip (dynamic, 0-based render index) | `chat-attachment-chip-{index}` (`ChatPage.CHAT_ATTACHMENT_CHIP`/`CHAT_ATTACHMENT_CHIP_PREFIX`) | on-main ✓ |
| Message input | `chat-message-input` (`ChatPage.message_input`) | on-main ✓ |
| Message item (user + AI) | `chat-message-item` (`ChatPage.messages_container`) | on-main ✓ |
| Send / composer state | `send-button` (existing `ChatPage.send_message()` internals) | on-main ✓ |

## Network Behavior
- No new network endpoints beyond the existing chat-send/attachment-upload traffic already documented by the neighbouring attachment tests. The AI response involves the existing predict/streaming pipeline — no toolkit calls are needed since the model reasons over the embedded attachment content directly (live-confirmed: the model's own "Thinking" trace states "The content has been embedded directly in the messages, so I don't need to use file reading tools").

## Known Defects Found During Exploration
None found. Full live walkthrough this session (blank composer → plus-menu → Attach Files → 4-file picker selection, counter 10→6 → typed "Please analyze these files" → Enter → message + 4 filenames rendered in thread, URL became `/chat/9082?name=Analyze+these+files` → composer chips cleared immediately (counter back to "10 left") while the AI response streamed → response (~20s) explicitly named `report_alpha.txt`, `notes_beta.txt`, `summary_gamma.txt` verbatim in both its "Thinking" trace and its final Markdown answer) reproduced every case step's expected result with no functional defect.

## Blocked Steps
None.

## Automation Hints
- Page object: extend `ChatPage` — every handle above already has a page-object field or an existing method (`click_create_conversation()`, `attach_files_via_menu(file_paths)`, `get_total_attached_file_count()`/`get_all_attached_file_names()`, `send_message(text, use_enter=True)`, `wait_for_ai_response(initial_count)`, `get_last_message_text()`, `wait_for_attachment_chip_count(0)`, `get_attachment_overflow_count()`). Don't duplicate — reuse verbatim.
- Fixture: NOT the shared `conversation_id` fixture — see § Test Data (`#691`). Create the conversation live via `+Chat`, same as `test_create_new_conversation_team_project_attachments_and_llm.py` (ELITEA-2091).
- **Response-content assertion is NOT a fidelity substitution.** The assertion reads `ChatPage.get_last_message_text()` AFTER `wait_for_ai_response()` — the real, live-generated response text — and checks each attached filename appears as a substring. This is the "capture the real response and assert against it" pattern (`.agents/testing.md` § Fidelity policy, "How to test a NONDETERMINISTIC producer without substituting it") — the assertion is a structural invariant over real output, not a hand-authored payload. Live-confirmed this session: small, distinctly-named `.txt` files with a short text body reliably elicit a response that quotes the filenames back verbatim (the model has no file-reading tool call to make — content is embedded directly in the message — so it engages with the literal filenames/content given). Use 4 small `.txt` files (well-supported format per ELITEA-2200), not exotic formats, to keep this reliable.
- Attach via `attach_files_via_menu(file_paths)` (opens the popper + file chooser + selects files in one call) — simpler than the multi-step popper-inspection sequence ELITEA-2091 uses, since this case doesn't need to assert the full popper item set.
- Chip-clear check (step 5) uses `wait_for_attachment_chip_count(0, timeout=...)` — a web-first, auto-retrying `expect(...).to_have_count(0)` wrapper — rather than a bare one-shot count read, since the chip-clear and the AI-response-start race each other slightly in the DOM.
- **Implementation-time finding:** at the headless default viewport, only 2 of 4 attached files rendered as visible chips (the rest landed in the width-driven overflow bucket), so `wait_for_attachment_chip_count(4)` failed. Set a wide, fixed viewport (`1700×1100`, same as ELITEA-2196/ELITEA-2197) so all 4 attachments render as visible chips and the count check is deterministic.
