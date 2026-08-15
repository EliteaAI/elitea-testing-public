# Test Case: Chat – Pin a Folder and Verify It Appears at the Top of the Left Panel

## Metadata
- **TMS ID**: ELITEA-2462
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (per source case's `priority: high`; traceability AFS, no priority-digit filename)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost: no login needed — `VITE_DEV_TOKEN` auto-auths)
- **Analyst**: qa-engineer (agent), batch `chat-remaining-w09`, 2026-08-15
- **Status**: already-covered
- **surface_key**: `chat-folder-context-menu` (same folder dot-menu Pin/Unpin surface as
  ELITEA-2121/2130/2152/2153/2154/2155/2156/2157/2158)

## Preconditions
- User is logged in to the Elitea platform.

## Dedup proof — Rule-6 behavioural equivalence

**Covering spec:** `automation/tests/ui/chat/test_pin_folder.py`, class
`TestPinFolderViaPinOnTop`, method `test_pin_folder_via_pin_on_top` (TMS ELITEA-2152, AFS
`test-specs/chat-interface/l3_pin-a-folder-via-pin-on-top-option_ELITEA-2152.md`). Merged to
`origin/automation/base` via PR #1552 (`fb306056`, "test: chat-remaining wave-08 —
pin/unpin conversation & folder basics (7 cases)"). Confirmed present this session via a fresh
`git fetch origin` + `git show origin/automation/base:automation/tests/ui/chat/test_pin_folder.py`
(class + method found).

**Behavioural-equivalence argument.** ELITEA-2462's title, objective, and all 6 steps are a
word-for-word match of ELITEA-2152's own case text and AFS — this is not a partial overlap, it is
the same case authored twice under two different TMS ids:

| ELITEA-2462 step | ELITEA-2152's AFS / `test_pin_folder_via_pin_on_top` step |
|---|---|
| 1. Navigate to Chats and identify an unpinned folder | Setup + AFS Step 1 — seeds `folder_target` (unpinned), navigates to Chats, confirms `data-pinned="false"` baseline |
| 2. Hover, click 3-dot icon, click "Pin on top" | AFS Step 2 — `open_folder_context_menu()`, asserts menu label reads "Pin on top", clicks it, awaits the `PATCH .../folder/prompt_lib/...` 200 |
| 3. Verify the folder moves to the top of the left panel in the pinned folders section | AFS Step 3 — `data-pinned` flips `false`→`true`; Y decreases; order vs `folder_sibling` reverses (folder now renders above it) |
| 4. Verify a pin icon is displayed next to the folder name | AFS Step 4 — `data-pinned="true"` re-asserted (the compliant "pin icon" locator per `.agents/testing.md` § Locator policy — the raw `<PinIcon>` has no testid and is driven by the same boolean) |
| 5. Verify the folder still displays all its conversations when expanded | AFS Step 5 — re-expands the folder (`force=True`, pinning triggers a list-partition remount that resets local expand state) and confirms `conv_in_folder` still resolves inside it |
| 6. Verify the folder is no longer present in its original unpinned position | AFS Step 6 — same Y/order fact as Step 3, re-asserted: final Y != baseline Y |

Every element of ELITEA-2462's 6 steps has a direct, one-to-one assertion in the covering test —
none of ELITEA-2462's asks exceed what it already proves, and none of the covering test's
assertions go unused by this case's wording.

**Live-reconfirmed this session** (not assumed from the digest alone, per the "coverage judgments
stand on your own execution" rule): re-ran the covering test live against `http://localhost:5173`:
```
tests/ui/chat/test_pin_folder.py::TestPinFolderViaPinOnTop::test_pin_folder_via_pin_on_top PASSED [100%]
============================== 1 passed in 18.40s ==============================
```
Confirms every one of ELITEA-2462's 6 steps still holds on today's live product, not just at the
covering test's original implementation time.

## Test Steps (source case, reproduced for traceability only — not re-implemented)
1. Navigate to the Chats section and identify an unpinned folder — Target page/section loads
   successfully.
2. Hover over the folder, click the three-dot icon, and click Pin on top — Action completes without
   error and produces the expected UI state.
3. Verify the folder moves to the top of the left panel in the pinned folders section — Condition
   holds as described.
4. Verify a pin icon is displayed next to the folder name — Condition holds as described.
5. Verify the folder still displays all its conversations when expanded — Condition holds as
   described.
6. Verify the folder is no longer present in its original unpinned position — Condition holds as
   described.

## Expected Results
- Pinning a folder via the dot-menu's "Pin on top" item moves it into the pinned section, above any
  unpinned folder it was previously below — proven live by `test_pin_folder_via_pin_on_top`.
- `data-pinned` flips `false`→`true` (the compliant "pin icon visible" proxy), the folder retains
  its conversations across the pin-triggered remount (re-expand shows them intact), and its
  rendered position measurably changes (Y decreases; relative order vs a stable unpinned sibling
  reverses) — proving it left its original position, not merely that a flag flipped.
- Reconfirmed live this session (see Dedup proof above).

## Coverage Map

### Axis 1 — Case elements

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state`/`VITE_DEV_TOKEN` (localhost) | framework fixture, covering test | already-covered |
| Step 1 — navigate to Chats, identify an unpinned folder | page/section loads | `test_pin_folder_via_pin_on_top` Setup + Step 1 | seeds `folder_target` unpinned, navigates, confirms `data-pinned="false"` baseline | already-covered |
| Step 2 — hover folder, click 3-dot icon, click Pin on top | action completes, expected UI state | `test_pin_folder_via_pin_on_top` Step 2 | menu label check ("Pin on top") + click on `chat-folder-menu-pin-menuitem` + `PATCH → 200` | already-covered |
| Step 3 — folder moves to top of left panel, pinned folders section | condition holds | `test_pin_folder_via_pin_on_top` Step 3 | `data-pinned` false→true; Y decreased; order vs `folder_sibling` reversed | already-covered |
| Step 4 — pin icon displayed next to folder name | condition holds | `test_pin_folder_via_pin_on_top` Step 4 | `data-pinned="true"` re-asserted (compliant locator for "pin icon visible") | already-covered |
| Step 5 — folder still displays all conversations when expanded | condition holds | `test_pin_folder_via_pin_on_top` Step 5 | re-expand (`force=True`) + `is_conversation_in_folder()` still True | already-covered |
| Step 6 — folder no longer present in original unpinned position | condition holds | `test_pin_folder_via_pin_on_top` Step 6 | final Y != baseline Y | already-covered |
| Expected Final State (prose): "folder is no longer present in its original unpinned position" | — | Step 6's covering assertion | covered by the row above | already-covered |
| Pass/Fail: "All steps complete without errors" | — | covering test | console-check side-channel (no unexpected console errors, `secrets/secrets/default` 403 excluded) | already-covered |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
None beyond what the covering spec already documents (see its own Coverage Map Axis 2 section,
ELITEA-2152's AFS) — none needed here.

## Cleanup
N/A — no new test written. Live-verification this session re-ran the existing covering test as-is
(its own setup/teardown creates and deletes its own fixture data); zero net pollution added by this
session.

## Concrete Handles (discovered during exploration)
Reuses the covering spec's handles verbatim — `chat-folder-menu-pin-menuitem`, `data-pinned` on
`chat-folder-item-{id}`, `chat-folder-item-{id}` bounding box, `chat-conversation-item-{id}` scoped
inside the folder container — all confirmed present and functioning on live localhost this session
(via the live test re-run). No new handles needed for this traceability pass.

## Known Defects Found During Exploration
None. The covering test passes live and its behavior matches this case's 6 steps exactly.

## Blocked Steps
None.

## TMS linkage
Link ELITEA-2462 to ELITEA-2152 in the TMS (both ways) so the audit trail resolves: ELITEA-2462's
`already-covered` disposition points at the automated test; ELITEA-2152's case gains an "also
satisfies ELITEA-2462" back-reference. Same pattern already established between ELITEA-2461/
ELITEA-2149+2151 and ELITEA-2159/ELITEA-2151.
