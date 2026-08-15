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

**Two product defects were found and filed during this cluster's analysis**
— see § Known Defects. One (missing toast for a single-item move, #1542) is
a tail-isolable assertion in THIS case's own steps. The other (folder-to-folder
drop misresolution, #1541) was confirmed on ELITEA-2144's scenario, not this
one — see § Automation Hints for the explicit build-time check this case
owes as a result.

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
   - **Known defect** (see § Known Defects, #1542): source-confirmed that
     `handleDragEnd`'s `toastSuccess(...)` call is gated behind
     `currentDraggedItems.length > 1` — a single-conversation drag NEVER
     shows a toast. Assert the CORRECT (buggy) live behavior —
     `[data-testid="toast-message"]` resolves 0 within a short window after
     the drop — via `expect.soft()` + `# Known defect: #1542`, not the
     case's literal "toast shown" expectation (reverse-masking guard: the
     case text is what's stale here once #1542 is understood, not a license
     to skip the check).

## Expected Results
- Dragging `conv_target` onto `target_folder` and releasing moves it
  server-side (`folder_id` set on the conversation).
- The conversation disappears from its date group and appears inside
  `target_folder` once expanded.
- No success toast appears for this single-item move (known defect #1542,
  soft-asserted — will flip green when #1542 ships a fix).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: conversation in date group + folder exist | Both visible | Setup + AFS step 1 | step 1: both visible | asserted |
| 2 Click and hold (drag) the conversation | Drag started | AFS step 2 | step 2: `isDragging` opacity/style transition | asserted |
| 3 Drag toward a folder in the left panel | Target folder becomes visually highlighted | AFS step 2/3 | see ELITEA-2143's own AFS — highlighting is that case's dedicated assertion; this case only needs the drag to REACH the folder, not re-prove the highlight | already-covered *(by ELITEA-2143, once merged — same code path, `DroppableFolderItem.shouldShowDropFeedback`, confirmed live via screenshot this session)* |
| 4 Drop the conversation onto the highlighted folder | Conversation removed from original date group | AFS steps 3-4 | step 3: `PUT` 200 with correct `folder_id`; step 4: scoped 0-count in date-group container | asserted, **with an explicit build-time risk flag** — see § Automation Hints; the sibling scenario (folder-to-folder, ELITEA-2144) hit a confirmed drop-target-misresolution defect (#1541) via the IDENTICAL `handleDragEnd` code path |
| 5 Verify the folder contains the dropped conversation when expanded | Conversation inside folder | AFS step 5 | step 5: `data-expanded` flip + scoped 1-count inside `target_folder` | asserted |
| 6 Verify a success toast confirms the move | Toast shown | AFS step 6 | step 6: soft-asserted ABSENCE of toast, tied to filed defect #1542 | clarification/known-defect *(case expects a toast; source-confirmed the DnD toast call is gated to multi-item drags only — #1542)* |
| Pass/Fail: "Drag and drop moves conversation to folder" | — | steps 3-5 | covered by the rows above | asserted, with 1 filed defect (#1542) that does not block completion of the CORE move assertion |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 3 asserts the actual `PUT` request/response, not just the toast (the
  toast is unreliable for single items per #1542) — *added: the network
  assertion is the only fully-trustworthy confirmation signal for this
  mutation now that the toast is known-broken for this case's shape.*
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
| Success toast | `[data-testid="toast-message"]` | pre-existing, `ChatPage.toast_message` | Generic app-wide toast — this case asserts its ABSENCE (see step 6 / #1542), not its presence. |

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

- **[MINOR] [elitea-testing-public#1542](https://github.com/EliteaAI/elitea-testing-public/issues/1542)**
  — no success toast for a single-conversation drag-and-drop move
  (`handleDragEnd`'s `toastSuccess(...)` call gated behind
  `currentDraggedItems.length > 1`). Source-confirmed (not just live-observed)
  — see the issue for the exact conditional. Does not block this case's core
  move assertion (steps 3-5); step 6 asserts the correct (buggy) absence via
  `expect.soft()` + `# Known defect: #1542` per the sanctioned-RED /
  analysis-time-entry procedure (`.agents/testing.md` § Merge gate).
- **[MAJOR] [elitea-testing-public#1541](https://github.com/EliteaAI/elitea-testing-public/issues/1541)**
  — confirmed on the SIBLING scenario (ELITEA-2144, folder-to-folder), not
  independently pristine-confirmed for THIS case's own Today→folder
  direction (see § Automation Hints for why, and the explicit build-time
  check this case owes). Referenced here, not asserted as failing.

## Blocked Steps
None. All case steps are executable; step 6 is a known-defect soft-assert,
not a block.

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
  `target_folder` (not ungrouped). If it reproduces the SAME
  drop-target-misresolution behavior as #1541 (folder_id stays null instead
  of becoming `target_folder`'s id), do NOT treat it as a new defect — it is
  the same root cause on the same code path. Tie step 3/4/5's assertions to
  #1541 via `expect.soft()` + `# Known defect: #1541` (same procedure as
  step 6/#1542) rather than reworking the test to force a pass, and note the
  occurrence as a comment on #1541 (same root cause confirmed on a second
  scenario). If it does NOT reproduce (this direction works correctly),
  assert the case's literal expected behavior as written above — no defect
  ticket needed for this direction.
- Priority marker: case frontmatter `priority: medium` → `@pytest.mark.p2`
  (matches the ELITEA-2135/2132 sibling mapping — see that AFS's own note on
  the `l`-number vs `p`-marker being different scales).
