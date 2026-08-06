# Test Case: Agent Hub — E2E start conversation with agent that has no conversation starters, type and send message, receive reply

## Metadata
- **TMS ID**: ELITEA-2368
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog` → `/chat/{id}`, EliteaUI `automation/testids`, DEV backend; sidebar project selector reads "Project: Private" by default for `${TEST_USER}` — no explicit project switch needed)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent)
- **Status**: **ready-for-automation** — all 16 case steps reproduced live end-to-end (Catalog → modal → Start Chat → chat page → send → AI reply → sidebar → Context Budget). Zero console errors beyond a pre-existing, unrelated dev-tooling warning (`docx-js-editor` module externalization — nothing to do with this flow); zero 4xx/5xx across the whole interaction. Two already-tracked case-text drifts (see § Known Defects); zero new testid gaps — every element this case touches already has a pre-existing testid.
- **Related surfaces reused**: `AgentHubPage` (`open_agent_by_name()`, `click_start_chat()`, modal fields) for steps 1-4; `ChatPage` (`wait_for_page_load()`, `new_conversation_greeting`, `is_agent_participant_in_composer()`, `chat_version_selector_trigger`, `expand_participants_panel_via_toggle()` + `get_participant_row_by_name()`, `send_message()`, `send_button`/`is_send_button_enabled()`, `wait_for_ai_response()`, `answer_thought_accordion`, `get_last_message_text()`, `is_conversation_in_group()`, `wait_for_context_budget_panel()`/`wait_for_context_budget_messages_count()`) for steps 5-16 — **all methods and testids already exist**, confirmed live this dispatch; no new page-object work needed.
- **Not a target for `extend-existing`/`already-covered`**: the only merged spec that also drives Catalog-modal → chat is `test_agent_hub_participant_readonly_canvas_llm_override.py` (ELITEA-2075, `automation/tests/ui/chat/`). It opens a *different* Catalog agent ("Reflexion") for a materially different purpose (read-only participant-settings canvas + per-conversation LLM override) and sends its one test message only as a final step to prove override persistence — it never asserts the welcome-message greeting, the composer agent chip, the PARTICIPANTS-panel AGENTS row, the "Thought for X secs" accordion, the sidebar Today grouping, or the Context Budget counter (0 of this case's 9 chat-side observables asserted there), and it requires an agent WITH starters/settings to exercise the canvas at all — the opposite precondition from this case. Genuinely fresh, narrow coverage: `ready-for-automation`.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (this project's default `${TEST_USER}` project on localhost).
- At least one published Catalog agent with no conversation starters and no welcome message exists. **Confirmed live, and it matches the case's own "e.g., Business Analyst" example verbatim**: "Business Analyst" (application id 31, author Levon Dadayan, 8 likes, description "Expert in business analysis and documentation") shows "No predefined chat starters – just type your request to begin." / "No welcome message set – the agent will start without a greeting." in its preview modal — same as every other 0-starter agent in this catalog (component rendering is generic, not agent-specific, per the sibling ELITEA-2356 AFS). This dispatch's live chat-continuation run (steps 5-16) used the equivalent agent **"User Story Creator"** (application id 172, 0 likes) — same modal rendering code path, same "no starters/no welcome" precondition, confirmed identically — since both satisfy the precondition identically, either is a valid automation target; the case's own literal example ("Business Analyst", id 31) is recommended for the implementation to match the case text exactly.

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Catalog agent: **"Business Analyst"** (case's own "e.g." example — confirmed present live with the required "no starters/no welcome" precondition, application id 31).

(No other test data required — case's own Test Data table says "(none required)".)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.navigate()` / `wait_for_page_load()`).
2. Click on an agent card that shows "No predefined conversation starters" (e.g., "Business Analyst").
   - **Verify**: click succeeds; the underlying `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` request fires and resolves `200` (confirmed live: `.../public_application/prompt_lib/31` for Business Analyst, `.../172` for the equivalent User Story Creator run) — reuse `AgentHubPage.open_agent_by_name()`, which already waits on this exact response.
3. Verify the detail modal opens displaying agent name, description, "CONVERSATION STARTERS" section with the no-starters text, and "WELCOME MESSAGE" section with the no-welcome-message text.
   - **CASE-TEXT DRIFT (CLARIFICATION, already tracked, not re-filed)**: live section headers read **"CHAT STARTERS"** (not "CONVERSATION STARTERS") and **"Welcome Message"** (title-case, not "WELCOME MESSAGE" all-caps) — confirmed live, tracked in [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042), which explicitly names ELITEA-2368 as an affected sibling.
   - **Verify**: `AgentHubPage.modal_agent_name` reads the agent's name; `modal_chat_starters_section` shows "No predefined chat starters – just type your request to begin."; `modal_welcome_message_section` shows "No welcome message set – the agent will start without a greeting." — confirmed live for both Business Analyst (id 31) and User Story Creator (id 172).
4. Click the "Start conversation" button.
   - **CASE-TEXT DRIFT (CLARIFICATION, already tracked in the same #1042, not re-filed)**: live button reads **"Start Chat"**, not "Start conversation".
   - **Verify**: `AgentHubPage.modal_start_chat_button` (`catalog-agent-modal-start-chat-button`) click succeeds — reuse `AgentHubPage.click_start_chat()`.
5. Verify a new chat is created and the user is redirected to the Chat interface.
   - **Verify**: `page.url` matches `/chat` (confirmed live: redirected to `/chat`, then to `/chat/{conversation_id}?name=...` once the conversation is named after the first message) — reuse `ChatPage.wait_for_page_load()`.
6. Verify the welcome message "Hello, [user]! What can I do for you today?" is displayed in the chat area.
   - **Verify**: `ChatPage.new_conversation_greeting` (`chat-new-conversation-greeting`) visible, reading **"Hello, Test! What can I do for you today?"** for `${TEST_USER}` (whose display name is "Test") — confirmed live, matches the case text exactly (modulo the literal `${TEST_USER}` display name substituted for "[user]").
7. Verify the agent chip (e.g., "Business Analyst v2.1") is visible in the message input bar.
   - **CASE-TEXT NUANCE (out of scope for THIS case — a dedicated sibling case, ELITEA-2362/#870, "Agent Hub — agent chip visible in message input with version and settings," already exists specifically to explore this element in depth; not yet analysed as of this dispatch)**: the case text implies a single combined "AgentName vX.X" chip; the live composer actually renders the agent name and its version as **two separate, adjacent testid-backed elements** in the same `Model Selector Menu` group — `ChatPage.switch_participant_button` (`chat-switch-participant-button`, accessible name "Switch Agent", shows the agent name + icon) and `ChatPage.chat_version_selector_trigger` (`chat-version-selector-trigger`, shows the version string, e.g. "skills-v3.0") — confirmed live for both agents. This case only needs to confirm SOME agent-identifying chip is visible in the input bar; the exact combined-vs-split shape is ELITEA-2362's job to formally document/clarify, not re-litigated here.
   - **Verify**: `ChatPage.is_agent_participant_in_composer(agent_name)` returns `True` for the active agent, and `chat_version_selector_trigger` is visible — confirmed live.
8. Verify the agent appears under the AGENTS section in the Participants panel on the right.
   - **Verify**: `ChatPage.expand_participants_panel_via_toggle()` then `get_participant_row_by_name(agent_name)` finds a row under an "Agents" section heading showing the agent name + version (e.g. "User Story Creator" / "skills-v3.0") — confirmed live (full Participants panel expanded via `chat-participants-panel-toggle-button`, showing "Agents" heading with the participant row, plus the Context Budget section below it — see step 16).
9. Click the message input field and type a message (e.g., "execute agent").
   - **Verify**: click + type succeeds via `ChatPage.message_input` (`chat-message-input`) — confirmed live, text "execute agent" entered.
10. Verify the typed text appears in the input field and the send button becomes active.
    - **Verify**: `message_input` value reads "execute agent"; `ChatPage.send_button` (`chat-send-button`, accessible name "send your question") becomes visible/enabled once text is present (confirmed live: the send button is not rendered at all on an empty input, and appears enabled the moment text is typed) — reuse `is_send_button_enabled()`.
11. Click the send button.
    - **Verify**: click succeeds via `send_button` — confirmed live, message submitted.
12. Verify the user message is displayed in the chat as sent.
    - **Verify**: a new message `<li>` renders showing sender "Test Bot" → "to" → the active agent name, body text "execute agent" — confirmed live via `ChatPage.get_message_count()` / `get_last_message_text()` idiom (message count went from 0 to 1 immediately on send).
13. Verify the agent begins processing (e.g., "Thought for X secs" indicator is shown).
    - **Verify**: `ChatPage.answer_thought_accordion` (`chat-answer-thought-accordion`) becomes visible reading "Thought for N secs" (confirmed live: "Thought for 5 secs", `[expanded]` state, with a model chip "Anthropic Sonnet 5" inside it).
14. Verify the agent reply is received and displayed in the chat.
    - **Verify**: `ChatPage.wait_for_ai_response(initial_count=1)` resolves (message count reaches 2 — user + AI); `get_last_message_text()` returns non-empty reply text — confirmed live (multi-paragraph reply asking for user-story details, since the sent message "execute agent" carried no actual feature content — expected/correct agent behavior for this prompt, not a defect).
15. Verify the new conversation appears in the chat list in the left sidebar under "Today".
    - **Verify**: `ChatPage.is_conversation_in_group(conversation_id, group="today")` returns `True` — confirmed live: the conversation ("Execute agent", auto-named from the first message) appeared under the sidebar's "Today" date-group heading immediately after sending.
16. Verify the Context Budget counter in the bottom right updates (if context management is active).
    - **Verify**: before the message is sent, no Context Budget panel/percentage renders at all (`is_context_budget_panel_visible()` — the panel/compact indicator only exists once ≥1 message has been sent, confirmed live: the collapsed bottom-right indicator was entirely absent pre-send). After send + AI reply: `ChatPage.wait_for_context_budget_panel()` becomes visible; the compact bottom-right indicator reads **"2%"**; the expanded panel (via `chat-participants-panel-toggle-button`) shows **"239 / 10 000 tokens"**, **"2%"**, `context_budget_messages_count` = **"2"**, `context_budget_summaries_count` = **"0"** — confirmed live via `wait_for_context_budget_messages_count("2")`. This is the "counter updates" the case asks for: 0/absent → a real, non-zero value once the exchange completes.

## Expected Results
- Clicking a no-starters Catalog agent card opens its preview modal showing the CHAT STARTERS / Welcome Message empty-state copy (case text: "CONVERSATION STARTERS" / "WELCOME MESSAGE" — drift, tracked in #1042).
- Clicking "Start Chat" (case text: "Start conversation" — same #1042 drift) redirects to `/chat` and opens a brand-new conversation showing the "Hello, {user}! What can I do for you today?" greeting.
- The active agent is shown as a chip/button in the message-input composer (name + version, as two adjacent elements — see step 7 nuance) and under an "Agents" heading in the expanded Participants panel.
- Typing enables the send button; sending displays the user's message, a "Thought for N secs" processing indicator, then the agent's reply.
- The new conversation appears under "Today" in the sidebar.
- The Context Budget indicator goes from absent/0 to a real percentage + token/message count once the exchange completes.
- Zero console errors (beyond a pre-existing unrelated dev-tooling warning), zero 4xx/5xx.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click a no-starters agent card | Control responds; expected next state shown | step 2 | agent-details GET fires, resolves 200 | asserted |
| 3 Modal shows name/description/CONVERSATION STARTERS/WELCOME MESSAGE | Condition holds as described | step 3 | `modal_agent_name`, `modal_chat_starters_section`, `modal_welcome_message_section` | asserted *(section-label drift, see clarification, already tracked #1042)* |
| 4 Click "Start conversation" | Control responds; expected next state shown | step 4 | `modal_start_chat_button` click | asserted *(label drift, same #1042)* |
| 5 New chat created, redirected to Chat interface | Condition holds as described | step 5 | URL matches `/chat`, `ChatPage.wait_for_page_load()` | asserted |
| 6 Welcome message "Hello, [user]! What can I do for you today?" | Condition holds as described | step 6 | `chat-new-conversation-greeting` text | asserted |
| 7 Agent chip (e.g. "Business Analyst v2.1") visible in input bar | Condition holds as described | step 7 | `chat-switch-participant-button` + `chat-version-selector-trigger` visible | asserted *(combined-vs-split nuance out of scope — see ELITEA-2362/#870)* |
| 8 Agent appears under AGENTS section in Participants panel | Condition holds as described | step 8 | expanded panel "Agents" heading + `get_participant_row_by_name()` | asserted |
| 9 Click input field, type message | Control responds; expected next state shown | step 9 | `chat-message-input` value | asserted |
| 10 Typed text appears, send button becomes active | Condition holds as described | step 10 | `message_input` value + `is_send_button_enabled()` | asserted |
| 11 Click send button | Control responds; expected next state shown | step 11 | `chat-send-button` click | asserted |
| 12 User message displayed as sent | Condition holds as described | step 12 | message count 0→1, `get_last_message_text()` | asserted |
| 13 Agent processing indicator ("Thought for X secs") shown | Condition holds as described | step 13 | `chat-answer-thought-accordion` text | asserted |
| 14 Agent reply received and displayed | Condition holds as described | step 14 | `wait_for_ai_response()`, message count 1→2 | asserted |
| 15 New conversation appears in sidebar under "Today" | Condition holds as described | step 15 | `is_conversation_in_group(conv_id, "today")` | asserted |
| 16 Context Budget counter updates | Condition holds as described | step 16 | `wait_for_context_budget_panel()` + `wait_for_context_budget_messages_count("2")` | asserted |
| Expected Final State: Context Budget counter updates | — | step 16 | as above | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- **step 2** asserts the underlying agent-details network request resolves 200, not merely "modal appears" — *added: deterministic ready-signal, same rationale as the sibling ELITEA-2356 AFS (avoids the known #1043 race class on Start Chat).*
- **steps 3-16** each assert zero new console errors / zero 4xx-5xx as a standing side-channel check (per this skill's discipline) rather than a single end-of-test check — *added: isolates exactly which interaction would have introduced a regression, not just "somewhere in the flow".*
- **step 16** additionally asserts the PRE-send absent state (no Context Budget indicator exists at all before the first message) — *added: "updates" is only provable by comparing a real before/after, not by reading the post-send value alone; the case text says "verify... updates" but doesn't specify the before-state, so this fills that gap with the actual observed live behavior (absent → 2%).*
- **step 7** documents, but explicitly defers to ELITEA-2362, the combined-vs-split chip nuance — *added: prevents this case's implementation from either silently asserting a non-existent combined string or duplicating ELITEA-2362's not-yet-written deeper exploration.*

## Cleanup

- The conversation created in step 5 (auto-named "Execute agent" from the sent message, id `7088` in this exploration run) should be deleted via `ConversationAPI.delete_conversation(conv_id)` in a `finally` block, matching the precedent in `test_agent_hub_participant_readonly_canvas_llm_override.py` (ELITEA-2075) — parse `conv_id` from the post-send URL (`/chat/{id}?...`) via `re.search(r"/chat/(\d+)", page.url)`. No agent state (like/unlike, starters, welcome message) is modified by this case — read/interact-only on the agent side.

## Concrete Handles (discovered/confirmed during exploration — all pre-existing, zero new testids needed)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | needs re-verification against `origin/main` (see surface digest's PROVENANCE CORRECTION) — confirmed present + functional on `automation/testids` (dev server) |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` / `get_agent_card()` (`[data-testid^="catalog-agent-card-"]`) | none | confirmed present + functional on `automation/testids` |
| Modal open/close/name/sections/Start Chat | `AgentHubPage.open_agent_by_name()`, `modal_agent_name`, `modal_chat_starters_section`, `modal_welcome_message_section`, `click_start_chat()` | none | pre-existing, see `l3_agent-hub-open-agent-detail-modal_ELITEA-2356.md` § Concrete Handles for full provenance detail |
| Blank-conversation greeting | `ChatPage.new_conversation_greeting` (`chat-new-conversation-greeting`) | none | confirmed present + functional live this dispatch |
| Composer agent-name chip | `ChatPage.switch_participant_button` (`chat-switch-participant-button`) | none | confirmed present + functional live this dispatch |
| Composer version chip | `ChatPage.chat_version_selector_trigger` (`chat-version-selector-trigger`) | none | confirmed present + functional live this dispatch |
| Participants panel toggle | `ChatPage.participants_panel_toggle_button` (`chat-participants-panel-toggle-button`) | none | confirmed present + functional live this dispatch |
| Message input | `ChatPage.message_input` (`chat-message-input`) | none | confirmed present + functional live this dispatch |
| Send button | `ChatPage.send_button` (`chat-send-button`) | none | confirmed present + functional live this dispatch |
| Thought/reasoning accordion | `ChatPage.answer_thought_accordion` (`chat-answer-thought-accordion`) | none | confirmed present + functional live this dispatch |
| Sidebar "Today" grouping | `ChatPage.CONVERSATION_GROUP_HEADER` / `is_conversation_in_group()` (`chat-conversation-group-header-{group}`) | none | confirmed present + functional live this dispatch |
| Context Budget panel/counters | `ChatPage.wait_for_context_budget_panel()`, `context_budget_messages_count`, `context_budget_summaries_count` | legacy `fallback=` present on `context_budget_panel`/`context_budget_tokens_display` fields (pre-existing tech debt — do NOT extend this pattern to any new field) | confirmed present + functional live this dispatch |

No `testid needed` rows — every element this case's own steps touch already has a page-object method or `LocatorDescriptor` field, confirmed live.

## Network Behavior
- `GET /api/v2/elitea_core/public_application/prompt_lib/{id}` — modal open (id 31 / 172 confirmed → `200`).
- `POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}` → `201` — new conversation created on "Start Chat".
- `PATCH /api/v2/elitea_core/entity_settings/prompt_lib/{project_id}/{conv_id}`, `PUT .../conversation/prompt_lib/{project_id}/{conv_id}`, `POST .../participants/prompt_lib/{project_id}/{conv_id}`, `POST .../select_conversation/prompt_lib/{project_id}/{conv_id}` — all `200`, conversation setup sequence following creation.
- `GET /api/v2/elitea_core/context_analytics/prompt_lib/{project_id}/{conv_id}` — fires (twice, confirmed live) after the message exchange; source of the Context Budget panel's token/message counts.
- No 4xx/5xx observed anywhere in the whole flow (Catalog → modal → chat → send → reply → sidebar → Context Budget).

## Known Defects Found During Exploration
- **[CLARIFICATION, already tracked, not re-filed]** [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) — case text says "CONVERSATION STARTERS" section / "Start conversation" button; live product reads "CHAT STARTERS" / "Start Chat" respectively (also "WELCOME MESSAGE" all-caps vs live "Welcome Message" title-case). Filed from a sibling case, explicitly names ELITEA-2368 as an affected sibling. Automation asserts the live copy as correct expected behavior.
- **[Deferred, not filed]** Case step 7's implied single combined "AgentName vX.X" chip is actually two separate adjacent elements live (`chat-switch-participant-button` + `chat-version-selector-trigger`). Not filed as its own clarification because a dedicated sibling TMS case, [ELITEA-2362/#870](https://github.com/EliteaAI/elitea-testing-public/issues/870) ("Agent Hub — agent chip visible in message input with version and settings"), exists specifically to explore this element and is not yet analysed — filing here would risk a duplicate once that case is picked up. Future analyst on ELITEA-2362: this is your target element; the split shows the agent name and version as two adjacent testid-backed buttons, not one combined chip.
- None else found — zero console errors (beyond a pre-existing unrelated `docx-js-editor` dev-tooling warning, unrelated to this flow), zero 4xx/5xx, all 16 case steps reproduced live and match the case's core intent.

## Blocked Steps
None — all 16 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- **No new page object needed** — both `AgentHubPage` and `ChatPage` already carry every field/method this case needs; the implementer composes them exactly as `test_agent_hub_participant_readonly_canvas_llm_override.py` (ELITEA-2075) already does (same two page objects, same composition pattern, `from api import ConversationAPI` for cleanup).
- Suggested test file location: `automation/tests/ui/chat/` (matches the ELITEA-2075 precedent for this exact Catalog→chat cross-surface shape — the bulk of the case's assertions are chat-surface, only steps 1-4 touch the Catalog/agent-hub surface as a setup path), OR `automation/tests/ui/agents/` (matches this AFS's own `test-specs/agent-hub/` location and the rest of the agent-hub sibling family, e.g. `test_agent_hub_open_agent_detail_modal.py`). Either is defensible; the implementer should pick based on which existing test-file cluster it will most often be run alongside. Declared improvisation: no canon rule pins this cross-surface case to one directory.
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy) — no new `LocatorDescriptor` fields needed for this case; every locator used already exists.
- AI reply wait: use `ChatPage.wait_for_ai_response(initial_count=1, timeout=AI_RESPONSE_TIMEOUT)` — never a sleep (`.agents/testing.md`). 60-90s timeout per existing precedent (`AI_RESPONSE_TIMEOUT` constant in ELITEA-2075's test).
- Context Budget: call `wait_for_context_budget_panel()` before reading any counter (the panel doesn't exist pre-send — confirmed live), then `wait_for_context_budget_messages_count("2")` before reading the percentage/token text, per the existing docstring's own race-condition warning (a one-shot read immediately after the panel appears can catch a stale "0").
- Marker suggestion: `@pytest.mark.p2` (medium priority → l3), `@pytest.mark.regression`, `@pytest.mark.chat` (matches the ELITEA-2075 precedent for this cross-surface shape) or `@pytest.mark.agents` depending on the chosen file location above.
- Cleanup: capture `conv_id` from `page.url` after step 5/11 (regex `r"/chat/(\d+)"`), delete via `ConversationAPI(browser_cookies=_browser_cookies).delete_conversation(conv_id)` in a `finally` block (ELITEA-2075 precedent).
