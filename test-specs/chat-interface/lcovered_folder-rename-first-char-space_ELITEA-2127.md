# Test Case: Chat – Folder Rename – First Character Cannot Be a Space

## Metadata
- **TMS ID**: ELITEA-2127
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

**Behavioural-equivalence argument.** ELITEA-2127 asks specifically whether a
SPACE typed as the FIRST character of a folder name is rejected. The covering
test's Step 3 proves precisely this, and does so more rigorously than a
bare single-space input would: it types `" ValidRest"` — a leading space
followed by an otherwise fully valid, sufficiently-long remainder — which
isolates the first-character-space rule from the separate length-floor rule
(a lone space would fail for BOTH reasons at once, an ambiguous proof). It
asserts `chat-folder-name-confirm-button` carries `data-disabled="true"`
(checkmark inactive), the exact quoted `FolderNameWarningMessage` tooltip
text, and — on clicking the inactive checkmark — three independent no-op
signals (editor stays open, input value unchanged, no
`PUT .../folder/prompt_lib/...` fires), i.e. save cannot be triggered. The
Space key is literally the first character `press_sequentially()` sends, so
"press Space as the first character [then continue typing a valid
remainder]" is exactly what the covering test drives.

**Live-reconfirmed this session** (not assumed from the digest alone, per the
"coverage judgments stand on your own execution" rule): opened the same
seeded folder's rename editor via the dot-menu → "Rename" (case says "Edit"
— the real menu item is labelled "Rename", same already-documented drift as
ELITEA-2121/2130/2123/2456), filled the input with a leading space + valid
text (`" ValidRest2127"`) via `browser_fill_form`. Observed: the validation
tooltip appeared with the exact quoted text, the confirm control's accessible
name became the tooltip text (the covering test's documented invalid-state
a11y behaviour), and clicking the confirm control fired NO `PUT` request
(confirmed via `browser_network_requests` — only the earlier folder-creation
`POST`/`GET` calls were present, no `PUT`) and the editor remained open with
the value unchanged. Confirms both the tooltip and the "save cannot be
triggered" behaviour hold on today's live UI.

| ELITEA-2127 step | Covered by (`test_folder_rename_checkmark_special_chars_and_leading_space_invalid`) |
|---|---|
| 1. Navigate to Chats, hover folder, 3-dot icon, Edit → folder name editable | Step 1 — seeds a folder, opens its rename editor via the dot-menu's "Rename" item (case says "Edit"; real item is "Rename" — documented drift, not a defect) |
| 2. Clear name, press Space as first character → space not accepted as first char OR checkmark stays inactive | Step 3 — `chat.set_folder_name(" ValidRest")` (space-first, valid remainder) + `input_value() == " ValidRest"` assertion — the space IS accepted by the field, but the checkmark stays inactive (the case's OR-condition second clause), proving the rule via `data-disabled` rather than field-level rejection |
| 3. Verify tooltip validation message appears | Step 3 — `tooltip_text == VALIDATION_TOOLTIP_TEXT`, byte-for-byte match |
| 4. Verify save cannot be triggered while name starts with a space → checkmark inactive | Step 3 — `assert not chat.is_folder_name_confirm_enabled()` + click + assert editor stays open, input unchanged, no PUT fires |

**Scope note (no gap, so no `extend-existing`).** All 4 of ELITEA-2127's
steps map onto Step 3 of the covering test. No case element lacks a
corresponding assertion in the covering spec.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to Chats, hover over a folder, click three-dot icon, click Edit — Folder name is editable.
2. Clear the current name and press the Space key as the first character — Space not accepted as first character or checkmark stays inactive.
3. Verify the tooltip validation message appears — Tooltip shows validation message.
4. Verify the save cannot be triggered while name starts with a space — Checkmark inactive.

## Expected Results
- Leading space rejected (checkmark stays inactive, tooltip shown, save
  cannot be triggered) — proven live by
  `test_folder_rename_checkmark_special_chars_and_leading_space_invalid`
  (see Dedup proof above) and reconfirmed live this session.

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — open rename editor via dot-menu | folder name editable | covering test Step 1 | `open_folder_rename_editor()` call | already-covered |
| Step 2 — space as first character | space accepted in field, checkmark stays inactive | covering test Step 3 | `input_value() == " ValidRest"` + `is_folder_name_confirm_enabled()` | already-covered |
| Step 3 — tooltip validation message appears | tooltip shows correct text | covering test Step 3 | `tooltip_text == VALIDATION_TOOLTIP_TEXT` | already-covered |
| Step 4 — save cannot be triggered, checkmark inactive | checkmark disabled, click no-op | covering test Step 3 | editor-open + input-unchanged + no-PUT assertions | already-covered |

### Axis 2 — Analyst additions
- None beyond the covering spec's own additions (already documented in
  `lextend_folder-rename-tooltip-special-chars-and-space-first-char_ELITEA-2459.md`'s
  Coverage Map Axis 2) — none needed here.

## Cleanup
N/A — no new test written. Live-verification exploration used the same
seeded folder as the ELITEA-2123 dedup pass (id 235,
"New folderELITEA2123W06Seed"), which was deleted via the UI's own Delete
flow within this session — zero net pollution left behind.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-name-input`,
`chat-folder-name-confirm-button` (with its `data-disabled` state attribute),
`chat-folder-name-cancel-button`, `chat-folder-menu-rename-menuitem`,
`conversation-menu-menu-button` (scoped), `chat-folder-item-{id}` — all
confirmed present and functioning on live localhost this session. No new
handles needed for this traceability pass.

## TMS linkage
Link ELITEA-2127 to ELITEA-2459 in the TMS (both ways) so the audit trail
resolves: ELITEA-2127's `already-covered` disposition points at ELITEA-2459's
automated test; ELITEA-2459's case gains an "also satisfies ELITEA-2127"
back-reference.
