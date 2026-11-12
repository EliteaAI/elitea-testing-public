# Test Case: Run own Skill from Skills page and verify message exchange

## Metadata
- **TMS ID**: ELITEA-4634
- **Priority**: l1 (TMS: critical regression)
- **Environment explored**: DEV `https://dev.elitea.ai/app`, project Private (575), `autotest_user_admin`, 2026-11-11 (scripted python-playwright probes, storage state from `dev_storage_state.py`; 3 full runs with per-run API-created skill)
- **Status**: **ready-for-automation** (with heavy case-text drift - live contract asserted, see Clarifications)
- **Analyst**: qa-engineer, batch `skills-run-own-skill-4634`
- **surface_key**: own-skill-run-test-panel
- **Neighbours read**: ELITEA-4633 AFS + `test_catalog_skill_run_message_exchange.py` (catalog Run DOES open a persisted `/chat/{id}`; own-skill Run does NOT - different flow, not coverage), ELITEA-4631 AFS (skill test panel, `skill_api` create/delete, `SkillDetailPage.send_test_message/wait_for_test_response`), `skills_list_page.py`. Not already-covered: no merged spec clicks `skill-run-menu-item` (grep automation/ -> none).

## Clarifications (case-text drift - product is correct per story EliteaAI/elitea_issues#6922 s3.2, NOT defects)
1. **Run is not a play-icon on the card.** Card view has only "Move to folder" + "Pin to top"; no Run. Run lives in the **table-view row "more" (three-dot) menu**: item "Run" (`skill-run-menu-item`, ▶ svg). Source: `SkillRowAction.jsx` `onRun`.
2. **Run does NOT create a new chat.** It navigates to the **skill detail page** `/skills/all/{id}?focus=run` (query is dropped to `/skills/all/{id}` after load), with the right-hand **Skill test panel** open and the message input focused. Story s3.2: "Skills list row menu: Run -> opens skill detail with Run panel focused".
3. No PARTICIPANTS panel / "Catalog" badge / version badge exists in this view (`chat-participant-*` count 0). "No Catalog badge" is vacuously true; assert absence of `chat-participant-catalog-tag` only as a cheap guard.
4. Input placeholder is **empty** (not "Type your message...").
5. Sending persists a conversation (`POST /conversations/prompt_lib/575` 201) and the URL becomes `/skills/all/{id}?run={convId}`. It is `source=skill`: **not** listed in the Chats sidebar (`chat-conversation-item-*` count 0 on /app/chat after reply) and not returned by `ConversationAPI.list_conversations()` - so case step 14 "chat appears in Chats list" is **not true on DEV** (drift; do not assert; assert run-history row instead, optional).
6. Reply sender label reads `Skill: <name>` + model chip; response text `HELLO WORLD`.

## Preconditions / Test data (generate-per-test)
- `skill_api.create_skill(name=f"autotest-4634-{ts}", description="4634 probe", instructions="Convert the user text to UPPERCASE and reply with only that.")` (name <=32, lowercase/digits/hyphen). Resolve `id` from response. Delete in `finally`: `skill_api.delete_skill(id)` AND the conversation id from the `?run=` URL via `ConversationAPI.delete_conversation(id)` (verified: delete works, id from `run=(\d+)`).
- Reuses a created skill, not a pre-existing "uppercase-text-converter" (shared-data independence).
- **Platform banners**: modal `platform-banner-center` appears ~5s after load and blocks pointer events (use `ChatPage.dismiss_platform_banner_dialog`); a **corner banner** (`platform-banner-close`) then overlays the lower-right and **covers the send button** - a `force=True` click lands on the banner and silently does NOT send. Click `platform-banner-close` (wait up to ~8s) before sending, then a normal click.

## Observed flow (all executed live)
1. `/app/skills/all` loads (first load can take >30s; wait on `entity-card`). Dismiss modal banner.
2. Table view: click `agent-table-view-button` (shared ViewToggle testid; `agent-card-view-button` is the card one).
3. Row for the skill: its overflow button is `<button id="{skillId}-skill-action" aria-label="more">` (no testid; id is stable per skill, `$="-skill-action"`). Table rows have **no testid**; do not use positional picks - use the id template.
4. Click it -> `role=menu` with items `Run`, `Move to folder`, `Delete`. `skill-run-menu-item` testid exists on **every row's hidden menu** (20 matches in DOM) - must be scoped to the open menu: use `get_by_role("menuitem", name="Run", exact=True)` (unique among open menus) .
5. Click Run -> URL `/app/skills/all/{id}?focus=run`; `skill-test-panel` visible; focus on `chat-message-input` (placeholder ""); `chat-message-item` count 0.
6. Dismiss corner banner; fill `chat-message-input` "Convert this to uppercase: hello world"; click `chat-send-button` (single match). User message item shows text + author.
7. Reply arrives ~3s (model Haiku, "Thought for 2 secs", "Skill: <name>"): second `chat-message-item`; `skill-test-last-response` testid on it; text `HELLO WORLD`. Existing `SkillDetailPage.wait_for_test_response()` handles waiting.
8. URL -> `/skills/all/{id}?run={convId}` after reply. Reload with that URL restores both messages (2). Chats sidebar: no item (clarification 5).
9. Console: no errors. Non-socket POSTs: only `conversations/prompt_lib/575` 201.

## Handles Reference (verified on DEV 2026-11-11)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `agent-table-view-button` | - | testid on DEV ✓ (shared ViewToggle; verify not already in `SkillsListPage`) |
| ladder (css, id template) | `button[id="{skillId}-skill-action"]` (row overflow, aria-label "more") | `skill-row-action-menu-button-{}` | ladder - no testid on DEV; unique per id; `ScopedLocator`/template constant |
| role+name | `menuitem` "Run" (exact), within open menu | `skill-run-menu-item` already exists but is non-unique page-wide (hidden menus) - scope with `.within(menu)` where menu = `role=menu` visible, or use role rung | testid exists but NOT unique; role+name unique when only one menu open |
| testid | `skill-test-panel`, `chat-message-input`, `chat-send-button`, `chat-message-item`, `skill-test-last-response`, `skill-run-history-button` | - | testid on DEV ✓ (existing `SkillDetailPage` / `ChatPage`) |
| testid | `platform-banner-center`, `platform-banner-close` | - | testid on DEV ✓ (existing) |
| testid | `chat-participant-catalog-tag` (expect count 0) | - | existing ChatPage constant |

## Steps (AFS)
1. Create skill via API; open `/skills/all`, dismiss modal banner; **Verify** skill appears in list (`entity-card-name`/ `skill_exists_in_list`).
2. Switch to table view (`agent-table-view-button`). **Verify** row for the skill exists (its `{id}-skill-action` button visible).
3. Open the row's overflow menu. **Verify** menu offers "Run" menuitem. (No Catalog badge anywhere in the row - cheap guard: `chat-participant-catalog-tag` count 0.)
4. Click "Run". **Verify** URL matches `/skills/all/{id}` (+ `focus=run` transient - use regex `/skills/all/{id}(\?.*)?$`), `skill-test-panel` visible, `chat-message-input` visible/empty, 0 `chat-message-item`.
5. Dismiss corner banner; send "Convert this to uppercase: hello world". **Verify** user `chat-message-item` contains the text.
6. Condition-wait for the reply (`wait_for_test_response()`). **Verify** `skill-test-last-response` text contains `HELLO WORLD` (case-insensitive; LLM, but instruction is deterministic - allow surrounding whitespace/punctuation), no error text.
7. **Verify** URL now matches `[?&]run=(\d+)`; capture id for cleanup. Optional: reload that URL -> 2 `chat-message-item` (persistence, story AC2).
8. Teardown: delete conversation(s) and skill.

## Coverage Map
| Case element | Expected | Covered by | Disposition |
|---|---|---|---|
| 1 Skills page | list loads | AFS 1 | covered (direct URL; sidebar nav is transit) |
| 2 skill card/row with Run (play icon) | Run visible | AFS 2-3 | **clarification**: Run is in table-row menu, not a card icon |
| 3 no Catalog badge | | AFS 3 | covered as absence guard |
| 4-5 click Run -> new chat | | AFS 4 | **clarification**: opens skill detail + test panel, no new chat |
| 6-7 participant w/ version badge, no Catalog | | - | **clarification/out-of-scope**: no participants panel in this view |
| 8 placeholder "Type your message..." | | - | **clarification**: placeholder empty; input focus + visible asserted instead |
| 9-10 type/send | message appears | AFS 5 | covered |
| 11-13 response HELLO WORLD | | AFS 6 | covered |
| 14 chat in Chats list | | - | **clarification**: skill-source runs are not in Chats sidebar; asserted `?run=` conversation persistence instead |
Axis 2 extras: `?run={id}` URL + reload restore (grounded: observed, story AC2).

## Known defects
None filed. Observations: (a) corner banner covers the test-panel send button on DEV (env noise, handled by dismissing); (b) clarification 5 may merit a case-text fix on the TMS side.

## Automation Hints
- Page objects: add to `SkillsListPage` (class-level only): table-view toggle, row action button template `[id="{}-skill-action"]` via `ScopedLocator`/template with `suggested_testid`, Run menuitem (role+name). Add a helper `run_skill_from_row(skill_id)`. Reuse `SkillDetailPage` (`test_panel`, `send_test_message`, `wait_for_test_response`, `get_last_test_response`). NOTE `send_test_message` clicks send without banner dismissal - dismiss `platform-banner-close` first (or extend it).
- Cleanup: `skill_api` fixture + `ConversationAPI(browser_cookies=_browser_cookies)`.
- Markers: `@pytest.mark.tms("ELITEA-4634")` + `@allure.issue` pair (file `ELITEA-4634_...md` under skills/ in TMS repo); skills/p1/regression.
