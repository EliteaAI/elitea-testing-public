# Test Case: Create New Conversation via Agent HUB — Using a Conversation Starter

## Metadata
- **TMS ID**: ELITEA-2093
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog` → `/chat`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (agent, combined analyst+implementer dispatch)
- **Status**: **ready-for-automation** — all 8 case steps reproduced live end-to-end (Catalog → modal → click starter tile IN the modal → chat opens directly, no "Start Chat" click involved → composer pre-populated → agent chip/version + all 3 starters shown → send → reply → sidebar auto-naming). Zero console errors, zero 4xx/5xx across the whole interaction. One already-tracked case-text drift (§ Known Defects, same #1042 the sibling ELITEA-2368/2369 hit).
- **Related surfaces reused**: `AgentHubPage` (`open_agent_by_name()`, `get_modal_starter_items()`) for steps 1-3; `ChatPage` (`wait_for_page_load()`, `is_agent_participant_in_composer()`, `switch_participant_button`, `chat_version_selector_trigger`, `get_chat_starter_tiles()`, `message_input`, `send_button`/`is_send_button_enabled()`, `wait_for_message_count()`, `wait_for_ai_response()`, `wait_for_naming_label_to_resolve()`, `is_conversation_in_group()`, `get_conversation_item_in_group()`) for steps 4-8 — all pre-existing, confirmed live this dispatch. **One new page-object method added this dispatch**: `AgentHubPage.click_modal_starter_item()` (see § Concrete Handles) — no new testid needed, `catalog-agent-modal-starter-item` already exists on `automation/testids` (added by the ELITEA-2369 dispatch).
- **Not a target for `extend-existing`/`already-covered`**: the two existing Catalog→chat siblings — `test_agent_hub_start_conversation_no_starters.py` (ELITEA-2368) and `test_agent_hub_start_conversation_with_starters.py` (ELITEA-2369) — both drive the flow through the **"Start Chat" button**, then (ELITEA-2369 only) click a starter tile **inside the chat area** after landing. Neither ever clicks a starter tile **inside the modal itself** — this case's entire flow (`AgentConversationStarterItem.onClick` → `onSelectStarter` → `onStartConversation` + `onClose()`, confirmed via source) is a materially different code path: the modal closes AND navigates AND pre-populates the composer off a SINGLE click, with no "Start Chat" click ever involved. Zero of this case's own steps (3-6) are exercised by either sibling. Genuinely fresh coverage: `ready-for-automation`.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- Active project context is "Private" (confirmed live: `${TEST_USER}`'s default project on localhost reads "Project: Private" with no explicit switch — same precedent as ELITEA-2368/2369, `test-specs/agent-hub/_surface.md` § Project context).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.
- Catalog agent: **"Assistant for ELITEA Documentation"** (case's own literal example — confirmed present live, application id `16`, category "Elitea", 3 configured CHAT STARTERS + a Welcome Message).
- Starter to click (case's own literal example, confirmed present live verbatim, no apostrophe/casing drift): *"Tell me about Elitea"*.
- Other 2 starters rendered alongside it (confirmed live, used only to verify the "all three starter prompts" count in step 6): *"Help me configure Jira toolkit?"*, *"Can I use Azure dev ops repo through Elitea"*.

(No other test data required — case's own Test Data table lists only the agent name + starter.)

## Test Steps

1. Navigate to Agent HUB from the left sidebar (`/elitea-catalog`).
   - **Verify**: page loads — `catalog-page-heading` visible (reuse `AgentHubPage.navigate()` / `wait_for_page_load()`).
2. Click on an agent card with predefined conversation starters (e.g. "Assistant for ELITEA Documentation").
   - **Verify**: click succeeds; the underlying `GET /api/v2/elitea_core/public_application/prompt_lib/16` request fires and resolves `200` (confirmed live) — reuse `AgentHubPage.open_agent_by_name()`, which already waits on this exact response.
3. Verify the CONVERSATION STARTERS section shows clickable starter buttons.
   - **CASE-TEXT DRIFT (CLARIFICATION, already tracked, not re-filed)**: live section header reads **"CHAT STARTERS"** (not "CONVERSATION STARTERS") — confirmed live, tracked in [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) (already names ELITEA-2368/2369 as affected siblings; this case is the same drift, same root component).
   - **Verify**: `AgentHubPage.modal_chat_starters_section` (`catalog-agent-modal-chat-starters-section`) visible, containing **3** starter items (confirmed live): *"Help me configure Jira toolkit?"*, *"Tell me about Elitea"*, *"Can I use Azure dev ops repo through Elitea"* — via `AgentHubPage.get_modal_starter_items()` (`catalog-agent-modal-starter-item`, pre-existing testid added by the ELITEA-2369 dispatch).
4. Click the "Tell me about Elitea" starter button.
   - **Verify**: `AgentModal.jsx`'s `onSelectStarter` handler fires on this SINGLE click — confirmed via source: it calls `onStartConversation(starter)()` (dispatches `setSelectedAgentInfo({agent, starter})`, then `navigate(Chat, {search:'create=1'})`) AND `onClose()` synchronously, no separate "Start Chat" click needed (materially different from the ELITEA-2368/2369 siblings' flow). Confirmed live: the modal closed and `page.url` became `/chat` off this one click. New page-object method `AgentHubPage.click_modal_starter_item(match_text)` (§ Concrete Handles) — no #1043-style race: the starter items only render once `agentDetails` has committed, so step 3's own "wait for starter items visible" already clears the same async gap #1043's "Start Chat" click has to work around separately.
5. Verify the selected starter text is pre-populated in the message input field.
   - **Verify**: `ChatPage.message_input.input_value()` reads exactly `"Tell me about Elitea"` — confirmed live (`NewConversationView.jsx`'s `onSendStarter()` → `chatInput.current.setValue(starter)`, fired ~100ms after the new-conversation view mounts with a `selectedAgentStarter` from Redux).
6. Verify the agent name and version are in the input bar and all three starter prompts are displayed as clickable suggestions.
   - **Verify**: `ChatPage.is_agent_participant_in_composer("Assistant for ELITEA Documentation")` returns `True`; `chat_version_selector_trigger` text reads `"v1.0"` (confirmed live, matches the case's own "agent name and version" wording — same combined-vs-split nuance as ELITEA-2368/2369, out of scope here per dedicated sibling ELITEA-2362/#870). `ChatPage.get_chat_starter_tiles()` (`chat-conversation-starter-tile`, pre-existing testid, `NewConversationView.jsx`'s own starters render — same `selectedParticipant.version_details.conversation_starters` list as the modal) resolves to **3** tiles, same 3 starter texts as step 3 — confirmed live.
7. Click the Send button.
   - **Verify**: `ChatPage.send_button` (`chat-send-button`) click succeeds; `page.url` matches `/chat/\d+` once the conversation is created (confirmed live: conversation id `8140` this exploration run); `ChatPage.wait_for_message_count(initial_count + 1)` confirms the user's message renders; `ChatPage.wait_for_ai_response()` confirms a non-empty agent reply (confirmed live: the agent replied explaining it lacks a documentation-fetch tool in this environment — content is agent-authored free text, asserted as non-empty only, never a literal string).
8. Verify a new entry appears in Today with a "Naming…" placeholder that resolves to an auto-generated title.
   - **Verify**: `ChatPage.wait_for_naming_label_to_resolve()` (no-op-safe if the placeholder already resolved by the time this reads — confirmed live: naming resolved to a real title, `"Tell about Elitea"` this run, essentially immediately, no observable intermediate "Naming" DOM state at the granularity a UI snapshot can catch) then `ChatPage.is_conversation_in_group(conv_id, group="today")` returns `True`, and `get_conversation_item_in_group(conv_id, "today").text_content()` is non-empty and does NOT equal/contain the literal placeholder `"Naming"` — same "not stuck on placeholder" assertion shape as `test_conversation_management.py` Step 6.

## Expected Results
- Clicking a starters-bearing Catalog agent card opens its preview modal showing the CHAT STARTERS section with 3 clickable starter options (case text: "CONVERSATION STARTERS" — drift, tracked #1042).
- Clicking a starter tile **inside the modal** closes the modal and navigates directly to `/chat` with a brand-new conversation — no "Start Chat" click involved.
- The composer is pre-populated with the exact clicked starter text; the active agent is shown as a chip/button pair (name + version) in the composer; the SAME 3 starters render as clickable tiles in the chat area.
- Sending the pre-populated message displays it in the chat, then produces a non-empty agent reply.
- The new conversation appears under the sidebar's "Today" date-group with a real (non-"Naming") title.
- Zero console errors, zero 4xx/5xx.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent HUB | Agent HUB page opens | step 1 | `catalog-page-heading` visible | asserted |
| 2 Click agent card with starters | Detail modal opens | step 2 | agent-details GET fires, resolves 200; `modal_agent_name`/`modal_dialog` visible | asserted |
| 3 CONVERSATION STARTERS section shows clickable starter buttons | Starter buttons visible | step 3 | `modal_chat_starters_section` + `get_modal_starter_items().count() == 3` | asserted *(section-label drift, #1042)* |
| 4 Click "Tell me about Elitea" starter button | Modal closes; Chat opens with agent pre-loaded | step 4 | `click_modal_starter_item()`; `modal_dialog` hidden; `page.url` matches `/chat` | asserted |
| 5 Selected starter text pre-populated in input field | Starter text is in the input field | step 5 | `message_input.input_value() == "Tell me about Elitea"` | asserted |
| 6 Agent name+version in input bar; all 3 starters shown as clickable suggestions | Agent chip and starters visible | step 6 | `is_agent_participant_in_composer()` + `chat_version_selector_trigger` text; `get_chat_starter_tiles().count() == 3` | asserted |
| 7 Click Send button | Pre-populated message is sent; agent responds | step 7 | `send_button` click; `wait_for_message_count()`; `wait_for_ai_response()` + non-empty reply | asserted |
| 8 New entry in Today with "Naming…" placeholder resolving to auto-generated title | Conversation auto-named | step 8 | `wait_for_naming_label_to_resolve()`; `is_conversation_in_group(conv_id, "today")`; title text non-empty, not "Naming" | asserted |
| Expected Final State: conversation opened with starter pre-populated, agent responds, conversation auto-named | — | steps 5, 7, 8 | as above | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- **step 2** asserts the underlying agent-details network request resolves 200, not merely "modal appears" — *added: deterministic ready-signal, same rationale as the ELITEA-2368/2369 siblings (this case has no #1043-style race on the click itself, but the modal's own content-ready signal is still worth a real assertion rather than a blind read).*
- **steps 1-8** each side-channel-check zero new console errors / zero 4xx-5xx rather than a single end-of-test check — *added: isolates exactly which interaction would have introduced a regression, same pattern as ELITEA-2368/2369.*
- **step 4** documents (docstring + AFS) that this flow has NO #1043-style click-race to work around, unlike the siblings' "Start Chat" button — *added: prevents a future implementer from reflexively copying the siblings' `page.wait_for_timeout(1000)` guard onto a click that doesn't need it (the starter items' own rendering already gates on the same async data).*
- **step 8** documents that "Naming" resolved effectively instantly in this live run (no observable intermediate placeholder state) — *added: prevents a future implementer from writing a brittle "assert the Naming placeholder IS visible first" step; the case's own wording ("resolves to") only requires the END state, and `wait_for_naming_label_to_resolve()` is already no-op-safe for a placeholder that never renders long enough to observe.*

## Cleanup

- The conversation created in step 7 (auto-named `"Tell about Elitea"` this exploration run, id `8140`) should be deleted via `ConversationAPI.delete_conversation(conv_id)` in a `finally` block, matching the ELITEA-2368/2369/ELITEA-2075 precedent — parse `conv_id` from the post-send URL (`/chat/{id}?...`) via `re.search(r"/chat/(\d+)", page.url)`. No agent state (like/unlike, starters, welcome message) is modified by this case — read/interact-only on the agent side.

## Concrete Handles (discovered/confirmed during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `AgentHubPage.page_heading` (`catalog-page-heading`) | none | pre-existing — re-verify against `origin/main` per surface digest's PROVENANCE CORRECTION before citing as on-main |
| Agent card | `AgentHubPage.AGENT_CARD_PREFIX` / `get_agent_card()` (`[data-testid^="catalog-agent-card-"]`) | none | pre-existing, confirmed live (id 16 = "Assistant for ELITEA Documentation") |
| Modal open/name/sections | `AgentHubPage.open_agent_by_name()`, `modal_agent_name`, `modal_chat_starters_section`, `modal_dialog` | none | pre-existing, confirmed live this dispatch |
| Modal starter item | `AgentHubPage.get_modal_starter_items()` (`catalog-agent-modal-starter-item`) | none | pre-existing testid (ELITEA-2369 dispatch), confirmed live — 3 items render for this agent |
| **Click a specific modal starter item (NEW METHOD, no new testid)** | `AgentHubPage.click_modal_starter_item(match_text)` — filters `MODAL_STARTER_ITEM` by `has_text`, same idiom as `ChatPage.click_chat_starter_tile()` | none | **added this dispatch** — no page-object method previously existed to click ONE modal starter (only `get_modal_starter_items()` to count them); the testid itself already existed |
| Blank-conversation composer | `ChatPage.message_input` (`chat-message-input`) | none | pre-existing, confirmed live this dispatch |
| Composer agent-name chip | `ChatPage.switch_participant_button` (`chat-switch-participant-button`) | none | pre-existing, confirmed live this dispatch |
| Composer version chip | `ChatPage.chat_version_selector_trigger` (`chat-version-selector-trigger`) | none | pre-existing, confirmed live this dispatch ("v1.0") |
| Chat-area starter tile | `ChatPage.get_chat_starter_tiles()` (`chat-conversation-starter-tile`) | none | pre-existing testid (ELITEA-2369 dispatch, wired at `NewConversationView.jsx`'s call site — exactly the call site this case's flow renders through too), confirmed live — 3 tiles |
| Send button | `ChatPage.send_button` (`chat-send-button`) / `is_send_button_enabled()` | none | pre-existing, confirmed live this dispatch |
| Sidebar date-group scoping | `ChatPage.is_conversation_in_group()` / `get_conversation_item_in_group()` (`CONVERSATION_GROUP_HEADER`/`CONVERSATION_ITEM` templated constants) | none | pre-existing (ELITEA-2091 addition), confirmed live this dispatch |
| Naming-placeholder resolution | `ChatPage.wait_for_naming_label_to_resolve()` | none | pre-existing, confirmed live this dispatch (no-op path exercised — placeholder never observed as visible) |

One new page-object METHOD this dispatch (`click_modal_starter_item`) — zero new testids, per canon ruling #511 (the testid this case touches was already added and referenced by a prior case).

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?query=&statuses=published&...` → `200` — Catalog bulk listing (Trending/category sections).
- `GET /api/v2/elitea_core/public_application/prompt_lib/16` → `200` — modal open (agent-details fetch).
- `POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}` → `201` — new conversation created on Send (NOT on the starter click — the click only navigates client-side with `create=1`; the conversation itself is created server-side once Send fires, confirmed live).
- `PATCH /api/v2/elitea_core/entity_settings/prompt_lib/{project_id}/{conv_id}`, `PUT .../conversation/prompt_lib/{project_id}/{conv_id}`, `POST .../participants/prompt_lib/{project_id}/{conv_id}`, `POST .../select_conversation/prompt_lib/{project_id}/{conv_id}` — all `200`, conversation setup sequence following Send.
- `GET /api/v2/elitea_core/context_analytics/prompt_lib/{project_id}/{conv_id}` — fires after the message exchange.
- No 4xx/5xx observed anywhere in the whole flow (Catalog → Private project → modal → click starter in modal → chat pre-populated → send → reply → sidebar Today group).

## Known Defects Found During Exploration
- **[CLARIFICATION, already tracked, not re-filed]** [EliteaAI/elitea-testing-public#1042](https://github.com/EliteaAI/elitea-testing-public/issues/1042) — case text says "CONVERSATION STARTERS" section; live product reads "CHAT STARTERS". Already names ELITEA-2368/2369 as affected siblings — this case hits the identical drift on the identical component (`AgentConversationStarters.jsx`); cite, don't re-file.
- **[Observed, not a defect]** The auto-generated conversation title dropped a word from the sent message this run ("Tell me about Elitea" → sidebar title "Tell about Elitea") and appeared to resolve near-instantly rather than staying on a visible "Naming" placeholder for any observable duration. Not asserted as a specific string (case text only requires "resolves to an auto-generated title", i.e. NOT stuck on the placeholder) — see AFS step 8 / Axis 2.
- None else found — zero console errors, zero 4xx/5xx, all 8 case steps reproduced live and match the case's core intent (starter text sourced correctly from the agent's own configuration, click-in-modal correctly both navigates and populates without an extra "Start Chat" click, send flow and reply and sidebar naming all work as expected).

## Blocked Steps
None — all 8 case steps were reached and observed live.

## Automation Hints
- Framework: Playwright + pytest (this project), Playwright MCP tools used this dispatch.
- **One new page-object method needed** (see § Concrete Handles) — `AgentHubPage.click_modal_starter_item(match_text)`. Zero new testids (`catalog-agent-modal-starter-item` and `chat-conversation-starter-tile` both already exist on `automation/testids` from the ELITEA-2369 dispatch).
- **No #1043-style timing workaround needed for the modal-starter click** (unlike ELITEA-2368/2369's "Start Chat" click) — the starter items only render once `agentDetails` has committed, so step 3's own wait for `get_modal_starter_items().first` to be visible already clears the same async gap. Do NOT copy the siblings' `page.wait_for_timeout(1000)` onto this click.
- Suggested test file location: `automation/tests/ui/chat/` (matches the ELITEA-2368/ELITEA-2369/ELITEA-2075 precedent — same cross-surface Catalog→chat shape, majority of assertions are chat-surface).
- Selector policy: testid-only, no fallback (`.agents/testing.md` § Locator policy).
- AI reply wait: use `ChatPage.wait_for_ai_response(initial_count=1, timeout=AI_RESPONSE_TIMEOUT)` — never a sleep. Budget the same 60-90s timeout as ELITEA-2075/ELITEA-2368/2369 (this exploration run took well under 60s).
- Step 8: `wait_for_naming_label_to_resolve()` is no-op-safe when the "Naming" placeholder never renders long enough to be observed (confirmed live this dispatch) — always call it before reading the sidebar title, never skip straight to a title read.
- Marker suggestion: `@pytest.mark.p1` (high priority → l2), `@pytest.mark.regression`, `@pytest.mark.chat`.
- Cleanup: capture `conv_id` from `page.url` after Send (regex `r"/chat/(\d+)"`), delete via `ConversationAPI(browser_cookies=_browser_cookies).delete_conversation(conv_id)` in a `finally` block (ELITEA-2075/ELITEA-2368/2369 precedent).
