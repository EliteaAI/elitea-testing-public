# Test Case: Chat – After Stopping Generation New Message Can Be Sent Normally

## Metadata
- **TMS ID**: ELITEA-2183
- **Linked Story**: EliteaAI/elitea_issues#5196
- **Priority**: l2 (TMS `high`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), headless Chromium via scratch pytest probe (Playwright MCP browser binary unavailable on this host - substitution recorded), 2 live runs
- **Analyst**: qa-engineer (analyst slot)
- **Status**: extend-existing
- **Surface key**: `chat-composer-stop-generation`

## Covering spec (merged to main, 8421e098)
`automation/tests/ui/chat/test_chat_stop_button_cancels_generation.py` - `TestChatStopButtonCancelsGeneration.test_stop_cancels_generation_and_restores_input` (Steps 1-7 there). It proves case steps 1-3 (send "generate a poem", Stop visible, click Stop, timeline returns to `initial_count` i.e. no user/assistant bubble, send bar back, input editable, value == original text). AFS: `l2_stop-button-cancels-generation-restores-input_ELITEA-2182.md`.

Overlap argument: ELITEA-2183 steps 1-3 are the same observable with the same expected result as 2182 (same prompt `generate a poem`, same stop-in-pre-answer-phase, same restore + empty timeline). Not `already-covered`: 2183's distinguishing observable (post-stop send works) is NOT asserted anywhere.

## Gap assertions (what the implementer adds)
Add a NEW test method (own `@pytest.mark.tms("ELITEA-2183")`; do not graft onto the 2182 test so each case keeps its own pass/fail) in the same file/class, reusing the same fixtures (`conversation_id`, `midturn_injection_enabled` - declared improvisation inherited from 2182) and the 2182 Stop flow for steps 1-3 (re-assert the key restore facts: timeline back to `initial_count`, input value == `generate a poem`). Then:
4. Clear input (`chat.message_input.fill("")`), type `hello` -> `chat-send-button` visible (`expect(chat.send_button).to_be_visible()`).
5. `n = chat.get_message_count()` (0 here), `chat.send_message("hello")`; expect `messages_container.filter(has_text="hello")` visible; new LLM response begins/completes.
6. No error: `toast-alert[data-severity="error"]` count 0 (`ChatPage.TOAST_ALERT_SEVERITY.format("error")`), and the timeline holds exactly user `hello` + one assistant reply; NO `generate a poem` bubble (`messages_container.filter(has_text="generate a poem")` count 0) - this is the "no trace of stopped exchange" proof across the whole history.

## Live observations (DEV 2026-10-20)
- Stop -> restored input `generate a poem`, timeline count 0 (matches 2182).
- fill("") then fill("hello") -> send button visible; Send -> timeline `li0` = user "hello", `li1` = assistant ("Thought for 1 sec", Claude Haiku 4.5, "Hello! 👋 I'm EliteA ..."). Response complete ~12s incl. Copy button. Final state: 2 `li`, poem count 0, error toasts 0, `[role=alert]` 0, input empty afterwards.
- **`ChatPage.wait_for_ai_response(initial_count=N)` takes the count BEFORE the user's send message** (N = count before send; AI lands at N+1). Passing `n+1` hangs 60s (first probe timed out that way) - pass `n`.
- Transit flag: `ChatPage.navigate_to_chat(conversation_id=...)` timed out 3x (15s `chat-message-input` wait) in a fresh scratch run; plain `page.goto('https://dev.elitea.ai/app/chat/<id>')` then waiting for the input worked. Same flake already noted for 2182 (possible #1847 networkidle class). Also: `settings.app_base_url` resolved to a host without `/app` in my scratch f-string (my usage, `/chat/<id>` 404'd) - not a product issue.

## Coverage Map

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Type first msg + Send; Stop visible | Stop visible in thinking phase | 2182 test Steps 1-2 (stop visible at first render; not gated on `Thinking` label - see 2182 Clarification) | existing spec | covered (existing) |
| 2 Click Stop | Generation stops; input restored with exact text | 2182 Steps 3, 6, 7 | existing spec | covered (existing) |
| 3 No user/assistant bubble remains | Chat as if never sent | 2182 Step 4 (count == initial_count) | existing spec | covered (existing) |
| 4 Clear input, type hello | Send button appears | gap step 4 | new method | asserted (new) |
| 5 Click Send | New message sent; LLM response begins | gap step 5 | new method | asserted (new) |
| 6 No error messages | Chat continues normally | gap step 6 | new method | asserted (new) |
| Expected Final State: no trace of stopped exchange | no stopped-exchange bubble in history | gap step 6 (poem filter count 0, exactly user+assistant) | new method | asserted (new) |

Axis 2 - Analyst additions: assert the AI reply actually completes (`wait_for_ai_response(initial_count=n)`) - added because "LLM responds normally" is the case's Objective and a mere sent bubble would pass on a dead backend.

## Concrete Handles (verified on DEV 2026-10-20)

| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Message input | 1 | `ChatPage.message_input` (`chat-message-input`) | - | testid on DEV ✓ |
| Send button | 1 | `ChatPage.send_button` (`chat-send-button`; `send_message()` handles force-click) | - | testid on DEV ✓ |
| Stop button | 5 | `ChatPage.STOP_BUTTON.within(chat.chat_inject_button)` (needs `midturn_injection_enabled`) | `chat-stop-button` | existing declaration; ladder - no testid on DEV |
| Timeline items | 4 | `ChatPage.messages_container` / `get_message_count()` | - | existing |
| Error toast | 1 | `ChatPage.TOAST_ALERT_SEVERITY.format("error")` | - | testid on DEV ✓ (`toast-alert` + `data-severity`) |

## Known Defects Found During Exploration
None. Console not inspected via MCP (browser unavailable); no error toast/alert observed.
