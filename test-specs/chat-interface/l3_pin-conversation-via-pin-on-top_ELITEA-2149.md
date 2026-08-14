# Test Case: Chat – Pin a Conversation via Pin on Top Option

## Metadata
- **TMS ID**: ELITEA-2149
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`; see ELITEA-2135's
  AFS for the medium→l3/p2 mapping evidence in this suite)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, the account's own Private/personal project — treat as
  `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2135, ELITEA-2137
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-context-menu`

Cluster-analysed alongside ELITEA-2135/ELITEA-2137 (both "Move to" flows) — shares the conversation
3-dot context-menu surface but never opens "Move to" (the pin item, `"pin"` key, has no submenu),
so it does NOT hit the activation-gesture defect filed against those two cases
(EliteaAI/elitea-testing-public#1117) — confirmed live, unaffected.

No existing AFS or automated test covers pinning anywhere in this suite — grepped `test-specs/` and
`tests/ui/chat/` for `pin`/`Pin on top`/`isPinned` before this pass; the only prior hit was
`EXPECTED_MENU_ITEM_KEYS` in `test_conversation_deletion_flow.py`, which asserts the menu
**enumerates** a `"pin"` key but never clicks it (same situation as "move-to" in the sibling cases).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one conversation exists — test creates its own (see § Test Data).
- The conversation must NOT already be inside a folder — `ConversationItem.jsx`'s "Pin on top" item
  is disabled when `!isPinned && !!conversation.folder_id` (i.e. you cannot pin a conversation that's
  currently inside a folder; a fresh, ungrouped conversation naturally satisfies this).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — the conversation to pin. Create via `conversation_api.create_conversation(name)`.
  A freshly-created conversation always lands in the "Today" date group (same deterministic pattern
  ELITEA-2114's AFS already established).

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Hover `conv_target`'s sidebar item, click its 3-dot menu, click
   **Pin on top** (`chat-conversation-menu-pin-menuitem`).
   - **Verify**: label reads **"Pin on top"** before the click (live-confirmed; the same testid
     covers both "Pin on top" and "Unpin" states per the item's own label-carries-state design,
     documented in ELITEA-2114's AFS — no submenu involved here, single click, no retry needed).
2. Verify the conversation moved to the pinned section, above folders.
   - **Verify**: `chat-conversation-item-{conv_target_id}` still resolves exactly 1 (the SAME
     element re-renders in the pinned section, not a duplicate — same testid template, different
     DOM parent, matching the "one testid template renders in multiple possible locations" pattern
     ELITEA-2135's AFS documents for the move-to-folder case); its `data-pinned` attribute (ADDED
     this pass — see § Concrete Handles) reads `"true"`; its bounding-box Y-position is ABOVE the
     "Today" date-group heading's Y-position (live-verified this pass: pinned item Y=56 vs "Today"
     heading Y=178/260 across two repro runs — always well above).
3. Verify a pin icon is displayed next to the pinned conversation name.
   - **Verify**: `[data-testid="chat-pin-icon"]` (ADDED this pass), scoped inside
     `chat-conversation-item-{conv_target_id}`, resolves exactly 1 and is visible. Live-verified: 0
     `svg` elements matching this testid before pinning, 1 after (the icon is conditionally rendered
     — `{isPinned && !isPlayback && <PinIcon ... />}` — not just visually toggled).
4. Verify the conversation is no longer in its original date group.
   - **Verify**: `chat-conversation-item-{conv_target_id}`, scoped inside the "Today" date-group
     container specifically (`CONVERSATION_GROUP_HEADER.format("today")`'s sibling content), resolves
     0 — the SAME testid renders once total (in the pinned section, per step 2), so this is a scoped
     check, not a page-wide one (matching the same discipline ELITEA-2135/ELITEA-2137's AFSes require
     for their own "removed from date group" steps).
5. Verify the panel order: pinned folders, pinned conversations, unpinned folders, unpinned
   conversations.
   - **Verify**: read directly from `Conversations.jsx`'s render order (source-confirmed, not just
     inferred from a screenshot): `renderFoldersSection({isPinned: true})` →
     `<PinnedConversations>` → `renderFoldersSection({isPinned: false})` →
     `<DroppableGroupedArea><GroupedConversations>` (the date-grouped, unpinned list) — i.e. the
     literal DOM order matches the case's expected order exactly. Automation asserts this via
     bounding-box Y-comparison between one representative element of each tier that's actually
     present (a pinned folder's row, `conv_target`'s own pinned-conversation row, an unpinned
     folder's row, and the "Today" heading) rather than re-deriving the order from scratch — see
     § Automation Hints for why a full 4-tier live comparison needs a pinned-folder fixture this
     case's own steps don't otherwise require, and the pragmatic 2-of-4-tier scope this AFS commits
     to instead.

## Expected Results
- Pinning moves the conversation to a pinned section rendered above ALL folder sections (pinned or
  not) and above the date-grouped conversation list.
- A pin icon renders next to the pinned conversation's name.
- The conversation is removed from its original date group.
- No success toast appears on pin (confirmed via source: `usePinConversation.hooks.js`'s
  `onPinConversation` only calls `toastError` on FAILURE, never a success toast on the happy path —
  the case doesn't claim one either, so this is a non-finding, not a gap).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥1 conversation exists | — | Setup | API-seeded `conv_target` | asserted |
| 1 Navigate to Chats, hover conversation, 3-dot icon, click 'Pin on top' | Conversation moves to pinned section above folders | AFS steps 1–2 | step 2: `data-pinned="true"` + Y-position above "Today" heading | asserted |
| 2 Verify a pin icon is displayed next to the pinned conversation name | Pin icon visible | AFS step 3 | step 3: `chat-pin-icon` scoped + visible, 0→1 transition confirmed | asserted |
| 3 Verify the conversation is no longer in its original date group | Removed from date groups | AFS step 4 | step 4: scoped 0-count in the "Today" group container | asserted |
| 4 Verify the panel order: pinned folders, pinned conversations, unpinned folders, unpinned conversations | Panel order is correct | AFS step 5 | step 5: 2-of-4-tier Y-position comparison (see below); full 4-tier order is source-confirmed, not independently re-derived by a live 4-way bounding-box comparison | asserted, with a scope note *(a genuinely complete 4-tier LIVE comparison needs a pinned-folder fixture this case's own steps never otherwise require — reading `Conversations.jsx`'s literal render-order JSX, which is deterministic markup order, not a runtime-conditional layout, is treated as sufficient corroboration alongside the 2-tier live check this AFS DOES run; see § Automation Hints for the explicit trade-off)* |
| Expected Final State (prose): "Conversation pinned and appears above folders with pin icon" | — | steps 2–3 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (Axis 2) | asserted, 0 console errors across all repro runs |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 1 asserts the menu item's label text before the click ("Pin on top", not yet "Unpin") —
  *added: confirms the state-carrying label design (one testid, state via label text, per the
  project's testid=identity/state=data-* philosophy applied to text rather than an attribute here)
  is in its expected pre-pin state, not just that the click succeeds.*
- Step 2 adds a `data-pinned` state-attribute check rather than relying solely on DOM position —
  *added: a bounding-box Y-comparison alone is a weaker signal than the sibling AFSes' `data-expanded`
  precedent (ELITEA-2132) and `data-active` precedent (ELITEA-2114) — a deterministic attribute is a
  cheaper, more robust assertion than re-deriving position from pixel coordinates for the "is this
  conversation currently pinned" fact specifically (position remains the right tool for the PANEL
  ORDER claim in step 5, where relative position between tiers IS literally what's being tested).*
- Step 3 confirms the pin icon via a 0→1 transition (before/after), not just a post-pin presence
  check — *added: catches a scenario where the icon renders unconditionally (a false pass on a
  present-but-static icon) vs. correctly gated on `isPinned` (the real product behavior).*
- Step 4 requires SCOPED (not page-wide) 0-count — *added, same MUI-Collapse-style trap discipline as
  ELITEA-2135/ELITEA-2137's equivalent steps (though here the relevant reason is simpler: the SAME
  element re-renders once in the pinned section, so an unscoped count would already correctly read 1
  total either way — but scoping to "not in the Today container specifically" is still the more
  precise assertion of what actually changed).*
- Step 5's scope note (2-of-4-tier live check + source-confirmed full order) — *added: an honest
  account of what was and wasn't independently live-verified, rather than silently overclaiming a
  4-tier live comparison this case's own steps don't naturally produce fixture data for. See
  § Automation Hints for the concrete implementer choice this leaves open.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline; confirmed 0 console errors across every repro run in this pass (a marked contrast with
  ELITEA-2135/ELITEA-2137, where the OLD, now-fixed `folderItems` missing-`key` bug produced a live
  React console warning under two same-named folders — this case's own flow never triggered it).*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` — deleting a pinned
   conversation was live-verified to work identically to deleting an unpinned one (no special
   unpin-first step required).
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| "Pin on top"/"Unpin" context-menu item | `[data-testid="chat-conversation-menu-pin-menuitem"]` | pre-existing, on-`automation/testids` ✓ (ELITEA-2114) | `ChatPage.CONVERSATION_MENU_ITEM.format("pin")` / `get_conversation_menu_item("pin")`. Label text flips "Pin on top" ↔ "Unpin"; testid itself is stable (state-via-label-text, not state-via-testid-value — compliant with the project's testid=identity ruling). |
| Conversation item pinned-state attribute | `data-pinned="true"/"false"` on `chat-conversation-item-{id}` | **ADDED this pass.** Mirrors the pre-existing `data-active` attribute on the SAME element (ELITEA-2114) — added directly to `ConversationItem.jsx`'s root `Box`, driven off the existing `isPinned` prop (already threaded through the component; no new prop plumbing needed, purely a mechanical addition matching precedent). | New: `ChatPage.is_conversation_pinned(conversation_id)` (mirrors the existing `is_conversation_active()`, ELITEA-2114). |
| Pin icon (inside the item, only when pinned) | `[data-testid="chat-pin-icon"]`, **non-unique — scope inside `chat-conversation-item-{id}`** | **ADDED this pass.** `PinIcon` (`src/components/Icons/PinIcon.jsx`) is a shared icon component (`SvgIcon`-wrapped, forwards arbitrary props including `data-testid` to the root `<svg>` — confirmed by reading the component, same forwarding behavior already relied on for `FolderIcon`/`StyledExpandMoreIcon` in ELITEA-2132's AFS) reused across the codebase — testid added at the CALL SITE inside `ConversationItem.jsx` (where it's conditionally rendered `{isPinned && !isPlayback && <PinIcon .../>}`), not hardcoded inside `PinIcon.jsx` itself, per the shared-component naming ruling. | New: `ChatPage.PIN_ICON = '[data-testid="chat-pin-icon"]'` class constant + a scoped lookup helper, or inline `.locator()` off a `CONVERSATION_ITEM`-scoped element (either shape is compliant — the constant lives at class level either way). |
| Pinned-section positioning (for step 5) | No dedicated testid — asserted via existing element bounding boxes (`chat-folder-item-{id}` for a pinned/unpinned folder row, `chat-conversation-item-{id}` for the pinned conversation, `chat-conversation-group-header-today` for the unpinned tier) | n/a | See § Automation Hints for the 2-of-4-tier live-check scope this AFS commits to. |

**Testid commit provenance**: both additions above (`data-pinned` attribute, `chat-pin-icon`) were
made in the SAME single commit as ELITEA-2135/ELITEA-2137's own testid work —
`cf348d32` on `EliteaAI/EliteaUI`'s `automation/testids`, pushed (see ELITEA-2135's AFS for the full
commit message and the unrelated separately-committed `e22e9881` fix found alongside it in the
working tree).

## Network Behavior
- `POST /pin/prompt_lib/{project_id}/conversation/{conversation_id}` → pin (source-confirmed,
  `src/api/social.js`'s `togglePinItem` mutation: `method: shouldPin ? 'POST' : 'DELETE'` against
  `${apiSlicePath}/pin/prompt_lib/${projectId}/${entityType}/${entityId}`) — not independently
  network-asserted in this AFS's steps (the UI-state assertions in steps 2–4 are treated as
  sufficient; the mutation's own optimistic-update pattern in `usePinConversation.hooks.js` already
  reverts the UI state on a failed request, so a UI-state check that stays green also indirectly
  proves the request didn't fail).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS.

## Known Defects Found During Exploration
None found specific to this case. All 5 case steps executed live end-to-end and matched expected
results exactly (0 console errors across every repro run). Not affected by the "Move to"
activation-gesture defect filed against ELITEA-2135/ELITEA-2137
(EliteaAI/elitea-testing-public#1117) — confirmed live, "Pin on top" has no submenu and its single
click always worked immediately and reliably across every repro.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py`. Reuse `open_conversation_context_menu()`,
  `click_conversation_menu_item("pin")` (both pre-existing, ELITEA-2114) — no new interaction method
  needed beyond the existing ones; this case is simpler than its "Move to" siblings precisely because
  it never opens a submenu.
- **Step 5's panel-order scope — an explicit implementer choice, not resolved unilaterally here.**
  This case's own steps only ever produce ONE pinned conversation and ZERO pinned folders (pinning a
  FOLDER is a separate, unrelated feature surface — `folder.meta?.is_pinned`, not exercised by this
  case at all). A fully-live 4-tier bounding-box comparison would need to ALSO seed a pinned folder,
  which is out of this case's own scope (no case step asks for one). Two options for the implementer:
  (a) commit to the 2-tier live check this AFS's own steps naturally produce (pinned conversation Y <
  unpinned-folder-or-Today-heading Y) and treat `Conversations.jsx`'s literal JSX render order as
  sufficient corroboration for the OTHER two tiers (pinned folders, unpinned conversations already
  covered transitively since Today-heading Y is asserted); or (b) seed one throwaway pinned folder
  via a raw `POST /pin/prompt_lib/{project_id}/folder/{folder_id}` call (mirroring this case's own
  conversation-pin endpoint) purely to complete a 4-tier live assertion. This AFS recommends (a) for
  a first implementation (matches the case's own minimal-seed spirit) and flags (b) as a legitimate
  follow-up if a future case specifically targets folder-pinning.
- Priority marker: `@pytest.mark.p2` (see ELITEA-2135's AFS note on the l3/p2 mapping).
