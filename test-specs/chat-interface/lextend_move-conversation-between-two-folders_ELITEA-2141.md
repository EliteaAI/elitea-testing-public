# Test Case: Chat – Move Conversation Between Two Folders via Move To Menu

## Metadata
- **TMS ID**: ELITEA-2141
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, Private project)
- **User set**: `${TEST_USER}` — dev-auth on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), chat-remaining-w07
- **Status**: extend-existing
- **surface_key**: `chat-conversation-context-menu`

## Extension target
`automation/tests/ui/chat/test_move_conversation_to_folder.py` (same file as
ELITEA-2135/2137/2138/2139/2140, merged `origin/automation/base`, commit `37dbd948`). **Purely
additive** — one new test method (`test_move_conversation_between_two_folders`, new class
`TestMoveConversationBetweenTwoFolders`). Differs from ELITEA-2135 (existing folder, but source is
the flat date-grouped list) in a way that matters mechanically: the source conversation starts
INSIDE a folder, not in a date group, and the "Move to" submenu's OWN source-folder entry must be
disabled (self-move prevention) — neither of which ELITEA-2135's test exercises.

## Live exploration (this session)

Set up via `conversation_api`: created two folders (`source_folder`, `target_folder`) and one
conversation, moved the conversation into `source_folder` via
`conversation_api.move_conversation_to_folder()` (API setup — the case's own precondition, "at
least two folders exist, one containing at least one conversation", names no required mechanism).
Expanded `source_folder`, opened the conversation's context menu, opened "Move to" (same known-
defect retry as every sibling case — #1117, not re-filed).

**Live-confirmed via `browser_snapshot` + network interception**:
- The open submenu lists "Create folder", "Back to the list", a separator, then EVERY folder
  including `source_folder` ITSELF — but `source_folder`'s own entry renders
  `aria-disabled="true"` (confirmed via `getAttribute`) and is visually/structurally a disabled
  `menuitem`, not absent. This is a genuine, previously-undocumented product behavior on this
  surface (self-move prevention) — worth asserting explicitly since a regression here (source
  folder becoming clickable, silently no-opping, or vanishing entirely) would be easy to miss
  without a dedicated check.
- `target_folder`'s entry is enabled and clickable.
- Clicking `target_folder`'s entry fired `PUT /elitea_core/conversation/prompt_lib/{project_id}/{id}`
  → `200`, response body `folder_id: <target_folder_id>` (changed from `source_folder_id`). Toast:
  `Chat moved to "<target_folder_name>" folder successfully` — the SAME move-INTO-a-folder template
  ELITEA-2135/2137/2138 already document, confirmed here to fire identically when the conversation's
  PRIOR container was a folder rather than a date group.
- Post-move: conversation absent from `source_folder` (scoped 0-count), present inside
  `target_folder` on expand.

## Preconditions
- User logged in (`${TEST_USER}` / dev-auth on localhost).
- At least two folders exist, one (`source_folder`) containing at least one conversation — satisfied
  by API setup.

## Test Data
- **`source_folder`**, **`target_folder`** — via `conversation_api.create_folder(name)` (two calls).
- **`conv_target`** — via `conversation_api.create_conversation(name)`, then
  `conversation_api.move_conversation_to_folder(conv_target_id, source_folder_id)` (setup).

## Test Steps
1. Navigate to Chats, expand `source_folder` (`expand_folder()`).
   - **Verify**: `conv_target` renders scoped inside `source_folder`
     (`is_conversation_in_folder(source_folder_id, conv_target_id) == True`).
2. Hover `conv_target`, click its 3-dot icon, hover "Move to" (`open_move_to_submenu()`, known-
   defect retry per #1117).
   - **Verify**: the submenu mounts and shows all available folders, including `source_folder`
     ITSELF (`get_move_to_folder_item(source_folder_id)` visible but `aria-disabled == "true"`) and
     `target_folder` (`get_move_to_folder_item(target_folder_id)` visible and NOT disabled).
3. Select `target_folder` from the submenu (`select_move_to_folder(target_folder_id)`).
   - **Verify**: `PUT .../conversation/prompt_lib/{project_id}/{conv_id}` resolves `200` with body
     `folder_id == target_folder_id`; success toast reads exactly
     `Chat moved to "<target_folder_name>" folder successfully`.
4. Verify the conversation is no longer listed under the source folder.
   - **Verify**: `is_conversation_in_folder(source_folder_id, conv_target_id) == False` (scoped
     0-count inside `source_folder`'s own container — same MUI-`Collapse`-mounted-children trap
     ELITEA-2135 documents, applied here to a folder container instead of a date-group one).
5. Expand `target_folder` and verify the conversation is inside.
   - **Verify**: `target_folder`'s `data-expanded` flips `"true"`;
     `is_conversation_in_folder(target_folder_id, conv_target_id) == True`.

## Expected Results
A conversation already inside one folder can be moved directly to a different folder via the same
"Move to" submenu; its own current folder appears in that submenu but disabled (cannot move a
conversation into the folder it's already in); the move fires the same `PUT` + toast mechanism as
moving from the flat list, just with a non-null starting `folder_id`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: 2 folders exist, one with a conversation | — | Setup | API-seeded 2 folders + move | asserted |
| 1 Expand folder containing a conversation | Conversation visible | AFS step 1 | step 1: scoped presence | asserted |
| 2 Hover, 3-dot, hover Move to | Submenu shows all available folders | AFS step 2 | step 2: submenu contents, incl. disabled source-folder entry | asserted |
| 3 Select a different folder (e.g. 'New folder5') | Success toast: 'Chat moved to New folder5 folder successfully' | AFS step 3 | step 3: exact toast text + `PUT` body | asserted *(case's paraphrase omits the quote marks the live toast includes — same documented CLARIFICATION as ELITEA-2135/2137/2138, not re-filed)* |
| 4 Verify conversation no longer listed under source folder | Removed from source folder | AFS step 4 | step 4: scoped 0-count inside `source_folder` | asserted |
| 5 Expand target folder, verify conversation inside | Conversation in target folder | AFS step 5 | step 5: `data-expanded` + scoped presence | asserted |
| Pass/Fail: "Fail: conversation remains in source or disappears" | — | steps 4–5 | negative-in-source + positive-in-target together | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 2 explicitly asserts `source_folder`'s own submenu entry is present-but-disabled (not
  absent) — *added: a previously-undocumented, genuinely new observable on this surface
  (self-move prevention); worth a dedicated check since three plausible regressions (clickable,
  silently no-op, vanished) would otherwise go undetected.*

## Cleanup
`try`/`finally`, independent per resource:
1. `conversation_api.delete_conversation(conv_target_id)`.
2. `chat.delete_folder_via_menu(source_folder_id)` and `chat.delete_folder_via_menu(target_folder_id)`
   (each independently, both fall back to `delete_folder_via_api()` per #1309).

## Concrete Handles (discovered during exploration)
No new handles. Reuses `ChatPage.open_move_to_submenu()`, `get_move_to_folder_item(folder_id)`,
`select_move_to_folder(folder_id)`, `is_conversation_in_folder()`, `expand_folder()`, `toast_message`
— all pre-existing (ELITEA-2098/2132/2135/2137). The disabled-source-folder-entry check reads the
SAME `MOVE_TO_FOLDER_ITEM` locator template already provisioned by ELITEA-2135's implementation
(`'[data-testid="chat-move-to-folder-{}-menuitem"]'`) via `get_attribute("aria-disabled")` — no new
testid or class constant needed.

## Network Behavior
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_id}` → `200`, body
  `folder_id: <target_folder_id>` (changed from the source folder's id) — live-confirmed.
- Toast: `Chat moved to "<target_folder_name>" folder successfully` (same template as
  ELITEA-2135/2137/2138's move-INTO-a-folder toast).
- Pre-existing, unrelated: `secrets/secrets/default` `403` noise (excluded, per every sibling AFS).

## Known Defects Found During Exploration
None. Reuses the already-filed, already-workaround-documented #1117 (submenu open-reliability) —
not re-filed.

## Blocked Steps
None.

## Automation Hints
- No new page-object work — every method and locator this case needs already exists.
- Read `aria-disabled` (not a custom `data-*` attribute) off `get_move_to_folder_item(folder_id)`
  for the "is this folder's own entry disabled" check — live-confirmed this is how MUI renders a
  disabled `menuitem` on this surface (consistent with the already-documented disabled "Pin on top"
  item shown for a folder-contained conversation's own context menu).
