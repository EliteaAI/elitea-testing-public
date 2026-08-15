# Test Case: Chat – Pin a Conversation and Verify It Appears Above Folders and Date Groups

## Metadata
- **TMS ID**: ELITEA-2461
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `priority: high`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w09`, 2026-08-15
- **Status**: already-covered
- **surface_key**: `chat-conversation-context-menu` (same pin/unpin surface as ELITEA-2149/2150/2151/
  2159; also touches the folder-pin surface, ELITEA-2121/2130)

## Preconditions
- User is logged in to the Elitea platform.

## Dedup proof — Rule-6 behavioural equivalence

**Covering specs (two, combined — each covers a disjoint subset of this case's 5 steps):**

1. `automation/tests/ui/chat/test_pin_conversation.py`, class `TestPinConversationViaPinOnTop`,
   method `test_pin_conversation_via_pin_on_top` (TMS ELITEA-2149, AFS
   `test-specs/chat-interface/l3_pin-conversation-via-pin-on-top_ELITEA-2149.md`) — covers this
   case's Steps 1–4.
2. `automation/tests/ui/chat/test_pin_conversation.py`, class
   `TestChatPanelOrderingPinnedFoldersAndConversations`, method
   `test_pinned_folder_and_conversation_render_above_unpinned_panel_order` (TMS ELITEA-2151, AFS
   `test-specs/chat-interface/lextend_pinned-conversation-panel-ordering_ELITEA-2151.md`) — covers
   this case's Step 5.

Both are merged to `origin/automation/base`. Confirmed present this session via a fresh
`git fetch origin` + `git show origin/automation/base:automation/tests/ui/chat/test_pin_conversation.py`
(both classes + methods found, line 85 and line 437 respectively).

**Behavioural-equivalence argument.** ELITEA-2461's 5 steps decompose cleanly into two already-proven
halves:

- **Steps 1–4** (navigate/hover a conversation → click 3-dot → Pin on top → conversation moves out
  of its date group into the pinned-conversations section → pin icon renders next to the name) are
  the EXACT flow `test_pin_conversation_via_pin_on_top` already implements end to end: it hovers a
  freshly-seeded conversation (naturally landing in "Today", satisfying "any conversation in Today,
  This Week, or Older"), opens the 3-dot menu, clicks the `chat-conversation-menu-pin-menuitem`
  ("Pin on top") item (Step 1 of that test = ELITEA-2461 steps 1–2), asserts `data-pinned="true"` +
  a Y-position above the "Today" heading (that test's Step 2 = ELITEA-2461 step 3's "appears in the
  pinned conversations section" half), asserts a pin icon 0→1 transition next to the conversation
  (that test's Step 3 = ELITEA-2461 step 4 verbatim), and explicitly asserts the conversation is no
  longer rendered under the "Today" date group while a sibling conversation still is (that test's
  Step 4 = ELITEA-2461 step 3's "moves out of its original date group" half, directly).
- **Step 5** (full left-panel order: pinned folders → pinned conversations → unpinned folders →
  unpinned conversations grouped by date) is the EXACT 4-tier check
  `test_pinned_folder_and_conversation_render_above_unpinned_panel_order` already implements: it
  seeds one pinned folder, one pinned conversation, one unpinned folder, and one unpinned
  conversation, then asserts 3 adjacent-tier bounding-box Y comparisons spanning all 4 tiers
  (`folder_pinned` above `conv_target`, `conv_target` above `folder_unpinned`, `folder_unpinned`
  above `conv_unpinned`) plus 2 additional non-adjacent "skip" pairs, proving the identical order
  ELITEA-2461's step 5 names. This is the same panel-order proof already accepted for
  `lcovered_left-panel-order-after-multiple-pin-actions_ELITEA-2159.md` (ELITEA-2159), whose step 3
  wording ("pinned folders, pinned conversations, unpinned folders, unpinned conversations by
  Today/This Week/Older") is near-verbatim to ELITEA-2461's step 5.

Every element of ELITEA-2461's 5 steps has a corresponding direct assertion across these two
covering tests — none of ELITEA-2461's asks exceed what the pair already proves.

**Live-reconfirmed this session** (not assumed from the digest alone, per the "coverage judgments
stand on your own execution" rule): re-ran BOTH covering tests live against `http://localhost:5173`:
```
tests/ui/chat/test_pin_conversation.py::TestPinConversationViaPinOnTop::test_pin_conversation_via_pin_on_top PASSED [ 50%]
tests/ui/chat/test_pin_conversation.py::TestChatPanelOrderingPinnedFoldersAndConversations::test_pinned_folder_and_conversation_render_above_unpinned_panel_order PASSED [100%]
============================== 2 passed in 45.98s ==============================
```
Confirms every one of ELITEA-2461's 5 steps still holds on today's live product, not just at the
covering tests' original implementation time.

| ELITEA-2461 step | Covered by | Asserted where |
|---|---|---|
| 1. Navigate to Chats, hover a conversation in Today/This Week/Older | `test_pin_conversation_via_pin_on_top` Setup + Step 1 | seeds `conv_target` (freshly API-created, lands in "Today"), navigates, hovers, opens the 3-dot menu |
| 2. Click the three-dot icon and click Pin on top | `test_pin_conversation_via_pin_on_top` Step 1 | asserts the menu item label reads "Pin on top" before click, then clicks `chat-conversation-menu-pin-menuitem` |
| 3. Verify the conversation moves out of its original date group and appears in the pinned conversations section | `test_pin_conversation_via_pin_on_top` Steps 2 + 4 | Step 2: `data-pinned="true"` + Y-position above the "Today" heading; Step 4: `is_conversation_in_group(conv_target_id, "today")` is False while a sibling conversation stays True |
| 4. Verify a pin icon is displayed next to the pinned conversation name | `test_pin_conversation_via_pin_on_top` Step 3 | `chat-pin-icon` scoped inside the conversation item, 0→1 transition (before/after) |
| 5. Verify the overall left panel order: pinned folders at top, then pinned conversations, then unpinned folders, then unpinned conversations grouped by Today/This Week/Older | `test_pinned_folder_and_conversation_render_above_unpinned_panel_order` Steps 2–3 | 3 adjacent-tier + 2 non-adjacent bounding-box Y comparisons spanning all 4 tiers (`folder_pinned` → `conv_target` → `folder_unpinned` → `conv_unpinned`) |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

**Scope note (no gap, so no `extend-existing`).** All 5 of ELITEA-2461's steps map onto assertions
the two covering tests already make. The only nuance: `test_pinned_folder_and_conversation_render_above_unpinned_panel_order`'s
"unpinned conversations" tier is represented by a single freshly-created conversation (naturally in
"Today"), not one row per date group (Today/This Week/Older) — the same scope already accepted for
ELITEA-2159's dedup (its step 3 carries the identical "by Today/This Week/Older" wording). The
underlying render-order mechanism (`Conversations.jsx`'s `renderFoldersSection({isPinned})` →
`<PinnedConversations>` → `renderFoldersSection({isPinned: false})` →
`<DroppableGroupedArea><GroupedConversations>`) source-confirmed in ELITEA-2151's AFS is
date-group-agnostic — the unpinned-conversations TIER (as a whole) is what's being ordered, not
each date sub-group independently, and the case's own steps never ask to verify the This
Week/Older sub-groups individually either.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to the Chats section and hover over any conversation in Today, This Week, or Older —
   Target page/section loads successfully.
2. Click the three-dot icon and click Pin on top — Control responds; expected next state is shown.
3. Verify the conversation moves out of its original date group and appears in the pinned
   conversations section — Condition holds as described.
4. Verify a pin icon is displayed next to the pinned conversation name — Condition holds as
   described.
5. Verify the overall left panel order is: pinned folders at top, then pinned conversations, then
   unpinned folders, then unpinned conversations grouped by Today/This Week/Older — Condition holds
   as described.

## Expected Results
- Pinning moves the conversation to a pinned section, removes it from its date group, and renders a
  pin icon next to its name — proven live by `test_pin_conversation_via_pin_on_top`.
- Full left-panel order, top to bottom: pinned folders → pinned conversations → unpinned folders →
  unpinned conversations (by date group) — proven live by
  `test_pinned_folder_and_conversation_render_above_unpinned_panel_order`.
- Both reconfirmed live this session (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state`/`VITE_DEV_TOKEN` (localhost) | framework fixture, both covering tests | already-covered |
| Step 1 — navigate to Chats, hover a conversation in Today/This Week/Older | page/section loads | `test_pin_conversation_via_pin_on_top` Setup | `chat.navigate_to_chat()` + `chat.wait_for_page_load()`, conversation item visible | already-covered |
| Step 2 — click 3-dot icon, click Pin on top | control responds | `test_pin_conversation_via_pin_on_top` Step 1 | menu item label check + click on `chat-conversation-menu-pin-menuitem` | already-covered |
| Step 3 — conversation moves out of original date group, appears in pinned section | condition holds | `test_pin_conversation_via_pin_on_top` Steps 2 + 4 | `data-pinned="true"` + Y-position above "Today" heading; scoped absence from the "Today" group | already-covered |
| Step 4 — pin icon displayed next to pinned conversation name | condition holds | `test_pin_conversation_via_pin_on_top` Step 3 | `chat-pin-icon` 0→1 transition, scoped inside the conversation item | already-covered |
| Step 5 — full panel order: pinned folders, pinned conversations, unpinned folders, unpinned conversations by date group | condition holds | `test_pinned_folder_and_conversation_render_above_unpinned_panel_order` Steps 2–3 | 3 adjacent-tier + 2 non-adjacent bounding-box Y comparisons across all 4 tiers | already-covered |
| Expected Final State (prose): "pinned folders, then pinned conversations, then unpinned folders, then unpinned conversations by date group" | — | Step 5's covering test | covered by the row above | already-covered |
| Pass/Fail: "All steps complete without errors" | — | both covering tests | console-check side-channel (no unexpected console errors, `secrets/secrets/default` 403 excluded) | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
None beyond what the two covering specs already document (see their own Coverage Map Axis 2
sections, ELITEA-2149's and ELITEA-2151's AFS files) — none needed here.

## Cleanup
N/A — no new test written. Live-verification this session re-ran the two existing covering tests
as-is (their own setup/teardown creates and deletes their own fixture data); zero net pollution
added by this session.

## Concrete Handles (discovered during exploration)
Reuses both covering specs' handles verbatim — `chat-conversation-menu-pin-menuitem`,
`data-pinned` on `chat-conversation-item-{id}` and `chat-folder-item-{id}`, `chat-pin-icon`,
`chat-folder-menu-pin-menuitem`, `chat-conversation-group-header-today` — all confirmed present and
functioning on live localhost this session (via the live test re-runs). No new handles needed for
this traceability pass.

## Known Defects Found During Exploration
None. Both covering tests pass live and the combined behavior matches this case's 5 steps exactly.

## Blocked Steps
None.

## TMS linkage
Link ELITEA-2461 to ELITEA-2149 AND ELITEA-2151 in the TMS (both ways) so the audit trail resolves:
ELITEA-2461's `already-covered` disposition points at both automated tests; ELITEA-2149's and
ELITEA-2151's cases each gain an "also satisfies ELITEA-2461" back-reference. (Same pattern already
established between ELITEA-2159 and ELITEA-2151.)
