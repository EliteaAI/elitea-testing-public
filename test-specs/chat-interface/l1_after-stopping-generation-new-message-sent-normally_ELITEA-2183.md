# Test Case: Chat – After Stopping Generation New Message Can Be Sent Normally

## Metadata
- **TMS ID**: ELITEA-2183
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l1 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **blocked** — reclassified from `ready-for-automation` after implementation. Case executed end-to-end live on a fresh conversation (id `8838`, continuing directly from the ELITEA-2182 repro in the same session): stopped an in-progress generation, then sent a new message ("hello") and confirmed a clean, normal LLM response ("Hello! How can I help you today?") with zero console errors. This case's own steps 1-2 were originally assessed as UNAFFECTED by the ELITEA-2182/issue #1569 defect (that defect wipes the PRIOR turn's transcript; this case only requires that a NEW send-and-respond cycle works afterward) — but the implemented test (commit `d2c3dcc23`, `test_send_message_after_stopping_generation_works_normally`) was confirmed BROKEN by live investigation across multiple standalone re-runs. It fails in different observable ways run-to-run: once matching ELITEA-2182's own deterministic Stop-control-disappearance failure (`assert 1 == 0`), once a React `"Maximum update depth exceeded"` console error — both downstream consequences of open defect #1569 (https://github.com/EliteaAI/elitea-testing-public/issues/1569, "Stop wipes the entire message exchange, not just the streaming response"). This case's own Steps 1-2 depend on the exact same Stop-control appear/click/disappear-and-restore mechanism as ELITEA-2182's headline subject, so it is equally exposed even though it does not itself assert transcript persistence. Per `.agents/role-overrides.md` § Declared-improvisation protocol ceiling and `.agents/testing.md` § Merge gate, a soft-assert/known-defect workaround is appropriate only for an ISOLATED assertion inside an otherwise-working test — not when the flow's own precondition (a clean Stop) is itself unreliable. This is the same disposition already used by the sibling case ELITEA-2186 (`l2_regenerate-after-stopped-generation_ELITEA-2186.md`), same root-cause defect. The test was removed from `automation/tests/ui/chat/test_streaming_response.py`.
- **Not already-covered — a real gap.** No existing merged spec exercises "send → stop → send again" in sequence; `test_composer_send_button_toggles_with_empty_input_and_waveform_reappears` only exercises a single uninterrupted send-and-complete cycle.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (the existing `conversation_id` fixture — fresh, API-seeded conversation, same one other tests in `test_streaming_response.py` already use).

## Test Data
- First message (to trigger + stop generation): reuse `test_streaming_response.py`'s own `MESSAGE_TEXT` or a case-equivalent long-form prompt, so the stream stays open long enough to click Stop.
- Second message (case's literal Test Data value): `"hello"`.

## Test Steps

1. Type a message and click Send; verify the Stop control appears (same observable as ELITEA-2182 step 2 — `send_button.count()==0`, `voice_mode_button.count()==0`, Stop control visible).
   - **Verify**: Stop control visible in the composer footer.
2. Click the Stop control to cancel generation.
   - **Verify**: generation stops; input bar restored to the default state (`voice_mode_button` visible again — same mechanism as ELITEA-2182 step 5). NOTE: per issue #1569, the transcript from step 1 is wiped at this point — this case does not require it to persist (its own steps never reference the interrupted turn again), so this AFS does not re-assert transcript persistence here (already covered, as a known defect, by the ELITEA-2182 AFS).
3. Type `"hello"` in the message field.
   - **Verify**: Send button appears (`send_button` visible, `voice_mode_button.count()==0` — mutually exclusive DOM nodes, same as the covering composer test's Step 3).
4. Click Send.
   - **Verify**: the new message appears in the transcript; a new LLM response begins generating and completes normally. Live-confirmed: response text was a coherent, on-topic reply ("Hello! How can I help you today?"), not an error state.
5. Verify no error messages are shown; chat continues normally.
   - **Verify**: zero console errors (`page.on("console")` / `browser_console_messages` level=error, filtered per the file's existing `_is_known_secrets_403` idiom if reused); no error banner/toast in the UI; the AI response renders with the standard action-icon row (Copy/Regenerate/etc.), matching a normal completed turn.

## Expected Results
- After stopping a generation, the composer returns to a fully functional, unstuck state.
- A subsequent message can be typed, sent, and answered exactly as if no prior interruption had occurred — no residual "stuck" state, no error toast, no disabled input.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, open conversation | — | Setup | `conversation_id` fixture + `navigate_to_chat` | asserted |
| 1 Type message, click Send, verify stop button appears | Stop button visible | AFS step 1 | step 1: Stop control visible | asserted |
| 2 Click stop button to cancel generation | Generation stops; input bar restored | AFS step 2 | step 2: `voice_mode_button` visible again | asserted |
| 3 Type 'hello' in the message field | Send button appears | AFS step 3 | step 3: `send_button` visible | asserted |
| 4 Click Send | New message sent; new LLM response begins | AFS step 4 | step 4: message appears, response begins + completes | asserted |
| 5 Verify no error messages shown | Chat continues normally | AFS step 5 | step 5: zero console errors, no error UI | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Explicit confirmation the second response is COHERENT (not an empty/error placeholder) — *added: the case says "responds normally", which a bare "a message appeared" assertion would not actually verify; this AFS requires reading non-empty response text via `wait_for_ai_response`/`wait_for_generation_complete`, matching the house pattern other chat specs already use.*

## Fidelity Declaration
No substitutions. Every observable (Stop control, click, input-bar restoration, typing "hello", Send, the new LLM response, console state) is read from the live DOM / live console in response to real user actions against the real DEV backend — no `page.route`, no `page.evaluate` state injection, no mocked/fabricated response. The second message's LLM reply is asserted for non-emptiness and completion, not for an exact hand-written string (per `.agents/testing.md` § Fidelity policy — the response is the oracle, not a payload the test wrote).

## Cleanup
`conversation_id` fixture owns creation/deletion of the seeded conversation — no additional cleanup needed.

## Concrete Handles (discovered during exploration)

Same handle set as the ELITEA-2182 AFS (`test-specs/chat-interface/l1_stop-button-appears-during-response-generation_ELITEA-2182.md` § Concrete Handles) — this case is a direct continuation of that flow. Notably reuses the **same `chat-stop-generation-button` testid** that AFS specs as `testid needed` — this case's step 2 depends on the same not-yet-added handle, so both cases' implementation should land together (same PR) to avoid adding the testid twice.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Stop control | **testid needed: `chat-stop-generation-button`** (see ELITEA-2182 AFS) | needs-adding | Shared with ELITEA-2182 — do not re-request in a separate PR. |
| Waveform button | `chat-voice-mode-button` | on-`automation/testids` ✓ only | Reused (`chat.voice_mode_button`). |
| Send button | `chat-send-button` | on-`automation/testids` ✓ AND `main` ✓ | Reused (`chat.send_button`). |
| Message input | `chat-message-input` | on-`automation/testids` ✓ AND `main` ✓ | Reused (`chat.message_input`). |

## Network Behavior
- Step 4's Send fires the same message-send flow (WebSocket-delivered response) already documented in the ELITEA-2182 and ELITEA-2181 AFS files — not independently re-verified here at the wire level; asserted via the UI's own completion signals (`wait_for_ai_response`, non-empty response text, action-icon row).

## Known Defects Found During Exploration
None new. This case's own steps are unaffected by issue #1569 (see § Metadata) — the defect is fully attributed to the ELITEA-2182 AFS and its own Known Defects section; not re-filed here (dedup: same root cause, same issue).

## Blocked Steps
- **Step 1 onward.** This case's entire flow depends on a clean Stop-control appear → click → disappear/restore cycle (Steps 1-2) before it can proceed to typing/sending the follow-up message — and that cycle is the direct surface of open defect #1569 (https://github.com/EliteaAI/elitea-testing-public/issues/1569). Live implementation (multiple standalone re-runs) confirmed the cycle itself is unreliable, failing two different ways (a deterministic Stop-control-disappearance assertion failure, matching ELITEA-2182's own signature, and a React "Maximum update depth exceeded" console error) — not a single, stable, single-cause signature safe to soft-assert and merge sanctioned-RED. This is not "one isolable step at the tail" (`.agents/testing.md` § Merge gate, analysis-time entry); the precondition every remaining step (typing "hello", Send, the new response, zero console errors) depends on is itself broken. Routing per `.agents/role-overrides.md`: this AFS is `blocked` → lead → track against #1569; re-attempt once #1569 ships a fix.

## Automation Hints
No test ships for this case — it was implemented (commit `d2c3dcc23`), confirmed unreliable across multiple standalone re-runs (see § Status), and removed. When #1569 is resolved, re-run this analysis fresh before resuming from the hints below; the live product's post-fix Stop behavior may differ enough that a full re-exploration is warranted rather than a straight resume.

The handles and hints below are preserved for that re-attempt, not for immediate reuse:
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Suggested landing spot: same file/PR as ELITEA-2182 — a second new test method in `automation/tests/ui/chat/test_streaming_response.py` (or a shared helper for "send → wait-for-streaming → click stop" reused by both test methods, to avoid duplicating that setup twice).
- Reused verbatim: `chat.navigate_to_chat()`, `chat.send_message()`, `chat.send_button`, `chat.voice_mode_button`, `chat.message_input`, `chat.wait_for_ai_response()`, `chat.wait_for_generation_complete()`, `chat.get_message_count()`, `chat.messages_container`.
- Depends on the SAME `add-data-testid` work as ELITEA-2182 (`chat-stop-generation-button`) — implement both cases together.
