# Test Case: Chat – Pinned Conversation Appears Above Unpinned Folders and Conversations

## Metadata
- **TMS ID**: ELITEA-2151
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case frontmatter: `priority: medium` → `@pytest.mark.p2`; same medium→l3-ish/p2
  mapping already used across this surface, e.g. ELITEA-2149's AFS — filename prefix bumped to
  `lextend_` per this AFS's `extend-existing` status, not a priority signal)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: test-automation-engineer (agent) — combined analyst+implementer slot, batch
  `chat-remaining-w08`
- **Status**: extend-existing
- **surface_key**: `chat-conversation-context-menu` (shares the pin/unpin surface with
  ELITEA-2149/2150; also touches the folder-pin surface, `chat-folder-context-menu`,
  ELITEA-2121/2130)
- **Extension target**: `automation/tests/ui/chat/test_pin_conversation.py`

## Preconditions (case)
- User is logged in to the Elitea platform.
- At least one pinned and one unpinned item exist.

This AFS's own setup satisfies both preconditions by seeding all four items itself (a pinned
folder, a pinned conversation, an unpinned folder, an unpinned conversation) rather than relying
on ambient shared-DEV-project data — deterministic, matches the read-only-by-default rule's escape
hatch (the observable — cross-tier ordering — inherently requires knowing the identity and freshly-
pinned state of specific rows, not just "some pinned thing exists somewhere").

## Why `extend-existing`, not `ready-for-automation`

`test_pin_conversation.py` (ELITEA-2149/2150) already exercises the SAME "Pin on top" conversation
mechanism and already asserts a 2-of-4-tier panel-order check (pinned conversation above the
"Today" heading / above an unpinned sibling conversation). ELITEA-2149's own AFS
(`test-specs/chat-interface/l3_pin-conversation-via-pin-on-top_ELITEA-2149.md`, § Automation Hints)
explicitly deferred the remaining 2 tiers as a named, un-taken option:

> "(b) seed one throwaway pinned folder via a raw `POST /pin/prompt_lib/{project_id}/folder/{folder_id}`
> call ... purely to complete a 4-tier live assertion. This AFS recommends (a) for a first
> implementation ... and flags (b) as a legitimate follow-up if a future case specifically targets
> folder-pinning."

ELITEA-2151 is precisely that follow-up case (its own case text asks for the full 4-tier ordering
and an explicit "no pinned item below any unpinned item" check). The digest
(`test-specs/chat-interface/_surface.md`, § Pin conversation) independently flags the same gap:
"a full 4-tier live check needs a seeded pinned FOLDER, which no case so far has needed; flagged as
a follow-up opportunity, not done." No existing test seeds a pinned folder anywhere in this suite
(only `test_chat_folder_rename_checkmark_validation.py`'s ELITEA-2130 pins a folder, but never
compares its position against a pinned/unpinned conversation — a different case, different
assertion). This is new coverage: a fresh test method appended to the existing pin-conversation
file, zero modification to ELITEA-2149/2150's existing method bodies.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_pinned`** — a folder that gets pinned via the UI during Step 1. Create via
  `conversation_api.create_folder(name)`, starts unpinned (server default).
- **`folder_unpinned`** — a folder that stays unpinned throughout. Create via
  `conversation_api.create_folder(name)`.
- **`conv_target`** — the conversation to pin. Create via `conversation_api.create_conversation(name)`.
  Must NOT already be inside a folder (same "Pin on top" precondition ELITEA-2149's AFS documents —
  a freshly API-created conversation naturally satisfies this).
- **`conv_unpinned`** — a conversation that stays unpinned, in its "Today" date group throughout.
  Create via `conversation_api.create_conversation(name)`.

## Test Steps

1. Pin `folder_pinned` via its dot-menu's "Pin on top" item (`chat-folder-menu-pin-menuitem`,
   PATCH `/elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → 200). Pin `conv_target` via
   its own 3-dot menu's "Pin on top" item (`chat-conversation-menu-pin-menuitem`).
   - **Verify**: both `chat-folder-item-{folder_pinned_id}` and
     `chat-conversation-item-{conv_target_id}` carry `data-pinned="true"` after their respective
     pin actions — "Conversation appears in pinned section" (case Step 1's expected result),
     mirrored for the folder side of the same mechanism.
2. Verify the left panel order from top to bottom: pinned folders, pinned conversations, unpinned
   folders, unpinned conversations.
   - **Verify**: bounding-box Y-position, adjacent-tier comparisons across all 4 tiers —
     `folder_pinned` above `conv_target` (pinned-folders block precedes `<PinnedConversations>`),
     `conv_target` above `folder_unpinned` (`<PinnedConversations>` precedes the unpinned-folders
     block), `folder_unpinned` above `conv_unpinned` (unpinned-folders block precedes the
     date-grouped/ungrouped conversation list). Source-confirmed render order
     (`Conversations.jsx`, `automation/base`-visible history — `renderFoldersSection({isPinned:
     true})` → `<PinnedConversations>` → `renderFoldersSection({isPinned: false})` →
     `<DroppableGroupedArea><GroupedConversations>`), now also LIVE-verified across all 4 tiers by
     this case (closing the gap ELITEA-2149's AFS left open).
3. Verify no pinned item appears below any unpinned item.
   - **Verify**: explicit cross-tier checks beyond the adjacent-tier comparisons in Step 2 —
     `folder_pinned` above `folder_unpinned`, `folder_pinned` above `conv_unpinned`, `conv_target`
     above `conv_unpinned` (the two "far" pinned-vs-unpinned pairs the adjacent-tier chain in Step 2
     only proves transitively; asserted directly here per the case's own literal Step 3 wording).

## Expected Results
- Both the pinned folder and pinned conversation carry `data-pinned="true"` and render in their
  respective pinned tiers.
- Full left-panel order, top to bottom: pinned folders → pinned conversations → unpinned folders →
  unpinned conversations (by date group).
- No pinned item (folder or conversation) renders below any unpinned item (folder or conversation).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥1 pinned and ≥1 unpinned item exist | — | Setup + AFS step 1 | pin both a folder and a conversation via UI; keep one unpinned folder and one unpinned conversation | asserted |
| 1 Pin at least one conversation using Pin on top | Conversation appears in pinned section | AFS step 1 | `data-pinned="true"` on both `folder_pinned` and `conv_target` after their pin actions | asserted |
| 2 Verify left panel order top to bottom: pinned folders, pinned conversations, unpinned folders, unpinned conversations by Today/This Week/Older | Panel order matches expected | AFS step 2 | 3 adjacent-tier bounding-box Y comparisons spanning all 4 tiers | asserted |
| 3 Verify no pinned item appears below any unpinned item | Ordering is correct | AFS step 3 | 3 explicit non-adjacent-pair bounding-box Y comparisons | asserted |
| Expected Final State (prose): "Panel maintains correct ordering with pinned items above unpinned" | — | steps 2–3 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (Axis 2) | asserted, 0 console errors expected (see § Network Behavior for the pre-existing exclusion) |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 1 pins BOTH a folder and a conversation (the case's own text only explicitly says "pin at
  least one conversation") — *added: the case's own Steps 2–3 require comparing against a pinned
  FOLDER tier too ("pinned folders" is literally the first tier named), which cannot exist without
  pinning one; this is not scope creep, it is the minimum fixture the case's own later steps
  require to be checkable at all — the exact gap ELITEA-2149's AFS named and deferred.*
- Step 2 uses 3 ADJACENT-tier comparisons (folder_pinned/conv_target, conv_target/folder_unpinned,
  folder_unpinned/conv_unpinned) rather than one direct top-tier-vs-bottom-tier check — *added: an
  adjacent-tier chain is a stronger, more diagnostic proof than a single first-vs-last comparison
  (pinpoints exactly which boundary breaks if one does), same reasoning as any ordered-sequence
  assertion.*
- Step 3 adds the 2 "skip" pairs the adjacent chain only proves transitively
  (`folder_pinned`-vs-`folder_unpinned`, `folder_pinned`-vs-`conv_unpinned`) plus the already-implied
  `conv_target`-vs-`conv_unpinned` — *added: matches the case's own literal Step 3 wording ("no
  pinned item appears below any unpinned item") as a direct assertion, not merely an inference from
  Step 2's chain — defends against a future partial-refactor that reorders two NON-adjacent tiers
  while leaving each adjacent pair individually correct (a scenario the chain alone cannot catch).*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline matching every sibling test in this file/surface.*
- Uses `expect_response()` around the folder PATCH (mirrors `test_chat_folder_rename_checkmark_
  validation.py`'s ELITEA-2130 pin-folder idiom exactly — proven deterministic there) rather than a
  bare click + immediate attribute read, for the folder side specifically — *added: reduces flake
  risk on the newer, less-exercised folder-pin path; the conversation-pin path reuses ELITEA-2149's
  own already-proven bare click + `is_conversation_pinned()` idiom unchanged.*

## Cleanup
1. Delete `conv_target`, `conv_unpinned` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_pinned`, `folder_unpinned` via `conversation_api.delete_folder(id)` — deleting a
   pinned folder was not previously independently verified in this digest, but deleting a pinned
   CONVERSATION was (ELITEA-2149's AFS: "no special unpin-first step required") and the folder
   delete endpoint (`DELETE /elitea_core/folder/prompt_lib/{project_id}/{folder_id}`) has no
   pin-state precondition documented anywhere — same `try/finally`, non-fatal on individual
   cleanup failure (logged, not raised), per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Folder pin/unpin context-menu item | `[data-testid="chat-folder-menu-pin-menuitem"]` | pre-existing, on `automation/testids` (ELITEA-2121/2130, commit `be489cee`; NOT yet on `main` — human cherry-pick pending, per that AFS/closure record) | `ChatPage.FOLDER_MENU_PIN_ITEM` / `pin_folder_via_menu(folder_id)` — both pre-existing, reused verbatim, zero new page-object work. |
| Folder pinned-state attribute | `data-pinned="true"/"false"` on `chat-folder-item-{id}` | pre-existing, same commit as above | `ChatPage.is_folder_pinned(folder_id)` — pre-existing, reused verbatim. |
| Conversation pin/unpin context-menu item | `[data-testid="chat-conversation-menu-pin-menuitem"]` | pre-existing, on-`automation/testids` ✓ (ELITEA-2114) | `ChatPage.get_conversation_menu_item("pin")` / `click_conversation_menu_item("pin")` — pre-existing, reused verbatim (ELITEA-2149). |
| Conversation pinned-state attribute | `data-pinned="true"/"false"` on `chat-conversation-item-{id}` | pre-existing (ELITEA-2149) | `ChatPage.is_conversation_pinned(conversation_id)` — pre-existing, reused verbatim. |
| Folder row (for bounding-box) | `[data-testid="chat-folder-item-{id}"]` | pre-existing | `ChatPage.get_folder_item(folder_id)` — pre-existing, reused verbatim. |
| Conversation row (for bounding-box) | `[data-testid="chat-conversation-item-{id}"]` | pre-existing | `ChatPage.get_conversation_item(conversation_id)` — pre-existing, reused verbatim. |

**No new testid work required** — every handle this AFS needs already exists and is already wired
into `ChatPage`, entirely from prior sessions' work on this same surface family.

## Network Behavior
- Folder pin: `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → 200
  (source/live-confirmed, ELITEA-2121/2130's AFS).
- Conversation pin: `POST /pin/prompt_lib/{project_id}/conversation/{conversation_id}` → pin
  (source-confirmed, `src/api/social.js`'s `togglePinItem`, ELITEA-2149's AFS) — not independently
  network-asserted here either, same reasoning ELITEA-2149's AFS gives (optimistic-update pattern
  means a UI-state check that stays green also proves the request succeeded).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. The 4-tier ordering behaves exactly as `Conversations.jsx`'s source already documented and as
this case's own steps expect — closing a previously-flagged-but-undone verification gap, not
uncovering new product behavior.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: `automation/pages/chat_page.py` — zero new methods needed; reuse
  `pin_folder_via_menu()`, `is_folder_pinned()`, `get_folder_item()` (folder side, ELITEA-2121/2130)
  and `open_conversation_context_menu()`, `get_conversation_menu_item()`,
  `click_conversation_menu_item()`, `is_conversation_pinned()`, `get_conversation_item()`
  (conversation side, ELITEA-2114/2149).
- Test file: append a new test class to `automation/tests/ui/chat/test_pin_conversation.py`
  (extend-existing target) — a THIRD scenario alongside the existing `TestPinConversationViaPinOnTop`
  (ELITEA-2149) and `TestUnpinConversationViaContextMenu` (ELITEA-2150) classes; zero modification
  to either existing class.
- Priority marker: `@pytest.mark.p2` (medium, same mapping as ELITEA-2149/2150 in this same file).
