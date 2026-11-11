# Test Case: Run Skill from Catalog Skills page and verify message exchange

## Metadata
- **TMS ID**: ELITEA-4633
- **Priority**: l1 (TMS: critical regression)
- **Environment explored**: DEV `https://dev.elitea.ai/app`, project Private (575), `autotest_user_admin`, 2026-11-11 (scripted python-playwright probes, storage state from `dev_storage_state.py`; 3 full runs)
- **Status**: **ready-for-automation**
- **Analyst**: qa-engineer, batch `skills-4633`
- **surface_key**: catalog-skill-run-to-chat
- **Neighbours read**: ELITEA-4628 AFS (plus-menu adds the same catalog `code-reviewer` skill as participant; same `chat-participant-catalog-tag` / `v1.0` observables, but via a different entry point and no message sent), `agent_hub_page.py` (Catalog page object, `skills_tab`, `SKILL_CARD_PREFIX`), agent_hub start-conversation test (agent analog). Not already-covered: no merged spec clicks `catalog-skill-run-button` (grep in automation/ -> none).

## Preconditions
- Logged in (`auth_state`). Catalog (project 1) holds published skill `code-reviewer` (resolve by NAME at runtime; fail loudly if absent - shared env data).
- Platform banner `platform-banner-close` can appear a few seconds after load and intercept pointer events (also on the chat send button); dismiss it (wait up to ~5s) before clicking; send button click may need `force=True` (existing `ChatPage.send_message` already does).
- **Cleanup required**: Run click **persists a conversation immediately** (`POST .../conversations/prompt_lib/575` 201, name `Run code-reviewer`). Delete in teardown via `ConversationAPI.delete_conversation(id)` (`api/client.py:486`); id from URL `/chat/(\d+)`. In one early probe a second `POST conversations` fired after send (two conversations 2008/2009 created); in two later runs only one. Teardown should delete the URL id AND any extra conversation titled `Run code-reviewer` created by the test (list + name filter) to be safe.

## Observed flow (all executed live)
1. `/app/elitea-catalog` -> heading `catalog-page-heading` "Welcome to ELITEA Catalog!" (`AgentHubPage` fields). Default tab Agents.
2. Click `catalog-skills-tab` -> `aria-selected=true`, URL `?tab=skills`.
3. **Skill cards carry NO `catalog-skill-card-*` testid on DEV today** (0 matches of `[data-testid^="catalog-skill-card-"]` although `agent_hub_page.py` declares `SKILL_CARD_PREFIX`; ELITEA-2370 relied on it - possible regression/undeployed, flag). Only `catalog-skill-run-button` (x16, one per card, `aria-label="run skill"`, tooltip "Run" on hover) exists. Card root is `div.MuiCard-root[data-tour="elitea-catalog-entity-card"]` (name in a `span` heading).
4. Reach one card deterministically: type `code-reviewer` into `catalog-search-input` (placeholder "Search for skills", live filter ~3s) -> exactly 1 `catalog-skill-run-button`. (Name-scoped alternative: card = ancestor of the run button containing the name; avoid positional picks.)
5. Hover run button -> role=tooltip "Run" (step 4 "highlights if applicable": observed tooltip only).
6. Click run -> `POST /conversations/prompt_lib/575` 201 -> `POST select_conversation/.../{id}` 200 -> URL `/app/chat/{id}?name=Run+code-reviewer` (suffix appears after load).
7. **No greeting message**: `chat-message-item` count 0 on the new chat (case says "Hello, Mariam! ..." - drift/clarification, assert absence not required; assert empty thread or just don't assert greeting).
8. Participants panel is collapsed -> `chat-participants-panel-toggle-button` expands. Exactly one row: `chat-participant-row-638` text `code-reviewer | Catalog | v1.0`; `chat-participant-catalog-tag` count 1 (same handles as ELITEA-4628; row id = catalog skill id 638/31 varies - match by name, do not hardcode). Section header text "SKILLS".
9. `chat-message-input` placeholder `Type your message...`.
10. Fill the case message, click `chat-send-button` (force). User message appears (`chat-message-item` #1, text contains the message, "to | code-reviewer").
11. Skill response: `chat-message-item` #2 appears after ~7s ("Thought for 7 secs", header "Skill: code-r...", model Haiku) with relevant review text (discusses `add(2,3)`, type coercion). Wait via count >=2 + non-empty text; content is LLM-generated: assert relevance loosely (non-empty, no error, contains one of `add`/`function`/`validation`/`type`), not exact text.
12. Sidebar chats list: `chat-conversation-item-{id}` (id from URL) count 1, text `Run code-reviewer` (the list item is present already right after Run, before any message). Name is `Run <skill>`, not the first message.
13. Console: only generic `404 Failed to load resource`. No functional errors.

## Handles Reference (verified on DEV 2026-11-11)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `catalog-page-heading`, `catalog-skills-tab`, `catalog-search-input` | - | testid on DEV ✓ (existing `AgentHubPage` fields) |
| testid | `catalog-skill-run-button` | - | testid on DEV ✓ - **no field in `AgentHubPage` yet; add** (single match after search filter) |
| ladder (css/role) | Run tooltip: `role=tooltip` name "Run" | `catalog-skill-run-tooltip` | ladder - optional (step 4); no testid |
| testid | `platform-banner-close` | - | testid on DEV ✓ (existing) |
| testid | `chat-participants-panel-toggle-button`, `chat-participant-row-{id}` (prefix + `has_text`), `chat-participant-catalog-tag`, `chat-message-input`, `chat-send-button`, `chat-message-item`, `chat-conversation-item-{id}` | - | testid on DEV ✓ (existing ChatPage constants/fields; see ELITEA-4628) |
| ladder (scoped text) | version text inside participant row ("v1.0") | `chat-participant-version-text` | ladder - assert via row `to_contain_text("v1.0")` (no testid) |
| ladder (scoped text) | skill-response header "Skill: code-r..." in `chat-message-item` #2 | `chat-message-sender-label` | ladder - assert via item text containing `code-reviewer` |

## Steps (AFS)
1. Open `/elitea-catalog`, dismiss banner. **Verify** `catalog-page-heading` text "Welcome to ELITEA Catalog!".
2. Click `catalog-skills-tab`. **Verify** `aria-selected="true"`.
3. Search `code-reviewer` in `catalog-search-input`. **Verify** exactly one `catalog-skill-run-button` visible (card shows name `code-reviewer`; do NOT assert `catalog-skill-card-*` - not served).
4. Hover run button. **Verify** tooltip "Run" (optional).
5. Click run button. **Verify** URL matches `/chat/(\d+)`; capture id for cleanup.
6. **Verify** sidebar `chat-conversation-item-{id}` has text `Run code-reviewer`; message thread has 0 `chat-message-item`.
7. Expand participants panel. **Verify** one participant row containing `code-reviewer`, `chat-participant-catalog-tag` text "Catalog", and "v1.0".
8. **Verify** `chat-message-input` placeholder "Type your message...".
9. Type "Review this code: function add(a, b) { return a + b; }" and send. **Verify** user message item contains the text.
10. Wait (condition) for 2nd `chat-message-item`. **Verify** non-empty text, no error toast, and relevance keyword (loose); sender text includes `code-reviewer`.
11. **Verify** chat remains in the sidebar list (`chat-conversation-item-{id}` count 1).
12. Teardown: delete conversation(s) via `ConversationAPI`.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Catalog page | heading | AFS 1 | covered (direct URL; sidebar "Catalog" nav is transit, optional) |
| 2 Skills tab | active | AFS 2 | covered |
| 3 card w/ name, icon, Run | | AFS 3 | covered via run button + name (card-root testid absent; icon not asserted) |
| 4 hover | highlight (if applicable) | AFS 4 | covered as tooltip "Run" |
| 5 click Run -> chat | navigates | AFS 5 | covered |
| 6 new chat with greeting | greeting | AFS 6 | **clarification**: no greeting rendered; thread empty |
| 7 participant + Catalog badge + v1.0 | | AFS 7 | covered |
| 8 input placeholder | | AFS 8 | covered |
| 9-10 type, send | appears | AFS 9 | covered |
| 11-13 response relevant | | AFS 10 | covered (loose keyword) |
| 14 chat in sidebar | | AFS 6, 11 | covered |
Axis 2 extras: conversation name `Run code-reviewer` (grounded: observed in sidebar + URL `?name=`); exactly one participant row.

## Clarifications (case-text drift, NOT defects)
- Greeting "Hello, <name>! What can I do for you today?" not shown for a skill-run chat on DEV.
- Participant row text is `code-reviewer | Catalog | v1.0` (full name at 1500px).
- Run-button hover shows tooltip only.

## Known defects
None filed. Observation: `catalog-skill-card-*` testid absent on DEV although the page object (ELITEA-2370) expects it - not used by this case.

## Automation Hints
- Add to `AgentHubPage`: `skill_run_button = LocatorDescriptor(testid="catalog-skill-run-button", ...)`, helper `search_and_run_skill(name)`. Reuse `click_skills_tab`, `ChatPage` participant/message fields (`expand_participants_panel_via_toggle`, `send_message`, `get_participant_row_by_name`, `wait_for_ai_response`).
- Markers: `@pytest.mark.tms("ELITEA-4633")` + `@allure.issue` pair; skills/catalog/chat + p1/regression.
- Case "Extends ELITEA-4253" (not in repo) - ignore.
