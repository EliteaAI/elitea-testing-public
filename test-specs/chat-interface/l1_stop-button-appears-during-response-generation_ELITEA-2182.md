# Test Case: Chat – Stop Button Appears During Response Generation

## Metadata
- **TMS ID**: ELITEA-2182
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l1 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **blocked** — reclassified from `ready-for-automation` after implementation. Case executed end-to-end live, twice on independent fresh conversations (ids `8837`, `8838`), via Playwright MCP against `localhost:5173`. **One CONFIRMED product defect filed** (issue #1569 — https://github.com/EliteaAI/elitea-testing-public/issues/1569 — "Stop wipes the entire message exchange, not just the streaming response"): clicking Stop wipes the entire message exchange (user prompt + AI reply) both client-side and server-side, not just the streaming response. The implemented test (commit `d2c3dcc23`, `test_stop_button_appears_during_response_generation`) was confirmed BROKEN by live investigation across multiple standalone re-runs — it fails in different observable ways run-to-run: deterministically `"Stop control should be gone once generation is cancelled: assert 1 == 0"` (2/2 in one investigation), and separately a React `"Maximum update depth exceeded"` console error — both downstream consequences of #1569's own broken Stop-handling, not a single stable single-cause signature. Per `.agents/role-overrides.md` § Declared-improvisation protocol ceiling and `.agents/testing.md` § Merge gate, a soft-assert/known-defect workaround is appropriate only for an ISOLATED assertion inside an otherwise-working test — NOT for a case's own headline/core subject observable, which this case's Step 2/3/5 (Stop control appears/disappears cleanly) IS. This is the same disposition already used by the sibling case ELITEA-2186 (`l2_regenerate-after-stopped-generation_ELITEA-2186.md`), same root-cause defect. The test was removed from `automation/tests/ui/chat/test_streaming_response.py`.
- **Not already-covered — a real gap.** `test_composer_send_button_toggles_with_empty_input_and_waveform_reappears` (merged on this batch's trunk, `tests/batch-chat-remaining-w12`, commit `27220fbb`) already proves that neither the Send button nor the waveform button render while streaming (`chat.send_button.count()==0` and `chat.voice_mode_button.count()==0`) — i.e. it proves a Stop-shaped control occupies that slot, by elimination. It does **not** click Stop, does not verify a Stop control is actually visible/enabled, and does not verify what happens when Stop IS clicked. That is this case's entire subject and is a genuine, unverified gap.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation. Live-confirmed: a fresh, API-seeded conversation (the existing `conversation_id` fixture, same one `test_streaming_response.py`'s own tests already use) is sufficient — no prior messages required.

## Test Data
- Case's literal Test Data value: `"generate a poem"`. Live-confirmed this environment's default participant answers "poem" prompts via a file-writing tool and can complete faster than a long-form prompt; either this or `test_streaming_response.py`'s own `MESSAGE_TEXT = "Write a long poem about the city"` reliably keeps the stream open long enough to click Stop mid-generation (confirmed live with `"generate a poem"` and, in a second repro, `"tell me a long story about a dragon"`).

## Test Steps

1. Open a fresh conversation; type the message and click Send (or press Enter).
   - **Verify**: the user's message appears in the transcript; generation starts (a loading/streaming indicator appears in the assistant's message slot).
2. While the response is generating, verify the Stop control is visible in the composer's send-button slot (replacing both the Send button and the waveform/"enter speaking mode" button — live-confirmed via `voice_mode_button.count()==0` AND `send_button.count()==0`, per the covering test's own Step 6 reasoning).
   - **Verify**: `send_button.count()==0`; `voice_mode_button.count()==0`; a Stop control (icon-only `BaseBtn`, `onClick={onStop}`, `UserInput.jsx` ~line 552-562) IS visible in that slot — **no `data-testid` today, see § Concrete Handles**.
3. Click the Stop control.
   - **Verify (KNOWN DEFECT — soft-assert, `# Known defect: #1569`)**: the message list still contains the user's sent message and the (now-interrupted) AI reply. **Live behavior**: BOTH vanish from the transcript — confirmed via a direct GET on the conversation's own REST endpoint (`GET /api/v2/elitea_core/conversation/prompt_lib/{project}/{conversation_id}?messages_limit=10&sort_order=desc`) returning `"message_groups_count":0,"message_groups":[]}` even after a full page reload. Reproduced 2/2 on independent fresh conversations.
4. Verify no further text streams after clicking Stop.
   - **Verify**: technically true (there is no message left to stream into — see Known Defect above), but this is a consequence of the defect, not an independent confirmation of a clean cancel. Assert via the message list's stable state (no growth) rather than treating this as proof the feature works as intended.
5. Verify the Stop control disappears and the default input bar (Send/waveform) is restored.
   - **Verify**: `voice_mode_button` becomes visible again (waveform reappears); this part of the flow works correctly and independently of the defect above.
6. Verify the input field is active and editable again.
   - **Verify**: `chat.message_input` is enabled (not `disabled`) and accepts new text (confirmed live by typing into it in the ELITEA-2183 follow-on flow — see that case's AFS).

## Expected Results
- A Stop control (not the idle-state Send/waveform pair) occupies the composer's send-button slot while a response streams.
- Clicking Stop halts the assistant's in-progress reply and restores the default input bar (Send-absent / waveform-visible, per empty input), with the input field re-enabled.
- **Per the case text, the already-sent user message and any partial AI content should remain in the transcript** — live product does NOT do this (see Known Defect).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in, open conversation | — | Setup | `conversation_id` fixture + `navigate_to_chat` | asserted |
| 1 Type message, click Send | User message appears; generation starts | AFS step 1 | step 1: message visible, streaming indicator visible | asserted |
| 2 Verify orange stop icon appears far right of input bar | Stop button visible | AFS step 2 | step 2: `send_button.count()==0`, `voice_mode_button.count()==0`, Stop control visible | asserted |
| 3 Click the orange stop button | Response generation stops immediately | AFS step 3 | step 3: click performed; soft-assert transcript persistence | `clarification`/known-defect (see below) |
| 4 Verify no further text streams after clicking stop | Streaming stopped | AFS step 4 | step 4: message list stable | asserted (weakened by defect — see notes) |
| 5 Verify stop button disappears and default input bar restored | Normal input bar visible | AFS step 5 | step 5: `voice_mode_button` visible again | asserted |
| 6 Verify input field is active and editable again | Input field active | AFS step 6 | step 6: `message_input` enabled | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Direct REST verification of the empty transcript after Stop (`conversation` GET endpoint, `message_groups_count:0`) — *added: the UI-only observation (empty list) could be a rendering glitch; the API cross-check (also required by `.agents/role-overrides.md` § 4xx/5xx-from-the-UI discipline in spirit — confirm via the contract, not just the DOM) proves the loss is server-side and persists across a full reload, which is what makes this a confirmed defect rather than a transient render race.*
- Reproduction on TWO independent fresh conversations (not one) — *added: a single occurrence risks being an environment fluke; 2/2 identical establishes the deterministic-single-cause criterion `.agents/testing.md` requires before treating a defect as sanctioned-RED / soft-assertable rather than a full `blocked`.*

## Fidelity Declaration
No substitutions. Every observable (message send, streaming indicator, Stop control visibility, the click itself, the resulting empty transcript, the restored input bar) is read from the live DOM in response to real user actions (`press_sequentially`/`.click()`) against the real DEV backend over the real WebSocket + REST stack — no `page.route`, no `page.evaluate` state injection, no mocked response. The one non-testid handle used during exploration (a raw CSS-class selector for the Stop button, since it has no `data-testid` yet) is explorer-only and does NOT belong in the shipped test — see § Concrete Handles for the required testid.

## Cleanup
`conversation_id` fixture owns creation/deletion of the seeded conversation (same mechanism `test_streaming_response_progressive_display` / `test_composer_send_button_toggles_with_empty_input_and_waveform_reappears` already rely on) — no additional cleanup needed.

## Concrete Handles (discovered during exploration)

Locator policy on this project is testid-only (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Stop control (composer footer, during streaming) | **testid needed: `chat-stop-generation-button`** | needs-adding | `UserInput.jsx` ~line 552-562 — bare `BaseBtn` with `onClick={onStop}`, zero testid today. Verified unique name (grepped EliteaUI `src/` — no existing `chat-stop*`/`stop-generation*` testid). This is implementer work per `.agents/role-overrides.md` § Analyst slot — NOT added by this analysis pass. |
| Waveform / "enter speaking mode" button | `chat-voice-mode-button` | on-`automation/testids` ✓ only (added by ELITEA-2179/2466's session, `EliteaAI/EliteaUI@b84f4f8d`) | Already a `LocatorDescriptor` in `ChatPage` (`voice_mode_button`, `chat_page.py:69`) — reused verbatim. |
| Send button | `chat-send-button` | on-`automation/testids` ✓ AND `main` ✓ | Pre-existing, reused (`chat.send_button`). |
| Message input | `chat-message-input` | on-`automation/testids` ✓ AND `main` ✓ | Pre-existing, reused (`chat.message_input`). |
| Message list container | `chat-message-item` (via `chat.messages_container`) | on-`automation/testids` ✓ AND `main` ✓ | Pre-existing, reused. |

## Network Behavior
- Step 1's Send fires the same conversation-creation/message flow the covering tests already document (`POST .../conversations/prompt_lib/...`, `PUT .../conversation/prompt_lib/.../{id}`, `POST .../select_conversation/...`) — the actual message content streams over the existing `socket.io` WebSocket connection (not a plain REST POST captured by request-listing tools), consistent with `.agents/architecture.md`'s "AI responses arrive over WebSocket ~2s after send".
- **Step 3's defect, confirmed via REST**: `GET /api/v2/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}?messages_limit=10&sort_order=desc` returns `"message_groups_count":0,"message_groups":[]` immediately after Stop AND after a full page reload — the loss happens server-side, not merely in the client render.

## Known Defects Found During Exploration
- **Issue #1569** — "[BUG][ELITEA-2182] Clicking Stop during generation wipes the entire message exchange (user prompt + AI reply), not just the streaming response." Filed against `EliteaAI/elitea-testing-public` (per `.agents/profile.md` § Bug filing). Deterministic (2/2), single-cause (clicking the Stop control), confirmed via the conversation's own REST contract. Dedup-checked before filing (no existing `bug`-labelled issue matched "stop"/"generation"/"message"/"history"/"wipe"/"clear"/"vanish" keywords in `EliteaAI/elitea-testing-public` — see § Bug filing dedup below).
- **Bug filing dedup performed**: `env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public --label bug --state all --limit 300 --json number,title,state`, keyword-matched locally against `stop|generat|cancel|poem|stream|message|history|wipe|clear|vanish|disappear|delete` — nearest hits (#655 Cancel-on-Artifact-form-navigation, #691 first-message-creates-new-conversation) are different bugs on different flows; no duplicate found.

## Blocked Steps
- **Step 2 onward.** The case's own headline subject — the Stop control's clean appearance during generation and clean disappearance/state-restore after being clicked (Steps 2, 3, 5) — is the direct surface of open defect #1569 (https://github.com/EliteaAI/elitea-testing-public/issues/1569). This is not "one isolable step at the tail" (`.agents/testing.md` § Merge gate, analysis-time entry) that could be soft-asserted while the rest of the flow is still meaningfully exercised — it IS the object every remaining step (Stop-control visibility, disappearance/restore, re-enabled input) is evaluating. Live implementation confirmed this via multiple standalone re-runs of the shipped test surfacing the defect two different ways (a deterministic `assert 1 == 0` on the Stop control's disappearance, and a React "Maximum update depth exceeded" console error) — not a single, stable, single-cause signature safe to merge sanctioned-RED. Routing per `.agents/role-overrides.md`: this AFS is `blocked` → lead → track against #1569; re-attempt once #1569 ships a fix.

## Automation Hints
No test ships for this case — it was implemented (commit `d2c3dcc23`), confirmed unreliable across multiple standalone re-runs (see § Status), and removed. When #1569 is resolved, re-run this analysis fresh before resuming from the hints below; the live product's post-fix Stop behavior may differ enough (e.g. what the Stop control's disappearance/restore sequence actually looks like) that a full re-exploration is warranted.

The handles and hints below are preserved for that re-attempt, not for immediate reuse:
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Suggested landing spot: a new test method in `automation/tests/ui/chat/test_streaming_response.py` (same file as the covering streaming/composer tests — shares the `conversation_id` fixture, timeout constants, and the `_is_known_secrets_403` console filter already defined there). A new dedicated file is also acceptable if the implementer judges the file is getting crowded; not a hard requirement.
- **Testid work required before implementation**: run `add-data-testid` to add `chat-stop-generation-button` to `UserInput.jsx`'s Stop `BaseBtn` (~line 558), then add `stop_generation_button = LocatorDescriptor(testid="chat-stop-generation-button")` to `ChatPage`.
- Reused verbatim: `chat.navigate_to_chat()`, `chat.send_message()` (or `message_input.press_sequentially()` + Enter, matching the covering test's own Step 3 idiom), `chat.send_button`, `chat.voice_mode_button`, `chat.message_input`, `chat.messages_container`, `chat.get_message_count()`.
- **Soft-assert pattern for step 3** (per `.agents/testing.md` § Merge gate, sanctioned-RED / analysis-time-entry shape):
  ```python
  soft_failures = []
  # ... click stop_generation_button ...
  if chat.get_message_count() < initial_count + 2:  # user + AI message expected to persist
      soft_failures.append(
          "# Known defect: https://github.com/EliteaAI/elitea-testing-public/issues/1569 — "
          "Stop wipes the message exchange instead of just cancelling the stream"
      )
  # ... continue asserting steps 5-6 as hard asserts ...
  if soft_failures:
      pytest.fail("\n".join(soft_failures))  # or expect.soft() aggregation per house pattern
  ```
  Follow whatever the file's existing soft-assert aggregation idiom is (check neighbouring specs in `tests/ui/chat/` for the house `soft_failures`/`expect.soft()` pattern before inventing one).
- Timing: reuse `test_streaming_response.py`'s existing `STREAM_GROWTH_TIMEOUT`/`AI_RESPONSE_TIMEOUT` constants for waiting on the streaming indicator to appear before clicking Stop — do not click Stop before the streaming indicator is confirmed visible (a race would make "Stop cancelled a real stream" unverifiable).
