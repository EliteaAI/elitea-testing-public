# Test Case (family): Chat – Pin on Top Disabled Inside a Folder, Enabled After Moving Out

## Metadata
- **TMS IDs**: ELITEA-2157 ("Chat – Conversation Inside a Folder Cannot Be Pinned Separately"),
  ELITEA-2158 ("Chat – Pin Conversation Inside Folder by Moving It Out First")
- **family_afs**: true — ELITEA-2158's own Step 1 ("verify 'Pin on top' is greyed out for
  conversation inside folder") IS ELITEA-2157's entire subject; ELITEA-2158 then continues the
  SAME live conversation through "Move to" > "Back to the list" and pins it. One continuous live
  flow honestly satisfies both cases' full Pass/Fail criteria — not a parameter-table variant pair
  (the two cases don't share identical steps end-to-end), but a genuine shared-mechanism family:
  ELITEA-2157 asserts the DISABLED half of the `disabled: !isPinned && !!conversation.folder_id`
  rule, ELITEA-2158 asserts the SAME rule's ENABLED half plus the resulting pin action, on the same
  conversation, in one session — reconfirmed live this pass, matching the digest's own framing
  ("reconfirmed here from the OTHER side") under `_surface.md` § ELITEA-2136/2138/2139/2140/2141.
- **Priority**: l3 for both (case frontmatter: `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV
  backend; project id 399, Private project)
- **User set**: `${TEST_USER}` — dev-auth on localhost
- **Analyst**: test-automation-engineer (combined analyst+implementer), chat-remaining-w09
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-context-menu`

## Live exploration (this session, both case IDs)

Reused an EXISTING ambient in-folder conversation (`W08_2152_conv seed message`, id `8514`, inside
folder `w08_2152target`/id `1091` — leftover fixture from a prior wave's session, same "leftover
exploration data" pattern already documented in `_surface.md` § ELITEA-2146/2147/2148) to
live-confirm the mechanism cheaply before committing to a fresh-seeded implementation:

1. Hovered it, opened its 3-dot context menu — live snapshot showed exactly 6 items:
   `Rename, Move to, Playback, Duplicate, Pin on top [disabled], Delete`. The `chat-conversation-
   menu-pin-menuitem` testid IS present (rendered regardless of disabled state — confirmed by
   reading `DotMenu.jsx`'s `BasicMenuItem`: `data-testid={testId ? \`${testId}-menuitem\` :
   undefined}` is set unconditionally, `disabled={disabled}` is a separate MUI `MenuItem` prop),
   matching the already-documented `disabled: !isPinned && !!conversation.folder_id` rule
   (`ConversationItem.jsx` line 260) — reconfirmed live, not just source-read.
2. Clicked "Move to" → "Back to the list" (`chat-move-to-back-to-list-menuitem`) — conversation
   moved to the "Today" date group (same mechanism ELITEA-2139/2140's AFS already documents:
   `updated_at` unconditionally refreshed server-side).
3. Re-hovered the SAME conversation (now un-foldered), re-opened its 3-dot menu — "Pin on top" now
   rendered WITHOUT `[disabled]`, a normal clickable `menuitem` with a `ref`.
4. Clicked "Pin on top" — the conversation moved into the pinned section (rendered directly after
   the pinned folder, ahead of the unpinned/date-grouped list), matching ELITEA-2149's
   already-covered pin mechanism exactly.
5. `browser_console_messages(level="error")` across the whole sequence: 0 errors, 0 warnings beyond
   the pre-existing baseline warning already present at page load (unrelated to this flow).

**Zero product defects found.** Both cases' mechanisms work exactly as cased, end to end, on the
real system.

## Preconditions
- User logged in (`${TEST_USER}` / dev-auth on localhost).
- A folder with at least one conversation inside it exists — test creates its own
  (API-seeded folder + conversation, then API-moved into the folder — mirrors ELITEA-2139/2140's
  own setup primitive, real API call, not the tested action; the case names no required mechanism
  for reaching "conversation inside a folder").

## Test Data
- **`folder`** — via `conversation_api.create_folder(name)`.
- **`conv_target`** — via `conversation_api.create_conversation(name)`, then
  `conversation_api.move_conversation_to_folder(conv_target_id, folder_id)` (setup — reaches the
  "conversation inside a folder" precondition; not the action under test).

## Test Steps (one continuous flow, shared by both case IDs)

1. Navigate to Chats, expand `folder` (`expand_folder()`); verify `conv_target` renders inside it.
   - **Verify**: `folder`'s `data-expanded` is `"true"`; `is_conversation_in_folder(folder_id,
     conv_target_id)` is `True`.
2. Hover `conv_target`, click its 3-dot icon (`open_conversation_context_menu()`).
   - **Verify**: context menu mounts, `get_open_conversation_menu_item_count()` is 6 (the
     in-folder set — `Rename, Move to, Playback, Duplicate, Pin on top, Delete` — one MORE than the
     flat-list 5-item set ELITEA-2114/2149 document, per `_surface.md`'s own flag on this).
3. Verify "Pin on top" is disabled. — **[ELITEA-2157 steps 1–2]**
   - **Verify**: `get_conversation_menu_item("pin")` resolves 1 element with `aria-disabled="true"`
     (MUI's own `MenuItem disabled` rendering — the testid itself is present regardless, per source
     read above; this is an attribute check on an already testid-selected element, not a new
     locator).
4. Attempt to click the disabled "Pin on top" item (forced click — a plain click would time out
   waiting for the element to become actionable, which is itself part of the proof). — **[ELITEA-2157
   step 3]**
   - **Verify**: no `POST/DELETE .../pin/prompt_lib/...` request fires (MUI's `ButtonBase` guards
     `onClick` internally when `disabled` — confirmed no network side effect); `conv_target` remains
     `data-pinned="false"` (or attribute absent — see § Concrete Handles) and its `chat-pin-icon`
     count stays `0`.
5. Verify `conv_target` is still inside `folder` and was never pinned. — **[ELITEA-2157 step 4]**
   - **Verify**: `is_conversation_in_folder(folder_id, conv_target_id)` is still `True`;
     `is_conversation_pinned(conv_target_id)` is `False`.
6. Close the menu, re-open it, click "Move to" (`open_move_to_submenu()`, with the known-defect
   retry — #1117, same as ELITEA-2135/2137/2138/2139/2140), click "Back to the list"
   (`select_move_to_back_to_list()`). — **[ELITEA-2158 step 2]**
   - **Verify**: `PUT .../conversation/prompt_lib/{project_id}/{conv_id}` resolves `200` with body
     `folder_id: null`; success toast reads `Chat moved to ungrouped area successfully` (same
     mechanism ELITEA-2139/2140 already assert).
7. Verify `conv_target` now renders in the "Today" date group.
   - **Verify**: `is_conversation_in_group(conv_target_id, "today")` is `True`.
8. Hover `conv_target` (now un-foldered), click its 3-dot icon; verify "Pin on top" is now enabled
   and clickable. — **[ELITEA-2158 steps 3–4]**
   - **Verify**: `get_conversation_menu_item("pin")` resolves 1 element with `aria-disabled` NOT
     `"true"` (either absent or `"false"`); label text reads exactly `"Pin on top"` (not yet
     "Unpin" — same pre-click label check ELITEA-2149's AFS already establishes).
9. Click "Pin on top" (`click_conversation_menu_item("pin")`). — **[ELITEA-2158 step 5]**
   - **Verify**: `conv_target` moves to the pinned section — `is_conversation_pinned(conv_target_id)`
     is `True`; `get_pin_icon(conv_target_id)` resolves exactly 1, visible (0→1 transition, same
     discipline ELITEA-2149's AFS applies); `conv_target`'s bounding-box Y renders above the "Today"
     heading's Y (reusing the exact assertion shape ELITEA-2149's already-merged test uses).

## Expected Results
- Inside a folder, "Pin on top" renders present-but-DISABLED (not absent) in the context menu; a
  forced click on it has no effect — the conversation stays in the folder, unpinned.
- After "Move to" → "Back to the list" moves the conversation out of the folder, "Pin on top"
  becomes enabled; clicking it pins the conversation into the pinned section with a pin icon, above
  the unpinned list — the same already-covered ELITEA-2149 pin mechanism, now reached via a
  different precondition path.

## Coverage Map

### Axis 1 — Case coverage

#### ELITEA-2157

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Preconditions: logged in, folder with ≥1 conversation | — | Setup | API-seeded folder + move | asserted |
| 1 Navigate to Chats, expand folder, hover conv, click 3-dot | Context menu visible | AFS steps 1–2 | step 2: menu mounts, 6-item count | asserted |
| 2 Verify 'Pin on top' option is greyed out / disabled | Pin on top is disabled | AFS step 3 | step 3: `aria-disabled="true"` | asserted |
| 3 Attempt to click the greyed out Pin on top option | Click has no effect | AFS step 4 | step 4: no network side effect, `data-pinned` stays false, pin icon stays 0 | asserted |
| 4 Verify the conversation is not pinned and remains inside the folder | Conversation stays in folder | AFS step 5 | step 5: still `is_conversation_in_folder` True, `is_conversation_pinned` False | asserted |
| Expected Final State: "Conversations inside folders cannot be pinned directly" | — | steps 3–5 | covered by the rows above | asserted |
| Pass/Fail: "All steps complete without errors" / "Pin on top works for conversations inside folders" (fail condition) | — | all steps | console-check (Axis 2) + step 4/5 | asserted, 0 console errors across all repro runs |

#### ELITEA-2158

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Expand folder, verify 'Pin on top' greyed out for conv inside | Pin on top disabled | AFS steps 1–3 (same mechanism as ELITEA-2157) | step 3: `aria-disabled="true"` | asserted |
| 2 Click Move to, select 'Back to the list' | Conversation moves to Today | AFS steps 6–7 | step 6: PUT 200 + toast; step 7: in Today group | asserted |
| 3 Hover conversation in Today, click 3-dot icon | Context menu visible | AFS step 8 | step 8: menu re-opens | asserted |
| 4 Verify 'Pin on top' is now active and clickable | Pin on top enabled | AFS step 8 | step 8: `aria-disabled` not `"true"`, label `"Pin on top"` | asserted |
| 5 Click 'Pin on top' | Conversation moves to pinned section with pin icon | AFS step 9 | step 9: `is_conversation_pinned` True, pin icon 0→1, Y-position above Today heading | asserted |
| Expected Final State: "Conversation moved out of folder and then successfully pinned" | — | steps 6–9 | covered by the rows above | asserted |
| Pass/Fail: "Fail: Pin on top still not available after moving out" | — | AFS step 8 | explicit enabled-state assertion | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
- Step 2's 6-item menu count for an in-folder conversation — *added: confirms the case's own
  "Context menu visible" claim goes further than presence — the in-folder item SET itself
  (`Duplicate` present, `Pin on top` present-but-disabled) differs from the flat-list 5-item set
  ELITEA-2114/2149 already assert, and no prior test in this suite encodes the in-folder set (flagged
  as a gap in `_surface.md` § ELITEA-2136/2138/2139/2140/2141 — this AFS closes it).*
- Step 4's network-side-effect check on the disabled click — *added: "click has no effect" (case
  text) is asserted at the mechanism level (no mutation request fires), not just "the UI still
  looks the same after 1 second" — a stronger, more durable proof than a pure DOM-state comparison
  alone.*
- Step 8's pre-click label-text check (`"Pin on top"`, not yet `"Unpin"`) — *added: same discipline
  ELITEA-2149's AFS already applies to its own step 1, confirming the state-carrying label design is
  in its expected pre-pin state after the un-foldering, not just that a click succeeds.*
- Console/network side-channel checked after every interaction — *added: standard side-channel
  discipline; confirmed 0 console errors across the live repro this pass.*

## Cleanup
`try`/`finally`, independent per resource:
1. `conversation_api.delete_conversation(conv_target_id)` — deleting a pinned conversation was
   already live-verified to work identically to an unpinned one (ELITEA-2149's AFS).
2. `chat.delete_folder_via_menu(folder_id)` (falls back to `delete_folder_via_api()` per #1309).

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| "Pin on top"/"Unpin" context-menu item | `[data-testid="chat-conversation-menu-pin-menuitem"]` | pre-existing, on-`automation/testids` ✓ (ELITEA-2114) | `get_conversation_menu_item("pin")`. Testid renders unconditionally (source-confirmed, `DotMenu.jsx`'s `BasicMenuItem`); `disabled` is a separate MUI prop read via `aria-disabled`. |
| In-folder disabled state | `aria-disabled="true"` on the same menuitem element | n/a — native MUI `MenuItem disabled` rendering, no testid needed | Attribute check on the already-testid-selected locator; no new locator added. |
| Folder item / expand state | `[data-testid="chat-folder-item-{id}"]`, `data-expanded` | pre-existing (ELITEA-2132) | Reused verbatim via `expand_folder()`/`get_folder_item()`. |
| "Move to" → "Back to the list" | `[data-testid="chat-move-to-back-to-list-menuitem"]` | pre-existing (ELITEA-2135's addition, first live caller ELITEA-2139/2140) | Reused via `select_move_to_back_to_list()`. |
| Pinned-state attribute | `data-pinned="true"/"false"` on `chat-conversation-item-{id}` | pre-existing (ELITEA-2149's addition) | Reused via `is_conversation_pinned()`. |
| Pin icon | `[data-testid="chat-pin-icon"]`, scoped inside `chat-conversation-item-{id}` | pre-existing (ELITEA-2149's addition) | Reused via `get_pin_icon()`. |

**No new testids needed for either case.** All handles already exist and are provisioned; no new
page-object METHOD is needed either — every interaction/verification composes pre-existing
`ChatPage` methods (`expand_folder`, `is_conversation_in_folder`, `open_conversation_context_menu`,
`get_conversation_menu_item`, `open_move_to_submenu`, `select_move_to_back_to_list`,
`is_conversation_in_group`, `is_conversation_pinned`, `get_pin_icon`,
`click_conversation_menu_item`).

## Network Behavior
- Disabled-click attempt (AFS step 4): NO `POST/DELETE .../pin/prompt_lib/{project_id}/conversation/
  {conversation_id}` fires — live-confirmed via MUI's internal `disabled` guard on `ButtonBase`'s
  click handler (source-read, `@mui/material`'s own `MenuItem`/`ButtonBase` implementation, not
  EliteaUI-specific code).
- "Back to the list" (AFS step 6): `PUT .../conversation/prompt_lib/{project_id}/{conv_id}` → `200`,
  body `folder_id: null` (same mechanism ELITEA-2139/2140 already document).
- Successful pin (AFS step 9): `POST /pin/prompt_lib/{project_id}/conversation/{conversation_id}`
  (same mechanism ELITEA-2149 already documents) — not independently network-asserted here either,
  same rationale as ELITEA-2149's AFS (UI-state assertions are sufficient; the optimistic-update
  hook reverts UI state on a failed request).
- Pre-existing, unrelated: `secrets/secrets/default` `403` noise on every page load — excluded, same
  as every sibling AFS.

## Known Defects Found During Exploration
None. Both cases' mechanisms work exactly as cased, end to end, live-confirmed this pass (0 console
errors). Not affected by the "Move to" activation-gesture defect (#1117) beyond the already-documented
workaround (retry-click via `open_move_to_submenu()`), which every sibling AFS in this cluster
already applies identically.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: `automation/pages/chat_page.py` — no new locators, no new methods. Compose the
  methods listed in § Concrete Handles.
- **One continuous test method**, not two — ELITEA-2158's own precondition (step 1) IS ELITEA-2157's
  entire subject; running them as a single live flow on ONE seeded conversation avoids re-deriving a
  second "conversation inside a folder" fixture purely to re-prove a fact the SAME test already
  proved a few lines earlier. Tag with two `@allure.issue` decorators (one per TMS ID), same
  established pattern as ELITEA-2139/2140's family test in
  `automation/tests/ui/chat/test_move_conversation_to_folder.py::TestMoveConversationBackToList`.
- Natural home: `automation/tests/ui/chat/test_pin_conversation.py` (new class alongside the existing
  `TestPinConversationViaPinOnTop`/`TestUnpinConversationViaContextMenu`) — same file's existing
  imports (`ChatPage`, `_is_known_secrets_403`, timeout constants, `PIN_ON_TOP_LABEL`) are directly
  reusable; this is a NEW class/test, not a modification of either existing test body (additive-only
  contract holds trivially — nothing existing changes).
- The forced-click-on-disabled-item step (AFS step 4) needs `force=True` on the click — a plain
  `.click()` on a `disabled`/`aria-disabled="true"` MUI item will time out waiting for it to become
  actionable, which is itself consistent with "click has no effect" but doesn't let the test proceed
  to assert the network/state side of it. Use `page.expect_response` with a SHORT timeout and assert
  it raises (no request fires) rather than asserting a positive absence over an open-ended wait.
- Priority marker: `@pytest.mark.p2` (see ELITEA-2135's AFS note on the l3/p2 mapping).
