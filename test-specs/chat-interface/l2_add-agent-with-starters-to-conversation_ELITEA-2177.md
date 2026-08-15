# Test Case: Chat – Add Agent with Conversation Starters to Conversation

## Metadata
- **TMS ID**: ELITEA-2177
- **Linked Story**: none
- **Priority**: l2 (medium — per case frontmatter)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend), project `Private` (`${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-2178, ELITEA-2465
- **Status**: `ready-for-automation` — all 6 case steps reproduced live end-to-end
  against an **existing** conversation (`/chat/{id}`, not a fresh/new-conversation
  landing view): opened an existing conversation, added an agent with
  conversation starters via the composer's "+" (plus menu) → Agents flow,
  verified 2 starter tiles rendered above the input (case allows up to 4;
  this environment's disposable agent had exactly 2 configured — case text
  says "max 4", not "exactly 4"), hovered a genuinely-truncated starter and
  confirmed the tooltip shows the full text, clicked the literal case-text
  starter ("here is your task: Explain Exponential Backoff") to populate the
  composer, confirmed the text is editable and the agent chip/version stayed
  visible, clicked Send, and confirmed a full agent response rendered with the
  model-name chip and an expanded "Thought for …" accordion. Zero console
  errors beyond the project's standing sanctioned `secrets 403` noise
  (`.agents/testing.md` known-noise entries), zero unexpected 4xx/5xx.

## Dedup check (why this is fresh work, not already-covered/extend-existing)
Grepped `test-specs/` and `automation/tests/` for prior conversation-starter
coverage:
- `test-specs/agent-hub/l3_agent-hub-start-conversation-with-starters_ELITEA-2369.md`
  (merged, `test_agent_hub_start_conversation_with_starters.py`) covers
  **starting a brand-new conversation** from the Agent Hub Catalog modal's
  "Start Chat" button — renders via `NewConversationView.jsx`'s pre-first-message
  landing view, a DIFFERENT React call site from this case.
- `test-specs/agents/l2_conversation-starter-chips-visible-and-clickable_ELITEA-1886.md`
  (merged, `test_agent_embedded_chat_conversation_starter_chips.py`) covers the
  **Agent Detail page's embedded chat panel** (`/agents/all/{id}`) — a
  different mounting context of `ChatBox.jsx`.
- **This case's flow is neither**: it adds an agent as a participant to an
  **already-open, pre-existing `/chat/{id}` conversation** via the composer's
  "+" → "Agents" menu (`ChatPage.add_agent_participant()` /
  `PLUS_MENU_ITEM_SUFFIX` testids), which is the SAME `ChatBox.jsx` +
  `ChatConversationStarters.jsx` render path ELITEA-1886 wired the
  `chat-conversation-starter-tile` testid on (confirmed live — the same
  testid renders here too, since `/chat/{id}` also mounts `ChatBox.jsx`), but
  NO existing spec drives the "add an agent mid-conversation via + menu" entry
  point or the participants-panel "Agents" section it produces. Fresh coverage.
- Also checked `grep -rl "add_agent_participant" automation/tests/` — used by
  toolkit/skill tests (`test_agent_with_toolkit_chat.py`,
  `test_agent_with_github_toolkit.py`, `test_skill_conversation_interaction.py`,
  `test_ghost_skill_after_agent_removed.py`) for unrelated observables (toolkit
  calls, skill ghosting) — none assert conversation-starter behavior.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing conversation is open (any pre-existing conversation with at
  least one prior message works — the case's "open a conversation" step does
  not require a brand-new/empty one; confirmed live against a conversation
  that already had a system greeting exchange).
- An agent with configured conversation starters exists in the current project.

## Test Data

### Case-text drift (CLARIFICATION, not a defect)
The case's example agent name **"Claude B" does not exist** in this
environment (confirmed: `GET .../applications/prompt_lib/{project}` — no
agent named "Claude B" among 49 agents in the `Private` project, nor in the
"Elitea Testing Team" project). Use any agent with `conversation_starters`
configured. The case's own literal starter-text example
("here is your task: Explain Exponential Backoff") is portable independent
of agent identity — use it as one of the disposable agent's configured
starters so the case's own literal text is exercised.

### generate-per-test (in test setup, cleaned up in its own teardown)
Create a disposable agent via `AgentAPI.create_agent_full()` with
`conversation_starters` pre-populated — **do not set `llm_settings.reasoning_effort`
at all** (a `"none"` value 400s the `participants` add-endpoint's stricter
validation — confirmed live this dispatch, see § Known Defects/Gaps):

```python
payload = {
    "name": f"autotest_{request.node.name}"[:32],
    "description": f"Auto-created for test {request.node.name}",
    "type": "interface",
    "versions": [{
        "name": "base",
        "tags": [],
        "instructions": "You are a test agent. Answer briefly, in one short sentence.",
        "variables": [],
        "tools": [],
        "llm_settings": {
            "max_tokens": -1,
            "model_name": settings.default_model_name,
            "model_project_id": settings.elitea_project_id,
            # reasoning_effort intentionally OMITTED
        },
        "conversation_starters": [
            "here is your task: Explain Exponential Backoff",
        ],
        "agent_type": "openai",
        "welcome_message": "",
        "meta": {"step_limit": 25},
    }],
}
agent = agent_api.create_agent_full(payload)
```
Confirmed live: `POST .../applications/prompt_lib/{project}` → `201`, the
agent immediately appears in the composer's "+ → Agents" search
(`agents-search-input`) **within the SAME project the browser session is
scoped to** — see § Known Defects/Gaps for the project-ID pitfall this
surfaced.

### Literal values
| Field | Value |
|-------|-------|
| Conversation starter (case's own example) | `here is your task: Explain Exponential Backoff` |

## Test Steps
1. Navigate to Chats, open an existing conversation, click the composer's "+"
   (plus menu) icon, select "Agents", search and select the disposable agent.
   - **Verify — PASSES.** Agent chip appears in the composer
     (`chat-switch-participant-button`, showing the agent name) alongside the
     version chip (`chat-version-selector-trigger`) and the settings gear
     (`chat-participant-settings-button`); the PARTICIPANTS panel's "Agents"
     badge (`chat-participants-badge-agents`) shows count "1"; conversation
     starter tile(s) render above the message input
     (`chat-conversation-starter-tile`, max 4 per case text — this
     environment's disposable agent has 1-2 configured, well under the cap).
2. Verify starters are displayed as clickable pills; hover over a truncated
   starter to see the tooltip.
   - **Verify — PASSES, with a caveat.** `EllipsisTextWithTooltip`'s tooltip is
     **conditional on actual visual truncation** (`clientWidth < scrollWidth`
     check in `handleMouseEnter` — confirmed via source,
     `src/components/ConversationStarters.jsx:218-223`) — a short starter that
     fits on one line shows NO tooltip on hover, which is correct behavior, not
     a defect. Confirmed live with a deliberately long starter text
     (>150 chars) added to the disposable agent for this verification: hover
     produced a floating tooltip showing the exact full text. The case's own
     example starter ("here is your task: Explain Exponential Backoff", 48
     chars) does NOT truncate at the tile's rendered width in this
     environment — implementer: use a starter text long enough to force
     truncation for THIS step's assertion (a second, throwaway starter is
     fine; it does not need to be the one clicked in step 3).
3. Click a conversation starter (the case's own example,
   "here is your task: Explain Exponential Backoff").
   - **Verify — PASSES.** Full starter text is inserted into the message
     input verbatim (`chat-message-input` value == clicked starter's exact
     text). Confirmed live via source too (`onSendConversationStarter` →
     `chatInput.current.setValue(starter)`, pre-fill only, no auto-send).
4. Verify text is editable and agent name/version still shown in input bar.
   - **Verify — PASSES.** The populated field remains a live editable
     textbox (confirmed: `Send` button transitions absent→enabled, matching
     the field having real content the app tracks); agent chip
     (`chat-switch-participant-button`) and version chip
     (`chat-version-selector-trigger`) remain visible and unchanged
     throughout.
5. Click Send.
   - **Verify — PASSES.** Message sent, appears in the conversation history
     directed "to {AgentName}" (confirmed: message-item header shows
     "Test Bot to {agent-name}", clicking the agent-name text is itself a
     "Chat now" affordance — not part of this case's own assertions).
     `POST .../conversations/prompt_lib/{project}` → `201`. Agent begins
     processing.
6. Verify agent responds with reasoning/Thinking section visible.
   - **Verify — PASSES.** Response renders with:
     - `chat-answer-thought-accordion` ("Thought for {n} secs" — collapsed
       label wording varies, e.g. "Thought for less than a second"),
       `[expanded]` during/immediately after generation (confirmed live via
       accessibility snapshot's `[expanded]` state attribute).
     - `chat-answer-model-chip` inside the accordion showing the LLM used
       (confirmed live: "Anthropic Claude 4.5 Sonnet" — the project's default
       model; not asserted as a literal string since model availability is
       environment-dependent — assert non-empty/contains a known-model
       substring pattern).
     - Full response text rendered in the message body, contextually
       relevant to the clicked starter (confirmed live: a correct one-sentence
       exponential-backoff explanation, not a stub/error).
     - Zero console errors beyond the sanctioned `secrets 403` noise; zero
       unexpected network 4xx/5xx.

## Expected Results
- Adding an agent with conversation starters to an existing conversation
  shows the starter tile(s) above the composer (max 4).
- A genuinely-truncated starter shows its full text in a hover tooltip; a
  short (non-truncated) starter correctly shows none.
- Clicking a starter pre-fills (does not auto-send) the composer with its
  exact text; the field remains editable; the agent chip/version persist.
- Sending produces a real agent response with the Thinking accordion and the
  LLM model chip, no console/network errors.

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture | n/a (fixture-level) | asserted |
| Precondition: agent with conversation starters exists | Agent reachable via + → Agents search | Test-data setup (`create_agent_full()`) | agent created, id returned, appears in search | asserted |
| Step 1: navigate to Chats, open conversation, + → Agents → select agent | Agent chip shown; starters visible above input (max 4) | Step 1 | agent chip testid visible, `chat-conversation-starter-tile` count ≤ 4 | asserted |
| Step 2: starters clickable pills; hover truncated starter shows tooltip | Full text shown in tooltip | Step 2 | tooltip element visible with full text on a genuinely-truncated starter | asserted *(clarified — tooltip is truncation-conditional by design, not a bug; see step 2 note)* |
| Step 3: click a conversation starter | Full text inserted in message field | Step 3 | `chat-message-input` value equals clicked starter's exact text | asserted |
| Step 4: text editable; agent name/version still shown | Text editable; agent chip visible | Step 4 | send-button enabled transition + agent/version chip visibility unchanged | asserted |
| Step 5: click Send | Message sent; agent processes; response shown with agent icon and LLM model label | Steps 5-6 | `POST .../conversations/...` 201; message item "to {agent}"; model chip present | asserted |
| Step 6: agent responds with reasoning/Thinking section visible | Agent response with Thinking section | Step 6 | `chat-answer-thought-accordion` visible/expanded, response text non-empty | asserted |
| Pass criterion: "all steps complete without errors" | No errors at any step | Steps 1-6 | console error check (secrets-403 excluded per project convention) at each step | asserted |
| Fail criterion: "starters not shown or agent fails" | n/a (negative condition) | Steps 1, 6 | presence assertions (step 1); response-received assertion (step 6) | asserted |

### Axis 2 — observables asserted beyond the case text

- Zero console errors / zero unexpected 4xx-5xx across the full add-agent →
  click-starter → send → response cycle — silent-error discipline per project
  convention.
- `chat-participants-badge-agents` count reflects "1" after adding the agent
  — *added: cheap, deterministic corroboration that the participant actually
  registered, independent of the composer's own chip render.*
- The response is contextually relevant to the specific starter clicked (not
  a generic/error fallback) — *added: rules out a stub/placeholder response
  passing a weaker "any text present" assertion.*

## Cleanup
1. Delete the sent user message + agent response via the response's "Delete"
   button (confirmed live: deleting the agent-response item cascades and
   removes the paired user message too, restoring the conversation to its
   pre-test message list — confirmed via reload).
2. Delete the disposable agent via `AgentAPI.delete_agent(agent_id)` — this
   also cleanly drops it as a chat participant (confirmed live: after
   deletion + reload, the composer reverted to the conversation's original
   default LLM with no leftover agent chip/starters, no console error).
3. No conversation-level cleanup needed if a pre-existing conversation was
   reused (as opposed to created fresh for this test) — restoring the message
   list in step 1 above is sufficient.

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Plus/attach menu trigger | `plus-menu-button` (confirmed live; `ChatPage.wait_for_add_agent_button()`/`add_agent_participant()` currently use `get_by_role("button", name="plus menu")` — pre-existing raw-handle tech debt, NOT this case's element to fix, but the testid exists and a future refactor could tighten it) | on-`automation/testids` (pre-existing) |
| Plus-menu "Agents" item | `agents-menuitem` (same `PLUS_MENU_ITEM_SUFFIX` family, confirmed live) | pre-existing |
| Agent search input (in +menu) | `agents-search-input` (confirmed live; current `add_agent_participant()` uses `get_by_placeholder("Search agents...")` — same tech-debt note as above) | pre-existing |
| Agent result row (in +menu) | `agents-menu-item-agent-{index}-{agent_id}` (dynamic, confirmed live — e.g. `agents-menu-item-agent-399-9334`) | pre-existing |
| Composer agent chip (name) | `chat-switch-participant-button` (`ChatPage.switch_participant_button`) | pre-existing |
| Composer version chip | `chat-version-selector-trigger` (`ChatPage.chat_version_selector_trigger`) | pre-existing |
| Composer settings gear icon | `chat-participant-settings-button` (`ChatPage.chat_participant_settings_button`) | pre-existing |
| Composer "X" / remove-participant icon (`aria-label="switch to model"`) | **`testid needed`** — `AgentEditorPanel.jsx`'s `IconButton` (lines ~178-192 and ~294-320) has NO `data-testid`, only `aria-label="switch to model"` + tooltip "Switch to model" (confirmed via source read). This case's own steps only VERIFY the icon's presence (case step 4/ELITEA-2465 step 4), never click it — recommend `chat-switch-to-model-button` if a future case needs to click it; for THIS case, a presence check needs a stable handle too. Add via `add-data-testid` before the implementer writes the visibility assertion. | needs-adding |
| Participants panel "Agents" badge | `chat-participants-badge-agents` (`PARTICIPANTS_BADGE.format("agents")`) + `chat-participants-badge-button` scoped inside it | pre-existing |
| Conversation starter tile | `chat-conversation-starter-tile` (`ChatPage.CHAT_STARTER_TILE`, `get_chat_starter_tiles()`, `click_chat_starter_tile()`) — confirmed live, renders identically on `/chat/{id}` (this case) and the embedded `/agents/all/{id}` chat (ELITEA-1886) since both mount `ChatBox.jsx` → `ChatConversationStarters.jsx` | pre-existing |
| Message input | `chat-message-input` (`ChatPage.message_input`) | pre-existing |
| Send button | (confirmed testid `chat-send-button` via live `getByTestId` resolution) `ChatPage.send_button` | pre-existing |
| Thought/reasoning accordion | `chat-answer-thought-accordion` (`ChatPage.answer_thought_accordion`) | pre-existing |
| Model chip in accordion | `chat-answer-model-chip` (`ChatPage.answer_model_chip`) | pre-existing |
| Delete-message confirm dialog button | `delete-confirm-button` (shared `Dialog` component idiom, confirmed live) | pre-existing |

## Network Behavior
- `POST .../elitea_core/participants/prompt_lib/{project}/{conversation_id}` —
  fires on selecting the agent in the +menu, `200` on success. **Gotcha
  (see § Known Defects/Gaps):** returns `400` if the agent's
  `llm_settings.reasoning_effort` is the literal string `"none"` — the
  endpoint's schema only accepts `low`/`medium`/`high` (or omitted/null),
  even though the AGENT-CREATE endpoint itself accepts `"none"` without
  complaint. Confirmed live this dispatch.
- `POST .../elitea_core/conversations/prompt_lib/{project}` — fires on Send,
  `201` on success, carries the pre-filled starter text as the message body.

## Known Defects Found During Exploration

**No functional product defect** in the case's own flow — the case's steps
pass end-to-end. Two analyst-environment gotchas worth flagging for the
implementer (both self-resolved during this dispatch, not product bugs):

1. **`reasoning_effort: "none"` 400s the participants-add endpoint, though
   agent-creation accepts it silently.** `POST .../applications/prompt_lib/{project}`
   with `llm_settings.reasoning_effort: "none"` returns `201` (agent created
   successfully with the invalid value persisted) — but
   `POST .../participants/prompt_lib/{project}/{conversation_id}` for that
   same agent returns `400`:
   `"1 validation error for EntitySettingsApplication\nllm_settings.reasoning_effort\n  Input should be 'low', 'medium' or 'high'"`.
   This is an inconsistency between the two endpoints' validation strictness
   (asymmetric schema enforcement) — arguably a minor backend issue, but NOT
   this case's subject and NOT reproduced against a normally-configured agent
   (any agent created without setting `reasoning_effort`, or with a valid
   enum value, adds cleanly). Test-data guidance above (§ Test Data) already
   routes around it by omitting the field. Not filed as a separate ticket —
   noting here per project convention (a genuinely new environment quirk
   worth a role-memory entry, which the analyst is separately recording).
2. **The browser's DEFAULT active project does not necessarily match
   `${ELITEA_PROJECT_ID}` (399, `Private`) from `.env.test`.** This session's
   Playwright MCP browser (persistent profile, `auth_state`/`VITE_DEV_TOKEN`)
   opened on project **471** ("Elitea Testing Team") by default, not project
   399. Data created via the Bearer-token `AgentAPI` client against project
   399 (config default) was invisible in the composer's agent search until
   the UI's own project switcher was used to select "Private" (`project 399`)
   — confirmed via network capture:
   `GET .../applications/prompt_lib/471?...` vs `.../399?...` are genuinely
   different result sets, and the participants-add endpoint 400s if the
   conversation's project and the agent's owning project don't match
   (`elitea_core/participants/prompt_lib/{conv_project}/{conv_id}` targets
   the CONVERSATION's project, not the agent's). **Implementer/fixture
   guidance:** whichever project the `agent_api`/`conversation_api` fixtures
   target must be the SAME project id the UI session is actually scoped to
   at test time — don't assume `settings.elitea_project_id` is automatically
   the active UI project on a persistent local browser profile; confirm via
   the sidebar's project-id textbox or force-select the project at test
   start if the fixture's default could drift.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest (confirmed, `.agents/testing.md`).
- Reuse `ChatPage.add_agent_participant(agent_name_prefix)` for step 1's
  agent-selection action (existing method, tech-debt raw handles inside —
  not this case's element to refactor, per project convention on pre-existing
  raw handles). New testid-based handles discovered live (`plus-menu-button`,
  `agents-menuitem`, `agents-search-input`,
  `agents-menu-item-agent-{index}-{id}`) are available for a future tightening
  pass but are NOT required for this case to be `ready-for-automation`.
- `ChatPage.CHAT_STARTER_TILE` / `get_chat_starter_tiles()` /
  `click_chat_starter_tile(match_text)` are ready-to-use as-is for steps 1-3.
- Wait strategy: after selecting the agent, wait on the
  `POST .../participants/...` response (or the composer's agent-chip becoming
  visible) before reading starter tiles — the row populates from the
  conversation's participant list, not instantaneously.
- Step 6 completion: use `ChatPage.wait_for_ai_response()`-style condition
  wait (WebSocket-driven, no sleeps per project convention), then assert
  `answer_thought_accordion` + `answer_model_chip` + non-empty response text.
- **Sibling case:** `test-specs/chat-interface/l1_add-agent-with-starters-and-send-via-starter_ELITEA-2465.md`
  drives the SAME underlying flow with finer-grained assertions (this case's
  steps 1-6 map roughly to ELITEA-2465's steps 1-15). They were analysed in
  the same session and MAY share one page-object/fixture set and even land
  in the same test file as two methods — but are kept as separate AFS
  because ELITEA-2465 asserts several observables this case's text never
  requests (default-LLM-before-add, explicit PARTICIPANTS "Agents" section
  check, an explicit processing indicator, explicit LLM-label check). See
  that AFS's own Coverage Map for the delta.
