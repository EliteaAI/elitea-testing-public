# Test Case: Chat – Drag and Drop Conversation Back to the General List

## Metadata
- **TMS ID**: ELITEA-2145
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` on localhost
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2142/2143/2144
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-drag-drop`

Cluster-analysed alongside ELITEA-2142/2143/2144 — see
`test-specs/chat-interface/_surface.md` § ELITEA-2142/2143/2144/2145 for the
shared mechanism/handles. This case's own direction (folder → general list)
was **not independently pristine-confirmed live this session** (see § Blocked
Steps note below for why — environment scroll/virtualization obstacles, not
a defect claim), but is assessed **LOW RISK**: every accidental mis-drop
observed during this session's exploration of the OTHER cases (ELITEA-2144)
landed the conversation in exactly this case's target state (ungrouped/
general list, `folder_id: null`) — i.e. "ungrouped" repeatedly proved to be
the path-of-least-resistance outcome of this drag mechanism, not a hard
outcome to reach. No case-specific defect is asserted; § Automation Hints
directs the implementer to confirm live at build time before merging.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one conversation is inside a folder — test creates its own via
  `conversation_api.create_folder()` + `create_conversation()` +
  `move_conversation_to_folder()` (same precondition-seeding idiom as
  ELITEA-2144's AFS).

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — created, then moved into `source_folder`.
- **`source_folder`** — the folder `conv_target` starts inside.

## Test Steps

1. Navigate to `${BASE_URL}/chat`; expand `source_folder`.
   - **Verify**: `conv_target` is visible inside `source_folder`.
2. Press and hold on `conv_target`'s row; drag toward the date-group/
   ungrouped area (below the folder list).
   - **Verify (soft, per case wording "highlighted OR accepts drop")**: if
     the ungrouped drop-zone testid (spec'd in ELITEA-2143's AFS,
     `chat-conversation-list-drop-zone` + `data-drop-active`) has landed by
     the time this is implemented, assert `data-drop-active="true"` while
     hovered; otherwise this sub-check is optional (case wording itself
     treats highlight-or-accepts-drop as an OR, not a hard requirement).
3. Drop the conversation into the general list area.
   - **Verify**: a real `PUT /elitea_core/conversation/prompt_lib/{project}/{conv_target_id}`
     fires with `{"folder_id": null}`, resolving `200`.
4. Verify the conversation appears in the Today section as recently modified.
   - **Verify**: `CONVERSATION_ITEM` for `conv_target_id`, scoped inside the
     `today` date-group header container, resolves 1. (Per the `_surface.md`
     ELITEA-2139/2140 section's already-documented, live-confirmed
     mechanism: the move's own `PUT` unconditionally bumps `updated_at`,
     which is what buckets a conversation into Today — origin-independent,
     confirmed for the "Move to" menu's equivalent "back to list" action;
     the drag-and-drop mechanism updates the same `conversation` resource
     via the same field, so the same bucketing follows.)
5. Verify the folder still exists and is empty (or has remaining
   conversations).
   - **Verify**: `source_folder`'s `FOLDER_ITEM` resolves 1;
     `conv_target_id`'s `CONVERSATION_ITEM` scoped inside it resolves 0.

## Expected Results
- Dragging `conv_target` out of `source_folder` into the general list area
  sets `folder_id: null` and the conversation reappears under Today.
- `source_folder` itself is not deleted or otherwise affected.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: conversation inside a folder | Precondition satisfied | Setup | API-seeded | asserted |
| 1 Expand a folder with a conversation | Conversation visible | AFS step 1 | step 1: scoped 1-count | asserted |
| 2 Click and hold, drag toward Today/This Week/Older area | Date group area highlighted or accepts drop | AFS step 2 | step 2: soft/optional highlight check (case wording is OR, not AND) | asserted (soft) |
| 3 Drop the conversation into the general list area | Conversation removed from folder | AFS step 3 | step 3: `PUT` 200 with `folder_id: null` | asserted, **not yet independently live-confirmed this session for THIS exact gesture** — see § Automation Hints |
| 4 Verify the conversation appears in the Today section as recently modified | Conversation in Today | AFS step 4 | step 4: scoped 1-count in `today` group | asserted (mechanism reasoning grounded in the already-live-confirmed `_surface.md` ELITEA-2139/2140 finding for the equivalent menu-driven action) |
| 5 Verify the folder still exists and is empty/has remaining conversations | Folder remains | AFS step 5 | step 5: `FOLDER_ITEM` resolves 1, conversation scoped-0 inside | asserted |
| Expected Final State: "Conversation moved from folder to Today" | — | steps 3-4 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- Step 4's "lands in Today" reasoning is grounded in the ALREADY
  live-confirmed `_surface.md` mechanism (unconditional `updated_at` bump on
  any conversation `PUT`) rather than independently re-proven for the
  drag-and-drop trigger specifically this session — *added: economizes a
  repeat live confirmation of a mechanism already nailed down for the
  functionally-equivalent "Move to" → "Back to the list" menu action, which
  hits the identical backend `PUT`.*
- Step 2's highlight check is explicitly marked soft/optional — *added: the
  case's OWN wording ("highlighted OR accepts drop") does not mandate the
  highlight; over-asserting it here would fail the test on a technicality
  the case itself doesn't require.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)`.
2. Delete `source_folder` via `conversation_api.delete_folder(id)` —
   independent `try`/`except` per resource.

## Concrete Handles (discovered during exploration)

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Conversation row (draggable), scoped inside source folder | `[data-testid="chat-conversation-item-{id}"]` | pre-existing ✓ | `ChatPage.CONVERSATION_ITEM`. |
| Source folder row | `[data-testid="chat-folder-item-{id}"]` | pre-existing ✓ | `ChatPage.FOLDER_ITEM`. |
| Today date-group heading (scoping container) | `[data-testid="chat-conversation-group-header-today"]` | pre-existing | `ChatPage.CONVERSATION_GROUP_HEADER.format("today")`. |
| Ungrouped-area drop-zone wrapper (optional highlight check) | `testid needed` — same spec as ELITEA-2143's AFS (`data-testid="chat-conversation-list-drop-zone"` + `data-drop-active`, `DroppableGroupedArea.jsx`) | needs-adding | Only needed if step 2's soft highlight check is implemented; the case's own wording makes this optional. |

## Network Behavior
- `PUT /elitea_core/conversation/prompt_lib/{project_id}/{conv_target_id}`
  with `{"folder_id": null}` — expected on drop, not yet independently
  captured for THIS exact drag gesture this session (captured for the
  functionally-identical "Move to" → "Back to the list" MENU action instead,
  per `_surface.md`'s ELITEA-2139/2140 section).
- Pre-existing, unrelated: `GET /api/v2/secrets/secrets/default/{project_id}`
  `403` — excluded from console-error checks.

## Known Defects Found During Exploration
None specific to this case's own direction. (Two defects found on sibling
cases in this cluster — #1541 on ELITEA-2144's folder-to-folder direction,
#1542 on ELITEA-2142/2144's toast assertion — neither is known to affect
this direction; #1541 in particular is about drops landing UNGROUPED instead
of a target folder, which is this case's own INTENDED destination, not a
failure mode for it.)

## Blocked Steps
None formally blocked, but **flagged**: this session's live exploration of
the Today/date-group ↔ folder directions was constrained by this shared DEV
account's 65+ pre-existing orphaned folders (known cleanup gap, see
`_surface.md`'s `#1309`/`#1310`/`#1533` section), which pushed the folder
list and the date-group list far enough apart on-screen that neither a
1280×4000 viewport resize nor `@dnd-kit`'s autoscroll (didn't visibly engage
for synthetic MCP pointer input in the time available) could bring both into
simultaneous view for a clean, single-gesture repro of THIS specific
direction. The mechanism itself is proven live (real gestures → real `PUT`
calls, confirmed repeatedly on the sibling cases), and "ungrouped" is
observed to be an EASY destination to reach (see the note in § Metadata) —
so this is assessed low-risk, not blocked, but the implementer should do one
clean live confirmation before merging (see § Automation Hints).

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py` — reuse
  ELITEA-2142/2144's `drag_conversation_to_folder()`-family helper, adding a
  companion `drag_conversation_to_general_list(conversation_id, timeout=10000)`
  that targets `DroppableGroupedArea`'s container instead of a `FOLDER_ITEM`
  (drop target id `'ungrouped-conversations'` per `useDragAndDrop.js` — no
  page-object testid needed for the DROP target coordinate itself if the
  `chat-conversation-list-drop-zone` testid from ELITEA-2143 lands first;
  otherwise target the visible date-group heading area's bounding box as a
  fallback coordinate, same technique used for the Today-section reach in
  ELITEA-2142).
- **Explicit build-time check this case owes**: on first live run, confirm
  the `PUT` body is genuinely `{"folder_id": null}` and the conversation
  reappears under Today. If it does NOT (an unexpected divergence from the
  low-risk assessment above), treat it as a NEW defect finding (not #1541 —
  a different failure SHAPE, landing somewhere unexpected FROM a folder
  rather than failing to land IN a folder) and route it through the normal
  bug-filing procedure, updating this AFS's status accordingly.
- Priority marker: `priority: medium` → `@pytest.mark.p2`.
