# Test Case: Chat – Drag and Drop Conversation to a Folder

## Metadata
- **TMS ID**: ELITEA-2142
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium` → `@pytest.mark.p2`,
  same medium→l3/p2 mapping as the ELITEA-2135 sibling AFS)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend; project id resolved from
  `${ELITEA_PROJECT_ID}` — don't hardcode)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN`
  skips explicit Keycloak login
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2143/2144/2145
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-drag-drop`

Cluster-analysed alongside ELITEA-2143 (hover-highlight during drag),
ELITEA-2144 (folder-to-folder move), ELITEA-2145 (folder back to the general
list). All four share the drag-and-drop mechanism
(`src/hooks/chat/useDragAndDrop.js`, `@dnd-kit/core`), but each has genuinely
different steps/assertions — written as four separate AFS files per the
skill's "differ in steps → separate AFS" rule, not a family. Full mechanism
details, live-confirmed handles, and both defects found during this pass are
recorded once in `test-specs/chat-interface/_surface.md` § ELITEA-2142/2143/
2144/2145 — this AFS cites that section rather than repeating it verbatim.

**Two product defects were originally filed during this cluster's analysis**
— see § Known Defects. **AMENDMENT (implementer exploration, this PR):**
#1542 (claimed missing toast for a single-item move) does NOT reproduce live
— corrected via a comment on the issue, and this case's own step 6 hard-
asserts toast presence instead of soft-asserting its absence. #1541
(folder-to-folder drop misresolution, confirmed on ELITEA-2144's scenario)
was flagged as a build-time risk for THIS case's own Today→folder direction;
the build-time check also came back clean (does not reproduce here) — see
§ Automation Hints.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- A conversation exists in a date group (Today/This Week/Older) and a target
  folder exists — test creates its own of each via
  `conversation_api.create_conversation()` / `conversation_api.create_folder()`
  (both pre-existing on `ConversationAPI`, `automation/api/client.py`), not
  relying on shared/ambient state.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — the conversation to drag. `conversation_api.create_conversation(name)`
  — lands in Today by construction (a freshly-created conversation always
  starts ungrouped/Today, matching the `_surface.md` ELITEA-2139/2140
  section's already-documented mechanism).
- **`target_folder`** — the destination folder. `conversation_api.create_folder(name)`.

## Test Steps

1. Navigate to `${BASE_URL}/chat`.
   - **Verify**: `conv_target` is visible under its date-group heading
     (`[data-testid="chat-conversation-group-header-today"]`-scoped
     `CONVERSATION_ITEM`) and `target_folder` is visible in the folder list
     (`FOLDER_ITEM`).
2. Press and hold on `conv_target`'s row; move the pointer in several
   incremental steps toward `target_folder`'s row (see § Automation Hints —
   re-measure the target's bounding box on every step, do not single-jump).
   - **Verify**: the drag activates (`DraggableConversationItem`'s `isDragging`
     — opacity drops to `0.5`; live-observable via a `style` attribute read,
     no dedicated testid needed for this transient state).
3. Continue the gesture onto `target_folder` and release (drop).
   - **Verify**: a real `PUT /elitea_core/conversation/prompt_lib/{project}/{conv_target_id}`
     fires with `{"folder_id": <target_folder_id>}`, resolving `200`.
4. Verify `conv_target` is no longer rendered under any date-group heading.
   - **Verify**: `CONVERSATION_ITEM` for `conv_target_id`, scoped inside the
     top-level date-group/ungrouped container (NOT page-wide — MUI `Collapse`
     keeps a collapsed folder's children DOM-mounted, same trap ELITEA-2135's
     AFS already documents), resolves 0.
5. Expand `target_folder` and verify `conv_target` is inside it.
   - **Verify**: `FOLDER_ITEM`'s `data-expanded` flips `"false"` → `"true"`;
     `CONVERSATION_ITEM` for `conv_target_id`, scoped inside `target_folder`'s
     container, resolves 1.
6. Verify a success toast confirms the move.
   - **AMENDMENT (implementer exploration, this PR — #1542 does NOT
     reproduce, filed in error):** the analyst's source read covered only
     `useDragAndDrop.js`'s OWN `toastSuccess(...)` call (correctly gated
     behind `currentDraggedItems.length > 1` — that is a SEPARATE, additive
     "N conversations moved" aggregate toast for multi-select drags). It
     missed that `handleDragEnd` also calls `await
     onMoveToFolderConversation(conversation, targetFolder)` per dragged
     item, and `onMoveToFolderConversation` itself (in
     `useMoveToFolderConversation.hooks.js`, the SAME hook the "Move to"
     context-menu flow uses) unconditionally fires its own `toastSuccess(...)`
     on a successful move — this call is NOT gated by item count at all.
     Live-confirmed this implementation (headless script + the real test
     run below): a single-conversation drag-and-drop move DOES show
     `Chat moved to "<target_folder.name>" folder successfully`, identical
     to the "Move to" menu's own toast. Assert the case's LITERAL expected
     result (toast shown, exact text) as a normal hard assertion — see
     `ChatPage.toast_message` / `test_move_conversation_to_folder.py`'s
     identical text-assertion pattern. #1542 is corrected via a comment
     (not closed — human disposition) rather than shipped as a
     known-defect soft-assert, per the reverse-masking guard: soft-asserting
     absence here would assert a STALE hypothesis against a working feature.
     **Second technique note (implementer exploration, this PR):** the
     toast's text is CAPTURED at step 3 (immediately after the drop, in the
     same `page.expect_response` block) rather than READ fresh at step 6 —
     live-confirmed the toast auto-dismisses before steps 4-5 (date-group
     removal check + folder-expand) finish running, so a step-6 DOM read
     found no element. The assertion still lands at step 6, matching the
     case's own step order; only the underlying DOM read moved earlier,
     same idiom as `test_move_conversation_to_folder.py`'s toast checks
     (which capture immediately after the triggering click).

## Expected Results
- Dragging `conv_target` onto `target_folder` and releasing moves it
  server-side (`folder_id` set on the conversation).
- The conversation disappears from its date group and appears inside
  `target_folder` once expanded.
- A success toast (`Chat moved to "<target_folder.name>" folder
  successfully`) confirms the move — hard-asserted; see the AMENDMENT
  note under step 6 (#1542 corrected, does not reproduce).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: conversation in date group + folder exist | Both visible | Setup + AFS step 1 | step 1: both visible | asserted |
| 2 Click and hold (drag) the conversation | Drag started | AFS step 2 | step 2: `isDragging` opacity/style transition | asserted |
| 3 Drag toward a folder in the left panel | Target folder becomes visually highlighted | AFS step 2/3 | see ELITEA-2143's own AFS — highlighting is that case's dedicated assertion; this case only needs the drag to REACH the folder, not re-prove the highlight | already-covered *(by ELITEA-2143, once merged — same code path, `DroppableFolderItem.shouldShowDropFeedback`, confirmed live via screenshot this session)* |
| 4 Drop the conversation onto the highlighted folder | Conversation removed from original date group | AFS steps 3-4 | step 3: `PUT` 200 with correct `folder_id`; step 4: scoped 0-count in date-group container | asserted, **with an explicit build-time risk flag** — see § Automation Hints; the sibling scenario (folder-to-folder, ELITEA-2144) hit a confirmed drop-target-misresolution defect (#1541) via the IDENTICAL `handleDragEnd` code path |
| 5 Verify the folder contains the dropped conversation when expanded | Conversation inside folder | AFS step 5 | step 5: `data-expanded` flip + scoped 1-count inside `target_folder` | asserted |
| 6 Verify a success toast confirms the move | Toast shown | AFS step 6 | step 6: hard-asserted presence + exact text (`Chat moved to "<target_folder.name>" folder successfully`) | asserted *(AMENDED — #1542 corrected, does not reproduce; see step 6 note)* |
| Pass/Fail: "Drag and drop moves conversation to folder" | — | steps 3-6 | covered by the rows above | asserted, no known defect blocks or weakens any assertion |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 3 asserts the actual `PUT` request/response, not just the toast —
  *added: the network assertion is the primary, fully-trustworthy
  confirmation signal for this mutation; the toast (step 6) is asserted too
  (AMENDED — #1542 does not reproduce, see step 6) but the network response
  remains the authoritative check for `folder_id` correctness.*
- Step 4 requires a SCOPED (not page-wide) 0-count — *added: same MUI
  `Collapse` trap ELITEA-2135's AFS already documents for the "Move to" menu
  flow; applies identically here since it's the same rendering mechanism.*
- Console/network side-channel checked after every interaction — *added:
  standard side-channel discipline, per every other AFS in this suite.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)` —
   works regardless of current folder membership (same note as ELITEA-2135's
   AFS).
2. Delete `target_folder` via `conversation_api.delete_folder(id)` — run in
   `finally`/independent `try`/`except` per resource
   (`.claude/rules/ui-tests.md` § Test Data Lifecycle), even if a mid-test
   assertion fails.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text
fallback ladder (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Conversation row (draggable) | `[data-testid="chat-conversation-item-{id}"]` | pre-existing, on-`automation/testids` ✓ | `ChatPage.CONVERSATION_ITEM` — confirmed live this pass as the correct drag-source element (dnd-kit `useDraggable` listeners attach to this Box's ancestor chain; pressing on this element and its descendants both work). |
| Folder row (drop target) | `[data-testid="chat-folder-item-{id}"]` | pre-existing, on-`automation/testids` ✓ | `ChatPage.FOLDER_ITEM` — confirmed live as the correct drop-target bounding box for computing drag-gesture coordinates. |
| Date-group heading (scoping container) | `[data-testid="chat-conversation-group-header-{}"]` | pre-existing | `ChatPage.CONVERSATION_GROUP_HEADER` — used to scope the "removed from date group" 0-count check. |
| Success toast | `[data-testid="toast-message"]` | pre-existing, `ChatPage.toast_message` | Generic app-wide toast — this case asserts its PRESENCE + exact text (AMENDED, step 6 — #1542 does not reproduce). |

**No new testid required for THIS case's own steps** — the drop-feedback
highlight testid gap (needed by ELITEA-2143) doesn't block ELITEA-2142's own
assertions, which don't require reading the highlight state.

## Network Behavior
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
  with `{"folder_id": <target_folder_id>}` — fires on drop, confirmed `200`,
  response body's `folder_id` field matches.
- `GET .../folder/prompt_lib/{project_id}?...&grouped=true` refetches after
  the move (standard folder-list refresh pattern, already documented in
  ELITEA-2132's AFS).
- Pre-existing, unrelated: project's `GET /api/v2/secrets/secrets/default/{project_id}`
  `403` on every page load — excluded from "no new console errors" checks
  (documented in every sibling AFS in this suite).

## Known Defects Found During Exploration

- **[CORRECTED — NOT a defect] [elitea-testing-public#1542](https://github.com/EliteaAI/elitea-testing-public/issues/1542)**
  — filed during analysis claiming no success toast for a single-conversation
  drag-and-drop move. **Implementer exploration this PR found the claim
  incorrect**: the analyst's source read covered only `useDragAndDrop.js`'s
  own gated `toastSuccess(...)` call (a SEPARATE multi-select aggregate
  toast), but missed that `handleDragEnd` also calls
  `onMoveToFolderConversation` per item, and THAT hook
  (`useMoveToFolderConversation.hooks.js`, shared with the "Move to" menu
  flow) fires its own toast unconditionally on success. Live-confirmed: a
  single-item drag DOES show `Chat moved to "<folder>" folder successfully`.
  Corrected via a comment on #1542 (left OPEN — human disposition, not
  closed by this implementation). Step 6 now hard-asserts toast presence +
  text, matching the case's literal expected result.
- **[MAJOR] [elitea-testing-public#1541](https://github.com/EliteaAI/elitea-testing-public/issues/1541)**
  — confirmed on the SIBLING scenario (ELITEA-2144, folder-to-folder), not
  independently pristine-confirmed for THIS case's own Today→folder
  direction (see § Automation Hints for why, and the explicit build-time
  check this case owes). **Build-time check result (this PR): does NOT
  reproduce for this direction** — the live PUT resolved with `folder_id`
  correctly set to `target_folder`'s own id. Referenced here, not asserted
  as failing; steps 3-5 assert the case's literal expected behavior with no
  soft-assert tie to #1541.

## Blocked Steps
None. All case steps are executable and fully asserted; no known defect
blocks or weakens any assertion (#1542 corrected — not a defect; #1541 does
not reproduce for this direction).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`
  (`.agents/testing.md`).
- Page object: extend `automation/pages/chat_page.py`. New method needed:
  `drag_conversation_to_folder(conversation_id, folder_id, timeout=10000)` —
  press on `CONVERSATION_ITEM`, move in several incremental
  `mouse.move(..., steps=3-5)` calls toward `FOLDER_ITEM`'s bounding box,
  **re-measuring `FOLDER_ITEM`'s `bounding_box()` on every iteration** (a
  stale captured rect can miss — confirmed live this pass, see
  `_surface.md`), then release. Do NOT reuse `drag_and_drop_file()`'s
  synthetic-`DataTransfer`-`DragEvent` technique (`chat_page.py:2243`) — this
  is a DIFFERENT drag mechanism (`@dnd-kit` `PointerSensor`, real pointer
  events, no OS-level file-drag limitation to work around) and dispatching
  synthetic `DragEvent`s here would NOT trigger the real handlers.
- **Explicit build-time check this case owes** (per the risk flagged in
  § Coverage Map row 4 / `_surface.md`): when this test is first run live
  against a real build, confirm `conv_target` actually lands in
  `target_folder` (not ungrouped). **Result (this PR): does NOT reproduce** —
  `conv_target` landed correctly in `target_folder` (`folder_id` matched),
  confirmed via a real PUT response capture. Steps 3/4/5 assert the case's
  literal expected behavior as written above, with no soft-assert tie to
  #1541 for this direction.
- **Drag gestures require `scroll_into_view_if_needed()` before every
  `bounding_box()` read** (discovered this implementation, not in the
  original AFS): `bounding_box()` is viewport-relative, and this shared DEV
  account's sidebar routinely carries 65+ folders ahead of the conversation
  list, pushing a fresh `conv_target` far below the fold. `page.mouse.move()`
  to an off-screen coordinate silently never reaches the element (the drag
  never activates — no error, just a `wait_for_conversation_dragging()`
  timeout). Both `ChatPage.start_conversation_drag()` and
  `ChatPage.move_drag_over_target()` scroll their target into view first.
- Priority marker: case frontmatter `priority: medium` → `@pytest.mark.p2`
  (matches the ELITEA-2135/2132 sibling mapping — see that AFS's own note on
  the `l`-number vs `p`-marker being different scales).
