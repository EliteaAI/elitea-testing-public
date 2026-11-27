# Test Case: Two chats run at once and Stop in one leaves the other running

## Metadata
- **TMS ID**: ELITEA-4957
- **Linked Story**: EliteaAI/elitea_issues#7385 (known issue elitea_issues#7763 OPEN, not exercised here)
- **Priority**: l1 (TMS `critical`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), 2026-11-27, headless scripted python-playwright probes (run via the existing `long_runner_agent` fixture)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

> Neighbours read: ELITEA-4953 (`test_chat_leave_and_return_running_agent.py`) and ELITEA-4956 specs share the `long_runner_agent` fixture (`automation/fixtures/chat_run_fixtures.py`), `ChatPage.get_conversation_running_icon`, `get_composer_stop_button`, `start_recording_delete_requests`. Neither asserts two concurrent runs or Stop isolation, so this is NOT already-covered. Build as a NEW spec in `tests/ui/chat/`, reusing the fixture.

## Fixtures
Reuse `long_runner_agent` (toolkits + agent, ~45 s run, `RUN-DONE <word>`). Conversations A and C: `conversation_api.create_conversation(f"autotest_run_A_{sfx}")` / `..._C_...` (fresh per run, deleted in teardown, like `two_conversations` in the 4953 spec).

## Test Data
Message in A `The word is SMK5A.`; in C `The word is SMK5C.`; expected A answer `RUN-DONE SMK5A`.

## Test Steps (live-observed)
Setup (UI): **adding the agent participant needs a workaround, see Gotchas.** Pre-attach the agent to A and C by API, then in each chat make it ACTIVE before sending.
1. Open A, activate agent, send A's message; click row C (in-app click), activate agent, send C's message.
   - Verify: `get_conversation_running_icon(A)` count 1 AND `get_conversation_running_icon(C)` count 1 (observed both 1 within ~15 s of sending). In C, first `chat-answer-tool-chip` within ~3 s, Stop button + "Agent is running…" visible.
2. In C click Stop (`ChatPage.get_composer_stop_button().click()`).
   - Verify (observed): exactly ONE `DELETE https://dev.elitea.ai/api/v2/elitea_core/task/prompt_lib/575/<uuid>` recorded (`start_recording_delete_requests()`, started before sends; filter to `/task/`); the uuid equals C's `message_group_uuid` (socket frame `chat_run_status` `status:"running"` for C's conversation_id, later `"stopped"`), NOT A's. After ~3 s: Stop button count 0 in C, C row running icon 0, A row running icon still 1. API `has_running_task`: A True, C False.
3. Click row A: `get_agent_running_indicator()` visible and Stop button present (count 1) - A still running.
4. Wait for A's row icon to detach (<= 90 s ceiling; ~45 s run): `messages_container.last` contains `RUN-DONE SMK5A`. Total DELETE /task requests still 1 (A never deleted).
   - API oracle: `conversation_api.has_running_task(A)` False at end; `get_message_groups(A)[-1].is_streaming` False; `get_message_traces(A)` 5 `tool_call` rows (filter by kind; +1 `thinking_step`).

## Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Conversation row | 1 | `chat-conversation-item-{id}` (`get_conversation_item`) | - | testid on DEV ✓ |
| Row running spinner | 1 | `chat-list-item-running-icon` scoped in row (`get_conversation_running_icon`) | - | testid on DEV ✓ |
| Stop button | 5 | `ChatPage.COMPOSER_STOP_BUTTON` via `get_composer_stop_button()` | `chat-stop-button` | ladder - no testid on DEV; unique live (count 1 while streaming) |
| Running indicator | text | `get_agent_running_indicator()` | `chat-agent-running-indicator` | ladder, existing |
| Tool chip | 1 | `chat-answer-tool-chip` | - | testid on DEV ✓ |
| Active participant | 1 | `chat-switch-participant-button` text = agent name | - | testid on DEV ✓ |
| Hash search result | existing | `ChatPage.HASH_SEARCH_RESULT_BY_NAME` | - | existing declaration |

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 | both rows spin | step 1 | two icon counts | covered |
| Step 2 | exactly one DELETE /task, for C's run; Stop gone | step 2 | request list len 1 + uuid == C's run uuid from socket frame | covered |
| Step 2 | "C's row gets no dot" | steps 2 and 3 | `get_conversation_unread_badge(conv_c)` count 0 after Stop (on C) and after opening A (adjusted per reviewer; handle as in ELITEA-4955) | covered |
| Step 3 | A still running | step 3 | indicator + Stop visible, row icon 1 | covered |
| Step 4 | A answer RUN-DONE SMK5A | step 4 | last message text | covered |
| Axis 2 | has_running_task A True/C False after Stop; A final is_streaming False; no 2nd DELETE | steps 2/4 | API oracle | grounded in case Notes oracle |

## Gotchas for the implementer (important)
- **`ChatPage.add_agent_participant_by_id` FAILED on DEV today** (picker search returns "No agents found" for the autotest agent when a 2nd conversation is configured in the same session; agent search `statuses=published` / `agents_type=classic` requests). The existing 4953 spec still passed in the same session (first conversation only). Do NOT rely on it for the second chat. Working path observed: (a) pre-attach via API `POST {api}/elitea_core/participants/prompt_lib/{pid}/{conv}` body `[{"entity_name":"application","entity_meta":{"id":<agent_id>,"project_id":<pid>},"entity_settings":{"variables":[],"icon_meta":{}}}]` -> 200; or (b) type `#<agent name>` in empty composer + `HASH_SEARCH_RESULT_BY_NAME` (`start_new_chat_with_agent_by_hash` pattern). With (a) the participant is NOT active after open: `chat-switch-participant-button` count 0 until activated - expand participants panel if needed (`chat-participants-panel-toggle-button`) and click the participant row (`chat-participant-row-*`), then `expect(switch_participant_button).to_contain_text(agent_name)` BEFORE sending (else message goes to the default assistant: observed "Got it, I've noted..." with no tools, no run).
- Navigate between chats by row click only (no goto).
- Run uuids: take from the `chat_run_status` websocket frames (`page.on("websocket")` -> `framereceived`; fields `conversation_id`, `message_group_uuid`, `status`). The DELETE url's last segment == C's `message_group_uuid`.
- Probe run: ~80 s total; use 90 s ceiling for A. Stop click when C has its first chip.
- Teardown: stop any still-running run of A/C (has_running_task -> stop_running_task), delete A, C, agent, toolkits; then log (warning, never change verdict) any still listed (limit=100 listing).

## Known Defects
None new. (#7763 chip names unrelated; do not assert chip names.)
