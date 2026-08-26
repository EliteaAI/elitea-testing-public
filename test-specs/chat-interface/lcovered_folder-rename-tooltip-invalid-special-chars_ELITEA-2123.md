# Test Case: Chat – Folder Rename – Validation Tooltip Displayed for Invalid Input

## Metadata
- **TMS ID**: ELITEA-2123
- **Linked Story**: none
- **Priority**: l2 (per source case's `medium`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: test-automation-engineer (agent, combined analyst+implementer slot), session 2026-08-15
- **Status**: already-covered

## Preconditions
- User is authenticated (localhost: automatic via `VITE_DEV_TOKEN`).
- At least one existing folder is present in the Chats section.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`,
method `test_folder_rename_checkmark_special_chars_and_leading_space_invalid`
(TMS ELITEA-2459, AFS
`test-specs/chat-interface/lextend_folder-rename-tooltip-special-chars-and-space-first-char_ELITEA-2459.md`),
merged to `origin/automation/base` (commit `5cc8647c`, PR #1313,
"test: (ELITEA-2459) Chat folder rename — validation tooltip for special
chars + leading space (extend-existing)"). Confirmed on `origin/automation/base`
via `git log origin/automation/base -- automation/tests/ui/chat/test_chat_folder_rename_checkmark_validation.py`
this session (fresh `git fetch origin` first) — `5cc8647c` is a confirmed
ancestor of `origin/automation/base` (`git merge-base --is-ancestor`).

**Behavioural-equivalence argument.** ELITEA-2123 asks for exactly the
scenario the covering test's Step 2 already implements END TO END, with the
**exact same literal test data**: seed a folder → open its inline rename
editor via the dot-menu → type `"Folder$$%%"` → assert the input shows the
value verbatim → assert `chat-folder-name-confirm-button` carries
`data-disabled="true"` (checkmark inactive) → assert the tooltip text is the
byte-for-byte `FolderNameWarningMessage` copy the case itself quotes → click
the inactive checkmark and assert THREE independent no-op signals (editor
stays open, input value unchanged, no `PUT .../folder/prompt_lib/...`
request fires) → the folder never re-renders in its display (unchanged) form,
proving the name was never persisted.

**Live-reconfirmed this session** (not assumed from the digest alone, per the
"coverage judgments stand on your own execution" rule): seeded a fresh folder
via the UI, opened its rename editor via the dot-menu → "Rename" (case text
says "Edit" — the real menu item is labelled "Rename", the same already-
documented case-text drift as ELITEA-2121/2130/2456, not a defect), cleared
and typed `"Folder$$%%"` via `browser_fill_form` (replacing, not appending —
the editor's known "append not replace" race with a bare `Control+a` was hit
once mid-exploration and worked around exactly as `ChatPage.set_folder_name()`'s
own docstring warns). Observed: the confirm control shows the exact quoted
validation tooltip as its accessible name (invalid-state a11y behaviour
matches the covering test's documented gotcha), and clicking it fired no
`PUT` (confirmed via `browser_network_requests`) — the editor stayed open,
proving both the tooltip and the no-op click hold on today's live UI, not
just at ELITEA-2459's original implementation time.

| ELITEA-2123 step | Covered by (`test_folder_rename_checkmark_special_chars_and_leading_space_invalid`) |
|---|---|
| 1. Navigate to Chats, hover folder, 3-dot icon, Edit → folder name editable | Step 1 — seeds a folder, opens its rename editor via the dot-menu's "Rename" item (case says "Edit"; real item is "Rename" — documented drift, not a defect) |
| 2. Clear name, type 'Folder$$%%' → input contains invalid characters | Step 2 — `chat.set_folder_name("Folder$$%%")` + `input_value() == "Folder$$%%"` assertion, same literal string |
| 3. Verify tooltip with the exact quoted validation message | Step 2 — `tooltip_text == VALIDATION_TOOLTIP_TEXT`, byte-for-byte match of the same message the case quotes |
| 4. Verify checkmark inactive | Step 2 — `assert not chat.is_folder_name_confirm_enabled()` (`data-disabled="true"`) |
| 5. Attempt click checkmark → no effect | Step 2 — click + assert editor stays open, input unchanged, no PUT fires |
| 6. Verify folder name remains unchanged | Step 2 — input value assertion + `get_folder_item(folder_id).count() == 0` (folder never re-renders in display mode, i.e. no save occurred) + no PUT fired |

**Scope note (no gap, so no `extend-existing`).** All 6 of ELITEA-2123's steps
map onto Step 2 of the covering test, using the identical literal test data
("Folder$$%%"). No case element lacks a corresponding assertion in the
covering spec.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to Chats, hover over a folder, click three-dot icon, click Edit — Folder name is editable.
2. Clear the current name and type 'Folder$$%%' — Input contains invalid characters.
3. Verify a tooltip appears with validation message: "The folder name should be 3 to 64 characters long. It can include letters (a-z, A-Z), numbers (0-9), underscores (_), brackets ([]), parentheses (()), dots (.), hyphen(-), and spaces. Please note that the first character should not be a space." — Tooltip shows correct validation message.
4. Verify the checkmark icon is inactive — Checkmark disabled.
5. Attempt to click the checkmark icon — Click has no effect.
6. Verify the folder name remains unchanged — Name unchanged.

## Expected Results
- Validation tooltip shown for invalid characters; checkmark disabled;
  click is a no-op — proven live by
  `test_folder_rename_checkmark_special_chars_and_leading_space_invalid`
  (see Dedup proof above) and reconfirmed live this session.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open rename editor via dot-menu | folder name editable | covering test Step 1 | `open_folder_rename_editor()` call | already-covered |
| Step 2 — type 'Folder$$%%' | input shows invalid characters | covering test Step 2 | `input_value() == "Folder$$%%"` | already-covered |
| Step 3 — exact tooltip message | tooltip shows correct text | covering test Step 2 | `tooltip_text == VALIDATION_TOOLTIP_TEXT` | already-covered |
| Step 4 — checkmark inactive | checkmark disabled | covering test Step 2 | `is_folder_name_confirm_enabled()` | already-covered |
| Step 5 — click checkmark, no effect | click is a no-op | covering test Step 2 | editor-open + input-unchanged + no-PUT assertions | already-covered |
| Step 6 — folder name unchanged | name unchanged | covering test Step 2 | `get_folder_item(folder_id).count() == 0` + no PUT | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `lextend_folder-rename-tooltip-special-chars-and-space-first-char_ELITEA-2459.md`'s
  Coverage Map Axis 2) — none needed here.

## Cleanup
N/A — no new test written. Live-verification exploration folder (id 235,
"New folderELITEA2123W06Seed") was created and deleted via the UI's own
Delete flow within this session — zero net pollution left behind.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-name-input`,
`chat-folder-name-confirm-button` (with its `data-disabled` state attribute),
`chat-folder-name-cancel-button`, `chat-folder-menu-rename-menuitem`,
`conversation-menu-menu-button` (scoped), `chat-folder-item-{id}` — all
confirmed present and functioning on live localhost this session. No new
handles needed for this traceability pass.

## TMS linkage
Link ELITEA-2123 to ELITEA-2459 in the TMS (both ways) so the audit trail
resolves: ELITEA-2123's `already-covered` disposition points at ELITEA-2459's
automated test; ELITEA-2459's case gains an "also satisfies ELITEA-2123"
back-reference.
