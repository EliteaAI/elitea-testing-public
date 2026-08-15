# Test Case: Chat – Multiple Folders Can Be Pinned Independently

## Metadata
- **TMS ID**: ELITEA-2161
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, same mapping as
  ELITEA-2152/2153)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer) — batch chat-remaining-w09,
  clustered with ELITEA-2160 (conversation equivalent) in the same session
- **Status**: extend-existing
- **Extension target**: `automation/tests/ui/chat/test_pin_folder.py` (merged
  `origin/automation/base` commit `fb306056`, wave-08) — new class
  `TestMultipleFoldersPinnedIndependently`, zero existing method bodies touched
- **surface_key**: `chat-folder-context-menu` (same surface as ELITEA-2121/2130/2152/2153/2154/2155/2156)

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least two folders exist. Test creates its own (see § Test Data).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_1`** — first folder to pin, seeded with one conversation (`conv_in_1`) so step 4's
  "retains conversations when expanded" has something real to check.
- **`folder_2`** — second folder to pin, created immediately after `folder_1`, seeded with its own
  conversation (`conv_in_2`).
- **`folder_sibling`** — a third, never-pinned, empty folder — the "unpinned content" comparison
  baseline for step 3 (needed because by step 2 BOTH `folder_1` and `folder_2` are pinned, so
  neither can serve as the "unpinned" comparison point any more).

## Test Steps

1. Navigate to `${BASE_URL}/chat`. Pin `folder_1` via its 3-dot menu → "Pin on top"
   (`FOLDER_MENU_PIN_ITEM`), awaiting the `PATCH .../folder/prompt_lib/.../{folder_1_id}` → 200.
   - **Verify**: `folder_1` carries `data-pinned="true"` on `chat-folder-item-{folder_1_id}`
     (moved to the pinned folders section).
2. Pin `folder_2` via the same mechanism.
   - **Verify**: `folder_2` carries `data-pinned="true"`; **AND** `folder_1` STILL carries
     `data-pinned="true"` (pinning the second did not silently unpin the first — the case's own
     core independence claim).
3. Verify both pinned folders appear at the top, above all unpinned content.
   - **Verify**: `folder_1` and `folder_2`'s bounding-box Y (+ height) are both `<=`
     `folder_sibling`'s bounding-box Y (source-confirmed render order, `Conversations.jsx`:
     `renderFoldersSection({isPinned: true})` renders first, above every other section).
4. Verify both folders retain their conversations when expanded.
   - **Verify**: expand `folder_1` (force=True — the pinned-folder disabled-ancestor gotcha,
     ELITEA-2121/2130) and confirm `conv_in_1` renders inside it; independently expand `folder_2`
     (force=True) and confirm `conv_in_2` renders inside it. Pinning is a genuine list-partition
     remount that resets each folder's own local expand state to collapsed (already documented,
     ELITEA-2152/2153's AFS) — re-expanding explicitly is the correct way to observe "when
     expanded", not an assumption that expand state survives the move.

## Expected Results
- Pinning `folder_2` after `folder_1` does not unpin, hide, or otherwise disturb `folder_1` — both
  remain independently pinned and visible.
- Both pinned folders render at the top, above the unpinned folder / conversation content.
- Both folders retain their own conversations, independently, when expanded.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: ≥2 folders exist | — | Setup | `folder_1`/`folder_2`/`folder_sibling` API-seeded | asserted |
| 1 Pin first folder; verify moves to pinned folders section | First folder pinned | AFS step 1 | `data-pinned="true"` on `chat-folder-item-{folder_1_id}` | asserted |
| 2 Pin second folder; verify also moves to pinned folders section | Second folder pinned | AFS step 2 | `data-pinned="true"` for `folder_2`, PLUS `folder_1` re-checked still pinned | asserted |
| 3 Verify both pinned folders appear at top above all unpinned content | Both pinned folders at top | AFS step 3 | Y-position of both vs `folder_sibling` | asserted |
| 4 Verify both folders retain their conversations when expanded | Conversations intact | AFS step 4 | `is_conversation_in_folder()` for each folder independently, post force-expand | asserted |
| Expected Final State: "Multiple folders pinned independently" | — | steps 1–4 | covered by rows above | asserted |
| Pass/Fail: "Only one folder can be pinned at a time" must NOT happen | — | step 2's `folder_1` re-check | `folder_1.data-pinned == "true"` after pinning `folder_2` | asserted — this is the test's central negative assertion |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 2 re-checks `folder_1`'s pinned state after pinning `folder_2` — *added: same reasoning as
  ELITEA-2160's sibling AFS — the case's Fail criterion is a claim about state AFTER a second
  action, made explicit here rather than left implied.*
- Step 3 uses a THIRD folder (`folder_sibling`) as the unpinned baseline, rather than reusing
  `folder_1`/`folder_2` pre-pin positions — *added: by the time step 3 runs, both target folders are
  already pinned, so neither can serve as its own "before" baseline any more; a genuinely-still-
  unpinned third folder is required for an honest "above unpinned content" comparison.*
- Step 4 force-expands BOTH folders independently (not just one) — *added: proves the
  remount-resets-expand-state behavior (ELITEA-2152/2153) applies uniformly to a SECOND pinned
  folder too, not just the first — not previously exercised with two simultaneously-pinned folders.*
- Console/network side-channel checked after every interaction, same idiom as ELITEA-2152/2153.

## Cleanup
1. Delete `conv_in_1`, `conv_in_2` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_1`, `folder_2`, `folder_sibling` via `conversation_api.delete_folder(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle.

## Concrete Handles (discovered during exploration)
All handles pre-exist from ELITEA-2121/2130/2152/2153 — zero new testid work.

| Element | Testid handle | Provenance |
|---|---|---|
| Pin/Unpin folder context-menu item | `FOLDER_MENU_PIN_ITEM` (`chat-folder-menu-pin-menuitem`) | on-`automation/testids` ✓ (ELITEA-2121/2130, commit `be489cee`); not yet independently re-verified on `main` this session |
| Folder pinned-state attribute | `data-pinned="true"/"false"` on `chat-folder-item-{id}` | same commit as above |
| Folder item / expand state | `chat-folder-item-{id}` / `data-expanded` | pre-existing (ELITEA-2098/2130) |

## Network Behavior
- `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` per pin (NOT `PUT`/`POST` —
  already-documented distinguishing fact, ELITEA-2121/2130's AFS) — awaited via
  `page.expect_response()` and status-checked `200` for both pins, same idiom
  `test_pin_folder.py`'s existing test already uses.
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks.

## Known Defects Found During Exploration
None. The independence mechanism (pinning a second folder does not affect the first) worked
correctly on live re-verification via the implementation's own pytest run (see Run Report).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: `automation/pages/chat_page.py` — zero new methods needed. Reuse
  `pin_folder_via_menu()`, `is_folder_pinned()`, `get_folder_item()`, `expand_folder(force=True)`,
  `is_conversation_in_folder()`, `open_folder_context_menu()` (all pre-existing).
- Priority marker: `@pytest.mark.p2`.
