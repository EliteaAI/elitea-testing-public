# Test Case: Embedded chat — Shift+Enter inserts new line, Enter sends message

## Metadata
- **TMS ID**: ELITEA-1875
- **Linked Story**: none
- **Priority**: l2 (source case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: localhost dev auth (`auth_state` / `VITE_DEV_TOKEN`) — no explicit `${TEST_USER}` needed
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `agents-batch1-1277`
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (`auth_state`).
- An existing agent with an embedded chat panel is available — created per-test via
  `agent_api.create_agent(...)` with plain "helpful assistant" instructions (no
  deterministic-reply requirement — this case only needs a message to send and any
  non-empty response, not a specific reply text).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated disposable agent via `agent_api.create_agent(name, description,
  "You are a helpful assistant. Reply concisely.")` — same `_default_llm_settings()`
  shape as ELITEA-1874, avoiding #524/#560 (see that AFS's Test Data section and
  `test-specs/agents/_surface.md`).
- Two-line message: line 1 = `"First line"`, line 2 (typed after Shift+Enter) =
  `"Second line"`.

## Test Steps
1. Create the disposable agent; navigate to its detail page
   (`AgentDetailPage.navigate(agent_id)`).
   - **Verify**: page loads (`information_section` visible), embedded chat
     (`chat_message_input`) visible.
2. Click `chat_message_input`.
   - **Verify**: field is focused (`expect(chat_message_input).to_be_focused()`).
3. Type `"First line"`, then press `Shift+Enter` on `chat_message_input`.
   - **Verify**: (a) the input value now contains a literal newline (`"\n" in
     chat_message_input.input_value()`), and (b) the chat message count has NOT
     increased — no message was submitted.
4. Type `"Second line"` (continuing in the same field, on the new line).
   - **Verify**: `chat_message_input.input_value()` now contains both lines
     (`"First line"` and `"Second line"`, newline-separated).
5. Press `Enter` (no `Shift`) on `chat_message_input`.
   - **Verify**: chat message count increases beyond the pre-send baseline once the
     response arrives (step 6) — the actual submission signal.
6. Wait for the assistant response
   (`wait_for_chat_response(initial_count=..., timeout=AI_RESPONSE_TIMEOUT)`).
   - **Verify**: an assistant response is rendered (`get_last_chat_response_text()`
     non-empty) AND the just-sent user message (`get_last_chat_message_full_text()`
     on the user's own message, or the transcript generally) reflects both typed
     lines — confirms the multi-line composition, not just "a" message, was what
     got submitted.

## Expected Results
- Shift+Enter inserts a line break into the composer without submitting.
- Enter (without Shift) submits the accumulated multi-line message.
- An assistant response is rendered after submission.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open agent detail page with embedded chat | Page + chat panel load | step 1 | `step 1`: `information_section`/`chat_message_input` visible | asserted |
| 2 Click chat input field | Input is focused | step 2 | `step 2`: `expect(...).to_be_focused()` | asserted |
| 3 Press Shift+Enter — new line inserted, no send | New line appears; no message submitted | step 3 | `step 3`: newline in input value + message count unchanged | asserted |
| 4 Type additional text on the new line | Text appears on new line | step 4 | `step 4`: input value contains both lines | asserted |
| 5 Press Enter (no Shift) — multi-line message submitted | Message sent | step 5→6 | `step 5`→`step 6`: message count increases | asserted |
| 6 Assistant response appears | Response rendered | step 6 | `step 6`: `get_last_chat_response_text()` non-empty | asserted |

**Axis 2 — Analyst additions**
- `step 6` additionally checks that the submitted user message itself carries both
  typed lines (not just that "some" message was sent) — a stronger check than the
  case's own step 5/6 wording, added because a regression that dropped the Shift+Enter
  newline silently (submitting only "Second line", say) would otherwise still pass a
  bare "a message was sent, a response arrived" check.

## Cleanup
1. Delete the disposable agent via `agent_api.delete_agent(agent_id)`.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Embedded chat: message input | `LocatorDescriptor(testid="chat-message-input")` — `chat_message_input`, already on `AgentDetailPage` | on-main ✓ (pre-existing, reused as-is) | none — testid only |
| Embedded chat: message list / items | `chat_message_list` (`chat-message-list`) + `CHAT_MESSAGE_ITEM_SELECTOR`, already on `AgentDetailPage` | on-main ✓ (pre-existing) | none |
| Embedded chat: last-response body | `skill_test_last_response` (`skill-test-last-response`), already on `AgentDetailPage` | on-main ✓ (pre-existing) | none |

**PROVENANCE freshness:** no new testid needed — all handles are pre-existing,
already-wired `LocatorDescriptor` fields confirmed live during this implementation
(2026-08-07).

## Network Behavior
- `POST /elitea_core/conversations/prompt_lib/{projectId}` — fires only once, on the
  Enter-submitted send in step 5 (Shift+Enter in step 3 fires no network request —
  purely client-side textarea state, same as the main `ChatPage.send_message_with_shift_enter`
  pattern).

## Known Defects Found During Exploration
- None found this run.

## Blocked Steps
- none

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: `AgentDetailPage` — no new methods needed; drive `chat_message_input`
  directly (`.click()`, `.press_sequentially()`, `.press("Shift+Enter")`,
  `.press("Enter")`, `.input_value()`) — the same direct-field-access pattern
  `ChatPage`'s own `send_message_with_shift_enter()` implements for the main chat
  composer, and that other suite tests already use directly on `chat_message_input`/
  `message_input` (e.g. `test_team_users_mention_and_remove_participants.py`).
- `chat_message_input` is the SAME shared composer testid `ChatPage.message_input`
  uses; `ChatPage.send_message(use_enter=True)` already proves Enter-to-send works on
  that testid, so no new keyboard-handling exploration was required.
- `wait_for_chat_response()` (existing method) already handles the AI-reply
  WebSocket delay.
