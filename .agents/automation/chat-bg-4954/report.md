# Batch chat-bg-4954 report

**Totals:** 1 case — blocked 1. Base `origin/main`, trunk `tests/batch-chat-bg-4954`.

| Case | Outcome | Note |
|---|---|---|
| ELITEA-4954 | blocked | gate red: Locator.wait_for timeout 15000ms waiting for `chat-message-input` in ChatPage.navigate_to_chat. Branch `tests/ELITEA-4954-leave-chat-four-ways-dot`, PR 3055. |

AFS: `test-specs/chat-interface/l1_leave-running-chat-four-ways-then-new-response-dot_ELITEA-4954.md`

## Findings

### defect
- Possible product defect in the #7385 New response dot. The "finished" frame arrives while the user is on Artifacts, but A's row shows no dot when the user left A, pressed Back and went straight to Artifacts before A finished reloading. Waiting for "Agent is running..." after Back, or clicking New chat before Artifacts, shows the dot. (Clipped; full text in the unit's receipt under `.agents/automation/_returns/`.)

### clarification
- Case step 5 says to open the chat list via New chat. On DEV the sidebar is collapsed on arrival at /chat, then auto-expands within seconds. `expand_sidebar_list` waits for rows and clicks the toggle only if absent; the AFS says to click unconditionally. (Clipped.)
- Case text says tooltip "New response"; the test asserts the aria-label (headless renders no tooltip). Declared in the AFS, so acceptable. (`test-specs/chat-interface/l1_leave-running-chat-four-ways-then-new-response-dot_ELITEA-4954.md`)

### note
- Merging origin/main into the trunk conflicted in `_surface.md` (append vs append); both sides kept.
- COMPOSER_STOP_BUTTON hard-assert fits teardown/failed-mid-run; in the happy path the run ends by itself.
- `long_runner_agent` fixture already creates the case's toolkits and agent from `test-data/chat-runs-continue`.
- Tooltip asserted via aria-label and data-reason=new_response; worker env had no .env.test (shell env APP_PREFIX=/app HEADLESS=true).
- Ladder grep over the diff: 0 hits. New descriptors are class-level (testid, role+name, two xpath text descriptors). (Clipped.) `automation/pages/chat_page.py:7458`
- Triangulation: every case step 1-6 and Pass criteria has an assertion at its step. (Clipped.)
- Lead adjustments applied: fresh conversation A per run, `long_runner_agent` reused, URL matched by regex, only tool_call rows counted, teardown stops a running task, no goto/reload after the run starts.
- Nit: `ConversationAPI.wait_until_run_ended` uses `time.sleep(1s)` in an API poll loop with a deadline; fine. `automation/api/client.py:510`
- Nit: `expand_sidebar_list` 4 s broad `except Exception` grace wait; narrow to PlaywrightTimeoutError if it flakes. `automation/pages/chat_page.py:7508`
- Nit: Step 4 Axis-2 running-indicator assertion needs gate confirmation; Step 2 does not assert the new chat is empty; teardown checks only conversation A. (Clipped.) `automation/tests/ui/chat/test_chat_leave_running_chat_new_response_dot.py:93`

## Gate

**Verdict: red** (runs: 0, seconds: 181.3)

- `tests/ui/chat/test_chat_leave_running_chat_new_response_dot.py::TestLeaveRunningChatNewResponseDot::test_leave_running_chat_four_ways_then_new_response_dot` (ELITEA-4954): playwright TimeoutError, Locator.wait_for 15000ms waiting for `chat-message-input`, raised in ChatPage.navigate_to_chat -> wait_for_page_load (pages/chat_page.py:1675/1721). The 2 reruns failed the same way (1 failed, 2 rerun in 178.65s). Log also showed "Missing elitea-staging_auth_session cookie". (Clipped; full text in the receipt.)

Quality flags: none. Quota halted: no. Expected red: none. Parked: none.
