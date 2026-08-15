# Test Case: Chat – Move To Submenu Folder List is Scrollable When Many Folders Exist

## Metadata
- **TMS ID**: ELITEA-2147
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`; see ELITEA-2135's
  AFS for the medium→l3/p2 mapping evidence in this suite)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2146, ELITEA-2148 (chat-remaining
  wave-07): one live session, per-case execution — this case shares the "Move to" submenu surface
  already deeply documented for ELITEA-2135/ELITEA-2137 (`chat-conversation-context-menu`), but its
  own steps (scrolling the submenu's folder list specifically) are new; genuinely different steps
  from ELITEA-2146/ELITEA-2148 (a different popover-based UI surface, not the sidebar), so it gets
  its own AFS rather than being merged into either.
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-list`

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- Many folders exist in the project (seeded, see § Test Data — same reasoning as ELITEA-2146: the
  account's 65+ ambient/orphaned folders already reproduce this live, but the test seeds its own
  deterministic set instead of depending on ambient state).
- **Known, already-filed defect affects the OPENING gesture, not this case's own assertion**: the
  "Move to" submenu does not reliably open on a single click
  (EliteaAI/elitea-testing-public#1117, documented in ELITEA-2135/ELITEA-2137's AFS and already
  handled by `ChatPage.click_move_to_and_wait_for_submenu()` / `open_move_to_submenu()`'s
  click-and-retry loop). This case reuses those existing methods rather than re-deriving the
  workaround — confirmed live this pass: the submenu opened on the FIRST click this run (the defect
  is non-deterministic, not "always fails"), and the existing retry loop is what makes that
  non-determinism safe to automate against.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`seeded_folders`** — 25 folders, created via `conversation_api.create_folder(f"AutoScrollMoveToFolder{i}")`
  for `i` in `range(25)` — same sizing rationale as ELITEA-2146 (25 × ~41px collapsed-row-equivalent
  submenu-item height comfortably exceeds the popover's measured available height; see § Concrete
  Handles for this case's own live measurement, which came out even larger than the sidebar's).
- **`conv_target`** — the conversation whose "Move to" submenu is opened. Create via
  `conversation_api.create_conversation(name)`. Must be UNGROUPED (no `folder_id`) and NOT pinned —
  "Move to" is disabled for a pinned conversation (`ConversationItem.jsx`: `disabled: isPinned || ...`,
  documented in ELITEA-2135/ELITEA-2149's AFSes); a freshly-created conversation satisfies both
  (lands ungrouped in "Today", never pinned by default).

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Hover `conv_target`'s sidebar item, click its 3-dot menu, hover
   (click, per the known-defect workaround) **Move to**.
   - **Verify**: submenu appears with **Create folder**, **Back to the list**, and the folder list —
     `chat-move-to-create-folder-menuitem` and `chat-move-to-back-to-list-menuitem` both visible
     (both pre-existing testids, ELITEA-2135/ELITEA-2137).
2. Verify that when many folders exist, the folder list in the submenu is scrollable.
   - **Verify**: the submenu's own MUI `Menu` popover Paper (**testid needed**, see § Concrete
     Handles) has `scrollHeight > clientHeight` via the same evaluate-based genuine-overflow check
     ELITEA-2146 uses for the sidebar container — never trust `overflow-y: auto` alone. Live-confirmed
     this pass: `scrollHeight=2781` vs `clientHeight=802` (with 67 ambient folder items rendered in
     the submenu) — genuinely overflowing, MUI's own default Popover sizing (`maxHeight: calc(100% -
     96px)`), not a bespoke behavior EliteaUI added.
3. Scroll down through the submenu folder list via a REAL scroll gesture (mouse wheel, hovering the
   popover Paper).
   - **Verify**: all seeded folders are accessible — after scrolling to the popover's maximum
     `scrollTop`, the LAST seeded folder's `chat-move-to-folder-{folder_id}-menuitem` is within the
     popover's own bounding box (same "prove reachability, not just scrollTop movement" discipline as
     ELITEA-2146 step 4).
4. Select the last seeded folder from the scrolled-to position.
   - **Verify**: `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
     `{"folder_id": <last_seeded_folder_id>}` fires and returns 200 (source-confirmed endpoint,
     `useMoveToFolderConversation.hooks.js`) — live-confirmed this pass via
     `browser_network_requests` (`PUT .../elitea_core/conversation/prompt_lib/399/8152` → 200 for an
     analogous move during this exploration). Conversation moved; success toast appears:
     `Chat moved to "${targetFolder.name}" folder successfully` (documented, ELITEA-2135/ELITEA-2137's
     AFS — WITH quote marks around the folder name, the case text's paraphrase omits them, cosmetic
     drift only). Additionally: `conv_target` now renders inside the last seeded folder's row
     (`is_conversation_in_folder(last_seeded_folder_id, conv_target_id)` reads `True`, pre-existing
     helper).

## Expected Results
- The submenu's folder-list popover genuinely overflows (`scrollHeight > clientHeight`) once enough
  folders exist.
- A real scroll gesture reveals folders beyond the popover's initial viewport, including the very
  last one.
- Selecting a folder reached only via scrolling still correctly moves the conversation (proves the
  scrolled-to items are not just visually present but functionally live, not decorative/inert).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: many folders exist | — | Setup | 25 API-seeded folders (§ Test Data) | asserted |
| 1 Navigate to Chats, hover conversation, click 3-dot icon, hover Move to | Submenu appears with Create folder, Back to the list, folder list | AFS step 1 | both fixed menu items visible | asserted |
| 2 Verify when many folders exist the folder list in the submenu is scrollable | Folder list is scrollable | AFS step 2 | popover Paper `scrollHeight > clientHeight` | asserted |
| 3 Scroll down through the submenu folder list | All folders are accessible | AFS step 3 | last seeded folder's menuitem within popover bounds at max scroll | asserted |
| 4 Select any folder from the scrollable list | Conversation moved; success toast appears | AFS step 4 | `PUT .../conversation/.../{id}` 200 + toast text + `is_conversation_in_folder()` True | asserted |
| Expected Final State (prose): "Submenu folder list is scrollable; all folders accessible" | — | steps 2–3 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (Axis 2) | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 2 asserts genuine popover overflow via computed `scrollHeight`/`clientHeight` rather than
  trusting MUI's default `overflow-y: auto` styling — *added: same "CSS declares scrollable ≠ proven
  scrollable" discipline as ELITEA-2146; a short folder list would still carry the `overflow-y: auto`
  declaration without ever overflowing.*
- Step 3 anchors on the actual LAST seeded folder's presence within the popover bounds, not just a
  `scrollTop` delta — *added: same reachability-proof discipline as ELITEA-2146 step 4; a `scrollTop`
  move alone doesn't prove any specific folder became reachable.*
- Step 4 goes beyond the case's own literal ask ("select any folder") by selecting SPECIFICALLY the
  folder reached only via scrolling (the last one), and verifies the real network mutation + resulting
  DOM placement, not just that the submenu closes — *added: closes the gap between "the item is
  visually present after scrolling" and "the item is functionally wired, not a stale/detached render"
  — a scrolled-into-view item that fails to actually move the conversation would be a real, distinct
  defect this case's literal wording wouldn't otherwise catch.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline for this suite.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` (works identically whether or
   not the conversation ended up inside a folder — no special unfile-first step required, same as the
   pattern ELITEA-2149's AFS already confirmed for pinned conversations).
2. Delete all 25 `seeded_folders` via `conversation_api.delete_folder(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| "Create folder" / "Back to the list" submenu items | `chat-move-to-create-folder-menuitem` / `chat-move-to-back-to-list-menuitem` | pre-existing, on-`automation/testids` ✓ (ELITEA-2135/ELITEA-2137, commit `cf348d32`) | `ChatPage.move_to_create_folder_menuitem`. |
| Existing-folder submenu entry (dynamic) | `[data-testid="chat-move-to-folder-{folder_id}-menuitem"]` (`MOVE_TO_FOLDER_ITEM` template) | pre-existing, on-`automation/testids` ✓ (ELITEA-2135/ELITEA-2137) | `ChatPage.get_move_to_folder_item(folder_id)` / `select_move_to_folder(folder_id)` (both pre-existing). |
| Submenu open (with retry for #1117) | n/a (composed action) | pre-existing | `ChatPage.open_move_to_submenu(conversation_id)` (pre-existing, `chat_page.py:3626`). |
| **Submenu folder-list popover container** (the MUI `Menu`'s Paper — role="menu" `<ul>`'s closest `.MuiPaper-root`) | **testid needed**: e.g. `chat-move-to-submenu-popover` on the nested `<Menu>` in `DotMenu.jsx` (line ~93, the `subMenuItems?.length &&` branch) — add via `slotProps={{ paper: { 'data-testid': 'chat-move-to-submenu-popover' } }}` (MUI Menu forwards this to its Paper). Zero new DOM node — MUI already renders this Paper, this is a pure attribute addition on an existing element. | **ADD via `add-data-testid`.** Currently carries NO testid and NO `id` at all (confirmed live this pass via DOM inspection — `paper.getAttribute('data-testid')` and `paper.id` both empty/null). | New: `ChatPage.move_to_submenu_popover = LocatorDescriptor(testid="chat-move-to-submenu-popover")` + `get_move_to_submenu_scroll_metrics()` / `is_move_to_submenu_scrollable()` / `scroll_move_to_submenu()`, mirroring the `chat_messages_scroll_container` trio (same pattern ELITEA-2146 specs for the sidebar container). **Scoping caveat**: `DotMenu.jsx` renders this SAME nested-`Menu` shape for every dot-menu instance in the app with `subMenuItems` (not folder-move-specific) — if a testid this specific would collide with a future unrelated submenu, the implementer should confirm at add-time whether a single static testid is safe (only one such submenu can be open at a time, so likely yes) or whether it needs scoping; call out either way in the Run Report. |

**Live measurement (this pass, confirms the submenu popover genuinely overflows):**
- With `conv_target`'s "Move to" submenu open and 67 ambient folder items rendered: popover Paper
  `scrollHeight=2781`, `clientHeight=802`, computed `overflow-y: auto`, computed
  `max-height: calc(100% - 96px)` (MUI's own default Popover/Menu sizing — EliteaUI adds no bespoke
  height logic here).
- Confirmed the mechanism is FUNCTIONAL, not just visual: scrolled the popover to `scrollTop=1979`
  (its max), clicked the then-visible last folder item
  (`chat-move-to-folder-88-menuitem` in this exploration run), and observed a real
  `PUT .../elitea_core/conversation/prompt_lib/399/8152 → 200` in `browser_network_requests` — the
  scrolled-to item is genuinely wired, not a decorative/detached render.

## Network Behavior
- Move: `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
  `{"folder_id": <target_folder_id>}` → 200 (source-confirmed, `useMoveToFolderConversation.hooks.js`;
  live-confirmed this pass for an analogous move during exploration).
- Folder create/delete: same endpoints as ELITEA-2146 (`ConversationAPI.create_folder`/`delete_folder`).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS.

## Known Defects Found During Exploration
None NEW to this case. Affected by the pre-existing, already-filed
EliteaAI/elitea-testing-public#1117 ("Move to" submenu doesn't reliably open on one click) at the
OPENING step only — already handled by the existing `click_move_to_and_wait_for_submenu()` retry
loop, not this case's own subject. This case's own subject (the submenu's folder-list scrollability)
worked correctly and genuinely on every check this pass.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py`. Reuse `open_move_to_submenu()`,
  `get_move_to_folder_item()`, `select_move_to_folder()` (all pre-existing, ELITEA-2135/ELITEA-2137).
  Add the popover-scroll trio per § Concrete Handles, mirroring the
  `chat_messages_scroll_container`/ELITEA-2146-sidebar pattern — do not invent a third shape for the
  same "is this container genuinely scrollable" question already answered twice elsewhere in this
  file.
- Real scroll gesture: hover the popover Paper, `page.mouse.wheel(0, delta_y)` — same idiom as
  ELITEA-2146 and `scroll_messages_container()`. The `el.scrollTop = N` assignment used in this
  exploration pass (via `browser_evaluate`) was for confirmation speed only and must not ship in the
  automated test — same fidelity-policy note as ELITEA-2146.
- Priority marker: `@pytest.mark.p2` (see ELITEA-2135's AFS note on the l3/p2 mapping).
- Feature markers: `@pytest.mark.chat`, `@pytest.mark.regression`.
