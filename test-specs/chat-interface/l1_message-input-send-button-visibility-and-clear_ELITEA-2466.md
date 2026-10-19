# Test Case: Chat – Message input empty shows no send button; typing shows send button; send clears field

## Metadata
- **TMS ID**: ELITEA-2466
- **Priority**: l1 (case priority: critical)
- **Environment Explored**: DEV `https://dev.elitea.ai/app/chat` (scripted Playwright probes with the DEV storage state; Playwright MCP's Chrome binary was missing in this session, so the case was executed via scratch `sync_playwright` scripts, headless 1440x900)
- **User set**: `${TEST_USER}`
- **Status**: **ready-for-automation** — executed live on DEV, all 10 steps observed. Two case-text drifts (clarifications, not defects): the "gear icon" is the model-settings button, and the "microphone / waveform" icons are two separate buttons (`start voice input` and `enter speaking mode`); the LLM name is the model-selector chip (no model icon asserted).

## Preconditions
- Logged in (`auth_state`). Conversation: use the `conversation_id` fixture's fresh conversation and navigate to it (the DEV account's sidebar had 0 existing conversations, so "any existing conversation" must be created by fixture).

## Test Data
- generate-per-test: conversation via `conversation_id` fixture. Message text: `"h"` (typing probe) and `"Hello"` (send). Prefer a short deterministic prompt such as `"Reply with just the word OK"` to keep the LLM response fast.

## Test Steps
1. Open the conversation (`/chat/{id}`). Dismiss the DEV platform banner if present (`platform-banner-close`, text "Got it") — it is a MuiDialog that intercepts pointer events on the composer until closed.
2. Verify `chat-message-input` value is `""` and `chat-send-button` count == 0 (absent from DOM, not just hidden).
3. Verify the composer shows: attach (`aria-label="attach files"`), `plus-menu-button`, `model-selector-name` (LLM name), `model-settings-button` (the "gear"), `start voice input` (mic), `enter speaking mode` (the "waveform/audio" icon, rightmost).
4. Click the input; verify it is focused (`:focus-within` / `to_be_focused`). Visual: the composer wrapper (3 ancestors above `chat-input`... the 6th ancestor of the textarea) gains `box-shadow: rgba(21,255,247,0.2) 0 -5px 20px` (teal glow); there is no distinct border-colour change on the textarea itself. Assert focus, not the colour (colour is CSS-computed, brittle; the case's "teal/cyan border" is satisfied only by the glow).
5. Type `h`: `chat-send-button` becomes visible (aria-label "send your question"); `enter speaking mode` button is gone (replaced by send in the same slot). `start voice input` stays.
6. Press Backspace: input empty; `chat-send-button` count == 0; `enter speaking mode` visible again.
7. Fill `Hello`, click `chat-send-button`.
8. Verify the user message appears as a `chat-message-item` containing the sender name ("autotest_user_admin") and avatar initials ("AA") and text "Hello".
9. Verify `chat-message-input` value `""` immediately and `chat-send-button` count == 0.
10. Verify a response begins generating: a second `chat-message-item` (participant "Elitea") with the rotating placeholder ("Waking the agent…"). **Caveat (observed live):** while the run is in flight the `enter speaking mode` button is NOT shown (absent during streaming; `chat-inject-button` replaces it). It reappears only after the response completes (wait on it with a long timeout, use `wait_for_ai_response`). So the case's step 10 "waveform reappears" holds only post-completion — assert placeholder/response-begins first, then waveform after completion.

## Expected Results
Send button present only while the input has text; send clears the field and removes the Send button; the user message shows name/avatar; a response starts; the speaking-mode (waveform) button returns after completion.

## Coverage Map
### Axis 1
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Pre: logged in | — | Setup | auth_state | asserted |
| 1 open conversation | loads | step 1 | URL + input visible | asserted |
| 2 empty input, no Send | absent | step 2 | send count 0 | asserted |
| 3 bottom bar icons | + / LLM / gear / mic / waveform | step 3 | aria/testid visibility | asserted (clarification: gear = model settings; mic and waveform separate buttons) |
| 4 focus teal border | focused | step 4 | focus assertion | asserted (colour not asserted — glow only) |
| 5 type "h" -> Send replaces waveform | send visible, waveform gone | step 5 | | asserted |
| 6 delete -> Send gone, waveform back | | step 6 | | asserted |
| 7 type Hello, click Send | | step 7 | | asserted |
| 8 message in history with name+avatar | | step 8 | | asserted |
| 9 input cleared, Send gone | | step 9 | | asserted |
| 10 waveform reappears + LLM response begins | | step 10 | | asserted (waveform only after completion — clarification) |
### Axis 2
- Step 2/6 assert send count==0 (absence), consistent with ELITEA-2181 baseline; step 10 splits "response begins" from "waveform returns" because live behaviour differs from the case order.

## Cleanup
`conversation_id` fixture teardown.

## Concrete Handles (verified DEV 2026-10-19)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `chat-message-input` (ChatPage.message_input) | — | testid on DEV ✓ |
| testid | `chat-send-button` (ChatPage.send_button; absent when empty) | — | testid on DEV ✓ |
| testid | `chat-input` (composer container), `chat-message-list`, `chat-message-item`, `chat-inject-button`, `plus-menu-button`, `model-selector-name`, `model-settings-button` | — | testid on DEV ✓ |
| role+name | `button` name "enter speaking mode" (waveform) — already used inline in `chat_page.py` ~L2109 | `chat-speaking-mode-button` | ladder — no testid on DEV; unique on page |
| role+name | `button` name "start voice input" (mic) | `chat-voice-input-button` | ladder — no testid on DEV; unique |
| role+name | `button` name "attach files" | `chat-attach-files-button` | ladder — no testid on DEV; unique |
| testid | `platform-banner-close` (button "Got it") | — | testid on DEV ✓ (check whether an existing fixture/page method already dismisses it) |
Sender name/avatar: assert via text inside `chat-message-item` (name "autotest_user_admin"/initials "AA"); no dedicated testids observed — use `ScopedLocator` under `chat-message-item` with role/text, or assert on item text (no positional picks; select the user item by hasText "Hello").

## Automation Hints
- Console errors: none. Reuse `ChatPage.send_message()`; add declared fields for the three icon buttons.
- Neighbour check: ELITEA-2181 AFS (chat-interface) observes send-button absence only incidentally; ELITEA-2418 (support assistant) covers empty-send on a different widget. No spec proves the type/clear toggle or waveform swap on the main chat -> not already-covered.
- Evidence (local): /tmp/ELITEA-2466-step-*.png
