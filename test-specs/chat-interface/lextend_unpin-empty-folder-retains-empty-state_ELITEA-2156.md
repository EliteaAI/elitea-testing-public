# Test Case: Chat – Empty Folder Can Be Unpinned

## Metadata
- **TMS ID**: ELITEA-2156
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, same medium→l3/p2
  mapping as every sibling AFS in this surface family)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, "Private" — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` skips explicit login on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), batch `chat-remaining-w08`
- **Status**: extend-existing
- **surface_key**: `chat-folder-context-menu` (same folder dot-menu Pin/Unpin surface
  ELITEA-2121/2130/2152/2153/2154/2155 already established)

## Extension target
`automation/tests/ui/chat/test_pin_folder.py`
(`TestUnpinFolderViaContextMenu`, ELITEA-2153, **on this batch's own trunk**
`tests/batch-chat-remaining-w08` — commit `63ffa308`, not yet merged to
`origin/automation/base`; merged-target rule permits `extend-existing` to target a
same-batch-trunk spec). **Purely additive** — one new test method
(`test_unpin_empty_folder_retains_empty_state`) in the SAME class
(`TestUnpinFolderViaContextMenu`), same file. No existing method body touched.

## Why `extend-existing`, not `already-covered` or a fresh spec

Mirrors ELITEA-2155's reasoning on the unpin side: ELITEA-2153's existing test
(`test_unpin_folder_via_context_menu`) already proves the unpin mechanism end-to-end (dot-menu
label, `data-pinned` flip, exact position round-trip, `PATCH` 200) against a folder that HAS a
conversation. It cannot exercise the empty-state rendering path across an unpin-triggered remount
— the case's own text ("A pinned empty folder exists" / "still shows an empty state") is a
distinct observable from anything ELITEA-2153's seeded data can prove. This is genuine additional
coverage on the SAME dot-menu/`data-pinned` mechanism ELITEA-2153 already automates — not a
duplicate, not a rewrite. `already-covered` does not apply: ELITEA-2153's spec is only on this
batch's trunk, not yet merged to `origin/automation/base` (`already-covered` may target ONLY a
spec merged to base, per the batch's merged-target rule).

## Live exploration (this session)

Driven live via `pytest` against `localhost:5173` using the real `conversation_api` fixture + the
real UI (no substitution — same idiom as every sibling test in this file; the test method below
WAS the exploration run, executed once, green, before being treated as the final artifact — same
combined analyst+implementer session). Confirmed:

- A freshly-seeded empty folder, pinned via the real UI dot-menu (the already-covered ELITEA-2155
  flow, `PATCH .../folder/prompt_lib/{project_id}/{folder_id}` → `200`), reaches the case's own
  precondition ("a pinned empty folder exists") and re-expanding it (`force=True` — disabled-ancestor
  gotcha) still shows the exact `chat-folder-empty-state` text **"No conversations added"**
  post-pin, matching ELITEA-2155's own finding.
- Unpinning via the SAME dot-menu item (now labelled "Unpin") flips `data-pinned` back to
  `"false"` for an EMPTY folder exactly as ELITEA-2153 already proves for a conversation-bearing
  one — no special-cased failure mode for the zero-conversations case, `PATCH` → `200`.
- Re-expanding the now-unpinned empty folder still shows the exact empty-state text, byte-identical
  across BOTH the pin (setup) and unpin (case) remounts — no blank body, no stale leftover content,
  no error.
- **No new handles, no new page-object methods.** Reuses `pin_folder_via_menu()`,
  `is_folder_pinned()`, `get_folder_item()`, `open_folder_context_menu()`, `expand_folder(force=True)`,
  and `get_folder_empty_state_text()` (ELITEA-2148, reused verbatim as ELITEA-2155 does), plus
  `conversation_api.create_folder()` / `delete_folder()`.
- **0 unexpected console errors** across the full seed → pin (setup) → unpin → re-expand → re-check
  flow (only the pre-existing, environment-wide `secrets/secrets/default` `403` noise, filtered per
  the file's existing `_is_known_secrets_403` idiom).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- A pinned empty folder exists — satisfied by API-seeding a fresh folder with no conversations
  moved into it, then pinning it via the real UI dot-menu flow (the already-covered ELITEA-2155
  mechanism) — deterministic, avoids depending on ambient shared-DEV-project folder contents, same
  reasoning ELITEA-2153's AFS gives for reaching its own "a pinned folder exists" precondition.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_empty`** — a fresh folder created via `conversation_api.create_folder(name)`, with NO
  conversation moved into it, then pinned via `pin_folder_via_menu()` during setup to reach the
  case's own precondition.

## Test Steps
1. Setup reaches the precondition: `folder_empty` seeded unpinned, confirmed empty (baseline —
   proves the seed is correct before any pin/unpin action), then pinned via the real UI dot-menu
   action (the already-covered ELITEA-2155 flow) and re-confirmed empty post-pin.
   - **Verify**: `chat-folder-item-{folder_empty_id}` exists, `data-pinned="false"` pre-pin;
     `get_folder_empty_state_text()` == `"No conversations added"` pre-pin; `PATCH
     .../folder/prompt_lib/{project_id}/{folder_id}` resolves `200` for the setup pin; `data-pinned`
     == `"true"` post-pin; `get_folder_empty_state_text()` still == `"No conversations added"`
     post-pin (re-expanded with `force=True`).
2. Hover `folder_empty`, click its 3-dot icon (force-click — REQUIRED, pinned-folder
   disabled-ancestor gotcha, ELITEA-2130). Verify the Pin/Unpin item reads **"Unpin"** before
   clicking it, then click it.
   - **Verify**: `chat-folder-menu-pin-menuitem` text content == `"Unpin"` pre-click; `PATCH
     .../folder/prompt_lib/{project_id}/{folder_id}` resolves `200`.
3. Verify the folder is removed from the pinned section: `data-pinned` flips `"true"` → `"false"`.
   - **Verify**: `is_folder_pinned(folder_empty_id)` is `False`.
4. Verify the pin icon is no longer visible.
   - **Verify**: `data-pinned="false"` IS the compliant locator for this observable per
     `.agents/testing.md` § Locator policy — same assertion as Step 3, restated because the case
     enumerates it as its own step.
5. Expand the folder and verify it is still empty (this case's own distinguishing subject).
   - **Verify**: `expand_folder(folder_empty_id, force=True)` succeeds (same idiom ELITEA-2153's
     AFS documents for the inverse remount direction) — `get_folder_empty_state_text()` still ==
     `"No conversations added"`, byte-identical to the Step 1 baseline.

## Expected Results
- Unpinning `folder_empty` via the dot-menu's "Unpin" item removes it from the pinned section
  (`data-pinned` flips `"true"`→`"false"`) — same mechanism ELITEA-2153 already automates, now
  proven to also work for a folder with zero conversations.
- After re-expanding the now-unpinned folder, it still shows the exact "No conversations added"
  empty state — no error, no blank body, no stale content — proving the unpin-triggered remount
  does not break the empty-state rendering path, mirroring ELITEA-2155's pin-side finding.
- No unexpected console errors across the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: a pinned empty folder exists | — | Setup | `folder_empty` seeded empty, pinned via real UI dot-menu, empty state re-confirmed post-pin | asserted |
| 1 Navigate to Chats, hover pinned empty folder, click 3-dot, click 'Unpin' | Folder moves to unpinned section | AFS steps 2–3 | step 2: menu label + click + PATCH 200; step 3: `data-pinned` flip | asserted |
| 2 Verify pin icon is no longer visible | Pin icon removed | AFS step 4 | `data-pinned="false"` per Locator policy | asserted |
| 3 Expand the folder and verify it is still empty | Folder shows empty state | AFS step 5 | `get_folder_empty_state_text()` re-checked post-unpin against the Step-1 baseline | asserted |
| Expected Final State: "Empty folder unpinned and still shows empty state" | — | steps 3, 5 | covered by the rows above | asserted |
| Pass/Fail: "Folder cannot be unpinned" (fail condition) | — | steps 3, 5 | `data-pinned` flip + exact empty-state text are the direct inverse of this fail condition | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`. All
rows `asserted`. No reverse-masking — no case-text/product drift found (live behavior matches the
case's own wording exactly: a pinned empty folder unpins normally and retains its empty state).

### Axis 2 — Analyst additions
- Step 1's setup captures a pre-pin empty-state baseline AND re-confirms it post-pin (before any
  unpin action) — *added: the case's own precondition ("a pinned empty folder exists") and Step 3
  ("verify it is still empty") together require a KNOWN-empty starting point that survived the pin
  action too, not just an assumed one; without this the case's own final check would have nothing
  concrete to compare against beyond the literal string — same reasoning ELITEA-2153's AFS gives
  for its own pre-pin baseline capture, extended to also cover the setup pin's own remount.*
- Console/network side-channel checked after the full flow — *added: standard side-channel
  discipline matching every sibling test in this file.*

## Cleanup
1. Delete `folder_empty` via `conversation_api.delete_folder(id)` — same endpoint ELITEA-2151's AFS
   already independently verified has no pin-state precondition.
2. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle; non-fatal on
   individual cleanup failure (logged, not raised) — same idiom as every sibling test method in
   this file.

## Concrete Handles (discovered during exploration)
No new handles. Reuses, all pre-existing (ELITEA-2121/2130/2148/2152/2153):
- `ChatPage.get_folder_item(folder_id)`
- `ChatPage.expand_folder(folder_id, timeout, force=True)`
- `ChatPage.is_folder_pinned(folder_id)`
- `ChatPage.pin_folder_via_menu(folder_id)`
- `ChatPage.open_folder_context_menu(folder_id)`
- `ChatPage.FOLDER_MENU_PIN_ITEM` (`[data-testid="chat-folder-menu-pin-menuitem"]`)
- `ChatPage.get_folder_empty_state_text(folder_id)` (ELITEA-2148, reused verbatim as ELITEA-2155
  already reuses it)

## Network Behavior
- Folder pin/unpin: `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`
  (source/live-confirmed, ELITEA-2121/2130/2152/2153's AFS chain; re-confirmed live this session
  for an EMPTY folder specifically, both directions — no different code path observed).
- Folder create: `POST /elitea_core/folder/prompt_lib/{project_id}` → `201 Created` (setup).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. Live-confirmed end-to-end (real pytest run against the real system): a pinned empty folder
unpins via the identical dot-menu mechanism as a conversation-bearing folder, and its empty-state
text survives both the pin (setup) and unpin (case) remounts unchanged.

## Blocked Steps
None. All 3 case steps (plus the analyst-added setup verification) executed live end-to-end this
session using the real UI dot-menu mechanism and the real `conversation_api` fixture.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new page-object work.
- New test method `test_unpin_empty_folder_retains_empty_state` added to the EXISTING
  `TestUnpinFolderViaContextMenu` class in `test_pin_folder.py`, alongside (not replacing)
  `test_unpin_folder_via_context_menu` — verify additive-only via
  `git diff <base> -- automation/tests/ui/chat/test_pin_folder.py | grep -E '^-[^-]'` (should be
  empty).
- Coverage tag: new method carries its own `@allure.issue(...)` pointing at the ELITEA-2156 case
  file (mirrors ELITEA-2154/2155's own tag-chain mechanic for a new sibling method in an extended
  file).
- Priority marker: `@pytest.mark.p2` (medium), same mapping as every sibling case in this file.
- Reuse the file's existing `_is_known_secrets_403` console filter, `UNPIN_LABEL` /
  `UI_ELEMENT_TIMEOUT` / `NAVIGATION_TIMEOUT` module constants — no new constants needed.
