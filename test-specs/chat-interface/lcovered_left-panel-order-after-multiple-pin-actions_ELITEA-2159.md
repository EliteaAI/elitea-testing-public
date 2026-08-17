# Test Case: Chat – Left Panel Order Verified After Multiple Pin Actions

## Metadata
- **TMS ID**: ELITEA-2159
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), batch `chat-remaining-w09`, 2026-08-15
- **Status**: already-covered
- **surface_key**: `chat-conversation-context-menu` (same pin/unpin surface as ELITEA-2149/2150/2151;
  also touches the folder-pin surface, ELITEA-2121/2130)

## Preconditions
- User is logged in to the Elitea platform.
- At least one folder and one ungrouped conversation exist.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_pin_conversation.py`, class
`TestChatPanelOrderingPinnedFoldersAndConversations`, method
`test_pinned_folder_and_conversation_render_above_unpinned_panel_order`
(TMS ELITEA-2151, AFS
`test-specs/chat-interface/lextend_pinned-conversation-panel-ordering_ELITEA-2151.md`),
merged to `origin/automation/base`. Confirmed present on `origin/automation/base`
this session via a fresh `git fetch origin` + `git show
origin/automation/base:automation/tests/ui/chat/test_pin_conversation.py` (class +
method both found).

**Behavioural-equivalence argument.** ELITEA-2159 asks for exactly the same
4-tier panel-order verification ELITEA-2151's covering test already implements
end to end: seed one pinned folder, one pinned conversation (not inside a
folder), one unpinned folder, one unpinned conversation → pin the folder and
the conversation via their respective "Pin on top" dot-menu items → assert
the full left-panel order top to bottom (pinned folders → pinned
conversations → unpinned folders → unpinned conversations) via bounding-box
Y-position → assert no pinned item renders below any unpinned item, directly
including the two "same-type" pairs (`folder_pinned` above `folder_unpinned`,
`conv_target` above `conv_unpinned`) and the pinned-folder-before-pinned-
conversation pair (`folder_pinned` above `conv_target`). Every element of
ELITEA-2159's 5 steps has a corresponding direct assertion in the covering
test — none of ELITEA-2159's asks exceed what ELITEA-2151 already proves.

**Live-reconfirmed this session** (not assumed from the digest alone, per the
"coverage judgments stand on your own execution" rule): re-ran the covering
test live against `http://localhost:5173` —
```
tests/ui/chat/test_pin_conversation.py::TestChatPanelOrderingPinnedFoldersAndConversations::test_pinned_folder_and_conversation_render_above_unpinned_panel_order PASSED [100%]
============================== 1 passed in 19.44s ==============================
```
Confirms the full 4-tier ordering (and therefore every one of ELITEA-2159's 5
steps) still holds on today's live product, not just at ELITEA-2151's original
implementation time.

| ELITEA-2159 step | Covered by (`test_pinned_folder_and_conversation_render_above_unpinned_panel_order`) |
|---|---|
| 1. Pin a folder using 'Pin on top' → Folder in pinned folders section | Setup + Step 1 — seeds `folder_pinned`, pins it via `pin_folder_via_menu()`, asserts `data-pinned="true"` via `is_folder_pinned()` |
| 2. Pin a conversation (not inside a folder) using 'Pin on top' → Conversation in pinned conversations section | Setup + Step 1 — seeds `conv_target` (freshly API-created, not in a folder), pins it via the 3-dot menu's "Pin on top" item, asserts `data-pinned="true"` via `is_conversation_pinned()` |
| 3. Verify panel order: pinned folders, pinned conversations, unpinned folders, unpinned conversations by date group → Panel order correct | Step 2 — 3 adjacent-tier bounding-box Y comparisons spanning all 4 tiers: `folder_pinned` above `conv_target`, `conv_target` above `folder_unpinned`, `folder_unpinned` above `conv_unpinned` |
| 4. Verify no unpinned item appears above a pinned item of the same type → Ordering maintained | Step 3 — direct assertions `folder_pinned` above `folder_unpinned` (folder same-type pair) and (transitively via Step 2's chain, plus Step 3's direct `conv_target` above `conv_unpinned`) the conversation same-type pair |
| 5. Verify no pinned conversation appears above pinned folders → Folders before conversations in pinned area | Step 2's first adjacent comparison — `folder_pinned_box["y"] + height <= conv_target_box["y"]` (pinned folder strictly above pinned conversation) |

**Scope note (no gap, so no `extend-existing`).** All 5 of ELITEA-2159's
steps map onto assertions the covering test already makes, using the same
4-tier seeded fixture (one pinned folder, one pinned conversation outside any
folder, one unpinned folder, one unpinned conversation). No case element
lacks a corresponding assertion in the covering spec.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Pin at least one folder using 'Pin on top' — Folder in pinned folders section.
2. Pin at least one conversation (not inside a folder) using 'Pin on top' — Conversation in pinned conversations section.
3. Verify panel order: pinned folders (pin icon), pinned conversations (pin icon), unpinned folders, unpinned conversations by Today/This Week/Older — Panel order correct.
4. Verify no unpinned item appears above a pinned item of the same type — Ordering maintained.
5. Verify no pinned conversation appears above pinned folders — Folders before conversations in pinned area.

## Expected Results
- Full left-panel order, top to bottom: pinned folders → pinned conversations
  → unpinned folders → unpinned conversations (by date group) — proven live
  by `test_pinned_folder_and_conversation_render_above_unpinned_panel_order`
  (see Dedup proof above) and reconfirmed live this session.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥1 folder and ≥1 ungrouped conversation exist | — | covering test Setup | seeds `folder_pinned`, `folder_unpinned`, `conv_target` (not in a folder), `conv_unpinned` via API | already-covered |
| Step 1 — pin a folder | folder in pinned folders section | covering test Step 1 | `pin_folder_via_menu()` + `is_folder_pinned()` == True | already-covered |
| Step 2 — pin a conversation not in a folder | conversation in pinned conversations section | covering test Step 1 | "Pin on top" menu item + `is_conversation_pinned()` == True | already-covered |
| Step 3 — full 4-tier panel order | panel order correct | covering test Step 2 | 3 adjacent-tier bounding-box Y comparisons | already-covered |
| Step 4 — no unpinned item above pinned item of same type | ordering maintained | covering test Step 3 | direct `folder_pinned` vs `folder_unpinned` assertion; conversation same-type pair covered by Step 2's chain + Step 3's `conv_target` vs `conv_unpinned` assertion | already-covered |
| Step 5 — no pinned conversation above pinned folders | folders before conversations in pinned area | covering test Step 2 | `folder_pinned` vs `conv_target` adjacent comparison | already-covered |
| Expected Final State (prose): "Panel order maintained correctly after multiple pins" | — | Steps 2–3 | covered by the rows above | already-covered |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check side-channel (no unexpected console errors, `secrets/secrets/default` 403 excluded) | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `lextend_pinned-conversation-panel-ordering_ELITEA-2151.md`'s Coverage Map
  Axis 2) — none needed here.

## Cleanup
N/A — no new test written. Live-verification this session re-ran the existing
covering test as-is (its own setup/teardown creates and deletes its own
fixture data); zero net pollution added by this session.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-menu-pin-menuitem`,
`data-pinned` on `chat-folder-item-{id}` and `chat-conversation-item-{id}`,
`chat-conversation-menu-pin-menuitem`, `chat-folder-item-{id}`,
`chat-conversation-item-{id}` — all confirmed present and functioning on live
localhost this session (via the live test re-run). No new handles needed for
this traceability pass.

## Known Defects Found During Exploration
None. The 4-tier ordering behaves exactly as documented and as this case's
own steps expect.

## Blocked Steps
None.

## TMS linkage
Link ELITEA-2159 to ELITEA-2151 in the TMS (both ways) so the audit trail
resolves: ELITEA-2159's `already-covered` disposition points at ELITEA-2151's
automated test; ELITEA-2151's case gains an "also satisfies ELITEA-2159"
back-reference.
