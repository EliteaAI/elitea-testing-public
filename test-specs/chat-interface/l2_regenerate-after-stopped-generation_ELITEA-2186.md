# Test Case: Chat – Regenerate After Stopped Generation (mid-stream) Produces New Output

## Metadata
- **TMS ID**: ELITEA-2186
- **Linked Story**: EliteaAI/elitea_issues#5196
- **Priority**: l2 (TMS `high`)
- **Environment Explored**: DEV (`https://dev.elitea.ai/app`, as deployed), headless Chromium via scratch pytest (Playwright MCP chrome missing), 5 live trials
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: defect-found
- **Surface key**: `chat-stop-then-regenerate`
- **Defect**: EliteaAI/elitea-testing-public#2524 (already filed earlier; this run re-confirmed it, not re-filed)

## Preconditions
- Fresh conversation (`conversation_id` fixture) with `midturn_injection_enabled` (needed so the Stop control resolves under `chat_inject_button`; see ELITEA-2182 AFS).

## Test Data
- Message: `generate a long detailed poem about the seasons`

## Test Steps (as the case intends)
1. Send the message with Enter; wait until the agent bubble holds streamed poem text; click Stop (`ChatPage.click_stop()`).
   - **Expected (case)**: partial text stays visible, message is not deleted.
   - **Observed on DEV (5/5 runs, Stop at ~450, ~1250, ~2650 and ~4600 chars)**: both user bubble and partial agent bubble are REMOVED (`chat-message-item` count 2 -> 0). `chat-send-button` returns, `chat-message-input` holds the original prompt, `chat-inject-button` count 0. Still 0 after 4s and after a reload (removal is persisted).
2. Hover the stopped response for Regenerate. Unreachable: no message exists.
3-6. Unreachable (regenerate, Stop during regeneration, completion, user message unchanged).

## Expected Results (when the product matches the case)
Partial text preserved after Stop; Regenerate (`chat-regenerate-button`) on it; clicking it replaces the item in place, `chat-inject-button` (Stop) shows while generating, then Copy/Regenerate/Delete/Read-out return, user message unchanged.

## Coverage Map

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Send + Stop after text visible | partial text preserved, not deleted | step 1 | step 1 | blocked by defect #2524 (actual: whole turn deleted) |
| 2 Regenerate action on stopped response | icon visible | step 2 | step 2 | blocked (no message) |
| 3 Click Regenerate | new generation begins | step 3 | step 3 | blocked |
| 4 Stop visible during regeneration | stop visible | step 4 | step 4 | blocked (handles known from ELITEA-2185: `chat-inject-button`) |
| 5 Wait for completion | full response | step 5 | step 5 | blocked |
| 6 Actions return; user message unchanged | actions visible; same user text | step 6 | step 6 | blocked |

Axis 2: none.

## Concrete Handles (verified on DEV 2026-10-22)

| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Message items | existing | `ChatPage.messages_container` (`chat-message-item`) | - | testid on DEV ✓ |
| Stop | 5 | `ChatPage.STOP_BUTTON.within(chat_inject_button)` via `click_stop()` | `chat-stop-button` | ladder, requires mid-turn injection on |
| Regenerate | 1 | `ChatPage.regenerate_action_button` (`chat-regenerate-button`) | - | testid on DEV ✓ (ELITEA-2185) |
| Copy / Delete / Read-out | 1 | `ChatPage.copy_action_button` etc. | - | testid on DEV ✓ |
| Loading / thought / model chip | 1 | `answer_loading_placeholder`, `answer_thought_accordion`, `answer_model_chip` | - | testid on DEV ✓ |

## Network / Behaviour
- Streaming timeline (Haiku 4.5): text starts ~2.4s, ~450 chars at 2.8s, ~4600 chars at ~14s; Stop is present throughout.
- On Stop (per #2524): `DELETE /api/v2/elitea_core/task/prompt_lib/575/<id>` 204, then two `PUT .../conversation/prompt_lib/575/<id>` 200; the UI sends no message DELETE (`ChatBox.jsx handleStopStreaming` only sets `stopRequestedRef`, calls `stopStreamingRef` and `onStopRun`), so removal is server-side.
- Console: no errors observed.

## Known Defects Found During Exploration
- #2524 (open, bug): Stop mid-stream deletes the whole turn instead of preserving the partial response. Deterministic. It blocks steps 2-6, so this is `defect-found`, not an isolable tail step (testing.md analysis-time sanctioned-RED does not apply).
- Open product question: does shipped behaviour intentionally discard the turn on Stop (ELITEA-2182/2618 say yes during thinking)? The case premise (issue #5196 salvage when content exists) is not observed. A decision is needed before the case is re-planned.

## Re-plan note for the implementer (once #2524 is fixed or the case is rewritten)
Reuse `test_chat_regenerate_new_response.py` structure (ELITEA-2185). New part: stop after `len(ai_text) > ~300` chars (poll ai item text), assert message count stays 2, hover and assert `chat-regenerate-button` count 1, then regenerate per 2185 steps. Output is nondeterministic: never assert new text != old text.

## Transit flag
`ChatPage.navigate_to_chat(conversation_id=...)` timed out at 15s again (4th analysis in a row, see #1847 class). `page.goto('https://dev.elitea.ai/app/chat/<id>')` plus a `chat-message-input` wait works.
