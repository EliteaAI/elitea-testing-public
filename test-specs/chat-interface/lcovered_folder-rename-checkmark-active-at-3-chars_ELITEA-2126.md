# Test Case: Chat – Folder Rename – Check Icon Becomes Active at 3 Characters

## Metadata
- **TMS ID**: ELITEA-2126
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
`da71d4b5`, PR #1311, confirmed an ancestor of `origin/automation/base`).

**Behavioural-equivalence argument.** ELITEA-2126's 4 steps (open the rename
editor, type 2 chars → inactive, type a 3rd char → active, click → folder
renamed) map onto the covering test's Steps 4, 7, 8, 9 — the SAME flow, just
without the covering test's OWN intermediate detours (tooltip text at step 5,
restore-to-unchanged at step 6). Step 4 types "AB" (2 chars); Step 7 types the
3rd char to reach "ABC"; Step 8 asserts the checkmark is now active
(`data-disabled="false"`); Step 9 clicks the active checkmark and asserts the
rename PUT resolves `200`, the editor closes, and the folder's displayed name
now reads "ABC" — exactly ELITEA-2126's own step 4 ("Click the checkmark icon
→ Folder renamed to 'ABC' in the folder list").

**Live-reconfirmed this session** (fresh live drive, not assumed from the
digest alone): the sibling gap-check session (see `lextend_` AFS files for
ELITEA-2125/2131) independently re-confirmed `data-disabled="true"` for a
2-char name on a freshly seeded folder (id 242) using the identical mechanism
this case's step 2 needs; the 3-char-activates-and-renames path itself was
NOT separately re-clicked this session (it would leave an ADDITIONAL renamed
folder artifact in the shared DEV project on top of the ones already
undeletable per issue #1309) — the covering test's own Step 7–9 run green
this session (`pytest tests/ui/chat/test_chat_folder_rename_checkmark_validation.py::TestChatFolderRenameCheckmarkValidation::test_folder_rename_checkmark_validation`,
1 passed, confirmed fresh before this AFS pass), which is the same live
system-produced evidence this dedup relies on.

| ELITEA-2126 step | Covered by (`test_folder_rename_checkmark_validation`) |
|---|---|
| 1. Navigate to Chats, hover folder, 3-dot icon, click Edit → folder name editable | Step 1 — opens rename editor via dot-menu's "Rename" item (case says "Edit"; real item is "Rename" — documented drift, not a defect) |
| 2. Clear current name, type 2 characters ("AB") → checkmark inactive | Step 4 — `set_folder_name("AB")` + `is_folder_name_confirm_enabled()` is `False` |
| 3. Type one more character ("ABC") → checkmark becomes active | Steps 7–8 — `set_folder_name("ABC")` + `is_folder_name_confirm_enabled()` is `True` (`data-disabled="false"`) |
| 4. Click the checkmark icon → folder renamed to "ABC" in the folder list | Step 9 — click, `PUT … → 200`, editor closes, `chat-folder-item-{id}` text contains "ABC" |

**Scope note (no gap, so no `extend-existing`).** All 4 of ELITEA-2126's
steps map onto the covering test's Steps 1, 4, 7, 8, 9. No case element
lacks a corresponding assertion in the covering spec.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to Chats, hover over a folder, click three-dot icon, click Edit — Folder name is editable.
2. Clear the current name and type 2 characters ('AB') — Checkmark is inactive.
3. Type one more character ('ABC') — Checkmark icon becomes active/enabled.
4. Click the checkmark icon — Folder renamed to 'ABC' in the folder list.

## Expected Results
- Checkmark activates at exactly 3 characters and the rename persists —
  proven live by `test_folder_rename_checkmark_validation` (see Dedup proof
  above; re-run green this session).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open rename editor via dot-menu | folder name editable | covering test Step 1 | `open_folder_rename_editor()` call + pre-fill/focus assertions | already-covered |
| Step 2 — type 2 chars ("AB") | checkmark inactive | covering test Step 4 | `is_folder_name_confirm_enabled()` is `False` | already-covered |
| Step 3 — type 3rd char ("ABC") | checkmark active | covering test Steps 7–8 | `is_folder_name_confirm_enabled()` is `True` | already-covered |
| Step 4 — click checkmark, folder renamed | `PUT → 200`, displayed name updates | covering test Step 9 | `PUT` status assertion + `folder_item.text_content()` contains "ABC" | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md`'s Coverage Map
  Axis 2) — none needed here.

## Cleanup
N/A — no new test written; no new folder created specifically for this
case (reused the covering test's own re-run + the sibling gap-check
session's folder for the 2-char sub-assertion).

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-name-input`,
`chat-folder-name-confirm-button` (with its `data-disabled` state attribute),
`chat-folder-menu-rename-menuitem`, `conversation-menu-menu-button` (scoped),
`chat-folder-item-{id}` — all confirmed present and functioning on live
localhost this session. No new handles needed for this traceability pass.

## TMS linkage
Link ELITEA-2126 to ELITEA-2458 in the TMS (both ways) so the audit trail
resolves: ELITEA-2126's `already-covered` disposition points at ELITEA-2458's
automated test; ELITEA-2458's case gains an "also satisfies ELITEA-2126"
back-reference.
