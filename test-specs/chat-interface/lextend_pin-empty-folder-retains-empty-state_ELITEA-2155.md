# Test Case: Chat – Empty Folder Can Be Pinned

## Metadata
- **TMS ID**: ELITEA-2155
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, same medium→l3/p2
  mapping as every sibling AFS in this surface family)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, "Private" — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` skips explicit login on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), batch `chat-remaining-w08`
- **Status**: extend-existing
- **surface_key**: `chat-folder-context-menu` (same folder dot-menu Pin/Unpin surface
  ELITEA-2121/2130/2152/2153/2154 already established)

## Extension target
`automation/tests/ui/chat/test_pin_folder.py`
(`TestPinFolderViaPinOnTop`, ELITEA-2152, **on this batch's own trunk**
`tests/batch-chat-remaining-w08` — commit `63ffa308`, not yet merged to
`origin/automation/base`; merged-target rule permits `extend-existing` to target a
same-batch-trunk spec). **Purely additive** — one new test method
(`test_pin_empty_folder_retains_empty_state`) in the SAME class (`TestPinFolderViaPinOnTop`),
same file. No existing method body touched.

## Why `extend-existing`, not `already-covered` or a fresh spec

ELITEA-2152's existing test (`test_pin_folder_via_pin_on_top`) already proves the pin
mechanism end-to-end (dot-menu label, `data-pinned` flip, position move, `PATCH` 200) against a
folder that HAS a conversation, and ELITEA-2154's test proves the same mechanism preserves
MULTIPLE conversations. Neither seeds — or could seed, without adding a distinct test — a folder
with ZERO conversations, so neither can catch a bug specific to the empty-state rendering path
(e.g. the empty-state text failing to (re-)render across the pin action's confirmed
remount-between-list-partitions, ELITEA-2152's own documented finding, or the folder's body
crashing/going blank instead of showing "No conversations added"). ELITEA-2155's case text is
explicit and different in subject from every existing test on this surface: "an empty folder"
throughout, and its own Step 3 asks specifically to verify the empty state SURVIVES pinning — a
distinct observable ELITEA-2152/2154 cannot exercise with their seeded data. This is genuine
additional coverage on the SAME dot-menu/`data-pinned` mechanism ELITEA-2152 already automates —
not a duplicate, not a rewrite. `already-covered` does not apply: even setting the data-shape
question aside, ELITEA-2152's spec is only on this batch's trunk, not yet merged to
`origin/automation/base` (`already-covered` may target ONLY a spec merged to base, per the
batch's merged-target rule).

## Live exploration (this session)

Driven live via `pytest` against `localhost:5173` using the real `conversation_api` fixture + the
real UI (no substitution — same idiom as every sibling test in this file; the test method below
WAS the exploration run, executed once, green, before being treated as the final artifact — same
combined analyst+implementer session). Confirmed:

- A freshly-seeded empty folder (`conversation_api.create_folder()`, no conversation moved in)
  renders `data-pinned="false"` and, once expanded, the exact `chat-folder-empty-state` text
  **"No conversations added"** — same idiom/text ELITEA-2148's already-merged test
  (`get_folder_empty_state_text()`) independently established for this project.
- Pinning via the real UI dot-menu (`PATCH .../folder/prompt_lib/{project_id}/{folder_id}` → `200`,
  same mechanism/testid ELITEA-2152 already proves) flips `data-pinned` to `"true"` for an EMPTY
  folder exactly as it does for a conversation-bearing one — no special-cased failure mode for the
  zero-conversations case.
- Re-expanding the pinned empty folder (`expand_folder(..., force=True)` — same disabled-ancestor
  gotcha ELITEA-2152's AFS documents, unconditional on a PINNED folder's whole row) still shows the
  exact empty-state text, byte-identical to the pre-pin baseline — no blank body, no stale
  leftover content, no error.
- **No new handles, no new page-object methods.** Reuses `pin_folder_via_menu()` (implicitly, via
  the same open-menu/click-item idiom `test_pin_folder_via_pin_on_top` uses directly),
  `is_folder_pinned()`, `get_folder_item()`, `open_folder_context_menu()`, `expand_folder(force=True)`,
  and — new to THIS test method but pre-existing on `ChatPage` since ELITEA-2148 —
  `get_folder_empty_state_text()`, plus `conversation_api.create_folder()` / `delete_folder()`.
- **0 unexpected console errors** across the full seed → baseline-empty-check → pin → re-expand →
  re-check flow (only the pre-existing, environment-wide `secrets/secrets/default` `403` noise,
  filtered per the file's existing `_is_known_secrets_403` idiom).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- An empty folder exists in the Chats section — satisfied by API-seeding a fresh folder with no
  conversations moved into it (deterministic, avoids depending on ambient shared-DEV-project
  folder contents — same reasoning ELITEA-2152's AFS gives for its own seed).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_empty`** — a fresh folder created via `conversation_api.create_folder(name)`, with NO
  conversation moved into it. This is the folder the case's own steps act on.

## Test Steps
1. Navigate to `${BASE_URL}/chat`. Expand `folder_empty`; verify it shows the empty state "No
   conversations added" — baseline, before any pin action (analyst addition: the case's own Step 3
   only asks to verify the empty state AFTER pinning; a pre-pin baseline is the minimum fixture
   needed to prove pinning is what's being tested, not that the folder was never populated
   correctly in the first place).
   - **Verify**: `chat-folder-item-{folder_empty_id}` exists, `data-expanded="true"` after
     `expand_folder()`; `get_folder_empty_state_text()` == `"No conversations added"`.
2. Hover `folder_empty`, click its 3-dot icon (force-click, same idiom as every sibling test in
   this file). Verify the Pin/Unpin item reads **"Pin on top"** before clicking it, then click it.
   - **Verify**: `chat-folder-menu-pin-menuitem` text content == `"Pin on top"` pre-click; `PATCH
     .../folder/prompt_lib/{project_id}/{folder_id}` resolves `200`.
3. Verify the folder moved into the pinned section: `data-pinned` flips `"false"` → `"true"`.
   - **Verify**: `is_folder_pinned(folder_empty_id)` is `True`.
4. Verify a pin icon is displayed next to the folder name.
   - **Verify**: `data-pinned="true"` IS the compliant locator for this observable per
     `.agents/testing.md` § Locator policy (raw icon has no testid, same driving boolean as every
     sibling test in this file) — same assertion as Step 3, restated because the case enumerates it
     as its own step.
5. Expand the pinned folder; verify it still shows the exact empty-state text "No conversations
   added" (this case's own distinguishing subject).
   - **Verify**: `expand_folder(folder_empty_id, force=True)` succeeds (same disabled-ancestor
     force-click requirement ELITEA-2152's AFS documents for a PINNED folder's whole row) —
     `get_folder_empty_state_text()` still == `"No conversations added"`, byte-identical to Step
     1's baseline.

## Expected Results
- Pinning `folder_empty` via the dot-menu's "Pin on top" item moves it into the pinned section
  (`data-pinned` flips `"false"`→`"true"`) — same mechanism ELITEA-2152 already automates, now
  proven to also work for a folder with zero conversations.
- After re-expanding the now-pinned folder, it still shows the exact "No conversations added"
  empty state — no error, no blank body, no stale content — proving the pin-triggered remount
  (ELITEA-2152's documented finding) does not break the empty-state rendering path.
- No unexpected console errors across the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: an empty folder exists in the Chats section | — | Setup | `folder_empty` seeded with zero conversations via API | asserted |
| 1 Navigate to Chats, hover empty folder, click 3-dot icon, click 'Pin on top' | Folder moves to pinned section | AFS steps 2–3 | step 2: menu label + click + PATCH 200; step 3: `data-pinned` flip | asserted |
| 2 Verify pin icon is displayed | Pin icon visible | AFS step 4 | `data-pinned="true"` per Locator policy (raw icon has no testid, same driving boolean) | asserted |
| 3 Expand the pinned folder | Shows 'No conversations added' | AFS step 5 | `get_folder_empty_state_text()` re-checked post-pin against the Step-1 baseline | asserted |
| Expected Final State: "Empty folder pinned and shows empty state" | — | steps 3, 5 | covered by the rows above | asserted |
| Pass/Fail: "Empty folder cannot be pinned or shows error" (fail condition) | — | steps 3, 5 | `data-pinned` flip + exact empty-state text are the direct inverse of this fail condition | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`. All
rows `asserted`. No reverse-masking — no case-text/product drift found (live behavior matches the
case's own wording exactly: an empty folder pins normally and retains its empty state).

### Axis 2 — Analyst additions
- Step 1 captures a pre-pin baseline of the exact empty-state text — *added: the case's own Step 3
  asks to verify the empty state AFTER pinning; without a captured BEFORE value, a byte-identical
  re-check after pinning has nothing concrete to compare against beyond the literal string, and a
  captured baseline also confirms the seed itself is correct (an empty folder that never rendered
  the empty state correctly would be a setup bug, not a pin-flow bug) — same reasoning ELITEA-2152's
  AFS gives for its own pre-pin baseline capture.*
- Console/network side-channel checked after the full flow — *added: standard side-channel
  discipline matching every sibling test in this file.*

## Cleanup
1. Delete `folder_empty` via `conversation_api.delete_folder(id)`.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle; non-fatal on
   individual cleanup failure (logged, not raised) — same idiom as every sibling test method in
   this file.

## Concrete Handles (discovered during exploration)
No new handles. Reuses, all pre-existing (ELITEA-2121/2130/2148/2152):
- `ChatPage.get_folder_item(folder_id)`
- `ChatPage.expand_folder(folder_id, timeout, force=True)`
- `ChatPage.is_folder_pinned(folder_id)`
- `ChatPage.open_folder_context_menu(folder_id)`
- `ChatPage.FOLDER_MENU_PIN_ITEM` (`[data-testid="chat-folder-menu-pin-menuitem"]`)
- `ChatPage.get_folder_empty_state_text(folder_id)` (ELITEA-2148, scopes `FOLDER_EMPTY_STATE`
  `[data-testid="chat-folder-empty-state"]` inside the folder's own row)

## Network Behavior
- Folder pin: `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`
  (source/live-confirmed, ELITEA-2121/2130/2152's AFS chain; re-confirmed live this session for an
  EMPTY folder specifically — no different code path observed).
- Folder create: `POST /elitea_core/folder/prompt_lib/{project_id}` → `201 Created` (setup).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. Live-confirmed end-to-end (real pytest run against the real system): an empty folder pins
via the identical dot-menu mechanism as a conversation-bearing folder, and its empty-state text
survives the pin-triggered remount unchanged.

## Blocked Steps
None. All 3 case steps (plus the analyst-added baseline step) executed live end-to-end this
session using the real UI dot-menu mechanism and the real `conversation_api` fixture.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new page-object work.
- New test method `test_pin_empty_folder_retains_empty_state` added to the EXISTING
  `TestPinFolderViaPinOnTop` class in `test_pin_folder.py`, alongside (not replacing)
  `test_pin_folder_via_pin_on_top` / `test_pin_folder_with_multiple_conversations_retains_all` —
  verify additive-only via
  `git diff <base> -- automation/tests/ui/chat/test_pin_folder.py | grep -E '^-[^-]'` (should be
  empty).
- Coverage tag: new method carries its own `@allure.issue(...)` pointing at the ELITEA-2155 case
  file (mirrors ELITEA-2154's own tag-chain mechanic for a new sibling method in an extended file).
- Priority marker: `@pytest.mark.p2` (medium), same mapping as every sibling case in this file.
- Reuse the file's existing `_is_known_secrets_403` console filter, `PIN_ON_TOP_LABEL` /
  `UNPIN_LABEL` / `UI_ELEMENT_TIMEOUT` / `NAVIGATION_TIMEOUT` module constants — no new constants
  needed.
