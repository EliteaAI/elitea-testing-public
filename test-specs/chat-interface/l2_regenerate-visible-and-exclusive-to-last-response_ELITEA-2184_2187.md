# Test Case: Chat – Regenerate Is Visible Only On The Last LLM Response (family: ELITEA-2184 + ELITEA-2187)

## Metadata
- **TMS IDs**: ELITEA-2184 ("Chat – Regenerate Button Visible on Last LLM Response"), ELITEA-2187 ("Chat – Regenerate Is Only Available on the Last Response Not on Earlier Messages")
- **Family AFS**: yes — both cases assert the identical live contract (Regenerate + Delete render ONLY on the last AI message; Copy/Read-out render on every AI message). ELITEA-2187 additionally asserts that clicking Regenerate on the last response triggers a new generation, which ELITEA-2184 does not touch. Differ only in required message-pair count (2184: "at least one LLM response"; 2187: "at least 3 message-response pairs") — a single 3-exchange conversation satisfies both.
- **Linked Story**: none (both cases `requirements: []`)
- **Priority**: l2 (case priority: high, both)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: **ready-for-automation** — both cases executed live end-to-end this session, against a from-scratch conversation driven via Playwright MCP (`http://localhost:5173/chat/8834`, a pre-existing multi-exchange conversation reused for the visibility probe, plus a same-session fresh send/regenerate cycle to confirm the click behavior). Root-cause confirmed via DOM `querySelectorAll` counts, not just a11y-tree hover snapshots (see § Automation Hints) — `chat-regenerate-button`/`chat-delete-button` testids exist in the DOM **only** for the message where `isLastMessage === true`; `chat-copy-button`/`chat-read-out-button` exist on every AI message. This makes the "exclusive to last" assertion a **deterministic testid-count check**, not a hover-visibility race.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- **ELITEA-2184**: a conversation with at least one LLM response exists.
- **ELITEA-2187**: a conversation with at least 3 message-response pairs exists.
- Implementation note: both are satisfied by ONE fresh conversation with 3 short exchanges (see § Test Data) — the family's shared setup.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Fresh conversation via the existing `conversation_id` API fixture.
- Three short, quick-completing messages sent sequentially in the SAME conversation (short text keeps each real generation to single-digit seconds, confirmed live — see § Automation Hints): e.g. `"Hi"`, `"Hi again"`, `"One more hello"`. Content is not semantically load-bearing for this case (only presence/position of the resulting AI responses matters) — any short, distinct prompts are acceptable so long as each produces a genuine LLM completion.

## Test Steps (parameter table — one row per case)

| # | Action | Expected Result | ELITEA-2184 | ELITEA-2187 |
|---|--------|--------------------|---|---|
| 1 | Send 3 short messages sequentially; wait for each AI response to complete | 3 user/AI exchange pairs exist | required (as 2+ to exercise "earlier") | required (case's own 3-pair precondition) |
| 2 | Hover over an earlier (non-last) LLM response | No Regenerate button visible on that response | ✓ (step 3 in case text) | ✓ (step 1 in case text) |
| 3 | Hover over the last LLM response | Regenerate button + full action-icon row (speaker, copy, regenerate, delete) visible | ✓ (steps 1-2, 4 in case text) | ✓ (step 2 in case text) |
| 4 | Click Regenerate on the last response | New generation triggered correctly (Stop control appears in the composer's send-slot; the response content resets/streams) | — (not in case) | ✓ (step 3 in case text) |
| 5 | Wait for the triggered regeneration to complete | Regenerate + action icons reappear on the (still-last) message | — (not in case, but included so the test leaves clean, deterministic state rather than an in-flight generation) | added (Axis 2) |

## Expected Results
- Regenerate (and Delete) render **only** for the message where `isLastMessage === true` — confirmed via a direct DOM query (`document.querySelectorAll('[data-testid="chat-regenerate-button"]').length === 1`) returning exactly 1 regardless of how many AI messages exist in the conversation (3 in this family's setup), and that single match is always inside the LAST `chat-message-item`.
- Copy and Read-out render on **every** AI message (not last-exclusive) — same DOM query for `chat-copy-button`/`chat-read-out-button` returns a count equal to the number of AI messages.
- Clicking Regenerate on the last response (ELITEA-2187 step 3) triggers a real new generation: the composer's send-slot shows the Stop control (`chat-stop-generation-button`, reused from ELITEA-2182/2183) and the last message's content is replaced.
- No functional product defect found for either case.

## Coverage Map

### Axis 1 — Case coverage (ELITEA-2184)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: conversation with ≥1 LLM response | — | step 1 | 3-exchange conversation built in setup | asserted |
| 1 Scroll to the last LLM response → Last response visible | last response visible | step 3 | `expect(last_message).to_be_visible()` | asserted |
| 2 Hover over the last response → Regenerate + action icons (speaker, copy, regenerate, delete) visible | 4 icons visible | step 3 | hover last message; assert 4 scoped icon locators visible | asserted |
| 3 Hover over any earlier LLM response → No Regenerate visible | regenerate absent | step 2 | hover earlier message; assert regenerate locator scoped to that message has count 0 | asserted |
| 4 Verify Regenerate only on last response | exclusivity | steps 2+3 | DOM-wide `chat-regenerate-button` count == 1, located inside the last `chat-message-item` | asserted |
| Expected Final State: "Regenerate is visible only on the last response." | — | steps 2-3 | as above | asserted |
| Pass/Fail: "Regenerate visible only on last response." | — | all steps | as above | asserted |

### Axis 1 — Case coverage (ELITEA-2187)

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: conversation with ≥3 message-response pairs | — | step 1 | 3-exchange conversation built in setup | asserted |
| 1 Hover over any earlier LLM response (not the last) → No Regenerate text button visible | regenerate absent | step 2 | hover earlier message; assert regenerate locator scoped to that message has count 0 | asserted |
| 2 Hover over the last LLM response → Regenerate button and regenerate icon visible | regenerate visible | step 3 | hover last message; assert regenerate locator visible | asserted |
| 3 Click Regenerate on last response → New generation triggered correctly | generation triggered | step 4 | click regenerate; assert `chat-stop-generation-button` becomes visible (composer send-slot occupied) | asserted |
| Expected Final State: "Regenerate is exclusive to the last response." | — | steps 1-2 | as above | asserted |
| Pass/Fail: "Regenerate only on last response." | — | all steps | as above | asserted |

### Axis 2 — Analyst additions

- Both cases' "visible"/"not visible" assertions are strengthened from a single hover-then-visibility check into a **DOM-wide testid-count check** (`querySelectorAll('[data-testid="chat-regenerate-button"]').length === 1`) — *added: this proves exclusivity structurally (the element genuinely does not exist for earlier messages, confirmed live via direct DOM inspection this session) rather than merely proving it's not currently painted/hovered, which is a weaker and more hover-timing-fragile signal.*
- ELITEA-2187 step 3's "new generation triggered correctly" is additionally waited out to full completion (Regenerate/action icons reappearing on the same, still-last message) rather than left in-flight — *added: an in-flight generation left un-awaited at test end is a source of cross-test interaction (the fixture's conversation-delete teardown racing a live generation); waiting for completion is standard project practice (`.agents/testing.md` "wait, never a sleep") and leaves deterministic end state.*
- **Added during implementer fix round 1 (review finding), documented here retroactively — was already in code but undocumented:** ELITEA-2187's completion check also HARD-asserts the regenerated body text differs from the pre-regenerate text (`assert post_click_body != pre_click_body`) — *added: a Regenerate that no-ops and resurfaces cached/identical text would otherwise pass this test green on the Stop-control-visible check alone; a same-vs-different comparison catches it. A rare coincidental identical LLM repeat on a short greeting prompt is accepted ordinary test flakiness, not a reason to weaken the assertion (same rationale as the sibling ELITEA-2185 AFS's Axis 2).*
- Console/network checked after the full flow — no new errors observed for either case's own actions.

## Cleanup
1. Conversation deleted via the `conversation_id` fixture's own teardown.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy: testid-only (`.agents/testing.md` § Locator policy). Provenance verified via `git fetch origin` + `git grep` on both `origin/main` and `origin/automation/testids`.

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Message item container | `chat-message-item` | on-main ✓ | Existing `ChatPage.messages_container`, `.nth(i)`. |
| Regenerate icon | `chat-regenerate-button` | on-main ✓ (ELITEA-2181) | Existing `ChatPage.regenerate_action_button` (page-wide field — safe to use bare only when exactly 1 AI message is in view; this family needs a message-SCOPED variant too, since 3 AI messages share the `chat-copy-button`/`chat-read-out-button` testids — see Automation Hints). |
| Delete icon | `chat-delete-button` | on-main ✓ | Existing `ChatPage.delete_action_button`. Same last-message-exclusivity as Regenerate (confirmed live this session — not previously documented as exclusive; see Automation Hints). |
| Copy icon | `chat-copy-button` | on-main ✓ (ELITEA-2181) | Existing `ChatPage.copy_action_button`. Renders on EVERY AI message (not last-exclusive) — confirmed live this session (3-message-item DOM query returned 2 matches for a 2-AI-message conversation). |
| Read-out icon | `chat-read-out-button` | on-main ✓ | Existing `ChatPage.read_out_button`. Same non-exclusive rendering as Copy. |
| Stop-generation control | `chat-stop-generation-button` | on-`automation/testids` (ELITEA-2182/2183; check current promotion state at implementation time) | Existing `ChatPage.stop_generation_button` — reused as the "new generation triggered" signal for ELITEA-2187 step 3 (same control that appears for a fresh Send, confirmed live to also appear for Regenerate). |

## Network Behavior
- Regeneration triggers the same WebSocket-streamed response contract as a normal Send (no new REST endpoint observed).
- No console errors observed in this session's exploration for either case's own flow.

## Known Defects Found During Exploration
- None for either case. (A DIFFERENT, already-filed defect — #1569, "Stop wipes the entire message exchange" — was independently re-confirmed this session while exploring the sibling case ELITEA-2186; it does not affect ELITEA-2184/2187, which never invoke Stop.)

## Blocked Steps
None. All steps for both cases executed and observed live this session.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **Family implementation as ONE spec file, two `test_` functions** (not a single parametrized function — the two cases' assertion sets diverge at ELITEA-2187's step 3 click-and-wait, which ELITEA-2184 does not have) sharing a suite-local setup helper for "send 3 short messages, wait for each" (Hard Rule 7).
- **New page-object work needed**: the existing `regenerate_action_button`/`copy_action_button`/`read_out_button`/`delete_action_button` `LocatorDescriptor` fields resolve PAGE-WIDE (`page.get_by_test_id(...)`), which is safe for Regenerate/Delete (always exactly 1 match, confirmed live) but throws a Playwright strict-mode violation for Copy/Read-out once 2+ AI messages are present (their testid is NOT last-message-exclusive). Add class-level UPPER_CASE scoped-selector constants (same idiom as the existing `MESSAGE_SENDER_NAME`/`MESSAGE_SENDER_AVATAR` constants) so a specific message's action row can be queried without page-wide ambiguity, e.g. `REGENERATE_ACTION_BUTTON = '[data-testid="chat-regenerate-button"]'` chained off `messages_container.nth(i)`. Do not build raw selectors inline in the test file (`.agents/testing.md` § Locator policy).
- **Fastest reliable "new generation triggered" signal** (ELITEA-2187 step 4): `chat.stop_generation_button` becoming visible — confirmed live this session to reuse the identical control/testid as a normal Send's mid-stream state, not a separate "regenerating" indicator.
- Short message text (`"Hi"`, `"Hi again"`, `"One more hello"`) keeps each of the 3 exchanges to single-digit seconds in this environment (confirmed live — none of the 3 invoked the file-writing tool that makes longer/creative prompts like "write a poem" take 34-54s per `.agents/testing.md`'s existing "Unconfirmed" note). Do not reuse the poem-prompt timeout sizing for this family; `AI_RESPONSE_TIMEOUT` can stay at the project's standard generous value (120s) for CI headroom without materially slowing the suite.
- Wait strategy: condition-based only, per `.agents/testing.md`.
