# Test Case: Chat – Drag and Drop Conversation Highlights Target Folder on Hover

## Metadata
- **TMS ID**: ELITEA-2143
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l3 (case frontmatter `priority: medium` → `@pytest.mark.p2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — `auth_state`/`VITE_DEV_TOKEN` on localhost
- **Analyst**: qa-engineer (agent) — cluster dispatch with ELITEA-2142/2144/2145
- **Status**: ready-for-automation
- **surface_key**: `chat-conversation-drag-drop`

Cluster-analysed alongside ELITEA-2142/2144/2145 — see
`test-specs/chat-interface/_surface.md` § ELITEA-2142/2143/2144/2145 for the
shared mechanism/handles this AFS builds on. This case's own assertion (the
dashed-border hover highlight) is DISTINCT from the others and was
**live-confirmed working** via screenshot evidence during this pass
(`.playwright-mcp/w07-mid-drag-hover-folderB.png`) — no defect found for this
case specifically.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- One conversation and at least two folders exist — test creates its own via
  `conversation_api.create_conversation()` / `create_folder()` ×2.

## Test Data

### generate-per-test (created via API in setup, cleaned up in teardown)
- **`conv_target`** — the conversation to drag.
- **`folder_a`**, **`folder_b`** — two candidate drop targets.

## Test Steps

1. Navigate to `${BASE_URL}/chat`; begin dragging `conv_target`.
   - **Verify**: drag activates (`isDragging` opacity transition on
     `CONVERSATION_ITEM`).
2. Drag over `folder_a`, then over `folder_b`, one at a time (pause on each
   with several incremental `mouse.move()` steps, re-measuring each folder's
   bounding box before the final approach — see § Automation Hints).
   - **Verify** (per folder, while hovered): the folder's drop-zone wrapper
     shows `data-drop-active="true"` (see § Concrete Handles — **testid
     needed** on this element) — live-confirmed via screenshot this pass:
     a `2px dashed` primary-color border + subtle background tint renders
     around the hovered folder (`DroppableFolderItem`'s
     `shouldShowDropFeedback` overlay).
3. Move away from `folder_a` (toward `folder_b`) and verify its highlight is
   removed.
   - **Verify**: `folder_a`'s drop-zone wrapper reverts to
     `data-drop-active="false"` once the pointer is no longer over it.
4. Drop the conversation on `folder_b`.
   - **Verify**: the highlight on `folder_b` disappears (drag ends,
     `isDragging`/`isOver` both clear); `PUT` fires with `folder_id` reflecting
     the drop. (Whether it resolves to `folder_b`'s own id or is affected by
     the #1541 misresolution defect is exactly ELITEA-2144's own concern, not
     re-asserted here — this case's own scope is the HOVER highlight, not the
     drop outcome. If reused as a transit step, note the #1541 risk per
     ELITEA-2142/2144's AFS.)

## Expected Results
- Each folder shows the dashed-border highlight while the dragged
  conversation hovers over it, and loses it when the pointer moves away.
- Dropping ends the drag and removes all highlights.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: conversation + ≥2 folders exist | Both visible | Setup | API-seeded | asserted |
| 1 Begin dragging a conversation from Today | Drag started | AFS step 1 | step 1: `isDragging` transition | asserted |
| 2 Drag over different folders one at a time | Each folder highlighted (dashed border) when hovered | AFS step 2 | step 2: `data-drop-active="true"` per folder, screenshot-confirmed live this pass | asserted |
| 3 Move away from a folder, verify highlight removed | Highlight removed | AFS step 3 | step 3: `data-drop-active="false"` reverts | asserted |
| 4 Drop on a desired folder | Conversation moved; highlight disappears | AFS step 4 | step 4: highlight clears; drop mechanism itself is ELITEA-2144's own scope | asserted (highlight-clear only) / out-of-scope (drop-outcome correctness — belongs to ELITEA-2144) |
| Expected Final State: "Folder highlighting works during drag" | — | steps 2-3 | covered by the rows above | asserted |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions

- The highlight is asserted via a NEW `data-drop-active` attribute (state via
  data-attribute, not a state-switched testid — `.agents/testing.md` §
  Locator policy) rather than a screenshot/visual diff — *added: a stable,
  scriptable assertion is required; the screenshot evidence from this pass
  proves the CSS effect exists, but a shipped test needs a DOM-readable
  signal, hence the testid-needed spec below.*
- Step 4's drop OUTCOME (does the conversation land in the right folder) is
  explicitly marked out-of-scope for THIS case — *added: avoids duplicating
  ELITEA-2144's own assertion and avoids this case inheriting the #1541
  defect risk it doesn't need to carry.*

## Cleanup
1. Delete `conv_target` via `conversation_api.delete_conversation(id)`.
2. Delete `folder_a`, `folder_b` via `conversation_api.delete_folder(id)` —
   independent `try`/`except` per resource, run even if a mid-test assertion
   fails.

## Concrete Handles (discovered during exploration)

Locator policy on this project is **testid-only** — no role/label/text
fallback ladder (`.agents/testing.md` § Locator policy).

| Element | Testid handle | Provenance | Notes |
|---|---|---|---|
| Conversation row (draggable) | `[data-testid="chat-conversation-item-{id}"]` | pre-existing ✓ | `ChatPage.CONVERSATION_ITEM`. |
| Folder row (drop target, for coordinates) | `[data-testid="chat-folder-item-{id}"]` | pre-existing ✓ | `ChatPage.FOLDER_ITEM`. |
| **Folder drop-zone wrapper (hover-highlight state)** | `testid needed`: add `data-testid="chat-folder-drop-zone-{folder_id}"` (dynamic template, `.agents/testing.md`'s dynamic-testid pattern) **+** `data-drop-active` boolean attribute reflecting `DroppableFolderItem`'s `shouldShowDropFeedback` (`isOver && isActive && isValidDropTarget`) | needs-adding | Add on the EXISTING outer `ref={setNodeRef}` `Box` in `DroppableFolderItem.jsx` (one level above the pre-existing `chat-folder-item-{id}` testid) — zero new DOM node, pure attribute addition to an already-rendered element. Do NOT put the testid on the conditionally-mounted anonymous overlay `Box` (mounts/unmounts with drag state — wrong node for an identity testid). Live-confirmed via screenshot the CSS effect fires correctly; only the scriptable-assertion hook is missing. |
| **Ungrouped/date-group drop-zone wrapper** | `testid needed`: `data-testid="chat-conversation-list-drop-zone"` (static, singular) **+** `data-drop-active` on `DroppableGroupedArea.jsx`'s existing outer ref `Box`, same shape as the folder one above | needs-adding | Same mechanism (`shouldShowDropFeedback`), not exercised by THIS case's own steps (2143 only drags over folders) — documented for ELITEA-2145's benefit, which mentions "Date group area highlighted or accepts drop" as a softer (not strictly required) expectation. |

## Network Behavior
- No new network calls specific to hover — highlight is a pure client-side
  `@dnd-kit` collision-state effect, no request fires until drop (step 4,
  same `PUT` as ELITEA-2142/2144).
- Pre-existing, unrelated: `GET /api/v2/secrets/secrets/default/{project_id}`
  `403` on every page load — excluded from console-error checks.

## Known Defects Found During Exploration
None for this case specifically — the highlight mechanism itself is
confirmed working correctly. (Two defects were found on the SIBLING cases in
this cluster — #1541 on ELITEA-2144, #1542 on ELITEA-2142/2144 — neither
affects this case's own hover-highlight assertion.)

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest, testid-only `LocatorDescriptor`.
- Page object: extend `automation/pages/chat_page.py` — reuse the same
  `drag_conversation_to_folder()`-family gesture helper ELITEA-2142 adds, but
  this case needs an intermediate variant that PAUSES mid-gesture (over each
  candidate folder) to read `data-drop-active` before continuing — e.g.
  `hover_conversation_drag_over_folder(conversation_id, folder_id, hold_ms=300)`
  that presses, moves onto the folder, waits, returns without releasing, so
  the test can assert the highlight, then either move to the next folder or
  complete the drop via a companion `release_drag_onto_folder(folder_id)`.
- `mouse.up()` must always be called before the test ends (even on assertion
  failure) — an unreleased mouse button leaks into the NEXT test's page
  state in the same browser context if not handled in a `finally`. Confirmed
  this matters live: this pass's exploration script had to explicitly
  release a stuck drag more than once.
- Priority marker: `priority: medium` → `@pytest.mark.p2`.
