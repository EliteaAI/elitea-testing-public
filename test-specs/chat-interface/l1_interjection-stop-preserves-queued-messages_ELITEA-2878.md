# Test Case: Stop preserves queued messages

## Metadata
- **TMS ID**: ELITEA-2878
- **Linked Story**: EliteaAI/elitea_issues#6115
- **Priority**: l1
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to Elitea.
- Chat interface is accessible, a fresh conversation exists (`conversation_id`
  fixture).
- Mid-turn injection enabled for the project — shared fixture, see ELITEA-2875
  AFS.

## Test Data
### reuse-existing
- Long-running prompt (same as ELITEA-2875).
- Interjection 1 = `"First queued message"`
- Interjection 2 = `"Second queued message"`
- A follow-up message to continue chatting after Stop, e.g.
  `"continuing chat after stop"`.

## Test Steps
1. Navigate to a fresh conversation, send the long-running prompt, and reach
   the interjectable window.
   - **Verify**: `interjection-composer` present.
2. Queue Interjection 1.
   - **Verify**: `interjection-queue-item` count is 1, text matches
     Interjection 1.
3. Queue Interjection 2.
   - **Verify**: `interjection-queue-label` reads exactly
     `"Waiting messages – 2"` (en dash — same drift note as ELITEA-2875/2876).
4. Click the Stop control. **No stable testid/aria-label exists on this
   control** (confirmed via source read, `UserInput.jsx` — see Blocked
   Steps/Automation Hints for the interim handle and the filed gap).
   - **Verify**: the click actually stops the run — immediately after
     clicking, confirm the run is interrupted (do not simply assume; the live
     mechanism, confirmed by source + live observation, is a RESCUE-AND-REDRAIN,
     not a hard freeze — see step 5 for the precise, confirmed behavior).
5. Verify queued messages are preserved — **confirmed exact live mechanism,
   which is MORE NUANCED than "both messages sit frozen in the queue"**:
   clicking Stop immediately converts the HEAD-OF-QUEUE item (Interjection 1)
   into a real, normally-sent user message (its own agent response begins
   "Waking the agent…" within ~1s — this is `ChatBox.jsx`'s documented
   stop-then-rescue-then-redrain path), while Interjection 2 remains visible
   in `interjection-queue-area` with the label decremented to
   `"Waiting messages – 1"`.
   - **Verify**: within ~1-2s of the Stop click, Interjection 1 appears as a
     normal timeline entry (`ul.MuiList-root > li.MuiListItem-root`) with its
     own agent response starting; `interjection-queue-area` still shows
     Interjection 2 with count 1.
6. Click Stop a second time to continue draining (same mechanism) and let the
   second rescued item (Interjection 2) also convert to a normal timeline
   message with its own response.
   - **Verify**: after the second Stop + full settle (poll
     `interjection-composer` count == 0), the timeline contains BOTH
     Interjection 1 and Interjection 2 as normal user messages, each with its
     own agent response, and `interjection-queue-area` is gone (count 0) —
     i.e. nothing was lost, both messages are now ordinary timeline entries.
7. Verify message text matches the original exactly for both.
   - **Verify**: the two user-authored timeline entries' text is byte-for-byte
     "First queued message" / "Second queued message" — no corruption, no
     truncation.
8. Send a new message to continue chatting.
   - **Verify**: `chat-send-button` → the new message sends normally and
     receives an agent response (poll `wait_for_ai_response()`), confirming
     the chat is NOT left in a broken/unresponsive state after the
     Stop-and-drain sequence.

## Expected Results
- Queued messages are NOT deleted when Stop is clicked.
- Both messages ultimately convert to normal user messages in the timeline,
  text preserved exactly, each with its own agent response.
- Chat continues functioning normally afterward (a new message sends and
  gets a response).

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Login and start long-running agent task | Agent starts processing | step 1 | step 1 | asserted |
| 2 Queue first interjection message | First message appears in queue | step 2 | step 2 | asserted |
| 3 Queue second interjection message | Second message appears in queue, count "Waiting messages · 2" | step 3 | step 3: exact live text `"Waiting messages – 2"` | asserted *(clarification: en dash not middot — same family-wide drift, see ELITEA-2875)* |
| 4 Click Stop button | Agent run stops immediately | step 4 | step 4 | asserted *(clarification: "stops immediately" is imprecise — the live mechanism rescues the head item into a resend rather than halting instantaneously with nothing moving; see row below)* |
| 5 Verify queued messages preserved in timeline | Both queued messages remain visible in chat timeline | steps 5-6 | step 6: both present as normal timeline entries after full drain | asserted *(decomposed: case implies both appear after ONE click; live mechanism needs Stop clicked once per queued item to fully drain — see Known Defects/Clarifications)* |
| 6 Verify message text matches original | Message content is exactly preserved | step 7 | step 7: byte-for-byte text match | asserted |
| 7 Send new message to continue chatting | New message sent successfully and receives response | step 8 | step 8 | asserted |

Axis 2 — Analyst additions:
- Step 5 asserts the INTERMEDIATE state (one item rescued, one still queued)
  before asserting the final fully-drained state in step 6 — *added: this is
  the step that actually proves "preserved, not discarded" as a mechanism
  rather than a coincidental end-state; skipping it would let a flaky
  "both just happen to appear eventually" implementation pass without
  proving the queue was ever genuinely non-destructive mid-drain.*
- Step 8's "chat continues functioning normally" check — *added: directly
  from the case's own Expected Final State wording, but elevated to its own
  verified step with a real wait rather than an implicit assumption.*

## Cleanup
1. Delete the conversation via `conversation_id` fixture teardown.
2. Restore `midturn_injection_enabled` per the shared fixture's teardown.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Stop control | **No stable rung exists today** — confirmed via source read (`UserInput.jsx`): a bare icon `BaseBtn` wrapped only in a `Tooltip` (title "Stop generating", not forwarded as an accessible name/aria-label). Live-confirmed interim handle: the icon button immediately preceding `chat-inject-button`'s own `sendButtonContainer` `Box` within the composer footer row (DOM-position relative to a stable sibling, not a raw position in an unrelated set) — **not a positional pick on an arbitrary list**; it is scoped relative to one already-stable, uniquely-testid'd sibling, which is the standard "scope to a declared parent" ladder technique applied to a 2-button row. `testid needed: chat-stop-button` on the Stop `BaseBtn` in `UserInput.jsx` — flagged for the migrator, this is this case's own executed path | None — this is the priority gap for this case; implementer may use the DOM-relative handle described above as a `ScopedLocator`/`xpath=` declaration with `description=` explaining the relative-sibling rationale per `.claude/rules/page-objects.md` |
| Queue label | `[data-testid="interjection-queue-label"]` | n/a |
| Queue item | `[data-testid="interjection-queue-item"]` | n/a |
| Queue area | `[data-testid="interjection-queue-area"]` | n/a |
| Message timeline | `ul.MuiList-root > li.MuiListItem-root` scoped under `main` | n/a |

## Network Behavior
Clicking Stop triggers the client-side `onStopStreaming`/`stopAll` path
(confirmed via source read, `ChatBox.jsx`'s `handleStopStreaming`) which halts
the current turn's stream and then — because items were still queued —
automatically re-emits the head-of-queue item through the normal
predict-stream path (same `POST`/WebSocket contract as a normal send, not the
`inject` endpoint, since by the time it's rescued it's no longer "mid-turn").
Not independently captured on the wire this pass; UI-observable effects
(timeline entries, queue count) were sufficient for this case's Pass/Fail
criteria.

## Known Defects Found During Exploration
**CLARIFICATION (not a defect) — case text implies a single Stop click
freezes the queue with both messages immediately visible; live mechanism is
rescue-and-auto-redrain, one item at a time, each converting to a real send
with its own response.** This is a `.agents/role-overrides.md` reverse-masking
case: the live behavior is almost certainly the INTENDED design (confirmed by
explicit code comments in `ChatBox.jsx` narrating exactly this rescue path —
"Safety net: only rescue pending items when the user explicitly stopped the
task" and "Dequeue one item at a time") — it is not a bug, and nothing is
ever lost; the case text under-specifies the mechanism, not the outcome. Filed
as part of the single family-wide clarification issue referenced in
ELITEA-2875's Automation Hints (bundled with the queue-count-text drift —
both are case-text-precision issues on the same TMS case family, not separate
defects) rather than a second new issue, per the same declared-improvisation
reasoning given there.

## Blocked Steps
None — the Stop-control handle gap is recorded above as a Concrete Handles
item + `testid needed`, not a blocker: the ladder's lowest rung (a
description-justified relative-position handle) is usable today, same as
any other `migrate-locators-to-testids` candidate.

## Automation Hints
- Shares the `midturn_injection_enabled` fixture with the rest of this
  family.
- The implementer should expect to call the Stop control TWICE to reach the
  fully-drained state asserted in step 6, when 2 items were queued (once per
  queued item) — this is the confirmed live mechanism, not an automation
  bug to work around.
- Reuse `wait_for_ai_response()`/`wait_for_message_content_stable()` for all
  post-Stop waits.
