# Test Case: Chat – empty input shows no Send button; typing shows it; send clears field

## Metadata
- **TMS ID**: ELITEA-2466 (priority `critical` -> l1)
- **Environment Explored**: DEV `https://dev.elitea.ai/app/chat` (scripted Playwright-Python probes; Playwright MCP chrome binary missing on this host)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer
- **Status**: ready-for-automation

## Summary
All 10 steps executed live. Only the Send/speaking-mode swap, input clearing, own-message render and the
return of the speaking-mode button are product behaviours worth asserting. No defects. Source confirms
(`SendButton.jsx`): `!question` -> "enter speaking mode" button (waveform icon, no testid); else
`chat-send-button` (`disabled={!question}`).

## Case-text drift (clarifications, not defects)
- Step 2/5/6/10 "waveform/audio icon" = DEV button `aria-label="enter speaking mode"`; "Send button NOT visible" = `chat-send-button` is absent from DOM (count 0), not merely hidden.
- Step 3 bottom bar order (observed left->right): attach files, plus-menu-button, chat-clear-button, model name (`model-selector-name`, "Anthropic Claude Haiku 4.5"), `model-settings-button` (gear), "start voice input" (microphone), speaking-mode / send, context-budget-ring. The "+" is `plus-menu-button`.
- Step 4 "teal/cyan focus border": computed border/outline on the focused textarea's InputBase reads white `rgb(255,255,255)`; colour is a visual judgment, not reliably assertable -> assert `to_be_focused()` only (not asserted: colour).
- Step 1 "any existing conversation": use the `conversation_id` fixture (fresh empty conversation) or new-chat `/chat`; the swap behaviour is identical.
- Step 10 "response begins generating": on DEV no Stop control is exposed unless mid-turn injection is on (see ELITEA-2182 spec); after send the composer shows NEITHER send nor speaking-mode for ~1.5-3s (input cleared), then speaking-mode returns when generation ends. Assert: send absent + input empty immediately after send; a new AI message (`img[alt=Elitea]` item) appears; speaking-mode button returns after the response.

## Preconditions
- Logged in (`auth_state`). A "platform announcement" dialog (`platform-banner-close`, "Got it") may overlay and block clicks; a corner banner (`platform-banner-corner`) can intercept the Send click -> send via click(force=True) like `ChatPage.send_message` or Enter. Existing helper handles the dialog (`base_page.py:157`).

## Steps (observed)
| # | Action | Observed |
|---|--------|----------|
| 1 | `navigate_to_chat(conversation_id=...)`; input visible | `/chat` loads; `#standard-multiline-static` visible |
| 2 | Input empty | value `''`; `chat-send-button` count 0; `enter speaking mode` count 1 |
| 3 | Bottom bar | see drift note; all of plus, model name, gear, mic, speaking-mode visible |
| 4 | Click input | focused (colour not assertable) |
| 5 | Type "h" | `chat-send-button` count 1 (enabled), speaking-mode count 0 |
| 6 | Backspace | send count 0, speaking-mode count 1, value `''` |
| 7 | Type "Hello", click send | URL for a new chat becomes `/chat/<id>?name=Hello`; for an existing id stays |
| 8 | Message in history | new `chat-message-item` `<li>` with user avatar (initials `.MuiAvatar-root`/img) + sender name + text "Hello" (text contains sender name e.g. `autotest_user_admin`) |
| 9 | After send | input value `''`; send count 0 |
| 10 | After response | AI `<li>` (`img[alt=Elitea]`, `chat-answer-content`) appears ~3s; speaking-mode button back; no console errors observed |

## Handles Reference
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| 1 | `testid=chat-message-input` (`ChatPage.message_input`) | - | testid on DEV ✓ |
| 1 | `testid=chat-send-button` (`ChatPage.send_button`) | - | testid on DEV ✓ (absent from DOM when input empty) |
| 2 | `role=button name="enter speaking mode"` | `chat-speaking-mode-button` | ladder - no testid on DEV; unique on page (count 1). Existing raw use: `chat_page.py:~2277` (css fallback, unmanaged) |
| 2 | `role=button name="start voice input"` (microphone) | `chat-voice-input-button` | ladder - no testid on DEV; unique (count 1) |
| 1 | `testid=plus-menu-button`, `model-selector-name`, `model-settings-button` | - | testid on DEV ✓ (`plus_menu_button` L396, `model_selector_name` L1473 exist; `model-settings-button` NOT yet in ChatPage - exists in agent/skill pages) |
| 1 | `testid=chat-message-item` (`messages_container`) | - | ✓; user vs AI via `_is_ai_message` (`img[alt=Elitea]`) |
| 1 | `chat-answer-content` inside AI item | - | ✓ |
Existing helper: `ChatPage.wait_for_generation_complete`-style speaking-mode wait (`chat_page.py:~2268`).
Assert absence via `expect(send_button).to_have_count(0)`; use auto-retrying expects, no sleeps.

## Coverage Map
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| S1-2 | input empty, no send | steps 1-2 | count(send)=0, value '' , speaking-mode visible | covered |
| S3 | bottom bar controls | step 3 | visibility of plus, model name, gear, mic, speaking-mode | covered (names per drift) |
| S4 | focus | step 4 | `to_be_focused` | covered; teal colour = out-of-scope (visual) |
| S5 | typing swaps icon | step 5 | send visible+enabled, speaking-mode count 0 | covered |
| S6 | delete restores | step 6 | send count 0, speaking-mode visible | covered |
| S7-8 | send, message in history w/ name+avatar | step 7-8 | user item text, avatar element present | covered |
| S9 | cleared, send gone | step 9 | value '', send count 0 | covered |
| S10 | icon returns, response generating | step 10 | new AI item appears; speaking-mode returns | covered (no Stop handle; "begins generating" = AI item appears) |
Axis 2: none beyond case.

## Neighbour check
No existing spec asserts the empty-vs-typed swap or the input-clear-on-send: `test_chat_stop_button_cancels_generation.py` (ELITEA-2182) only checks send bar returns after Stop; streaming/export tests only use send as an action. -> not already-covered.

## Suggested spec
Single test, `conversation_id` fixture, `@pytest.mark.tms("ELITEA-2466")` + allure.issue pair, p1/chat/regression. Short prompt "Hello" costs one LLM call.
