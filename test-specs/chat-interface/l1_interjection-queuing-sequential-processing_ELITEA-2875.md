# Test Case: Basic interjection queuing and sequential processing

## Metadata
- **TMS ID**: ELITEA-2875
- **Linked Story**: EliteaAI/elitea_issues#6115
- **Priority**: l1
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to Elitea (`${TEST_USER_EMAIL}` / `${TEST_USER_PASSWORD}`).
- Chat interface is accessible, a fresh conversation exists (`conversation_id`
  fixture — API-created, confirmed reliable this pass; never a raw
  `sidebar-create-button` click, see `_surface.md` #1085-class note).
- **Mid-turn injection must be enabled for the project** (feature-gated, OFF by
  default — see Automation Hints and `_surface.md`). Platform tier is already
  unblocked in this environment (`is_midturn_injection_blocked: false`);
  project tier (`midturn_injection_enabled`) must be turned on via
  `PUT ${ELITEA_API_BASE}/social/module_settings/${ELITEA_PROJECT_ID}`
  (`{"midturn_injection_enabled": true}`) before this test runs, and the fixture
  that does this should restore the prior value afterward (not independently
  verified whether a project-wide toggle persisted by a test could affect other
  parallel tests — serial execution recommended for this whole family, see
  Automation Hints).

## Test Data
### reuse-existing
- No fixed test data beyond a prompt guaranteed to keep the agent busy long
  enough to interject against. Confirmed live: "Please write a detailed
  500-word story about a dragon who learns to code. Take your time and be
  thorough." against this environment's default model (`Dial-GPT-5.6-Luna`)
  reliably takes 5-6s ("Thought for N secs") — long enough to reach the
  interjectable window every time across 10+ live runs.
- Interjection text: any short string, e.g. `"Interjection message"`.

## Test Steps
1. Navigate to a fresh conversation (`conversation_id` fixture) and confirm the
   chat interface is displayed (`chat-message-input` visible).
   - **Verify**: `chat-message-input` is visible and enabled.
2. Send the long-running prompt via `chat-message-input` + `chat-send-button`.
   - **Verify**: the agent begins processing — a loading/"Waking the agent…"
     placeholder, then streaming content, appears for the agent's turn.
3. Once the turn reports it is listening, the composer swaps its chrome:
   `interjection-composer` (data-testid on the composer's outer `Box`) becomes
   present, and `chat-inject-button` (send-to-running-agent icon) appears
   alongside the Stop icon.
   - **Verify**: `interjection-composer` is present (confirms the run is both
     streaming AND accepting interjections — this is NOT merely "a run is in
     progress"; there is a window right after Send, during "Waking the
     agent…", where the composer has NOT yet swapped — don't assert
     interjectability from the mere presence of a loading indicator).
4. While the agent is still processing (interjection-composer present), type
   an interjection message into `chat-message-input` and click
   `chat-inject-button`.
   - **Verify**: the click succeeds — no error toast, `chat-inject-button`
     has no `aria-disabled`/error state afterward.
5. Verify the queue indicator appears with the correct count and text.
   - **Verify**: `interjection-queue-area` is present; `interjection-queue-label`
     reads exactly `"Waiting messages – 1"` (en dash `–`, confirmed exact
     string — the case's own paraphrase using a middot `·` is cosmetic
     case-text drift, assert the live en-dash string); `interjection-queue-item`
     count is 1 and its text matches the sent interjection.
6. Wait for the initial (first) agent response to complete.
   - **Verify**: the first turn's agent message reaches a stable, non-loading
     state (use `wait_for_ai_response()` + `wait_for_message_content_stable()`
     per project convention, never a fixed sleep).
7. Verify the interjection is processed and receives its own, separate agent
   response, and assert FIFO/structural order in the timeline.
   - **Verify**: the message timeline (`ul.MuiList-root > li.MuiListItem-root`,
     per `.claude/rules/mui-patterns.md`) shows, in order: user's initial
     message → agent response to it → user's interjection message (now a
     normal message in the timeline) → agent's separate response to the
     interjection. Exactly 4 timeline entries for this exchange, no more, no
     fewer (no duplicate responses).
   - **Verify**: `interjection-queue-area` is gone (count 0) once the
     interjection has been folded into the timeline.

## Expected Results
- Both the initial message and the interjection each receive their own,
  individual agent response.
- The queue indicator (`interjection-queue-area`/`interjection-queue-label`)
  appears while the interjection is pending and disappears once it is
  consumed.
- FIFO order is maintained: initial message → its response → interjection →
  its response.
- No duplicate or missing responses.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Login and navigate to chat | Chat interface is displayed | step 1 | step 1: `chat-message-input` visible | asserted |
| 2 Send initial message to trigger agent run | Agent starts processing the message | step 2 | step 2: loading/streaming indicator | asserted |
| 3 While agent is processing, send interjection message | Interjection is sent successfully | steps 3-4 | step 4: no error state after click | asserted *(decomposed: step 3 isolates the interjectable-window check first)* |
| 4 Verify "Waiting messages · 1" indicator appears | Queue indicator shows "Waiting messages · 1" | step 5 | step 5: exact live text `"Waiting messages – 1"` | asserted *(clarification: live text uses en dash, not middot — case-text drift, not a defect)* |
| 5 Wait for initial response to complete | First agent response completes successfully | step 6 | step 6: stable non-loading state | asserted |
| 6 Verify interjection is processed and gets separate response | Interjection receives its own agent response | step 7 | step 7: 4 distinct timeline entries | asserted |
| 7 Assert message order in timeline | FIFO order: initial → response → interjection → response | step 7 | step 7: timeline order check | asserted |

Axis 2 — Analyst additions:
- Step 3 asserts `interjection-composer` presence as a precondition gate before
  attempting the interjection — *added: live exploration showed a real
  "not-yet-interjectable" window right after Send ("Waking the agent…") where
  attempting the interjection prematurely would be testing the wrong state;
  without this gate a flaky implementation could pass by accident on a fast
  response.*
- `interjection-queue-area` becoming absent (count 0) after consumption is
  asserted in step 7 — *added: confirms the queue UI doesn't leak a stale
  "0 remaining" chip; observed live that the area unmounts entirely
  (`PendingInjectionList` returns `null` on empty items), not just empties.*

## Cleanup
1. Delete the conversation via `conversation_id` fixture teardown (API
   `DELETE /elitea_core/conversation/prompt_lib/{project_id}/{id}`).
2. Restore `midturn_injection_enabled` to its prior value if the enabling
   fixture mutated project-level state (see Preconditions).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Message input | `[data-testid="chat-message-input"]` (existing `ChatPage.message_input`) | n/a — testid confirmed live |
| Send button | `[data-testid="chat-send-button"]` (existing `ChatPage.send_button`) | n/a — testid confirmed live |
| Interjection-aware composer wrapper | `[data-testid="interjection-composer"]` | n/a — testid confirmed live, present only while `isStreaming && isInjectable` |
| Send-to-running-agent (inject) button | `[data-testid="chat-inject-button"]` | n/a — testid confirmed live |
| Queue container | `[data-testid="interjection-queue-area"]` | n/a — testid confirmed live, unmounts (not just empties) when `pendingInjections.length === 0` |
| Queue label (count text) | `[data-testid="interjection-queue-label"]` | n/a — testid confirmed live; exact text `"Waiting messages – {N}"` (en dash) |
| Queue item (per queued message) | `[data-testid="interjection-queue-item"]` | n/a — testid confirmed live, one per queued item |
| Message timeline | `ul.MuiList-root > li.MuiListItem-root` scoped under `main` (per `.claude/rules/mui-patterns.md`) | n/a — existing project convention |

## Network Behavior
- `POST ${ELITEA_API_BASE}/elitea_core/inject/prompt_lib/{projectId}/{conversationUuid}`
  — fires when `chat-inject-button` is clicked, body `{"user_input": ..., "injection_id": ...}`.
  Confirmed live (source-read, `injectMessageApi.js`) — not independently
  asserted on status code this pass; worth a network-tab assertion if the
  implementer wants an extra signal, not required for Pass/Fail per the case.
- WebSocket events `injection_ready` (enables the inject affordance),
  `agent_midturn_injection_consumed` (per-interjection ack, pins it into the
  timeline), and the turn-end `InjectionConsumedReport` (authoritative —
  confirms what was actually folded in) drive all of the above UI transitions.
  Confirmed via source read of `src/components/Chat/hooks.js`; not
  independently captured on the wire this pass (UI-observable effects were
  sufficient to verify the case's Pass/Fail criteria).

## Known Defects Found During Exploration
None found. Case text's "Waiting messages · 1" (middot) vs. the live
"Waiting messages – 1" (en dash) is case-text drift, not a defect — filed as
a clarification per `.agents/role-overrides.md`'s reverse-masking guard (see
Coverage Map row 4). No separate tracker issue filed for this clarification
alone since it is covered by the identical note already present verbatim in
each sibling case's AFS in this family — filing once per family avoids four
near-duplicate "same cosmetic text drift" issues (strict-per-bug bundling
policy is about distinct defects, not about re-filing the same observation
once per case in a cluster); see Automation Hints for the single tracker
issue reference.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, per `.agents/testing.md`.
- Mid-turn injection is feature-gated at the PROJECT level
  (`midturn_injection_enabled`, default `false` in this environment) and the
  PLATFORM level (already unblocked here). A new fixture is needed —
  something like `midturn_injection_enabled` (function- or session-scoped,
  PUT the module_settings flag true before the test, restore the original
  value after) — this is new shared infrastructure the whole
  ELITEA-2875/2876/2877/2878 family depends on; implement it once, reuse
  across all four specs in this family (same batch, same PR set is fine —
  it's one fixture file in `fixtures/`, not per-test duplication).
- CLARIFICATION to file (once, covers the whole family): case text's queue-count
  format "Waiting messages · N" (middot) doesn't match the live
  "Waiting messages – N" (en dash). File ONE clarification issue referencing
  all four case IDs (ELITEA-2875/2876/2877/2878) rather than four separate
  near-identical issues — this is a judgment call favoring the spirit of
  strict-per-bug (distinct defects get distinct tickets) over its letter
  (a single verbatim cosmetic observation repeated four times is not four
  defects). Declared improvisation — flagging for reviewer sign-off per
  `.agents/role-overrides.md` § Declared-improvisation protocol.
- Reuse `ChatPage.wait_for_ai_response()` / `wait_for_message_content_stable()`
  for all waits — never a fixed sleep (AI responses arrive over WebSocket with
  ~2-6s delay in this environment, confirmed live).
- This family's 4 cases share one surface and one new fixture — see
  `test-specs/chat-interface/_surface.md` § Mid-turn interjection for the full
  handle set and quirks shared across all four.
