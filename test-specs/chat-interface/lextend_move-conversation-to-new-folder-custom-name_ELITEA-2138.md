# Test Case: Chat – Move Conversation to a New Folder with Custom Name via Move To Menu

## Metadata
- **TMS ID**: ELITEA-2138
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, Private project)
- **User set**: `${TEST_USER}` — dev-auth on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), chat-remaining-w07
- **Status**: extend-existing
- **surface_key**: `chat-conversation-context-menu`

## Extension target
`automation/tests/ui/chat/test_move_conversation_to_folder.py` (same file as ELITEA-2135/2137,
merged `origin/automation/base`, commit `37dbd948`). **Purely additive** — a brand-new test method
appended to the file (no existing method body touched). No existing test exercises the
"Move to" → "Create folder" flow with a TYPED, non-default folder name: ELITEA-2137's existing
`test_move_conversation_to_new_folder` deliberately keeps the "New folder" default untouched
(its own docstring: "Click the checkmark **without changing the name**"). ELITEA-2138 is the
genuinely-untested variant — clear the default, type a custom name, confirm.

Live-confirmed this session (Playwright MCP against `localhost:5173`, project 399):
1. Opened `conv_target`'s "Move to" submenu (known-defect retry per #1117, same as ELITEA-2135/2137),
   clicked "Create folder" — inline editor pre-filled `"New folder"`, focused.
2. **Reproduced the already-documented "append not replace" race** (`_surface.md` § ELITEA-2128/2129,
   ELITEA-2458): a raw `Control+a` + `Backspace` did NOT clear the field — typing "Sprint Chats"
   after that sequence produced `"Sprint ChatsNew folder"` (append, not replace), and confirming
   created a REAL folder with that wrong name (`POST` → `201`, `name: "Sprint ChatsNew folder"`,
   `id: 293` — cleaned up via `conversation_api.delete_folder(293)` afterward). This is a live
   reconfirmation of the pre-existing gotcha, not a new defect — `ChatPage.set_folder_name()`'s
   OWN existing implementation already avoids it correctly via `.clear()` (see below), so this is
   purely a "how to drive the input" note for the implementer, not a product bug.
3. Redone correctly using `ChatPage.set_folder_name()`'s exact idiom (`.click()` → `.clear()` →
   `.press_sequentially(name, delay=30)`): input read back exactly `"Sprint Chats"`, confirm fired
   `POST /elitea_core/folder/prompt_lib/399` → `201`, response body `name: "Sprint Chats"`, `id: 294`.
   Toast: `Chat moved to "Sprint Chats" folder successfully` (same
   `useMoveToFolderConversation.hooks.js` template ELITEA-2135/2137 already documented, with the
   custom name substituted in). Conversation confirmed removed from Today and present inside the
   new "Sprint Chats" folder on expand. Both the folder and the conversation were deleted via API
   afterward (`conversation_api.delete_conversation`/`delete_folder`) — zero net pollution from this
   exploration pass.

## Preconditions
- User logged in (`${TEST_USER}` / dev-auth on localhost).
- `conv_target` is a fresh, never-pinned, never-moved conversation (same constraint as
  ELITEA-2135/2137 — `ConversationItem.jsx` disables "Move to" while `isPinned`).

## Test Data
- **`conv_target`** — created via `conversation_api.create_conversation(name)` (API, no LLM
  round-trip — same pattern as ELITEA-2135/2137).
- **Custom folder name**: `"Sprint Chats"` (case's own Test Data table, literal value).

## Test Steps
1. Navigate to Chats, hover `conv_target`, click its 3-dot menu, hover "Move to", click "Create
   folder" (reusing `open_move_to_submenu()` + `select_move_to_create_folder()`, both pre-existing —
   ELITEA-2135/2137).
   - **Verify**: the inline folder-name editor (`chat-folder-name-input`) appears, pre-filled
     `"New folder"`, focused — same shared editor ELITEA-2137 already asserts.
2. Clear the default name and type `"Sprint Chats"` via `ChatPage.set_folder_name("Sprint Chats")`
   (its existing `.clear()`-based implementation — do NOT hand-roll `Control+a`+`Backspace`, see
   the live-reconfirmed race above), click the confirm checkmark.
   - **Verify**: `folder_name_input.input_value() == "Sprint Chats"` before confirming (proves
     replace, not append); the `POST /elitea_core/folder/prompt_lib/{project_id}` request resolves
     `201` with response body `name == "Sprint Chats"` and a real `id`.
3. Verify a success toast appears confirming the move.
   - **Verify**: `toast-message` text is exactly `Chat moved to "Sprint Chats" folder successfully`
     (live-verified string, matches the ELITEA-2135/2137-documented template with the custom name
     substituted).
4. Verify the conversation is no longer in its original date group.
   - **Verify**: `chat.is_conversation_in_group(conv_target_id, "today")` is `False` (same
     scoped-0-count discipline ELITEA-2135/2137 established — MUI `Collapse` keeps a folder's
     children DOM-mounted).
5. Expand "Sprint Chats" and verify the conversation is listed inside.
   - **Verify**: the new folder's `data-expanded` flips `"true"`; `conv_target` renders scoped
     inside it (`chat.is_conversation_in_folder(new_folder_id, conv_target_id)`).

## Expected Results
Same mechanism as ELITEA-2137 (Create-folder-and-move is a single confirm action, `POST` + move in
one server round-trip, toast-confirmed) but with a user-supplied name instead of the default —
proving the inline editor's name field genuinely feeds the folder-creation payload rather than being
cosmetic.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: logged in, conversation exists | — | Setup | `auth_state` + API-seeded conv | asserted |
| 1 Hover conv, 3-dot, Move to, Create folder | New folder input appears | AFS step 1 | step 1: input visible + pre-filled default | asserted |
| 2 Clear default, type 'Sprint Chats', click checkmark | Folder created; conversation moved | AFS step 2 | step 2: input value + `POST` 201 body | asserted |
| 3 Verify success toast | Toast shown | AFS step 3 | step 3: exact toast text | asserted |
| 4 Verify conversation no longer in its original date group | Removed from date groups | AFS step 4 | step 4: scoped 0-count under "today" | asserted |
| 5 Expand 'Sprint Chats', verify conversation inside | Conversation inside folder | AFS step 5 | step 5: `data-expanded` + scoped 1-count | asserted |
| Pass/Fail: "Conversation not moved or folder name wrong" | — | steps 2,5 | folder-name + membership assertions together | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 2 explicitly asserts the input's value BEFORE confirming (`== "Sprint Chats"`, not just the
  eventual server response) — *added: isolates a replace-vs-append regression (the exact live
  gotcha this pass reproduced once) from a folder-naming regression; asserting only the `POST` body
  would not distinguish "typed correctly, sent correctly" from "typed wrong, sent wrong", both of
  which would otherwise look identical if the test only checked the end state.*

## Cleanup
`try`/`finally`, independent per resource (`.claude/rules/ui-tests.md` § Test Data Lifecycle):
1. `conversation_api.delete_conversation(conv_target_id)`.
2. `chat.delete_folder_via_menu(new_folder_id)` (falls back to `delete_folder_via_api()` per
   #1309 — same pattern ELITEA-2135/2137 already use).

## Concrete Handles (discovered during exploration)
No new handles — reuses `ChatPage.set_folder_name()`, `folder_name_input`,
`folder_name_confirm_button`, `move_to_create_folder_menuitem`, `toast_message`,
`is_conversation_in_group()`, `is_conversation_in_folder()`, `expand_folder()` — all pre-existing
(ELITEA-2098/2132/2135/2137/2458).

## Network Behavior
- `POST /elitea_core/folder/prompt_lib/{project_id}` → `201`, body `{"name": "Sprint Chats", ...,
  "id": <new_folder_id>}` (live-confirmed this session).
- Toast fires client-side off the same response — no separate PUT for the move (same single-request
  create-and-move shape ELITEA-2137's AFS already documented, confirmed here with a non-default
  name too).
- Pre-existing, unrelated: `secrets/secrets/default` `403` noise (excluded from console-error
  checks, per every sibling AFS in this suite).

## Known Defects Found During Exploration
None. The "append not replace" behavior reproduced during exploration is a documented, pre-existing
gotcha in how the input is DRIVEN (`_surface.md` § ELITEA-2128/2129) — not a product defect;
`ChatPage.set_folder_name()`'s own existing implementation already avoids it correctly.

## Blocked Steps
None.

## Automation Hints
- Reuse `ChatPage.set_folder_name(name)` verbatim — do NOT type via `press_sequentially` after a
  bare `Control+a`+`Backspace` (reproduces the append race live-confirmed above).
- New test method, appended to the file — suggested placement: alongside
  `TestMoveConversationToNewFolder` (either as a second method on that class or a small sibling
  class `TestMoveConversationToNewFolderWithCustomName`) since it shares that class's setup shape
  (fresh `conv_target` via API, no existing folder needed).
