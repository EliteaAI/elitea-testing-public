# Test Case: Chat – Pinned Folder Retains All Conversations After Pinning

## Metadata
- **TMS ID**: ELITEA-2154
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter: `priority: medium` → `@pytest.mark.p2`, same medium→l3/p2
  mapping as every sibling AFS in this surface family)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, "Private" — treat as `${ELITEA_PROJECT_ID}`, don't hardcode)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` skips explicit login on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), batch `chat-remaining-w08`
- **Status**: extend-existing
- **surface_key**: `chat-folder-context-menu` (same folder dot-menu Pin/Unpin surface
  ELITEA-2121/2130/2152/2153 already established)

## Extension target
`automation/tests/ui/chat/test_pin_folder.py`
(`TestPinFolderViaPinOnTop::test_pin_folder_via_pin_on_top`, ELITEA-2152, **on this batch's own
trunk** `tests/batch-chat-remaining-w08` — commit `63ffa308`, not yet merged to
`origin/automation/base`; merged-target rule permits `extend-existing` to target a same-batch-trunk
spec). **Purely additive** — one new test method
(`test_pin_folder_with_multiple_conversations_retains_all`) in the SAME class
(`TestPinFolderViaPinOnTop`), same file. No existing method body touched.

## Why `extend-existing`, not `already-covered` or a fresh spec

ELITEA-2152's existing test (`test_pin_folder_via_pin_on_top`) already asserts, as its own Step 5,
that a folder's conversation survives pinning — but with exactly **ONE** seeded conversation
(`conv_in_folder`). ELITEA-2154's case text is explicit and different in emphasis: Step 1 says
"Expand a folder with **multiple** conversations and **note conversation names**", and Step 4 says
"Verify **no conversations were lost**" (plural, an aggregate/count claim, not "the one conversation
is still there"). A single-conversation check cannot distinguish "all conversations survive" from
"at least one survives" — e.g. a hypothetical bug that truncates a folder's conversation list to
its first N items after a remount (plausible given the pin action's confirmed remount mechanism,
`_surface.md` § ELITEA-2152/2153) would pass ELITEA-2152's existing assertion but fail ELITEA-2154's
own literal wording. This is genuine additional coverage on the SAME surface/mechanism ELITEA-2152
already automates — not a duplicate, not a rewrite. `already-covered` does not apply: even if the
observable were identical, ELITEA-2152's spec is only on this batch's trunk, not yet merged to
`origin/automation/base` (`already-covered` may target ONLY a spec merged to base, per the batch's
merged-target rule).

## Live exploration (this session)

Driven live via `pytest` against `localhost:5173` using the real `conversation_api` fixture + the
real UI (no substitution — same idiom as ELITEA-2152/2153's own implementation; the multi-
conversation test method below WAS the exploration run, executed once, green, before being treated
as the final artifact — same combined analyst+implementer session). Confirmed:

- **3 distinct conversations, seeded via `conversation_api.create_conversation()` and moved into
  one fresh folder via `conversation_api.move_conversation_to_folder()`, all render inside the
  folder BEFORE pinning** — `is_conversation_in_folder()` true for all 3 ids, and each item's
  `.text_content()` matches its seeded name exactly (proves "note conversation names" is a real,
  checkable per-item fact, not just an id-presence check).
- **After pinning via the real UI dot-menu `PATCH` (same `pin_folder_via_menu()`/
  `chat-folder-menu-pin-menuitem` mechanism ELITEA-2152 already proves) and re-expanding
  (`expand_folder(..., force=True)` — same disabled-ancestor gotcha ELITEA-2152's AFS documents,
  unconditional on a PINNED folder's whole row, not specific to conversation count), ALL 3
  conversations still resolve inside the folder, and every one's name text still matches its
  seeded value exactly** — live-confirmed this session, no truncation, no reordering-induced name
  mismatch, no lost item. Confirms the hypothetical truncation risk named above does NOT occur on
  the real system.
- **No new handles, no new page-object methods.** Reuses `pin_folder_via_menu()`,
  `is_folder_pinned()`, `get_folder_item()`, `expand_folder(force=True)`,
  `is_conversation_in_folder()` (all ELITEA-2121/2130/2152) verbatim, plus
  `conversation_api.create_folder()` / `create_conversation()` / `move_conversation_to_folder()` /
  `delete_conversation()` / `delete_folder()` (all pre-existing).
- **0 unexpected console errors** across the full seed → pin → re-expand → verify flow (only the
  pre-existing, environment-wide `secrets/secrets/default` `403` noise, filtered per the file's
  existing `_is_known_secrets_403` idiom).

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- A folder with multiple conversations exists — satisfied by API-seeding a fresh folder plus 3
  conversations moved into it (deterministic, avoids depending on ambient shared-DEV-project
  folder contents — same reasoning ELITEA-2152's AFS gives for its own single-conversation seed).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`folder_multi`** — a fresh folder created via `conversation_api.create_folder(name)`.
- **`conv_a` / `conv_b` / `conv_c`** — three conversations, each created via
  `conversation_api.create_conversation(name)` with a distinct, deterministic name (timestamp-
  suffixed, matching the file's existing naming idiom), then each moved into `folder_multi` via
  `conversation_api.move_conversation_to_folder(id, folder_multi_id)`. Three (not two) is the
  minimum count that meaningfully exercises "multiple" beyond ELITEA-2152's existing
  single-conversation case while staying cheap to seed/verify/clean up.

## Test Steps
1. Navigate to `${BASE_URL}/chat`. Expand `folder_multi` and note (read) each of `conv_a`/`conv_b`/
   `conv_c`'s rendered names — baseline, proves the seed is correct and each name is legible before
   any pin action.
   - **Verify**: `chat-folder-item-{folder_multi_id}` exists, `data-expanded="true"` after
     `expand_folder()`; all 3 conversation items resolve inside it via `is_conversation_in_folder()`;
     each item's `.text_content()` equals its seeded name exactly.
2. Hover `folder_multi`, click its 3-dot icon (force-click, same idiom as ELITEA-2152), click
   **"Pin on top"**.
   - **Verify**: `data-pinned` flips `"false"` → `"true"` on `chat-folder-item-{folder_multi_id}`
     (folder moved into the pinned section — same mechanism/assertion ELITEA-2152's own Step 3
     already proves; not re-derived here beyond a single flip check, since THIS case's own
     distinguishing subject is the conversations, not the move mechanics).
3. Expand the pinned folder.
   - **Verify**: `expand_folder(folder_multi_id, force=True)` succeeds (same disabled-ancestor
     force-click requirement ELITEA-2152's AFS documents for a PINNED folder's whole row) —
     `data-expanded="true"` after.
4. Verify no conversations were lost — all 3 previous conversations still present, by id AND by
   name.
   - **Verify**: `is_conversation_in_folder()` true for `conv_a`/`conv_b`/`conv_c`; each item's
     `.text_content()` still equals its Step-1-recorded name exactly (catches truncation,
     reordering-induced mismatch, or silent renaming — not just "some 3 items exist").

## Expected Results
- Pinning `folder_multi` via the dot-menu's "Pin on top" item moves it into the pinned section
  (`data-pinned` flips `"false"`→`"true"`) — same mechanism ELITEA-2152 already automates.
- After re-expanding the now-pinned folder, ALL 3 conversations that were present before pinning
  are still present after — by id (`is_conversation_in_folder()`) and by exact name text, proving
  the multi-item aggregate is preserved, not just a single sampled item.
- No unexpected console errors across the flow.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: a folder with multiple conversations exists | — | Setup | `folder_multi` seeded with `conv_a`/`conv_b`/`conv_c` via API | asserted |
| 1 Expand a folder with multiple conversations and note conversation names | Conversations noted | AFS step 1 | baseline: all 3 present + name text captured | asserted |
| 2 Hover folder, click 3-dot icon, click 'Pin on top' | Folder moves to pinned section | AFS step 2 | `data-pinned` flip | asserted |
| 3 Expand the pinned folder | All previous conversations still present | AFS steps 3–4 | step 3: re-expand succeeds; step 4: all 3 ids + names re-verified | asserted |
| 4 Verify no conversations were lost | All conversations intact | AFS step 4 | id + exact-name-text re-check for all 3 | asserted |
| Expected Final State: "All conversations preserved after folder pinning" | — | step 4 | covered by the row above | asserted |
| Pass/Fail: "Conversations lost after pinning" (fail condition) | — | step 4 | direct inverse — any of the 3 missing/renamed fails the assertion | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`. All
rows `asserted`. No reverse-masking — no case-text/product drift found (live behavior matches the
case's own wording exactly: pinning does not lose or rename any conversation).

### Axis 2 — Analyst additions
- 3 conversations (not 1) seeded specifically — *added: the case's own Step 1 says "multiple
  conversations" and Step 4 says "no conversations" (plural); a single-conversation seed (already
  covered by ELITEA-2152) cannot distinguish "all survive" from "at least one survives". This is
  the entire reason this case earns its own test method rather than folding into ELITEA-2152's
  existing single-conversation assertion.*
- Per-item exact-name-text re-check in Step 4, not just id-presence — *added: the case's own Step 1
  explicitly asks to "note conversation names", implying identity is tracked by name, not merely by
  count; a name-blind re-check (e.g. `folder.count() == 3`) would pass on a bug that lost the
  correct items but happened to leave 3 OTHER stale/duplicated rows. Name-scoped-by-id re-check
  catches that.*
- Console/network side-channel checked after the full flow — *added: standard side-channel
  discipline matching every sibling test in this file.*

## Cleanup
1. Delete `conv_a`, `conv_b`, `conv_c` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_multi` via `conversation_api.delete_folder(id)`.
3. Standard `try/finally` per `.claude/rules/ui-tests.md` § Test Data Lifecycle; non-fatal on
   individual cleanup failure (logged, not raised) — same idiom as ELITEA-2152/2153's own test
   methods in this file.

## Concrete Handles (discovered during exploration)
No new handles. Reuses, all pre-existing (ELITEA-2121/2130/2152):
- `ChatPage.get_folder_item(folder_id)`
- `ChatPage.expand_folder(folder_id, timeout, force=True)`
- `ChatPage.is_folder_pinned(folder_id)`
- `ChatPage.pin_folder_via_menu(folder_id)`
- `ChatPage.is_conversation_in_folder(folder_id, conversation_id)`
- `ChatPage.CONVERSATION_ITEM` (`[data-testid="chat-conversation-item-{}"]`, scoped inside the
  folder container) — used directly for `.text_content()` name reads, same idiom
  `is_conversation_in_folder()` itself already uses internally.

## Network Behavior
- Folder pin: `PATCH /elitea_core/folder/prompt_lib/{project_id}/{folder_id}` → `200 OK`
  (source/live-confirmed, ELITEA-2121/2130/2152's AFS chain) — reused, not independently
  re-asserted here since this case's own distinguishing subject is the conversation aggregate, not
  the pin mechanics.
- Folder create: `POST /elitea_core/folder/prompt_lib/{project_id}` → `201 Created` (setup).
- Conversation create: `POST /elitea_core/conversation/prompt_lib/{project_id}` → `201 Created`
  (setup, ×3).
- Conversation move-to-folder: `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}`
  with `{"folder_id": ...}` → `200 OK` (setup, ×3).
- Pre-existing, unrelated: project 399's `secrets/secrets/default` `403` on every page load —
  excluded from "no new console errors" checks, same as every sibling AFS in this suite.

## Known Defects Found During Exploration
None. Live-confirmed end-to-end (real pytest run against the real system): all 3 seeded
conversations, each with a distinct name, survive the pin action and re-expand with their names
and ids unchanged. No truncation, no reordering-induced mismatch, no lost item.

## Blocked Steps
None. All 4 case steps executed live end-to-end this session using the real UI dot-menu mechanism
(`pin_folder_via_menu()`'s proven force-click path) and the real `conversation_api` fixture.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`. Zero new page-object work.
- New test method `test_pin_folder_with_multiple_conversations_retains_all` added to the EXISTING
  `TestPinFolderViaPinOnTop` class in `test_pin_folder.py`, alongside (not replacing)
  `test_pin_folder_via_pin_on_top` — verify additive-only via
  `git diff <base> -- automation/tests/ui/chat/test_pin_folder.py | grep -E '^-[^-]'` (should be
  empty).
- Coverage tag: new method carries its own `@allure.issue(...)` pointing at the ELITEA-2154 case
  file (mirrors ELITEA-2150/2151's own tag-chain mechanic for a new sibling method in an extended
  file — this is a NEW method, not an insertion into the existing method body, so no in-body tag
  list to append to).
- Priority marker: `@pytest.mark.p2` (medium), same mapping as every sibling case in this file.
- Reuse the file's existing `_is_known_secrets_403` console filter and `UI_ELEMENT_TIMEOUT` /
  `NAVIGATION_TIMEOUT` module constants — no new constants needed.
