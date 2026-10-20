# Test Case: Chat – Clicking Regenerate Generates a New Response Based on Previous User Input

## Metadata
- **TMS ID**: ELITEA-2185
- **Priority**: l2 (case: high)
- **Environment Explored**: DEV `https://dev.elitea.ai/app` (scratch pytest run with project fixtures, deleted after; Playwright MCP chrome is not installed in this session)
- **User set**: `${TEST_USER}`
- **Status**: **ready-for-automation** (executed live, all 6 steps)
- **Neighbours read**: ELITEA-2184 spec `automation/tests/ui/chat/test_chat_regenerate_last_response_only.py` (on main; asserts Regenerate is present only on the last response, never clicks it), ELITEA-2181 AFS (streaming widget), ELITEA-2183 (stop). Not covered: no merged spec clicks Regenerate.

## Preconditions
- Logged in; fresh conversation via the `conversation_id` fixture; send ONE short prompt and wait for the response (`wait_for_ai_response`). Prompt: `"Write one random 6-digit number and a one-sentence fun fact about it."` (nondeterministic on purpose, so a regenerated answer differs). For a wider in-progress window use a longer prompt (e.g. "Write a 120-word paragraph about rivers"): the default prompt regenerates in ~2s, so the loading state is visible for under 1s.

## Test Steps
1. Last AI item: `scroll_into_view_if_needed()` + `hover()`.
   - Verify: `chat-regenerate-button` count 1 and visible within the AI item (observed visible).
2. Record `user_text_before` (user item `inner_text`) and `ai_text_before`. Click `chat-regenerate-button`.
   - Verify: message count stays 2 (response REPLACED in place, not appended); old response is no longer shown (placeholder takes its place).
3. Right after click, verify the in-progress state on the AI item.
   - Verify (observed t=0..0.6s): `chat-answer-loading-placeholder` (RotatingMessages text, e.g. "Waking the agent...") count 1, Copy/Regenerate absent; then (t~0.6-1.7s) `chat-answer-thought-accordion` appears with the model label ("Anthropic Claude Haiku 4.5") and `chat-inject-button` (Stop) present, `[role=progressbar]` present while thinking. Assert with `expect(...).to_be_visible()` on placeholder OR stop button, not exact phrases; with the short prompt the window is tight, so prefer the longer prompt.
4. Verify the user message is unchanged.
   - Verify: user item `inner_text` == `user_text_before`; count of user items still 1.
5. Wait for completion (`wait_for_ai_response(initial_count=0)` works: Copy visible + non-transient content).
   - Verify: AI item body non-empty and contains the model label. Do NOT hard-assert the new text differs from the old one (observed 271,828 -> 314159, but two LLM runs can collide); optionally soft-record the difference.
6. Hover the AI item again.
   - Verify: `chat-regenerate-button`, `chat-copy-button`, `chat-read-out-button`, `chat-delete-button` each count 1 and visible (observed 1/1/1/1). Stop button gone.

## Observations (live, 2026-10-20)
- Source: `ChatBox.jsx onRegenerateAnswer` marks the message for regeneration, re-sends the stored question from `chat_history[questionIndex]` (so the user input is reused, never edited) via `regenerate({...payload, message_id: uuid})`; the AI item keeps its id (replace in place). `ChatMessageWrapper.jsx:160` gates `onRegenerate` on `isLastMessage && !isLoading && !isRegenerating && ...`, so the button disappears during regeneration (observed reg count 0 at t=0..1.7s, back to 1 at t=2.2s).
- Case text drift (clarification, same as ELITEA-2181/#1100): no literal "spinning loading circle" at the bubble start; the loader is the RotatingMessages text placeholder, later the thought accordion with the model chip. `[role=progressbar]` appears briefly during thinking. Spec the live widget, not a spinner circle.
- Model label is inside the thought accordion, not the header.
- Console/network: not separately inspected; no UI error toast.

## Coverage Map
### Axis 1
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precond: logged in; conversation with user message + LLM response | - | setup | fixtures + one send | asserted |
| 1 Scroll to last response, hover | Regenerate visible | step 1 | testid visible | asserted |
| 2 Click Regenerate | previous response replaced; new generation begins | step 2 | count stays 2, placeholder/stop appear | asserted |
| 3 Model label + spinning circle | loading indicator visible | step 3 | placeholder / stop / accordion + model chip text | asserted (clarification: no literal spinner circle) |
| 4 User input unchanged | unchanged | step 4 | text equality | asserted |
| 5 New response streams and completes | full response | step 5 | wait_for_ai_response + non-empty body | asserted |
| 6 Regenerate + action icons reappear | visible | step 6 | 4 testids visible | asserted |
### Axis 2
- Message count stays 2 after click: proves replace-not-append, grounded in `message_id: uuid` payload.
- Regenerate absent while generating: grounded in `!message.isRegenerating` gate; cheap, observed.

## Concrete Handles Reference
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Message item | 1 | `chat-message-item` (`ChatPage.messages_container`) | - | testid on DEV ✓ |
| AI filter | - | `ChatPage._is_ai_message` / `AI_MESSAGE_LOGO` | - | existing, used live ✓ |
| Regenerate | 1 | `chat-regenerate-button` (`ChatPage.regenerate_action_button`) | - | testid on DEV ✓ |
| Copy / Delete / Read-out | 1 | `chat-copy-button` / `chat-delete-button` / `chat-read-out-button` | - | testid on DEV ✓ |
| Loading placeholder | 1 | `chat-answer-loading-placeholder` (`ChatPage.answer_loading_placeholder`) | - | testid on DEV ✓ |
| Thought accordion | 1 | `chat-answer-thought-accordion` (`ChatPage.answer_thought_accordion`) | - | testid on DEV ✓ |
| Stop button | 1 | `chat-inject-button` (`ChatPage.chat_inject_button`; `STOP_BUTTON.within(...)` for the inner stop control) | - | testid on DEV ✓ (count 1 while streaming) |
Scope with `.within(ai_item)`; no `.nth()` picks except enumerating AI items. Do NOT use legacy `ChatPage.regenerate_response()` / `regenerate_button` (stale testid `message-regenerate-button`).

## Automation Hints
- Dismiss `platform-banner-close` if present. The "New Models are added" toast can cover the Send button: send with `use_enter=True`.
- Transit flag (possible regression): `ChatPage.navigate_to_chat(conversation_id=...)` times out again (same as 2182/2183/2184 notes). Workaround: `page.goto(f"{settings.app_base_url}/app/chat/<id>")` and wait for `chat-message-input`. Note: in a shell where `.env.test` was not resolved, `settings.app_base_url` lacked `/app` and gave a 404 page; in-suite it is `https://dev.elitea.ai/app` per `config.py` (verify; hand-built path may need `/app` removed).
- Scratch runs also showed `wait_for_ai_response` fine for regenerated answer (Copy visible + content).
- No sleeps; expect auto-wait.

## Known Defects / Blocked
None.
