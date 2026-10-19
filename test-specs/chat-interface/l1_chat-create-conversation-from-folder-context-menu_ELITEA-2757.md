# Test Case: Chat – Create new conversation from folder context menu

## Metadata
- **TMS ID**: ELITEA-2757 (requirements: EliteaAI/elitea_issues#1604; tags feat:chat, r-2.0.6)
- **Priority**: l1 (case `priority: critical`)
- **Environment Explored**: DEV `https://dev.elitea.ai/app`, project id 575 (`${ELITEA_PROJECT_ID}`), `${TEST_USER}`
- **Tool**: scripted Python Playwright probes (Playwright MCP chrome binary absent on this host; substitution noted), headless, storage state from `dev_storage_state.py`
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-context-menu`
- **Analyst**: qa-engineer (agent)

Neighbours read: ELITEA-2132 (folder creation), 2135/2137 (Move to folder), 2458/2459 (folder rename), 2149 (pin). None covers the folder dot-menu "New chat" item (grepped `New chat`, `onCreateConversationInFolder` in specs/pages/tests: only the page-object folder helpers exist). Not already-covered.

## Preconditions
- Logged in; Chats panel open; test creates its own empty folder (see Test Data) rather than depend on ambient folders.

## Test Data (generate-per-test, API setup/teardown)
- `target_folder`: `POST {ELITEA_API_BASE}/elitea_core/folder/prompt_lib/{project_id}` body `{"name":"<unique>"}` -> 201 `{id,...}`. Fresh folder renders collapsed (`data-expanded="false"`) with `chat-folder-empty-state` in DOM (not visible while collapsed).
  Name must satisfy `ConversationNameRegExp` (3-64 chars).
- Cleanup: `chat_page.delete_folder_via_api(folder_id)` (also deletes contained conversations? NOT verified - delete the conversation first: `DELETE .../elitea_core/conversation/prompt_lib/{project}/{conv_id}` -> 204, then the folder -> 204).
- Message: "Explain the concept of machine learning".
- `ChatPage` helpers reusable: `get_folder_item`, `is_folder_expanded`, `expand_folder`, `is_conversation_in_folder`, `delete_folder_via_api`, `CONVERSATION_MENU_BUTTON`, `FOLDER_ICON`, `wait_for_naming_label_to_resolve`, `send_message`.

## Test Steps (all executed live, 2 clean runs + variants)
1. Open `/chat`. Dismiss the "Announcing ELITEA 2.0.7" release dialog if present (`platform-banner-center` MuiDialog intercepts pointer events; its button "Got it" - role=button name "Got it"; the standard `dismiss_banner_if_present()` (aria-label=close) does NOT close it). Hover `FOLDER_ICON` inside `chat-folder-item-{id}` (reveals dot-menu), click scoped `conversation-menu-menu-button` (`.first`, `force=True`).
   - **Verify**: `role=menu` items exactly: **New chat, Rename, Pin on top, Delete** (live-confirmed order and labels).
2. Click menuitem `New chat` (role=menuitem, name "New chat"; the menu item has NO data-testid).
   - **Verify**: URL stays `/app/chat` (blank conversation, no id yet); message list has 2 `chat-message-item` (greeting placeholders); folder row still has **no conversation item**.
   - **DRIFT (clarification)**: case says "folder auto-expands if collapsed" at this step. Live: `data-expanded` stays `"false"` after the click; it flips to `"true"` only once the first message is sent and the conversation is created (observed at 0.0s after Enter). Assert expand AFTER send (step 4/5), not after the click.
3. Verify default LLM: `model-selector-name` text = **`Dial-GPT-5.6-Luna`** (same as plain landing; do NOT hardcode: compare against landing-page `model-selector-name` read before the menu action, case example "Anthropic Sonnet 5" is stale).
4. Fill `chat-message-input` with the message, press Enter.
   - **Verify**: within ~0.4s the folder row shows a `chat-conversation-item-{id}` whose text is **`Naming`** (spinner label) and folder `data-expanded="true"`; URL becomes `/app/chat/{id}?name=Explain+concept+machine+learning`.
5. Wait for naming to finish: the item text becomes **`Explain concept machine learning`** (~0.8s after send; first runs: seen resolved at 0.8s). Wait with `expect(...).not_to_have_text("Naming")` / `wait_for_naming_label_to_resolve`; assert non-empty and != "Naming" rather than the exact auto-name (LLM-generated; seen identical 3/3 but not contractual).
6. Verify placement: `[data-testid="chat-folder-item-{fid}"] [data-testid="chat-conversation-item-{id}"]` count == 1 AND page-wide `chat-conversation-item-{id}` count == 1 (so not duplicated in a date group); no `chat-conversation-group-header-*` (Today/This week/Older) rendered at all when the folder is the only home of conversations (live: 0 group headers). Prefer the generic form: `is_conversation_in_group(id, "today"/"this_week"/"older")` == False.
7. Collapse then re-expand the folder by clicking `FOLDER_ICON`/folder row: `data-expanded` true -> false -> true; item count in folder == 1 after re-expand (note: MUI Collapse keeps children mounted while collapsed, so "remains visible" must be asserted AFTER re-expanding; do not use mounted-count while collapsed).
8. `page.reload()`, re-open `/chat`: folder row present, `data-expanded="true"`, same `chat-conversation-item-{id}` inside the folder with the auto-name intact. (Message content intact: optionally open the item and assert the user message text appears in `chat-message-item`; not exercised live - verify when implementing.)

## Expected Results
- Dot-menu offers New chat; clicking it opens a blank chat; first send creates the conversation INSIDE the folder (not in any date group), auto-named, persisting across reload.
- Network (observed): `POST elitea_core/conversations/prompt_lib/575` (create, carries folder), `PUT .../conversation/prompt_lib/575/{id}` (rename/naming), `POST select_conversation/...`. No console errors observed in probes (console not formally dumped; implementer must run the usual error filter).

## Coverage Map

### Axis 1
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Open folder 3-dot menu | Options New chat/Rename/Pin on top/Delete | step 1 | menu item labels | asserted |
| 2 Click New chat | Blank conversation opens; folder auto-expands if collapsed | step 2 (+4) | blank chat (no id, no folder child); expansion asserted post-send | clarification (expansion occurs on send, not click) |
| 3 Default LLM pre-selected | Default project LLM shown | step 3 | model-selector-name == landing default | asserted |
| 4 Send message | Sent; "Naming..." next to entry | step 4 | item text "Naming" (short ~0.4s window: assert via expect with tight poll, tolerate missing if already resolved) | asserted (flaky window - see hints) |
| 5 Auto-naming completes | Auto-named, spinner gone | step 5 | text != Naming, non-empty | asserted |
| 6 In folder, NOT in Today/This Week/Older | folder-only | step 6 | scoped count 1, page-wide count 1, no group header holds it | asserted |
| 7 Collapse + re-expand | still visible | step 7 | data-expanded toggle + item present | asserted |
| 8 Refresh | persists with name | step 8 | post-reload folder-scoped item + text | asserted |
| Expected Final State: "available in folder context menu (both right-click and three-dot)" | right-click menu | - | - | clarification: right-click on the folder row opens NO menu (no onContextMenu handler in FolderItem/FolderAccordion on origin/main; live right-click -> 0 menuitems). Only three-dot exists. Not automated; do not assert. |

### Axis 2
- Page-wide count == 1 of the new conversation testid (added: catches "appears in both folder and date sections" Fail criterion, stated in case Pass/Fail but not in steps).
- Default model compared against the landing value instead of hardcoded string (added: case example is stale).

## Handles Reference (verified on DEV)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `chat-folder-item-{id}` (+`data-expanded`) | - | testid on DEV ✓ |
| testid | `chat-folder-icon`, `chat-folder-expand-icon` | - | testid on DEV ✓ |
| testid | `conversation-menu-menu-button` (scope inside folder row, `.first`) | - | testid on DEV ✓ |
| role+name | `role=menuitem[name="New chat"]` (menu is a MUI popper at page level; exactly 1 match) | `chat-folder-menu-new-chat-menuitem` | ladder - no testid on DEV (FolderItem.jsx menuItems carry no key for "New chat"; Delete/Rename got testids in earlier batches) |
| testid | `chat-message-input`, `model-selector-name`, `chat-message-item`, `chat-conversation-item-{id}` | - | testid on DEV ✓ |
| role+name | `role=button[name="Got it"]` in `platform-banner-center` dialog (transit only) | `platform-banner-got-it-button` | ladder - no testid on DEV; only present until dismissed |
| text | "Naming" label (existing `text="Naming"` raw in `wait_for_naming_label_to_resolve`, pre-ladder debt) | `chat-conversation-item-naming-label` | ladder; implementer should scope to the folder's conversation item |

## Automation Hints
- Menu item: a new class-level `LocatorDescriptor(role="menuitem", name="New chat", suggested_testid=...)` on `ChatPage`; add `create_conversation_in_folder_via_menu(folder_id)` mirroring `open_folder_rename_editor` (hover FOLDER_ICON, click menu button `.first` force=True).
- The "Naming" window is ~0.4-0.8s on DEV; do not make "Naming" visible a hard gate unless polled tightly (expect with short interval) - prefer asserting end state (name set, != Naming) and treat the transient as soft/optional, declared in the Run Report.
- Cleanup order: conversation (UI-created, id from URL regexp `/chat/(\d+)`), then folder. Leaked probe folders on DEV are pre-existing hazard (#1309).
- Banner "Got it" dialog blocked hover in my probes only on a fresh storage state; the autouse `dismiss_banner_after_navigation` does not handle it - spec may need a one-line guarded dismiss in the page object (note as a possible framework gap; flag to lead).
- Interaction ladder (role-overrides): right-click/hover/Enter variants tried; New chat via three-dot is the intended activation (onClick -> onCreateConversationInFolder, FolderItem.jsx:86-88, origin/main).

## Known Defects / Clarifications
- Clarification (case text): auto-expand occurs on first send, not on clicking New chat. Not a product defect (conversation is unaffected). Sub-observation: if the intended UX is expand-on-click, that is a UX question for the product team; filed as note, not a bug.
- Clarification: "right-click" menu in Expected Final State does not exist.
- Clarification: default LLM example "Anthropic Sonnet 5" stale; DEV default is Dial-GPT-5.6-Luna.
