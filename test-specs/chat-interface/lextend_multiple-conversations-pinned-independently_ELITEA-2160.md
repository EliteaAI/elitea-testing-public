# Test Case: Chat – Multiple Conversations Can Be Pinned Independently

## Metadata
- **TMS ID**: ELITEA-2160
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, same mapping as
  ELITEA-2149/2150/2152/2153)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — `${ELITEA_PROJECT_ID}`)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer) — batch chat-remaining-w09,
  clustered with ELITEA-2161 (folder equivalent) in the same session
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_pin_conversation.py` (merged
  `origin/automation/base` commit `fb306056`, wave-08) — new class
  `TestMultipleConversationsPinnedIndependently`, zero existing method bodies touched
- **surface_key**: `chat-conversation-context-menu` (same surface as ELITEA-2149/2150/2151/2159)

## Case-text drift (environmental, documented before this pass — no new probe needed)
The case's Step 2 asks to pin "a second conversation from This Week". This environment has **zero
non-today conversations** in either accessible project, and the API cannot backdate
`created_at`/`updated_at` (`ConversationCreate`/`ConversationUpdate` OpenAPI schemas carry no
timestamp field at all) — already documented in `test-specs/chat-interface/_surface.md` §
"Date-group bucketing (Today/This Week/Older) is SERVER-computed" (ELITEA-2096/2097, `blocked` for
this exact reason) and re-confirmed live this session (`conversation_api.list_conversations()` on
project 399: 5 rows, 0 non-today). Unlike ELITEA-2096/2097 (whose own subject IS opening a
This-Week/Older item), this case's actual subject — pinning multiple conversations
**independently** (pinning the second does not disturb the first; both appear; both leave their
origin group) — does not require the two conversations to start in *different* date groups, only
that each starts in *some* date group and both correctly leave it. Both `conv_1`/`conv_2` are
seeded fresh (both land in "Today", the only reachable group); the AFS asserts the real,
live-reachable scenario rather than a "This Week" origin that cannot be honestly produced.
Recommend a case-text CLARIFICATION on this environmental limitation — not a product bug (the
product itself is never exercised in a way that could reveal one here; this is purely a test-data
reachability gap already tracked for ELITEA-2096/2097).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least two conversations exist, both ungrouped (not inside a folder) — "Pin on top" is disabled
  for an in-folder, not-yet-pinned conversation (`!isPinned && !!conversation.folder_id`,
  ELITEA-2136/2138's already-documented rule). Test creates its own (see § Test Data).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_1`** — first conversation to pin. `conversation_api.create_conversation(name)`.
- **`conv_2`** — second conversation to pin, created immediately after `conv_1`.
- **`folder_unpinned`** — an empty, never-pinned folder (`conversation_api.create_folder(name)`),
  used purely as the "unpinned content" comparison baseline for step 3's panel-order check (the
  case's own wording is "above unpinned FOLDERS", not "above unpinned conversations").

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Pin `conv_1` via its 3-dot menu → "Pin on top"
   (`chat-conversation-menu-pin-menuitem`).
   - **Verify**: `conv_1` carries `data-pinned="true"` on `chat-conversation-item-{conv_1_id}`; a
     `chat-pin-icon` renders inside it (0→1 transition).
2. Pin `conv_2` via the same mechanism.
   - **Verify**: `conv_2` carries `data-pinned="true"` + `chat-pin-icon` renders inside it; **AND**
     `conv_1` STILL carries `data-pinned="true"` (pinning the second did not silently unpin the
     first — this is the case's own core independence claim, asserted as a re-check, not assumed).
3. Verify both pinned conversations are visible above unpinned folders.
   - **Verify**: `conv_1` and `conv_2`'s bounding-box Y (+ height) are both `<=` `folder_unpinned`'s
     bounding-box Y (source-confirmed render order, `Conversations.jsx`: pinned folders →
     `<PinnedConversations>` → unpinned folders → date-grouped conversations — pinned conversations
     render above ANY folder section, pinned or not).
4. Verify both conversations are no longer in their original date groups.
   - **Verify**: `chat-conversation-item-{conv_1_id}` and `chat-conversation-item-{conv_2_id}`, each
     scoped inside the "today" date-group container (`CONVERSATION_GROUP_HEADER.format("today")`),
     resolve 0 (both items still exist page-wide, in the pinned section — this is a scoped check).

## Expected Results
- Pinning `conv_2` after `conv_1` does not unpin, hide, or otherwise disturb `conv_1` — both remain
  independently pinned and visible.
- Both pinned conversations render above all folder sections (pinned or unpinned).
- Both conversations are removed from their original ("today") date group.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥2 conversations in different date groups | — | Setup + case-text drift note | `conv_1`/`conv_2` API-seeded, both reachable "today" group (see drift note) | asserted, with documented environmental scope note |
| 1 Pin conv from Today; verify appears pinned + pin icon | First conversation pinned | AFS step 1 | `data-pinned="true"` + `chat-pin-icon` count 1 | asserted |
| 2 Pin second conv from This Week; verify also appears pinned + pin icon | Second conversation pinned | AFS step 2 | `data-pinned="true"` + `chat-pin-icon` count 1 for `conv_2`, PLUS `conv_1` re-checked still pinned | asserted (origin group per drift note) |
| 3 Verify both pinned conversations visible above unpinned folders | Both pinned; above unpinned content | AFS step 3 | Y-position of both vs `folder_unpinned` | asserted |
| 4 Verify both conversations no longer in original date groups | Removed from date groups | AFS step 4 | scoped 0-count in "today" group container, both ids | asserted |
| Expected Final State: "Multiple conversations pinned independently and visible in pinned section" | — | steps 1–4 | covered by rows above | asserted |
| Pass/Fail: "Only one conversation can be pinned at a time" must NOT happen | — | step 2's `conv_1` re-check | `conv_1.data-pinned == "true"` after pinning `conv_2` | asserted — this is the test's central negative assertion |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 2 re-checks `conv_1`'s pinned state after pinning `conv_2` — *added: the case's own Fail
  criterion ("Only one conversation can be pinned at a time") is a negative claim about the FIRST
  conversation's state after the SECOND action, which the case's literal step list never explicitly
  re-asserts; this AFS makes it an explicit assertion rather than an implied one.*
- Step 3 asserts against `folder_unpinned` specifically (not a date-group heading) — *added: matches
  the case's own literal wording ("above unpinned folders"), a stronger/more specific claim than the
  2-tier date-group-heading comparison ELITEA-2149's own AFS uses, and distinct from it (this pair of
  cases is the first to specifically request the folder-tier comparison for CONVERSATIONS).*
- Console/network side-channel checked after every interaction, same idiom as ELITEA-2149/2151.

## Cleanup
1. Delete `conv_1`, `conv_2` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_unpinned` via `conversation_api.delete_folder(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)
All handles pre-exist from ELITEA-2114/2149/2150 — zero new testid work.

| Element | Testid handle | Provenance |
|---|---|---|
| Pin/Unpin context-menu item | `[data-testid="chat-conversation-menu-pin-menuitem"]` | on-`automation/testids` ✓ + on-`main` ✓ (ELITEA-2114) |
| Conversation pinned-state attribute | `data-pinned="true"/"false"` on `chat-conversation-item-{id}` | on-`automation/testids` ✓ (ELITEA-2149, not yet independently re-verified on `main` this session — same commit `cf348d32` as ELITEA-2149) |
| Pin icon | `[data-testid="chat-pin-icon"]`, scoped inside `chat-conversation-item-{id}` | same commit as above |
| Folder item (for step 3's comparison) | `chat-folder-item-{id}` | pre-existing (ELITEA-2121/2130) |
| Date-group container | `chat-conversation-group-header-{group}` | pre-existing (ELITEA-2095) |

## Network Behavior
- `POST /pin/prompt_lib/{project_id}/conversation/{conversation_id}` per pin (source-confirmed,
  `usePinConversation.hooks.js`) — not independently network-asserted; UI-state assertions are
  treated as sufficient (same reasoning as ELITEA-2149's AFS).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks.

## Known Defects Found During Exploration
None. The independence mechanism (pinning a second conversation does not affect the first) worked
correctly on live re-verification via the implementation's own pytest run (see Run Report). The only
finding is the environmental This-Week-origin gap documented above (not a product defect).

## Blocked Steps
None — the case's core subject (independent multi-pin) is fully automatable; only the flavor detail
of a "This Week" origin for `conv_2` is environmentally unreachable, and is not required to prove the
case's actual pass/fail criteria.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: `automation/pages/chat_page.py` — zero new methods needed. Reuse
  `open_conversation_context_menu()`, `click_conversation_menu_item("pin")`,
  `is_conversation_pinned()`, `get_pin_icon()`, `get_conversation_item()`,
  `is_conversation_in_group()`, `get_folder_item()` (all pre-existing).
- Priority marker: `@pytest.mark.p2`.
