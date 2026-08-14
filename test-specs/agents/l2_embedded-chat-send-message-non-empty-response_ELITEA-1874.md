# Test Case: Embedded chat — send message and verify response is non-empty

## Metadata
- **TMS ID**: ELITEA-1874
- **Linked Story**: none
- **Priority**: l2 (source case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: localhost dev auth (`auth_state` / `VITE_DEV_TOKEN`) — no explicit `${TEST_USER}` needed
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `agents-batch1-1277`
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (`auth_state`).
- An agent exists whose instructions are exactly: "You are a helpful assistant. Reply
  only with: PONG" — created per-test via `agent_api.create_agent(name, description,
  instructions)`, not a shared fixture agent (avoids xdist races on chat state, same
  pattern as `test_agent_llm_selector_anthropic_models.py`/`test_agent_run_history_select_past_run.py`).

## Test Data
### generate-per-test (in test setup, cleaned up in its own teardown)
- Dedicated disposable agent via `agent_api.create_agent(name, description,
  instructions="You are a helpful assistant. Reply only with: PONG")`. Uses the
  convenience method's `_default_llm_settings()` (`temperature: null`,
  `reasoning_effort: "medium"`) — avoids both the open #524 creation-400
  (`temperature` + non-`"none"` `reasoning_effort`) and the #560 embedded-chat-500
  (`reasoning_effort: "none"` breaks `POST .../conversations/prompt_lib/{project}`),
  same as every other disposable chat-agent fixture in this feature area
  (`test-specs/agents/_surface.md` § Agent creation payload gotcha).
- User message: `"PING"` (literal, case Test Data table).
- Expected response substring: `"PONG"` (literal, case-specified — the agent's
  instructions make this a live, deterministic-ish LLM round trip, same pattern
  already proven reliable in `test_agent_llm_selector_anthropic_models.py`'s
  "Reply only with: CONFIRMED" / assert `"CONFIRMED" in response`).

## Test Steps
1. Create the disposable agent (instructions above) via `agent_api.create_agent(...)`;
   navigate to its detail page (`AgentDetailPage.navigate(agent_id)`).
   - **Verify**: page loads (`information_section` visible).
2. Locate the embedded chat panel (`chat_message_input` / `chat_message_list`).
   - **Verify**: both are visible.
3. Type `"PING"` into `chat_message_input` via `press_sequentially()` (MUI onChange
   requirement, `.claude/rules/mui-patterns.md`).
   - **Verify**: `chat_message_input.input_value() == "PING"`.
4. Press `Enter` (no `Shift`) directly on `chat_message_input`
   (`chat_message_input.press("Enter")`) — NOT `chat_send_button.click()`, since this
   case's own step specifically exercises the keyboard-submission path (distinct from
   every other embedded-chat test in this suite, which all click the Send button via
   `send_chat_message()`).
   - **Verify**: message count increases beyond the pre-send baseline once the
     response arrives (step 5) — the actual submission signal; no separate
     immediate-post-press assertion (message rendering is async).
5. Wait for the assistant response to stabilise
   (`wait_for_chat_response(initial_count=..., timeout=AI_RESPONSE_TIMEOUT)`).
   - **Verify**: chat message count `>` the pre-send baseline.
6. Read the response body (`get_last_chat_response_text()` —
   `skill-test-last-response` testid, the correct handle for the LAST message per
   `ApplicationAnswer.jsx`'s `isLastMessage` ternary, documented in that method's
   own docstring).
   - **Verify**: response text is non-empty AND contains `"PONG"`.
7. Re-read `chat_message_input.input_value()`.
   - **Verify**: input is empty (`""`) — case step 7.

## Expected Results
- The embedded chat panel accepts "PING" typed into the input.
- Pressing Enter (without Shift) submits the message via the keyboard, without
  clicking the Send button.
- The agent's response is non-empty and contains "PONG".
- The chat input field is cleared once the message is sent.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to agent detail page (PONG instructions) | Agent detail page loads | step 1 | `step 1`: `information_section` visible | asserted |
| 2 Locate embedded chat panel | Chat panel visible | step 2 | `step 2`: `chat_message_input`/`chat_message_list` visible | asserted |
| 3 Type "PING" in chat input | Input displays "PING" | step 3 | `step 3`: `input_value() == "PING"` | asserted |
| 4 Press Enter (no Shift) | Message is submitted | step 4 | `step 4`→`step 5`: message count increases | asserted |
| 5 Wait for response to appear and stabilise | Response fully rendered | step 5 | `step 5`: `wait_for_chat_response()` + count check | asserted |
| 6 Response is non-empty and contains "PONG" | Response text non-empty + contains "PONG" | step 6 | `step 6`: `get_last_chat_response_text()` assertions | asserted |
| 7 Input field cleared after sending | Input is empty | step 7 | `step 7`: `input_value() == ""` | asserted |

**Axis 2 — Analyst additions**
- None beyond the case's own steps — this case is fully self-contained and the
  existing embedded-chat infrastructure (`send_chat_message`/`wait_for_chat_response`/
  `get_last_chat_response_text`) already covers every handle needed; no new testid or
  scope addition required.

## Cleanup
1. Delete the disposable agent via `agent_api.delete_agent(agent_id)`.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Embedded chat: message input | `LocatorDescriptor(testid="chat-message-input")` — `chat_message_input`, already on `AgentDetailPage` | on-main ✓ (pre-existing, reused as-is) | none — testid only |
| Embedded chat: message list / items | `chat_message_list` (`chat-message-list`) + `CHAT_MESSAGE_ITEM_SELECTOR`, already on `AgentDetailPage` | on-main ✓ (pre-existing) | none |
| Embedded chat: last-response body | `skill_test_last_response` (`skill-test-last-response`), already on `AgentDetailPage`, read via `get_last_chat_response_text()` | on-main ✓ (pre-existing) | none |

**PROVENANCE freshness:** no new testid needed — all three handles are pre-existing,
already-wired `LocatorDescriptor` fields confirmed live during this implementation
(2026-08-07). No fetch-and-grep needed since nothing new was added.

## Network Behavior
- `POST /elitea_core/conversations/prompt_lib/{projectId}` — fires on first message
  send (creates the conversation).
- WebSocket streaming of the assistant reply (~2-15s depending on model latency, per
  `.agents/testing.md`).

## Known Defects Found During Exploration
- None found this run.

## Blocked Steps
- none

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Page object: `AgentDetailPage` — no new methods needed; drive `chat_message_input`
  directly for the type→Enter sequence (steps 3-4) so the per-step assertions
  ("input shows PING" then "Enter submits") stay independently verifiable, rather
  than folding them into one compound helper call. Same direct-field-access pattern
  already used across the suite (e.g. `test_team_users_mention_and_remove_participants.py`'s
  `chat.message_input.press(...)`/`press_sequentially(...)`).
- Disposable-agent fixture: `agent_api.create_agent(name, description, instructions)`
  (the convenience method, not `create_agent_full`) — its `_default_llm_settings()`
  already avoids both #524 and #560.
- `wait_for_chat_response()` (existing method) already handles the AI-reply
  WebSocket delay.
