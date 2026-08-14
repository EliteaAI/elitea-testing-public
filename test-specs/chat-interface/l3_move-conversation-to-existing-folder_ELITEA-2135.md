# Test Case: Chat – Move Conversation to Existing Folder via Move To Menu

## Metadata
- **TMS ID**: ELITEA-2135
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, matching the
  ELITEA-2132 sibling's medium→l3/p2 mapping in this suite)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2137, ELITEA-2149
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-context-menu`

Cluster-analysed alongside ELITEA-2137 (move to a NEW folder) and ELITEA-2149 (pin). All three
share the conversation 3-dot context-menu surface, but each has genuinely different steps beyond
opening that menu (2135 picks an existing folder from the "Move to" submenu; 2137 drives the
"Create folder" flow inside that same submenu, including an inline editable name input the 2135
flow never touches; 2149 doesn't open "Move to" at all) — written as three separate AFS files per
the skill's "differ in steps → separate AFS" rule, not a family. They ARE bundled as one PR/branch
since analysed together.

No existing AFS or automated test covers the "Move to" submenu (existing folder or new folder)
anywhere in this suite — grepped `test-specs/` and `tests/ui/chat/` for `move-to`/`move_to`/
`Move to` before this pass; the only prior hit was `EXPECTED_MENU_ITEM_KEYS` in
`test_conversation_deletion_flow.py`, which asserts the menu **enumerates** a `"move-to"` key but
never clicks it. The ELITEA-2114 AFS (`l2_conversation-deletion_ELITEA-2114.md`) already
established the live menu-item set for a Private-project conversation: **Rename, Move to, Playback,
Pin on top, Delete** (5 items — `Make public`/`Share` conditionally hidden for the account's own
Private project; live-reconfirmed this pass, unchanged).

**A MAJOR product defect was found and filed during this pass** — see § Known Defects. It affects
the interaction that opens the "Move to" submenu (shared by both this case and ELITEA-2137), not
this case's later steps, and does not block completing the case (a documented workaround exists).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one folder and one conversation exist — test creates its own of each (see § Test Data);
  the case's ambient-data precondition is satisfied by setup, not by relying on shared state.
- The target conversation must NOT be pinned and NOT already inside a folder — `ConversationItem.jsx`
  disables the "Move to" item entirely when `isPinned` is true (`disabled: isPinned || ...`), and a
  fresh, never-pinned, never-moved conversation naturally satisfies this.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — the conversation that will be moved. Create via
  `conversation_api.create_conversation(name)` (fast, no LLM round-trip — matches the pattern
  established in ELITEA-2114/ELITEA-2132's own AFSes).
- **`target_folder`** — the destination folder, named `"New folder6"` per the case's own Test Data
  table (live-confirmed: the toast text embeds the folder name verbatim, so an arbitrary name works
  equally well functionally — kept `"New folder6"` to match the case literally). Create via a raw
  API call: `POST {ELITEA_API_BASE}/elitea_core/folder/prompt_lib/{project_id}` with
  `{"name": "New folder6"}` — **no `FolderAPI` client exists yet** in `automation/api/client.py`
  (only `ConversationAPI` et al.); this AFS's own exploration used a raw `requests.post` with the
  same Bearer-token fallback pattern `ConversationAPI` uses on localhost (see § Automation Hints for
  the recommended client addition, same standing recommendation as ELITEA-2132's AFS).

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Hover `conv_target`'s sidebar item, click its 3-dot menu button.
   - **Verify**: the context menu shows exactly 5 items for this project — Rename, Move to,
     Playback, Pin on top, Delete (live-reconfirmed this pass, matches ELITEA-2114's
     CLARIFICATION-2; NOT the case's literal 6-item list — see § Coverage Map / § Known Defects for
     why "Move to" itself is separately defect-tracked, and note the case's list omits "Pin on top"
     order-wise but the live set is otherwise a subset match).
2. Click the **Move to** menu item.
   - **Verify (with retry — see § Known Defects)**: the submenu (`chat-move-to-create-folder-menuitem`,
     `chat-move-to-back-to-list-menuitem`, and one `chat-move-to-folder-{target_folder_id}-menuitem`
     per existing folder) mounts. **Live-confirmed defect**: a single click does not reliably open
     this submenu (roughly half of ~6 isolated repros needed a second click) and hovering (even a
     real, slow mouse move + 1.5s dwell) never opens it at all — filed as
     EliteaAI/elitea-testing-public#1117. Automation must poll-and-retry the click (see § Automation
     Hints); this is a workaround for a known, filed, isolated defect on the *activation gesture*,
     not a weakening of what this step proves (the submenu's correct CONTENTS are still asserted in
     full once it does open).
3. Click the target folder's own submenu item
   (`chat-move-to-folder-{target_folder_id}-menuitem`, text = `"New folder6"`).
   - **Verify**: the app-wide success toast (`toast-message`) appears with text
     **`Chat moved to "New folder6" folder successfully`** (live-verified exact string, INCLUDING
     the quote marks around the folder name — the case's own wording,
     `'Chat moved to [folder name] folder successfully'`, doesn't show quotes; matches
     `useMoveToFolderConversation.hooks.js`'s literal template
     `` `Chat moved to "${targetFolder.name}" folder successfully` `` — a minor case-text-drift
     CLARIFICATION, not a defect; assert the live string with quotes).
4. Verify `conv_target` is no longer rendered under any date-group heading.
   - **Verify**: `[data-testid="chat-conversation-item-{conv_target_id}"]`, when queried scoped to
     the top-level date-group/ungrouped container (NOT page-wide), resolves 0. A page-wide,
     unscoped count is NOT sufficient — MUI `Collapse` keeps a folder's children mounted (just
     height-animated) even while the folder is collapsed, matching the same behaviour ELITEA-2132's
     AFS documented for the empty-state text — so a bare page-wide `count()` would still return 1
     (the conversation now rendering, hidden, inside the collapsed folder) and give a false pass on
     a real "conversation was never removed from the date group" regression.
5. Expand `target_folder` (click its row) and verify `conv_target` is inside it.
   - **Verify**: `chat-folder-item-{target_folder_id}`'s `data-expanded` flips `"false"` → `"true"`;
     `[data-testid="chat-conversation-item-{conv_target_id}"]` scoped inside that folder container
     resolves 1.

## Expected Results
- Clicking "Move to" opens a submenu offering "Create folder", "Back to the list", and every
  existing folder by name (workaround for the known activation-gesture defect: retry the click if
  the submenu hasn't mounted within ~350ms — see § Known Defects).
- Picking an existing folder moves the conversation server-side (confirmed via the success toast
  text; no separate network-response assertion was added here since the toast IS the product's own
  confirmation signal for this specific mutation, unlike ELITEA-2132's raw `POST` assertion for
  folder CREATION, which has no equivalent user-facing toast to lean on).
- The conversation disappears from its date group and appears inside the target folder.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in, folder + conversation exist | — | Setup | `auth_state` fixture + API-seeded conv/folder | asserted |
| 1 Navigate to Chats, hover conversation, click 3-dot icon | Context menu appears | AFS step 1 | step 1: menu visible | asserted |
| 2 Verify context menu has: Delete, Edit, Move to, Export, Playback, Pin on top | Options visible | AFS step 1 | step 1: live set is Rename, Move to, Playback, Pin on top, Delete (5 items) | clarification *(the case's literal 6-item list — "Edit"/"Export" instead of "Rename" — doesn't match either the live product or ELITEA-2114's own already-established 5-item CLARIFICATION-2 set for this project; asserting the live, previously-confirmed set per the reverse-masking guard rather than re-litigating a settled case-text drift)* |
| 3 Hover over the Move to option | Submenu appears: Create folder, Back to the list, existing folders | AFS step 2 | step 2: submenu opened + enumerated (all 3 item types present) | asserted, with a filed defect *(hover never opens it — 0/2 live-confirmed with real mouse movement; a plain click, the component's own coded activation gesture, is also unreliable — see § Known Defects, EliteaAI/elitea-testing-public#1117. Automation reaches this state via a documented poll-and-retry workaround; the submenu's correct CONTENTS are still fully asserted once open, so this is a activation-gesture defect, not a masked assertion)* |
| 4 Click on an existing folder name (e.g. 'New folder6') | Success toast: 'Chat moved to [folder name] folder successfully' | AFS step 3 | step 3: toast text `Chat moved to "New folder6" folder successfully` | asserted *(live text includes quote marks around the folder name that the case's paraphrase omits — CLARIFICATION, not a defect; live text and case intent agree in substance)* |
| 5 Verify the conversation is no longer in Today/This Week/Older | Conversation removed from date groups | AFS step 4 | step 4: scoped 0-count in the top-level date-group container | asserted |
| 6 Expand the selected folder and verify the moved conversation is inside | Conversation inside the folder | AFS step 5 | step 5: `data-expanded` flips + scoped 1-count inside the folder | asserted |
| Expected Final State (prose): "Conversation moved to the selected folder; success toast appeared" | — | steps 3–5 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check after every interaction (Axis 2) | asserted, with 1 filed defect that does not block completion |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 1 asserts the LIVE 5-item menu set (matching ELITEA-2114's already-established
  CLARIFICATION-2), not the case's literal 6-item list — *added: re-verifying a settled case-text
  drift on every sibling case would be redundant busywork; citing the prior AFS's finding instead,
  reconfirmed live this pass rather than assumed stale.*
- Step 2 documents and works around a live-confirmed activation-gesture defect (filed
  EliteaAI/elitea-testing-public#1117) rather than silently masking it — *added: this is exactly the
  "isolated defect → `expect.soft()`-equivalent + linked ticket" shape the no-defect-masking policy
  calls for; the workaround reaches the state under test without weakening what step 2 itself
  proves once the submenu IS open (its full, correct item enumeration).*
- Step 3 asserts the exact live toast text including its embedded quote marks — *added: matches the
  sibling AFSes' pattern (ELITEA-2114's delete-confirmation text, ELITEA-2132's `POST` response
  shape) of confirming the product's own literal wording rather than a paraphrase.*
- Step 4 explicitly requires a SCOPED (not page-wide) 0-count — *added: ELITEA-2132's AFS already
  established that MUI `Collapse` keeps a collapsed folder's children mounted in the DOM; a bare
  page-wide count would silently pass even if the "removed from date groups" behaviour regressed,
  since the moved conversation is still present (hidden) inside the folder. This is worth spelling
  out explicitly since it's an easy trap for a first-pass implementation.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline, per every other AFS in this suite.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` if the move-and-assertions
   flow didn't already leave it in a state the fixture teardown handles — the conversation still
   exists (now inside the folder), it's simply had its `folder_id` changed, so a plain
   `delete_conversation` by id still works regardless of which container it's currently rendered in.
2. Delete `target_folder` via the UI Delete flow (`ChatPage.delete_folder_via_menu()`, already added
   by ELITEA-2132's implementation) OR a raw `DELETE {ELITEA_API_BASE}/elitea_core/folder/prompt_lib/{project_id}/{folder_id}`
   call if a `FolderAPI` client is added (see § Automation Hints) — either way, cleanup MUST run
   even if a mid-test assertion fails (`try`/`finally` per `.claude/rules/ui-tests.md` § Test Data
   Lifecycle). Live-verified this pass: deleting a folder that still contains a conversation
   succeeds (`204`) and doesn't orphan the conversation — it reappears in the ungrouped/date-group
   list on the next `GET .../folder/prompt_lib/{project_id}?grouped=true`, so conversation cleanup
   should run AFTER folder cleanup, or independently by id (either order works; independent
   `try`/`except` per resource, matching ELITEA-2132's round-3 pattern, is the safest shape).

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text fallback ladder
(`.agents/testing.md` § Locator policy, `.agents/role-overrides.md`).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Conversation 3-dot menu button | `[data-testid="conversation-menu-menu-button"]`, scoped inside `chat-conversation-item-{id}` | pre-existing, on-`automation/testids` ✓ | Already `ChatPage.CONVERSATION_MENU_BUTTON` / `get_conversation_menu_button()` (ELITEA-2114). |
| "Move to" context-menu item | `[data-testid="chat-conversation-menu-move-to-menuitem"]` | pre-existing, on-`automation/testids` ✓ | Already `ChatPage.CONVERSATION_MENU_ITEM.format("move-to")` / `get_conversation_menu_item("move-to")` (ELITEA-2114). |
| "Move to" submenu — "Create folder" item | `[data-testid="chat-move-to-create-folder-menuitem"]` | **ADDED this pass.** `Conversations.jsx`'s `getMoveConversationToFoldersMenuItems()` already had `key: 'create_folder'`, renamed to `'chat-move-to-create-folder'` (the `{section}-{element}-{type}` family); `DotMenu.jsx`'s `BasicMenuItem` nested-submenu rendering never forwarded `testId` to submenu items at all (root cause — see § Known Defects for the SEPARATE activation-gesture bug; this is a different, purely-cosmetic gap that happened to be found alongside it), so NO submenu item ever rendered a `data-testid` before this pass regardless of `key`. Fixed by adding `testId: subMenuItem.key` to `DotMenu.jsx`'s `subCommonProps`. Committed `automation/testids` (see commit list below). | Used by ELITEA-2137, not this case. Documented here since it's part of the same submenu. |
| "Move to" submenu — "Back to the list" item | `[data-testid="chat-move-to-back-to-list-menuitem"]` | **ADDED this pass** (same fix as above; `key` renamed `'back_to_the_list'` → `'chat-move-to-back-to-list'`). | Not exercised by either ELITEA-2135 or ELITEA-2137's steps — documented for completeness of the submenu inventory; not "referenced" per canon #511, no test currently calls it. |
| "Move to" submenu — a specific existing folder | `[data-testid="chat-move-to-folder-{folder_id}-menuitem"]` (dynamic) | **ADDED this pass.** `folderItems` in `getMoveConversationToFoldersMenuItems()` had **no `key` field at all** before this pass (only `label: targetFolder.name`) — combined with the `DotMenu.jsx` gap above, this meant clicking an existing folder in the submenu had to be done by accessible name/role (a testid-policy violation for real automation). Added `key: \`chat-move-to-folder-${targetFolder.id}\`` to the `folderItems.map()` callback. **This also fixed a live-confirmed side-effect defect**: without an explicit `key`, `DotMenu.jsx`'s submenu rendering falls back to `subMenuItem.key \|\| subMenuItem.label` for React's own list key — two folders sharing the same default `"New folder"` name (a very plausible real-world scenario, and this suite's own ELITEA-2137 test creates exactly that name) collided on that fallback, producing a live-confirmed React console warning: `Warning: Encountered two children with the same key ... .$New folder`. Reconfirmed clean (0 console errors) after this fix. | This case's own step-3 handle. |
| Success toast | `[data-testid="toast-message"]` | pre-existing, `ChatPage.toast_message` (ELITEA-2162) | Generic app-wide toast, reused verbatim. |
| Target folder's own row (for step 5) | `[data-testid="chat-folder-item-{folder_id}"]`, `data-expanded` attribute | pre-existing, `ChatPage.FOLDER_ITEM` (ELITEA-2132) | Reused verbatim. |
| Conversation item inside a folder (for step 4/5) | `[data-testid="chat-conversation-item-{id}"]`, scoped inside `FOLDER_ITEM` for the "is inside" check, scoped inside the top-level date-group/ungrouped container for the "is removed" check | pre-existing (`ChatPage.CONVERSATION_ITEM`) | Same testid template renders in EITHER location — scoping via the parent container is what distinguishes "in a folder" from "in the flat list", not a different testid. See step 4's note on why an UNSCOPED count is a trap. |

**Testid commit provenance**: all 3 additions above (`chat-move-to-create-folder-menuitem`,
`chat-move-to-back-to-list-menuitem`, `chat-move-to-folder-{id}-menuitem`) plus 2 more used only by
ELITEA-2149 (`data-pinned` attribute, `chat-pin-icon`) were made in ONE commit on
`EliteaAI/EliteaUI`'s `automation/testids`, commit `cf348d32` ("test: [EL-2135] add data-testid for
Move-to submenu items + pin icon/state"), pushed. A separate, unrelated pre-existing uncommitted fix
found in the working tree (a `modules-toggle-{tool}` testid wiring bug from an earlier ELITEA-2162
session) was committed independently as `e22e9881` in the same push — not part of this case's own
testid budget, called out here only so the two commits aren't conflated.

## Network Behavior
- `PUT`/edit request via `useConversationEditMutation` (same mutation family as
  `ConversationAPI.rename_conversation`) — `{"folder_id": <target_folder_id>}` — fires on confirm;
  not independently asserted in this AFS (see § Expected Results — the toast is treated as the
  product's own confirmation signal for this mutation, consistent with not re-deriving what the UI
  already proves).
- `GET .../folder/prompt_lib/{project_id}?...&grouped=true` refetches after the move (standard
  folder-list refresh pattern already documented in ELITEA-2132's AFS).
- Pre-existing, unrelated: project 399's `GET /api/v2/secrets/secrets/default/{project_id}` `403` —
  present on every page load in this environment (documented in every sibling AFS); excluded from
  "no new console errors" checks.

## Known Defects Found During Exploration

- **[MAJOR] EliteaAI/elitea-testing-public#1117** — "Move to" submenu does not open reliably.
  Hovering the "Move to" menu item (the interaction the case text describes, and the interaction its
  own right-pointing arrow icon visually implies, matching desktop-submenu conventions) NEVER opens
  the submenu — confirmed 0/2 with a real, slow mouse movement + 1.5s dwell (ruling out a
  hover-intent-threshold explanation), and 0/1 via the standard MUI/WAI-ARIA keyboard gesture
  (`ArrowDown` ×2 to focus "Move to", then `ArrowRight`). The component's own CODED intended
  activation — confirmed by reading `ConversationItem.jsx`'s `menuItems` array (`hasSubMenu: true`)
  and `DotMenu.jsx`'s `BasicMenuItem` (`onClick={subMenuItems?.length ? onClickMenu : onClick}`) — IS
  a plain click, not hover. But even that coded-intended click is unreliable in practice: across ~6
  isolated fresh-conversation repros, the submenu opened on the first click roughly half the time and
  needed a second click the rest; a click while the submenu is already open closes it again
  (consistent with the click landing on the submenu's own invisible backdrop and being read as a
  click-away). This satisfies the interaction-discovery ladder (`.agents/role-overrides.md`): wait
  N/A (no debounced field), Enter N/A, no adjacent activation control exists, blur N/A, no close
  analog in-app, and the decisive "read the source" step confirms the intended mode (click) still
  fails — so this is a CONFIRMED product defect, not a case-text drift. **Does not block this case**:
  a documented poll-and-retry workaround reliably reaches the open-submenu state (see § Automation
  Hints), and the submenu's own correct contents are still fully asserted once open — this is an
  activation-gesture defect, isolated to opening the submenu, not a defect in the move itself (which
  works correctly and completely once the submenu is reached).

## Blocked Steps
None. All case steps were executable and confirmed live (working around the filed defect above).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor` (`.agents/testing.md`).
- Page object: extend `automation/pages/chat_page.py`. Reuse `open_conversation_context_menu()`,
  `get_conversation_menu_item()`, `click_conversation_menu_item()` (all pre-existing, ELITEA-2114).
- **New method needed to reach the open submenu reliably**:
  `open_move_to_submenu(conversation_id, max_attempts=4)` — click
  `CONVERSATION_MENU_ITEM.format("move-to")`, then poll for
  `[data-testid="chat-move-to-create-folder-menuitem"]` (or any submenu member) to become visible
  within ~350–500ms; if not, click "Move to" again (up to `max_attempts`). Live-verified this pattern
  reaches the open state reliably within 1–2 attempts every time across ~6 repros. **Do NOT** use
  `page.wait_for_timeout` alone without the retry-click — a longer fixed wait after a single click
  was ALSO tested (700ms, then separately 1.5s of pure dwell with no second click) and did not open
  it; the retry-CLICK is what's load-bearing, not additional wait time.
- New method needed: `select_move_to_folder(folder_id_or_new)` — click
  `chat-move-to-folder-{id}-menuitem` for an existing folder (this case) or
  `chat-move-to-create-folder-menuitem` (ELITEA-2137's flow).
- New class constant: `MOVE_TO_FOLDER_ITEM = '[data-testid="chat-move-to-folder-{}-menuitem"]'`
  (dynamic template, per `.agents/testing.md` § Locator policy's dynamic-testid pattern — format
  with the folder id, never an inline f-string `get_by_test_id`).
- **No `FolderAPI` client exists yet** in `automation/api/client.py` — same standing recommendation
  as ELITEA-2132's AFS (a small class mirroring `ConversationAPI`'s shape:
  `create_folder(name)`/`delete_folder(id)`/`list_folders()` against the endpoints confirmed live in
  § Network Behavior and ELITEA-2132's own Network Behavior section). Until it exists, seed via a raw
  `requests` call using the same Bearer-token-on-localhost fallback `ConversationAPI` already uses,
  or via the existing UI create-folder flow (`ChatPage.create_folder()`, ELITEA-2132) if avoiding a
  second HTTP client entirely is preferred for a single test.
- Priority marker: this case's frontmatter `priority: medium` maps to `@pytest.mark.p2` (per
  `pytest.ini`'s p0=critical…p3=low scale) — NOT `@pytest.mark.p3`, despite the AFS filename's `l3`
  prefix. The `l`-number and the `p`-marker are on different scales in this suite (confirmed against
  the ELITEA-2132/ELITEA-2114 sibling AFSes: `medium`→`l3`/`p2`, `high`→`l2`/`p1`) — use `p2`.
