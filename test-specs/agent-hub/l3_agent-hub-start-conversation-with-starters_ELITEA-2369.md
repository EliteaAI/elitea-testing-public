# Test Case: Agent Hub — E2E start conversation with agent that has conversation starters, use starter to send message, receive reply

## Metadata
- **TMS ID**: ELITEA-2369
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog` → `/chat/{id}`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — all 16 case steps reproduced live end-to-end (Catalog → modal with starters → Start Chat → chat page → click starter tile → input populated → send → agent processing/tools-used indicator). Zero console errors, zero 4xx/5xx across the whole interaction. Two already-tracked case-text drifts (see § Known Defects, same #1042/#1043 the no-starters sibling ELITEA-2368 hit). **Two new testid gaps found** — the modal's individual starter items and the chat-area starter tiles have zero testids (see § Concrete Handles).
- **Related surfaces reused**: `AgentHubPage` (`open_agent_by_name()`, `click_start_chat()`, `modal_chat_starters_section`) for steps 1-4; `ChatPage` (`wait_for_page_load()`, `is_agent_participant_in_composer()`, `switch_participant_button`, `chat_version_selector_trigger`, `expand_participants_panel_via_toggle()` + `get_participant_row_by_name()`, `message_input`, `send_button`/`is_send_button_enabled()`, `wait_for_message_count()`, `wait_for_ai_response()`, `answer_thought_accordion`, `answer_tool_chip`, `get_last_message_text()`) for steps 5-16 — all pre-existing, confirmed live this dispatch.
- **Not a target for `extend-existing`/`already-covered`**: the only merged spec that also drives Catalog-modal → chat with a starters-bearing agent is the sibling `test_agent_hub_start_conversation_no_starters.py` (ELITEA-2368) — but that one deliberately opens a **no-starters** agent and asserts the no-starters/no-welcome empty-state copy; it never opens the CHAT STARTERS list, never asserts multiple starter tiles render, never clicks a starter tile to populate the composer, and never asserts the send button transitioning from absent→enabled via a starter click. Zero of this case's starter-specific observables (steps 4, 8, 11-13) are asserted there. Genuinely fresh coverage of the opposite precondition: `ready-for-automation`.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- At least one published Catalog agent with predefined conversation starters exists. **Confirmed live, and it matches the case's own "e.g., API Testing Buddy" example verbatim**: "API Testing Buddy" (application id 34, author Levon Dadayan, 4 likes, category "Other") shows 4 CHAT STARTERS tiles and a configured Welcome Message reading "Welcome! I'm your API Testing Buddy—ready to validate documentation, plan rigorous API test suites, and execute Python-based checks once all required tooling is confirmed." — matches the case text's truncated example exactly.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Catalog agent: **"API Testing Buddy"** (case's own "e.g." example — confirmed present live with 4 configured chat starters + welcome message, application id 34).
- Starter to click (case's own "e.g." example, confirmed present live verbatim): *"I've uploaded a Swagger spec—can you confirm tooling readiness and outline the test plan?"* (live copy uses a curly apostrophe "'" vs the case text's straight `'` — cosmetic, not worth its own clarification ticket; automation should match on the live copy, curly apostrophe included, or use a substring match that tolerates it).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.navigate()` / `wait_for_page_load()`).
2. Click on an agent card that has predefined conversation starters (e.g., "API Testing Buddy").
   - **Verify**: click succeeds; the underlying `GET /api/v2/elitea_core/public_application/prompt_lib/34` request fires and resolves `200` (confirmed live) — reuse `AgentHubPage.open_agent_by_name()`, which already waits on this exact response.
3. Verify the detail modal opens displaying agent name and description.
   - **Verify**: `AgentHubPage.modal_agent_name` reads "API Testing Buddy"; description text ("Tests API by Provided swagger or postman collection, then you can ask to create Test Plan, Test Cases, execute test cases") visible — confirmed live.
4. Verify the "CONVERSATION STARTERS" section displays multiple predefined starter options.
   - **CASE-TEXT DRIFT (CLARIFICATION, already tracked, not re-filed)**: live section header reads **"CHAT STARTERS"** (not "CONVERSATION STARTERS") — confirmed live, tracked in [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042), which explicitly names ELITEA-2369 as an affected sibling.
   - **Verify**: `AgentHubPage.modal_chat_starters_section` (`catalog-agent-modal-chat-starters-section`) visible, containing **4** starter items (confirmed live): *"I've uploaded a Swagger spec—can you confirm tooling readiness and outline the test plan?"*, *"Here's a Postman collection; generate full test cases across happy paths and edge cases."*, *"Validate these cURL commands, then build a dependency graph and data flow matrix."*, and a code-formatted starter *"could you test me `curl -XGET https://example.com`"*.
   - **NEW TESTID GAP (this dispatch)**: individual starter items inside the section (`AgentConversationStarterItem.jsx`) carry **zero** `data-testid`/`testId` — confirmed via source read (component only wires `onClick`/hover state, no testid prop threaded from `AgentConversationStarters.jsx`). "Multiple options display" needs a way to count/select individual items — see § Concrete Handles.
5. Verify the "WELCOME MESSAGE" section displays the agent's configured welcome text (e.g., "Welcome! I'm your API Testing Buddy—ready to validate documentation...").
   - **CASE-TEXT DRIFT (CLARIFICATION, same #1042)**: live header reads **"Welcome Message"** (title-case, not "WELCOME MESSAGE" all-caps).
   - **Verify**: `AgentHubPage.modal_welcome_message_section` text starts with "Welcome! I'm your API Testing Buddy—ready to validate documentation..." — confirmed live, verbatim match to the case's own truncated example.
6. Click the "Start conversation" button.
   - **CASE-TEXT DRIFT (CLARIFICATION, same #1042)**: live button reads **"Start Chat"**, not "Start conversation".
   - **KNOWN DEFECT, already tracked, not re-filed**: [EliteaAI/elitea-testing-public#1043](https://github.com/EliteaAI/elitea-testing-public/issues/1043) (already names ELITEA-2369 as an affected sibling) — clicking Start Chat before the modal's async `agentDetails` fetch commits throws an uncaught TypeError and silently no-ops. The implementation must add the same documented `page.wait_for_timeout(1000)` immediately before the click that ELITEA-2368's implementation added, citing #1043 — confirmed live this dispatch (waited ~1s before clicking, click succeeded deterministically).
   - **Verify**: `AgentHubPage.modal_start_chat_button` click succeeds — reuse `AgentHubPage.click_start_chat()`.
7. Verify a new chat is created and the user is redirected to the Chat interface.
   - **Verify**: `page.url` matches `/chat` (confirmed live: redirected to `/chat`, then to `/chat/{conversation_id}?name=...` once the conversation is auto-named from the first sent message) — reuse `ChatPage.wait_for_page_load()`.
8. Verify the conversation starters are displayed as clickable suggestion tiles in the chat area.
   - **Verify**: 4 clickable tiles render in the chat composer area, same 4 starter texts as the modal (confirmed live — `ChatConversationStarters.jsx` renders the same `conversation_starters` list, once the conversation has zero prior user activity).
   - **NEW TESTID GAP (this dispatch)**: the chat-area tiles are rendered via the SHARED `EllipsisTextWithTooltip` component (`src/components/ConversationStarters.jsx`, also used by `NewConversationView.jsx`'s pre-chat composer) with **zero** `data-testid`/`testId` prop threaded — confirmed via source read AND live: clicking required falling back to a raw CSS-class locator during this exploration (`.MuiBox-root.css-vjd7yg`), which is not a stable handle and is NOT what the implementer may ship. See § Concrete Handles.
9. Verify the agent chip (e.g., "API Testing Buddy v1.1") is visible in the message input bar.
   - Same combined-vs-split nuance as ELITEA-2368 (out of scope here, dedicated sibling case ELITEA-2362/#870 owns it): live renders TWO separate adjacent elements — `ChatPage.switch_participant_button` (`chat-switch-participant-button`, shows "API Testing Buddy") and `chat_version_selector_trigger` (`chat-version-selector-trigger`, shows "v1.1") — confirmed live, matches the case's own literal example verbatim (name + version).
   - **Verify**: `ChatPage.is_agent_participant_in_composer("API Testing Buddy")` returns `True`, and `chat_version_selector_trigger` text reads "v1.1" — confirmed live.
10. Verify the agent appears under the AGENTS section in the Participants panel on the right.
    - **Verify**: `ChatPage.expand_participants_panel_via_toggle()` then `get_participant_row_by_name("API Testing Buddy")` finds a row under an "Agents" heading showing "API Testing Buddy" / "v1.1" — confirmed live.
11. Click one of the conversation starter tiles (e.g., "I've uploaded a Swagger spec—can you confirm tooling readiness and outline the test plan?").
    - **Verify**: click succeeds on the tile matching that text (once the testid gap in step 8 is closed, scope the click to `[data-testid="<new-testid>"]` filtered by text) — confirmed live via the fallback CSS selector used for this exploration only.
12. Verify the selected starter text is populated into the message input field.
    - **Verify**: `ChatPage.message_input` value reads the exact starter text clicked — confirmed live (`I've uploaded a Swagger spec—can you confirm tooling readiness and outline the test plan?`, curly apostrophe included).
    - **Observed, not a defect for this case**: the starter tiles remain visible/rendered below the input immediately after the populate-click (they only disappear once the message is actually sent and streaming starts, i.e. `isTheUserChattingNow` flips true) — the case text doesn't require them to disappear at this step, so this is documented here to prevent a future analyst/implementer from mis-asserting "tiles hidden after click" as an expected result.
13. Verify the send button becomes active.
    - **Verify**: `ChatPage.is_send_button_enabled()` returns `True` once the input has the populated text — confirmed live (the send button, absent on an empty composer, renders and is enabled the moment text exists, matching the case's own "becomes active" wording, same mechanism as the no-starters sibling's typed-text case).
14. Click the send button.
    - **Verify**: `ChatPage.send_button` (`chat-send-button`) click succeeds — confirmed live.
15. Verify the message is sent and displayed in the chat.
    - **Verify**: `ChatPage.wait_for_message_count(initial_count + 1)` then `get_last_message_text()` returns the starter text sent by "Test Bot" to "API Testing Buddy" — confirmed live (message count 0→1 immediately on send).
16. Verify the agent begins processing (e.g., "Thought for X secs" indicator is shown) and tools used are visible.
    - **Verify**: `ChatPage.answer_thought_accordion` (`chat-answer-thought-accordion`) becomes visible reading "Thought for N secs" `[expanded]` (confirmed live: "Thought for 38 secs"); `ChatPage.answer_tool_chip` (`chat-answer-tool-chip`) locator resolves ≥1 match with tool-call text (confirmed live: 3 tool-call chips — "Python sandbox: pyodide_sandbox", "Artifacts: get_artifacts_buckets" ×1, "Artifacts: get_artifacts_artifacts" ×2 — interleaved with 2 `answer_model_chip` "GPT-5.4" chips). `wait_for_ai_response(initial_count=1)` then resolves with a full reply.

## Expected Results
- Clicking a starters-bearing Catalog agent card opens its preview modal showing the CHAT STARTERS section with 4 clickable starter options and the configured Welcome Message (case text: "CONVERSATION STARTERS" / "WELCOME MESSAGE" — drift, tracked in #1042).
- Clicking "Start Chat" (case text: "Start conversation" — same #1042 drift; and hits known-defect #1043's race, mitigated with a documented wait) redirects to `/chat` and opens a brand-new conversation.
- The chat area renders the SAME 4 starters as clickable tiles; the active agent is shown as a chip/button pair in the composer (name + version) and under an "Agents" heading in the expanded Participants panel.
- Clicking a starter tile populates its full text into the message input and enables the send button (without auto-sending).
- Sending displays the user's message, a "Thought for N secs" processing indicator with visible tool-call chips, then the agent's reply.
- Zero console errors, zero 4xx/5xx.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click agent card with starters | Control responds; expected next state shown | step 2 | agent-details GET fires, resolves 200 | asserted |
| 3 Modal shows agent name and description | Condition holds as described | step 3 | `modal_agent_name`, description text | asserted |
| 4 CONVERSATION STARTERS section shows multiple options | Condition holds as described | step 4 | `modal_chat_starters_section` + item count (new testid) | asserted *(section-label drift, #1042; item testid gap, new)* |
| 5 WELCOME MESSAGE section shows configured welcome text | Condition holds as described | step 5 | `modal_welcome_message_section` text | asserted *(header-label drift, #1042)* |
| 6 Click "Start conversation" | Control responds; expected next state shown | step 6 | `modal_start_chat_button` click | asserted *(label drift #1042; race #1043, mitigated wait)* |
| 7 New chat created, redirected to Chat interface | Condition holds as described | step 7 | URL matches `/chat`, `wait_for_page_load()` | asserted |
| 8 Conversation starters displayed as clickable tiles in chat | Condition holds as described | step 8 | tile count/text (new testid) | asserted *(new testid gap)* |
| 9 Agent chip (e.g. "API Testing Buddy v1.1") visible in input bar | Condition holds as described | step 9 | `chat-switch-participant-button` + `chat-version-selector-trigger` | asserted *(combined-vs-split nuance out of scope — ELITEA-2362/#870)* |
| 10 Agent appears under AGENTS section in Participants panel | Condition holds as described | step 10 | expanded panel "Agents" heading + `get_participant_row_by_name()` | asserted |
| 11 Click a starter tile | Control responds; expected next state shown | step 11 | tile click (new testid) | asserted *(new testid gap)* |
| 12 Selected starter text populated into input field | Condition holds as described | step 12 | `message_input` value | asserted |
| 13 Send button becomes active | Condition holds as described | step 13 | `is_send_button_enabled()` | asserted |
| 14 Click send button | Control responds; expected next state shown | step 14 | `chat-send-button` click | asserted |
| 15 Message sent and displayed in chat | Condition holds as described | step 15 | message count 0→1, `get_last_message_text()` | asserted |
| 16 Agent begins processing ("Thought for X secs") and tools used visible | Condition holds as described | step 16 | `chat-answer-thought-accordion` text + `chat-answer-tool-chip` count ≥1 | asserted |
| Expected Final State: agent processing indicator + tools used visible | — | step 16 | as above | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- **step 2** asserts the underlying agent-details network request resolves 200, not merely "modal appears" — *added: deterministic ready-signal, same rationale as the no-starters sibling AFS (avoids the known #1043 race class on Start Chat).*
- **steps 3-16** each assert zero new console errors / zero 4xx-5xx as a standing side-channel check rather than a single end-of-test check — *added: isolates exactly which interaction would have introduced a regression.*
- **step 16** asserts tool-call chips specifically (`answer_tool_chip`, ≥1 match) rather than just eyeballing the accordion body text — *added: "tools used are visible" is the case's own explicit final-state wording; a dedicated locator makes it a real assertion instead of a substring match against free-form AI-generated prose.*
- **step 12** documents the observed non-disappearance of the tile list immediately after a populate-click (tiles persist until the message actually sends and streaming starts) — *added: prevents a future implementer from writing an incorrect "tiles hidden on click" assertion that would flap depending on timing.*

## Cleanup

- The conversation created in step 7 (auto-named "I've uploaded Swagger spec—can you" from the sent message, id `7096` in this exploration run) should be deleted via `ConversationAPI.delete_conversation(conv_id)` in a `finally` block, matching the ELITEA-2368/ELITEA-2075 precedent — parse `conv_id` from the post-send URL (`/chat/{id}?...`) via `re.search(r"/chat/(\d+)", page.url)`. No agent state (like/unlike, starters, welcome message) is modified by this case — read/interact-only on the agent side.

## Concrete Handles (discovered/confirmed during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | pre-existing — re-verify against `origin/main` per surface digest's PROVENANCE CORRECTION before citing as on-main |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` / `get_agent_card()` (`[data-testid^="catalog-agent-card-"]`) | none | pre-existing, confirmed live (id 34 = "API Testing Buddy") |
| Modal open/name/description/sections/Start Chat | `AgentHubPage.open_agent_by_name()`, `modal_agent_name`, `modal_chat_starters_section`, `modal_welcome_message_section`, `click_start_chat()` | none | pre-existing, confirmed live this dispatch |
| **Modal starter item (NEW GAP)** | `testid needed: catalog-agent-modal-starter-item` — static testid repeated on every `AgentConversationStarterItem.jsx` render, scoped inside `catalog-agent-modal-chat-starters-section`; select a specific one via `.filter(has_text=...)` | none — `AgentConversationStarterItem.jsx` currently has zero testid/data attribute of any kind | **needs-adding** — implementer adds via `add-data-testid` in EliteaUI's `src/[fsd]/features/agent-hub/ui/AgentConversationStarterItem.jsx`, threaded from `AgentConversationStarters.jsx`'s `.map()` (not a shared component — feature-scoped, static testid is fine per `.agents/testing.md`'s dynamic-testid guidance, since disambiguation happens via text-filter, not a data-driven suffix) |
| Blank-conversation greeting | `ChatPage.new_conversation_greeting` (`chat-new-conversation-greeting`) | none | pre-existing (not directly asserted by this case's steps, but the same chat page render) |
| Composer agent-name chip | `ChatPage.switch_participant_button` (`chat-switch-participant-button`) | none | pre-existing, confirmed live this dispatch |
| Composer version chip | `ChatPage.chat_version_selector_trigger` (`chat-version-selector-trigger`) | none | pre-existing, confirmed live this dispatch |
| Participants panel toggle | `ChatPage.participants_panel_toggle_button` (`chat-participants-panel-toggle-button`) | none | pre-existing, confirmed live this dispatch |
| **Chat-area starter tile (NEW GAP, shared component)** | `testid needed: chat-conversation-starter-tile` — static testid threaded via a new `testId` prop on the SHARED `EllipsisTextWithTooltip` (`src/components/ConversationStarters.jsx`), supplied by `ChatConversationStarters.jsx`'s call site; select a specific tile via `.filter(has_text=...)` | none — during this exploration, clicking required a raw CSS-class locator (`.MuiBox-root.css-vjd7yg`), which is NOT an acceptable shipped locator per this project's testid-only policy | **needs-adding** — `EllipsisTextWithTooltip` is shared with `NewConversationView.jsx`'s pre-chat composer (a DIFFERENT, not-yet-analysed flow), so per `.agents/testing.md`'s shared-component rule the prop must be caller-supplied (`testId`), never hardcoded inside `ConversationStarters.jsx` itself. `NewConversationView.jsx`'s call site is out of scope for THIS case — only wire the `ChatConversationStarters.jsx` call site's prop; leave `NewConversationView.jsx`'s own opt-in for whichever case exercises it (canon ruling #511 — "touches" = code path this test executes) |
| Message input | `ChatPage.message_input` (`chat-message-input`) | none | pre-existing, confirmed live this dispatch |
| Send button | `ChatPage.send_button` (`chat-send-button`) / `is_send_button_enabled()` | none | pre-existing, confirmed live this dispatch |
| Thought/reasoning accordion | `ChatPage.answer_thought_accordion` (`chat-answer-thought-accordion`) | none | pre-existing, confirmed live this dispatch ("Thought for 38 secs") |
| Tool-call chip (tools used) | `ChatPage.answer_tool_chip` (`chat-answer-tool-chip`) | none | pre-existing, confirmed live this dispatch (3 matches: pyodide_sandbox, get_artifacts_buckets, get_artifacts_artifacts ×2) |
| Model chip (inside accordion, not a tool) | `ChatPage.answer_model_chip` (`chat-answer-model-chip`) | none | pre-existing, confirmed live this dispatch ("GPT-5.4" ×2) — NOT a tool chip, don't conflate when asserting "tools used" |

Two new `testid needed` rows — both scoped to elements this case's own steps actually touch (step 4's item count / step 8+11's tile click), per canon ruling #511.

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?query=API+Testing&...` → `200` — search filter to locate "API Testing Buddy".
- `GET /api/v2/elitea_core/public_application/prompt_lib/34` → `200` — modal open (fires twice across the flow: once on card click, once more after Start Chat's redirect).
- `POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}` → `201` — new conversation created on "Start Chat".
- `PATCH /api/v2/elitea_core/entity_settings/prompt_lib/{project_id}/{conv_id}`, `PUT .../conversation/prompt_lib/{project_id}/{conv_id}`, `POST .../participants/prompt_lib/{project_id}/{conv_id}`, `POST .../select_conversation/prompt_lib/{project_id}/{conv_id}` — all `200`, conversation setup sequence following creation.
- `GET /api/v2/elitea_core/context_analytics/prompt_lib/{project_id}/{conv_id}` — fires after the message exchange.
- No 4xx/5xx observed anywhere in the whole flow (Catalog → search → modal → Start Chat → chat → starter click → send → reply → participants panel).

## Known Defects Found During Exploration
- **[CLARIFICATION, already tracked, not re-filed]** [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) — case text says "CONVERSATION STARTERS" section / "Start conversation" button / "WELCOME MESSAGE" all-caps; live product reads "CHAT STARTERS" / "Start Chat" / "Welcome Message" title-case respectively. Already names ELITEA-2369 as an affected sibling — cite, don't re-file.
- **[KNOWN DEFECT, already tracked, not re-filed]** [EliteaAI/elitea-testing-public#1043](https://github.com/EliteaAI/elitea-testing-public/issues/1043) — Start Chat click race (modal content ready before `agentDetails` async fetch commits); already names ELITEA-2369 as an affected sibling. Mitigated in this exploration with a 1s wait before the click, consistent with ELITEA-2368's implementation. Implementer should add the same documented `page.wait_for_timeout(1000)` + comment citing #1043.
- **[NEW, this dispatch — testid gap, not a behavioral defect]** Two new testid gaps found (see § Concrete Handles): the modal's individual starter items (`AgentConversationStarterItem.jsx`) and the chat-area starter tiles (shared `EllipsisTextWithTooltip` in `src/components/ConversationStarters.jsx`) have zero stable handles. Neither is a product misbehavior — both render and function correctly, they simply lack `data-testid`. Filed as implementer work orders in the Concrete Handles table per `.agents/testing.md` § Locator policy (missing testid ⇒ add it, not a defect ticket).
- **[Observed, not filed]** After a starter-click populates the input, the starter-tile list remains visible/rendered (does not hide) until the message is actually sent and AI streaming begins — the case text doesn't require hiding at that point, so this is not a defect, just documented in step 12 to prevent a future mis-assertion.
- None else found — zero console errors, zero 4xx/5xx, all 16 case steps reproduced live and match the case's core intent (agent name/description/starters/welcome-message correctly sourced from the agent's own configuration, starter click correctly populates the composer without auto-sending, send flow and processing/tools-used indicator all work as expected).

## Blocked Steps
None — all 16 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- **No new page object needed beyond the two testid additions** — both `AgentHubPage` and `ChatPage` already carry every OTHER field/method this case needs; the implementer composes them exactly as `test_agent_hub_start_conversation_no_starters.py` (ELITEA-2368) already does (same two page objects, same composition pattern, `from api import ConversationAPI` for cleanup).
- **Two testid additions required before automation** (see § Concrete Handles) — both go through `add-data-testid` on EliteaUI's `automation/testids`:
  1. `catalog-agent-modal-starter-item` on `AgentConversationStarterItem.jsx`'s root `Box` (feature-scoped, not shared — hardcode is fine).
  2. A new `testId` PROP on the shared `EllipsisTextWithTooltip` (`src/components/ConversationStarters.jsx`), wired to `data-testid={testId}` on its root `Box`, with `ChatConversationStarters.jsx` supplying `testId="chat-conversation-starter-tile"` at its call site only (leave `NewConversationView.jsx`'s call site unwired — out of scope, canon ruling #511).
- Suggested test file location: `automation/tests/ui/chat/` (matches the ELITEA-2368/ELITEA-2075 precedent — same cross-surface Catalog→chat shape, majority of assertions are chat-surface).
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy).
- Known defect #1043 — add `page.wait_for_timeout(1000)` immediately before `AgentHubPage.click_start_chat()`, with a docstring/comment citing #1043 (same as ELITEA-2368's implementation — this modal-race defect is shared).
- AI reply wait: use `ChatPage.wait_for_ai_response(initial_count=1, timeout=AI_RESPONSE_TIMEOUT)` — never a sleep (`.agents/testing.md`). This case's live run took 38s to finish "thinking" (tool calls involved) — budget the same 60-90s timeout as ELITEA-2075/ELITEA-2368.
- Step 12/13: read `message_input`'s value via its Playwright `input_value()`/`text_content()` equivalent (whichever `ChatPage.message_input` already exposes) immediately after the tile click — no wait needed here since `setValue()` is synchronous in `onSendConversationStarter`.
- Step 15: use `ChatPage.wait_for_message_count(initial_count + 1, timeout=...)` before reading `get_message_count()`/`get_last_message_text()` (same race precedent noted in ELITEA-2368's AFS — an immediate read right after Send races the DOM commit).
- Step 16 tools-used assertion: `ChatPage.answer_tool_chip` should resolve to `.count() >= 1` after `wait_for_ai_response()` — do NOT assert on `answer_model_chip` text for "tools used" (that's the model-name chip, a sibling but distinct element in the same chip row).
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.chat`.
- Cleanup: capture `conv_id` from `page.url` after step 7/15 (regex `r"/chat/(\d+)"`), delete via `ConversationAPI(browser_cookies=_browser_cookies).delete_conversation(conv_id)` in a `finally` block (ELITEA-2075/ELITEA-2368 precedent).
