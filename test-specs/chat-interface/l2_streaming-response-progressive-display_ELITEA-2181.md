# Test Case: Chat – Streaming Response Displayed While LLM Generates Output

## Metadata
- **TMS ID**: ELITEA-2181
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login (dev-token user renders as "Test Bot"/"TB")
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — case executed end-to-end live, four times (via a from-scratch `sync_playwright` scratch script reusing the project's own `page`/`conversation_id`/`auth_state` fixtures — no Playwright MCP server was wired in this session, see § Automation Hints), across all 9 steps. One CLARIFICATION filed (issue #1100): the case's literal "spinning loading circle" / bubble-level "Pause scroll" wording does not match the live widget shape (see step 2/4 notes below) — treated as case-text drift (reverse-masking guard), not a defect; this AFS specs the ACTUAL live contract. Several interactive elements this case touches have **no testid today** (model-name chip, Pause/Resume-scroll toggle, pre-content loading placeholder, Copy button, Regenerate button) — flagged `testid needed` in § Concrete Handles, per `.agents/role-overrides.md` (missing testid is implementer work, not a reason to downgrade or soften to a MINOR defect).

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- User has an open conversation (a fresh, empty conversation is sufficient — no prior messages required; confirmed live via the `conversation_id` fixture's freshly-created conversation).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Message text (case's literal Test Data value): `"Write a long poem about the city"`.

### generate-per-test (created in test setup, cleaned up in its own teardown)
- Fresh conversation via the existing `conversation_id` API fixture (`fixtures/data_fixtures.py`) — no UI-driven creation needed for this case; the case only cares about ONE exchange's streaming behavior, not conversation-list state.

## Test Steps

1. Navigate to the conversation, type `"Write a long poem about the city"` into the message input (`chat-message-input`), and click Send (`chat-send-button`).
   - **Verify**: the user's message appears immediately as a new list item; `message_input.input_value()` is `""` immediately after send; `chat-send-button` is absent (see step 6 note — this is a general "hidden while input is empty" rule, not a streaming-specific one).
2. Verify a loading/in-progress indicator appears, followed by the model name once content starts arriving.
   - **Verify (CLARIFICATION — case-text drift, issue #1100, reverse-masking guard):** there is **no literal "spinning loading circle."** Live sequence, confirmed across 4 runs:
     1. Immediately after send, a text placeholder renders inside the answer area — one of `RotatingMessages.jsx`'s rotating phrases ("Waking the agent…", "Packing its tools…", …), with an opacity-wave animation (no `CircularProgress`/spinner icon anywhere in `RotatingMessages.jsx`, `ApplicationAnswer.jsx`, or `ApplicationThinkView.jsx`).
     2. Within ~2–3s, a "Thought for `<n>` secs" accordion appears below/in place of the placeholder (`ApplicationThinkView.jsx` → `ActionView.jsx`). **The model-name chip (e.g. "Anthropic Claude 4.5 Sonnet") renders INSIDE this accordion**, not in the message header (the header only shows the participant name — "Elitea" — and a relative timestamp, both pre-existing, no case-relevant assertion needed there).
     - Assert: the RotatingMessages placeholder text is present at t≈0 (any one of its 9 known phrases, case-insensitive substring match — do not assert an exact phrase, they rotate every 2s); the "Thought for …" accordion + model-name chip become visible within a generous timeout (confirmed live up to ~3s, budget 15s for CI headroom).
3. Verify the response text streams progressively (word by word or chunk by chunk), not all at once.
   - **Verify**: confirmed live — polling `ChatPage._extract_message_body(last_message)` (existing method) every 3s during generation shows monotonically growing text inside the "Thought…" accordion's tool-preview pane (observed growing from a title line, e.g. `"# Poem: The City's Pulse"`, to the full draft over ~30–50s in this environment's default participant, which used a file-writing tool to produce the poem — see § Automation Hints on why this run is comparatively slow and tool-mediated). Assert: two body-text samples taken ≥2s apart during the `isStreaming` window differ AND the second is a superset/extension of the first (never shrinks) — the standard progressive-streaming signature, robust to whichever participant/tool path the environment's default agent takes.
4. Verify a "Pause scroll" button/control appears at the bottom-right area during streaming.
   - **Verify (CLARIFICATION, issue #1100):** confirmed present, but scoped to the SAME "Thought…" accordion from step 2/3 (`ActionView.jsx:471-483`), not a bubble-level or page-level control. Text reads exactly `"Pause scroll"` while `autoScrollEnabled` is true. Absent before the accordion's streamed content begins and absent again once streaming ends (see step 7). Confirmed via `page.get_by_text("Pause scroll", exact=False)`.
5. Click "Pause scroll" and verify auto-scroll stops.
   - **Verify**: confirmed live — clicking the control flips its own label to `"Resume scroll"` (`ActionView.jsx`'s `onToggleAutoScroll` toggles `autoScrollEnabled`; `page.get_by_text("Resume scroll")` count goes from 0→1, `"Pause scroll"` count goes 1→0 in the same click). **Automation caveat**: in this environment a single poem's streamed content fit entirely within the visible viewport (`scrollHeight == clientHeight == 610px` observed), so `chat_messages_scroll_container`'s `scrollTop` does not itself move regardless of the pause state — it is NOT a reliable secondary signal for THIS message length. The label-flip assertion above is the stable, sufaces-agnostic signal; if the implementer wants to additionally prove the scroll genuinely freezes, they'd need to force enough content to overflow (e.g. request an especially long poem) and compare `scrollTop` deltas pre/post-click during active streaming — optional, not required by this case's Pass/Fail criteria.
6. Verify the Send button is not visible during streaming.
   - **Verify (behavioral caveat, not a defect):** confirmed absent throughout streaming — but `chat-send-button` is unconditionally absent from the DOM whenever `message_input` is empty (confirmed via a baseline probe: `count()==0` with empty input BEFORE any message is sent, `count()==1`+`visible` the instant text is typed, `count()==0` again after clearing). Since the input stays empty for the whole exchange (user sent their message and typed nothing new), the button's absence during streaming is a special case of this general rule, not streaming-aware hide/show logic. Assert absence as specced by the case, but do not claim it proves streaming-specific behavior.
7. Wait for streaming to complete; verify the loading indicator disappears and "Pause scroll" is gone.
   - **Verify**: confirmed — existing `ChatPage.wait_for_ai_response()`/the raw `[data-testid="message-copy-button"], button[aria-label="Copy to clipboard"]` visibility signal (whichever resolves live — see § Concrete Handles note on stale testid) marks completion; at that same instant, `page.get_by_text("Pause scroll")` count is 0 and no `[role="progressbar"]`/`RotatingMessages` element remains. Completion observed between ~34s–54s across 4 runs for a full poem (see § Automation Hints on timeout sizing).
8. Verify the Regenerate button and message action icons (speaker, copy, regenerate, delete) appear.
   - **Verify**: confirmed, but ALL FOUR icons require a **hover** over the message block first — none render unconditionally (existing `ChatPage.copy_message()`/`delete_message()` methods already hover before acting; this case is the first to assert simple VISIBILITY of the full icon row, not just click one of them). Live, hovering the last message reveals exactly: `chat-read-out-button` (the "speaker"/Read-out icon, testid confirmed), an unlabeled Copy icon (tooltip "Copy to clipboard", MUI auto-injects `aria-label="Copy to clipboard"` onto it — no `data-testid`), an unlabeled, unnamed Regenerate icon (**no aria-label AND no testid** — MUI's tooltip-driven aria-label injection did not reach it, likely because its `StyledTooltip` wraps a bare `<Box>` rather than the `IconButton` directly, unlike Copy/Delete — see `ApplicationAnswer.jsx:876-896`), and `chat-delete-button` (testid confirmed, no aria-label). "Regenerate" is the ONLY one of the four with neither a stable testid nor an accessible name today — flagged `testid needed` in § Concrete Handles.
9. Verify the input field becomes active again after completion.
   - **Verify**: confirmed — `message_input.is_editable()` is `True` immediately after the Copy button becomes visible (step 7's completion signal), with no additional wait needed.

## Expected Results
- All 9 steps pass as specced above, with the step-2/4 CLARIFICATION corrections (issue #1100): the "loading indicator" is a text placeholder → model-chip-bearing "Thought…" accordion, not a spinning circle; "Pause scroll" is scoped to that accordion, not the bubble/page.
- Response text streams progressively and monotonically during generation; Pause/Resume-scroll toggles correctly; Send button is absent (empty-input rule); post-completion the four action icons are present-on-hover and the input is editable again.
- One CLARIFICATION filed (issue #1100); no functional product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | Setup | `auth_state` fixture | asserted |
| Precondition: user has an open conversation | — | Setup | `conversation_id` fixture | asserted |
| 1 Type message and click Send → User message appears; input cleared | message appears, input cleared | step 1 | `step 1`: new list item + `input_value()==""` | asserted |
| 2 Verify LLM response bubble appears with model name and spinning loading circle → Loading indicator visible | model name + loading indicator | step 2 | `step 2`: RotatingMessages placeholder then model-chip inside "Thought…" accordion | asserted *(clarification: no literal spinning circle — issue #1100, reverse-masking guard)* |
| 3 Verify response text streams progressively word by word or chunk by chunk → Streaming behavior visible | progressive streaming | step 3 | `step 3`: two ≥2s-apart body samples differ and grow monotonically | asserted |
| 4 Verify 'Pause scroll' button appears at bottom right during streaming → Pause scroll button visible | button visible | step 4 | `step 4`: `get_by_text("Pause scroll")` present during accordion streaming | asserted *(clarification: scoped to the reasoning/tool accordion, not bubble/page-level — issue #1100)* |
| 5 Click 'Pause scroll' and verify auto-scroll stops → Auto-scroll stops | auto-scroll stops | step 5 | `step 5`: label flips to "Resume scroll" | asserted *(scrollTop-delta proof needs an overflowing message — see step 5 caveat; not required by this case's Pass/Fail)* |
| 6 Verify Send button not visible during streaming → Send button hidden | button hidden | step 6 | `step 6`: `chat-send-button` count==0 throughout | asserted *(caveat: absence is the general empty-input rule, not streaming-specific — see step 6 note)* |
| 7 Wait for streaming to complete → Spinning circle disappears; 'Pause scroll' button gone | completion signals | step 7 | `step 7`: Copy button visible AND Pause-scroll count==0 | asserted |
| 8 Verify Regenerate button and action icons (speaker, copy, regenerate, delete) appear → Post-streaming actions visible | 4 icons visible | step 8 | `step 8`: hover last message, assert all 4 icon elements visible | asserted *(Regenerate has neither testid nor aria-label — flagged `testid needed`)* |
| 9 Verify input field becomes active again → Input field active | input active | step 9 | `step 9`: `message_input.is_editable()==True` | asserted |
| Expected Final State: "Streaming response works correctly with all indicators; input restored after completion." | — | steps 2–9 | as above | asserted |
| Pass/Fail: "All steps complete without errors; streaming works; all indicators correct; input restored." | — | all steps | as above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- `step 1` additionally asserts a BASELINE (before any message is sent/typed) that `chat-send-button` count is 0 with an empty input, and count is 1+visible the instant text is typed — *added: this is what makes step 6's "hidden during streaming" assertion honest rather than coincidental; without the baseline, a reviewer can't tell the two apart.*
- `step 3` asserts the growing text is a strict superset across polls (never shrinks) — *added: guards against a regression where the streamed preview gets replaced/reset mid-generation instead of appended, which would still show "changing text" but not genuine progressive streaming.*
- `step 7` cross-checks completion via TWO independent signals (Copy-button visibility AND Pause-scroll absence) rather than either alone — *added: observed these land within the same ~0.5s window across all 4 runs; asserting both catches a regression where one lags the other.*
- Console/network checked after every step across all 4 runs — *added: standard side-channel discipline; no new console errors or failed requests observed in this case's own flow (the default participant's tool-call path — file creation — completed cleanly).*
- (No console errors, no network errors, and no defects beyond the filed clarification were found — nothing else added beyond the case's own criteria.)

## Cleanup
1. Conversation is deleted via the `conversation_id` fixture's own teardown (existing pattern, `fixtures/data_fixtures.py`) — no case-specific cleanup needed since no separate entity was created.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder (`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`). Provenance verified via `git fetch origin` + `git grep` on both `origin/main` and `origin/automation/testids` in the sibling `EliteaUI` clone (2026-08-02).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Message input | `chat-message-input` | on-main ✓ | Existing `ChatPage.message_input`. |
| Send button | `chat-send-button` | on-main ✓ | Existing `ChatPage.send_button`. Rendered only while input is non-empty (see step 1/6 notes). |
| Last message container | `chat-message-item` | on-main ✓ | Existing `ChatPage.messages_container` (`.last`). Use `ChatPage._extract_message_body()` (existing static method) for progressive-text sampling — do not re-derive. |
| Answer content block | `chat-answer-content` **OR** `skill-test-last-response` (SAME element, value flips on `isLastMessage`) | on-main ✓ (both string literals present) | **Pre-existing tech debt, not introduced by this case** — `ApplicationAnswer.jsx:640`'s `Answer` component sets `data-testid={isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'}`, a same-element state-conditional testid value (the anti-pattern `.agents/testing.md` § Locator policy normally forbids for NEW code — this is existing code, flagged here, not fixed by this AFS). **For this case's single-exchange scenario the live value will be `skill-test-last-response`** (the message being asserted IS the last one) — the name is misleading (says "skill-test" though this is general chat, unrelated to the Skills feature). Do not rely on either literal string alone; prefer scoping through the parent `chat-message-item` (`messages_container.last`) instead, which is stable regardless of this flip. |
| Model-name chip (e.g. "Anthropic Claude 4.5 Sonnet") | **NO TESTID** | needs-adding | `testid needed: chat-answer-model-chip`. Renders inside the "Thought…" accordion's chip row (`ApplicationThinkView.jsx`'s `renderGroupChips` → `ActionView.jsx`). No `data-testid` anywhere in either file today. |
| "Thought for `<n>` secs" accordion header | **NO TESTID** | needs-adding | `testid needed: chat-answer-thought-accordion`. Useful as a scoping parent for the model chip / pause-scroll toggle once added (disambiguates from the separate `swarm-child-accordion-*` sub-accordions rendered for sub-agent responses, `ApplicationAnswer.jsx:606-632`, which this case doesn't touch). |
| "Pause scroll" / "Resume scroll" toggle | **NO TESTID** | needs-adding | `testid needed: chat-answer-pause-scroll-toggle`. `ActionView.jsx:471-483` — a `Typography` with `onClick={onToggleAutoScroll}`, text flips between the two labels. Currently only resolvable via `get_by_text("Pause scroll"/"Resume scroll", exact=False)`. |
| Pre-content loading placeholder | **NO TESTID** | needs-adding | `testid needed: chat-answer-loading-placeholder`. `RotatingMessages.jsx`, rendered by `ApplicationAnswer.jsx:951-961` while `(isLoading \|\| isRegenerating) && !answer && …`. Text cycles through 9 known phrases every 2s — assert PRESENCE of the wrapping element, not any specific phrase. |
| Copy-to-clipboard button | **NO TESTID** (aria-label present) | needs-adding | `testid needed: chat-copy-button` (sibling naming to the existing `chat-read-out-button`/`chat-delete-button` — do **not** reuse the page object's stale `message-copy-button` field name, which does not exist in source; it is dead-code tech debt, not a naming precedent). Currently resolvable ONLY via `button[aria-label="Copy to clipboard"]` (MUI auto-injects the label from the `StyledTooltip`'s `title` since the tooltip wraps the `IconButton` directly — `ApplicationAnswer.jsx:840-856`). |
| Regenerate button | **NO TESTID, NO aria-label** | needs-adding | `testid needed: chat-regenerate-button` (same sibling naming; again, do not reuse the stale `message-regenerate-button` page-object field name). `ApplicationAnswer.jsx:876-896` — the `StyledTooltip` here wraps a bare `<Box>`, not the `IconButton` directly, so MUI does NOT auto-inject the accessible name (confirmed live: hovering the message reveals 5 buttons total; this one alone has neither `aria-label` nor `data-testid`, unlike its Copy/Delete siblings). This is the ONLY one of the case's 4 action icons with zero stable handle today — highest-priority add for this case. |
| Delete button | `chat-delete-button` | on-main ✓ | Existing `ChatPage`'s `delete_message()` locates it positionally (`buttons.last`) rather than by this testid — **existing tech debt**, not introduced here; this case only needs to assert its VISIBILITY-on-hover, for which the testid is sufficient and should be used directly rather than the positional approach. |
| Read-out ("speaker") button | `chat-read-out-button` | on-main ✓ | Existing testid, not yet wired into `ChatPage` as a `LocatorDescriptor` field — add one (`read_out_button` already exists per `chat_page.py:287` — reuse it, confirm it points at this testid). |
| Messages scroll container | `chat-messages-scroll-container` | on-`automation/testids` only (awaiting human promotion to main) | Existing `ChatPage.chat_messages_scroll_container` / `get_messages_scroll_metrics()`. Note (step 5): `testId="chat-messages-scroll-container"` is a PROP, not a literal `data-testid=` string in the JSX — matches `.agents/workflow.md` § Closure record's documented prop-indirection grep caveat; confirmed present via the two-stage grep pattern, not the naive one. |

## Network Behavior
- No new REST calls beyond the standard `POST` that creates the AI response (participant/model selection already resolved by the time this case starts — out of this case's scope). The actual token stream arrives over **WebSocket**, consistent with `.agents/testing.md`'s documented ~2s+ delay pattern — this case's generation ran 34–54s end-to-end across the 4 live runs (default participant used a file-writing tool to produce the poem rather than a pure-text completion; see § Automation Hints).
- No console errors observed in any of the 4 runs for this case's own flow.

## Known Defects Found During Exploration
- **[CLARIFICATION, filed]** Issue #1100 — case text implies a literal spinning-circle loader and a bubble/page-level "Pause scroll" control; live product shows a text-cycling placeholder (`RotatingMessages`) followed by a model-chip-bearing "Thought…" reasoning/tool accordion, with "Pause scroll" scoped to that accordion. Reverse-masking guard applied — live behavior is intentional and reasonably matches the case's SPIRIT (an in-progress indicator + model attribution + a way to stop auto-scroll during a long stream); the case text is stale about the exact widget shape. See § Test Steps steps 2 and 4.
- No functional product defects found. "none" beyond the above.

## Blocked Steps
None. All 9 case steps were executed and observed end-to-end live, across 4 separate runs (to confirm step 5's toggle behavior and step 8's hover-reveal separately from the main streaming-timeline run).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- **No Playwright MCP server was wired in this analyst session** — exploration was driven via a from-scratch `sync_playwright`-backed pytest scratch file reusing the project's own `page`/`conversation_id`/`auth_state` fixtures (placed temporarily under `automation/tests/ui/chat/`, run directly, then deleted — never committed). The implementer should have normal MCP/CLI tooling; this is noted only so the discovered timings/behaviors are understood as coming from the SAME real Playwright browser context the suite already uses, not a different tool.
- **Timeout sizing**: this environment's default chat participant used a file-writing TOOL to produce the poem (visible via "I'll create this poem in a file for you." in the final answer, and a `chat-artifact-file-list` reference appearing post-completion in some runs) rather than a plain text completion, making full generation take 34–54s across 4 runs — size the "wait for completion" timeout generously (≥90s) to avoid environment-dependent flakiness; do NOT assume a short "Write a poem" prompt completes quickly on this environment's default participant.
- Wait strategy: condition-based only (`get_by_text(...).wait_for(state="visible")`, `expect().to_have_text()`, polling `_extract_message_body()`), never a fixed `sleep()`, per `.agents/testing.md`. The exploration script used `time.sleep()` for INSTRUMENTATION/observation only (printing state every N seconds) — this is not the pattern the real automated test should follow; the implementer should replace every such poll with a genuine Playwright wait/expect.
- Reuse `ChatPage.get_messages_scroll_metrics()` / `is_messages_scrollable()` (existing methods) if the implementer chooses to add the optional scrollTop-delta proof for step 5 (see step 5 caveat) — do not re-implement scroll-metric reading.
- Six new testids are needed for this case (`chat-answer-model-chip`, `chat-answer-thought-accordion`, `chat-answer-pause-scroll-toggle`, `chat-answer-loading-placeholder`, `chat-copy-button`, `chat-regenerate-button`) — all via `add-data-testid` on `EliteaUI/src/[fsd]/features/chat/ui/chat-box/ApplicationAnswer.jsx`, `src/components/Chat/ActionView.jsx`, and `src/components/RotatingMessages.jsx`. Scope is exactly these 6 elements (the ones this case's steps touch) — do not blanket-add testids to sibling elements in the same files that this case doesn't assert on (e.g. the "Show more"/"Show less" toggle, the "Copy to Messages" or "Edit response" icons, the swarm-child accordions).
