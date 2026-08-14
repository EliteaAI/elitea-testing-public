# Test Case: Conversation starter chips appear in chat panel and are clickable

## Metadata
- **TMS ID**: ELITEA-1886
- **Linked Story**: none
- **Priority**: l2 (medium — per case frontmatter/header, both agree; same
  mapping precedent as the sibling `l2_welcome-message-is-shown-as-agent-bubble-before-first-user-message_ELITEA-1885.md`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}`=399
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login
  via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — all 8 case steps reproduced live
  end-to-end (agent form → add 2 starters → Save → chips visible in the
  embedded chat panel before any message → click a chip → pre-fills the
  input → explicit Send → agent responds). Zero console errors, zero 4xx/5xx
  across the whole interaction. **One new testid gap found** — the starter
  chips themselves (rendered inside the *embedded ChatBox* used on the Agent
  Detail page) have **no testid**; see § Concrete Handles and § Known
  Defects/Gaps. This is the UI's **agent-detail-page embedded chat**, a
  *different* React call site from the one ELITEA-2369 already covers (the
  standalone `/chat/{id}` "start new conversation" landing view) — see the
  Coverage Map / dedup note below for why this is fresh work, not
  `already-covered`.

## Dedup check (why this is NOT `already-covered`)
`test-specs/agent-hub/l3_agent-hub-start-conversation-with-starters_ELITEA-2369.md`
(merged, `automation/tests/ui/chat/test_agent_hub_start_conversation_with_starters.py`)
already automates "click a starter chip → pre-fill → Send → agent responds" —
but for a **different component**: it flows through Agent Hub Catalog → "Start
Chat" → the standalone `/chat/{id}` route, whose landing view is
`NewConversationView.jsx`, which renders starter tiles via its OWN call site of
the shared `EllipsisTextWithTooltip` (testid `chat-conversation-starter-tile`,
already wired). This case (ELITEA-1886) instead flows through the **Agent
Detail page's embedded chat** (`ChatBox.jsx`, mounted directly on
`/agents/all/{id}`), which renders starters via `ChatConversationStarters.jsx`
— a *different* call site of the *same* shared `EllipsisTextWithTooltip`
component, and this one is confirmed (source read,
`src/pages/NewChat/ChatConversationStarters.jsx`) to pass **no `testId` prop
at all**. Same visual concept, different, previously-unexercised code path,
different (currently missing) testid wiring — not the same observable, so
Rule-6 dedup does not apply. `automation/pages/chat_page.py` even documents
this exact split in a comment above `CHAT_STARTER_TILE` (lines 642-653):
"NOT `ChatConversationStarters.jsx`, a different call site consumed only by
the embedded `ChatBox.jsx` surface ... intentionally left unwired (out of
[ELITEA-2369's] executed code path, canon ruling #511)". This case is exactly
the one that exercises that left-unwired path.

Also checked: `grep -rl "conversation_starter_add_button\|add_conversation_starter"
automation/tests/` → only `test_agent_character_limits.py` (character-limit
behavior of the starter *input fields* in the agent form) and
`test_pipeline_create_full_details_persist.py` (unrelated pipeline case) — no
existing test asserts starter-chip visibility/click/pre-fill/response
behavior in the embedded chat.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available in the current project.
- **Test-data setup**: use `AgentAPI.create_agent_full()` with the
  `reasoning_effort: "none"` / no-`temperature` payload shape (same
  documented workaround as `lcritical_edit-agent-instructions-verify-persistence_ELITEA-1872.md`
  and `l2_welcome-message-is-shown-as-agent-bubble-before-first-user-message_ELITEA-1885.md`
  — the plain `agent_id` fixture / `AgentAPI.create_agent()` 400s against DEV,
  tracked as [#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)).
  Set `conversation_starters` directly in the creation payload (confirmed
  accepted field on the version object — see `data_fixtures.py`'s
  `_build_with_ai_agent_payload()` for the empty-list precedent):
  ```python
  payload = {
      "name": f"autotest_{request.node.name}"[:32],
      "description": f"Auto-created for test {request.node.name}",
      "type": "interface",
      "versions": [{
          "name": "base",
          "tags": [],
          "instructions": "You are a test agent.",
          "variables": [],
          "tools": [],
          "llm_settings": {
              "max_tokens": -1,
              "reasoning_effort": "none",
              "model_name": settings.default_model_name,
              "model_project_id": settings.default_model_project_id,
          },
          "conversation_starters": [
              "How do I create a new agent?",
              "What toolkits are available?",
          ],
          "agent_type": "openai",
          "welcome_message": "",
          "meta": {"step_limit": 25},
      }],
  }
  agent = agent_api.create_agent_full(payload)
  ```
  **Analyst's own exploration run used the UI form path instead** (this
  case's steps 1-3 literally exercise `AgentFormPage`'s Conversation
  Starters/"Chat starters" accordion, so both routes are legitimate — the
  API-payload route above is offered as a faster/cleaner option for the
  automated test to seed data without re-testing the form-fill mechanics
  that `test_agent_character_limits.py` already covers elsewhere); confirmed
  live against agent id `6732` (`elitea-1736-conversation-agent`, a
  pre-existing shared fixture agent) — both starters typed via the form,
  Saved, chips verified, then **removed again and re-Saved to restore the
  agent's original (no-starters) state** so no shared fixture pollution was
  left behind. **Implementer: do not reuse agent `6732`** — use a disposable
  agent per the payload above (or add starters via the form to a disposable
  agent) and delete it at teardown, matching `TestAgentActions`'s pattern in
  `automation/tests/ui/agents/test_agent_management.py`.

## Test Data

### Literal values
| Field | Value |
|-------|-------|
| Starter 1 | `How do I create a new agent?` |
| Starter 2 | `What toolkits are available?` |

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner`.
   - **Verify — PASSES.** Agent detail page loads. The "Chat starters"
     accordion section is present (case text calls it "Conversation
     Starters" — see § Known Defects/Gaps for this label drift). The
     embedded chat panel is already mounted with an empty message list — no
     separate "open chat" navigation exists on this route (same no-op note
     as ELITEA-1885's Step 1/4).
2. Click `agent-conversation-starter-add` twice (once per starter) and type
   each starter's text into the newly-added `agent-conversation-starter-input`
   field via `press_sequentially` (MUI React-onChange convention — confirmed
   `fill()` also works here per this run's live exploration, but
   `press_sequentially` is the project's standard and is what character-limit
   counter updates were confirmed against).
   - **Verify — PASSES.** Both starter texts appear in their respective
     input fields; character counter (`agent-conversation-starter-counter`)
     updates per field. **Also observed (Axis 2, matching the ELITEA-1885
     welcome-message precedent):** the embedded chat panel's starter-chip row
     renders **live, reactively, on every keystroke** — before Save. This is
     not itself the case's pass criterion (which is about the *saved* state
     reachable via steps 4-5) but the implementer should not mistake this
     pre-Save live-preview for the persistence proof point.
3. Click `agent-save-button` and wait for network idle.
   - **Verify — PASSES.** `PUT /api/v2/elitea_core/application/prompt_lib/399/{agent_id}`
     returns `201 Created`. Save/Discard buttons become disabled (no unsaved
     changes). Zero console errors.
4. (Full-navigation reload recommended, mirroring ELITEA-1885's pristine-state
   discipline) Reload `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` to
   get a clean "before any user message" state with no synthetic input
   carried over from step 2's live-preview render, and to independently
   re-verify persistence (case's Save-then-reopen intent). This is
   effectively "open a new chat session with this agent" on this route — the
   embedded chat is always freshly mounted on load, matching the case's
   step 4 language.
   - **Verify — PASSES.** Page reloads; `GET
     /api/v2/elitea_core/application/prompt_lib/399/{agent_id}` → `200 OK`,
     `version_details.conversation_starters` contains both literals. Chat
     message list is empty (no messages sent yet).
5. Verify both starter chips are visible in the chat panel before any message
   is sent.
   - **Verify — PASSES.** Two chip elements render inside the embedded chat
     area (`ChatConversationStarters.jsx`'s `EllipsisTextWithTooltip` items),
     each showing one starter's exact literal text, above the message
     input, with no message yet in `chat-message-list`. **Currently
     locatable only by visible text** — see § Concrete Handles for the
     testid gap.
6. Click one starter chip (e.g. "How do I create a new agent?").
   - **Verify — PASSES.** Click handled without error (`ChatBox.jsx`'s
     `onSendConversationStarter` fires — confirmed via source read,
     `src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx:1853`).
7. Verify the starter text is submitted as a pre-filled value in the input.
   - **Verify — PASSES.** `chat-message-input`'s value equals the clicked
     starter's exact text. **Also observed (Axis 2):** the click ONLY
     pre-fills — it does **not** auto-send. The starter-chip row disappears
     immediately on click (`ChatBox.jsx`'s `hasStarterBeenSent` flag flips to
     `true` the instant a chip is clicked, hiding
     `conversation_starters={hasStarterBeenSent || isTheUserChattingNow ? []
     : conversationStarters}` — confirmed via source read, same file lines
     2359-2362), regardless of whether a message is actually sent
     afterward. No message appears in `chat-message-list` yet at this point
     — the case's step 7 wording ("submitted as a pre-filled") describes
     exactly this pre-fill-only behavior, not an actual chat submission.
8. Click `chat-send-button` to submit the pre-filled message, then verify the
   agent responds.
   - **Verify — PASSES.** `POST /api/v2/elitea_core/conversations/prompt_lib/399`
     → `201 Created`. A user message item appears in `chat-message-list`
     with the starter's exact text, followed by an agent response item
     (`skill-test-last-response`/`chat-answer-content`, contextually
     relevant reply to the clicked starter's question, confirmed live —
     model `Anthropic Claude 4.5 Sonnet`). Zero console errors, zero
     network 4xx/5xx across the whole send→respond cycle. **Note: this
     explicit Send click is not a literal case step** — the case's own step
     list (6 → click chip, 7 → verify pre-fill, 8 → verify response) has no
     separate "click Send" step, but the pre-fill-only behavior confirmed in
     step 7 makes an explicit Send click the only way to reach step 8's
     "agent responds" — same decomposition ELITEA-2369's automated test
     already uses for the sibling starter-tile flow (`chat.send_button.click()`
     between its starter-click and its `wait_for_ai_response()`).

## Expected Results
- Both conversation starter chips are visible in the embedded chat panel
  before any message is sent, showing their exact configured text.
- Clicking a chip pre-fills the chat input with that starter's exact text and
  hides the starter-chip row (one-shot; does not reappear even if Send is
  never clicked).
- Sending the pre-filled message produces a real agent response, rendered via
  the normal agent-message code path.
- No console errors or 4xx/5xx network responses at any step.
- `PUT .../application/prompt_lib/{project}/{agent_id}` returns `201` on
  Save; `POST .../conversations/prompt_lib/{project}` returns `201` on send.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture | n/a (fixture-level) | asserted |
| Precondition: existing agent available | Agent detail page reachable | Test-data setup (`create_agent_full()`) | agent created, id returned | asserted |
| Step 1: navigate to agent detail page | Page loads | Step 1 | page title, section presence | asserted |
| Step 2: add both starters | Both entered in the field | Step 2 | input `.input_value()` per field, counter update | asserted |
| Step 3: click Save | Save completes | Step 3 | PUT response `201`, zero console errors | asserted |
| Step 4: open a new chat session with this agent | New chat session opens | Step 4 | full reload → freshly-mounted embedded chat, empty message list (no separate "open chat" action exists on this route) | asserted *(no-op-by-design, same as ELITEA-1885 Step 1/4)* |
| Step 5: both chips visible before any message | Both chips displayed | Step 5 | 2 chip elements present, empty `chat-message-list`, text matches literals | asserted |
| Step 6: click one starter chip | Chip is clicked | Step 6 | click succeeds, no error | asserted |
| Step 7: starter text submitted as pre-filled in input | Text appears in input | Step 7 | `chat-message-input.input_value()` equals clicked starter's text | asserted |
| Step 8: agent responds to the clicked starter | Agent response rendered | Step 8 (decomposed — adds an explicit Send click not itemized in the case text) | `POST .../conversations/...` `201`, agent message item appears in `chat-message-list` | asserted *(decomposed)* |
| Pass criterion: "all steps complete without errors" | No errors at any step | Steps 1-8 | console error check at each step (all zero) | asserted |
| Fail criterion: "chips absent / not clickable / no pre-fill / no response" | n/a (negative condition) | Steps 5-8 | presence/count assertions (absent would fail step 5); click+value assertions (not-clickable/no-pre-fill would fail steps 6-7); response assertion (no-response would fail step 8) | asserted |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Starter chips render live in the embedded chat preview on every keystroke, before Save | Discovered during exploration — mirrors the same live-preview behavior already documented for the welcome message (ELITEA-1885); flagged so the implementer doesn't mistake the pre-Save preview for the persisted-state proof point |
| Clicking a chip is pre-fill-only (no auto-send) and hides the chip row immediately, even if Send is never clicked | Confirmed via source read (`ChatBox.jsx`'s `onSendConversationStarter` + `hasStarterBeenSent` flag) and live click — the case's step 7/8 split only makes sense once this mechanic is understood; without it, an implementer might assume step 6's click alone should also produce a response |
| Zero console errors across the whole add-starters → Save → reload → click-chip → Send → response cycle | Silent-error check per project convention |
| Zero network 4xx/5xx across the same cycle | Same silent-failure discipline as the console check — a chip click or Send that silently 4xx's would otherwise look identical to success in the DOM |
| Agent's response is contextually relevant to the specific starter clicked (not a generic/error fallback) | Confirmed live — the response engaged with "How do I create a new agent?" specifically (asked clarifying questions about agent type), ruling out a stub/placeholder response |

## Cleanup
1. Analyst's live-exploration run added the two starters to the **shared**
   fixture agent `elitea-1736-conversation-agent` (id `6732`) via the UI form,
   Saved, verified all 8 steps, then **deleted both starters and re-Saved**
   to restore the agent to its original (no-starters) state. Confirmed via a
   final snapshot: Save/Discard buttons both `disabled` (no unsaved diff)
   and the "Chat starters" section shows only the empty "add" state.
2. **For the implementer:** do not repeat this pattern against a shared
   fixture agent — create a disposable agent (via `AgentAPI.create_agent_full()`
   with `conversation_starters` pre-populated, see Preconditions) and delete
   it at teardown, matching `TestAgentActions` in
   `automation/tests/ui/agents/test_agent_management.py`.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| "Chat starters" accordion section | `agent-conversation-starters-section` (`AgentFormPage.conversation_starters_section`) | pre-existing. **Note:** the field's testid/description still says "conversation-starters" but the rendered accordion label reads "Chat starters" — case-text drift already baked into the pre-existing page object's docstring, not a new finding; case text saying "Conversation Starters field" matches the testid semantics, not the visible label. Not filing separately — cosmetic, does not affect automation. |
| Add-starter button | `agent-conversation-starter-add` (`AgentFormPage.conversation_starter_add_button`) | pre-existing |
| Starter input field(s) | `agent-conversation-starter-input` (`AgentFormPage.conversation_starter_inputs`) | pre-existing |
| Starter char counter | `agent-conversation-starter-counter` (`AgentFormPage.conversation_starter_counter`) | pre-existing |
| Save button | `agent-save-button` | pre-existing |
| Embedded chat message input | `chat-message-input` (`AgentDetailPage.chat_message_input`) | pre-existing |
| Embedded chat send button | `chat-send-button` (`AgentDetailPage.chat_send_button`) | pre-existing |
| Embedded chat message list container | `chat-message-list` (`AgentDetailPage.chat_message_list`) | pre-existing |
| Each message item | `chat-message-item` / `CHAT_MESSAGE_ITEM_SELECTOR` | pre-existing |
| Agent-answer body (last/only message) | `skill-test-last-response` (`AgentDetailPage.skill_test_last_response`) | pre-existing — same grandfathered state-ternary noted in ELITEA-1885's AFS, not this case's element to fix |
| **Starter chip in the embedded chat (THIS case's actual target element)** | **`testid needed: chat-conversation-starter-tile`** on `ChatConversationStarters.jsx`'s `<EllipsisTextWithTooltip>` call site (`src/pages/NewChat/ChatConversationStarters.jsx`, renders the shared `EllipsisTextWithTooltip` from `src/components/ConversationStarters.jsx` without a `testId` prop — confirmed via source read). **Reuse the exact same literal `chat-conversation-starter-tile`** already wired on the *sibling* call site in `NewConversationView.jsx:1020` (`testId="chat-conversation-starter-tile"`, confirmed live/source, backs ELITEA-2369's `ChatPage.CHAT_STARTER_TILE`) — same visual/functional concept ("a clickable conversation-starter tile in a chat area"), and the two call sites never render on the same page simultaneously (`/chat/{id}` standalone route vs. `/agents/all/{id}` embedded chat), so there is no collision risk in sharing the literal. Implementer: run `add-data-testid` to add `testId="chat-conversation-starter-tile"` to the `<EllipsisTextWithTooltip>` call at `ChatConversationStarters.jsx`'s render (mirroring the prop already used one file over in `NewConversationView.jsx`), then add a matching page-object handle on `AgentDetailPage` (e.g. `CHAT_STARTER_TILE` UPPER_CASE constant identical to `ChatPage.CHAT_STARTER_TILE`, or better — hoist the constant to a shared location both pages import, since it is now genuinely the same handle on two pages). Until added, steps 5-6 have **no stable handle** — do not ship a text-only/role-only fallback per the project's testid-only locator policy; this AFS's `ready-for-automation` status is contingent on the implementer doing this add-data-testid work first. **Precedent/caution (qa-engineer memory, ELITEA-2369/PR #1235):** this exact pair of call sites has a documented history of wrong-call-site wiring AND an orphan-testid leftover from a prior correction — after that PR's fix rounds, the verified-correct end state is `NewConversationView.jsx` wired / `ChatConversationStarters.jsx` unwired (matches this run's fresh source read). When the reviewer verifies this case's implementation, re-run `git grep -n "chat-conversation-starter-tile" origin/automation/testids -- src/` fresh (per that memory's reusable check) rather than trusting a "wired at the correct call site" claim — confirm it now appears at exactly the two intended call sites (`NewConversationView.jsx` pre-existing + `ChatConversationStarters.jsx` newly added by this case), not a stray third location. | **needs-adding** |

**Resolved during implementation (2026-08-07):** `testId="chat-conversation-starter-tile"`
added to `ChatConversationStarters.jsx`'s `<EllipsisTextWithTooltip>` call
(EliteaAI/EliteaUI `automation/testids` commit `afb48435`). Fresh
`git grep -n "chat-conversation-starter-tile" origin/automation/testids -- src/`
(post-fetch) confirms exactly the two intended call sites — `NewConversationView.jsx:1020`
(pre-existing) + `ChatConversationStarters.jsx:39` (this case's addition) — no stray
third location. `AgentDetailPage.CHAT_STARTER_TILE` + `get_chat_starter_tiles()` /
`click_chat_starter_tile()` added (duplicated-field shape, mirroring how
`chat_message_input`/`chat_send_button` are already duplicated between `ChatPage` and
`AgentDetailPage` for their respective routes — not hoisted, since the two classes share
no common ancestor besides `BasePage`).

## Network Behavior
- `PUT /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` —
  fires on Save click, `201 Created` on success (confirmed this run).
- `GET /api/v2/elitea_core/application/prompt_lib/{project_id}/{agent_id}` —
  fires on page load/reload, `200 OK`, returns
  `version_details.conversation_starters` which `ChatBox.jsx` reads to seed
  the starter-chip row.
- `POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}` — fires on
  Send click, `201 Created` on success (confirmed this run — new conversation
  created carrying the pre-filled starter text as the first user message).

## Known Defects Found During Exploration
None — no functional defect. One **testid gap** (see § Concrete Handles,
`chat-conversation-starter-tile` needed on `ChatConversationStarters.jsx`) —
this is implementer work per `.agents/role-overrides.md` § Analyst slot
("Do not soften a testid demand into a MINOR defect or a note; it is
implementer work, and the AFS is its work order"), not a bug ticket. One
**minor label-text observation** (case text says "Conversation Starters
field", live UI accordion label reads "Chat starters") — already reflected
in a pre-existing page-object testid/description, not a new drift to file;
noted for completeness only, no action needed.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, `.agents/testing.md`).
- Page objects: `AgentFormPage` (starter add/input/counter, inherited by
  `AgentDetailPage`) + `AgentDetailPage`'s embedded-chat testids
  (`chat_message_input`, `chat_send_button`, `chat_message_list`,
  `chat_message_item`) already cover everything except the starter-chip
  element itself (needs-adding, see Concrete Handles).
- Test-data setup: use `AgentAPI.create_agent_full()` with
  `conversation_starters` pre-populated in the payload (see Preconditions) —
  avoids re-driving the form-fill mechanics that `test_agent_character_limits.py`
  already exercises, and sidesteps reusing/mutating a shared fixture agent.
  If the implementer prefers to exercise the form-fill UI path instead (to
  keep steps 1-3 as literal UI actions matching the case text), that is
  equally valid — this run confirmed both work — but MUST use a disposable
  agent either way.
- Wait strategy: after Save, wait for network idle (`PUT .../application/...`
  settling) before reload; after reload, wait for the chip row to be visible
  (once `chat-conversation-starter-tile` exists) before asserting chip count
  — the row populates from the `GET .../application/...` response, which
  lands slightly after the shell renders (same pattern as ELITEA-1885's
  welcome-message timing note).
- Sequencing for steps 6-8: click chip → assert `chat-message-input` value
  equals the clicked starter's text (step 7) → click `chat-send-button` →
  `wait_for_ai_response()`-style wait (per project convention, no sleeps) →
  assert an agent message item appears (step 8). Mirrors
  `test_agent_hub_start_conversation_with_starters.py`'s existing
  click-tile → assert-input → click-send → wait-for-response sequencing for
  the sibling `/chat/{id}` flow.
- Disambiguating which chip was clicked: use `.filter(has_text=...)` against
  the (to-be-added) `chat-conversation-starter-tile` locator, same idiom as
  `ChatPage.click_chat_starter_tile()`'s `CHAT_STARTER_TILE` usage.
