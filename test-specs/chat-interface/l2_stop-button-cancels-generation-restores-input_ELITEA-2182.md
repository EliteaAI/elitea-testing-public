# Test Case: Chat – Stop button appears during response generation and cancels it

## Metadata
- **TMS ID**: ELITEA-2182
- **Linked Story**: EliteaAI/elitea_issues#5196
- **Priority**: l2 (TMS `high`)
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed), headless Chromium, 4 live trials
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation
- **Surface key**: `chat-composer-stop-generation`

## Preconditions
- Logged in (framework `auth_state`); a fresh conversation (`conversation_id` fixture, empty).
- NO `midturn_injection_enabled` needed for the stop button itself (it renders regardless), but see Network/Behaviour note: with mid-turn injection ON the Stop control is the same button and `chat-inject-button` sits beside it.

## Test Data
- Message: `generate a poem` (verbatim, no trailing text).

## Test Steps
1. Navigate to the fresh conversation; type `generate a poem`; click Send (`chat_page.send_message`).
   - **Verify**: user message appears in the timeline (`ul.MuiList-root > li.MuiListItem-root`, text contains `generate a poem`); `chat-send-button` disappears (generation started).
2. Wait for the thinking/sub-agent phase and verify the Stop control is visible at the far right of the composer footer.
   - **Verify**: `ChatPage.STOP_BUTTON.within(chat_inject_button)` — NOTE `chat_inject_button` is NOT present when mid-turn injection is off (see Handles + Question 1). Stop first renders ~0.5s after click (while the agent bubble reads "Waking the agent…"), stays until final text begins; the agent bubble shows `Thinking` text from ~2.3s.
3. Click Stop while the agent bubble still shows `Thinking` (final answer not started).
   - **Verify**: click succeeds.
4. Verify no further text streams.
   - **Verify**: after the click, the timeline holds NO agent answer text; poll ~2.5s: `li` count stays 0 (new chat) and never reappears (observed 0 in 3/3 clicks; in a non-empty conversation both the new user turn and the partial agent bubble are removed and the earlier turns remain).
5. Verify Stop disappears and the default input bar returns.
   - **Verify**: Stop button absent (count 0); `chat-send-button` visible again.
6. Verify input is active/editable.
   - **Verify**: `chat-message-input` `is_editable()` true (it is `disabled` for ~100ms right after the click - wait for editable, don't assert instantly).
7. Verify input holds the exact original text.
   - **Verify**: `chat-message-input` value == `generate a poem` exactly (observed 4/4 trials: restored).

## Expected Results
Generation cancelled in the thinking phase; no answer text; default input bar restored with the exact original prompt and editable.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Type + Send | user msg appears; generation starts | step 1 | step 1 | asserted |
| 2 Stop visible during thinking | stop visible | step 2 | step 2 | asserted *(clarification: "far right of bottom input bar" - it is in the footer row left of the inject/send slot; assert visibility, not geometry)* |
| 3 Click stop during thinking | stops immediately | step 3 | step 3-4 | asserted |
| 4 No further text streams | streaming stopped | step 4 | step 4 (no agent text, stays 0 over ~2.5s) | asserted *(live nuance: the partial agent bubble AND the user bubble are REMOVED from the timeline, not left half-rendered - case text silent on this)* |
| 5 Stop gone, default bar | normal input bar | step 5 | step 5 | asserted |
| 6 Input active/editable | editable | step 6 | step 6 | asserted |
| 7 Input has exact original text | "generate a poem" | step 7 | step 7 | asserted |

Axis 2 - Analyst additions:
- Step 4 asserts timeline empties (user turn removed) - *added: it is the observable proof that the stop cancelled rather than finished; without it a response that completed in 3s would pass steps 5-7 on a null stop.*
- Step 2/3 gate on the agent bubble showing `Thinking` (not just Stop visible) - *added: the case is explicitly scoped to the thinking phase (#5196); clicking after final text starts gives a different outcome (button already gone).*

## Concrete Handles (verified on DEV 2026-10-20)

| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Message input | 1 | `chat-message-input` (`ChatPage.message_input`) | - | testid on DEV ✓ |
| Send button | 1 | `chat-send-button` (`ChatPage.send_button`; needs `force=True` click, MUI overlay) | - | testid on DEV ✓ |
| Stop button | 5 | existing `ChatPage.STOP_BUTTON` (xpath, scoped under `chat_inject_button`) | `chat-stop-button` | ladder - no testid on DEV; BUT see Question 1: the existing scoping anchor only exists with mid-turn injection enabled |
| Stop button (injection OFF) | 5 | within the composer (`chat-message-input` -> 4th ancestor) the only `button` with no `data-testid` and no `aria-label` | `chat-stop-button` | ladder - verified unique in 4 trials; implementer must declare a ScopedLocator anchored on a declared parent (e.g. `chat-input` has no testid-less alternative; `chat-message-input` ancestor hops) - raise to lead if no non-positional form exists |
| Timeline items | 4 | `ul.MuiList-root > li.MuiListItem-root` (`ChatPage.get_message_count`) | - | existing |
| Thinking indicator | text | agent bubble text contains `Thinking` (≈2.3s after send); later collapses to `Thought for N secs` | `chat-thinking-label` | ladder - text only, no testid |

## Network / Behaviour
- Timing is tight and fast on DEV (model Claude Haiku 4.5): Stop appears at ~0.5s, `Thinking` text ~2.3s, final text ~2.9-3.5s, Stop vanishes when final text starts. Polling must be tight (<=100ms) via `page.wait_for_function`/Playwright locator waits - a 500ms+ poll can miss the window. If the run is too fast to catch `Thinking`, the test must fail loudly, not skip.
- Stop on a brand-new chat: conversation row "Generate poem" is created in the sidebar and URL becomes `/chat/<id>?name=Generate+poem`; the conversation is left empty (use `conversation_id` fixture, the API teardown deletes it).
- Clicking Stop at "Waking the agent..." (before Thinking) behaves the same (input restored) - one intermittent observation: at that moment Stop can re-flicker once (stop/enter-speaking-mode toggles) before settling; so click only after `Thinking`.
- Console: no errors observed.

## Known Defects Found During Exploration
None. Clarifications (not defects): (a) case "far right" wording; (b) cancelled turn is removed from the timeline; (c) existing ELITEA-2878 AFS documents the Stop button without a testid - same gap.

## Questions for the lead
1. `ChatPage.STOP_BUTTON` is `ScopedLocator.within(chat_inject_button)`; `chat-inject-button` only renders when mid-turn injection is enabled. Either the implementer uses the `midturn_injection_enabled` fixture (changes the composer under test - Stop is the same button either way, so acceptable and cheapest, declare it) or adds a second non-positional declaration. Recommend the fixture route.
2. Optional hardening: neighbour specs (ELITEA-2878 etc.) already exercise `click_stop()` but none asserts input restoration or timeline removal - no coverage of this case's observable, hence not `extend-existing`/`already-covered`.
