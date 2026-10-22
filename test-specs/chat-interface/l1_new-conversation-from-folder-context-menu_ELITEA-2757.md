# Test Case: Chat – Create new conversation from folder context menu

## Metadata
- **TMS ID**: ELITEA-2757
- **Linked Story**: EliteaAI/elitea_issues#1604
- **Priority**: l1 (case `priority: critical` -> `@pytest.mark.p0`)
- **Environment Explored**: DEV `https://dev.elitea.ai/app/chat`, project 575 ("Private"), `${TEST_USER}`
- **Analyst**: qa-engineer, 2026-10-22
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-context-menu`
- **Tooling note**: Playwright MCP chrome is not installed on this host; exploration was done with scripted Python Playwright using `.playwright-mcp/dev-storage-state.json`. DEV had a ~5 min 503 outage at start (transient). Platform banner dialog (`platform-banner-close`) intercepts pointer events on first load - dismiss it first (existing `BasePage` handle).

## Preconditions
- Logged in. The test creates its OWN folder (do not rely on shared folders on DEV, e.g. `autotest_2757_*` leftovers exist).

## Test Data
- Folder name: generate-per-test, e.g. `autotest_2757_<epoch>`. Create via UI: `click_create_folder_button()` -> `set_folder_name()` -> `folder_name_confirm_button` click (all existing in `ChatPage`; folder id read back from the DOM `chat-folder-item-{id}`). No `FolderAPI` client exists.
- Message: `Explain the concept of machine learning`

## Test Steps
1. Navigate to `/chat`, dismiss banner, hover the folder row, click the folder 3-dot button (`conversation-menu-menu-button` scoped inside `chat-folder-item-{id}`).
   - **Verify**: menu items exactly `New chat`, `Rename`, `Pin on top`, `Delete` (live-confirmed, 4 items, order as listed).
2. Click `New chat` (menuitem, accessible name).
   - **Verify**: URL stays `/app/chat` (blank composer, no conversation id yet); `chat-input` visible and empty.
3. Read selected model.
   - **Verify**: `model-selector-name` text is non-empty and equals the project default (live: `Anthropic Claude Haiku 4.5`). Do NOT hardcode the model name (changes by deployment; known flaky text); compare against the model shown on a plain `/chat` blank new chat, or just assert non-empty.
4. Type the message into `chat-input` and send (Enter).
   - **Verify**: URL becomes `/app/chat/<id>?name=...`; the folder row flips `data-expanded` `false` -> `true` and contains exactly one `chat-conversation-item-{id}` whose text is the auto name (live: `Explain concept machine learning`, an AI-shortened name, appeared within <1s; assert non-empty and not `Naming`, never the exact string).
5. Wait for naming to resolve (`wait_for_naming_label_to_resolve()` - tolerant of the label never appearing).
   - **Verify**: no "Naming" text remains.
6. Verify the conversation is ONLY in the folder.
   - **Verify**: `chat-conversation-item-{id}` count scoped inside `chat-folder-item-{id}` == 1 AND the same testid scoped OUTSIDE any folder (page-wide count minus in-folder count) == 0. Use the existing scoped-count pattern from ELITEA-2135/2137 AFS (`is_conversation_in_group` / `is_conversation_in_folder`). No Today/This week headings rendered at all when only the folder holds chats.
7. Collapse and re-expand the folder (click the row / `chat-folder-expand-icon`).
   - **Verify**: `data-expanded` toggles true -> false -> true (MUI Collapse keeps children mounted while collapsed, so assert visibility, not DOM count, after re-expand); conversation visible.
8. `page.reload()` (dismiss banner), expand the folder if collapsed (after reload it came back `data-expanded=true` live, but expand defensively via state check).
   - **Verify**: conversation still inside the folder with the same name; zero outside the folder.

## Expected Results
Conversation created in the folder via "New chat", named automatically, persists after reload, never appears in date groups.

## Coverage Map

### Axis 1 - Case coverage
| Case element | Expected | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Pre: folder exists | - | Setup (UI create) | fixture | asserted |
| 1 three-dot -> menu options New chat, Rename, Pin on top, Delete | menu with 4 options | step 1 | exact 4-item list | asserted |
| Expected Final State: "New chat" in right-click menu too | right-click menu | step 1 | n/a | clarification *(live: right-click on the folder row opens NO menu, same as conversation rows per ELITEA-3779; only the 3-dot exists. Do not automate right-click.)* |
| 2 click New chat -> blank conversation; folder auto-expands if collapsed | blank chat; folder expands | steps 2, 4 | step 2 blank; step 4 expanded | clarification *(live: folder stays collapsed immediately after clicking New chat; it expands only once the first message is sent and the conversation is created (POST /conversations + PUT folder_id). Assert expansion after send.)* |
| 3 default LLM pre-selected | default project LLM shown | step 3 | `model-selector-name` non-empty | asserted *(case says "e.g. Anthropic Sonnet 5"; live default is Claude Haiku 4.5 - example text only, not asserted)* |
| 4 send message -> "Naming..." spinner next to entry | spinner | step 4/5 | entry present with a name | clarification *(live: the entry showed the final shortened name within the first 1s poll; the "Naming" label was never observed (0 matches). Spinner is transient/unreliable - assert end state only)* |
| 5 auto-naming completes | named from content | step 5 | name non-empty, != Naming | asserted |
| 6 only in folder, not Today/This week/Older | folder-only | step 6 | scoped in-folder == 1, outside == 0 | asserted |
| 7 collapse/re-expand keeps conversation | visible | step 7 | visibility after re-expand | asserted |
| 8 reload persists with name | present | step 8 | name equality with step 5 | asserted |
| Pass/Fail "not in both folder and date sections" | - | step 6 | outside == 0 | asserted |

### Axis 2 - Analyst additions
- Step 1 exact 4-item list: pins the New chat item's presence among siblings (Disabled state: item is enabled for owner; `disabled` computed from owner/permission/`folder.isNew` in FolderItem.jsx).
- Step 6 outside-folder count scoped explicitly: MUI Collapse keeps folder children mounted, so an unscoped count cannot distinguish placement.
- Console errors checked: 0 errors across the flow.

## Cleanup
`finally`: delete conversation via `conversation_api.delete_conversation(id)` (id parsed from URL) and folder via `ChatPage.delete_folder_via_api(folder_id)` (live 204). Independent try/except per resource.

## Concrete Handles (verified live on DEV)
| Element | rung | handle | suggested_testid | provenance |
|---|---|---|---|---|
| Create-folder header button | 1 | `chat-create-folder-button` | - | testid on DEV, existing `create_folder_button` |
| Folder name input / confirm | 1 | `chat-folder-name-input`, `chat-folder-name-confirm-button` | - | testid on DEV, existing |
| Folder row | 1 | `[data-testid="chat-folder-item-{id}"]` + `data-expanded` | - | existing `FOLDER_ITEM`, `get_folder_item()` |
| Folder 3-dot button | 1 | `conversation-menu-menu-button` scoped in folder row (button hidden until hover - hover the row first; force-click on hidden fails) | - | testid on DEV (shared with conversation rows) |
| Folder menu "New chat" | 2 | `role=menuitem` name `New chat` | `chat-folder-menu-new-chat-menuitem` | ladder - no testid on DEV (menuitem has no data-testid; Rename/Pin items also none; only Delete/Rename have `FOLDER_MENU_*` constants - verify live: Rename item testid not seen null in this run's enumeration, which showed None for all 4). Name unique within the open menu. |
| Composer | 1 | `chat-input` | - | existing |
| Model selector name | 1 | `model-selector-name` | - | existing |
| Conversation item | 1 | `chat-conversation-item-{id}` | - | existing `CONVERSATION_ITEM` |
| Folder delete (cleanup) | - | `ChatPage.delete_folder_via_api` | - | existing |
| Banner close | 1 | `platform-banner-close` | - | existing |

Note: enumeration showed `data-testid` None on all 4 folder menu items in this run, including Delete/Rename for which `ChatPage` declares `chat-folder-menu-*-menuitem` constants - those may have regressed (cf. #1309 history). Implementer: verify live; the New chat handle must be a class-level `LocatorDescriptor(role="menuitem", name="New chat", suggested_testid=...)`.

## Network Behavior
- `POST /api/v2/elitea_core/conversations/prompt_lib/575` -> 201 (on first send), then `PUT /elitea_core/conversation/prompt_lib/575/{id}` x2 (folder_id/name), `POST select_conversation` 200. No 4xx/5xx. `GET default_model/...` is 404 (not an endpoint; ignore).
