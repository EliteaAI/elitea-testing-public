# Test Case: FIFO message order preservation

## Metadata
- **TMS ID**: ELITEA-2876
- **Linked Story**: EliteaAI/elitea_issues#6115, EliteaAI/elitea_issues#6457
- **Priority**: l1
- **Environment Explored**: dev (`https://dev.elitea.ai/app`, as deployed)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (analyst slot)
- **Status**: ready-for-automation

## Preconditions
- User is logged in to Elitea.
- Chat interface is accessible, a fresh conversation exists (`conversation_id`
  fixture).
- Mid-turn injection enabled for the project — same fixture dependency as
  ELITEA-2875 (see that AFS's Preconditions/Automation Hints; the fixture is
  shared infrastructure for this whole family, implement once).

## Test Data
### reuse-existing
- Long-running prompt (same as ELITEA-2875): "Please write a detailed
  500-word story about a dragon who learns to code. Take your time and be
  thorough."
- Interjection texts, sent in order:
  - Message A = `"First message"`
  - Message B = `"Second message"`
  - Message C = `"Third message"`
  (Case text's literal "First message"/"Second message"/"Third message" was
  used verbatim and confirmed live — no drift here, unlike the case's
  queue-count-text paraphrase documented in the ELITEA-2875 AFS.)

## Test Steps
1. Navigate to a fresh conversation and send the long-running prompt.
   - **Verify**: agent starts processing (`interjection-composer` eventually
     present, confirming the interjectable window).
2. Queue Message A, Message B, Message C in rapid succession (type into
   `chat-message-input`, click `chat-inject-button`, repeat for all three with
   no explicit delay beyond what the UI itself needs between actions).
   - **Verify**: after each queue action, `interjection-queue-item` count
     increments by 1 and the newest item's text matches the message just
     queued, appended to the END of the existing items (not prepended) —
     confirmed live: `interjection-queue-item` nth(0)/(1)/(2) read A, B, C in
     that exact order immediately after all three are queued.
3. Verify the queue count shows 3.
   - **Verify**: `interjection-queue-label` reads exactly
     `"Waiting messages – 3"` (en dash — see ELITEA-2875 AFS's clarification
     note on the case text's middot paraphrase, same drift applies here).
4. Wait for all three messages to process (drain fully — queue area gone AND
   the agent's turn fully settled, no `interjection-composer` present).
   - **Verify**: use a poll loop on `interjection-composer` count == 0 AND
     `interjection-queue-area` count == 0, never a fixed sleep (confirmed
     live: full drain for 3 queued items against this environment's model
     took ~11-12s across repeated runs).
5. Assert processing order matches send order by reading the full message
   timeline, not just the queue snapshot.
   - **Verify**: scanning `ul.MuiList-root > li.MuiListItem-root` top-to-bottom,
     the USER-authored messages (filter out agent-authored entries) appear in
     the exact order: initial prompt → A → B → C. Each of A, B, C is
     immediately followed by its own distinct agent response before the next
     user message appears (interleaved user/agent, never two user messages
     back-to-back without an intervening response).
6. Verify each message has exactly one response.
   - **Verify**: count agent-authored timeline entries between the initial
     prompt's response and the end — exactly 3 (one per A/B/C), no duplicates,
     no entry skipped. Confirmed live across 2 independent runs with this
     exact 3-message sequence: 8 total timeline entries (prompt, response,
     A, response, B, response, C, response) — a non-8 count is a genuine
     failure, not noise.

## Expected Results
- All three messages processed in strict FIFO order: A, B, C.
- Each message gets exactly one response — no message is skipped or
  duplicated.
- The queue count increments to 3 correctly and reaches 0 after drain.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Login and start long-running agent task | Agent starts processing | step 1 | step 1 | asserted |
| 2 Queue message A rapidly | Message A appears in queue | step 2 | step 2: queue item 0 text | asserted |
| 3 Queue message B rapidly | Message B appears in queue | step 2 | step 2: queue item 1 text | asserted |
| 4 Queue message C rapidly | Message C appears in queue | step 2 | step 2: queue item 2 text | asserted |
| 5 Verify queue count shows 3 | Queue indicator displays "Waiting messages · 3" | step 3 | step 3: exact live text `"Waiting messages – 3"` | asserted *(clarification: en dash not middot, same drift as ELITEA-2875)* |
| 6 Wait for all messages to process | All three receive responses sequentially | step 4 | step 4: poll to full drain | asserted |
| 7 Assert processing order matches send order | A → B → C | step 5 | step 5: timeline scan, user-message order | asserted |
| 8 Verify each message has exactly one response | Each has exactly one response | step 6 | step 6: exact timeline-entry count (8) | asserted |

Axis 2 — Analyst additions:
- Step 2 asserts queue items append in submission order (position 0/1/2
  matching A/B/C) at queue-time, not just at drain-time — *added: this is the
  mechanism the case's FIFO claim actually rests on
  (`stopQueueRef.current.push`, confirmed via source read), and catching an
  ordering bug here is cheaper/faster than only catching it after a full
  ~12s drain.*
- Step 6's exact total-entry-count assertion (8, not "at least 4") — *added:
  guards against a silent duplicate-response regression that a looser
  "each of A/B/C has >=1 response" check would miss.*

## Cleanup
1. Delete the conversation via `conversation_id` fixture teardown.
2. Restore `midturn_injection_enabled` per the shared fixture's teardown (see
   ELITEA-2875 AFS).

## Concrete Handles (discovered during exploration)

Same handle set as ELITEA-2875 (`interjection-composer`, `chat-inject-button`,
`interjection-queue-area`, `interjection-queue-label`, `interjection-queue-item`,
message timeline) — see that AFS's Concrete Handles table and
`test-specs/chat-interface/_surface.md` § Mid-turn interjection for the full
set; not re-tabulated here.

| Element | Recommended Locator | Fallback |
|---|---|---|
| Queue items in order | `[data-testid="interjection-queue-item"]` (indexed, `.nth(0/1/2)` is a non-positional read of a count-verified set — enumerating every match, not picking one, per the project's locator-ladder exception for `.nth()`) | n/a |

## Network Behavior
Same `POST .../elitea_core/inject/...` + WebSocket event sequence as
ELITEA-2875 — not re-described here. Three independent inject POSTs expected,
one per queued message.

## Known Defects Found During Exploration
None found. Same cosmetic queue-count-text drift as ELITEA-2875 (middot vs.
en dash) — covered by the single family-wide clarification issue referenced
in ELITEA-2875's Automation Hints, not re-filed here.

## Blocked Steps
None.

## Automation Hints
- Shares the `midturn_injection_enabled` fixture with ELITEA-2875/2877/2878 —
  implement once, reuse across the family.
- Send the three interjections back-to-back via `chat-inject-button` with
  only a short settle wait (~200-300ms) between clicks, not a long delay —
  confirmed live this still reliably reaches 3 queued items before any of
  them drains (the model's ~5-6s response time comfortably outlasts 3 rapid
  clicks).
- Reuse `wait_for_ai_response()`/`wait_for_message_content_stable()` for the
  final drain wait; poll on `interjection-composer`/`interjection-queue-area`
  counts reaching 0 as the "fully drained" signal (confirmed reliable live).
