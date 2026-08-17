# Test Case: Chat – Unpin a Pinned Folder

## Metadata
- **TMS ID**: ELITEA-2153
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium`; same mapping as its pin-sibling
  ELITEA-2152 and the conversation pin/unpin pair ELITEA-2149/2150)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project "Private", `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: test-automation-engineer (agent) — combined analyst+implementer slot, batch
  `chat-remaining-w08`, same live session as ELITEA-2152 (its pin counterpart)
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-context-menu` (same surface as ELITEA-2152/2121/2130)

## Preconditions (case)
- User is logged in to the Elitea platform.
- At least one pinned folder exists.

This AFS's own setup satisfies the precondition by seeding a fresh folder and pinning it via the
UI dot-menu (the already-covered ELITEA-2152 flow) as a SETUP action, rather than assuming a
pre-existing pinned folder in the shared, already-polluted DEV project — same reasoning ELITEA-2130's
AFS and ELITEA-2150's AFS (conversation side) both already give for their own analogous setups.

## Why `ready-for-automation`, not `extend-existing`

Same reasoning as ELITEA-2152's AFS: no existing test's OWN subject is unpinning a folder and
verifying its position/icon/conversations reversion — ELITEA-2130 pins-then-renames (never unpins),
ELITEA-2151 pins-for-ordering (never unpins). This is new coverage. Lands in the SAME new file as
ELITEA-2152 (`test_pin_folder.py`) as a second test class — mirrors exactly how ELITEA-2149
(`TestPinConversationViaPinOnTop`, `ready-for-automation`) and ELITEA-2150
(`TestUnpinConversationViaContextMenu`, appended to the same file) paired up on the conversation
side. Both this AFS and ELITEA-2152's are `ready-for-automation` (not one `extend-existing` on the
other) because neither has a MERGED covering spec at analysis time — both are being authored and
implemented together, in the same session, landing in one new file.

> **Corrected during implementation** (Phase 2 amend-in-PR): same corrections as ELITEA-2152's AFS —
> creation order reversed (the AFS's original "sibling created first" claim was backwards) and the
> expand-state-persistence claim removed (pinning AND unpinning both remount the row and reset
> `data-expanded`, not merely the pin direction). See ELITEA-2152's AFS intro for the full context.

## Test Data

### generate-per-test (created via API + one UI setup action, cleaned up in teardown)
- **`folder_pinned`** — created FIRST via `conversation_api.create_folder(name)`, then PINNED via
  the UI dot-menu's "Pin on top" item (`pin_folder_via_menu()`, the already-covered ELITEA-2152
  mechanism) as setup, reaching the "at least one pinned folder exists" precondition through the
  real UI action rather than an API-only shortcut.
- **`folder_sibling`** — created SECOND via `conversation_api.create_folder(name)`, AFTER
  `folder_pinned`, stays unpinned throughout. Being the more-recently-created/touched folder, it
  renders ABOVE `folder_pinned` pre-pin — same corrected ordering rule ELITEA-2152's AFS documents.
  A stable comparison point proving the unpinned folder never moves, so `folder_pinned`'s position
  relative to it is meaningful evidence of reversion.
- **`conv_in_folder`** — created via `conversation_api.create_conversation(name)`, moved into
  `folder_pinned` via `conversation_api.move_conversation_to_folder(id, folder_pinned_id)` BEFORE
  pinning. Gives Step 6 ("folder retains all its conversations") a real conversation to prove
  "retained" against.

## Test Steps

1. Setup reaches the precondition: `folder_pinned` seeded unpinned; expand it and verify
   `conv_in_folder` resolves inside it (`data-expanded="true"`) — this check runs BEFORE pinning,
   as the pre-pin baseline. Capture `folder_pinned`'s pre-pin bounding-box Y (`original_unpinned_y`,
   alongside `folder_sibling`'s Y) — the exact analog of ELITEA-2152's `initial_y`. THEN pin
   `folder_pinned` via the real UI dot-menu action.
   - **Verify**: `data-pinned="true"` on `folder_pinned` after the setup pin action resolves.
2. Hover `folder_pinned`, click its 3-dot icon (`force=True` — REQUIRED here: the folder IS pinned,
   so the disabled-ancestor gotcha ELITEA-2130's AFS documents genuinely applies). Verify the
   Pin/Unpin item reads **"Unpin"** before clicking it, then click it.
   - **Verify**: `chat-folder-menu-pin-menuitem` text content == `"Unpin"` pre-click (proves the
     menu's own state-derivation reflects the pinned precondition correctly, not just presence).
3. Verify the folder is removed from the pinned section.
   - **Verify**: `data-pinned` flips `"true"` → `"false"`.
4. Verify the pin icon is no longer visible.
   - **Verify**: same `data-pinned="false"` fact as Step 3 — per `.agents/testing.md` § Locator
     policy this IS the compliant "pin icon" observable (raw icon has no testid, driven by the same
     boolean), restated because the case enumerates it as its own step, exactly as ELITEA-2152's
     AFS documents for the inverse direction.
5. Verify the folder reappears in the unpinned folders section.
   - **Verify**: bounding-box Y returns to `original_unpinned_y`, within a small sub-pixel tolerance
     (~2px — `getBoundingClientRect()` can shift a fraction of a pixel between two reads of an
     unmoved element; a real reflow moves a row by a full row height, ~41px, far above this
     tolerance) — live-confirmed this session that a folder's position, once unpinned, returns to
     the SAME Y coordinate it held before it was ever pinned (not merely "some unpinned position");
     `folder_sibling`'s Y checked the same way, for the same relative-order comparison ELITEA-2152's
     AFS uses — a direct, deterministic reversal.
6. Verify the folder retains all its conversations.
   - **Verify**: the unpin action ALSO remounts the row (same corrected fact as ELITEA-2152's AFS
     Step 5, inverse direction) — `data-expanded` is NOT assumed to survive; re-expand explicitly
     (`expand_folder(..., force=True)`) and THEN verify `conv_in_folder` still resolves inside
     `folder_pinned`'s container, proving the full pin→unpin round-trip didn't drop it.

## Expected Results
- Unpinning a folder via the dot-menu's "Unpin" item (SAME testid as pinning,
  `chat-folder-menu-pin-menuitem`, label toggles per state; `PATCH .../folder/prompt_lib/{project_id}
  /{folder_id}` → `200 OK`) removes it from the pinned section and returns it to its original
  unpinned position (Y within a small sub-pixel tolerance of the pre-pin baseline).
- `data-pinned` flips `"true"` → `"false"` — the compliant "pin icon removed" observable.
- Unpinning also remounts the row (same fact as pinning, inverse direction) — re-expanding after
  the action shows the folder's conversations unaffected by the full pin/unpin round-trip.
- No new console errors beyond the pre-existing, environment-wide `secrets` 403 noise.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: at least one pinned folder exists | — | Setup + AFS step 1 | `folder_pinned` seeded unpinned then pinned via real UI action | asserted |
| 1 Navigate to Chats, hover pinned folder, click 3-dot, click 'Unpin' | Folder removed from pinned section | AFS steps 1–3 | step 1: baseline; step 2: menu label + click; step 3: `data-pinned` flip | asserted |
| 2 Verify the pin icon is no longer visible | Pin icon removed | AFS step 4 | `data-pinned="false"` per Locator policy | asserted |
| 3 Verify the folder reappears in the unpinned folders section | Folder in unpinned section | AFS step 5 | Y returns to `original_unpinned_y`; order vs `folder_sibling` matches pre-pin baseline | asserted |
| 4 Verify the folder retains all its conversations | Conversations intact | AFS step 6 | folder re-expanded post-unpin (`force=True`, corrected — see Step 6 note); `conv_in_folder` still resolves inside `folder_pinned` | asserted |
| Expected Final State: "Folder unpinned and in unpinned section, conversations intact" | — | steps 3–6 | covered by the rows above | asserted |
| Pass/Fail: "Folder remains pinned or conversations lost" (fail condition) | — | steps 3, 6 | `data-pinned`/conversation-presence checks are the direct inverse of this fail condition | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`. All
rows `asserted`. No case-text/product drift found for this case (same note as ELITEA-2152's AFS).

### Axis 2 — Analyst additions

- Step 1's setup PINS the folder via the real UI dot-menu action (not a raw API-only precondition
  shortcut) — *added: reusing the already-covered ELITEA-2152 mechanism as setup is the same "reuse
  to travel, not to conclude" precedent ELITEA-2150's AFS already establishes for the conversation
  side; the case's own subject (unpin) is still fully exercised live by this case's own steps.*
- `folder_sibling` + the pre-pin `original_unpinned_y` capture — *added: same reasoning as
  ELITEA-2152's AFS — "reappears in the unpinned section" needs a concrete BEFORE/AFTER comparison
  to be checkable as more than a flag flip; live-confirmed this session that the reversal is exact
  within sub-pixel tolerance (folder returns to the SAME Y it started at), which is stronger, more
  diagnostic evidence than "some position below the pinned tier".*
- Step 6's "retains conversations" check requires a REAL conversation inside the folder — *added:
  same reasoning as ELITEA-2152's AFS Step 5.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline matching every sibling test in this file/surface.*

## Cleanup
1. Delete `conv_in_folder` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_pinned`, `folder_sibling` via `conversation_api.delete_folder(id)` — deleting a
   PINNED folder was not previously independently verified anywhere in this digest (only deleting a
   pinned CONVERSATION was, per ELITEA-2149's AFS); this test unpins `folder_pinned` as its own last
   case step before cleanup, so by teardown time it is already unpinned — no new verification gap
   opened here.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle; non-fatal on
   individual cleanup failure (logged, not raised).

## Concrete Handles (discovered during exploration)

Identical handle set to ELITEA-2152's AFS — same surface, same page-object methods, zero new work:

| Element | Testid / attribute | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu "Pin on top"/"Unpin" item | `[data-testid="chat-folder-menu-pin-menuitem"]` | pre-existing, `EliteaAI/EliteaUI@be489cee` (`automation/testids` only; re-verified fresh this session) | `ChatPage.FOLDER_MENU_PIN_ITEM` / `pin_folder_via_menu(folder_id)` — pre-existing, reused verbatim for BOTH directions (same click toggles state). |
| Folder pinned-state attribute | `data-pinned="true"/"false"` on `chat-folder-item-{id}` | same commit as above | `ChatPage.is_folder_pinned(folder_id)` — pre-existing, reused verbatim. |
| Folder row (bounding-box + expand state) | `[data-testid="chat-folder-item-{id}"]`, `data-expanded` | pre-existing | `ChatPage.get_folder_item()` / `is_folder_expanded()` / `expand_folder()` — pre-existing; `expand_folder()` gained an additive `force: bool = False` param this implementation (see ELITEA-2152's AFS). |
| Conversation-inside-folder check | `[data-testid="chat-conversation-item-{id}"]` scoped inside `FOLDER_ITEM` | pre-existing | `ChatPage.is_conversation_in_folder()` — pre-existing, reused verbatim. |

**No new testid work required.**

## Network Behavior
- Folder pin (setup): `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`.
- Folder unpin (case step): SAME endpoint, SAME method — `PATCH .../folder/prompt_lib/{project_id}
  /{folder_id}` → `200 OK` (toggles `meta.is_pinned` back; live-confirmed this session, folder id
  `1091` — request fired on the "Unpin" click, response 200, `data-pinned` observed flipping
  `"true"`→`"false"` immediately after).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. Live-confirmed (MCP exploration + implementer's pytest run), folder id `1091`: pinned (Y=56,
`data-pinned=true`, above unpinned sibling id `1092` at Y=178) → unpin action (`PATCH → 200`) →
`data-pinned` flips `true`→`false`, Y returns to `138` (within sub-pixel tolerance) — the SAME Y it
held before it was ever pinned, and the same relative order vs the sibling as the original pre-pin
baseline. **Corrected during implementation**: `data-expanded` does NOT survive the unpin action
either (same remount fact as ELITEA-2152's pin direction) — settled state is `"false"` post-unpin;
re-expanding (`force=True`) shows conversation `8514` intact throughout the full pin→unpin
round-trip. Not filed as a product defect, same reasoning as ELITEA-2152's AFS.

**Note on exploration technique, not a product defect**: same raw-DOM-click console-warning artifact
already documented in ELITEA-2152's AFS (MCP-only, does not reproduce with the implementation's real
`.click(force=True)` path).

## Blocked Steps
None. All 4 case steps (plus the analyst-added baseline/comparison steps) executed live end-to-end
this session, in the SAME browser session as ELITEA-2152 (pinning then unpinning the same folder,
id `1091`, proving the full round-trip).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: `automation/pages/chat_page.py` — identical reuse list to ELITEA-2152's AFS, including
  the same additive `expand_folder(..., force: bool = False)` parameter that AFS introduces (shared
  by both classes in the one new test file — not duplicated work).
- Test file: **same new file as ELITEA-2152**, `automation/tests/ui/chat/test_pin_folder.py` — a
  `TestUnpinFolderViaContextMenu` class appended alongside `TestPinFolderViaPinOnTop`; zero
  modification to that class's body (mirrors `test_pin_conversation.py`'s
  `TestPinConversationViaPinOnTop` / `TestUnpinConversationViaContextMenu` pairing exactly).
- Menu-item label assertion: read `.text_content()` on `FOLDER_MENU_PIN_ITEM`'s locator, asserting
  `"Unpin"` this time (inverse of ELITEA-2152's `"Pin on top"` assertion).
- Bounding-box comparisons: raw `Locator.bounding_box()` calls in the test body, same idiom as
  ELITEA-2152's AFS and `test_pin_conversation.py`.
- Priority marker: `@pytest.mark.p2` (medium), same mapping as the rest of this surface family.
- Wait strategy: `page.expect_response()` around the folder create `POST`s and BOTH `PATCH`
  requests (setup pin + case-step unpin), mirroring ELITEA-2130's proven-deterministic idiom.
