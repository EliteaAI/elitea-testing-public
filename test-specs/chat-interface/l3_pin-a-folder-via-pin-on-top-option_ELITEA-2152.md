# Test Case: Chat – Pin a Folder via Pin on Top Option

## Metadata
- **TMS ID**: ELITEA-2152
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium`; same medium→l3/p2 mapping as
  ELITEA-2149's sibling AFS in this same surface family)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project "Private", `projectId=399` — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit
  Keycloak login
- **Analyst**: test-automation-engineer (agent) — combined analyst+implementer slot, batch
  `chat-remaining-w08`
- **Status**: ready-for-automation
- **surface_key**: `chat-folder-context-menu` (same folder dot-menu Pin/Unpin surface
  ELITEA-2121/2130 already added the `chat-folder-menu-pin-menuitem` testid and
  `data-pinned` attribute for; this is the first case whose OWN subject is the pin
  action's position/visibility effects, not incidental setup for a rename case)

## Preconditions (case)
- User is logged in to the Elitea platform.
- At least one unpinned folder exists.

This AFS's own setup satisfies the precondition by seeding a fresh unpinned folder (plus an
unpinned sibling folder and a conversation moved inside the target folder) rather than relying on
ambient shared-DEV-project data — deterministic, and the seeded conversation lets Step 3 ("folder
still shows all its conversations when expanded") be a genuine live check instead of an assumption.

## Why `ready-for-automation`, not `extend-existing`

`test_chat_folder_rename_checkmark_validation.py`'s ELITEA-2130 test already pins a folder via the
SAME `pin_folder_via_menu()`/`chat-folder-menu-pin-menuitem` mechanism, but only as an incidental
SETUP step to reach "a pinned folder exists" — it asserts `data-pinned="true"` once and moves on to
testing RENAME, never checking panel position, the folder's conversations, or the "moved from its
original position" observable this case's own steps ask for. ELITEA-2151 (panel-ordering,
`test_pin_conversation.py`) also pins a folder as part of its 4-tier ordering setup, but only
checks 3 adjacent-tier Y comparisons against conversation rows — it never captures a folder's
BEFORE-pin position to prove it moved, and never touches a folder's own conversations. No existing
test's OWN subject is "pin a folder and verify its position/icon/conversations" — this is new
coverage, landing in a new file (`test_pin_folder.py`) mirroring `test_pin_conversation.py`'s
already-proven pin/unpin pairing structure (ELITEA-2149/2150).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_sibling`** — created first via `conversation_api.create_folder(name)`, stays unpinned
  throughout. Gives Step 4 ("folder no longer in its original position") a stable unpinned
  reference to compare against, and gives Step 1 a deterministic "folder A is above folder B"
  baseline before any pinning happens (live-confirmed this session: a folder created AFTER another
  one renders ABOVE it in the default `sort_by=updated_at&sort_order=desc` list — i.e. most
  recently created/touched first).
- **`folder_target`** — created via `conversation_api.create_folder(name)` AFTER `folder_sibling`,
  so it starts BELOW `folder_sibling` in the unpinned list (live-confirmed baseline this session).
  This is the folder the case's own steps act on.
- **`conv_in_folder`** — created via `conversation_api.create_conversation(name)`, then moved into
  `folder_target` via `conversation_api.move_conversation_to_folder(id, folder_target_id)` — both
  transit/setup, not the case's own subject. Gives Step 3 a real conversation to prove "intact"
  against.

## Test Steps

1. Navigate to Chats. Expand `folder_target` and verify `conv_in_folder` renders inside it (baseline
   — proves the seed is correct before any pin action). Capture `folder_target`'s bounding-box Y
   position (`initial_y`) and confirm `data-pinned="false"`.
   - **Verify**: `chat-folder-item-{folder_target_id}` exists, `data-expanded="true"` after
     `expand_folder()`, contains `chat-conversation-item-{conv_in_folder_id}`; `data-pinned="false"`.
2. Hover `folder_target`, click its 3-dot icon (force-click — REQUIRED even before pinning is
   consistent with the folder row's shared dot-menu mechanism, though the disabled-ancestor gotcha
   specifically affects PINNED folders per ELITEA-2130's AFS; using `force=True` unconditionally
   avoids a state-dependent method signature). Verify the Pin/Unpin item reads **"Pin on top"**
   before clicking it, then click it.
   - **Verify**: `chat-folder-menu-pin-menuitem` text content == `"Pin on top"` pre-click.
3. Verify the folder moved into the pinned section: `data-pinned` flips `"false"` → `"true"`;
   bounding-box Y decreased below `initial_y`; `folder_target` now renders ABOVE `folder_sibling`
   (a direct reversal of the pre-pin order captured in Step 1 — `folder_sibling` was above
   `folder_target` before pinning, live-confirmed this session).
   - **Verify**: `is_folder_pinned(folder_target_id)` is `True`; new Y < `initial_y`; new Y +
     height <= `folder_sibling`'s Y.
4. Verify a pin icon is displayed next to the folder name.
   - **Verify**: `data-pinned="true"` IS the compliant locator for this observable per
     `.agents/testing.md` § Locator policy — the raw `<PinIcon>` `FolderAccordion.jsx` conditionally
     renders in the header has no testid and is source-confirmed driven by the exact same `isPinned`
     boolean the attribute exposes (ELITEA-2121/2130's AFS already established this equivalence); a
     bare icon-presence check is not a stronger observable, just a non-compliant locator for the
     same fact already asserted in Step 3. No separate handle needed — this step is the SAME
     assertion as Step 3's `data-pinned` check, restated because the case enumerates it as its own
     step.
5. Verify the folder still shows all its conversations when expanded.
   - **Verify**: `data-expanded="true"` persists through the pin action WITHOUT re-clicking (live-
     confirmed this session — pinning does not collapse an already-expanded folder); `conv_in_folder`
     still resolves inside `folder_target`'s container post-pin.
6. Verify the folder is no longer in its original position (same observable as Step 3's Y/order
   check, re-asserted per the case's own explicit Step 4 wording — not a new mechanism).
   - **Verify**: new Y != `initial_y` (strictly less); relative order vs `folder_sibling` has
     reversed from Step 1's baseline.

## Expected Results
- Pinning a folder via the dot-menu's "Pin on top" item (`chat-folder-menu-pin-menuitem`, existing
  testid from ELITEA-2121/2130, `PATCH .../folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`)
  moves it into the pinned section, above any unpinned folder it was previously below.
- `data-pinned` on `chat-folder-item-{folder_id}` flips `"false"` → `"true"` — the compliant,
  policy-mandated proxy for "pin icon visible" (raw icon has no testid, is driven by the same
  boolean).
- The folder's expand state and conversation contents are unaffected by pinning — it does not
  collapse, and its conversations remain rendered inside it.
- The folder's rendered position changes measurably (Y decreases; relative order vs a stable
  unpinned sibling reverses) — proving it left its original position, not merely that a flag
  flipped.
- No new console errors beyond the pre-existing, environment-wide `secrets` 403 noise.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: at least one unpinned folder exists | — | Setup | `folder_target` seeded unpinned via API | asserted |
| 1 Navigate to Chats, hover unpinned folder, click 3-dot, click 'Pin on top' | Folder moves to pinned folders section at top | AFS steps 1–3 | step 1: baseline; step 2: menu label + click; step 3: `data-pinned` flip + Y decrease + order reversal vs `folder_sibling` | asserted |
| 2 Verify a pin icon is displayed next to the folder name | Pin icon visible | AFS step 4 | `data-pinned="true"` per Locator policy (raw icon has no testid, same driving boolean) | asserted |
| 3 Verify the folder still shows all its conversations when expanded | Conversations intact | AFS step 5 | `data-expanded="true"` persists; `conv_in_folder` still resolves inside `folder_target` | asserted |
| 4 Verify the folder is no longer in its original position | Folder moved from original position | AFS step 6 | Y != `initial_y`; order vs `folder_sibling` reversed | asserted |
| Expected Final State: "Folder pinned and appears at top with pin icon, conversations intact" | — | steps 3–6 | covered by the rows above | asserted |
| Pass/Fail: "Folder not pinned or conversations lost" (fail condition) | — | steps 3, 5 | `data-pinned`/conversation-presence checks are the direct inverse of this fail condition | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`. All
rows `asserted`. No reverse-masking — no case-text/product drift found for this case (the menu-item
label/set drift from ELITEA-2121/2130/`#1534` doesn't recur here since this case's own text never
enumerates the menu's full item set, only "Pin on top").

### Axis 2 — Analyst additions

- Step 1 captures `initial_y` and confirms the pre-pin `data-pinned="false"` baseline and conversation
  placement BEFORE any pin action — *added: the case's own Steps 2–4 ask to verify "moved",
  "no longer in original position", and "conversations intact" — none of these are checkable without
  a captured BEFORE state; this is the minimum fixture the case's own later steps require, not scope
  creep (same reasoning ELITEA-2151's AFS gives for its own precondition-satisfying setup).*
- `folder_sibling` seeded specifically to give the "moved from original position" observable a
  concrete, live comparison point (order reversal) rather than only a Y-delta on the folder itself —
  *added: a bare "Y decreased" check could pass on any layout jitter; comparing relative order
  against a folder that provably never moves is stronger, more diagnostic evidence, matching the
  same reasoning ELITEA-2149's AFS gives for its adjacent-tier comparisons.*
- Step 5's "conversations intact" check requires a REAL conversation inside the folder, not just
  the empty-state — *added: `conv_in_folder` is seeded and moved in specifically so this step has
  something concrete to lose if the pin action collapsed the folder or dropped its contents; the
  case's own precondition text doesn't specify folder contents, but the case's own Step 3 requires
  them to exist to be checkable at all.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline matching every sibling test in this file/surface.*

## Cleanup
1. Delete `conv_in_folder` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_target`, `folder_sibling` via `conversation_api.delete_folder(id)` — same endpoint
   ELITEA-2151's AFS already independently verified has no pin-state precondition.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle; non-fatal on
   individual cleanup failure (logged, not raised).

## Concrete Handles (discovered during exploration)

| Element | Testid / attribute | Provenance | Notes |
|---|---|---|---|
| Folder dot-menu "Pin on top"/"Unpin" item | `[data-testid="chat-folder-menu-pin-menuitem"]` | pre-existing, `EliteaAI/EliteaUI@be489cee` (`automation/testids` only; NOT yet on `main`, human-cherry-pick pending, per ELITEA-2121/2130's AFS/closure record — RE-VERIFIED this session via fresh `git fetch origin` + `git grep` against both refs) | `ChatPage.FOLDER_MENU_PIN_ITEM` / `pin_folder_via_menu(folder_id)` — both pre-existing, reused verbatim. |
| Folder pinned-state attribute | `data-pinned="true"/"false"` on `chat-folder-item-{id}` | same commit as above | `ChatPage.is_folder_pinned(folder_id)` — pre-existing, reused verbatim. This IS the compliant "pin icon" locator per project policy. |
| Folder row (bounding-box + expand state) | `[data-testid="chat-folder-item-{id}"]`, `data-expanded="true"/"false"` | pre-existing | `ChatPage.get_folder_item(folder_id)` / `is_folder_expanded()` / `expand_folder()` — all pre-existing, reused verbatim. |
| Conversation-inside-folder check | `[data-testid="chat-conversation-item-{id}"]` scoped inside `FOLDER_ITEM` | pre-existing | `ChatPage.is_conversation_in_folder(folder_id, conversation_id)` — pre-existing, reused verbatim. |

**No new testid work required** — every handle this AFS needs already exists and is already wired
into `ChatPage`, entirely from prior sessions' work on this same surface family (ELITEA-2121/2130).

## Network Behavior
- Folder pin: `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`
  (source/live-confirmed, ELITEA-2121/2130's AFS; re-confirmed live this session — folder id `1091`,
  `PATCH .../folder/prompt_lib/399/1091 => [200] OK`).
- Folder create: `POST /elitea_core/folder/prompt_lib/{project_id}` → `201 Created` (setup, not the
  case's own subject).
- Conversation move-to-folder: `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
  with `{"folder_id": ...}` → `200 OK` (setup, pre-existing `conversation_api.move_conversation_to_folder()`).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. Live-confirmed this session, end-to-end, folder id `1091` (`w08_2152target`) against sibling
`1092` (`w08_2152sibling`) with conversation `8514` moved inside: pre-pin Y=138 (below sibling's
Y=97) → pin action (`PATCH → 200`) → `data-pinned` `false`→`true`, Y=56 (now ABOVE sibling's new
Y=178 — a full order reversal), folder stayed `data-expanded="true"` throughout with the
conversation still resolving inside it. Behaves exactly as the case's own steps expect.

**Note on exploration technique, not a product defect**: driving the folder's dot-menu via a raw DOM
`element.click()` (`browser_evaluate`, no `force` option in Playwright MCP) produced 4 transient
React console warnings (`Invalid prop 'expanded'/'in' of type object`, `MUI anchorEl invalid`) not
seen when using a real Playwright `.click(force=True)` — the same distinction ELITEA-2121/2130's AFS
already documented for the disabled-ancestor gotcha. `pin_folder_via_menu()`'s existing
`.click(force=True)` (proper synthetic-event path) does not reproduce these; ELITEA-2130's own test
already runs this exact click pattern with "0 console errors observed". Not re-filed; consistent with
the already-established precedent.

## Blocked Steps
None. All 4 case steps (plus the analyst-added baseline/comparison steps) executed live end-to-end
this session using the real UI dot-menu mechanism (raw-DOM-click for MCP exploration only — the
implementation uses the proven `pin_folder_via_menu()` force-click path).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: `automation/pages/chat_page.py` — **zero new methods needed**; reuse
  `pin_folder_via_menu()`, `is_folder_pinned()`, `get_folder_item()`, `is_folder_expanded()`,
  `expand_folder()`, `is_conversation_in_folder()` (all ELITEA-2121/2130), plus
  `conversation_api.create_folder()` / `create_conversation()` / `move_conversation_to_folder()` /
  `delete_conversation()` / `delete_folder()`.
- Test file: **new** `automation/tests/ui/chat/test_pin_folder.py`, mirroring
  `test_pin_conversation.py`'s structure (ELITEA-2149/2150) — a `TestPinFolderViaPinOnTop` class
  here; ELITEA-2153's `TestUnpinFolderViaContextMenu` class lands in the SAME file (see that AFS).
- Menu-item label assertion: read `.text_content()` on `FOLDER_MENU_PIN_ITEM`'s locator, same idiom
  as ELITEA-2130's AFS ("Unpin" label check) and ELITEA-2149's AFS (conversation "Pin on top" label
  check) — proves the menu's own state-derivation, not just DOM existence.
- Bounding-box comparisons: raw `Locator.bounding_box()` calls in the test body (Playwright
  primitive, not a raw selector) — same idiom `test_pin_conversation.py` already uses directly, no
  page-object wrapper needed.
- Priority marker: `@pytest.mark.p2` (medium), same mapping as ELITEA-2149/2150/2151 in this surface
  family.
- Wait strategy: `page.expect_response()` around the folder create `POST`s and the pin `PATCH`,
  mirroring ELITEA-2130's proven-deterministic folder-pin idiom.
