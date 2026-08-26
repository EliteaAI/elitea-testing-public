# Test Case: Chat – Folder Rename – Check Icon Inactive When Name is Empty

## Metadata
- **TMS ID**: ELITEA-2124
- **Linked Story**: none
- **Priority**: l2 (per source case's `medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend; project "Private", `projectId=399`)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-15, wave-06

- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- At least one existing folder is present in the Chats section.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`,
method `test_folder_rename_checkmark_validation`
(TMS ELITEA-2458, AFS `test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`),
merged to `origin/automation/base` (fresh `git fetch origin` this session; commit
`da71d4b5`, PR #1311, confirmed an ancestor of `origin/automation/base` via
`git log origin/automation/base -- automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`).

**Behavioural-equivalence argument.** ELITEA-2124's 4 steps (open the rename
editor, clear the field to empty, verify the checkmark is disabled, click it
and verify no effect) map EXACTLY onto the covering test's Steps 1–3: Step 1
opens the rename editor via the dot-menu's Rename item and confirms the input
is pre-filled/focused; Step 2 clears the input entirely and asserts it reads
`""`; Step 3 asserts `chat-folder-name-confirm-button` carries
`data-disabled="true"` for the empty name, then clicks it and asserts THREE
independent no-op signals (editor stays open, input value still `""`, no
`PUT .../folder/prompt_lib/{project_id}/{folder_id}` fires — the accordion
row itself doesn't re-render either, since `FolderAccordion.jsx` only mounts
when not editing). No case element lacks a corresponding assertion.

**Live-reconfirmed this session** (fresh live drive, not assumed from the
digest alone): seeded a fresh folder ("W06GapCheck5", id 242), opened its
rename editor via the dot-menu → "Rename" (case says "Edit" — same
already-documented drift as the sibling ELITEA-2121/2130/2122/2127/2123
cases, not re-filed here), cleared the field, and independently drove the
adjacent 2-char/unchanged states in the same session (see the sibling
`lextend_` AFS files for ELITEA-2125/2131 for that evidence) — confirming the
SAME `isFolderSaveEnabled`/`data-disabled` mechanism the covering test
exercises for the empty-name case is live and correct today.

| ELITEA-2124 step | Covered by (`test_folder_rename_checkmark_validation`) |
|---|---|
| 1. Navigate to Chats, hover folder, 3-dot icon, click Edit → folder name editable | Step 1 — opens rename editor via dot-menu's "Rename" item (case says "Edit"; real item is "Rename" — documented drift, not a defect) |
| 2. Clear the entire content of the input field → field is empty | Step 2 — `chat.folder_name_input.clear()` + `input_value() == ""` assertion |
| 3. Verify the checkmark icon is disabled/inactive → checkmark inactive | Step 3 — `assert not chat.is_folder_name_confirm_enabled()` (`data-disabled="true"`) |
| 4. Attempt to click the checkmark → click has no effect, save not triggered | Step 3 — click + assert editor stays open, input still `""`, folder row doesn't re-render, zero new PUT requests |

**Scope note (no gap, so no `extend-existing`).** All 4 of ELITEA-2124's
steps map onto the covering test's Steps 1–3. No case element lacks a
corresponding assertion in the covering spec.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to Chats, hover over a folder, click three-dot icon, click Edit — Folder name is editable.
2. Clear the entire content of the input field — Field is empty.
3. Verify the checkmark icon is in a disabled/inactive state — Checkmark inactive.
4. Attempt to click the checkmark icon — Click has no effect; save not triggered.

## Expected Results
- Empty name disables the checkmark; save cannot be triggered — proven live
  by `test_folder_rename_checkmark_validation` (see Dedup proof above) and
  reconfirmed live this session.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open rename editor via dot-menu | folder name editable | covering test Step 1 | `open_folder_rename_editor()` call + pre-fill/focus assertions | already-covered |
| Step 2 — clear the field entirely | field is empty | covering test Step 2 | `input_value() == ""` | already-covered |
| Step 3 — checkmark disabled/inactive | checkmark inactive | covering test Step 3 | `is_folder_name_confirm_enabled()` is `False` (`data-disabled="true"`) | already-covered |
| Step 4 — click has no effect, save not triggered | no-op | covering test Step 3 | editor-open + input-unchanged + folder-row-absent + no-PUT assertions | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`'s Coverage Map
  Axis 2) — none needed here.

## Cleanup
N/A — no new test written. Live-verification exploration used a folder
(id 242, "W06GapCheck5") seeded and driven jointly with the ELITEA-2125/2131
gap checks (see those AFS files) in this same session; the UI Delete flow's
dot-menu item is currently dead (issue #1309, unresolved) so the folder was
NOT cleaned up — same class of leaked test artifact already present ~40 times
over in the shared DEV project per the digest, tracked there, not a new
regression introduced by this session.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-name-input`,
`chat-folder-name-confirm-button` (with its `data-disabled` state attribute),
`chat-folder-name-cancel-button`, `chat-folder-menu-rename-menuitem`,
`conversation-menu-menu-button` (scoped), `chat-folder-item-{id}` — all
confirmed present and functioning on live localhost this session. No new
handles needed for this traceability pass.

## TMS linkage
Link ELITEA-2124 to ELITEA-2458 in the TMS (both ways) so the audit trail
resolves: ELITEA-2124's `already-covered` disposition points at ELITEA-2458's
automated test; ELITEA-2458's case gains an "also satisfies ELITEA-2124"
back-reference.
