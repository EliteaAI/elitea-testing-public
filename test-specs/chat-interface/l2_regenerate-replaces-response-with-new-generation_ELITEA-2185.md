# Test Case: Chat – Clicking Regenerate Generates a New Response Based on Previous User Input

## Metadata
- **TMS ID**: ELITEA-2185
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: **ready-for-automation** — executed live this session against a real conversation (`http://localhost:5173/chat/8834`): sent a user message, waited for its AI response, hovered + clicked Regenerate, and observed the full replace-and-regenerate cycle end-to-end via the accessibility snapshot and DOM state. Confirmed: the LAST message's content is replaced **in place** (the message-list item count does not grow), the user's own message is untouched, and the new response text genuinely differs from the original (both LLM-produced, not test-authored — see § Fidelity Declaration).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- A conversation with at least one user message and LLM response exists.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Fresh conversation via the existing `conversation_id` API fixture.
- One short message (case's own Test Data: "none required" — content is not load-bearing, only needs to produce a real LLM completion quickly): e.g. `"Hi there"`.

## Test Steps

1. Send a message; wait for its AI response to complete; scroll to it and hover.
   - **Verify**: Regenerate button visible (existing `chat-regenerate-button` handle, confirmed exclusive to the last message per the sibling ELITEA-2184/2187 family AFS).
2. Click the Regenerate button (circular-arrows icon).
   - **Verify**: confirmed live — the previous response's content is replaced **in place** (message-list item count is unchanged before/after: the AI message that was at index N is still at index N, its body text differs). A NEW generation begins immediately (see step 3).
3. Verify the model label and a loading/streaming indicator appear on the regenerating response.
   - **Verify**: confirmed live — same widget sequence as a normal Send (RotatingMessages placeholder → "Thought for `<n>` secs" accordion with the model-name chip inside it, per the already-documented ELITEA-2181 contract). The composer's send-slot shows the Stop control (`chat-stop-generation-button`) while regenerating, same reused control as ELITEA-2182/2183 and the sibling ELITEA-2187.
4. Verify the user's previous input remains unchanged.
   - **Verify**: confirmed live — the user message's text content is byte-identical before and after the regenerate cycle (captured via `ChatPage._extract_message_body()` on the user message, compared pre/post).
5. Verify the new response streams and completes.
   - **Verify**: confirmed live — `ChatPage.wait_for_ai_response()`-style completion signal (Copy button visibility) resolves; the completed response body is non-empty. **Fidelity note**: the response text is asserted for non-emptiness/coherence and for being DIFFERENT from the pre-regenerate text, not for an exact hand-written string — the LLM is a nondeterministic producer, and the response itself is the oracle (`.agents/testing.md` § Fidelity policy, "capture the real response and assert against it").
6. Verify Regenerate and action icons reappear after completion.
   - **Verify**: confirmed live — hovering the (still-last) message shows all 4 icons again (speaker, copy, regenerate, delete).

## Expected Results
- Regenerate replaces the last message's content in place (no new message-list item is created) with a genuinely new LLM-produced response.
- The user's own message is byte-identical before and after.
- The regenerating response goes through the same loading/streaming widget sequence as a normal Send, then completes and restores the full action-icon row.
- No functional product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: conversation with ≥1 user message + LLM response | — | Setup | fresh conversation + 1 sent message | asserted |
| 1 Scroll to last LLM response and hover → Regenerate button visible | regenerate visible | step 1 | hover; `expect(chat.regenerate_action_button).to_be_visible()` | asserted |
| 2 Click Regenerate → Previous response replaced; new generation begins | replace + new gen | step 2 | message-item count unchanged; body text differs pre/post | asserted |
| 3 Verify model label and spinning loading circle on new response → Loading indicator visible | loading indicator | step 3 | Stop control visible; `chat.answer_loading_placeholder`/`answer_thought_accordion`/`answer_model_chip` visible (RotatingMessages/Thought-accordion/model-chip sequence, reused ELITEA-2181 contract) | asserted *(same case-text-vs-live-widget clarification already filed under issue #1100 for ELITEA-2181 applies here too — no new clarification needed, cross-referenced not re-filed)*. **Amended during implementer fix round 1 (review finding):** the initial implementation asserted only the Stop control, narrowing this row without documenting it — the full RotatingMessages/Thought-accordion/model-chip sequence is now actually asserted in code (`automation/tests/ui/chat/test_regenerate_response.py` Step 3), so the row's original claim is now accurate. |
| 4 Verify user's previous input remains unchanged → User message unchanged | message unchanged | step 4 | `_extract_message_body()` on user message, compared pre/post | asserted |
| 5 Verify new response streams and completes → Full response generated | full response | step 5 | completion signal + non-empty, differing body text | asserted |
| 6 Verify Regenerate and action icons reappear after completion → Actions visible again | actions reappear | step 6 | hover; all 4 icon locators visible | asserted |
| Expected Final State: "New response generated; previous user message unchanged." | — | steps 2-6 | as above | asserted |
| Pass/Fail: "Regenerate generates new response; user message unchanged." | — | all steps | as above | asserted |

### Axis 2 — Analyst additions

- Step 2's "replaced" is proven structurally (message-item count unchanged, not merely "new text appeared") — *added: distinguishes a true in-place replace from a regression where Regenerate instead APPENDS a new message, which would still show new streaming text but corrupt the conversation's turn structure.*
- Step 5 asserts the new response body TEXT DIFFERS from the pre-regenerate text (in addition to non-emptiness) — *added: a regression where Regenerate silently no-ops (re-renders the same cached text without a real new generation) would still pass a bare non-emptiness check; a same-vs-different comparison catches it. **Amended during implementer fix round 1 (review finding):** this is a HARD assertion (`assert post_click_body != pre_click_body`), not a soft/logged comparison — the case's own headline claim is "clicking Regenerate generates a NEW response," and demoting that to a `logger.warning` is the No Defect Masking Rule's forbidden "demote expect() to log.info" shape (a no-op Regenerate would pass this test green). Accepted risk: an LLM could rarely coincidentally reproduce identical text on a short, open-ended prompt — treated as ordinary test flakiness (investigate on occurrence), not a reason to weaken the assertion.*
- Console/network checked across the whole flow — no new errors observed for this case's own actions.

## Cleanup
1. Conversation deleted via the `conversation_id` fixture's own teardown.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Fidelity Declaration
- No substitution. Every observable (Send, the initial AI response, the Regenerate click, the loading/streaming sequence, the new AI response, the user-message text, the reappeared action icons) is produced and read live against the real DEV backend — no `page.route`/`page.evaluate`/mock. The new response's exact text is NOT asserted as an exact hand-authored string; it is the oracle (per `.agents/testing.md` § Fidelity policy — "capture the real response and assert the UI against it").

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Regenerate icon | `chat-regenerate-button` | on-main ✓ | `ChatPage.regenerate_action_button` — safe to use bare here (single-exchange conversation, exactly 1 AI message). |
| Copy icon | `chat-copy-button` | on-main ✓ | `ChatPage.copy_action_button` — same single-match safety. |
| Read-out icon | `chat-read-out-button` | on-main ✓ | `ChatPage.read_out_button`. |
| Delete icon | `chat-delete-button` | on-main ✓ | `ChatPage.delete_action_button`. |
| Stop-generation control | `chat-stop-generation-button` | on-`automation/testids` (ELITEA-2182/2183; check current promotion state at implementation time) | `ChatPage.stop_generation_button` — reused as the "regeneration in progress" signal. |
| Message item container | `chat-message-item` | on-main ✓ | `ChatPage.messages_container`. |

## Network Behavior
- Regeneration reuses the same WebSocket-streamed response contract as a normal Send — no new REST endpoint observed.
- No console errors observed in this session's exploration.

## Known Defects Found During Exploration
None for this case.

## Blocked Steps
None. All 6 steps executed and observed live this session.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Reuse `ChatPage.wait_for_ai_response()` / `ChatPage._extract_message_body()` — do not re-derive.
- Wait strategy: condition-based only, per `.agents/testing.md`. `AI_RESPONSE_TIMEOUT` at the project's standard 120s (CI headroom) is generous for a short prompt like `"Hi there"` (confirmed live to complete in single-digit seconds without invoking the file-writing tool).
- **Amended during implementer fix round 1 (review finding):** the text-differs comparison from Axis 2 is a HARD `assert`, not a soft/logged signal — see Axis 2 bullet above. A coincidentally-identical LLM completion is accepted as ordinary test flakiness, not a reason to demote the assertion.
