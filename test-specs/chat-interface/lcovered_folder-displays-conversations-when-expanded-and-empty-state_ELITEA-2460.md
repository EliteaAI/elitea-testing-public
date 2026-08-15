# Test Case: Chat – Folder Displays Conversations When Expanded and Empty State When No Conversations

## Metadata
- **TMS ID**: ELITEA-2460
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (per source case's `medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), chat-remaining
  wave-09, 2026-08-15
- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- At least one folder with conversations and one empty folder exist in the Chats section.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_folder_list_scrollability_and_expand_states.py`,
method `test_folder_displays_conversations_or_empty_state`
(TMS ELITEA-2148, AFS
`test-specs/chat-interface/l3_folder-displays-conversations-or-empty-state_ELITEA-2148.md`),
merged to `origin/automation/base` (commit `d2b5d1aa`, PR #1545, "test(chat-remaining-w07):
move/drag conversation between folders + list scrolling — 8 automated, 1 blocked
(defect-found)"). Confirmed on `origin/automation/base` this session via `git fetch origin`
(fresh) followed by `git merge-base --is-ancestor d2b5d1aa origin/automation/base` — exit 0,
confirmed ancestor.

**Behavioural-equivalence argument.** ELITEA-2460's 5 steps decompose into exactly the same
3 observables ELITEA-2148 already automates — the wording differs (5 granular steps vs. 3
compound ones) but the underlying assertions are identical, verified step by step:

| ELITEA-2460 step | Expected result | ELITEA-2148 covering-test step |
|---|---|---|
| 1. Navigate to Chats, click a folder with conversations to expand it | Target page/section loads | Setup — `chat.navigate_to_chat()` + `wait_for_any_folder_visible()`; Step 1 — `chat.expand_folder(folder_with_conversation_id)` |
| 2. Verify conversations are listed below the folder name when expanded | Condition holds | Step 1 — `is_folder_expanded()` True + `is_conversation_in_folder()` True |
| 3. Click the folder again to collapse it and verify conversations are hidden | Control responds; hidden | Step 2 — `chat.collapse_folder()`, `is_folder_expanded()` False, conversation item `not_to_be_visible()` |
| 4. Click an empty folder to expand it | Control responds | Step 3 — `chat.expand_folder(empty_folder_id)`, `is_folder_expanded()` True |
| 5. Verify the folder shows "No conversations added" text inside | Condition holds | Step 3 — `get_folder_empty_state_text() == "No conversations added"` |

No case element lacks a corresponding assertion in the covering spec — the mapping is 1:1 for
every step, and the covering spec is in fact stricter (it asserts the exact empty-state string
and a visibility-based, not count-based, collapse check — see its own AFS § Axis 2 for why that
matters).

**Live-reconfirmed this session, not assumed from the digest alone** (the "coverage judgments
stand on your own execution" rule applies to dedup verdicts too): re-ran the covering test
standalone against `http://localhost:5173` —
```
tests/ui/chat/test_folder_list_scrollability_and_expand_states.py::TestFolderDisplaysConversationsOrEmptyState::test_folder_displays_conversations_or_empty_state PASSED [100%]
1 passed in 17.09s
```
This is a stronger reconfirmation than a manual click-through: it's the actual automated proof
the TMS coverage claim relies on, executed live and green today, not source-read or historical.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to the Chats section and click a folder with conversations to expand it — Target
   page/section loads successfully.
2. Verify conversations are listed below the folder name when expanded — Condition holds as
   described.
3. Click the folder again to collapse it and verify conversations are hidden — Control responds;
   expected next state is shown.
4. Click an empty folder to expand it — Control responds; expected next state is shown.
5. Verify the folder shows "No conversations added" text inside — Condition holds as described.

## Expected Results
- Expanding a folder with conversations lists them below the folder name.
- Collapsing hides them again (via CSS visibility, not DOM removal — see the covering AFS).
- Expanding an empty folder shows "No conversations added" — proven live by
  `test_folder_displays_conversations_or_empty_state` and reconfirmed live this session.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — navigate + click folder-with-conversations to expand | page loads, folder expands | covering test Setup + Step 1 | `navigate_to_chat()` + `expand_folder()` + `is_folder_expanded()` True | already-covered |
| Step 2 — conversations listed below folder name when expanded | condition holds | covering test Step 1 | `is_conversation_in_folder()` True | already-covered |
| Step 3 — click folder again to collapse; conversations hidden | control responds, hidden | covering test Step 2 | `is_folder_expanded()` False + `not_to_be_visible()` | already-covered |
| Step 4 — click empty folder to expand | control responds | covering test Step 3 | `expand_folder(empty_folder_id)` + `is_folder_expanded()` True | already-covered |
| Step 5 — folder shows "No conversations added" text | condition holds | covering test Step 3 | `get_folder_empty_state_text() == "No conversations added"` | already-covered |
| Expected Final State (prose) | folder shows empty-state text | steps 1–5 | covered by the rows above | already-covered |
| Pass/Fail: "All steps complete without errors" | — | all steps | console-check (covering test's own Axis 2 side-channel step) | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l3_folder-displays-conversations-or-empty-state_ELITEA-2148.md`'s Coverage Map Axis 2 —
  visibility-based collapse assertion, exact empty-state string match, console/network
  side-channel) — none needed here.

## Cleanup
N/A — no new test written. Live-verification this session was a standalone re-run of the
already-merged covering test, which owns its own API-seeded setup/teardown
(`folder_with_conversation` + `empty_folder`, deleted via `conversation_api` in its own
`finally` block) — zero net pollution from this AFS's own verification pass.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-item-{id}` (`FOLDER_ITEM`),
`data-expanded="true"/"false"` state attribute, `chat-conversation-item-{id}` (scoped inside
`FOLDER_ITEM`), `chat-folder-empty-state` (`FOLDER_EMPTY_STATE`, scoped inside `FOLDER_ITEM`) —
all confirmed present and functioning on live localhost this session via the standalone
re-run above. No new handles needed for this traceability pass.

## TMS linkage
Link ELITEA-2460 to ELITEA-2148 in the TMS (both ways) so the audit trail resolves:
ELITEA-2460's `already-covered` disposition points at ELITEA-2148's automated test;
ELITEA-2148's case gains an "also satisfies ELITEA-2460" back-reference.
